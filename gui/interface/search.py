import datetime
import os
from enum import Enum

import sys
import json
from collections import defaultdict
from typing import Optional, List, Tuple, Set, Dict

from PySide6.QtCore import Signal, QTimer
from PySide6.QtGui import QFont, Qt, QCloseEvent
from loguru import logger
from qasync import asyncSlot, QEventLoop, asyncClose

import asyncio

from AnillistPython import MediaFormat, MediaSeason, MediaStatus, MediaSource, MediaSort, MediaType, MediaGenre, \
    SearchQueryBuilder, MediaQueryBuilder, parse_searched_media, AnilistMedia, AnilistSearchResult

from PySide6.QtWidgets import QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QButtonGroup, QSizePolicy, \
    QSpacerItem
from qfluentwidgets import Slider, SearchLineEdit, ComboBox, CheckableMenu, ToolButton, FluentIcon, PrimaryPushButton, \
    FlyoutViewBase, FlowLayout, TogglePushButton, CheckBox, TransparentPushButton, LineEdit, Flyout, \
    FlyoutAnimationType, TransparentToggleToolButton, FluentIconBase

from core import ImageDownloader
from gui.common import MyLabel, EnumComboBox, TriStateButton, KineticScrollArea
from gui.components import SpinCard, CardContainer, MediaVariants
from utils import IconManager


# from gui.components.container import  FixedCardContainer


class TagType(Enum):
    TAGS = "tags"
    GENRES = "genres"

class FilterContainer(QWidget):
    def __init__(self, title: str, widget: Optional[QWidget] = None, font_size: int =  16, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.title_label = MyLabel(title, font_size, QFont.DemiBold, self)
        layout.addWidget(self.title_label)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)
        if widget is not None:
            layout.addWidget(widget)
    def addWidget(self, widget: QWidget):
        self.layout().addWidget(widget)

    def addLayout(self, layout):
        layout: QVBoxLayout = self.layout()
        if layout is not None:
            layout.addLayout(layout, stretch = 1)


class FilterNavigation(QWidget):
    variantChanged = Signal(MediaVariants)
    def __init__(self, variant: MediaVariants = MediaVariants.PORTRAIT, parent=None):
        super().__init__(parent)
        self.chips: Dict[str, PrimaryPushButton] = dict()
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        sort_combo = EnumComboBox(MediaSort)
        portrait_view_button = TransparentToggleToolButton(IconManager.GRID_3X3, self)
        portrait_view_button.setChecked(variant == MediaVariants.PORTRAIT)
        portrait_view_button.clicked.connect(lambda: self.variantChanged.emit(MediaVariants.PORTRAIT))
        landscape_view_button = TransparentToggleToolButton(IconManager.STACK, self)
        landscape_view_button.setChecked(variant == MediaVariants.LANDSCAPE)
        landscape_view_button.clicked.connect(lambda: self.variantChanged.emit(MediaVariants.LANDSCAPE))
        gird_view_button = TransparentToggleToolButton(IconManager.GRID, self)
        gird_view_button.setChecked(variant == MediaVariants.WIDE_LANDSCAPE)
        gird_view_button.clicked.connect(lambda: self.variantChanged.emit(MediaVariants.WIDE_LANDSCAPE))

        button_group = QButtonGroup(self)
        button_group.addButton(portrait_view_button)
        button_group.addButton(gird_view_button)
        button_group.addButton(landscape_view_button)

        #chip view
        self.chip_container = KineticScrollArea(self)
        self.chip_container.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget(self)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Policy.Minimum)
        self.chip_container_layout = QHBoxLayout(container)
        self.chip_container_layout.setContentsMargins(0, 0, 0, 0)
        self.chip_container.setFixedHeight(40)
        self.chip_container.setWidget(container)
        self.chip_container.setWidgetResizable(True)

        self.chip_spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        #init ui
        # self.main_layout.addWidget(sort_combo, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(self.chip_container)
        self.main_layout.addWidget(portrait_view_button)
        self.main_layout.addWidget(landscape_view_button)
        self.main_layout.addWidget(gird_view_button)

    def add_chip(self, type: str, value: str, icon: FluentIconBase = FluentIcon.TAG):
        logger.info(f"Adding chip '{type}': '{value}' to filter navigation")
        self.chip_container_layout.removeItem(self.chip_spacer)
        name = f"{type}: {value}"
        button = PrimaryPushButton(icon, name, self)
        self.chips[name] = button
        self.chip_container_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignLeft)
        button.clicked.connect(lambda: self.remove_chip(type, value))

        self.chip_container_layout.addItem(self.chip_spacer)


    def clear_chips(self):
        for button in self.chips.values():
            button.setVisible(False)
            button.setParent(None)
            self.chip_container_layout.removeWidget(button)
            button.deleteLater()

    def remove_chip(self, type: str, value: str):
        name = f"{type}: {value}"
        button = self.chips.get(name, None)
        if button:
            self.main_layout.removeWidget(button)
            button.deleteLater()
            self.chips.pop(name, None)


