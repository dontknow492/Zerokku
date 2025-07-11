import sys
from enum import Enum
from typing import Union, Optional

from PySide6.QtCore import Property, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton
from PySide6.QtCore import (
    Qt, QSize, QPoint, QPointF, QRectF,
    QEasingCurve, QPropertyAnimation, QSequentialAnimationGroup,
    Slot, Property)

from PySide6.QtWidgets import QCheckBox, QApplication
from PySide6.QtGui import QColor, QBrush, QPaintEvent, QPen, QPainter
from qfluentwidgets import PushButton, FluentIconBase, setCustomStyleSheet, ToolButton, FluentIcon, \
    TransparentToolButton
from qfluentwidgets.common import icon


class RoundedPushButton(PushButton):
    def __init__(
            self,
            text: str = None,
            icon: Union[QIcon, str, FluentIconBase] = None,
            parent = None
    ):
        super().__init__(parent)
        self.setText(text)
        if icon:
            self.setIcon(icon)

        self._radius = 16
        qss = self._build_style()
        setCustomStyleSheet(self, qss, qss)

    def _build_style(self):
        return f"""
            PushButton{{
            border-radius:{self._radius}px;}}
"""

    def setRadius(self, radius: int):
        self._radius = radius
        qss = self._build_style()
        setCustomStyleSheet(self, qss, qss)

    def getRadius(self):
        return self._radius

    radius = Property(int, getRadius, setRadius)

class RoundedToolButton(ToolButton):
    def __init__(
            self,
            icon: Union[QIcon, str, FluentIconBase] = None,
            parent=None
    ):
        super().__init__(parent)
        self.setIcon(icon)
        self.setIconSize(QSize(18, 18))

        self._radius = 17
        # self.setCursor(Qt.CursorShape.PointingHandCursor)

        qss = self._build_style()
        setCustomStyleSheet(self, qss, qss)

    def _build_style(self):
        return f"""
                ToolButton{{
                border-radius:{self._radius}px;}}
    """

    def setRadius(self, radius: int):
        self._radius = radius
        qss = self._build_style()
        setCustomStyleSheet(self, qss, qss)

    def getRadius(self):
        return self._radius

    radius = Property(int, getRadius, setRadius)

