import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os

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

      # Descargar modelo si no existe
      if not os.path.exists(MODEL_PATH):
          print("⬇️  Descargando modelo MediaPipe Pose...")
          urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
          print("✅ Modelo descargado")

      # Nueva API 0.10+
      base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
      options = vision.PoseLandmarkerOptions(
          base_options=base_options,
          running_mode=vision.RunningMode.IMAGE,
          num_poses=1,
          min_pose_detection_confidence=0.5,
          min_pose_presence_confidence=0.5,
          min_tracking_confidence=0.5
      )
      self._detector = vision.PoseLandmarker.create_from_options(options)

  def generate(self, frame_bgr: np.ndarray) -> np.ndarray:
      # Fondo variable
      self._bg_phase += 0.04
      base_temp = AMBIENT_TEMP + 2.5 * np.sin(self._bg_phase)
      matrix = np.random.normal(base_temp, 1.0, (THERMAL_GRID_H, THERMAL_GRID_W))

      for _ in range(np.random.randint(0, 3)):
          r = np.random.randint(0, THERMAL_GRID_H - 3)
          c = np.random.randint(0, THERMAL_GRID_W - 3)
          matrix[r:r+3, c:c+3] = np.random.normal(27.0, 1.0, (3, 3))

      # MediaPipe nueva API — necesita mp.Image
      frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
      mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
      results = self._detector.detect(mp_image)

      if not results.pose_landmarks:
          return matrix

      if np.random.random() < FALSE_NEGATIVE_PROB:
          return matrix

      # En 0.10+ los landmarks son listas de objetos con x, y, z, visibility
      lm = results.pose_landmarks[0]  # primera persona

      def to_grid(x_norm, y_norm):
          gx = int(x_norm * THERMAL_GRID_W) + np.random.randint(-1, 2)
          gy = int(y_norm * THERMAL_GRID_H) + np.random.randint(-1, 2)
          return (
              max(0, min(gx, THERMAL_GRID_W - 1)),
              max(0, min(gy, THERMAL_GRID_H - 1))
          )
      
      def vis(idx):
          # Bajar de 0.3 a 0.15 — más permisivo
          return lm[idx].visibility > 0.15 if hasattr(lm[idx], 'visibility') else True

      def paint_polygon(points_idx, zone, expand=0):
          """
          Dibuja un polígono relleno entre los landmarks dados.
          Mucho más realista que puntos individuales.
          """
          pts = [to_grid(lm[i].x, lm[i].y) for i in points_idx if vis(i)]
          if len(pts) < 3:
              return
          mean_temp, std_temp = ZONE_TEMPS[zone]
          # Crear máscara del polígono
          mask = np.zeros((THERMAL_GRID_H, THERMAL_GRID_W), dtype=np.uint8)
          poly = np.array(pts, dtype=np.int32)
          cv2.fillConvexPoly(mask, poly, 1)
          # Pintar temperatura con ruido gaussiano en el área del polígono
          noise = np.random.normal(mean_temp, std_temp,
                                    (THERMAL_GRID_H, THERMAL_GRID_W))
          matrix[mask == 1] = noise[mask == 1]

      def paint_circle(idx, radius, zone):
          """Para partes pequeñas — cabeza, manos"""
          if not vis(idx):
              return
          cx, cy = to_grid(lm[idx].x, lm[idx].y)
          mean_temp, std_temp = ZONE_TEMPS[zone]
          mask = np.zeros((THERMAL_GRID_H, THERMAL_GRID_W), dtype=np.uint8)
          cv2.circle(mask, (cx, cy), radius, 1, -1)
          noise = np.random.normal(mean_temp, std_temp,
                                    (THERMAL_GRID_H, THERMAL_GRID_W))
          matrix[mask == 1] = noise[mask == 1]

      # ── CABEZA ────────────────────────────────────────────────────────
      paint_circle(0, radius=2, zone="cabeza")   # nariz como centro

      # ── TORSO —──────────────────────
      # ANTES:  polígono entre hombros y caderas : hombro_izq, hombro_der, cadera_der, cadera_izq → cuadrilátero
      # AHORA: — usar hombros + punto estimado del centro del torso
      shoulder_l = lm[11]
      shoulder_r = lm[12]

      if vis(11) and vis(12):
          # Centro entre hombros
          cx_s = (shoulder_l.x + shoulder_r.x) / 2
          cy_s = (shoulder_l.y + shoulder_r.y) / 2
          
          # Estimar torso hacia abajo (30% de la altura del frame)
          torso_cx, torso_cy = to_grid(cx_s, cy_s + 0.15)
          
          # Pintar polígono con puntos estimados aunque no haya caderas visibles
          pts = [
              to_grid(shoulder_l.x, shoulder_l.y),
              to_grid(shoulder_r.x, shoulder_r.y),
              to_grid(shoulder_r.x + 0.02, shoulder_r.y + 0.25),  # cadera der estimada
              to_grid(shoulder_l.x - 0.02, shoulder_l.y + 0.25),  # cadera izq estimada
          ]
          mean_temp, std_temp = ZONE_TEMPS["torso"]
          mask = np.zeros((THERMAL_GRID_H, THERMAL_GRID_W), dtype=np.uint8)
          poly = np.array(pts, dtype=np.int32)
          cv2.fillConvexPoly(mask, poly, 1)
          noise = np.random.normal(mean_temp, std_temp, (THERMAL_GRID_H, THERMAL_GRID_W))
          matrix[mask == 1] = noise[mask == 1]

      # ── BRAZO IZQUIERDO — hombro → codo → muñeca ─────────────────────
      paint_polygon([11, 13, 15], zone="brazos")

      # ── BRAZO DERECHO ─────────────────────────────────────────────────
      paint_polygon([12, 14, 16], zone="brazos")

      # ── PIERNA IZQUIERDA — cadera → rodilla → tobillo ─────────────────
      paint_polygon([23, 25, 27], zone="piernas")

      # ── PIERNA DERECHA ────────────────────────────────────────────────
      paint_polygon([24, 26, 28], zone="piernas")

      # ── MANOS (opcional, muy pequeñas en 32x24) ───────────────────────
      paint_circle(15, radius=1, zone="brazos")  # muñeca izq
      paint_circle(16, radius=1, zone="brazos")  # muñeca der

      return matrix


  def to_visual_frame(self, temp_matrix: np.ndarray,
                      target_w: int, target_h: int) -> np.ndarray:
      normalized = cv2.normalize(temp_matrix, None, 0, 255,
                                  cv2.NORM_MINMAX, cv2.CV_8U)
      colored = cv2.applyColorMap(normalized, cv2.COLORMAP_INFERNO)
      scaled = cv2.resize(colored, (target_w, target_h),
                          interpolation=cv2.INTER_NEAREST)
      return scaled

  def overlay_on_frame(self, rgb_frame: np.ndarray,
                        temp_matrix: np.ndarray,
                        alpha: float = 0.45) -> np.ndarray:
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