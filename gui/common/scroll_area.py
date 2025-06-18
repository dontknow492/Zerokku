from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScroller, QScrollArea, QScrollerProperties


class KineticScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        #scrollarea
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

        #scroller
        self._scroller = QScroller.scroller(self.viewport())
        props = self._scroller.scrollerProperties()
        props.setScrollMetric(QScrollerProperties.DragVelocitySmoothingFactor, 0.6)
        self._scroller.setScrollerProperties(props)
        self._scroller.grabGesture(self.viewport(), QScroller.LeftMouseButtonGesture)

    @property
    def scroller(self)->QScroller:
        return self._scroller