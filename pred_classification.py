import os
from ultralytics import YOLO
import shutil

# Load the model
model = YOLO('./runs/classify/train/weights/best.pt')
desired_classes = ['wall', 'window', 'door', 'symbol']
probability_threshold = 0.995
image_paths = []

# Collect all image paths from the test directory and its subdirectories
for root, dirs, files in os.walk('./cad_data'):
    for file in files:
        if file.endswith(('.jpg', '.jpeg', '.png')):  # Adjust extensions as needed
            image_paths.append(os.path.join(root, file))

# Directory to save the filtered images
filtered_dir = './filtered_layers'
os.makedirs(filtered_dir, exist_ok=True)

# Open a text file to save the results with UTF-8 encoding
with open('classification_results.txt', 'w', encoding='utf-8') as result_file:
    # Perform inference on each image and filter based on the predicted class and probability
    for image_path in image_paths:
        results = model(image_path, imgsz=1024)
        
        for result in results:
            # Check if the result has the 'probs' attribute
            if hasattr(result, 'probs'):
                top1_index = result.probs.top1
                top1_conf = result.probs.top1conf.item()  # Get the confidence score as a float
                classes = result.names
                predicted_class = classes[top1_index]

                if predicted_class in desired_classes and top1_conf >= probability_threshold:
                    shutil.copy(image_path, filtered_dir)
                    result_text = f"Image: {image_path}, Class: {predicted_class}, Probability: {top1_conf}\n"
                else:
                    result_text = f"Image: {image_path}, Class: {predicted_class}, Probability: {top1_conf} - Ignored\n"

                # Write the result to the text file
                result_file.write(result_text)
            else:
                result_file.write(f"Image: {image_path}, No probabilities found in results\n")
