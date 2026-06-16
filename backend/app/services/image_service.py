import numpy as np
from typing import Tuple, Optional
from PIL import Image
import tifffile
from io import BytesIO
from sqlalchemy.orm import Session
from uuid import UUID

from ..models.image import Image as ImageModel
from ..models.tile import Tile as TileModel
from ..schemas.image import ImageMetadataCreate, ImageMetadataResponse
from .minio_service import MinioService
from .tile_service import TileService
from ..core.config import settings


class ImageService:
    def __init__(self, db: Session):
        self.db = db
        self.minio_service = MinioService()
        self.tile_service = TileService(tile_size=settings.tile_size)

    def _load_image(self, file_data: bytes, filename: str) -> Tuple[np.ndarray, str]:
        ext = filename.lower().split('.')[-1]
        if ext in ['png', 'jpg', 'jpeg']:
            img = Image.open(BytesIO(file_data))
            img_array = np.array(img)
            format_type = 'png'
        elif ext in ['tif', 'tiff']:
            img_array = tifffile.imread(BytesIO(file_data))
            format_type = 'tiff'
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        if len(img_array.shape) == 2:
            img_array = np.stack([img_array] * 3, axis=-1)
        elif img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]

        return img_array, format_type

    async def upload_image(self, file_data: bytes, filename: str, content_type: str, file_size: int) -> ImageMetadataResponse:
        img_array, format_type = self._load_image(file_data, filename)
        height, width = img_array.shape[:2]

        num_tiles_x, num_tiles_y, total_tiles = self.tile_service.calculate_tiling(width, height)

        minio_bucket, minio_object = self.minio_service.upload_image(file_data, filename, content_type)

        db_image = ImageModel(
            filename=filename,
            format=format_type,
            width=width,
            height=height,
            file_size=file_size,
            tile_size=settings.tile_size,
            num_tiles_x=num_tiles_x,
            num_tiles_y=num_tiles_y,
            total_tiles=total_tiles,
            minio_bucket=minio_bucket,
            minio_object=minio_object
        )
        self.db.add(db_image)
        self.db.flush()

        tiles = self.tile_service.slice_image(img_array)
        for tile_info in tiles:
            db_tile = TileModel(
                image_id=db_image.id,
                tile_x=tile_info['tile_x'],
                tile_y=tile_info['tile_y'],
                pixel_x=tile_info['pixel_x'],
                pixel_y=tile_info['pixel_y']
            )
            self.db.add(db_tile)

        self.db.commit()
        self.db.refresh(db_image)

        return ImageMetadataResponse.model_validate(db_image)

    def get_image(self, image_id: UUID) -> Optional[ImageModel]:
        return self.db.query(ImageModel).filter(ImageModel.id == image_id).first()

    def get_image_array(self, image_id: UUID) -> np.ndarray:
        db_image = self.get_image(image_id)
        if not db_image:
            raise ValueError(f"Image not found: {image_id}")

        image_data = self.minio_service.get_image(db_image.minio_object)

        if db_image.format == 'tiff':
            img_array = tifffile.imread(image_data)
        else:
            img = Image.open(image_data)
            img_array = np.array(img)

        if len(img_array.shape) == 2:
            img_array = np.stack([img_array] * 3, axis=-1)
        elif img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]

        return img_array

    def get_tiles(self, image_id: UUID):
        return self.db.query(TileModel).filter(TileModel.image_id == image_id).all()

    def get_tile(self, image_id: UUID, tile_x: int, tile_y: int) -> Optional[TileModel]:
        return self.db.query(TileModel).filter(
            TileModel.image_id == image_id,
            TileModel.tile_x == tile_x,
            TileModel.tile_y == tile_y
        ).first()

    def get_dzi_tile(self, image_id: UUID, z: int, x: int, y: int) -> bytes:
        img_array = self.get_image_array(image_id)
        return self.tile_service.generate_dzi_tile(img_array, z, x, y)

    def get_dzi_xml(self, image_id: UUID) -> str:
        db_image = self.get_image(image_id)
        if not db_image:
            raise ValueError(f"Image not found: {image_id}")

        props = self.tile_service.get_dzi_properties(db_image.width, db_image.height)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Image xmlns="http://schemas.microsoft.com/deepzoom/2008"
       Url="/api/images/{image_id}/tile/"
       Format="{props['format']}"
       Overlap="{props['overlap']}"
       TileSize="{props['tile_size']}">
  <Size Height="{props['height']}" Width="{props['width']}"/>
</Image>'''

    def list_images(self, skip: int = 0, limit: int = 100):
        return self.db.query(ImageModel).order_by(ImageModel.upload_time.desc()).offset(skip).limit(limit).all()

    def list_images_with_count(self, skip: int = 0, limit: int = 100) -> Tuple[List[ImageModel], int]:
        query = self.db.query(ImageModel).order_by(ImageModel.upload_time.desc())
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
