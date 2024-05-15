import sys
import os
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QGraphicsView, QGraphicsScene, QShortcut, QListWidget, QGraphicsPixmapItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPixmap, QPen, QColor, QKeySequence, QCursor, QPainter

class AnnotationTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pose Detection Annotation Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        # Layouts
        self.mainLayout = QHBoxLayout(self.centralWidget)
        self.leftPanel = QVBoxLayout()
        self.midPanel = QVBoxLayout()
        self.rightPanel = QVBoxLayout()
        
        self.mainLayout.addLayout(self.leftPanel, 15)
        self.mainLayout.addLayout(self.midPanel, 70)
        self.mainLayout.addLayout(self.rightPanel, 15)
        
        # Left panel
        self.uploadButton = QPushButton("Upload Folder", self)
        self.uploadButton.clicked.connect(self.upload_folder)
        self.leftPanel.addWidget(self.uploadButton)

        self.fileListWidget = QListWidget(self)
        self.leftPanel.addWidget(self.fileListWidget)

        self.zoomInButton = QPushButton("Zoom In", self)
        self.zoomInButton.clicked.connect(self.zoom_in)
        self.leftPanel.addWidget(self.zoomInButton)
        
        self.zoomOutButton = QPushButton("Zoom Out", self)
        self.zoomOutButton.clicked.connect(self.zoom_out)
        self.leftPanel.addWidget(self.zoomOutButton)

        self.drawLineButton = QPushButton("Draw Line", self)
        self.drawLineButton.clicked.connect(self.enable_drawing)
        self.leftPanel.addWidget(self.drawLineButton)

        self.editButton = QPushButton("Edit", self)
        self.editButton.clicked.connect(self.enable_editing)
        self.leftPanel.addWidget(self.editButton)

        # Mid panel
        self.graphicsView = QGraphicsView(self)
        self.graphicsView.setRenderHint(QPainter.Antialiasing)
        self.graphicsView.setDragMode(QGraphicsView.ScrollHandDrag)
        self.scene = QGraphicsScene(self)
        self.graphicsView.setScene(self.scene)
        self.graphicsView.viewport().installEventFilter(self)
        self.midPanel.addWidget(self.graphicsView)

        # Right panel
        self.dataTable = QTableWidget(self)
        self.dataTable.setColumnCount(3)
        self.dataTable.setHorizontalHeaderLabels(["Index", "Start (x, y)", "End (x, y)"])
        self.rightPanel.addWidget(self.dataTable)
        
        self.saveButton = QPushButton("Save Data", self)
        self.saveButton.clicked.connect(self.save_data)
        self.rightPanel.addWidget(self.saveButton)
        
        # Variables for drawing
        self.drawing = False
        self.editing = False
        self.startPoint = QPointF()
        self.endPoint = QPointF()
        self.currentLine = None
        self.lines = []
        self.pointSize = 6  # Increased size for better visibility
        self.closePointThreshold = 10  # Threshold to consider points as overlapping
        self.selectedItem = None
        
        self.imageFiles = []
        self.currentImageIndex = -1
        self.pixmapItem = None

        # Shortcuts
        self.shortcut_next = QShortcut(QKeySequence("D"), self)
        self.shortcut_next.activated.connect(self.next_image)
        self.shortcut_prev = QShortcut(QKeySequence("A"), self)
        self.shortcut_prev.activated.connect(self.prev_image)
        self.shortcut_escape = QShortcut(QKeySequence("Esc"), self)
        self.shortcut_escape.activated.connect(self.disable_drawing)
        self.shortcut_draw = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_draw.activated.connect(self.fit_to_screen)
        self.shortcut_enable_drawing = QShortcut(QKeySequence("W"), self)
        self.shortcut_enable_drawing.activated.connect(self.enable_drawing)
        self.shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut_undo.activated.connect(self.undo)

    def upload_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.imageFiles = [os.path.join(folder, file) for file in os.listdir(folder) if file.lower().endswith(('png', 'jpg', 'jpeg'))]
            if self.imageFiles:
                self.currentImageIndex = 0
                self.fileListWidget.clear()
                for file in self.imageFiles:
                    self.fileListWidget.addItem(os.path.basename(file))
                self.load_image()
    
    def load_image(self):
        if 0 <= self.currentImageIndex < len(self.imageFiles):
            self.pixmap = QPixmap(self.imageFiles[self.currentImageIndex])
            self.scene.clear()
            self.pixmapItem = QGraphicsPixmapItem(self.pixmap)
            self.scene.addItem(self.pixmapItem)
            self.fit_to_screen()
            self.lines.clear()
            self.update_data_table()

    def zoom_in(self):
        self.graphicsView.scale(1.2, 1.2)

    def zoom_out(self):
        self.graphicsView.scale(0.8, 0.8)

    def enable_drawing(self):
        self.drawing = True
        self.editing = False
        self.setCursor(QCursor(Qt.CrossCursor))
    
    def enable_editing(self):
        self.drawing = False
        self.editing = True
        self.setCursor(QCursor(Qt.OpenHandCursor))
    
    def disable_drawing(self):
        self.drawing = False
        self.editing = False
        self.setCursor(QCursor(Qt.ArrowCursor))
    
    def fit_to_screen(self):
        self.graphicsView.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
    
    def next_image(self):
        if self.currentImageIndex < len(self.imageFiles) - 1:
            self.currentImageIndex += 1
            self.load_image()
            self.fileListWidget.setCurrentRow(self.currentImageIndex)
    
    def prev_image(self):
        if self.currentImageIndex > 0:
            self.currentImageIndex -= 1
            self.load_image()
            self.fileListWidget.setCurrentRow(self.currentImageIndex)
    
    def save_data(self):
        if not self.imageFiles:
            return

        data = []
        for i, (start, end) in enumerate(self.lines):
            data.append([i, f"({start.x()}, {start.y()})", f"({end.x()}, {end.y()})"])
        
        filename = os.path.splitext(self.imageFiles[self.currentImageIndex])[0] + ".csv"
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["Index", "Start (x, y)", "End (x, y)"])
            writer.writerows(data)

    def update_data_table(self):
        self.dataTable.setRowCount(len(self.lines))
        for i, (start, end) in enumerate(self.lines):
            self.dataTable.setItem(i, 0, QTableWidgetItem(str(i)))
            self.dataTable.setItem(i, 1, QTableWidgetItem(f"({start.x()}, {start.y()})"))
            self.dataTable.setItem(i, 2, QTableWidgetItem(f"({end.x()}, {end.y()})"))

    def undo(self):
        if self.lines:
            self.lines.pop()
            self.update_scene()
            self.update_data_table()

    def eventFilter(self, source, event):
        if source == self.graphicsView.viewport():
            if self.drawing:
                if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                    self.handle_mouse_press(event)
                elif event.type() == event.MouseMove and event.buttons() == Qt.LeftButton:
                    self.handle_mouse_move(event)
                elif event.type() == event.MouseButtonDblClick and event.button() == Qt.LeftButton:
                    self.handle_mouse_double_click(event)
            elif self.editing:
                if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                    self.handle_edit_press(event)
                elif event.type() == event.MouseMove and event.buttons() == Qt.LeftButton:
                    self.handle_edit_move(event)
                elif event.type() == event.MouseButtonRelease and event.button() == Qt.LeftButton:
                    self.handle_edit_release(event)
        return super().eventFilter(source, event)

    def handle_mouse_press(self, event):
        scenePos = self.graphicsView.mapToScene(event.pos())
        if not self.currentLine:
            self.startPoint = self.get_nearby_point(scenePos)
            self.currentLine = self.scene.addEllipse(self.startPoint.x() - self.pointSize / 2, self.startPoint.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))
        else:
            self.endPoint = self.get_nearby_point(scenePos)
            color = Qt.blue
            if (self.startPoint - self.endPoint).manhattanLength() < self.closePointThreshold:
                self.endPoint = self.startPoint
                color = Qt.blue
            self.scene.addEllipse(self.endPoint.x() - self.pointSize / 2, self.endPoint.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(color), QColor(color))
            self.lines.append((self.startPoint, self.endPoint))
            self.currentLine = None
            self.update_scene()
            self.update_data_table()

    def handle_mouse_move(self, event):
        if self.currentLine:
            self.endPoint = self.graphicsView.mapToScene(event.pos())
            self.update_scene()

    def handle_mouse_double_click(self, event):
        self.currentLine = None
        self.setCursor(QCursor(Qt.ArrowCursor))

    def handle_edit_press(self, event):
        scenePos = self.graphicsView.mapToScene(event.pos())
        item = self.scene.itemAt(scenePos, self.graphicsView.transform())
        if item and isinstance(item, QGraphicsEllipseItem):
            self.selectedItem = item
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def handle_edit_move(self, event):
        if self.selectedItem:
            scenePos = self.graphicsView.mapToScene(event.pos())
            self.selectedItem.setRect(scenePos.x() - self.pointSize / 2, scenePos.y() - self.pointSize / 2, self.pointSize, self.pointSize)
            self.update_lines_with_moved_point(self.selectedItem, scenePos)

    def handle_edit_release(self, event):
        if self.selectedItem:
            self.setCursor(QCursor(Qt.OpenHandCursor))
            self.selectedItem = None
            self.update_data_table()

    def update_lines_with_moved_point(self, selectedItem, newPos):
        center = selectedItem.rect().center()
        for i, (start, end) in enumerate(self.lines):
            if (center - start).manhattanLength() < self.closePointThreshold:
                self.lines[i] = (newPos, end)
            elif (center - end).manhattanLength() < self.closePointThreshold:
                self.lines[i] = (start, newPos)
        self.update_scene()

    def get_nearby_point(self, point):
        for start, end in self.lines:
            if (point - start).manhattanLength() < self.closePointThreshold:
                return start
            if (point - end).manhattanLength() < self.closePointThreshold:
                return end
        return point

    def update_scene(self):
        # Clear only the lines and circles
        for item in self.scene.items():
            if item != self.pixmapItem:
                self.scene.removeItem(item)
        
        pen = QPen(QColor(0, 255, 0), 2)
        for start, end in self.lines:
            self.scene.addLine(start.x(), start.y(), end.x(), end.y(), pen)
            color = Qt.blue
            if (start - end).manhattanLength() < self.closePointThreshold:
                color = Qt.magenta
            self.scene.addEllipse(start.x() - self.pointSize / 2, start.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(color), QColor(color))
            self.scene.addEllipse(end.x() - self.pointSize / 2, end.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(color), QColor(color))
        if self.currentLine:
            self.scene.addEllipse(self.startPoint.x() - self.pointSize / 2, self.startPoint.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))
            self.scene.addLine(self.startPoint.x(), self.startPoint.y(), self.endPoint.x(), self.endPoint.y(), pen)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnnotationTool()
    window.show()
    sys.exit(app.exec_())
