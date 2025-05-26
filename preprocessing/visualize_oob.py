import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt


def draw_yolo_obb(img_path, annotation_path, class_file):
    # Load image
    img = cv2.imread(str(img_path))
    if img is None:
        raise FileNotFoundError(f"Image not found: {img_path}")

    # Load class names
    with open(class_file, "r") as f:
        class_names = [line.strip() for line in f.readlines()]

    # Load annotations
    with open(annotation_path, "r") as f:
        lines = f.readlines()

    # Skip the "YOLO_OBB" header if present
    if lines[0].strip().upper() == "YOLO_OBB":
        lines = lines[1:]

    # Draw each bounding box
    for line in lines:
        values = line.strip().split()
        if len(values) != 6:
            print(f"Skipping malformed line: {line.strip()}")
            continue

        cls_id, cx, cy, w, h, angle = values
        cls_id = int(cls_id)
        if cls_id < 0 or cls_id >= len(class_names):
            print(f"Skipping invalid class ID {cls_id}")
            class_name = f"class_{cls_id}"
        else:
            class_name = class_names[cls_id]

        cx, cy, w, h, angle = map(float, [cx, cy, w, h, angle])
        box = cv2.boxPoints(((cx, cy), (w, h), angle))
        box = np.intp(box)

        # Draw box
        cv2.drawContours(img, [box], 0, (0, 255, 0), 2)
        cv2.putText(img, class_name, (int(cx), int(cy)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 1, cv2.LINE_AA)

    # Convert to RGB for display
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(10, 10))
    plt.imshow(img_rgb)
    plt.axis("off")
    plt.title(f"Visualisation: {img_path.name}")
    plt.show()

    return img_rgb


# --- Paths ---

num = 32
img_path = Path(f"./images/{num}.png")
annotation_path = Path(f"./object/{num}.txt")
class_file = Path("./object/classes.txt")

# --- Draw and Show ---
result = draw_yolo_obb(img_path, annotation_path, class_file)

# Display the result
cv2.imshow("YOLO OBB Visualization", result)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Optionally, save:
# cv2.imwrite("visualized_32.png", result)
