import simplepyble 
import os
import matplotlib.pyplot as plt
import bluetooth
import cv2
import numpy as np
import qimage2ndarray

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtCore import QThread
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
#from pyqtgraph.opengl import GLViewWidget, MeshData, GLMeshItem
from PIL import Image

from scripts import Images
import binascii
from bleak import BleakClient, BleakScanner
import ble_devices
import webbrowser
import imageio
from skimage.transform import resize, rescale
#import pyqtgraph.opengl as gl
#from stl import mesh
from datetime import datetime
import threading
from threading import Event
import sys
import time

devices_names = []
peripherals = []
services__ = None
holo_image_path = []
service_uuid = None
characteristic_uuid = None
peripheral = None
progress_count = 0
holo_name = None
bleindex = 0
ble_flag = False
ble_check_flag = False
images_paths = []
class BLEThread(QThread):
    def __init__(self):
        super().__init__()
    global bleindex
    def run(self):
        global services__
        global peripheral
        global service_uuid
        global characteristic_uuid
        global peripherals
        global ble_flag

        peripheral = peripherals[bleindex]
        if peripheral.is_connectable():
            try:
                peripheral.connect()
                services__= peripheral.services()
                service_characteristic_pair = []
                for service in services__:
                    for characteristic in service.characteristics():
                        service_characteristic_pair.append((service.uuid(), characteristic.uuid()))
                service_uuid, characteristic_uuid = service_characteristic_pair[5]
                ble_flag = True
            except Exception as e:
                ble_flag = False

class Ble_connection_check(QThread):
        '''
        This function checks the bluetooth connection continuously and it will show message box
        when ever bluetooth disconnected.
        '''
        message_signal = pyqtSignal(str)
        def run(self):    
            global peripheral
            global ble_check_flag
            global services__
            while ble_check_flag==True:
                if peripheral.is_connected():
                    pass
                else:
                    services__ = None
                    ble_check_flag = False
                    self.message_signal.emit("Work done")

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
    

class Worker(QtCore.QObject):
    '''
    this class is used for scanning ble devices and append the names/mac addresses of devices in list
    '''
    finished = QtCore.pyqtSignal()

    def run(self): 
        global devices_names
        global peripherals
        adapters = simplepyble.Adapter.get_adapters()

        if len(adapters) == 0:
            self.finished.emit()
        adapter = adapters[0]
        adapter.set_callback_on_scan_stop(lambda: print("Scan complete."))
        adapter.scan_for(5000)
        peripherals = adapter.scan_get_results()
        self.devices_found = ble_devices.devices_found()
        self.mac_address = []
        devices_names = []
        for peripheral in peripherals:
            self.mac_address.append(peripheral.address())
        devices_names = []
        if len(self.devices_found) == 0:
            devices_names = self.mac_address.copy()
        else:
            for addr in self.mac_address:
                for index, j in enumerate(self.devices_found):
                    d_addr = j.address
                    d_addr= d_addr.lower()
                    if addr == d_addr and j.name is not None:
                        devices_names.append(j.name)
                        break
                    elif addr == d_addr and j.name is None:
                        devices_names.append(addr)
                        break                    
                    elif addr != d_addr and index+1 == len(self.devices_found):
                        devices_names.append(addr)
                    else:
                        pass
        self.finished.emit()
