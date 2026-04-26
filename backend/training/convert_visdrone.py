"""
Converts VisDrone2019-DET annotations to YOLO format, keeping only
pedestrian (class 1) and people (class 2), mapped to YOLO class 0 (person).

VisDrone format per line:
  x_left, y_top, width, height, score, category, truncation, occlusion

YOLO format per line:
  class_id x_center y_center width height  (all normalized 0-1)

Output structure:
  datasets/VisDrone_person/
    images/train/   images/val/
    labels/train/   labels/val/
    dataset.yaml
"""

import os
import shutil
from pathlib import Path
from PIL import Image

PERSON_CLASSES = {1, 2}  # pedestrian, people

SPLITS = {
    "train": (
        Path("datasets/VisDrone2019-DET-train"),
        "train",
    ),
    "val": (
        Path("datasets/VisDrone2019-DET-val"),
        "val",
    ),
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "VisDrone_person"


def convert_split(src_dir: Path, split: str):
    img_out = OUTPUT_DIR / "images" / split
    lbl_out = OUTPUT_DIR / "labels" / split
    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)

    ann_dir = src_dir / "annotations"
    img_dir = src_dir / "images"

    skipped = 0
    converted = 0

    for ann_file in sorted(ann_dir.glob("*.txt")):
        stem = ann_file.stem
        img_file = img_dir / f"{stem}.jpg"

        if not img_file.exists():
            skipped += 1
            continue

        img_w, img_h = Image.open(img_file).size

        yolo_lines = []
        with open(ann_file) as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < 6:
                    continue
                x, y, w, h, score, cat = (int(p) for p in parts[:6])

                if score == 0 or cat not in PERSON_CLASSES:
                    continue
                if w <= 0 or h <= 0:
                    continue

                x_c = (x + w / 2) / img_w
                y_c = (y + h / 2) / img_h
                w_n = w / img_w
                h_n = h / img_h

                # clamp to [0, 1]
                x_c = max(0.0, min(1.0, x_c))
                y_c = max(0.0, min(1.0, y_c))
                w_n = max(0.0, min(1.0, w_n))
                h_n = max(0.0, min(1.0, h_n))

                yolo_lines.append(f"0 {x_c:.6f} {y_c:.6f} {w_n:.6f} {h_n:.6f}")

        if not yolo_lines:
            skipped += 1
            continue

        shutil.copy2(img_file, img_out / img_file.name)
        with open(lbl_out / f"{stem}.txt", "w") as f:
            f.write("\n".join(yolo_lines))
        converted += 1

    print(f"  [{split}] converted: {converted}, skipped (no persons): {skipped}")


def write_yaml():
    yaml_path = OUTPUT_DIR / "dataset.yaml"
    content = f"""path: {OUTPUT_DIR.as_posix()}
train: images/train
val: images/val

nc: 1
names:
  0: person
"""
    yaml_path.write_text(content)
    print(f"  dataset.yaml written to {yaml_path}")


if __name__ == "__main__":
    print("Converting VisDrone -> YOLO (person only)...")
    for split_name, (src, out_split) in SPLITS.items():
        src_abs = PROJECT_ROOT / src
        print(f"\nProcessing {split_name} from {src_abs}")
        convert_split(src_abs, out_split)
    write_yaml()
    print("\nDone.")
