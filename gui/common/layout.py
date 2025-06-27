from typing import List

from PySide6.QtCore import Signal, QRect, Property, Qt
from PySide6.QtWidgets import QGridLayout, QLayoutItem, QWidget, QLayout, QWidgetItem, QSpacerItem
from loguru import logger

class DynamicGridLayout(QGridLayout):
    def __init__(self, parent=None, columns=1):
        super().__init__(parent)
        self._columns = max(1, columns)  # Ensure at least 1 column
        self._widgets = []  # Track widgets and their properties

    def setColumnCount(self, columns):
        """Set the number of columns and rearrange widgets."""
        columns = max(1, columns)  # Ensure at least 1 column
        if self._columns != columns:
            self._columns = columns
            self._rearrangeWidgets()

    def getColumnCount(self):
        """Return the current number of columns."""
        return self._columns

    def addWidget(self, widget, row=None, column=None, rowSpan=1, columnSpan=1, alignment: Qt.AlignmentFlag = None):
        """Override addWidget to track widgets and their properties."""
        if row is None or column is None:
            row, column = self._calculate_row_col(len(self._widgets))
            self._add_widget(widget, row, column, rowSpan, columnSpan, alignment)
        else:
            super().addWidget(widget, row, column, rowSpan, columnSpan)
        self._widgets.append((widget, rowSpan, columnSpan, alignment))

    def _calculate_row_col(self, index):
        return index// self._columns, index % self._columns

    def insertWidget(self, index, widget, rowSpan=1, columnSpan=1, alignment: Qt.AlignmentFlag = None):
        self._widgets.insert(index, (widget, rowSpan, columnSpan, alignment))
        self._rearrangeWidgets()

    def _rearrangeWidgets(self):
        """Rearrange all widgets based on the current column count."""
        # Remove all widgets from the layout
        for widget, _, _, _ in self._widgets:
            if widget:
                super().removeWidget(widget)

        # Re-add widgets in a grid pattern
        row = 0
        col = 0
        for widget, rowSpan, columnSpan, alignment in self._widgets:
            if widget:
                self._add_widget(widget, row, col, rowSpan, columnSpan, alignment)
                col += columnSpan
                if col >= self._columns:
                    col = 0
                    row += rowSpan

    def _add_widget(self, widget, row, column, rowSpan, columnSpan, alignment):
        if alignment is None:
            super().addWidget(widget, row, column, rowSpan, columnSpan)
        else:
            super().addWidget(widget, row, column, rowSpan, columnSpan, alignment)

    # def _insert_widget(self, widget, row, col, rowSpan, columnSpan, alignment: Qt.AlignmentFlag = None):


    def clear(self):
        """Remove all widgets from the layout and clear the internal list."""
        for widget, _, _ in self._widgets:
            if widget:
                super().removeWidget(widget)
                widget.deleteLater()
        self._widgets.clear()


class ResponsiveLayout(QGridLayout):
    layoutChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._columns = 1
        self._max_columns = 1
        self.setSpacing(6)
        self._pre_geometry: QRect = self.geometry()

    def addWidget(self, widget: QWidget):
        column = self.columnCount()
        index = self.count()

        row = index // column
        col = index % column
        super().addWidget(widget, row, col)

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
        if columns == self._max_columns:
            return
        self._max_columns = max(1, columns)
        self._update_arrangement(self.geometry())

    def columnCount(self):
        return self._columns

    def relayout(self):
        self._doLayout(self._columns)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        if self._pre_geometry.width() == rect.width():
            return
        self._update_arrangement(rect)

    def _update_arrangement(self, rect: QRect) -> None:
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