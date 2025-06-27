import asyncio
from PySide6.QtGui import QIcon
from qfluentwidgets import FluentWindow, FluentIcon, setTheme, Theme, ScrollArea
from PySide6.QtWidgets import QApplication, QWidget, QFrame, QScrollArea
import sys
from qasync import QEventLoop

from gui.common import KineticScrollArea
from gui.interface import HomeInterface


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Zerokku')
        self.setWindowIcon(QIcon('app.ico'))

        self.anime_home_interface = HomeInterface()
        # self.anime_home_interface.setAutoFillBackground(False)
        self.anime_home_interface.setObjectName("Anime Home Interface")

        self.addSubInterface(self.anime_home_interface, FluentIcon.MOVIE, "Anime", isTransparent=True)

if __name__ == '__main__':
    # setTheme(Theme.DARK)
    app = QApplication(sys.argv)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    main_window = MainWindow()
    main_window.show()

    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())