"""
This code changes class name based on folder name where the are saved.
To compare original file and class images, it compares the file with center point of the image.
"""

import os
import xml.etree.ElementTree as ET
from PIL import Image
import re

def extract_center_points(file_name):
    matches = re.findall(r'\d+\.\d+', file_name)
    if len(matches) >= 2:
        center_x = float(matches[-2])
        center_y = float(matches[-1])
    else:
        raise ValueError("Could not find sufficient floating point numbers in filename: " + file_name)
    return center_x, center_y

def process_xml(xml_file, class_data_folder, image_centers):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for obj in root.findall('object'):
        bbox = obj.find('bndbox')
        xmin = float(bbox.find('xmin').text)
        xmax = float(bbox.find('xmax').text)
        ymin = float(bbox.find('ymin').text)
        ymax = float(bbox.find('ymax').text)
        center_x = (xmin + xmax) / 2
        center_y = (ymin + ymax) / 2
        # Compare centers and adjust XML only if a match is found
        for (image_center_x, image_center_y, subfolder) in image_centers:
            if abs(center_x - image_center_x) < 0.00001 and abs(center_y - image_center_y) < 0.00001:
                obj.find('name').text = subfolder
                break
    tree.write(xml_file)

def prepare_image_data(class_data_folder):
    image_centers = []
    for subfolder in os.listdir(class_data_folder):
        if not subfolder.startswith('.'):  # Ignore hidden files
            subfolder_path = os.path.join(class_data_folder, subfolder)
            for image_file in os.listdir(subfolder_path):
                if image_file.endswith(('.png', '.jpg', '.PNG')):
                    try:
                        image_center_x, image_center_y = extract_center_points(image_file)
                        image_centers.append((image_center_x, image_center_y, subfolder))
                    except ValueError as e:
                        print(e)
    return image_centers

def main():
    xml_folder = './raw_data_I_changed/direction_xmls'
    class_data_folder = './class_data_refined_I/junc_I'
    image_centers = prepare_image_data(class_data_folder)  # Pre-load image center data
    for xml_file in os.listdir(xml_folder):
        if xml_file.endswith('.xml'):
            xml_path = os.path.join(xml_folder, xml_file)
            process_xml(xml_path, class_data_folder, image_centers)

if __name__ == "__main__":
    main()
