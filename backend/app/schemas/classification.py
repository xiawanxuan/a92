from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum


class SubstrateType(str, Enum):
    SEDIMENT = "sediment"
    ROCK = "rock"
    CORAL = "coral"
    MAN_MADE = "man_made"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ClassificationStartRequest(BaseModel):
    image_id: UUID


class ClassificationTaskResponse(BaseModel):
    id: UUID
    image_id: UUID
    status: TaskStatus
    progress: int
    processed_tiles: int
    total_tiles: int
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class TileClassificationResponse(BaseModel):
    tile_id: UUID
    tile_x: int
    tile_y: int
    pixel_x: int
    pixel_y: int
    predicted_class: SubstrateType
    confidence: float
    is_corrected: bool
    corrected_class: Optional[SubstrateType] = None
    corrected_at: Optional[datetime] = None
    corrected_by: Optional[str] = None

    class Config:
        from_attributes = True


class ClassificationResultsResponse(BaseModel):
    task_id: UUID
    status: TaskStatus
    total_tiles: int
    results: List[TileClassificationResponse]


class CorrectionRequest(BaseModel):
    new_class: SubstrateType
    reason: Optional[str] = None
    operator: str = "anonymous"


class CorrectionResponse(BaseModel):
    success: bool
    tile_id: UUID
    original_class: SubstrateType
    new_class: SubstrateType
    message: str


class CorrectionRecordResponse(BaseModel):
    id: UUID
    image_id: UUID
    task_id: UUID
    tile_id: UUID
    tile_x: int
    tile_y: int
    original_class: SubstrateType
    new_class: SubstrateType
    reason: Optional[str]
    operator: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    items: List[ClassificationTaskResponse]
    total: int
    page: int
    page_size: int


class CorrectionListResponse(BaseModel):
    items: List[CorrectionRecordResponse]
    total: int
    page: int
    page_size: int
