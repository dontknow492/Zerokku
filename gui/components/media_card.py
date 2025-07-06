import datetime

import sys
from enum import Enum
from pathlib import Path
from typing import List, Union

from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QObject, QRect, Signal
from PySide6.QtGui import QColor, QFont, QResizeEvent, QImage, QPixmap, QMouseEvent
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QFrame, QScrollArea, QWidget, \
    QGraphicsOpacityEffect, QLabel, QSizePolicy
from loguru import logger
from qfluentwidgets import SubtitleLabel, BodyLabel, FlowLayout, ScrollArea, TransparentToolButton, \
    setTheme, Theme, CardWidget, setCustomStyleSheet, SimpleCardWidget, ElevatedCardWidget, ThemeColor

from gui.common import (WaitingLabel, OutlinedChip, MyLabel, SkimmerWidget, SkeletonMode, KineticScrollArea,
                        MultiLineElideLabel)
from utils import FontAwesomeRegularIcon, get_scale_factor

from AnillistPython import AnilistMedia, AnilistScore, AnilistMediaInfo, MediaType, MediaStatus, AnilistTitle, \
    MediaCoverImage, MediaGenre


class MediaVariants(Enum):
    PORTRAIT = 0
    LANDSCAPE = 1
    WIDE_LANDSCAPE = 2


