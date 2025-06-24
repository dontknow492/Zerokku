import sys
from typing import Union, Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QSurface, QIcon, Qt
from PySide6.QtWidgets import QPushButton, QWidget, QApplication
from qfluentwidgets import PushButton, FluentIcon, FluentIconBase, setCustomStyleSheet, toggleTheme, setTheme, Theme
from qfluentwidgets.common.icon import SvgIconEngine, writeSvg


class Chip(PushButton):
    def __init__(
        self,
        text: str,
        icon: Union[FluentIconBase, QIcon, str] = None,
        primary_color: QColor = QColor("#0078D7"),
        outline_color: QColor = QColor("#0078D7"),
        surface_color: QColor = QColor("#E6F0FA"),
        border_radius: int = 16,
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self._primary_color = primary_color
        self._outline_color = outline_color
        self._surface_color = surface_color
        self._border_radius = border_radius
        self.setText(text)
        self.setIcon(icon)



        # self.setStyleSheet(self._build_style())
        light_qss, dark_qss = self._build_style()
        setCustomStyleSheet(self, light_qss, dark_qss)

    def setIcon(self, icon: Union[FluentIconBase, QIcon, str]):
        if isinstance(icon, FluentIconBase):
            icon = icon.icon(color = self._primary_color)
        if isinstance(icon, str):
            icon = SvgIconEngine(writeSvg(icon, fill = self._primary_color))


        super().setIcon(icon)
        self.setIconSize(QSize(18, 18))


    def _build_style(self):
        left_padding = 8 if not self.icon().isNull() else 16

        light = f"""
            QPushButton {{
                background-color: {self._surface_color.name()};
                color: {self._primary_color.name()};
                border: 1px solid {self._outline_color.name()};
                border-radius: {self._border_radius}px;
                padding: 0px;
            }}
            QPushButton:checked {{
                background-color: {self._primary_color.name()};
                color: white;
                border: 1px solid {self._primary_color.name()};
            }}
            QPushButton:hover {{
                background-color: {self._surface_color.lighter(110).name()};
            }}
            """

        dark_surface = self._surface_color.darker(150).name()
        dark_hover = QColor(self._surface_color).lighter(115).name()
        dark_text = self._primary_color.name()

        dark = f"""
            PushButton {{
                background-color: {dark_surface};  /* Darker background */
                color: {dark_text};               /* Softer light text */
                border: 1px solid {self._outline_color.darker(120).name()};
                border-radius: {self._border_radius}px;
                padding: 7px 16px 7px {left_padding}px;
            }}
            PushButton:checked {{
                background-color: {self._primary_color.name()};
                color: black;
                border: 1px solid {self._primary_color.name()};
            }}
            PushButton:hover {{
                background-color: {dark_hover};
            }}
        """

        return light, dark

class OutlinedChip(Chip):
    def __init__(
            self,
            text: str,
            icon: Union[FluentIconBase, QIcon, str] = None,
            primary_color: QColor = QColor("#0078D7"),
            border_radius: int = 16,
            parent = None,
    ):
        super().__init__(text, icon, primary_color, primary_color.darker(110), primary_color.lighter(180),
                        border_radius=border_radius, parent = parent )


if __name__ == "__main__":
    # setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    window = OutlinedChip("Hello World", FluentIcon.HOME, QColor("red"))

    window.show()
    window.adjustSize()
    app.exec()


