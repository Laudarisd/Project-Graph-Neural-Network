from PyQt5.QtWidgets import QGraphicsRectItem, QInputDialog
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtWidgets import QTableWidgetItem

class BoundingBoxTool:
    def __init__(self, scene, pointSize, dataTable, classListWidget):
        self.scene = scene
        self.pointSize = pointSize
        self.dataTable = dataTable
        self.classListWidget = classListWidget
        self.boxes = []
        self.drawing = False
        self.startPoint = None
        self.endPoint = None
        self.currentBox = None
        self.boxDrawingMode = False
        self.selectedItem = None

    def set_mode(self, mode):
        self.boxDrawingMode = mode

    def enable_drawing(self):
        self.drawing = True
        self.startPoint = None
        self.endPoint = None

    def handle_mouse_press(self, event):
        if self.boxDrawingMode and self.drawing:
            scenePos = self.scene.views()[0].mapToScene(event.pos())
            self.startPoint = scenePos
            self.currentBox = QGraphicsRectItem(QRectF(self.startPoint, self.startPoint))
            self.currentBox.setPen(QPen(QColor(255, 0, 0), 2))
            self.scene.addItem(self.currentBox)

    def handle_mouse_move(self, event):
        if self.boxDrawingMode and self.drawing and self.startPoint:
            scenePos = self.scene.views()[0].mapToScene(event.pos())
            rect = QRectF(self.startPoint, scenePos).normalized()
            self.currentBox.setRect(rect)

    def handle_mouse_release(self, event):
        if self.boxDrawingMode and self.drawing and self.startPoint:
            self.endPoint = self.scene.views()[0].mapToScene(event.pos())
            rect = QRectF(self.startPoint, self.endPoint).normalized()
            self.currentBox.setRect(rect)
            self.boxes.append(self.currentBox)
            self.drawing = False
            self.startPoint = None
            self.endPoint = None
            self.currentBox = None
            self.show_class_selection_dialog()
            self.update_data_table()

    def update_data_table(self):
        self.dataTable.setRowCount(len(self.boxes))
        for i, box in enumerate(self.boxes):
            rect = box.rect()
            self.dataTable.setItem(i, 0, QTableWidgetItem(str(i)))  # Index
            self.dataTable.setItem(i, 1, QTableWidgetItem("class_name"))  # Change to dynamic class if needed
            self.dataTable.setItem(i, 2, QTableWidgetItem(str(int(rect.left()))))
            self.dataTable.setItem(i, 3, QTableWidgetItem(str(int(rect.top()))))
            self.dataTable.setItem(i, 4, QTableWidgetItem(str(int(rect.right()))))
            self.dataTable.setItem(i, 5, QTableWidgetItem(str(int(rect.bottom()))))

    def highlight_from_table(self, row, column):
        for i, box in enumerate(self.boxes):
            pen = QPen(QColor(255, 0, 0), 2) if i == row else QPen(QColor(0, 0, 0), 2)
            box.setPen(pen)

    def show_class_selection_dialog(self):
        classes = [self.classListWidget.item(i).text() for i in range(self.classListWidget.count())]
        if classes:
            selected_class, ok = QInputDialog.getItem(self.scene.views()[0], "Select Class", "Choose class:", classes, 0, False)
            if ok and selected_class:
                self.update_box_class(selected_class)
        else:
            self.add_class()

    def add_class(self):
        text, ok = QInputDialog.getText(self.scene.views()[0], 'Add Class', 'Enter class name:')
        if ok and text:
            self.classListWidget.addItem(text)
            self.update_box_class(text)

    def update_box_class(self, class_name):
        row = self.dataTable.rowCount() - 1
        self.dataTable.setItem(row, 1, QTableWidgetItem(class_name))  # Update class name in table
