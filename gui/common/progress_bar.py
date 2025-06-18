import sys

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property, QRectF, QAbstractAnimation
from PySide6.QtGui import QPainter, QPen, Qt
from PySide6.QtWidgets import QApplication
from qfluentwidgets import ProgressRing, isDarkTheme


class RotableProgressRing(ProgressRing):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rotation = 0


        # Setup animation
        self._rotation_anim = QPropertyAnimation(self, b'rotation')
        self._rotation_anim.setStartValue(0)
        self._rotation_anim.setEndValue(360)
        self._rotation_anim.setDuration(2000)
        self._rotation_anim.setLoopCount(-1)
        self._rotation_anim.setEasingCurve(QEasingCurve.Type.Linear)
        # self._rotation_anim.start()


    def startRotation(self, duration: int = 2000,
                      loop_count: int = -1,
                      easing_curve: QEasingCurve = QEasingCurve.Type.Linear):
        self._rotation_anim.setLoopCount(loop_count)
        self._rotation_anim.setDuration(duration)
        self._rotation_anim.setEasingCurve(easing_curve)

        self._rotation_anim.start()

    def stopRotation(self):
        self._rotation_anim.stop()

    def getRotation(self):
        return self._rotation

    def setRotation(self, value):
        self._rotation = value
        self.update()  # trigger repaint

    rotation = Property(float, getRotation, setRotation)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Apply rotation before drawing anything
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._rotation)
        painter.translate(-self.width() / 2, -self.height() / 2)

        cw = self._strokeWidth  # circle thickness
        w = min(self.height(), self.width()) - cw
        rc = QRectF(cw / 2, self.height() / 2 - w / 2, w, w)

        # draw background circle
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        pen = QPen(bc, cw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(rc, 0, 360 * 16)

        if self.maximum() <= self.minimum():
            return

        # draw progress arc
        pen.setColor(self.barColor())
        painter.setPen(pen)
        degree = int(self.val / (self.maximum() - self.minimum()) * 360)
        painter.drawArc(rc, 90 * 16, -degree * 16)

        # draw text (not rotated)
        if self.isTextVisible():
            # Save painter state, reset transform to draw text upright
            painter.save()
            painter.resetTransform()
            self._drawText(painter, self.valText())
            painter.restore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    progress = RotableProgressRing()

    progress.startRotation()
    progress.setValue(34)
    progress.show()
    app.exec()