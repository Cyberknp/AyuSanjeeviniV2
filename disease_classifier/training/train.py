"""Training pipeline: initial head training + base fine-tuning.

Implements a two-phase transfer-learning strategy:

**Phase 1 — Head training**
    The MobileNetV2 base is frozen.  Only the classification head
    (GAP → BN → Dropout → Dense) is trained at a higher learning rate.
    This quickly adapts the randomly-initialised head to the domain.

**Phase 2 — Fine-tuning**
    The top layers of the base model are unfrozen and trained at a
    lower learning rate.  This allows the high-level feature extractors
    to specialise for the target disease classification task.

Both phases share callbacks (early stopping, LR reduction, checkpointing,
TensorBoard) and automatically compute class weights to handle imbalance.

Artefacts produced:
    * ``checkpoints/best_model.keras`` — best checkpoint (by val_accuracy)
    * ``results/class_names.json`` — ordered class label list
    * ``results/split_info.json`` — sample counts per split
    * ``results/training_history.json`` — epoch-level metrics
    * ``results/training_curves.png`` — accuracy & loss plots
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import tensorflow as tf
from data.dataset import (
    build_dataset,
    collect_file_paths,
    compute_class_weights,
    discover_classes,
    split_dataset,
)
from models.mobilenetv2 import build_mobilenetv2, unfreeze_for_finetuning
from utils.visualization import plot_training_history

logger = logging.getLogger(__name__)


def _get_callbacks(cfg: dict[str, Any]) -> list[tf.keras.callbacks.Callback]:
    """Build Keras callback list from config.

    Callbacks created:
        * **ModelCheckpoint** — saves best model by ``val_accuracy``.
        * **EarlyStopping** — halts training if ``val_loss`` stops improving.
        * **ReduceLROnPlateau** — halves LR when ``val_loss`` plateaus.
        * **TensorBoard** *(optional)* — logs histograms & scalars.

    Args:
        cfg: Configuration dictionary.

    Returns:
        List of configured Keras callbacks.
    """
    checkpoint_dir = Path(cfg["checkpoint_dir"])
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    callbacks: list[tf.keras.callbacks.Callback] = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(checkpoint_dir / "best_model.keras"),
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=cfg.get("early_stopping_patience", 7),
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=cfg.get("reduce_lr_factor", 0.5),
            patience=cfg.get("reduce_lr_patience", 3),
            min_lr=1e-7,
            verbose=1,
        ),
    ]

    if cfg.get("tensorboard", False):
        log_dir = Path(cfg.get("tensorboard_log_dir", "logs/tensorboard"))
        log_dir.mkdir(parents=True, exist_ok=True)
        callbacks.append(
            tf.keras.callbacks.TensorBoard(
                log_dir=str(log_dir),
                histogram_freq=1,
            )
        )

    return callbacks


def run_training(cfg: dict[str, Any]) -> tf.keras.Model:
    """Execute the full two-phase training pipeline.

    Steps:
        1. Discover classes and collect file paths.
        2. Stratified split into train / val / test.
        3. Build ``tf.data`` pipelines with augmentation on training set.
        4. Compute class weights for imbalance handling.
        5. Build MobileNetV2 model with frozen base.
        6. **Phase 1**: Train classification head.
        7. Unfreeze upper base layers.
        8. **Phase 2**: Fine-tune end-to-end at lower LR.
        9. Save training curves and history.

    Args:
        cfg: Configuration dictionary (loaded from ``config.yaml``).

    Returns:
        Trained ``tf.keras.Model``.
    """
    t_start = time.time()

    # ---- Mixed precision ---------------------------------------------------
    if cfg.get("mixed_precision", False):
        tf.keras.mixed_precision.set_global_policy("mixed_float16")
        logger.info("Mixed precision enabled (mixed_float16).")

    # ---- GPU check ---------------------------------------------------------
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        logger.info("GPU(s) available: %s", gpus)
        for gpu in gpus:
            try:
                tf.config.experimental.set_memory_growth(gpu, True)
            except RuntimeError:
                logger.debug("Memory growth already set for %s", gpu)
    else:
        logger.warning("No GPU detected — training will use CPU (slow).")

    # ---- Dataset -----------------------------------------------------------
    dataset_dir = Path(cfg["dataset_dir"])
    class_names = discover_classes(dataset_dir)
    num_classes = len(class_names)

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

    image_size: int = cfg.get("image_size", 224)
    batch_size: int = cfg.get("batch_size", 32)

    train_ds = build_dataset(
        *splits["train"],
        image_size=image_size,
        batch_size=batch_size,
        augment=True,
        shuffle=True,
        seed=cfg.get("seed", 42),
    )
    val_ds = build_dataset(
        *splits["val"],
        image_size=image_size,
        batch_size=batch_size,
    )

    # ---- Class weights -----------------------------------------------------
    class_weights = compute_class_weights(splits["train"][1])

    # ---- Persist metadata --------------------------------------------------
    results_dir = Path(cfg.get("results_dir", "results"))
    results_dir.mkdir(parents=True, exist_ok=True)

    class_names_path = results_dir / "class_names.json"
    with open(class_names_path, "w") as f:
        json.dump(class_names, f, indent=2)
    logger.info("Class names saved to %s", class_names_path)

    split_info = {k: {"count": len(v[0])} for k, v in splits.items()}
    with open(results_dir / "split_info.json", "w") as f:
        json.dump(split_info, f, indent=2)

    # ---- Build model -------------------------------------------------------
    model = build_mobilenetv2(
        num_classes=num_classes,
        image_size=image_size,
        dropout_rate=cfg.get("dropout_rate", 0.3),
        fine_tune_at=cfg.get("fine_tune_at", 100),
        freeze_base=True,
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=cfg.get("learning_rate", 1e-3)
        ),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.summary(print_fn=logger.info)

    # ---- Phase 1: Train head -----------------------------------------------
    epochs = cfg.get("epochs", 30)
    callbacks_phase1 = _get_callbacks(cfg)

    logger.info("=" * 60)
    logger.info("Phase 1: Training head layers (%d epochs)", epochs)
    logger.info("=" * 60)

    history1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        class_weight=class_weights,
        callbacks=callbacks_phase1,
    )

    # Track actual epochs completed (EarlyStopping may have stopped early)
    actual_phase1_epochs = len(history1.history.get("loss", []))
    logger.info("Phase 1 completed: %d / %d epochs.", actual_phase1_epochs, epochs)

    # ---- Phase 2: Fine-tune ------------------------------------------------
    fine_tune_epochs = cfg.get("fine_tune_epochs", 15)
    if fine_tune_epochs > 0:
        logger.info("=" * 60)
        logger.info(
            "Phase 2: Fine-tuning from layer %d (%d epochs)",
            cfg.get("fine_tune_at", 100),
            fine_tune_epochs,
        )
        logger.info("=" * 60)

        model = unfreeze_for_finetuning(
            model, fine_tune_at=cfg.get("fine_tune_at", 100)
        )

        model.compile(
            optimizer=tf.keras.optimizers.Adam(
                learning_rate=cfg.get("fine_tune_lr", 1e-4)
            ),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        # Use actual Phase 1 epoch count (not the config value) so that
        # Phase 2 starts from the correct epoch even if EarlyStopping
        # halted Phase 1 early.
        callbacks_phase2 = _get_callbacks(cfg)
        total_epochs = actual_phase1_epochs + fine_tune_epochs

        history2 = model.fit(
            train_ds,
            validation_data=val_ds,
            initial_epoch=actual_phase1_epochs,
            epochs=total_epochs,
            class_weight=class_weights,
            callbacks=callbacks_phase2,
        )

        # Merge histories for plotting
        combined_history: dict[str, list[float]] = {}
        for key in history1.history:
            combined_history[key] = history1.history[key] + history2.history.get(
                key, []
            )
    else:
        combined_history = dict(history1.history)

    # ---- Save training curves ----------------------------------------------
    plot_training_history(
        combined_history,
        save_path=results_dir / "training_curves.png",
    )

    # ---- Save training history JSON ----------------------------------------
    serialisable = {k: [float(v) for v in vs] for k, vs in combined_history.items()}
    with open(results_dir / "training_history.json", "w") as f:
        json.dump(serialisable, f, indent=2)

    elapsed = time.time() - t_start
    logger.info("Training complete in %.1f minutes.", elapsed / 60)
    return model
