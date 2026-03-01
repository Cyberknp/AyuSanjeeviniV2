"""Single-image inference with optional Grad-CAM overlay.

Usage from CLI::

    python main.py predict --image path/to/image.jpg

Programmatic usage::

    from inference.predict import run_prediction
    result = run_prediction(cfg, "path/to/image.jpg")
    print(result["predicted_class"], result["confidence"])

The result dictionary includes:
    * ``predicted_class`` — string label
    * ``confidence`` — float in [0, 1]
    * ``probabilities`` — dict of class_name → probability
    * ``gradcam_path`` — path to Grad-CAM overlay (if OpenCV available)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import tensorflow as tf

logger = logging.getLogger(__name__)


def load_and_preprocess(
    image_path: str | Path,
    image_size: int = 224,
) -> tuple[np.ndarray, np.ndarray]:
    """Load, decode, resize, and normalise a single image for inference.

    The preprocessing matches the training pipeline:
        1. Decode to RGB uint8
        2. Resize to ``(image_size, image_size)``
        3. Cast to float32
        4. Apply ``MobileNetV2.preprocess_input`` ([0, 255] → [-1, 1])

    Args:
        image_path: Path to the image file.
        image_size: Target spatial dimension.

    Returns:
        ``(preprocessed_batch, original_image)`` where
        ``preprocessed_batch`` has shape ``(1, H, W, 3)`` in [-1, 1] and
        ``original_image`` is the raw decoded uint8 array.

    Raises:
        FileNotFoundError: If *image_path* does not exist.
        ValueError: If the file cannot be decoded as an image.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    raw = tf.io.read_file(str(image_path))
    try:
        image = tf.image.decode_image(raw, channels=3, expand_animations=False)
    except tf.errors.InvalidArgumentError as exc:
        raise ValueError(f"Cannot decode image: {image_path}") from exc

    image.set_shape([None, None, 3])
    original = image.numpy()  # keep raw pixels for Grad-CAM overlay

    image = tf.image.resize(image, [image_size, image_size])
    image = tf.cast(image, tf.float32)
    preprocessed = tf.keras.applications.mobilenet_v2.preprocess_input(image)
    batch = tf.expand_dims(preprocessed, axis=0)

    return batch.numpy(), original


def run_prediction(cfg: dict[str, Any], image_path: str) -> dict[str, Any]:
    """Run inference on a single image.

    Loads the best available checkpoint, preprocesses the image, runs
    a forward pass, and returns the prediction with all class
    probabilities.  If OpenCV is installed, a Grad-CAM overlay is
    generated and saved to the results directory.

    Args:
        cfg: Configuration dictionary.
        image_path: Path to the input image file.

    Returns:
        Dict with keys:
            * ``image_path`` — input file path
            * ``predicted_class`` — string label of the top prediction
            * ``confidence`` — float probability of the top prediction
            * ``probabilities`` — dict mapping each class name to its probability
            * ``gradcam_path`` — *(optional)* path to saved Grad-CAM overlay

    Raises:
        FileNotFoundError: If class_names.json or model checkpoint is missing.
    """
    results_dir = Path(cfg.get("results_dir", "results"))
    checkpoint_dir = Path(cfg.get("checkpoint_dir", "checkpoints"))

    # ---- Load class names --------------------------------------------------
    class_names_path = results_dir / "class_names.json"
    if not class_names_path.exists():
        raise FileNotFoundError(
            f"class_names.json not found at {class_names_path}. "
            "Run 'python main.py train' first."
        )
    with open(class_names_path) as f:
        class_names: list[str] = json.load(f)

    # ---- Load model --------------------------------------------------------
    model_path = checkpoint_dir / "best_model.keras"
    if not model_path.exists():
        export_dir = Path(cfg.get("export_dir", "exported_models"))
        model_path = export_dir / "model.h5"
    if not model_path.exists():
        raise FileNotFoundError(
            "No trained model found. Run 'python main.py train' first."
        )

    logger.info("Loading model from %s", model_path)
    model = tf.keras.models.load_model(str(model_path))

    # ---- Preprocess --------------------------------------------------------
    image_size: int = cfg.get("image_size", 224)
    batch, original = load_and_preprocess(image_path, image_size)

    # ---- Predict -----------------------------------------------------------
    probs = model.predict(batch, verbose=0)[0]
    pred_idx = int(np.argmax(probs))
    pred_class = class_names[pred_idx]
    confidence = float(probs[pred_idx])

    result: dict[str, Any] = {
        "image_path": str(image_path),
        "predicted_class": pred_class,
        "confidence": confidence,
        "probabilities": {
            name: round(float(probs[i]), 6) for i, name in enumerate(class_names)
        },
    }

    logger.info("Prediction: %s (%.2f%%)", pred_class, confidence * 100)
    for name, prob in result["probabilities"].items():
        logger.info("  %-25s %.4f", name, prob)

    # ---- Optional Grad-CAM ------------------------------------------------
    try:
        import cv2  # noqa: F401
        from utils.visualization import grad_cam, overlay_grad_cam

        heatmap = grad_cam(model, batch, class_index=pred_idx)
        original_resized = (
            tf.image.resize(original, [image_size, image_size]).numpy().astype(np.uint8)
        )
        results_dir.mkdir(parents=True, exist_ok=True)
        gradcam_path = results_dir / "gradcam_last_prediction.png"
        overlay_grad_cam(original_resized, heatmap, save_path=gradcam_path)
        result["gradcam_path"] = str(gradcam_path)
        logger.info("Grad-CAM overlay saved to %s", gradcam_path)
    except ImportError:
        logger.debug("OpenCV not installed — skipping Grad-CAM overlay.")
    except Exception as exc:
        logger.warning("Grad-CAM generation failed: %s", exc)

    return result