class MediaCard(CardWidget):
    COVER_SIZE = QSize(195, 270)
    MINI_COVER_SIZE = QSize(55, 76)
    DEFAULT_MARGIN = 9

    Title_FONT_SIZE = 17
    TILE_FONT_WEIGHT = QFont.Weight.DemiBold

    BODY_FONT_WEIGHT = QFont.Weight.Normal
    STRONG_BODY_FONT_WEIGHT = QFont.Weight.DemiBold
    BODY_FONT_SIZE = 14

    #signal
    cardClicked = Signal(int, AnilistMedia)

    def __init__(self, variant: MediaVariants = MediaVariants.PORTRAIT, parent=None):
        super().__init__(parent)
        self._press_pos = None
        self._drag_threshold = 10  # pixels
        self._mal_id: int = None
        self._min_sizeHint = QSize(self.COVER_SIZE.width(), self.COVER_SIZE.height() + 50)
        self.variant = variant
        self.rating_color = QColor("green")
        self._is_loading = True
        self._media_id: int = None
        self._media_data: AnilistMedia = None
        self._create_widgets()
        # self._create_genre()
        self.setup_ui()

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _create_widgets(self):
        self.title_label = MultiLineElideLabel("Solo Leveling", 1, 17, QFont.Weight.DemiBold, parent=self)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        # self.title_label.setStyleSheet("background-color:rgb(240, 240, 240);")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.title_label.setContentsMargins(4, 0, 0, 0)
        self.title_label.setText("Solo Leveling")
        self.title_label.setWordWrap(True)

        self.cover_label = WaitingLabel()
        self.cover_label.setFixedSize(self.COVER_SIZE)
        self.cover_label.start()

        self.description_label = MyLabel("This is Media Description", self.BODY_FONT_SIZE, self.BODY_FONT_WEIGHT)
        self.description_label.setWordWrap(True)

        self.start_year = 2023
        self.end_year = 2024
        self.time_label = MyLabel(f"{self.start_year}-{self.end_year}", self.BODY_FONT_SIZE,
                                  self.STRONG_BODY_FONT_WEIGHT)
        self.status_label = MyLabel("Releasing", self.BODY_FONT_SIZE, self.STRONG_BODY_FONT_WEIGHT)

        self.release_status_label = MyLabel("Release", self.Title_FONT_SIZE, self.TILE_FONT_WEIGHT)
        self.release_status_label.setText(f"{self.status_label.text()} {self.start_year}-{self.end_year}")

        self.rating_widget = QFrame()
        layout = QHBoxLayout(self.rating_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.rating_label = MyLabel("87%", self.BODY_FONT_SIZE, self.STRONG_BODY_FONT_WEIGHT)
        # self.rating_label = BodyLabel("87%")
        self.rating_label.setContentsMargins(0, 9, 0, 0)
        self.rating_icon = TransparentToolButton(FontAwesomeRegularIcon("\uf118"))
        self.rating_icon.setIconSize(QSize(30, 30))
        self.rating_icon.setFixedSize(QSize(30, 36))
        self.setRating(75)
        layout.addWidget(self.rating_icon)
        layout.addWidget(self.rating_label)

        # self.rating_widget.setIconSize(QSize(24, 24))
        self.users_label = MyLabel("1234 users", self.BODY_FONT_SIZE, self.STRONG_BODY_FONT_WEIGHT)
        self.genres = ['Action', 'Adventure', 'Isekai']
        self.genre_container = QWidget(self)
        self.genre_layout = FlowLayout(self.genre_container)
        self.genre_layout.setContentsMargins(0, 0, 0, 0)
        self.media_type = MyLabel("Manga", self.BODY_FONT_SIZE, self.STRONG_BODY_FONT_WEIGHT)
        self.media_episode_chapters = MyLabel("56 Chapters", self.BODY_FONT_SIZE, self.STRONG_BODY_FONT_WEIGHT)

    def _create_genre(self, color: QColor):
        self.genre_layout.takeAllWidgets()
        for genre in self.genres:
            if isinstance(genre, MediaGenre):
                genre = genre.value
            button = OutlinedChip(genre[:15], primary_color=color, border_radius=14)
            button.setMaximumHeight(28)
            self.genre_layout.addWidget(button)

    def setup_ui(self):
        # Clear existing layout if any
        self._clear_layout()
        if self.layout():
            QWidget().setLayout(self.layout())  # Transfer ownership to a temporary widget to delete
        self._configure_layout()

    def _configure_layout(self):
        if self.variant == MediaVariants.WIDE_LANDSCAPE:
            self._init_detailed_layout()
        elif self.variant == MediaVariants.LANDSCAPE:
            self._init_landscape_layout()
        elif self.variant == MediaVariants.PORTRAIT:
            self._init_minimal_layout()

    def _clear_layout(self):
        self.title_label.setParent(None)
        self.cover_label.setParent(None)
        self.description_label.setParent(None)
        self.time_label.setParent(None)
        self.status_label.setParent(None)
        self.rating_widget.setParent(None)
        self.users_label.setParent(None)
        self.genre_container.setParent(None)
        self.media_type.setParent(None)
        self.media_episode_chapters.setParent(None)
        self.release_status_label.setParent(None)

    def set_variant(self, variant: MediaVariants):
        """Switch the card to a new previous_variant and update the UI."""
        if self.variant != variant:
            self.variant = variant
            self.setup_ui()

    def create_vbox(self, *widgets, alignments=None, spacing=0):
        vbox = QVBoxLayout()
        vbox.addStretch()
        vbox.setSpacing(spacing)
        for i, widget in enumerate(widgets):
            alignment = alignments[i] if alignments and i < len(alignments) else None
            if alignment:
                vbox.addWidget(widget, alignment=alignment)
            else:
                vbox.addWidget(widget)
        vbox.addStretch()
        return vbox

    def create_scrollable_area(self, widget: QWidget) -> QScrollArea:
        scroll = ScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        return scroll

    def _init_detailed_layout(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 1, 1, 1)
        layout.setSpacing(0)

        radius = self.borderRadius
        self.cover_label.setFixedSize(self.COVER_SIZE)
        self.cover_label.setBorderRadius(radius, 0, radius, 0)
        self.title_label.max_lines = 2
        # self.title_label.setStyleSheet("background: red;")
        self.release_status_label.setText(f"{self.status_label.text()} • {self.start_year}-{self.end_year}")
        # }")

        main_vlayout = QVBoxLayout()
        content_widget = QFrame()
        vboxlayout = QVBoxLayout(content_widget)
        vboxlayout.setSpacing(10)
        # vboxlayout.setContentsMargins(0, 0, 0, 0)

        time_layout = QHBoxLayout()
        time_layout.addWidget(self.release_status_label)
        time_layout.addStretch(1)
        time_layout.addWidget(self.rating_widget)

        info_layout = QHBoxLayout()
        info_layout.setSpacing(0)
        info_layout.addWidget(self.media_type)
        info_layout.addWidget(MyLabel("•", self.BODY_FONT_SIZE, self.STRONG_BODY_FONT_WEIGHT))
        info_layout.addWidget(self.media_episode_chapters)
        info_layout.addStretch(1)

        info_time_layout = QVBoxLayout()
        info_time_layout.setSpacing(0)
        info_time_layout.addLayout(time_layout)
        info_time_layout.addSpacing(-6)
        info_time_layout.addLayout(info_layout)

        vboxlayout.addLayout(info_time_layout)
        vboxlayout.addWidget(self.description_label)
        vboxlayout.addStretch(1)

        scrollarea = self.create_scrollable_area(content_widget)

        self.genre_container.layout().setContentsMargins(self.DEFAULT_MARGIN, self.DEFAULT_MARGIN, self.DEFAULT_MARGIN,
                                                         self.DEFAULT_MARGIN)
        main_vlayout.addWidget(scrollarea)
        main_vlayout.addWidget(self.genre_container)

        layout.addWidget(self.cover_label)
        layout.addLayout(main_vlayout)

        self.title_label.setParent(self.cover_label)
        self.title_label.setMinimumWidth(self.cover_label.width())
        self.title_label.adjustSize()
        self.title_label.move(0, self.cover_label.height() - self.title_label.height() - 9)
        # self.title_label.raise_()

        self.setLayout(layout)
        self.setMaximumHeight(self.cover_label.height())
        self._min_sizeHint.setWidth(self.cover_label.width() * 2)
        self.setMaximumWidth(10000)

        # if isDarkTheme():
        self.genre_container.setStyleSheet(f"background: gray; border-bottom-right-radius: {self.borderRadius}px;")

        self.adjustSize()

    def _init_landscape_layout(self):
        self.cover_label.setFixedSize(self.MINI_COVER_SIZE)
        self.cover_label.setBorderRadius(4, 4, 4, 4)

        self.title_label.max_lines = 2
        self.genre_layout.setContentsMargins(0, 0, 0, 0)
        # self.title_label.setParent(None)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(self.DEFAULT_MARGIN, self.DEFAULT_MARGIN, self.DEFAULT_MARGIN,
                                       self.DEFAULT_MARGIN)
        main_layout.setSpacing(10)

        layout_1 = self.create_vbox(self.title_label, self.genre_container,
                                    alignments=[Qt.AlignBottom, None], spacing=4)

        layout_2 = self.create_vbox(self.rating_widget, self.users_label,
                                    alignments=[Qt.AlignBottom | Qt.AlignHCenter, Qt.AlignTop | Qt.AlignHCenter])

        layout_3 = self.create_vbox(self.time_label, self.status_label,
                                    alignments=[Qt.AlignBottom | Qt.AlignHCenter, Qt.AlignTop | Qt.AlignHCenter])

        layout_4 = self.create_vbox(self.media_type, self.media_episode_chapters,
                                    alignments=[Qt.AlignBottom | Qt.AlignHCenter, Qt.AlignTop | Qt.AlignHCenter])

        main_layout.addWidget(self.cover_label, stretch=0, alignment=Qt.AlignLeft)
        main_layout.addLayout(layout_1, stretch=4)
        main_layout.addLayout(layout_2, stretch=1)
        main_layout.addLayout(layout_4, stretch=1)
        main_layout.addLayout(layout_3, stretch=1)

        self.setLayout(main_layout)
        self.adjustSize()
        margin = main_layout.contentsMargins()

        self.setFixedHeight(self.cover_label.height() + margin.top() + margin.bottom())
        self.setMaximumWidth(10000)

        self.genre_container.setStyleSheet("background: transparent;")

        # self.adjustSize()

    def _init_minimal_layout(self):
        radius = self.borderRadius
        self.cover_label.setFixedSize(self.COVER_SIZE)
        self.cover_label.setBorderRadius(radius, radius, 0, 0)
        self.title_label.max_lines = 1
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 1, 0, self.DEFAULT_MARGIN)
        layout.addWidget(self.cover_label, stretch=1)
        layout.addWidget(self.title_label, alignment=Qt.AlignBottom)
        self.setLayout(layout)

        self.title_label.adjustSize()
        self.setMaximumSize(self.cover_label.width(), self.cover_label.height() + self.title_label.height() + 15)

        self.adjustSize()

    def setData(self, data: AnilistMedia):
        media_id = data.id
        if not id:
            logger.warning(f"Media {media_id} has no ID")

        self.setMediaId(media_id)
        self._media_data = data
        self.setMyAniListId(data.idMal)

        self.setTitle(data.title.romaji or "Unknown Title")
        self.description_label.setText(data.description or "No description available.")

        # Set rating and user count
        score = data.score
        if score:
            average_score = score.average_score or score.mean_score or -1
            self.setRating(average_score)

            favourites = score.favourites or score.popularity or -1
            self.setUsers(favourites)

            # Set status
        info = data.info
        if info:
            status_value = data.info.status
            self.setStatus(status_value)

        # Set airing/publishing years
        start_year = data.startDate.year if data.startDate else None
        end_year = data.endDate.year if data.endDate else datetime.datetime.today().year
        self.setYear(start_year, end_year)

        # Set media type and episode/chapter count
        media_type = data.media_type
        self.setMediaType(media_type)

        count = 0
        count_label = "unknown"
        if media_type == MediaType.MANGA:
            count = data.chapters or -1
            count_label = "chapters"
        elif media_type == MediaType.ANIME:
            count = data.episodes or -1
            count_label = "episodes"
        self.setMediaEpisodeChapters(count, count_label)

        # Set genres


        genres = data.genres
        if genres:
            dominant_color = data.coverImage.color if data.coverImage else None
            if dominant_color:
                dominant_color = QColor(dominant_color)
                # logger.critical(f"Media has  dominant color: {dominant_color}")
            else:
                dominant_color = ThemeColor.PRIMARY.color()
            self.setGenre(data.genres or [], dominant_color)


        # Debug info
        # print(f"{count} {count_label}, {favourites} users, {average_score} score, status: {status_value}")
    def setMediaId(self, media_id: int):
        self._media_id = media_id

    def setMyAniListId(self, mal_media_id: int):
        self._mal_id = mal_media_id

    def setTitle(self, title, hover_color: QColor = None):
        if title is None:
            return
        self.title_label.setText(title)
        if self.variant == MediaVariants.WIDE_LANDSCAPE:
            self.title_label.setParent(self.cover_label)
            self.title_label.setMinimumWidth(self.cover_label.width())
            self.title_label.adjustSize()
            self.title_label.move(0, self.cover_label.height() - self.title_label.height() - 9)
        # qss = f"SubtitleLabel {{ color: gray; }} SubtitleLabel:hover {{ color: {hover_color.name()}; }}"
        # setCustomStyleSheet(self.title_label, qss, qss)

    def setDescription(self, description: str):
        if description is None:
            return
        self.description_label.setText(description)

    def setRating(self, rating: int):
        if rating is None:
            return
        self.rating_label.setText(f"{rating}%" if rating > 0 else "??%")
        if rating >= 75:
            color = QColor("green")
            str_icon = "\uf118"
        elif rating >= 50:
            color = QColor("orange")
            str_icon = "\uf11a"
        elif rating >= 0:
            color = QColor("red")
            str_icon = "\uf119"
        else:
            color = QColor("orange")
            str_icon = "\uf11a"
        self.rating_icon.setIcon(FontAwesomeRegularIcon(str_icon).colored(color, color))

    def setUsers(self, users: int):
        if users is None:
            return
        users = f"{users} users" if users > 0 else "unknown"
        self.users_label.setText(users)

    def setStatus(self, status: Union[str, MediaStatus]):
        if status is None:
            return
        if isinstance(status, MediaStatus):
            if status == MediaStatus.RELEASING:
                status = "Airing"
            elif status == MediaStatus.FINISHED:
                status = "Completed"
            else:
                status = status.value
        self.status_label.setText(status)

    def setYear(self, start_year: int, end_year: int):
        if start_year is None or end_year is None:
            return
        self.start_year = start_year
        self.end_year = end_year
        start_year = start_year if start_year > 0 else "????"
        end_year = end_year if end_year > 0 else "????"
        self.time_label.setText(f"{start_year}-{end_year}")

    def setMediaType(self, media_type: MediaType):
        if media_type is None:
            return
        self.media_type.setText(media_type.value)

    def setMediaEpisodeChapters(self, value: int, value_type: str):
        if value_type is None or value is None:
            return
        value = value if value >= 0 else "???"
        self.media_episode_chapters.setText(f"{value} {value_type}")

    def setCover(self, cover: Union[Path, QPixmap]):
        if cover is None:
            return
        self.cover_label.setImage(cover)
        if self.variant == MediaVariants.LANDSCAPE:
            self.cover_label.setScaledSize(self.MINI_COVER_SIZE)
        else:
            self.cover_label.setScaledSize(self.COVER_SIZE)

    def setGenre(self, genres: List[Union[str, MediaGenre]], color: QColor = ThemeColor.PRIMARY.color()):
        if genres is None or len(genres) == 0:
            return
        self.genres = genres
        self._create_genre(color)

    def setProgress(self, progress: float):
        if progress is None:
            return

    def minimumSizeHint(self, /):
        return self._min_sizeHint

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.position()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self._press_pos:
            release_pos = event.position()
            distance = (release_pos - self._press_pos).manhattanLength()

            if distance < self._drag_threshold:
                print("Mouse Clicked!")
                self.cardClicked.emit(self._media_id, self._media_data)
                # handle your click action here
            else:
                print("Drag detected, ignoring click.")
        self._press_pos = None
        super().mouseReleaseEvent(event)


