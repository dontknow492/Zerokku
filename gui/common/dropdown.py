import sys
from enum import Enum
from typing import Optional, List, Dict

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QPainter, QAction
from PySide6.QtWidgets import QWidget, QApplication, QHBoxLayout
from qfluentwidgets import ComboBox, CheckableMenu, RoundMenu, Action, DropDownPushButton, MenuAnimationType, \
    isDarkTheme, FluentIcon, SimpleCardWidget, LineEdit, FlowLayout, CardWidget

from enum import Enum

from qfluentwidgets.common.animation import TranslateYAnimation
from qfluentwidgets.components.widgets.button import DropDownButtonBase, PushButton


from gui.common import OutlinedChip

class DropDownWidgetBase(CardWidget):
    """ Drop down widget base class """
    itemAdded = Signal(str)
    itemRemoved = Signal(str)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isPressed = False
        self.isHover = False
        self._menu = None
        self.isMenuVisible = False
        self.selected: Dict[str, PushButton] = dict()
        self.arrowAni = TranslateYAnimation(self)

        self.clicked.connect(self.onClick)

        self.itemLayout = FlowLayout(self)
        self.itemLayout.setContentsMargins(4, 4, 4, 4)

    def addSelected(self, value: str, chip: bool = False):
        if value in self.selected:
            return
        if chip:
            button = OutlinedChip(icon = FluentIcon.CLOSE, text = value, parent = self)
        else:
            button = PushButton(icon = FluentIcon.CLOSE, text = value, parent = self)
        button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        button.setCursor(Qt.PointingHandCursor)

        self.itemLayout.addWidget(button)
        self.selected[value] = button
        self.itemAdded.emit(value)

        button.clicked.connect(lambda: self.removeSelected(value))

    def removeAll(self):
        self.itemLayout.takeAllWidgets()
        self.selected.clear()

    def removeSelected(self, value):
        pass
        button = self.selected.get(value)
        if button:
            self.itemLayout.removeWidget(button)
            button.setParent(None)
            button.deleteLater()
            self.selected.pop(value)
        #
            self.itemRemoved.emit(value)

    def onClick(self):
        self._showMenu()


    def setMenu(self, menu: RoundMenu):
        self._menu = menu

    def menu(self) -> RoundMenu:
        return self._menu

    def _showMenu(self):
        if not self.menu():
            return

        self.isMenuVisible = True

        menu = self.menu()
        menu.view.setMinimumWidth(self.width())
        menu.view.adjustSize()
        menu.adjustSize()

        # determine the animation type by choosing the maximum height of view
        x = -menu.width() // 2 + menu.layout().contentsMargins().left() + self.width() // 2
        pd = self.mapToGlobal(QPoint(x, self.height()))
        hd = menu.view.heightForAnimation(pd, MenuAnimationType.DROP_DOWN)

        pu = self.mapToGlobal(QPoint(x, 0))
        hu = menu.view.heightForAnimation(pu, MenuAnimationType.PULL_UP)

        if hd >= hu:
            menu.view.adjustSize(pd, MenuAnimationType.DROP_DOWN)
            menu.exec(pd, aniType=MenuAnimationType.DROP_DOWN)
        else:
            menu.view.adjustSize(pu, MenuAnimationType.PULL_UP)
            menu.exec(pu, aniType=MenuAnimationType.PULL_UP)

    def _hideMenu(self):
        self.isMenuVisible = False
        if self.menu():
            self.menu().hide()

    def _drawDropDownIcon(self, painter, rect):
        if isDarkTheme():
            FluentIcon.ARROW_DOWN.render(painter, rect)
        else:
            FluentIcon.ARROW_DOWN.render(painter, rect, fill="#646464")

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        if self.isHover:
            painter.setOpacity(0.8)
        elif self.isPressed:
            painter.setOpacity(0.7)

        rect = QRectF(self.width() - 22, self.height() /
                      2 - 5 + self.arrowAni.y, 10, 10)
        self._drawDropDownIcon(painter, rect)

    def enterEvent(self, e):
        super().enterEvent(e)
        self.isHover = True

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.isHover = False

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        # self._showMenu()
        self.isPressed = True

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.isPressed = False

class EnumDropDownWidget(DropDownWidgetBase):
    """Take enum and set it value in combo box and on select return Enum"""
    def __init__(self, enum: Enum = None, checkable: bool = False, parent: QWidget = None):
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


        if checkable:
            self._menu = CheckableMenu(parent = self)
        else:
            self._menu = RoundMenu(parent = self)


        self.setMenu(self._menu)

        self.itemRemoved.connect(self._on_item_removed)

        if enum:
            self.setEnum(enum)

    def setEnum(self, enum: Enum):
        self.enum = enum
        self.enum_map = {str(e.value): e for e in self.enum}

        for value in self.enum_map.keys():
            self._add_action(value)

    def _add_action(self, value: str):
        action = Action(value, checkable=self.checkable, triggered= lambda: self._on_clicked(value))
        self.action_map[value] = action
        self._menu.addAction(action)

    def _on_clicked(self, value):
        if self.checkable:
            if value in self.selected.keys():
                self.removeSelected(value)
            else:
                self.addSelected(value)
        else:
            self.removeAll()
            self.addSelected(value)

    def _on_item_removed(self, value):
        print("item removed", value)
        action = self.action_map.get(value)
        if action:
            action.setChecked(False)










if __name__ == '__main__':
    class Status(Enum):
        ONGOING = 1
        COMPLETED = 2
        HIATUS = 3
    app = QApplication(sys.argv)

    menu = RoundMenu()

    # Add actions one by one, Action inherits from QAction and accepts icons of type FluentIconBase
    menu.addAction(Action(FluentIcon.COPY, 'Copy', triggered=lambda: print("Copy successful")))
    menu.addAction(Action(FluentIcon.CUT, 'Cut', triggered=lambda: print("Cut successful")))

    # Add actions in batches
    menu.addActions([
        Action(FluentIcon.PASTE, 'Paste'),
        Action(FluentIcon.CANCEL, 'Undo')
    ])

    # Add a separator
    menu.addSeparator()

    menu.addAction(QAction('Select All', shortcut='Ctrl+A'))


    widget = EnumDropDownWidget(Status, False)
    # widget = DropDownWidgetBase()
    # widget.addSelected('Select All')
    # widget.setMenu(menu)
    widget.show()
    app.exec()