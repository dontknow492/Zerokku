# QWidget + MPV Example

import os
import sys

# Add the directory where libmpv-2.dll is located to PATH
libmpv_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["PATH"] = libmpv_dir + os.pathsep + os.environ.get("PATH", "")

# Now import mpv
import mpv


from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PySide6.QtOpenGLWidgets import QOpenGLWidget
import mpv
import sys
import os
from loguru import logger

class MPVPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anime Player - QWidget")
        self.resize(800, 450)

        # Widget where video will render
        self.video_widget = QOpenGLWidget(self)
        layout = QVBoxLayout(self.video_widget)
        self.setCentralWidget(self.video_widget)

        # Add libmpv directory to PATH (if needed)
        os.environ["PATH"] = os.path.dirname(__file__) + os.pathsep + os.environ["PATH"]

        # Setup MPV to render into the widget using winId()
        self.mpv = mpv.MPV(wid=int(self.video_widget.winId()), log_handler=print, input_default_bindings=True, ytdl = True)

        # Play button
        btn = QPushButton("Play YouTube Video")
        btn.clicked.connect(self.play_video)
        layout.addWidget(btn)

    def play_video(self):
        url = "https://9dd.project-zenith-220.biz/peem/c4/b8nfETuh_AlMZILwIdA5HTPHn_8Wy5WT90RxDzTIaY4DKL4F3JnLtR2XEfxOXkb7qbC4cRcJdURUT5fombiCr7QpvfcGdzJ8MmQ/3/aGxzLzcyMC83MjA,sj6HE7oiDVsIJ7FLYw9UHLGl9-r48g.m3u8"  # Example
        self.mpv.play(url)
        self.media_info()

    def media_info(self):
        logger.debug(self.mpv.properties)

app = QApplication(sys.argv)
window = MPVPlayer()
window.show()
app.exec()
