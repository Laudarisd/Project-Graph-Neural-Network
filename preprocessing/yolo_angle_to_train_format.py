import math
from pathlib import Path
import shutil
from PIL import Image
import numpy as np


def convert_to_corners(class_id, center_x, center_y, width, height, angle, img_width, img_height):
    angle_rad = np.radians(angle)
    half_width = width / 2
    half_height = height / 2

    corners = np.array([
        [-half_width, -half_height],
        [half_width, -half_height],
        [half_width, half_height],
        [-half_width, half_height]
    ])

    rotation_matrix = np.array([
        [np.cos(angle_rad), -np.sin(angle_rad)],
        [np.sin(angle_rad), np.cos(angle_rad)]
    ])

    rotated_corners = np.dot(corners, rotation_matrix)
    corners_x = rotated_corners[:, 0] + center_x
    corners_y = rotated_corners[:, 1] + center_y

    # Normalize to YOLO format (0 to 1)
    corners_x /= img_width
    corners_y /= img_height

    corners = [corners_x[0], corners_y[0], corners_x[1], corners_y[1],
               corners_x[2], corners_y[2], corners_x[3], corners_y[3]]

    return [int(class_id)] + corners


# Dataset split folders
splits = ['train', 'valid', 'test']
src_root = Path('./raw_dataset')
dst_root = Path('./train_oob_final')

for split in splits:
    src_img_dir = src_root / split / 'images'
    src_lbl_dir = src_root / split / 'labels'
    dst_img_dir = dst_root / split / 'images'
    dst_lbl_dir = dst_root / split / 'labels'
    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)

    for txt_file in src_lbl_dir.glob("*.txt"):
        base_name = txt_file.stem
        img_path = None

        # Try to find matching image file
        for ext in ['.png', '.jpg', '.jpeg']:
            test_img_path = src_img_dir / f"{base_name}{ext}"
            if test_img_path.exists():
                img_path = test_img_path
                break

        if not img_path:
            print(f"Image not found for {txt_file.name}, skipping.")
            continue

        with Image.open(img_path) as img:
            img_width, img_height = img.size

        with open(txt_file, 'r') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) != 6:
                continue
            cls, cx, cy, w, h, angle = map(float, parts)
            corners = convert_to_corners(cls, cx, cy, w, h, angle, img_width, img_height)
            cls_str = str(int(corners[0]))
            coords_str = " ".join(f"{c:.6f}" for c in corners[1:])
            new_lines.append(f"{cls_str} {coords_str}\n")

        with open(dst_lbl_dir / txt_file.name, 'w') as f:
            f.writelines(new_lines)

        shutil.copy(img_path, dst_img_dir / img_path.name)

print("\n All labels converted to normalized 4-corner format with clean integer class IDs and dataset organized into train_oob_final/")