class SearchBar(QWidget):
    searchSignal = Signal(str)
    def __init__(self, tags_path: str, parent=None):
        super().__init__(parent)

        self._screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.tags_path = tags_path

        self.search_bar = SearchLineEdit()
        self.search_bar.setPlaceholderText("Search anime/manga")

        self.type_filter = EnumComboBox(MediaType, parent = self, add_default=False)

        self.genre_filter = EnumComboBox(MediaGenre, parent = self)
        self.genre_filter.setPlaceholderText("Genre")

        self.format_filter = EnumComboBox(MediaFormat, parent = self)
        self.format_filter.setPlaceholderText("Format")

        self.sort_filter = EnumComboBox(MediaSort, parent= self, add_default=True, default_text="Default")
        self.sort_filter.setPlaceholderText("Sort By")

        self.advance_filter_button = ToolButton(FluentIcon.MENU, self)
        self.filter_button = PrimaryPushButton(FluentIcon.FILTER, "Filter", self)


        self._init_ui()
        self._signal_handler()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.advance_filter_button, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.search_bar, stretch=1, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.type_filter, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.genre_filter, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.format_filter, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.sort_filter)

        layout.addWidget(self.filter_button, alignment=Qt.AlignmentFlag.AlignBottom)

    def _signal_handler(self):
        self.advance_filter_button.clicked.connect(self._on_advance_filter)
        self.search_bar.searchSignal.connect(self.searchSignal.emit)
        self.filter_button.clicked.connect(lambda: self.searchSignal.emit(self.search_bar.text()))

        self.type_filter.enumChanged.connect(self._on_type_change)


    def _on_type_change(self, media_type: MediaType):
        # logger.debug(f"Media type: {media_type}")
        if hasattr(self, "advance_filter"):
            self.advance_filter.set_media_type(media_type)
        if media_type == MediaType.ANIME:
            self.format_filter.setVisible(True)
        elif media_type == MediaType.MANGA:
            self.format_filter.setVisible(False)
        else:
            logger.warning(f"Unknown media type: {media_type}")


    def _on_advance_filter(self):
        if not hasattr(self, "advance_filter"):
            self.advance_filter = AdvanceFilter(self.tags_path)
            self.advance_filter.setFixedWidth(int(self._screen_geometry.width() * 0.7))
            self.advance_filter.setMinimumHeight(int(self._screen_geometry.height() * 0.8))
            self.advance_filter.setAttribute(Qt.WA_TranslucentBackground)
            self.advance_filter.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint |
                                Qt.NoDropShadowWindowHint)

            center = self._screen_geometry.center()
            widget_rect = self.advance_filter.frameGeometry()
            widget_rect.moveCenter(center)
            self.advance_filter.move(widget_rect.topLeft())

            self.advance_filter.set_media_type(self.type_filter.getCurrentEnum())

            #signal
            self.type_filter.enumChanged.connect(self.advance_filter.set_media_type)

        self.advance_filter.show()

    def get_options(self):
        payload = dict()

        search = self.search_bar.text()
        if search:
            payload["search"] = search

        media_type = self.type_filter.getCurrentEnum()
        if media_type is not None:
            payload["type"] = media_type

        genre = self.genre_filter.getCurrentEnum()
        if genre is not None:
            payload["genre"] = genre

        media_format = self.format_filter.getCurrentEnum()
        if media_format is not None:
            payload["format"] = media_format

        if hasattr(self, "advance_filter"):
            adv_options = self.advance_filter.get_options()
            if adv_options:
                payload.update(adv_options)

        return payload

    def get_media_type(self)->MediaType:
        return self.type_filter.getCurrentEnum()


