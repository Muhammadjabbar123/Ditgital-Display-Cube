import sys
import cv2
import qimage2ndarray
import pathlib
from copy import deepcopy
from scripts import Images
import numpy as np
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
#from widgets import Brightness
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from rembg import remove
from PIL import Image
#import easygui as eg
import os




def show_info_messagebox(info,param):
    '''
    this function is used to show message box
    '''
    msg = QMessageBox()
    msg.setStyleSheet(	#"border: none;"
                        "background-color: #16191d;"
                        # "background: transparent;"
                        # "padding:0;"
                        # "margin: 0;"
                        "color: #ffffff;"
                        )
    msg.setWindowIcon(QtGui.QIcon('icons/D-blue.png'))
   

    # setting message for Message Box
    msg.setText(param)
    
    # setting Message box window title
    msg.setWindowTitle(info)
    
    # declaring buttons on Message Box
    msg.setStandardButtons(QMessageBox.Ok)
    
    # start the app
    retval = msg.exec_()
    if msg.clickedButton() is msg.button(QMessageBox.Ok):
        return True
def show_feature_messagebox(info,param):
    '''
    this function is used to show message box
    '''
    msg = QMessageBox()
    msg.setStyleSheet(	#"border: none;"
                        "background-color: #16191d;"
                        # "background: transparent;"
                        # "padding:0;"
                        # "margin: 0;"
                        "color: #ffffff;"
                        )
    msg.setWindowIcon(QtGui.QIcon('icons/D-blue.png'))
   

    # setting message for Message Box
    msg.setText(param)
    
    # setting Message box window title
    msg.setWindowTitle(info)
    
    # declaring buttons on Message Box
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No )
    
    # start the app
    retval = msg.exec_()
    if msg.clickedButton() is msg.button(QMessageBox.Yes):
        return True
    if msg.clickedButton() is msg.button(QMessageBox.No):
        return False




