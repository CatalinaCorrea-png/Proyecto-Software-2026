"""
REST endpoints for detections.
"""
from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from persistence.repositories import detection_repo
from persistence.schemas import DetectionCreate, DetectionResponse, DetectionFilters

router = APIRouter(prefix="/api/detections", tags=["detections"])


@router.post("/", response_model=DetectionResponse, status_code=201)
async def create_detection(
    body: DetectionCreate,
    db:   AsyncSession = Depends(get_db),
):
    """Save a single detection (called by FastAPI pipeline or external clients)."""
    detection = await detection_repo.create_detection(db, body)
    return detection


@router.get("/", response_model=list[DetectionResponse])
async def list_detections(
    mission_id:  Optional[UUID]     = Query(None),
    confidence:  Optional[str]      = Query(None, pattern="^(low|medium|high)$"),
    source:      Optional[str]      = Query(None, pattern="^(rgb|thermal|fused)$"),
    date_from:   Optional[datetime] = Query(None),
    date_to:     Optional[datetime] = Query(None),
    lat_min:     Optional[float]    = Query(None),
    lat_max:     Optional[float]    = Query(None),
    lng_min:     Optional[float]    = Query(None),
    lng_max:     Optional[float]    = Query(None),
    limit:       int                = Query(100, le=1000),
    offset:      int                = Query(0,   ge=0),
    db:          AsyncSession       = Depends(get_db),
):
    """
    Query detections with optional filters.
    Example: GET /api/detections?confidence=high&date_from=2024-01-01&limit=50
    """
    filters = DetectionFilters(
        mission_id=mission_id, confidence=confidence, source=source,
        date_from=date_from, date_to=date_to,
        lat_min=lat_min, lat_max=lat_max,
        lng_min=lng_min, lng_max=lng_max,
        limit=limit, offset=offset,
    )
    return await detection_repo.list_detections(db, filters)


@router.get("/{detection_id}", response_model=DetectionResponse)
async def get_detection(
    detection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    detection = await detection_repo.get_detection(db, detection_id)
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detection


@router.delete("/{detection_id}", status_code=204)
async def delete_detection(
    detection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    deleted = await detection_repo.delete_detection(db, detection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Detection not found")