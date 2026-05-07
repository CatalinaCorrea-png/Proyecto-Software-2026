"""
Merges SARD + Okutama + COCO subsets into Person_Multisource_v2/.

Doesn't copy any image — generates train.txt / val.txt with absolute image
paths, plus a dataset.yaml for YOLOv8. YOLO finds labels automatically by
swapping '/images/' for '/labels/' in each path, which all three sources
already follow.

Run from project root (after build_coco_subset.py and extract_okutama.py
have populated their respective COCO_raw/ and OKUTAMA_raw/):
  python backend/training/build_dataset_v2.py
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS = PROJECT_ROOT / "datasets"
OUTPUT_DIR = DATASETS / "Person_Multisource_v2"

# (label, source images dir relative to DATASETS, target split)
SOURCES = [
    ("sard_train",    "SARD_raw/train/images",     "train"),
    ("sard_valid",    "SARD_raw/valid/images",     "val"),
    ("sard_test",     "SARD_raw/test/images",      "val"),
    ("okutama_train", "OKUTAMA_raw/train/images",  "train"),
    ("okutama_val",   "OKUTAMA_raw/val/images",    "val"),
    ("coco_train",    "COCO_raw/train/images",     "train"),
    ("coco_val",      "COCO_raw/val/images",       "val"),
]

IMG_EXTS = {".jpg", ".jpeg", ".png"}


def collect_images(rel: str) -> list[Path]:
    src = DATASETS / rel
    if not src.exists():
        print(f"  [WARN] missing: {src}")
        return []
    labels_dir = src.parent / "labels"
    out = []
    for img in sorted(src.iterdir()):
        if img.suffix.lower() not in IMG_EXTS:
            continue
        if not (labels_dir / f"{img.stem}.txt").exists():
            continue
        out.append(img.resolve())
    return out


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    buckets: dict[str, list[Path]] = {"train": [], "val": []}
    for label, rel, split in SOURCES:
        imgs = collect_images(rel)
        buckets[split].extend(imgs)
        print(f"  {label} -> {split}: {len(imgs)}")

    for split in ("train", "val"):
        listing = OUTPUT_DIR / f"{split}.txt"
        listing.write_text(
            "\n".join(p.as_posix() for p in buckets[split]) + "\n"
        )
        print(f"  Wrote {listing} ({len(buckets[split])} entries)")

    yaml_path = OUTPUT_DIR / "dataset.yaml"
    yaml_path.write_text(
        f"""path: {OUTPUT_DIR.as_posix()}
train: train.txt
val: val.txt

nc: 1
names:
  0: person
"""
    )
    print(f"  Wrote {yaml_path}")
    print(f"\nTotal: {len(buckets['train'])} train + {len(buckets['val'])} val")


if __name__ == "__main__":
    main()
