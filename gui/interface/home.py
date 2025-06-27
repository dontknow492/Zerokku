import asyncio
from enum import Enum, auto
from typing import List, Union

import sys
from PySide6.QtWidgets import QWidget, QFrame, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from loguru import logger
from qasync import QEventLoop
from qfluentwidgets import Theme, setTheme

from AnillistPython import AnilistMedia
from gui.common import KineticScrollArea, MyLabel
from gui.components import MediaCard, MediaVariants, HeroContainerSkeleton, \
    MediaCardSkeletonLandscape, ViewMoreContainer, LandscapeContainer


class HeroContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.skeleton = HeroContainerSkeleton(self)
        # self.skeleton.setFixedSize(self.size())

    def resizeEvent(self, event):
        self.skeleton.setFixedSize(self.size())

    def start(self):
        self.skeleton.start()


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
        self.title_label = MyLabel(text="Top Hundred", font_size=20, parent=self)

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
    TRENDING = auto()  # Update every 1–3 hours (depending on traffic/activity)
    TOP100 = auto()  # Update daily or weekly
    CONTINUE_WATCHING = auto()  # Real-time or every time the user returns
    LATEST_ADDED = auto()  # Update every 15–30 minutes


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
        self.continue_watching_container = ViewMoreContainer("Continue watching", parent)
        self.continue_watching_container.setMinimumHeight(self.CONTAINER_MIN_HEIGHT)
        self.latest_added_container = ViewMoreContainer("Latest added", parent)
        self.latest_added_container.setMinimumHeight(self.CONTAINER_MIN_HEIGHT)
        self.trending_container = ViewMoreContainer("Trending", parent)
        self.trending_container.setMinimumHeight(self.CONTAINER_MIN_HEIGHT)

        self.top_hundred_container = LandscapeContainer(parent=self)

        self.main_layout.addWidget(self.hero_banner)
        self.main_layout.addWidget(self.continue_watching_container)
        # self.main_layout.addWidget(self.recently_updated_container)
        self.main_layout.addWidget(self.latest_added_container)
        self.main_layout.addWidget(self.trending_container)
        self.main_layout.addWidget(MyLabel("Top 100", 20, parent=self))
        self.main_layout.addWidget(self.top_hundred_container)

    def add_continue_watching_medias(self, data: List[AnilistMedia]):
        self.continue_watching_container.add_medias(data)

    def add_trending_medias(self, data: List[AnilistMedia]):
        self.trending_container.add_medias(data)

    def add_top_hundred_medias(self, data: List[AnilistMedia]):
        self.top_hundred_container.add_medias(data)

    def add_latest_added_medias(self, data: List[AnilistMedia]):
        self.latest_added_container.add_medias(data)


def main():
    # with open(r"D:\Program\Zerokku\demo\data.json", "r", encoding="utf-8") as data:
    #     result = json.load(data)
    # cards = parse_searched_media(result, None)

    # cards.extend(cards)
    # cards.extend(cards)
    # print(len(cards))

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
    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())


if __name__ == '__main__':
    setTheme(Theme.DARK)
    main()