from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from modules.drone.simulator import simulate_telemetry
from modules.detection.yolo_detector import YoloDetector
from modules.detection.thermal_detector import ThermalDetector
from modules.detection.thermal_simulator import ThermalSimulator   # ← Simulacion de camara térmica
from modules.detection.fusion import fuse_detections
from core.state import drone_state, search_grid
from core.database import create_tables, AsyncSessionLocal
# from core.config import CAMERA_SOURCE, CAMERA_INDEX
from modules.drone.camera import open_camera

# - routers REST de persistencia
from persistence.routers import detections, missions, images
from persistence.services.detection_service import save_detection_with_frames 
from persistence.schemas import DetectionCreate                                

import json, cv2, numpy as np, base64, asyncio, time, uuid, os

app = FastAPI(title="AeroSearch AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

# - registrar routers REST
app.include_router(detections.router)
app.include_router(missions.router)
app.include_router(images.router)

# - servir imágenes locales como archivos estáticos (dev)
os.makedirs("media/detections", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

# - crear tablas al arrancar (dev). En prod usar Alembic.
@app.on_event("startup")
async def startup():
    await create_tables()   # no-op si las tablas ya existen

yolo = YoloDetector(model_size="yolov8n")
thermal = ThermalDetector()
thermal_sim = ThermalSimulator()          # ← Simulacion de camara térmica
last_detection_time = 0.0
DETECTION_COOLDOWN = 3.0
grid_clients: list[WebSocket] = []

# Variable global para trackear si ya hay una simulación corriendo
_simulation_running = False

# — ID de la misión activa. Setearlo antes de volar via POST /api/missions.
# None = las detecciones se guardan sin misión asociada.
active_mission_id = None


@app.get("/")
def health():
    return {"status": "AeroSearch AI online"}


# Este es el dron. Envía Telemetría GPS, batería, estado.
@app.websocket("/ws/mission")
async def mission_websocket(websocket: WebSocket):
    global _simulation_running
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
        _simulation_running = False  # liberar cuando termina


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

            # 5. ── Tres vistas del frame ──────────────────────────
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

            # 6. GPS
            geo_detections = []
            for det in fused:
                det_id = str(uuid.uuid4())
                position = {
                    "lat": drone_state.lat,
                    "lng": drone_state.lng,
                    "altitude": drone_state.altitude,
                    "timestamp": int(time.time() * 1000)
                }
                geo_det = {**det, "id": det_id, "position": position}
                geo_detections.append(geo_det)

                now = time.time()
                if det["confidence"] in ("high", "medium") and \
                   (now - last_detection_time) >= DETECTION_COOLDOWN:
                    last_detection_time = now

                    # — Persistir en PostgreSQL (fire-and-forget, no bloquea el stream)
                    asyncio.create_task(
                        _persist_detection(det, position, frame_b64, overlay_b64, thermal_b64)
                    )

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
                            "id": det_id,
                            "position": position,
                            "confidence": det["confidence"],
                            "source": det["source"],
                            "temperature": det.get("temperature"),
                            "timestamp": int(time.time() * 1000)
                        }
                    }))

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


async def _persist_detection(det: dict, position: dict,
                              frame_b64: str, overlay_b64: str, thermal_b64: str):
    """
    Coroutine fire-and-forget — corre fuera del loop del WebSocket.
    Cualquier error de DB se loguea pero nunca crashea el stream.
    """
    try:
        payload = DetectionCreate(
            mission_id           = active_mission_id,
            latitude             = position["lat"],
            longitude            = position["lng"],
            altitude             = position.get("altitude"),
            confidence           = det["confidence"],
            source               = det["source"],
            temperature          = det.get("temperature"),
            raw_confidence_score = det.get("raw_confidence_score"),
        )
        async with AsyncSessionLocal() as db:
            await save_detection_with_frames(
                db           = db,
                payload      = payload,
                frame_b64    = frame_b64,
                thermal_b64  = overlay_b64,
                thermal_raw_b64 = thermal_b64,
            )
            await db.commit()
            print(f"💾 Detection saved [{det['confidence']}] {position['lat']:.5f},{position['lng']:.5f}")
    except Exception as e:
        print(f"⚠️  Persistence error (non-fatal): {e}")