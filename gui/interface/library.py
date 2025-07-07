import asyncio
import json
import os
from pathlib import Path

import sys
from loguru import logger
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from qasync import QEventLoop, asyncSlot

from qfluentwidgets import SearchLineEdit, PopUpAniStackedWidget, SegmentedWidget, PrimaryToolButton, \
    TransparentToggleToolButton, FluentIcon
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QApplication, QButtonGroup
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from AnillistPython import MediaType, parse_searched_media
from database import AsyncLibraryRepository, init_db, AsyncMediaRepository, UserCategory
from gui.common import EnumComboBox, MyLabel, KineticScrollArea
from gui.components import CardContainer, MediaVariants
from utils import IconManager


class LibraryNavigation(QWidget):
    variantChanged = Signal(MediaVariants)
    typeChanged = Signal(MediaType)
    def __init__(self, variant: MediaVariants = MediaVariants.PORTRAIT,
                 media_type: MediaType = MediaType.ANIME, parent=None):
        super().__init__(parent)

        self.variant = variant

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.type_segment = SegmentedWidget(self)
        self.type_segment.addItem("anime", "Anime", lambda: self.typeChanged.emit(MediaType.ANIME), FluentIcon.MOVIE)
        self.type_segment.addItem("manga", "Manga", lambda: self.typeChanged.emit(MediaType.MANGA), FluentIcon.ALBUM)

        if media_type == MediaType.ANIME:
            self.type_segment.setCurrentItem("anime")
        elif media_type == MediaType.MANGA:
            self.type_segment.setCurrentItem("manga")

        #segment
        self.category_segment = SegmentedWidget(self)
        self.status_segment = SegmentedWidget(self)






        self._init_ui()


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
        scroll_area.setFixedHeight(40)
        container = QWidget(self)
        scroll_area.setWidget(container)
        scroll_area.setWidgetResizable(True)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        container_layout.addWidget(self.category_segment, alignment=Qt.AlignmentFlag.AlignLeft)
        container_layout.addWidget(self.status_segment, alignment=Qt.AlignmentFlag.AlignLeft)
        container_layout.addStretch()

        self.main_layout.addWidget(scroll_area, stretch=1)
        self.main_layout.addWidget(self.type_segment, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(portrait_view_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(landscape_view_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(gird_view_button, alignment=Qt.AlignmentFlag.AlignRight)

    def add_category(self, category: UserCategory, selected: bool = True):
        # self.type_segment.addItem("anime", "Anime", lambda: self.typeChanged.emit(MediaType.ANIME), FluentIcon.MOVIE)
        self.category_segment.addItem(category.name, category.name, None, None)
        if selected:
            self.category_segment.setCurrentItem(category.name)


class LibraryInterface(QWidget):
    TITLE_FONT_SIZE = 20
    TITLE_FONT_WEIGHT = QFont.Weight.DemiBold
    def __init__(self, async_library_repo: AsyncLibraryRepository, user_id: int, parent=None):
        super().__init__(parent)

        self.user_id = user_id
        self.async_library_repo = async_library_repo




        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 9, 0, 9)
        # self.mainLayout.setSpacing(0)



        self.title_label = MyLabel("Library", self.TITLE_FONT_SIZE, self.TITLE_FONT_WEIGHT)
        self.count_label = MyLabel("(59)", self.TITLE_FONT_SIZE, self.TITLE_FONT_WEIGHT)
        self.search_bar = SearchLineEdit(self)
        self.search_bar.setPlaceholderText("Search")

        self.library_nav = LibraryNavigation(parent = self)

        self.sort_combobox = EnumComboBox(parent=self)
        self.sort_combobox.setPlaceholderText("Sort by")
        self.order_combobox = EnumComboBox(parent=self)
        self.order_combobox.setPlaceholderText("Order")
        self.grouping_combobox = EnumComboBox(parent=self)
        self.grouping_combobox.setPlaceholderText("Grouping")

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





async def main():
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