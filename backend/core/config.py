import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

ESP32_STREAM_URL = os.getenv("ESP32_STREAM_URL", "http://192.168.1.1:81/stream")
CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "webcam") # Si no existe o no se para parametro: default="webcam"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Database ──────────────────────────────────────────────
    # asyncpg driver required: pip install asyncpg
    DATABASE_URL: str = "postgresql+asyncpg://aerosearch:aerosearch@localhost:5432/aerosearch"
    DB_ECHO:      bool = False   # set True in dev to log SQL

    # ── Image storage ─────────────────────────────────────────
    # "local" → saves to IMAGES_LOCAL_ROOT on disk
    # "s3"    → saves to AWS S3 (needs boto3 + credentials)
    STORAGE_BACKEND: str = "local"
    IMAGES_LOCAL_ROOT: str = "media/detections"   # relative to project root

    # S3 (only needed when STORAGE_BACKEND=s3)
    S3_BUCKET:     str = ""
    S3_REGION:     str = "us-east-1"
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""

settings = Settings()

# ── Camera index ─────────────────────────
CAMERA_INDEX: dict = {
    "webcam":    (0, True),   # (índice, usar DSHOW)
    "camo":      (1, True),   # Camo ocupa el índice 1
    "esp32":     (ESP32_STREAM_URL, False),  # ← URL del ESP32
    "synthetic": (None, False), # sin cámara - video.mp4 o simulación interna
    "webcam_1":   (1, True),
}