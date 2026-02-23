import math
import random
import shutil
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_PATH = SCRIPT_DIR.parent / "Tooth dataset"
OUTPUT_PATH = SCRIPT_DIR.parent / "Tooth dataset_augmented"

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff")
SAVE_FORMAT = "JPEG"
SAVE_QUALITY = 95

# All classes will be brought up to this count.
# Defaults to the size of the largest class (auto-detected at runtime).
TARGET_COUNT: int | None = None  # set to an int to override, e.g. 2017

# Augmentation intensity thresholds.
# Classes whose image count is below these fractions of the target
# receive correspondingly stronger augmentation.
HEAVY_THRESHOLD = 0.40  # < 40 % of target  → heavy
MILD_THRESHOLD = 0.90  # < 90 % of target  → mild
# >= 90 % of target → copy-only


# ============================================================================
# Individual Augmentation Operations
# ============================================================================


def aug_horizontal_flip(img: Image.Image) -> Image.Image:
    """Mirror image left-to-right."""
    return ImageOps.mirror(img)


def aug_vertical_flip(img: Image.Image) -> Image.Image:
    """Mirror image top-to-bottom."""
    return ImageOps.flip(img)


def aug_rotation(img: Image.Image, max_angle: float = 30.0) -> Image.Image:
    """Rotate by a random angle in [-max_angle, +max_angle] degrees."""
    angle = random.uniform(-max_angle, max_angle)
    return img.rotate(angle, resample=Image.BICUBIC, expand=False)


def aug_brightness(
    img: Image.Image, low: float = 0.6, high: float = 1.4
) -> Image.Image:
    """Randomly adjust brightness."""
    factor = random.uniform(low, high)
    return ImageEnhance.Brightness(img).enhance(factor)


def aug_contrast(img: Image.Image, low: float = 0.6, high: float = 1.4) -> Image.Image:
    """Randomly adjust contrast."""
    factor = random.uniform(low, high)
    return ImageEnhance.Contrast(img).enhance(factor)


def aug_saturation(
    img: Image.Image, low: float = 0.5, high: float = 1.5
) -> Image.Image:
    """Randomly adjust colour saturation."""
    factor = random.uniform(low, high)
    return ImageEnhance.Color(img).enhance(factor)


def aug_sharpness(img: Image.Image, low: float = 0.2, high: float = 2.5) -> Image.Image:
    """Randomly adjust sharpness."""
    factor = random.uniform(low, high)
    return ImageEnhance.Sharpness(img).enhance(factor)


def aug_gaussian_blur(img: Image.Image, max_radius: float = 1.8) -> Image.Image:
    """Apply a light Gaussian blur."""
    radius = random.uniform(0.3, max_radius)
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def aug_gaussian_noise(img: Image.Image, std: float = 12.0) -> Image.Image:
    """Add zero-mean Gaussian noise to pixel values."""
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, std, arr.shape).astype(np.float32)
    noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy)


def aug_random_crop(img: Image.Image, crop_frac: float = 0.85) -> Image.Image:
    """
    Crop a random sub-region (at least crop_frac of each dimension)
    and resize back to the original dimensions.
    """
    w, h = img.size
    crop_w = int(w * random.uniform(crop_frac, 1.0))
    crop_h = int(h * random.uniform(crop_frac, 1.0))
    x0 = random.randint(0, w - crop_w)
    y0 = random.randint(0, h - crop_h)
    cropped = img.crop((x0, y0, x0 + crop_w, y0 + crop_h))
    return cropped.resize((w, h), resample=Image.BICUBIC)


def aug_gamma_correction(
    img: Image.Image, low: float = 0.6, high: float = 1.8
) -> Image.Image:
    """Apply a random gamma correction via a lookup table."""
    gamma = random.uniform(low, high)
    table = [int(((i / 255.0) ** (1.0 / gamma)) * 255) for i in range(256)]
    if img.mode == "RGB":
        table = table * 3
    return img.point(table)


# ============================================================================
# Augmentation Pipelines
# ============================================================================

# Each pipeline is a list of (function, kwargs, probability) tuples.
# During synthesis a coin-flip per operation decides whether it is applied.


