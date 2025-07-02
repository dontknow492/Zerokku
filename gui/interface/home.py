import asyncio
from enum import Enum, auto
from typing import List, Union

import sys
from PySide6.QtCore import QSize, Qt, QTimer, Signal, QRect
from PySide6.QtGui import QColor, QPixmap, QCloseEvent
from PySide6.QtWidgets import QWidget, QFrame, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from loguru import logger
from qasync import QEventLoop, asyncSlot, asyncClose
from qfluentwidgets import Theme, setTheme

from AnillistPython import AnilistMedia, parse_searched_media, MediaType
from core import ImageDownloader
from gui.common import KineticScrollArea, MyLabel
from utils import apply_gradient_overlay_pixmap, create_left_gradient_pixmap, add_margins_pixmap, create_gradient_pixmap
from gui.components import MediaCard, MediaVariants, \
    MediaCardSkeletonLandscape, ViewMoreContainer, LandscapeContainer, HeroContainer
from utils import apply_gradient_overlay_pixmap, create_left_gradient_pixmap, add_margins_pixmap


class HomeContainers(Enum):
    TRENDING = auto()  # Update every 1–3 hours (depending on traffic/activity)
    TOP100 = auto()  # Update daily or weekly
    CONTINUE_WATCHING = auto()  # Real-time or every time the user returns
    LATEST_ADDED = auto()  # Update every 15–30 minutes


