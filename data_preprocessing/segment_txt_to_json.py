import os
import json
import cv2
import base64

def get_image_size(image_path):
    image = cv2.imread(image_path)
    return image.shape[1], image.shape[0]  # width, height

def yolo_to_labelme(yolo_path, images_folder, output_folder, relative_image_path_prefix):
    ensure_dir(output_folder)
    for yolo_file in os.listdir(yolo_path):
        if yolo_file.endswith('.txt'):
            image_name_png = yolo_file.replace('.txt', '.png')
            image_name_jpg = yolo_file.replace('.txt', '.jpg')
            image_name_PNG = yolo_file.replace('.txt', '.PNG')

            image_path_png = os.path.join(images_folder, image_name_png)
            image_path_jpg = os.path.join(images_folder, image_name_jpg)
            image_path_PNG = os.path.join(images_folder, image_name_PNG)

            if os.path.exists(image_path_png):
                image_path = image_path_png
            elif os.path.exists(image_path_jpg):
                image_path = image_path_jpg
            elif os.path.exists(image_path_PNG):
                image_path = image_path_PNG
            else:
                print(f"Image for {yolo_file} not found.")
                continue

            width, height = get_image_size(image_path)
            shapes = []

            with open(os.path.join(yolo_path, yolo_file), 'r') as file:
                for line in file:
                    data = line.split()
                    label = data[0]
                    points = [(float(data[i]) * width, float(data[i+1]) * height) for i in range(1, len(data), 2)]
                    shapes.append({
                        "label": label,
                        "points": points,
                        "group_id": None,
                        "description": "",
                        "shape_type": "polygon",
                        "flags": {},
                        "mask": None
                    })

            json_data = {
                "version": "5.4.1",
                "flags": {},
                "shapes": shapes,
                "imagePath": os.path.join(relative_image_path_prefix, os.path.basename(image_path)).replace("/", "\\"),
                "imageData": None,
                "imageHeight": height,
                "imageWidth": width
            }

            output_json_path = os.path.join(output_folder, yolo_file.replace('.txt', '.json'))
            with open(output_json_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            print(f"Converted {yolo_file} to {output_json_path}")

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Define paths
yolo_path = './json'
images_folder = './images'
output_folder = './output_json'
relative_image_path_prefix = '..\\raw_data-v2\\images'

# Run the conversion
yolo_to_labelme(yolo_path, images_folder, output_folder, relative_image_path_prefix)
