from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Confidence(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


class DetectionSource(str, Enum):
    RGB     = "rgb"
    THERMAL = "thermal"
    FUSION  = "fusion"


class BoundingBox(BaseModel):
    x_norm: float   # 0.0 - 1.0 relativo al ancho del frame
    y_norm: float
    w_norm: float
    h_norm: float


class DetectionPayload(BaseModel):
    confidence: Confidence
    confidence_score: float
    source: DetectionSource
    temperature_celsius: Optional[float] = None
    bounding_box: BoundingBox


class ImageUploadRequest(BaseModel):
    mission_id: str
    lat: float
    lng: float
    altitude_m: float
    timestamp: datetime
    view_mode: str = "rgb"          # rgb | thermal | overlay
    camera_source: str = "esp32"
    detections: List[DetectionPayload] = []


class DetectionResponse(BaseModel):
    id: str
    mission_id: str
    image_id: str
    timestamp: datetime
    lat: float
    lng: float
    altitude_m: float
    confidence: Confidence
    confidence_score: float
    source: DetectionSource
    temperature_celsius: Optional[float]
    bounding_box: BoundingBox


class ImageResponse(BaseModel):
    id: str
    mission_id: str
    timestamp: datetime
    lat: float
    lng: float
    altitude_m: float
    view_mode: str
    has_detections: bool
    detection_count: int
    thumbnail_b64: str
    detection_ids: List[str]


class ImageListResponse(BaseModel):
    items: List[ImageResponse]
    total: int
    page: int
    page_size: int
