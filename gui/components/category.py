from typing import List, Tuple

import sys
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from PySide6.QtWidgets import QApplication, QVBoxLayout, QGroupBox, QHBoxLayout, QGridLayout, QWidget
from qfluentwidgets import FlyoutViewBase, SwitchButton, LineEdit, TextEdit, PrimaryPushButton, PushButton, themeColor, \
    setThemeColor, CheckBox

from database import UserCategory
from gui.common import AnimatedToggle, MyLabel


class CreateCategory(FlyoutViewBase):
    cancelSignal = Signal()
    acceptSignal = Signal(str, str, bool)  # name, description, show in shelf
    showInfoSignal = Signal(str, str, str) #lvl, title, message
    def __init__(self, parent=None):
        super().__init__(parent)

        self.primary_color = themeColor()
        weight = QFont.Weight.DemiBold

        self.ok_button = PrimaryPushButton("Ok", self)
        self.cancel_button = PushButton("Cancel", self)

        # Title
        title = MyLabel("Create Category", 22, weight, self)

        # Inputs
        self.name_line_edit = LineEdit(self)
        self.name_line_edit.setPlaceholderText("Name of category")

        self.description_line_edit = TextEdit(self)
        self.description_line_edit.setPlaceholderText("Description of category")

        self.show_in_shelf_button = AnimatedToggle(
            self,
            checked_color=self.primary_color,
            pulse_checked_color=self.primary_color.lighter(180)
        )

        # Layouts
        self.viewLayout = QVBoxLayout(self)

        # Category name
        name_group = MyLabel("Name", weight=weight, parent=self)

        # Category description
        description_group = MyLabel("Description", weight=weight, parent=self)

        # Shelf toggle layout
        toggle_layout = QHBoxLayout()
        toggle_label = MyLabel("Show in shelf", weight=weight, parent=self)
        toggle_layout.addWidget(toggle_label, stretch=1)
        toggle_layout.addWidget(self.show_in_shelf_button)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        # Container
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(name_group)
        container_layout.addWidget(self.name_line_edit)
        container_layout.addWidget(description_group)
        container_layout.addWidget(self.description_line_edit)
        container_layout.addLayout(toggle_layout)

        # Assemble view
        self.viewLayout.addWidget(title)
        self.viewLayout.addWidget(container)
        self.viewLayout.addLayout(button_layout)
        self.viewLayout.addStretch()

        # Connections
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.cancel_button.clicked.connect(self.cancelSignal.emit)

    def _on_ok_clicked(self):
        name = self.name_line_edit.text().strip()
        description = self.description_line_edit.toPlainText().strip()
        show_in_shelf = self.show_in_shelf_button.isChecked()

        if not name:
            self.showInfoSignal.emit("error", "Validation Error", "Category name cannot be empty.")
            return

        self.acceptSignal.emit(name, description, show_in_shelf)
        # self.close()

    def clear(self):
        self.name_line_edit.clear()
        self.description_line_edit.clear()
        self.show_in_shelf_button.setChecked(False)








class AddToCategory(FlyoutViewBase):
    def __init__(self, categories: List[UserCategory], parent = None):
        super().__init__(parent)

        title_label = MyLabel("Select categories", 22, QFont.Weight.DemiBold, parent = self)

        self.primary_color = themeColor()

        container = QWidget(self)

        self.viewLayout = QVBoxLayout(container)
        self.viewLayout.setSpacing(8)


        hbox = QHBoxLayout()
        self.edit_button = PushButton("Edit", self)
        self.ok_button = PrimaryPushButton("Ok", self)
        self.cancel_button = PushButton("Cancel", self)
        hbox.addWidget(self.edit_button)
        hbox.addStretch(1)
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)

        row = 0
        col = 0

        for index, category in enumerate(categories):
            button = self._create_category(category)
            self.viewLayout.addWidget(button)




        layout = QVBoxLayout(self)
        layout.addWidget(title_label)
        layout.addWidget(container, stretch = 1)
        layout.addLayout(hbox)



    def _create_category(self, category: UserCategory)->CheckBox:
        check_box = CheckBox(category.name, self)
        # check_box.setCursor(Qt.CursorShape.PointingHandCursor)
        return check_box




if __name__ == '__main__':
    setThemeColor(QColor("#db2d69"))
    categories = [
        UserCategory(id=1, name="Watching", description="Currently watching this anime"),
        UserCategory(id=2, name="Completed", description="Anime you've finished watching"),
        UserCategory(id=3, name="Plan to Watch", description="Anime you intend to watch later"),
        UserCategory(id=4, name="Dropped", description="Anime you stopped watching"),
        UserCategory(id=5, name="On Hold", description="Anime you're temporarily not watching"),
        UserCategory(id=6, name="Rewatching", description="Anime you're watching again"),
        UserCategory(id=7, name="Favorites", description="Your favorite anime selections"),
    ]
    app = QApplication(sys.argv)
    dialog = CreateCategory()
    # dialog = AddToCategory(categories)
    dialog.show()
    app.exec()