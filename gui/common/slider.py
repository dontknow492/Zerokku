import math
import sys
from typing import Optional, Union

from PySide6.QtCore import Qt, QPoint, Signal, QPropertyAnimation, Property, QEasingCurve, QRectF, QSizeF, QPointF, \
    QSize
from PySide6.QtGui import QColor, QPainter, QEnterEvent, QMouseEvent
from PySide6.QtWidgets import QApplication, QWidget, QSlider, QVBoxLayout
from qfluentwidgets import isDarkTheme, SimpleCardWidget, setTheme, Theme
from qfluentwidgets.common.color import autoFallbackThemeColor
from qfluentwidgets.components.widgets.slider import Slider
from superqt import QRangeSlider, QLabeledRangeSlider


# from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtSignal, pyqtProperty
# from PyQt5.QtGui import QPainter, QColor, QMouseEvent, QEnterEvent
# from PyQt5.QtWidgets import QWidget, QSlider
# from typing import Optional, Union
# from .theme_utils import isDarkTheme, autoFallbackThemeColor


class SliderHandle(QWidget):
    """ Slider handle """

    pressed = Signal()
    released = Signal()

    def __init__(self, parent: QSlider = None):
        super().__init__(parent=parent)
        self.setFixedSize(22, 22)
        self._radius = 5
        self._org_radius = 5
        self.lightHandleColor = QColor()
        self.darkHandleColor = QColor()
        self.radiusAni = QPropertyAnimation(self, b'_radi', self)
        self.radiusAni.setDuration(100)

    @Property(int)
    def _radi(self):
        return self._radius
    @_radi.setter
    def _radi(self, value):
        self._radius = value
        self.update()

    @Property(int)
    def radius(self):
        return self._org_radius

    @radius.setter
    def radius(self, r):
        self._radius = r
        self._org_radius = r
        size = r*2 + 16 #int(r * 2 + math.sqrt(r) * 4)  # or math.log(r + 1) * 6
        # self.setFixedSize(size, size)
        self.setFixedSize(size, size)
        # print(f"Handler Radius: {r}")
        # print(f"Handler Size: {size}")
        self.update()

    def setHandleColor(self, light, dark):
        self.lightHandleColor = QColor(light)
        self.darkHandleColor = QColor(dark)
        self.update()

    def enterEvent(self, e):
        # target_radius = round(self._org_radius * 1.2)
        # target_radius += 0 if self._is_even(target_radius) else 1
        target_radius = max(self._org_radius + 7, 10)
        self._startAni(target_radius)

    def leaveEvent(self, e):
        self._startAni(self._org_radius)

    def mousePressEvent(self, e):
        target_radius = max(4, self._org_radius - 7)
        # target_radius = max(1, round(self._org_radius * 0.8))  # Shrinks by 20%, with lower bound
        # target_radius -= 0 if self._is_even(target_radius) else 1
        self._startAni(target_radius)
        self.pressed.emit()

    def mouseReleaseEvent(self, e):
        self._startAni(self._org_radius )
        self.released.emit()

    def _startAni(self, radius):
        self.radiusAni.stop()
        self.radiusAni.setStartValue(self._radi)
        self.radiusAni.setEndValue(radius)
        self.radiusAni.start()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        isDark = isDarkTheme()
        painter.setPen(QColor(0, 0, 0, 90 if isDark else 25))
        painter.setBrush(QColor(69, 69, 69) if isDark else Qt.GlobalColor.white)

        center = QPointF(self.rect().center())
        painter.drawRoundedRect(self.rect(), self.width() / 2, self.height() / 2)
        painter.setBrush(autoFallbackThemeColor(self.lightHandleColor, self.darkHandleColor))
        # rect = QRectF(center.x() - self._radius, center.y() - self._radius,
        #               self._radius * 2, self._radius * 2)
        rect = QRectF((self.width()-self._radius*2)/2, (self.height()-self._radius*2)/2, self._radius*2, self._radius*2)
        painter.drawRoundedRect(rect, self._radius, self._radius)

    # def minimumSizeHint(self):
    #     size = self.sizeHint()  # Add padding or a reasonable fallback
    #     print("Minimum Size", size)
    #     return size
    #
    # def sizeHint(self):
    #     size = self._radius * 3 + 20 # Slightly larger for aesthetics
    #     print("Size", size)
    #     return QSize(size, size)

