import os
from dotenv import load_dotenv

load_dotenv()

CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "webcam") # Si no existe o no se para parametro: default="webcam"
ESP32_STREAM_URL = os.getenv("ESP32_STREAM_URL", "http://192.168.1.1:81/stream")


# Índices por fuente
CAMERA_INDEX = {
    "webcam":    (0, True),   # (índice, usar DSHOW)
    "camo":      (1, True),   # Camo ocupa el índice 1
    "esp32":     (ESP32_STREAM_URL, False),  # ← URL del ESP32
    "synthetic": (None, False) # sin cámara - video.mp4 o simulación interna
}