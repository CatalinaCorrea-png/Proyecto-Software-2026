# Fine-Tuning Log — YOLOv8n Aerial Person Detection

## Context

The base model (`yolov8n.pt`) is pre-trained on COCO, which contains mostly ground-level,
front-facing images of people. Deployed on a drone, it partially detected body parts and
failed to reliably detect people from a top-down perspective.

**Goal:** fine-tune YOLOv8n to detect people from aerial/drone viewpoints.

---

## Dataset

**Source:** VisDrone2019-DET (Task 1: Object Detection in Images)  
**Download:** https://github.com/VisDrone/VisDrone-Dataset

| Split | Original images | After filtering (person only) |
|---|---|---|
| Train | 6,471 | 5,684 |
| Val | 548 | 531 |

VisDrone has 10 object classes. We kept only:
- Class 1: `pedestrian`
- Class 2: `people`

Both mapped to YOLO class `0` (person). Images with zero person annotations were discarded.

Conversion script: `backend/training/convert_visdrone.py`

---

## Model & Strategy

**Base weights:** `yolov8n.pt` (YOLOv8 Nano, COCO pretrained, 3M parameters)  
**Framework:** Ultralytics 8.4.41  
**Hardware:** NVIDIA GeForce RTX 3060 Ti (8 GB VRAM)  
**Training time:** ~37 min (Phase 1) + ~26 min (Phase 2)

### Transfer Learning Strategy

Two-phase approach (mirrors IBM AI Engineering Course 3/6 transfer learning):

| | Phase 1 | Phase 2 |
|---|---|---|
| **Frozen layers** | First 10 (backbone) | None |
| **Trainable** | Neck + detection head | All layers |
| **Optimizer** | AdamW | AdamW |
| **Learning rate** | 1e-3 | 1e-4 (lower to preserve Phase 1 weights) |
| **Epochs** | 30 | 20 |
| **Batch size** | 16 | 16 |
| **Image size** | 640×640 | 640×640 |

Rationale: freezing the backbone in Phase 1 preserves low-level feature detectors learned
from COCO (edges, textures) while adapting the neck and head to the aerial domain.
Phase 2 then allows the backbone to also adjust with a conservative learning rate.

---

## Phase 1 Results (frozen backbone, 30 epochs)

| Epoch | mAP50 | mAP50-95 | Precision | Recall | box_loss | cls_loss |
|---|---|---|---|---|---|---|
| 1 | 0.197 | 0.062 | 0.355 | 0.242 | 3.085 | 2.143 |
| 5 | 0.276 | 0.092 | 0.447 | 0.298 | 2.883 | 1.733 |
| 10 | 0.315 | 0.108 | 0.476 | 0.324 | 2.781 | 1.611 |
| 15 | 0.322 | 0.111 | 0.480 | 0.325 | 2.737 | 1.553 |
| 20 | 0.339 | 0.119 | 0.485 | 0.339 | 2.691 | 1.518 |
| 25 | 0.342 | 0.121 | 0.495 | 0.338 | 2.565 | 1.452 |
| **30** | **0.349** | **0.124** | **0.501** | **0.346** | **2.532** | **1.425** |

Best checkpoint (used as Phase 2 starting point):  
`backend/training/runs/phase1_frozen/weights/best.pt` — mAP50: **0.349**, mAP50-95: **0.125**

---

## Phase 2 Results (all layers unfrozen, 20 epochs)

| Epoch | mAP50 | mAP50-95 | Precision | Recall | box_loss | cls_loss |
|---|---|---|---|---|---|---|
| 1 | 0.227 | 0.072 | 0.378 | 0.258 | 2.789 | 1.634 |
| 2 | 0.355 | 0.126 | 0.540 | 0.343 | 2.666 | 1.524 |
| 5 | 0.388 | 0.140 | 0.538 | 0.375 | 2.587 | 1.450 |
| 10 | 0.402 | 0.144 | 0.545 | 0.381 | 2.530 | 1.384 |
| 15 | 0.405 | 0.149 | 0.560 | 0.383 | 2.419 | 1.331 |
| **20** | **0.409** | **0.152** | **0.557** | **0.388** | **2.393** | **1.313** |

