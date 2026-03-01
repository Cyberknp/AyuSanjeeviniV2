#!/usr/bin/env python3
"""CLI entry-point for MobileNetV2 disease classifier.

Supported commands::

    python main.py train                           # Train + fine-tune
    python main.py evaluate                        # Evaluate on test set
    python main.py predict --image path/to/img.jpg # Predict single image
    python main.py export                          # Export model formats
    python main.py info                            # Dataset statistics
    python main.py train --config custom.yaml      # Use custom config
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so package imports work when
# the file is invoked directly (python main.py …).
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.seed import set_global_seed  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("disease_classifier")


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML configuration file.

    Relative ``dataset_dir`` paths are resolved against the project root
    so that the config works regardless of the current working directory.

    Args:
        config_path: Path to config YAML.  Defaults to
            ``config/config.yaml`` inside the project root.

    Returns:
        Configuration dictionary.
    """
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)

    with open(config_path) as f:
        cfg: dict[str, Any] = yaml.safe_load(f)

    # Resolve relative dataset_dir against project root
    ds = cfg.get("dataset_dir", "")
    ds_path = Path(ds)
    if not ds_path.is_absolute():
        cfg["dataset_dir"] = str((PROJECT_ROOT / ds_path).resolve())

    logger.info("Configuration loaded from %s", config_path)
    return cfg


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------


def cmd_train(cfg: dict[str, Any]) -> None:
    """Run the full two-phase training pipeline."""
    from training.train import run_training

    run_training(cfg)
    logger.info("Training finished successfully.")


def cmd_evaluate(cfg: dict[str, Any]) -> None:
    """Run evaluation on the held-out test split."""
    from evaluation.evaluate import run_evaluation

    metrics = run_evaluation(cfg)
    # Print JSON-serialisable subset to stdout
    printable = {
        k: v
        for k, v in metrics.items()
        if k not in ("confusion_matrix", "classification_report")
    }
    print(json.dumps(printable, indent=2))


def cmd_predict(cfg: dict[str, Any], image_path: str) -> None:
    """Run single-image prediction with optional Grad-CAM."""
    from inference.predict import run_prediction

    result = run_prediction(cfg, image_path)
    print(json.dumps(result, indent=2))


def cmd_export(cfg: dict[str, Any]) -> None:
    """Export model to SavedModel, H5, and TFLite formats."""
    from export.export import run_export

    run_export(cfg)
    logger.info("Export finished successfully.")


def cmd_info(cfg: dict[str, Any]) -> None:
    """Print dataset statistics without training.

    Shows:
        * Number of classes
        * Per-class image counts
        * Class imbalance ratio (max / min)
        * Total image count
        * Train / val / test split sizes
    """
    from collections import Counter

    from data.dataset import collect_file_paths, discover_classes, split_dataset

    dataset_dir = Path(cfg["dataset_dir"])
    class_names = discover_classes(dataset_dir)
    file_paths, labels = collect_file_paths(
        dataset_dir,
        class_names,
        valid_extensions=set(cfg.get("valid_extensions", [".jpg", ".jpeg", ".png"])),
    )

    counter = Counter(labels)
    total = len(file_paths)

    print("\n" + "=" * 60)
    print("  DATASET INFORMATION")
    print("=" * 60)
    print(f"  Directory : {dataset_dir}")
    print(f"  Classes   : {len(class_names)}")
    print(f"  Total imgs: {total}")
    print()

    print("  Per-class distribution:")
    max_count = max(counter.values())
    min_count = min(counter.values())
    for idx, name in enumerate(class_names):
        count = counter.get(idx, 0)
        bar = "█" * int(40 * count / max_count)
        print(f"    {name:25s}  {count:5d}  ({100 * count / total:5.1f}%)  {bar}")

    print()
    imbalance_ratio = max_count / min_count if min_count > 0 else float("inf")
    print(f"  Imbalance ratio (max/min): {imbalance_ratio:.2f}x")

    # Show split sizes
    splits = split_dataset(
        file_paths,
        labels,
        val_split=cfg.get("validation_split", 0.15),
        test_split=cfg.get("test_split", 0.10),
        seed=cfg.get("seed", 42),
    )
    print()
    print("  Split sizes:")
    for name, (paths, _) in splits.items():
        print(f"    {name:6s}: {len(paths):5d}  ({100 * len(paths) / total:5.1f}%)")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="MobileNetV2 Disease Classifier CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py info                            # Show dataset stats\n"
            "  python main.py train                           # Train model\n"
            "  python main.py evaluate                        # Test-set metrics\n"
            "  python main.py predict --image sample.jpg      # Single prediction\n"
            "  python main.py export                          # Export all formats\n"
        ),
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Path to YAML config file (default: config/config.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # info
    subparsers.add_parser("info", help="Show dataset statistics")

    # train
    subparsers.add_parser("train", help="Train the model (Phase 1 + Phase 2)")

    # evaluate
    subparsers.add_parser("evaluate", help="Evaluate on the held-out test set")

    # predict
    predict_parser = subparsers.add_parser("predict", help="Predict on a single image")
    predict_parser.add_argument(
        "--image",
        "-i",
        type=str,
        required=True,
        help="Path to the input image",
    )

    # export
    subparsers.add_parser("export", help="Export model to SavedModel / H5 / TFLite")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry-point.  Dispatches to the appropriate sub-command."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    cfg = load_config(args.config)
    set_global_seed(cfg.get("seed", 42))

    commands = {
        "info": lambda: cmd_info(cfg),
        "train": lambda: cmd_train(cfg),
        "evaluate": lambda: cmd_evaluate(cfg),
        "predict": lambda: cmd_predict(cfg, args.image),
        "export": lambda: cmd_export(cfg),
    }

    handler = commands.get(args.command)
    if handler:
        handler()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
