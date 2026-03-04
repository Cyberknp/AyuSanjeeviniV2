# Models — Dental Disease Classification Pipeline

This directory contains the complete **data preparation and analysis pipeline** for the AyuSanjeevini dental disease image classifier. It handles everything from raw dataset cleaning through augmentation to produce a balanced, training-ready dataset.

---

## Table of Contents

- [Overview](#overview)
- [Disease Classes](#disease-classes)
- [Directory Structure](#directory-structure)
- [Pipeline Stages](#pipeline-stages)
  - [1. Data Cleaning](#1-data-cleaning)
  - [2. Preprocessing & Analysis](#2-preprocessing--analysis)
  - [3. Augmentation](#3-augmentation)
- [Dataset Details](#dataset-details)
- [Analysis Outputs](#analysis-outputs)
- [Usage](#usage)
  - [Prerequisites](#prerequisites)
  - [Running the Pipeline](#running-the-pipeline)
  - [Environment Variables](#environment-variables)
- [Configuration](#configuration)

---

## Overview

The pipeline takes an **imbalanced raw dental image dataset** and transforms it into a **balanced, augmented dataset** suitable for training a classification model. The original dataset had severe class imbalance (ranging from 219 to 2,017 images per class), which is resolved through intelligent augmentation that applies heavier transformations to underrepresented classes.

**Final output:** 2,017 images per class × 5 classes = **10,085 balanced images** in `Tooth_dataset_augmented/`.

---

## Disease Classes

| Class                  | Description                                              |
| ---------------------- | -------------------------------------------------------- |
| **Calculus**           | Hardened dental plaque (tartar) deposits on teeth        |
| **Caries**            | Tooth decay / cavities caused by bacterial acid erosion  |
| **Hypodontia**        | Congenital absence of one or more teeth                  |
| **Mouth Ulcer**       | Sores or lesions on the oral mucosa                      |
| **Tooth Discoloration** | Abnormal staining or colour changes in teeth           |

---

## Directory Structure

```
Models/
├── README.md                       # This file
├── data_cleaning.py                # Stage 1: Image integrity verification & visual audit
├── preprocessing.py                # Stage 2: Statistical analysis & visualisation
├── augmentations.py                # Stage 3: Augmentation pipeline & class balancing
│
├── Tooth_dataset_augmented/        # Final balanced dataset (output)
│   ├── Calculus/                   #   2,017 images
│   ├── caries/                     #   2,017 images
│   ├── hypodontia/                 #   2,017 images
│   ├── Mouth Ulcer/                #   2,017 images
│   └── Tooth Discoloration/        #   2,017 images
│
└── analysis_output/                # Generated charts and plots
    ├── class_distribution.png
    ├── aspect_ratio_resolution.png
    ├── duplicate_detection.png
    ├── brightness_contrast.png
    ├── augmentation_before_after.png
    ├── sample_aug_Calculus.png
    ├── sample_aug_Mouth_Ulcer.png
    ├── sample_aug_caries.png
    └── sample_aug_hypodontia.png
```

---

## Pipeline Stages

### 1. Data Cleaning

**Script:** `data_cleaning.py`

Ensures dataset integrity before any analysis or training begins.

- **Image Integrity Check** — Opens every image file twice: first pass verifies file structure (`img.verify()`), second pass loads pixel data to detect truncation. Corrupted or unreadable files are automatically deleted.
- **Visual Audit** — Randomly samples images from each class and displays them in a matplotlib grid for manual inspection. Helps catch mislabelled or low-quality images early.

**Supported formats:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`

### 2. Preprocessing & Analysis

**Script:** `preprocessing.py`

Performs four statistical analyses on the dataset, printing console summaries and saving publication-quality plots to `analysis_output/`:

| Analysis                        | What It Reveals                                                          | Output Plot                     |
| ------------------------------- | ------------------------------------------------------------------------ | ------------------------------- |
| **Class Distribution**          | Image count & percentage share per class (bar + pie chart)               | `class_distribution.png`        |
| **Aspect Ratio & Resolution**   | Width/height distributions, aspect ratio spread across classes           | `aspect_ratio_resolution.png`   |
| **Duplicate Detection (MD5)**   | Identifies identical images within and across classes via file hashing   | `duplicate_detection.png`       |
| **Brightness & Contrast**       | Per-class brightness/contrast histograms, scatter plots, and box plots   | `brightness_contrast.png`       |

### 3. Augmentation

**Script:** `augmentations.py`

Balances the dataset by augmenting underrepresented classes up to a target count (defaults to the size of the largest class: **2,017**).

#### Augmentation Intensity Tiers

Classes receive augmentation strength proportional to how underrepresented they are:

| Tier       | Condition                    | Augmentation Strategy                                                                                                     |
| ---------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Heavy**  | < 40% of target count        | Full pipeline — flips, rotation, translation, zoom, brightness/contrast shifts, sharpening, blur, noise, gamma correction |
| **Mild**   | 40–90% of target count       | Lighter pipeline — flips, moderate rotation, brightness adjustments, slight blur                                          |
| **Copy**   | ≥ 90% of target count        | Originals copied as-is (already well-represented)                                                                         |

#### Original Class Distribution (Before Augmentation)

| Class                | Original Count | Share   | Augmentation Tier |
| -------------------- | -------------- | ------- | ----------------- |
| Tooth Discoloration  | 2,017          | 40.0%   | Copy (target)     |
| Calculus             | 1,296          | 25.7%   | Mild              |
| Hypodontia           | 1,251          | 24.8%   | Mild              |
| Mouth Ulcer          | 265            | 5.2%    | Heavy             |
| Caries               | 219            | 4.3%    | Heavy             |

#### Available Augmentation Operations

| Operation                      | Description                                        |
| ------------------------------ | -------------------------------------------------- |
| `aug_horizontal_flip`          | Mirror image left-to-right                         |
| `aug_vertical_flip`            | Mirror image top-to-bottom                         |
| `aug_rotation`                 | Random rotation                                    |
| `aug_brightness`               | Random brightness adjustment                       |
| `aug_contrast`                 | Random contrast adjustment                         |
| `aug_brightness_contrast_stretch` | Combined brightness + contrast stretching       |
| `aug_saturation`               | Random saturation shift                            |
| `aug_sharpness`                | Sharpness enhancement                              |
| `aug_gaussian_blur`            | Apply Gaussian blur                                |
| `aug_gaussian_noise`           | Add random Gaussian noise                          |
| `aug_random_crop`              | Random crop and resize                             |
| `aug_gamma_correction`         | Apply gamma correction                             |

---

## Dataset Details

| Property                | Value                                              |
| ----------------------- | -------------------------------------------------- |
| **Total classes**       | 5                                                  |
| **Images per class**    | 2,017 (after augmentation)                         |
| **Total images**        | 10,085                                             |
| **Original total**      | 5,048                                              |
| **Image format**        | JPEG (augmented output at quality 95)              |
| **Supported inputs**    | PNG, JPG, JPEG, BMP, TIFF                          |

---

## Analysis Outputs

All plots are saved to `analysis_output/` at 150 DPI. These include:

- **`class_distribution.png`** — Bar chart + pie chart showing image counts and percentage share per class.
- **`aspect_ratio_resolution.png`** — Distribution of image widths, heights, and aspect ratios across all classes.
- **`duplicate_detection.png`** — Grouped bar chart of unique vs. duplicate images per class, with overall pie chart.
- **`brightness_contrast.png`** — Four-panel plot: brightness histogram, contrast histogram, brightness-vs-contrast scatter, and brightness box plot per class.
- **`augmentation_before_after.png`** — Side-by-side class distribution comparison before and after augmentation.
- **`sample_aug_*.png`** — Visual samples of augmented images for individual classes.

---

## Usage

### Prerequisites

- **Python 3.10+**
- Required packages:

```
numpy
matplotlib
Pillow
```

### Running the Pipeline

Run the scripts **in order** from the `Models/` directory:

**Step 1 — Clean the dataset** (remove corrupted images):

```sh
python data_cleaning.py
```

**Step 2 — Analyse the dataset** (generate distribution plots and statistics):

```sh
python preprocessing.py
```

**Step 3 — Augment and balance** (produce `Tooth_dataset_augmented/`):

```sh
python augmentations.py
```

### Environment Variables

| Variable                     | Purpose                                           | Default                          |
| ---------------------------- | ------------------------------------------------- | -------------------------------- |
| `TOOTH_DATASET_PATH`         | Override the path to the raw source dataset        | Auto-detected from script directory |
| `TOOTH_DATASET_OUTPUT_PATH`  | Override the path for augmented output             | `<dataset_path>_augmented`       |

Example:

```sh
export TOOTH_DATASET_PATH="/path/to/your/Tooth dataset"
python augmentations.py
```

---

## Configuration

Key constants in `augmentations.py` that can be tuned:

| Constant            | Default   | Description                                                       |
| ------------------- | --------- | ----------------------------------------------------------------- |
| `TARGET_COUNT`      | `None`    | Target images per class. `None` = auto-detect from largest class. |
| `HEAVY_THRESHOLD`   | `0.40`    | Classes below 40% of target get heavy augmentation.               |
| `MILD_THRESHOLD`    | `0.90`    | Classes between 40–90% of target get mild augmentation.           |
| `SAVE_FORMAT`       | `"JPEG"`  | Output image format.                                              |
| `SAVE_QUALITY`      | `95`      | JPEG compression quality (1–100).                                 |

Key constants in `data_cleaning.py`:

| Constant              | Default | Description                                      |
| --------------------- | ------- | ------------------------------------------------ |
| `NUM_IMAGES_PER_CLASS` | `5`    | Number of images sampled per class for visual audit. |