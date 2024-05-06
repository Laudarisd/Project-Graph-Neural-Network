
import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QFileDialog
from PyQt5.QtGui import QPainter, QPen, QPixmap
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
        self.point_radius = 6  # Making point size bigger for better visibility

    def initUI(self):
        self.setWindowTitle('Pose Annotation Tool')
        self.setGeometry(100, 100, 800, 600)
        self.label = QLabel(self)
        self.label.resize(800, 600)

        loadButton = QPushButton('Load Image', self)
        loadButton.clicked.connect(self.loadImage)

        saveButton = QPushButton('Save Annotations', self)
        saveButton.clicked.connect(self.saveAnnotations)

        layout = QVBoxLayout()
        layout.addWidget(loadButton)
        layout.addWidget(saveButton)
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def loadImage(self):
        imagePath, _ = QFileDialog.getOpenFileName()
        if imagePath:
            self.current_image = QPixmap(imagePath)
            self.current_image_path = imagePath
            self.label.setPixmap(self.current_image)
            self.points.clear()
            self.lines.clear()
            self.update()

    def saveAnnotations(self):
        df = pd.DataFrame(self.lines, columns=['image_name', 'start_coordinates', 'end_coordinates'])
        df.to_csv('annotations.csv', index=False)
        print('Annotations saved.')

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            point = (event.pos().x(), event.pos().y())  # Corrected point acquisition
            overlapping = False
            for existing_point in self.points:
                if (existing_point[0] - self.point_radius <= point[0] <= existing_point[0] + self.point_radius) and \
                   (existing_point[1] - self.point_radius <= point[1] <= existing_point[1] + self.point_radius):
                    overlapping = True
                    point = existing_point  # Snap to existing point if overlapping
                    break
            
            if not self.drawing:
                self.start_point = point
                self.points.append(point)
                self.drawing = True
            else:
                self.points.append(point)
                self.lines.append([self.current_image_path, self.start_point, point])
                self.start_point = None
                self.drawing = False
            self.update()

    def paintEvent(self, event):
        if self.current_image:
            painter = QPainter(self.label.pixmap())
            pen = QPen(Qt.red, 6)  # Increased point size for visibility
            painter.setPen(pen)
            for point in self.points:
                # Check for overlapping points to change color
                if self.points.count(point) > 1:
                    pen.setColor(Qt.blue)  # Different color for overlapping points
                else:
                    pen.setColor(Qt.red)
                painter.setPen(pen)
                painter.drawEllipse(QPoint(*point), self.point_radius, self.point_radius)  # Draw larger circles

            pen.setColor(Qt.green)
            painter.setPen(pen)
            for line in self.lines:
                painter.drawLine(QPoint(*line[1]), QPoint(*line[2]))

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.temp_point = (event.pos().x(), event.pos().y())
            self.update()

    # def mouseReleaseEvent(self, event):
    #     pass

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # When the mouse is released, we check if it was released after dragging
            if self.drawing and self.temp_point:
                # If a temporary point exists (indicating a drag operation was in progress),
                # finalize the line drawing if applicable. However, as per the design,
                # the line is already finalized on the second click, so we might just clean up.
                self.temp_point = None
                self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AnnotationTool()
    ex.show()
    sys.exit(app.exec_())


