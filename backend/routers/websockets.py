import asyncio
import base64
import json
import time
import uuid
from datetime import datetime, datetime as _dt, timezone

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import core.mission_state as ms
import core.state as state
from core.config import CAMERA_SOURCE
from core.detectors import thermal, thermal_sim, yolo
from core.state import drone_state
from db.database import SessionLocal
from db.models import Detection as DetectionModel, Mission as MissionModel
from modules.detection.fusion import fuse_detections
from modules.drone.frame_grabber import get_grabber
from modules.drone.simulation import run_simulation
from modules.drone.simulator import get_current_telemetry
from modules.storage.image_service import save_image
from modules.storage.schemas import BoundingBox, DetectionPayload, ImageUploadRequest

router = APIRouter(tags=["websockets"])

_DETECTION_COOLDOWN = 3.0


@router.websocket("/ws/mission")
async def mission_websocket(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Misión conectada")

    if ms.mission_configured and (ms.simulation_task is None or ms.simulation_task.done()):
        drone_state.mission_start = time.time()
        drone_state.sim_step = 0
        drone_state.battery = 100.0
        drone_state.status = "idle"

        db = SessionLocal()
        try:
            mission = MissionModel(
                name=ms.mission_name or None,
                altitude=ms.mission_altitude,
                cell_size_m=ms.mission_cell_size_m,
                started_at=datetime.now(timezone.utc),
                initial_battery=drone_state.battery,
                grid_rows=state.search_grid.rows,
                grid_cols=state.search_grid.cols,
                grid_center_lat=state.search_grid.center_lat,
                grid_center_lng=state.search_grid.center_lng,
            )
            db.add(mission)
            db.commit()
            db.refresh(mission)
            ms.active_mission_id = mission.id
        except Exception as e:
            print(f"DB error creating mission: {e}")
            db.rollback()
        finally:
            db.close()

        ms.simulation_task = asyncio.create_task(run_simulation())

    try:
        while True:
            await websocket.send_text(json.dumps(get_current_telemetry()))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("❌ Misión desconectada (simulación sigue corriendo)")


@router.websocket("/ws/grid")
async def grid_websocket(websocket: WebSocket):
    await websocket.accept()
    ms.grid_clients.append(websocket)
    await websocket.send_text(json.dumps({
        "type": "grid_init",
        "cells": state.search_grid.get_all_cells(),
        "coverage": state.search_grid.coverage_percent(),
    }))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ms.grid_clients.remove(websocket)


@router.websocket("/ws/detection")
async def detection_websocket(websocket: WebSocket):
    await websocket.accept()

    if ms.detection_history:
        await websocket.send_text(json.dumps({
            "type": "detection_history",
            "data": ms.detection_history,
        }))

    for _ in range(20):
        if ms.active_mission_id is not None:
            break
        await asyncio.sleep(0.25)

    grabber = get_grabber()
    has_camera = grabber._running
    frame_w = grabber.frame_w
    frame_h = grabber.frame_h
    last_frame: np.ndarray | None = None
    detected_positions: set[tuple[float, float]] = set()
    last_detection_time: float = 0.0

    try:
        while True:
            if has_camera:
                frame = grabber.grab()
                if frame is None:
                    await asyncio.sleep(0.05)
                    continue
                last_frame = frame
            else:
                frame = last_frame if last_frame is not None else \
                    np.random.randint(80, 120, (frame_h, frame_w, 3), dtype=np.uint8)

            rgb_detections, (t_matrix, t_dets) = await asyncio.gather(
                asyncio.to_thread(yolo.detect, frame),
                asyncio.to_thread(_run_thermal, frame),
            )

            fused, frame_b64, overlay_b64 = await asyncio.to_thread(
                _fuse_and_encode, frame, rgb_detections, t_matrix, t_dets, frame_w, frame_h
            )

            geo_detections = []
            for det in fused:
                geo_det = {
                    **det,
                    "id": str(uuid.uuid4()),
                    "position": {
                        "lat": drone_state.lat,
                        "lng": drone_state.lng,
                        "altitude": drone_state.altitude,
                        "timestamp": int(time.time() * 1000),
                    },
                }
                geo_detections.append(geo_det)

                conf_label = det["confidence"]
                pos_key = (round(drone_state.lat, 5), round(drone_state.lng, 5))
                now = time.time()
                if (
                    conf_label in ("high", "medium")
                    and (now - last_detection_time) >= _DETECTION_COOLDOWN
                    and pos_key not in detected_positions
                ):
                    last_detection_time = now
                    detected_positions.add(pos_key)
                    await _handle_detection(websocket, det, geo_det, rgb_detections, frame, conf_label)

            await websocket.send_text(json.dumps({
                "type": "frame",
                "frame": frame_b64,
                "thermal_overlay": overlay_b64,
                "fused_detections": geo_detections,
                "detection_count": len(fused),
            }))

            await asyncio.sleep(1 / 15)

    except WebSocketDisconnect:
        pass


def _run_thermal(frame: np.ndarray) -> tuple:
    t_matrix = thermal_sim.generate(frame)
    t_dets = thermal.detect(t_matrix)
    return t_matrix, t_dets


def _fuse_and_encode(
    frame: np.ndarray, rgb_dets, t_mat, t_ds, frame_w: int, frame_h: int
) -> tuple:
    fused = fuse_detections(rgb_dets, t_ds, frame_w=frame_w, frame_h=frame_h)

    annotated = yolo.draw(frame.copy(), rgb_dets)
    _, buf1 = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 60])
    frame_b64 = base64.b64encode(buf1).decode()

    overlay = thermal_sim.overlay_on_frame(frame, t_mat, alpha=0.65)
    _, buf2 = cv2.imencode('.jpg', overlay, [cv2.IMWRITE_JPEG_QUALITY, 60])
    overlay_b64 = base64.b64encode(buf2).decode()

    return fused, frame_b64, overlay_b64


