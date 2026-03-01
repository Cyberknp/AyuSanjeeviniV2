"""Data loading, splitting, augmentation and tf.data pipeline construction.

This module provides the full data pipeline for training, validation, and
test datasets.  It handles:

* **Class discovery** — auto-detects class labels from sub-folder names.
* **File collection** — gathers image paths with extension filtering and
  per-class counts for imbalance analysis.
* **Stratified splitting** — train / val / test with sklearn's stratified
  split so class ratios are preserved.
* **Class-weight computation** — inverse-frequency weighting to counter
  dataset imbalance.
* **tf.data pipeline** — efficient I/O with parallel reads, on-the-fly
  augmentation, batching, caching, and prefetching.

.. note::
    Augmentation is applied **before** MobileNetV2 ``preprocess_input``
    (which maps [0, 255] → [-1, 1]).  Applying brightness / contrast
    adjustments after normalisation would corrupt the input distribution.

Typical usage::

    class_names = discover_classes(dataset_dir)
    paths, labels = collect_file_paths(dataset_dir, class_names)
    splits = split_dataset(paths, labels)
    train_ds = build_dataset(*splits["train"], augment=True, shuffle=True)
"""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import tensorflow as tf

logger = logging.getLogger(__name__)

VALID_EXTENSIONS_DEFAULT = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_classes(dataset_dir: Path) -> list[str]:
    """Return sorted list of class names (subdirectory names).

    Each immediate sub-directory of *dataset_dir* is treated as a class.
    Hidden directories (names starting with ``"."``) are ignored.

    Args:
        dataset_dir: Root directory containing one subfolder per class.

    Returns:
        Sorted list of class name strings.

    Raises:
        FileNotFoundError: If *dataset_dir* does not exist.
        ValueError: If no class subdirectories are found.

    Example::

        >>> discover_classes(Path("data/Tooth_dataset_augmented"))
        ['Calculus', 'Mouth Ulcer', 'Tooth Discoloration', 'caries', 'hypodontia']
    """
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    classes = sorted(
        d.name
        for d in dataset_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )
    if not classes:
        raise ValueError(f"No class subdirectories found in {dataset_dir}")

    logger.info("Discovered %d classes: %s", len(classes), classes)
    return classes


def collect_file_paths(
    dataset_dir: Path,
    class_names: list[str],
    valid_extensions: set[str] | None = None,
) -> tuple[list[str], list[int]]:
    """Collect all image paths and their integer labels.

    Iterates through each class sub-directory, filters by file extension
    (case-insensitive), and produces parallel lists of file paths and
    integer labels.

    Args:
        dataset_dir: Root dataset directory.
        class_names: Ordered list of class names (determines label indices).
        valid_extensions: Allowed file suffixes (lowercase, e.g. ``".jpg"``).
            Defaults to :data:`VALID_EXTENSIONS_DEFAULT`.

    Returns:
        ``(file_paths, labels)`` — both lists of equal length.

    Raises:
        ValueError: If no valid images are found.
    """
    if valid_extensions is None:
        valid_extensions = VALID_EXTENSIONS_DEFAULT

    file_paths: list[str] = []
    labels: list[int] = []
    skipped = 0
    per_class_counts: dict[str, int] = {}

    for idx, cls_name in enumerate(class_names):
        cls_dir = dataset_dir / cls_name
        if not cls_dir.is_dir():
            logger.warning("Class directory missing: %s", cls_dir)
            per_class_counts[cls_name] = 0
            continue
        count = 0
        for fp in cls_dir.iterdir():
            if fp.is_file() and fp.suffix.lower() in valid_extensions:
                file_paths.append(str(fp))
                labels.append(idx)
                count += 1
            elif fp.is_file():
                skipped += 1
        per_class_counts[cls_name] = count

    if not file_paths:
        raise ValueError("No valid images found in dataset directory.")

    logger.info(
        "Collected %d images across %d classes (%d non-image files skipped).",
        len(file_paths),
        len(class_names),
        skipped,
    )
    for name, cnt in per_class_counts.items():
        logger.info("  %-25s %d images", name, cnt)

    return file_paths, labels


# ---------------------------------------------------------------------------
# Class weights
# ---------------------------------------------------------------------------