class MediaRelationCard(CardWidget):
    COVER_SIZE = QSize(195, 270)
    Title_FONT_SIZE = 17
    TILE_FONT_WEIGHT = QFont.Weight.DemiBold

    BODY_FONT_WEIGHT = QFont.Weight.Normal
    STRONG_BODY_FONT_WEIGHT = QFont.Weight.DemiBold
    BODY_FONT_SIZE = 14

    def __init__(self, parent=None):
        super().__init__(parent)



        self.cover_label = WaitingLabel()
        self.cover_label.setFixedSize(self.COVER_SIZE)
        self.cover_label.start()

        self.title_label = MyLabel("This is title", self.Title_FONT_SIZE, self.TILE_FONT_WEIGHT)
        self.body_label = MyLabel("Side Story", self.BODY_FONT_SIZE, self.BODY_FONT_WEIGHT)

        # overlay
        self.overlay_widget = SimpleCardWidget(self)
        layout = QVBoxLayout(self.overlay_widget)
        layout.setSpacing(0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.body_label)

        self.overlay_widget.raise_()

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 0)
        layout.addWidget(self.cover_label)

    def setTitle(self, title: str):
        self.title_label.setText(title)

    def setBody(self, body: str):
        self.body_label.setText(body)

    def setCover(self, cover: Union[str, QImage, QPixmap, Path]):
        self.cover_label.setImage(cover)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.overlay_widget.adjustSize()
        self.overlay_widget.setFixedWidth(self.width())
        self.overlay_widget.move(0, self.height() - self.overlay_widget.height())

        self.overlay_widget.raise_()




# Example usage
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MediaCard(MediaVariants.LANDSCAPE)
    genres = [MediaGenre.ACTION, MediaGenre.ROMANCE, MediaGenre.ADVENTURE]
    color = QColor.fromRgbF(0.839216, 0.262745, 0.101961, 1.000000)

    data = AnilistMedia(
        id = 1,
        title=AnilistTitle("2", "2", "2"),
        genres=genres,
        coverImage= MediaCoverImage(color = color.name())
    )
    test = QColor(color.name())
    print(test)
    ex.setData(data)
    ex.show()
    sys.exit(app.exec())


