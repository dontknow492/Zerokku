import sys
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont

from PySide6.QtWidgets import QWidget, QApplication, QGroupBox, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, \
    QMessageBox
from qfluentwidgets import PasswordLineEdit, LineEdit, CheckBox, TransparentPushButton, PrimaryPushButton, ImageLabel, \
    PopUpAniStackedWidget, MessageBox, setCustomStyleSheet, isDarkTheme, Theme, setTheme, FluentTitleBar
from qframelesswindow import FramelessWindow
from sqlalchemy.orm import sessionmaker

from database import User
from gui.common import MyLabel, AniStackedWidget

import re

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>])[A-Za-z\d!@#$%^&*(),.?\":{}|<>]{8,}$"
)

class LoginPage(QWidget):
    signInSignal = Signal()
    signUpSignal = Signal()
    forgetPasswordSignal = Signal()
    errorSignal = Signal(str, str)
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self._screen_geometry = QApplication.primaryScreen().availableGeometry()
        # self.setMaximumSize(self._screen_geometry.size())
        self.image_label = ImageLabel(self)
        self.image_label.setImage(image_path)
        self.image_label.setScaledSize(QSize(int(self._screen_geometry.width() * 0.65), self._screen_geometry.height()))
        # self.image_label.setFixedSize(QSize(200, 200))

        self.login_container = QWidget(self)

        self.title_label = MyLabel("Welcome Back", 34, QFont.Weight.DemiBold, self)
        self.body_label = MyLabel("Enter your username and password to access your account.")

        self.username_heading_label = MyLabel("Username", weight=QFont.Weight.DemiBold)
        self.username_line_edit = LineEdit()
        self.username_line_edit.setMaxLength(20)

        self.username_line_edit.setPlaceholderText("Enter your username")
        self.password_heading_label = MyLabel("Password", weight=QFont.Weight.DemiBold)
        self.password_line_edit = PasswordLineEdit()
        self.password_line_edit.setMaxLength(16)
        self.password_line_edit.setPlaceholderText("Enter your password")

        self.remember_me_checkbox = CheckBox("Remember me", parent=self)
        self.remember_me_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forget_password_button = TransparentPushButton("Forget password?", parent = self)
        self.forget_password_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.signin_button = PrimaryPushButton("Sign in", parent = self)
        self.signin_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.signup_text = "Don't have a account?"
        self.signup_button = TransparentPushButton("Sign up", parent = self)
        self.signup_button.setCursor(Qt.CursorShape.PointingHandCursor)


        self._init_ui()

        self._signal_handler()

    def _init_ui(self):

        h_layout = QHBoxLayout(self)
        # h_layout.setSpacing(70)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(self.image_label)


        v_layout = QVBoxLayout(self.login_container)
        v_layout.setContentsMargins(70, 0, 70, 0)
        v_layout.setSpacing(0)
        # v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.addStretch()
        h_sublayout = QHBoxLayout(self)
        h_sublayout.addWidget(self.remember_me_checkbox)
        h_sublayout.addWidget(self.forget_password_button)

        h2_sublayout = QHBoxLayout(self)
        text_label = MyLabel(self.signup_text)
        h2_sublayout.addStretch()
        h2_sublayout.addWidget(text_label)
        h2_sublayout.addWidget(self.signup_button)
        h2_sublayout.addStretch()

        v_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.body_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        v_layout.addSpacing(40)
        v_layout.addWidget(self.username_heading_label)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.username_line_edit)
        v_layout.addSpacing(20)
        v_layout.addWidget(self.password_heading_label)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.password_line_edit)
        # v_layout.addSpacing(10)
        v_layout.addLayout(h_sublayout)
        v_layout.addSpacing(20)
        v_layout.addWidget(self.signin_button)
        v_layout.addSpacing(10)
        v_layout.addLayout(h2_sublayout)
        v_layout.addStretch()


        h_layout.addWidget(self.image_label, stretch=1)
        h_layout.addWidget(self.login_container)

    def _signal_handler(self):
        self.signin_button.clicked.connect(self._verify)
        self.signup_button.clicked.connect(self.signUpSignal.emit)
        self.forget_password_button.clicked.connect(self.forgetPasswordSignal.emit)

    def _verify(self):
        username = self.getUsername().strip()
        password = self.getPassword().strip()

        errors = [
            (not username, "Invalid Username", "Username is required."),
            (not USERNAME_REGEX.match(username), "Invalid Username",
             "Username must be 3–20 characters (letters, numbers, underscores only)."),
            (not password, "Invalid Password", "Password is required."),
            (len(password) < 8, "Invalid Password", "Password must be at least 8 characters."),
            (not PASSWORD_REGEX.match(password), "Invalid Password",
             "Password must include uppercase, lowercase, digit, and special character.")
        ]

        for condition, title, message in errors:
            if condition:
                self.errorSignal.emit(title, message)
                return

        self.signInSignal.emit()

    def clear(self):
        self.username_line_edit.clear()
        self.password_line_edit.clear()

    def getPassword(self) -> str:
        return self.password_line_edit.text()

    def getUsername(self) -> str:
        return self.username_line_edit.text()

    def isRemembered(self) -> bool:
        return self.remember_me_checkbox.isChecked()


