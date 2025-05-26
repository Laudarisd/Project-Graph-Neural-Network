import os
import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
from labelme import utils

def load_image(image_path):
    return cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)

def load_json(json_path):
    with open(json_path) as f:
        data = json.load(f)
    return data

def create_mask(label_data, img_shape):
    label_name_to_value = {'_background_': 0}
    for shape in label_data['shapes']:
        label_name = shape['label']
        if label_name in label_name_to_value:
            label_value = label_name_to_value[label_name]
        else:
            label_value = len(label_name_to_value)
            label_name_to_value[label_name] = label_value
    lbl, _ = utils.shapes_to_label(img_shape, label_data['shapes'], label_name_to_value)
    return lbl, label_name_to_value

def apply_mask(image, mask, label_name_to_value, alpha=0.5):
    # Generate consistent colors for labels
    colors = {label: tuple(np.random.RandomState(label).randint(0, 255, 3).tolist()) 
              for label in label_name_to_value.values()}
    
    output = image.copy()
    for label, color in colors.items():
        output[mask == label] = alpha * np.array(color) + (1 - alpha) * output[mask == label]
    
    return output, colors

def visualize_and_save_segmentation(image_folder, json_folder, output_folder, alpha=0.5):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    for image_file in image_files:
        image_path = os.path.join(image_folder, image_file)
        json_path = os.path.join(json_folder, image_file.replace('.jpg', '.json').replace('.png', '.json'))

        if not os.path.exists(json_path):
            continue

        # Load image and label data
        image = load_image(image_path)
        label_data = load_json(json_path)
        mask, label_name_to_value = create_mask(label_data, image.shape[:2])

        # Apply mask and get color mapping
        segmented_image, colors = apply_mask(image, mask, label_name_to_value, alpha)

        # Prepare legend data
        label_names = {v: k for k, v in label_name_to_value.items()}
        
        # Calculate figure size with extra space for legend
        extra_width_ratio = 0.3  # 30% extra width for legend
        figsize = (
            (image.shape[1] * (1 + extra_width_ratio)) / 100, 
            image.shape[0] / 100
        )
        
        # Create figure with explicit white background
        plt.figure(figsize=figsize, dpi=100, facecolor='white')
        plt.subplots_adjust(wspace=0, hspace=0)
        
        # Plot segmented image
        plt.imshow(segmented_image)
        plt.axis('off')
        
        # Add legend on the right side
        legend_labels = [label_names[label] for label in sorted(label_names.keys()) if label != 0]
        legend_colors = [np.array(colors[label])/255.0 for label in sorted(label_names.keys()) if label != 0]
        
        # Create legend patches
        legend_patches = [plt.Rectangle((0,0), 1, 1, fc=color) for color in legend_colors]
        
        # Add legend
        plt.legend(legend_patches, legend_labels, 
                   title='Segmentation Classes',
                   loc='center left', 
                   bbox_to_anchor=(1, 0.5), 
                   frameon=True)
        
        # Adjust layout to prevent cutting off legend
        plt.tight_layout()
        
        # Save the image with white background
        output_path = os.path.join(output_folder, image_file)
        plt.savefig(output_path, 
                    bbox_inches='tight', 
                    dpi=100, 
                    facecolor='white', 
                    edgecolor='none')
        plt.close()

        print(f'Saved masked image to {output_path}')

# Change these paths to your folders
image_folder = './images'
json_folder = './json'
output_folder = './output'

visualize_and_save_segmentation(image_folder, json_folder, output_folder, alpha=0.2)