class Sending_hologram_thread(QtCore.QObject):
    '''
    this class is used for sending holograms over bluetooth to esp32
    it will first send upper hlogarm and then lower hologram
    '''
    finished = QtCore.pyqtSignal(int)

    def run(self):
        global services__
        global holo_image_path
        global service_uuid
        global characteristic_uuid
        global peripheral
        global progress_count
        try:
            for val in holo_image_path:

                second_image_path = val.split('_')[0]
                path = second_image_path + '_b.png'
                filename = val
                short_list=[]
                filename_1=val
                filename_2=path

                with open(filename_1, 'rb') as f:
                    content1 = f.read()
                with open(filename_2, 'rb') as f:
                    content2 = f.read()    
                real_content_1 = binascii.hexlify(content1).decode('utf-8')
                real_content_2 = binascii.hexlify(content2).decode('utf-8')

                final_list_1=[]
                final_list_2=[]

                for (op, code) in zip(real_content_1[0::2], real_content_1[1::2]):
                    final_list_1.append('0x'+op+code)
                for i in range(0, len(final_list_1)):  
                    final_list_1[i] = int(final_list_1[i],16)
                for (op, code) in zip(real_content_2[0::2], real_content_2[1::2]):
                    final_list_2.append('0x'+op+code)
                for i in range(0, len(final_list_2)):  
                    final_list_2[i] = int(final_list_2[i],16)

                numpyArr_1 = np.array(final_list_1)
                numpyArr_2 = np.array(final_list_2)

                length_1 = numpyArr_1.shape[0]//100 
                extra_1 = numpyArr_1[length_1*100:numpyArr_1.shape[0]].tobytes()

                length_2 = numpyArr_2.shape[0]//100 
                extra_2 = numpyArr_2[length_2*100:numpyArr_2.shape[0]].tobytes()
                print("sending data image 1 ")

                for  i in range(1,101):
                    sess = numpyArr_1[length_1*(i-1):length_1*i]
                    
                    content_1 = sess.tobytes()
                    peripheral.write_request(service_uuid, characteristic_uuid, content_1)
                    if i%2 ==1:
                        progress_count = progress_count + 1
                        self.finished.emit(progress_count)

                peripheral.write_request(service_uuid, characteristic_uuid, extra_1)   


                image_first_check = 111
                end1 = image_first_check.to_bytes(1, byteorder="big")
                image_2nd_check = 222
                end2 = image_2nd_check.to_bytes(1, byteorder="big")
                image_3rd_check = 111
                end3 = image_3rd_check.to_bytes(1, byteorder="big")
                peripheral.write_request(service_uuid, characteristic_uuid, end1)
                peripheral.write_request(service_uuid, characteristic_uuid, end2) 
                peripheral.write_request(service_uuid, characteristic_uuid, end3) 

                print("sending data image 2 ")
                progress_count = 50
                for  i in range(1,101):
                    sess = numpyArr_2[length_2*(i-1):length_2*i]
                    
                    content_2 = sess.tobytes()
                    peripheral.write_request(service_uuid, characteristic_uuid, content_2)
                    if i%2 ==1:
                        progress_count = progress_count + 1
                        self.finished.emit(progress_count) 
                peripheral.write_request(service_uuid, characteristic_uuid, extra_2)  

                image_first_check = 222
                end1 = image_first_check.to_bytes(1, byteorder="big")
                image_2nd_check = 111
                end2 = image_2nd_check.to_bytes(1, byteorder="big")
                image_3rd_check = 222
                end3 = image_3rd_check.to_bytes(1, byteorder="big")      

                peripheral.write_request(service_uuid, characteristic_uuid, end1)
                peripheral.write_request(service_uuid, characteristic_uuid, end2) 
                peripheral.write_request(service_uuid, characteristic_uuid, end3) 


                print('Data Sent Sucessfully ')
                progress_count = 0
                image_sent_flag = -1
            #self.ui.progressBar.hide()
        except:
            image_sent_flag = -2
            progress_count = 0
            services__ = None
            pass
        self.finished.emit(image_sent_flag)
        #peripheral.disconnect()  

class BlueToothButton(QPushButton):
    '''
    this class is used for creating push buttons(having text connection) for bluetooth connection
    '''
    def __init__(self, *args, **kwargs):
        QListWidget.__init__(self, *args, **kwargs)
        self.setStyleSheet("QPushButton"
                             "{"
                             "background-color : lightblue;"
                             "    background-color: transparent;\n"
                            "    border-style: outset;\n"
                            "    border-width: 2px;\n"
                            "    border-radius: 10px;\n"
                            "    border-color: beige;\n"
                            "    font: bold 14px;\n"
                            "    max-width: 10em;\n"
                            "    padding: 4px;\n"
                             "}"
                             "QPushButton::pressed"
                             "{"
                             "background-color : white;"
                             "}"
                             )
        self.setText('CONNECT')
        self.setMaximumSize(QtCore.QSize(200, 35))

class BlueToothLabel(QLabel):
    '''
    This class is used for creating label (showing name of ble device) on bluetooth connection page
    '''
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)

        self.setMinimumSize(QtCore.QSize(600, 35))
        

        #self.setMaximumWidth(500)
        self.setFont(QtGui.QFont("Times",12,weight=QtGui.QFont.Bold))
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("border: 1px solid black;")
       


class HoloQList(QListWidget):
    '''
    This class is used to create holoqlist on page six of application from where we 
    can use images for hologram creation
    '''
    def __init__(self, *args, **kwargs):
        QListWidget.__init__(self, *args, **kwargs)
        self.setMinimumSize(QtCore.QSize(0, 100))
        self.setMaximumSize(QtCore.QSize(16777215, 100))
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setIconSize(QtCore.QSize(100, 60))
        self.setMovement(QtWidgets.QListView.Static)
        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setProperty("isWrapping", False)
        self.setGridSize(QtCore.QSize(200, 200))
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setUniformItemSizes(True)
        self.setObjectName("holoqlist")


class DropLabel(QLabel):
    '''
    This class is used for creating labels on page 6 (hologram creation page)
    '''
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self.setMinimumSize(QtCore.QSize(240, 240))
        self.setMaximumSize(QtCore.QSize(240, 240))
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 4px dashed #aaa;")
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setScaledContents(True)
        self.active = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.active == 0:
                self.setStyleSheet('border: 4px dashed green;')
                self.active= 1
            else:
                self.setStyleSheet("border: 4px dashed #aaa;")
                self.active = 0
