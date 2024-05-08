import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout,
                             QWidget, QFileDialog, QListWidget, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QScrollArea, QSplitter, QShortcut)
from PyQt5.QtGui import QPainter, QPen, QPixmap, QKeySequence, QIcon, QCursor
from PyQt5.QtCore import Qt, QPoint, QSize

class AnnotationTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.points = []
        self.lines = []
        self.current_image = None
        self.current_image_path = ''
        self.drawing = False
        self.start_point = None
        self.temp_point = None
        self.point_radius = 6
        self.zoom_scale = 1.0

    def initUI(self):
        self.setWindowTitle('Pose Annotation Tool')
        self.setGeometry(100, 100, 1200, 800) # Set the window size

        mainSplitter = QSplitter(Qt.Horizontal, self)
        leftWidget = QWidget()
        leftLayout = QVBoxLayout(leftWidget)
        uploadButton = QPushButton('Upload Files')
        uploadButton.clicked.connect(self.uploadFiles)
        zoomInButton = QPushButton('Zoom In')
        zoomInButton.clicked.connect(self.zoomIn)
        zoomOutButton = QPushButton('Zoom Out')
        zoomOutButton.clicked.connect(self.zoomOut)
        self.imageList = QListWidget()
        self.imageList.itemClicked.connect(self.showImage)
        leftLayout.addWidget(uploadButton)
        leftLayout.addWidget(self.imageList)

        #add zoom in and zoom out buttons
        leftLayout.addWidget(zoomInButton)
        leftLayout.addWidget(zoomOutButton)

        self.scrollArea = QScrollArea()
        self.label = QLabel()
        self.label.setScaledContents(True)
        self.scrollArea.setWidget(self.label)
        self.scrollArea.setWidgetResizable(True)

        rightWidget = QWidget()
        rightLayout = QVBoxLayout(rightWidget)
        self.pointsTable = QTableWidget()
        self.pointsTable.setColumnCount(4)
        self.pointsTable.setHorizontalHeaderLabels(['Idx From', 'Idx To', 'Starting Coordinate', 'End Coordinate'])
        saveButton = QPushButton('Save Annotations')
        saveButton.clicked.connect(self.saveAnnotations)
        rightLayout.addWidget(self.pointsTable)
        rightLayout.addWidget(saveButton)

        mainSplitter.addWidget(leftWidget)
        mainSplitter.addWidget(self.scrollArea)
        mainSplitter.addWidget(rightWidget)
        mainSplitter.setSizes([130, 950, 130])
        self.setCentralWidget(mainSplitter)

        QShortcut(QKeySequence('Esc'), self, self.abortTask)
        QShortcut(QKeySequence('Ctrl+Z'), self, self.undo)
        QShortcut(QKeySequence('A'), self, self.previousImage)
        QShortcut(QKeySequence('D'), self, self.nextImage)
        QShortcut(QKeySequence('W'), self, self.toggleDrawingMode)
        QShortcut(QKeySequence('Ctrl+S'), self, self.saveAnnotations)

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

    def updatePointsTable(self):
        self.pointsTable.setRowCount(len(self.lines))
        for row, line in enumerate(self.lines):
            idx_from = QTableWidgetItem(str(row))
            idx_to = QTableWidgetItem(str(row + 1))
            start_item = QTableWidgetItem(str(tuple(line[0].toTuple())))
            end_item = QTableWidgetItem(str(tuple(line[1].toTuple())))
            self.pointsTable.setItem(row, 0, idx_from)
            self.pointsTable.setItem(row, 1, idx_to)
            self.pointsTable.setItem(row, 2, start_item)
            self.pointsTable.setItem(row, 3, end_item)
    def saveAnnotations(self):
        os.makedirs('csv_annotations', exist_ok=True)
        image_name = os.path.basename(self.current_image_path)
        csv_path = os.path.join('csv_annotations', f"{image_name.split('.')[0]}.csv")
        df = pd.DataFrame(self.lines, columns=['start_coordinates', 'end_coordinates'])
        df.to_csv(csv_path, index=False)
        print(f'Annotations for {image_name} saved.')

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing and self.current_image:
            point = self.getMousePosition(event)
            if point:
                self.points.append(point)
                if not self.start_point:
                    self.start_point = point
                else:
                    self.lines.append([self.start_point, point])
                    self.updatePointsTable()  # Update the table after appending the new line
                    self.start_point = point
                self.update()

    def getMousePosition(self, event):
        if self.current_image:
            mouse_pos = event.pos()
            x = mouse_pos.x() - self.label.x()
            y = mouse_pos.y() - self.label.y()
            return QPoint(x, y)
        return None

    def paintEvent(self, event):
        if self.current_image is None:
            return

        pixmap = self.current_image.copy()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(Qt.red, 6)
        painter.setPen(pen)
        for point in self.points:
            scaled_point = QPoint(int(point.x() * self.zoom_scale), int(point.y() * self.zoom_scale))
            painter.drawEllipse(scaled_point, self.point_radius, self.point_radius)

        pen.setColor(Qt.green)
        pen.setWidth(2)
        painter.setPen(pen)
        for line in self.lines:
            start_point = QPoint(int(line[0].x() * self.zoom_scale), int(line[0].y() * self.zoom_scale))
            end_point = QPoint(int(line[1].x() * self.zoom_scale), int(line[1].y() * self.zoom_scale))
            painter.drawLine(start_point, end_point)

        painter.end()
        self.label.setPixmap(pixmap)

    def mouseMoveEvent(self, event):
        if self.drawing and self.current_image:
            self.temp_point = self.getMousePosition(event)
            if self.temp_point:
                self.update()
        self.temp_point = None  # Reset temp_point to None after drawing a line

    def update(self):
        self.label.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AnnotationTool()
    ex.show()
    sys.exit(app.exec_())
