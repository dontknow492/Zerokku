import asyncio

from PySide6.QtGui import QIcon
from qfluentwidgets import FluentWindow
from PySide6.QtWidgets import QApplication
import sys
from qasync import QEventLoop

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Zerokku')
        self.setWindowIcon(QIcon('app.ico'))







if __name__ == '__main__':
    if __name__ == "__main__":
        app = QApplication(sys.argv)

        event_loop = QEventLoop(app)
        asyncio.set_event_loop(event_loop)

        app_close_event = asyncio.Event()
        app.aboutToQuit.connect(app_close_event.set)

        main_window = MainWindow()
        main_window.show()

        with event_loop:
            event_loop.run_until_complete(app_close_event.wait())