import os
import shutil
import random
import yaml
from glob import glob

base_dir = "./dataset"

def create_dir_structure(base_dir):
    """ Create the required directory structure"""
    for split in ['train', 'test', 'valid']:
        os.makedirs(os.path.join(base_dir, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(base_dir, split, 'labels'), exist_ok=True)
    print(f"Created directory structure in {base_dir}")

def copy_files(file_list, split, base_dir='dataset'):
    """ Move/copy files to appropriate directory."""
    for file_path in file_list:
        file_name = os.path.basename(file_path)
        if file_name.endswith('.txt'):
            dest = os.path.join(base_dir, split, 'labels', file_name)
        else:
            dest = os.path.join(base_dir, split, 'images', file_name)
        shutil.copy(file_path, dest)
        print(f"Copied {file_path} to {dest}")

def split_dataset(images_dir, labels_dir, base_dir):
    """ Split the dataset according to the specified rules."""
    image_files = glob(os.path.join(images_dir, '*.jpg')) + glob(os.path.join(images_dir, '*.png')) + glob(os.path.join(images_dir, '*.PNG'))
    label_files = glob(os.path.join(labels_dir, '*.txt')) 
    
    print(f"Found {len(image_files)} image files and {len(label_files)} label files")
    
    train_images, test_images, valid_images = [], [], []
    
    for img_file in image_files:
        file_name = os.path.basename(img_file)
        prefix = file_name[:2].upper()
        print(f"Checking file name: {file_name} with prefix: {prefix}")
        
        if prefix == 'TR':
            train_images.append(img_file)
        elif prefix == 'TE':
            test_images.append(img_file)
        elif prefix == 'VA':
            valid_images.append(img_file)
        else:
            train_images.append(img_file)
    
    # If no explicit prefix is found, split based on 70-20-10
    remaining_images = [img for img in image_files if img not in train_images + test_images + valid_images]

    random.shuffle(remaining_images)
    num_images = len(remaining_images)
    train_split = int(0.7 * num_images)
    valid_split = int(0.2 * num_images)

    train_images += remaining_images[:train_split]
    valid_images += remaining_images[train_split:train_split + valid_split]
    test_images += remaining_images[train_split + valid_split:]

    print(f"Split results: Train: {len(train_images)}, Valid: {len(valid_images)}, Test: {len(test_images)}")

    train_labels = [os.path.join(labels_dir, os.path.splitext(os.path.basename(img))[0] + '.txt') for img in train_images]
    valid_labels = [os.path.join(labels_dir, os.path.splitext(os.path.basename(img))[0] + '.txt') for img in valid_images]
    test_labels = [os.path.join(labels_dir, os.path.splitext(os.path.basename(img))[0] + '.txt') for img in test_images]

    copy_files(train_images + train_labels, 'train', base_dir)
    copy_files(valid_images + valid_labels, 'valid', base_dir)
    copy_files(test_images + test_labels, 'test', base_dir)

def generate_yaml(base_dir, class_names):
    """Generate the data.yaml file."""
    data_yaml = {
        'path': base_dir,
        'train': 'train/images',
        'val': 'valid/images',
        'test': 'test/images',
        'nc': len(class_names),
        'names': class_names
    }

    yaml_path = os.path.join(base_dir, 'data.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(data_yaml, f, default_flow_style=False)
    print(f"Generated YAML file at {yaml_path}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(script_dir, 'images')
    labels_dir = os.path.join(script_dir, 'yolo_format')
    base_dir = os.path.join(script_dir, 'dataset')  # This will be used for the output structure

    class_names = [
        "wall", "bed_room", "bathroom", "balcony", "entrance", "elevator", 
        "dressing_room", "air_room", "utility_room", "pantry", "hallway", 
        "stairs", "living_kitchen", "others", "background"
    ]

    print(f"Starting dataset processing")
    print(f"Images directory: {images_dir}")
    print(f"Labels directory: {labels_dir}")
    print(f"Output directory: {base_dir}")

    create_dir_structure(base_dir)
    split_dataset(images_dir, labels_dir, base_dir)
    generate_yaml(base_dir, class_names)
    print("Dataset processing completed.")

if __name__ == "__main__":
    main()