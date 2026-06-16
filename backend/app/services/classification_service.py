import numpy as np
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from collections import defaultdict

from ..models.correction import ClassificationTask, TileClassification, CorrectionRecord
from ..models.tile import Tile
from ..models.image import Image
from ..schemas.classification import SubstrateType, TaskStatus, CorrectionRequest
from .image_service import ImageService
from ..core.config import settings


class ClassificationService:
    def __init__(self, db: Session):
        self.db = db
        self.image_service = ImageService(db)

    def create_task(self, image_id: UUID) -> ClassificationTask:
        db_image = self.image_service.get_image(image_id)
        if not db_image:
            raise ValueError(f"Image not found: {image_id}")

        existing_task = self.db.query(ClassificationTask).filter(
            ClassificationTask.image_id == image_id,
            ClassificationTask.status.in_(['pending', 'processing'])
        ).first()

        if existing_task:
            return existing_task

        db_task = ClassificationTask(
            image_id=image_id,
            total_tiles=db_image.total_tiles,
            status='pending'
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def get_task(self, task_id: UUID) -> Optional[ClassificationTask]:
        return self.db.query(ClassificationTask).filter(ClassificationTask.id == task_id).first()

    def update_task_progress(self, task_id: UUID, processed: int, total: int):
        task = self.get_task(task_id)
        if task:
            task.processed_tiles = processed
            task.progress = int((processed / total) * 100)
            self.db.commit()

    def complete_task(self, task_id: UUID, error: Optional[str] = None):
        task = self.get_task(task_id)
        if task:
            task.status = 'failed' if error else 'completed'
            task.end_time = datetime.utcnow()
            task.error_message = error
            task.progress = 100 if not error else task.progress
            self.db.commit()

    def save_classification_results(self, task_id: UUID, results: List[Dict]):
        for result in results:
            tile = self.db.query(Tile).filter(
                Tile.image_id == result['image_id'],
                Tile.tile_x == result['tile_x'],
                Tile.tile_y == result['tile_y']
            ).first()

            if tile:
                classification = TileClassification(
                    task_id=task_id,
                    tile_id=tile.id,
                    predicted_class=result['predicted_class'],
                    confidence=result['confidence']
                )
                self.db.add(classification)
        self.db.commit()

    def get_classification_results(self, task_id: UUID) -> List[TileClassification]:
        return self.db.query(TileClassification).filter(
            TileClassification.task_id == task_id
        ).join(Tile).all()

    def get_classification_by_tile(self, task_id: UUID, tile_id: UUID) -> Optional[TileClassification]:
        return self.db.query(TileClassification).filter(
            TileClassification.task_id == task_id,
            TileClassification.tile_id == tile_id
        ).first()

    def correct_tile_classification(
        self,
        task_id: UUID,
        tile_id: UUID,
        request: CorrectionRequest
    ) -> Tuple[bool, Optional[TileClassification]]:
        classification = self.get_classification_by_tile(task_id, tile_id)
        if not classification:
            return False, None

        original_class = classification.corrected_class if classification.is_corrected else classification.predicted_class

        if original_class == request.new_class.value:
            return True, classification

        task = self.get_task(task_id)
        tile = self.db.query(Tile).filter(Tile.id == tile_id).first()

        correction = CorrectionRecord(
            classification_id=classification.id,
            image_id=task.image_id,
            task_id=task_id,
            tile_id=tile_id,
            tile_x=tile.tile_x,
            tile_y=tile.tile_y,
            original_class=original_class,
            new_class=request.new_class.value,
            reason=request.reason,
            operator=request.operator
        )
        self.db.add(correction)

        classification.is_corrected = True
        classification.corrected_class = request.new_class.value
        classification.corrected_at = datetime.utcnow()
        classification.corrected_by = request.operator

        self.db.commit()
        self.db.refresh(classification)
        return True, classification

    def get_stats_summary(self, task_id: UUID) -> Dict:
        classifications = self.get_classification_results(task_id)
        if not classifications:
            return {'task_id': task_id, 'total_tiles': 0, 'class_distribution': {}}

        total = len(classifications)
        class_stats = defaultdict(lambda: {'count': 0, 'confidences': []})

        for cls in classifications:
            actual_class = cls.corrected_class if cls.is_corrected else cls.predicted_class
            class_stats[actual_class]['count'] += 1
            class_stats[actual_class]['confidences'].append(cls.confidence)

        distribution = {}
        for class_type in ['sediment', 'rock', 'coral', 'man_made']:
            stats = class_stats[class_type]
            count = stats['count']
            distribution[SubstrateType(class_type)] = {
                'count': count,
                'percentage': (count / total * 100) if total > 0 else 0,
                'avg_confidence': (sum(stats['confidences']) / len(stats['confidences'])) if stats['confidences'] else 0
            }

        return {
            'task_id': task_id,
            'total_tiles': total,
            'class_distribution': distribution
        }

    def get_profile_data(self, task_id: UUID) -> Dict:
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        image = self.image_service.get_image(task.image_id)
        classifications = self.get_classification_results(task_id)

        tile_size = image.tile_size
        num_tiles_x = image.num_tiles_x

        column_data = defaultdict(lambda: defaultdict(int))
        column_total = defaultdict(int)

        for cls in classifications:
            tile = self.db.query(Tile).filter(Tile.id == cls.tile_id).first()
            if tile:
                actual_class = cls.corrected_class if cls.is_corrected else cls.predicted_class
                column_data[tile.tile_x][actual_class] += 1
                column_total[tile.tile_x] += 1

        profile_data = []
        for x in range(num_tiles_x):
            position = x * tile_size + tile_size // 2
            total = column_total[x]
            if total > 0:
                profile_data.append({
                    'position': position,
                    'sediment': column_data[x].get('sediment', 0) / total * 100,
                    'rock': column_data[x].get('rock', 0) / total * 100,
                    'coral': column_data[x].get('coral', 0) / total * 100,
                    'man_made': column_data[x].get('man_made', 0) / total * 100
                })
            else:
                profile_data.append({
                    'position': position,
                    'sediment': 0,
                    'rock': 0,
                    'coral': 0,
                    'man_made': 0
                })

        return {
            'task_id': task_id,
            'profile_data': profile_data,
            'image_width': image.width,
            'tile_size': tile_size
        }

    def get_heatmap_data(self, task_id: UUID) -> Dict:
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        image = self.image_service.get_image(task.image_id)
        classifications = self.get_classification_results(task_id)

        tile_data = []
        for cls in classifications:
            tile = self.db.query(Tile).filter(Tile.id == cls.tile_id).first()
            if tile:
                actual_class = cls.corrected_class if cls.is_corrected else cls.predicted_class
                tile_data.append({
                    'tile_id': str(cls.tile_id),
                    'tile_x': tile.tile_x,
                    'tile_y': tile.tile_y,
                    'pixel_x': tile.pixel_x,
                    'pixel_y': tile.pixel_y,
                    'predicted_class': cls.predicted_class,
                    'actual_class': actual_class,
                    'confidence': cls.confidence,
                    'is_corrected': cls.is_corrected
                })

        return {
            'task_id': task_id,
            'tile_size': image.tile_size,
            'num_tiles_x': image.num_tiles_x,
            'num_tiles_y': image.num_tiles_y,
            'tile_data': tile_data
        }

    def list_tasks(self, skip: int = 0, limit: int = 100):
        return self.db.query(ClassificationTask).order_by(ClassificationTask.start_time.desc()).offset(skip).limit(limit).all()

    def list_tasks_with_count(self, skip: int = 0, limit: int = 100) -> Tuple[List[ClassificationTask], int]:
        query = self.db.query(ClassificationTask).order_by(ClassificationTask.start_time.desc())
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_correction_records(self, skip: int = 0, limit: int = 100):
        return self.db.query(CorrectionRecord).order_by(CorrectionRecord.created_at.desc()).offset(skip).limit(limit).all()

    def get_correction_records_with_count(self, skip: int = 0, limit: int = 100) -> Tuple[List[CorrectionRecord], int]:
        query = self.db.query(CorrectionRecord).order_by(CorrectionRecord.created_at.desc())
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def export_report(self, task_id: UUID) -> Dict:
        summary = self.get_stats_summary(task_id)
        profile = self.get_profile_data(task_id)
        task = self.get_task(task_id)
        image = self.image_service.get_image(task.image_id)

        return {
            'task_id': str(task_id),
            'image_info': {
                'filename': image.filename,
                'width': image.width,
                'height': image.height,
                'format': image.format,
                'upload_time': image.upload_time.isoformat()
            },
            'classification_summary': summary,
            'profile_data': profile,
            'task_status': task.status,
            'start_time': task.start_time.isoformat(),
            'end_time': task.end_time.isoformat() if task.end_time else None
        }

    def export_task_report(self, task_id: UUID) -> Dict:
        return self.export_report(task_id)