class RegisterPage(QWidget):
    signInSignal = Signal()
    signUpSignal = Signal()
    errorSignal = Signal(str, str)
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self._screen_geometry = QApplication.primaryScreen().availableGeometry()
        # self.setMaximumSize(self._screen_geometry.size())
        self.image_label = ImageLabel(self)
        self.image_label.setImage(image_path)
        self.image_label.setScaledSize(QSize(int(self._screen_geometry.width() * 0.65), self._screen_geometry.height()))
        # self.image_label.setFixedSize(QSize(200, 200))

        self.login_container = QWidget(self)

        self.title_label = MyLabel("Create an account", 34, QFont.Weight.DemiBold, self)
        self.body_label = MyLabel("Enter a following details to create an account.")

        self.username_heading_label = MyLabel("Username", weight=QFont.Weight.DemiBold)
        self.username_line_edit = LineEdit()
        self.username_line_edit.setMaxLength(20)
        self.username_line_edit.setPlaceholderText("Enter your username")

        self.email_heading_label = MyLabel("Email", weight=QFont.Weight.DemiBold)
        self.email_line_edit = LineEdit()
        self.email_line_edit.setPlaceholderText("Enter your email")

        self.password_heading_label = MyLabel("Password", weight=QFont.Weight.DemiBold)
        self.password_line_edit = PasswordLineEdit()
        self.password_line_edit.setMaxLength(16)
        self.password_line_edit.setPlaceholderText("Enter your password")

        self.confirm_password_heading_label = MyLabel("Confirm password", weight=QFont.Weight.DemiBold)
        self.confirm_password_line_edit = PasswordLineEdit()
        self.confirm_password_line_edit.setPlaceholderText("Re-enter your password")

        self.signup_button = PrimaryPushButton("Sign up", parent=self)
        self.signup_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.signin_text = "Already have a account?"
        self.signin_button = TransparentPushButton("Sign in", parent=self)
        self.signin_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self._init_ui()
        self._signal_handler()

    def _init_ui(self):
        h_layout = QHBoxLayout(self)
        # h_layout.setSpacing(70)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(self.image_label)

        v_layout = QVBoxLayout(self.login_container)
        v_layout.setContentsMargins(70, 0, 70, 0)
        v_layout.setSpacing(0)
        # v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.addStretch()

        h2_sublayout = QHBoxLayout(self)
        text_label = MyLabel(self.signin_text)
        h2_sublayout.addStretch()
        h2_sublayout.addWidget(text_label)
        h2_sublayout.addWidget(self.signin_button)
        h2_sublayout.addStretch()

        v_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.body_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        v_layout.addSpacing(40)
        v_layout.addWidget(self.username_heading_label)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.username_line_edit)
        v_layout.addSpacing(20)
        v_layout.addWidget(self.email_heading_label)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.email_line_edit)
        v_layout.addSpacing(30)
        v_layout.addWidget(self.password_heading_label)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.password_line_edit)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.confirm_password_heading_label)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.confirm_password_line_edit)
        v_layout.addSpacing(20)
        v_layout.addWidget(self.signup_button)
        v_layout.addSpacing(10)
        v_layout.addLayout(h2_sublayout)
        v_layout.addStretch()

        h_layout.addWidget(self.image_label, stretch=1)
        h_layout.addWidget(self.login_container)

    def _signal_handler(self):
        self.signin_button.clicked.connect(self.signInSignal.emit)
        self.signup_button.clicked.connect(self._verify)

    def _verify(self):
        username = self.getUsername().strip()
        email = self.getEmail().strip()
        password = self.getPassword().strip()
        confirm = self.getConfirmPassword().strip()

        errors = [
            (not username, "Invalid Username", "Username is required."),
            (not USERNAME_REGEX.match(username), "Invalid Username",
             "Username must be 3–20 characters (letters, numbers, underscores only)."),
            (not email, "Invalid Email", "Email is required."),
            (not EMAIL_REGEX.match(email), "Invalid Email", "Please enter a valid email address."),
            (not password, "Invalid Password", "Password is required."),
            (len(password) < 8, "Invalid Password", "Password must be at least 8 characters."),
            (not PASSWORD_REGEX.match(password), "Invalid Password",
             "Password must include uppercase, lowercase, digit, and special character."),
            (password != confirm, "Invalid Password", "Passwords do not match.")
        ]

        for condition, title, message in errors:
            if condition:
                self.errorSignal.emit(title, message)
                return

        self.signUpSignal.emit()

    def clear(self):
        self.password_line_edit.clear()
        self.username_line_edit.clear()
        self.email_line_edit.clear()
        self.confirm_password_line_edit.clear()

    def getPassword(self) -> str:
        return self.password_line_edit.text()

    def getConfirmPassword(self) -> str:
        return self.confirm_password_line_edit.text()

    def getUsername(self) -> str:
        return self.username_line_edit.text()

    def getEmail(self) -> str:
        return self.email_line_edit.text()

    def isRemembered(self) -> bool:
        return self.remember_me_checkbox.isChecked()


