from datetime import datetime
from pathlib import Path
from typing import List, Union, Dict, Optional

import sys
from PySide6.QtCore import QSize, Qt, QMargins, QPoint, QRect, QTimer, Signal
from PySide6.QtGui import QFont, QCursor, QPixmap, QImage, QColor, QPainter, QLinearGradient, QResizeEvent

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication, QGraphicsDropShadowEffect, QLayout, \
    QLabel, QSizePolicy
from loguru import logger
from qfluentwidgets import TransparentToolButton, TransparentPushButton, FluentIcon, ProgressRing, getFont, ToolButton, \
    isDarkTheme, setTheme, Theme, FlowLayout, PipsPager, ComboBox
from scipy.cluster.hierarchy import average

from AnillistPython import MediaStatus, AnilistEpisode, MediaType, AnilistMedia, AnilistTag, MediaGenre, AnilistTitle, \
    AnilistScore, AnilistMediaInfo
from database import Manga, Anime, Genre, get_index_enum, Tag
from gui.common import MyLabel, MultiLineElideLabel, WaitingLabel, MyImageLabel, KineticScrollArea, RoundedToolButton, \
    RoundedPushButton, AniStackedWidget
from gui.components.watch_card import WatchCardVariant, WatchCard
from gui.components import ViewMoreContainer, WatchCardLandscapeSkeleton, WatchCardCoverSkeleton, MediaCard


class SideBar(QWidget):
    TITLE_FONT = getFont(20, QFont.Weight.DemiBold)
    SPACING = 20
    def __init__(self, parent=None):
        super().__init__(parent)

        self.vboxLayout = QVBoxLayout(self)
        self.vboxLayout.setSpacing(0)

    def addWidget(self, title: str, widget: QWidget):
        title_label = self._create_title_label(title)
        self.vboxLayout.addWidget(title_label)
        self.vboxLayout.addWidget(widget)
        self.vboxLayout.addSpacing(self.SPACING)


    def addLayout(self, title: str, layout: QLayout):
        title_label = self._create_title_label(title)
        self.vboxLayout.addWidget(title_label)
        self.vboxLayout.addLayout(layout)
        self.vboxLayout.addSpacing(self.SPACING)

    def _create_title_label(self, title:str)->MyLabel:
        title_label = MyLabel(title, parent = self)
        title_label.setFont(self.TITLE_FONT)
        return title_label

