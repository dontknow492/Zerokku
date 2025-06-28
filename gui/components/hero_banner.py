from typing import List, Union

import sys
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QPixmap, QImage

from PySide6.QtWidgets import QWidget, QApplication, QHBoxLayout, QVBoxLayout, QPushButton

from qfluentwidgets import PipsPager, FlowLayout, PushButton, ImageLabel, setTheme, Theme, FluentIcon

from gui.components import HeroContainerSkeleton
from gui.common import AniStackedWidget, MyLabel, MultiLineElideLabel, OutlinedChip, RoundedToolButton, Chip
from utils import apply_gradient_overlay_pixmap, create_left_gradient_pixmap, add_margins_pixmap


class HeroBanner(QWidget):
    def __init__(self, size: QSize, parent: QWidget = None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self._size = size
        self.banner_label = ImageLabel(self)
        self.banner_label.setFixedSize(size)


        self.skeleton = HeroContainerSkeleton(parent=self)

        self.container = QWidget(self)
        self.container.setFixedWidth(size.width()//3)
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(16)
        container_layout.setContentsMargins(36, 16, 16, 16)
        self.title_label = MyLabel("Hero Banner Title", 43, QFont.Weight.Bold, parent=self)
        self.title_label.setWordWrap(True)
        self.title_label.setContentsMargins(0, 0, 0, 0)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.description_label = MultiLineElideLabel("This is Description", 4, 16, QFont.Weight.DemiBold, parent=self)
        # self.description_label.max_lines = 4
        self.genre_layout = FlowLayout()
        self.learn_more_button = PushButton(FluentIcon.VIEW, " Learn more", parent=self)
        self.learn_more_button.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.learn_more_button.setIconSize(QSize(22, 22))
        self.save_button = PushButton(FluentIcon.FOLDER_ADD, " Add to Watchlist", parent=self)
        self.save_button.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.save_button.setIconSize(QSize(22, 22))
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.learn_more_button)
        hbox_layout.addWidget(self.save_button)
        hbox_layout.addStretch()

        container_layout.addStretch(3)
        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.description_label)
        container_layout.addLayout(self.genre_layout)
        container_layout.addLayout(hbox_layout)

        container_layout.addStretch(3)



        # self.container.raise_()
        # self.container.raise_()

        self.container.setFixedHeight(self._size.height())

        self.container.move(0, self._size.height() - self.container.height())


    def _create_genres(self, genres: List[str], color: QColor):
        for genre in genres:
            # genre = Chip(genre.title(), None, color, color.lighter(100), QColor("gray"), parent=self)
            # color.setRgb(100, 100, 100)
            genre = OutlinedChip(genre.title(), None, color, parent=self)
            self.genre_layout.addWidget(genre)

    def setDescription(self, description: str):
        self.description_label.setText(description)

    def setGenres(self, genres: List[str], color: QColor):
        self._create_genres(genres, color)

    def setTitle(self, title: str):
        self.title_label.setText(title.upper())

    def setBannerImage(self, image: Union[QPixmap, str, QImage]):
        if isinstance(image, str):
            image = QPixmap(image)
        # image = image.scaled(self._size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        # x = image.rect().center().x()
        # x = x - self._size.width()//2
        # image = image.copy(x, 0, self._size.width(), self._size.height())
        self.banner_label.setImage(image)
        self.banner_label.setScaledSize(self._size)

    def resizeEvent(self, event):
        self.skeleton.setFixedSize(self.size())

        # self.container.

    def start(self):
        self.container.setVisible(False)

        self.skeleton.start()

    def stop(self):
        self.skeleton.stop()
        self.container.setVisible(True)

