from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QCheckBox

class LoginWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create username field
        self.username_label = QLabel('Username:')
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
        self.login_button.clicked.connect(self.login)

        # Add widgets to layout
        layout = QVBoxLayout()
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
        print('Username:', username)
        print('Password:', password)


if __name__ == '__main__':
    app = QApplication([])
    window = LoginWidget()
    window.show()
    app.exec_()
