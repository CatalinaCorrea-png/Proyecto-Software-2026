from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from modules.drone.simulator import get_current_telemetry
from modules.detection.yolo_detector import YoloDetector
from modules.detection.thermal_detector import ThermalDetector
from modules.detection.thermal_simulator import ThermalSimulator
from modules.detection.fusion import fuse_detections
import core.state as state
from core.state import drone_state, BASE_LAT, BASE_LNG, reset_mission
from modules.mapping.grid import CELL_SIZE_METERS
from core.config import DRONE_IP, DRONE_UDP_PORT, DRONE_UDP_TX_PORT
from core.config import CAMERA_SOURCE, CAMERA_INDEX
from modules.drone.camera import open_camera
from modules.drone.udp_telemetry import start_udp_listener, hw_watchdog
from contextlib import asynccontextmanager
from db.mongodb import connect as mongo_connect, disconnect as mongo_disconnect
from routers.images import router as images_router
from routers.missions_mongo import router as missions_mongo_router
from routers.stats import router as stats_router
from modules.storage.image_service import save_image
from modules.storage.schemas import (ImageUploadRequest, DetectionPayload, BoundingBox,)
from datetime import datetime as _dt
import json, cv2, numpy as np, base64, asyncio, time, uuid, socket, threading, requests, math, glob, os
from datetime import datetime, timezone
from db.database import SessionLocal, init_db
from db.models import Mission as MissionModel, Detection as DetectionModel, GridCell as GridCellModel

init_db()

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
    # Se guarda el transport para cerrarlo en el shutdown.
    # Sin esto, el socket UDP quedaba ocupado al reiniciar y el puerto
    # lanzaba WinError 10048 en el siguiente arranque.
    udp_transport = await start_udp_listener(DRONE_UDP_TX_PORT)
    asyncio.create_task(hw_watchdog())
    asyncio.create_task(_keepalive_loop())
    yield
    udp_transport.close()  # libera el puerto UDP al cerrar
    if _grabber is not None:
        _grabber.stop()
    try:
        await mongo_disconnect()
    except Exception:
        pass

app = FastAPI(title="AeroSearch AI", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images_router)
app.include_router(missions_mongo_router)
app.include_router(stats_router)

yolo = YoloDetector()
thermal = ThermalDetector()
thermal_sim = ThermalSimulator()
last_detection_time = 0.0
DETECTION_COOLDOWN = 3.0
grid_clients: list[WebSocket] = []
detection_history: list[dict] = []

_simulation_task: asyncio.Task | None = None
active_mission_id: int | None = None
_mission_configured: bool = False
_mission_name: str = ""
_mission_altitude: float | None = None
_mission_cell_size_m: float | None = None

class MissionSetupRequest(BaseModel):
    name: str = "Misión sin nombre"
    lat: float
    lng: float
    altitude: float = 25.0
    grid_rows: int = 20
    grid_cols: int = 20
    cell_size_m: float = 20.0

class DroneCommand(BaseModel):
    throttle: int = 0
    yaw: int = 0
    pitch: int = 0
    roll: int = 0

_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_last_cmd_time: float = 0.0


async def _keepalive_loop():
    while True:
        await asyncio.sleep(2.0)
        if time.time() - _last_cmd_time > 3.0:
            try:
                _udp_sock.sendto(b"T:0,Y:0,P:0,R:0", (DRONE_IP, DRONE_UDP_PORT))
            except Exception:
                pass


