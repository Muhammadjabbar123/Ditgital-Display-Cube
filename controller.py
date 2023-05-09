from main import FirstWindow
from main import show_info_messagebox
from second import SecondWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import resources_rc
from PyQt5.QtGui import QIcon

class Controller:
    def Start(self):
        self.firstWindow = FirstWindow()
        icon = QIcon("D-blue.png")
        self.firstWindow.ui.imageeditBtn.clicked.connect(self.on_click)
        
        self.secondWindow = SecondWindow()
        self.secondWindow.ui2.backBtn.clicked.connect(self.Welcomeback)

        
        self.widget = QtWidgets.QStackedWidget()
        self.widget.setWindowIcon(icon)
        self.widget.setWindowTitle('DIMI')
        self.widget.addWidget(self.firstWindow)
        self.widget.addWidget(self.secondWindow)

        self.widget.setCurrentIndex(0)
        
        self.topleft = QtWidgets.QDesktopWidget().availableGeometry().topLeft()
        self.widget.move(self.topleft)

        self.widget.show()
    
    def on_click(self):
        '''
        This function closes the first screen and open the 2nd screen
        '''
        val = self.firstWindow.image_path
        self.firstWindow.image_path = ''
        if val == '':
            info = "Image selection"
            param = "Please select an image"
            show_info_messagebox(info,param)

        else:

            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
            self.secondWindow.display_image(val)
            val = ''
    
    def Welcomeback(self):
        # self.firstWindow.image_path = None
        self.secondWindow.ui2.slider.setValue(0)
        self.firstWindow.loading_imgs_to_library()
        self.secondWindow.img_list.clear()
        self.widget.setCurrentIndex(self.widget.currentIndex() - 1)
        
        

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    cont = Controller()
    cont.Start()
    sys.exit(app.exec_())