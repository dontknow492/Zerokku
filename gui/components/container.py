from collections import deque
from pathlib import Path
from typing import List, Any, Tuple, Union, Callable, Optional, Dict, Type, Deque

import sys
from PIL.ImageQt import QPixmap
from PySide6 import QtAsyncio
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QPoint
from PySide6.QtGui import QCloseEvent, QResizeEvent
from PySide6.QtWidgets import QApplication, QWidget, QButtonGroup, QVBoxLayout, QHBoxLayout, QGridLayout, \
    QStackedWidget, QSpacerItem, QSizePolicy, QLayout

from AnillistPython import AnilistMedia, parse_searched_media
from gui.common import KineticScrollArea, ResponsiveLayout, EnumComboBox, AnimationManager, AnimationDirection, \
    DynamicGridLayout, SlideAniStackedWidget, AniStackedWidget, MyLabel, RoundedToolButton
from gui.components import MediaCardSkeletonLandscape, MediaCardSkeletonMinimal, MediaCardSkeletonDetailed, \
    MediaCard, MediaVariants
from qfluentwidgets import TransparentToggleToolButton, FluentIcon, PrimaryPushButton, FlowLayout, TransparentPushButton
from loguru import logger

from core import ImageDownloader

from utils import IconManager

from enum import Enum

from qasync import QEventLoop, asyncSlot, asyncClose
import asyncio

class MediaSort(Enum):
    TITLE = "TITLE"
    POPULARITY = "POPULARITY"
    AVERAGE_SCORE = "AVERAGE_SCORE"
    TRENDING = "TRENDING"
    FAVORITES = "FAVORITES"
    DATA_ADDED = "DATA_ADDED"

class BaseMediaContainer(QWidget):
    requestCover = Signal(str)
    cardLoaded = Signal()
    cardLoadingCanceled = Signal()
    SkeletonType: Type[QWidget] = MediaCardSkeletonMinimal
    LayoutType: Type[QLayout] = QVBoxLayout
    Variant: MediaVariants = MediaVariants.PORTRAIT
    CHUNK_SIZE: int = 10

    chunk_loaded = Signal()
    cardClicked = Signal(int, object)

    def __init__(self, skeletons: int = 7, parent=None):
        super().__init__(parent)
        self._data_queue: Deque[Union[List[AnilistMedia], List[MediaCard]]] = deque()
        self._chunk_index = None
        self._chunk_data = None
        self._is_chunk_loading = False
        self.cards: List[MediaCard] = []
        self.card_pixmap_map: Dict[str, MediaCard] = {}
        self.pixmap_card_map: Dict[MediaCard, str] =  {} #reverse look up
        self.skeletons = [self.SkeletonType() for _ in range(skeletons)]
        self.container_layout = self.LayoutType()
        self.setLayout(self.container_layout)

        self._cancel_loading_flag = False
        self._chunk_timer = QTimer()
        self._chunk_timer.setInterval(100)
        self._chunk_timer.setSingleShot(True)

        self.show_all_skeletons()





    def _signal_handler(self):
        self.chunk_loaded.connect(self._on_chunk_finished)

    def show_all_skeletons(self):
        for skeleton in self.skeletons:
            self.show_skeleton(skeleton)

    def hide_all_skeletons(self, remove: bool = False, delete: bool = False):
        for skeleton in self.skeletons:
            self.hide_skeleton(skeleton, remove, delete)

    def show_skeleton(self, skeleton: QWidget):
        if hasattr(skeleton, "start"):
            skeleton.start()

        if skeleton.parent() is None:
            self.addWidget(skeleton)
        skeleton.setVisible(True)

    def hide_skeleton(self, skeleton: QWidget, remove: bool = False, delete: bool = False):
        if hasattr(skeleton, "stop"):
            skeleton.stop()
        skeleton.setVisible(False)
        if remove:
            self.remove_skeleton(skeleton, delete)

    def remove_skeleton(self, skeleton: QWidget, delete: bool = False):
        try:
            self.removeWidget(skeleton, delete)
        except Exception as e:
            logger.exception(f"Error occurred while removing skeleton: {e}")

    def add_download(self, url: str, card: MediaCard):
        if not url or not card:
            return
        self.card_pixmap_map[url] = card
        self.pixmap_card_map[card] = url
        self.requestCover.emit(url)

    def on_download_finished(self, url: str, pixmap: QPixmap, path: Path):
        if card := self.card_pixmap_map.pop(url, None):
            self.pixmap_card_map.pop(card, None) #removing from reverse map
            if pixmap.isNull():
                card.setCover(path)
            else:
                card.setCover(pixmap)



    def add_medias(self, data: List[AnilistMedia]):
        """Starts chunked creation and insertion of media cards."""
        logger.debug(f"Received {len(data)} media items for lazy loading")
        self._data_queue.append(data)
        self._start_next_chunk()

    def add_cards(self, cards: List[MediaCard]):
        """Adds a batch of media cards to the layout."""
        logger.debug(f"Adding {len(cards)} cards starting at index {len(self.cards)}")
        self._data_queue.append(cards)
        self._start_next_chunk()

    def _start_next_chunk(self):
        logger.debug(f"Starting next chunk: {len(self._data_queue)}")
        if not self._data_queue:
            logger.debug(f"Data queue is empty.")
            self.cardLoaded.emit()
            return
        if self._is_chunk_loading:
            logger.debug(f"Task already running, adding it in queue:")

        next_data = self._data_queue.popleft()
        self._is_chunk_loading = True
        self._start_chunk_loading(next_data)

    def _on_chunk_finished(self):
        self._is_chunk_loading = False
        self._start_next_chunk()

    def _start_chunk_loading(self, data: Union[List[MediaCard], List[AnilistMedia]]):
        self._cancel_loading_flag = False
        self._chunk_index = 0
        self._chunk_data = data

        def process_chunk():
            if self._cancel_loading_flag:
                logger.debug("Chunk loading cancelled")
                self.cardLoadingCanceled.emit()
                return

            self.setUpdatesEnabled(False)
            self.setVisible(False)

            start_index = self._chunk_index
            end_index = min(start_index + self.CHUNK_SIZE, len(self._chunk_data))
            chunk = self._chunk_data[start_index:end_index]
            logger.debug(f"Processing chunk: {start_index} to {end_index} ({len(chunk)} cards)")

            for media in chunk:
                if self._cancel_loading_flag:
                    logger.debug("Chunk loading cancelled during card processing")
                    self.cardLoadingCanceled.emit()
                    self._finalize_chunk_loading()
                    return
                if isinstance(media, AnilistMedia):
                    card = self._create_card(media)
                else:
                    card = media
                card.set_variant(self.Variant)
                self.insertWidget(len(self.cards), card)

            self._chunk_index = end_index
            if self._chunk_index < len(self._chunk_data) and not self._cancel_loading_flag:
                self._finalize_chunk_loading()
                self._chunk_timer.start()
            else:
                self.chunk_loaded.emit()
                logger.debug(f"All chunks processed or loading cancelled: {len(self._data_queue)}")
                self._start_next_chunk()
            self._finalize_chunk_loading()

        self._reset_chunk_timer(process_chunk)
        self._chunk_timer.start()

    def _finalize_chunk_loading(self):
        self.setVisible(True)
        self.setUpdatesEnabled(True)

    def _reset_chunk_timer(self, callback: Callable):
        """(Re)initializes the chunk processing QTimer."""
        if hasattr(self, "_chunk_timer") and self._chunk_timer:
            self._chunk_timer.stop()
            self._chunk_timer.deleteLater()
        self._chunk_timer = QTimer(self)
        self._chunk_timer.setInterval(100)
        self._chunk_timer.setSingleShot(True)
        self._chunk_timer.timeout.connect(callback)

    def cancel_chunk_loading(self):
        logger.debug(f"Cancelling chunk loading at: {len(self.cards)} card")
        self._cancel_loading_flag = True
        if hasattr(self, "_chunk_timer") and self._chunk_timer:
            self._chunk_timer.stop()
            self._is_chunk_loading = False


    def _create_card(self, media: AnilistMedia) -> MediaCard:
        logger.trace(f"Creating media card for: {media.title.romaji}")
        card = MediaCard(self.Variant)
        card.cardClicked.connect(self.cardClicked.emit)
        card.setData(media)
        self.add_download(media.coverImage.large, card)
        return card

    def addWidget(self, card: Union[MediaCard, QWidget]):
        if isinstance(card, MediaCard):
            self.cards.append(card)
        self.container_layout.addWidget(card)

    def insertWidget(self, index: int, card: MediaCard):
        # self.setUpdatesEnabled(False)
        # self.setVisible(False)
        if isinstance(card, MediaCard):
            self.cards.append(card)
        # self.container_layout.addWidget(card)
        self.container_layout.insertWidget(index, card)
        # self.setUpdatesEnabled(True)
        # self.setVisible(True)

    def setSpacing(self, spacing: int):
        self.container_layout.setSpacing(spacing)

    def remove_medias(self, is_delete: bool = False) -> List[MediaCard]:
        """Remove all media cards from the layout.

        :param is_delete: If True, deletes the media cards.
        :return: List of removed MediaCard instances.
        """
        self.clear_queue()
        self.cancel_chunk_loading()
        removed_cards = []
        while len(self.cards):
            card = self.cards.pop()
            self.removeWidget(card, is_delete)
            removed_cards.append(card)

        self.card_pixmap_map.clear() # map clean
        return removed_cards

    def removeWidget(self, widget: QWidget, is_delete: bool = False):
        # Remove from layout
        self.container_layout.removeWidget(widget)

        # Clean up from tracking structures
        if isinstance(widget, MediaCard):
            try:
                self.cards.remove(widget)
            except ValueError:
                pass

            # Remove from reverse map and forward map
            url = self.pixmap_card_map.pop(widget, None)
            if url:
                self.card_pixmap_map.pop(url, None)

        # Unparent and optionally schedule deletion
        widget.setParent(None)

        if is_delete:
            widget.deleteLater()

    def setChunkSize(self, size: int):
        self.CHUNK_SIZE = max(2, size)

    def getChunkSize(self) -> int:
        return self.CHUNK_SIZE

    def clear_queue(self):
        self._data_queue.clear()
        logger.info("Cleared pending data queue.")

    # def cancel_chunk_loading(self):
    #     logger.debug("Cancelling chunk loading")
    #     self._cancel_loading_flag = True
    #     if hasattr(self, "_chunk_timer") and self._chunk_timer:
    #         self._chunk_timer.stop()


