"""Metrics computation utilities.

Wraps scikit-learn's classification metrics into a single
:func:`compute_metrics` call that returns everything needed for
evaluation reports.

Metrics computed:
    * **Accuracy** — overall fraction of correct predictions.
    * **Precision** (weighted) — positive predictive value, weighted by
      class support to handle imbalance.
    * **Recall** (weighted) — sensitivity / true positive rate.
    * **F1-score** (weighted) — harmonic mean of precision and recall.
    * **Per-class metrics** — precision, recall, and F1 for each class.
    * **Confusion matrix** — ``(n_classes × n_classes)`` count matrix.
    * **Classification report** — human-readable table string.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)

logger = logging.getLogger(__name__)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str] | None = None,
) -> dict[str, Any]:
    """Compute a comprehensive set of classification metrics.

    Args:
        y_true: Ground-truth label indices, shape ``(n_samples,)``.
        y_pred: Predicted label indices, shape ``(n_samples,)``.
        class_names: Optional human-readable class names for reporting.

    Returns:
        Dictionary with keys:

        * ``accuracy`` (float)
        * ``precision`` (float, weighted average)
        * ``recall`` (float, weighted average)
        * ``f1_score`` (float, weighted average)
        * ``per_class`` (dict of class_name → {precision, recall, f1, support})
        * ``confusion_matrix`` (np.ndarray)
        * ``classification_report`` (str)

    Example::

        >>> metrics = compute_metrics(y_true, y_pred, ["cat", "dog"])
        >>> metrics["accuracy"]
        0.92
        >>> metrics["per_class"]["cat"]["f1"]
        0.91
    """
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    recall = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    cm = confusion_matrix(y_true, y_pred)
    report = classification_report(
        y_true, y_pred, target_names=class_names, zero_division=0
    )

    # Per-class breakdown
    per_class: dict[str, dict[str, float]] = {}
    p_per, r_per, f_per, s_per = precision_recall_fscore_support(
        y_true, y_pred, zero_division=0
    )
    labels = class_names if class_names else [str(i) for i in range(len(p_per))]
    for i, name in enumerate(labels):
        per_class[name] = {
            "precision": float(p_per[i]),
            "recall": float(r_per[i]),
            "f1": float(f_per[i]),
            "support": int(s_per[i]),
        }

    metrics: dict[str, Any] = {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "per_class": per_class,
        "confusion_matrix": cm,
        "classification_report": report,
    }

    logger.info("Accuracy : %.4f", accuracy)
    logger.info("Precision: %.4f  (weighted)", precision)
    logger.info("Recall   : %.4f  (weighted)", recall)
    logger.info("F1-score : %.4f  (weighted)", f1)
    logger.info("Per-class breakdown:")
    for name, vals in per_class.items():
        logger.info(
            "  %-25s  P=%.3f  R=%.3f  F1=%.3f  n=%d",
            name,
            vals["precision"],
            vals["recall"],
            vals["f1"],
            vals["support"],
        )

    return metrics