class HomeInterface(KineticScrollArea):
    CONTAINER_MIN_HEIGHT = 380
    downloaderInitialized = Signal()
    def __init__(self, screen_geometry:QRect, type: MediaType, parent: QWidget = None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self.setStyleSheet("""
            KineticScrollArea, KineticScrollArea QWidget {
                background-color: transparent;
                
            }
        """)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.verticalScrollBar().style().drawPrimitive(QStyle.)

        self._screen_geometry = screen_geometry
        # self.setFixedSize(self._screen_geometry.size())
        self._banner_size = QSize(self._screen_geometry.width(), int(self._screen_geometry.height() * 0.9))

        self.image_downloader: ImageDownloader = None

        central_widget = QWidget(self)
        self.setWidget(central_widget)
        self.setWidgetResizable(True)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(20)

        self.hero_container = HeroContainer(5, self._banner_size, self)
        # self.hero_container.setStyleSheet("background-color: red;")
        self.hero_container.start()
        # self.hero_container.setFixedHeight(int(self._screen_geometry.height() * 0.6))
        continue_str = f"Continue {"watching" if type == MediaType.ANIME else "reading"}"
        self.continue_container = ViewMoreContainer(continue_str, parent)
        self.continue_container.setMinimumHeight(self.CONTAINER_MIN_HEIGHT)
        self.latest_added_container = ViewMoreContainer("Latest added", parent)
        self.latest_added_container.setMinimumHeight(self.CONTAINER_MIN_HEIGHT)
        self.trending_container = ViewMoreContainer("Trending", parent)
        self.trending_container.setMinimumHeight(self.CONTAINER_MIN_HEIGHT)

        self.top_hundred_container = LandscapeContainer(parent=self)

        self.main_layout.addWidget(self.hero_container)
        self.main_layout.addSpacing(-130)
        self.main_layout.addWidget(self.continue_container)
        # self.main_layout.addWidget(self.recently_updated_container)
        self.main_layout.addWidget(self.latest_added_container)
        self.main_layout.addWidget(self.trending_container)
        top_label = MyLabel("Top 100", 20, parent=self)
        top_label.setContentsMargins(18, 0, 0, 0)
        self.main_layout.addWidget(top_label)
        self.main_layout.addWidget(self.top_hundred_container)

        asyncio.ensure_future(self._post_init())
        self._signal_handler()

    asyncSlot()
    async def _post_init(self):
        self.image_downloader = ImageDownloader()
        self.image_downloader.imageDownloaded.connect(self.continue_container.on_download_finished)
        self.image_downloader.imageDownloaded.connect(self.trending_container.on_download_finished)
        self.image_downloader.imageDownloaded.connect(self.latest_added_container.on_download_finished)
        self.image_downloader.imageDownloaded.connect(self.top_hundred_container.on_download_finished)
        self.downloaderInitialized.emit()

    def _signal_handler(self):
        self.continue_container.requestCover.connect(self._on_cover_download_request)
        self.latest_added_container.requestCover.connect(self._on_cover_download_request)
        self.trending_container.requestCover.connect(self._on_cover_download_request)
        self.top_hundred_container.requestCover.connect(self._on_cover_download_request)


    @asyncSlot(str)
    async def _on_cover_download_request(self, url: str):
        # logger.debug(f"Downloading {url}")
        await self.image_downloader.fetch(url, True)

    def update_screen_geometry(self, geometry: QRect):
        self._screen_geometry = geometry
        self.setFixedWidth(self._screen_geometry.width())

    def add_continue_watching_medias(self, data: List[AnilistMedia]):
        self.continue_container.add_medias(data)

    def add_trending_medias(self, data: List[AnilistMedia]):
        self.trending_container.add_medias(data)

    def add_top_hundred_medias(self, data: List[AnilistMedia]):
        self.top_hundred_container.add_medias(data)

    def add_latest_added_medias(self, data: List[AnilistMedia]):
        self.latest_added_container.add_medias(data)

    def add_hero_banner(self, page_index: int, title: str, description: str,
                        genres: List[str], color: QColor, banner_image: str):
        if isinstance(banner_image, str):
            image = QPixmap(banner_image)
        if image is not None:
            image = image.scaled(self._banner_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                 Qt.SmoothTransformation)
            x = image.rect().center().x()
            x = x - self._banner_size.width() // 2
            image = image.copy(x, 0, self._banner_size.width(), self._banner_size.height())
            gradient_image = create_gradient_pixmap(image, color, self._banner_size.width() // 3 + 200,
                                                    self._banner_size.width() // 3)

        self.hero_container.set_info(page_index, title, description, genres, color, gradient_image)

    @asyncClose
    async def closeEvent(self, event: QCloseEvent):
        if isinstance(self.image_downloader, ImageDownloader):
            await self.image_downloader.close()


def main():
    import json
    with open(r"D:\Program\Zerokku\samples\data\home.json", "r", encoding="utf-8") as f:
        home = json.load(f)
    with open(r"D:\Program\Zerokku\demo\data.json", "r", encoding="utf-8") as data:
        result = json.load(data)
    # cards = parse_searched_media(result, None)

    latest = parse_searched_media(home["latest"]["data"], None)
    trending = parse_searched_media(home["trending"]["data"], None)
    top = parse_searched_media(result, None)
    #

    # cards.extend(cards)
    # cards.extend(cards)
    # print(len(cards))

    titles = ["One Piece", "Berserker", "Lord of Mysteries", "Takopi's Original Sin", "The Greatest Estate Developer"]
    images = [r"D:\Program\Zerokku\demo\banners\banner.jpg", r"D:\Program\Zerokku\demo\banners\banner-1.jpg",
            r"D:\Program\Zerokku\demo\banners\banner-3.jpg"
        , r"D:\Program\Zerokku\demo\banners\banner-4.jpg", r"D:\Program\Zerokku\demo\banners\banner-5.jpg"]
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
        " family out of debt and build a better future?\n<br><br>(Source: WEBTOONS, edited)"
    ]
    genres = ["romance", "slice of life", "comedy"]
    colors = ["#e49335", "#aed6e4", "#e4bb50", "#f15d78", "#e4c95d"]

    app = QApplication(sys.argv)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    # main_window = ViewMoreContainer("Trending")
    # main_window = LandscapeContainer()
    # main_window = PortraitContainer()
    # main_window = WideLandscapeContainer()
    main_window = HomeInterface()
    main_window.show()


    def add_data():
        for index, (title, description, color, image) in enumerate(zip(titles, descriptions, colors, images)):
            color = QColor(color)
            main_window.add_hero_banner(index, title, description, genres, color, image)
        main_window.add_continue_watching_medias(latest)
        main_window.add_trending_medias(trending)
        main_window.add_latest_added_medias(latest)
        main_window.add_top_hundred_medias(top[:10])

    main_window.downloaderInitialized.connect(lambda: QTimer.singleShot(1000, add_data))

    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())





if __name__ == '__main__':
    # setTheme(Theme.DARK)
    main()
