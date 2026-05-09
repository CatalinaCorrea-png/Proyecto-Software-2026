"""
Two-phase YOLOv8n fine-tune for AeroSearch v2.

Differences vs v1 (train.py):
  - Multi-source dataset (SARD + Okutama + COCO person subset)
  - flipud=0.5  -> vertical flip aug, fixes upside-down miss (swimmer case)
  - degrees=45  -> arbitrary-orientation rotation aug

Run from project root (after build_dataset_v2.py):
  python backend/training/train_v2.py
"""

from pathlib import Path
import torch
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_YAML = PROJECT_ROOT / "datasets" / "Person_Multisource_v2" / "dataset.yaml"
PRETRAINED_WEIGHTS = PROJECT_ROOT / "backend" / "yolov8n.pt"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "training" / "runs"

AUG = dict(
    flipud=0.5,
    degrees=45.0,
    # YOLOv8 defaults kept for: hsv_h/s/v, fliplr, scale, translate, mosaic
)


def train():
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA not available. Install a CUDA build of torch or run on the GPU machine."
        )
    device = 0
    print(f"GPU: {torch.cuda.get_device_name(device)} | CUDA {torch.version.cuda}")

    model = YOLO(str(PRETRAINED_WEIGHTS))

    print("=== Phase 1: frozen backbone (transfer learning) ===")
    model.train(
        data=str(DATASET_YAML),
        epochs=30,
        imgsz=640,
        batch=16,
        freeze=10,
        lr0=1e-3,
        lrf=0.01,
        optimizer="AdamW",
        device=device,
        project=str(OUTPUT_DIR),
        name="v2_phase1_frozen",
        exist_ok=True,
        verbose=True,
        **AUG,
    )

    print("\n=== Phase 2: full fine-tune (all layers unfrozen) ===")
    best_phase1 = OUTPUT_DIR / "v2_phase1_frozen" / "weights" / "best.pt"
    model2 = YOLO(str(best_phase1))

    model2.train(
        data=str(DATASET_YAML),
        epochs=20,
        imgsz=640,
        batch=16,
        freeze=0,
        lr0=1e-4,
        lrf=0.01,
        optimizer="AdamW",
        device=device,
        project=str(OUTPUT_DIR),
        name="v2_phase2_full",
        exist_ok=True,
        verbose=True,
        **AUG,
    )

    final = OUTPUT_DIR / "v2_phase2_full" / "weights" / "best.pt"
    print(f"\nFine-tuned weights saved to: {final}")
    print("Copy to backend/yolov8n_tuned_v2.pt when validation looks good.")


if __name__ == "__main__":
    train()
