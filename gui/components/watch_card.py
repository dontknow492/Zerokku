from datetime import datetime, timedelta
from typing import Union

import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QVBoxLayout, QApplication, QWidget, QHBoxLayout

from gui.common import WaitingLabel, MyLabel
from utils import seconds_to_time_string, trim_time_string

from qfluentwidgets import SimpleCardWidget, getFont

from enum import Enum, auto


class WatchCardVariant(Enum):
    LANDSCAPE = auto()
    MINIMAL = auto()
    COVER = auto()

class WatchCard(SimpleCardWidget):
    LANDSCAPE_SIZE = QSize(55, 76)
    MINIMAL_SIZE = QSize(200, 200)
    COVER_SIZE = QSize(320, 180)
    TITLE_FONT = getFont(20, QFont.Weight.Bold)
    BODY_FONT = getFont(14, QFont.Weight.DemiBold)
    def __init__(self, variant: WatchCardVariant = WatchCardVariant.COVER, parent=None):
        super().__init__(parent)

        self._episode: int = 0

        self.variant = variant
        self.thumbnail_label = WaitingLabel(parent=self)
        self.thumbnail_label.start()


        self.title_label = MyLabel("Title", parent=self)
        self.title_label.setFont(self.TITLE_FONT)
        self.episode_chapter_label = MyLabel("E1", parent=self)
        self.episode_chapter_label.setFont(self.TITLE_FONT)
        self.separate_label = MyLabel("-", parent=self)
        self.separate_label.setFont(self.TITLE_FONT)

        self.date_label = MyLabel("2025", parent=self)
        self.date_label.setFont(self.BODY_FONT)
        self.media_title_label = MyLabel("Naruto", parent=self)
        self.media_title_label.setFont(self.BODY_FONT)
        self.duration_label = MyLabel("24 min", parent=self)
        self.duration_label.setFont(self.BODY_FONT)

        self.setup_ui()

    def setup_ui(self):
        # Clear existing layout if any
        self._clear_layout()
        self._hide_all()
        if self.layout():
            QWidget().setLayout(self.layout())  # Transfer ownership to a temporary widget to delete
        self._configure_layout()

    def _configure_layout(self):
        if self.variant == WatchCardVariant.MINIMAL:
            self._setup_minimal()
        elif self.variant == WatchCardVariant.LANDSCAPE:
            self._setup_landscape()
        elif self.variant == WatchCardVariant.COVER:
            self._setup_cover()

    def set_variant(self, variant: WatchCardVariant):
        """Switch the card to a new previous_variant and update the UI."""
        if self.variant != variant:
            self.variant = variant
            self.setup_ui()


    # def setup
    def _setup_minimal(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        layout.addStretch()
        layout.addWidget(self.episode_chapter_label)
        layout.addStretch()

        self.episode_chapter_label.setVisible(True)

    def _setup_landscape(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 9, 19, 9)
        self.setBorderRadius(7)

        self.thumbnail_label.setFixedSize(self.LANDSCAPE_SIZE)
        self.thumbnail_label.setBorderRadius(4, 4, 4, 4)

        vboxLayout = QVBoxLayout(self)
        vboxLayout.setSpacing(0)

        title_layout = QHBoxLayout(self)
        title_layout.setContentsMargins(9, 0, 0, 0)
        title_layout.setSpacing(4)

        title_layout.addWidget(self.episode_chapter_label)
        title_layout.addWidget(self.separate_label)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.duration_label)

        body_layout = QHBoxLayout(self)
        body_layout.setContentsMargins(9, 0, 0, 0)
        body_layout.setSpacing(6)
        body_layout.addWidget(self.media_title_label)
        # body_layout.addWidget(self.progress_label)

        body_layout.addStretch()
        body_layout.addWidget(self.date_label)

        vboxLayout.addStretch()
        vboxLayout.addLayout(title_layout)
        vboxLayout.addLayout(body_layout)
        vboxLayout.addStretch()

        layout.addWidget(self.thumbnail_label)
        layout.addLayout(vboxLayout)

        self.thumbnail_label.setVisible(True)
        self.duration_label.setVisible(True)
        self.title_label.setVisible(True)
        self.episode_chapter_label.setVisible(True)
        self.date_label.setVisible(True)
        self.media_title_label.setVisible(True)
        # self.progress_label.setVisible(True)

    def _setup_cover(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(1, 0, 1, 9)

        self.thumbnail_label.setFixedSize(self.COVER_SIZE)
        self.thumbnail_label.setBorderRadius(10, 10, 0, 0)
        self.setBorderRadius(10)



        title_layout = QHBoxLayout(self)
        title_layout.setContentsMargins(9, 0, 0, 0)
        title_layout.setSpacing(4)

        title_layout.addWidget(self.episode_chapter_label)
        title_layout.addWidget(self.separate_label)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        body_layout = QHBoxLayout(self)
        body_layout.setContentsMargins(9, 0, 9, 0)
        body_layout.setSpacing(6)

        body_layout.addWidget(self.media_title_label)
        body_layout.addStretch()
        body_layout.addWidget(self.date_label)

        # body_layout.addStretch()

        layout.addWidget(self.thumbnail_label)
        layout.addLayout(title_layout)
        layout.addLayout(body_layout)

        #overlay
        self.duration_label.setContentsMargins(9, 2, 9, 2)
        self.duration_label.adjustSize()
        self.duration_label.setParent(self.thumbnail_label)

        self.duration_label.raise_()
        self.duration_label.raise_()

        self.duration_label.move(self.thumbnail_label.width() - self.duration_label.width() - 10,
                                 self.thumbnail_label.height()- self.duration_label.height() - 5)

        self.duration_label.setStyleSheet("QLabel { background-color: rgba(40, 40, 40, 0.5); border-radius: 7px; }")


        self.thumbnail_label.setVisible(True)
        self.duration_label.setVisible(True)
        self.title_label.setVisible(True)
        self.episode_chapter_label.setVisible(True)
        self.date_label.setVisible(True)
        self.media_title_label.setVisible(True)




    def _clear_layout(self):
        self.thumbnail_label.setParent(None)
        self.duration_label.setParent(None)
        self.title_label.setParent(None)
        self.episode_chapter_label.setParent(None)
        self.date_label.setParent(None)
        self.media_title_label.setParent(None)

    def _hide_all(self):
        self.thumbnail_label.setVisible(False)
        self.duration_label.setVisible(False)
        self.title_label.setVisible(False)
        self.episode_chapter_label.setVisible(False)
        self.date_label.setVisible(False)
        self.media_title_label.setVisible(False)

    def setTitle(self, title: str):
        if title is None:
            title = ""
            self.separate_label.setText("")
        else:
            self.separate_label.setText("-")
        self.title_label.setText(title)

    def setMediaTitle(self, title: str):
        self.media_title_label.setText(title)

    def setEpisodeChapter(self, episode: int, is_episode: bool= True):
        self._episode = episode
        ep = "Episode" if is_episode else "Chapter"
        self.episode_chapter_label.setText(f"{ep} {episode}")


    def setDate(self, date: datetime):
        now = datetime.now()
        delta = now - date

        if delta < timedelta(minutes=1):
            seconds = int(delta.total_seconds())
            date_str = "Just now" if seconds < 5 else f"{seconds} seconds ago"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() // 60)
            date_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() // 3600)
            date_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            date_str = date.strftime("%B %d, %Y")

        self.date_label.setText(date_str)


    def setDuration(self, duration: int):
        self.duration_label.setText(f"{duration} min")

    def setThumbnail(self, thumbnail: Union[str, QPixmap]):
        if self.variant == WatchCardVariant.MINIMAL:
            return
        size = self.thumbnail_label.size()
        if isinstance(thumbnail, str):
            thumbnail = QPixmap(thumbnail)
        thumbnail_size = thumbnail.size()
        if self.variant == WatchCardVariant.LANDSCAPE:
            pass
        elif thumbnail_size != size:
            thumbnail = thumbnail.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            thumbnail = thumbnail.copy(self.thumbnail_label.geometry())

        self.thumbnail_label.setImage(thumbnail)
        self.thumbnail_label.setScaledSize(size)

    @property
    def episode(self)->int:
        return self._episode



if __name__ == '__main__':
    from PySide6.QtCore import QTimer
    ep = 1
    season = 1
    title = None
    anime = "Naruto"
    progress = 134
    duration = 24
    date = datetime(2020, 1, 1, 0, 0, 0)
    thumbnail = r"D:\Program\Zerokku\demo\poster.jpg"

    app = QApplication(sys.argv)
    card = WatchCard(WatchCardVariant.LANDSCAPE)
    card.show()
    card.setTitle(title)
    card.setEpisodeChapter(ep, is_episode=True)
    card.setDuration(duration)
    card.setDate(date)
    card.setThumbnail(thumbnail)

    # QTimer.singleShot(1000, lambda:card.set_variant(WatchCardVariant.))
    sys.exit(app.exec())