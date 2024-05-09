import os
import xml.etree.ElementTree as ET
from collections import defaultdict

def count_classes_in_xmls(directories):
    class_counts = defaultdict(int)
    for dir in directories:
        for filename in os.listdir(dir):
            #print(f"Check files {filename}")
            if filename.endswith('.xml'):
                filepath = os.path.join(dir, filename)
                tree = ET.parse(filepath)
                root = tree.getroot()
                for obj in root.findall('object'):
                    class_name = obj.find('name').text
                    class_counts[class_name] += 1
    return class_counts

if __name__ == "__main__":
    directories = ['./raw_data_I_changed/direction_xmls']
    class_counts = count_classes_in_xmls(directories)
    #print(class_counts)
    
    print("{:<10} | {:<5}".format('Classes', 'Total'))
    print("-" * 20)
    for class_name, count in class_counts.items():
        print("{:<10} | {:<5}".format(class_name, count))
