import sys
import os
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QGraphicsView, QGraphicsScene, QShortcut, QListWidget, QGraphicsPixmapItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPixmap, QPen, QColor, QKeySequence, QCursor, QPainter, QWheelEvent
from utils.gnn_features import GNNFeatures

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

        self.saveDirButton = QPushButton("Select Save Directory", self)
        self.saveDirButton.clicked.connect(self.select_save_directory)
        self.leftPanel.addWidget(self.saveDirButton)

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

        self.coordinatesLabel = QLabel(self)
        self.coordinatesLabel.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.coordinatesLabel.setStyleSheet("background-color: white; padding: 2px;")
        self.coordinatesLabel.setFixedWidth(150)
        self.midPanel.addWidget(self.coordinatesLabel)

        # Right panel
        self.dataTable = QTableWidget(self)
        self.dataTable.setColumnCount(6)
        self.dataTable.setHorizontalHeaderLabels(["Start Index", "Start X", "Start Y", "End Index", "End X", "End Y"])
        self.rightPanel.addWidget(self.dataTable)
        
        self.saveButton = QPushButton("Save Data", self)
        self.saveButton.clicked.connect(self.save_data)
        self.rightPanel.addWidget(self.saveButton)
        
        # Variables for drawing
        self.drawing = False
        self.editing = False
        self.zooming = False
        self.startPoint = None
        self.endPoint = None
        self.currentLine = None
        self.lines = []
        self.points = []  # To store drawn points
        self.actions = []  # To store actions for undo functionality
        self.pointSize = 6  # Increased size for better visibility
        self.closePointThreshold = 10  # Threshold to consider points as overlapping
        self.selectedItem = None
        self.axisLineX = None
        self.axisLineY = None
        self.mask = None
        self.colorToggled = False  # Track the current color state
        self.saveDirectory = ''  # Directory to save the CSV files

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

        self.gnn_features = GNNFeatures(self)

    def select_save_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.saveDirectory = directory

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
            self.points.clear()
            self.actions.clear()  # Clear actions when a new image is loaded
            self.update_data_table()
            self.load_existing_annotations()

    def load_existing_annotations(self):
        csv_file = os.path.join(os.path.dirname(self.imageFiles[self.currentImageIndex]), os.path.splitext(os.path.basename(self.imageFiles[self.currentImageIndex]))[0] + ".csv")
        if os.path.exists(csv_file):
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip the header
                for row in reader:
                    start_index, start_x, start_y, end_index, end_x, end_y, _, _ = row
                    start_point = QPointF(float(start_x), float(start_y))
                    end_point = QPointF(float(end_x), float(end_y))
                    self.lines.append((start_point, end_point))
                    start_item = self.scene.addEllipse(float(start_x) - self.pointSize / 2, float(start_y) - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))
                    end_item = self.scene.addEllipse(float(end_x) - self.pointSize / 2, float(end_y) - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))
                    self.points.append({"index": int(start_index), "point": start_point, "item": start_item})
                    self.points.append({"index": int(end_index), "point": end_point, "item": end_item})
            self.update_scene()
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
            start_index = self.gnn_features.get_point_index(start)
            end_index = self.gnn_features.get_point_index(end)
            data.append([start_index, start.x(), start.y(), end_index, end.x(), end.y(), img_width, img_height])
        
        if not self.saveDirectory:
            folder = 'csv_data'
            if not os.path.exists(folder):
                os.makedirs(folder)
            filename = os.path.join(folder, os.path.splitext(os.path.basename(self.imageFiles[self.currentImageIndex]))[0] + ".csv")
        else:
            filename = os.path.join(self.saveDirectory, os.path.splitext(os.path.basename(self.imageFiles[self.currentImageIndex]))[0] + ".csv")
        
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["Start Index", "Start X", "Start Y", "End Index", "End X", "End Y", "Image Width", "Image Height"])
            writer.writerows(data)

    # def update_data_table(self):
    #     self.dataTable.setRowCount(len(self.lines))
    #     for i, (start, end) in enumerate(self.lines):
    #         start_index = self.gnn_features.get_point_index(start)
    #         end_index = self.gnn_features.get_point_index(end)
    #         self.dataTable.setItem(i, 0, QTableWidgetItem(str(start_index)))
    #         self.dataTable.setItem(i, 1, QTableWidgetItem(f"{start.x()}"))
    #         self.dataTable.setItem(i, 2, QTableWidgetItem(f"{start.y()}"))
    #         self.dataTable.setItem(i, 3, QTableWidgetItem(str(end_index)))
    #         self.dataTable.setItem(i, 4, QTableWidgetItem(f"{end.x()}"))
    #         self.dataTable.setItem(i, 5, QTableWidgetItem(f"{end.y()}"))
    def update_data_table(self):
        self.dataTable.setRowCount(len(self.lines))
        for i, (start, end) in enumerate(self.lines):
            start_index = self.gnn_features.get_point_index(start)
            end_index = self.gnn_features.get_point_index(end)
            self.dataTable.setItem(i, 0, QTableWidgetItem(str(start_index)))
            self.dataTable.setItem(i, 1, QTableWidgetItem(str(end_index)))
            self.dataTable.setItem(i, 2, QTableWidgetItem(f"{start.x()}"))
            self.dataTable.setItem(i, 3, QTableWidgetItem(f"{start.y()}"))
            self.dataTable.setItem(i, 4, QTableWidgetItem(f"{end.x()}"))
            self.dataTable.setItem(i, 5, QTableWidgetItem(f"{end.y()}"))

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
            elif event.type() == event.MouseMove:
                self.update_axis_lines(event)
                self.show_coordinates(event)
            elif event.type() == event.MouseMove and event.buttons() == Qt.LeftButton and not self.drawing:
                self.graphicsView.setDragMode(QGraphicsView.ScrollHandDrag)
            elif event.type() == event.MouseButtonRelease:
                self.graphicsView.setDragMode(QGraphicsView.NoDrag)
        return super().eventFilter(source, event)

    def handle_mouse_press(self, event):
        scenePos = self.graphicsView.mapToScene(event.pos())
        nearby_point = self.gnn_features.get_nearby_point(scenePos)
        if isinstance(nearby_point, QPointF):
            point_index = self.gnn_features.get_point_index(nearby_point)
            self.startPoint = {"point": nearby_point, "item": self.scene.addEllipse(nearby_point.x() - self.pointSize / 2, nearby_point.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))}
            point_info = {"index": point_index, "point": self.startPoint["point"], "item": self.startPoint["item"]}
            if point_info not in self.points:
                self.points.append(point_info)
            self.actions.append({"type": "point", "point": point_info})  # Store the action for undo
        else:
            self.startPoint = nearby_point

    def handle_mouse_move(self, event):
        if self.startPoint:
            self.endPoint = {"point": self.graphicsView.mapToScene(event.pos()), "item": None}
            self.update_scene()
        self.show_coordinates(event)

    def handle_mouse_release(self, event):
        if self.startPoint:
            scenePos = self.graphicsView.mapToScene(event.pos())
            nearby_point = self.gnn_features.get_nearby_point(scenePos)
            if isinstance(nearby_point, QPointF):
                self.endPoint = {"point": nearby_point, "item": None}
            else:
                self.endPoint = nearby_point
            color = Qt.blue
            if (self.startPoint["point"] - self.endPoint["point"]).manhattanLength() < self.closePointThreshold:
                self.endPoint = self.startPoint
            else:
                self.gnn_features.break_line_if_needed(self.startPoint["point"], self.endPoint["point"])
            if not self.endPoint["item"]:
                point_index = self.gnn_features.get_point_index(self.endPoint["point"])
                endPointItem = self.scene.addEllipse(self.endPoint["point"].x() - self.pointSize / 2, self.endPoint["point"].y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(color), QColor(color))
                point_info = {"index": point_index, "point": self.endPoint["point"], "item": endPointItem}
                if point_info not in self.points:
                    self.points.append(point_info)
                self.actions.append({"type": "point", "point": point_info})  # Store the action for undo
                self.endPoint["item"] = endPointItem
            self.lines.append((self.startPoint["point"], self.endPoint["point"]))
            self.actions.append({"type": "line"})  # Store the action for undo
            self.update_scene()
            self.update_data_table()
            self.startPoint = self.endPoint  # Set startPoint for the next line

    def handle_mouse_double_click(self, event):
        self.currentLine = None
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.startPoint = None  # End the drawing session

    def handle_edit_press(self, event):
        scenePos = self.graphicsView.mapToScene(event.pos())
        item = self.scene.itemAt(scenePos, self.graphicsView.transform())
        if item and isinstance(item, QGraphicsEllipseItem):
            self.selectedItem = item
            self.selectedItem.setPen(QPen(Qt.red))  # Highlight the selected item in red
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def handle_edit_move(self, event):
        if self.selectedItem:
            scenePos = self.graphicsView.mapToScene(event.pos())
            self.selectedItem.setRect(scenePos.x() - self.pointSize / 2, scenePos.y() - self.pointSize / 2, self.pointSize, self.pointSize)
            self.gnn_features.update_lines_with_moved_point(self.selectedItem, scenePos)

    def handle_edit_release(self, event):
        if self.selectedItem:
            self.setCursor(QCursor(Qt.OpenHandCursor))
            self.selectedItem.setPen(QPen(Qt.blue))  # Reset the pen color to blue
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

    def undo(self):
        self.gnn_features.undo()

    def delete_selected_item(self):
        self.gnn_features.delete_selected_item()

    def update_scene(self):
        self.gnn_features.update_scene()

    def update_axis_lines(self, event=None):
        self.gnn_features.update_axis_lines(event)

    def show_coordinates(self, event):
        self.gnn_features.show_coordinates(event)

    def remove_axis_lines(self):
        self.gnn_features.remove_axis_lines()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnnotationTool()
    window.show()
    sys.exit(app.exec_())