class MySlider(Slider):
    def __init__(self, orientation: Qt.Orientation, parent=None):

        super().__init__(orientation, parent)
        self._tick_radius = 1
        self._grove_thickness = 4
        self.handle.deleteLater()
        self.handle = SliderHandle(parent=self)
        # self.handle.radius = 20
        self._tick_color = QColor("gray").lighter() if isDarkTheme() else QColor("black")
        self._light_tick_color = QColor("black")
        self._dark_tick_color = QColor("white")
        # self.setOrientation(orientation)
        self.setContentsMargins(0, 0, 0, 0)

    @property
    def light_tick_color(self):
        return self._light_tick_color

    @light_tick_color.setter
    def light_tick_color(self, color: QColor):
        self._light_tick_color = color

    @property
    def dark_tick_color(self):
        return self._dark_tick_color

    @dark_tick_color.setter
    def dark_tick_color(self, color: QColor):
        self._dark_tick_color = color

    def setOrientation(self, orientation: Qt.Orientation) -> None:
        super().setOrientation(orientation)
        self._fix_cropping()

    def _fix_cropping(self):
        minimum = int(self.handle.radius * 4.4)
        # print("Slider Size: ", minimum)
        if self.orientation() == Qt.Orientation.Horizontal:
            self.setMinimumHeight(self.handle.minimumHeight())
        elif self.orientation() == Qt.Orientation.Vertical:
            self.setMinimumWidth(self.handle.minimumWidth())
        # print("Slider Minimum", self.minimumSize())

    def paintEvent(self, event):
        super().paintEvent(event)  # Optional: call if you want base painting logic
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setBrush(autoFallbackThemeColor(self.light_tick_color, self.dark_tick_color))
        #
        if self.tickInterval():
            self._drawCircleTicks(painter)

    def setGrooveThickness(self, thickness):
        self._grove_thickness = thickness
        # print("\nGroove Thickness: ", thickness)
        handle_radius = round(thickness * 1.2)
        self.handle.radius = handle_radius
        self._fix_cropping()


    def setTickRadius(self, radius):
        self._tick_radius = radius

    def setHandleRadius(self, radius):
        self.handle.radius = radius

    def _drawHorizonGroove(self, painter: QPainter):
        w, r = self.width(), self.handle.width() / 2
        groove_y = r - self._grove_thickness/2
        groove_radius = self._grove_thickness / 2
        painter.drawRoundedRect(QRectF(r, groove_y, w-r*2, self._grove_thickness), groove_radius, groove_radius)

        if self.maximum() - self.minimum() == 0:
            return

        painter.setBrush(autoFallbackThemeColor(self.lightGrooveColor, self.darkGrooveColor))
        aw = (self.value() - self.minimum()) / (self.maximum() - self.minimum()) * (w - r*2)
        painter.drawRoundedRect(QRectF(r, groove_y, aw, self._grove_thickness), groove_radius, groove_radius)

    def _drawVerticalGroove(self, painter: QPainter):
        h, r = self.height(), self.handle.width() / 2
        groove_x = r - self._grove_thickness / 2
        groove_radius = self._grove_thickness / 2
        painter.drawRoundedRect(QRectF(groove_x, r, self._grove_thickness, h-2*r), groove_radius, groove_radius)

        if self.maximum() - self.minimum() == 0:
            return

        painter.setBrush(autoFallbackThemeColor(self.lightGrooveColor, self.darkGrooveColor))
        ah = (self.value() - self.minimum()) / (self.maximum() - self.minimum()) * (h - r*2)
        painter.drawRoundedRect(QRectF(groove_x, r, self._grove_thickness, ah), groove_radius, groove_radius)



    def _drawCircleTicks(self, painter: QPainter):
        tick_interval = self.tickInterval()  # or use (self.maximum() - self.minimum()) // step
        tick_count = (self.maximum() - self.minimum()) // tick_interval
        radius = self._tick_radius
        offset = self.handle.width() / 2


        for i in range(tick_count + 1):
            ratio = i / tick_count
            r = self.handle.width() / 2
            if i == 0: #skip first and last tick
                continue
            elif i == tick_count:
                continue
            if self.orientation() == Qt.Orientation.Horizontal:
                x = ratio * self.grooveLength + offset
                y = self.height() / 2

                painter.drawEllipse(QPointF(x, r), radius, radius)

            else:
                y = ratio * self.grooveLength + offset
                x = self.width() / 2
                painter.drawEllipse(QPointF(r, y), radius, radius)

    def sizeHint(self):
        padding = max(self.handle.radius, self._tick_radius * 2) + 4
        length = 150  # or dynamically based on context
        if self.orientation() == Qt.Orientation.Horizontal:
            return QSize(length, padding * 2)
        else:
            return QSize(padding * 2, length)

    def minimumSizeHint(self):
        return self.sizeHint()


class RangeSlider(QLabeledRangeSlider):
    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Vertical, parent=None):
        super().__init__(orientation, parent)

        self.barColor = autoFallbackThemeColor(QColor(), QColor())

        self.setStyleSheet("color:black")

if __name__ == '__main__':
    # setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    window = SimpleCardWidget()
    layout = QVBoxLayout(window)
    slider = RangeSlider(parent=window)

    layout.addWidget(slider)

    window.show()
    app.exec()
