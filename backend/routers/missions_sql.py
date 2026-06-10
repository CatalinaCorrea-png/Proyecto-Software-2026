import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import core.mission_state as ms
from core.state import drone_state, reset_mission
from db.database import SessionLocal
from db.mission_ops import close_mission_db
from db.models import Detection as DetectionModel, Mission as MissionModel
from modules.storage.image_service import delete_images_by_mission

router = APIRouter(tags=["missions-sql"])


class MissionSetupRequest(BaseModel):
    name: str = "Misión sin nombre"
    lat: float
    lng: float
    altitude: float = 25.0
    grid_rows: int = 20
    grid_cols: int = 20
    cell_size_m: float = 20.0


class ResolveRequest(BaseModel):
    action: str  # "confirm" | "dismiss"


class RevisitDismissRequest(BaseModel):
    id: str


def _set_detection_status(det_ids: list[str], status: str) -> None:
    """Marca el status de una o más detecciones en SQLite."""
    if not det_ids:
        return
    db = SessionLocal()
    try:
        db.query(DetectionModel).filter(DetectionModel.id.in_(det_ids)).update(
            {DetectionModel.status: status}, synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


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


@router.get("/mission/detections")
def mission_detections():
    """Todas las detecciones de la misión activa (para mostrar el histórico
    completo en el mapa al terminar, no solo las últimas)."""
    if ms.active_mission_id is None:
        return []
    db = SessionLocal()
    try:
        dets = (
            db.query(DetectionModel)
            .filter(DetectionModel.mission_id == ms.active_mission_id)
            .all()
        )
        return [
            {
                "id": d.id,
                "position": {
                    "lat": d.position_lat,
                    "lng": d.position_lng,
                    "altitude": d.position_altitude,
                    "timestamp": int(d.timestamp.timestamp() * 1000),
                },
                "confidence": d.confidence,
                "source": d.source,
                "temperature": d.temperature,
                "status": d.status,
                "timestamp": int(d.timestamp.timestamp() * 1000),
            }
            for d in dets
        ]
    finally:
        db.close()


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


@router.post("/mission/pause")
def mission_pause():
    """Pausa supervisada del barrido autónomo (el dron queda en hover)."""
    drone_state.sweep_paused = True
    return {"paused": True}


@router.post("/mission/resume")
def mission_resume():
    """Reanuda el barrido autónomo tras una pausa supervisada."""
    drone_state.sweep_paused = False
    return {"paused": False}


@router.post("/mission/detection/resolve")
def mission_detection_resolve(req: ResolveRequest):
    """Resuelve la detección que frenó al dron (alta confianza durante el
    barrido, o un punto durante la revisita): 'confirm' la marca como real,
    'dismiss' la descarta. Luego el dron continúa según el contexto."""
    pending = drone_state.pending_detection
    if pending is None:
        raise HTTPException(status_code=400, detail="No hay detección pendiente")
    if req.action not in ("confirm", "dismiss"):
        raise HTTPException(status_code=400, detail="action debe ser 'confirm' o 'dismiss'")

    new_status = "confirmed" if req.action == "confirm" else "dismissed"
    _set_detection_status([pending["id"]], new_status)

    was_revisit = drone_state.sweep_state == "revisit_confirm"
    drone_state.pending_detection = None
    if was_revisit:
        # Llegada a un punto encolado: seguir con el próximo de la cola.
        drone_state.revisit_target = None
        drone_state.sweep_state = "revisiting"
    else:
        # Hallazgo de alta confianza: retomar la fase que se interrumpió
        # (barrido, revisita en tránsito o regreso a base).
        drone_state.sweep_state = drone_state.resume_state or "sweeping"
    return {
        "resolved": new_status,
        "id": pending["id"],
        "context": "revisit" if was_revisit else "sweep",
    }


@router.post("/mission/revisit/start")
def mission_revisit_start():
    """Dispara la fase de revisita a pedido del operador (sin esperar a que
    termine el barrido). El dron vuela a los puntos encolados uno por uno."""
    if drone_state.pending_detection is not None:
        raise HTTPException(status_code=409, detail="Resolvé la detección pendiente primero")
    if not drone_state.revisit_queue:
        raise HTTPException(status_code=400, detail="La cola de revisita está vacía")
    drone_state.sweep_state = "revisiting"
    return {"sweep_state": "revisiting", "queued": len(drone_state.revisit_queue)}


@router.post("/mission/revisit/dismiss")
def mission_revisit_dismiss(req: RevisitDismissRequest):
    """Descarta una detección de la cola de revisita (falso positivo):
    la saca de la cola y la marca 'dismissed' en la DB."""
    before = len(drone_state.revisit_queue)
    drone_state.revisit_queue = [d for d in drone_state.revisit_queue if d.get("id") != req.id]
    if len(drone_state.revisit_queue) == before:
        raise HTTPException(status_code=404, detail="Detección no está en la cola")
    _set_detection_status([req.id], "dismissed")
    return {"dismissed": req.id, "remaining": len(drone_state.revisit_queue)}


@router.post("/mission/revisit/clear")
def mission_revisit_clear():
    """Vacía la cola de revisita marcando todo como 'dismissed'."""
    ids = [d["id"] for d in drone_state.revisit_queue if d.get("id")]
    _set_detection_status(ids, "dismissed")
    drone_state.revisit_queue = []
    return {"cleared": len(ids)}


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
async def delete_mission(mission_id: int):
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
    await delete_images_by_mission(str(mission_id))


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
