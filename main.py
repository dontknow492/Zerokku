import asyncio
import json
import os
import secrets
from datetime import timedelta
from typing import Optional, Union, Dict, List

# from Demos.security.lsastore import retrieveddata
from PySide6 import QtGui
from PySide6.QtCore import QRect, QTimer, QSize, Qt, Signal, QObject
from PySide6.QtGui import QIcon, QColor
from loguru import logger
from numpy.f2py.cfuncs import callbacks
from qfluentwidgets import FluentWindow, FluentIcon, setTheme, Theme, ScrollArea, FluentStyleSheet, qconfig, \
    MSFluentWindow, NavigationItemPosition, NavigationAvatarWidget, setThemeColor, SplashScreen, Flyout, InfoBar
from PySide6.QtWidgets import QApplication, QWidget, QFrame, QScrollArea, QVBoxLayout, QHBoxLayout
import sys
from qasync import QEventLoop, asyncSlot, asyncClose
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from AnillistPython import MediaType, MediaQueryBuilderBase, SearchQueryBuilder, MediaSeason, MediaSort, \
    MediaQueryBuilder, AnilistMedia, parse_searched_media
from database import Anime, Manga, AsyncMediaRepository, AsyncLibraryRepository, init_db, drop_all_tables, User, \
    verify_login_token, populate_reference_tables, get_all_genres, get_all_statuses, get_all_formats, get_all_seasons, \
    get_all_sources, get_all_relation_types, get_all_character_roles, UserCategory
from gui.components import AddToCategory, CreateCategory
from gui.interface import HomeInterface, SearchInterface, LibraryInterface, DownloadInterface, MediaPage, LoginWindow

from core import AnilistHelper, ImageDownloader
# from gui.interface.media_page import media_type
from utils import get_current_season_and_year

from sqlalchemy.orm import sessionmaker

from database import anilist_to_manga, anilist_to_anime






# page_cache.

class PageManager(QObject):
    pageEvicted = Signal(int, MediaPage)
    requestData = Signal(int, MediaType, MediaQueryBuilder)
    def __init__(self, available_screen: QRect, parent = None, maxsize: int = 15):
        super().__init__(parent)
        self.available_screen = available_screen
        self.parent = parent
        self.image_downloader: ImageDownloader = None
        self.maxsize = maxsize

        self.page_cache: Dict[int, MediaPage] = {}
        self.page_index: List[int] = []

    async def connect_image_downloader(self):
        self.image_downloader = ImageDownloader()

    @asyncSlot(str)
    async def on_image_request(self, url):
        logger.critical(f"Requested page image: {url} to download")
        await self.image_downloader.fetch(url)


    # async def _download_image(self, url):


    def add_page(self, media_id: int, data: Union[AnilistMedia, Manga, Anime])->Optional[MediaPage]:
        # media_id = data.id
        if not media_id:
            return None
        page = self.get_page(media_id)
        if page:
            logger.info(f"Page {media_id} already exists")
            return page
        logger.info(f"Creating page {media_id}")
        page = self.create_media_page(data)
        self.cache_page(media_id, page)
        return page

    def remove_page(self, media_id: int):
        if media_id in self.page_cache:
            page = self.page_cache.pop(media_id)
            self._disconnect_page_signal(page)
            self.pageEvicted.emit(media_id, page)

            if media_id in self.page_index:
                self.page_index.remove(media_id)

            # Memory cleanup
            # page.setParent(None)
            # page.deleteLater()


    def update_page(self, page_id, data):
        page = self.page_cache.get(page_id)
        if page:
            page.setData(data)


    def get_page(self, page_id)->Optional[MediaPage]:
        return self.page_cache.get(page_id)

    def cache_page(self, page_id, page):
        if len(self.page_cache) >= self.maxsize and self.page_index:
            page_id = self.page_index[0]
            self.remove_page(page_id)

        self.page_cache[page_id] = page

    def create_media_page(self, data: Union[AnilistMedia, Manga, Anime]):
        if isinstance(data, AnilistMedia):
            media_type = data.media_type
        elif isinstance(data, Manga):
            media_type = MediaType.MANGA
        else:
            media_type = MediaType.ANIME
        page = MediaPage(self.available_screen, media_type, self.parent)
        self._connect_page_signal(page)
        page.setData(data)

        return page

    def clear_all_pages(self):
        for media_id in list(self.page_cache.keys()):
            self.remove_page(media_id)

    def has_page(self, media_id: int) -> bool:
        return media_id in self.page_cache

    def _disconnect_page_signal(self, page: MediaPage):
        if not isinstance(page, MediaPage):
            return
        page.requestImage.disconnect(self.on_image_request)
        self.image_downloader.imageDownloaded.disconnect(page.on_image_downloaded)
        page.requestData.disconnect(self.requestData)

    def _connect_page_signal(self, page: MediaPage):
        if not isinstance(page, MediaPage):
            return
        page.requestImage.connect(self.on_image_request)
        self.image_downloader.imageDownloaded.connect(page.on_image_downloaded)
        page.requestData.connect(self.requestData)

    async def close(self):
        if isinstance(self.image_downloader, ImageDownloader):
            await self.image_downloader.close()




