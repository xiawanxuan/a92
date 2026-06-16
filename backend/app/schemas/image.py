from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ImageMetadataBase(BaseModel):
    filename: str
    format: str
    width: int
    height: int
    file_size: int


class ImageMetadataCreate(ImageMetadataBase):
    tile_size: int = 512
    num_tiles_x: int
    num_tiles_y: int
    total_tiles: int
    minio_bucket: str
    minio_object: str
    dzi_bucket: Optional[str] = None
    dzi_object: Optional[str] = None


class ImageMetadataResponse(ImageMetadataBase):
    id: UUID
    tile_size: int
    num_tiles_x: int
    num_tiles_y: int
    total_tiles: int
    minio_bucket: str
    minio_object: str
    dzi_bucket: Optional[str] = None
    dzi_object: Optional[str] = None
    upload_time: datetime
    original_filename: str = Field(alias="filename")

    class Config:
        from_attributes = True
        populate_by_name = True


class TileInfo(BaseModel):
    id: UUID
    tile_x: int
    tile_y: int
    pixel_x: int
    pixel_y: int

    class Config:
        from_attributes = True


class ImageUploadResponse(BaseModel):
    id: UUID
    original_filename: str = Field(alias="filename")
    width: int
    height: int
    total_tiles: int
    message: str

    class Config:
        populate_by_name = True


class ImageListResponse(BaseModel):
    items: List[ImageMetadataResponse]
    total: int
    page: int
    page_size: int
