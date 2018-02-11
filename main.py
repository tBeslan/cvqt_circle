import sys
from PyQt5.QtCore import QPoint, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QMessageBox
from PyQt5.QtGui import QImage, QPainter, QBrush, QPalette, QPixmap
from PyQt5 import uic, QtGui, QtWidgets, QtCore
from queue import Queue
import cv2
import numpy as np
import threading
import messagebox

# from mainui import Ui_MainWindow

qtCreatorFile = "mainwindow.ui"
qtDialogFile = "dialog.ui"

running = False
capture_thread = None
q = Queue()

param1=40
param2=20
minRadius=60
maxRadius=70

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
Ui_Dialog, QtBaseClass = uic.loadUiType(qtDialogFile)

def grab(cam, queue, width, height, fps):
    global running
    capture = cv2.VideoCapture(cam)
    if capture.isOpened() == False:
       return -1

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    capture.set(cv2.CAP_PROP_FPS, fps)

    while(running):
        global param1
        global param2
        global minRadius
        global maxRadius
        print(param1)
        frame = {}
        # -----------------------------
        capture.grab()
        retval, img = capture.retrieve(0)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        equ = cv2.equalizeHist(gray)
        res = np.hstack((gray, equ))  # stacking images side-by-side
        cv2.medianBlur(res, 7, res)
        circles = cv2.HoughCircles(res, cv2.HOUGH_GRADIENT, 1, 150, param1=param1, param2=param2,
                                   minRadius=minRadius, maxRadius=maxRadius)
        if circles is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            circles = np.round(circles[0, :]).astype("int")
            cv2.putText(img, str(len(circles) / 2), (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255))
            # loop over the (x, y) coordinates and radius of the circles
            for (x, y, r) in circles:
                # draw the circle in the output image, then draw a rectangle
                # corresponding to the center of the circle
                # count=count+1
                text = "x: " + str(x) + "  y: " + str(y)
                cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 0)
                cv2.circle(img, (x, y), r, (0, 255, 0), 4)
                cv2.rectangle(img, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
        #--------------------------------------
        frame["img"] = img

        if queue.qsize() < 10:
            queue.put(frame)
        else:
            print (queue.qsize())

class OwnImageWidget(QWidget):
    def __init__(self, parent=None):
        super(OwnImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        sz = image.size()
        self.setMinimumSize(sz)
        self.update()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QtCore.QPoint(0, 0), self.image)
        qp.end()


class myMainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(myMainWindow, self).__init__(parent)  # call init of QMainWindow, or QWidget or whatever)
        self.setupUi(self)  # call the function that actually does all the stuff you set up in QtDesigner

        self.startButton.clicked.connect(self.start_clicked)

        self.maxRadiusSpin.setValue(maxRadius)
        self.minRadiusSpin.setValue(minRadius)
        self.param1Spin.setValue(param1)
        self.param2Spin.setValue(param2)

        self.param1Spin.valueChanged.connect(self.param1Change)
        self.param2Spin.valueChanged.connect(self.param2Change)
        self.minRadiusSpin.valueChanged.connect(self.minRadiusChange)
        self.maxRadiusSpin.valueChanged.connect(self.maxRadiusChange)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1)

    def param1Change(self):
        global param1
        param1 = self.param1Spin.value()

    def param2Change(self):
        global param2
        param2 = self.param2Spin.value()

    def minRadiusChange(self):
        global minRadius
        minRadius = self.minRadiusSpin.value()

    def maxRadiusChange(self):
        global maxRadius
        maxRadius = self.maxRadiusSpin.value()

    def start_clicked(self):

        # Dialog.exec_()
        # if Dialog.exec_():  # here dialog will be shown and main script will wait for its closing (with no errors)
        #     print("Done dialog")
        global running
        if running == False:
            running = True
            capture_thread.start()
            # self.startButton.setEnabled(False)
            self.startButton.setText('Starting...')
        else:
            running = False
            # capture_thread._stop()

    def update_frame(self):
        if not q.empty():
            self.startButton.setText('Camera is live')
            frame = q.get()
            img = frame["img"]

            img_height, img_width, img_colors = img.shape

            screenShape = self.videoLabel.geometry()
            scale_w = float(screenShape.width()) / float(img_width)
            scale_h = float(screenShape.height()) / float(img_height)
            scale = min([scale_w, scale_h])

            if scale == 0:
                scale = 1

            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            height, width, bpc = img.shape
            bpl = bpc * width
            image = QtGui.QImage(img.data, width, height, bpl, QtGui.QImage.Format_RGB888)
            palette = QPalette()
            palette.setBrush(10, QBrush(image))
            self.videoLabel.setPixmap(QPixmap(image))

    def closeEvent(self, event):
        global running
        running = False

class myDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(myDialog, self).__init__(parent)  # call init of QMainWindow, or QWidget or whatever)
        self.setupUi(self)  # call the function that actually does all the stuff you set up in QtDesigner

    def accept(self):
        print("accept")

    def reject(self):
        print("reject")


if __name__ == "__main__":
    import sys

    capture_thread = threading.Thread(target=grab, args=(0, q, 800, 600, 30))

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = myMainWindow()
    # Dialog = myDialog()

    # error_dialog = QtWidgets.QErrorMessage()
    # error_dialog.showMessage('Oh No')
    MainWindow.show()
    sys.exit(app.exec_())