def _build_heavy_pipeline() -> list[tuple]:
    """
    Heavy augmentation for severely under-represented classes
    (caries, Mouth Ulcer).  Many transforms with wide parameter ranges.
    """
    return [
        (aug_horizontal_flip, {}, 0.50),
        (aug_vertical_flip, {}, 0.25),
        (aug_rotation, {"max_angle": 30.0}, 0.70),
        (aug_brightness, {"low": 0.55, "high": 1.50}, 0.70),
        (aug_contrast, {"low": 0.55, "high": 1.50}, 0.70),
        (aug_saturation, {"low": 0.45, "high": 1.60}, 0.60),
        (aug_sharpness, {"low": 0.20, "high": 3.00}, 0.50),
        (aug_gaussian_blur, {"max_radius": 2.0}, 0.35),
        (aug_gaussian_noise, {"std": 14.0}, 0.40),
        (aug_random_crop, {"crop_frac": 0.82}, 0.55),
        (aug_gamma_correction, {"low": 0.55, "high": 2.0}, 0.45),
    ]


def _build_mild_pipeline() -> list[tuple]:
    """
    Mild augmentation for moderately under-represented classes
    (Calculus, hypodontia).  Fewer transforms with tighter ranges.
    """
    return [
        (aug_horizontal_flip, {}, 0.50),
        (aug_vertical_flip, {}, 0.10),
        (aug_rotation, {"max_angle": 15.0}, 0.50),
        (aug_brightness, {"low": 0.80, "high": 1.25}, 0.50),
        (aug_contrast, {"low": 0.80, "high": 1.25}, 0.50),
        (aug_saturation, {"low": 0.80, "high": 1.25}, 0.35),
        (aug_sharpness, {"low": 0.60, "high": 1.80}, 0.30),
        (aug_gaussian_blur, {"max_radius": 1.0}, 0.20),
        (aug_gaussian_noise, {"std": 6.0}, 0.20),
        (aug_random_crop, {"crop_frac": 0.90}, 0.35),
        (aug_gamma_correction, {"low": 0.75, "high": 1.40}, 0.25),
    ]


def apply_pipeline(img: Image.Image, pipeline: list[tuple]) -> Image.Image:
    """
    Apply each operation in *pipeline* with its associated probability.
    Guarantees that at least one operation is applied so no augmented image
    is identical to its source.
    """
    result = img.copy()
    applied = 0

    # Shuffle so we don't always apply in the same order
    ops = list(pipeline)
    random.shuffle(ops)

    for fn, kwargs, prob in ops:
        if random.random() < prob:
            result = fn(result, **kwargs)
            applied += 1

    # Safety net: if nothing was applied, force the first operation
    if applied == 0:
        fn, kwargs, _ = pipeline[0]
        result = fn(result, **kwargs)

    return result


# ============================================================================
# Utility Helpers
# ============================================================================


def get_class_image_map(dataset_path: Path) -> dict[str, list[Path]]:
    """Return {class_name: [image_paths ...]} for every sub-directory."""
    class_map: dict[str, list[Path]] = {}
    for cls_dir in sorted(dataset_path.iterdir()):
        if cls_dir.is_dir():
            images = [
                f
                for f in cls_dir.iterdir()
                if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS
            ]
            class_map[cls_dir.name] = sorted(images)
    return class_map


def classify_intensity(
    current: int,
    target: int,
) -> str:
    """Return 'copy', 'mild', or 'heavy' based on how far below target a class is."""
    ratio = current / target
    if ratio >= MILD_THRESHOLD:
        return "copy"
    if ratio >= HEAVY_THRESHOLD:
        return "mild"
    return "heavy"


def print_section(title: str) -> None:
    bar = "=" * 70
    print(f"\n{bar}\n  {title}\n{bar}")


# ============================================================================
# Core: Copy Originals
# ============================================================================


def copy_originals(
    class_map: dict[str, list[Path]],
    output_path: Path,
) -> None:
    """
    Copy every original image into the mirrored output directory tree.
    Existing files are skipped so the function is safe to re-run.
    """
    print_section("STEP 1 — COPYING ORIGINAL IMAGES")
    total_copied = 0

    for cls_name, images in class_map.items():
        dest_dir = output_path / cls_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        copied = 0
        for src in images:
            dst = dest_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
                copied += 1
        total_copied += copied
        print(
            f"  {cls_name:<25} {len(images):>5} originals  ->  {copied:>5} newly copied"
        )

    print(f"\n  Total copied : {total_copied}")


