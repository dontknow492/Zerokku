import asyncio
from typing import Optional, Union

from PySide6 import QtGui
from PySide6.QtCore import QRect, QTimer, QSize, Qt
from PySide6.QtGui import QIcon, QColor
from loguru import logger
from qfluentwidgets import FluentWindow, FluentIcon, setTheme, Theme, ScrollArea, FluentStyleSheet, qconfig, \
    MSFluentWindow, NavigationItemPosition, NavigationAvatarWidget, setThemeColor, SplashScreen
from PySide6.QtWidgets import QApplication, QWidget, QFrame, QScrollArea, QVBoxLayout, QHBoxLayout
import sys
from qasync import QEventLoop, asyncSlot

from AnillistPython import MediaType, MediaQueryBuilderBase, SearchQueryBuilder, MediaSeason, MediaSort, \
    MediaQueryBuilder, AnilistMedia
from database import Anime, Manga, AsyncMediaRepository, AsyncLibraryRepository
from gui.common import KineticScrollArea
from gui.interface import HomeInterface, SearchInterface, LibraryInterface, DownloadInterface, MediaPage, LoginInterface

from core import AnilistHelper
from utils import get_current_season_and_year

from sqlalchemy.orm import sessionmaker

class MainWindow(MSFluentWindow):
    DATABASE_URL = ""
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Zerokku')
        self.setWindowIcon(QIcon('app.ico'))

        self._screen_geometry = QApplication.primaryScreen().availableGeometry()

        self.splashScreen = SplashScreen("splash.png", self)
        self.splashScreen.setIconSize(QSize(self._screen_geometry.height() - 100 , self._screen_geometry.height() - 100))
        # self.splashScreen.setWindowIconText(self.windowIconText())
        self.splashScreen.showFullScreen()


        self.cache_dir = r"./.cache"

        # self.session_maker = sessionmaker()
        #
        # self.db_media_helper = AsyncMediaRepository(self.session_maker)
        # self.db_library_helper = AsyncLibraryRepository(self.session_maker, self.db_media_helper, )
        self.anilist_helper = AnilistHelper(cache_dir=self.cache_dir)

        self.tags_path = "assets//tags.json"



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

        # self.library_interface = LibraryInterface(self)
        # self.library_interface.setObjectName("Library Interface")

        self.download_interface = DownloadInterface(self)
        self.download_interface.setObjectName("Download Interface")

        #
        self.setting_interface = QWidget()
        self.setting_interface.setObjectName("Settings Interface")


        #
        self.page_interface = MediaPage(self._available_geometry, MediaType.ANIME, parent = self)

        self._init_interface()

        asyncio.ensure_future(self._post_init())



    def _init_interface(self):
        self.addSubInterface(self.anime_home_interface, FluentIcon.MOVIE, "Anime", isTransparent=False)
        self.addSubInterface(self.manga_home_interface, FluentIcon.ALBUM, "Manga", isTransparent=False)
        self.addSubInterface(self.search_interface, FluentIcon.SEARCH, "Search", isTransparent=False)
        # self.addSubInterface(self.library_interface, FluentIcon.LIBRARY, "Library", isTransparent=False)

        #bottom
        self.addSubInterface(self.download_interface, FluentIcon.DOWNLOAD, "Download",
                             position = NavigationItemPosition.BOTTOM, isTransparent=False)
        self.addSubInterface(self.setting_interface, FluentIcon.SETTING, "Settings",
                             position=NavigationItemPosition.BOTTOM, isTransparent=False)

        self.navigationInterface.addWidget("user", NavigationAvatarWidget("User"),
                            lambda: print("avatar"), NavigationItemPosition.BOTTOM )


        #adding non navi widget
        self.stackedWidget.addWidget(self.page_interface)


    def on_card_clicked(self, media_id: int, media_data: Union[AnilistMedia, Anime, Manga]):
        logger.debug(f"Media: {media_id}, type: {type(media_data)}")
        self.switchTo(self.page_interface)

    @asyncSlot()
    async def _post_init(self):
        await self.anilist_helper.connect()
        self._signal_handler()
        await self.anime_home_interface.connect_image_downloader()
        await self.manga_home_interface.connect_image_downloader()
        await self.search_interface.init_image_downloader()

        QTimer.singleShot(10, self.splashScreen.finish)


    def _signal_handler(self):
        page = 1
        per_page = 6

        self.anime_home_interface.downloaderInitialized.connect(
            lambda: self.get_trending(MediaType.ANIME, page, per_page))
        self.anime_home_interface.downloaderInitialized.connect(
            lambda: self.get_latest(MediaType.ANIME, page, per_page))
        self.anime_home_interface.downloaderInitialized.connect(
            lambda: self.get_top_rated(MediaType.ANIME, page, per_page))
        self.anime_home_interface.downloaderInitialized.connect(
            lambda: self.get_top_medias(MediaType.ANIME, page, per_page))

        self.anime_home_interface.downloaderInitialized.connect(
            lambda: self.get_hero_media(MediaType.ANIME, 6)
        )

        # #manga home
        self.manga_home_interface.downloaderInitialized.connect(
            lambda: self.get_trending(MediaType.MANGA, page, per_page))
        self.manga_home_interface.downloaderInitialized.connect(
            lambda: self.get_latest(MediaType.MANGA, page, per_page))
        self.manga_home_interface.downloaderInitialized.connect(
            lambda: self.get_top_rated(MediaType.MANGA, page, per_page))
        self.manga_home_interface.downloaderInitialized.connect(
            lambda: self.get_top_medias(MediaType.MANGA, page, per_page))

        self.manga_home_interface.downloaderInitialized.connect(
            lambda: self.get_hero_media(MediaType.MANGA, 6)
        )

        #card clicked signal
        self.anime_home_interface.cardClicked.connect(self.on_card_clicked)
        self.manga_home_interface.cardClicked.connect(self.on_card_clicked)

        #search
        self.search_interface.searchSignal.connect(self.search)
        self.search_interface.cardClicked.connect(self.on_card_clicked)

    @asyncSlot()
    async def get_hero_media(self, media_type: MediaType, items: int = 1):
        season, year = get_current_season_and_year()
        hero_fields_builder = MediaQueryBuilder().include_title().include_description().include_genres()
        hero_fields_builder.include_images(False, False, True, True)
        hero_fields_builder.include_banner_image()
        #what item to display
        hero_search_builder = SearchQueryBuilder()
        if media_type == MediaType.ANIME:
            hero_search_builder.set_season(season, year).set_sort(MediaSort.POPULARITY_DESC)
        elif media_type == MediaType.MANGA:
            hero_search_builder.set_year_range(year).set_sort(MediaSort.POPULARITY_DESC)

        data = await self.anilist_helper.get_hero_banner(hero_fields_builder, hero_search_builder, media_type, items)
        print(data)
        if media_type == MediaType.ANIME:
            self.anime_home_interface.add_hero_banner_data(data)
        elif media_type == MediaType.MANGA:
            self.manga_home_interface.add_hero_banner_data(data)

    @asyncSlot(MediaType, int, int)
    async def get_trending(self, media_type: MediaType, page: int, per_page: int = 5):
        if media_type == MediaType.ANIME:
            builder = self.anime_home_interface.get_card_query_builder()
            data = await self.anilist_helper.get_trending(builder, MediaType.ANIME, page, per_page)
            # logger.debug(data[0])
            self.anime_home_interface.add_trending_medias(
                data
            )
        elif media_type == MediaType.MANGA:
            builder = self.manga_home_interface.get_card_query_builder()
            data = await self.anilist_helper.get_trending(builder, MediaType.MANGA, page, per_page)
            self.manga_home_interface.add_trending_medias(data)

    @asyncSlot(MediaType, int, int)
    async def get_latest(self, media_type: MediaType, page: int, per_page: int = 5):
        if media_type == MediaType.ANIME:
            builder = self.anime_home_interface.get_card_query_builder()
            data = await self.anilist_helper.get_latest(builder, MediaType.ANIME, page, per_page)
            self.anime_home_interface.add_latest_added_medias(data)
        elif media_type == MediaType.MANGA:
            builder = self.manga_home_interface.get_card_query_builder()
            data = await self.anilist_helper.get_latest(builder, MediaType.MANGA, page, per_page)
            self.manga_home_interface.add_latest_added_medias(data)

    @asyncSlot(MediaType, int, int)
    async def get_top_medias(self, media_type: MediaType, page: int, per_page: int = 5):
        builder = self.anime_home_interface.get_card_query_builder()
        builder.include_dates()
        builder.include_score()
        builder.include_info()
        builder.include_genres()
        if media_type == MediaType.ANIME:
            data = await self.anilist_helper.get_top_popular(builder, MediaType.ANIME, page, per_page)
            # logger.critical(data[0].coverImage)
            self.anime_home_interface.add_top_hundred_medias(data)
        elif media_type == MediaType.MANGA:
            data = await self.anilist_helper.get_top_popular(builder, MediaType.MANGA, page, per_page)
            self.manga_home_interface.add_top_hundred_medias(data)

    @asyncSlot(MediaType, int, int)
    async def get_top_rated(self, media_type: MediaType, page: int, per_page: int = 5):
        if media_type == MediaType.ANIME:
            builder = self.anime_home_interface.get_card_query_builder()
            data = await self.anilist_helper.get_top_rated(builder, MediaType.ANIME, page, per_page)
            self.anime_home_interface.add_top_rated_medias(data)
        if media_type == MediaType.MANGA:
            builder = self.manga_home_interface.get_card_query_builder()
            data = await self.anilist_helper.get_top_popular(builder, MediaType.MANGA, page, per_page)
            self.manga_home_interface.add_top_rated_medias(data)

    @asyncSlot(MediaType, MediaQueryBuilder, SearchQueryBuilder, str, int, int)
    async def search(self, media_type: MediaType, fields: MediaQueryBuilder, filters: SearchQueryBuilder,
                    query: Optional[str], page: int, per_page: int = 5):

        data = await self.anilist_helper.search(media_type, fields, filters, query, page, per_page)
        self.search_interface.add_medias(data)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        if self.splashScreen.isVisible():
            self.splashScreen.setFixedSize(self.size())
        # logger.debug(f"resizeEvent- {self.splashScreen.isVisible()}")
        super().resizeEvent(event)




if __name__ == '__main__':
    setTheme(Theme.DARK)
    setThemeColor(QColor("#db2d69"))
    app = QApplication(sys.argv)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    login = r".\assets\login.png"
    register = r".\assets\register.png"
    forget = r".\assets\forget.png"
    login_interface = LoginInterface(login, register, forget)

    login_interface.showMaximized()

    def create_main():
        main_window = MainWindow()

        main_window.setMicaEffectEnabled(False)
        main_window.setCustomBackgroundColor(QColor(242, 242, 242), QColor("#1b1919"))
        main_window.showMaximized()

    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())