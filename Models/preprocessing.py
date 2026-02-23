import hashlib
import os
import random
from collections import defaultdict
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageStat

# ============================================================================
# Dataset Path Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_PATH = SCRIPT_DIR.parent / "Tooth dataset"
VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")
OUTPUT_DIR = SCRIPT_DIR / "analysis_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Helpers
# ============================================================================


def get_class_image_map(dataset_path: Path) -> dict[str, list[Path]]:
    """
    Return a mapping of class_name -> list of image Paths.
    Only immediate subdirectories are treated as classes.
    """
    class_map: dict[str, list[Path]] = {}
    for cls_dir in sorted(dataset_path.iterdir()):
        if cls_dir.is_dir():
            images = [
                f
                for f in cls_dir.iterdir()
                if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS
            ]
            class_map[cls_dir.name] = images
    return class_map


def print_section(title: str) -> None:
    bar = "=" * 70
    print(f"\n{bar}")
    print(f"  {title}")
    print(f"{bar}")


# ============================================================================
# 1. Class Distribution Analysis
# ============================================================================


def run_class_distribution(class_map: dict[str, list[Path]]) -> None:
    """
    Count images per class, print a summary table, and plot a bar chart
    with a pie chart side-by-side.
    """
    print_section("1. CLASS DISTRIBUTION ANALYSIS")

    class_names = list(class_map.keys())
    class_counts = [len(v) for v in class_map.values()]
    total = sum(class_counts)

    # ── Console summary ──────────────────────────────────────────────────────
    col_w = max(len(n) for n in class_names) + 2
    print(f"\n{'Class':<{col_w}} {'Count':>8}  {'Share':>8}")
    print("-" * (col_w + 20))
    for name, count in zip(class_names, class_counts):
        pct = count / total * 100
        print(f"{name:<{col_w}} {count:>8}  {pct:>7.1f}%")
    print("-" * (col_w + 20))
    print(f"{'TOTAL':<{col_w}} {total:>8}  {'100.0%':>8}")

    # ── Plot ─────────────────────────────────────────────────────────────────
    colors = plt.cm.tab10.colors[: len(class_names)]

    fig, (ax_bar, ax_pie) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Class Distribution", fontsize=15, fontweight="bold")

    # Bar chart
    bars = ax_bar.bar(
        class_names, class_counts, color=colors, edgecolor="black", linewidth=0.6
    )
    ax_bar.set_xlabel("Class", fontsize=11)
    ax_bar.set_ylabel("Image Count", fontsize=11)
    ax_bar.set_title("Images per Class", fontsize=12)
    ax_bar.tick_params(axis="x", rotation=15)
    for bar, count in zip(bars, class_counts):
        ax_bar.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + total * 0.005,
            str(count),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    # Pie chart
    wedges, texts, autotexts = ax_pie.pie(
        class_counts,
        labels=class_names,
        autopct="%1.1f%%",
        colors=colors,
        startangle=140,
        wedgeprops=dict(edgecolor="white", linewidth=1.2),
    )
    for at in autotexts:
        at.set_fontsize(8)
    ax_pie.set_title("Class Share", fontsize=12)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "class_distribution.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\n  [Saved] {out_path}")


# ============================================================================
# 2. Aspect Ratio and Resolution Distribution
# ============================================================================


