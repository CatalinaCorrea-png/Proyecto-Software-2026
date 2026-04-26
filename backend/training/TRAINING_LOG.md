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

## Deployment

The fine-tuned weights are loaded automatically by `backend/modules/detection/yolo_detector.py`
if `backend/training/runs/phase2_full/weights/best.pt` exists. Otherwise it falls back to
the original `yolov8n.pt`.

Confidence threshold was lowered from **0.40 → 0.25** to account for the lower confidence
scores typical in aerial small-object detection.

---

## Potential Next Steps

- **More epochs:** Phase 2 loss was still decreasing; 20 more epochs on Phase 2 would likely
  push mAP50 past 0.45.
- **Larger model:** swap YOLOv8n → YOLOv8s for better accuracy at a modest speed cost.
- **Tile inference:** split high-resolution frames into overlapping tiles before inference,
  then merge results — standard technique for small object detection.
- **SAHI (Slicing Aided Hyper Inference):** library built on top of Ultralytics that
  automates tile inference, specifically designed for drone/satellite imagery.
- **Custom drone footage:** collect and label images from your own drone to supplement
  VisDrone with data from your specific altitude and camera setup.