Best checkpoint (deployed in backend):  
`backend/training/runs/phase2_full/weights/best.pt` — mAP50: **0.410**, mAP50-95: **0.152**

---

## Summary

| Model | mAP50 | mAP50-95 | Notes |
|---|---|---|---|
| YOLOv8n (COCO base) | ~0.00 | ~0.00 | No aerial training data |
| After Phase 1 | 0.349 | 0.125 | Backbone frozen |
| **After Phase 2** | **0.410** | **0.152** | **Deployed** |

The mAP50-95 being relatively low (0.152) is expected: VisDrone images contain very small
person instances (sometimes 10×20 px), making tight bounding box IoU thresholds hard to satisfy.
mAP50 is the more meaningful metric for this use case.

The model was still improving at epoch 20 of Phase 2 — additional epochs would likely yield
further gains.

---

## v1 Deployment (superseded — see v2 below)

v1 was deployed as `backend/yolov8n_aerial.pt` together with `yolov8n.pt` (COCO base)
under an altitude-based switch in `yolo_detector.py`:
altitude < 15 m → base (conf 0.40); altitude ≥ 15 m → aerial (conf 0.25).

The dual-model setup was retired in v2 — see below.

---

# v2 Re-train — Multi-Source, Orientation-Aware

## Motivation

v1 was tuned on VisDrone (60–80 m altitudes). The drone never flies that high, and v1
struggled below 30 m. Test outputs also showed a **total miss on the upside-down swimmer**
(`testing_images/swimming_person.jpg`) and weak field-with-people coverage — both due to
training data being limited to a single high-altitude dataset with no vertical-flip
augmentation.

**Goal:** a single model targeting **20–30 m altitude** with detection across orientations
(front, back, sides, above, upside-down), replacing the dual-model altitude switch entirely.

---

## Dataset — `Person_Multisource_v2`

Three sources merged, all converted to YOLO class 0 (person):

| Source | Train | Val | Notes |
|---|---|---|---|
| **SARD** (Roboflow) | 4,041 | 1,144 + 570 (test→val) | Drone SAR, people in grass/woods. Already in YOLO format. |
| **Okutama-Action** | 2,751 | 716 | UAV at 10–45 m, includes lying-down poses. Frames subsampled at stride=20. |
| **COCO 2017 (person)** | 4,999 | 1,000 | Filtered to images with non-crowd person annotations. Front/back/side ground-level coverage. |
| **Total** | **11,791** | **3,430** | |

Build scripts:
- `backend/training/extract_okutama.py` — subsamples + converts Okutama labels (3840×2160 → 1280×720, YOLO format)
- `backend/training/build_coco_subset.py` — downloads COCO annotations, filters person images, downloads sampled subset
- `backend/training/build_dataset_v2.py` — merges all three into `train.txt`/`val.txt` with absolute paths (no file copy, saves disk)

---

## Training Recipe

Same two-phase shape as v1, with **two augmentation additions**:

| Hyperparameter | Phase 1 | Phase 2 |
|---|---|---|
| Frozen layers | 10 (backbone) | 0 |
| Optimizer | AdamW | AdamW |
| Learning rate | 1e-3 | 1e-4 |
| Epochs | 30 | 20 |
| Batch size | 16 | 16 |
| Image size | 640×640 | 640×640 |
| **`flipud=0.5`** | ✓ | ✓ |
| **`degrees=45`** | ✓ | ✓ |

`flipud=0.5` was the single most important change — it directly addresses the upside-down
swimmer miss. `degrees=45` adds arbitrary-orientation coverage. Other YOLOv8 augmentation
defaults (HSV jitter, mosaic, fliplr, scale, translate) were preserved.

**Base weights:** `yolov8n.pt` (COCO pretrained), NOT v1's `yolov8n_aerial.pt`.

