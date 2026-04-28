import cv2
import numpy as np
from ultralytics import YOLO
import time

class YoloDetector:
    def __init__(self, model_size: str = "yolov8n"):
        """
        model_size opciones: yolov8n (rápido), yolov8s (balance), yolov8m (preciso)
        La primera vez descarga el modelo automáticamente (~6MB para nano)
        """
        print(f"🧠 Cargando modelo {model_size}...")
        self.model = YOLO(f"{model_size}.pt")
        self.person_class_id = 0  # en COCO dataset, clase 0 = persona
        print("✅ Modelo listo")

    def detect(self, frame: np.ndarray) -> list[dict]:
        """
        Recibe un frame (numpy array BGR de OpenCV)
        Retorna lista de detecciones de personas
        """
        results = self.model(
            source=frame,
            verbose=False,   # no imprimir en consola cada frame
            conf=0.4,        # confianza mínima 40%
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