class TagSelector(QWidget):
    tagStateChanged = Signal(int, CheckBox) #state, button
    def __init__(self, tags_path: str, parent=None):
        super().__init__(parent)
        self._tags_file = tags_path
        self._included_tags = []
        self._excluded_tags = []
        self._included_genres = []
        self._excluded_genres = []
        self._initialize_data_structures()
        self._setup_ui()
        self._load_tags()

    def _initialize_data_structures(self) -> None:
        """Initialize data structures for storing UI elements and tags."""
        self.tag_buttons: List[Tuple[CheckBox, str, FilterContainer]] = []
        self.containers: Set[FilterContainer] = set()


    def _setup_ui(self) -> None:
        """Set up the main UI layout and components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Search Bar
        self.search_bar = SearchLineEdit()
        self.search_bar.setPlaceholderText("Filter tags...")
        self.search_bar.textChanged.connect(self._filter_tags)
        main_layout.addWidget(self.search_bar)

        # Scroll Area
        scroll_area = KineticScrollArea(self)
        scroll_area.setStyleSheet("background: transparent;")
        scroll_area.setWidgetResizable(True)

        # Central Widget
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(15)
        scroll_area.setWidget(central_widget)

        main_layout.addWidget(scroll_area)
        self._central_layout = central_layout

    def _load_tags(self) -> None:
        """Load tags from JSON file and create UI elements."""
        # Add Genre Section
        self._add_genre_section()

        # Load and categorize tags
        if not os.path.exists(self._tags_file):
            logger.debug(f"Error: {self._tags_file} not found")
            return

        try:
            with open(self._tags_file, "r", encoding="utf-8") as f:
                tags = json.load(f)
        except json.JSONDecodeError as e:
            logger.debug(f"Error decoding JSON: {e}")
            return

        categories = defaultdict(list)
        for tag in tags:
            if isinstance(tag, dict) and "category" in tag and "name" in tag:
                categories[tag["category"]].append(tag)

        # Create category sections
        for category, tag_list in sorted(categories.items()):
            category = category.replace("_", " ").replace("-", "/").title()
            self._add_category_section(category, tag_list)

        self._central_layout.addStretch(1)

    def _add_genre_section(self) -> None:
        """Add genre filter section to the UI."""
        genre_box = FilterContainer("Genre", parent=self)
        genre_container = QWidget()
        genre_layout = FlowLayout(genre_container, isTight=True)

        for genre in MediaGenre:
            name = genre.value
            button = self._create_button(name, TagType.GENRES)
            genre_layout.addWidget(button)
            self.tag_buttons.append((button, name.lower(), genre_box))

        genre_box.addWidget(genre_container)
        self._central_layout.addWidget(genre_box)
        self.containers.add(genre_box)

    def _add_category_section(self, category: str, tag_list: List[dict]) -> None:
        """Add a category section with its tags to the UI."""
        container = FilterContainer(category, parent=self)
        widget = QWidget()
        container_layout = FlowLayout(widget, isTight=True)

        for tag in sorted(tag_list, key=lambda x: x["name"]):
            # button = CheckBox(tag["name"])
            name = tag["name"]
            button = self._create_button(name)
            # button.setTristate(True)
            container_layout.addWidget(button)
            self.tag_buttons.append((button, name.lower(), container))

        container.addWidget(widget)
        self._central_layout.addWidget(container)
        self.containers.add(container)

    def _create_button(self, text: str, button_type: TagType = TagType.TAGS)->CheckBox:
        button = CheckBox(text, self)
        button.setTristate(True)
        button.stateChanged.connect(lambda state: self._on_tag_state_changed(state, button, button_type))
        return button

    def _on_tag_state_changed(self, state, button, button_type: TagType):
        # Validate inputs
        try:
            button_str = button.text().strip()
            if not button_str:
                return  # Ignore empty or invalid button text
        except AttributeError:
            return  # Invalid button, skip processing

        try:
            button_type = TagType(button_type)
        except ValueError:
            return  # Invalid button_type, skip processing

        # Select appropriate lists based on button_type
        lists = {
            TagType.TAGS: (self._included_tags, self._excluded_tags),
            TagType.GENRES: (self._included_genres, self._excluded_genres)
        }
        included_list, excluded_list = lists[button_type]

        # Ensure lists are sets for efficiency
        if not isinstance(included_list, set):
            included_list = set(included_list)
            excluded_list = set(excluded_list)

        # Handle state changes
        if state == 2:
            excluded_list.discard(button_str)  # Remove from excluded if present
            included_list.add(button_str)  # Add to included
        elif state == 0:
            included_list.discard(button_str)  # Remove from included if present
            excluded_list.discard(button_str)  # Remove from excluded if present
        elif state == 1:
            included_list.discard(button_str)  # Remove from included if present
            excluded_list.add(button_str)  # Add to excluded
        else:
            logger.debug(f"Unexpected state {state}")

        # Update instance lists (if they were modified as sets)
        if isinstance(self._included_tags, list):
            if button_type == TagType.TAGS:
                self._included_tags = list(included_list)
                self._excluded_tags = list(excluded_list)
            else:
                self._included_genres = list(included_list)
                self._excluded_genres = list(excluded_list)


    def getIncludedGenres(self) -> list[str]:
        return self._included_genres

    def getExcludedGenres(self) -> list[str]:
        return self._excluded_genres

    def getIncludedTags(self) -> list[str]:
        return self._included_tags

    def getExcludedTags(self) -> list[str]:
        return self._excluded_tags

    def _filter_tags(self, text: str) -> None:
        """Filter tags based on search query."""
        query = text.lower().strip()
        visible_count = 0
        container_visible_count = 0

        # Update button visibility
        for button, name, _ in self.tag_buttons:
            is_visible = query in name
            button.setVisible(is_visible)
            if is_visible:
                visible_count += 1

        # Update container visibility
        for container in self.containers:
            container.setVisible(True)
            any_visible = any(
                btn.isVisible() for btn, _, c in self.tag_buttons if c == container
            )
            if any_visible:
                container_visible_count += 1

            container.setVisible(any_visible)

        # Log filtering results (optional, can be removed in production)
        logger.debug(f"Visible: {visible_count}/{len(self.tag_buttons)}, Visible Container: {container_visible_count}/{len(self.containers)} ")

    def clear_search(self) -> None:
        """Clear search bar and show all tags."""
        self.search_bar.clear()
        self._filter_tags("")


class AdvanceFilter(FlyoutViewBase):
    def __init__(self, tags_path: str, parent=None):
        super().__init__(parent)
        self.media_type = MediaType.ANIME
        layout = QGridLayout(self)

        # ... Enum filters ...
        self.airing_filter = EnumComboBox(enum=MediaStatus, parent=self)
        self.airing_box = FilterContainer("Airing", self.airing_filter, 18, parent=self)

        self.source_filter = EnumComboBox(enum=MediaSource, parent=self)
        self.source_box = FilterContainer("Source", self.source_filter, 18, parent=self)

        self.season_filter = EnumComboBox(enum=MediaSeason, parent=self)
        self.season_box = FilterContainer("Season", self.season_filter, 18, parent=self)

        self.year_filter = EnumComboBox(parent=self)
        self.year_filter.setPlaceholderText("Year")
        self.year_box = FilterContainer("Year", self.year_filter, 18, parent=self)

        # Define ranges
        self.year_range = (1970, datetime.datetime.now().year + 1)
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

        # Tags
        self.tag_button = MyLabel("Advance Genre and Tags Filter", 18, QFont.Weight.DemiBold, self)
        self.tags_filter = TagSelector(tags_path, self)

        # Layout
        layout.addWidget(self.airing_box, 0, 1)
        layout.addWidget(self.source_box, 0, 2)
        layout.addWidget(self.season_box, 0, 3)
        layout.addWidget(self.year_box, 0, 4)

        layout.addWidget(self.min_year_slider, 1, 1, 1, 2, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.max_year_slider, 1, 3, 1, 2, Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self.min_episode_slider, 2, 1, 1, 2, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.max_episode_slider, 2, 3, 1, 2, Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self.min_duration_slider, 3, 1, 1, 2, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.max_duration_slider, 3, 3, 1, 2, Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self.tag_button, 4, 1, 1, 4)
        layout.addWidget(self.tags_filter, 5, 1, 1, 4)

        layout.setRowStretch(5, 1)


    def set_media_type(self, media_type: MediaType):
        logger.debug(f"Set media type: {media_type}")
        self.media_type = media_type
        if media_type == MediaType.ANIME:
            self.source_box.setVisible(True)
            self.season_box.setVisible(True)
            self.max_duration_slider.setVisible(True)
            self.min_duration_slider.setVisible(True)

            self.min_episode_slider.setTitle("Minimum Episode")
            self.max_episode_slider.setTitle("Maximum Episode")
        elif media_type == MediaType.MANGA:

            self.source_box.setVisible(False)
            self.season_box.setVisible(False)
            self.max_duration_slider.setVisible(False)
            self.min_duration_slider.setVisible(False)

            self.min_episode_slider.setTitle("Minimum Chapter")
            self.max_episode_slider.setTitle("Maximum Chapter")


    def get_options(self):
        payload = dict()
        #status, source, season, fixed year


        status = self.airing_filter.getCurrentEnum()
        if status:
            payload["status"]= status

        if self.media_type == MediaType.ANIME:
            source = self.source_filter.getCurrentEnum()
            if source:
                payload["source"]= source

            season = self.season_filter.getCurrentEnum()
            if season:
                payload["season"] = season


        # Genre and tag filters
        included_genres = self.tags_filter.getIncludedGenres()
        if included_genres:
            payload["included_genres"] = included_genres

        included_tags = self.tags_filter.getIncludedTags()
        if included_tags:
            payload["included_tags"] = included_tags

        excluded_genres = self.tags_filter.getExcludedGenres()
        if excluded_genres:
            payload["excluded_genres"] = excluded_genres

        excluded_tags = self.tags_filter.getExcludedTags()
        if excluded_tags:
            payload["excluded_tags"] = excluded_tags

        # Year range filter
        if self.min_year_slider.value() > self.year_range[0]:
            payload["min_year"] = self.min_year_slider.value()
        if self.max_year_slider.value() < self.year_range[1]:
            payload["max_year"] = self.max_year_slider.value()

        # Episode range filter
        if self.min_episode_slider.value() > self.episode_range[0]:
            payload["min_episodes"] = self.min_episode_slider.value()
        if self.max_episode_slider.value() < self.episode_range[1]:
            payload["max_episodes"] = self.max_episode_slider.value()

        # Duration range filter
        if self.media_type == MediaType.ANIME:
            if self.min_duration_slider.value() > self.duration_range[0]:
                payload["min_duration"] = self.min_duration_slider.value()
            if self.max_duration_slider.value() < self.duration_range[1]:
                payload["max_duration"] = self.max_duration_slider.value()


        return payload


class SearchInterface(QWidget):
    PER_PAGE = 12
    searchSignal = Signal(MediaType, MediaQueryBuilder, SearchQueryBuilder, str, int, int) #query, builder, page, perpage
    def __init__(self, tags_path: str,  parent=None):
        super().__init__(parent)

        self.image_downloader: Optional[ImageDownloader] = None

        self.page = 1 # used for pacification
        self.builder: SearchQueryBuilder = None
        self._fields_builder: MediaQueryBuilder = MediaQueryBuilder()
        self.options: Dict = {}
        self.query: str = None


        self.search_bar = SearchBar(tags_path, self)
        self.filter_nav = FilterNavigation(parent = self)
        # self.filter_nav.add_chip("Search", "")
        self.view_stack = CardContainer(parent = self)
        self.view_stack.layout().setContentsMargins(0, 0, 0, 0)
        self.view_stack.hide_loading()
        # self.view_stack.show_loading()

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.filter_nav)
        layout.addWidget(self.view_stack, stretch=1)


        self._init_required_fields()

        self._signal_handler()

    @asyncSlot()
    async def init_image_downloader(self):
        self.image_downloader = ImageDownloader()
        self.image_downloader.imageDownloaded.connect(self.view_stack.on_cover_downloaded)

    def _init_required_fields(self):
        self._fields_builder.include_title().include_images(include_extra_large=True, include_color=True).include_score()
        self._fields_builder.include_description().include_genres().include_dates().include_info()


    def _signal_handler(self):
        self.search_bar.searchSignal.connect(self._on_search)
        self.filter_nav.variantChanged.connect(self.view_stack.switch_view)
        self.view_stack.endReached.connect(self._on_end_reached)
        self.view_stack.switching.connect(self._on_switching)
        self.view_stack.switchingFinished.connect(self._on_switching_finished)

        self.view_stack.requestCover.connect(self._on_cover_request)

    @asyncSlot(str)
    async def _on_cover_request(self, url):
        # return
        if not isinstance(self.image_downloader, ImageDownloader):
            await self.init_image_downloader()
        await self.image_downloader.fetch(url)

    def _emit_signal(self, query: str, builder: SearchQueryBuilder, page: int, per_page: int):
        self.searchSignal.emit(self.search_bar.get_media_type(), self._fields_builder, builder, query, page, per_page)

    def _on_end_reached(self):
        self.page += 1
        self._emit_signal(self.query, self.builder, self.page+ 1, self.PER_PAGE)

    def _on_switching(self):
        self.filter_nav.setEnabled(False)

    def _on_switching_finished(self):
        self.filter_nav.setEnabled(True)

    def _on_search(self, search_value):
        logger.debug(f"Search signal received")
        self.view_stack.show_loading()
        options = self.search_bar.get_options()
        search_value = search_value if search_value not in ["", None] else None

        # Only skip re-query if both search and filters are the same
        if search_value == self.query and self.options == options:
            logger.debug(f"Same search filters so ignoring: ")
            return

        builder = self._build_query(options)

        self.builder = builder
        self.page = 1  # Reset for search
        self.query = search_value
        self.options = options



        self._emit_signal(search_value, self.builder, self.page, self.PER_PAGE)


        logger.critical(f"Builder_hash: {hash(self.builder)}")



    def _build_query(self, filters: Dict):
        logger.debug(f"Building query based on filters: {filters}")
        self.filter_nav.clear_chips()
        builder = SearchQueryBuilder()

        # Basic filters
        if value := filters.get("search"):
            builder.set_search(value)
            self.filter_nav.add_chip("Search", value, FluentIcon.SEARCH)

        if value := filters.get("type"):
            builder.set_type(value)
            self.filter_nav.add_chip("Type", value)

        if value := filters.get("genre"):
            builder.set_genres([value])
            self.filter_nav.add_chip("Genre", value)

        if value := filters.get("format"):
            builder.set_formats([value])
            self.filter_nav.add_chip("Format", value)

        if value := filters.get("status"):
            builder.set_status([value])
            self.filter_nav.add_chip("Status", value)

        if value := filters.get("season"):
            builder.set_season(value)
            self.filter_nav.add_chip("Season", value)

        if value := filters.get("source"):
            builder.set_sources([value])
            self.filter_nav.add_chip("Source", value)

        # Advanced filters
        if value := filters.get("included_genres"):
            builder.set_genres(include=value)

        if value := filters.get("excluded_genres"):
            builder.set_genres(exclude=value)

        if value := filters.get("included_tags"):
            builder.set_tags(include=value)

        if value := filters.get("excluded_tags"):
            builder.set_tags(exclude=value)

        min_year = filters.get("min_year")
        max_year = filters.get("max_year")
        min_episodes = filters.get("min_episodes")
        max_episodes = filters.get("max_episodes")
        min_duration = filters.get("min_duration")
        max_duration = filters.get("max_duration")

        if min_year or max_year:
            builder.set_year_range(min_year, max_year)
            self.filter_nav.add_chip("Year Range", f"{min_year}-{max_year}", FluentIcon.CALENDAR)

        if min_episodes or max_episodes:
            if (media_type := filters.get("type")) == MediaType.ANIME:
                builder.set_episodes_range(min_episodes, max_episodes)
                self.filter_nav.add_chip("Ep Range", f"{min_episodes}-{max_episodes}")
            elif media_type == MediaType.MANGA:
                builder.set_chapters_range(min_episodes, max_episodes)
                self.filter_nav.add_chip("Ch Range", f"{min_episodes}-{max_episodes}")

        if min_duration or max_duration:
            builder.set_duration_range(min_duration, max_duration)
            self.filter_nav.add_chip("Duration Range", f"{min_duration}-{max_duration}", FluentIcon.DATE_TIME)

        return builder

    def add_medias(self, data: AnilistSearchResult):
        if not isinstance(data, AnilistSearchResult):
            logger.error(f"add_medias expects AnilistSearchResult but got {type(data)}")
            return
        is_increment = False if self.page <= 1 else True
        medias = data.medias
        self.view_stack.add_medias(medias, is_increment)

    def get_media_field_builder(self)->MediaQueryBuilder:
        return self._fields_builder

    @asyncClose
    async def closeEvent(self, event: QCloseEvent):
        if isinstance(self.image_downloader, ImageDownloader):
            await self.image_downloader.close()


async def main():
    def on_search():
        QTimer.singleShot(2000, lambda: window.add_medias(cards))

    tags_path = r"D:\Program\Zerokku\assets\tags.json"
    with open(r"D:\Program\Zerokku\demo\data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    cards = parse_searched_media(data, MediaType.ANIME, None, None, None)

    app = QApplication(sys.argv)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)


    # main = AdvanceFilter()
    window = SearchInterface(tags_path)
    await window.init_image_downloader()
    # print(window.get_media_field_builder().build())
    window.searchSignal.connect(lambda: on_search())
    window.searchSignal.connect(print)
    # filter = SearchBar()
    # filter.show()
    window.show()
    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())

if __name__ == "__main__":
    asyncio.run(main())