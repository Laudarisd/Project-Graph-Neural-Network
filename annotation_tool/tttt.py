import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QTableWidget, QTableWidgetItem, QFileDialog
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtCore import Qt
import csv

class AnnotationTool(QWidget):
    def __init__(self):
        super().__init__()
        self.drawMode = False
        self.drawing = False
        self.initUI()

    def initUI(self):
        # Create the main layout
        mainLayout = QHBoxLayout()

        # Left panel
        leftPanel = QWidget()
        leftPanelLayout = QVBoxLayout()
        leftPanel.setLayout(leftPanelLayout)
        #leftPanel.setFixedWidth(int(self.width() * 0.15))

        # Load files button
        loadFilesButton = QPushButton("Load Files")
        loadFilesButton.clicked.connect(self.loadFiles)
        leftPanelLayout.addWidget(loadFilesButton)

        # Image list
        self.imageList = QListWidget()
        leftPanelLayout.addWidget(self.imageList)

        # Zoom buttons
        zoomInButton = QPushButton("Zoom In")
        zoomInButton.clicked.connect(self.zoomIn)
        leftPanelLayout.addWidget(zoomInButton)

        zoomOutButton = QPushButton("Zoom Out")
        zoomOutButton.clicked.connect(self.zoomOut)
        leftPanelLayout.addWidget(zoomOutButton)

        # Mid panel
        midPanel = QWidget()
        midPanelLayout = QVBoxLayout()
        midPanel.setLayout(midPanelLayout)
        # midPanel.setFixedWidth(int(self.width() * 0.7))

        # Image label
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setMouseTracking(True)
        midPanelLayout.addWidget(self.imageLabel)

        # Cursor coordinates label
        self.coordLabel = QLabel()
        midPanelLayout.addWidget(self.coordLabel, 0, Qt.AlignTop | Qt.AlignRight)

        # Navigation buttons
        navigationLayout = QHBoxLayout()
        prevButton = QPushButton("Previous")
        prevButton.clicked.connect(self.prevImage)
        navigationLayout.addWidget(prevButton)

        nextButton = QPushButton("Next")
        nextButton.clicked.connect(self.nextImage)
        navigationLayout.addWidget(nextButton)

        drawButton = QPushButton("Draw")
        drawButton.clicked.connect(self.toggleDrawMode)
        navigationLayout.addWidget(drawButton)

        midPanelLayout.addLayout(navigationLayout)

        # Right panel
        rightPanel = QWidget()
        rightPanelLayout = QVBoxLayout()
        rightPanel.setLayout(rightPanelLayout)
        # rightPanel.setFixedWidth(int(self.width() * 0.15))

        # Connections table
        self.connectionsTable = QTableWidget()
        self.connectionsTable.setColumnCount(4)
        self.connectionsTable.setHorizontalHeaderLabels(["Index From", "Index To", "Start Coordinates", "End Coordinates"])
        rightPanelLayout.addWidget(self.connectionsTable)

        # Save annotation button
        saveAnnotationButton = QPushButton("Save Annotation")
        saveAnnotationButton.clicked.connect(self.saveAnnotation)
        rightPanelLayout.addWidget(saveAnnotationButton)

        # Add panels to the main layout
        mainLayout.addWidget(leftPanel)
        mainLayout.addWidget(midPanel, stretch=1)  # Allow mid panel to stretch
        mainLayout.addWidget(rightPanel)

        self.setLayout(mainLayout)
        self.setWindowTitle("Annotation Tool")
        self.setMouseTracking(True)

    def loadFiles(self):
        fileNames, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Image Files (*.png *.jpg *.bmp)")
        if fileNames:
            self.imageList.clear()
            self.imageList.addItems(fileNames)
            self.displayImage(0)

    def displayImage(self, index):
        if index < len(self.imageList):
            fileName = self.imageList.item(index).text()
            image = QImage(fileName)
            pixmap = QPixmap.fromImage(image)
            self.imageLabel.setPixmap(pixmap)
            self.imageLabel.adjustSize()

    def prevImage(self):
        currentRow = self.imageList.currentRow()
        if currentRow > 0:
            self.imageList.setCurrentRow(currentRow - 1)
            self.displayImage(currentRow - 1)

    def nextImage(self):
        currentRow = self.imageList.currentRow()
        if currentRow < self.imageList.count() - 1:
            self.imageList.setCurrentRow(currentRow + 1)
            self.displayImage(currentRow + 1)

    def zoomIn(self):
        self.imageLabel.resize(self.imageLabel.pixmap().size() * 1.25)

    def zoomOut(self):
        self.imageLabel.resize(self.imageLabel.pixmap().size() / 1.25)

    # Helper methods for drawing
    def startDrawing(self, event):
        if self.drawMode:
            self.drawing = True
            self.lastPoint = event.pos()
            self.drawingPoints = [self.lastPoint]

    def updateDrawing(self, event):
        if self.drawing:
            painter = QPainter(self.imageLabel.pixmap())
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            if len(self.drawingPoints) > 1:
                painter.drawLine(self.drawingPoints[-1], event.pos())
            self.drawingPoints.append(event.pos())
            self.update()

    def stopDrawing(self, event):
        if self.drawMode:
            self.drawing = False
            self.addConnectionToTable()

    def toggleDrawMode(self):
        if self.drawMode:
            self.drawMode = False
            self.imageLabel.setDragMode(QLabel.NoDrag)
        else:
            self.drawMode = True
            self.imageLabel.setDragMode(QLabel.RubberBandDrag)

    def addConnectionToTable(self):
        row = self.connectionsTable.rowCount()
        self.connectionsTable.insertRow(row)
        self.connectionsTable.setItem(row, 0, QTableWidgetItem(str(row)))  # Index From
        self.connectionsTable.setItem(row, 1, QTableWidgetItem(str(row)))  # Index To
        self.connectionsTable.setItem(row, 2, QTableWidgetItem(str(self.drawingPoints[0])))  # Start Coordinates
        self.connectionsTable.setItem(row, 3, QTableWidgetItem(str(self.drawingPoints[-1])))  # End Coordinates
        self.drawingPoints = []

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startDrawing(event)

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.updateDrawing(event)
        x, y = event.x(), event.y()
        self.coordLabel.setText(f"Cursor: ({x}, {y})")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.stopDrawing(event)

    def saveAnnotation(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Annotation", "", "CSV Files (*.csv)")
        if fileName:
            with open(fileName, 'w', newline='') as csvFile:
                writer = csv.writer(csvFile)
                writer.writerow(["Index From", "Index To", "Start Coordinates", "End Coordinates"])
                for row in range(self.connectionsTable.rowCount()):
                    rowData = []
                    for column in range(self.connectionsTable.columnCount()):
                        item = self.connectionsTable.item(row, column)
                        if item is not None:
                            rowData.append(item.text())
                        else:
                            rowData.append("")
                    writer.writerow(rowData)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    annotationTool = AnnotationTool()
    annotationTool.show()
    sys.exit(app.exec_())