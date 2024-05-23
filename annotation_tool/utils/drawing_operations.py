import os
import csv
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtWidgets import QFileDialog, QGraphicsRectItem
from PyQt5.QtGui import QPen, QColor
import xml.etree.ElementTree as ET

def upload_folder(fileListWidget):
    folder = QFileDialog.getExistingDirectory(None, "Select Folder")
    if folder:
        imageFiles = [os.path.join(folder, file) for file in os.listdir(folder) if file.lower().endswith(('png', 'jpg', 'jpeg'))]
        fileListWidget.clear()
        for file in imageFiles:
            fileListWidget.addItem(os.path.basename(file))
        return imageFiles
    return []

def save_data_as(saveFolder):
    folder = QFileDialog.getExistingDirectory(None, "Select Folder to Save Annotations")
    if folder:
        return folder
    return saveFolder

def save_pascal_voc(imageFile, boxes, imageSize, saveFolder):
    annotation = ET.Element("annotation")
    ET.SubElement(annotation, "folder").text = os.path.basename(os.path.dirname(imageFile))
    ET.SubElement(annotation, "filename").text = os.path.basename(imageFile)
    
    size = ET.SubElement(annotation, "size")
    ET.SubElement(size, "width").text = str(imageSize[0])
    ET.SubElement(size, "height").text = str(imageSize[1])
    ET.SubElement(size, "depth").text = "3"
    
    for box in boxes:
        obj = ET.SubElement(annotation, "object")
        ET.SubElement(obj, "name").text = "class_name"
        bndbox = ET.SubElement(obj, "bndbox")
        rect = box.rect()
        ET.SubElement(bndbox, "xmin").text = str(int(rect.left()))
        ET.SubElement(bndbox, "ymin").text = str(int(rect.top()))
        ET.SubElement(bndbox, "xmax").text = str(int(rect.right()))
        ET.SubElement(bndbox, "ymax").text = str(int(rect.bottom()))
    
    tree = ET.ElementTree(annotation)
    xml_file = os.path.join(saveFolder, os.path.splitext(os.path.basename(imageFile))[0] + ".xml")
    tree.write(xml_file)

def load_boxes(imageFile):
    xml_file = os.path.splitext(imageFile)[0] + ".xml"
    boxes = []
    if os.path.exists(xml_file):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for obj in root.findall("object"):
            bndbox = obj.find("bndbox")
            xmin = int(bndbox.find("xmin").text)
            ymin = int(bndbox.find("ymin").text)
            xmax = int(bndbox.find("xmax").text)
            ymax = int(bndbox.find("ymax").text)
            rect = QRectF(QPointF(xmin, ymin), QPointF(xmax, ymax))
            box = QGraphicsRectItem(rect)
            box.setPen(QPen(QColor(255, 0, 0), 2))
            boxes.append(box)
    return boxes

def load_lines(imageFile):
    csv_file = os.path.splitext(imageFile)[0] + ".csv"
    lines = []
    if os.path.exists(csv_file):
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                start = QPointF(float(row["Start X"]), float(row["Start Y"]))
                end = QPointF(float(row["End X"]), float(row["End Y"]))
                lines.append((start, end))
    return lines

def save_lines(imageFile, lines, saveFolder):
    csv_file = os.path.join(saveFolder, os.path.splitext(os.path.basename(imageFile))[0] + ".csv")
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Index", "Start X", "Start Y", "End X", "End Y"])
        for i, (start, end) in enumerate(lines):
            writer.writerow([i, int(start.x()), int(start.y()), int(end.x()), int(end.y())])
