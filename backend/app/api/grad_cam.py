from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import numpy as np
import io

from ..core.database import get_db
from ..schemas.grad_cam import (
    GradCAMResultResponse,
    GradCAMHeatmapResponse,
    GradCAMListResponse
)
from ..services.classification_service import ClassificationService

router = APIRouter(prefix="/api/grad-cam", tags=["grad-cam"])


@router.get("/task/{task_id}", response_model=GradCAMListResponse)
def list_grad_cam_results(
    task_id: UUID,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db)
):
    service = ClassificationService(db)
    skip = (page - 1) * page_size
    items, total = service.get_grad_cam_results(task_id, skip=skip, limit=page_size)
    
    return GradCAMListResponse(
        items=[GradCAMResultResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{grad_cam_id}", response_model=GradCAMResultResponse)
def get_grad_cam_result(
    grad_cam_id: UUID,
    db: Session = Depends(get_db)
):
    service = ClassificationService(db)
    result = service.get_grad_cam_result(grad_cam_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Grad-CAM result not found")
    
    return GradCAMResultResponse.model_validate(result)


@router.get("/{grad_cam_id}/heatmap", response_model=GradCAMHeatmapResponse)
def get_grad_cam_heatmap(
    grad_cam_id: UUID,
    db: Session = Depends(get_db)
):
    service = ClassificationService(db)
    heatmap_data = service.get_grad_cam_heatmap(grad_cam_id)
    
    if not heatmap_data:
        raise HTTPException(status_code=404, detail="Grad-CAM result not found")
    
    return GradCAMHeatmapResponse(**heatmap_data)


@router.get("/{grad_cam_id}/heatmap/image")
def get_grad_cam_heatmap_image(
    grad_cam_id: UUID,
    colormap: str = "jet",
    db: Session = Depends(get_db)
):
    service = ClassificationService(db)
    result = service.get_grad_cam_result(grad_cam_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Grad-CAM result not found")
    
    try:
        import cv2
        
        heatmap_array = np.frombuffer(result.heatmap_data, dtype=np.uint8)
        heatmap_array = heatmap_array.reshape(result.heatmap_height, result.heatmap_width)
        
        colormap_map = {
            'jet': cv2.COLORMAP_JET,
            'hot': cv2.COLORMAP_HOT,
            'cool': cv2.COLORMAP_COOL,
            'viridis': cv2.COLORMAP_VIRIDIS,
            'plasma': cv2.COLORMAP_PLASMA,
            'inferno': cv2.COLORMAP_INFERNO,
            'magma': cv2.COLORMAP_MAGMA,
            'cividis': cv2.COLORMAP_CIVIDIS,
        }
        
        cmap = colormap_map.get(colormap.lower(), cv2.COLORMAP_JET)
        heatmap_colored = cv2.applyColorMap(heatmap_array, cmap)
        
        if result.has_bbox and result.bbox_x is not None:
            cv2.rectangle(
                heatmap_colored,
                (result.bbox_x, result.bbox_y),
                (result.bbox_x + result.bbox_width, result.bbox_y + result.bbox_height),
                (255, 255, 255),
                2
            )
        
        _, buffer = cv2.imencode('.png', heatmap_colored)
        img_bytes = buffer.tobytes()
        
        return Response(
            content=img_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=gradcam_{grad_cam_id}.png"
            }
        )
        
    except ImportError:
        raise HTTPException(status_code=500, detail="OpenCV not available for image generation")


@router.get("/task/{task_id}/tile/{tile_x}/{tile_y}", response_model=GradCAMResultResponse)
def get_grad_cam_by_tile(
    task_id: UUID,
    tile_x: int,
    tile_y: int,
    db: Session = Depends(get_db)
):
    service = ClassificationService(db)
    result = service.get_grad_cam_by_tile(task_id, tile_x, tile_y)
    
    if not result:
        raise HTTPException(status_code=404, detail="Grad-CAM result not found for this tile")
    
    return GradCAMResultResponse.model_validate(result)
