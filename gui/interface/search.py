import os
import sys
import json
from collections import defaultdict
from typing import Optional, List, Tuple, Set

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont, Qt

from enums import MediaFormat, MediaSeason, MediaStatus, MediaSource, MediaSort, MediaType, MediaGenre

from PySide6.QtWidgets import QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout
from qfluentwidgets import Slider, SearchLineEdit, ComboBox, CheckableMenu, ToolButton, FluentIcon, PrimaryPushButton, \
    FlyoutViewBase, FlowLayout, TogglePushButton, CheckBox, TransparentPushButton, LineEdit, Flyout, FlyoutAnimationType

from superqt import QRangeSlider, QLabeledRangeSlider

from gui.common import MyLabel, EnumComboBox, TriStateButton, KineticScrollArea


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


class SearchBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.search_bar = SearchLineEdit()
        self.search_bar.setPlaceholderText("Search anime/manga")
        self.search_box = FilterContainer("Search", self.search_bar)
        self.type_filter = EnumComboBox(MediaType, parent = self)
        self.type_box = FilterContainer("Type", self.type_filter)
        # self.type_box.setPlaceholderText("Type")
        self.genre_filter = EnumComboBox(MediaGenre, parent = self)
        self.genre_box = FilterContainer("Genre", self.genre_filter)
        # self.genre_filter.setPlaceholderText("Genre")
        self.format_filter = EnumComboBox(MediaFormat, parent = self)
        self.format_box = FilterContainer("Format", self.format_filter)
        # self.format_filter.setPlaceholderText("Format")
        self.advance_filter_button = ToolButton(FluentIcon.MENU, self)
        self.filter_button = PrimaryPushButton(FluentIcon.FILTER, "Filter", self)


        self._init_ui()
        self._signal_handler()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.addWidget(self.advance_filter_button, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.search_box, stretch=1, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.type_box, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.genre_box, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.format_box, alignment=Qt.AlignmentFlag.AlignBottom)

        layout.addWidget(self.filter_button, alignment=Qt.AlignmentFlag.AlignBottom)

    def _signal_handler(self):
        self.advance_filter_button.clicked.connect(self._on_advance_filter)

    def _on_advance_filter(self):
        if not hasattr(self, "advance_filter"):
            self.advance_filter = AdvanceFilter()
            self.advance_filter.setFixedWidth(self.width())
        Flyout.make(self.advance_filter, self.advance_filter_button, self, aniType=FlyoutAnimationType.DROP_DOWN,
                    isDeleteOnClose=False)

class TagSelector(QWidget):
    tagStateChanged = Signal(int, CheckBox) #state, button
    def __init__(self, parent=None):
        super().__init__(parent)
        self._initialize_data_structures()
        self._setup_ui()
        self._load_tags()

    def _initialize_data_structures(self) -> None:
        """Initialize data structures for storing UI elements and tags."""
        self.tag_buttons: List[Tuple[CheckBox, str, FilterContainer]] = []
        self.containers: Set[FilterContainer] = set()
        self._tags_file = "tags.json"

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
            print(f"Error: {self._tags_file} not found")
            return

        try:
            with open(self._tags_file, "r", encoding="utf-8") as f:
                tags = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
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
            button = self._create_button(name)
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

    def _create_button(self, text: str)->CheckBox:
        button = CheckBox(text, self)
        button.setTristate(True)
        button.stateChanged.connect(lambda state: self.tagStateChanged.emit(state, button))
        return button

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
        print(f"Visible: {visible_count}/{len(self.tag_buttons)}, Visible Container: {container_visible_count}/{len(self.containers)} ")

    def clear_search(self) -> None:
        """Clear search bar and show all tags."""
        self.search_bar.clear()
        self._filter_tags("")




class AdvanceFilter(FlyoutViewBase):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QGridLayout(self)

        self.airing_filter = EnumComboBox(enum = MediaStatus, parent = self)
        self.airing_box = FilterContainer("Airing", self.airing_filter, 18, parent = self)

        self.source_filter = EnumComboBox(enum = MediaSource, parent = self)
        self.source_box = FilterContainer("Source", self.source_filter, 18, parent = self)

        self.season_filter = EnumComboBox(enum = MediaSeason, parent = self)
        self.season_box = FilterContainer("Season", self.season_filter, 18, parent = self)

        self.year_filter = EnumComboBox(parent = self)
        self.year_filter.setPlaceholderText("Year")
        self.year_box = FilterContainer("Year", self.year_filter, 18, parent = self)


        self.episode_slider = QLabeledRangeSlider(Qt.Orientation.Horizontal, parent = self)
        # self.episode_slider.set


        # self.tag_button = MyLabel("Advance Genre and Tags Filter", 18, QFont.Weight.DemiBold, self)
        # self.tags_filter = TagSelector(self)








        layout.addWidget(self.airing_box, 0, 1)
        layout.addWidget(self.source_box, 0, 2)
        layout.addWidget(self.season_box, 0, 3)
        layout.addWidget(self.year_box, 0, 4)

        layout.addWidget(self.episode_slider, 1, 1)

        # layout.addWidget(self.tag_button, 1, 1, 1, 4)
        # layout.addWidget(self.tags_filter, 2, 1, 1, 4)

        layout.setRowStretch(2, 1)





if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = AdvanceFilter()
    # main = SearchBar()
    main.show()
    sys.exit(app.exec())