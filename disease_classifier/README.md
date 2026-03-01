# MobileNetV2 Disease Classifier

Multi-class dental / oral disease classifier built with **MobileNetV2** transfer learning on TensorFlow 2.x.

Detects **5 conditions** from intraoral photographs:
| Class | Description |
|---|---|
| Calculus | Mineralised plaque deposits on teeth |
| Mouth Ulcer | Aphthous ulcers / canker sores |
| Tooth Discoloration | Extrinsic or intrinsic staining |
| Caries | Dental cavities / tooth decay |
| Hypodontia | Congenitally missing teeth |

---

## Dataset Format

The pipeline expects a directory with one sub-folder per class, each containing images:

```
dataset_root/
├── Calculus/
│   ├── img001.jpg
│   └── ...
├── Mouth Ulcer/
├── Tooth Discoloration/
├── caries/
└── hypodontia/
```

Supported formats: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff` (case-insensitive).

The default config points to `../Models/Tooth_dataset_augmented` relative to the project root.

---

## Setup

```bash
cd disease_classifier

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **GPU**: Install `tensorflow[and-cuda]` or the appropriate GPU build for your system.

---

## Quick Start

```bash
# 1. Inspect dataset before training
python main.py info

# 2. Train (Phase 1: head training + Phase 2: fine-tuning)
python main.py train

# 3. Evaluate on held-out test set
python main.py evaluate

# 4. Predict on a new image
python main.py predict --image path/to/image.jpg

# 5. Export to SavedModel / H5 / TFLite
python main.py export
```

---

## Commands

### `info` — Dataset Exploration

```bash
python main.py info
```

Prints class distribution, imbalance ratio, and split sizes without touching the model. Run this first to verify your dataset is correct.

### `train` — Two-Phase Training

```bash
python main.py train
python main.py train --config path/to/custom_config.yaml
```

- **Phase 1**: Frozen MobileNetV2 base — trains only the classification head (GAP → BN → Dropout → Dense).
- **Phase 2**: Unfreezes top layers of the base for fine-tuning at a lower learning rate.
- Automatically computes class weights to handle imbalance.
- Saves best checkpoint to `checkpoints/best_model.keras`.
- Training curves saved to `results/training_curves.png`.
- Supports mixed-precision training (set `mixed_precision: true` in config).
- TensorBoard logging enabled by default.

### `evaluate` — Test-Set Evaluation

```bash
python main.py evaluate
```

- Uses the same deterministic split as training (reproducible results).
- Outputs accuracy, precision, recall, F1-score (weighted and per-class).
- Saves confusion matrix (raw counts + normalised) to `results/`.
- Saves classification report to `results/classification_report.txt`.

### `predict` — Single-Image Inference

```bash
python main.py predict --image path/to/image.jpg
```

- Prints predicted class, confidence, and all class probabilities as JSON.
- Generates a Grad-CAM overlay in `results/gradcam_last_prediction.png` (requires OpenCV).

### `export` — Multi-Format Export

```bash
python main.py export
```

| Format | Location | Use Case |
|---|---|---|
| SavedModel | `exported_models/saved_model/` | TF Serving, further conversion |
| Keras H5 | `exported_models/model.h5` | Python inference, fine-tuning |
| TFLite (float16) | `exported_models/model.tflite` | Mobile / edge deployment |

---

## Project Structure

```
disease_classifier/
├── config/
│   └── config.yaml          # All hyper-parameters & paths
├── data/
│   └── dataset.py           # Data loading, splitting, tf.data pipeline
├── models/
│   └── mobilenetv2.py       # Model architecture & freeze/unfreeze
├── training/
│   └── train.py             # Two-phase training loop
├── evaluation/
│   └── evaluate.py          # Test-set evaluation & metrics
├── inference/
│   └── predict.py           # Single-image inference + Grad-CAM
├── export/
│   └── export.py            # Multi-format model export
├── utils/
│   ├── metrics.py           # sklearn metric wrappers + per-class stats
│   ├── visualization.py     # Confusion matrix, curves, Grad-CAM
│   └── seed.py              # Deterministic seeding
├── main.py                  # CLI entry-point
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Architecture

```
Input (224×224×3)
    │
    ▼
