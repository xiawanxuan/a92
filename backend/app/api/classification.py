from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import io
import json

from ..core.database import get_db
from ..schemas.classification import (
    ClassificationStartRequest,
    ClassificationTaskResponse,
    ClassificationResultsResponse,
    TileClassificationResponse,
    CorrectionRequest,
    CorrectionResponse,
    CorrectionRecordResponse,
    TaskStatus,
    TaskListResponse,
    CorrectionListResponse
)
from ..schemas.stats import HeatmapDataResponse
from ..services.classification_service import ClassificationService
from ..services.image_service import ImageService
from ..services.tile_service import TileService
from ..ml.inference import get_inference_service
from ..core.config import settings

router = APIRouter(prefix="/api/classification", tags=["classification"])


def run_classification_task(task_id: UUID, image_id: UUID, db: Session):
    try:
        service = ClassificationService(db)
        image_service = ImageService(db)
        tile_service = TileService(tile_size=settings.tile_size)
        inference_service = get_inference_service()

        task = service.get_task(task_id)
        if not task:
            return

        task.status = TaskStatus.PROCESSING.value
        db.commit()

        img_array = image_service.get_image_array(image_id)
        tiles = tile_service.slice_image(img_array)

        def progress_callback(processed: int, total: int):
            service.update_task_progress(task_id, processed, total)

        results, grad_cam_results = inference_service.run_inference(
            tiles=tiles,
            image_id=str(image_id),
            progress_callback=progress_callback
        )

        service.save_classification_results(task_id, results)
        
        if grad_cam_results:
            service.save_grad_cam_results(task_id, results, grad_cam_results)
        
        service.complete_task(task_id)

    except Exception as e:
        service = ClassificationService(db)
        service.complete_task(task_id, error=str(e))


@router.post("/start", response_model=ClassificationTaskResponse)
def start_classification(
    request: ClassificationStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    service = ClassificationService(db)

    try:
        task = service.create_task(request.image_id)

        if task.status == TaskStatus.PENDING.value:
            background_tasks.add_task(
                run_classification_task,
                task.id,
                request.image_id,
                db
            )

        return ClassificationTaskResponse.model_validate(task)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start classification: {str(e)}")


@router.get("/{task_id}/status", response_model=ClassificationTaskResponse)
def get_task_status(task_id: UUID, db: Session = Depends(get_db)):
    service = ClassificationService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ClassificationTaskResponse.model_validate(task)


@router.get("/{task_id}/results", response_model=ClassificationResultsResponse)
def get_classification_results(task_id: UUID, db: Session = Depends(get_db)):
    service = ClassificationService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    classifications = service.get_classification_results(task_id)

    results = []
    for cls in classifications:
        tile = cls.tile
        results.append(TileClassificationResponse(
            tile_id=cls.tile_id,
            tile_x=tile.tile_x,
            tile_y=tile.tile_y,
            pixel_x=tile.pixel_x,
            pixel_y=tile.pixel_y,
            predicted_class=cls.predicted_class,
            confidence=cls.confidence,
            is_corrected=cls.is_corrected,
            corrected_class=cls.corrected_class,
            corrected_at=cls.corrected_at,
            corrected_by=cls.corrected_by
        ))

    return ClassificationResultsResponse(
        task_id=task_id,
        status=task.status,
        total_tiles=task.total_tiles,
        results=results
    )


@router.get("/{task_id}/heatmap", response_model=HeatmapDataResponse)
def get_heatmap_data(task_id: UUID, db: Session = Depends(get_db)):
    service = ClassificationService(db)
    try:
        heatmap_data = service.get_heatmap_data(task_id)
        return HeatmapDataResponse(**heatmap_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{task_id}/tile/{tile_id}/correct", response_model=CorrectionResponse)
def correct_tile(
    task_id: UUID,
    tile_id: UUID,
    request: CorrectionRequest,
    db: Session = Depends(get_db)
):
    service = ClassificationService(db)
    success, classification = service.correct_tile_classification(task_id, tile_id, request)

    if not success:
        raise HTTPException(status_code=404, detail="Classification not found")

    original_class = classification.predicted_class
    if classification.is_corrected and classification.corrected_class != request.new_class:
        original_class = classification.corrected_class

    return CorrectionResponse(
        success=True,
        tile_id=tile_id,
        original_class=original_class,
        new_class=request.new_class,
        message="Correction saved successfully"
    )


@router.get("", response_model=TaskListResponse)
def list_tasks(page: int = 1, page_size: int = 50, db: Session = Depends(get_db)):
    service = ClassificationService(db)
    skip = (page - 1) * page_size
    tasks, total = service.list_tasks_with_count(skip=skip, limit=page_size)
    return TaskListResponse(
        items=[ClassificationTaskResponse.model_validate(task) for task in tasks],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/corrections", response_model=CorrectionListResponse)
def get_correction_records(page: int = 1, page_size: int = 100, db: Session = Depends(get_db)):
    service = ClassificationService(db)
    skip = (page - 1) * page_size
    records, total = service.get_correction_records_with_count(skip=skip, limit=page_size)
    return CorrectionListResponse(
        items=[CorrectionRecordResponse.model_validate(record) for record in records],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{task_id}/export")
def export_report(task_id: UUID, db: Session = Depends(get_db)):
    service = ClassificationService(db)
    try:
        report = service.export_task_report(task_id)
        json_str = json.dumps(report, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(json_str.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=classification_report_{task_id}.json"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
