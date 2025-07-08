import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from enum import StrEnum, Enum
from typing import List, Dict, Optional, Union, Tuple

import sys
from loguru import logger
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QFont, QCursor
from qasync import QEventLoop, asyncSlot, asyncClose

from qfluentwidgets import SearchLineEdit, PopUpAniStackedWidget, SegmentedWidget, PrimaryToolButton, \
    TransparentToggleToolButton, FluentIcon, TransparentTogglePushButton, TogglePushButton, PushButton, \
    setCustomStyleSheet, setTheme, Theme, TeachingTip, FlyoutViewBase, ToolButton
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QApplication, QButtonGroup, QPushButton, QGroupBox, \
    QGridLayout
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from AnillistPython import MediaType, parse_searched_media, MediaStatus, MediaFormat, MediaSeason
from core import ImageDownloader
from database import AsyncLibraryRepository, init_db, AsyncMediaRepository, UserCategory, SortBy, SortOrder, Status, \
    Manga, Anime
from gui.common import EnumComboBox, MyLabel, KineticScrollArea
from gui.components import CardContainer, MediaVariants, MediaCard, SpinCard
# from gui.interface.media_page import screen_geometry
from utils import IconManager


class GroupingFlag(StrEnum):
    UNGROUPED = "ungrouped"
    CATEGORY = "category"
    SEASON = "season"
    FORMAT = "format"
    STATUS = "status"


