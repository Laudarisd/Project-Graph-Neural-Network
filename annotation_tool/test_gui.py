import sys
import os
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QGraphicsView, QGraphicsScene, QShortcut, QListWidget, QGraphicsPixmapItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPixmap, QPen, QColor, QKeySequence, QCursor, QPainter, QWheelEvent

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

        self.changeColorButton = QPushButton("Change Color", self)
        self.changeColorButton.clicked.connect(self.change_color_mode)
        self.leftPanel.addWidget(self.changeColorButton)

        # Mid panel
        self.graphicsView = QGraphicsView(self)
        self.graphicsView.setRenderHint(QPainter.Antialiasing)
        self.scene = QGraphicsScene(self)
        self.graphicsView.setScene(self.scene)
        self.graphicsView.viewport().installEventFilter(self)
        self.midPanel.addWidget(self.graphicsView)

        # Right panel
        self.dataTable = QTableWidget(self)
        self.dataTable.setColumnCount(5)
        self.dataTable.setHorizontalHeaderLabels(["Index", "Start X", "Start Y", "End X", "End Y"])
        self.rightPanel.addWidget(self.dataTable)
        
        self.saveButton = QPushButton("Save Data", self)
        self.saveButton.clicked.connect(self.save_data)
        self.rightPanel.addWidget(self.saveButton)
        
        # Variables for drawing
        self.drawing = False
        self.editing = False
        self.zooming = False
        self.startPoint = QPointF()
        self.endPoint = QPointF()
        self.currentLine = None
        self.lines = []
        self.actions = []  # To store actions for undo functionality
        self.pointSize = 6  # Increased size for better visibility
        self.closePointThreshold = 10  # Threshold to consider points as overlapping
        self.selectedItem = None
        self.axisLineX = None
        self.axisLineY = None
        self.mask = None
        self.colorToggled = False  # Track the current color state
        
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
        self.shortcut_delete = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_delete.activated.connect(self.delete_selected_item)

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
            self.actions.clear()  # Clear actions when a new image is loaded
            self.update_data_table()

    def add_mask(self):
        if self.pixmapItem:
            rect = self.pixmapItem.boundingRect()
            self.mask = self.scene.addRect(rect, QPen(Qt.NoPen), QColor(0, 0, 0, 100))

    def remove_mask(self):
        if self.mask:
            self.scene.removeItem(self.mask)
            self.mask = None

    def zoom_in(self):
        self.graphicsView.scale(1.2, 1.2)
        self.zooming = True

    def zoom_out(self):
        self.graphicsView.scale(0.8, 0.8)
        self.zooming = True

    def enable_drawing(self):
        self.drawing = True
        self.editing = False
        self.setCursor(QCursor(Qt.CrossCursor))
        self.update_axis_lines()
    
    def enable_editing(self):
        self.drawing = False
        self.editing = True
        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.remove_axis_lines()
    
    def disable_drawing(self):
        self.drawing = False
        self.editing = False
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.remove_axis_lines()
    
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
        img_width = self.pixmap.width()
        img_height = self.pixmap.height()
        for i, (start, end) in enumerate(self.lines):
            data.append([i, start.x(), start.y(), end.x(), end.y(), img_width, img_height])
        
        folder = 'csv_data'
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = os.path.join(folder, os.path.splitext(os.path.basename(self.imageFiles[self.currentImageIndex]))[0] + ".csv")
        
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["Index", "Start X", "Start Y", "End X", "End Y", "Image Width", "Image Height"])
            writer.writerows(data)

    def update_data_table(self):
        self.dataTable.setRowCount(len(self.lines))
        for i, (start, end) in enumerate(self.lines):
            self.dataTable.setItem(i, 0, QTableWidgetItem(str(i)))
            self.dataTable.setItem(i, 1, QTableWidgetItem(f"{start.x()}"))
            self.dataTable.setItem(i, 2, QTableWidgetItem(f"{start.y()}"))
            self.dataTable.setItem(i, 3, QTableWidgetItem(f"{end.x()}"))
            self.dataTable.setItem(i, 4, QTableWidgetItem(f"{end.y()}"))

    def undo(self):
        if self.actions:
            last_action = self.actions.pop()
            if last_action["type"] == "line":
                self.lines.pop()
            elif last_action["type"] == "point":
                self.scene.removeItem(last_action["item"])
            self.update_scene()
            self.update_data_table()

    def delete_selected_item(self):
        if self.selectedItem:
            center = self.selectedItem.rect().center()
            self.lines = [(start, end) for start, end in self.lines if not (self.close_to_point(center, start) or self.close_to_point(center, end))]
            self.scene.removeItem(self.selectedItem)
            self.selectedItem = None
            self.update_scene()
            self.update_data_table()

    def change_color_mode(self):
        if self.colorToggled:
            self.setStyleSheet("")
            self.dataTable.setStyleSheet("")
            self.graphicsView.setStyleSheet("")
            self.remove_mask()
        else:
            self.setStyleSheet("background-color: lightgray; color: black;")
            self.dataTable.setStyleSheet("background-color: lightgray; color: black;")
            self.graphicsView.setStyleSheet("background-color: lightgray; color: black;")
            self.add_mask()
        self.colorToggled = not self.colorToggled

    def eventFilter(self, source, event):
        if source == self.graphicsView.viewport():
            if self.drawing:
                if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                    self.handle_mouse_press(event)
                elif event.type() == event.MouseMove and event.buttons() == Qt.LeftButton:
                    self.handle_mouse_move(event)
                elif event.type() == event.MouseButtonRelease and event.button() == Qt.LeftButton:
                    self.handle_mouse_release(event)
                elif event.type() == event.MouseButtonDblClick and event.button() == Qt.LeftButton:
                    self.handle_mouse_double_click(event)
                elif event.type() == event.MouseMove:
                    self.update_axis_lines(event)
            elif self.editing:
                if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                    self.handle_edit_press(event)
                elif event.type() == event.MouseMove and event.buttons() == Qt.LeftButton:
                    self.handle_edit_move(event)
                elif event.type() == event.MouseButtonRelease and event.button() == Qt.LeftButton:
                    self.handle_edit_release(event)
                elif event.type() == event.MouseMove:
                    self.handle_edit_hover(event)
            elif event.type() == event.MouseButtonDblClick and event.button() == Qt.LeftButton:
                self.zoom_in()
            elif event.type() == event.Wheel:
                self.handle_wheel_event(event)
            elif event.type() == event.MouseMove and event.buttons() == Qt.LeftButton and not self.drawing:
                self.graphicsView.setDragMode(QGraphicsView.ScrollHandDrag)
            elif event.type() == event.MouseButtonRelease:
                self.graphicsView.setDragMode(QGraphicsView.NoDrag)
        return super().eventFilter(source, event)

    def handle_mouse_press(self, event):
        scenePos = self.graphicsView.mapToScene(event.pos())
        if not self.currentLine:
            self.startPoint = self.get_nearby_point(scenePos)
            self.currentLine = self.scene.addEllipse(self.startPoint.x() - self.pointSize / 2, self.startPoint.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))
            self.actions.append({"type": "point", "item": self.currentLine})  # Store the action for undo
        else:
            self.endPoint = self.get_nearby_point(scenePos)
            color = Qt.blue
            if (self.startPoint - self.endPoint).manhattanLength() < self.closePointThreshold:
                self.endPoint = self.startPoint
            else:
                self.break_line_if_needed(self.startPoint, self.endPoint)
            self.scene.addEllipse(self.endPoint.x() - self.pointSize / 2, self.endPoint.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(color), QColor(color))
            self.lines.append((self.startPoint, self.endPoint))
            self.actions.append({"type": "line"})  # Store the action for undo
            self.currentLine = None
            self.update_scene()
            self.update_data_table()

    def handle_mouse_move(self, event):
        if self.currentLine:
            self.endPoint = self.graphicsView.mapToScene(event.pos())
            self.update_scene()

    def handle_mouse_release(self, event):
        if self.currentLine:
            self.endPoint = self.graphicsView.mapToScene(event.pos())
            color = Qt.blue
            if (self.startPoint - self.endPoint).manhattanLength() < self.closePointThreshold:
                self.endPoint = self.startPoint
            else:
                self.break_line_if_needed(self.startPoint, self.endPoint)
            self.scene.addEllipse(self.endPoint.x() - self.pointSize / 2, self.endPoint.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(color), QColor(color))
            self.lines.append((self.startPoint, self.endPoint))
            self.actions.append({"type": "line"})  # Store the action for undo
            self.currentLine = None
            self.update_scene()
            self.update_data_table()
            self.startPoint = self.endPoint  # Set startPoint for the next line

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

    def handle_edit_hover(self, event):
        scenePos = self.graphicsView.mapToScene(event.pos())
        item = self.scene.itemAt(scenePos, self.graphicsView.transform())
        if item and isinstance(item, QGraphicsEllipseItem):
            self.setCursor(QCursor(Qt.SizeAllCursor))
        else:
            self.setCursor(QCursor(Qt.OpenHandCursor))

    def handle_wheel_event(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def update_lines_with_moved_point(self, selectedItem, newPos):
        center = selectedItem.rect().center()
        for i, (start, end) in enumerate(self.lines):
            if (center - start).manhattanLength() < self.closePointThreshold:
                self.lines[i] = (newPos, end)
            elif (center - end).manhattanLength() < self.closePointThreshold:
                self.lines[i] = (start, newPos)
        self.update_scene()
        self.update_data_table()

    def break_line_if_needed(self, start, end):
        for i, (line_start, line_end) in enumerate(self.lines):
            if self.point_on_line(end, line_start, line_end):
                self.lines.pop(i)
                self.lines.append((line_start, end))
                self.lines.append((end, line_end))
                break

    def point_on_line(self, point, line_start, line_end):
        dxc = point.x() - line_start.x()
        dyc = point.y() - line_start.y()
        dxl = line_end.x() - line_start.x()
        dyl = line_end.y() - line_start.y()
        cross = dxc * dyl - dyc * dxl
        if abs(cross) > self.closePointThreshold:
            return False
        if abs(dxl) >= abs(dyl):
            if dxl > 0:
                return line_start.x() <= point.x() <= line_end.x()
            else:
                return line_end.x() <= point.x() <= line_start.x()
        else:
            if dyl > 0:
                return line_start.y() <= point.y() <= line_end.y()
            else:
                return line_end.y() <= point.y() <= line_start.y()

    def get_nearby_point(self, point):
        for start, end in self.lines:
            if (point - start).manhattanLength() < self.closePointThreshold:
                return start
            if (point - end).manhattanLength() < self.closePointThreshold:
                return end
        return point

    def close_to_point(self, p1, p2):
        return (p1 - p2).manhattanLength() < self.closePointThreshold

    def update_scene(self):
        # Clear only the lines and circles
        for item in self.scene.items():
            if item != self.pixmapItem and item != self.mask and not isinstance(item, QGraphicsEllipseItem):
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
        self.update_axis_lines()

    def update_axis_lines(self, event=None):
        if self.axisLineX:
            self.scene.removeItem(self.axisLineX)
        if self.axisLineY:
            self.scene.removeItem(self.axisLineY)
        if event:
            scenePos = self.graphicsView.mapToScene(event.pos())
            self.axisLineX = self.scene.addLine(scenePos.x(), 0, scenePos.x(), self.scene.height(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))
            self.axisLineY = self.scene.addLine(0, scenePos.y(), self.scene.width(), scenePos.y(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))

    def remove_axis_lines(self):
        if self.axisLineX:
            self.scene.removeItem(self.axisLineX)
            self.axisLineX = None
        if self.axisLineY:
            self.scene.removeItem(self.axisLineY)
            self.axisLineY = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnnotationTool()
    window.show()
    sys.exit(app.exec_())
