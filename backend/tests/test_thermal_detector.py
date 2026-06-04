import numpy as np
import pytest
from modules.detection.thermal_detector import ThermalDetector, HUMAN_TEMP_MIN, HUMAN_TEMP_MAX, MIN_BLOB_SIZE


@pytest.fixture
def detector():
    return ThermalDetector()


# ─── detect ─────────────────────────────────────────────────────────────────

# Verifica que una matriz completamente fría (temperatura ambiente) no genere
# ninguna detección, ya que ningún píxel cae en el rango de temperatura corporal
def test_detect_cold_matrix_returns_empty(detector):
    matrix = np.full((24, 32), 20.0)  # todo frío, sin humanos
    assert detector.detect(matrix) == []


# Verifica que un parche de temperatura corporal (3×4 píxeles) sea detectado
# correctamente: source "thermal", temperatura en rango humano y bbox_normalized presente
def test_detect_single_human_patch(detector):
    matrix = np.full((24, 32), 20.0)
    matrix[5:8, 10:14] = 36.5  # parche 3×4 = 12 px, temperatura corporal
    detections = detector.detect(matrix)
    assert len(detections) == 1
    d = detections[0]
    assert d["source"] == "thermal"
    assert HUMAN_TEMP_MIN <= d["max_temp"] <= HUMAN_TEMP_MAX
    assert d["avg_temp"] <= d["max_temp"]
    assert "bbox_normalized" in d


# Verifica que dos parches de calor separados en la matriz sean detectados
# como dos blobs independientes (dos personas distintas en el área)
def test_detect_two_separate_patches(detector):
    matrix = np.full((24, 32), 20.0)
    matrix[2:5, 2:6] = 35.0    # parche 1: 3×4 = 12 px
    matrix[15:18, 22:26] = 36.0  # parche 2: 3×4 = 12 px, separado
    detections = detector.detect(matrix)
    assert len(detections) == 2


# Verifica que un parche muy pequeño (por debajo de MIN_BLOB_SIZE)
# sea descartado como ruido térmico y no genere detección
def test_detect_patch_below_min_size_ignored(detector):
    matrix = np.full((24, 32), 20.0)
    # 2×2 = 4 píxeles, menor que MIN_BLOB_SIZE=6
    matrix[5:7, 5:7] = 36.0
    assert detector.detect(matrix) == []


# Verifica que un parche con temperatura por encima del máximo humano (ej. fuego, metal caliente)
# no genere detección, ya que queda fuera del rango HUMAN_TEMP_MAX
def test_detect_patch_too_hot_ignored(detector):
    matrix = np.full((24, 32), 20.0)
    matrix[5:8, 10:14] = 50.0  # por encima de HUMAN_TEMP_MAX
    assert detector.detect(matrix) == []


# Verifica que las coordenadas del bounding box normalizado estén siempre
# en el rango [0.0, 1.0] y que x1 < x2, y1 < y2 (bbox válido)
def test_detect_bbox_normalized_coords_valid(detector):
    matrix = np.full((24, 32), 20.0)
    matrix[5:8, 10:14] = 36.0
    detections = detector.detect(matrix)
    assert len(detections) == 1
    bbox = detections[0]["bbox_normalized"]
    assert 0.0 <= bbox["x1"] < bbox["x2"] <= 1.0
    assert 0.0 <= bbox["y1"] < bbox["y2"] <= 1.0
    assert 0.0 <= bbox["cx"] <= 1.0
    assert 0.0 <= bbox["cy"] <= 1.0


# Verifica que el campo "area" esté presente en la detección y sea un entero
# mayor o igual a MIN_BLOB_SIZE (garantía de que el filtro de ruido funcionó)
def test_detect_area_field_present(detector):
    matrix = np.full((24, 32), 20.0)
    matrix[5:8, 10:14] = 36.0
    d = detector.detect(matrix)[0]
    assert isinstance(d["area"], int)
    assert d["area"] >= MIN_BLOB_SIZE


# ─── simulate ───────────────────────────────────────────────────────────────

# Verifica que la simulación genere una matriz con las dimensiones correctas
# del sensor MLX90640: 24 filas × 32 columnas
def test_simulate_returns_correct_shape(detector):
    matrix = detector.simulate()
    assert matrix.shape == (24, 32)


# Verifica que simulate() retorne un ndarray de NumPy (no una lista ni otro tipo)
def test_simulate_returns_numpy_array(detector):
    matrix = detector.simulate()
    assert isinstance(matrix, np.ndarray)


# Verifica que los valores simulados sean físicamente plausibles:
# mínimo cercano al rango ambiente (≥14°C) y máximo sin superar temperatura corporal extrema
def test_simulate_background_in_ambient_range(detector):
    results = [detector.simulate() for _ in range(20)]
    for matrix in results:
        assert matrix.min() >= 14.0
        assert matrix.max() <= 40.0