class LibraryNavigation(QWidget):
    variantChanged = Signal(MediaVariants)
    typeChanged = Signal(MediaType)
    group_segment_changed = Signal()
    def __init__(self, variant: MediaVariants = MediaVariants.PORTRAIT,
                 media_type: MediaType = MediaType.ANIME, grouping: GroupingFlag = GroupingFlag.CATEGORY, parent=None):
        super().__init__(parent)

        self.variant = variant

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.button_map: Dict[TransparentTogglePushButton, Union[Enum, str, UserCategory]] = dict()

        self.type_segment = SegmentedWidget(self)
        # self.type_segment.setContentsMargins(5, 0, 5, 0)
        self.type_segment.addItem("anime", "Anime", lambda: self.typeChanged.emit(MediaType.ANIME), FluentIcon.MOVIE)
        self.type_segment.addItem("manga", "Manga", lambda: self.typeChanged.emit(MediaType.MANGA), FluentIcon.ALBUM)

        if media_type == MediaType.ANIME:
            self.type_segment.setCurrentItem("anime")
        elif media_type == MediaType.MANGA:
            self.type_segment.setCurrentItem("manga")

        #segment

        self.category_container = QWidget(self)
        self.category_layout = QHBoxLayout(self.category_container)
        self.category_layout.setContentsMargins(0, 0, 0, 0)

        self.category_button_group = QButtonGroup(self)

        self.status_container = QWidget(self)
        self.status_layout = QHBoxLayout(self.status_container)
        self.status_layout.setContentsMargins(0, 0, 0, 0)

        self.status_button_group = QButtonGroup(self)

        self.format_container = QWidget(self)
        self.format_layout = QHBoxLayout(self.format_container)
        self.format_layout.setContentsMargins(0, 0, 0, 0)

        self.format_button_group = QButtonGroup(self)

        self.season_container = QWidget(self)
        self.season_layout = QHBoxLayout(self.season_container)
        self.season_layout.setContentsMargins(0, 0, 0, 0)

        self.season_button_group = QButtonGroup(self)


        for index, status in enumerate(MediaStatus, start = 0):
            button = self._create_button(status.value, not index, self.status_button_group)
            self.button_map[button] = status
            self.status_layout.addWidget(button)

        for index, format in enumerate(MediaFormat, start = 0):
            format_button = self._create_button(format.value, not index, self.format_button_group)
            self.button_map[format_button] = format
            self.format_layout.addWidget(format_button)

        for index, season in enumerate(MediaSeason, start = 0):
            season_button = self._create_button(season.value, not index, self.season_button_group)
            self.button_map[season_button] = season
            self.season_layout.addWidget(season_button)


        self._init_ui()

        self.set_grouping(grouping)


    def _create_button(self, text, checked: bool, group: QButtonGroup = None, on_click = None):
        button = TransparentTogglePushButton(text, self)
        button.setFixedHeight(30)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if on_click:
            button.clicked.connect(on_click)
        if group:
            group.addButton(button)
        button.setChecked(checked)
        button.toggled.connect(self.group_segment_changed)
        return button

    def _init_ui(self):
        portrait_view_button = TransparentToggleToolButton(IconManager.GRID_3X3, self)
        portrait_view_button.setChecked(self.variant == MediaVariants.PORTRAIT)
        portrait_view_button.clicked.connect(lambda: self.variantChanged.emit(MediaVariants.PORTRAIT))
        landscape_view_button = TransparentToggleToolButton(IconManager.STACK, self)
        landscape_view_button.setChecked(self.variant == MediaVariants.LANDSCAPE)
        landscape_view_button.clicked.connect(lambda: self.variantChanged.emit(MediaVariants.LANDSCAPE))
        gird_view_button = TransparentToggleToolButton(IconManager.GRID, self)
        gird_view_button.setChecked(self.variant == MediaVariants.WIDE_LANDSCAPE)
        gird_view_button.clicked.connect(lambda: self.variantChanged.emit(MediaVariants.WIDE_LANDSCAPE))
        button_group = QButtonGroup(self)
        button_group.addButton(portrait_view_button)
        button_group.addButton(gird_view_button)
        button_group.addButton(landscape_view_button)

        scroll_area = KineticScrollArea(self)
        scroll_area.setStyleSheet("background: transparent;")
        scroll_area.setFixedHeight(32)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget(self)
        # container.setFixedHeight(40)
        scroll_area.setWidget(container)
        scroll_area.setWidgetResizable(True)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(9, 0, 0, 0)
        container_layout.setSpacing(0)

        container_layout.addWidget(self.category_container)
        container_layout.addWidget(self.status_container)
        container_layout.addWidget(self.format_container)
        container_layout.addWidget(self.season_container)

        container_layout.addStretch()

        self.main_layout.addWidget(scroll_area, stretch=1)
        self.main_layout.addWidget(self.type_segment, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(portrait_view_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(landscape_view_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(gird_view_button, alignment=Qt.AlignmentFlag.AlignRight)


    def add_category(self, category: UserCategory, selected: bool = True):
        category_button = self._create_button(category.name, selected, self.category_button_group, None)
        self.button_map[category_button] = category
        self.category_layout.addWidget(category_button)



    def set_grouping(self, group: GroupingFlag):
        logger.debug(f"Set grouping flag: {group}")
        self.status_container.setVisible(False)
        self.season_container.setVisible(False)
        self.format_container.setVisible(False)
        self.category_container.setVisible(False)
        if group == GroupingFlag.STATUS:
            self.status_container.setVisible(True)
        elif group == GroupingFlag.SEASON:
            self.season_container.setVisible(True)
        elif group == GroupingFlag.FORMAT:
            self.format_container.setVisible(True)
        elif group == GroupingFlag.CATEGORY:
            self.category_container.setVisible(True)
        elif group == GroupingFlag.UNGROUPED:
            return

    def get_grouping(self, group: GroupingFlag) -> Optional[Union[Enum, UserCategory]]:
        logger.debug(f"Get grouping flag: {group}")
        if group == GroupingFlag.STATUS:
            return self.button_map.get(self.status_button_group.checkedButton())
        elif group == GroupingFlag.SEASON:
            return self.button_map.get(self.season_button_group.checkedButton())
        elif group == GroupingFlag.FORMAT:
            return self.button_map.get(self.format_button_group.checkedButton())
        elif group == GroupingFlag.CATEGORY:
            return self.button_map.get(self.category_button_group.checkedButton())
        elif group == GroupingFlag.UNGROUPED:
            return None
        return None



    def setFormat(self, format: MediaFormat):
        logger.debug(f"Set format: {format}")

    def getFormat(self):
        pass

    def setStatus(self, status:MediaStatus):
        logger.debug(f"Set status: {status}")

    def setSeason(self, season: MediaSeason):
        logger.debug(f"Set season: {season}")

    def getCurrentType(self)->MediaType:
        route_key = self.type_segment.currentRouteKey()
        return MediaType.ANIME if route_key == "anime" else MediaType.MANGA

class ExtraFilter(FlyoutViewBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.media_type = MediaType.ANIME
        layout = QGridLayout(self)



        # Define ranges
        self.year_range = (1970, datetime.now().year + 1)
        self.episode_range = (1, 2000)
        self.duration_range = (1, 170)

        # Year sliders
        self.min_year_slider = SpinCard(icon=FluentIcon.CALENDAR, title="Minimum Year")
        self.max_year_slider = SpinCard(icon=FluentIcon.CALENDAR, title="Maximum Year")
        self.min_year_slider.setRange(*self.year_range)
        self.max_year_slider.setRange(*self.year_range)
        self.max_year_slider.setValue(self.year_range[1])
        self.min_year_slider.setValue(self.year_range[0])

        # Episode sliders
        self.min_episode_slider = SpinCard(icon=None, title="Minimum Episode")
        self.max_episode_slider = SpinCard(icon=None, title="Maximum Episode")
        self.min_episode_slider.setRange(*self.episode_range)
        self.max_episode_slider.setRange(*self.episode_range)
        self.max_episode_slider.setValue(self.episode_range[1])
        self.min_episode_slider.setValue(self.episode_range[0])

        # Duration sliders
        self.min_duration_slider = SpinCard(icon=FluentIcon.STOP_WATCH, title="Minimum Duration")
        self.max_duration_slider = SpinCard(icon=FluentIcon.STOP_WATCH, title="Maximum Duration")
        self.min_duration_slider.setRange(*self.duration_range)
        self.max_duration_slider.setRange(*self.duration_range)
        self.max_duration_slider.setValue(self.duration_range[1])
        self.min_duration_slider.setValue(self.duration_range[0])



        # Layout

        layout.addWidget(self.min_year_slider, 1, 1, 1, 2, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.max_year_slider, 1, 3, 1, 2, Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self.min_episode_slider, 2, 1, 1, 2, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.max_episode_slider, 2, 3, 1, 2, Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self.min_duration_slider, 3, 1, 1, 2, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.max_duration_slider, 3, 3, 1, 2, Qt.AlignmentFlag.AlignTop)



    def set_media_type(self, media_type: MediaType):
        logger.debug(f"Set media type: {media_type}")
        self.media_type = media_type
        if media_type == MediaType.ANIME:
            self.max_duration_slider.setVisible(True)
            self.min_duration_slider.setVisible(True)

            self.min_episode_slider.setTitle("Minimum Episode")
            self.max_episode_slider.setTitle("Maximum Episode")
        elif media_type == MediaType.MANGA:
            self.max_duration_slider.setVisible(False)
            self.min_duration_slider.setVisible(False)

            self.min_episode_slider.setTitle("Minimum Chapter")
            self.max_episode_slider.setTitle("Maximum Chapter")




class LibraryInterface(QWidget):
    TITLE_FONT_SIZE = 20
    TITLE_FONT_WEIGHT = QFont.Weight.DemiBold
    def __init__(self, async_library_repo: AsyncLibraryRepository, user_id: int, parent=None):
        super().__init__(parent)

        self.user_id = user_id
        self.async_library_repo = async_library_repo
        self.anime_card_id_map: Dict[int, MediaCard] = dict()
        self.manga_card_id_map: Dict[int, MediaCard] = dict()
        self.image_downloader: ImageDownloader = None




        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 9, 0, 9)
        # self.mainLayout.setSpacing(0)



        self.title_label = MyLabel("Library", self.TITLE_FONT_SIZE, self.TITLE_FONT_WEIGHT)
        self.count_label = MyLabel("59", self.TITLE_FONT_SIZE, self.TITLE_FONT_WEIGHT)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


        self.count_label.setFixedSize(QSize(36, 33))

        light_qss = "MyLabel {color: black; background-color: lightgray; border-radius: 16px;}"
        dark_qss = "MyLabel {color: white; background-color: gray; border-radius: 16px;}"

        setCustomStyleSheet(self.count_label, light_qss, dark_qss)
        self.search_bar = SearchLineEdit(self)
        self.search_bar.setPlaceholderText("Search in title, description, synonyms")

        self.library_nav = LibraryNavigation(parent = self)

        self.sort_combobox = EnumComboBox(SortBy, parent=self, add_default=False)
        self.sort_combobox.setCurrentEnum(SortBy.TITLE_ROMAJI)
        self.sort_combobox.setToolTip("Sort By")
        self.order_combobox = EnumComboBox(SortOrder, parent=self, add_default=False)
        self.order_combobox.setToolTip("Sort Order")
        self.grouping_combobox = EnumComboBox(GroupingFlag, parent=self, add_default=False)
        self.grouping_combobox.setCurrentEnum(GroupingFlag.CATEGORY)
        self.grouping_combobox.setToolTip("Grouping Flag")
        self.extra_filters = ToolButton(FluentIcon.MENU, parent=self)

        self.extra_filter_options = ExtraFilter()
        self.extra_filter_options.setAttribute(Qt.WA_TranslucentBackground)
        self.extra_filter_options.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint |
                                           Qt.NoDropShadowWindowHint)
        # self.extra_filter_options.setFixedWidth(700)

        self.extra_filter_options.setMinimumWidth(500)

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = screen_geometry.center().x() - self.extra_filter_options.width() // 2
        y = screen_geometry.center().y() - self.extra_filter_options.height() // 2



        # Move the widget
        self.extra_filter_options.move(x, y)

        self.type_stac = PopUpAniStackedWidget(parent=self) #anime/manga stack
        self.anime_view = CardContainer(parent=self)
        self.manga_view = CardContainer(parent=self)

        self.type_stac.addWidget(self.anime_view)
        self.type_stac.addWidget(self.manga_view)

        self._init_ui()
        self._signal_handler()

        # asyncio.ensure_future(self._post_init())
        QTimer.singleShot(200, self._post_init)

    @asyncSlot()
    async def _post_init(self):
        categories = await self.async_library_repo.get_all_categories(self.user_id)
        print(categories)
        for category in categories:
            self.library_nav.add_category(category)

        self.image_downloader = ImageDownloader()
        #signal
        self.image_downloader.imageDownloaded.connect(self.anime_view.on_cover_downloaded)
        self.image_downloader.imageDownloaded.connect(self.manga_view.on_cover_downloaded)

        await self.update_count()
        await self.update_filter()

        # animes = await  self.async_library_repo.get_by_advanced_filters(MediaType.ANIME, self.user_id, limit = -1)
        #
        # self.filter_card(animes)

    def _init_ui(self):

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.title_label)
        search_layout.addWidget(self.count_label)
        search_layout.addWidget(self.search_bar, stretch=1)
        search_layout.addWidget(self.sort_combobox)
        search_layout.addWidget(self.order_combobox)
        search_layout.addWidget(self.grouping_combobox)
        search_layout.addWidget(self.extra_filters)


        self.mainLayout.addLayout(search_layout)
        self.mainLayout.addWidget(self.library_nav)
        self.mainLayout.addWidget(self.type_stac, stretch=1)

    def _signal_handler(self):
        self.library_nav.variantChanged.connect(self._switch_view)
        self.library_nav.typeChanged.connect(self._switch_type)
        self.library_nav.typeChanged.connect(self.update_count)

        self.library_nav.group_segment_changed.connect(self.update_filter)

        self.grouping_combobox.enumChanged.connect(self.library_nav.set_grouping)

        self.grouping_combobox.enumChanged.connect(self.update_filter)
        self.sort_combobox.enumChanged.connect(self.update_filter)
        self.order_combobox.enumChanged.connect(self.update_filter)
        self.search_bar.searchSignal.connect(self.update_filter)

        #cover signal
        self.anime_view.requestCover.connect(self.download_image)
        self.manga_view.requestCover.connect(self.download_image)

        #
        self.extra_filters.clicked.connect(self.extra_filter_options.show)

    @asyncSlot(str)
    async def download_image(self, url: str):
        await self.image_downloader.fetch(url, True)

    def _switch_view(self, variant: MediaVariants):
        self.anime_view.switch_view(variant)
        self.manga_view.switch_view(variant)

    def _switch_type(self, type: MediaType):
        if type == MediaType.ANIME:
            self.type_stac.setCurrentWidget(self.anime_view)
        elif type == MediaType.MANGA:
            self.type_stac.setCurrentWidget(self.manga_view)

    @asyncSlot()
    async def update_count(self):
        """Update total library count based on current view type"""
        count = await self.async_library_repo.count_all_library_items(self.user_id, self.getCurrentViewType())
        self.setTotalCount(count)

    def setTotalCount(self, total: int):
        self.count_label.setText(str(total))

    def getCurrentViewType(self)->MediaType:
        return self.library_nav.getCurrentType()

    def get_current_variant(self)->MediaVariants:
        view: CardContainer = self.type_stac.currentWidget()
        return view.get_current_variant()


    @asyncSlot()
    async def update_filter(self):
        sort_order = self.order_combobox.getCurrentEnum()
        sort_by = self.sort_combobox.getCurrentEnum()
        search = self.search_bar.text()
        search = search.strip()
        segment = self.library_nav.get_grouping(self.grouping_combobox.getCurrentEnum())
        print(segment)
        format = None
        status = None
        season = None
        category_id = None
        if segment:
            if isinstance(segment, MediaStatus):
                status = segment
            elif isinstance(segment, MediaFormat):
                format = segment
            elif isinstance(segment, MediaSeason):
                season = segment
            elif isinstance(segment, UserCategory):
                category_id = segment.id



        animes = await  self.async_library_repo.get_by_advanced_filters(
            MediaType.ANIME,
            self.user_id,
            category_id = category_id,
            query=search,
            status=status,
            season=season,
            format=format,
            limit = -1,
            order = sort_order,
            sort_by = sort_by,
        )

        self.filter_card(animes)

    # def grouping_changed(self):
    #     segment = self.library_nav.get_grouping(self.grouping_combobox.getCurrentEnum())
    #     print(segment)

    def filter_card(self, data: Union[List[Manga], List[Anime]]):
        # if data:
        self.anime_view.show_loading()
        view_type = self.getCurrentViewType()
        variant = self.get_current_variant()
        if view_type == MediaType.ANIME:
            cards = self.anime_view.remove_cards(variant, False, True)
        else:
            cards = self.manga_view.remove_cards(variant, False, True)

        logger.critical(len(cards))

        for item in data:
            card = self.check_card_with_list(item, cards)
            if card:
                self.anime_view.portrait_container.add_cards([card])
                # card.setVisible(True)

            else:
                self.add_media_to_view(item)
                # non_added.append(item)

        timer = len(data)*100
        QTimer.singleShot(timer, lambda: self.anime_view.hide_loading())



        # self.anime_view.add_medias(data, is_increment=True)
        # self.manga_view.add_medias(data, is_increment=True)

    def check_card_with_list(self, data: Union[Manga, Anime], cards: List[MediaCard]) -> Optional[MediaCard]:
        for card in cards:
            if card and card.getMediaId() == data.id:
                return card
        return None

    def check_card(self, data: Union[Manga, Anime])->Optional[MediaCard]:
        if isinstance(data, Manga):
            cards = self.anime_view.getCards()
        else:
            cards = self.manga_view.getCards()
        for card in cards:
            if card and card.getMediaId() == data.id:
                return card
        return None

    def add_media_to_view(self, media: Union[Manga, Anime]):
        if isinstance(media, Manga):
            self.manga_view.add_media(media)
        elif isinstance(media, Anime):
            self.anime_view.add_media(media)


    @asyncClose
    async def closeEvent(self, event, /):
        await self.image_downloader.close()





async def main():
    setTheme(Theme.DARK)
    # Load your data upfront
    # tags_path = r"D:\Program\Zerokku\assets\tags.json"
    # with open(r"D:\Program\Zerokku\demo\data.json", "r", encoding="utf-8") as f:
    #     data = json.load(f)

    # cards = parse_searched_media(data, MediaType.ANIME, None, None, None)

    app = QApplication(sys.argv)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    default_path = Path("D:/Program/Zerokku/demo/mydatabase.db")
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{default_path}")

        # Create synchronous engine

    engine = create_async_engine(DATABASE_URL, echo=False)
    # await drop_all_tables(engine)
    await init_db(engine)
    session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=False,
                                 autoflush=False)
    session = session_maker()
    # session_maker = sessionmaker()

    async_media_repo = AsyncMediaRepository(session_maker)
    async_library_repo = AsyncLibraryRepository(session_maker, async_media_repo, 1)

    print(await async_library_repo.get_all_categories(1))



    window = LibraryInterface(async_library_repo, 1)
    window.show()


    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())

if __name__ == "__main__":
    asyncio.run(main())