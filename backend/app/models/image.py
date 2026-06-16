from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base


class Image(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    format = Column(String(10), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    tile_size = Column(Integer, nullable=False, default=512)
    num_tiles_x = Column(Integer, nullable=False)
    num_tiles_y = Column(Integer, nullable=False)
    total_tiles = Column(Integer, nullable=False)
    minio_bucket = Column(String(100), nullable=False)
    minio_object = Column(String(255), nullable=False)
    dzi_bucket = Column(String(100), nullable=True)
    dzi_object = Column(String(255), nullable=True)
    upload_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tiles = relationship("Tile", back_populates="image", cascade="all, delete-orphan")
    tasks = relationship("ClassificationTask", back_populates="image", cascade="all, delete-orphan")
