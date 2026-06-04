import pytest
from modules.detection.fusion import compute_iou, fuse_detections


# ─── compute_iou ────────────────────────────────────────────────────────────

# Verifica que dos bounding boxes que no se tocan devuelvan IoU = 0.0
def test_iou_no_overlap():
    rgb = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    # Thermal ocupa la esquina inferior-derecha, sin tocar el rgb
    thermal_norm = {"x1": 0.5, "y1": 0.5, "x2": 1.0, "y2": 1.0}
    assert compute_iou(rgb, thermal_norm, frame_w=200, frame_h=200) == 0.0


# Verifica que dos bounding boxes idénticos (mismo área exacta) devuelvan IoU = 1.0
def test_iou_perfect_overlap():
    rgb = {"x1": 0, "y1": 0, "x2": 640, "y2": 480}
    thermal_norm = {"x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0}
    iou = compute_iou(rgb, thermal_norm, frame_w=640, frame_h=480)
    assert abs(iou - 1.0) < 1e-6


# Verifica que dos bounding boxes con solapamiento parcial devuelvan un IoU entre 0 y 1
def test_iou_partial_overlap():
    # RGB: [0,0] → [200,200] en frame 640×480
    rgb = {"x1": 0, "y1": 0, "x2": 200, "y2": 200}
    # Thermal normalizado cubre [0.25,0.25] → [0.75,0.75] → en píxeles [160,120] → [480,360]
    thermal_norm = {"x1": 0.25, "y1": 0.25, "x2": 0.75, "y2": 0.75}
    iou = compute_iou(rgb, thermal_norm, frame_w=640, frame_h=480)
    assert 0.0 < iou < 1.0


# Verifica que dos bounding boxes que se tocan en un borde (sin área en común) devuelvan IoU = 0.0
def test_iou_adjacent_boxes_do_not_overlap():
    rgb = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    # Thermal empieza justo donde termina el rgb (x=100)
    thermal_norm = {"x1": 100/640, "y1": 0.0, "x2": 200/640, "y2": 100/480}
    iou = compute_iou(rgb, thermal_norm, frame_w=640, frame_h=480)
    assert iou == 0.0


# ─── fuse_detections ────────────────────────────────────────────────────────

# Verifica que fusionar listas vacías devuelva una lista vacía sin errores
def test_fuse_empty_inputs():
    assert fuse_detections([], []) == []


# Verifica que una detección solo RGB (sin contraparte térmica) quede como confianza "medium"
# y conserve el valor de rgb_confidence con temperature en None
def test_fuse_only_rgb_produces_medium():
    rgb_dets = [{"bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}, "confidence": 0.9}]
    result = fuse_detections(rgb_dets, [])
    assert len(result) == 1
    assert result[0]["source"] == "rgb"
    assert result[0]["confidence"] == "medium"
    assert result[0]["rgb_confidence"] == 0.9
    assert result[0]["temperature"] is None


# Verifica que una detección solo térmica (sin contraparte RGB) quede como confianza "medium"
# y conserve la temperatura máxima del blob con bbox en None
def test_fuse_only_thermal_produces_medium():
    thermal_dets = [
        {"bbox_normalized": {"x1": 0.1, "y1": 0.1, "x2": 0.4, "y2": 0.4}, "max_temp": 36.5}
    ]
    result = fuse_detections([], thermal_dets)
    assert len(result) == 1
    assert result[0]["source"] == "thermal"
    assert result[0]["confidence"] == "medium"
    assert result[0]["temperature"] == 36.5
    assert result[0]["bbox"] is None


# Verifica que cuando RGB y térmica se solapan con IoU alto (> umbral 0.3)
# la detección fusionada resulte con source "fusion" y confianza "high"
def test_fuse_high_iou_produces_fusion_high():
    rgb_dets = [{"bbox": {"x1": 0, "y1": 0, "x2": 320, "y2": 240}, "confidence": 0.85}]
    thermal_dets = [
        {"bbox_normalized": {"x1": 0.0, "y1": 0.0, "x2": 0.5, "y2": 0.5}, "max_temp": 36.0}
    ]
    result = fuse_detections(rgb_dets, thermal_dets, frame_w=640, frame_h=480, iou_threshold=0.3)
    assert len(result) == 1
    assert result[0]["source"] == "fusion"
    assert result[0]["confidence"] == "high"
    assert result[0]["temperature"] == 36.0
    assert result[0]["rgb_confidence"] == 0.85
    assert result[0]["iou"] > 0.3


# Verifica que cuando RGB y térmica están en posiciones muy alejadas (IoU bajo)
# ambas detecciones se emitan por separado con confianza "medium"
def test_fuse_low_iou_both_stay_medium():
    rgb_dets = [{"bbox": {"x1": 0, "y1": 0, "x2": 50, "y2": 50}, "confidence": 0.7}]
    thermal_dets = [
        {"bbox_normalized": {"x1": 0.9, "y1": 0.9, "x2": 1.0, "y2": 1.0}, "max_temp": 35.0}
    ]
    result = fuse_detections(rgb_dets, thermal_dets, frame_w=640, frame_h=480)
    assert len(result) == 2
    sources = {r["source"] for r in result}
    assert "rgb" in sources
    assert "thermal" in sources
    for r in result:
        assert r["confidence"] == "medium"


# Verifica que con dos detecciones RGB y una sola térmica, el algoritmo empareja
# la térmica con la RGB más cercana (mayor IoU) y deja la otra como "medium"
def test_fuse_two_rgb_one_thermal_matched_to_closest():
    rgb_dets = [
        {"bbox": {"x1": 0, "y1": 0, "x2": 320, "y2": 240}, "confidence": 0.9},
        {"bbox": {"x1": 400, "y1": 300, "x2": 500, "y2": 400}, "confidence": 0.6},
    ]
    thermal_dets = [
        {"bbox_normalized": {"x1": 0.0, "y1": 0.0, "x2": 0.5, "y2": 0.5}, "max_temp": 37.0}
    ]
    result = fuse_detections(rgb_dets, thermal_dets, frame_w=640, frame_h=480)
    assert len(result) == 2
    fused = [r for r in result if r["source"] == "fusion"]
    medium_rgb = [r for r in result if r["source"] == "rgb"]
    assert len(fused) == 1
    assert len(medium_rgb) == 1
    assert fused[0]["confidence"] == "high"


# Verifica que toda detección fusionada incluya el campo "timestamp" como entero
# (necesario para ordenar eventos cronológicamente en el frontend)
def test_fuse_result_has_timestamp():
    rgb_dets = [{"bbox": {"x1": 0, "y1": 0, "x2": 100, "y2": 100}, "confidence": 0.8}]
    result = fuse_detections(rgb_dets, [])
    assert "timestamp" in result[0]
    assert isinstance(result[0]["timestamp"], int)
