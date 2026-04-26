"""
Fine-tunes YOLOv8n on VisDrone_person (aerial person detection).

Transfer learning strategy (mirrors IBM AI Engineering Course 3/6):
  - Start from COCO pretrained yolov8n.pt weights
  - Freeze backbone (first 10 layers) so low-level features are preserved
  - Only train neck + detection head on aerial data
  - After initial training, optionally unfreeze all layers for a final pass

Run from project root:
  python backend/training/train.py
"""

from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_YAML = PROJECT_ROOT / "datasets" / "VisDrone_person" / "dataset.yaml"
PRETRAINED_WEIGHTS = PROJECT_ROOT / "backend" / "yolov8n.pt"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "training" / "runs"


def train():
    model = YOLO(str(PRETRAINED_WEIGHTS))

    print("=== Phase 1: frozen backbone (transfer learning) ===")
    model.train(
        data=str(DATASET_YAML),
        epochs=30,
        imgsz=640,
        batch=16,
        freeze=10,           # freeze first 10 layers (backbone)
        lr0=1e-3,
        lrf=0.01,
        optimizer="AdamW",
        project=str(OUTPUT_DIR),
        name="phase1_frozen",
        exist_ok=True,
        verbose=True,
    )

    print("\n=== Phase 2: full fine-tune (all layers unfrozen) ===")
    best_weights = OUTPUT_DIR / "phase1_frozen" / "weights" / "best.pt"
    model2 = YOLO(str(best_weights))

    model2.train(
        data=str(DATASET_YAML),
        epochs=20,
        imgsz=640,
        batch=16,
        freeze=0,            # unfreeze everything
        lr0=1e-4,            # lower LR to avoid destroying phase 1 weights
        lrf=0.01,
        optimizer="AdamW",
        project=str(OUTPUT_DIR),
        name="phase2_full",
        exist_ok=True,
        verbose=True,
    )

    final = OUTPUT_DIR / "phase2_full" / "weights" / "best.pt"
    print(f"\nFine-tuned weights saved to: {final}")


if __name__ == "__main__":
    train()
