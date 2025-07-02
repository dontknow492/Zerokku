import asyncio

from PySide6.QtCore import QRect
from PySide6.QtGui import QIcon, QColor
from loguru import logger
from qfluentwidgets import FluentWindow, FluentIcon, setTheme, Theme, ScrollArea, FluentStyleSheet, qconfig, \
    MSFluentWindow, NavigationItemPosition, NavigationAvatarWidget, setThemeColor
from PySide6.QtWidgets import QApplication, QWidget, QFrame, QScrollArea, QVBoxLayout, QHBoxLayout
import sys
from qasync import QEventLoop
from qfluentwidgets.window.stacked_widget import StackedWidget

from AnillistPython import MediaType
from gui.common import KineticScrollArea
from gui.interface import HomeInterface, SearchInterface, LibraryInterface, DownloadInterface


class MyFluentWindow(FluentWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.hBoxLayout.removeItem(self.widgetLayout)
        self.hBoxLayout.addSpacing(-50)
        self.hBoxLayout.addLayout(self.widgetLayout)

        # self._isMicaEnabled = False
        # self._lightBackgroundColor = QColor(240, 244, 249)
        # self._darkBackgroundColor = QColor(32, 32, 32)
        # # super().__init__(parent=parent)
        #

        # FluentStyleSheet.FLUENT_WINDOW.apply(self.stackedWidget)
        #
        # # enable mica effect on win11
        # self.setMicaEffectEnabled(True)
        #
        # # show system title bar buttons on macOS
        # if sys.platform == "darwin":
        #     self.setSystemTitleBarButtonVisible(True)
        #
        # qconfig.themeChangedFinished.connect(self._onThemeChangedFinished)


class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()

        # self.navigationInterface.setCollapsible(False)

        # self.stackedWidget.setParent(None)
        # self.layout().addSpacing(-50)
        # self.layout().addWidget(self.stackedWidget)


        self.tags_path = "assets//tags.json"
        self._screen_geometry = QApplication.primaryScreen().availableGeometry()

        self.setWindowTitle('Zerokku')
        self.setWindowIcon(QIcon('app.ico'))

        # self.navigationInterface.displayModeChanged.disconnect()


        self._available_geometry = QRect(self._screen_geometry.x(), self._screen_geometry.y(),
                                         self._screen_geometry.width() - 60-14, self._screen_geometry.height())

        self.anime_home_interface = HomeInterface(self._available_geometry, MediaType.ANIME)
        # self.anime_home_interface.setAutoFillBackground(False)
        self.anime_home_interface.setObjectName("Anime Home Interface")
        self.manga_home_interface = HomeInterface(self._available_geometry, MediaType.MANGA)
        self.manga_home_interface.setObjectName("Manga Home Interface")
        self.search_interface = SearchInterface(self.tags_path)
        self.search_interface.setObjectName("Search Interface")

        self.library_interface = LibraryInterface(self)
        self.library_interface.setObjectName("Library Interface")

        self.download_interface = DownloadInterface(self)
        self.download_interface.setObjectName("Download Interface")

        #
        self.setting_interface = QWidget()
        self.setting_interface.setObjectName("Settings Interface")

        self._init_interface()

    def _init_interface(self):
        self.addSubInterface(self.anime_home_interface, FluentIcon.MOVIE, "Anime", isTransparent=False)
        self.addSubInterface(self.manga_home_interface, FluentIcon.ALBUM, "Manga", isTransparent=False)
        self.addSubInterface(self.search_interface, FluentIcon.SEARCH, "Search", isTransparent=False)
        self.addSubInterface(self.library_interface, FluentIcon.LIBRARY, "Library", isTransparent=False)

        #bottom
        self.addSubInterface(self.download_interface, FluentIcon.DOWNLOAD, "Download",
                             position = NavigationItemPosition.BOTTOM, isTransparent=False)
        self.addSubInterface(self.setting_interface, FluentIcon.SETTING, "Settings",
                             position=NavigationItemPosition.BOTTOM, isTransparent=False)

        self.navigationInterface.addWidget("user", NavigationAvatarWidget("User"),
                            lambda: print("avatar"), NavigationItemPosition.BOTTOM )


if __name__ == '__main__':
    setTheme(Theme.DARK)
    setThemeColor(QColor("#db2d69"))
    app = QApplication(sys.argv)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    main_window = MainWindow()
    main_window.setMicaEffectEnabled(False)
    main_window.setBackgroundColor(QColor("#1b1919"))
    main_window.show()

    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())