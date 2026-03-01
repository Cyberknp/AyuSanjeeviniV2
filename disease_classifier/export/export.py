"""Export trained model to SavedModel, .h5, and quantised .tflite formats.

Produces three export artefacts:

1. **SavedModel** (``exported_models/saved_model/``) — TensorFlow's native
   format, suitable for TF Serving or further conversion.

2. **Keras H5** (``exported_models/model.h5``) — portable single-file
   format, compatible with ``tf.keras.models.load_model()``.

3. **TFLite** (``exported_models/model.tflite``) — float16-quantised model
   for mobile and edge deployment.  Reduces model size by ~50 % with
   minimal accuracy loss.

Additionally copies ``class_names.json`` alongside the exports so that
downstream consumers know the label mapping.

Usage::

    python main.py export
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import tensorflow as tf

logger = logging.getLogger(__name__)


def run_export(cfg: dict[str, Any]) -> None:
    """Export the best checkpoint to multiple deployment formats.

    Args:
        cfg: Configuration dictionary.

    Raises:
        FileNotFoundError: If no trained checkpoint exists.
    """
    checkpoint_dir = Path(cfg.get("checkpoint_dir", "checkpoints"))
    export_dir = Path(cfg.get("export_dir", "exported_models"))
    export_dir.mkdir(parents=True, exist_ok=True)

    model_path = checkpoint_dir / "best_model.keras"
    if not model_path.exists():
        raise FileNotFoundError(
            f"No checkpoint found at {model_path}. Run 'python main.py train' first."
        )

    logger.info("Loading model from %s", model_path)
    model = tf.keras.models.load_model(str(model_path))

    # ---- SavedModel --------------------------------------------------------
    saved_model_dir = export_dir / "saved_model"
    tf.saved_model.save(model, str(saved_model_dir))
    logger.info("✓ SavedModel exported to %s", saved_model_dir)

    # ---- H5 ----------------------------------------------------------------
    h5_path = export_dir / "model.h5"
    model.save(str(h5_path))
    logger.info("✓ H5 model saved to %s", h5_path)

    # ---- TFLite (float16 quantisation) -------------------------------------
    tflite_path = export_dir / "model.tflite"
    _export_tflite(model, tflite_path, cfg)
    logger.info("✓ TFLite model saved to %s", tflite_path)

    # ---- Copy class names alongside exports --------------------------------
    results_dir = Path(cfg.get("results_dir", "results"))
    cn_src = results_dir / "class_names.json"
    cn_dst = export_dir / "class_names.json"
    if cn_src.exists():
        shutil.copy2(str(cn_src), str(cn_dst))
        logger.info("✓ class_names.json copied to %s", cn_dst)
    else:
        logger.warning("class_names.json not found at %s — skipping copy.", cn_src)

    logger.info("Export complete. All artefacts in %s", export_dir)


def _export_tflite(
    model: tf.keras.Model,
    output_path: Path,
    cfg: dict[str, Any],
) -> None:
    """Convert a Keras model to TFLite with float16 quantisation.

    Float16 quantisation halves the model size while maintaining
    accuracy — ideal for mobile deployment on the Flutter app.

    Args:
        model: Trained Keras model.
        output_path: Destination ``.tflite`` file path.
        cfg: Config dict (used for ``image_size``).
    """
    image_size = cfg.get("image_size", 224)

    @tf.function(
        input_signature=[
            tf.TensorSpec(shape=[1, image_size, image_size, 3], dtype=tf.float32)
        ]
    )
    def serving_fn(x: tf.Tensor) -> tf.Tensor:
        return model(x, training=False)

    concrete = serving_fn.get_concrete_function()

    converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete])
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]

    tflite_model = converter.convert()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / (1024 * 1024)
    logger.info("  TFLite model size: %.2f MB", size_mb)
