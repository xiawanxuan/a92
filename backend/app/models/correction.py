from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base


class ClassificationTask(Base):
    __tablename__ = "classification_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(Integer, nullable=False, default=0)
    processed_tiles = Column(Integer, nullable=False, default=0)
    total_tiles = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime)
    error_message = Column(Text)

    image = relationship("Image", back_populates="tasks")
    tile_classifications = relationship("TileClassification", back_populates="task", cascade="all, delete-orphan")


class TileClassification(Base):
    __tablename__ = "tile_classifications"
    __table_args__ = (
        UniqueConstraint('task_id', 'tile_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("classification_tasks.id", ondelete="CASCADE"), nullable=False)
    tile_id = Column(UUID(as_uuid=True), ForeignKey("tiles.id", ondelete="CASCADE"), nullable=False)
    predicted_class = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    is_corrected = Column(Boolean, nullable=False, default=False)
    corrected_class = Column(String(20))
    corrected_at = Column(DateTime)
    corrected_by = Column(String(100))

    task = relationship("ClassificationTask", back_populates="tile_classifications")
    tile = relationship("Tile", back_populates="classifications")
    correction_records = relationship("CorrectionRecord", back_populates="classification", cascade="all, delete-orphan")
    grad_cam_results = relationship("GradCAMResult", back_populates="classification", cascade="all, delete-orphan")


class CorrectionRecord(Base):
    __tablename__ = "correction_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    classification_id = Column(UUID(as_uuid=True), ForeignKey("tile_classifications.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("classification_tasks.id", ondelete="CASCADE"), nullable=False)
    tile_id = Column(UUID(as_uuid=True), ForeignKey("tiles.id", ondelete="CASCADE"), nullable=False)
    tile_x = Column(Integer, nullable=False)
    tile_y = Column(Integer, nullable=False)
    original_class = Column(String(20), nullable=False)
    new_class = Column(String(20), nullable=False)
    reason = Column(Text)
    operator = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    classification = relationship("TileClassification", back_populates="correction_records")