def compute_class_weights(labels: list[int] | np.ndarray) -> dict[int, float]:
    """Compute balanced class weights inversely proportional to frequency.

    Uses the formula from scikit-learn's ``compute_class_weight("balanced")``:
    ``weight_c = n_samples / (n_classes * n_samples_c)``

    This ensures that rare classes receive higher loss weight and dominant
    classes are down-weighted during training.

    Args:
        labels: Integer label array.

    Returns:
        Dict mapping class index → weight (float).
    """
    counter = Counter(labels)
    total = sum(counter.values())
    n_classes = len(counter)
    weights = {cls: total / (n_classes * count) for cls, count in counter.items()}
    logger.info("Class weights: %s", weights)
    return weights


# ---------------------------------------------------------------------------
# Train / Val / Test split
# ---------------------------------------------------------------------------


def split_dataset(
    file_paths: list[str],
    labels: list[int],
    val_split: float = 0.15,
    test_split: float = 0.10,
    seed: int = 42,
) -> dict[str, tuple[list[str], list[int]]]:
    """Stratified split into train / val / test sets.

    Performs two successive stratified splits:

    1. ``(train + val)`` vs ``test``
    2. ``train`` vs ``val``

    Stratification ensures class proportions are preserved in every split.

    Args:
        file_paths: Image file paths.
        labels: Corresponding integer labels.
        val_split: Fraction of total data for validation (0 < val_split < 1).
        test_split: Fraction of total data for test (0 < test_split < 1).
        seed: Random seed for reproducibility.

    Returns:
        Dict with keys ``'train'``, ``'val'``, ``'test'``, each mapping to
        ``(file_paths, labels)``.

    Raises:
        ValueError: If split fractions are invalid (sum ≥ 1 or ≤ 0).
    """
    # ---- Validate fractions ------------------------------------------------
    if not (0 < val_split < 1):
        raise ValueError(f"validation_split must be in (0, 1), got {val_split}")
    if not (0 < test_split < 1):
        raise ValueError(f"test_split must be in (0, 1), got {test_split}")
    if val_split + test_split >= 1.0:
        raise ValueError(
            f"val_split ({val_split}) + test_split ({test_split}) = "
            f"{val_split + test_split} — must be < 1.0 to leave data for training."
        )

    from sklearn.model_selection import train_test_split

    paths_arr = np.array(file_paths)
    labels_arr = np.array(labels)

    # First split: train+val vs test
    train_val_paths, test_paths, train_val_labels, test_labels = train_test_split(
        paths_arr,
        labels_arr,
        test_size=test_split,
        stratify=labels_arr,
        random_state=seed,
    )

    # Second split: train vs val (relative to remaining data)
    relative_val = val_split / (1.0 - test_split)
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        train_val_paths,
        train_val_labels,
        test_size=relative_val,
        stratify=train_val_labels,
        random_state=seed,
    )

    splits = {
        "train": (train_paths.tolist(), train_labels.tolist()),
        "val": (val_paths.tolist(), val_labels.tolist()),
        "test": (test_paths.tolist(), test_labels.tolist()),
    }

    total = len(file_paths)
    for name, (p, l) in splits.items():
        logger.info("  %-6s %5d samples  (%.1f%%)", name, len(p), 100 * len(p) / total)

    return splits


# ---------------------------------------------------------------------------
# tf.data pipeline
# ---------------------------------------------------------------------------


def _decode_and_resize(
    file_path: tf.Tensor,
    label: tf.Tensor,
    image_size: int,
) -> tuple[tf.Tensor, tf.Tensor]:
    """Read, decode, and resize an image to [0, 255] float32.

    This intentionally does **not** apply ``preprocess_input`` yet so that
    downstream augmentation operates on the natural [0, 255] pixel range.

    Args:
        file_path: Scalar string tensor — path to image file.
        label: Scalar int tensor — class label.
        image_size: Target H and W (square).

    Returns:
        ``(image, label)`` where image is float32 in [0, 255].
    """
    raw = tf.io.read_file(file_path)
    # decode_jpeg is faster than decode_image for .jpg/.jpeg files but
    # decode_image handles png/bmp/tiff transparently.
    image = tf.image.decode_image(raw, channels=3, expand_animations=False)
    image.set_shape([None, None, 3])
    image = tf.image.resize(image, [image_size, image_size])
    image = tf.cast(image, tf.float32)  # [0, 255]
    return image, label