class ForgotPasswordPage(QWidget):
    updatePasswordSignal = Signal()
    signUpSignal = Signal()
    errorSignal = Signal(str, str) #heading, message
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self._screen_geometry = QApplication.primaryScreen().availableGeometry()
        # self.setMaximumSize(self._screen_geometry.size())
        self.image_label = ImageLabel(self)
        self.image_label.setImage(image_path)
        self.image_label.setScaledSize(QSize(int(self._screen_geometry.width() * 0.65), self._screen_geometry.height()))
        # self.image_label.setFixedSize(QSize(200, 200))

        self.login_container = QWidget(self)

        self.title_label = MyLabel("Forget Password", 34, QFont.Weight.DemiBold, self)
        self.body_label = MyLabel("Enter a following details to create to update your password.")

        self.username_heading_label = MyLabel("Username", weight=QFont.Weight.DemiBold)
        self.username_line_edit = LineEdit()
        self.username_line_edit.setMaxLength(20)
        self.username_line_edit.setPlaceholderText("Enter your username")

        self.email_heading_label = MyLabel("Email", weight=QFont.Weight.DemiBold)
        self.email_line_edit = LineEdit()
        self.email_line_edit.setPlaceholderText("Enter your email")

        self.password_heading_label = MyLabel("New Password", weight=QFont.Weight.DemiBold)
        self.password_line_edit = PasswordLineEdit()
        self.password_line_edit.setMaxLength(16)
        self.password_line_edit.setPlaceholderText("Enter your new password")

        self.confirm_password_heading_label = MyLabel("Confirm password", weight=QFont.Weight.DemiBold)
        self.confirm_password_line_edit = PasswordLineEdit()
        self.confirm_password_line_edit.setPlaceholderText("Re-enter your password")

        self.update_password = PrimaryPushButton("Update Password", parent=self)
        self.update_password.setCursor(Qt.CursorShape.PointingHandCursor)

        self.signup_text = "Don't hava a account?"
        self.signup_button = TransparentPushButton("Sign up", parent=self)
        self.signup_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self._init_ui()
        self._signal_handler()

    def _init_ui(self):
        h_layout = QHBoxLayout(self)
        # h_layout.setSpacing(70)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(self.image_label)

        v_layout = QVBoxLayout(self.login_container)
        v_layout.setContentsMargins(70, 0, 70, 0)
        v_layout.setSpacing(0)
        # v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.addStretch()

        h2_sublayout = QHBoxLayout(self)
        text_label = MyLabel(self.signup_text)
        h2_sublayout.addStretch()
        h2_sublayout.addWidget(text_label)
        h2_sublayout.addWidget(self.signup_button)
        h2_sublayout.addStretch()

        v_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.body_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        v_layout.addSpacing(40)
        v_layout.addWidget(self.username_heading_label)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.username_line_edit)
        v_layout.addSpacing(20)
        v_layout.addWidget(self.email_heading_label)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.email_line_edit)
        v_layout.addSpacing(30)
        v_layout.addWidget(self.password_heading_label)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.password_line_edit)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.confirm_password_heading_label)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.confirm_password_line_edit)
        v_layout.addSpacing(30)
        v_layout.addWidget(self.update_password)
        v_layout.addSpacing(10)
        v_layout.addLayout(h2_sublayout)
        v_layout.addStretch()

        h_layout.addWidget(self.image_label, stretch=1)
        h_layout.addWidget(self.login_container)

    def _signal_handler(self):
        self.signup_button.clicked.connect(self.signUpSignal.emit)
        self.update_password.clicked.connect(self._verify)

    def _verify(self):
        username = self.getUsername().strip()
        email = self.getEmail().strip()
        password = self.getPassword().strip()
        confirm = self.getConfirmPassword().strip()

        errors = [
            (not username, "Invalid Username", "Username is required."),
            (not USERNAME_REGEX.match(username), "Invalid Username",
             "Username must be 3–20 characters (letters, numbers, underscores only)."),
            (not email, "Invalid Email", "Email is required."),
            (not EMAIL_REGEX.match(email), "Invalid Email", "Please enter a valid email address."),
            (not password, "Invalid Password", "Password is required."),
            (len(password) < 8, "Invalid Password", "Password must be at least 8 characters."),
            (not PASSWORD_REGEX.match(password), "Invalid Password",
             "Password must include uppercase, lowercase, digit, and special character."),
            (password != confirm, "Invalid Password", "Passwords do not match.")
        ]

        for condition, title, message in errors:
            if condition:
                self.errorSignal.emit(title, message)
                return

        self.updatePasswordSignal.emit()

    def getPassword(self)->str:
        return self.password_line_edit.text()

    def getConfirmPassword(self)->str:
        return self.confirm_password_line_edit.text()

    def getUsername(self)->str:
        return self.username_line_edit.text()

    def getEmail(self)->str:
        return self.email_line_edit.text()

    def isRemembered(self)->bool:
        return self.remember_me_checkbox.isChecked()

    def clear(self):
        self.password_line_edit.clear()
        self.username_line_edit.clear()
        self.email_line_edit.clear()
        self.confirm_password_line_edit.clear()