def run_aspect_ratio_resolution(class_map: dict[str, list[Path]]) -> None:
    """
    For every image collect (width, height), compute aspect ratio,
    print per-class statistics and plot:
      - scatter of width vs height coloured by class
      - histogram of aspect ratios per class
      - box plot of widths and heights per class
    """
    print_section("2. ASPECT RATIO & RESOLUTION DISTRIBUTION")

    # Collect data
    all_data: dict[str, dict] = {}
    for cls_name, images in class_map.items():
        widths, heights, aspects = [], [], []
        for img_path in images:
            try:
                with Image.open(img_path) as img:
                    w, h = img.size
                    widths.append(w)
                    heights.append(h)
                    aspects.append(round(w / h, 4))
            except Exception:
                continue
        all_data[cls_name] = {
            "widths": widths,
            "heights": heights,
            "aspects": aspects,
        }

    # ── Console summary ──────────────────────────────────────────────────────
    col_w = max(len(n) for n in all_data) + 2
    header = (
        f"{'Class':<{col_w}} {'MinW':>6} {'MaxW':>6} {'AvgW':>6} "
        f"{'MinH':>6} {'MaxH':>6} {'AvgH':>6}  {'AvgAR':>7}"
    )
    print(f"\n{header}")
    print("-" * len(header))
    for cls_name, d in all_data.items():
        print(
            f"{cls_name:<{col_w}} "
            f"{min(d['widths']):>6} {max(d['widths']):>6} {np.mean(d['widths']):>6.0f} "
            f"{min(d['heights']):>6} {max(d['heights']):>6} {np.mean(d['heights']):>6.0f}  "
            f"{np.mean(d['aspects']):>7.3f}"
        )

    colors = plt.cm.tab10.colors
    class_list = list(all_data.keys())

    fig = plt.figure(figsize=(18, 13))
    fig.suptitle(
        "Aspect Ratio & Resolution Distribution", fontsize=15, fontweight="bold"
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.32)

    ax_scatter = fig.add_subplot(gs[0, 0])
    ax_ar_hist = fig.add_subplot(gs[0, 1])
    ax_w_box = fig.add_subplot(gs[1, 0])
    ax_h_box = fig.add_subplot(gs[1, 1])

    # Scatter: width vs height
    for i, cls_name in enumerate(class_list):
        d = all_data[cls_name]
        ax_scatter.scatter(
            d["widths"], d["heights"], alpha=0.35, s=12, color=colors[i], label=cls_name
        )
    ax_scatter.set_xlabel("Width (px)", fontsize=10)
    ax_scatter.set_ylabel("Height (px)", fontsize=10)
    ax_scatter.set_title("Width vs Height", fontsize=11)
    ax_scatter.legend(fontsize=7, markerscale=1.5)

    # Histogram: aspect ratios
    for i, cls_name in enumerate(class_list):
        ax_ar_hist.hist(
            all_data[cls_name]["aspects"],
            bins=40,
            alpha=0.55,
            color=colors[i],
            label=cls_name,
        )
    ax_ar_hist.set_xlabel("Aspect Ratio (W/H)", fontsize=10)
    ax_ar_hist.set_ylabel("Frequency", fontsize=10)
    ax_ar_hist.set_title("Aspect Ratio Distribution", fontsize=11)
    ax_ar_hist.legend(fontsize=7)

    # Box: widths per class
    ax_w_box.boxplot(
        [all_data[c]["widths"] for c in class_list],
        labels=class_list,
        patch_artist=True,
        boxprops=dict(facecolor="steelblue", alpha=0.6),
        medianprops=dict(color="red", linewidth=2),
    )
    ax_w_box.set_ylabel("Width (px)", fontsize=10)
    ax_w_box.set_title("Width Distribution per Class", fontsize=11)
    ax_w_box.tick_params(axis="x", rotation=15)

    # Box: heights per class
    ax_h_box.boxplot(
        [all_data[c]["heights"] for c in class_list],
        labels=class_list,
        patch_artist=True,
        boxprops=dict(facecolor="darkorange", alpha=0.6),
        medianprops=dict(color="red", linewidth=2),
    )
    ax_h_box.set_ylabel("Height (px)", fontsize=10)
    ax_h_box.set_title("Height Distribution per Class", fontsize=11)
    ax_h_box.tick_params(axis="x", rotation=15)

    out_path = OUTPUT_DIR / "aspect_ratio_resolution.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\n  [Saved] {out_path}")


# ============================================================================
# 3. Duplicate Detection (MD5 Hashing)
# ============================================================================


def _md5_hash(image_path: Path) -> str | None:
    """Return the MD5 hex-digest of the raw file bytes."""
    try:
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None


