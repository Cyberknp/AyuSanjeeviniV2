import os
import random
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

# ============================================================================
# Dataset Path Configuration
# ============================================================================

# Resolve the dataset path relative to this script's location
SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_PATH = SCRIPT_DIR.parent / "Tooth dataset"

# Number of images to sample per class for visual audit
NUM_IMAGES_PER_CLASS = 5

# Supported image extensions
VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")


# ============================================================================
# Image Integrity Verification
# ============================================================================


def verify_image(file_path: str) -> bool:
    """
    Verify image integrity by opening it twice:
    - First pass: verify file structure
    - Second pass: load pixel data to detect truncation

    Args:
        file_path: Full path to the image file

    Returns:
        True if image is valid, False if corrupted
    """
    try:
        # First pass: verify file structure
        with Image.open(file_path) as img:
            img.verify()

        # Second pass: reload and load pixel data (verify() exhausts the file handle)
        with Image.open(file_path) as img:
            img.load()

        return True
    except (IOError, SyntaxError, AttributeError):
        return False


def run_integrity_check(dataset_path: Path) -> None:
    """
    Walk through the dataset directory and check all images for corruption.
    Deletes any corrupted or unreadable image files found.

    Args:
        dataset_path: Path to the root dataset directory
    """
    if not dataset_path.exists():
        print(f"Error: Dataset path does not exist: {dataset_path}")
        return

    if not dataset_path.is_dir():
        print(f"Error: Provided path is not a directory: {dataset_path}")
        return

    print(f"Starting integrity check for images in: {dataset_path}")
    print("-" * 60)

    corrupted_files_count = 0
    total_files_checked = 0

    for root, _, files in os.walk(dataset_path):
        for filename in files:
            if filename.lower().endswith(VALID_EXTENSIONS):
                file_path = os.path.join(root, filename)
                total_files_checked += 1

                if not verify_image(file_path):
                    print(f"Corrupted or invalid image detected: {file_path}")
                    try:
                        os.remove(file_path)
                        corrupted_files_count += 1
                        print(f"  -> Deleted corrupted file: {file_path}")
                    except OSError as ose:
                        print(f"  -> Error deleting file {file_path}: {ose}")
                else:
                    print(f"  [OK] {file_path}")

    print("\n--- Integrity Check Complete ---")
    print(f"Total files checked:            {total_files_checked}")
    print(
        f"Total valid files:              {total_files_checked - corrupted_files_count}"
    )
    print(f"Total corrupted files deleted:  {corrupted_files_count}")


# ============================================================================
# Visual Audit
# ============================================================================


def run_visual_audit(
    dataset_path: Path, num_images_per_class: int = NUM_IMAGES_PER_CLASS
) -> None:
    """
    Perform a visual audit by randomly sampling and displaying images
    from each class folder in a matplotlib grid.

    One figure is generated per class, showing a row of sampled images
    with their filenames as titles.

    Args:
        dataset_path: Path to the root dataset directory
        num_images_per_class: Number of images to randomly sample per class
    """
    if not dataset_path.exists():
        print(f"Error: Dataset path does not exist: {dataset_path}")
        return

    if not dataset_path.is_dir():
        print(f"Error: Provided path is not a directory: {dataset_path}")
        return

    # Each immediate subdirectory is treated as a class
    class_dirs = sorted([d for d in dataset_path.iterdir() if d.is_dir()])

    if not class_dirs:
        print(f"No class subdirectories found in: {dataset_path}")
        return

    print(f"\nStarting visual audit for: {dataset_path}")
    print(f"Classes found: {[d.name for d in class_dirs]}")
    print(f"Sampling {num_images_per_class} image(s) per class...")
    print("-" * 60)

    for class_dir in class_dirs:
        # Collect all valid images in this class folder
        image_files = [
            f
            for f in class_dir.iterdir()
            if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS
        ]

        if not image_files:
            print(f"  [SKIP] No images found in class: {class_dir.name}")
            continue

        # Randomly sample up to num_images_per_class images
        sample_count = min(num_images_per_class, len(image_files))
        sampled_files = random.sample(image_files, sample_count)

        print(
            f"  [CLASS] {class_dir.name} — showing {sample_count} of {len(image_files)} images"
        )

        # Create a figure with one column per sampled image
        fig, axes = plt.subplots(1, sample_count, figsize=(4 * sample_count, 4))

        # Ensure axes is always iterable even when sample_count == 1
        if sample_count == 1:
            axes = [axes]

        fig.suptitle(f"Class: {class_dir.name}", fontsize=14, fontweight="bold", y=1.02)

        for ax, image_path in zip(axes, sampled_files):
            try:
                with Image.open(image_path) as img:
                    # Convert to RGB to handle palette/RGBA images uniformly
                    img_rgb = img.convert("RGB")
                    ax.imshow(img_rgb)
                    ax.set_title(image_path.name, fontsize=7, wrap=True)
                    ax.axis("off")
            except Exception as e:
                ax.set_title(f"Error\n{image_path.name}", fontsize=7, color="red")
                ax.axis("off")
                print(f"    [ERROR] Could not display {image_path.name}: {e}")

        plt.tight_layout()
        plt.show()

    print("\n--- Visual Audit Complete ---")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    # Step 1: Integrity check — detect and remove corrupted images
    run_integrity_check(DATASET_PATH)

    # Step 2: Visual audit — randomly sample and display images per class
    run_visual_audit(DATASET_PATH, num_images_per_class=NUM_IMAGES_PER_CLASS)
