import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import time

_V2_WEIGHTS = Path(__file__).resolve().parents[2] / "yolov8n_tuned_v2.pt"
_FALLBACK_WEIGHTS = Path(__file__).resolve().parents[2] / "yolov8n.pt"

CONFIDENCE_THRESHOLD = 0.25


class YoloDetector:
    def __init__(self):
        if _V2_WEIGHTS.exists():
            weights_path = _V2_WEIGHTS
        else:
            print(f"v2 weights no encontrados, usando fallback {_FALLBACK_WEIGHTS.name}")
            weights_path = _FALLBACK_WEIGHTS

        self.model = YOLO(str(weights_path))
        self.weights_name = weights_path.name
        self.person_class_id = 0
        print(f"Modelo cargado: {self.weights_name} (conf={CONFIDENCE_THRESHOLD})")

    def detect(self, frame: np.ndarray) -> list[dict]:
        results = self.model(
            frame,
            verbose=False,
            conf=CONFIDENCE_THRESHOLD,
            classes=[self.person_class_id],
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