class LoginWindow(FramelessWindow):
    def __init__(self, login_image_path: str, register_image_path: str, forget_image_path: str,
                 session_maker: sessionmaker = None, parent=None) -> None:
        super().__init__(parent)
        self.setTitleBar(FluentTitleBar(self))

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.stackedWidget = PopUpAniStackedWidget(self)
        self.stackedWidget.lower()
        vlayout.addWidget(self.stackedWidget)

        self.login_page = LoginPage(login_image_path, self)
        self.register_page = RegisterPage(register_image_path, self)
        self.forget_password_page = ForgotPasswordPage(forget_image_path, self)

        self.stackedWidget.addWidget(self.login_page)
        self.stackedWidget.addWidget(self.register_page)
        self.stackedWidget.addWidget(self.forget_password_page)

        self._signal_handler()
        # QColor(242, 242, 242), QColor("#1b1919")
        self.setStyleSheet(
            "background-color:rgb(242, 242, 242);" if not isDarkTheme() else "background-color: #1b1919;")

    def _signal_handler(self):
        self.forget_password_page.updatePasswordSignal.connect(self.update_password)
        self.forget_password_page.signUpSignal.connect(lambda: self.switchTo(1))

        self.register_page.signInSignal.connect(lambda: self.switchTo(0))

        self.login_page.signUpSignal.connect(lambda: self.switchTo(1))
        self.login_page.forgetPasswordSignal.connect(lambda: self.switchTo(2))

        # error
        self.forget_password_page.errorSignal.connect(self.showMessage)
        self.login_page.errorSignal.connect(self.showMessage)
        self.register_page.errorSignal.connect(self.showMessage)

    def update_password(self):
        pass

    def create_account(self):
        pass

    def login_to_account(self):
        pass

    def switchTo(self, index: int):
        self.login_page.clear()
        self.register_page.clear()
        self.forget_password_page.clear()
        self.stackedWidget.setCurrentIndex(index)

    def showMessage(self, title: str, content: str):
        message_box = MessageBox(title, content, self)
        message_box.exec()


if __name__ == '__main__':
    setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    login = r"D:\Program\Zerokku\assets\login.png"
    register = r"D:\Program\Zerokku\assets\register.png"
    forget = r"D:\Program\Zerokku\assets\forget.png"
    login_page = LoginWindow(login, register, forget)
    login_page.showMaximized()
    app.exec()