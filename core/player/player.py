import os
import sys
from pathlib import Path
from typing import Union, Optional

from PySide6.QtGui import QColor, QMouseEvent, QCursor, QKeyEvent
from loguru import logger

# Add the directory where libmpv-2.dll is located to PATH
libmpv_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["PATH"] = libmpv_dir + os.pathsep + os.environ.get("PATH", "")

# Now import mpv
import mpv


import sys
from PySide6.QtCore import QTimer, QUrl, Qt, QPoint, Slot, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from core.player.overlay import PlayerSettings, TopNavigation, BottomNavigation, PlayerAnimationManager
from gui.common import WaitingSpinner

class PlayerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)



        self.video_widget = QWidget(self)
        self.video_widget.installEventFilter(self)
        self.mpv = mpv.MPV(
                        wid=int(self.video_widget.winId()),
                        input_vo_keyboard=True,
                        cache=True,  # ✅ Boolean
                        demuxer_max_bytes=50 * 1024 * 1024,  # ✅ Integer (bytes)
                        demuxer_max_back_bytes=25 * 1024 * 1024,  # ✅ Integer (bytes)
                        cache_pause=True,  # ✅ Boolean
                        cache_pause_initial=True,
                        vo= "gpu",
                        hwdec = "auto-safe",
                        ytdl=True
        )

        #
        self._buffer_time = None
        self._forward_seek_duration = 10
        self._backward_seek_duration = 10
        #layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.video_widget)

        #overlays
        self.top_navigation = TopNavigation(self)
        self.top_navigation.adjustSize()
        self.bottom_navigation = BottomNavigation(self)
        self.bottom_navigation.adjustSize()
        self.settings = PlayerSettings(self)
        self.settings.setVisible(False)
        self.animation_manager = PlayerAnimationManager(self.top_navigation, self.bottom_navigation, self.settings)

        color = QColor("#009faa")
        self.waiting_spinner = WaitingSpinner(line_length=20, lines = 25, line_width=4, radius=20, color=color, parent=self)
        self.waiting_spinner.show()
        self.waiting_spinner.start()


        self._current_time_timer = QTimer(self)
        self._current_time_timer.setSingleShot(False)
        self._current_time_timer.timeout.connect(self._update_current_time)
        self._current_time_timer.setInterval(1000)

        self.mpv.observe_property('duration', self._update_total_time)
        self.mpv.observe_property('cache-buffering-state', self._on_buffering)
        self.mpv.observe_property("paused-for-cache", self._on_buffering)
        # self.mpv.observe_property('file-loaded', self._on_file_loaded)

        self._signal_handler()


    def _signal_handler(self):
        self.bottom_navigation.playPauseSignal.connect(self.toggle_pause)
        self.bottom_navigation.currentChanged.connect(self.set_current_time)
        self.bottom_navigation.playbackFinishedSignal.connect(self._current_time_timer.stop)
        self.bottom_navigation.seekForwardSignal.connect(lambda: self.seek(10))
        self.bottom_navigation.seekBackwardSignal.connect(lambda: self.seek(-10))

    def load_media(self, url: Union[Path, QUrl]):
        if isinstance(url, QUrl):
            str_url = url.toString()
            logger.info(f"Loading media from url: {str_url}")
        elif isinstance(url, Path):
            str_url = str(url)
            logger.info(f"Loading media from local: {str_url}")
        else:
            raise TypeError("url must be QUrl or Path")

        self.mpv.play(str_url)
        self._current_time_timer.start()

    def _update_total_time(self, name, value):
        if value is None:
            return
        logger.debug(f"Updating total time: {value}")
        self.bottom_navigation.duration = value

    def _update_current_time(self, name = "playback_time", value: int = None):
        time = self.mpv.playback_time
        if time is None or self._buffer_time == self.mpv.playback_time:
            self.start_loading()
            return

        self.stop_loading()
        self.bottom_navigation.playback_time = time

    def _on_finished(self, name, value):
        logger.info(f"Finished playback")
        self._current_time_timer.stop()

    def _on_buffering(self, name, value):
        self._buffer_time = self.mpv.playback_time
        logger.info(f"Buffering at: {self._buffer_time}, value: {value}, name: {name}")
        # self.start_loading()

    def setTitle(self, title):
        logger.info(f"Setting Title: {title}")
        self.top_navigation.setTitle(title)

    def setDescription(self, description):
        logger.info(f"Setting Descriptions: {description}")
        self.top_navigation.setDescription(description)

    @Slot(int)
    def set_current_time(self, seconds):
        logger.info(f"Setting current time: {seconds}")
        self.mpv.playback_time = seconds

    def seek(self, duration: int):
        logger.info(f"Seeking {duration} seconds")
        self.mpv.seek(duration)
        self.bottom_navigation.playback_time = self.mpv.playback_time

    def seek_forward(self, duration: Optional[int] = None):
        if not duration:
            duration = self._forward_seek_duration
        self.seek(duration)

    def seek_backward(self, duration: Optional[int] = None):
        if not duration:
            duration = self._backward_seek_duration
        self.seek(-duration)


    @Slot()
    def toggle_pause(self):
        self.mpv.pause = not self.mpv.pause
        if self.mpv.pause:
            self._current_time_timer.stop()
        else:
            self._current_time_timer.start()
        logger.info(f"Pausing: {self.mpv.pause}")

    def set_volume(self, volume: int):
        logger.info(f"Setting volume to: {volume}")
        self.mpv.volume = volume

    def set_playback_speed(self, speed: float):
        logger.info(f"Setting playback speed to: {speed}")
        self.mpv.playback_speed = speed

    def show_nav(self):
        self._updateNavPosition()
        self.animation_manager.show_nav()

    def hide_nav(self):
        if self.bottom_navigation.isVisible() or self.top_navigation.isVisible():
            self.animation_manager.hide_nav()

    def start_loading(self):
        if not self.waiting_spinner.is_spinning:
            logger.info(f"Starting loading")
            self.waiting_spinner.start()
            self.waiting_spinner.setVisible(False)

    def stop_loading(self):
        if self.waiting_spinner.is_spinning:
            logger.info(f"Stopping loading")
            self.waiting_spinner.stop()
            self.waiting_spinner.setVisible(False)




    def mouseDoubleClickEvent(self, event, /):
        super().mouseDoubleClickEvent(event)
        self.hide_nav()

    def keyPressEvent(self, event:QKeyEvent, /):
        logger.info(f"Key pressed: {event.key()}")
        if event.key() == Qt.Key_Escape:
            pass
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_pause()
        elif event.key() == Qt.Key.Key_J:
            self.seek_backward()
        elif event.key() == Qt.Key.Key_L:
            self.seek_forward()
        elif event.key() == Qt.Key.Key_F:
            pass
        elif event.key() == Qt.Key.Key_P and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            pass

        super().keyPressEvent(event)



    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._updateNavSize()

        self.waiting_spinner.move((self.width()-self.waiting_spinner.width())//2,
                                (self.height()-self.waiting_spinner.height())//2)

        # self._updateNavPosition()

    def moveEvent(self, event, /):
        super().moveEvent(event)
        # self._updateNavPosition()

    def _updateNavSize(self):
        self.top_navigation.setFixedWidth(self.width())
        self.top_navigation.move(0, 0)
        self.bottom_navigation.setFixedWidth(self.width())
        self.bottom_navigation.move(0, self.height() - self.bottom_navigation.height())

    def _updateNavPosition(self):
        geometry = self.geometry()
        if hasattr(self, "top_navigation"):
            self.top_navigation.move(geometry.x(), geometry.y())
        if hasattr(self, "bottom_navigation"):
            self.bottom_navigation.move(geometry.x(), geometry.y() + geometry.height() - self.bottom_navigation.height())

    def closeEvent(self, event, /):
        self.top_navigation.close()
        self.bottom_navigation.close()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    path = Path(r"D:\Program\Zerokku\samples\anime\anime.mkv")
    url = QUrl("https://9dd.echo-318-initiative.biz/p3d8/c4/b8nfETuh_AlMZILwIfBQIXvS_ocLj8Wukj0BWmnNTI5qSL8plLy7iQGHMPASTmbDrMW1XVthdFkNBqfo1ZSe28AM2JoXIzJ8MmQ/3/aGxzLzcyMC83MjA,sj6HE7oiDVsIJ7FLYw9UHLGl94f1_mLm_w4B.m3u8")
    player = PlayerWindow()
    player.setTitle("Leveling up with Gods")
    player.setDescription("Episode 7: The tower.")
    player.show()
    player.resize(800, 600)
    player.load_media(path)
    # QTimer.singleShot(1000, player.hide_nav)
    sys.exit(app.exec())