# ============================================================================
# Core: Synthetic Generation
# ============================================================================


def generate_augmented_images(
    class_map: dict[str, list[Path]],
    output_path: Path,
    target: int,
) -> dict[str, int]:
    """
    For each class that falls below *target*, generate synthetic images by
    applying random augmentation pipelines to randomly-sampled originals.

    Returns a dict {class_name: num_generated}.
    """
    print_section("STEP 2 — SYNTHETIC IMAGE GENERATION")

    col = max(len(n) for n in class_map) + 2
    generated_counts: dict[str, int] = {}

    for cls_name, images in class_map.items():
        current = len(images)
        needed = max(0, target - current)
        intensity = classify_intensity(current, target)
        dest_dir = output_path / cls_name

        print(
            f"\n  [{intensity.upper():<5}]  {cls_name:<{col}}"
            f"  current={current:>5}  target={target:>5}  to_generate={needed:>5}"
        )

        if needed == 0 or intensity == "copy":
            print(f"           -> Skipped (already at or near target)")
            generated_counts[cls_name] = 0
            continue

        pipeline = (
            _build_heavy_pipeline() if intensity == "heavy" else _build_mild_pipeline()
        )
        generated = 0

        # How many passes over the original images do we need?
        # We cycle through originals repeatedly until we hit the quota.
        source_pool = list(images)  # all originals as source candidates
        random.shuffle(source_pool)
        pool_index = 0

        for i in range(needed):
            # Round-robin source selection with shuffling each full cycle
            if pool_index >= len(source_pool):
                random.shuffle(source_pool)
                pool_index = 0
            src_path = source_pool[pool_index]
            pool_index += 1

            try:
                with Image.open(src_path) as src_img:
                    src_img = src_img.convert("RGB")
                    aug_img = apply_pipeline(src_img, pipeline)

                # Build a unique filename: <original_stem>_aug_<zero-padded index>.jpg
                new_name = f"{src_path.stem}_aug_{i:05d}.jpg"
                dst_path = dest_dir / new_name

                # Avoid overwriting if we re-run the script
                if dst_path.exists():
                    new_name = (
                        f"{src_path.stem}_aug_{i:05d}_r{random.randint(100, 999)}.jpg"
                    )
                    dst_path = dest_dir / new_name

                aug_img.save(dst_path, format=SAVE_FORMAT, quality=SAVE_QUALITY)
                generated += 1

                # Progress indicator every 200 images
                if generated % 200 == 0:
                    print(f"           -> {generated}/{needed} generated ...")

            except Exception as exc:
                print(f"           [WARN] Skipped {src_path.name}: {exc}")

        generated_counts[cls_name] = generated
        print(f"           -> Done: {generated} synthetic images saved to {dest_dir}")

    return generated_counts


# ============================================================================
# Verification
# ============================================================================


def verify_output(
    output_path: Path,
    class_map: dict[str, list[Path]],
    target: int,
) -> dict[str, int]:
    """
    Count images per class in the augmented dataset and print a report.
    Returns {class_name: count_in_output}.
    """
    print_section("STEP 3 — VERIFICATION")

    col = max(len(n) for n in class_map) + 2
    result: dict[str, int] = {}

    print(
        f"\n  {'Class':<{col}} {'Original':>10}  {'Augmented':>10}  {'Delta':>8}  {'Status':>10}"
    )
    print("  " + "-" * (col + 46))

    for cls_name in class_map:
        original_count = len(class_map[cls_name])
        augmented_dir = output_path / cls_name
        augmented_count = (
            len(
                [
                    f
                    for f in augmented_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS
                ]
            )
            if augmented_dir.exists()
            else 0
        )

        delta = augmented_count - original_count
        status = "[OK]" if augmented_count >= target else "[LOW]"
        result[cls_name] = augmented_count

        print(
            f"  {cls_name:<{col}} {original_count:>10}  {augmented_count:>10}  {delta:>+8}  {status:>10}"
        )

    print()
    return result


# ============================================================================
# Visualisation: Before / After Comparison
# ============================================================================