class MainWindow(MSFluentWindow):
    logoutSignal = Signal()
    def __init__(self, user: User, session_maker: sessionmaker):
        super().__init__()

        self.setWindowTitle('Zerokku')
        self.setWindowIcon(QIcon('app.ico'))

        self.user: User = user
        self.session_maker = session_maker
        self.async_media_repo = AsyncMediaRepository(self.session_maker)
        self.async_library_repo = AsyncLibraryRepository(self.session_maker, self.async_media_repo, self.user.id)

        self._screen_geometry = QApplication.primaryScreen().availableGeometry()

        self.splashScreen = SplashScreen("splash.png", self)
        self.splashScreen.setIconSize(QSize(self._screen_geometry.height() - 100 , self._screen_geometry.height() - 100))
        self.splashScreen.finish()


        self.cache_dir = r"./.cache"
        self.anilist_helper = AnilistHelper(cache_dir=self.cache_dir)

        self.tags_path = "assets//tags.json"



        # self.navigationInterface.displayModeChanged.disconnect()
        self._available_geometry = QRect(self._screen_geometry.x(), self._screen_geometry.y(),
                                         self._screen_geometry.width() - 60-14, self._screen_geometry.height())

        self.page_manager = PageManager(self._available_geometry, self)

        self.create_category_widget = CreateCategory()
        self.create_category_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.create_category_widget.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint |
                                                   Qt.NoDropShadowWindowHint)

        self.anime_home_interface = HomeInterface(self._available_geometry, MediaType.ANIME)
        self.anime_home_interface.setObjectName("Anime Home Interface")
        self.manga_home_interface = HomeInterface(self._available_geometry, MediaType.MANGA)
        self.manga_home_interface.setObjectName("Manga Home Interface")
        self.search_interface = SearchInterface(self.tags_path)
        self.search_interface.setObjectName("Search Interface")

        self.library_interface = LibraryInterface(self.async_library_repo, self.user.id, self)
        self.library_interface.setObjectName("Library Interface")

        self.download_interface = DownloadInterface(self)
        self.download_interface.setObjectName("Download Interface")

        #
        self.setting_interface = QWidget()
        self.setting_interface.setObjectName("Settings Interface")

        self.avatar_widget = NavigationAvatarWidget(self.user.name, None, self)


        #
        self.page_interface = MediaPage(self._available_geometry, MediaType.ANIME, parent = self)

        self._init_interface()

        # asyncio.ensure_future(self._post_init())
        QTimer.singleShot(100, self._post_init)



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

        self.navigationInterface.addWidget("user", self.avatar_widget,
                            lambda: print("avatar"), NavigationItemPosition.BOTTOM )


        #adding non navi widget
        self.stackedWidget.addWidget(self.page_interface)


    def on_card_clicked(self, media_id: int, media_data: Union[AnilistMedia, Anime, Manga]):
        page = self.page_manager.add_page(media_id, media_data)
        if page:
            self.add_page_to_stacked_widget(page)
            return
        logger.error(f"Failed to add page: {media_id}")

    def add_page_to_stacked_widget(self, page):
        if self.stackedWidget.indexOf(page) == -1:
            self.stackedWidget.addWidget(page)
        self.stackedWidget.setCurrentWidget(page)

    def remove_page_from_stacked_widget(self, page):
        if self.stackedWidget.indexOf(page) == -1:
            return
        self.stackedWidget.removeWidget(page, is_delete = True)

    @asyncSlot()
    async def _post_init(self):
        #adding fav, watch later category pre populate
        await self.add_category_to_db("Favorite", "All your liked media here",
                                      True, is_deletable=False, position=0)
        await self.add_category_to_db("Watch Later", "All your media saved to watch later", True,
                                      is_deletable=False, position=1)


        await self.anilist_helper.connect()
        await self.page_manager.connect_image_downloader()
        self._signal_handler()
        await self.anime_home_interface.connect_image_downloader()
        await self.manga_home_interface.connect_image_downloader()
        await self.search_interface.init_image_downloader()

        QTimer.singleShot(10, self.splashScreen.finish)


    def _signal_handler(self):
        page = 1
        per_page = 6

        # self.anime_home_interface.downloaderInitialized.connect(
        #     lambda: self.get_trending(MediaType.ANIME, page, per_page))
        # self.anime_home_interface.downloaderInitialized.connect(
        #     lambda: self.get_latest(MediaType.ANIME, page, per_page))
        # self.anime_home_interface.downloaderInitialized.connect(
        #     lambda: self.get_top_rated(MediaType.ANIME, page, per_page))
        # self.anime_home_interface.downloaderInitialized.connect(
        #     lambda: self.get_top_medias(MediaType.ANIME, page, per_page))
        #
        # self.anime_home_interface.downloaderInitialized.connect(
        #     lambda: self.get_hero_media(MediaType.ANIME, 6)
        # )
        #
        # # #manga home
        # self.manga_home_interface.downloaderInitialized.connect(
        #     lambda: self.get_trending(MediaType.MANGA, page, per_page))
        # self.manga_home_interface.downloaderInitialized.connect(
        #     lambda: self.get_latest(MediaType.MANGA, page, per_page))
        # self.manga_home_interface.downloaderInitialized.connect(
        #     lambda: self.get_top_rated(MediaType.MANGA, page, per_page))
        # self.manga_home_interface.downloaderInitialized.connect(
        #     lambda: self.get_top_medias(MediaType.MANGA, page, per_page))
        #
        # self.manga_home_interface.downloaderInitialized.connect(
        #     lambda: self.get_hero_media(MediaType.MANGA, 6)
        # )

        #card clicked signal
        self.anime_home_interface.cardClicked.connect(self.on_card_clicked)
        self.manga_home_interface.cardClicked.connect(self.on_card_clicked)

        #search
        self.search_interface.searchSignal.connect(self.search)
        self.search_interface.cardClicked.connect(self.on_card_clicked)

        self.page_manager.pageEvicted.connect(lambda page_id, page: self.remove_page_from_stacked_widget(page))
        self.page_manager.requestData.connect(self.get_media_page_data)

    def update_user(self, user: User) -> None:
        self.user = user

    @asyncSlot(int, MediaType, MediaQueryBuilder)
    async def get_media_page_data(self, media_id: int, media_type: MediaType, fields: MediaQueryBuilder):
        # return
        data = await  self.anilist_helper.get_media_info(media_id, media_type, fields)
        if data:
            self.page_manager.update_page(media_id, data)
            self.queue_media_insert_to_db(data, media_type)
        # self.anilist_helper.get

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
        # print(data)
        if media_type == MediaType.ANIME:
            self.anime_home_interface.add_hero_banner_data(data)
        elif media_type == MediaType.MANGA:
            self.manga_home_interface.add_hero_banner_data(data)

        if data:
            self.queue_medias_insert_to_db(data.medias, media_type)

    @asyncSlot(MediaType, int, int)
    async def get_trending(self, media_type: MediaType, page: int, per_page: int = 5):
        if media_type == MediaType.ANIME:
            builder = self.anime_home_interface.get_card_query_builder()
            trending_data = await self.anilist_helper.get_trending(builder, MediaType.ANIME, page, per_page)
            # logger.debug(trending_data[0])
            self.anime_home_interface.add_trending_medias(
                trending_data
            )
        elif media_type == MediaType.MANGA:
            builder = self.manga_home_interface.get_card_query_builder()
            trending_data = await self.anilist_helper.get_trending(builder, MediaType.MANGA, page, per_page)
            self.manga_home_interface.add_trending_medias(trending_data)

        else:
            trending_data = None

        if trending_data:
            self.queue_medias_insert_to_db(trending_data.medias, media_type)

    @asyncSlot(MediaType, int, int)
    async def get_latest(self, media_type: MediaType, page: int, per_page: int = 5):
        if media_type == MediaType.ANIME:
            builder = self.anime_home_interface.get_card_query_builder()
            latest_data = await self.anilist_helper.get_latest(builder, MediaType.ANIME, page, per_page)
            self.anime_home_interface.add_latest_added_medias(latest_data)
        elif media_type == MediaType.MANGA:
            builder = self.manga_home_interface.get_card_query_builder()
            latest_data = await self.anilist_helper.get_latest(builder, MediaType.MANGA, page, per_page)
            self.manga_home_interface.add_latest_added_medias(latest_data)
        else:
            latest_data = None

        if latest_data:
            self.queue_media_insert_to_db(latest_data.medias, media_type)

    @asyncSlot(MediaType, int, int)
    async def get_top_medias(self, media_type: MediaType, page: int, per_page: int = 5):
        builder = self.anime_home_interface.get_card_query_builder()
        builder.include_dates()
        builder.include_score()
        builder.include_info()
        builder.include_genres()
        if media_type == MediaType.ANIME:
            top_medias = await self.anilist_helper.get_top_popular(builder, MediaType.ANIME, page, per_page)
            # logger.critical(top_medias[0].coverImage)
            self.anime_home_interface.add_top_hundred_medias(top_medias)
        elif media_type == MediaType.MANGA:
            top_medias = await self.anilist_helper.get_top_popular(builder, MediaType.MANGA, page, per_page)
            self.manga_home_interface.add_top_hundred_medias(top_medias)
        else:
            top_medias = None

        if top_medias:
            self.queue_media_insert_to_db(top_medias.medias, media_type)

    @asyncSlot(MediaType, int, int)
    async def get_top_rated(self, media_type: MediaType, page: int, per_page: int = 5):
        if media_type == MediaType.ANIME:
            builder = self.anime_home_interface.get_card_query_builder()
            top_rated_data = await self.anilist_helper.get_top_rated(builder, MediaType.ANIME, page, per_page)
            self.anime_home_interface.add_top_rated_medias(top_rated_data)
        elif media_type == MediaType.MANGA:
            builder = self.manga_home_interface.get_card_query_builder()
            top_rated_data = await self.anilist_helper.get_top_popular(builder, MediaType.MANGA, page, per_page)
            self.manga_home_interface.add_top_rated_medias(top_rated_data)
        else:
            top_rated_data = None

        if top_rated_data:
            self.queue_medias_insert_to_db(top_rated_data.medias, media_type)

    @asyncSlot(MediaType, MediaQueryBuilder, SearchQueryBuilder, str, int, int)
    async def search(self, media_type: MediaType, fields: MediaQueryBuilder, filters: SearchQueryBuilder,
                    query: Optional[str], page: int, per_page: int = 5):


        #demo
        with open(r"D:\Program\Zerokku\demo\data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        searched_data = parse_searched_media(data, MediaType.ANIME)

        self.queue_medias_insert_to_db(searched_data.medias, media_type)

        # data = await self.anilist_helper.search(media_type, fields, filters, query, page, per_page)
        self.search_interface.add_medias(searched_data)

    def queue_medias_insert_to_db(self, data: Union[List[Anime], List[Manga], List[AnilistMedia]],
                                  media_type: MediaType):
        QTimer.singleShot(0, lambda: asyncio.create_task(self.add_medias_to_db(data, media_type)))

    def queue_media_insert_to_db(self, data: Union[Anime, Manga, AnilistMedia], media_type: MediaType):
        QTimer.singleShot(0, lambda: asyncio.create_task(self.add_media_to_db(data, media_type)))

    @asyncSlot()
    async def add_media_to_db(self, data: Union[Anime, Manga, AnilistMedia], media_type: MediaType):
        if isinstance(data, AnilistMedia):
            media = anilist_to_manga(data) if media_type == MediaType.MANGA else anilist_to_anime(data)
        elif isinstance(data, Union[Manga, Anime]):
            media = data
        else:
            return
        await self.async_media_repo.create_update_media(media)

    @asyncSlot()
    async def add_medias_to_db(self, data: Union[List[Anime], List[Manga], List[AnilistMedia]], media_type: MediaType):
        for media in data:
            await self.add_media_to_db(media, media_type)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        if self.splashScreen.isVisible():
            self.splashScreen.setFixedSize(self.size())
        # logger.debug(f"resizeEvent- {self.splashScreen.isVisible()}")
        super().resizeEvent(event)

    def show_categories(self, categories: List[UserCategory]):
        Flyout.make(
            AddToCategory(categories),
        )

    def create_category(self):
        center = self.geometry().center()
        x = center.x() - self.create_category_widget.width() // 2
        y = center.y() - self.create_category_widget.height() // 2
        self.create_category_widget.move(x, y)
        self.create_category_widget.show()

    @asyncSlot(str, str, bool, bool, int)
    async def add_category_to_db(self, name, description, show_in_shelf=True, is_deletable: bool = True,
                                 position: int = -1):
        self.create_category_widget.clear()
        category = await self.async_library_repo.create_category(self.user_id, name, description,
                                                                 hidden=not show_in_shelf, is_deletable=is_deletable,
                                                                 position=position)
        if not category:
            self.showInfo("Warning", "Category Error", "Category with same name already exists.")
        else:
            await self.library_interface.update_categories()
            self.create_category_widget.hide()



    def showInfo(self, lvl: str, title: str, content: str):
        msg = f"{title}: {content}"
        lvl = lvl.lower()
        if lvl == "success":
            logger.success(msg)
            InfoBar.success(title, content, isClosable=True, duration=3000, parent=self)
        elif lvl == "error":
            logger.error(msg)
            InfoBar.error(title, content, isClosable=True, duration=3000, parent=self)
        elif lvl == "warning":
            logger.warning(msg)
            InfoBar.warning(title, content, isClosable=True, duration=3000, parent=self)
        else:
            logger.info(msg)
            InfoBar.info(title, content, isClosable=True, duration=3000, parent=self)

    def showMessage(self):
        pass

    @asyncClose
    async def closeEvent(self, event, /):
        await self.anilist_helper.close()
        await self.page_manager.close()
        super().closeEvent(event)



logger.add(
    "logs/app.log",            # Log file path
    rotation= "1 MB",           # Rotate after 1 MB
    encoding="utf-8",
    retention=timedelta(days=7),# Keep logs for 7 days
    level="DEBUG",             # Minimum level to log
    enqueue=True,              # Thread-safe logging
    backtrace=True,            # Show full trace on exceptions
    diagnose=True              # Show variable values in trace
)

logger.info("Logging Initialized")

os.makedirs("./data", exist_ok=True)

DATABASE_URL =  os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/zerokku.db")

def save_token(user_id: int, token: str):
    # token = secrets.token_hex(16)
    # Save to file
    with open("data/credentials.json", "w") as f:
        json.dump({"user_id": user_id, "token": token}, f)



def load_token():
    try:
        with open("data/credentials.json", "r") as f:
            data = json.load(f)
            return data["user_id"], data["token"]
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None



# Globals to hold references
# login_window = None
# main_window = None
# session_maker = None


def show_login(session_maker):
    logger.info("🔐 Showing Login Window")

    login_window = LoginWindow(
        login_image_path=r"./assets/login.png",
        register_image_path=r"./assets/register.png",
        forget_image_path=r"./assets/forget.png",
        session_maker=session_maker
    )
    login_window.loginSignal.connect(lambda user, remember_me: show_main_window(user, remember_me, session_maker))
    login_window.loginSignal.connect(login_window.close)
    login_window.showMaximized()
#
#
def show_main_window(user: User, remember_me: bool, session_maker: sessionmaker):
    logger.success(f"✅ Logged in as user ID {user.id}")

    if remember_me:
        save_token(user.id, user.token)

    main_window = MainWindow(user = user, session_maker=session_maker)
    main_window.logoutSignal.connect(lambda: show_login(session_maker))  # Reconnect login
    main_window.setMicaEffectEnabled(False)
    main_window.setCustomBackgroundColor(QColor(242, 242, 242), QColor("#1b1919"))
    main_window.showMaximized()


async def main():
    try:
        logger.info("🚀 App Starting")

        # Step 1: UI Theme
        setTheme(Theme.DARK)
        setThemeColor(QColor("#db2d69"))

        # Step 2: Setup DB
        logger.info(f"🔌 Connecting to database: {DATABASE_URL}")
        engine = create_async_engine(DATABASE_URL, echo=False)
        # await drop_all_tables(engine)
        await init_db(engine)

        session_maker = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Populating database with enums")
        genres = get_all_genres()
        status = get_all_statuses()
        formats = get_all_formats()
        seasons = get_all_seasons()
        sources = get_all_sources()
        relation_types = get_all_relation_types()
        character_roles = get_all_character_roles()

        # populating the db
        await  populate_reference_tables(
            session=session_maker(),
            status=status,
            genres=genres,
            formats=formats,
            character_roles=character_roles,
            sources=sources,
            relation_types=relation_types,
            seasons=seasons,
        )

        logger.info("🔍 Looking for saved token")
        user_id, token = load_token()
        skip_login = False
        if user_id and token:
            async with session_maker() as session:
                async with session.begin():
                    user = await verify_login_token(session, user_id, token)
                    if user:
                        skip_login = True

        # skip_login = False

        logger.info(f"Initializing QApplication")

        app = QApplication(sys.argv)
        event_loop = QEventLoop(app)
        asyncio.set_event_loop(event_loop)

        app_close_event = asyncio.Event()
        app.aboutToQuit.connect(app_close_event.set)

        if skip_login and user:
            show_main_window(user, True, session_maker)
            # main_window = MainWindow(user = user, session_maker=session_maker)
            # main_window.setMicaEffectEnabled(False)
            # main_window.setCustomBackgroundColor(QColor(242, 242, 242), QColor("#1b1919"))
            # main_window.showMaximized()

        else:
            show_login(session_maker)
            # login_image_path = r".\assets\login.png"
            # register_image_path = r".\assets\register.png"
            # forget_image_path = r".\assets\forget.png"
            # login_window = LoginWindow(
            #     login_image_path=login_image_path,
            #     register_image_path=register_image_path,
            #     forget_image_path=forget_image_path,
            #     session_maker=session_maker,
            # )
            #
            # login_window.showMaximized()
            # login_window.loginSignal.connect(show)


        with event_loop:
            event_loop.run_until_complete(app_close_event.wait())

    except Exception as error:
        logger.error(error)




if __name__ == "__main__":
    asyncio.run(main())