def _augment(image: tf.Tensor, label: tf.Tensor) -> tuple[tf.Tensor, tf.Tensor]:
    """Apply on-the-fly augmentation on [0, 255] pixel data.

    Augmentations applied:
        * Random horizontal flip
        * Random vertical flip  (dental images have no canonical orientation)
        * Random brightness shift (±20 %)
        * Random contrast adjustment (0.8× – 1.2×)
        * Random crop to 90 % then resize back (simulates zoom / translation)

    Values are clipped to [0, 255] after augmentation to prevent overflow
    before ``preprocess_input`` scales them to [-1, 1].

    Args:
        image: float32 tensor in [0, 255], shape ``(H, W, 3)``.
        label: integer label.

    Returns:
        ``(augmented_image, label)``
    """
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_flip_up_down(image)
    image = tf.image.random_brightness(image, max_delta=50.0)  # ±50 on [0,255]
    image = tf.image.random_contrast(image, lower=0.8, upper=1.2)

    # Random crop (90 %) + resize simulates zoom / translation
    shape = tf.shape(image)
    crop_h = tf.cast(tf.cast(shape[0], tf.float32) * 0.9, tf.int32)
    crop_w = tf.cast(tf.cast(shape[1], tf.float32) * 0.9, tf.int32)
    image = tf.image.random_crop(image, [crop_h, crop_w, 3])
    image = tf.image.resize(image, [shape[0], shape[1]])

    # Clip to valid pixel range before normalisation
    image = tf.clip_by_value(image, 0.0, 255.0)
    return image, label


def _normalize(image: tf.Tensor, label: tf.Tensor) -> tuple[tf.Tensor, tf.Tensor]:
    """Apply MobileNetV2 preprocessing (maps [0, 255] → [-1, 1]).

    This is separated from decode/augment so that augmentation can
    operate on natural pixel values.

    Args:
        image: float32 tensor in [0, 255].
        label: integer label.

    Returns:
        ``(normalised_image, label)``
    """
    image = tf.keras.applications.mobilenet_v2.preprocess_input(image)
    return image, label


def build_dataset(
    file_paths: list[str],
    labels: list[int],
    image_size: int = 224,
    batch_size: int = 32,
    augment: bool = False,
    shuffle: bool = False,
    seed: int = 42,
) -> tf.data.Dataset:
    """Build a performant ``tf.data.Dataset``.

    Pipeline order (training):
        1. Shuffle file paths
        2. Read & decode images → [0, 255] float32
        3. **Cache** decoded images (before augmentation)
        4. Augment (random, different each epoch)
        5. Normalise via ``preprocess_input``  (→ [-1, 1])
        6. Batch
        7. Prefetch

    Pipeline order (validation / test):
        1. Read & decode → [0, 255]
        2. Normalise → [-1, 1]
        3. Batch
        4. Cache (safe — deterministic pipeline)
        5. Prefetch

    .. important::
        Caching is placed **before** augmentation for training so that
        random transforms produce different results every epoch.  For
        eval pipelines (no augmentation) caching is placed after batching
        for maximum efficiency.

    Args:
        file_paths: List of image file paths.
        labels: List of integer labels.
        image_size: Target spatial dimension (square).
        batch_size: Batch size.
        augment: Whether to apply random augmentation.
        shuffle: Whether to shuffle each epoch.
        seed: Shuffle seed.

    Returns:
        Batched and prefetched ``tf.data.Dataset`` yielding
        ``(images, labels)`` pairs.
    """
    ds = tf.data.Dataset.from_tensor_slices((file_paths, labels))

    if shuffle:
        ds = ds.shuffle(
            buffer_size=len(file_paths), seed=seed, reshuffle_each_iteration=True
        )

    # Decode and resize (output is [0, 255] float32)
    ds = ds.map(
        lambda fp, lbl: _decode_and_resize(fp, lbl, image_size),
        num_parallel_calls=tf.data.AUTOTUNE,
    )

    if augment:
        # Cache decoded images BEFORE augmentation so augmentation is
        # re-applied with fresh randomness every epoch.
        ds = ds.cache()
        ds = ds.map(_augment, num_parallel_calls=tf.data.AUTOTUNE)

    # Normalise [0,255] → [-1,1] for MobileNetV2
    ds = ds.map(_normalize, num_parallel_calls=tf.data.AUTOTUNE)

    ds = ds.batch(batch_size)

    if not augment:
        # For deterministic eval pipelines, cache after batching
        ds = ds.cache()

    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds
