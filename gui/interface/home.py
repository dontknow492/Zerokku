import sys
from enum import Enum, auto
from typing import List, Union

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QMouseEvent
from PySide6.QtWidgets import QWidget, QFrame, QApplication, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, \
    QScrollBar, QStyle, QStyleOptionFocusRect, QStyleOptionSlider
from loguru import logger
from qfluentwidgets import TitleLabel, TransparentPushButton, FluentIcon, SubtitleLabel, Theme, setTheme, \
    SmoothScrollBar, ScrollBar

from gui.common import KineticScrollArea, MyLabel
from gui.common.mylabel import SkeletonMode
from gui.components import MediaCard, MediaVariants, MediaCardSkeletonMinimal, HeroContainerSkeleton, \
    MediaCardSkeletonLandscape


class HeroContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.skeleton = HeroContainerSkeleton(self)
        # self.skeleton.setFixedSize(self.size())

    def resizeEvent(self, event):
        self.skeleton.setFixedSize(self.size())

    def start(self):
        self.skeleton.start()

class Container(QWidget):
    seeMoreSignal = Signal()
    cardClickedSignal = Signal()

    MAX_CARDS = 7
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        titlelayout = QHBoxLayout()
        titlelayout.setContentsMargins(0, 0, 0, 0)

        self.title_label = MyLabel(text = title, font_size=20, parent = self)
        self.more_button = TransparentPushButton(FluentIcon.RIGHT_ARROW, "See more", self)
        self.more_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.more_button.setCursor(Qt.CursorShape.PointingHandCursor)
        titlelayout.addWidget(self.title_label)
        titlelayout.addStretch(1)
        titlelayout.addWidget(self.more_button, alignment=Qt.AlignmentFlag.AlignBottom)

        central_widget = KineticScrollArea(self)
        central_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        central_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # central_widget.setFrameShape(QFrame.Shape.NoFrame)

        self.card_container = QWidget(self)
        self.container_layout = QHBoxLayout(self.card_container)
        self.container_layout.setSpacing(30)
        self.container_layout.setContentsMargins(9, 0, 0, 0)
        central_widget.setWidget(self.card_container)
        central_widget.setWidgetResizable(True)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.container_layout.addItem(self.spacer)

        layout.addLayout(titlelayout)
        layout.addWidget(central_widget)

        self._current_cards = 0

        self._skeletons: List[MediaCardSkeletonMinimal] = list()

        self._create_skeletons()

        #scrollbar

    def _create_skeletons(self):
        for _ in range(self.MAX_CARDS):
            skeleton = MediaCardSkeletonMinimal()
            skeleton.start()
            self._skeletons.append(skeleton)
            self._addWidget(skeleton)

    def addCard(self, widget: QWidget):
        if self._current_cards >= self.MAX_CARDS:
            return
        self._addWidget(widget)
        self._current_cards += 1


    def _addWidget(self, widget: Union[MediaCardSkeletonMinimal, QWidget]):
        self.container_layout.removeItem(self.spacer)
        if isinstance(widget, MediaCardSkeletonMinimal):
            self.container_layout.addWidget(widget)
        elif isinstance(widget, QWidget):
            if len(self._skeletons):
                skeleton = self._skeletons.pop(0)
                skeleton.setParent(None)
                skeleton.deleteLater()
            self.container_layout.insertWidget(self._current_cards, widget)
            logger.debug(f"Added {widget} at {self._current_cards}")
        self.container_layout.addItem(self.spacer)

class TopHundred(QWidget):
    MAX_CARDS = 100
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_cards = 0
        self._skeletons: List[MediaCardSkeletonLandscape] = list()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.title_label = MyLabel(text = "Top Hundred", font_size=20, parent = self)

        self.main_layout.addItem(self.spacer)

        self._create_skeletons()

    def _create_skeletons(self):
        for _ in range(10):
            skeleton = MediaCardSkeletonLandscape()
            skeleton.start()
            self._skeletons.append(skeleton)
            self._addWidget(skeleton)

    def addCard(self, widget: MediaCard):
        if self._current_cards >= self.MAX_CARDS:
            return
        if widget.variant != MediaVariants.LANDSCAPE:
            widget.set_variant(MediaVariants.LANDSCAPE)
        self._addWidget(widget)
        self._current_cards += 1

    def _addWidget(self, widget: Union[MediaCardSkeletonLandscape, MediaCard]):
        self.main_layout.removeItem(self.spacer)
        if isinstance(widget, MediaCardSkeletonLandscape):
            self.main_layout.addWidget(widget)
        elif isinstance(widget, MediaCard):
            if len(self._skeletons) > 0:
                skeleton = self._skeletons.pop(0)
                skeleton.setParent(None)
                skeleton.deleteLater()
            self.main_layout.insertWidget(self._current_cards, widget)
            logger.debug(f"Added {widget}  at {self._current_cards}")
        self.main_layout.addItem(self.spacer)




