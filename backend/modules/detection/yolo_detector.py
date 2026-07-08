import os
import cv2
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from ultralytics import YOLO
import time

# Cargar backend/.env acá también: este módulo lee YOLO_WEIGHTS/YOLO_IMGSZ y
# puede importarse antes que core.config (que es quien normalmente hace load_dotenv).
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_V2_WEIGHTS = _BACKEND_DIR / "yolov8n_tuned_v2.pt"
_FALLBACK_WEIGHTS = _BACKEND_DIR / "yolov8n.pt"

CONFIDENCE_THRESHOLD = 0.27


def _resolve_weights() -> Path:
    """Resuelve los pesos a usar: YOLO_WEIGHTS si está seteado, si no v2, si no fallback."""
    weights_env = os.getenv("YOLO_WEIGHTS")
    if weights_env:
        p = Path(weights_env)
        if not p.is_absolute():
            p = _BACKEND_DIR / p
        if p.exists():
            return p
        print(f"YOLO_WEIGHTS={weights_env} no encontrado, cayendo a v2")
    if _V2_WEIGHTS.exists():
        return _V2_WEIGHTS
    print(f"v2 weights no encontrados, usando fallback {_FALLBACK_WEIGHTS.name}")
    return _FALLBACK_WEIGHTS


class YoloDetector:
    def __init__(self):
        weights_path = _resolve_weights()

        self.model = YOLO(str(weights_path))
        self.weights_name = weights_path.name
        # Ruta relativa a backend/ para que se vea de qué modelo se trata (v2/v3/...).
        try:
            self.weights_rel = str(weights_path.relative_to(_BACKEND_DIR))
        except ValueError:
            self.weights_rel = str(weights_path)
        self.imgsz = int(os.getenv("YOLO_IMGSZ", "640"))
        self.person_class_id = 0
        print(f"Modelo cargado: {self.weights_rel} (conf={CONFIDENCE_THRESHOLD}, imgsz={self.imgsz})")

    def detect(self, frame: np.ndarray) -> list[dict]:
        results = self.model(
            frame,
            verbose=False,
            conf=CONFIDENCE_THRESHOLD,
            classes=[self.person_class_id],
            imgsz=self.imgsz,
        )

        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                detections.append({
                    "bbox": {
                        "x1": int(x1), "y1": int(y1),
                        "x2": int(x2), "y2": int(y2),
                        "cx": int((x1 + x2) / 2),
                        "cy": int((y1 + y2) / 2),
                    },
                    "confidence": confidence,
                    "source": "rgb",
                    "timestamp": int(time.time() * 1000)
                })

        return detections

    def draw(self, frame: np.ndarray, detections: list[dict]) -> np.ndarray:
        """Dibuja los bounding boxes en el frame para debug visual"""
        for det in detections:
            bbox = det["bbox"]
            color = (0, 255, 0) if det["confidence"] > 0.7 else (0, 165, 255)
            cv2.rectangle(frame, (bbox["x1"], bbox["y1"]), (bbox["x2"], bbox["y2"]), color, 2)
            label = f"persona {det['confidence']:.0%}"
            cv2.putText(frame, label, (bbox["x1"], bbox["y1"] - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return frame
