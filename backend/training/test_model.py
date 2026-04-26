"""
Test the fine-tuned aerial detection model on images.

Usage:
  # Single image
  python backend/training/test_model.py ruta/a/imagen.jpg

  # Folder of images
  python backend/training/test_model.py ruta/a/carpeta/

  # Compare fine-tuned vs base model side by side
  python backend/training/test_model.py ruta/a/imagen.jpg --compare

Results are saved to backend/training/test_output/
"""

import sys
import argparse
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

BACKEND = Path(__file__).resolve().parents[1]
FINETUNED = BACKEND / "yolov8n_aerial.pt"
BASE      = BACKEND / "yolov8n.pt"
OUTPUT    = Path(__file__).resolve().parent / "test_output"

SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def draw_detections(img: np.ndarray, results, label_prefix: str = "") -> np.ndarray:
    out = img.copy()
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])
            color = (0, 200, 0) if conf >= 0.5 else (0, 140, 255)
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            text = f"{label_prefix}persona {conf:.0%}"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(out, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
            cv2.putText(out, text, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    return out


def run_single(model: YOLO, img_path: Path, conf: float) -> tuple[np.ndarray, int]:
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"  No se pudo leer: {img_path}")
        return None, 0
    results = model(img, conf=conf, classes=[0], verbose=False)
    n = sum(len(r.boxes) for r in results)
    return draw_detections(img, results), n


def process(img_path: Path, model_ft: YOLO, model_base: YOLO | None, conf: float):
    print(f"\n{img_path.name}")

    annotated_ft, n_ft = run_single(model_ft, img_path, conf)
    if annotated_ft is None:
        return
    print(f"  fine-tuned  → {n_ft} persona(s) detectada(s)")

    OUTPUT.mkdir(exist_ok=True)

    if model_base is not None:
        annotated_base, n_base = run_single(model_base, img_path, conf)
        print(f"  base (COCO) → {n_base} persona(s) detectada(s)")

        # stack side by side with labels
        h = max(annotated_ft.shape[0], annotated_base.shape[0])
        def pad(img, h):
            if img.shape[0] < h:
                img = cv2.copyMakeBorder(img, 0, h - img.shape[0], 0, 0,
                                         cv2.BORDER_CONSTANT, value=(30, 30, 30))
            return img
        left  = pad(annotated_base, h)
        right = pad(annotated_ft, h)

        for panel, title in [(left, "BASE (COCO)"), (right, "FINE-TUNED (aerial)")]:
            cv2.rectangle(panel, (0, 0), (panel.shape[1], 28), (30, 30, 30), -1)
            cv2.putText(panel, title, (8, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        combined = np.hstack([left, right])
        out_path = OUTPUT / f"{img_path.stem}_compare.jpg"
        cv2.imwrite(str(out_path), combined)
    else:
        out_path = OUTPUT / f"{img_path.stem}_detected.jpg"
        cv2.imwrite(str(out_path), annotated_ft)

    print(f"  guardado en: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="imagen o carpeta")
    parser.add_argument("--compare", action="store_true",
                        help="comparar fine-tuned vs modelo base lado a lado")
    parser.add_argument("--conf", type=float, default=0.25,
                        help="umbral de confianza (default: 0.25)")
    args = parser.parse_args()

    if not FINETUNED.exists():
        print(f"No se encontraron pesos fine-tuneados en {FINETUNED}")
        sys.exit(1)

    print(f"Cargando modelo fine-tuneado: {FINETUNED.name}")
    model_ft = YOLO(str(FINETUNED))

    model_base = None
    if args.compare:
        base_path = BASE if BASE.exists() else "yolov8n.pt"
        print(f"Cargando modelo base: {base_path}")
        model_base = YOLO(str(base_path))

    input_path = Path(args.input)
    if input_path.is_dir():
        images = [p for p in sorted(input_path.iterdir()) if p.suffix.lower() in SUPPORTED]
        if not images:
            print("No se encontraron imágenes en la carpeta.")
            sys.exit(1)
        print(f"\n{len(images)} imagen(s) encontrada(s)")
        for img in images:
            process(img, model_ft, model_base, args.conf)
    elif input_path.is_file():
        process(input_path, model_ft, model_base, args.conf)
    else:
        print(f"No existe: {input_path}")
        sys.exit(1)

    print(f"\nResultados en: {OUTPUT}/")


if __name__ == "__main__":
    main()
