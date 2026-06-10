import os
from dotenv import load_dotenv

load_dotenv()

CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "webcam")
CAMERA_FLIP   = os.getenv("CAMERA_FLIP", "0") not in ("0", "false", "no", "")

# IP del ESP32-CAM — debe definirse en .env al usar CAMERA_SOURCE=esp32
DRONE_IP = os.getenv("DRONE_IP")
ESP32_STREAM_URL = os.getenv("ESP32_STREAM_URL") or (f"http://{DRONE_IP}/stream" if DRONE_IP else None)

# Puertos UDP para control y telemetría (deben coincidir con pch.h)
DRONE_UDP_PORT = int(os.getenv("DRONE_UDP_PORT", "4210"))
DRONE_UDP_TX_PORT = int(os.getenv("DRONE_UDP_TX_PORT", "4211"))

VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "media/videos/video6.mp4")

# Apidrone API (driver opcional — activa integración cuando está definida)
APIDRONE_API_URL = os.getenv("APIDRONE_API_URL")
APIDRONE_WS_URL = (
    APIDRONE_API_URL.replace("https://", "wss://").replace("http://", "ws://")
    if APIDRONE_API_URL else None
)

_apidrone_mjpeg = f"{APIDRONE_API_URL}/mjpeg" if APIDRONE_API_URL else None

CAMERA_INDEX = {
    "webcam":    (0, True),
    "camo":      (1, True),
    "esp32":     (ESP32_STREAM_URL, False),
    "video":     (VIDEO_SOURCE, False),
    "synthetic": (None, False),
    "apidrone":  (_apidrone_mjpeg, False),
}

# MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB",  "aerosearch")
