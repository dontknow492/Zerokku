import sys
from enum import Enum
from typing import Dict, Type, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QApplication
from qfluentwidgets import ComboBox, Action, CheckableMenu, RoundMenu

from AnillistPython import MediaType


class EnumComboBox(ComboBox):
    enumChanged = Signal(Enum)
    defaultSignal = Signal()
    def __init__(self, enum: Type[Enum] = None, parent: QWidget = None, add_default: bool = True, default_text: str = "Any"):
        """
        :param enum: Enum class to populate the combo box with
        :param parent: Parent QWidget
        :param add_default: If True, adds a default option (e.g., "Any")
        :param default_text: Text for the default option
        """
        super().__init__(parent)
        self.enum = enum
        self.enum_map: Dict[str, Enum] = dict()
        self.action_map: Dict[str, Action] = dict()
        self._default_text = default_text
        self._has_default_text = add_default

        if enum:
            self.setEnum(enum)

        self.currentTextChanged.connect(self._on_clicked)

    def setEnum(self, enum: Type[Enum]):
        self.enum = enum
        self.clear()
        self.enum_map.clear()

        if self._has_default_text:
            self.addItem(self._default_text)  # Placeholder has no enum value

        for item in self.enum:
            value = self._format_str(str(item.value))
            self.enum_map[value] = item
            self.addItem(value)
            # print(value, item)

    def getCurrentEnum(self) -> Optional[Type[Enum]]:
        """Return the selected Enum value, or None if default/placeholder is selected."""
        text = self.currentText()
        if (self._has_default_text or self.text() == self._default_text) and text == self._placeholderText:
            return None
        return self.enum_map.get(text)

    def _format_str(self, value: str) -> str:
        return value.replace("_", " ").title()

    def _on_clicked(self, value: str):
        enum = self.enum_map.get(value)
        if enum:
            self.enumChanged.emit(enum)
        else:
            if self.text() == self._default_text:
                self.defaultSignal.emit()



if __name__ == '__main__':
    class Status(Enum):
        ONGOING = 1
        COMPLETED = 2
        HIATUS = 3

    data = {1: Status.ONGOING, 2: Status.COMPLETED, 3: Status.HIATUS}
    # print(data.get(1))
    app = QApplication(sys.argv)

    menu = RoundMenu()


    menu = EnumComboBox(MediaType, add_default=False)
    enum = menu.getCurrentEnum()
    print(type(enum))
    print(enum.value)
    # Add actions one by one, Action inherits from QAction and accepts icons of type FluentIconBase

    # widget = DropDownWidgetBase()
    # widget.addSelected('Select All')
    # widget.setMenu(menu)
    menu.show()
    app.exec()

