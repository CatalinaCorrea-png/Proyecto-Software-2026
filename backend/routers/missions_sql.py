import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import core.mission_state as ms
from core.state import drone_state, reset_mission
from db.database import SessionLocal
from db.mission_ops import close_mission_db
from db.models import Mission as MissionModel

router = APIRouter(tags=["missions-sql"])


class MissionSetupRequest(BaseModel):
    name: str = "Misión sin nombre"
    lat: float
    lng: float
    altitude: float = 25.0
    grid_rows: int = 20
    grid_cols: int = 20
    cell_size_m: float = 20.0


def _mission_to_dict(m: MissionModel) -> dict:
    return {
        "id": m.id,
        "name": m.name,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "started_at": m.started_at.isoformat() if m.started_at else None,
        "ended_at": m.ended_at.isoformat() if m.ended_at else None,
        "status": m.status,
        "initial_battery": m.initial_battery,
        "final_battery": m.final_battery,
        "coverage_percent": m.coverage_percent,
        "detections_count": len(m.detections),
        "altitude": m.altitude,
        "cell_size_m": m.cell_size_m,
        "grid_rows": m.grid_rows,
        "grid_cols": m.grid_cols,
        "grid_center_lat": m.grid_center_lat,
        "grid_center_lng": m.grid_center_lng,
    }


@router.get("/mission/active")
def mission_active():
    return {"active": ms.mission_configured and drone_state.mission_active}


@router.post("/mission/stop")
async def mission_stop():
    if not drone_state.mission_active and (ms.simulation_task is None or ms.simulation_task.done()):
        raise HTTPException(status_code=400, detail="No hay misión activa")
    drone_state.mission_active = False
    if ms.simulation_task and not ms.simulation_task.done():
        try:
            await asyncio.wait_for(ms.simulation_task, timeout=3.0)
        except (asyncio.TimeoutError, Exception):
            ms.simulation_task.cancel()
    close_mission_db()
    ms.mission_configured = False
    drone_state.status = "idle"
    return {"status": "stopped"}


@router.post("/mission/setup")
async def mission_setup(req: MissionSetupRequest):
    ms.mission_name = req.name
    ms.mission_altitude = req.altitude
    ms.mission_cell_size_m = req.cell_size_m
    if ms.simulation_task and not ms.simulation_task.done():
        drone_state.mission_active = False
        try:
            await asyncio.wait_for(ms.simulation_task, timeout=3.0)
        except (asyncio.TimeoutError, Exception):
            ms.simulation_task.cancel()
    close_mission_db()
    ms.mission_configured = True

    grid = reset_mission(
        lat=req.lat, lng=req.lng, altitude=req.altitude,
        rows=req.grid_rows, cols=req.grid_cols,
        cell_size_m=req.cell_size_m,
    )
    ms.detection_history.clear()
    return {
        "status": "ready",
        "name": req.name,
        "lat": req.lat,
        "lng": req.lng,
        "altitude": req.altitude,
        "grid_rows": req.grid_rows,
        "grid_cols": req.grid_cols,
        "cell_size_m": req.cell_size_m,
        "total_cells": grid.rows * grid.cols,
    }


@router.get("/missions")
def list_missions():
    db = SessionLocal()
    try:
        missions = db.query(MissionModel).order_by(MissionModel.created_at.desc()).all()
        return [_mission_to_dict(m) for m in missions]
    finally:
        db.close()


@router.delete("/missions/{mission_id}", status_code=204)
def delete_mission(mission_id: int):
    db = SessionLocal()
    try:
        m = db.query(MissionModel).filter(MissionModel.id == mission_id).first()
        if not m:
            raise HTTPException(status_code=404, detail="Mission not found")
        if m.status == "active":
            raise HTTPException(status_code=409, detail="Cannot delete an active mission")
        db.delete(m)
        db.commit()
    finally:
        db.close()


@router.get("/missions/{mission_id}")
def get_mission(mission_id: int):
    db = SessionLocal()
    try:
        m = db.query(MissionModel).filter(MissionModel.id == mission_id).first()
        if not m:
            raise HTTPException(status_code=404, detail="Mission not found")
        return {
            **_mission_to_dict(m),
            "detections_count": m.detections_count,
            "detections": [
                {
                    "id": d.id,
                    "timestamp": d.timestamp.isoformat(),
                    "position_lat": d.position_lat,
                    "position_lng": d.position_lng,
                    "position_altitude": d.position_altitude,
                    "confidence": d.confidence,
                    "source": d.source,
                    "temperature": d.temperature,
                    "rgb_confidence": d.rgb_confidence,
                }
                for d in m.detections
            ],
        }
    finally:
        db.close()
