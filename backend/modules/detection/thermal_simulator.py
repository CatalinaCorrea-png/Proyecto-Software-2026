import numpy as np
import cv2

# Temperatura ambiente base
AMBIENT_TEMP = 20.0
HUMAN_TEMP = 36.5
THERMAL_GRID_W = 32
THERMAL_GRID_H = 24

class ThermalSimulator:
    """
    Simula el MLX90640 de forma realista usando los bounding boxes de YOLO.
    Si YOLO detecta una persona en cierta zona del frame,
    la matriz térmica va a tener calor corporal en esa misma zona.
    """

    def __init__(self, frame_w: int = 640, frame_h: int = 480):
        self.frame_w = frame_w
        self.frame_h = frame_h

    def generate(self, rgb_detections: list[dict]) -> np.ndarray:
        """
        Genera matriz de temperatura 32x24 basada en las detecciones RGB.
        """
        # Base: ruido de temperatura ambiente
        matrix = np.random.normal(AMBIENT_TEMP, 0.8, (THERMAL_GRID_H, THERMAL_GRID_W))

        for det in rgb_detections:
            bbox = det["bbox"]

            # Convertir bbox del frame RGB a coordenadas de la grilla 32x24
            tx1 = int((bbox["x1"] / self.frame_w) * THERMAL_GRID_W)
            ty1 = int((bbox["y1"] / self.frame_h) * THERMAL_GRID_H)
            tx2 = int((bbox["x2"] / self.frame_w) * THERMAL_GRID_W)
            ty2 = int((bbox["y2"] / self.frame_h) * THERMAL_GRID_H)

            # Clamp para no salir de la grilla
            tx1 = max(0, min(tx1, THERMAL_GRID_W - 1))
            ty1 = max(0, min(ty1, THERMAL_GRID_H - 1))
            tx2 = max(0, min(tx2, THERMAL_GRID_W - 1))
            ty2 = max(0, min(ty2, THERMAL_GRID_H - 1))

            if tx2 <= tx1 or ty2 <= ty1:
                continue

            # Rellenar zona con temperatura corporal + ruido pequeño
            h = ty2 - ty1
            w = tx2 - tx1
            heat_patch = np.random.normal(HUMAN_TEMP, 0.5, (h, w))
            matrix[ty1:ty2, tx1:tx2] = heat_patch

            # Gradiente de calor — el centro es más caliente que los bordes
            # (simula que el torso irradia más que las extremidades)
            cy = (ty1 + ty2) // 2
            cx = (tx1 + tx2) // 2
            if ty1 < cy < ty2 and tx1 < cx < tx2:
                matrix[cy-1:cy+1, cx-1:cx+1] = np.random.normal(37.2, 0.2, (2, 2))

        return matrix

    def to_visual_frame(self, temp_matrix: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
        """
        Convierte la matriz térmica a una imagen visual con colormap INFERNO
        escalada al tamaño del frame de la webcam.
        """
        normalized = cv2.normalize(temp_matrix, None, 0, 255,
                                   cv2.NORM_MINMAX, cv2.CV_8U)
        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_INFERNO)
        # Escalar a tamaño del frame con interpolación nearest para efecto "pixelado"
        scaled = cv2.resize(colored, (target_w, target_h),
                           interpolation=cv2.INTER_NEAREST)
        return scaled

    def overlay_on_frame(
        self,
        rgb_frame: np.ndarray,
        temp_matrix: np.ndarray,
        alpha: float = 0.45
    ) -> np.ndarray:
        """
        Mezcla el frame RGB con el overlay térmico.
        alpha = 0.0 → solo RGB
        alpha = 1.0 → solo térmico
        alpha = 0.45 → balance donde se ve la persona y el calor
        """
        h, w = rgb_frame.shape[:2]
        thermal_visual = self.to_visual_frame(temp_matrix, w, h)
        blended = cv2.addWeighted(rgb_frame, 1 - alpha, thermal_visual, alpha, 0)
        return blended