class HomeContainers(Enum):
    TRENDING = auto()             # Update every 1–3 hours (depending on traffic/activity)
    TOP100 = auto()               # Update daily or weekly
    RECENTLY_UPDATED = auto()     # Update every 30 minutes to 1 hour
    CONTINUE_WATCHING = auto()    # Real-time or every time the user returns
    LATEST_ADDED = auto()         # Update every 15–30 minutes

class HomeInterface(KineticScrollArea):
    CONTAINER_MIN_HEIGHT = 360
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self.setStyleSheet("""
            KineticScrollArea, KineticScrollArea QWidget {
                background: none;
                # background-color: transparent;
                
            }
        """)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.verticalScrollBar().style().drawPrimitive(QStyle.)



        self._screen_geometry = QApplication.primaryScreen().availableGeometry()

        central_widget = QWidget(self)
        self.setWidget(central_widget)
        self.setWidgetResizable(True)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(20)


        self.hero_banner = HeroContainer(self)
        self.hero_banner.start()
        self.hero_banner.setFixedHeight(int(self._screen_geometry.height() * 0.6))
        self.continue_watching_container = Container("Continue watching", parent)
        self.continue_watching_container.setMinimumHeight(self.CONTAINER_MIN_HEIGHT)
        self.recently_updated_container = Container("Recently updated", parent)
        self.recently_updated_container.setMinimumHeight(self.CONTAINER_MIN_HEIGHT)
        self.latest_added_container = Container("Latest added", parent)
        self.latest_added_container.setMinimumHeight(self.CONTAINER_MIN_HEIGHT)
        self.trending_container = Container("Trending", parent)
        self.trending_container.setMinimumHeight(self.CONTAINER_MIN_HEIGHT)

        self.top_hundred_container = TopHundred(parent)


        self.main_layout.addWidget(self.hero_banner)
        self.main_layout.addWidget(self.continue_watching_container)
        self.main_layout.addWidget(self.recently_updated_container)
        self.main_layout.addWidget(self.latest_added_container)
        self.main_layout.addWidget(self.trending_container)
        self.main_layout.addWidget(MyLabel("Top 100", 20, parent = self))
        self.main_layout.addWidget(self.top_hundred_container)

    def addCard(self, card: MediaCard, container: HomeContainers):
        if container == HomeContainers.CONTINUE_WATCHING:
            card.set_variant(MediaVariants.PORTRAIT)
            self.continue_watching_container.addCard(card)
        elif container == HomeContainers.LATEST_ADDED:
            card.set_variant(MediaVariants.PORTRAIT)
            self.latest_added_container.addCard(card)
        elif container == HomeContainers.RECENTLY_UPDATED:
            card.set_variant(MediaVariants.PORTRAIT)
            self.recently_updated_container.addCard(card)
        elif container == HomeContainers.TRENDING:
            card.set_variant(MediaVariants.PORTRAIT)
            self.trending_container.addCard(card)
        elif container == HomeContainers.TOP100:
            self.top_hundred_container.addCard(card)
        else:
            logger.warning(f"Unknown container {container}")
            return

if __name__ == '__main__':
    setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    main = Container("Trending", parent = None)
    main = HomeInterface()
    container = HomeContainers.CONTINUE_WATCHING
    for x in range(20):
        if x >3:
            container = HomeContainers.TRENDING
        if x >9:
            container = HomeContainers.RECENTLY_UPDATED
        if x >15:
            container = HomeContainers.LATEST_ADDED
        # if x >20:
        #     container = HomeContainers.TOP100
        title = f"My Title{x}"
        card = MediaCard(parent=main)
        main.addCard(card, container)


    main.show()
    sys.exit(app.exec())