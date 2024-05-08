import os
import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout,
                             QWidget, QFileDialog, QListWidget, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QScrollArea, QSplitter, QShortcut)
from PyQt5.QtGui import QPainter, QPen, QPixmap, QKeySequence, QIcon, QCursor
from PyQt5.QtCore import Qt, QPoint, QSize


class ExtraFeatures(QWidget, ):
    def __init__(self, imageList, label):
        super().__init__()
        self.points = []
        self.lines = []
        self.current_image = None
        self.current_image_path = ''
        self.drawing = False
        self.start_point = None
        self.temp_point = None
        self.point_radius = 6
        self.zoom_scale = 1.0
        self.imageList = imageList  # Now ExtraFeatures has access to imageList
        self.label = label  # Now ExtraFeatures has access to label




    def uploadFiles(self):
        filePaths, _ = QFileDialog.getOpenFileNames(self, 'Select Images', '', 'Image Files (*.jpg *.jpeg *.png *.bmp *.gif)')
        if filePaths:
            self.image_paths = filePaths
            self.imageList.clear()
            for path in filePaths:
                self.imageList.addItem(os.path.basename(path))
            self.imageList.setCurrentRow(0)
            self.showImage(self.imageList.currentItem())

    def zoomIn(self):
        self.zoom_scale *= 1.25
        self.label.resize(self.zoom_scale * self.label.pixmap().size())

    def zoomOut(self):
        self.zoom_scale *= 0.8
        self.label.resize(self.zoom_scale * self.label.pixmap().size())

    def toggleDrawingMode(self):
        self.drawing = not self.drawing
        if self.drawing:
            self.label.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.label.setCursor(QCursor(Qt.ArrowCursor))

    def showImage(self, item):
        image_path = self.image_paths[self.imageList.row(item)]
        self.current_image = QPixmap(image_path)
        self.label.setPixmap(self.current_image)
        self.label.resize(self.zoom_scale * self.current_image.size())
        self.update()

    def abortTask(self):
        self.drawing = False
        self.start_point = None
        self.points.clear()
        self.lines.clear()
        self.updatePointsTable()
        self.update()

    def undo(self):
        if self.lines:
            self.lines.pop()
            self.points.pop()
            self.updatePointsTable()
            self.update()
    def previousImage(self):
        current_index = self.imageList.currentRow()
        if current_index > 0:
            self.imageList.setCurrentRow(current_index - 1)
            self.showImage(self.imageList.currentItem())
    def nextImage(self):
        current_index = self.imageList.currentRow()
        if current_index < len(self.image_paths) - 1:
            self.imageList.setCurrentRow(current_index + 1)
            self.showImage(self.imageList.currentItem())
    
    # ctrl + s to save annotations
    def saveAnnotations(self):
        os.makedirs('csv_annotations', exist_ok=True)
        image_name = os.path.basename(self.current_image_path)
        csv_path = os.path.join('csv_annotations', f"{image_name.split('.')[0]}.csv")
        df = pd.DataFrame(self.lines, columns=['start_coordinates', 'end_coordinates'])
        df.to_csv(csv_path, index=False)
        print(f'Annotations for {image_name} saved.')