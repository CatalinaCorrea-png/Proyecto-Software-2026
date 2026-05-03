from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from modules.drone.simulator import simulate_telemetry
from modules.detection.yolo_detector import YoloDetector
from modules.detection.thermal_detector import ThermalDetector
from modules.detection.thermal_simulator import ThermalSimulator   # ← Simulacion de camara térmica
from modules.detection.fusion import fuse_detections
from core.state import drone_state, search_grid
# from core.config import CAMERA_SOURCE, CAMERA_INDEX
from modules.drone.camera import open_camera
import json, cv2, numpy as np, base64, asyncio, time, uuid
from datetime import datetime, timezone
from db.database import SessionLocal, init_db
from db.models import Mission as MissionModel, Detection as DetectionModel, GridCell as GridCellModel

app = FastAPI(title="AeroSearch AI")
init_db()

# Cerrar misiones que quedaron abiertas por un reinicio abrupto del backend
def _close_orphan_missions():
    db = SessionLocal()
    try:
        orphans = db.query(MissionModel).filter(MissionModel.status == "active").all()
        for m in orphans:
            m.status = "aborted"
            m.ended_at = datetime.now(timezone.utc)
            m.detections_count = len(m.detections)
        if orphans:
            db.commit()
            print(f"⚠️  {len(orphans)} misión(es) huérfana(s) marcadas como 'aborted'")
    finally:
        db.close()

_close_orphan_missions()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

# Detector de objetos RGB (YOLOv8n), detector térmico (+ simulacion)
yolo = YoloDetector(model_size="yolov8n")
thermal = ThermalDetector()
thermal_sim = ThermalSimulator()          # ← Simulacion de camara térmica
# Variables para cooldown de detecciones
last_detection_time = 0.0
DETECTION_COOLDOWN = 3.0
# Lista de clientes WebSocket conectados a la grilla para enviar actualizaciones en tiempo real
grid_clients: list[WebSocket] = []

# Variable global para trackear si ya hay una simulación corriendo
_simulation_running = False
active_mission_id: int | None = None

@app.get("/")
def health():
    return {"status": "AeroSearch AI online"}

# Este es el dron. Envía Telemetría GPS, batería, estado.
@app.websocket("/ws/mission")
async def mission_websocket(websocket: WebSocket):
    global _simulation_running, active_mission_id
    await websocket.accept()
    print("🔌 Misión conectada")

    # Si ya hay una simulación corriendo, no arrancar otra
    if _simulation_running:
        print("⚠️  Simulación ya en curso, usando estado existente")
        try:
            while True:
                # Solo mandar el estado actual sin re-simular
                await websocket.send_text(json.dumps({
                    "type": "telemetry",
                    "data": {
                        "position": {
                            "lat": drone_state.lat,
                            "lng": drone_state.lng,
                            "altitude": drone_state.altitude,
                            "timestamp": int(time.time() * 1000)
                        },
                        "battery": round(drone_state.battery, 1),
                        "status": drone_state.status,
                        "speed": 5.0
                    }
                }))
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            print("❌ Cliente secundario desconectado")
        return

    _simulation_running = True
    db = SessionLocal()
    try:
        mission = MissionModel(
            started_at=datetime.now(timezone.utc),
            initial_battery=drone_state.battery,
            grid_rows=search_grid.rows,
            grid_cols=search_grid.cols,
            grid_center_lat=search_grid.center_lat,
            grid_center_lng=search_grid.center_lng,
        )
        db.add(mission)
        db.commit()
        db.refresh(mission)
        active_mission_id = mission.id
    except Exception as e:
        print(f"DB error creating mission: {e}")
        db.rollback()
    finally:
        db.close()

    try:
        async for message in simulate_telemetry():
            changed_cells = search_grid.update_position(drone_state.lat, drone_state.lng)
            if changed_cells and grid_clients:
                grid_update = {
                    "type": "grid_update",
                    "cells": changed_cells,
                    "coverage": search_grid.coverage_percent()
                }
                for client in grid_clients.copy():
                    try:
                        await client.send_text(json.dumps(grid_update))
                    except Exception:
                        grid_clients.remove(client)
            await websocket.send_text(json.dumps(message))
    except WebSocketDisconnect:
        print("❌ Misión desconectada")
    finally:
        if active_mission_id:
            db = SessionLocal()
            try:
                m = db.query(MissionModel).filter(MissionModel.id == active_mission_id).first()
                if m:
                    m.ended_at = datetime.now(timezone.utc)
                    m.status = "completed"
                    m.final_battery = round(drone_state.battery, 1)
                    m.coverage_percent = search_grid.coverage_percent()
                    m.detections_count = db.query(DetectionModel).filter(
                        DetectionModel.mission_id == active_mission_id
                    ).count()
                    for cell in search_grid.cells.values():
                        if cell["status"] != "unexplored":
                            db.add(GridCellModel(
                                mission_id=active_mission_id,
                                row=cell["row"],
                                col=cell["col"],
                                cell_lat=cell["lat"],
                                cell_lng=cell["lng"],
                                status=cell["status"],
                                explored_at=datetime.fromtimestamp(
                                    cell["explored_at"] / 1000, tz=timezone.utc
                                ) if cell["explored_at"] else None,
                            ))
                    db.commit()
            except Exception as e:
                print(f"DB error closing mission: {e}")
                db.rollback()
            finally:
                db.close()
        active_mission_id = None
        _simulation_running = False