def run_duplicate_detection(class_map: dict[str, list[Path]]) -> None:
    """
    Hash every image with MD5 and group files that share the same hash.
    Reports duplicates per-class and across classes, then plots a summary.
    """
    print_section("3. DUPLICATE DETECTION (MD5 HASHING)")

    hash_to_paths: dict[str, list[Path]] = defaultdict(list)

    total_images = 0
    for cls_name, images in class_map.items():
        for img_path in images:
            digest = _md5_hash(img_path)
            if digest:
                hash_to_paths[digest].append(img_path)
                total_images += 1

    # Separate unique vs duplicated groups
    duplicate_groups = {
        h: paths for h, paths in hash_to_paths.items() if len(paths) > 1
    }

    total_duplicate_files = sum(len(v) - 1 for v in duplicate_groups.values())
    total_duplicate_groups = len(duplicate_groups)

    # ── Console report ───────────────────────────────────────────────────────
    print(f"\n  Total images hashed  : {total_images}")
    print(f"  Unique hashes        : {len(hash_to_paths)}")
    print(f"  Duplicate groups     : {total_duplicate_groups}")
    print(f"  Redundant files      : {total_duplicate_files}")

    if duplicate_groups:
        print(f"\n  {'Group':>6}  {'Copies':>6}  Files")
        print("  " + "-" * 60)
        for idx, (digest, paths) in enumerate(list(duplicate_groups.items())[:20], 1):
            short = digest[:10] + "..."
            file_names = ", ".join(p.parent.name + "/" + p.name for p in paths)
            print(f"  {idx:>6}  {len(paths):>6}  [{short}]  {file_names}")
        if total_duplicate_groups > 20:
            print(f"  ... and {total_duplicate_groups - 20} more duplicate group(s)")
    else:
        print("\n  No duplicates found — dataset is clean.")

    # ── Per-class duplicate count ─────────────────────────────────────────────
    class_dup_count: dict[str, int] = defaultdict(int)
    for paths in duplicate_groups.values():
        for p in paths[1:]:  # first occurrence is the "original"
            class_dup_count[p.parent.name] += 1

    print(f"\n  {'Class':<25}  {'Duplicates':>10}")
    print("  " + "-" * 38)
    for cls_name in class_map:
        print(f"  {cls_name:<25}  {class_dup_count.get(cls_name, 0):>10}")

    # ── Plot ─────────────────────────────────────────────────────────────────
    class_names = list(class_map.keys())
    dup_counts = [class_dup_count.get(c, 0) for c in class_names]
    clean_counts = [len(class_map[c]) - class_dup_count.get(c, 0) for c in class_names]

    fig, (ax_bar, ax_pie) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Duplicate Detection Summary", fontsize=15, fontweight="bold")

    x = np.arange(len(class_names))
    width = 0.4
    ax_bar.bar(
        x - width / 2,
        clean_counts,
        width,
        label="Unique",
        color="steelblue",
        edgecolor="black",
        linewidth=0.5,
    )
    ax_bar.bar(
        x + width / 2,
        dup_counts,
        width,
        label="Duplicates",
        color="tomato",
        edgecolor="black",
        linewidth=0.5,
    )
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(class_names, rotation=15)
    ax_bar.set_ylabel("Image Count", fontsize=10)
    ax_bar.set_title("Unique vs Duplicate per Class", fontsize=11)
    ax_bar.legend(fontsize=9)

    pie_values = [total_images - total_duplicate_files, total_duplicate_files]
    pie_labels = [
        f"Unique ({total_images - total_duplicate_files})",
        f"Duplicates ({total_duplicate_files})",
    ]
    ax_pie.pie(
        pie_values,
        labels=pie_labels,
        autopct="%1.1f%%",
        colors=["steelblue", "tomato"],
        startangle=90,
        wedgeprops=dict(edgecolor="white", linewidth=1.2),
    )
    ax_pie.set_title("Overall Unique vs Duplicate", fontsize=11)

    out_path = OUTPUT_DIR / "duplicate_detection.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\n  [Saved] {out_path}")


# ============================================================================
# 4. Brightness and Contrast Distribution
# ============================================================================


def _brightness_contrast(image_path: Path) -> tuple[float, float] | tuple[None, None]:
    """
    Return (mean_brightness, contrast) for a single image.

    - brightness : mean of the grayscale pixel values  (0-255)
    - contrast   : standard deviation of grayscale values (spread of intensities)
    """
    try:
        with Image.open(image_path) as img:
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            return stat.mean[0], stat.stddev[0]
    except Exception:
        return None, None


