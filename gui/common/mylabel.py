import sys
from pathlib import Path
from typing import Union, Optional

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property, QRectF, Qt, QSize, QTimer, QAbstractAnimation
from PySide6.QtGui import QPainter, QTransform, QColor, QPen, QPixmap, QImage, QFont, QPaintEvent, QLinearGradient, \
    QBrush, QFontMetrics, QTextLayout, QTextOption
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsAnchorLayout, QGraphicsOpacityEffect

from qfluentwidgets import ImageLabel, ProgressRing, isDarkTheme, PushButton, BodyLabel, StrongBodyLabel \
    , setCustomStyleSheet, SimpleCardWidget, FluentLabelBase, getFont

from gui.common.progress_bar import RotableProgressRing
from gui.common.spinner import WaitingSpinner

from enum import Enum, auto

class SkeletonMode(Enum):
    OPACITY = auto()
    SHIMMER = auto()

class MyLabel(FluentLabelBase):
    def __init__(self, text: Optional[str]=None, font_size: int = 14, weight: QFont.Weight = QFont.Weight.Normal, parent: QWidget = None):
        self._font_size = font_size
        self._weight = weight
        FluentLabelBase.__init__(self, text)



    def getFont(self):
        return getFont(self._font_size, self._weight)

    @property
    def font_size(self):
        return self._font_size

    @property
    def weight(self):
        return self._weight


class MyImageLabel(ImageLabel):
    def __init__(self, image: Union[QImage, QPixmap, str, None] = None, parent = None):
        ImageLabel.__init__(self, parent)
        self.setImage(image)
        if isinstance(image, str):
            image = QImage(image)
        self._original_image = image
        self._zoom_factor = 1.0
        self._zoom_step = 0.15

        self.progress_ring = RotableProgressRing(self)
        self.progress_ring.setStyleSheet("background-color: transparent;")
        if image is not None:
            self.progress_ring.hide()

    def setImage(self, image: Union[QImage, QPixmap, str, None]):
        if image is None:
            # raise
            return
        super().setImage(image)
        if isinstance(image, str):
            image = QImage(image)
        self._original_image = image
        self.updateGeometry()

    def setPixmap(self, pixmap: QPixmap):
        self.setImage(pixmap)

    def setZoomStep(self, step: float):
        self._zoom_step = step

    def getZoomStep(self):
        return self._zoom_step

    zoomStep = Property(float, getZoomStep, setZoomStep)

    def zoomIn(
            self
    ):
        self._zoom_factor *= (1+self._zoom_step)
        self._zoom()

    def zoomOut(
            self
    ):
        self._zoom_factor *= (1 - self._zoom_step)
        self._zoom()

    def resetZoom(self):
        if self._zoom_factor == 1.0:
            return
        self._zoom_factor = 1
        self._zoom()

    def _zoom(self):
        width = int(self._original_image.width() * self._zoom_factor)
        height = int(self._original_image.height() * self._zoom_factor)
        self.setScaledSize(QSize(width, height))
        # scaled_image = self._original_image.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio,
        #                                         Qt.TransformationMode.SmoothTransformation)
        # super().setImage(scaled_image)

    def setProgress(self, progress: int):
        self.progress_ring.setVisible(True)
        progress = max(min(progress, 100), 0)
        self.progress_ring.setValue(progress)

    def start_rotation(self):
        self.progress_ring.startRotation()

    def stop_rotation(self):
        self.progress_ring.stopRotation()

    def start_loading(self):
        self.start_rotation()

    def stop_loading(self):
        self.stop_rotation()

    def resizeEvent(self, e):
        if self.progress_ring.isVisible():
            self.progress_ring.move((self.width()-self.progress_ring.width())//2,
                                    (self.height()-self.progress_ring.height()) //2)


class WaitingLabel(ImageLabel):
    def __init__(self, image: Union[QImage, QPixmap, str, None] = None, parent = None):
        ImageLabel.__init__(self, parent)
        self.setImage(image)


        #overlay
        self.dark_overlay = SimpleCardWidget(self)
        self.dark_overlay.setStyleSheet("background-color: green;")
        self.dark_overlay.setFixedSize(self.width(), self.height())
        layout= QVBoxLayout(self.dark_overlay)
        self.waiting_spinner = WaitingSpinner(self)
        self.waiting_spinner.setVisible(True)
        layout.addWidget(self.waiting_spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        self.dark_overlay.setVisible(False)

    def setImage(self, image: Union[QImage, QPixmap, str, None, Path]):
        if image is None:
            return
        if isinstance(image, Path):
            image = str(image.absolute())
        super().setImage(image)
        self.stop()

    def setPixmap(self, pixmap: QPixmap):
        self.setImage(pixmap)

    def start(self):
        self.dark_overlay.show()
        self.waiting_spinner.start()

    def stop(self):
        self.waiting_spinner.stop()
        self.dark_overlay.hide()

    def resizeEvent(self, e):
        self.dark_overlay.setFixedSize(self.size())


class MultiLineElideLabel(MyLabel):
    def __init__(self, text='', max_lines=3, font_size=14, weight=QFont.Weight.Normal, elide: bool = True, parent=None):
        super().__init__(text, font_size, weight, parent)
        self.isElide = elide
        self._max_lines = max_lines
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.full_text = text
        self._elide_time()

    def setText(self, text: str):
        self.full_text = text
        self._elide_time()
        # self._update_elided_text()
    def _elide_time(self):
        if not self.isElide:
            super().setText(self.full_text)
            return
        metrics = QFontMetrics(self.font())
        elide = metrics.elidedText(self.full_text, Qt.ElideRight, (self.width()- 18) * self._max_lines - self.width() / 5)
        if metrics.width(elide) > self.width():
            self.setMinimumHeight(metrics.height() * 2)
        else:
            self.setMinimumHeight(metrics.height())

        texto = elide
        super(MultiLineElideLabel, self).setText(texto)

    def set_elide(self, elide: bool):
        self.isElide = elide
        self._elide_time()

    def get_elide(self):
        return self.isElide

    elide = Property(bool, get_elide, set_elide)

    def set_max_lines(self, max_lines: int):
        self._max_lines = max_lines
        self._elide_time()

    def get_max_lines(self):
        return self._max_lines

    max_lines = Property(int, get_max_lines, set_max_lines)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide_time()



if __name__ == '__main__':
    from qasync import QApplication
    from PySide6.QtWidgets import QStackedLayout
    app = QApplication(sys.argv)
    label = MultiLineElideLabel("Hello this is multi line elide test so here it is used fo rthesing purpose so be patient.")
    #
    label.show()
    label.elide = False
    label.elide = True
    # image = r"D:\Program\Zerokku\demo\001.webp"
    # page = MyImageLabel(image)
    # # page.start()
    # page.show()
    # # page.loading = True
    # page.skeleton_mode = SkeletonMode.OPACITY
    # page.scaledToWidth(300)

    # page.scaledToHeight(200)
    sys.exit(app.exec())