class InputDialog(QDialog):
    '''
    This class is used for showing input dialog box for OTA update
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet( "background-color: #16191d;"
                            "color: #ffffff;"
                             )
        self.setWindowTitle('Wi-Fi credentials')
        self.setMaximumSize(QtCore.QSize(200, 35))
        self.setWindowIcon(QtGui.QIcon('icons/D-blue.png'))
        self.label = QLabel("Please enter your Wi-Fi credentials")

        self.username_label = QLabel('Network Name:')
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText('Enter username')
        
        # Create password field
        self.password_label = QLabel('Password:')
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText('Enter password')
        
        # Create checkbox to show/hide password
        self.show_password_checkbox = QCheckBox('Show password')
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)

        # Create login button
        self.login_button = QPushButton('Login')
        self.login_button.clicked.connect(self.accept)

        # Add widgets to layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.show_password_checkbox)
        layout.addWidget(self.login_button)
        self.setLayout(layout)
        

    def toggle_password_visibility(self, state):
        if state == Qt.Checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)

    def login(self):
        # TODO: Implement login functionality
        username = self.username_edit.text()
        password = self.password_edit.text()


    def getInputs(self):
        return (self.username_edit.text(), self.password_edit.text())

class saving_holo(QDialog):
    '''
    this class is used to show input box (when save as button on hologram creation page is pressed)
    it will take the name of hologram as input and return the name so name can be used for saveing hologram. 
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet( "background-color: #16191d;"
                            "color: #ffffff;"
                             )
        self.setWindowTitle('Saving Hologram')
        self.setMaximumSize(QtCore.QSize(200, 35))
        self.setWindowIcon(QtGui.QIcon('icons/D-blue.png'))
        self.label = QLabel("Please enter Hologram-name")

        self.first = QLineEdit(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self);

        layout = QFormLayout(self)
        
        layout.addRow(self.label)
        layout.addRow("Holo-name", self.first)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return (self.first.text())

class FirstWindow(QtWidgets.QMainWindow):
    image_path = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = uic.loadUi('firstscreen.ui', self)
        self.ui.progressBar.hide()
        self.holoqlist = HoloQList(self.ui.page_6)
        self.holoqlist.itemDoubleClicked.connect(self.imageDoubleClicked)
        self.ui.verticalLayout_17.addWidget(self.holoqlist)
        self.image_label1 = DropLabel(self.ui.frame_12)
        self.image_label1.setGeometry(QtCore.QRect(56, 212, 240, 240))
        self.image_label2 = DropLabel(self.ui.frame_12)
        self.image_label2.setGeometry(QtCore.QRect(320, 0, 240, 240))
        self.image_label3 = DropLabel(self.ui.frame_12)
        self.image_label3.setGeometry(QtCore.QRect(320, 290, 240, 240))
        self.image_label4 = DropLabel(self.ui.frame_12)
        self.image_label4.setGeometry(QtCore.QRect(590, 210, 240, 240))

        

        self.ui.connectBtn.clicked.connect(self.bluetooth_connection_page)
        self.ui.controBtn.clicked.connect(self.controls_page)
        self.ui.homeBtn.clicked.connect(self.home_page)
        self.ui.addBtn.clicked.connect(self.adding_image_to_library)
        self.ui.scanBtn.clicked.connect(self.startScanning)
        self.ui.saveholoBtn.clicked.connect(self.save_clicked)
        self.ui.imageslist.itemClicked.connect(self.Library_Image_Clicked)
        self.ui.hologramlist.itemClicked.connect(self.holo_Image_Clicked)
        self.ui.uploadBtn.clicked.connect(self.sending_holograms)
        self.ui.otaupdateBtn.clicked.connect(self.takeinputs)
        self.ui.eraseBtn.clicked.connect(self.erase)
        self.ui.saveasholoBtn.clicked.connect(self.save_as_clicked)
        self.ui.createhologramBtn.clicked.connect(self.loading_imgs_to_holoqlist)
        self.ui.holobackBtn.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(1))
        self.ui.disconnectBtn.hide()
        self.ui.disconnectBtn.clicked.connect(self.disconnect_bluetooth)
        

        self.display_home_img()
        self.loading_imgs_to_library()
        self.load_holograms()
    

        self.img1,self.img2,self.img3,self.img4 = None,None,None,None
        #self.image_path = ''
        self.counter = 0
        self.count = 0
        progress_count = 0
        self.groupBox1 = None

#////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////// Library Menu ////////////////////////////////////////////////////////
        sub_menu_buttons = [
            'Images',
            'Holograms',
        ]
        menu = QMenu()
        menu.setStyleSheet(
                "background-color: #16191d;"
                "color: #ffffff;"
                )
        menu.triggered.connect(lambda x: self.whchBtn(x))
        self.ui.libraryBtn.setMenu(menu)
        self.add_menu(sub_menu_buttons, menu)
