from typing import List

from PySide6.QtCore import Signal, QRect
from PySide6.QtWidgets import QGridLayout, QLayoutItem
from loguru import logger

class ResponsiveLayout(QGridLayout):
    layoutChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._columns = 1
        self._max_columns = 1
        self._items: List[QLayoutItem] = []
        self.setSpacing(6)
        self._pre_geometry: QRect = self.geometry()

    def clearLayout(self):
        items: List[QLayoutItem] = []
        while self.count():
            item = self.takeAt(0)
            items.append(item)
        return items

    def setColumnCount(self, columns: int):
        columns = max(1, min(columns, max(1, self.count())))
        if self._columns != columns:
            self._columns = columns
            self.relayout()

    def setMaximumColumnCount(self, columns: int):
        self._max_columns = max(1, columns)

    def columnCount(self):
        return self._columns

    def relayout(self):
        self._doLayout(self._columns)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        if self._pre_geometry.width() == rect.width():
            return
        columns = self.columnCount()

        is_shrinking = self._pre_geometry.width() > rect.width()

        responsive_col = self.calculateColumns(rect, is_shrinking)
        if columns != responsive_col:
            self._doLayout(responsive_col)
            self._columns = responsive_col
        self._pre_geometry = rect

    def _doLayout(self, column: int):
        items = self.clearLayout()
        for index, item in enumerate(items):
            if item:
                row = index // column
                col = index % column
                super().addItem(item, row, col)
        self.layoutChanged.emit()

    def calculateColumns(self, rect: QRect, is_shrinking: bool) -> int:
        if self._max_columns == 1:
            return 1
        margins = self.contentsMargins()
        available_width = rect.width() - margins.left() - margins.right()

        total_width = 0
        columns = 0

        for i in range(self.count()):
            item = self.itemAt(i)
            if item is None:
                continue

            hint_width = item.sizeHint().width()
            if columns > 0:
                total_width += self.horizontalSpacing()
            total_width += hint_width

            if total_width > available_width:
                break

            if abs(total_width - available_width) <= 10:
                logger.debug(f"total_width: {total_width}, available_width: {available_width}, columns: {columns}")
                if not is_shrinking:
                    columns += 1
                    logger.debug(f"Columns After: {columns}, Shrinking: {columns}")
                break
            columns += 1

        return max(1, min(self._max_columns, columns))