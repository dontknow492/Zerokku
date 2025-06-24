import sys
from enum import Enum
from typing import Dict, Type

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QApplication
from qfluentwidgets import ComboBox, Action, CheckableMenu, RoundMenu


class EnumComboBox(ComboBox):
    enumChanged = Signal(Enum)
    def __init__(self, enum: Type[Enum] = None, checkable: bool = False, parent: QWidget = None):
        """
        :param enum: the Enum class to populate the combo box with
        :param checkable: if True, items are checkable (multi-select)
        :param parent: parent widget
        """
        super().__init__(parent)
        self.enum = enum
        self.checkable = checkable
        self.enum_map: Dict[str, Enum] = dict()

        self.action_map: Dict[str, Action] = dict()

        if enum:
            self.setEnum(enum)

        self.currentTextChanged.connect(self._on_clicked)

    def setEnum(self, enum: Enum):
        self.enum = enum
        for item in self.enum:
            value = str(item.value)
            value = self._format_str(value)
            self.enum_map[value] = item

        for value in self.enum_map.keys():
            self.addItem(value)

    def _format_str(self, value: str) -> str:
        value = value.replace("_", " ")
        return value.title()


    def _on_clicked(self, value):
        enum = self.enum_map.get(value)
        if enum:
            self.enumChanged.emit(enum)



if __name__ == '__main__':
    class Status(Enum):
        ONGOING = 1
        COMPLETED = 2
        HIATUS = 3
    app = QApplication(sys.argv)

    menu = RoundMenu()


    menu = EnumComboBox(Status)
    # Add actions one by one, Action inherits from QAction and accepts icons of type FluentIconBase

    # widget = DropDownWidgetBase()
    # widget.addSelected('Select All')
    # widget.setMenu(menu)
    menu.show()
    app.exec()

