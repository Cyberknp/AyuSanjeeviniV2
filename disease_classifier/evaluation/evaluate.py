"""Evaluation pipeline: run test-set through a trained model and report metrics.

Produces:
    * ``results/confusion_matrix.png`` — raw-count confusion matrix
    * ``results/confusion_matrix_normalized.png`` — row-normalised (recall) matrix
    * ``results/classification_report.txt`` — per-class precision / recall / F1
    * ``results/metrics.json`` — scalar summary (accuracy, precision, recall, F1)

The test split is reconstructed deterministically from the same seed used
during training, so results are comparable across runs.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import tensorflow as tf
from data.dataset import (
    build_dataset,
    collect_file_paths,
    discover_classes,
    split_dataset,
)
from utils.metrics import compute_metrics
from utils.visualization import plot_confusion_matrix

logger = logging.getLogger(__name__)


def run_evaluation(cfg: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a trained model on the held-out test split.

    The function:
        1. Loads class names (from training artefacts or re-discovers them).
        2. Rebuilds the same deterministic test split used during training.
        3. Loads the best checkpoint (or exported H5 fallback).
        4. Runs inference on all test samples.
        5. Computes and persists classification metrics.

    Args:
        cfg: Configuration dictionary.

    Returns:
        Metrics dictionary with keys ``accuracy``, ``precision``,
        ``recall``, ``f1_score``, ``per_class``, ``confusion_matrix``,
        and ``classification_report``.

    Raises:
        FileNotFoundError: If no trained model checkpoint exists.
    """
    results_dir = Path(cfg.get("results_dir", "results"))
    checkpoint_dir = Path(cfg.get("checkpoint_dir", "checkpoints"))

    # ---- Load class names --------------------------------------------------
    class_names_path = results_dir / "class_names.json"
    if class_names_path.exists():
        with open(class_names_path) as f:
            class_names: list[str] = json.load(f)
        logger.info("Loaded %d class names from %s", len(class_names), class_names_path)
    else:
        dataset_dir = Path(cfg["dataset_dir"])
        class_names = discover_classes(dataset_dir)

    # ---- Rebuild test split -----------------------------------------------
    dataset_dir = Path(cfg["dataset_dir"])
    file_paths, labels = collect_file_paths(
        dataset_dir,
        class_names,
        valid_extensions=set(cfg.get("valid_extensions", [".jpg", ".jpeg", ".png"])),
    )

    splits = split_dataset(
        file_paths,
        labels,
        val_split=cfg.get("validation_split", 0.15),
        test_split=cfg.get("test_split", 0.10),
        seed=cfg.get("seed", 42),
    )

    test_paths, test_labels = splits["test"]
    image_size: int = cfg.get("image_size", 224)
    batch_size: int = cfg.get("batch_size", 32)

    test_ds = build_dataset(
        test_paths,
        test_labels,
        image_size=image_size,
        batch_size=batch_size,
    )

    # ---- Load model --------------------------------------------------------
    model_path = checkpoint_dir / "best_model.keras"
    if not model_path.exists():
        export_dir = Path(cfg.get("export_dir", "exported_models"))
        model_path = export_dir / "model.h5"

    if not model_path.exists():
        raise FileNotFoundError(
            f"No trained model found at {checkpoint_dir / 'best_model.keras'} "
            f"or {Path(cfg.get('export_dir', 'exported_models')) / 'model.h5'}. "
            "Run 'python main.py train' first."
        )

    logger.info("Loading model from %s", model_path)
    model = tf.keras.models.load_model(str(model_path))

    # ---- Predict -----------------------------------------------------------
    logger.info("Running predictions on %d test samples …", len(test_paths))
    y_pred_probs = model.predict(test_ds, verbose=1)
    y_pred = np.argmax(y_pred_probs, axis=1)
    y_true = np.array(test_labels)

    # ---- Metrics -----------------------------------------------------------
    metrics = compute_metrics(y_true, y_pred, class_names=class_names)

    # ---- Confusion matrices ------------------------------------------------
    results_dir.mkdir(parents=True, exist_ok=True)

    # Raw counts
    plot_confusion_matrix(
        metrics["confusion_matrix"],
        class_names,
        save_path=results_dir / "confusion_matrix.png",
        title="Confusion Matrix (counts)",
    )

    # Row-normalised (each row sums to 1 → shows per-class recall)
    cm = metrics["confusion_matrix"]
    cm_norm = cm.astype("float") / (cm.sum(axis=1, keepdims=True) + 1e-8)
    plot_confusion_matrix(
        cm_norm,
        class_names,
        save_path=results_dir / "confusion_matrix_normalized.png",
        title="Confusion Matrix (normalised)",
        fmt=".2f",
    )

    # ---- Save reports ------------------------------------------------------
    report_path = results_dir / "classification_report.txt"
    with open(report_path, "w") as f:
        f.write(metrics["classification_report"])
    logger.info("Classification report saved to %s", report_path)

    metrics_summary = {
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1_score": metrics["f1_score"],
        "per_class": metrics.get("per_class", {}),
        "num_test_samples": len(test_labels),
    }
    with open(results_dir / "metrics.json", "w") as f:
        json.dump(metrics_summary, f, indent=2)

    logger.info("\n%s", metrics["classification_report"])
    return metrics
