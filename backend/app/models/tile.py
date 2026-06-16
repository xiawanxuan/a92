from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base


class Tile(Base):
    __tablename__ = "tiles"
    __table_args__ = (
        UniqueConstraint('image_id', 'tile_x', 'tile_y'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    tile_x = Column(Integer, nullable=False)
    tile_y = Column(Integer, nullable=False)
    pixel_x = Column(Integer, nullable=False)
    pixel_y = Column(Integer, nullable=False)

    image = relationship("Image", back_populates="tiles")
    classifications = relationship("TileClassification", back_populates="tile", cascade="all, delete-orphan")
