import sys

from PySide6.QtCore import Property, QAbstractAnimation, QTimer, QPropertyAnimation, Qt
from PySide6.QtGui import QPaintEvent, QPainter, QLinearGradient, QColor, QBrush
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect, QApplication

from qfluentwidgets import isDarkTheme

from gui.common.mylabel import SkeletonMode


class SkimmerWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self._x_radius = 4
        self._y_radius = 4
        self._loading = False
        self._skeleton_mode = SkeletonMode.SHIMMER  # or "opacity"
        self._shimmer_pos = -1.0

        # Opacity animation setup
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._opacity_anim.setDuration(1000)
        self._opacity_anim.setStartValue(0.4)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.finished.connect(self._reverse_opacity_direction)

        self.setOpacity(1)

        #
        # # Shimmer timer
        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.timeout.connect(self._update_shimmer)
        self._shimmer_speed = 0.05

        self.hidden_widgets = list()

    def _hide_layout_items(self):
        layout = self.layout()
        if layout is not None:
            for x in range(layout.count()):
                item = layout.itemAt(x)
                widget = item.widget()
                if widget is not None:
                    if widget.isVisible():
                        widget.hide()
                        self.hidden_widgets.append(widget)

    def _show_layout_items(self):
        for widget in self.hidden_widgets:
            widget.setVisible(True)

    def _reverse_opacity_direction(self):
        current_direction = self._opacity_anim.direction()
        new_direction = QAbstractAnimation.Direction.Backward if current_direction == QAbstractAnimation.Direction.Forward else QAbstractAnimation.Direction.Forward
        self._opacity_anim.setDirection(new_direction)
        self._opacity_anim.start()

    def set_loading(self, value: bool):
        self._loading = value
        if value:
            if self._skeleton_mode == SkeletonMode.OPACITY:
                self._opacity_anim.start()
                self._shimmer_timer.stop()
            elif self._skeleton_mode == SkeletonMode.SHIMMER:
                self._hide_layout_items()
                self._opacity_anim.stop()
                self._shimmer_pos = -0.5
                self._shimmer_timer.start(30)
        else:
            self._opacity_anim.stop()
            self._shimmer_timer.stop()
            self._shimmer_pos = -1.0
            self.update()

    def is_loading(self):
        return self._loading

    def set_skeleton_mode(self, mode: SkeletonMode):
        self._skeleton_mode = mode
        if self._loading:
            self.set_loading(True)  # Restart animation with new mode

    def get_skeleton_mode(self):
        return self._skeleton_mode

    loading = Property(bool, is_loading, set_loading)
    skeleton_mode = Property(SkeletonMode, get_skeleton_mode, set_skeleton_mode)

    def _update_shimmer(self):
        self._shimmer_pos += self._shimmer_speed
        if self._shimmer_pos > 1.5:
            self._shimmer_pos = -0.5
        self.update()

    def setOpacity(self, opacity: float):
        self._opacity_effect.setOpacity(opacity)

    def paintEvent(self, event: QPaintEvent):
        if not self._loading or self._skeleton_mode != SkeletonMode.SHIMMER:
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        if isDarkTheme():
            base_color = QColor(35, 42, 50)  # Slightly brighter than background (25,33,42)
            highlight = QColor(55, 65, 75)  # Used for hover, active, etc.
        else:
            base_color = QColor(200, 200, 200)  # Clean against light gray (242,242,242)
            highlight = QColor(220, 220, 220)  # Subtle hover/active effect

        # base_color = QColor(30, 30, 30) if isDarkTheme() else QColor(200, 200, 200)
        # highlight = QColor(60, 60, 60) if isDarkTheme() else

        shimmer_start = self._shimmer_pos
        shimmer_end = shimmer_start + 0.3

        gradient.setColorAt(0.0, base_color)
        gradient.setColorAt(max(0.0, shimmer_start), base_color)
        gradient.setColorAt(min(1.0, shimmer_start + 0.15), highlight)
        gradient.setColorAt(min(1.0, shimmer_end), base_color)
        gradient.setColorAt(1.0, base_color)

        # painter.fillRect(rect, QBrush(gradient))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self._x_radius, self._y_radius)

    def setXRadius(self, radius: float):
        self._x_radius = radius

    def getXRadius(self):
        return self._x_radius

    x_radius = Property(float, getXRadius, setXRadius)

    def setYRadius(self, radius: float):
        self._y_radius = radius

    def getYRadius(self):
        return self._y_radius

    y_radius = Property(float, getYRadius, setYRadius)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = SkimmerWidget()
    widget.show()
    widget.loading = True
    sys.exit(app.exec())