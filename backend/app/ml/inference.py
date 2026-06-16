import torch
import numpy as np
from typing import List, Dict, Callable, Optional
from tqdm import tqdm

from .model import ClassificationModel
from .dataset import create_dataloader
from ..core.config import settings


class InferenceService:
    def __init__(self, model: Optional[ClassificationModel] = None):
        self.model = model or ClassificationModel(
            model_path=settings.model_path,
            device=settings.device
        )
        self.batch_size = settings.batch_size

    def run_inference(
        self,
        tiles: List[Dict],
        image_id: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        if not tiles:
            return []

        dataloader = create_dataloader(
            tiles,
            batch_size=self.batch_size,
            tile_size=settings.tile_size
        )

        total_tiles = len(tiles)
        processed = 0
        results = []

        with torch.no_grad():
            for batch_tensors, batch_metadata in tqdm(dataloader, desc="Classifying tiles"):
                original_h = batch_metadata.get('original_h')
                original_w = batch_metadata.get('original_w')
                
                predictions, confidences, _ = self.model.predict(
                    batch_tensors,
                    original_h=original_h,
                    original_w=original_w
                )

                for i in range(len(predictions)):
                    class_idx = predictions[i].item()
                    confidence = confidences[i].item()
                    class_name = self.model.get_class_name(class_idx)

                    result = {
                        'image_id': image_id,
                        'tile_x': batch_metadata['tile_x'][i].item() if isinstance(batch_metadata['tile_x'][i], torch.Tensor) else batch_metadata['tile_x'][i],
                        'tile_y': batch_metadata['tile_y'][i].item() if isinstance(batch_metadata['tile_y'][i], torch.Tensor) else batch_metadata['tile_y'][i],
                        'pixel_x': batch_metadata['pixel_x'][i].item() if isinstance(batch_metadata['pixel_x'][i], torch.Tensor) else batch_metadata['pixel_x'][i],
                        'pixel_y': batch_metadata['pixel_y'][i].item() if isinstance(batch_metadata['pixel_y'][i], torch.Tensor) else batch_metadata['pixel_y'][i],
                        'predicted_class': class_name,
                        'confidence': round(confidence, 4)
                    }
                    results.append(result)

                processed += len(predictions)
                if progress_callback:
                    progress_callback(processed, total_tiles)

        return results


_inference_service: Optional[InferenceService] = None


def get_inference_service() -> InferenceService:
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService()
    return _inference_service
