from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from modules.drone.simulator import simulate_telemetry
from modules.detection.yolo_detector import YoloDetector
from modules.detection.thermal_detector import ThermalDetector
from modules.detection.thermal_simulator import ThermalSimulator
from modules.detection.fusion import fuse_detections
from core.state import drone_state, search_grid
from core.config import DRONE_IP, DRONE_UDP_PORT, DRONE_UDP_TX_PORT
from core.config import CAMERA_SOURCE, CAMERA_INDEX
from modules.drone.camera import open_camera # se usa el FrameGrabber ahora
from modules.drone.udp_telemetry import start_udp_listener, hw_watchdog
from contextlib import asynccontextmanager
from db.mongodb import connect as mongo_connect, disconnect as mongo_disconnect
from routers.images import router as images_router
from routers.missions_mongo import router as missions_mongo_router
# Auto-guardado en MongoDB de frames con detección
from modules.storage.image_service import save_image
from modules.storage.schemas import (ImageUploadRequest, DetectionPayload, BoundingBox,)
from datetime import datetime as _dt
import json, cv2, numpy as np, base64, asyncio, time, uuid, socket, threading, requests
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

@asynccontextmanager
async def lifespan(app):
    await mongo_connect()
    await start_udp_listener(DRONE_UDP_TX_PORT)
    asyncio.create_task(hw_watchdog())
    asyncio.create_task(_keepalive_loop())
    yield
    if _grabber is not None:
        _grabber.stop()
    await mongo_disconnect()

app = FastAPI(title="AeroSearch AI", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.on_event("shutdown")
# def shutdown_event():
#     if _grabber is not None:
#         _grabber.stop()
app.include_router(images_router)
app.include_router(missions_mongo_router)

yolo = YoloDetector()
thermal = ThermalDetector()
thermal_sim = ThermalSimulator()          # ← Simulacion de camara térmica
# Variables para cooldown de detecciones
last_detection_time = 0.0
DETECTION_COOLDOWN = 3.0
# Lista de clientes WebSocket conectados a la grilla para enviar actualizaciones en tiempo real
grid_clients: list[WebSocket] = []

# Variable global para trackear si ya hay una simulación corriendo
_simulation_running = False

class DroneCommand(BaseModel):
    throttle: int = 0   # 0-255 (PWM directo al motor)
    yaw: int = 0        # -100 a 100
    pitch: int = 0      # -100 a 100
    roll: int = 0       # -100 a 100

_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_last_cmd_time: float = 0.0


# @app.on_event("startup")
# async def startup():
#     await start_udp_listener(DRONE_UDP_TX_PORT)
#     asyncio.create_task(hw_watchdog())
#     asyncio.create_task(_keepalive_loop())


async def _keepalive_loop():
    """Envía T:0,Y:0,P:0,R:0 al ESP32 cada 2s si no hubo comandos recientes.
    Esto establece nuestra IP como destino para la telemetría periódica."""
    while True:
        await asyncio.sleep(2.0)
        if time.time() - _last_cmd_time > 3.0:
            try:
                _udp_sock.sendto(b"T:0,Y:0,P:0,R:0", (DRONE_IP, DRONE_UDP_PORT))
            except Exception:
                pass


class FrameGrabber:
    """Lee frames en un hilo dedicado. Usa requests para MJPEG (ESP32) y cv2 para cámaras locales."""
    def __init__(self):
        self._cap: cv2.VideoCapture | None = None
        self._stream_url: str | None = None
        self._frame: np.ndarray | None = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self.frame_w = 640
        self.frame_h = 480

    def start(self) -> bool:
        source, use_dshow = CAMERA_INDEX.get(CAMERA_SOURCE, (None, False))

        if source is None:
            print("📷 Modo sintético")
            return False

        # URL = stream MJPEG (ESP32-CAM), parsear con requests
        if isinstance(source, str):
            self._stream_url = source
            self._running = True
            self._thread = threading.Thread(target=self._mjpeg_reader_loop, daemon=True)
            self._thread.start()
            # No esperar — el hilo sigue intentando en background
            print(f"✅ Cámara: {CAMERA_SOURCE} (url: {source}) — conectando...")
            return True

        # Cámara local con cv2
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW if use_dshow else cv2.CAP_ANY)
        if not cap.isOpened():
            print(f"⚠️ No se pudo abrir {CAMERA_SOURCE}, usando sintético")
            return False
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0:
            cap.release()
            print(f"⚠️ No se pudo leer de {CAMERA_SOURCE}, usando sintético")
            return False
        self._cap = cap
        self._frame = frame
        self.frame_w = frame.shape[1]
        self.frame_h = frame.shape[0]
        self._running = True
        self._thread = threading.Thread(target=self._cv2_reader_loop, daemon=True)
        self._thread.start()
        print(f"✅ Cámara: {CAMERA_SOURCE} (índice: {source})")
        return True

    def _mjpeg_reader_loop(self):
        """Parsea el stream MJPEG del ESP32-CAM frame a frame."""
        while self._running:
            try:
                resp = requests.get(self._stream_url, stream=True, timeout=10)
                buf = b''
                for chunk in resp.iter_content(chunk_size=1024):
                    if not self._running:
                        break
                    buf += chunk
                    # Buscar JPEG completo: FF D8 (inicio) hasta FF D9 (fin)
                    while True:
                        start = buf.find(b'\xff\xd8')
                        if start == -1:
                            buf = b''  # descartar basura sin inicio JPEG
                            break
                        end = buf.find(b'\xff\xd9', start)
                        if end == -1:
                            # Todavía no llegó el fin, recortar basura anterior
                            buf = buf[start:]
                            break
                        jpg = buf[start:end + 2]
                        buf = buf[end + 2:]
                        frame = cv2.imdecode(
                            np.frombuffer(jpg, dtype=np.uint8),
                            cv2.IMREAD_COLOR
                        )
                        if frame is not None:
                            with self._lock:
                                self._frame = frame
                resp.close()
            except Exception as e:
                print(f"⚠️ MJPEG stream error: {e}, reconectando...")
                time.sleep(2)

    def _cv2_reader_loop(self):
        while self._running and self._cap is not None:
            ret, frame = self._cap.read()
            if ret and frame is not None:
                with self._lock:
                    self._frame = frame

    def grab(self) -> np.ndarray | None:
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
            self._cap = None
            self._cap = None