def run_brightness_contrast(class_map: dict[str, list[Path]]) -> None:
    """
    Compute per-pixel brightness (mean) and contrast (std-dev) for every image,
    print per-class statistics, and plot:
      - KDE-style histogram of brightness per class
      - KDE-style histogram of contrast per class
      - Scatter of brightness vs contrast coloured by class
      - Box plots of brightness and contrast per class
    """
    print_section("4. BRIGHTNESS & CONTRAST DISTRIBUTION")

    all_data: dict[str, dict] = {}
    for cls_name, images in class_map.items():
        brightnesses, contrasts = [], []
        for img_path in images:
            b, c = _brightness_contrast(img_path)
            if b is not None:
                brightnesses.append(b)
                contrasts.append(c)
        all_data[cls_name] = {"brightness": brightnesses, "contrast": contrasts}

    # ── Console summary ──────────────────────────────────────────────────────
    col_w = max(len(n) for n in all_data) + 2
    header = (
        f"{'Class':<{col_w}} {'AvgBright':>10} {'StdBright':>10} "
        f"{'AvgContrast':>12} {'StdContrast':>12}"
    )
    print(f"\n{header}")
    print("-" * len(header))
    for cls_name, d in all_data.items():
        b = d["brightness"]
        c = d["contrast"]
        print(
            f"{cls_name:<{col_w}} "
            f"{np.mean(b):>10.2f} {np.std(b):>10.2f} "
            f"{np.mean(c):>12.2f} {np.std(c):>12.2f}"
        )

    colors = plt.cm.tab10.colors
    class_list = list(all_data.keys())

    fig = plt.figure(figsize=(18, 13))
    fig.suptitle("Brightness & Contrast Distribution", fontsize=15, fontweight="bold")
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.32)

    ax_b_hist = fig.add_subplot(gs[0, 0])
    ax_c_hist = fig.add_subplot(gs[0, 1])
    ax_scatter = fig.add_subplot(gs[1, 0])
    ax_box = fig.add_subplot(gs[1, 1])

    # Brightness histogram
    for i, cls_name in enumerate(class_list):
        ax_b_hist.hist(
            all_data[cls_name]["brightness"],
            bins=50,
            alpha=0.55,
            color=colors[i],
            label=cls_name,
        )
    ax_b_hist.set_xlabel("Mean Brightness (0–255)", fontsize=10)
    ax_b_hist.set_ylabel("Frequency", fontsize=10)
    ax_b_hist.set_title("Brightness Distribution per Class", fontsize=11)
    ax_b_hist.legend(fontsize=7)
    ax_b_hist.axvline(
        128, color="black", linestyle="--", linewidth=1, label="Midpoint (128)"
    )

    # Contrast histogram
    for i, cls_name in enumerate(class_list):
        ax_c_hist.hist(
            all_data[cls_name]["contrast"],
            bins=50,
            alpha=0.55,
            color=colors[i],
            label=cls_name,
        )
    ax_c_hist.set_xlabel("Contrast (Std Dev of Pixel Intensity)", fontsize=10)
    ax_c_hist.set_ylabel("Frequency", fontsize=10)
    ax_c_hist.set_title("Contrast Distribution per Class", fontsize=11)
    ax_c_hist.legend(fontsize=7)

    # Scatter: brightness vs contrast
    for i, cls_name in enumerate(class_list):
        ax_scatter.scatter(
            all_data[cls_name]["brightness"],
            all_data[cls_name]["contrast"],
            alpha=0.3,
            s=10,
            color=colors[i],
            label=cls_name,
        )
    ax_scatter.set_xlabel("Mean Brightness", fontsize=10)
    ax_scatter.set_ylabel("Contrast (Std Dev)", fontsize=10)
    ax_scatter.set_title("Brightness vs Contrast per Class", fontsize=11)
    ax_scatter.legend(fontsize=7, markerscale=2)

    # Box plot: brightness per class
    bp = ax_box.boxplot(
        [all_data[c]["brightness"] for c in class_list],
        labels=class_list,
        patch_artist=True,
        medianprops=dict(color="red", linewidth=2),
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax_box.set_ylabel("Mean Brightness", fontsize=10)
    ax_box.set_title("Brightness Box Plot per Class", fontsize=11)
    ax_box.tick_params(axis="x", rotation=15)

    out_path = OUTPUT_DIR / "brightness_contrast.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\n  [Saved] {out_path}")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    print(f"\nDataset  : {DATASET_PATH}")
    print(f"Output   : {OUTPUT_DIR}")

    if not DATASET_PATH.exists():
        print(f"\n[ERROR] Dataset path not found: {DATASET_PATH}")
        raise SystemExit(1)

    class_map = get_class_image_map(DATASET_PATH)

    if not class_map:
        print("[ERROR] No class folders found inside the dataset directory.")
        raise SystemExit(1)

    total = sum(len(v) for v in class_map.values())
    print(f"Classes  : {list(class_map.keys())}")
    print(f"Total    : {total} images across {len(class_map)} classes")

    # ── Run all analyses ──────────────────────────────────────────────────────
    run_class_distribution(class_map)
    run_aspect_ratio_resolution(class_map)
    run_duplicate_detection(class_map)
    run_brightness_contrast(class_map)

    print("\n" + "=" * 70)
    print("  All analyses complete. Charts saved to:", OUTPUT_DIR)
    print("=" * 70 + "\n")
