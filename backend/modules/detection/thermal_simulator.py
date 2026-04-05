import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io

AMBIENT_TEMP = 20.0
THERMAL_GRID_W = 32
THERMAL_GRID_H = 24
FALSE_NEGATIVE_PROB = 0.25

ZONE_TEMPS = {
    "torso":   (37.0, 0.4),
    "cabeza":  (36.5, 0.5),
    "brazos":  (34.5, 0.8),
    "piernas": (33.5, 0.8),
}

MODEL_PATH = "pose_landmarker_lite.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"

class ThermalSimulator:
    def __init__(self, frame_w: int = 640, frame_h: int = 480):
        self.frame_w = frame_w
        self.frame_h = frame_h
        self._bg_phase = 0.0

        # ── Descargar modelo Pose si no existe ───────────────────────────
        if not os.path.exists(MODEL_PATH):
            print("⬇️  Descargando modelo MediaPipe Pose...")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("✅ Modelo descargado")

        # ── Pose Landmarker (nueva API 0.10+) ────────────────────────────
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=True   # ← pedir máscara de segmentación
        )
        self._pose_detector = vision.PoseLandmarker.create_from_options(options)

        # ── Selfie Segmentation (API legacy, más rápida para esto) ───────
        # self._selfie_seg = mp.solutions.selfie_segmentation.SelfieSegmentation(
        #     model_selection=0  # 0 = general (más rápido), 1 = landscape
        # )

        # ── Matplotlib — figura cacheada para interpolación bilinear ─────
        self._fig, self._ax = plt.subplots(
            figsize=(frame_w / 100, frame_h / 100), dpi=100
        )
        self._thermal_img = self._ax.imshow(
            np.zeros((THERMAL_GRID_H, THERMAL_GRID_W)),
            vmin=15, vmax=42,
            cmap='inferno',
            interpolation='bilinear'
        )
        self._ax.axis('off')
        self._fig.tight_layout(pad=0)

    def generate(self, frame_bgr: np.ndarray) -> np.ndarray:
        """
        Genera matriz de temperatura 32x24.
        
        Pipeline:
        1. Selfie Segmentation → máscara de silueta exacta
        2. Pose Landmarker → zonas del cuerpo (torso, brazos, piernas)
        3. Combinar → temperatura diferenciada sobre silueta real
        """
        # Flip horizontal y resize — corregir espejo de la webcam
        # frame_bgr = cv2.flip(frame_bgr, 1)
        small = cv2.resize(frame_bgr, (320, 240))
        # ── Fondo variable ────────────────────────────────────────────────
        self._bg_phase += 0.04
        base_temp = AMBIENT_TEMP + 2.5 * np.sin(self._bg_phase)
        matrix = np.random.normal(base_temp, 1.0, (THERMAL_GRID_H, THERMAL_GRID_W))

        for _ in range(np.random.randint(0, 3)):
            r = np.random.randint(0, THERMAL_GRID_H - 3)
            c = np.random.randint(0, THERMAL_GRID_W - 3)
            matrix[r:r+3, c:c+3] = np.random.normal(27.0, 1.0, (3, 3))

        frame_rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # ── PASO 1: Selfie Segmentation → silueta exacta ─────────────────
        # ── Un solo detector hace pose + segmentación ─────────────────────
        pose_result = self._pose_detector.detect(mp_image)

        if not pose_result.pose_landmarks:
            return matrix

        if np.random.random() < FALSE_NEGATIVE_PROB:
            return matrix

        # ── Máscara de silueta del Pose Landmarker ────────────────────────
        if pose_result.segmentation_masks:
            seg_mask_full = pose_result.segmentation_masks[0].numpy_view()
            seg_mask = cv2.resize(
                (seg_mask_full > 0.5).astype(np.uint8),
                (THERMAL_GRID_W, THERMAL_GRID_H),
                interpolation=cv2.INTER_AREA
            )
            seg_mask = (seg_mask > 0).astype(np.uint8)
        else:
            # Fallback: silueta completa si no hay máscara
            seg_mask = np.ones((THERMAL_GRID_H, THERMAL_GRID_W), dtype=np.uint8)

        # Temperatura base sobre toda la silueta
        body_temp = np.random.normal(35.5, 0.6, (THERMAL_GRID_H, THERMAL_GRID_W))
        matrix[seg_mask == 1] = body_temp[seg_mask == 1]

        # ── PASO 2: Pose Landmarker → zonas del cuerpo ───────────────────
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        pose_result = self._pose_detector.detect(mp_image)

        # Temperatura base para toda la silueta (si no hay pose, uniforme)
        body_temp = np.random.normal(35.5, 0.6, (THERMAL_GRID_H, THERMAL_GRID_W))
        matrix[seg_mask == 1] = body_temp[seg_mask == 1]

        # Si no detectó pose, la silueta queda con temperatura uniforme
        if not pose_result.pose_landmarks:
            return matrix

        lm = pose_result.pose_landmarks[0]

        def vis(idx: int) -> bool:
            return lm[idx].visibility > 0.15 if hasattr(lm[idx], 'visibility') else True

        def to_grid(x_norm: float, y_norm: float) -> tuple[int, int]:
            gx = max(0, min(int(x_norm * THERMAL_GRID_W), THERMAL_GRID_W - 1))
            gy = max(0, min(int(y_norm * THERMAL_GRID_H), THERMAL_GRID_H - 1))
            return gx, gy

        def zone_mask(points_idx: list[int]) -> np.ndarray:
            """
            Genera máscara de una zona corporal como polígono,
            INTERSECTADA con la silueta real de Selfie Seg.
            Esto garantiza que el calor solo aparece donde hay cuerpo real.
            """
            pts = [to_grid(lm[i].x, lm[i].y) for i in points_idx if vis(i)]
            if len(pts) < 2:
                return np.zeros((THERMAL_GRID_H, THERMAL_GRID_W), dtype=np.uint8)

            poly_mask = np.zeros((THERMAL_GRID_H, THERMAL_GRID_W), dtype=np.uint8)

            if len(pts) == 2:
                # Solo dos puntos → círculo en el centro
                cx = (pts[0][0] + pts[1][0]) // 2
                cy = (pts[0][1] + pts[1][1]) // 2
                cv2.circle(poly_mask, (cx, cy), 3, 1, -1)
            else:
                hull = cv2.convexHull(np.array(pts, dtype=np.int32))
                cv2.fillConvexPoly(poly_mask, hull, 1)

            # ← intersección con silueta real
            return cv2.bitwise_and(poly_mask, seg_mask)

        def paint_zone(points_idx: list[int], zone: str):
            mask = zone_mask(points_idx)
            if mask.sum() == 0:
                return
            mean_temp, std_temp = ZONE_TEMPS[zone]
            noise = np.random.normal(mean_temp, std_temp,
                                     (THERMAL_GRID_H, THERMAL_GRID_W))
            matrix[mask == 1] = noise[mask == 1]

        # ── PASO 3: Pintar zonas sobre silueta ───────────────────────────

        # CABEZA — nariz, ojos, orejas, boca
        paint_zone([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], zone="cabeza")

        # CUELLO — entre orejas y hombros
        paint_zone([7, 8, 11, 12], zone="cabeza")

        # TORSO — hombros + caderas estimadas
        shoulder_l, shoulder_r = lm[11], lm[12]
        if vis(11) and vis(12):
            # Expandir el torso hacia abajo para incluir zona abdominal
            torso_pts = [
                to_grid(shoulder_l.x - 0.03, shoulder_l.y),
                to_grid(shoulder_r.x + 0.03, shoulder_r.y),
                to_grid(shoulder_r.x + 0.05, shoulder_r.y + 0.28),
                to_grid(shoulder_l.x - 0.05, shoulder_l.y + 0.28),
            ]
            if vis(23) and vis(24):
                # Si hay caderas reales, usarlas
                torso_pts[2] = to_grid(lm[24].x + 0.02, lm[24].y)
                torso_pts[3] = to_grid(lm[23].x - 0.02, lm[23].y)

            torso_poly = np.zeros((THERMAL_GRID_H, THERMAL_GRID_W), dtype=np.uint8)
            hull = cv2.convexHull(np.array(torso_pts, dtype=np.int32))
            cv2.fillConvexPoly(torso_poly, hull, 1)
            torso_final = cv2.bitwise_and(torso_poly, seg_mask)

            mean_temp, std_temp = ZONE_TEMPS["torso"]
            noise = np.random.normal(mean_temp, std_temp, (THERMAL_GRID_H, THERMAL_GRID_W))
            matrix[torso_final == 1] = noise[torso_final == 1]

        # BRAZO IZQUIERDO — hombro, codo, muñeca, mano
        paint_zone([11, 13, 15, 17, 19], zone="brazos")

        # BRAZO DERECHO
        paint_zone([12, 14, 16, 18, 20], zone="brazos")

        # PIERNA IZQUIERDA — cadera, rodilla, tobillo, pie
        paint_zone([23, 25, 27, 29, 31], zone="piernas")

        # PIERNA DERECHA
        paint_zone([24, 26, 28, 30, 32], zone="piernas")

        # ── Suavizado final — blur leve para transiciones más naturales ───
        # Simula la difusión de calor que hace un sensor real
        matrix = cv2.GaussianBlur(matrix, (3, 3), 0)

        return matrix

    def to_visual_frame(self, temp_matrix: np.ndarray,
                        target_w: int, target_h: int) -> np.ndarray:
        # Normalizar a 0-255
        normalized = cv2.normalize(
            temp_matrix, None, 0, 255,
            cv2.NORM_MINMAX, cv2.CV_8U
        )
        # Colormap INFERNO o BONE
        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_INFERNO)
        # Escalar con interpolación cúbica (suave, no pixelado)
        return cv2.resize(
            colored, (target_w, target_h),
            interpolation=cv2.INTER_CUBIC
        )

    def overlay_on_frame(self, rgb_frame: np.ndarray,
                         temp_matrix: np.ndarray,
                         alpha: float = 0.55) -> np.ndarray:
        h, w = rgb_frame.shape[:2]
        thermal_visual = self.to_visual_frame(temp_matrix, w, h)
        blended = cv2.addWeighted(rgb_frame, 1 - alpha, thermal_visual, alpha, 0)
        vignette = self._make_vignette(h, w)
        return (blended * vignette).astype(np.uint8)

    def _make_vignette(self, h: int, w: int) -> np.ndarray:
        if not hasattr(self, '_vignette_cache') or \
           self._vignette_cache.shape != (h, w, 1):
            x = np.linspace(-1, 1, w)
            y = np.linspace(-1, 1, h)
            xv, yv = np.meshgrid(x, y)
            dist = np.sqrt(xv**2 + yv**2)
            vignette = np.clip(1.0 - 0.5 * dist, 0.6, 1.0)
            self._vignette_cache = vignette[:, :, np.newaxis]
        return self._vignette_cache