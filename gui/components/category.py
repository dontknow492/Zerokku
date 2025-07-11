from typing import List, Tuple, Optional

import sys
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QFont, QColor, QDrag, QPixmap, QDropEvent, QDragMoveEvent, QDragEnterEvent, QResizeEvent

from PySide6.QtWidgets import QApplication, QVBoxLayout, QGroupBox, QHBoxLayout, QGridLayout, QWidget, QScrollArea
from qfluentwidgets import FlyoutViewBase, SwitchButton, LineEdit, TextEdit, PrimaryPushButton, PushButton, themeColor, \
    setThemeColor, CheckBox, TransparentToolButton, FluentIcon, CardWidget, Flyout

from database import UserCategory
from gui.common import AnimatedToggle, MyLabel, KineticScrollArea


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
        self.title_label = MyLabel("Create Category", 22, weight, self)

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
        self.viewLayout.addWidget(self.title_label)
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


class EditCategory(CreateCategory):
    def __init__(self, category: Optional[UserCategory] = None, parent=None):
        super().__init__(parent)
        self.category = category

        self.title_label.setText("Edit Category")
        if category:
            self.setCategory(category)

    def setCategory(self, category: UserCategory):
        self.clear()
        self.category = category
        self.name_line_edit.setText(category.name)
        self.description_line_edit.setText(category.description)
        self.show_in_shelf_button.setChecked(not category.hidden)

    def _on_ok_clicked(self):
        name = self.name_line_edit.text().strip()
        description = self.description_line_edit.toPlainText().strip()
        show_in_shelf = self.show_in_shelf_button.isChecked()

        if not name:
            self.showInfoSignal.emit("error", "Validation Error", "Category name cannot be empty.")
            return

        if name == self.category.name and self.category.description == description and self.category.hidden != show_in_shelf:
            self.showInfoSignal.emit("warning", "Input Error", "Value are same as before")

        self.acceptSignal.emit(name, description, show_in_shelf)


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


class CategoryCard(CardWidget):
    editCategory = Signal(UserCategory)
    viewToggled = Signal(UserCategory)
    deleteCategory = Signal(UserCategory)
    def __init__(self, category: UserCategory, parent=None):
        super().__init__(parent)
        self.category = category
        self._is_dragging = False

        layout = QHBoxLayout(self)

        self.drag_button = TransparentToolButton(FluentIcon.MOVE, self)
        self.drag_button.setCursor(Qt.CursorShape.OpenHandCursor)

        self.title_label = MyLabel(category.name)
        self.edit_button = TransparentToolButton(FluentIcon.EDIT, self)
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.view_button = TransparentToolButton(FluentIcon.VIEW, self)
        self.view_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_view()

        self.delete_button = TransparentToolButton(FluentIcon.DELETE, self)
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(self.drag_button)
        layout.addWidget(self.title_label, stretch=1)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.view_button)
        layout.addWidget(self.delete_button)

        # Mouse press tracking
        self.drag_button.mousePressEvent = self._drag_button_mouse_press
        self.drag_button.mouseReleaseEvent = self._drag_button_mouse_release
        self.drag_button.mouseMoveEvent = self._drag_button_mouse_move
        self._drag_start_pos = QPoint()

        #signal
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.view_button.clicked.connect(self._on_show_clicked)
        self.delete_button.clicked.connect(lambda: self.deleteCategory.emit(self.category))

    def get_id(self):
        return self.category.id

    def get_name(self):
        return self.category.name

    def get_description(self):
        return self.category.description

    def get_position(self):
        return self.category.position

    def set_position(self, position: int):
        self.category.position = position

    def get_category(self):
        return self.category

    def _on_edit_clicked(self):
        self.editCategory.emit(self.category)

    def _on_show_clicked(self):
        self.category.hidden = not self.category.hidden
        self._update_view()
        self.viewToggled.emit(self.category)

    def _update_view(self):
        icon = FluentIcon.HIDE if self.category.hidden else FluentIcon.VIEW
        self.view_button.setIcon(icon)





    def _drag_button_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
            self.drag_button.setCursor(Qt.CursorShape.ClosedHandCursor)

    def _drag_button_mouse_release(self, event):
        self.drag_button.setCursor(Qt.CursorShape.OpenHandCursor)

    def _drag_button_mouse_move(self, event):
        if event.buttons() & Qt.LeftButton:
            if (event.pos() - self._drag_start_pos).manhattanLength() > QApplication.startDragDistance():
                drag = QDrag(self)
                mime = QMimeData()
                drag.setMimeData(mime)

                # Visual
                pixmap = QPixmap(self.size())
                pixmap.fill(Qt.GlobalColor.transparent)
                self.render(pixmap)
                drag.setPixmap(pixmap)

                drag.exec(Qt.MoveAction)






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

    dialog = CategoryCard(categories[0])
    # dialog = CreateCategory()
    # dialog = AddToCategory(categories)
    dialog.show()
    app.exec()