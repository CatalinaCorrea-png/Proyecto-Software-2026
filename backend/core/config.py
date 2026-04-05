import os
from dotenv import load_dotenv

load_dotenv()

CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "webcam") # Si no existe o no se para parametro: default="webcam"
ESP32_STREAM_URL = os.getenv("ESP32_STREAM_URL", "http://192.168.1.1:81/stream")


# Índices por fuente
CAMERA_INDEX = {
    "webcam":    (0, True),   # (índice, usar DSHOW)
    "camo":      (0, True),   # Camo ocupa el índice 0
    "esp32":     (ESP32_STREAM_URL, False),  # ← URL del ESP32
    "synthetic": (None, False) # sin cámara - video.mp4 o simulación interna
}

# PARA SABER EL INDICE DE CADA CAMARA: ejecutar este snippet en consola una vez con todas las cámaras conectadas
# python -c "
# import cv2
# for i in range(4):
#     cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
#     if cap.isOpened():
#         ret, frame = cap.read()
#         print(f'Índice {i}: frame={ret}, size={frame.size if ret and frame is not None else 0}')
#         cap.release()
#     else:
#         print(f'Índice {i}: no disponible')
# "