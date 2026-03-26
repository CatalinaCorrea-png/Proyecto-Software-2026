import time
import random

def compute_iou(bbox_rgb: dict, bbox_thermal_norm: dict, frame_w: int, frame_h: int) -> float:
    """
    Calcula Intersection over Union entre detección RGB y térmica.
    
    IoU = área de intersección / área de unión
    
    IoU = 0.0 → no se solapan para nada
    IoU = 1.0 → son exactamente iguales
    Umbral típico: 0.3 → hay suficiente solapamiento para confirmar
    """
    # Convertir bbox térmica normalizada a píxeles del frame RGB
    tx1 = bbox_thermal_norm["x1"] * frame_w
    ty1 = bbox_thermal_norm["y1"] * frame_h
    tx2 = bbox_thermal_norm["x2"] * frame_w
    ty2 = bbox_thermal_norm["y2"] * frame_h

    rx1, ry1 = bbox_rgb["x1"], bbox_rgb["y1"]
    rx2, ry2 = bbox_rgb["x2"], bbox_rgb["y2"]

    # Intersección
    ix1 = max(rx1, tx1)
    iy1 = max(ry1, ty1)
    ix2 = min(rx2, tx2)
    iy2 = min(ry2, ty2)

    if ix2 < ix1 or iy2 < iy1:
        return 0.0  # no hay intersección

    intersection = (ix2 - ix1) * (iy2 - iy1)
    area_rgb = (rx2 - rx1) * (ry2 - ry1)
    area_thermal = (tx2 - tx1) * (ty2 - ty1)
    union = area_rgb + area_thermal - intersection

    return intersection / union if union > 0 else 0.0


def fuse_detections(
    rgb_detections: list[dict],
    thermal_detections: list[dict],
    frame_w: int = 640,
    frame_h: int = 480,
    iou_threshold: float = 0.3
) -> list[dict]:
    """
    Combina detecciones RGB y térmicas.
    
    Reglas de confianza:
    - Ambas coinciden (IoU > umbral) → HIGH
    - Solo térmica                   → MEDIUM (puede ser animal u objeto caliente)
    - Solo RGB                       → MEDIUM (puede ser foto, maniquí)
    - Ninguna                        → nada
    """
    fused = []
    thermal_matched = set()

    # Buscar pares RGB + Thermal que se solapen
    for rgb_det in rgb_detections:
        best_iou = 0.0
        best_thermal = None
        best_idx = -1

        for idx, thermal_det in enumerate(thermal_detections):
            iou = compute_iou(rgb_det["bbox"], thermal_det["bbox_normalized"], frame_w, frame_h)
            if iou > best_iou:
                best_iou = iou
                best_thermal = thermal_det
                best_idx = idx

        if best_iou >= iou_threshold and best_thermal is not None:
            # ✅ FUSIÓN: ambas cámaras confirman
            thermal_matched.add(best_idx)
            fused.append({
                "source": "fusion",
                "confidence": "high",
                "rgb_confidence": rgb_det["confidence"],
                "temperature": best_thermal["max_temp"],
                "iou": round(best_iou, 3),
                "bbox": rgb_det["bbox"],
                "timestamp": int(time.time() * 1000)
            })
        else:
            # Solo RGB
            fused.append({
                "source": "rgb",
                "confidence": "medium",
                "rgb_confidence": rgb_det["confidence"],
                "temperature": None,
                "iou": 0.0,
                "bbox": rgb_det["bbox"],
                "timestamp": int(time.time() * 1000)
            })

    # Térmicas sin match con RGB
    for idx, thermal_det in enumerate(thermal_detections):
        if idx not in thermal_matched:
            fused.append({
                "source": "thermal",
                "confidence": "medium",
                "rgb_confidence": None,
                "temperature": thermal_det["max_temp"],
                "iou": 0.0,
                "bbox": None,
                "timestamp": int(time.time() * 1000)
            })

    return fused