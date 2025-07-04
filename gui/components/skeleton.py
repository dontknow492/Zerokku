import sys

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPaintEvent
from qasync import QApplication
from qfluentwidgets import SimpleCardWidget

from gui.common import SkimmerWidget



class MediaCardSkeletonMinimal(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cover_size = QSize(195, 270)
        self.setFixedWidth(self.cover_size.width())
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.cover_skeleton = SkimmerWidget(self)
        self.cover_skeleton.setFixedSize(self.cover_size)
        self.title_skeleton = SkimmerWidget(self)
        self.title_skeleton.setFixedHeight(22)
        self.title_skeleton.setMaximumWidth(self.cover_size.width())
        layout.addWidget(self.cover_skeleton, stretch=1)
        layout.addWidget(self.title_skeleton)

        self.setLayout(layout)

    def start(self):
        self.cover_skeleton.loading = True
        self.title_skeleton.loading = True

    def stop(self):
        self.cover_skeleton.loading = False
        self.title_skeleton.loading = False


class MediaCardSkeletonLandscape(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cover_size = QSize(55, 76)
        self.setFixedHeight(self.cover_size.height())
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(9, 0, 9, 0)

        self.cover_skeleton = SkimmerWidget(self)
        self.cover_skeleton.setFixedSize(self.cover_size)

        self.title_skeleton = SkimmerWidget(self)
        self.title_skeleton.setMaximumHeight(22)
        self.genre_skeleton = SkimmerWidget(self)
        self.genre_skeleton.setMaximumHeight(22)

        self.status_skeleton = SkimmerWidget(self)
        self.status_skeleton.setMaximumHeight(22)
        self.rating_skeleton = SkimmerWidget(self)
        self.rating_skeleton.setMaximumHeight(22)

        self.media_type_skeleton = SkimmerWidget(self)
        self.media_type_skeleton.setMaximumHeight(22)
        self.users_skeleton = SkimmerWidget(self)
        self.users_skeleton.setMaximumHeight(22)

        self.episode_skeleton = SkimmerWidget(self)
        self.episode_skeleton.setMaximumHeight(22)
        self.value_skeleton = SkimmerWidget(self)
        self.value_skeleton.setMaximumHeight(22)

        # Add to grid layout
        layout.addWidget(self.cover_skeleton, stretch=0)

        h1_layout = QHBoxLayout()
        h1_layout.setSpacing(30)
        h1_layout.setContentsMargins(0, 0, 0, 0)
        h1_layout.addWidget(self.title_skeleton, 4)
        h1_layout.addWidget(self.genre_skeleton, 1)
        h1_layout.addWidget(self.status_skeleton, 1)
        h1_layout.addWidget(self.rating_skeleton, 1)

        h2_layout = QHBoxLayout()
        h2_layout.setSpacing(30)
        h2_layout.setContentsMargins(0, 0, 0, 0)
        h2_layout.addWidget(self.episode_skeleton, 3)
        h2_layout.addWidget(self.value_skeleton, 1)
        h2_layout.addWidget(self.media_type_skeleton, 1)
        h2_layout.addWidget(self.users_skeleton, 2)

        vlayout = QVBoxLayout()
        vlayout.addSpacing(-10)
        vlayout.addLayout(h1_layout, stretch=2)
        vlayout.addSpacing(-15)
        vlayout.addLayout(h2_layout, stretch=1)
        # vlayout.addStretch(stretch=2)

        layout.addLayout(vlayout)

        # row, column, rowspan=2, colspan=1
        # layout.setVerticalSpacing(60)



        # Optional: set stretch or fixed sizes if needed
        self.setLayout(layout)

    def start(self):
        self.cover_skeleton.loading = True
        self.title_skeleton.loading = True
        self.genre_skeleton.loading = True
        self.status_skeleton.loading = True
        self.rating_skeleton.loading = True
        self.media_type_skeleton.loading = True
        self.users_skeleton.loading = True
        self.value_skeleton.loading = True
        self.episode_skeleton.loading = True

    def stop(self):
        self.cover_skeleton.loading = False
        self.title_skeleton.loading = False
        self.genre_skeleton.loading = False
        self.status_skeleton.loading = False
        self.rating_skeleton.loading = False
        self.media_type_skeleton.loading = False
        self.users_skeleton.loading = False
        self.value_skeleton.loading = False
        self.episode_skeleton.loading = False


class MediaCardSkeletonDetailed(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cover_size = QSize(195, 270)
        self.setFixedHeight(self.cover_size.height())
        self._init_ui()

    def _init_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.cover_skeleton = SkimmerWidget(self)
        self.cover_skeleton.setFixedSize(self.cover_size)

        self.title_skeleton = SkimmerWidget(self)
        self.genre_skeleton = SkimmerWidget(self)

        self.status_skeleton = SkimmerWidget(self)
        self.rating_skeleton = SkimmerWidget(self)

        self.media_type_skeleton = SkimmerWidget(self)
        self.users_skeleton = SkimmerWidget(self)

        self.episode_skeleton = SkimmerWidget(self)
        self.value_skeleton = SkimmerWidget(self)

        self.line_skeleton = SkimmerWidget(self)


        layout.addWidget(self.cover_skeleton, 0, 0, 10, 1)

        layout.addWidget(self.title_skeleton, 0, 1, 2, 2)
        layout.addWidget(self.genre_skeleton, 2, 1, 1, 1)


        layout.addWidget(self.rating_skeleton, 4, 1, 1, 3)
        layout.addWidget(self.media_type_skeleton, 5, 1, 1, 3)
        layout.addWidget(self.users_skeleton, 6, 1, 1, 2)
        layout.addWidget(self.line_skeleton, 7, 1)


        layout.addWidget(self.status_skeleton, 9, 1, 1, 1)
        layout.addWidget(self.episode_skeleton, 9, 2, 1, 1)
        layout.addWidget(self.value_skeleton, 9, 3, 1, 1)

    def start(self):
        self.cover_skeleton.loading = True
        self.title_skeleton.loading = True
        self.genre_skeleton.loading = True
        self.status_skeleton.loading = True
        self.rating_skeleton.loading = True
        self.media_type_skeleton.loading = True
        self.users_skeleton.loading = True
        self.value_skeleton.loading = True
        self.episode_skeleton.loading = True
        self.line_skeleton.loading = True

    def stop(self):
        self.cover_skeleton.loading = False
        self.title_skeleton.loading = False
        self.genre_skeleton.loading = False
        self.status_skeleton.loading = False
        self.rating_skeleton.loading = False
        self.media_type_skeleton.loading = False
        self.users_skeleton.loading = False
        self.value_skeleton.loading = False
        self.episode_skeleton.loading = False
        self.line_skeleton.loading = False

class MediaCardRelationSkeleton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cover_size = QSize(195, 270)

        self.cover_skeleton = SkimmerWidget(self)
        self.cover_skeleton.setFixedSize(self.cover_size)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.cover_skeleton)

    def start(self):
        self.cover_skeleton.loading = True

    def stop(self):
        self.cover_skeleton.loading = False


class HeroContainerSkeleton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.cover_size = QSize(470, 245)
        self.setMinimumWidth(int(self.cover_size.width()* 1.5))
        self.setMinimumHeight(self.cover_size.height()*2)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.cover_skeleton = SkimmerWidget(self)
        self.cover_skeleton.setFixedSize(self.cover_size)

        self.title_skeleton = SkimmerWidget(self)
        self.title_skeleton.setFixedWidth(self.cover_size.width())

        self.line_1_skeleton = SkimmerWidget(self)
        self.line_1_skeleton.setFixedWidth(int(self.cover_size.width()* 1.5))
        self.line_2_skeleton = SkimmerWidget(self)
        self.line_2_skeleton.setFixedWidth(int(self.cover_size.width()* 1.5))
        self.line_3_skeleton = SkimmerWidget(self)
        self.line_3_skeleton.setFixedWidth(int(self.cover_size.width()* 1.5))
        self.line_4_skeleton = SkimmerWidget(self)
        self.line_4_skeleton.setFixedWidth(int(self.cover_size.width()* 1.5))

        self.block_skeleton = SkimmerWidget(self)
        self.block_skeleton.setMaximumWidth(self.cover_size.width()//2)

        layout.addWidget(self.cover_skeleton)
        layout.addWidget(self.title_skeleton, stretch=3)
        layout.addSpacing(20)
        layout.addWidget(self.line_1_skeleton, stretch=2)
        layout.addWidget(self.line_2_skeleton, stretch=2)
        layout.addWidget(self.line_3_skeleton, stretch=2)
        layout.addWidget(self.line_4_skeleton, stretch=2)
        layout.addSpacing(30)
        layout.addWidget(self.block_skeleton, stretch=4)
        layout.addSpacing(150)

    def start(self):
        self.cover_skeleton.loading = True
        self.title_skeleton.loading = True
        self.line_1_skeleton.loading = True
        self.line_2_skeleton.loading = True
        self.line_3_skeleton.loading = True
        self.line_4_skeleton.loading = True
        self.block_skeleton.loading = True

    def stop(self):
        self.cover_skeleton.loading = False
        self.title_skeleton.loading = False
        self.line_1_skeleton.loading = False
        self.line_2_skeleton.loading = False
        self.line_3_skeleton.loading = False
        self.line_4_skeleton.loading = False
        self.block_skeleton.loading = False

class ReviewSkeleton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.user_avatar_size = QSize(64, 64)

        self.user_avatar_skeleton = SkimmerWidget(self)
        self.user_avatar_skeleton.setFixedSize(self.user_avatar_size)
        self.user_avatar_skeleton.setXRadius(self.user_avatar_size.width()//2)
        self.user_avatar_skeleton.setYRadius(self.user_avatar_size.height()//2)

        self.username_skeleton = SkimmerWidget(self)
        self.username_skeleton.setMaximumWidth(self.user_avatar_size.width()*3)
        self.username_skeleton.setFixedHeight(self.user_avatar_size.height()//2.5)
        self.comment_line_1_skeleton = SkimmerWidget(self)
        self.comment_line_1_skeleton.setFixedHeight(self.user_avatar_size.height()//3)
        self.comment_line_2_skeleton = SkimmerWidget(self)
        self.comment_line_2_skeleton.setFixedHeight(self.user_avatar_size.height()//3)
        self.comment_line_3_skeleton = SkimmerWidget(self)
        self.comment_line_3_skeleton.setFixedHeight(self.user_avatar_size.height()//3)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.user_avatar_skeleton, alignment=Qt.AlignmentFlag.AlignTop)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.username_skeleton)
        vbox.addSpacing(6)
        vbox.addWidget(self.comment_line_1_skeleton)
        vbox.addWidget(self.comment_line_2_skeleton)
        vbox.addWidget(self.comment_line_3_skeleton)
        vbox.addStretch()

        layout.addLayout(vbox)

    def start(self):
        self.user_avatar_skeleton.loading = True
        self.username_skeleton.loading = True
        self.comment_line_1_skeleton.loading = True
        self.comment_line_2_skeleton.loading = True
        self.comment_line_3_skeleton.loading = True

    def stop(self):
        self.user_avatar_skeleton.loading = False
        self.username_skeleton.loading = False
        self.comment_line_1_skeleton.loading = False
        self.comment_line_2_skeleton.loading = False
        self.comment_line_3_skeleton.loading = False


class WatchCardCoverSkeleton(QWidget):
    COVER_SIZE = QSize(320, 180)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cover_skeleton = SkimmerWidget(self)
        self.cover_skeleton.setFixedSize(self.COVER_SIZE)

        self.title_skeleton = SkimmerWidget(self)
        self.title_skeleton.setFixedHeight(30)
        self.body_skeleton = SkimmerWidget(self)
        self.body_skeleton.setFixedHeight(20)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.cover_skeleton)
        layout.addWidget(self.title_skeleton)
        layout.addWidget(self.body_skeleton)

    def start(self):
        self.cover_skeleton.loading = True
        self.title_skeleton.loading = True
        self.body_skeleton.loading = True

    def stop(self):
        self.cover_skeleton.loading = False
        self.title_skeleton.loading = False
        self.body_skeleton.loading = False

class WatchCardLandscapeSkeleton(QWidget):
    LANDSCAPE_SIZE = QSize(55, 76)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cover_skeleton = SkimmerWidget(self)
        self.cover_skeleton.setFixedSize(self.LANDSCAPE_SIZE)

        self.title_skeleton = SkimmerWidget(self)
        self.title_skeleton.setFixedHeight(25)
        # self.title_skeleton.setFixedWidth(400)
        self.body_skeleton = SkimmerWidget(self)
        self.body_skeleton.setFixedHeight(15)
        # self.body_skeleton.setFixedWidth(100)


        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.cover_skeleton, alignment=Qt.AlignmentFlag.AlignLeft)
        vbox = QVBoxLayout()
        vbox.addWidget(self.title_skeleton)
        vbox.addWidget(self.body_skeleton)

        layout.addLayout(vbox, stretch=1)

    def start(self):
        self.cover_skeleton.loading = True
        self.title_skeleton.loading = True
        self.body_skeleton.loading = True

    def stop(self):
        self.cover_skeleton.loading = False
        self.title_skeleton.loading = False
        self.body_skeleton.loading = False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = QWidget()
    layout = QVBoxLayout()
    widget.setLayout(layout)

    # skeleton = MediaCardSkeletonDetailed()
    # skeleton = MediaCardSkeletonMinimal()
    # skeleton = MediaCardSkeletonLandscape()
    # skeleton = HeroContainerSkeleton()
    # skeleton = MediaCardRelationSkeleton()
    # skeleton = ReviewSkeleton()
    # skeleton = WatchCardCoverSkeleton()
    skeleton = WatchCardLandscapeSkeleton()

    skeleton.start()

    layout.addWidget(skeleton)

    widget.show()
    sys.exit(app.exec())