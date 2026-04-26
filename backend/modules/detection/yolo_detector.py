import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import time

_FINETUNED_WEIGHTS = Path(__file__).resolve().parents[2] / "yolov8n_aerial.pt"
_BASE_WEIGHTS      = Path(__file__).resolve().parents[2] / "yolov8n.pt"

# Altitud (metros) a partir de la cual se usa el modelo aéreo
AERIAL_ALTITUDE_THRESHOLD = 15.0


class YoloDetector:
    def __init__(self, model_size: str = "yolov8n"):
        base_path = str(_BASE_WEIGHTS) if _BASE_WEIGHTS.exists() else f"{model_size}.pt"
        self.model_base = YOLO(base_path)
        print(f"Modelo base cargado: {base_path}")

        if _FINETUNED_WEIGHTS.exists():
            self.model_aerial = YOLO(str(_FINETUNED_WEIGHTS))
            print(f"Modelo aéreo cargado: {_FINETUNED_WEIGHTS.name}")
        else:
            self.model_aerial = self.model_base
            print("Modelo aéreo no encontrado, usando base para ambos modos")

        self.person_class_id = 0

    def detect(self, frame: np.ndarray, altitude: float = 0.0) -> list[dict]:
        aerial = altitude >= AERIAL_ALTITUDE_THRESHOLD
        model = self.model_aerial if aerial else self.model_base
        conf  = 0.25 if aerial else 0.40

        results = model(frame, verbose=False, conf=conf, classes=[self.person_class_id])

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