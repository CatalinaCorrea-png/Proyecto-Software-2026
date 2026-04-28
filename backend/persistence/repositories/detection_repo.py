"""
All DB operations for the detections table.  Pure async SQLAlchemy — no business logic.
"""
from uuid import UUID
from typing import Optional, List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from persistence.models import Detection
from persistence.schemas import DetectionCreate, DetectionFilters


async def create_detection(db: AsyncSession, data: DetectionCreate) -> Detection:
    detection = Detection(
        mission_id           = data.mission_id,
        latitude             = data.latitude,
        longitude            = data.longitude,
        altitude             = data.altitude,
        confidence           = data.confidence,
        source               = data.source,
        temperature          = data.temperature,
        raw_confidence_score = data.raw_confidence_score,
        **({"detected_at": data.detected_at} if data.detected_at else {}),
    )
    db.add(detection)
    await db.flush()    # get the generated UUID without committing
    await db.refresh(detection)
    return detection


async def get_detection(db: AsyncSession, detection_id: UUID) -> Optional[Detection]:
    result = await db.execute(
        select(Detection)
        .options(selectinload(Detection.images))   # eager-load images
        .where(Detection.id == detection_id)
    )
    return result.scalar_one_or_none()


async def list_detections(db: AsyncSession, filters: DetectionFilters) -> List[Detection]:
    conditions = []

    if filters.mission_id:
        conditions.append(Detection.mission_id == filters.mission_id)
    if filters.confidence:
        conditions.append(Detection.confidence == filters.confidence)
    if filters.source:
        conditions.append(Detection.source == filters.source)
    if filters.date_from:
        conditions.append(Detection.detected_at >= filters.date_from)
    if filters.date_to:
        conditions.append(Detection.detected_at <= filters.date_to)
    if filters.lat_min is not None:
        conditions.append(Detection.latitude >= filters.lat_min)
    if filters.lat_max is not None:
        conditions.append(Detection.latitude <= filters.lat_max)
    if filters.lng_min is not None:
        conditions.append(Detection.longitude >= filters.lng_min)
    if filters.lng_max is not None:
        conditions.append(Detection.longitude <= filters.lng_max)

    stmt = (
        select(Detection)
        .options(selectinload(Detection.images))
        .where(and_(*conditions) if conditions else True)
        .order_by(Detection.detected_at.desc())
        .limit(filters.limit)
        .offset(filters.offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_detection(db: AsyncSession, detection_id: UUID) -> bool:
    detection = await get_detection(db, detection_id)
    if not detection:
        return False
    await db.delete(detection)
    return True