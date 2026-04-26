import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import time

_FINETUNED_WEIGHTS = (
    Path(__file__).resolve().parents[3]
    / "training" / "runs" / "phase2_full" / "weights" / "best.pt"
)
_FALLBACK_WEIGHTS = Path(__file__).resolve().parents[2] / "yolov8n.pt"


class YoloDetector:
    def __init__(self, model_size: str = "yolov8n"):
        if _FINETUNED_WEIGHTS.exists():
            weights = str(_FINETUNED_WEIGHTS)
            print(f"Cargando modelo fine-tuneado: {weights}")
        else:
            weights = str(_FALLBACK_WEIGHTS) if _FALLBACK_WEIGHTS.exists() else f"{model_size}.pt"
            print(f"Cargando modelo base: {weights}")

        self.model = YOLO(weights)
        self.person_class_id = 0
        print("Modelo listo")

    def detect(self, frame: np.ndarray) -> list[dict]:
        """
        Recibe un frame (numpy array BGR de OpenCV)
        Retorna lista de detecciones de personas
        """
        results = self.model(
            frame,
            verbose=False,   # no imprimir en consola cada frame
            conf=0.25,       # umbral bajo: detecciones aéreas tienen scores menores
            classes=[self.person_class_id]  # solo buscar personas
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
                        "cx": int((x1 + x2) / 2),  # centro X
                        "cy": int((y1 + y2) / 2),  # centro Y
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