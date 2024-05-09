import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QFileDialog, QHBoxLayout, QListWidget, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QPen, QPixmap, QCursor
from PyQt5.QtCore import Qt, QPoint

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
        self.annotations = []
        self.image_list = []

    def initUI(self):
        self.setWindowTitle('Pose Annotation Tool')
        self.setGeometry(100, 100, 1200, 600)

        # Create left panel for image list
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        self.image_list_widget = QListWidget()
        left_layout.addWidget(self.image_list_widget)
        left_panel.setLayout(left_layout)

        # Create middle panel for image display
        middle_panel = QWidget()
        middle_layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setMouseTracking(True)  # Enable mouse tracking
        middle_layout.addWidget(self.label)
        middle_panel.setLayout(middle_layout)

        # Create right panel for annotations
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        self.annotation_table = QTableWidget()
        self.annotation_table.setColumnCount(4)
        self.annotation_table.setHorizontalHeaderLabels(['Image Name', 'idx_from', 'idx_to', 'Start Coordinates', 'End Coordinates'])
        self.save_csv_button = QPushButton('Save CSV')
        self.save_csv_button.clicked.connect(self.saveAnnotations)
        right_layout.addWidget(self.annotation_table)
        right_layout.addWidget(self.save_csv_button)
        right_panel.setLayout(right_layout)

        # Create main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(left_panel)
        main_layout.addWidget(middle_panel)
        main_layout.addWidget(right_panel)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Load Image button
        loadButton = QPushButton('Load Images', self)
        loadButton.clicked.connect(self.loadImages)
        self.statusBar().addPermanentWidget(loadButton)

    def loadImages(self):
        imagePaths, _ = QFileDialog.getOpenFileNames()
        if imagePaths:
            self.image_list.clear()
            self.image_list = sorted(imagePaths)
            self.image_list_widget.addItems(sorted([path.split('/')[-1] for path in self.image_list]))
            self.current_image_path = self.image_list[0]
            self.current_image = QPixmap(self.current_image_path)
            self.label.setPixmap(self.current_image)
            self.points.clear()
            self.lines.clear()
            self.annotations.clear()
            self.annotation_table.setRowCount(0)
            self.update()

    def saveAnnotations(self):
        df = pd.DataFrame(self.annotations, columns=['image_name', 'idx_from', 'idx_to', 'start_coordinates', 'end_coordinates'])
        df.to_csv('annotations.csv', index=False)
        print('Annotations saved.')

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            point = self.label.mapFromParent(event.pos())
            overlapping = False
            for existing_point in self.points:
                if (existing_point[0] - self.point_radius <= point.x() <= existing_point[0] + self.point_radius) and \
                   (existing_point[1] - self.point_radius <= point.y() <= existing_point[1] + self.point_radius):
                    overlapping = True
                    point = QPoint(existing_point[0], existing_point[1])  # Snap to existing point if overlapping
                    break
            
            if not self.drawing:
                self.start_point = point
                self.points.append((point.x(), point.y()))
                self.drawing = True
            else:
                self.points.append((point.x(), point.y()))
                idx_from = self.points.index(self.start_point)
                idx_to = self.points.index((point.x(), point.y()))
                self.lines.append([self.current_image_path, self.start_point, (point.x(), point.y())])
                self.annotations.append([self.current_image_path.split('/')[-1], idx_from, idx_to, self.start_point, (point.x(), point.y())])
                self.updateAnnotationTable()
                self.start_point = None
                self.drawing = False
            self.update()

    def paintEvent(self, event):
        if self.current_image:
            painter = QPainter(self.label.pixmap())
            pen = QPen(Qt.red, 6)
            painter.setPen(pen)
            for point in self.points:
                if self.points.count(point) > 1:
                    pen.setColor(Qt.blue)
                else:
                    pen.setColor(Qt.red)
                painter.setPen(pen)
                painter.drawEllipse(QPoint(*point), self.point_radius, self.point_radius)

            pen.setColor(Qt.green)
            painter.setPen(pen)
            for line in self.lines:
                painter.drawLine(QPoint(*line[1]), QPoint(*line[2]))

            if self.drawing and self.start_point and self.temp_point:
                painter.drawLine(QPoint(*self.start_point), QPoint(*self.temp_point))

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.temp_point = self.label.mapFromParent(event.pos()).toTuple()
            self.update()

        # Update cursor position
        cursor_pos = self.label.mapFromParent(event.pos())
        self.label.setCursor(QCursor(Qt.CrossCursor))  # Set custom cursor shape

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.drawing and self.temp_point:
                self.temp_point = None
                self.update()

    def updateAnnotationTable(self):
        self.annotation_table.setRowCount(len(self.annotations))
        for row, annotation in enumerate(self.annotations):
            self.annotation_table.setItem(row, 0, QTableWidgetItem(annotation[0]))
            self.annotation_table.setItem(row, 1, QTableWidgetItem(str(annotation[1])))
            self.annotation_table.setItem(row, 2, QTableWidgetItem(str(annotation[2])))
            self.annotation_table.setItem(row, 3, QTableWidgetItem(str(annotation[3])))
            self.annotation_table.setItem(row, 4, QTableWidgetItem(str(annotation[4])))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AnnotationTool()
    ex.show()
    sys.exit(app.exec_())