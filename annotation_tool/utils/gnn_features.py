import csv
import os
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QGraphicsEllipseItem

class GNNFeatures:
    def __init__(self, gui):
        self.gui = gui

    def undo(self):
        if self.gui.actions:
            last_action = self.gui.actions.pop()
            if last_action["type"] == "line":
                self.gui.lines.pop()
            elif last_action["type"] == "point":
                point_to_remove = last_action["point"]
                self.gui.points.remove(point_to_remove)
                self.gui.scene.removeItem(point_to_remove["item"])
                self.gui.lines = [(start, end) for start, end in self.gui.lines if not (self.close_to_point(point_to_remove["point"], start) or self.close_to_point(point_to_remove["point"], end))]
            self.gui.update_scene()
            self.gui.update_data_table()

    def delete_selected_item(self):
        if self.gui.selectedItem:
            center = self.gui.selectedItem.rect().center()
            self.gui.lines = [(start, end) for start, end in self.gui.lines if not (self.close_to_point(center, start) or self.close_to_point(center, end))]
            self.gui.points = [pt for pt in self.gui.points if not self.close_to_point(center, pt["point"])]
            self.gui.scene.removeItem(self.gui.selectedItem)
            self.gui.selectedItem = None
            self.gui.update_scene()
            self.gui.update_data_table()

    def update_lines_with_moved_point(self, selectedItem, newPos):
        center = selectedItem.rect().center()
        for i, (start, end) in enumerate(self.gui.lines):
            if (center - start).manhattanLength() < self.gui.closePointThreshold:
                self.gui.lines[i] = (newPos, end)
            elif (center - end).manhattanLength() < self.gui.closePointThreshold:
                self.gui.lines[i] = (start, newPos)
        self.gui.update_scene()
        self.gui.update_data_table()

    def break_line_if_needed(self, start, end):
        for i, (line_start, line_end) in enumerate(self.gui.lines):
            if self.point_on_line(end, line_start, line_end):
                self.gui.lines.pop(i)
                self.gui.lines.append((line_start, end))
                self.gui.lines.append((end, line_end))
                break

    def point_on_line(self, point, line_start, line_end):
        dxc = point.x() - line_start.x()
        dyc = point.y() - line_start.y()
        dxl = line_end.x() - line_start.x()
        dyl = line_end.y() - line_start.y()
        cross = dxc * dyl - dyc * dxl
        if abs(cross) > self.gui.closePointThreshold:
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
        for pt in self.gui.points:
            if (point - pt["point"]).manhattanLength() < self.gui.closePointThreshold:
                return pt["point"]
        return point

    def close_to_point(self, p1, p2):
        return (p1 - p2).manhattanLength() < self.gui.closePointThreshold

    def get_point_index(self, point):
        for pt in self.gui.points:
            if (point - pt["point"]).manhattanLength() < self.gui.closePointThreshold:
                return pt["index"]
        return len(self.gui.points)  # Assign new index if not found

    def update_scene(self):
        # Clear only the lines and circles
        for item in self.gui.scene.items():
            if item != self.gui.pixmapItem and item != self.gui.mask and not isinstance(item, QGraphicsEllipseItem):
                self.gui.scene.removeItem(item)
        
        pen = QPen(QColor(0, 255, 0), 2)
        for start, end in self.gui.lines:
            self.gui.scene.addLine(start.x(), start.y(), end.x(), end.y(), pen)
            color = Qt.blue
            if (start - end).manhattanLength() < self.gui.closePointThreshold:
                color = Qt.magenta
            self.gui.scene.addEllipse(start.x() - self.gui.pointSize / 2, start.y() - self.gui.pointSize / 2, self.gui.pointSize, self.gui.pointSize, QPen(color), QColor(color))
            self.gui.scene.addEllipse(end.x() - self.gui.pointSize / 2, end.y() - self.gui.pointSize / 2, self.gui.pointSize, self.gui.pointSize, QPen(color), QColor(color))
        if self.gui.startPoint:
            self.gui.scene.addEllipse(self.gui.startPoint["point"].x() - self.gui.pointSize / 2, self.gui.startPoint["point"].y() - self.gui.pointSize / 2, self.gui.pointSize, self.gui.pointSize, QPen(Qt.blue), QColor(Qt.blue))
        if self.gui.startPoint and self.gui.endPoint:
            self.gui.scene.addLine(self.gui.startPoint["point"].x(), self.gui.startPoint["point"].y(), self.gui.endPoint["point"].x(), self.gui.endPoint["point"].y(), pen)
        self.update_axis_lines()

    def update_axis_lines(self, event=None):
        if self.gui.axisLineX:
            self.gui.scene.removeItem(self.gui.axisLineX)
        if self.gui.axisLineY:
            self.gui.scene.removeItem(self.gui.axisLineY)
        if event:
            scenePos = self.gui.graphicsView.mapToScene(event.pos())
            self.gui.axisLineX = self.gui.scene.addLine(scenePos.x(), 0, scenePos.x(), self.gui.scene.height(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))
            self.gui.axisLineY = self.gui.scene.addLine(0, scenePos.y(), self.gui.scene.width(), scenePos.y(), QPen(QColor(200, 200, 200), 1, Qt.DashLine))

    def show_coordinates(self, event):
        scenePos = self.gui.graphicsView.mapToScene(event.pos())
        self.gui.coordinatesLabel.setText(f"X: {scenePos.x():.2f}, Y: {scenePos.y():.2f}")

    def remove_axis_lines(self):
        if self.gui.axisLineX:
            self.gui.scene.removeItem(self.gui.axisLineX)
            self.gui.axisLineX = None
        if self.gui.axisLineY:
            self.gui.scene.removeItem(self.gui.axisLineY)
            self.gui.axisLineY = None