class ResizableRubberBand(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ResizableRubberBand, self).__init__(parent)

        self.draggable = True
        self.dragging_threshold = 5
        self.mousePressPos = None
        self.mouseMovePos = None
        self.borderRadius = 5
        self.setMinimumSize(150, 150)

        self.setWindowFlags(QtCore.Qt.SubWindow)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            QtWidgets.QSizeGrip(self), 0,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        layout.addWidget(
            QtWidgets.QSizeGrip(self), 0,
            QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self._band = QtWidgets.QRubberBand(
            QtWidgets.QRubberBand.Rectangle, self)
        self._band.show()
        self.show()

    def resizeEvent(self, event):
        self._band.resize(self.size())

    def paintEvent(self, event):
        # Get current window size
        window_size = self.size()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        qp.drawRoundedRect(0, 0, window_size.width(), window_size.height(),
                           self.borderRadius, self.borderRadius)
        qp.end()

    def mousePressEvent(self, event):
        if self.draggable and event.button() == QtCore.Qt.RightButton:
            self.mousePressPos = event.globalPos()                # global
            self.mouseMovePos = event.globalPos() - self.pos()    # local
        super(ResizableRubberBand, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() & QtCore.Qt.RightButton:
            globalPos = event.globalPos()
            moved = globalPos - self.mousePressPos
            if moved.manhattanLength() > self.dragging_threshold:
                # Move when user drag window more than dragging_threshold
                diff = globalPos - self.mouseMovePos
                self.move(diff)
                self.mouseMovePos = globalPos - self.pos()
        super(ResizableRubberBand, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mousePressPos is not None:
            if event.button() == QtCore.Qt.RightButton:
                moved = event.globalPos() - self.mousePressPos
                if moved.manhattanLength() > self.dragging_threshold:
                    # Do not call click event or so on
                    event.ignore()
                self.mousePressPos = None
        super(ResizableRubberBand, self).mouseReleaseEvent(event)


class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super(QGraphicsView, self).__init__(parent)
        self.setMinimumSize(QtCore.QSize(892, 500))
        self._zoom = 0
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(1)
        self.aspectRatioMode = Qt.AspectRatioMode.KeepAspectRatio
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.imageCrop = None
        self.rect_item = None

        self.show()

    def setPixmap(self, img):
        self.scene_img = QGraphicsPixmapItem(img)
        self.scene.addItem(self.scene_img)
        self.setSceneRect(self.scene_img.boundingRect())
        self.centerOn(self.scene_img.boundingRect().center())

    def setRect(self, rect):
        self.rect_item = QGraphicsRectItem(rect)
        self.rect_item.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.rect_item.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(self.rect_item)
        self.x = self.rect_item.boundingRect().center().x()
        self.y = self.rect_item.boundingRect().center().y()
        self.rect_x = self.scene_img.boundingRect().center().x() - self.x
        self.rect_y = self.scene_img.boundingRect().center().y() - self.y
        self.rect_item.setPos(self.rect_x, self.rect_y)

    def setRubberband(self):
        self.imageCrop = ResizableRubberBand(self.viewport())
        self.imageCrop.move(self.viewport().rect().center() - self.imageCrop.rect().center())
    
    def wheelEvent(self, event):
        zoomInFactor = 1.25
        zoomOutFactor = 1 / zoomInFactor
        # Zoom
        if event.angleDelta().y() > 0:
            self._zoom += 1
            if self._zoom < 0:
                self._zoom = 0
            else:
                #self.scale(zoomInFactor, zoomInFactor)
                if self.scene_img.scale() < 10:
                    self.scene_img.setScale(self.scene_img.scale() * zoomInFactor)
                    self.setSceneRect(0, 0, self.scene_img.boundingRect().width() ** zoomInFactor, self.scene_img.boundingRect().height() ** zoomInFactor)
                    center = self.mapToScene(self.viewport().rect().center())
                    self.centerOn(center)
                    if self.rect_item:
                        self.rect_x = center.x() - self.x
                        self.rect_y = center.y() - self.y
                        self.rect_item.setPos(self.rect_x, self.rect_y)
                    if self.imageCrop:
                        self.imageCrop.move(self.viewport().rect().center() - self.imageCrop.rect().center())

        else:
            self._zoom -= 1
            if self._zoom < 0:
                self._zoom = 0
            else:
                if self.scene_img.scale() > 1:
                    self.scene_img.setScale(self.scene_img.scale() * zoomOutFactor)
                    center = self.mapToScene(self.viewport().rect().center())
                    self.centerOn(center)
                    if self.rect_item:
                        self.rect_x = center.x() - self.x
                        self.rect_y = center.y() - self.y
                        self.rect_item.setPos(self.rect_x, self.rect_y)
                    if self.imageCrop:
                        self.imageCrop.move(self.viewport().rect().center() - self.imageCrop.rect().center())
                else: 
                    self.scene_img.setScale(1.00)
                    self.setSceneRect(0, 0, self.scene_img.boundingRect().width(), self.scene_img.boundingRect().height())
                    center = self.mapToScene(self.viewport().rect().center())
                    self.centerOn(self.scene_img.boundingRect().center())
                    if self.rect_item:
                        self.rect_x = center.x() - self.x
                        self.rect_y = center.y() - self.y
                        self.rect_item.setPos(self.rect_x, self.rect_y)
                    if self.imageCrop:
                        self.imageCrop.move(self.viewport().rect().center() - self.imageCrop.rect().center())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.rect_item:
            center = self.mapToScene(self.viewport().rect().center())
            self.rect_x = center.x() - self.x
            self.rect_y = center.y() - self.y
            self.rect_item.setPos(self.rect_x, self.rect_y)
        if self.imageCrop:
            self.imageCrop.move(self.viewport().rect().center() - self.imageCrop.rect().center())
        return super().mouseMoveEvent(event)



class Worker(QtCore.QObject):
    '''
    this class is used for scanning ble devices and append the names/mac addresses of devices in list
    '''
    finished = QtCore.pyqtSignal(np.ndarray)

    def run(self,val): 

        pil_image=Image.fromarray(val)
        print(pil_image)
        back_g_removed = np.array(remove(pil_image))

        
        self.finished.emit(back_g_removed)
                


class SecondWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui2 = uic.loadUi('second_screen.ui', self)
        self.ui2.saveBtn.clicked.connect(self.click_save)
        self.ui2.saveasBtn.clicked.connect(self.click_save_as)
        # self.ui2.backBtn.clicked.connect(self.on_click)
        self.ui2.cropBtn.clicked.connect(self.click_crop)
        self.ui2.brightnessBtn.clicked.connect(self.click_brightness)
        self.ui2.backremoveBtn.clicked.connect(self.remove_background)
        self.ui2.y_Btn.clicked.connect(self.click_y1)
        self.ui2.n_Btn.clicked.connect(self.click_n1)
        # self.ui2.viewfinderBtn.clicked.connect(self.view_finder_on_img)
        self.ui2.slider.hide()
        self.ui2.buttonswidget.hide()

        self.gv = ImageViewer()
        self.ui2.vbox4.addWidget(self.gv)
        
    
    def display_image(self, val):
        self.gv.scene.clear()
        print('val-------------',val)
        self.val = val
        files = [self.val]
        self.img_list, self.rb = [], None
        #print(type(files),'ooooooooooooooooo')
        for f in files:
            self.img_list.append(Images(f))
        self.img_id = 0
        self.img_class = self.img_list[self.img_id]


        self.img = QPixmap(qimage2ndarray.array2qimage(cv2.cvtColor(self.img_class.img, cv2.COLOR_BGR2RGB)))
        self.gv.setPixmap(self.img)

        self.view_finder_on_img()

        
        info = "Image editing "
        param = "Steps for image editing\nEditing options\n'Crop,Brightness,Backgroudremoval'\n1.For cropping click on crop button and move the resizeable rubber band to select the image area.\n2.For brightness control click on brightness button and adjust brightness with the slider movement.\n3.For background-removal click on background remove button.\n4.If you click on 'Back' button it will take you to the first screen.)"
        show_info_messagebox(info,param)


    def view_finder_on_img(self):
        '''
        this function places viewfoinder over an image.
        '''
        print('in viewfinder function')
        self.rect = QRectF()
        self.rect.setSize(QSizeF(50, 70))

        self.gv.setRect(self.rect)


    def hide_unhide(self):
        print('oooooooooooooo')
        if self.ui2.slider.isHidden():
            self.ui2.slider.show()
        else:
            self.ui2.slider.hide()
    

    def click_brightness(self, mode=0):
        self.hide_unhide()
        self.ui2.buttonswidget.show()
        self.ui2.y_Btn.disconnect()
        self.ui2.y_Btn.clicked.connect(self.click_y1)
        self.ui2.n_Btn.disconnect()
        self.ui2.n_Btn.clicked.connect(self.click_n1)
        self.ui2.brightnessBtn.setEnabled(False)
        self.ui2.backremoveBtn.setEnabled(False)
        self.ui2.cropBtn.setEnabled(False)
        if mode == 1:
            self.slider.setRange(0, 300)
            self.slider.setValue(100)
            self.slider.valueChanged.connect(self.change_slide_contr)
        else:
            self.slider.setRange(-120, 160)
            # self.slider.setValue(0)
            self.slider.valueChanged.connect(self.change_slide)

    def click_y1(self):
        self.img_class.img_copy = deepcopy(self.img_class.img)
        self.update_img()
        self.hide_unhide()
        self.ui2.buttonswidget.hide()
        self.ui2.cropBtn.setEnabled(True)
        self.ui2.brightnessBtn.setEnabled(True)
        self.ui2.backremoveBtn.setEnabled(True)

    def click_n1(self):
        if not np.array_equal(self.img_class.img_copy, self.img_class.img):
            msg = QMessageBox.question(self, "Cancel edits", "Confirm to discard all the changes?   ", QMessageBox.Yes | QMessageBox.No)
            if msg != QMessageBox.Yes:
                return
            else:
                self.img_class.reset()
                self.update_img()
                self.ui2.buttonswidget.hide()
                self.hide_unhide()
                self.ui2.brightnessBtn.setEnabled(True)
                self.ui2.cropBtn.setEnabled(True)
                self.ui2.backremoveBtn.setEnabled(True)
        else:
            self.img_class.reset()
            self.update_img()
            self.ui2.buttonswidget.hide()
            self.hide_unhide()
            self.ui2.brightnessBtn.setEnabled(True)
            self.ui2.cropBtn.setEnabled(True)
            self.ui2.backremoveBtn.setEnabled(True)

    def change_slide(self):
        self.brightness_value = self.slider.value()
       
        self.img_class.reset()
        self.img_class.change_b_c(beta=self.brightness_value)
        self.update_img()

    def update_img(self):
        self.gv.scene.clear()
        self.img = QPixmap(qimage2ndarray.array2qimage(cv2.cvtColor(self.img_class.img, cv2.COLOR_BGR2RGB)))
        self.gv.scene_img = self.gv.scene.addPixmap(self.img)
        self.view_finder_on_img()

    def click_crop(self):
        self.gv.setRubberband()
        self.ui2.buttonswidget.show()
        self.ui2.cropBtn.setEnabled(False)
        self.ui2.brightnessBtn.setEnabled(False)
        self.ui2.backremoveBtn.setEnabled(False)
        self.ui2.y_Btn.disconnect()
        self.ui2.y_Btn.clicked.connect(self.click_yCrop)
        self.ui2.n_Btn.disconnect()
        self.ui2.n_Btn.clicked.connect(self.click_nCrop)

    def click_yCrop(self):
        self.newImage = self.img
        poly = self.gv.mapToScene(self.gv.imageCrop.geometry())
        rect = poly.boundingRect()
        print(rect)
        self.img = QPixmap(self.newImage.copy(rect.toRect()))
        dim = self.img.size()
        image = self.img.toImage()
        s = image.bits().asstring(dim.width() * dim.height() * 4)
        image = np.fromstring(s, dtype=np.uint8).reshape((dim.height(), dim.width(), 4)) 

        self.img_class.img = image
        self.img_class.img_copy = image
        self.img_class.grand_img_copy = image

        self.update_img()

        self.gv.imageCrop.close()
        self.ui2.buttonswidget.hide()
        self.ui2.cropBtn.setEnabled(True)
        self.ui2.brightnessBtn.setEnabled(True)
        self.ui2.backremoveBtn.setEnabled(True)

    def click_nCrop(self):
        self.gv.imageCrop.close()
        self.ui2.buttonswidget.hide()
        self.ui2.cropBtn.setEnabled(True)
        self.ui2.brightnessBtn.setEnabled(True)

    def remove_background(self):

        self.ui2.backBtn.setDisabled(True)
        self.ui2.cropBtn.setDisabled(True)
        self.ui2.brightnessBtn.setDisabled(True)
        print(self.img_class.img)
        print(type(self.img_class.img))
        imag = self.img_class.img
        self.thread = QtCore.QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(lambda: self.worker.run(imag))
        self.worker.finished.connect(self.backgroundremoved)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()


        # pil_image=Image.fromarray(self.img_class.img)
        # print(pil_image)
        # back_g_removed = np.array(remove(pil_image))
    def backgroundremoved(self,back_remove_signal):
        self.img_class.img = back_remove_signal
        self.img_class.img_copy = back_remove_signal
        self.img_class.grand_img_copy = back_remove_signal
        
        self.update_img()
        info = "Image editing "
        param = "Background removed"
        show_info_messagebox(info,param)
        self.ui2.backBtn.setEnabled(True)
        self.ui2.cropBtn.setEnabled(True)
        self.ui2.brightnessBtn.setEnabled(True)

    def click_save_as(self):
        try:
            file, _ = QFileDialog.getSaveFileName(self, 'Save File', f"{self.img_class.img_name}."
                                                                     f"{self.img_class.img_format}",
                                                  "Image Files (.jpg *.png *.jpeg *.ico);;All Files ()")
            print(file, " here is the file name and path")
            self.img_class.save_img(file)
        except Exception:
            pass

    def click_save(self):
        name = self.val.split('/')[1]
        name = "edited_" + name    
        print(name,"VVVVVVV")
        script_dir = os.path.dirname(__file__)
        rel_path = "images\\"
        abs_file_path = os.path.join(script_dir, rel_path)
        print('Here is the Save path',abs_file_path+name )
        cv2.imwrite(abs_file_path+name,self.img_class.img)
        print("done------------------------")