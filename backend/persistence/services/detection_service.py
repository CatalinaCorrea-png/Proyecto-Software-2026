"""
Business logic layer — called from both REST endpoints
and directly from the WebSocket pipeline in main.py.
"""
from __future__ import annotations
from typing import Optional
import base64

from sqlalchemy.ext.asyncio import AsyncSession

from persistence.repositories import detection_repo
from persistence.services.image_service import store_image
from persistence.schemas import DetectionCreate
from persistence.models import Detection


async def save_detection_with_frames(
    db:              AsyncSession,
    payload:         DetectionCreate,
    frame_b64:       Optional[str] = None,           # RGB annotated frame
    thermal_b64:     Optional[str] = None,           # thermal overlay
    thermal_raw_b64: Optional[str] = None,           # pure thermal miniature
) -> Detection:
    """
    1. Persist the Detection row.
    2. If frame bytes are provided, persist each image variant.
    
    Called from main.py every time confidence is 'medium' or 'high'.
    Runs inside the same DB transaction — all or nothing.
    """
    detection = await detection_repo.create_detection(db, payload)

    if frame_b64:
        await store_image(
            db, detection,
            image_bytes = base64.b64decode(frame_b64),
            image_type  = "rgb",
        )

    if thermal_b64:
        await store_image(
            db, detection,
            image_bytes = base64.b64decode(thermal_b64),
            image_type  = "thermal_overlay",
        )

    if thermal_raw_b64:
        await store_image(
            db, detection,
            image_bytes = base64.b64decode(thermal_raw_b64),
            image_type  = "thermal_pure",
        )

    return detection