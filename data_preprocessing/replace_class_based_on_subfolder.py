import os
import xml.etree.ElementTree as ET
import re
import pandas as pd

def extract_center_points(file_name):
    matches = re.findall(r'\d+\.\d+', file_name)
    if len(matches) >= 2:
        center_x = float(matches[-2])
        center_y = float(matches[-1])
    else:
        raise ValueError("Could not find sufficient floating point numbers in filename: " + file_name)
    return center_x, center_y

def count_classes(xml_folder):
    class_count = {}
    for xml_file in os.listdir(xml_folder):
        if xml_file.endswith('.xml'):
            tree = ET.parse(os.path.join(xml_folder, xml_file))
            root = tree.getroot()
            for obj in root.findall('object'):
                class_name = obj.find('name').text
                if class_name not in class_count:
                    class_count[class_name] = 1
                else:
                    class_count[class_name] += 1
    return class_count

def process_xml(xml_file, image_centers, save_to):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    updated = False

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
            if abs(center_x - image_center_x) < 0.00001 and abs(center_y - image_center_y) < 0.0001:
                obj.find('name').text = subfolder
                updated = True
                break

    if updated:
        new_xml_path = os.path.join(save_to, os.path.basename(xml_file))
        tree.write(new_xml_path)
        print(f"Updated XML saved to: {new_xml_path}")
    else:
        print(f"No updates for XML: {xml_file}")

def prepare_image_data(class_data_folder):
    image_centers = []
    for root, dirs, files in os.walk(class_data_folder):
        for image_file in files:
            if image_file.endswith(('.png', '.jpg', '.PNG')):
                try:
                    image_center_x, image_center_y = extract_center_points(image_file)
                    subfolder = os.path.basename(root)
                    image_centers.append((image_center_x, image_center_y, subfolder))
                except ValueError as e:
                    print(e)
    print(f"Total center points: {len(image_centers)}")
    return image_centers

if __name__ == '__main__':
    class_data_folder = './raw_data-v2/direction/direction_case'
    xml_files_folder = './raw_data-v2/direction/xmls'
    save_to_folder = './raw_data-v2/direction/xmls_direction-v2'
    os.makedirs(save_to_folder, exist_ok=True)

    # Count old class instances
    old_class_count = count_classes(xml_files_folder)
    
    # Prepare image centers
    image_centers = prepare_image_data(class_data_folder)

    # Process XML files
    for xml_file in os.listdir(xml_files_folder):
        if xml_file.endswith('.xml'):
            xml_path = os.path.join(xml_files_folder, xml_file)
            process_xml(xml_path, image_centers, save_to_folder)

    # Count new class instances
    # new_class_count = count_classes(save_to_folder)

    # # Convert counts to DataFrame for display
    # df_old = pd.DataFrame(list(old_class_count.items()), columns=['Class', 'Old Instances'])
    # df_new = pd.DataFrame(list(new_class_count.items()), columns=['Class', 'New Instances'])
    # df = pd.merge(df_old, df_new, on='Class', how='outer').fillna(0)
    # df['Old Instances'] = df['Old Instances'].astype(int)
    # df['New Instances'] = df['New Instances'].astype(int)

    # print(df)
