"""
Pydantic v2 DTOs — used by REST endpoints and internally
when saving detections from the WebSocket pipeline.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ─────────────────────────────────────────────────────────────
# MISSION
# ─────────────────────────────────────────────────────────────
class MissionCreate(BaseModel):
    name:        str
    description: Optional[str] = None
    area_geojson: Optional[dict] = None   # GeoJSON polygon


class MissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:          UUID
    name:        str
    description: Optional[str]
    status:      str
    started_at:  datetime
    ended_at:    Optional[datetime]
    created_at:  datetime


# ─────────────────────────────────────────────────────────────
# DETECTION
# ─────────────────────────────────────────────────────────────
class DetectionCreate(BaseModel):
    """
    Payload sent from main.py WebSocket pipeline → persistence layer.
    Matches exactly what your detection pipeline already produces.
    """
    mission_id:           Optional[UUID] = None
    latitude:             float
    longitude:            float
    altitude:             Optional[float] = None
    confidence:           str   = Field(..., pattern="^(low|medium|high)$")
    source:               str   = Field(..., pattern="^(rgb|thermal|fused)$")
    temperature:          Optional[float] = None
    raw_confidence_score: Optional[float] = None
    detected_at:          Optional[datetime] = None  # if None, DB uses NOW()


class DetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                   UUID
    mission_id:           Optional[UUID]
    latitude:             float
    longitude:            float
    altitude:             Optional[float]
    confidence:           str
    source:               str
    temperature:          Optional[float]
    raw_confidence_score: Optional[float]
    detected_at:          datetime
    created_at:           datetime
    images:               List[ImageResponse] = []


# ─────────────────────────────────────────────────────────────
# IMAGE
# ─────────────────────────────────────────────────────────────
class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              UUID
    detection_id:    UUID
    image_type:      str
    storage_backend: str
    storage_key:     str
    url:             Optional[str]
    file_size_bytes: Optional[int]
    mime_type:       str
    created_at:      datetime


# ─────────────────────────────────────────────────────────────
# QUERY FILTERS — used by GET /api/detections
# ─────────────────────────────────────────────────────────────
class DetectionFilters(BaseModel):
    mission_id:  Optional[UUID]   = None
    confidence:  Optional[str]    = None          # low | medium | high
    source:      Optional[str]    = None          # rgb | thermal | fused
    date_from:   Optional[datetime] = None
    date_to:     Optional[datetime] = None
    lat_min:     Optional[float]  = None
    lat_max:     Optional[float]  = None
    lng_min:     Optional[float]  = None
    lng_max:     Optional[float]  = None
    limit:       int = Field(default=100, le=1000)
    offset:      int = Field(default=0,   ge=0)


# forward ref resolution
DetectionResponse.model_rebuild()