class LandscapeContainer(BaseMediaContainer):
    SkeletonType = MediaCardSkeletonLandscape
    LayoutType = QVBoxLayout
    Variant = MediaVariants.LANDSCAPE
    CHUNK_SIZE = 5

class PortraitContainer(BaseMediaContainer):
    SkeletonType = MediaCardSkeletonMinimal
    LayoutType = FlowLayout
    Variant = MediaVariants.PORTRAIT
    CHUNK_SIZE = 5

    def setSpacing(self, spacing: int):
        self.setHorizontalSpacing(spacing)
        self.setVerticalSpacing(spacing)

    def setHorizontalSpacing(self, horizontalSpacing: int):
        self.container_layout.setHorizontalSpacing(horizontalSpacing)

    def setVerticalSpacing(self, verticalSpacing: int):
        self.container_layout.setVerticalSpacing(verticalSpacing)

class WideLandscapeContainer(BaseMediaContainer):
    SkeletonType = MediaCardSkeletonDetailed
    LayoutType = QGridLayout
    Variant = MediaVariants.WIDE_LANDSCAPE  # or MediaVariants.WIDE_LANDSCAPE, if you have one
    CHUNK_SIZE = 5
    def __init__(self, skeletons: int = 4, parent=None, columns: int = 2):
        self._grid_columns = columns
        self._grid_index = 0  # tracks next available slot
        super().__init__(skeletons, parent)

    def _get_grid_position(self, index: int) -> tuple[int, int]:
        row = index // self._grid_columns
        col = index % self._grid_columns
        return row, col

    def addWidget(self, card: Union[MediaCard, QWidget]):
        if isinstance(card, MediaCard):
            self.cards.append(card)
        row, col = self._get_grid_position(self._grid_index)
        self.container_layout.addWidget(card, row, col)
        self._grid_index += 1

    def insertWidget(self, index: int, card: MediaCard):
        if isinstance(card, MediaCard):
            self.cards.append(card)
        row, col = self._get_grid_position(index)
        self.safe_add_to_grid(card, row, col)
        self._grid_index = max(self._grid_index, index + 1)

    def safe_add_to_grid(self, widget: QWidget, row: int, col: int):
        item = self.container_layout.itemAtPosition(row, col)
        if item is not None:
            old_widget = item.widget()
            if old_widget is not None:
                self.container_layout.removeWidget(old_widget)
                old_widget.setVisible(True)  # keep it visible if needed
                # Re-add at the end (row++, col=0) or any designated area
                last_row = self.container_layout.rowCount()
                self.container_layout.addWidget(old_widget, last_row,0)

        self.container_layout.addWidget(widget, row, col)

        self.container_layout.addWidget(widget, row, col)

    def setSpacing(self, spacing: int):
        self.setHorizontalSpacing(spacing)
        self.setVerticalSpacing(spacing)

    def setHorizontalSpacing(self, horizontalSpacing: int):
        self.container_layout.setHorizontalSpacing(horizontalSpacing)

    def setVerticalSpacing(self, verticalSpacing: int):
        self.container_layout.setVerticalSpacing(verticalSpacing)


