"""
Subsamples Okutama-Action frames + labels into OKUTAMA_raw/.

Output structure:
    OKUTAMA_raw/
        train/images/   (*.jpg)
        train/labels/   (*.txt, YOLO format class 0)
        val/images/
        val/labels/

Usage:
    python extract_okutama.py \
        --train  "C:/Users/nicol/Downloads/TrainSetFrames" \
        --test   "C:/Users/nicol/Downloads/TestSetFrames" \
        --output "C:/Users/nicol/Documents/Proyecto-Software-2026/datasets/OKUTAMA_raw" \
        --stride 20
"""

import argparse
import shutil
from pathlib import Path

IMG_W, IMG_H = 1280, 720
LABEL_W, LABEL_H = 3840, 2160

DRONE_TIME_MAP = {
    ("1", "1"): ("Drone1", "Morning"),
    ("1", "2"): ("Drone1", "Noon"),
    ("2", "1"): ("Drone2", "Morning"),
    ("2", "2"): ("Drone2", "Noon"),
}


def seq_frames_dir(seq_id: str, base: Path) -> Path:
    d, t, _ = seq_id.split(".")
    drone, tod = DRONE_TIME_MAP[(d, t)]
    return base / drone / tod / "Extracted-Frames-1280x720" / seq_id


def parse_label_file(path: Path) -> dict[int, list[tuple]]:
    """Return {frame_id: [(x1,y1,x2,y2), ...]} skipping lost detections."""
    detections: dict[int, list] = {}
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) < 7:
                continue
            _, x1, y1, x2, y2, frame_id, lost = parts[:7]
            if int(lost) == 1:
                continue
            fid = int(frame_id)
            detections.setdefault(fid, []).append(
                (int(x1), int(y1), int(x2), int(y2))
            )
    return detections


def to_yolo(x1: int, y1: int, x2: int, y2: int) -> tuple[float, ...] | None:
    """Convert absolute bbox at label resolution to YOLO normalised format."""
    sx = IMG_W / LABEL_W
    sy = IMG_H / LABEL_H
    x1, x2 = x1 * sx, x2 * sx
    y1, y2 = y1 * sy, y2 * sy
    w = x2 - x1
    h = y2 - y1
    if w <= 0 or h <= 0:
        return None
    cx = (x1 + x2) / 2 / IMG_W
    cy = (y1 + y2) / 2 / IMG_H
    w /= IMG_W
    h /= IMG_H
    return (
        max(0.0, min(1.0, cx)),
        max(0.0, min(1.0, cy)),
        max(0.0, min(1.0, w)),
        max(0.0, min(1.0, h)),
    )


def process_split(frames_root: Path, output_split: Path, stride: int) -> int:
    label_dir = frames_root / "Labels" / "SingleActionLabels" / "3840x2160"
    img_out = output_split / "images"
    lbl_out = output_split / "labels"
    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)

    copied = 0
    for label_file in sorted(label_dir.glob("*.txt")):
        seq_id = label_file.stem
        frames_dir = seq_frames_dir(seq_id, frames_root)
        if not frames_dir.exists():
            print(f"  [WARN] frames not found: {frames_dir}")
            continue

        detections = parse_label_file(label_file)
        all_frames = sorted(frames_dir.glob("*.jpg"), key=lambda p: int(p.stem))

        for frame_path in all_frames[::stride]:
            fid = int(frame_path.stem)
            bboxes = detections.get(fid)
            if not bboxes:
                continue

            yolo_lines = []
            for box in bboxes:
                result = to_yolo(*box)
                if result:
                    yolo_lines.append(f"0 {result[0]:.6f} {result[1]:.6f} {result[2]:.6f} {result[3]:.6f}")
            if not yolo_lines:
                continue

            stem = f"{seq_id.replace('.', '_')}_{fid}"
            shutil.copy2(frame_path, img_out / f"{stem}.jpg")
            (lbl_out / f"{stem}.txt").write_text("\n".join(yolo_lines) + "\n")
            copied += 1

    return copied


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train",  required=True, help="Path to TrainSetFrames")
    parser.add_argument("--test",   required=True, help="Path to TestSetFrames")
    parser.add_argument("--output", required=True, help="Output path (OKUTAMA_raw)")
    parser.add_argument("--stride", type=int, default=20, help="Frame sampling stride (default: 20)")
    args = parser.parse_args()

    out = Path(args.output)
    print(f"Stride: every {args.stride} frames")

    print("Processing train...")
    n_train = process_split(Path(args.train), out / "train", args.stride)
    print(f"  → {n_train} frames saved")

    print("Processing test → val...")
    n_val = process_split(Path(args.test), out / "val", args.stride)
    print(f"  → {n_val} frames saved")

    print(f"\nDone. Total: {n_train + n_val} frames in {out}")


if __name__ == "__main__":
    main()
