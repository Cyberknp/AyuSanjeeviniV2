"""MobileNetV2-based classification model builder.

Provides factory functions for constructing a MobileNetV2 transfer-learning
model suitable for multi-class disease classification.

Architecture overview::

    Input (224×224×3)
        │
        ▼
    MobileNetV2 (ImageNet pre-trained, top removed)
        │
        ▼
    GlobalAveragePooling2D   ← spatial dims → 1280-d vector
        │
        ▼
    BatchNormalization       ← stabilises head training
        │
        ▼
    Dropout(rate)            ← regularisation
        │
        ▼
    Dense(num_classes, softmax)

Training strategy:
    1. **Phase 1 — head training**: The entire MobileNetV2 base is frozen;
       only GAP → BN → Dropout → Dense are trained.
    2. **Phase 2 — fine-tuning**: Layers from ``fine_tune_at`` onward in the
       base are unfrozen and trained at a lower learning rate.

.. note::
    A ``BatchNormalization`` layer is inserted between GAP and Dropout.
    This normalises the 1280-d feature vector, which reduces the
    sensitivity of the head to the frozen base's output scale and
    accelerates convergence during Phase 1.
"""

from __future__ import annotations

import logging

import tensorflow as tf

logger = logging.getLogger(__name__)

# Name of the base model layer in the outer wrapper model.
# Used by other modules (e.g. Grad-CAM) to locate the inner model.
BASE_MODEL_LAYER_NAME = "mobilenetv2_base"


def build_mobilenetv2(
    num_classes: int,
    image_size: int = 224,
    dropout_rate: float = 0.3,
    fine_tune_at: int = 100,
    freeze_base: bool = True,
) -> tf.keras.Model:
    """Build a MobileNetV2 transfer-learning model.

    Args:
        num_classes: Number of output classes (≥ 2).
        image_size: Input spatial dimension (square).
        dropout_rate: Dropout probability before the final dense layer.
        fine_tune_at: Layer index in the base model from which layers will
            be unfrozen during fine-tuning.  MobileNetV2 has 154 layers;
            index 100 leaves ~54 layers trainable.
        freeze_base: If ``True``, freeze all base model weights initially.

    Returns:
        An **uncompiled** ``tf.keras.Model`` ready to be compiled.

    Raises:
        ValueError: If *num_classes* < 2.
    """
    if num_classes < 2:
        raise ValueError(f"num_classes must be ≥ 2, got {num_classes}")

    input_shape = (image_size, image_size, 3)

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )
    base_model._name = BASE_MODEL_LAYER_NAME  # deterministic name for lookup

    if freeze_base:
        base_model.trainable = False
        logger.info(
            "Base MobileNetV2 frozen (%d layers). Fine-tune from layer %d later.",
            len(base_model.layers),
            fine_tune_at,
        )
    else:
        _unfreeze_from(base_model, fine_tune_at)

    inputs = tf.keras.Input(shape=input_shape, name="input_image")
    x = base_model(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = tf.keras.layers.BatchNormalization(name="head_bn")(x)
    x = tf.keras.layers.Dropout(dropout_rate, name="dropout")(x)
    outputs = tf.keras.layers.Dense(
        num_classes, activation="softmax", name="predictions"
    )(x)

    model = tf.keras.Model(
        inputs=inputs, outputs=outputs, name="mobilenetv2_classifier"
    )
    logger.info("Model built — %d total params.", model.count_params())
    return model


def unfreeze_for_finetuning(
    model: tf.keras.Model,
    fine_tune_at: int = 100,
) -> tf.keras.Model:
    """Unfreeze the base model from ``fine_tune_at`` onward for fine-tuning.

    Only layers *at or after* index ``fine_tune_at`` become trainable.
    Layers before remain frozen to preserve low-level ImageNet features.

    Args:
        model: Model previously built by :func:`build_mobilenetv2`.
        fine_tune_at: Layer index in the **base** model from which to
            unfreeze.  Must be ``0 <= fine_tune_at < len(base.layers)``.

    Returns:
        The same model (mutated in-place) with layers unfrozen.

    Raises:
        ValueError: If *fine_tune_at* exceeds the number of base layers.
    """
    base_model = model.get_layer(BASE_MODEL_LAYER_NAME)

    if fine_tune_at >= len(base_model.layers):
        raise ValueError(
            f"fine_tune_at={fine_tune_at} exceeds base model layer count "
            f"({len(base_model.layers)}). Nothing would be unfrozen."
        )

    base_model.trainable = True
    _unfreeze_from(base_model, fine_tune_at)

    trainable = sum(1 for l in base_model.layers if l.trainable)
    frozen = len(base_model.layers) - trainable
    logger.info(
        "Base model: %d layers frozen, %d layers trainable (from layer %d).",
        frozen,
        trainable,
        fine_tune_at,
    )
    return model


def get_last_conv_layer_name(model: tf.keras.Model) -> str:
    """Return the name of the last Conv2D layer inside the base model.

    This is used by Grad-CAM to locate the feature map to visualise.
    The function drills into the nested MobileNetV2 base rather than
    searching the outer wrapper's layers.

    Args:
        model: Model built by :func:`build_mobilenetv2`.

    Returns:
        Layer name string (e.g. ``"out_relu"``).

    Raises:
        ValueError: If no convolutional layer is found.
    """
    base_model = model.get_layer(BASE_MODEL_LAYER_NAME)
    for layer in reversed(base_model.layers):
        if isinstance(layer, (tf.keras.layers.Conv2D, tf.keras.layers.DepthwiseConv2D)):
            return layer.name
        # Also match activation layers that sit right after the last conv block
        if hasattr(layer, "output") and len(layer.output.shape) == 4:
            # Check if it's a real feature-producing layer (not an input)
            if not isinstance(layer, tf.keras.layers.InputLayer):
                return layer.name
    raise ValueError("Could not find a convolutional layer in the base model.")


def _unfreeze_from(base_model: tf.keras.Model, fine_tune_at: int) -> None:
    """Freeze layers before *fine_tune_at*, unfreeze the rest.

    Also freezes any ``BatchNormalization`` layers in the base model to
    prevent running-mean/variance corruption when training with small
    batch sizes (a well-known transfer-learning pitfall).

    Args:
        base_model: The MobileNetV2 base model.
        fine_tune_at: Layer index cutoff.
    """
    base_model.trainable = True
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False
    # Keep BatchNorm layers frozen even in the unfrozen portion to
    # avoid corrupting running statistics with small-batch updates.
    for layer in base_model.layers[fine_tune_at:]:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
