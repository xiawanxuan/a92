from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import io

from ..core.database import get_db
from ..schemas.image import (
    ImageMetadataResponse,
    ImageUploadResponse,
    ImageListResponse
)
from ..services.image_service import ImageService

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        allowed_extensions = {'.png', '.tif', '.tiff'}
        filename_lower = file.filename.lower()
        if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
            )

        file_data = await file.read()
        file_size = len(file_data)

        service = ImageService(db)
        metadata = await service.upload_image(
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            file_size=file_size
        )

        return ImageUploadResponse(
            id=metadata.id,
            filename=metadata.filename,
            width=metadata.width,
            height=metadata.height,
            total_tiles=metadata.total_tiles,
            message="Image uploaded successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{image_id}", response_model=ImageMetadataResponse)
def get_image_metadata(image_id: UUID, db: Session = Depends(get_db)):
    service = ImageService(db)
    image = service.get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return ImageMetadataResponse.model_validate(image)


@router.get("/{image_id}/dzi")
def get_dzi(image_id: UUID, db: Session = Depends(get_db)):
    service = ImageService(db)
    try:
        dzi_xml = service.get_dzi_xml(image_id)
        return Response(content=dzi_xml, media_type="application/xml")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{image_id}/tile/{z}/{x}_{y}")
def get_tile(image_id: UUID, z: int, x: int, y: int, db: Session = Depends(get_db)):
    service = ImageService(db)
    try:
        tile_data = service.get_dzi_tile(image_id, z, x, y)
        return Response(content=tile_data, media_type="image/jpeg")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{image_id}/download")
def download_original(image_id: UUID, db: Session = Depends(get_db)):
    service = ImageService(db)
    image = service.get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        image_data = service.minio_service.get_image(image.minio_object)
        return StreamingResponse(
            image_data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={image.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("", response_model=ImageListResponse)
def list_images(page: int = 1, page_size: int = 100, db: Session = Depends(get_db)):
    service = ImageService(db)
    skip = (page - 1) * page_size
    images, total = service.list_images_with_count(skip=skip, limit=page_size)
    return ImageListResponse(
        items=[ImageMetadataResponse.model_validate(img) for img in images],
        total=total,
        page=page,
        page_size=page_size
    )
