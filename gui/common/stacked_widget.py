from enum import Enum, auto

from PySide6.QtWidgets import QStackedWidget, QWidget, QGraphicsOpacityEffect, QApplication
from PySide6.QtCore import QPropertyAnimation, QPoint, QAbstractAnimation, QEasingCurve, Signal, QParallelAnimationGroup

# from gui.common import
# from qasync import

from gui.common.animation import AnimationManager, AnimationDirection, AnimationType

# class AnimationDirection(Enum):
#     LEFT = auto()
#     RIGHT = auto()
#     TOP = auto()
#     BOTTOM = auto()

class SlideAniInfo:
    """Pop up animation info"""

    def __init__(self, widget: QWidget, deltaX: int, deltaY: int, ani: QPropertyAnimation):
        self.widget = widget
        self.deltaX = deltaX
        self.deltaY = deltaY
        self.ani = ani


class AniStackedWidget(QStackedWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.animation_manager = AnimationManager()

    def addWidget(self, widget: QWidget):
        super().addWidget(widget)

    def setCurrentWidget(self, widget: QWidget, duration: int = 300, distance: int = 300):
        self.setCurrentIndex(self.indexOf(widget), duration, distance)

    def setCurrentIndex(self, index, duration: int = 300, distance: int = 300):
        pre_index = self.indexOf(self.currentWidget())
        des_index = index
        super().setCurrentIndex(des_index)
        self.slide(pre_index, des_index, duration, distance)

    # def setAnimation(self):

    def slide(self, from_index: int, to_index: int, duration: int = 3, distance: int = 300):
        widget = self.currentWidget()
        if from_index > to_index:
            direction = AnimationDirection.LEFT
        elif from_index < to_index:
            direction = AnimationDirection.RIGHT
        elif from_index == to_index:
            direction = AnimationDirection.BOTTOM
        else:
            direction = AnimationDirection.TOP
        self.animation_manager.slide_in(widget, direction=direction, distance=distance, duration=duration)



class SlideAniStackedWidget(QStackedWidget):
    """Stacked widget with alternating slide animation (left-to-right and right-to-left)"""

    aniFinished = Signal()
    aniStart = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.aniInfos = []  # type: List[SlideAniInfo]
        self._nextIndex = None
        self._ani = None
        self._width = self.width()  # Store widget width for slide calculations

    def resizeEvent(self, event):
        """Update width on resize to ensure correct slide animations"""
        super().resizeEvent(event)
        self._width = self.width()

    def addWidget(self, widget, deltaX=0, deltaY=76):
        """ add widget to window

        Parameters
        -----------
        widget:
            widget to be added

        deltaX: int
            the x-axis offset from the beginning to the end of animation

        deltaY: int
            the y-axis offset from the beginning to the end of animation
        """
        super().addWidget(widget)

        self.aniInfos.append(SlideAniInfo(
            widget=widget,
            deltaX=deltaX,
            deltaY=deltaY,
            ani=QPropertyAnimation(widget, b'pos')
        ))

    def removeWidget(self, widget: QWidget):
        """Remove widget and its animation info"""
        index = self.indexOf(widget)
        if index == -1:
            return
        self.aniInfos.pop(index)
        super().removeWidget(widget)

    def setCurrentIndex(self, index: int, showNextWidgetDirectly: bool = True,
                        duration: int = 250, easingCurve=QEasingCurve.OutQuad,
                        slide_direction: str = "alternate"):
        """Set current widget to display with slide animation

        Parameters
        ----------
        index: int
            the index of widget to display
        showNextWidgetDirectly: bool
            whether to show next widget directly when animation starts
        duration: int
            animation duration
        easingCurve: QEasingCurve
            the interpolation mode of animation
        slide_direction: str
            slide direction: 'left' (left-to-right), 'right' (right-to-left), or 'alternate' (based on index)
        """
        if index < 0 or index >= self.count():
            raise Exception(f'The index `{index}` is illegal')

        if index == self.currentIndex():
            return

        if self._ani and self._ani.state() == QAbstractAnimation.Running:
            self._ani.stop()
            self.__onAniFinished()

        self._nextIndex = index
        nextAniInfo = self.aniInfos[index]
        nextWidget = nextAniInfo.widget
        self._ani = nextAniInfo.ani

        # Determine slide direction
        if slide_direction == "alternate":
            direction = 1 if index % 2 == 0 else -1  # Even: left-to-right, Odd: right-to-left
        else:
            direction = 1 if slide_direction == "left" else -1  # Explicit direction

        startX = direction * self._width
        endX = 0
        startPos = QPoint(startX, nextWidget.y())
        endPos = QPoint(endX, nextWidget.y())

        self.__setAnimation(self._ani, startPos, endPos, duration, easingCurve)
        nextWidget.setVisible(showNextWidgetDirectly)
        super().setCurrentIndex(index)

        # Start animation
        self._ani.finished.connect(self.__onAniFinished)
        self._ani.start()
        self.aniStart.emit()

    def setCurrentWidget(self, widget, showNextWidgetDirectly: bool = True,
                         duration: int = 250, easingCurve=QEasingCurve.OutQuad,
                         slide_direction: str = "alternate"):
        """Set current widget with slide animation

        Parameters
        ----------
        widget:
            the widget to be displayed
        showNextWidgetDirectly: bool
            whether to show next widget directly when animation starts
        duration: int
            animation duration
        easingCurve: QEasingCurve
            the interpolation mode of animation
        slide_direction: str
            slide direction: 'left' (left-to-right), 'right' (right-to-left), or 'alternate' (based on index)
        """
        self.setCurrentIndex(
            self.indexOf(widget), showNextWidgetDirectly, duration, easingCurve, slide_direction)

    def __setAnimation(self, ani, startValue, endValue, duration, easingCurve=QEasingCurve.Linear):
        """Set the config of animation"""
        ani.setEasingCurve(easingCurve)
        ani.setStartValue(startValue)
        ani.setEndValue(endValue)
        ani.setDuration(duration)

    def __onAniFinished(self):
        """Animation finished slot"""
        if self._ani:
            self._ani.finished.disconnect()
        super().setCurrentIndex(self._nextIndex)
        self.aniFinished.emit()


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QLabel, QPushButton
    app = QApplication(sys.argv)
    window = AniStackedWidget()
    for x in range(10):
        button = QPushButton(str(x))
        button.clicked.connect(lambda : window.setCurrentIndex(window.currentIndex()+1))
        window.addWidget(button)
    window.show()
    app.exec()