MobileNetV2 (ImageNet pre-trained, top removed)
    │  frozen in Phase 1, top layers unfrozen in Phase 2
    ▼
GlobalAveragePooling2D     ← (7×7×1280) → 1280-d vector
    │
    ▼
BatchNormalization         ← stabilises head training
    │
    ▼
Dropout (0.3)              ← regularisation
    │
    ▼
Dense (5, softmax)         ← class probabilities
```

### Training Pipeline

```
[Decode JPEG] → [Resize 224×224] → [Cache]
    │
    ▼  (training only)
[Random Flip] → [Brightness ±50] → [Contrast 0.8–1.2] → [Crop 90% + Resize] → [Clip 0–255]
    │
    ▼
[preprocess_input: [0,255] → [-1,1]] → [Batch 32] → [Prefetch]
```

> ⚠️ **Design note**: Augmentation is applied *before* `preprocess_input` normalisation. Applying brightness/contrast on already-normalised [-1, 1] data would corrupt the distribution.

---

## Configuration Reference (`config/config.yaml`)

| Key | Default | Description |
|---|---|---|
| `dataset_dir` | `../Models/Tooth_dataset_augmented` | Path to dataset root |
| `image_size` | 224 | Input image spatial size |
| `valid_extensions` | `.jpg .jpeg .png .bmp .tiff` | Allowed image formats |
| `batch_size` | 32 | Training batch size |
| `epochs` | 30 | Phase 1 (head training) epochs |
| `learning_rate` | 0.001 | Phase 1 learning rate |
| `fine_tune_epochs` | 15 | Phase 2 (fine-tuning) epochs |
| `fine_tune_lr` | 0.0001 | Phase 2 learning rate |
| `fine_tune_at` | 100 | Unfreeze base from this layer index |
| `dropout_rate` | 0.3 | Dropout before final Dense |
| `validation_split` | 0.15 | Fraction for validation |
| `test_split` | 0.10 | Fraction for test |
| `seed` | 42 | Random seed for reproducibility |
| `early_stopping_patience` | 7 | Epochs without improvement before stopping |
| `reduce_lr_patience` | 3 | Epochs before reducing LR |
| `reduce_lr_factor` | 0.5 | Factor to reduce LR by |
| `mixed_precision` | false | Enable float16 mixed precision |
| `tensorboard` | true | Enable TensorBoard logging |

---

## Performance Tuning Tips

1. **Increase `epochs` / `fine_tune_epochs`** if validation accuracy is still improving when training stops.
2. **Reduce `fine_tune_at`** (e.g. 50) to unfreeze more base layers — helps when the domain is very different from ImageNet.
3. **Enable `mixed_precision: true`** for ~2× speedup on Tensor Core GPUs (A100, V100, T4).
4. **Increase `batch_size`** if GPU memory allows — improves gradient stability.
5. **Monitor TensorBoard** (`tensorboard --logdir logs/tensorboard`) for overfitting detection.
6. **Class weights** are computed automatically — no manual balancing needed.
7. **The dataset already includes offline augmentations** — the on-the-fly pipeline adds further diversity (flips, brightness, contrast, crop).

---

## Design Decisions & Known Caveats

| Decision | Rationale |
|---|---|
| BatchNorm in head | Normalises the 1280-d feature vector from the frozen base — accelerates Phase 1 convergence |
| BatchNorm frozen during fine-tuning | Prevents running mean/variance corruption with small batch sizes — a well-known transfer-learning pitfall |
| Cache before augmentation | Decoded images are cached in memory; augmentation is re-applied fresh each epoch |
| Stratified splits | Preserves class proportions in train/val/test to avoid evaluation bias |
| Float16 TFLite quantisation | ~50% size reduction with negligible accuracy loss — ideal for the Flutter mobile app |
| Grad-CAM drills into base model | The outer model has only 5 layers (Input, MobileNetV2, GAP, BN, Dropout, Dense); Grad-CAM finds conv layers inside the nested MobileNetV2 |

---

## License

This project is provided as-is for research and educational purposes.