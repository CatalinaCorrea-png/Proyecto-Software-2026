from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from modules.drone.simulator import simulate_telemetry
from modules.detection.yolo_detector import YoloDetector
from modules.detection.thermal_detector import ThermalDetector
from modules.detection.thermal_simulator import ThermalSimulator   # ← nuevo
from modules.detection.fusion import fuse_detections
from core.state import drone_state, search_grid
import json, cv2, numpy as np, base64, asyncio, time, uuid

app = FastAPI(title="AeroSearch AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

yolo = YoloDetector(model_size="yolov8n")
thermal = ThermalDetector()
thermal_sim = ThermalSimulator()          # ← nuevo
last_detection_time = 0.0
DETECTION_COOLDOWN = 3.0
grid_clients: list[WebSocket] = []

@app.get("/")
def health():
    return {"status": "AeroSearch AI online"}

@app.websocket("/ws/mission")
async def mission_websocket(websocket: WebSocket):
    await websocket.accept()
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
        pass

@app.websocket("/ws/grid")
async def grid_websocket(websocket: WebSocket):
    await websocket.accept()
    grid_clients.append(websocket)
    await websocket.send_text(json.dumps({
        "type": "grid_init",
        "cells": search_grid.get_all_cells(),
        "coverage": search_grid.coverage_percent()
    }))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        grid_clients.remove(websocket)

@app.websocket("/ws/detection")
async def detection_websocket(websocket: WebSocket):
    await websocket.accept()
    global last_detection_time
         
    cap = cv2.VideoCapture(0)

    # # IP que te muestra la app Camo en el iPhone
    # CAMO_STREAM = "rtsp://192.168.1.X:7878/live"
    # cap = cv2.VideoCapture(CAMO_STREAM, cv2.CAP_FFMPEG) #  es importante para streams RTSP — sin eso OpenCV a veces no los abre bien.
    

    # if not cap.isOpened():
    #     print("⚠️  No se pudo conectar al celu, usando webcam local")
    #     cap = cv2.VideoCapture(0)  # fallback a webcam

    # Probar Camo primero, fallback a webcam
    cap = cv2.VideoCapture(1)
    if not cap.isOpened() or not cap.read()[0]:
        cap = cv2.VideoCapture(2)
    if not cap.isOpened() or not cap.read()[0]:
        print("⚠️ Usando webcam local")
        cap = cv2.VideoCapture(0)

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

            # 3. ── NUEVO: térmica simulada basada en detecciones reales ───
            temp_matrix = thermal_sim.generate(rgb_detections)
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
            # 6. ── NUEVO: tres vistas del frame ──────────────────────────
            # Vista 1: RGB con bounding boxes
            annotated = yolo.draw(frame.copy(), rgb_detections)
            _, buf = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 60])
            frame_b64 = base64.b64encode(buf).decode()

            # Vista 2: overlay térmico sobre el frame (lo nuevo)
            thermal_overlay = thermal_sim.overlay_on_frame(frame, temp_matrix, alpha=0.5)
            _, buf2 = cv2.imencode('.jpg', thermal_overlay, [cv2.IMWRITE_JPEG_QUALITY, 60])
            overlay_b64 = base64.b64encode(buf2).decode()

            # Vista 3: térmica pura 32x24 escalada (miniatura)
            thermal_pure = thermal_sim.to_visual_frame(temp_matrix, 128, 96)
            _, buf3 = cv2.imencode('.jpg', thermal_pure)
            thermal_b64 = base64.b64encode(buf3).decode()

            await websocket.send_text(json.dumps({
                "type": "frame",
                "frame": frame_b64,
                "thermal_overlay": overlay_b64,    # ← nuevo
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