class EpisodeWidget(QWidget):
    requestImage = Signal(str)
    def __init__(self, series_name: str, media_type: MediaType, perpage: int = 25, parent=None):
        super().__init__(parent)
        self._sort = "ascending"
        self.duration: int = 0
        self.series_name = series_name
        self.media_type = media_type
        self.episodes: Dict[QWidget, List[WatchCard]] = {}
        self.episode_image_map: Dict[str, WatchCard] = {}

        self.episodes_skeleton = [WatchCardCoverSkeleton() for _ in range(9)]

        self.total_episodes: int = 0
        self.episode_index: int = 0
        self.perpage: int = perpage
        self.is_anime = True if self.media_type == MediaType.ANIME else False
        self.default_series_cover: QPixmap = QPixmap()
        self.default_landscape_cover: QPixmap = QPixmap()
        self.default_cover: QPixmap = QPixmap()
        self.episode_data: List[AnilistEpisode] = []
        self.loaded_index: Dict[int, QWidget] = {}

        self.navigation_bar = QWidget(self)

        self.title_label = MyLabel("Episode", 24, QFont.Weight.Bold, parent=self.navigation_bar)
        self.source_box = ComboBox(self.navigation_bar)
        self.source_box.setPlaceholderText("Source")
        self.sort_box = ComboBox(self.navigation_bar)
        self.settting_button = ToolButton(FluentIcon.SETTING, self.navigation_bar)
        self.page_box = ComboBox(self.navigation_bar)

        items = ["Ascending", "Descending"]
        self.sort_box.addItems(items)
        self.sort_box.currentTextChanged.connect(self.on_sort)

        self.episode_stack = AniStackedWidget(self)

        self._init_ui()
         #skeleton add
        self.skeleton_widget = QWidget(self)
        layout = FlowLayout(self.skeleton_widget)
        for skeleton in self.episodes_skeleton:
            layout.addWidget(skeleton)
            layout.setContentsMargins(50, 0, 0, 0)
            layout.setHorizontalSpacing(30)
            layout.setVerticalSpacing(40)
            skeleton.start()

        self.episode_stack.addWidget(self.skeleton_widget)

    def _init_ui(self):
        nav_layout = QHBoxLayout(self.navigation_bar)
        nav_layout.setSpacing(10)
        nav_layout.addWidget(self.title_label)
        nav_layout.addWidget(self.page_box, stretch=1)
        nav_layout.addWidget(self.source_box)
        nav_layout.addWidget(self.sort_box)
        nav_layout.addWidget(self.settting_button)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.navigation_bar)
        main_layout.addWidget(self.episode_stack, stretch=1)

    def _add_page_nav(self):
        for x in range(0, self.total_episodes, self.perpage):
            start = x
            end = min(self.total_episodes, x + self.perpage)
            self.page_box.addItem(f"{start + 1} - {end}")

        self.page_box.currentIndexChanged.connect(self.on_page_change)

    def on_image_downloaded(self, url: str, pixmap: QPixmap, path: Path) -> None:
        if card:=self.episode_image_map.pop(url):
            if pixmap and not pixmap.isNull():
                card.setThumbnail(pixmap)


    def setEpisodes(self, episodes_data: list[AnilistEpisode]
                    , series_name: str, episodes: int, duration: int, default_cover: QPixmap):

        #deleating skeleon
        self.episode_stack.removeWidget(self.skeleton_widget)
        self.skeleton_widget.setParent(None)
        self.skeleton_widget.setVisible(False)
        self.skeleton_widget.deleteLater()
        self.episodes_skeleton.clear()


        self.title_label.setText("Episodes" if self.is_anime else "Chapters")
        self.total_episodes = episodes
        self.duration = duration
        self.series_name = series_name
        self.default_series_cover = default_cover
        self.episode_data = episodes_data

        self._add_page_nav()
        self._process_cover()

        self._create_page(0)

    def _process_cover(self):
        self.default_landscape_cover = self.default_series_cover

        size = WatchCard.COVER_SIZE
        thumbnail = self.default_series_cover.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        thumbnail = thumbnail.copy(QRect(QPoint(0,0), size))
        self.default_cover = thumbnail

    def _create_page(self, page_index: int):
        if page_index in self.loaded_index:
            logger.debug(f"Page {page_index} already loaded")
            self.episode_stack.setCurrentIndex(page_index, 700, 400)
            widget = self.episode_stack.currentWidget()
            reverse = False if self._sort == "ascending" else True
            self._sort_widget(widget, reverse)
            return
        widget = QWidget(self)
        layout = FlowLayout(widget) if self.is_anime else QVBoxLayout(widget)
        card_list = list()
        if isinstance(layout, FlowLayout):
            layout.setVerticalSpacing(30)
            layout.setHorizontalSpacing(30)
        else:
            layout.setSpacing(30)
        variant = WatchCardVariant.COVER if self.is_anime else WatchCardVariant.LANDSCAPE
        start = self.perpage * page_index
        end = min(self.total_episodes, start + self.perpage)

        reverse = False if self._sort == "ascending" else True
        episode_numbers = range(start, end)
        if reverse:
            episode_numbers = reversed(episode_numbers)
        for i in episode_numbers:
            if i <len(self.episode_data):
                episode = self.episode_data[i]
            else:
                episode = None
            card = self.create_card(episode, variant, i+1) #episode start for 1, index form 0
            layout.addWidget(card)
            card_list.append(card)

        self.episode_stack.addWidget(widget)
        self.episodes[widget] = card_list
        self.loaded_index[page_index] = widget

        if widget != self.episode_stack.currentWidget():
            self.episode_stack.setCurrentWidget(widget, 700, 400)

        logger.success(f"Page {page_index} loaded")

    def create_card(self, episode: AnilistEpisode, variant: WatchCardVariant, episode_num: int):
        card = WatchCard(variant)
        if episode:
            title = episode.title
            thumbnail = episode.thumbnail
        else:
            title = None
            thumbnail = None

        card.setTitle(title)
        card.setObjectName(f"ep-ch-{episode_num}")
        card.setEpisodeChapter(episode_num, is_episode= self.is_anime)
        card.setMediaTitle(self.series_name)
        card.setDate(datetime.today())
        card.setDuration(self.duration)

        if thumbnail is None or isinstance(thumbnail, str):
            thumbnail = self.default_cover if self.is_anime else self.default_landscape_cover
        card.setThumbnail(thumbnail)

        return card

    def on_page_change(self, index):
        self._create_page(index)

    def on_sort(self, value):
        if value.lower() == "ascending":
            reverse = False
            self._sort = "ascending"
        elif value.lower() == "descending":
            reverse = True
            self._sort = "descending"
        else:
            raise ValueError("Sort order must be 'ascending' or 'descending'")

        if not  len(self.episodes.keys()):
            return

        widget = self.episode_stack.currentWidget()

        if widget:
            self._sort_widget(widget, reverse)
    #
    def _sort_widget(self, widget, reverse):
        cards = self.episodes[widget]
        # cards = sorted(cards, key=lambda card: card.episode, reverse=reverse)
        new_cards = sorted(cards, key=lambda card: card.episode, reverse=reverse)

        if cards == new_cards:
            logger.debug("Cards are in the correct order already.")
            return
        else:
            cards = new_cards
            logger.debug("Cards order changed.")

        self.episodes[widget] = cards
        self._rearrange_cards()

    def _rearrange_cards(self):
        widget = self.episode_stack.currentWidget()
        cards = self.episodes[widget]
        layout = widget.layout()

        # Clear existing widgets from layout
        while layout.count():
            item = layout.takeAt(0)
            if isinstance(item, QWidget):
                layout.removeWidget(item)
                item.setParent(None)
                continue
            widget_to_remove = item.widget()
            if widget_to_remove is not None:
                layout.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)

        # Re-add sorted cards
        logger.debug("done removing")
        for index, card in enumerate(cards):
            logger.debug(f"{index}: {card.episode}")
            layout.insertWidget(index, card)

    def update_card(self, number: int, title: Optional[str]=None, series_name: Optional[str]=None,
                    thumbnail: Optional[Union[str, QPixmap, Path]] = None, duration: Optional[int] = None):
        obj_name = f"ep-ch-{number}"
        card = self.layout().findChild(WatchCard, obj_name)
        if card:
            if title:
                card.setTitle(title)
            if series_name:
                card.setMediaTitle(series_name)
            if thumbnail:
                card.setThumbnail(thumbnail)
            if duration:
                card.setDuration(duration)