**Hardware:** NVIDIA GeForce RTX 3060 Ti  
**Training time:** ~42 min (Phase 1) + ~33 min (Phase 2) = ~75 min total

---

## v2 Phase 1 Results (frozen backbone, 30 epochs)

| Epoch | mAP50 | mAP50-95 | Precision | Recall |
|---|---|---|---|---|
| 1  | 0.488 | 0.183 | 0.572 | 0.477 |
| 5  | 0.577 | 0.236 | 0.657 | 0.552 |
| 10 | 0.624 | 0.246 | 0.686 | 0.583 |
| 15 | 0.653 | 0.275 | 0.727 | 0.588 |
| 20 | 0.671 | 0.292 | 0.739 | 0.607 |
| 25 | 0.689 | 0.306 | 0.761 | 0.621 |
| **30** | **0.697** | **0.314** | **0.771** | **0.630** |

---

## v2 Phase 2 Results (all unfrozen, 20 epochs)

| Epoch | mAP50 | mAP50-95 | Precision | Recall |
|---|---|---|---|---|
| 1  | 0.490 | 0.160 | 0.636 | 0.477 |
| 2  | 0.664 | 0.280 | 0.722 | 0.600 |
| 5  | 0.700 | 0.318 | 0.770 | 0.627 |
| 10 | 0.710 | 0.336 | 0.785 | 0.632 |
| 15 | 0.719 | 0.349 | 0.784 | 0.642 |
| **20** | **0.720** | **0.355** | **0.784** | **0.643** |

Best checkpoint (deployed): `backend/training/runs/v2_phase2_full/weights/best.pt`,
copied to `backend/yolov8n_tuned_v2.pt`.

---

## v1 vs v2 — Headline Comparison

| Metric | v1 (VisDrone) | v2 (multi-source) | Δ |
|---|---|---|---|
| mAP50 | 0.410 | **0.720** | **+76%** |
| mAP50-95 | 0.152 | **0.355** | **+134%** |

---

## Visual Validation (`testing_images/`)

Side-by-side base vs v2 comparison at conf=0.25:

| Image | Base (COCO) | v2 | Verdict |
|---|---|---|---|
| `swimming_person.jpg` (upside-down swimmer) | 52% | **54%** | v1 missed entirely → v2 detects |
| `field_people_and_dog.jpg` (aerial, partly occluded in grass) | **0% (miss)** | **30%** | Major improvement on the SAR-relevant case |
| `beach_people.jpg` (group) | 30% + 31% | 33% + 43% | Higher confidence |
| `beach_person_alone.jpg` (sunset, ground level) | 70% | 49% | Regression — acceptable trade-off (ground-level isn't the SAR case) |

The training mAP50 of 0.72 doesn't fully translate to test images (which are out-of-distribution
web photos, not SARD/Okutama/COCO). Real-world confidences land in the 30–55% range, which
informs the deployment threshold.

---

## v2 Deployment

`backend/modules/detection/yolo_detector.py` now loads **a single model**, with no altitude
switch. Loading priority:

1. `backend/yolov8n_tuned_v2.pt` (preferred)
2. `backend/yolov8n.pt` (fallback if v2 weights missing)

Single confidence threshold: **`CONFIDENCE_THRESHOLD = 0.25`**, chosen to cover the lowest
detected case in the visual validation (field at 30%) without opening the door to excessive
false positives.

`yolov8n_aerial.pt` (v1) remains in the repo as an archive but is no longer loaded.

---

## Potential Next Steps

- **Longer Phase 2 training:** Phase 2 converged with lr at 5.95e-6 — there's likely no more
  to extract from this recipe, but a fresh phase with restart-style LR could push mAP50 higher.
- **Calibrate confidence:** test confidences (30–55%) suggest the model is under-confident
  on real-world data. Temperature scaling on the val set could raise confidence without
  changing rankings.
- **Larger model:** swap YOLOv8n → YOLOv8s for better accuracy if inference latency budget
  allows.
- **Custom drone footage:** add labeled images from the actual hardware (ESP32-CAM at the
  target 20–30 m altitude) to close the train/test domain gap.
