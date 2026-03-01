"""Visualization helpers: confusion matrix, Grad-CAM, training curves.

All plotting functions accept an optional ``save_path`` argument.  When
provided the figure is saved to disk and the matplotlib figure is closed
to avoid memory leaks during long training runs.  When ``save_path`` is
``None`` the figure remains open for interactive display.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # non-interactive backend — safe for headless servers
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Confusion Matrix
# ---------------------------------------------------------------------------


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: list[str],
    save_path: Path | str | None = None,
    title: str = "Confusion Matrix",
    fmt: str = "d",
) -> None:
    """Plot and optionally save a confusion matrix heatmap.

    Args:
        cm: Confusion matrix array ``(n_classes, n_classes)``.
            Can be integer counts or float (normalised) values.
        class_names: List of class label strings.
        save_path: If provided, save figure to this path.
        title: Plot title.
        fmt: Format string for cell labels.  Use ``"d"`` for integer
            counts and ``".2f"`` for normalised floats.
    """
    fig, ax = plt.subplots(
        figsize=(max(8, len(class_names) + 1), max(6, len(class_names) + 1))
    )
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.set_title(title, fontsize=14, pad=12)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    tick_marks = np.arange(len(class_names))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(class_names, rotation=45, ha="right", fontsize=10)
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(class_names, fontsize=10)

    # Determine threshold for text colour (white on dark, black on light)
    thresh = (cm.max() + cm.min()) / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j,
                i,
                format(cm[i, j], fmt),
                ha="center",
                va="center",
                color="white" if cm[i, j] > thresh else "black",
                fontsize=11,
            )

    ax.set_ylabel("True label")
    ax.set_xlabel("Predicted label")
    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(save_path), dpi=150, bbox_inches="tight")
        logger.info("Confusion matrix saved to %s", save_path)

    plt.close(fig)


# ---------------------------------------------------------------------------
# Training History Curves
# ---------------------------------------------------------------------------


def plot_training_history(
    history: dict[str, list[float]],
    save_path: Path | str | None = None,
) -> None:
    """Plot training / validation accuracy and loss curves.

    Generates a 1×2 subplot with accuracy on the left and loss on the
    right.  A vertical dashed line is drawn at the Phase 1 / Phase 2
    boundary if the learning-rate drops (detected via ``lr`` key).

    Args:
        history: Keras-style history dict with keys like
            ``'accuracy'``, ``'val_accuracy'``, ``'loss'``, ``'val_loss'``.
        save_path: If provided, save figure to this path.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Accuracy
    if "accuracy" in history:
        axes[0].plot(history["accuracy"], label="Train Accuracy")
    if "val_accuracy" in history:
        axes[0].plot(history["val_accuracy"], label="Val Accuracy")
    axes[0].set_title("Model Accuracy", fontsize=13)
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Accuracy")
    axes[0].legend(loc="lower right")
    axes[0].grid(True, alpha=0.3)

    # Loss
    if "loss" in history:
        axes[1].plot(history["loss"], label="Train Loss")
    if "val_loss" in history:
        axes[1].plot(history["val_loss"], label="Val Loss")
    axes[1].set_title("Model Loss", fontsize=13)
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Loss")
    axes[1].legend(loc="upper right")
    axes[1].grid(True, alpha=0.3)

    # Detect phase boundary from learning-rate discontinuity
    if "lr" in history and len(history["lr"]) > 1:
        lrs = history["lr"]
        for i in range(1, len(lrs)):
            # A large LR jump (>2×) indicates a new phase / recompile
            if lrs[i] > lrs[i - 1] * 2 or lrs[i] < lrs[i - 1] * 0.1:
                for ax in axes:
                    ax.axvline(
                        x=i,
                        color="red",
                        linestyle="--",
                        alpha=0.5,
                        label="Phase boundary" if i == 1 else None,
                    )
                break

    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(save_path), dpi=150, bbox_inches="tight")
        logger.info("Training curves saved to %s", save_path)

    plt.close(fig)


# ---------------------------------------------------------------------------
# Grad-CAM
# ---------------------------------------------------------------------------


