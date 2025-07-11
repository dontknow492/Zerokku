import sys
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QResizeEvent, QDropEvent, QDragMoveEvent, QDragEnterEvent, QFont, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QApplication
from qfluentwidgets import setThemeColor

from database import UserCategory
from gui.common import MyLabel
from gui.components import CategoryCard, EditCategory


class CategoriesInterface(QScrollArea):
    orderChanged = Signal(list)

    def __init__(self, categories: Optional[List[UserCategory]] = None, parent=None):
        super().__init__(parent)
        self.categories: List[UserCategory] = []
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAcceptDrops(True)

        # self.categories = categories
        self.edit_category_widget = EditCategory()
        self.edit_category_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.edit_category_widget.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint |
                                                 Qt.NoDropShadowWindowHint)
        self.edit_category_widget.acceptSignal.connect(self._on_category_edited)
        self.edit_category_widget.cancelSignal.connect(self.edit_category_widget.hide)

        self._move_edit_window_to_center()

        self.central_widget = QWidget(self)
        self.central_widget.setAcceptDrops(True)
        self.setWidget(self.central_widget)
        self.setWidgetResizable(True)

        self.vlayout = QVBoxLayout(self.central_widget)
        self.vlayout.setAlignment(Qt.AlignTop)
        self.vlayout.setSpacing(8)

        self.title_label = MyLabel("Edit Category", 22, QFont.Weight.DemiBold, self)
        self.vlayout.addWidget(self.title_label)

        if categories:
            self.set_categories(categories)

    def set_categories(self, categories: List[UserCategory]):
        self.clear_categories()
        self.categories = categories
        for category in self.categories:
            self.add_category_card(category)

    def add_category_card(self, category: UserCategory):
        card = CategoryCard(category)
        card.editCategory.connect(self._on_edit_clicked)

        self.vlayout.addWidget(card)

    def clear_categories(self):
        """Remove all CategoryCard widgets from the layout and clear the category list."""
        count = self.vlayout.count()
        for i in reversed(range(count)):
            item = self.vlayout.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, CategoryCard):
                widget.setParent(None)
                widget.deleteLater()

        self.categories.clear()

    def _on_edit_clicked(self, category: UserCategory):
        self.edit_category_widget.setCategory(category)

        self.edit_category_widget.show()

    def _on_category_edited(self, name: str, description: str, show_in_self: bool):
        if self.category.hidden != show_in_self and self.category.name == name and self.category.description == description:
            return
        self.category.name = name
        self.category.description = description
        self.category.hidden = not show_in_self
        self.categoryEdited.emit(self.category)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        event.accept()

    def dropEvent(self, event: QDropEvent):
        source_card = event.source()
        if not isinstance(source_card, CategoryCard):
            return

        pos = event.pos()
        insert_index = self._find_insert_position(pos.y(), exclude_widget=source_card)

        self.vlayout.removeWidget(source_card)
        self.vlayout.insertWidget(insert_index, source_card)

        event.acceptProposedAction()
        self._emit_reordered_categories()

    def _find_insert_position(self, y_pos: int, exclude_widget: QWidget) -> int:
        for i in range(self.vlayout.count()):
            item = self.vlayout.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if not widget or widget is exclude_widget or not isinstance(widget, CategoryCard):
                continue

            widget_y = widget.y()
            if y_pos < widget_y + widget.height() // 2:
                return i
        return self.vlayout.count()

    def _emit_reordered_categories(self):
        updated_order = []
        for index in range(self.vlayout.count()):
            item = self.vlayout.itemAt(index)
            if not item:
                continue
            widget = item.widget()
            if isinstance(widget, CategoryCard):
                category_id = widget.get_id()
                widget.set_position(index)
                updated_order.append(widget.get_category())  # index = new position

        self.orderChanged.emit(updated_order)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._move_edit_window_to_center()

    def _move_edit_window_to_center(self):
        center = self.geometry().center()
        self.edit_category_widget.move(center.x() - self.edit_category_widget.width() // 2,
                                       center.y() - self.edit_category_widget.height() // 2)


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
    dialog = CategoriesInterface(categories)


    #
    def on_order_changed(categories: List[UserCategory]):
        for category in categories:
            print(f"{category.name} -> {category.id} -> {category.position}")


    #
    dialog.orderChanged.connect(on_order_changed)
    dialog.show()
    app.exec()