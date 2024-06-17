import cv2
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO
import os
import shutil
import colorsys

# Initialize YOLO models once
model_classification = YOLO("./models/classification_best.pt")
model_detection = YOLO('./models/best_augmented.pt')

img_path = './original_img/1.png'  # Main image
layer_dir = './filtered_layers/'  # Directory containing layer images
result_dir = './result/'  # Directory to store similar images
classify_dir = './cad_data/'
desired_class = ['door_normal', 'window']
classification_class = ["door", "window"]
classification_threshold = 0.999

# Initialize colors
hsv_tuples = [(x / len(desired_class), 1., 1.) for x in range(len(desired_class))]
colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
colors = list(map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)), colors))

# Create result directories
os.makedirs(result_dir, exist_ok=True)
original_detection_dir = os.path.join('original_detection')
os.makedirs(original_detection_dir, exist_ok=True)
os.makedirs(layer_dir, exist_ok=True)

# Classification and copying to filtered_layers
for img in os.listdir(classify_dir):
    if img.lower().endswith(('.png', '.jpg', '.jpeg')):
        img_path_full = os.path.join(classify_dir, img)
        results = model_classification.predict(img_path_full, imgsz=1024)
        for result in results:
            if hasattr(result, 'probs'):
                top1_index = result.probs.top1
                top1_conf = result.probs.top1conf.item()
                classes = result.names
                predicted_class = classes[top1_index]
                if predicted_class in classification_class and top1_conf > classification_threshold:
                    shutil.copy2(img_path_full, os.path.join(layer_dir, img))
                    print(f"Image {img} has been copied to the '{layer_dir}' directory.")
                    break

for cls in desired_class:
    os.makedirs(os.path.join(result_dir, cls), exist_ok=True)

# Load the original image and perform detection
original_img = cv2.imread(img_path)
original_img_with_boxes = original_img.copy()

results = model_detection.predict(img_path, imgsz=1024)

detection_details = []
for result in results:
    for idx, cls in enumerate(result.boxes.cls):
        class_index = int(cls)
        class_name = result.names[class_index]
        if class_name in desired_class:
            box = result.boxes.xyxy[idx].cpu().numpy().astype(np.int32)
            detection_details.append([class_name, (box[0], box[1], box[2], box[3])])

            # Draw bounding box on the original image
            color = colors[desired_class.index(class_name)]
            cv2.rectangle(original_img_with_boxes, (box[0], box[1]), (box[2], box[3]), color, 2)
            cv2.putText(original_img_with_boxes, class_name, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

# Save the original image with detections
original_img_filename = os.path.basename(img_path)
cv2.imwrite(os.path.join(original_detection_dir, f'detected_{original_img_filename}'), original_img_with_boxes)

# Dictionary to store results
similar_images = {cls: [] for cls in desired_class}
different_images = {cls: [] for cls in desired_class}

# Process each image in the layer directory
for layer_filename in os.listdir(layer_dir):
    if layer_filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        layer_path = os.path.join(layer_dir, layer_filename)
        layer_img_original = cv2.imread(layer_path)
        layer_img = layer_img_original.copy()

        for current_class in desired_class:
            matching_score_list = []

            # Draw bounding boxes on the layer image
            for class_name, (x1, y1, x2, y2) in detection_details:
                if class_name == current_class:
                    cv2.rectangle(layer_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Process each detection of the current class
            for idx, (class_name, (x1, y1, x2, y2)) in enumerate(detection_details):
                if class_name != current_class:
                    continue

                crop = 2
                original_roi = original_img[y1 + crop:y2 - crop, x1 + crop:x2 - crop]
                layer_roi = layer_img_original[y1 + crop:y2 - crop, x1 + crop:x2 - crop]

                if original_roi.size == 0 or layer_roi.size == 0:
                    continue  # Skip if any ROI is empty

                original_gray = cv2.cvtColor(original_roi, cv2.COLOR_BGR2GRAY)
                layer_gray = cv2.cvtColor(layer_roi, cv2.COLOR_BGR2GRAY)

                _, original_binary = cv2.threshold(original_gray, 128, 255, cv2.THRESH_BINARY_INV)
                _, layer_binary = cv2.threshold(layer_gray, 128, 255, cv2.THRESH_BINARY_INV)

                intersection = np.logical_and(original_binary, layer_binary)
                union = np.logical_or(original_binary, layer_binary)
                iou = np.sum(intersection) / np.sum(union)
                similarity_percentage = iou * 100

                matching_score_list.append(int(similarity_percentage))

            filter_list = [i for i in matching_score_list if i > 2]
            average_matching_score = sum(filter_list) / len(filter_list) if len(filter_list) > 0 else 0

            if average_matching_score > 36:
                similar_images[current_class].append((layer_filename, average_matching_score))
                shutil.copy2(layer_path, os.path.join(result_dir, current_class, layer_filename))
            else:
                different_images[current_class].append((layer_filename, average_matching_score))

            print(f"Processed {layer_filename} for {current_class}: Average Matching Score = {average_matching_score:.2f}%")

# Print summary
for cls in desired_class:
    print(f"\nClass: {cls}")
    print("Similar Images (score > 36%):")
    for img, score in similar_images[cls]:
        print(f"{img}: {score:.2f}%")

    print("\nDifferent Images (score <= 36%):")
    for img, score in different_images[cls]:
        print(f"{img}: {score:.2f}%")

    print(f"\nSimilar images for {cls} have been copied to the '{os.path.join(result_dir, cls)}' directory.")

print(f"\nOriginal image with detections has been saved to '{original_detection_dir}'.")
