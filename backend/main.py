from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
import json, cv2, numpy as np, base64, asyncio, time, uuid, socket, threading, requests

app = FastAPI(title="AeroSearch AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("shutdown")
def shutdown_event():
    if _grabber is not None:
        _grabber.stop()

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

class DroneCommand(BaseModel):
    throttle: int = 0   # 0-255 (PWM directo al motor)
    yaw: int = 0        # -100 a 100
    pitch: int = 0      # -100 a 100
    roll: int = 0       # -100 a 100

_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_last_cmd_time: float = 0.0


@app.on_event("startup")
async def startup():
    await start_udp_listener(DRONE_UDP_TX_PORT)
    asyncio.create_task(hw_watchdog())
    asyncio.create_task(_keepalive_loop())


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
    return {"sent": payload, "target": f"{DRONE_IP}:{DRONE_UDP_PORT}"}

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

    grabber = get_grabber()
    has_camera = grabber._running

    frame_w = grabber.frame_w
    frame_h = grabber.frame_h
    last_frame = None

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

            rgb_detections = await asyncio.to_thread(yolo.detect, frame)
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
                now = time.time()
                if conf_label in ("high", "medium") and \
                   (now - last_detection_time) >= DETECTION_COOLDOWN:
                    last_detection_time = now

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