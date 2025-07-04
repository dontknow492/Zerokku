from typing import List, Union

import sys
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QPixmap, QImage

from PySide6.QtWidgets import QWidget, QApplication, QHBoxLayout, QVBoxLayout, QPushButton
from loguru import logger

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
        self.title_label = MultiLineElideLabel("Hero Banner Title", 4, 43, QFont.Weight.Bold, parent=self)
        self.title_label.setWordWrap(True)
        self.title_label.setContentsMargins(0, 0, 0, 0)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.description_label = MultiLineElideLabel("This is Description", 6, 16, QFont.Weight.DemiBold, parent=self)
        # self.overview_label.max_lines = 4
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
        self.pips_pager.setCursor(Qt.CursorShape.PointingHandCursor)

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
            self._pages = page_index
        page = self._hero_banners[page_index]
        page.stop()
        page.setTitle(title)
        page.setDescription(description)
        page.setGenres(genres, color)
        if isinstance(banner_image, str):
            banner_image = QPixmap(banner_image)
        banner_image = banner_image.scaled(self._banner_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        banner_image = banner_image.copy(0, 0, self._banner_size.width(), self._banner_size.height())
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

        self.next_button.setEnabled(True)
        self.previous_button.setEnabled(True)

        if index >= self._pages-1:
            self.next_button.setEnabled(False)
        elif index <= 0:
            self.previous_button.setEnabled(False)


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
        self.pips_pager.move((self.width() - self.pips_pager.width())//2, 10)

        height = (self.height() - self.next_button.height())//2
        self.previous_button.move(0, height)
        self.next_button.move(self.width() - self.next_button.width(), height)


if __name__ == '__main__':
    # setTheme(Theme.DARK)
    # app = QApplication(sys.argv)
    # size = QSize(1460, 600)
    # screen_geometry = QApplication.primaryScreen().availableGeometry()
    banner_size = QSize(1460, 600)
    print((banner_size.width()-300)/banner_size.height())
    titles = ["One Piece", "Berserker", "Lord of Mysteries", "Takopi's Original Sin", "The Greatest Estate Developer",
              "I need GirlFriend"]
    images = [r"D:\Program\Zerokku\demo\banners\banner.jpg", r"D:\Program\Zerokku\demo\banners\banner-1.jpg",
              r"D:\Program\Zerokku\demo\banners\banner-3.jpg"
        , r"D:\Program\Zerokku\demo\banners\banner-4.jpg", r"D:\Program\Zerokku\demo\banners\banner-5.jpg",
              r"D:\Program\Zerokku\demo\poster.jpg"]
    # images = r"D:\Program\Zerokku\demo\poster.jpg"
    descriptions = [
        "In a Victorian world of steam, dreadnoughts, and occult horrors, Zhou Mingrui awakens as Klein Moretti."
        " He walks a razor’s edge between light and darkness, entangled with warring Churches. This is the legend"
        " of unlimited potential…and unspeakable danger.\n<br><br>\n(Source: Crunchyroll)",
        "The second season of <i>Kusuriya no Hitorigoto</i>.<br><br>\n\nMaomao and Jinshi face palace intrigue as "
        "a pregnant concubine's safety and a looming conspiracy collide.<br><br>\n\n(Source: Crunchyroll News)",
        "A Happy alien, Takopi, lands on Earth with one mission: to spread happiness! When he meets Shizuka, a lonely"
        " fourth grader, he vows to bring back her smile using his magical Happy Gadgets. But as he uncovers the pain"
        " in her life, Takopi learns that true happiness may require more than gadgets.\n<br><br>\n(Source: Crunchyroll)",
        "Gold Roger was known as the Pirate King, the strongest and most infamous being to have sailed the Grand Line."
        " The capture and death of Roger by the World Government brought a change throughout the world. His last words"
        " before his death revealed the location of the greatest treasure in the world, One Piece. It was this "
        "revelation that brought about the Grand Age of Pirates, men who dreamed of finding One Piece (which promises an"
        " unlimited amount of riches and fame), and quite possibly the most coveted of titles for the person who found "
        "it, the title of the Pirate King.<br><br>\nEnter Monkey D. Luffy, a 17-year-old boy that defies your standard "
        "definition of a pirate. Rather than the popular persona of a wicked, hardened, toothless pirate who ransacks"
        " villages for fun, Luffy’s reason for being a pirate is one of pure wonder; the thought of an exciting "
        "adventure and meeting new and intriguing people, along with finding One Piece, are his reasons of becoming "
        "a pirate. Following in the footsteps of his childhood hero, Luffy and his crew travel across the Grand Line, "
        "experiencing crazy adventures, unveiling dark mysteries and battling strong enemies, all in order to reach "
        "One Piece.<br><br>\n<b>*This includes following special episodes:</b><br>\n- Chopperman to the Rescue! Protect the TV Station by the Shore! (Episode 336)<br>\n- The Strongest Tag-Team! Luffy and Toriko's Hard Struggle! (Episode 492)<br>\n- Team Formation! Save Chopper (Episode 542)<br>\n- History's Strongest Collaboration vs. Glutton of the Sea (Episode 590)<br>\n- 20th Anniversary! Special Romance Dawn (Episode 907)",
        "When civil engineering student Su-Ho Kim falls asleep reading a fantasy novel, he wakes up as a character in "
        "the book! Su-Ho is now in the body of Lloyd Frontera, a lazy noble who loves to drink, and whose family is in "
        "a mountain of debt. Using his engineering knowledge, Su-Ho designs inventions to avert the terrible future that"
        " lies in wait for him. With the help of a giant hamster, a knight, and the world’s magic, can Su-Ho dig his new"
        " family out of debt and build a better future?\n<br><br>(Source: WEBTOONS, edited)",
        "Curently no descriptions"
    ]
    genres = ["romance", "slice of life", "comedy"]
    colors = ["#e49335", "#aed6e4", "#e4bb50", "#f15d78", "#e4c95d", "#f15d78"]
    pages = 6
    # window = HeroContainer(pages, banner_size)
    ratio = banner_size.width()/banner_size.height()
    for i, title, color, image, description in zip(range(pages), titles, colors, images, descriptions):
        img = detect_faces_and_draw_boxes(image)
        img.show()

        # img = detect_faces_and_crop(image, ratio)
        # img.show()
        # paged_image = add_padding(img, 300, 0, 0, 0 , (0,0,0,0))
        # grad_image = apply_left_gradient(paged_image, 300, 500, (200, 0, 0, 255), (255, 0, 0, 0))
        # grad_image.show()
        # qimage = ImageQt.ImageQt(grad_image)
        # break
        # print(i, title, genres, color, image, description)
        # window.set_info(i, title, description, genres, QColor(color), qimage)
    # window.setTitle(title)
    # window.setDescription(description)
    # window.setGenres(genres, color)
    # window.setBannerImage(image)
    # window.start()
    # window.show()
    # app.exec()