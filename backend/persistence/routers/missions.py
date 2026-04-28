from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from persistence.models import Mission
from persistence.schemas import MissionCreate, MissionResponse

router = APIRouter(prefix="/api/missions", tags=["missions"])


@router.post("/", response_model=MissionResponse, status_code=201)
async def create_mission(body: MissionCreate, db: AsyncSession = Depends(get_db)):
    mission = Mission(**body.model_dump())
    db.add(mission)
    await db.flush()
    await db.refresh(mission)
    return mission


@router.get("/", response_model=list[MissionResponse])
async def list_missions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Mission).order_by(Mission.started_at.desc()))
    return list(result.scalars().all())


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.patch("/{mission_id}/complete", response_model=MissionResponse)
async def complete_mission(mission_id: UUID, db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timezone
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    mission.status   = "completed"
    mission.ended_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(mission)
    return mission