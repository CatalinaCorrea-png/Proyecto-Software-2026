"""
Builds a COCO 2017 person-only subset for AeroSearch v2 fine-tuning.

Steps:
  1. Download COCO 2017 instance annotations (~241 MB) if not cached.
  2. Filter images that contain at least one non-crowd 'person' annotation.
  3. Sample N_TRAIN / N_VAL images per split (deterministic seed).
  4. Download those images via their COCO URLs (concurrent).
  5. Convert bboxes to YOLO format (class 0 = person) at original resolution.

Output:
  datasets/COCO_raw/
    train/images/   train/labels/
    val/images/     val/labels/

Run from project root:
  python backend/training/build_coco_subset.py
"""

import json
import random
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import URLError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "COCO_raw"
ANN_CACHE = OUTPUT_DIR / "_annotations_cache"
ANNOTATIONS_URL = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"

PERSON_CATEGORY_ID = 1
N_TRAIN = 5000
N_VAL = 1000
SEED = 42
DOWNLOAD_WORKERS = 16


def ensure_annotations() -> tuple[Path, Path]:
    train_json = ANN_CACHE / "annotations" / "instances_train2017.json"
    val_json = ANN_CACHE / "annotations" / "instances_val2017.json"
    if train_json.exists() and val_json.exists():
        return train_json, val_json

    ANN_CACHE.mkdir(parents=True, exist_ok=True)
    zip_path = ANN_CACHE / "annotations_trainval2017.zip"
    if not zip_path.exists():
        print(f"Downloading COCO annotations (~241 MB) -> {zip_path}")
        urllib.request.urlretrieve(ANNOTATIONS_URL, zip_path)
    print("Extracting annotations...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(ANN_CACHE)
    return train_json, val_json


def select_person_images(json_path: Path, n: int, seed: int) -> tuple[list, dict]:
    print(f"Loading {json_path.name}...")
    with open(json_path) as f:
        coco = json.load(f)

    anns_by_img: dict[int, list] = {}
    for ann in coco["annotations"]:
        if ann["category_id"] == PERSON_CATEGORY_ID and not ann.get("iscrowd", 0):
            anns_by_img.setdefault(ann["image_id"], []).append(ann)

    person_imgs = [img for img in coco["images"] if img["id"] in anns_by_img]
    print(f"  {len(person_imgs)} person images available; sampling {n}")

    rng = random.Random(seed)
    rng.shuffle(person_imgs)
    return person_imgs[:n], anns_by_img


def coco_to_yolo(bbox, img_w, img_h):
    x, y, w, h = bbox
    if w <= 0 or h <= 0:
        return None
    cx = (x + w / 2) / img_w
    cy = (y + h / 2) / img_h
    return (
        max(0.0, min(1.0, cx)),
        max(0.0, min(1.0, cy)),
        max(0.0, min(1.0, w / img_w)),
        max(0.0, min(1.0, h / img_h)),
    )


def write_labels(images, anns_by_img, lbl_dir: Path):
    for img in images:
        stem = Path(img["file_name"]).stem
        lines = []
        for ann in anns_by_img[img["id"]]:
            yolo = coco_to_yolo(ann["bbox"], img["width"], img["height"])
            if yolo:
                lines.append(f"0 {yolo[0]:.6f} {yolo[1]:.6f} {yolo[2]:.6f} {yolo[3]:.6f}")
        if lines:
            (lbl_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n")


def download_one(url: str, target: Path) -> bool:
    if target.exists() and target.stat().st_size > 0:
        return True
    try:
        urllib.request.urlretrieve(url, target)
        return True
    except (URLError, OSError):
        return False


def download_images(images, img_dir: Path, workers: int) -> int:
    img_dir.mkdir(parents=True, exist_ok=True)
    ok = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {
            ex.submit(download_one, img["coco_url"], img_dir / img["file_name"]): img
            for img in images
        }
        for i, fut in enumerate(as_completed(futs), 1):
            if fut.result():
                ok += 1
            if i % 250 == 0:
                print(f"  {i}/{len(images)} ({ok} ok)")
    return ok


def process_split(json_path: Path, n: int, split: str):
    out_split = OUTPUT_DIR / split
    img_dir = out_split / "images"
    lbl_dir = out_split / "labels"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    images, anns = select_person_images(json_path, n, SEED)
    print(f"  Writing labels...")
    write_labels(images, anns, lbl_dir)
    print(f"  Downloading {len(images)} images (workers={DOWNLOAD_WORKERS})...")
    ok = download_images(images, img_dir, DOWNLOAD_WORKERS)

    # Drop labels whose image failed to download
    for lbl in lbl_dir.glob("*.txt"):
        if not (img_dir / f"{lbl.stem}.jpg").exists():
            lbl.unlink()

    print(f"  [{split}] {ok}/{len(images)} images downloaded")
    return ok


if __name__ == "__main__":
    print(f"Output: {OUTPUT_DIR}")
    train_json, val_json = ensure_annotations()
    n_train = process_split(train_json, N_TRAIN, "train")
    n_val = process_split(val_json, N_VAL, "val")
    print(f"\nDone. {n_train} train + {n_val} val")
