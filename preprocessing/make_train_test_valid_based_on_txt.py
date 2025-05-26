import os
import shutil
from pathlib import Path

# --- Setup ---
image_src = Path("./img")
label_src = Path("./labels")
list_files = {
    'train': Path('./all_train.txt'),
    'valid': Path('./all_valid.txt'),
    'test': Path('./all_test.txt'),
}
output_root = Path('./train_dataset')

# --- Create folder structure ---
for split in ['train', 'valid', 'test']:
    (output_root / split / 'images').mkdir(parents=True, exist_ok=True)
    (output_root / split / 'labels').mkdir(parents=True, exist_ok=True)

# --- Supported image extensions ---
image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
image_extensions = set(ext.lower() for ext in image_extensions)

# --- Copy files based on each split ---
for split, txt_file in list_files.items():
    with open(txt_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    for name in lines:
        name = name.strip()
        if not name:
            continue

        stem = Path(name).stem

        # --- Copy image ---
        found_image = None
        for ext in image_extensions:
            img_path = image_src / f"{stem}{ext}"
            if img_path.exists():
                found_image = img_path
                break

        if found_image:
            shutil.copy(found_image, output_root / split / 'images' / found_image.name)
        else:
            print(f"[WARN] Image not found for: {name}")

        # --- Copy label ---
        label_path = label_src / f"{stem}.txt"
        if label_path.exists():
            shutil.copy(label_path, output_root / split / 'labels' / label_path.name)
        else:
            print(f"[WARN] Label not found for: {name}")

print("\n✅ Dataset organized into train_dataset/{train,valid,test}/[images|labels]")