class ViewMoreContainer(QWidget):
    seeMoreSignal = Signal()
    cardClicked = Signal(int, object)
    requestCover = Signal(str)
    MAX_CARDS = 25
    MAX_SKELETON = 10
    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self.variant = MediaVariants.PORTRAIT
        self.cards: List[MediaCard] = list()
        self.card_pixmap_map: Dict[str, MediaCard] = dict()
        self._media_data: List[AnilistMedia] = list()
        self._media_index = 0
        self._batch_size = 12
        self._card_width = 195


        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(6)
        titlelayout = QHBoxLayout()
        titlelayout.setContentsMargins(0, 0, 0, 0)

        self.title_label = MyLabel(text=title, font_size=20, parent=self)
        self.more_button = TransparentPushButton(FluentIcon.RIGHT_ARROW, "See more", self)
        self.more_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.more_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.more_button.setEnabled(False)
        titlelayout.addWidget(self.title_label)
        titlelayout.addStretch(1)
        titlelayout.addWidget(self.more_button, alignment=Qt.AlignmentFlag.AlignBottom)

        self.scrollarea = KineticScrollArea(self)
        self.scrollarea.setStyleSheet("background-color: transparent;")
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # central_widget.setFrameShape(QFrame.Shape.NoFrame)

        self.card_container = QWidget(self)
        self.container_layout = QHBoxLayout(self.card_container)
        self.container_layout.setSpacing(30)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.scrollarea.setWidget(self.card_container)
        self.scrollarea.setWidgetResizable(True)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.container_layout.addItem(self.spacer)

        layout.addLayout(titlelayout)
        layout.addWidget(self.scrollarea)

        self._current_cards = 0

        self._skeletons: List[MediaCardSkeletonMinimal] = list()

        self._create_skeletons()

        # scrollbar
        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self._handle_scroll_timeout)

        self.scrollarea.horizontalScrollBar().valueChanged.connect(self._onScroll)

        #overlay
        button_size = QSize(48, 48)
        icon_size = QSize(20, 20)
        button_radius = button_size.width() // 2
        self.next_button = self._create_button(FluentIcon.RIGHT_ARROW, button_size, icon_size,Qt.CursorShape.PointingHandCursor, "Next")
        self.next_button.clicked.connect(self._on_next)
        self.next_button.setEnabled(False)
        self.previous_button = self._create_button(FluentIcon.LEFT_ARROW, button_size, icon_size, Qt.CursorShape.PointingHandCursor, "Previous")
        self.previous_button.clicked.connect(self._on_previous)
        self.previous_button.setEnabled(False)

    def _create_button(self, icon, button_size, icon_size, cursor, tooltip):
        button = RoundedToolButton(icon, self)
        button.setFixedSize(button_size)
        button.setRadius(button_size.width() // 2)
        button.setCursor(cursor)
        button.setIconSize(icon_size)
        button.setToolTip(tooltip)

        return button

    def add_download(self, url: str, card: MediaCard):
        if url is None or card is None:
            logger.warning(f"Url and card cannot be None: url - {url}, card - {card}")
            return
        self.card_pixmap_map[url] = card
        self.requestCover.emit(url)

    def on_download_finished(self, url: str, pixmap: QPixmap, path: Path) -> None:
        if card := self.card_pixmap_map.pop(url, None):
            if pixmap.isNull():
                card.setCover(path)
            else:
                card.setCover(pixmap)

    def scrollTo(self, value: Union[int, QPoint], duration: int = 0):
        if isinstance(value, int):
            value = QPoint(value, 0)
        self.scrollarea.scrollTo(value, duration)

    def _on_next(self):
        if self.scrollarea.horizontalScrollBar().value() == self.scrollarea.horizontalScrollBar().maximum():
            return
        widget = self.get_first_visible_widget()
        value = widget.width() + self.container_layout.spacing() + widget.x()
        print(value, type(widget), isinstance(widget, MediaCard))
        self.scrollTo(value, 300)

    def _on_previous(self):
        if self.scrollarea.horizontalScrollBar().value() == self.scrollarea.horizontalScrollBar().minimum():
            return
        widget = self.get_first_visible_widget()
        value = widget.x() - widget.width() - self.container_layout.spacing()
        print(value, type(widget), isinstance(widget, MediaCard))
        self.scrollTo(value, 300)

    def get_first_visible_widget(self):
        viewport = self.scrollarea.viewport()
        scroll_x = self.scrollarea.horizontalScrollBar().value()

        for widget in self.scrollarea.findChildren(MediaCard):
            if not widget.isVisible():
                continue

            pos = widget.mapTo(viewport, QPoint(0, 0))

            # Check if any part of the widget is visible horizontally
            if pos.x() + widget.width() >= 0:
                return widget

        return None

    def get_last_visible_widget(self):
        viewport = self.scrollarea.viewport()
        viewport_width = viewport.width()
        last_visible = None

        for widget in self.scrollarea.findChildren(MediaCard):
            if not widget.isVisible():
                continue

            pos = widget.mapTo(viewport, QPoint(0, 0))
            right_edge = pos.x() + widget.width()

            # Check if any part is visible within the viewport bounds
            if pos.x() < viewport_width and right_edge > 0:
                last_visible = widget

        return last_visible

    def _onScroll(self, value):
        logger.trace("Scroll event triggered")
        if not len(self._media_data) or value < self.scrollarea.horizontalScrollBar().minimum() + 30:
            self.previous_button.setEnabled(False)
        elif not len(self._media_data) or value > self.scrollarea.horizontalScrollBar().maximum() - 30:
            self.next_button.setEnabled(False)
        else:
            self.next_button.setEnabled(True)
            self.previous_button.setEnabled(True)
        self.scroll_timer.start(100)

    def _handle_scroll_timeout(self):
        logger.debug("Scroll debounce timeout")
        if self.scrollarea.horizontalScrollBar().value() >= self.scrollarea.horizontalScrollBar().maximum() - 500:
            logger.debug("User scrolled near bottom, updating view")
            self._load_batch()

    def _create_skeletons(self):
        for _ in range(self._batch_size):
            skeleton = MediaCardSkeletonMinimal()
            skeleton.start()
            self._skeletons.append(skeleton)
            self.container_layout.addWidget(skeleton)

    def add_medias(self, data: List[AnilistMedia]):
        logger.debug(f"Data added: {len(data)}")
        self._media_data = data[:self.MAX_CARDS]
        self._media_index = 0
        self._load_batch()
        self.next_button.setEnabled(True)
        self.more_button.setEnabled(True)


    def _load_batch(self):
        end = min(self._media_index + self._batch_size, len(self._media_data))
        logger.debug(f"Loading media batch: {self._media_index} to {end}")
        for index, media in enumerate(self._media_data[self._media_index:end], start = self._media_index):
            self._create_card(media, index)

        self._media_index = end
        logger.debug(f"Setting media index to '{self._media_index}' for next batch")

    def _create_card(self, data: AnilistMedia, index: int):
        logger.trace(f"Adding media card at index {index}")
        card = MediaCard(self.variant)
        card.setData(data)
        card.cardClicked.connect(self.cardClicked.emit)
        url = data.coverImage.large
        self.cards.append(card)
        self.addWidget(card, index)

        self.add_download(url, card)

    def addWidget(self, card: MediaCard, index: int):
        #skeleton
        if index < len(self._skeletons):
            item = self._skeletons[index]
            item.setVisible(False)
            item.stop()
        self.container_layout.insertWidget(index, card)


    def get_batch_size(self):
        return self._batch_size

    def stop_skeletons(self):
        logger.debug("Stopping skeletons")
        for skeleton in self._skeletons:
            skeleton.stop()

    def start_skeletons(self):
        logger.debug("Starting skeletons")
        for skeleton in self._skeletons:
            skeleton.start()


    def resizeEvent(self, event: QResizeEvent):
        # logger.debug(f"Resize event triggered")
        height = (self.scrollarea.height() - self.previous_button.height())//2 + self.scrollarea.y()
        offset_height = self.scrollarea.y()
        self.previous_button.move(0, height)
        self.next_button.move(self.width() - self.next_button.width(), height)

class FilterNavigation(QWidget):
    variantChanged = Signal(MediaVariants)
    def __init__(self, variant: MediaVariants, parent=None):
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


        #init ui
        # self.main_layout.addWidget(sort_combo, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(portrait_view_button)
        self.main_layout.addWidget(landscape_view_button)
        self.main_layout.addWidget(gird_view_button)

    def add_chip(self, type: str, value: str, icon = FluentIcon.TAG):
        logger.info(f"Adding chip '{type}': '{value}' to filter navigation")
        name = f"{type}: {value}"
        button = PrimaryPushButton(icon, name, self)
        self.chips[name] = button
        self.main_layout.insertWidget(0, button, alignment=Qt.AlignmentFlag.AlignLeft)
        button.clicked.connect(lambda: self.remove_chip(type, value))

    def remove_chip(self, type: str, value: str):
        name = f"{type}: {value}"
        button = self.chips.get(name, None)
        if button:
            self.main_layout.removeWidget(button)
            button.deleteLater()


class CardContainer(QWidget):
    BATCH_SIZE = 10
    switching = Signal()
    switchingFinished = Signal()
    endReached = Signal()
    requestCover = Signal(str) #url
    cardClicked = Signal(int, object)
    def __init__(self, variant: MediaVariants = MediaVariants.PORTRAIT, batch_size: int = 10, parent=None):
        super().__init__(parent)
        logger.info(f"Initializing CardContainer with variant: {variant.name}")
        self._screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.animation_manager = AnimationManager()
        self._has_more = False
        self._waiting_for_more = False
        self.cards: List[MediaCard] = list()
        self.card_pixmap_map: Dict[str, MediaCard] = dict()
        self._media_data: List[AnilistMedia] = list()
        self._media_index = 0
        self.BATCH_SIZE = batch_size
        self.is_skeleton = False
        self.previous_variant = variant
        self.variant = variant


        # self.filter_navigation = FilterNavigation(variant, self)
        # self.filter_navigation.add_chip("Search", "abc")

        self.view_stack = AniStackedWidget(self)

        spacing = 32
        self.portrait_container = PortraitContainer(skeletons = 12, parent=self)
        self.portrait_container.setSpacing(spacing)
        self.landscape_container = LandscapeContainer(skeletons=10, parent=self)
        self.landscape_container.setSpacing(spacing)
        self.wide_landscape_container = WideLandscapeContainer(skeletons=4, parent=self)
        self.wide_landscape_container.setSpacing(spacing)


        self.portrait_scrollArea = self.create_view(self.portrait_container)
        self.landscape_scrollArea = self.create_view(self.landscape_container)
        self.wide_landscape_scrollArea = self.create_view(self.wide_landscape_container)


        self.view_stack.addWidget(self.portrait_scrollArea)
        self.view_stack.addWidget(self.landscape_scrollArea)
        self.view_stack.addWidget(self.wide_landscape_scrollArea)

        self.variant_map = {
            MediaVariants.PORTRAIT: [self.portrait_scrollArea, self.portrait_container],
            MediaVariants.LANDSCAPE: [self.landscape_scrollArea, self.landscape_container],
            MediaVariants.WIDE_LANDSCAPE: [self.wide_landscape_scrollArea, self.wide_landscape_container],
        }

        self.view_stack.setCurrentWidget(self.get_variant_view(variant))

        layout = QVBoxLayout(self)
        # layout.addWidget(self.filter_navigation)
        layout.addWidget(self.view_stack, stretch=1)

        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self._handle_scroll_timeout)

        self._signal_handler()

    def create_view(self, central_widget):
        scroll_area = KineticScrollArea(self)
        scroll_area.setStyleSheet("""
            KineticScrollArea, KineticScrollArea QWidget {
                background-color: transparent;
                
            }
        """)
        central_widget.setContentsMargins(0, 0, 0, 0)
        scroll_area.setWidget(central_widget)
        scroll_area.setWidgetResizable(True)
        return scroll_area

    def _signal_handler(self):
        # self.filter_navigation.variantChanged.connect(self.switch_view)
        self.portrait_scrollArea.verticalScrollBar().valueChanged.connect(self._onScroll)
        self.landscape_scrollArea.verticalScrollBar().valueChanged.connect(self._onScroll)
        self.wide_landscape_scrollArea.verticalScrollBar().valueChanged.connect(self._onScroll)

        #cover
        self.portrait_container.requestCover.connect(self.requestCover.emit)
        self.landscape_container.requestCover.connect(self.requestCover.emit)
        self.wide_landscape_container.requestCover.connect(self.requestCover.emit)

        #cardclick
        self.portrait_container.cardClicked.connect(self.cardClicked.emit)
        self.landscape_container.cardClicked.connect(self.cardClicked.emit)
        self.wide_landscape_container.cardClicked.connect(self.cardClicked.emit)

    def show_loading(self):
        self.portrait_container.show_all_skeletons()
        self.landscape_container.show_all_skeletons()
        self.wide_landscape_container.show_all_skeletons()

    def hide_loading(self):
        self.portrait_container.hide_all_skeletons(False, False)
        self.landscape_container.hide_all_skeletons(False, False)
        self.wide_landscape_container.hide_all_skeletons(False, False)

    def on_cover_downloaded(self, url, pixmap, path):
        self.portrait_container.on_download_finished(url, pixmap, path)
        self.landscape_container.on_download_finished(url, pixmap, path)
        self.wide_landscape_container.on_download_finished(url, pixmap, path)

    def scrollTo(self, pos: QPoint, duration: int = 0):
        view = self.get_variant_view(self.variant)
        view.scrollTo(pos, duration)

    def _onScroll(self, value):
        logger.trace("Scroll event triggered")
        self.scroll_timer.start(100)

    def _handle_scroll_timeout(self):
        logger.debug("Scroll debounce timeout")
        view = self.get_variant_view(self.variant)
        scrollbar = view.verticalScrollBar()
        if scrollbar.value() >= scrollbar.maximum() - self._screen_geometry.height() // 2:
            logger.debug("User scrolled near bottom, updating view")
            self._load_next_batch()
            # self._update_view(self.previous_variant, self.variant)

    def switch_view(self, variant: MediaVariants):
        view = self.get_variant_view(variant)
        self.view_stack.setCurrentWidget(view)
        if len(self._media_data):
            QTimer.singleShot(400, lambda: self.switch_cards(self.previous_variant, variant))

        self.previous_variant = self.variant
        self.variant = variant #updating variant flag

    def add_medias(self, data: List[AnilistMedia], is_increment=True):
        logger.info(f"Adding {'more' if is_increment else 'new'} media items: {len(data)}")
        if is_increment:
            self._media_data.extend(data)
        else:
            self._media_index = 0
            self._media_data = data
            # self.remove_cards(True)
            self.scrollTo(QPoint(0, 0), 100) #reseting scroll
        self._load_next_batch()
        # QTimer.singleShot(50, self._check_scroll_and_continue)

    def remove_cards(self, delete: bool):
        current_container = self.get_variant_container(self.variant)
        current_container.remove_medias(delete)

    def _load_next_batch(self):
        batch_size = self.get_batch_size()
        start = self._media_index
        end = min(start + batch_size, len(self._media_data))
        logger.debug(f"Loading media batch: {start} to {end}")
        # for index, media in enumerate(self._media_data[start:end], start=start):
        #     self.addMedia(media, index)
        current_container = self.get_variant_container(self.variant)
        current_container.add_medias(self._media_data[start:end])

        self._media_index = end
        logger.debug(f"Next media index set to {self._media_index}")
        if self._media_index >= len(self._media_data):
            self.endReached.emit()

    def switch_cards(self, previous_variant: MediaVariants, next_variant: MediaVariants):
        if previous_variant == next_variant:
            logger.debug(f"Previous variant and next variant are equal: {previous_variant.name}")
            return
        try:
            self.switching.emit()
            # self.filter_navigation.setEnabled(False)
            previous_container = self.get_variant_container(previous_variant)
            next_container = self.get_variant_container(next_variant)
            next_container.cardLoaded.connect(self.switchingFinished.emit)

            cards = previous_container.remove_medias(False)
            cards.reverse()
            #todo: add if loaded card is less then batch size, then add media
            batch_size = self.get_batch_size()
            logger.debug(f"Adding cards: {len(cards)}")
            if len(cards) == 0:
                return
            elif len(cards) < batch_size:
                next_container.add_cards(cards)
                medias = self._media_data[len(cards):batch_size]
                QTimer.singleShot(10, lambda: next_container.add_medias(medias))
                # next_container.add_medias
            elif len(cards) >= batch_size:
                next_container.add_cards(cards)

        except Exception as e:
            logger.error(e)





    def get_batch_size(self):
        return self.BATCH_SIZE

    def get_variant_view(self, variant: MediaVariants):
        return self.variant_map[variant][0]

    def get_variant_container(self, variant: MediaVariants)->BaseMediaContainer:
        return self.variant_map[variant][1]



def main():
    import json
    with open(r"D:\Program\Zerokku\demo\data.json", "r", encoding="utf-8") as data:
        result = json.load(data)
    cards = parse_searched_media(result, None)

    # cards.extend(cards)
    # cards.extend(cards)
    print(len(cards))

    app = QApplication(sys.argv)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    # main_window = ViewMoreContainer("Trending")
    # main_window = LandscapeContainer()
    # main_window = PortraitContainer()
    # main_window = WideLandscapeContainer()
    main_window = CardContainer()
    main_window.hide_loading()
    main_window.show()
    main_window.endReached.connect(lambda: QTimer.singleShot(2000, lambda: main_window.add_medias(cards)))
    # main_window._batch_size = 80

    QTimer.singleShot(2000, lambda: main_window.add_medias(cards))

    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())


if __name__ == '__main__':
    main()



