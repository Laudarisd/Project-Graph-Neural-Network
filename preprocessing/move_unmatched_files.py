import os
import shutil
from pathlib import Path

# --- Config ---
image_dir = Path("./img")
txt_dir = Path("./labels")
not_found_dir = Path("./file_not_found")
not_found_dir.mkdir(exist_ok=True)

# Supported image extensions (case-insensitive)
image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
image_extensions = set(ext.lower() for ext in image_extensions)

# --- Collect Files ---
image_files = [f for f in image_dir.iterdir() if f.suffix.lower() in image_extensions]
txt_files = list(txt_dir.glob("*.txt"))

image_basenames = {f.stem for f in image_files}
txt_basenames = {f.stem for f in txt_files}

# --- Identify Unmatched Files ---
only_images = image_basenames - txt_basenames
only_txts = txt_basenames - image_basenames

# --- Move Unmatched Image Files ---
for image_path in image_files:
    if image_path.stem in only_images:
        shutil.move(str(image_path), not_found_dir / image_path.name)

# --- Move Unmatched TXT Files ---
for txt_path in txt_files:
    if txt_path.stem in only_txts:
        shutil.move(str(txt_path), not_found_dir / txt_path.name)

# --- Summary ---
print(f"✅ Moved {len(only_images)} image(s) and {len(only_txts)} txt file(s) to ./file_not_found/")