def plot_before_after(
    class_map: dict[str, list[Path]],
    after_counts: dict[str, int],
    target: int,
    output_dir: Path,
) -> None:
    """
    Side-by-side bar charts (before / after) and a comparison table figure.
    """
    class_names = list(class_map.keys())
    before = [len(class_map[c]) for c in class_names]
    after = [after_counts.get(c, 0) for c in class_names]
    colors = plt.cm.tab10.colors[: len(class_names)]

    fig = plt.figure(figsize=(18, 14))
    fig.suptitle(
        "Oversampling & Synthetic Generation — Class Balance Report",
        fontsize=15,
        fontweight="bold",
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.30)

    ax_before = fig.add_subplot(gs[0, 0])
    ax_after = fig.add_subplot(gs[0, 1])
    ax_cmp = fig.add_subplot(gs[1, 0])
    ax_gain = fig.add_subplot(gs[1, 1])

    # ── Before ───────────────────────────────────────────────────────────────
    bars_b = ax_before.bar(
        class_names, before, color=colors, edgecolor="black", linewidth=0.6
    )
    ax_before.axhline(
        target, color="red", linestyle="--", linewidth=1.4, label=f"Target ({target})"
    )
    ax_before.set_title("Before Augmentation", fontsize=12, fontweight="bold")
    ax_before.set_ylabel("Image Count", fontsize=10)
    ax_before.tick_params(axis="x", rotation=18)
    ax_before.legend(fontsize=8)
    for bar, val in zip(bars_b, before):
        ax_before.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 20,
            str(val),
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
        )

    # ── After ────────────────────────────────────────────────────────────────
    bars_a = ax_after.bar(
        class_names, after, color=colors, edgecolor="black", linewidth=0.6
    )
    ax_after.axhline(
        target, color="red", linestyle="--", linewidth=1.4, label=f"Target ({target})"
    )
    ax_after.set_title("After Augmentation", fontsize=12, fontweight="bold")
    ax_after.set_ylabel("Image Count", fontsize=10)
    ax_after.tick_params(axis="x", rotation=18)
    ax_after.legend(fontsize=8)
    for bar, val in zip(bars_a, after):
        ax_after.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 20,
            str(val),
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
        )

    # ── Side-by-side grouped comparison ─────────────────────────────────────
    x = np.arange(len(class_names))
    w = 0.38
    ax_cmp.bar(
        x - w / 2,
        before,
        w,
        label="Before",
        color="steelblue",
        edgecolor="black",
        linewidth=0.5,
    )
    ax_cmp.bar(
        x + w / 2,
        after,
        w,
        label="After",
        color="darkorange",
        edgecolor="black",
        linewidth=0.5,
    )
    ax_cmp.axhline(
        target, color="red", linestyle="--", linewidth=1.2, label=f"Target ({target})"
    )
    ax_cmp.set_xticks(x)
    ax_cmp.set_xticklabels(class_names, rotation=18)
    ax_cmp.set_ylabel("Image Count", fontsize=10)
    ax_cmp.set_title("Before vs After per Class", fontsize=11, fontweight="bold")
    ax_cmp.legend(fontsize=8)

    # ── Gain (synthetic images added) ────────────────────────────────────────
    gains = [a - b for a, b in zip(after, before)]
    gain_colors = ["tomato" if g > 0 else "lightgrey" for g in gains]
    bars_g = ax_gain.bar(
        class_names, gains, color=gain_colors, edgecolor="black", linewidth=0.6
    )
    ax_gain.set_title(
        "Synthetic Images Added per Class", fontsize=11, fontweight="bold"
    )
    ax_gain.set_ylabel("Images Added", fontsize=10)
    ax_gain.tick_params(axis="x", rotation=18)
    ax_gain.axhline(0, color="black", linewidth=0.8)
    for bar, val in zip(bars_g, gains):
        if val > 0:
            ax_gain.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 10,
                f"+{val}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
            )

    out_path = output_dir / "augmentation_before_after.png"
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"  [Saved] {out_path}")


