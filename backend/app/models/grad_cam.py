from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..core.database import Base


class GradCAMResult(Base):
    __tablename__ = "grad_cam_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    classification_id = Column(UUID(as_uuid=True), ForeignKey("tile_classifications.id", ondelete="CASCADE"), nullable=False)
    tile_id = Column(UUID(as_uuid=True), ForeignKey("tiles.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("classification_tasks.id", ondelete="CASCADE"), nullable=False)
    
    tile_x = Column(Integer, nullable=False)
    tile_y = Column(Integer, nullable=False)
    
    target_class = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    
    heatmap_data = Column(LargeBinary, nullable=False)
    heatmap_width = Column(Integer, nullable=False)
    heatmap_height = Column(Integer, nullable=False)
    
    bbox_x = Column(Integer)
    bbox_y = Column(Integer)
    bbox_width = Column(Integer)
    bbox_height = Column(Integer)
    bbox_area_ratio = Column(Float)
    bbox_avg_intensity = Column(Float)
    bbox_max_intensity = Column(Float)
    bbox_confidence = Column(Float)
    
    has_bbox = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    classification = relationship("TileClassification", back_populates="grad_cam_results")
    tile = relationship("Tile")
    image = relationship("ImageMetadata")
    task = relationship("ClassificationTask")