#/////////////////////////////////////////////////////////////////////////////////////////////////
    def whchBtn(self,x):
        '''
        This function is use to select images/holograms page
        if we click images it will take us to image library.
        if we click hologram then it will take us to hologram page
        '''
        button_text = x.text()
        if button_text == 'Images':
            global holo_image_path
            if holo_image_path:
                holo_image_path.clear()
            self.ui.stackedWidget.setCurrentIndex(1)
        if button_text == 'Holograms':
            self.load_holograms()
            self.ui.stackedWidget.setCurrentIndex(2)


    def add_menu(self, data, menu_obj):
        """
        Menu creation for library
        """
        if isinstance(data, list):
            for element in data:
                self.add_menu(element, menu_obj)
        else:
            action = menu_obj.addAction(data)
            action.setIconVisibleInMenu(False)
    
    def home_page(self):
        global holo_image_path
        if holo_image_path:
            holo_image_path.clear()
        self.ui.stackedWidget.setCurrentIndex(0)
    def controls_page(self):
        global holo_image_path
        if holo_image_path:
            holo_image_path.clear()
        self.ui.stackedWidget.setCurrentIndex(3)

    def disconnect_bluetooth(self):
        global peripheral
        global services__
        peripheral.disconnect()
        self.ui.disconnectBtn.hide()
        services__ = None
        info = "Bluetooth connection"
        param = "Bluetooth disconnected"
        show_info_messagebox(info,param)
    def imageDoubleClicked(self, item):
        """
        This function sets Images on labels for hologram creation
        """
        if self.image_label1.active == 1:    
            self.image_label1.setObjectName(item.text())
            self.image_label1.setPixmap(QPixmap('images/' + item.text()))
            self.image_label1.setStyleSheet("border: 4px dashed #aaa;")
            self.image_label1.active = 0
            self.count += 1
        if self.image_label2.active == 1:
            self.image_label2.setObjectName(item.text())
            self.image_label2.setPixmap(QPixmap('images/' + item.text()))
            self.image_label2.setStyleSheet("border: 4px dashed #aaa;")
            self.image_label2.active = 0
            self.count += 1
        if self.image_label3.active == 1:
            self.image_label3.setObjectName(item.text())
            self.image_label3.setPixmap(QPixmap('images/' + item.text()))
            self.image_label3.setStyleSheet("border: 4px dashed #aaa;")
            self.image_label3.active = 0
            self.count += 1
        if self.image_label4.active == 1:
            self.image_label4.setObjectName(item.text())
            self.image_label4.setPixmap(QPixmap('images/' + item.text()))
            self.image_label4.setStyleSheet("border: 4px dashed #aaa;")
            self.image_label4.active = 0
            self.count += 1
        if self.count >= 1:
            self.label_paths()

    def label_paths(self):
            global images_paths
            self.img1 = self.image_label1.objectName()
            if len(self.img1)>=1:
                path1= "images/" + self.img1
                images_paths.append(path1)
                self.image_label1.setObjectName('')
            if len(self.img1)<1:
                images_paths.append('')
            self.img2 = self.image_label2.objectName()
            if len(self.img2) >= 1:
                path2= "images/" + self.img2
                images_paths.append(path2)
                self.image_label2.setObjectName('')
            if len(self.img2)<1:
                images_paths.append('')    
            self.img3 = self.image_label3.objectName()
            if len(self.img3) >= 1:
                path3= "images/" + self.img3
                images_paths.append(path3)
                self.image_label3.setObjectName('')
            if len(self.img3)<1:
                images_paths.append('')  
            self.img4 = self.image_label4.objectName()
            if len(self.img4) >= 1:
                path4= "images/" + self.img4
                images_paths.append(path4)
                self.image_label4.setObjectName('')
            if len(self.img4)<1:
                images_paths.append('')  

            self.image_splitting(images_paths)

    def save_clicked(self):
        if self.count >= 1:
            self.saveHolo(self.upper_holo,self.lower_holo,self.holo_upper_path,self.holo_lower_path)
        else:
            info = "Hologram creation"
            param = "Please place images on all four labels"
            show_info_messagebox(info,param)

    def saveHolo(self,holo_up,holo_low,up_path,low_path):
        """
        This function ensures that images are being set on all four labels.
        and save upper and lower holograms in holograms folder at last clear all the labels
        """
            

        holo_up_ = Image.fromarray((holo_up * 255).astype(np.uint8))
        holo_low_ = Image.fromarray((holo_low * 255).astype(np.uint8))
        holo_up = holo_up_.resize((240,240))
        holo_low = holo_low_.resize((240,240))
        holo_up.save(up_path,optimize = True,quality = 10)
        holo_low.save(low_path,optimize = True,quality = 10)
        # holo_up.save(up_path)
        # holo_low.save(low_path)
        info = "Hologram creation"
        param = "Holgram created"
        show_info_messagebox(info,param)
        self.count = 0
        self.image_label1.clear()
        self.image_label2.clear()
        self.image_label3.clear()
        self.image_label4.clear()
        images_paths.clear()




    def display_home_img(self):
        """
        This function displays the home page image
        """        
        self.img = QPixmap("DDC_HOME.ico")
        self.gv = self.findChild(QGraphicsView, "gv")
        self.scene = QGraphicsScene()
        self.scene_img = self.scene.addPixmap(self.img)
        self.gv.setScene(self.scene)





    def adding_image_to_library(self):
        '''
        This function is used to add images to library
        '''
        save_path = "images/"
        files, files_indi = QFileDialog.getOpenFileNames(self, "Choose Image File", "",
                                                "Image Files (.jpg *.png *.jpeg *.ico);;All Files ()")
        print(files_indi,'VVVVVVVVVVVVVVVVVVVVVVVVVV')
        if files:
            self.files = files
            #self.close()

            name = os.path.basename(files[0])
            it = QtWidgets.QListWidgetItem(name)
            it.setIcon(QtGui.QIcon(files[0]))
            self.ui.imageslist.addItem(it)

            image_file = cv2.imread(files[0])
            script_dir = os.path.dirname(__file__)
            rel_path = "images\\"
            abs_file_path = os.path.join(script_dir, rel_path)
            cv2.imwrite(abs_file_path+name,image_file)

            self.ui.stackedWidget.setCurrentIndex(1)


    def loading_imgs_to_library(self):
        '''
        This function loads images from Images folder
        and display those images in Image library.
        '''
        
        directory = "images/"
        self.filenames_iterator = self.load_images(directory)
        for filename in self.filenames_iterator:
            name = os.path.basename(filename)
            it = QtWidgets.QListWidgetItem(name)
            it.setIcon(QtGui.QIcon(filename))
            self.ui.imageslist.addItem(it)
    
    def load_holograms(self):
        '''
        This function is used to load holograms from holograms directory
        '''
        self.ui.hologramlist.clear()
        directory = "holoimages/"
        self.filenames_iterator = self.load_images(directory)
        for filename in self.filenames_iterator:
            name = os.path.basename(filename)
            if name.endswith("a.png"):
                it = QtWidgets.QListWidgetItem(name)
                it.setIcon(QtGui.QIcon(filename))
                self.ui.hologramlist.addItem(it)

    def loading_imgs_to_holoqlist(self):
        '''
        This function load images from images directory for hologram creation
        '''

        directory = "images/"
        self.filenames_iterator = self.load_images(directory)
        for filename in self.filenames_iterator:
            name = os.path.basename(filename)
            it = QtWidgets.QListWidgetItem(name)
            it.setIcon(QtGui.QIcon(filename))
            self.holoqlist.addItem(it)
        self.ui.stackedWidget.setCurrentIndex(5)
        info = "Hologram Creation"
        param = "Steps for creating hologram\n1.first select the label one by one on which you want to place image\n2.double clicking the image will paste the image on label\n3.Save and Save_as button are used to save holograms"
        show_info_messagebox(info,param)

    def load_images(self, directory):
        '''
        This function load images path and append them in a list so that they (paths of images)
        can be used to load images in to library or holograms
        '''
        mylist=[]
        import glob
        import os
        folder_path = directory
        for filename in glob.glob(os.path.join(folder_path,"*.png")):
            with open(filename, 'r') as f:
                mylist.append(filename)
        return mylist

    def bluetooth_connection_page(self):
        '''
        This function takes us to bluetooth page
        '''
        global holo_image_path
        if holo_image_path:
            holo_image_path.clear()
        self.ui.stackedWidget.setCurrentIndex(4)

    def startScanning(self):
        self.ui.scanBtn.setEnabled(False)
        self.movie = QMovie("giphy.gif")
        self.gif_label = QtWidgets.QLabel()
        # self.gif_label.move(50,50)
        self.gif_label.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        # self.gif_label.setMinimumSize(QtCore.QSize(200, 200))

        self.gif_label.setMaximumSize(QtCore.QSize(200, 200))
        #self.gif_label.move(600,600)
        self.gif_label.setMovie(self.movie)
        self.ui.scrollArea.setWidget(self.gif_label)
        self.ui.scrollArea.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.movie.start()

        self.thread = QtCore.QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()


        self.thread.finished.connect(self.available_devices)


    def available_devices(self):
        '''
        This function scans the bluetooth devices and saves there names
        and mac address in a list. Also display them on screen to establish
        bluetooth connection
        '''        
        global devices_names

        formLayout1 = QFormLayout()
        self.groupBox1 = QGroupBox()
        

        labelList = []
        buttonList = []
        for i in range(len(devices_names)):
            label = BlueToothLabel(devices_names[i])
            button = BlueToothButton()
            labelList.append(label)
            buttonList.append(button)
            formLayout1.addRow(labelList[i],buttonList[i])
            #formLayout1.setFormAlignment()
            formLayout1.setHorizontalSpacing(40)
            formLayout1.setFormAlignment(QtCore.Qt.AlignHCenter)
            buttonList[i].clicked.connect(lambda index, i=i:self.bluetooth_connection(i))
        self.groupBox1.setLayout(formLayout1)
        #groupBox1.setAlignment(QtCore.Qt.AlignCenter)
        self.ui.scrollArea.setWidget(self.groupBox1)
        self.ui.scanBtn.setEnabled(True)
        print("done")

    def bluetooth_connection(self, index):
        '''
        This function is used to make bluetooth connection between our application and device
        '''
        global peripherals
        global services__
        global characteristic_uuid
        global  service_uuid
        global peripheral
        global bleindex
        global ble_flag
        global ble_check_flag
        bleindex = index
        blethread = BLEThread()
        blethread.start()
        blethread.wait()
    
        if ble_flag == True:
            print("Successfully connected, to ESP32...")
            info = "Bluetooth Connection"
            param = "Connected"
            show_info_messagebox(info,param)
            self.ui.stackedWidget.setCurrentIndex(0)
            self.ui.disconnectBtn.show()
            ble_check_flag = True

            # self.ble_check = Ble_connection_check()
            # self.ble_check.message_signal.connect(self.show_message)
     
            # self.ble_check.start()
            print('done----------')
        if ble_flag == False:
            info = "Bluetooth connection"
            param = "Not Connected"
            show_info_messagebox(info,param)
        ble_flag = False

        
    def ble_notification(self,indication):
        if indication == 0:
            info = "Bluetooth connection"
            param = "Bluetooth disconnected"
            show_info_messagebox(info,param)
        else:
            pass

    def Library_Image_Clicked(self,item):
        global holo_image_path
        if holo_image_path:
            holo_image_path.clear()
        if len(self.image_path) > 0:
            self.image_path = "" 
            self.image_path = "images/" +item.text()
        if len(self.image_path) == 0:
            self.image_path = "images/" +item.text()
        
    def holo_Image_Clicked(self,item):
        global holo_image_path
        holograms_path = "holoimages/" +item.text()
        holo_image_path.append(holograms_path)



    def image_splitting(self,images_paths):
        holoimages_list1 = []
        holoimages_list2 = []
        for v in images_paths:
            if len(v) >= 1:
                label_im = cv2.imread(v)
                label_img=cv2.cvtColor(label_im, cv2.COLOR_RGB2BGR)
                i,j = (int(label_img.shape[1]), int(label_img.shape[0]/2))
                crop1 = self.rotate_bound(label_img[0:j,0:i,:],180)
                crop2 = label_img[j-1:-1,0:i,:]
                holoimages_list1.append(crop1)
                holoimages_list2.append(crop2)
            else:
                vector = np.vectorize(np.int_)
                no_image = np.array(1)
                holoimages_list1.append(no_image)
                holoimages_list2.append(no_image)

        dt = datetime.today()  # Get timezone naive now
        seconds = dt.timestamp()
        self.counter = seconds



        self.upper_hologram_creation(holoimages_list1)
        self.lower_hologram_creation(holoimages_list2)
        
    def upper_hologram_creation(self,holoimages_list1):
        holoimg2 = holoimages_list1[2]
        holoimg3 = holoimages_list1[3]
        holoimg4 = holoimages_list1[0]
        up = holoimages_list1[1]

        img_up = [up, 83, 83, -1]
        img_down = [holoimg2, 83, 83, -1]
        img_left = [holoimg4, 83, 83, -1]
        img_right = [holoimg3, 83, 83, -1]
        self.create_holo_upper(img_up,img_left,img_down,img_right,self.counter)
    def lower_hologram_creation(self,holoimages_list2):
        holoimg2 = holoimages_list2[2]
        holoimg3 = holoimages_list2[3]
        holoimg4 = holoimages_list2[0]
        up = holoimages_list2[1]

        img_up = [up, 83, 83, -1]
        img_down = [holoimg2, 83, 83, -1]
        img_left = [holoimg4, 83, 83, -1]
        img_right = [holoimg3, 83, 83, -1]
        self.create_holo_lower(img_up,img_left,img_down,img_right,self.counter)

        #self.makeHologram1(holoimages_list1,self.counter)
        #self.makeHologram2(holoimages_list2,self.counter)
    def create_holo_upper(self,img_up_params, img_left_params, img_down_params, img_right_params,counter):
        ## [img, hegiht, width, offset]
        hologram = np.zeros(((img_up_params[1]+img_down_params[1]+img_up_params[-1]+img_down_params[-1]+max(img_left_params[2], img_right_params[2])),\
                            (img_left_params[1]+img_right_params[1]+img_left_params[-1]+img_right_params[-1]+img_up_params[2]), 3))
        img_up = resize(img_up_params[0].copy(), (img_up_params[1], img_up_params[2], 3))
        img_left = self.rotate_bound(resize(img_left_params[0].copy(), (img_left_params[1], img_left_params[2], 3)), 270)
        img_down = self.rotate_bound(resize(img_down_params[0].copy(), (img_down_params[1], img_down_params[2], 3)), 180)
        img_right = self.rotate_bound(resize(img_right_params[0].copy(), (img_right_params[1], img_right_params[2], 3)), 90)

        hologram[0:img_up.shape[0], img_left.shape[1]+img_left_params[-1]:img_left.shape[1]+img_left_params[-1]+img_up.shape[1], :] = img_up
        hologram[img_up.shape[0]+img_up_params[-1]:img_up.shape[0]+img_up_params[-1]+img_left.shape[0], 0:img_left.shape[1], :] = img_left
        hologram[img_up.shape[0]+img_left.shape[0]+img_down_params[-1]+img_up_params[-1]:hologram.shape[0], img_left.shape[1]+img_left_params[-1]:img_down.shape[1]+img_left.shape[1]+img_left_params[-1]:] = img_down
        hologram[img_up.shape[0]+img_up_params[-1]:img_right.shape[0]+img_up.shape[0]+img_up_params[-1], img_left.shape[1]+img_left_params[-1]+img_right_params[-1]+img_up.shape[1]:hologram.shape[1], :] = img_right
        
        # pil_image = Image.fromarray((hologram * 255).astype(np.uint8))
        #pil_image.thumbnail((240,240))
        # plt.imshow(hologram)
        # plt.show()
        script_dir = os.path.dirname(__file__)
        rel_path = "holoimages"
        abs_file_path = os.path.join(script_dir, rel_path)
        self.up_path = abs_file_path + "//"
        image_name = '/holo' + str(counter) + "_b.png"
        # plt.axis("off")
        self.holo_upper_path = abs_file_path+image_name
        #pil_image.save(abs_file_path+image_name)
        # plt.close()
        self.upper_holo = hologram
        return hologram
    def create_holo_lower(self,img_up_params, img_left_params, img_down_params, img_right_params,counter):
        ## [img, hegiht, width, offset]
        hologram = np.zeros(((img_up_params[1]+img_down_params[1]+img_up_params[-1]+img_down_params[-1]+max(img_left_params[2], img_right_params[2])),\
                            (img_left_params[1]+img_right_params[1]+img_left_params[-1]+img_right_params[-1]+img_up_params[2]), 3))
        img_up = resize(img_up_params[0].copy(), (img_up_params[1], img_up_params[2], 3))
        img_left = self.rotate_bound(resize(img_left_params[0].copy(), (img_left_params[1], img_left_params[2], 3)), 270)
        img_down = self.rotate_bound(resize(img_down_params[0].copy(), (img_down_params[1], img_down_params[2], 3)), 180)
        img_right = self.rotate_bound(resize(img_right_params[0].copy(), (img_right_params[1], img_right_params[2], 3)), 90)

        hologram[0:img_up.shape[0], img_left.shape[1]+img_left_params[-1]:img_left.shape[1]+img_left_params[-1]+img_up.shape[1], :] = img_up
        hologram[img_up.shape[0]+img_up_params[-1]:img_up.shape[0]+img_up_params[-1]+img_left.shape[0], 0:img_left.shape[1], :] = img_left
        hologram[img_up.shape[0]+img_left.shape[0]+img_down_params[-1]+img_up_params[-1]:hologram.shape[0], img_left.shape[1]+img_left_params[-1]:img_down.shape[1]+img_left.shape[1]+img_left_params[-1]:] = img_down
        hologram[img_up.shape[0]+img_up_params[-1]:img_right.shape[0]+img_up.shape[0]+img_up_params[-1], img_left.shape[1]+img_left_params[-1]+img_right_params[-1]+img_up.shape[1]:hologram.shape[1], :] = img_right
        # pil_image = Image.fromarray((hologram * 255).astype(np.uint8))
        #pil_image.thumbnail((240,240))
        # plt.imshow(hologram)
        # plt.show()
        script_dir = os.path.dirname(__file__)
        rel_path = "holoimages"
        abs_file_path = os.path.join(script_dir, rel_path)
        self.low_path = abs_file_path + '//'
        image_name = '/holo' + str(counter) + "_a.png"
        # plt.imshow(hologram)
        # plt.show()
        # plt.axis("off")
        self.holo_lower_path = abs_file_path+image_name
        #pil_image.save(abs_file_path+image_name)
        self.lower_holo = hologram
        

        return hologram

    def rotate_bound(self,image, angle):
        # grab the dimensions of the image and then determine the
        # center
        (h, w) = image.shape[:2]
        (cX, cY) = (w // 2, h // 2)
    
        # grab the rotation matrix (applying the negative of the
        # angle to rotate clockwise), then grab the sine and cosine
        # (i.e., the rotation components of the matrix)
        M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
    
        # compute the new bounding dimensions of the image
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))
    
        # adjust the rotation matrix to take into account translation
        M[0, 2] += (nW / 2) - cX
        M[1, 2] += (nH / 2) - cY
    
        # perform the actual rotation and return the image
        return cv2.warpAffine(image, M, (nW, nH))
    def sending_holograms(self):
        '''
        This function is used to upload holograms to device
        '''
        global holo_image_path
        global services__
        if holo_image_path:
            original_holo = ""
            for name in holo_image_path:
                name_of_holo = name.split('/')[1]
                original_holo = original_holo + " "+ name_of_holo

            if services__ is None:
                info = "Bluetooth connection"
                param = "Please connect with bluetooth device-------"
                show_info_messagebox(info,param)


            else:
                info = "Hologram uploading"
                param = "Do you want to upload" + original_holo
                ret = show_info_messagebox(info,param)
                if ret==True:
                    self.ui.progressBar.show()
                    self.thread = QtCore.QThread()
                    self.worker = Sending_hologram_thread()
                    self.worker.moveToThread(self.thread)
                    self.thread.started.connect(self.worker.run)
                    self.worker.finished.connect(self.updateProgressBar)
                    self.worker.finished.connect(self.thread.quit)
                    self.worker.finished.connect(self.worker.deleteLater)
                    self.thread.finished.connect(self.thread.deleteLater)

                    self.thread.start()
                else:
                    self.ui.stackedWidget.setCurrentIndex(2)
        elif not holo_image_path:
            if services__ is None:
                info = "Bluetooth connection"
                param = "Please connect with bluetooth device"
                show_info_messagebox(info,param)
            else:
                info = "Hologram selection"
                param = "Please select hologram"
                show_info_messagebox(info,param)


        #self.thread.finished.connect(self.updateProgressBar)
    def updateProgressBar(self,maxval):
        global progress_count
        global holo_image_path
        if maxval == -1:
            self.ui.progressBar.hide()
            self.ui.progressBar.setValue(0)
            progress_count = 0
            info = "Uploading hologram"
            param = "Hologram is uploaded"
            show_info_messagebox(info,param)
            holo_image_path.clear()   
        if maxval == -2:
            self.ui.progressBar.hide()
            self.ui.progressBar.setValue(0)
            progress_count = 0
            info = "Bluetooth Connection"
            param = "Bluetooth disconnected while uploading hologram."
            show_info_messagebox(info,param)
            holo_image_path.clear()
            self.ui.disconnectBtn.hide()


        self.ui.progressBar.setValue(maxval)

        #self.thread.finished.connect(self.available_devices)

    

    def takeinputs(self):
        '''
        this functions takes SSID and Password as input for OTA update
        '''
        global service_uuid
        global characteristic_uuid
        global peripheral
        if services__ is None:
            info = "Bluetooth Connection"
            param = "Please connect with bluetooth device"
            show_info_messagebox(info,param)
        else:
            dialog = InputDialog()
            dialog.setStyleSheet(	#"border: none;"
                            "background-color: #16191d;"
                            "background: transparent;"
                            # "padding:0;"
                            # "margin: 0;"
                            "color: #ffffff;"
                            )
            dialog.exec()
            ssid,password=dialog.getInputs()
            if len(ssid) == 0 or len(password) == 0:
                info = "OTA update"
                param = "Please fill the fields of network and password "
                show_info_messagebox(info,param)
            else:
                self.string ="(SSID)"+ ssid + ":::"+"(PASS)"+password
                self.string = bytes(self.string, 'utf-8')
                try:
                    peripheral.write_request(service_uuid, characteristic_uuid, self.string)
                except:
                    print('not sended')
                    pass
    def stl_file_display(self,stl_mesh):
        self.viewer = gl.GLViewWidget()
        self.viewer.setCameraPosition(distance=40)
        try:
            self.viewer.removeItem(self.currentSTL)
        except:
            self.verticalLayout_15.addWidget(self.viewer, 1)
            g = gl.GLGridItem()
            g.setSize(100, 100)
            g.setSpacing(5, 5)
            self.viewer.addItem(g)

            points = stl_mesh.points.reshape(-1, 3)
            faces = np.arange(points.shape[0]).reshape(-1, 3)

            mesh_data = MeshData(vertexes=points, faces=faces)
            mesh = GLMeshItem(meshdata=mesh_data, smooth=True, drawFaces=False, drawEdges=True, edgeColor=(0, 1, 0, 1))
            self.viewer.addItem(mesh)
            self.ui.stackedWidget.setCurrentIndex(6)
    def erase(self):
        self.ui.eraseBtn.setDisabled(True)
        info = "Erase"
        param = "This button is disabled for now"
        ret = show_info_messagebox(info,param)
    def save_as_clicked(self):
        if self.count >= 4:
            self.click_save_as(self.upper_holo,self.lower_holo,self.up_path,self.low_path)
        else:
            info = "Hologram creation"
            param = "Please place images on all four labels"
            show_info_messagebox(info,param)

    def click_save_as(self,upper,lower,upper_path,lower_path):
        global holo_name
        
        self.saving_holo = saving_holo()
        self.saving_holo.exec()
        holo_name = self.saving_holo.getInputs()
        if len(holo_name) > 0:
            upper_ = Image.fromarray((upper * 255).astype(np.uint8))
            lower_ = Image.fromarray((lower * 255).astype(np.uint8))
            upper = upper_.resize((240,240))
            lower = lower_.resize((240,240))
            up_name = upper_path + str(holo_name) + '_a.png'
            low_name = lower_path + str(holo_name) + '_b.png'
            upper.save(up_name)
            lower.save(low_name)
            info = "Hologram creation"
            param = "Holograms created"
            show_info_messagebox(info,param)
        else:
            pass
        self.count = 0
        self.image_label1.clear()
        self.image_label2.clear()
        self.image_label3.clear()
        self.image_label4.clear()

 
    def show_message(self):
        info = "Bluetooth connection"
        param = "Bluetooth disconnected"


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
        retval = msg.exec()
        if retval == QMessageBox.Ok:
            print("OK!")
        self.ui.disconnectBtn.hide()