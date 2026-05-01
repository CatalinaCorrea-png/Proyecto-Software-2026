import os
from dotenv import load_dotenv

load_dotenv()

CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "webcam")

# IP del ESP32-CAM en la red local (configurar con env var DRONE_IP)
DRONE_IP = os.getenv("DRONE_IP", "192.168.4.1")
ESP32_STREAM_URL = os.getenv("ESP32_STREAM_URL", f"http://{DRONE_IP}/stream")

# Puertos UDP para control y telemetría (deben coincidir con pch.h)
DRONE_UDP_PORT = int(os.getenv("DRONE_UDP_PORT", "4210"))   # ESP32 escucha comandos aquí
DRONE_UDP_TX_PORT = int(os.getenv("DRONE_UDP_TX_PORT", "4211"))  # ESP32 envía telemetría aquí

CAMERA_INDEX = {
    "webcam":    (0, True),
    "camo":      (1, True),
    "esp32":     (ESP32_STREAM_URL, False),
    "synthetic": (None, False)
}