def grad_cam(
    model: Any,
    image: np.ndarray,
    class_index: int | None = None,
    last_conv_layer_name: str | None = None,
) -> np.ndarray:
    """Generate a Grad-CAM heatmap for the given image.

    Grad-CAM (Gradient-weighted Class Activation Mapping) highlights the
    regions of the input image most important for the model's prediction.

    For **nested** model architectures (``Input → MobileNetV2 → Head``),
    auto-detection drills into the base model to find the last
    convolutional layer rather than searching only the outer wrapper.

    Args:
        model: Trained ``tf.keras.Model``.
        image: Preprocessed image array of shape ``(1, H, W, 3)``.
        class_index: Target class index.  If ``None``, the predicted
            class is used.
        last_conv_layer_name: Name of the last convolutional layer.
            If ``None``, auto-detected via
            :func:`models.mobilenetv2.get_last_conv_layer_name`.

    Returns:
        Heatmap array of shape ``(H_feat, W_feat)`` with values in [0, 1].

    Raises:
        ValueError: If no convolutional layer can be found.
    """
    import tensorflow as tf

    # ---- Auto-detect last conv layer (handling nested models) --------------
    if last_conv_layer_name is None:
        try:
            from models.mobilenetv2 import (
                BASE_MODEL_LAYER_NAME,
                get_last_conv_layer_name,
            )

            last_conv_layer_name = get_last_conv_layer_name(model)
            # Build the grad model from the base model's inner layers
            base_model = model.get_layer(BASE_MODEL_LAYER_NAME)
            target_layer = base_model.get_layer(last_conv_layer_name)
        except (ValueError, KeyError):
            # Fallback: flat model — search outer layers
            target_layer = None
            for layer in reversed(model.layers):
                if isinstance(
                    layer, (tf.keras.layers.Conv2D, tf.keras.layers.DepthwiseConv2D)
                ):
                    target_layer = layer
                    last_conv_layer_name = layer.name
                    break
            if target_layer is None:
                raise ValueError("Could not auto-detect last conv layer.")
    else:
        # Caller provided the name — try outer model first, then base
        try:
            target_layer = model.get_layer(last_conv_layer_name)
        except ValueError:
            from models.mobilenetv2 import BASE_MODEL_LAYER_NAME

            base_model = model.get_layer(BASE_MODEL_LAYER_NAME)
            target_layer = base_model.get_layer(last_conv_layer_name)

    # ---- Build gradient model ----------------------------------------------
    grad_model = tf.keras.Model(
        inputs=model.input,
        outputs=[target_layer.output, model.output],
    )

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(image)
        if class_index is None:
            class_index = int(tf.argmax(predictions[0]))
        loss = predictions[:, class_index]

    grads = tape.gradient(loss, conv_outputs)
    if grads is None:
        logger.warning("Grad-CAM: gradients are None — layer may be disconnected.")
        # Return a blank heatmap rather than crashing
        h, w = conv_outputs.shape[1], conv_outputs.shape[2]
        return np.zeros((h, w), dtype=np.float32)

    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)

    return heatmap.numpy()


def overlay_grad_cam(
    image: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.4,
    save_path: Path | str | None = None,
) -> np.ndarray:
    """Overlay a Grad-CAM heatmap on an image.

    Uses OpenCV's JET colourmap to colourize the heatmap, then alpha-blends
    it with the original image.

    Args:
        image: Original image ``(H, W, 3)`` in [0, 255] uint8.
        heatmap: Heatmap ``(H_cam, W_cam)`` in [0, 1].
        alpha: Blending factor (0 = original only, 1 = heatmap only).
        save_path: If provided, save the blended image.

    Returns:
        Blended image array ``(H, W, 3)`` uint8.
    """
    import cv2  # type: ignore

    heatmap_resized = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
    heatmap_colored = cv2.applyColorMap(
        np.uint8(255 * heatmap_resized), cv2.COLORMAP_JET
    )
    blended = cv2.addWeighted(image, 1 - alpha, heatmap_colored, alpha, 0)

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(save_path), blended)
        logger.info("Grad-CAM overlay saved to %s", save_path)

    return blended
