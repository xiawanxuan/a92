from pydantic import BaseModel
from typing import Dict, List
from uuid import UUID
from .classification import SubstrateType


class ClassStats(BaseModel):
    count: int
    percentage: float
    avg_confidence: float


class StatsSummaryResponse(BaseModel):
    task_id: UUID
    total_tiles: int
    class_distribution: Dict[SubstrateType, ClassStats]


class ProfileDataPoint(BaseModel):
    position: int
    sediment: float
    rock: float
    coral: float
    man_made: float


class ProfileResponse(BaseModel):
    task_id: UUID
    profile_data: List[ProfileDataPoint]
    image_width: int
    tile_size: int


class HeatmapDataResponse(BaseModel):
    task_id: UUID
    tile_size: int
    num_tiles_x: int
    num_tiles_y: int
    tile_data: List[Dict]
