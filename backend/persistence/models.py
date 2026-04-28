"""
SQLAlchemy 2.x ORM models.  All tables use UUID primary keys.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    CheckConstraint, Column, DateTime, Double,
    Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────────
# MISSION
# ─────────────────────────────────────────────────────────────
class Mission(Base):
    __tablename__ = "missions"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String(120), nullable=False)
    description = Column(Text)
    started_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at    = Column(DateTime(timezone=True))
    status      = Column(
        String(20), nullable=False, default="active",
        info={"check": "status IN ('active','completed','aborted')"}
    )
    area_geojson = Column(JSONB)          # optional GeoJSON polygon
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    detections = relationship("Detection", back_populates="mission", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Mission id={self.id} name={self.name} status={self.status}>"


# ─────────────────────────────────────────────────────────────
# DETECTION
# ─────────────────────────────────────────────────────────────
class Detection(Base):
    __tablename__ = "detections"
    __table_args__ = (
        CheckConstraint("confidence IN ('low','medium','high')", name="ck_confidence"),
        CheckConstraint("source IN ('rgb','thermal','fused')",   name="ck_source"),
    )

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="SET NULL"), nullable=True)

    # GPS
    latitude   = Column(Double, nullable=False)
    longitude  = Column(Double, nullable=False)
    altitude   = Column(Float)

    # AI result
    confidence           = Column(String(10), nullable=False)   # low | medium | high
    source               = Column(String(20), nullable=False)   # rgb | thermal | fused
    temperature          = Column(Float)                        # thermal reading, nullable
    raw_confidence_score = Column(Float)                        # 0.0-1.0 float from YOLO

    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    mission = relationship("Mission", back_populates="detections")
    images  = relationship("Image",   back_populates="detection", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Detection id={self.id} confidence={self.confidence} source={self.source}>"


# ─────────────────────────────────────────────────────────────
# IMAGE
# Images are NEVER stored as blobs.
# We store only the path/key; files live on disk or S3.
# ─────────────────────────────────────────────────────────────
class Image(Base):
    __tablename__ = "images"
    __table_args__ = (
        CheckConstraint(
            "image_type IN ('rgb','thermal_overlay','thermal_pure')",
            name="ck_image_type"
        ),
        CheckConstraint(
            "storage_backend IN ('local','s3','gcs')",
            name="ck_storage_backend"
        ),
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    detection_id     = Column(UUID(as_uuid=True), ForeignKey("detections.id", ondelete="CASCADE"), nullable=False)

    image_type       = Column(String(20), nullable=False, default="rgb")
    storage_backend  = Column(String(20), nullable=False, default="local")

    # local  → relative path  e.g. "missions/uuid/detections/uuid/rgb.jpg"
    # s3/gcs → object key     e.g. "aerosearch/missions/uuid/rgb.jpg"
    storage_key      = Column(Text, nullable=False)

    url              = Column(Text)             # pre-signed / CDN URL (populated on read)
    file_size_bytes  = Column(Integer)
    mime_type        = Column(String(40), nullable=False, default="image/jpeg")
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    detection = relationship("Detection", back_populates="images")

    def __repr__(self):
        return f"<Image id={self.id} type={self.image_type} backend={self.storage_backend}>"