@app.get("/")
def health():
    return {"status": "AeroSearch AI online"}

@app.post("/drone/control")
def drone_control(cmd: DroneCommand):
    global _last_cmd_time
    _last_cmd_time = time.time()
    drone_state.cmd_throttle = cmd.throttle
    drone_state.cmd_pitch = cmd.pitch
    drone_state.cmd_roll = cmd.roll
    payload = f"T:{cmd.throttle},Y:{cmd.yaw},P:{cmd.pitch},R:{cmd.roll}"
    _udp_sock.sendto(payload.encode(), (DRONE_IP, DRONE_UDP_PORT))
    _last_cmd_time = time.time()
    return {"sent": payload, "target": f"{DRONE_IP}:{DRONE_UDP_PORT}"}

@app.get("/drone/state")
def get_drone_state():
    return {
        "altitude": drone_state.altitude,
        "model": yolo.weights_name,
    }

@app.post("/drone/{altitude}")
def set_altitude(altitude: float):
    drone_state.altitude = max(0.0, altitude)
    return {
        "altitude": drone_state.altitude,
        "model": yolo.weights_name,
    }

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

# Singleton: una sola conexión al ESP32 compartida por todos los clientes
_grabber: FrameGrabber | None = None

def get_grabber() -> FrameGrabber:
    global _grabber
    if _grabber is None:
        _grabber = FrameGrabber()
        _grabber.start()
    return _grabber

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
         
 #   cap = open_camera()

    # Leer dimensiones reales del frame
  #  frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if cap else 640
  #  frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if cap else 480

    grabber = get_grabber()
    has_camera = grabber._running

    frame_w = grabber.frame_w
    frame_h = grabber.frame_h
    last_frame = None
    detected_positions: set[tuple[float, float]] = set()

    # Actualizar simulador con dimensiones reales
    # thermal_sim.frame_w = frame_w
    # thermal_sim.frame_h = frame_h

    try:
        while True:
            # 1. Frame — nunca bloquea, toma el último disponible
            if has_camera:
                frame = grabber.grab()
                if frame is None:
                    await asyncio.sleep(0.05)
                    continue
                last_frame = frame
            else:
                frame = last_frame if last_frame is not None else \
                    np.random.randint(80, 120, (frame_h, frame_w, 3), dtype=np.uint8)


            # 2-4. Detección + fusión en thread
            # def process(f):
            #     rgb_dets = yolo.detect(f)
            #     t_matrix = thermal_sim.generate(f)
            #     t_dets = thermal.detect(t_matrix)
            #     fused = fuse_detections(rgb_dets, t_dets, frame_w=frame_w, frame_h=frame_h)
            #     return rgb_dets, t_matrix, fused
            
            # def encode(f):
            #     _, buf = cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 70])
            #     return base64.b64encode(buf).decode()
            
            # 2. Detección RGB
            rgb_detections = yolo.detect(frame)
            # rgb_detections, temp_matrix, fused = await asyncio.to_thread(process, frame)
            # frame_b64 = await asyncio.to_thread(encode, frame)

            # 5. GPS
            geo_detections = []
            for det in rgb_detections:
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

                conf = det["confidence"]
                conf_label = "high" if conf > 0.7 else "medium" if conf > 0.4 else "low"
                pos_key = (round(drone_state.lat, 5), round(drone_state.lng, 5))
                now = time.time()
                if conf_label in ("high", "medium") and \
                   (now - last_detection_time) >= DETECTION_COOLDOWN and \
                   pos_key not in detected_positions:
                    last_detection_time = now
                    detected_positions.add(pos_key)

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
                    await websocket.send_text(json.dumps({
                        "type": "detection",
                        "data": {
                            "id": geo_det["id"],
                            "position": geo_det["position"],
                            "confidence": conf_label,
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

                    # Guardar frame con detección en MongoDB (no bloquea el WS)
                    async def _persist(
                        _frame=frame,
                        _conf_label=conf_label,
                        _det=det,
                        _lat=drone_state.lat,
                        _lng=drone_state.lng,
                        _alt=drone_state.altitude,
                    ):
                        _, buf = cv2.imencode('.jpg', _frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                        det_payload = DetectionPayload(
                            confidence=_conf_label,
                            confidence_score=float(_det.get("confidence", 0.5)),
                            source=_det.get("source", "rgb"),
                            temperature_celsius=_det.get("temperature"),
                            bounding_box=BoundingBox(
                                x_norm=_det.get("x", 0.0), y_norm=_det.get("y", 0.0),
                                w_norm=_det.get("w", 0.0), h_norm=_det.get("h", 0.0),
                            ),
                        )
                        await save_image(
                            buf.tobytes(),
                            ImageUploadRequest(
                                mission_id=str(active_mission_id),
                                lat=_lat,
                                lng=_lng,
                                altitude_m=_alt,
                                timestamp=_dt.utcnow(),
                                view_mode="rgb",
                                camera_source=CAMERA_SOURCE,
                                detections=[det_payload],
                            ),
                        )
                    asyncio.create_task(_persist())
            # 6. Encode frames en thread
            # def encode_frames(f, rgb_dets, t_matrix):
            def encode_frame(f, rgb_dets):
                annotated = yolo.draw(f.copy(), rgb_dets)
                _, buf = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 60])
                return base64.b64encode(buf).decode()

            #     thermal_overlay = thermal_sim.overlay_on_frame(f, t_matrix, alpha=0.65)
            #     _, buf2 = cv2.imencode('.jpg', thermal_overlay, [cv2.IMWRITE_JPEG_QUALITY, 60])
            #     o_b64 = base64.b64encode(buf2).decode()

            #     thermal_pure = thermal_sim.to_visual_frame(t_matrix, 128, 96)
            #     _, buf3 = cv2.imencode('.jpg', thermal_pure)
            #     t_b64 = base64.b64encode(buf3).decode()
            #     return f_b64, o_b64, t_b64

            # frame_b64, overlay_b64, thermal_b64 = await asyncio.to_thread(
            #     encode_frames, frame, rgb_detections, temp_matrix
            # )
            frame_b64 = await asyncio.to_thread(
                encode_frame, frame, rgb_detections
            )

            await websocket.send_text(json.dumps({
                "type": "frame",
                "frame": frame_b64,
                # "thermal_overlay": overlay_b64,
                # "thermal_frame": thermal_b64,
                # "fused_detections": geo_detections,
                # "detection_count": len(fused)
                "thermal_overlay": None,
                "thermal_frame": None,
                "fused_detections": geo_detections,
                "detection_count": len(geo_detections)
            }))

            await asyncio.sleep(1/15)

    except WebSocketDisconnect:
        pass


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