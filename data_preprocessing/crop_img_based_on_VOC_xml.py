from collections import defaultdict
import csv
import errno
from PIL import Image
import xml.etree.ElementTree as ET
import os
import glob

class XMLParser:
    def __init__(self, img_folder, dst, xmls):
        self.img_folder = img_folder
        self.dst = dst
        self.xmls = xmls
        self.seed_arr = []
        self.img_class_counts = defaultdict(lambda: defaultdict(int))

    def check_folder_exists(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                print('create ' + path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

    def parse_xml_files(self):
        for xml_file in glob.glob(os.path.join(self.xmls, '*.xml')):
            self.parse_xml_file(xml_file)

    def parse_xml_file(self, xml_file):
        root = ET.parse(xml_file).getroot()
        filename = root.find('filename').text

        for type_tag in root.findall('size'):
            width = type_tag.find('width').text
            height = type_tag.find('height').text

        for type_tag in root.findall('object'):
            class_name = type_tag.find('name').text
            self.img_class_counts[filename][class_name] += 1
            xmin = type_tag.find('bndbox/xmin').text
            ymin = type_tag.find('bndbox/ymin').text
            xmax = type_tag.find('bndbox/xmax').text
            ymax = type_tag.find('bndbox/ymax').text
            all_list = [filename, width, height, class_name, xmin, ymin, xmax, ymax]
            self.seed_arr.append(all_list)

    def save_results_to_csv(self, csv_file):
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['img_name', 'class', 'total'])
            for img_name, class_counts in self.img_class_counts.items():
                for class_name, count in class_counts.items():
                    writer.writerow([img_name, class_name, count])

    def print_results(self):
        print("img_name | class | total")
        for img_name, class_counts in self.img_class_counts.items():
            for class_name, count in class_counts.items():
                print(f"{img_name} | {class_name} | {count}")

    def save_images(self):
        self.seed_arr.sort()
        unique_class = set()
        for index, line in enumerate(self.seed_arr):
            filename, width, height, class_name, xmin, ymin, xmax, ymax = line
            unique_class.add(class_name)
            load_img_path = os.path.join(self.img_folder, filename)
            if not os.path.exists(load_img_path):
                print(f"Image file not found: {load_img_path}")
                continue

            save_class_path = os.path.join(self.dst, class_name)
            self.check_folder_exists(save_class_path)
            save_img_path = os.path.join(save_class_path, f"{index}_{filename}")

            filename_without_ext = os.path.splitext(filename)[0]
            save_img_path = os.path.join(save_class_path, f"{index}_{filename_without_ext}")

            # Calculate centered points x, y
            x_center = (int(xmin) + int(xmax)) / 2
            y_center = (int(ymin) + int(ymax)) / 2

            # Format with 6 decimal places
            x_center = format(x_center, ".6f")
            y_center = format(y_center, ".6f")

            # Include center point in image file name
            save_img_path = f"{save_img_path}_{x_center}_{y_center}.{filename.split('.')[-1]}"

            img = Image.open(load_img_path)
            crop_img = img.crop((int(xmin), int(ymin), int(xmax), int(ymax)))
            newsize = (224, 224)
            im1 = crop_img.resize(newsize)
            im1.save(save_img_path, 'PNG')

            print(f"Unique class name: {class_name}")
            print('save ' + save_img_path)

if __name__ == '__main__':
    img_folder = './raw_data_I_changed/images'
    dst = './raw_data_I_changed/cropped_img/'
    xmls = './raw_data_I_changed/direction_xmls'
    csv_file = './results.csv'

    parser = XMLParser(img_folder, dst, xmls)
    parser.parse_xml_files()
    parser.save_results_to_csv(csv_file)
    parser.print_results()
    parser.save_images()