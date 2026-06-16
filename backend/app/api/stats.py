from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from ..core.database import get_db
from ..schemas.stats import StatsSummaryResponse, ProfileResponse
from ..services.classification_service import ClassificationService

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/{task_id}/summary", response_model=StatsSummaryResponse)
def get_stats_summary(task_id: UUID, db: Session = Depends(get_db)):
    service = ClassificationService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")

    summary = service.get_stats_summary(task_id)
    return StatsSummaryResponse(**summary)


@router.get("/{task_id}/profile", response_model=ProfileResponse)
def get_profile_data(task_id: UUID, db: Session = Depends(get_db)):
    service = ClassificationService(db)
    try:
        profile_data = service.get_profile_data(task_id)
        return ProfileResponse(**profile_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
