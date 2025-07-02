import sys
from PySide6.QtCore import Qt

from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout
from qfluentwidgets import SegmentedWidget, FluentIcon

from AnillistPython import MediaType
from gui.common import AniStackedWidget, KineticScrollArea


class DownloadInterface(QWidget):
    def __init__(self, parent=None, media_type=None):
        super().__init__(parent)

        self.view_stack = AniStackedWidget(self)
        self.anime_downloads_view = KineticScrollArea(self)
        self.anime_downloads_view.setStyleSheet("background: transparent;")
        self.manga_downloads_view = KineticScrollArea(self)
        self.manga_downloads_view.setStyleSheet("background: transparent;")

        self.view_stack.addWidget(self.anime_downloads_view)
        self.view_stack.addWidget(self.manga_downloads_view)

        self.type_segment = SegmentedWidget(self)
        self.type_segment.addItem("anime", "Anime", lambda: self.view_stack.setCurrentIndex(0), FluentIcon.MOVIE)
        self.type_segment.addItem("manga", "Manga", lambda: self.view_stack.setCurrentIndex(1), FluentIcon.ALBUM)

        if media_type == MediaType.ANIME:
            self.type_segment.setCurrentItem("anime")
        elif media_type == MediaType.MANGA:
            self.type_segment.setCurrentItem("manga")


        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.type_segment, alignment=Qt.AlignmentFlag.AlignLeft)
        self.mainLayout.addWidget(self.view_stack, stretch=1)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DownloadInterface()
    window.show()
    app.exec()