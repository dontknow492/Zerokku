import sys
from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from qfluentwidgets import SearchLineEdit, PopUpAniStackedWidget, SegmentedWidget, PrimaryToolButton, \
    TransparentToggleToolButton, FluentIcon
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QApplication, QButtonGroup

from AnillistPython import MediaType
from gui.common import EnumComboBox, MyLabel
from gui.components import CardContainer, MediaVariants
from utils import IconManager


class LibraryNavigation(QWidget):
    variantChanged = Signal(MediaVariants)
    typeChanged = Signal(MediaType)
    def __init__(self, variant: MediaVariants = MediaVariants.PORTRAIT, media_type: MediaType = MediaType.ANIME, parent=None):
        super().__init__(parent)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.type_segment = SegmentedWidget(self)
        self.type_segment.addItem("anime", "Anime", lambda: self.typeChanged.emit(MediaType.ANIME), FluentIcon.MOVIE)
        self.type_segment.addItem("manga", "Manga", lambda: self.typeChanged.emit(MediaType.MANGA), FluentIcon.ALBUM)

        if media_type == MediaType.ANIME:
            self.type_segment.setCurrentItem("anime")
        elif media_type == MediaType.MANGA:
            self.type_segment.setCurrentItem("manga")

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

        self.main_layout.addStretch()
        self.main_layout.addWidget(self.type_segment, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(portrait_view_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(landscape_view_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(gird_view_button, alignment=Qt.AlignmentFlag.AlignRight)

class LibraryInterface(QWidget):
    TITLE_FONT_SIZE = 20
    TITLE_FONT_WEIGHT = QFont.Weight.DemiBold
    def __init__(self, parent=None):
        super().__init__(parent)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 9, 0, 9)
        # self.mainLayout.setSpacing(0)



        self.title_label = MyLabel("Library", self.TITLE_FONT_SIZE, self.TITLE_FONT_WEIGHT)
        self.count_label = MyLabel("(59)", self.TITLE_FONT_SIZE, self.TITLE_FONT_WEIGHT)
        self.search_bar = SearchLineEdit(self)
        self.search_bar.setPlaceholderText("Search")

        self.library_nav = LibraryNavigation(parent = self)

        self.sort_combobox = EnumComboBox(parent=self)
        self.order_combobox = EnumComboBox(parent=self)
        self.grouping_combobox = EnumComboBox(parent=self)

        self.type_stac = PopUpAniStackedWidget(parent=self) #anime/manga stack
        self.anime_view = CardContainer(parent=self)
        self.manga_view = CardContainer(parent=self)

        self.type_stac.addWidget(self.anime_view)
        self.type_stac.addWidget(self.manga_view)

        self._init_ui()
        self._signal_handler()

    def _init_ui(self):

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.title_label)
        search_layout.addWidget(self.count_label)
        search_layout.addWidget(self.search_bar, stretch=1)
        search_layout.addWidget(self.sort_combobox)
        search_layout.addWidget(self.order_combobox)
        search_layout.addWidget(self.grouping_combobox)


        self.mainLayout.addLayout(search_layout)
        self.mainLayout.addWidget(self.library_nav)
        self.mainLayout.addWidget(self.type_stac, stretch=1)

    def _signal_handler(self):
        self.library_nav.variantChanged.connect(self._switch_view)
        self.library_nav.typeChanged.connect(self._switch_type)

    def _switch_view(self, variant: MediaVariants):
        self.anime_view.switch_view(variant)
        self.manga_view.switch_view(variant)

    def _switch_type(self, type: MediaType):
        if type == MediaType.ANIME:
            self.type_stac.setCurrentWidget(self.anime_view)
        elif type == MediaType.MANGA:
            self.type_stac.setCurrentWidget(self.manga_view)





if __name__ == '__main__':
    app = QApplication(sys.argv)
    library = LibraryInterface()
    library.show()
    sys.exit(app.exec())