# Envia Estado de la grilla
# Event-driven. No tiene loop propio. Escucha y recibe broadcasts del canal de misión y detección
@app.websocket("/ws/grid")
async def grid_websocket(websocket: WebSocket):
    await websocket.accept()
    # Se crea/agrega el cliente de la grilla
    grid_clients.append(websocket)
    await websocket.send_text(json.dumps({
        "type": "grid_init",
        "cells": search_grid.get_all_cells(), # Devuelve lista de cells.values() (cada celda dict)
        "coverage": search_grid.coverage_percent()
    }))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        grid_clients.remove(websocket)

# Envía  Video frames + detecciones IA
@app.websocket("/ws/detection")
async def detection_websocket(websocket: WebSocket):
    await websocket.accept()
    global last_detection_time

    # Esperar a que mission_websocket cree el registro en DB antes de procesar
    for _ in range(20):
        if active_mission_id is not None:
            break
        await asyncio.sleep(0.25)

    cap = open_camera()

    # Leer dimensiones reales del frame
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if cap else 640
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if cap else 480

    # Actualizar simulador con dimensiones reales
    thermal_sim.frame_w = frame_w
    thermal_sim.frame_h = frame_h

    try:
        while True:
            # 1. Frame
            if cap is not None:
                ret, frame = cap.read()
                if not ret:
                    break
            else:
                frame = np.random.randint(80, 120, (frame_h, frame_w, 3), dtype=np.uint8)

            # 2. Detección RGB
            rgb_detections = yolo.detect(frame)

            # 3. Térmica simulada (para demo sin cámara térmica)
            temp_matrix = thermal_sim.generate(frame) # genera matriz térmica 32x24 usando MediaPipe Pose
            thermal_detections = thermal.detect(temp_matrix)

            # 4. Fusión
            fused = fuse_detections(rgb_detections, thermal_detections,
                                    frame_w=frame_w, frame_h=frame_h)

            # 5. GPS
            geo_detections = []
            for det in fused:
                geo_det = {
                    **det,
                    "id": str(uuid.uuid4()),
                    "position": {
                        "lat": drone_state.lat,
                        "lng": drone_state.lng,
                        "altitude": drone_state.altitude,
                        "timestamp": int(time.time() * 1000)
                    }
                }
                geo_detections.append(geo_det)

                now = time.time()
                if det["confidence"] in ("high", "medium") and \
                   (now - last_detection_time) >= DETECTION_COOLDOWN:
                    last_detection_time = now

                    # Celda naranja en la grilla
                    detection_cell = search_grid.mark_detection(drone_state.lat, drone_state.lng)
                    if detection_cell and grid_clients:
                        # Broadcast a grid_clients para actualizar la celda y el porcentaje de cobertura
                        await asyncio.gather(*[
                            client.send_text(json.dumps({
                                "type": "grid_update",
                                "cells": [detection_cell],
                                "coverage": search_grid.coverage_percent()
                            }))
                            for client in grid_clients.copy()
                        ])
                    # Punto verde en el mapa + alerta en el panel
                    await websocket.send_text(json.dumps({
                        "type": "detection",
                        "data": {
                            "id": geo_det["id"],
                            "position": geo_det["position"],
                            "confidence": det["confidence"],
                            "source": det["source"],
                            "temperature": det.get("temperature"),
                            "timestamp": int(time.time() * 1000)
                        }
                    }))

                    if active_mission_id:
                        db = SessionLocal()
                        try:
                            db.add(DetectionModel(
                                id=geo_det["id"],
                                mission_id=active_mission_id,
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

            # 6. ── Tres vistas del frame ──────────────────────────
            # Vista 1: RGB con bounding boxes
            annotated = yolo.draw(frame.copy(), rgb_detections)
            _, buf = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 60])
            frame_b64 = base64.b64encode(buf).decode()

            # Vista 2: overlay térmico sobre el frame
            thermal_overlay = thermal_sim.overlay_on_frame(frame, temp_matrix, alpha=0.65)  # era 0.45
            _, buf2 = cv2.imencode('.jpg', thermal_overlay, [cv2.IMWRITE_JPEG_QUALITY, 60])
            overlay_b64 = base64.b64encode(buf2).decode()

            # Vista 3: térmica pura 32x24 escalada (miniatura)
            thermal_pure = thermal_sim.to_visual_frame(temp_matrix, 128, 96)
            _, buf3 = cv2.imencode('.jpg', thermal_pure)
            thermal_b64 = base64.b64encode(buf3).decode()

            await websocket.send_text(json.dumps({
                "type": "frame",
                "frame": frame_b64,
                "thermal_overlay": overlay_b64,   
                "thermal_frame": thermal_b64,
                "fused_detections": geo_detections,
                "detection_count": len(fused)
            }))

            await asyncio.sleep(1/15)

    except WebSocketDisconnect:
        pass
    finally:
        if cap:
            cap.release()