class HeroContainer(AniStackedWidget):
    def __init__(self, pages: int, banner_size: QSize, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)

        self._pages = pages
        self._banner_size = banner_size
        self._hero_banners: List[HeroBanner] = list()
        self.pips_pager = PipsPager(self)

        self.pips_pager.setPageNumber(pages)

        button_size = QSize(48, 48)
        icon_size = QSize(20, 20)
        button_radius = button_size.width() // 2
        self.next_button = self._create_button(FluentIcon.RIGHT_ARROW, button_size, icon_size,
                                               Qt.CursorShape.PointingHandCursor, "Next")

        # self.next_button.setEnabled(False)
        self.previous_button = self._create_button(FluentIcon.LEFT_ARROW, button_size, icon_size,
                                                   Qt.CursorShape.PointingHandCursor, "Previous")

        self.previous_button.setEnabled(False)

        for page in range(pages):
            banner = HeroBanner(self._banner_size, parent=self)
            banner.start()
            self._hero_banners.append(banner)
            self.addWidget(banner)

        self.pips_pager.raise_()
        # self.pips_pager.raise_()
        self.next_button.raise_()
        self.previous_button.raise_()

        self.setFixedSize(banner_size)
        self._signal_handler()

    def _create_button(self, icon, button_size, icon_size, cursor, tooltip):
        button = RoundedToolButton(icon, self)
        button.setFixedSize(button_size)
        button.setRadius(button_size.width() // 2)
        button.setCursor(cursor)
        button.setIconSize(icon_size)
        button.setToolTip(tooltip)

        return button

    def _signal_handler(self):
        self.pips_pager.currentIndexChanged.connect(self.switchPage)
        self.previous_button.clicked.connect(self._on_previous)
        self.next_button.clicked.connect(self._on_next)


    def set_info(self, page_index: int, title: str, description: str, genres: List[str],
                 color: QColor, banner_image: Union[str, QPixmap, QImage]):
        if page_index >= self._pages:
            raise IndexError("Page index out of range")
        page = self._hero_banners[page_index]
        page.stop()
        page.setTitle(title)
        page.setDescription(description)
        page.setGenres(genres, color)
        page.setBannerImage(banner_image)

    def _on_next(self):
        page = self.currentIndex()
        next_page = min(page + 1, self._pages)
        self.switchPage(next_page)

    def _on_previous(self):
        page = self.currentIndex()
        prev_page = max(page - 1, 0)
        self.switchPage(prev_page)



    def switchPage(self, index: int):
        if self.currentIndex() == index:
            return
        if index >= self._pages-1:
            self.next_button.setEnabled(False)
        elif index <= 0:
            self.previous_button.setEnabled(False)
        else:
            self.next_button.setEnabled(True)
            self.previous_button.setEnabled(True)

        self.setCurrentIndex(index, self._banner_size.width()//2, distance=self._banner_size.width()//2)
        if self.pips_pager.currentIndex() != index:
            self.pips_pager.setCurrentIndex(index)
        self.pips_pager.raise_()
        # self.pips_pager.raise_()
        self.next_button.raise_()
        self.previous_button.raise_()

    def start(self):
        current_widget = self.currentWidget()
        if current_widget:
            current_widget.start()

    def stop(self):
        current_widget = self.currentWidget()
        if current_widget:
            current_widget.stop()

    def resizeEvent(self, event):
        self.pips_pager.adjustSize()
        self.pips_pager.move((self.width() - self.pips_pager.width())//2, self.height() - self.pips_pager.height())

        height = (self.height() - self.next_button.height())//2
        self.previous_button.move(0, height)
        self.next_button.move(self.width() - self.next_button.width(), height)


if __name__ == '__main__':
    setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    size = QSize(1460, 600)
    screen_geometry = QApplication.primaryScreen().availableGeometry()
    banner_size = QSize(screen_geometry.width(), int(screen_geometry.height() * 0.8))
    title = "Demon Slayer\nKimetsu No Yaiba"
    image = r"D:\Program\Zerokku\demo\hero.png"
    description = ("It is the Taisho Period in Japan. Tanjiro, a kindhearted boy who sells charcoal for a living,"
                   " finds his family slaughter by a demon. To make matters worse, his younger sister Nezuko,"
                   " the sole survivor, has been ")
    genres = ["action", "adventure", "fantasy"]
    color = QColor("#e46b5d")
    pages = 5
    window = HeroContainer(pages, banner_size)
    for i in range(pages):
        window.set_info(i, title, description, genres, color, image)
    # window.setTitle(title)
    # window.setDescription(description)
    # window.setGenres(genres, color)
    # window.setBannerImage(image)
    # window.start()
    window.show()
    app.exec()