async def _handle_detection(websocket, det, geo_det, rgb_detections, frame, conf_label: str):
    detection_cell = state.search_grid.mark_detection(drone_state.lat, drone_state.lng)
    if detection_cell and ms.grid_clients:
        await asyncio.gather(*[
            client.send_text(json.dumps({
                "type": "grid_update",
                "cells": [detection_cell],
                "coverage": state.search_grid.coverage_percent(),
            }))
            for client in ms.grid_clients.copy()
        ])

    det_msg = {
        "id": geo_det["id"],
        "position": geo_det["position"],
        "confidence": conf_label,
        "source": det["source"],
        "temperature": det.get("temperature"),
        "timestamp": int(time.time() * 1000),
    }
    ms.detection_history.append(det_msg)
    await websocket.send_text(json.dumps({"type": "detection", "data": det_msg}))

    # Triage del movimiento autónomo según confianza:
    #   high   → frenar y esperar confirmación del operador
    #   medium → encolar para revisita (Fase 3), seguir barriendo
    if conf_label == "high":
        # Opción B: un hallazgo nuevo (incluso en tránsito de revisita o RTL)
        # frena al dron, pero recordamos la fase para retomarla al resolver.
        if drone_state.sweep_state in ("sweeping", "revisiting", "returning_home"):
            drone_state.resume_state = drone_state.sweep_state
        drone_state.sweep_state = "awaiting_confirmation"
        drone_state.pending_detection = det_msg
        drone_state.pending_since = time.time()
    elif conf_label == "medium":
        drone_state.revisit_queue.append(det_msg)

    if ms.active_mission_id:
        db = SessionLocal()
        try:
            db.add(DetectionModel(
                id=geo_det["id"],
                mission_id=ms.active_mission_id,
                timestamp=datetime.fromtimestamp(
                    geo_det["position"]["timestamp"] / 1000, tz=timezone.utc
                ),
                position_lat=geo_det["position"]["lat"],
                position_lng=geo_det["position"]["lng"],
                position_altitude=geo_det["position"]["altitude"],
                confidence=det["confidence"],
                source=det["source"],
                temperature=det.get("temperature"),
                rgb_confidence=det.get("rgb_confidence"),
            ))
            db.commit()
        except Exception as e:
            print(f"DB error saving detection: {e}")
            db.rollback()
        finally:
            db.close()

        asyncio.create_task(_persist_image(
            frame, conf_label, det, rgb_detections, ms.active_mission_id
        ))


async def _persist_image(frame, conf_label: str, det, all_dets, mission_id: int):
    lat = drone_state.lat
    lng = drone_state.lng
    alt = drone_state.altitude
    annotated = yolo.draw(frame.copy(), all_dets)
    _, buf = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 60])
    bbox = det.get("bbox") or {}
    det_payload = DetectionPayload(
        confidence=conf_label,
        confidence_score=float(det.get("rgb_confidence") or det.get("iou") or 0.5),
        source=det.get("source", "rgb"),
        temperature_celsius=det.get("temperature"),
        bounding_box=BoundingBox(
            x_norm=bbox.get("x1", 0.0),
            y_norm=bbox.get("y1", 0.0),
            w_norm=bbox.get("x2", 0.0) - bbox.get("x1", 0.0),
            h_norm=bbox.get("y2", 0.0) - bbox.get("y1", 0.0),
        ),
    )
    await save_image(
        buf.tobytes(),
        ImageUploadRequest(
            mission_id=str(mission_id),
            lat=lat,
            lng=lng,
            altitude_m=alt,
            timestamp=_dt.utcnow(),
            view_mode="rgb",
            camera_source=CAMERA_SOURCE,
            detections=[det_payload],
        ),
    )
