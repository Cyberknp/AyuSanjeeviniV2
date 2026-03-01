"""Deterministic seed setting for reproducibility.

Sets seeds for:
    * ``PYTHONHASHSEED`` environment variable
    * Python ``random`` module
    * NumPy random generator
    * TensorFlow random generator

.. note::
    TensorFlow determinism is best-effort.  GPU operations may still
    introduce non-determinism due to floating-point reduction order.
    Set ``TF_DETERMINISTIC_OPS=1`` for stricter (but slower) behaviour.
"""

from __future__ import annotations

import logging
import os
import random

import numpy as np

logger = logging.getLogger(__name__)


def set_global_seed(seed: int = 42) -> None:
    """Set seeds across all random generators for reproducible experiments.

    Should be called **once** at the start of the program, before any
    model or data operations.

    Args:
        seed: Integer seed value (≥ 0).
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)

    try:
        import tensorflow as tf

        tf.random.set_seed(seed)
    except ImportError:
        pass

    logger.info("Global seed set to %d", seed)
