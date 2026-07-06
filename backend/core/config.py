import os
from dotenv import load_dotenv

load_dotenv()

CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "webcam")

# IP del ESP32-CAM — debe definirse en .env al usar CAMERA_SOURCE=esp32
DRONE_IP = os.getenv("DRONE_IP")
ESP32_STREAM_URL = os.getenv("ESP32_STREAM_URL") or (f"http://{DRONE_IP}/stream" if DRONE_IP else None)

# Puertos UDP para control y telemetría (deben coincidir con pch.h)
DRONE_UDP_PORT = int(os.getenv("DRONE_UDP_PORT", "4210"))
DRONE_UDP_TX_PORT = int(os.getenv("DRONE_UDP_TX_PORT", "4211"))

VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "media/videos/video6.mp4")

CAMERA_INDEX = {
    "webcam":    (0, True),
    "camo":      (1, True),
    "esp32":     (ESP32_STREAM_URL, False),
    "video":     (VIDEO_SOURCE, False),
    "synthetic": (None, False)
}

# Base de datos SQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aerosearch.db")

# MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB",  "aerosearch")

# JWT Auth
JWT_SECRET_KEY     = os.getenv("JWT_SECRET_KEY", "aerosearch-dev-secret-change-in-production")
JWT_ALGORITHM      = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 hours