def plot_sample_augmentations(
    class_map: dict[str, list[Path]],
    output_dir: Path,
    n_per_class: int = 5,
) -> None:
    """
    For each minority class pick one source image and display it alongside
    n_per_class augmented variants (heavy pipeline) so the user can visually
    verify the transforms look realistic.
    """
    print_section("STEP 4 — VISUAL SAMPLE OF AUGMENTED IMAGES")

    minority_classes = [
        cls
        for cls, imgs in class_map.items()
        if classify_intensity(len(imgs), _resolve_target(class_map)) != "copy"
    ]

    for cls_name in minority_classes:
        images = class_map[cls_name]
        src_path = random.choice(images)
        pipeline = _build_heavy_pipeline()

        with Image.open(src_path) as src_img:
            src_img = src_img.convert("RGB")
            variants = [apply_pipeline(src_img, pipeline) for _ in range(n_per_class)]

        total_cols = 1 + n_per_class
        fig, axes = plt.subplots(1, total_cols, figsize=(3.5 * total_cols, 4))
        fig.suptitle(
            f"Class: {cls_name}  —  Original + {n_per_class} Augmented Variants",
            fontsize=12,
            fontweight="bold",
        )

        # Original
        axes[0].imshow(src_img)
        axes[0].set_title("Original", fontsize=9, color="green", fontweight="bold")
        axes[0].axis("off")

        # Augmented variants
        for i, (ax, aug) in enumerate(zip(axes[1:], variants), 1):
            ax.imshow(aug)
            ax.set_title(f"Aug #{i}", fontsize=9)
            ax.axis("off")

        plt.tight_layout()
        out_path = output_dir / f"sample_aug_{cls_name.replace(' ', '_')}.png"
        plt.savefig(out_path, dpi=130, bbox_inches="tight")
        plt.show()
        print(f"  [Saved] {out_path}")


# ============================================================================
# Internal Helper
# ============================================================================


def _resolve_target(class_map: dict[str, list[Path]]) -> int:
    """Return the effective target count (global override or max class size)."""
    if TARGET_COUNT is not None:
        return TARGET_COUNT
    return max(len(v) for v in class_map.values())


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    print(f"\n  Source dataset : {DATASET_PATH}")
    print(f"  Output dataset : {OUTPUT_PATH}")

    if not DATASET_PATH.exists():
        print(f"\n[ERROR] Dataset path not found: {DATASET_PATH}")
        raise SystemExit(1)

    # ── Load class map ────────────────────────────────────────────────────────
    class_map = get_class_image_map(DATASET_PATH)
    if not class_map:
        print("[ERROR] No class folders found inside the dataset directory.")
        raise SystemExit(1)

    target = _resolve_target(class_map)

    print(f"\n  Classes  : {list(class_map.keys())}")
    print(f"  Target   : {target} images per class")
    print(f"  Total original images : {sum(len(v) for v in class_map.values())}")
    print(f"  Total after balancing : {target * len(class_map)}")

    # Show per-class intensity assignment
    print_section("AUGMENTATION PLAN")
    col = max(len(n) for n in class_map) + 2
    print(f"\n  {'Class':<{col}}  {'Count':>7}  {'Needed':>7}  {'Intensity':>10}")
    print("  " + "-" * (col + 32))
    for cls_name, imgs in class_map.items():
        needed = max(0, target - len(imgs))
        intensity = classify_intensity(len(imgs), target)
        print(
            f"  {cls_name:<{col}}  {len(imgs):>7}  {needed:>7}  {intensity.upper():>10}"
        )

    # ── Step 1: Copy originals ────────────────────────────────────────────────
    copy_originals(class_map, OUTPUT_PATH)

    # ── Step 2: Generate synthetic images ────────────────────────────────────
    generated = generate_augmented_images(class_map, OUTPUT_PATH, target)

    # ── Step 3: Verify ───────────────────────────────────────────────────────
    after_counts = verify_output(OUTPUT_PATH, class_map, target)

    # ── Step 4: Visual sample of augmentations ────────────────────────────────
    analysis_dir = SCRIPT_DIR / "analysis_output"
    plot_sample_augmentations(class_map, analysis_dir)

    # ── Step 5: Before / After chart ─────────────────────────────────────────
    plot_before_after(class_map, after_counts, target, analysis_dir)

    # ── Final summary ─────────────────────────────────────────────────────────
    total_before = sum(len(v) for v in class_map.values())
    total_after = sum(after_counts.values())
    total_synth = sum(generated.values())

    print_section("SUMMARY")
    print(f"\n  Original images    : {total_before:>6}")
    print(f"  Synthetic images   : {total_synth:>6}")
    print(f"  Total (augmented)  : {total_after:>6}")
    print(f"  Classes balanced   : {len(class_map)}")
    print(f"  Target per class   : {target}")
    print(f"\n  Augmented dataset saved to:\n  {OUTPUT_PATH}\n")