class FrameGrabber:
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

        if CAMERA_SOURCE == "video":
            self._running = True
            self._thread = threading.Thread(
                target=self._video_reader_loop, args=(source,), daemon=True
            )
            self._thread.start()
            print(f"✅ Video: {source}")
            return True

        if isinstance(source, str):
            self._stream_url = source
            self._running = True
            self._thread = threading.Thread(target=self._mjpeg_reader_loop, daemon=True)
            self._thread.start()
            print(f"✅ Cámara: {CAMERA_SOURCE} (url: {source}) — conectando...")
            return True

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
        while self._running:
            resp = None
            try:
                resp = requests.get(
                    self._stream_url, stream=True,
                    timeout=(5, 10),
                )
                buf = b''
                for chunk in resp.iter_content(chunk_size=4096):
                    if not self._running:
                        break
                    buf += chunk
                    while True:
                        start = buf.find(b'\xff\xd8')
                        if start == -1:
                            buf = b''
                            break
                        end = buf.find(b'\xff\xd9', start)
                        if end == -1:
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
            except Exception as e:
                print(f"⚠️ MJPEG stream error: {e}, reconectando en 2s...")
            finally:
                if resp:
                    try:
                        resp.close()
                    except Exception:
                        pass
            time.sleep(2)

    def _cv2_reader_loop(self):
        while self._running and self._cap is not None:
            ret, frame = self._cap.read()
            if ret and frame is not None:
                with self._lock:
                    self._frame = frame

    def _video_reader_loop(self, path: str):
        """Lee videos de media/videos/ en rotación, o una URL de YouTube en loop."""
        if "youtube.com/" in path or "youtu.be/" in path:
            try:
                import yt_dlp
                ydl_opts = {"format": "best[height<=720]", "quiet": True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(path, download=False)
                    path = info["url"]
            except ImportError:
                print("yt-dlp no instalado. pip install yt-dlp")
                return
            except Exception as e:
                print(f"Error obteniendo URL de YouTube: {e}")
                return
            playlist = [path]
        else:
            video_dir = os.path.dirname(path) or "media/videos"
            exts = (".mp4", ".avi", ".mkv", ".mov", ".webm")
            playlist = sorted(
                f for f in glob.glob(os.path.join(video_dir, "*"))
                if os.path.splitext(f)[1].lower() in exts
            )
            if not playlist:
                print(f"No hay videos en {video_dir}")
                return

        idx = 0
        while self._running:
            video = playlist[idx % len(playlist)]
            cap = cv2.VideoCapture(video)
            if not cap.isOpened():
                print(f"No se pudo abrir: {video}, saltando...")
                idx += 1
                time.sleep(1)
                continue

            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            delay = 1.0 / fps
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if w and h:
                self.frame_w = w
                self.frame_h = h
            print(f"Reproduciendo: {os.path.basename(video)}")

            while self._running:
                ret, frame = cap.read()
                if not ret:
                    break
                with self._lock:
                    self._frame = frame
                time.sleep(delay)

            cap.release()
            idx += 1

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

@app.get("/")
def health():
    return {"status": "AeroSearch AI online"}

@app.get("/mission/active")
def mission_active():
    return {"active": _mission_configured and drone_state.mission_active}

@app.post("/mission/stop")
async def mission_stop():
    global _simulation_task, _mission_configured
    if not drone_state.mission_active and (_simulation_task is None or _simulation_task.done()):
        raise HTTPException(status_code=400, detail="No hay misión activa")
    drone_state.mission_active = False
    if _simulation_task and not _simulation_task.done():
        try:
            await asyncio.wait_for(_simulation_task, timeout=3.0)
        except (asyncio.TimeoutError, Exception):
            _simulation_task.cancel()
    _close_mission_db()
    _mission_configured = False
    drone_state.status = "idle"
    return {"status": "stopped"}

@app.post("/mission/setup")
async def mission_setup(req: MissionSetupRequest):
    global _simulation_task, _mission_configured, _mission_name, _mission_altitude, _mission_cell_size_m
    _mission_name = req.name
    _mission_altitude = req.altitude
    _mission_cell_size_m = req.cell_size_m
    if _simulation_task and not _simulation_task.done():
        drone_state.mission_active = False
        try:
            await asyncio.wait_for(_simulation_task, timeout=3.0)
        except (asyncio.TimeoutError, Exception):
            _simulation_task.cancel()
    _close_mission_db()
    _mission_configured = True

    grid = reset_mission(
        lat=req.lat, lng=req.lng, altitude=req.altitude,
        rows=req.grid_rows, cols=req.grid_cols,
        cell_size_m=req.cell_size_m,
    )
    detection_history.clear()
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

@app.post("/drone/reverse")
def drone_reverse():
    drone_state.sim_direction = -1 if drone_state.sim_direction >= 0 else 1
    return {"direction": drone_state.sim_direction}

@app.post("/drone/hover")
def drone_hover():
    if drone_state.sim_direction == 0:
        drone_state.sim_direction = 1
        return {"status": "resumed", "direction": 1}
    drone_state.sim_direction = 0
    drone_state.cmd_throttle = 0
    drone_state.cmd_pitch = 0
    drone_state.cmd_roll = 0
    return {"status": "hover"}

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

@app.websocket("/ws/mission")
async def mission_websocket(websocket: WebSocket):
    global _simulation_task, active_mission_id
    await websocket.accept()
    print("🔌 Misión conectada")

    if _mission_configured and (_simulation_task is None or _simulation_task.done()):
        drone_state.mission_start = time.time()
        drone_state.sim_step = 0
        drone_state.battery = 100.0
        drone_state.status = "idle"

        db = SessionLocal()
        try:
            mission = MissionModel(
                name=_mission_name or None,
                altitude=_mission_altitude,
                cell_size_m=_mission_cell_size_m,
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
            active_mission_id = mission.id
        except Exception as e:
            print(f"DB error creating mission: {e}")
            db.rollback()
        finally:
            db.close()

        _simulation_task = asyncio.create_task(_simulation_with_grid())

    try:
        while True:
            message = get_current_telemetry()
            await websocket.send_text(json.dumps(message))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("❌ Misión desconectada (simulación sigue corriendo)")


def _snap_step_to_position(spc: int, cols: int, steps_per_cycle: int) -> int:
    grid = state.search_grid
    south_lat = grid.origin_lat - (grid.rows - 0.5) * grid.cell_lat
    row_f = (drone_state.lat - south_lat) / grid.cell_lat
    row = max(0, round(row_f))

    if row % 2 == 0:
        col_f = (drone_state.lng - grid.origin_lng) / grid.cell_lng - 0.5
    else:
        col_f = (cols - 0.5) - (drone_state.lng - grid.origin_lng) / grid.cell_lng

    col_f = max(0.0, min(col_f, cols - 1.0))
    pos_h = min(int(col_f * spc), (cols - 1) * spc - 1)

    return row * steps_per_cycle + max(0, pos_h)


def _close_mission_db():
    global active_mission_id
    if not active_mission_id:
        return
    db = SessionLocal()
    try:
        m = db.query(MissionModel).filter(MissionModel.id == active_mission_id).first()
        if m:
            m.ended_at = datetime.now(timezone.utc)
            m.status = "completed"
            m.final_battery = round(drone_state.battery, 1)
            m.coverage_percent = state.search_grid.coverage_percent()
            m.detections_count = db.query(DetectionModel).filter(
                DetectionModel.mission_id == active_mission_id
            ).count()
            for cell in state.search_grid.cells.values():
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


async def _simulation_with_grid():
    grid = state.search_grid
    spc = int(grid.cell_size_m / 5.0)
    cols = grid.cols
    steps_horizontal = (cols - 1) * spc
    steps_vertical = spc
    steps_per_cycle = steps_horizontal + steps_vertical

    origin_lat = grid.origin_lat
    origin_lng = grid.origin_lng

    drone_state.mission_active = True
    was_manual = False

    while drone_state.mission_active:
        elapsed = int(time.time() - drone_state.mission_start)

        if drone_state.battery <= 0:
            drone_state.status = "landed"
            drone_state.mission_active = False
            _close_mission_db()
            return

        if drone_state.real_telemetry_active:
            source = "hardware"
            current_speed = 5.0
            was_manual = True
        elif drone_state.cmd_throttle > 0:
            thrust = drone_state.cmd_throttle / 255.0
            pitch_norm = drone_state.cmd_pitch / 100.0
            roll_norm = drone_state.cmd_roll / 100.0

            speed_mps = thrust * 10.0
            drone_state.lat += (speed_mps * pitch_norm) / 111_000
            cos_lat = max(math.cos(math.radians(drone_state.lat)), 0.01)
            drone_state.lng += (speed_mps * roll_norm) / (111_000 * cos_lat)

            magnitude = min(math.sqrt(pitch_norm**2 + roll_norm**2), 1.0)
            source = "manual"
            current_speed = round(speed_mps * magnitude, 1)
            was_manual = True
        else:
            source = "sim"
            if was_manual:
                drone_state.sim_step = _snap_step_to_position(spc, cols, steps_per_cycle)
                was_manual = False

            step = drone_state.sim_step
            row = step // steps_per_cycle
            pos_in_cycle = step % steps_per_cycle

            grid_row = grid.rows - 1 - row

            if pos_in_cycle < steps_horizontal:
                frac = pos_in_cycle / spc
                lat = origin_lat - (grid_row + 0.5) * grid.cell_lat
                if row % 2 == 0:
                    lng = origin_lng + (0.5 + frac) * grid.cell_lng
                else:
                    lng = origin_lng + (cols - 0.5 - frac) * grid.cell_lng
            else:
                v_frac = (pos_in_cycle - steps_horizontal + 1) / spc
                lat = origin_lat - (grid_row + 0.5 - v_frac) * grid.cell_lat
                if row % 2 == 0:
                    lng = origin_lng + (cols - 0.5) * grid.cell_lng
                else:
                    lng = origin_lng + 0.5 * grid.cell_lng

            drone_state.lat = lat
            drone_state.lng = lng
            drone_state.sim_step = max(0, drone_state.sim_step + drone_state.sim_direction)
            current_speed = 0.0 if drone_state.sim_direction == 0 else 5.0

        drone_state.battery = max(0, drone_state.battery - 0.05)
        if drone_state.sim_direction == 0 and not drone_state.real_telemetry_active and drone_state.cmd_throttle == 0:
            drone_state.status = "hover"
        else:
            drone_state.status = "flying"
        drone_state.last_update = time.time()

        changed_cells = state.search_grid.update_position(drone_state.lat, drone_state.lng)
        if changed_cells and grid_clients:
            grid_update = {
                "type": "grid_update",
                "cells": changed_cells,
                "coverage": state.search_grid.coverage_percent()
            }
            for client in grid_clients.copy():
                try:
                    await client.send_text(json.dumps(grid_update))
                except Exception:
                    grid_clients.remove(client)

        drone_state._last_telemetry = {
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
                "speed": current_speed,
                "elapsed": elapsed,
                "source": source,
            }
        }

        await asyncio.sleep(1)

@app.websocket("/ws/grid")
async def grid_websocket(websocket: WebSocket):
    await websocket.accept()
    grid_clients.append(websocket)
    await websocket.send_text(json.dumps({
        "type": "grid_init",
        "cells": state.search_grid.get_all_cells(),
        "coverage": state.search_grid.coverage_percent()
    }))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        grid_clients.remove(websocket)

_grabber: FrameGrabber | None = None

def get_grabber() -> FrameGrabber:
    global _grabber
    if _grabber is None:
        _grabber = FrameGrabber()
        _grabber.start()
    return _grabber

@app.websocket("/ws/detection")
async def detection_websocket(websocket: WebSocket):
    await websocket.accept()
    global last_detection_time

    if detection_history:
        await websocket.send_text(json.dumps({
            "type": "detection_history",
            "data": detection_history
        }))

    for _ in range(20):
        if active_mission_id is not None:
            break
        await asyncio.sleep(0.25)

    grabber = get_grabber()
    has_camera = grabber._running

    frame_w = grabber.frame_w
    frame_h = grabber.frame_h
    last_frame = None
    detected_positions: set[tuple[float, float]] = set()

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

            def run_yolo(f):
                return yolo.detect(f)

            def run_thermal(f):
                t_matrix = thermal_sim.generate(f)
                t_dets = thermal.detect(t_matrix)
                return t_matrix, t_dets

            rgb_future = asyncio.to_thread(run_yolo, frame)
            thermal_future = asyncio.to_thread(run_thermal, frame)
            rgb_detections, (t_matrix, t_dets) = await asyncio.gather(
                rgb_future, thermal_future
            )

            def fuse_and_encode(f, rgb_dets, t_mat, t_ds):
                fused = fuse_detections(rgb_dets, t_ds, frame_w=frame_w, frame_h=frame_h)

                annotated = yolo.draw(f.copy(), rgb_dets)
                _, buf1 = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 60])
                f_b64 = base64.b64encode(buf1).decode()

                overlay = thermal_sim.overlay_on_frame(f, t_mat, alpha=0.65)
                _, buf2 = cv2.imencode('.jpg', overlay, [cv2.IMWRITE_JPEG_QUALITY, 60])
                o_b64 = base64.b64encode(buf2).decode()

                return fused, f_b64, o_b64

            fused, frame_b64, overlay_b64 = await asyncio.to_thread(
                fuse_and_encode, frame, rgb_detections, t_matrix, t_dets
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
                        "timestamp": int(time.time() * 1000)
                    }
                }
                geo_detections.append(geo_det)

                conf_label = det["confidence"]
                pos_key = (round(drone_state.lat, 5), round(drone_state.lng, 5))
                now = time.time()
                if conf_label in ("high", "medium") and \
                   (now - last_detection_time) >= DETECTION_COOLDOWN and \
                   pos_key not in detected_positions:
                    last_detection_time = now
                    detected_positions.add(pos_key)

                    detection_cell = state.search_grid.mark_detection(drone_state.lat, drone_state.lng)
                    if detection_cell and grid_clients:
                        await asyncio.gather(*[
                            client.send_text(json.dumps({
                                "type": "grid_update",
                                "cells": [detection_cell],
                                "coverage": state.search_grid.coverage_percent()
                            }))
                            for client in grid_clients.copy()
                        ])
                    det_msg = {
                        "id": geo_det["id"],
                        "position": geo_det["position"],
                        "confidence": conf_label,
                        "source": det["source"],
                        "temperature": det.get("temperature"),
                        "timestamp": int(time.time() * 1000)
                    }
                    detection_history.append(det_msg)
                    await websocket.send_text(json.dumps({
                        "type": "detection",
                        "data": det_msg
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

                    if active_mission_id:
                        async def _persist(
                            _frame=frame,
                            _conf_label=conf_label,
                            _det=det,
                            _all_dets=rgb_detections,
                            _lat=drone_state.lat,
                            _lng=drone_state.lng,
                            _alt=drone_state.altitude,
                        ):
                            annotated = yolo.draw(_frame.copy(), _all_dets)
                            _, buf = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 60])
                            bbox = _det.get("bbox") or {}
                            det_payload = DetectionPayload(
                                confidence=_conf_label,
                                confidence_score=float(_det.get("rgb_confidence") or _det.get("iou") or 0.5),
                                source=_det.get("source", "rgb"),
                                temperature_celsius=_det.get("temperature"),
                                bounding_box=BoundingBox(
                                    x_norm=bbox.get("x1", 0.0), y_norm=bbox.get("y1", 0.0),
                                    w_norm=bbox.get("x2", 0.0) - bbox.get("x1", 0.0),
                                    h_norm=bbox.get("y2", 0.0) - bbox.get("y1", 0.0),
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

            await websocket.send_text(json.dumps({
                "type": "frame",
                "frame": frame_b64,
                "thermal_overlay": overlay_b64,
                "fused_detections": geo_detections,
                "detection_count": len(fused)
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
            for m in missions
        ]
    finally:
        db.close()


@app.delete("/missions/{mission_id}", status_code=204)
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


@app.get("/missions/{mission_id}")
def get_mission(mission_id: int):
    db = SessionLocal()
    try:
        m = db.query(MissionModel).filter(MissionModel.id == mission_id).first()
        if not m:
            raise HTTPException(status_code=404, detail="Mission not found")
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
            "detections_count": m.detections_count,
            "altitude": m.altitude,
            "cell_size_m": m.cell_size_m,
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
