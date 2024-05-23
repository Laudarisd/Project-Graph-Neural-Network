import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton,
                             QTableWidget, QGraphicsView, QGraphicsScene, QListWidget, QGraphicsPixmapItem, QHeaderView,
                             QSplitter, QShortcut, QTableWidgetItem, QMenu, QFileDialog, QGraphicsLineItem, QGraphicsEllipseItem, QInputDialog, QLineEdit, QMessageBox, QListWidgetItem)
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPixmap, QCursor, QPainter, QKeySequence, QPen, QColor, QWheelEvent

from utils.drawing_operations import upload_folder, save_data_as, save_pascal_voc, load_boxes, load_lines, save_lines
from utils.bounding_box_operations import BoundingBoxTool

class AnnotationTool(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Initializing AnnotationTool...")
        self.setWindowTitle("Pose Detection Annotation Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        # Layouts
        self.mainLayout = QHBoxLayout(self.centralWidget)
        
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        self.leftWidget = QWidget()
        self.leftPanel = QVBoxLayout(self.leftWidget)
        
        self.midWidget = QWidget()
        self.midPanel = QVBoxLayout(self.midWidget)
        
        self.rightWidget = QWidget()
        self.rightPanel = QVBoxLayout(self.rightWidget)
        
        self.splitter.addWidget(self.leftWidget)
        self.splitter.addWidget(self.midWidget)
        self.splitter.addWidget(self.rightWidget)
        
        self.splitter.setSizes([180, 840, 180])  # Set initial sizes to maintain original proportions
        
        self.mainLayout.addWidget(self.splitter)
        
        # Left panel
        self.uploadButton = QPushButton("Upload Folder", self)
        self.uploadButton.clicked.connect(self.upload_folder)
        self.leftPanel.addWidget(self.uploadButton)

        self.fileListWidget = QListWidget(self)
        self.fileListWidget.itemSelectionChanged.connect(self.load_image)
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

        self.drawBoxButton = QPushButton("Draw Box", self)
        self.drawBoxButton.clicked.connect(self.enable_box_drawing)
        self.leftPanel.addWidget(self.drawBoxButton)

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
        self.dataTable.setColumnCount(6)
        self.dataTable.setHorizontalHeaderLabels(["Index", "Class", "xmin", "ymin", "xmax", "ymax"])
        self.rightPanel.addWidget(self.dataTable)
        
        self.dataTable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # Allow resizing columns
        self.dataTable.cellClicked.connect(self.highlight_from_table)  # Connect cell click to highlight function
        self.dataTable.setContextMenuPolicy(Qt.CustomContextMenu)  # Enable custom context menu
        self.dataTable.customContextMenuRequested.connect(self.show_context_menu)  # Connect context menu request to handler

        self.saveAsButton = QPushButton("Choose Save Folder", self)
        self.saveAsButton.clicked.connect(self.save_data_as)
        self.rightPanel.addWidget(self.saveAsButton)
        
        self.saveButton = QPushButton("Save Data", self)
        self.saveButton.clicked.connect(self.save_data)
        self.rightPanel.addWidget(self.saveButton)

        # Class List for Bounding Box
        self.classListWidget = QListWidget(self)
        self.classListWidget.itemClicked.connect(self.select_class)
        self.rightPanel.addWidget(self.classListWidget)
        self.classListWidget.hide()  # Hide by default, show when drawing boxes

        self.addClassButton = QPushButton("Add Class", self)
        self.addClassButton.clicked.connect(self.add_class)
        self.rightPanel.addWidget(self.addClassButton)
        self.addClassButton.hide()

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
        self.edited = False  # Track if the file has been edited
        
        self.imageFiles = []
        self.currentImageIndex = -1
        self.pixmapItem = None
        self.saveFolder = 'annotation_data'  # Default save folder

        self.boundingBoxTool = BoundingBoxTool(self.scene, self.pointSize, self.dataTable, self.classListWidget)

        # Shortcuts
        self.shortcut_next = QShortcut(QKeySequence("D"), self)
        self.shortcut_next.activated.connect(self.next_image)
        self.shortcut_prev = QShortcut(QKeySequence("A"), self)
        self.shortcut_prev.activated.connect(self.prev_image)
        self.shortcut_escape = QShortcut(QKeySequence("Esc"), self)
        self.shortcut_escape.activated.connect(self.disable_drawing)
        self.shortcut_draw = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_draw.activated.connect(self.fit_to_screen)
        self.shortcut_enable_drawing = QShortcut(QKeySequence("Ctrl+W"), self)  # Change this shortcut
        self.shortcut_enable_drawing.activated.connect(self.enable_drawing)
        self.shortcut_enable_box_drawing = QShortcut(QKeySequence("W"), self)  # Change this shortcut
        self.shortcut_enable_box_drawing.activated.connect(self.enable_box_drawing)
        self.shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut_undo.activated.connect(self.undo)
        self.shortcut_delete = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_delete.activated.connect(self.delete_selected_item)
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_data)
        self.shortcut_zoom_in = QShortcut(QKeySequence("Ctrl++"), self)
        self.shortcut_zoom_in.activated.connect(self.zoom_in)
        self.shortcut_zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcut_zoom_out.activated.connect(self.zoom_out)

    def change_color_mode(self):
        if self.colorToggled:
            self.setStyleSheet("")
            self.dataTable.setStyleSheet("")
            self.graphicsView.setStyleSheet("")
        else:
            self.setStyleSheet("background-color: lightgray; color: black;")
            self.dataTable.setStyleSheet("background-color: lightgray; color: black;")
            self.graphicsView.setStyleSheet("background-color: lightgray; color: black;")
        self.colorToggled = not self.colorToggled

    def upload_folder(self):
        print("Uploading folder...")
        self.imageFiles = upload_folder(self.fileListWidget)
        if self.imageFiles:
            self.currentImageIndex = 0
            self.load_image()

    def load_image(self):
        print("Loading image...")
        self.currentImageIndex = self.fileListWidget.currentRow()
        if 0 <= self.currentImageIndex < len(self.imageFiles):
            self.pixmap = QPixmap(self.imageFiles[self.currentImageIndex])
            self.clear_scene()
            self.clear_data()
            self.pixmapItem = QGraphicsPixmapItem(self.pixmap)
            self.scene.addItem(self.pixmapItem)
            self.fit_to_screen()
            # Load existing annotations
            self.load_existing_annotations()
            self.update_data_table()
            self.boundingBoxTool.update_data_table()
            self.update_scene()
            self.edited = False  # Reset edited flag when loading a new image

    def clear_scene(self):
        """Clear the scene while preserving the current pixmapItem."""
        items = self.scene.items()
        for item in items:
            if item != self.pixmapItem:
                self.scene.removeItem(item)

    def clear_data(self):
        """Clear all drawing data."""
        self.lines.clear()
        self.points.clear()
        self.actions.clear()
        self.boundingBoxTool.boxes.clear()
        self.dataTable.clearContents()
        self.dataTable.setRowCount(0)

    def zoom_in(self):
        self.graphicsView.scale(1.2, 1.2)
        self.zooming = True

    def zoom_out(self):
        self.graphicsView.scale(0.8, 0.8)
        self.zooming = True

    def enable_drawing(self):
        self.drawing = True
        self.editing = False
        self.boundingBoxTool.set_mode(False)
        self.setCursor(QCursor(Qt.CrossCursor))
        self.classListWidget.hide()
        self.addClassButton.hide()
        self.dataTable.show()

    def enable_editing(self):
        self.drawing = False
        self.editing = True
        self.boundingBoxTool.set_mode(False)
        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.classListWidget.hide()
        self.addClassButton.hide()
        self.dataTable.show()

    def disable_drawing(self):
        self.drawing = False
        self.editing = False
        self.boundingBoxTool.set_mode(False)
        self.setCursor(QCursor(Qt.ArrowCursor))

    def enable_box_drawing(self):
        self.drawing = True
        self.editing = False
        self.boundingBoxTool.set_mode(True)
        self.setCursor(QCursor(Qt.CrossCursor))
        self.classListWidget.show()
        self.addClassButton.show()
        self.dataTable.show()
        self.boundingBoxTool.enable_drawing()

    def save_data(self):
        if self.boundingBoxTool.boxDrawingMode:
            save_pascal_voc(self.imageFiles[self.currentImageIndex], self.boundingBoxTool.boxes, (self.pixmap.width(), self.pixmap.height()), self.saveFolder)
        else:
            save_lines(self.imageFiles[self.currentImageIndex], self.lines, self.saveFolder)
        self.edited = False

    def save_data_as(self):
        self.saveFolder = save_data_as(self.saveFolder)
        self.save_data()

    def highlight_from_table(self, row, column):
        self.clear_highlight()
        if self.boundingBoxTool.boxDrawingMode:
            self.boundingBoxTool.highlight_from_table(row, column)
        else:
            if row < len(self.lines):
                start_point = self.points[row * 2]["point"]
                end_point = self.points[row * 2 + 1]["point"]
                for item in self.scene.items():
                    if isinstance(item, QGraphicsLineItem):
                        data = item.data(0)
                        if data and ((data["start"] == start_point and data["end"] == end_point) or (data["start"] == end_point and data["end"] == start_point)):
                            item.setPen(QPen(QColor(255, 0, 0), 2))  # Highlight
                        else:
                            item.setPen(QPen(QColor(0, 255, 0), 2))  # Reset color
                    elif isinstance(item, QGraphicsEllipseItem):
                        if item.rect().center() == start_point or item.rect().center() == end_point:
                            item.setBrush(QColor(255, 0, 0, 100))  # Highlight
                        else:
                            item.setBrush(QColor(Qt.blue))

    def show_context_menu(self, pos):
        contextMenu = QMenu(self)
        deleteAction = contextMenu.addAction("Delete")
        action = contextMenu.exec_(self.dataTable.mapToGlobal(pos))
        if action == deleteAction:
            self.delete_selected_item()

    def next_image(self):
        if self.edited:
            reply = QMessageBox.question(self, 'Message', 'You have unsaved changes. Do you want to save them?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.save_data()
                self.currentImageIndex += 1
                self.fileListWidget.setCurrentRow(self.currentImageIndex)
                self.load_image()
        elif self.currentImageIndex < len(self.imageFiles) - 1:
            self.currentImageIndex += 1
            self.fileListWidget.setCurrentRow(self.currentImageIndex)
            self.load_image()
    
    def prev_image(self):
        if self.edited:
            reply = QMessageBox.question(self, 'Message', 'You have unsaved changes. Do you want to save them?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.save_data()
                self.currentImageIndex -= 1
                self.fileListWidget.setCurrentRow(self.currentImageIndex)
                self.load_image()
        elif self.currentImageIndex > 0:
            self.currentImageIndex -= 1
            self.fileListWidget.setCurrentRow(self.currentImageIndex)
            self.load_image()

    def fit_to_screen(self):
        self.graphicsView.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def undo(self):
        if self.actions:
            last_action = self.actions.pop()
            if last_action["type"] == "line":
                line = self.lines.pop()
                self.remove_point(line[0])
                self.remove_point(line[1])  # Remove end point of the line
                self.startPoint = None  # Reset startPoint after undo
            elif last_action["type"] == "point":
                point_to_remove = last_action["point"]
                self.remove_point(point_to_remove["point"])
            self.update_scene()
            self.update_data_table()
            self.edited = True

    def delete_selected_item(self):
        current_row = self.dataTable.currentRow()
        if current_row >= 0:
            self.delete_row(current_row)

    def delete_row(self, row):
        if row < 0 or row >= self.dataTable.rowCount():
            return
        if self.boundingBoxTool.boxDrawingMode:
            if row < len(self.boundingBoxTool.boxes):
                self.boundingBoxTool.boxes.pop(row)
        else:
            try:
                self.lines.pop(row)
                self.remove_point(self.points[row * 2]["point"])
                self.remove_point(self.points[row * 2 + 1]["point"])
                self.points.pop(row * 2)
                self.points.pop(row * 2)
            except IndexError:
                print(f"Error: Index {row} out of range for points array.")
        self.update_data_table()
        self.update_scene()
        self.edited = True

    def eventFilter(self, source, event):
        if source == self.graphicsView.viewport():
            if self.boundingBoxTool.boxDrawingMode:
                if self.drawing:
                    if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                        self.boundingBoxTool.handle_mouse_press(event)
                    elif event.type() == event.MouseMove:
                        self.boundingBoxTool.handle_mouse_move(event)
                    elif event.type() == event.MouseButtonRelease and event.button() == Qt.LeftButton:
                        self.boundingBoxTool.handle_mouse_release(event)
            else:
                if self.drawing:
                    if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                        self.handle_mouse_press(event)
                    elif event.type() == event.MouseMove:
                        self.handle_mouse_move(event)
                    elif event.type() == event.MouseButtonDblClick and event.button() == Qt.LeftButton:
                        self.zoom_in()  # Enable double-click zoom in drawing mode
                elif self.editing:
                    if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                        item = self.scene.itemAt(self.graphicsView.mapToScene(event.pos()), self.graphicsView.transform())
                        if isinstance(item, QGraphicsEllipseItem) or isinstance(item, QGraphicsLineItem):
                            self.selectedItem = item
                            self.setCursor(QCursor(Qt.ClosedHandCursor))
                        elif isinstance(item, QGraphicsRectItem):
                            self.boundingBoxTool.selectedItem = item
                            self.setCursor(QCursor(Qt.ClosedHandCursor))
                    elif event.type() == event.MouseMove and self.selectedItem:
                        self.handle_edit_move(event)
                    elif event.type() == event.MouseButtonRelease and event.button() == Qt.LeftButton:
                        self.selectedItem = None
                        self.setCursor(QCursor(Qt.OpenHandCursor))
                elif event.type() == event.MouseButtonDblClick and event.button() == Qt.LeftButton:
                    self.zoom_in()
                elif event.type() == event.Wheel:
                    self.handle_wheel_event(event)
                elif event.type() == event.MouseMove:
                    self.handle_mouse_move(event)
        return super().eventFilter(source, event)

    def handle_edit_move(self, event):
        if self.boundingBoxTool.boxDrawingMode and isinstance(self.selectedItem, QGraphicsRectItem):
            # Handle moving and resizing boxes
            scenePos = self.graphicsView.mapToScene(event.pos())
            if self.selectedItem:
                rect = self.selectedItem.rect()
                newRect = QRectF(rect.topLeft(), scenePos).normalized()
                self.selectedItem.setRect(newRect)
                self.boundingBoxTool.update_data_table()
        elif isinstance(self.selectedItem, QGraphicsEllipseItem):
            # Handle moving points
            scenePos = self.graphicsView.mapToScene(event.pos())
            self.selectedItem.setRect(scenePos.x() - self.pointSize / 2, scenePos.y() - self.pointSize / 2, self.pointSize, self.pointSize)
            self.update_lines_from_points()
            self.update_data_table()

    def update_lines_from_points(self):
        for i in range(0, len(self.points), 2):
            self.lines[i // 2] = (self.points[i]["point"], self.points[i + 1]["point"])
        self.update_scene()

    def handle_wheel_event(self, event: QWheelEvent):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()

    def load_existing_annotations(self):
        if self.boundingBoxTool.boxDrawingMode:
            self.boundingBoxTool.boxes = load_boxes(self.imageFiles[self.currentImageIndex])
        else:
            self.lines = load_lines(self.imageFiles[self.currentImageIndex])
            for start, end in self.lines:
                start_point = {"point": start, "item": self.scene.addEllipse(start.x() - self.pointSize / 2, start.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))}
                end_point = {"point": end, "item": self.scene.addEllipse(end.x() - self.pointSize / 2, end.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))}
                self.points.append(start_point)
                self.points.append(end_point)

    def update_scene(self):
        self.clear_scene()
        if self.pixmapItem is not None:
            self.scene.addItem(self.pixmapItem)
            pen = QPen(QColor(0, 255, 0), 2)
            for start, end in self.lines:
                line_item = self.scene.addLine(start.x(), start.y(), end.x(), end.y(), pen)
                line_item.setData(0, {"start": start, "end": end})
                color = Qt.blue
                if (start - end).manhattanLength() < self.closePointThreshold:
                    color = Qt.magenta
                self.scene.addEllipse(start.x() - self.pointSize / 2, start.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(color), QColor(color))
                self.scene.addEllipse(end.x() - self.pointSize / 2, end.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(color), QColor(color))
            for box in self.boundingBoxTool.boxes:
                self.scene.addItem(box)

    def get_nearby_point(self, point):
        for pt in self.points:
            if (point - pt["point"]).manhattanLength() < self.closePointThreshold:
                return pt["point"]
        return point

    def handle_mouse_press(self, event):
        scenePos = self.graphicsView.mapToScene(event.pos())
        item = self.scene.itemAt(scenePos, self.graphicsView.transform())
        if self.drawing and not self.boundingBoxTool.boxDrawingMode:
            nearby_point = self.get_nearby_point(scenePos)
            if not self.startPoint:
                self.startPoint = {"point": nearby_point, "item": self.scene.addEllipse(nearby_point.x() - self.pointSize / 2, nearby_point.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))}
                point_info = {"point": self.startPoint["point"], "item": self.startPoint["item"]}
                self.points.append(point_info)
                self.actions.append({"type": "point", "point": point_info})  # Store the action for undo
            else:
                self.endPoint = {"point": nearby_point, "item": self.scene.addEllipse(nearby_point.x() - self.pointSize / 2, nearby_point.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))}
                point_info = {"point": self.endPoint["point"], "item": self.endPoint["item"]}
                self.points.append(point_info)
                self.actions.append({"type": "point", "point": point_info})  # Store the action for undo
                self.lines.append((self.startPoint["point"], self.endPoint["point"]))
                self.actions.append({"type": "line"})  # Store the action for undo
                self.update_scene()
                self.update_data_table()
                self.startPoint = None  # Finish the line after connecting start and end points
                self.edited = True
        elif self.editing and isinstance(item, QGraphicsEllipseItem):
            self.selectedItem = item
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            item.setBrush(QColor(255, 0, 0, 100))  # Highlight selected item
        elif self.editing and isinstance(item, QGraphicsLineItem):
            line = item.line()
            new_point = QPointF((line.p1().x() + line.p2().x()) / 2, (line.p1().y() + line.p2().y()) / 2)
            new_item = self.scene.addEllipse(new_point.x() - self.pointSize / 2, new_point.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))
            point_info = {"point": new_point, "item": new_item}
            self.points.append(point_info)
            self.actions.append({"type": "point", "point": point_info})  # Store the action for undo
            self.update_scene()
            self.update_data_table()
            self.edited = True

    def handle_mouse_move(self, event):
        scenePos = self.graphicsView.mapToScene(event.pos())
        nearby_point = self.get_nearby_point(scenePos)
        if isinstance(nearby_point, QPointF):
            self.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.CrossCursor))
        if self.drawing and not self.boundingBoxTool.boxDrawingMode:
            self.update_axis_lines(event)

    def update_axis_lines(self, event=None):
        if self.axisLineX:
            self.scene.removeItem(self.axisLineX)
        if self.axisLineY:
            self.scene.removeItem(self.axisLineY)
        if event:
            scenePos = self.graphicsView.mapToScene(event.pos())
            self.axisLineX = self.scene.addLine(scenePos.x(), 0, scenePos.x(), self.scene.height(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))
            self.axisLineY = self.scene.addLine(0, scenePos.y(), self.scene.width(), scenePos.y(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))
        elif self.drawing or self.editing:
            cursor_pos = self.graphicsView.mapFromGlobal(QCursor.pos())
            scene_pos = self.graphicsView.mapToScene(cursor_pos)
            self.axisLineX = self.scene.addLine(scene_pos.x(), 0, scene_pos.x(), self.scene.height(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))
            self.axisLineY = self.scene.addLine(0, scene_pos.y(), self.scene.width(), scene_pos.y(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))

    def remove_point(self, point):
        for p in self.points:
            if p["point"] == point:
                self.scene.removeItem(p["item"])
                self.points.remove(p)
                break

    def update_data_table(self):
        if self.boundingBoxTool.boxDrawingMode:
            self.boundingBoxTool.update_data_table()
        else:
            self.dataTable.setRowCount(len(self.lines))
            for i, (start, end) in enumerate(self.lines):
                self.dataTable.setItem(i, 0, QTableWidgetItem(str(i)))  # Index
                self.dataTable.setItem(i, 1, QTableWidgetItem(""))  # Empty class for lines
                self.dataTable.setItem(i, 2, QTableWidgetItem(f"{int(start.x())}"))
                self.dataTable.setItem(i, 3, QTableWidgetItem(f"{int(start.y())}"))
                self.dataTable.setItem(i, 4, QTableWidgetItem(f"{int(end.x())}"))
                self.dataTable.setItem(i, 5, QTableWidgetItem(f"{int(end.y())}"))

    def add_class(self):
        text, ok = QInputDialog.getText(self, 'Add Class', 'Enter class name:')
        if ok and text:
            self.classListWidget.addItem(text)

    def select_class(self, item):
        class_name = item.text()
        self.boundingBoxTool.update_box_class(class_name)

    def clear_highlight(self):
        for item in self.scene.items():
            if isinstance(item, QGraphicsLineItem):
                item.setPen(QPen(QColor(0, 255, 0), 2))  # Reset color
            elif isinstance(item, QGraphicsEllipseItem):
                item.setBrush(QColor(Qt.blue))

    def load_existing_annotations(self):
        if self.boundingBoxTool.boxDrawingMode:
            self.boundingBoxTool.boxes = load_boxes(self.imageFiles[self.currentImageIndex])
        else:
            self.lines = load_lines(self.imageFiles[self.currentImageIndex])
            self.points = [{"point": line[0], "item": None} for line in self.lines] + [{"point": line[1], "item": None} for line in self.lines]

    def handle_wheel_event(self, event: QWheelEvent):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def handle_mouse_press(self, event):
        scenePos = self.graphicsView.mapToScene(event.pos())
        item = self.scene.itemAt(scenePos, self.graphicsView.transform())
        if self.drawing:
            nearby_point = self.get_nearby_point(scenePos)
            if not self.startPoint:
                self.startPoint = {"point": nearby_point, "item": self.scene.addEllipse(nearby_point.x() - self.pointSize / 2, nearby_point.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))}
                point_info = {"point": self.startPoint["point"], "item": self.startPoint["item"]}
                self.points.append(point_info)
                self.actions.append({"type": "point", "point": point_info})  # Store the action for undo
            else:
                self.endPoint = {"point": nearby_point, "item": self.scene.addEllipse(nearby_point.x() - self.pointSize / 2, nearby_point.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))}
                point_info = {"point": self.endPoint["point"], "item": self.endPoint["item"]}
                self.points.append(point_info)
                self.actions.append({"type": "point", "point": point_info})  # Store the action for undo
                self.lines.append((self.startPoint["point"], self.endPoint["point"]))
                self.actions.append({"type": "line"})  # Store the action for undo
                self.update_scene()
                self.update_data_table()
                self.startPoint = None  # Finish the line after connecting start and end points
                self.edited = True
        elif self.editing and isinstance(item, QGraphicsEllipseItem):
            self.selectedItem = item
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            item.setBrush(QColor(255, 0, 0, 100))  # Highlight selected item
        elif self.editing and isinstance(item, QGraphicsLineItem):
            line = item.line()
            new_point = QPointF((line.p1().x() + line.p2().x()) / 2, (line.p1().y() + line.p2().y()) / 2)
            new_item = self.scene.addEllipse(new_point.x() - self.pointSize / 2, new_point.y() - self.pointSize / 2, self.pointSize, self.pointSize, QPen(Qt.blue), QColor(Qt.blue))
            point_info = {"point": new_point, "item": new_item}
            self.points.append(point_info)
            self.actions.append({"type": "point", "point": point_info})  # Store the action for undo
            self.update_scene()
            self.update_data_table()
            self.edited = True

    def handle_mouse_move(self, event):
        scenePos = self.graphicsView.mapToScene(event.pos())
        nearby_point = self.get_nearby_point(scenePos)
        if isinstance(nearby_point, QPointF):
            self.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.CrossCursor))
        if self.drawing:
            self.update_axis_lines(event)

    def update_axis_lines(self, event=None):
        if self.axisLineX:
            self.scene.removeItem(self.axisLineX)
        if self.axisLineY:
            self.scene.removeItem(self.axisLineY)
        if event:
            scenePos = self.graphicsView.mapToScene(event.pos())
            self.axisLineX = self.scene.addLine(scenePos.x(), 0, scenePos.x(), self.scene.height(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))
            self.axisLineY = self.scene.addLine(0, scenePos.y(), self.scene.width(), scenePos.y(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))
        elif self.drawing or self.editing:
            cursor_pos = self.graphicsView.mapFromGlobal(QCursor.pos())
            scene_pos = self.graphicsView.mapToScene(cursor_pos)
            self.axisLineX = self.scene.addLine(scene_pos.x(), 0, scene_pos.x(), self.scene.height(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))
            self.axisLineY = self.scene.addLine(0, scene_pos.y(), self.scene.width(), scene_pos.y(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))

    def remove_point(self, point):
        for p in self.points:
            if p["point"] == point:
                self.scene.removeItem(p["item"])
                self.points.remove(p)
                break

    def update_data_table(self):
        if self.boundingBoxTool.boxDrawingMode:
            self.boundingBoxTool.update_data_table()
        else:
            self.dataTable.setRowCount(len(self.lines))
            for i, (start, end) in enumerate(self.lines):
                self.dataTable.setItem(i, 0, QTableWidgetItem(str(i)))  # Index
                self.dataTable.setItem(i, 1, QTableWidgetItem(""))  # Empty class for lines
                self.dataTable.setItem(i, 2, QTableWidgetItem(f"{int(start.x())}"))
                self.dataTable.setItem(i, 3, QTableWidgetItem(f"{int(start.y())}"))
                self.dataTable.setItem(i, 4, QTableWidgetItem(f"{int(end.x())}"))
                self.dataTable.setItem(i, 5, QTableWidgetItem(f"{int(end.y())}"))

    def add_class(self):
        text, ok = QInputDialog.getText(self, 'Add Class', 'Enter class name:')
        if ok and text:
            self.classListWidget.addItem(text)

    def select_class(self, item):
        class_name = item.text()
        self.boundingBoxTool.update_box_class(class_name)

    def clear_highlight(self):
        for item in self.scene.items():
            if isinstance(item, QGraphicsLineItem):
                item.setPen(QPen(QColor(0, 255, 0), 2))  # Reset color
            elif isinstance(item, QGraphicsEllipseItem):
                item.setBrush(QColor(Qt.blue))

    def load_existing_annotations(self):
        if self.boundingBoxTool.boxDrawingMode:
            self.boundingBoxTool.boxes = load_boxes(self.imageFiles[self.currentImageIndex])
        else:
            self.lines = load_lines(self.imageFiles[self.currentImageIndex])
            self.points = [{"point": line[0], "item": None} for line in self.lines] + [{"point": line[1], "item": None} for line in self.lines]

    def handle_wheel_event(self, event: QWheelEvent):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

if __name__ == "__main__":
    print("Starting application...")
    app = QApplication(sys.argv)
    window = AnnotationTool()
    window.show()
    sys.exit(app.exec_())