class MediaPage(KineticScrollArea):
    COVER_SIZE = QSize(300, 450)
    BANNER_SIZE = None
    #signal
    requestImage = Signal(str)          # url
    requestData = Signal(int)
    requestRecommendation = Signal(int)
    requestEpisode = Signal(int)
    # media id
    def __init__(self, available_screen: QRect, media_type: MediaType, parent=None):
        super().__init__(parent)

        self._media_id = None
        self.media_type = media_type
        self.image_map:Dict[str, Union[WatchCard, MediaCard, WaitingLabel]] = dict()
        self._anilist_media_data: AnilistMedia = None
        self._sql_alchemy_media_data: Union[Anime, Manga] = None
        self._screen_geometry = available_screen


        self.BANNER_SIZE = QSize(self._screen_geometry.width(), int(self._screen_geometry.height() * 0.7))

        self.container = QWidget(self)
        self.container.setMaximumWidth(self._screen_geometry.width())
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.setWidget(self.container)
        self.setWidgetResizable(True)

        self._create_widgets()
        self._init_ui()

    def _create_widgets(self):
        self._body_font = getFont(14, QFont.Weight.DemiBold)
        self.banner_label = WaitingLabel(parent=self)
        self.banner_label.start()
        self.banner_label.setFixedSize(self.BANNER_SIZE)

        self.cover_label = WaitingLabel(parent=self)
        self.cover_label.setFixedSize(self.COVER_SIZE)
        self.cover_label.start()
        self.cover_label.setBorderRadius(10, 10, 10, 10)
        # self.cover_label.start()
        self.cover_shadow_effect = QGraphicsDropShadowEffect(self.cover_label)
        self.cover_shadow_effect.setBlurRadius(40)
        self.cover_shadow_effect.setXOffset(5)
        self.cover_shadow_effect.setYOffset(5)
        self.cover_shadow_effect.setColor(QColor("gray"))

        self.cover_label.setGraphicsEffect(self.cover_shadow_effect)

        self.status_label_top = MyLabel("Unknown", parent=self)
        self.title_label = MyLabel("Unknown title", 38, QFont.Weight.Bold, parent=self)
        self.overview_label = MultiLineElideLabel("Unknown overview", 8,  parent=self)
        self.overview_label.setCursor(Qt.CursorShape.IBeamCursor)
        self.overview_label.setFont(self._body_font)
        self.duration_label = MyLabel("Duration", parent=self)
        self.start_date_label = MyLabel("Start Date", parent=self)
        self.format_label = MyLabel("Format", parent=self)
        #buttons

        self.play_trailer_button = TransparentPushButton(FluentIcon.PLAY_SOLID, "Play Trailer", parent=self)
        self.play_trailer_button.setFont(getFont(20, QFont.Weight.DemiBold))
        self.play_trailer_button.setIconSize(QSize(18, 18))

        icon_size = QSize(20, 20)

        self.like_button = self._create_rounded_button(FluentIcon.HEART, icon_size,
                                                    "Like", Qt.CursorShape.PointingHandCursor, 20, 40)
        self.save_to_watchlist_button = self._create_rounded_button(FluentIcon.LIBRARY, icon_size,
                                                    "Add to watchlist", Qt.CursorShape.PointingHandCursor, 20, 40)
        self.add_to_category_button = self._create_rounded_button(FluentIcon.ADD_TO, icon_size,
                                                    "Add to library", Qt.CursorShape.PointingHandCursor, 20, 40)
        self.webpage_button = self._create_rounded_button(FluentIcon.GLOBE, icon_size,
                                                                  "Open in Browser", Qt.CursorShape.PointingHandCursor,
                                                                  20, 40)
        #score
        self.user_score = ProgressRing(parent=self)
        font = getFont(28, QFont.Weight.DemiBold)
        self.user_score.setFont(font)
        self.user_score.setTextVisible(True)
        self.user_score.setValue(0)

        font = getFont(18, QFont.Weight.DemiBold)

        self.user_score_label = MyLabel("User\nScore", parent=self)
        self.user_score_label.setFont(font)
        self.rating_button = RoundedPushButton("What's your Rating?", parent=self)
        self.rating_button.setFont(font)

        #genre
        self.genre_layout = QHBoxLayout()
        # self.genre_layout.addWidget(self.format_label)

        #extra
        self.status_label = MyLabel("Status", parent=self)
        self.start_date_label = MyLabel("Start Date", parent=self)
        self.end_date_label = MyLabel("End Date", parent=self)
        self.average_score_label = MyLabel("Average Score", parent=self)
        self.mean_score_label = MyLabel("Mean Score", parent=self)
        self.popularity_label = MyLabel("Popularity", parent=self)
        self.favorites_label = MyLabel("Favorites", parent=self)
        self.synonyms_layout = QVBoxLayout()
        self.tags_layout = FlowLayout()


        #containers
        margins = QMargins(50, 0, 50, 0)

        self.top_container = self._init_top_container_ui()
        self.top_container.setContentsMargins(margins)
        self.top_container.setParent(self.banner_label)
        self.top_container.setFixedSize(self.banner_label.size())


        self.bottom_container = QWidget(self)

        self.bottom_container_layout = QHBoxLayout(self.bottom_container)
        self.bottom_container_layout.setContentsMargins(margins)

        self.recommendations_container = ViewMoreContainer("Recommendations", parent=self)
        self.recommendations_container.layout().setSpacing(10)
        self.recommendations_container.title_label.setFont(getFont(24, QFont.Weight.Bold))

        self.central_widget = self._init_central_container_ui()
        self.side_bar = self._init_sidebar_ui()

    @staticmethod
    def _create_rounded_button(icon, icon_size: QSize, tooltip:str, cursor:QCursor, radius:int, min_height: int):
        button = RoundedToolButton(icon)
        button.setIconSize(icon_size)
        button.setToolTip(tooltip)
        button.setCursor(cursor)
        button.setRadius(radius)
        button.setMinimumHeight(min_height)
        return button

    def _init_ui(self):
        self.bottom_container_layout.addWidget(self.central_widget, stretch=1)
        self.bottom_container_layout.addWidget(self.side_bar)

        self.container_layout.addWidget(self.banner_label, alignment=Qt.AlignmentFlag.AlignTop)
        self.container_layout.addWidget(self.bottom_container)


    def add_download(self, url, card):
        if url and card:
            self.image_map[url] = card
            self.requestImage.emit(url)

    def on_image_downloaded(self, url: str, pixmap: QPixmap, path: Path) -> None:
        if card:= self.image_map.pop(url):
            if pixmap and not pixmap.isNull():
                card.setCover(pixmap)
            else:
                card.setCover(path)


    def _init_top_container_ui(self):
        top_container = QWidget(self)
        top_layout = QHBoxLayout(top_container)
        # top_layout.setContentsMargins(50, 0, 50, 0)
        top_layout.setSpacing(50)

        top_layout.addWidget(self.cover_label)

        vbox = QVBoxLayout(top_container)
        vbox.setSpacing(0)
        vbox.addStretch(1)

        # vbox.addWidget(self.status_label_top)
        vbox.addSpacing(-10)
        vbox.addWidget(self.title_label)
        vbox.addSpacing(-10)
        vbox.addLayout(self.genre_layout)
        vbox.addSpacing(20)

        user_layout = QHBoxLayout()
        user_layout.setSpacing(10)
        user_layout.addWidget(self.user_score)
        user_layout.addWidget(self.user_score_label)
        user_layout.addSpacing(20)
        user_layout.addWidget(self.rating_button)

        user_layout.addStretch(1)

        vbox.addLayout(user_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addWidget(self.add_to_category_button)
        button_layout.addWidget(self.like_button)
        button_layout.addWidget(self.save_to_watchlist_button)
        button_layout.addWidget(self.webpage_button)
        button_layout.addWidget(self.play_trailer_button)
        button_layout.addStretch(1)

        vbox.addSpacing(10)
        vbox.addLayout(button_layout)
        vbox.addSpacing(30)
        vbox.addWidget(MyLabel("Overview", 24, QFont.Weight.DemiBold, parent=self))
        vbox.addSpacing(10)
        vbox.addWidget(self.overview_label)
        vbox.addStretch(1)

        top_layout.addLayout(vbox, 1)
        # top_layout.addStretch(1)

        return top_container

    def _init_central_container_ui(self):
        central_container = QWidget(self)
        self.episode_container = EpisodeWidget("My Dress up Darling", self.media_type, parent = self)

        central_layout = QVBoxLayout(central_container)
        central_layout.setSpacing(10)
        central_layout.addWidget(self.episode_container)
        central_layout.addWidget(self.recommendations_container)
        central_layout.addStretch(1)
        return central_container

    def _init_sidebar_ui(self):
        side_bar = SideBar(parent=self)

        #title card

        #adding
        side_bar.addWidget("Status", self.status_label)
        side_bar.addWidget("Start Date", self.start_date_label)
        side_bar.addWidget("End Date", self.end_date_label)
        side_bar.addWidget("Average Score", self.average_score_label)
        side_bar.addWidget("Mean Score", self.mean_score_label)
        side_bar.addWidget("Popularity", self.popularity_label)
        side_bar.addWidget("Favorites", self.favorites_label)
        side_bar.addLayout("Synonyms", self.synonyms_layout)
        side_bar.addLayout("Tags", self.tags_layout)


        side_bar.layout().addStretch(1)


        return side_bar


    def setData(self, data: Union[AnilistMedia, Anime, Manga]):
        if isinstance(data, AnilistMedia):
            self._sql_alchemy_media_data = None
            self._parse_anilist_media(data)
        elif isinstance(data, (Anime, Manga)):
            self._anilist_media_data = None
            self._parse_sql_alchemy_model(data)

    def _parse_anilist_media(self, data: AnilistMedia):
        self.setMediaId(data.id)
        title = data.title
        self.setTitle(title.romaji or title.english or title.native)
        self.setGenre(data.genres or [])
        score = data.score
        if score:
            self.setMeanScore(score.mean_score)
            self.setAverageScore(score.average_score)

        self.setOverview(data.description)
        cover_image = data.coverImage.extraLarge
        banner_image = data.bannerImage

        self.add_download(cover_image, self.cover_label)
        self.add_download(banner_image, self.banner_label)

        episodes = data.episodes

        # extra
        info = data.info
        if info:
            self.setStatus(info.status)

            # status = info.status
            # format  = info.format
            # source = info.source
            # season = info.season

        self.setStartDate(data.startDate)
        self.setEndDate(data.endDate or -1)
        self.setSynonyms(data.synonyms)

        self.setTags(data.tags)

    def _parse_sql_alchemy_model(self, data: Union[Anime, Manga]):
        self.setMediaId(data.id)
        self.setTitle(data.title_romaji or data.title_english or data.title_native)
        self.setGenre(data.genres or [])
        self.setMeanScore(data.mean_score)
        self.setAverageScore(data.average_score)
        self.setPopularity(data.popularity)
        self.setFavorites(data.favourites)
        self.setOverview(data.description)

        self.setRating(data.mean_score or data.average_score)

        cover_image = data.cover_image_extra_large or data.cover_image_large
        banner_image = data.cover_image_extra_large or data.banner_image
        episodes = data.episodes

        status_id = data.status_id
        status = get_index_enum(MediaStatus, status_id)

        self.setStatus(status)

        self.setStartDate(data.start_date)
        self.setEndDate(data.end_date)

        self.setSynonyms(data.synonyms)

        self.setTags(data.tags)


    def setTags(self, tags: List[Union[AnilistTag, Tag]]):
        if tags is None:
            return
        for tag in tags:
            self._create_tag(tag)


    def _create_genres(self, genres: List[Union[MediaGenre, Genre, str]]):
        self.genre_layout.setSpacing(0)
        self.genre_layout.setContentsMargins(0, 0, 0, 0)
        for genre in genres:
            if isinstance(genre, MediaGenre):
                genre = genre.value
            elif isinstance(genre, Genre):
                genre = genre.name
            button = TransparentPushButton(genre, parent=self)
            button.setContentsMargins(0, 0, 0, 0)
            button.setFont(self._body_font)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.genre_layout.addWidget(button)

        self.genre_layout.addStretch(1)



    def _create_tag(self, tag: Union[dict, Tag, AnilistTag]):
        # for tag in tags:
        if isinstance(tag, Tag):
            name = tag.name
            tag_id = tag.id
        elif isinstance(tag, dict):
            name = tag["name"]
            tag_id = tag["id"]
        elif isinstance(tag, AnilistTag):
            name = tag.name
            tag_id = tag.id
        else:
            return
        button = RoundedPushButton(name, parent=self)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFont(self._body_font)
        self.tags_layout.addWidget(button)

    def _create_synonyms(self, synonyms: List[str]):
        if synonyms is None:
            return
        for index, syn in enumerate(synonyms, start=1):
            syn = syn.strip()
            if not syn:
                continue
            # num_label = MyLabel(f"{index:02d}")
            label = MyLabel(f"{index:02d}. {syn}", parent=self)
            label.setWordWrap(True)
            label.setFont(self._body_font)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setCursor(Qt.CursorShape.IBeamCursor)
            self.synonyms_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)

        # self.side_bar.addLayout("Synonyms", self.synonyms_layout)

    def setMediaId(self, media_id: int):
        self._media_id = media_id

    def setTitle(self, title: str):
        if title is None:
            return
        self.title_label.setText(title.upper())

    def setRating(self, rating: int):
        if rating is None:
            rating = 0
        rating = min(max(0, rating), 100)
        self.user_score.setValue(rating)

    def setGenre(self, genres: List[str]):
        self._create_genres(genres[:10])

    def setOverview(self, overview: str):
        if overview is None:
            return
        self.overview_label.setText(overview)

    def setCover(self, cover: Union[str, QPixmap, QImage]):
        self.cover_label.setImage(cover)
        self.cover_label.setScaledSize(self.COVER_SIZE)

    def setBanner(self, banner: Union[str, QPixmap, QImage]):
        if isinstance(banner, str):
            banner = QPixmap(banner)
        banner = banner.scaled(self.banner_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        banner = banner.copy(self.banner_label.geometry())
        # faded_banner = apply_fade_out_mask(banner)
        self.banner_label.setImage(banner)

    def setSynonyms(self, synonyms: List[str]):
        self._create_synonyms(synonyms)

    # def setTags(self, tags: List[Dict]):
    #     self._create_tags(tags)

    def setStartDate(self, start_date: datetime):
        if start_date is None:
            return
        date_str = start_date.strftime("%B %d, %Y")
        self.start_date_label.setText(date_str)

    def setEndDate(self, end_date: datetime):
        if end_date is None:
            end_date = datetime.today()
        date_str = end_date.strftime("%B %d, %Y")
        self.end_date_label.setText(date_str)

    def setStatus(self, status: MediaStatus):
        if status is None:
            status = MediaStatus.RELEASING
        self.status_label.setText(status.value)

    def setPopularity(self, popularity: int):
        if popularity is None:
            popularity = "???"
        self.popularity_label.setText(str(popularity))

    def setFavorites(self, favorites: int):
        if favorites is None:
            favorites = "???"
        self.favorites_label.setText(str(favorites))

    def setAverageScore(self, average_score: int):
        if average_score is None:
            average_score = "???"
        self.average_score_label.setText(str(average_score))

    def setMeanScore(self, mean_score: int):
        if mean_score is None:
            mean_score = "???"
        self.mean_score_label.setText(str(mean_score))


    def setTopContainerColor(self, color: QColor):
        # Convert to HSV and modify if needed
        # Set custom alpha here
        # color = color.darker() if isDarkTheme() else color.lighter()


        # r = color.red()
        # g = color.green()
        # b = color.blue()
        a = 180
        r = g = b = 0

        print(f"rgba({r}, {g}, {b}, {a})")

        self.top_container.setStyleSheet(
            f"""
            QWidget {{
                background-color: rgba({r}, {g}, {b}, {a});
            }}
            QLabel {{
                background-color: none;
            }}
            """
        )

        self.cover_shadow_effect.setColor(color.darker())

    def setEpisode(self, episode_number: int, episode_data: List[AnilistEpisode], duration: int):
        self.episode_container.setEpisodes(
            episode_data,
            self.media_type,
            self.title_label.text(),
            episode_number,
            duration,
            self.cover_label.pixmap(),
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    episode = EpisodeWidget("Naruto", MediaType.ANIME, 13)
    episode.show()
    app.exec()

if __name__ == '__main__2':
    setTheme(Theme.DARK)
    media_type = MediaType.ANIME
    title = "My Dress Up Darling"
    genres = ["Slice of Life", "Ecchi", "Romance", "Comedy"]
    rating = 86
    description = ("Wakana Gojo is a high school boy who wants to become a kashirashi--a master craftsman who makes "
                   "traditional Japanese Hina dolls. Though he's gung-ho about the craft, he knows nothing about the "
                   "latest trends, and has a hard time fitting in with his class. The popular kids--especially one girl,"
                   " Marin Kitagawa--seem like they live in a completely different world. That all changes one day, when"
                   " she shares an unexpected secret with him, and their completely different worlds collide.")
    cover = r"D:\Program\Zerokku\demo\poster.jpg"
    banner = r"D:\Program\Zerokku\demo\poster.jpg"
    dominant_color = QColor("#9c564b")
    synonyms= [
        "카우보이 비밥",
        "קאובוי ביבופ",
        "คาวบอย บีบ๊อป",
        "Ковбой Бибоп",
        "Καουμπόηδες του Διαστήματος",
        "Kowboj Bebop"
    ]
    start_date = datetime(2022, 12, 5)
    end_date = datetime.today()
    status = MediaStatus.FINISHED
    favourites = 40000
    popularity = 45332
    average_score = 85
    mean_score = 89
    episodes = 12
    duration = 24

    tags =  [
        {
          "name": "Space",
          "id": 63
        },
        {
          "name": "Crime",
          "id": 648
        },
        {
          "name": "Episodic",
          "id": 193
        },
        {
          "name": "Ensemble Cast",
          "id": 105
        },
        {
          "name": "Primarily Adult Cast",
          "id": 109
        },
        {
          "name": "Tragedy",
          "id": 85
        },
        {
          "name": "Travel",
          "id": 1310
        },
        {
          "name": "Noir",
          "id": 327
        },
        {
          "name": "Philosophy",
          "id": 391
        },
        {
          "name": "Anti-Hero",
          "id": 104
        },
        {
          "name": "Guns",
          "id": 157
        },
        {
          "name": "Cyberpunk",
          "id": 108
        },
        {
          "name": "Male Protagonist",
          "id": 82
        },
        {
          "name": "Found Family",
          "id": 1277
        },
        {
          "name": "Terrorism",
          "id": 285
        },
        {
          "name": "Female Protagonist",
          "id": 98
        },
        {
          "name": "Cowboys",
          "id": 1648
        },
        {
          "name": "Martial Arts",
          "id": 30
        },
        {
          "name": "Cyborg",
          "id": 801
        },
        {
          "name": "Tomboy",
          "id": 931
        },
        {
          "name": "Amnesia",
          "id": 240
        },
        {
          "name": "Gambling",
          "id": 91
        },
        {
          "name": "Heterosexual",
          "id": 1045
        },
        {
          "name": "Yakuza",
          "id": 199
        },
        {
          "name": "Drugs",
          "id": 489
        },
        {
          "name": "Police",
          "id": 40
        },
        {
          "name": "Nudity",
          "id": 100
        },
        {
          "name": "Cult",
          "id": 586
        },
        {
          "name": "Tanned Skin",
          "id": 335
        },
        {
          "name": "Circus",
          "id": 476
        },
        {
          "name": "CGI",
          "id": 90
        }
      ]
    # dominant_color_nearest = pick_overlay_color(dominant_color)

    app = QApplication(sys.argv)
    screen_geometry = QApplication.primaryScreen().geometry()
    screen_geometry.setWidth(screen_geometry.width()-14)
    main_page = MediaPage(screen_geometry, media_type)
    main_page.showMaximized()

    sql_tags = []
    anilist_tags = []
    for tag in tags:
        id = tag["id"]
        name = tag["name"]
        sql_tags.append(Tag(id=id, name=name))
        anilist_tags.append(AnilistTag(id=id, name=name))

    data = AnilistMedia(
        id = 1,
        media_type = media_type,
        title= AnilistTitle(english=title, native=title, romaji=title ),
        description= description,
        duration=duration,
        episodes=episodes,
        score = AnilistScore(
            id = 1,
            average_score=average_score, mean_score=mean_score,
            popularity=popularity, favourites=favourites
        ),
        info = AnilistMediaInfo(
            id = 1,
            status = status,
        ),
        startDate = start_date,
        endDate = end_date,
        bannerImage=banner,
        tags = tags,
        synonyms=synonyms,

    )
    genre_1 = Genre(id=1, name="Action")
    genre_2 = Genre(id=2, name="Roman")
    genre_3 = Genre(id=3, name="Adventure")



    anime = Anime(
        id = 1,
        title_english=title,
        title_native=title,
        title_romaji=title,
        description=description,
        duration=duration,
        episodes=episodes,
        average_score=average_score,
        mean_score=mean_score,
        popularity=popularity,
        favourites=favourites,
        status_id=0,
        genres=[genre_1, genre_2, genre_3],
        start_date=start_date,
        end_date=end_date,
        tags=sql_tags,
        synonyms=synonyms,
    )

    main_page.setData(anime)

    app.exec()