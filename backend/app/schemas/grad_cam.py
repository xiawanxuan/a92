from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    area_ratio: float
    avg_intensity: float
    max_intensity: float
    confidence: float


class GradCAMResultResponse(BaseModel):
    id: UUID
    classification_id: UUID
    tile_id: UUID
    image_id: UUID
    task_id: UUID
    tile_x: int
    tile_y: int
    target_class: str
    confidence: float
    heatmap_width: int
    heatmap_height: int
    has_bbox: bool
    bbox: Optional[BoundingBox] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GradCAMHeatmapResponse(BaseModel):
    id: UUID
    tile_x: int
    tile_y: int
    target_class: str
    confidence: float
    heatmap: List[List[float]]
    bbox: Optional[BoundingBox] = None


class GradCAMListResponse(BaseModel):
    items: List[GradCAMResultResponse]
    total: int
    page: int
    page_size: int