class AnimatedToggle(QCheckBox):
    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)

    def __init__(self,
                 parent=None,
                 bar_color=Qt.gray,
                 checked_color: QColor=QColor("#00B0FF"),
                 handle_color: QColor=Qt.white,
                 pulse_unchecked_color: QColor=QColor("#44999999"),
                 pulse_checked_color: QColor= QColor("#4400B0EE")
                 ):
        super().__init__(parent)

        # Save our properties on the object via self, so we can access them later
        # in the paintEvent.

        self._bar_color = bar_color
        self._checked_color = checked_color
        self._handle_color = handle_color
        self._pulse_unchecked_color = pulse_unchecked_color
        self._pulse_checked_color = pulse_checked_color

        self._bar_brush = QBrush(bar_color)
        self._bar_checked_brush = QBrush(QColor(checked_color).lighter())

        self._handle_brush = QBrush(handle_color)
        self._handle_checked_brush = QBrush(checked_color)

        self._pulse_unchecked_animation = QBrush(pulse_unchecked_color)
        self._pulse_checked_animation = QBrush(pulse_checked_color)

        # Setup the rest of the widget.
        self.setContentsMargins(8, 0, 8, 0)
        self._handle_position = 0

        self._pulse_radius = 0

        self.animation = QPropertyAnimation(self, b"handle_position", self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(200)  # time in ms

        self.pulse_anim = QPropertyAnimation(self, b"pulse_radius", self)
        self.pulse_anim.setDuration(350)  # time in ms
        self.pulse_anim.setStartValue(10)
        self.pulse_anim.setEndValue(20)

        self.animations_group = QSequentialAnimationGroup()
        self.animations_group.addAnimation(self.animation)
        self.animations_group.addAnimation(self.pulse_anim)

        self.stateChanged.connect(self.setup_animation)




    def sizeHint(self):
        return QSize(58, 45)

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    @Slot(int)
    def setup_animation(self, value):
        self.animations_group.stop()
        if value:
            self.animation.setEndValue(1)
        else:
            self.animation.setEndValue(0)
        self.animations_group.start()

    def paintEvent(self, e: QPaintEvent):

        contRect = self.contentsRect()
        handleRadius = round(0.24 * contRect.height())

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(self._transparent_pen)
        barRect = QRectF(
            0, 0,
            contRect.width() - handleRadius, 0.40 * contRect.height()
        )
        barRect.moveCenter(contRect.center())
        rounding = barRect.height() / 2

        # the handle will move along this line
        trailLength = contRect.width() - 2 * handleRadius

        xPos = contRect.x() + handleRadius + trailLength * self._handle_position

        if self.pulse_anim.state() == QPropertyAnimation.Running:
            p.setBrush(
                self._pulse_checked_animation if
                self.isChecked() else self._pulse_unchecked_animation)
            p.drawEllipse(QPointF(xPos, barRect.center().y()),
                          self._pulse_radius, self._pulse_radius)

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setPen(self._light_grey_pen)
            p.setBrush(self._handle_brush)

        p.drawEllipse(
            QPointF(xPos, barRect.center().y()),
            handleRadius, handleRadius)

        p.end()

    @Property(float)
    def handle_position(self):
        return self._handle_position

    @handle_position.setter
    def handle_position(self, pos):
        """change the property
        we need to trigger QWidget.update() method, either by:
            1- calling it here [ what we doing ].
            2- connecting the QPropertyAnimation.valueChanged() signal to it.
        """
        self._handle_position = pos
        self.update()

    @Property(float)
    def pulse_radius(self):
        return self._pulse_radius

    @pulse_radius.setter
    def pulse_radius(self, pos):
        self._pulse_radius = pos
        self.update()

    @property
    def bar_color(self):
        return self._bar_color

    @bar_color.setter
    def bar_color(self, value: QColor):
        self._bar_color = value
        self._bar_brush.setColor(value)


    @property
    def handle_color(self):
        return self._handle_color

    @handle_color.setter
    def handle_color(self, value: QColor):
        self._handle_color = value
        self._handle_brush.setColor(value)

    @property
    def pulse_unchecked_color(self):
        return self._pulse_unchecked_color

    @pulse_unchecked_color.setter
    def pulse_unchecked_color(self, value: QColor):
        self._pulse_unchecked_color = value
        self._pulse_unchecked_animation.setColor(value)

    @property
    def pulse_checked_color(self):
        return self._pulse_checked_color

    @pulse_checked_color.setter
    def pulse_checked_color(self, value: QColor):
        self._pulse_checked_color = value
        self._pulse_checked_animation.setColor(value)

    @property
    def checked_color(self):
        return self._checked_color

    @checked_color.setter
    def checked_color(self, value: QColor):
        self._checked_color = value
        self._handle_checked_brush.setColor(value)
        self._bar_checked_brush.setColor(value.lighter())




class ColoredToolButton(ToolButton):
    def __init__(self, icon: FluentIconBase, color: QColor, parent=None):
        ToolButton.__init__(self, parent=parent)

        self._fluent_icon = icon
        self._color = color

        self.setIcon(self._fluent_icon.icon(color = color))

    def setColorIcon(self, icon: FluentIconBase):
        self._fluent_icon = icon
        self.setIcon(self._fluent_icon.icon(color=self.color))

    def setColor(self, color: QColor):
        self._color = color
        super().setIcon(self._fluent_icon.icon(color=color))

    def getColor(self):
        return self._color

    color = Property(QColor, getColor, setColor)

class TransparentColoredToolButton(TransparentToolButton):
    def __init__(self, icon: FluentIconBase, color: QColor, parent=None):
        ToolButton.__init__(self, parent)

        self._fluent_icon = icon
        self._color = color

        self.setIcon(self._fluent_icon.icon(color=color))

    def setColorIcon(self, icon: FluentIconBase):
        self._fluent_icon = icon
        self.setIcon(self._fluent_icon.icon(color=self.color))

    def setColor(self, color: QColor):
        self._color = color
        super().setIcon(self._fluent_icon.icon(color=color))

    def getColor(self):
        return self._color

    color = Property(QColor, getColor, setColor)


from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt


class ButtonState(Enum):
    UNCHECKED = 0
    PARTIAL_CHECKED = 1
    CHECKED = 2

class TriStateButton(PushButton):


    def __init__(self, text, icon, parent=None):
        super().__init__(parent)
        self.STATES = {
            ButtonState.UNCHECKED: (text, QColor(Qt.GlobalColor.transparent), icon),
            ButtonState.PARTIAL_CHECKED: (text, QColor("orange"), icon),
            ButtonState.CHECKED: (text, QColor("green"), icon),
        }
        self.setText(text)
        self.setIcon(icon)
        self.state: ButtonState = ButtonState.UNCHECKED
        self._border_radius = 4
        self.update_visual()
        self.clicked.connect(self.next_state)



    def set_border_radius(self, radius):
        self._border_radius = radius
        self.update_visual()

    def get_border_radius(self):
        return self._border_radius

    borderRadius = Property(int, get_border_radius, set_border_radius)

    def setStateProperty(self, state: ButtonState, text: Optional[str] = None,
                        background_color: Optional[QColor] = None, icon: Optional = None):
        state_value = self.STATES.get(state)
        text = text if text else state_value[0]
        background_color = background_color if background_color else state_value[1]
        icon = icon if icon else state_value[2]
        if icon is None or icon.isNull():
            icon = self.icon()

        state_value = (text, background_color, icon)
        self.STATES[state] = state_value


    def next_state(self):
        if self.state == ButtonState.PARTIAL_CHECKED:
            self.state = ButtonState.CHECKED
        elif self.state == ButtonState.CHECKED:
            self.state = ButtonState.UNCHECKED
        else:
            self.state = ButtonState.PARTIAL_CHECKED
        self.update_visual()

    def update_visual(self):
        state_values = self.STATES[self.state]

        super().setText(state_values[0])
        if not state_values[2]:
            self.setIcon(state_values[2])
        color = state_values[1]
        # if color and color.name() != QColor().name():
        if self.state == ButtonState.UNCHECKED:
            style = f"PushButton {{background-color: transparent; border-radius: {self.borderRadius}}};"
        else:
            style = f"PushButton {{background-color: {state_values[1].name()}; border-radius: {self.borderRadius}}};"
        setCustomStyleSheet(self, style, style)

    def get_state(self):
        return self.state

    def set_state(self, state: ButtonState):
        self.state = state
        self.update_visual()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tri-State PushButton Example")
        layout = QVBoxLayout()

        self.button = TriStateButton("", icon = FluentIcon.INFO)
        self.button.borderRadius = 16
        layout.addWidget(self.button)

        self.label = QLabel("Current State: Unchecked")
        layout.addWidget(self.label)

        # self.button.clicked.connect(self.update_label)
        self.setLayout(layout)

    # def update_label(self):
    #     states = ["Unchecked", "Partially Checked", "Checked"]
    #     self.label.setText(f"Current State: {states[self.button.get_state()]}")


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()



# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     button = TransparentColoredToolButton(FluentIcon.TAG, QColor('blue'))
#     button.show()
#     button.radius = 16
#     app.exec()