@app.get("/missions")
def list_missions():
    db = SessionLocal()
    try:
        missions = db.query(MissionModel).order_by(MissionModel.created_at.desc()).all()
        return [
            {
                "id": m.id,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "started_at": m.started_at.isoformat() if m.started_at else None,
                "ended_at": m.ended_at.isoformat() if m.ended_at else None,
                "status": m.status,
                "initial_battery": m.initial_battery,
                "final_battery": m.final_battery,
                "coverage_percent": m.coverage_percent,
                "detections_count": len(m.detections),
                "grid_rows": m.grid_rows,
                "grid_cols": m.grid_cols,
                "grid_center_lat": m.grid_center_lat,
                "grid_center_lng": m.grid_center_lng,
            }
            for m in missions
        ]
    finally:
        db.close()


@app.get("/missions/{mission_id}")
def get_mission(mission_id: int):
    db = SessionLocal()
    try:
        m = db.query(MissionModel).filter(MissionModel.id == mission_id).first()
        if not m:
            raise HTTPException(status_code=404, detail="Mission not found")
        return {
            "id": m.id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "started_at": m.started_at.isoformat() if m.started_at else None,
            "ended_at": m.ended_at.isoformat() if m.ended_at else None,
            "status": m.status,
            "initial_battery": m.initial_battery,
            "final_battery": m.final_battery,
            "coverage_percent": m.coverage_percent,
            "detections_count": m.detections_count,
            "grid_rows": m.grid_rows,
            "grid_cols": m.grid_cols,
            "grid_center_lat": m.grid_center_lat,
            "grid_center_lng": m.grid_center_lng,
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