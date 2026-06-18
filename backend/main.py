import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from modules.drone.simulator import get_current_telemetry
from modules.detection.yolo_detector import YoloDetector, CONFIDENCE_THRESHOLD
from modules.detection.thermal_detector import ThermalDetector
from modules.detection.thermal_simulator import ThermalSimulator
from modules.detection.fusion import fuse_detections
import core.state as state
from core.state import drone_state, BASE_LAT, BASE_LNG, reset_mission
from modules.mapping.grid import CELL_SIZE_METERS
from core.config import DRONE_IP, DRONE_UDP_PORT, DRONE_UDP_TX_PORT
from core.config import CAMERA_SOURCE, CAMERA_INDEX, VIDEO_SOURCE
from modules.drone.camera import open_camera
from modules.drone.udp_telemetry import start_udp_listener, hw_watchdog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import DRONE_UDP_TX_PORT
from db.database import init_db
from db.mission_ops import close_orphan_missions
from db.mongodb import connect as mongo_connect, disconnect as mongo_disconnect
from modules.drone.frame_grabber import stop_grabber
from modules.drone.udp_telemetry import hw_watchdog, start_udp_listener
from routers import images, missions_mongo, stats
from routers import drone, missions_sql, websockets

init_db()
close_orphan_missions()

yolo = YoloDetector()


def _print_startup_banner():
    """Resumen de config al arrancar: de dónde sale el video y con qué modelo se infiere."""
    if CAMERA_SOURCE == "video":
        fuente = f"VIDEO (loop): {os.path.dirname(VIDEO_SOURCE) or 'media/videos'}/"
    elif CAMERA_SOURCE == "synthetic":
        fuente = "SINTÉTICO (sin cámara)"
    else:
        fuente = f"CÁMARA EN VIVO: {CAMERA_SOURCE}"
    print("\n" + "=" * 56)
    print("  AeroSearch AI — configuración de arranque")
    print("-" * 56)
    print(f"  Fuente   : {fuente}")
    print(f"  Modelo   : {yolo.weights_rel}")
    print(f"  imgsz    : {yolo.imgsz}   conf: {CONFIDENCE_THRESHOLD}")
    print("=" * 56 + "\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo_connect()
    _print_startup_banner()
    # Se guarda el transport para cerrarlo en el shutdown.
    # Sin esto, el socket UDP quedaba ocupado al reiniciar y el puerto
    # lanzaba WinError 10048 en el siguiente arranque.
    udp_transport = await start_udp_listener(DRONE_UDP_TX_PORT)
    asyncio.create_task(hw_watchdog())
    asyncio.create_task(drone.keepalive_loop())
    yield
    udp_transport.close()  # libera el puerto UDP al cerrar
    stop_grabber()
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

app.include_router(drone.router)
app.include_router(missions_sql.router)
app.include_router(websockets.router)
app.include_router(images.router)
app.include_router(missions_mongo.router)
app.include_router(stats.router)


@app.get("/")
def health():
    return {"status": "AeroSearch AI online"}
