import numpy as np
import time

# Rango de temperatura corporal humana detectable
# (con distancia y ropa puede bajar, por eso el rango es amplio)
HUMAN_TEMP_MIN = 28.0
HUMAN_TEMP_MAX = 40.0
MIN_BLOB_SIZE = 4  # mínimo de píxeles para considerar detección (en 32x24)

class ThermalDetector:
    def __init__(self):
        self.grid_w = 32
        self.grid_h = 24

    def detect(self, temp_matrix: np.ndarray) -> list[dict]:
        """
        Recibe matriz de temperaturas 32x24 del MLX90640
        Retorna lista de blobs que podrían ser humanos
        """
        # Máscara: píxeles dentro del rango de temperatura humana
        mask = ((temp_matrix >= HUMAN_TEMP_MIN) &
                (temp_matrix <= HUMAN_TEMP_MAX)).astype(np.uint8)

        # Encontrar regiones conectadas (blobs)
        import cv2
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

        detections = []
        for i in range(1, num_labels):  # 0 = fondo, empezamos en 1
            area = stats[i, cv2.CC_STAT_AREA]
            if area < MIN_BLOB_SIZE:
                continue  # demasiado chico, probablemente ruido

            # Normalizar posición a 0.0-1.0 (relativo al frame térmico)
            cx_norm = centroids[i][0] / self.grid_w
            cy_norm = centroids[i][1] / self.grid_h

            # Temperatura máxima en el blob (útil para reportar)
            blob_mask = (labels == i)
            max_temp = float(temp_matrix[blob_mask].max())
            avg_temp = float(temp_matrix[blob_mask].mean())

            detections.append({
                "bbox_normalized": {
                    "cx": cx_norm,
                    "cy": cy_norm,
                    "x1": stats[i, cv2.CC_STAT_LEFT] / self.grid_w,
                    "y1": stats[i, cv2.CC_STAT_TOP] / self.grid_h,
                    "x2": (stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH]) / self.grid_w,
                    "y2": (stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT]) / self.grid_h,
                },
                "max_temp": max_temp,
                "avg_temp": avg_temp,
                "area": int(area),
                "source": "thermal",
                "timestamp": int(time.time() * 1000)
            })

        return detections

    def simulate(self) -> np.ndarray:
        """
        Simula una lectura del MLX90640 mientras no tenés el hardware.
        Genera ruido térmico de fondo con un 'humano' random cada tanto.
        """
        # Fondo: temperatura ambiente (15-25°C)
        matrix = np.random.uniform(15, 25, (self.grid_h, self.grid_w))

        # Simular humano con 5% de probabilidad
        if np.random.random() < 0.05:
            # Posición random
            r = np.random.randint(4, 20)
            c = np.random.randint(4, 28)
            # Parche de calor corporal
            matrix[r:r+3, c:c+4] = np.random.uniform(34, 37, (3, 4))

        return matrix

    def to_image(self, temp_matrix: np.ndarray):
        """Convierte la matriz térmica a imagen con colormap para visualizar"""
        import cv2
        normalized = cv2.normalize(temp_matrix, None, 0, 255,
                                   cv2.NORM_MINMAX, cv2.CV_8U)
        return cv2.applyColorMap(normalized, cv2.COLORMAP_INFERNO)