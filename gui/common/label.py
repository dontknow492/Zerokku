import sys
from typing import Union, Optional

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property, QRectF, Qt, QSize
from PySide6.QtGui import QPainter, QTransform, QColor, QPen, QPixmap, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import ImageLabel, ProgressRing, isDarkTheme, PushButton, BodyLabel, StrongBodyLabel \
    , setCustomStyleSheet

from gui.common.progress_bar import RotableProgressRing



class MyImageLabel(ImageLabel):
    def __init__(self, image: Union[QImage, QPixmap, str, None] = None, parent = None):
        super().__init__(parent)
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








if __name__ == '__main__':
    from qasync import QApplication
    from PySide6.QtWidgets import QStackedLayout
    app = QApplication(sys.argv)
    image = r"D:\Program\Zerokku\demo\001.webp"
    page = MyImageLabel(image)
    page.setProgress(25)
    # page.start_rotation()
    page.show()
    page.resize(800, 600)
    page.zoomStep = 0.5
    page.start_loading()
    page.zoomOut()
    sys.exit(app.exec())