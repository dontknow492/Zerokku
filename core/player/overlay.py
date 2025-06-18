import sys
from email.mime import audio
from enum import Enum
from typing import Union

from PySide6.QtCore import Qt, QObject, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint, Signal, \
    Property
from PySide6.QtGui import QPainter, QColor, QKeySequence
from loguru import logger
from qfluentwidgets import SimpleCardWidget, FluentIcon, TransparentToolButton, StrongBodyLabel, BodyLabel, \
    SwitchButton, SubtitleLabel, Slider, Flyout
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QApplication, QGroupBox
from gui.common import AnimatedToggle

from utils import IconManager, trim_time_string
from gui.components import VolumeWidget, VolumeFlyoutWidget
from gui.common import KineticScrollArea
from gui.components import OptionsCard, ToggleCard, SpinCard


class HwDecoding(Enum):
    AUTO_SAFE = "auto-safe"
    VAAPI = "vaapi"
    DXVA2 = "dxva2"
    CUDA = "cuda"
    D3D11VA = "d3d11va"
    VIDEOTOOLBOX = "videotoolbox"
    NVDEC = "nvdec"
    MEDIACODEC = "mediacodec"
    NO = "no"

    def __str__(self):
        return self.value

class AudioChannels(Enum):
    AUTO = "auto"
    MONO = "mono"
    STEREO = "stereo"


    def __str__(self):
        return self.value

class TopNavigation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.back_button = TransparentToolButton(FluentIcon.LEFT_ARROW, self)
        self.title_label = SubtitleLabel(self)
        self.description_label = BodyLabel(self)
        self.auto_play_button = TransparentToolButton(FluentIcon.PAUSE_BOLD, self)
        self.subtitle_button = TransparentToolButton(IconManager.SUBTITLE, self)
        self.audio_button = TransparentToolButton(FluentIcon.MUSIC, self)
        self.quality_button = TransparentToolButton(IconManager.HQ_FILL, self)
        self.more_button = TransparentToolButton(IconManager.MORE_VERTICAL, self)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        main_layout.addWidget(self.back_button)
        vbox_layout = QVBoxLayout()
        vbox_layout.setContentsMargins(15, 0, 0, 0)
        vbox_layout.setSpacing(0)
        vbox_layout.addWidget(self.title_label)
        vbox_layout.addWidget(self.description_label)
        main_layout.addLayout(vbox_layout, stretch=1)
        main_layout.addWidget(self.auto_play_button)
        main_layout.addWidget(self.subtitle_button)
        main_layout.addWidget(self.audio_button)
        main_layout.addWidget(self.quality_button)
        main_layout.addWidget(self.more_button)

    def setTitle(self, title: str):
        self.title_label.setText(title)

    def setDescription(self, description: str):
        self.description_label.setText(description)

class BottomNavigation(QWidget):
    playPauseSignal = Signal()
    currentChanged = Signal(int)
    playbackFinishedSignal = Signal()
    seekForwardSignal = Signal()
    seekBackwardSignal = Signal()
    settingsClickedSignal = Signal()
    viewModeChangeSignal = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_paused = False

        self.slider = Slider(Qt.Orientation.Horizontal, self)
        self.current_label = StrongBodyLabel("00:00", self)
        self.total_label = StrongBodyLabel("00:00", self)
        self.play_button = TransparentToolButton(FluentIcon.PAUSE_BOLD, self)
        self.seek_forward_button = TransparentToolButton(FluentIcon.SKIP_FORWARD, self)
        self.seek_back_button = TransparentToolButton(FluentIcon.SKIP_BACK, self)
        self.lock_button = TransparentToolButton(FluentIcon.INFO, self)
        self.settings_button = TransparentToolButton(FluentIcon.SETTING, self)
        self.fit_button = TransparentToolButton(FluentIcon.FULL_SCREEN, self)

        self.volume_button = TransparentToolButton(FluentIcon.VOLUME, self)
        self.volume_flyout = VolumeFlyoutWidget()

        self._setup_ui()
        self._signal_handler()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        main_layout.addWidget(self.slider)

        hbox_layout = QHBoxLayout(self)
        hbox_layout.addWidget(self.play_button)
        hbox_layout.addWidget(self.volume_button)
        hbox_layout.addWidget(self.current_label)
        hbox_layout.addWidget(StrongBodyLabel("/"))
        hbox_layout.addWidget(self.total_label)

        hbox_layout.addStretch()

        hbox_layout.addWidget(self.seek_back_button)
        hbox_layout.addWidget(self.seek_forward_button)
        hbox_layout.addWidget(self.lock_button)
        hbox_layout.addWidget(self.settings_button)
        hbox_layout.addWidget(self.fit_button)


        main_layout.addLayout(hbox_layout, stretch=1)


    def _signal_handler(self):
        self.volume_button.clicked.connect(self.show_volume_flyout)
        self.play_button.clicked.connect(self.playPauseSignal.emit)
        self.play_button.clicked.connect(self.toggle_pause)
        self.seek_forward_button.clicked.connect(self.seekForwardSignal.emit)
        self.seek_back_button.clicked.connect(self.seekBackwardSignal.emit)

        self.slider.valueChanged.connect(self._on_slider_value_changed)

    def _on_slider_value_changed(self, value):
        self.currentChanged.emit(value)
        str_value = trim_time_string(value)
        self.current_label.setText(str_value)

    def show_volume_flyout(self):
        Flyout.make(self.volume_flyout, self.volume_button, isDeleteOnClose=False)

    def set_current_time(self, sec: Union[int, float]):
        if sec is None:
            return

        if isinstance(sec, float):
            sec = int(sec)

        if self.slider.value() == sec:
            return

        self.slider.valueChanged.disconnect(self._on_slider_value_changed)
        self.slider.setValue(sec)
        if sec == self.slider.maximum():
            self.playbackFinishedSignal.emit()
        time_string = trim_time_string(sec)
        self.current_label.setText(time_string)
        self.slider.valueChanged.connect(self._on_slider_value_changed)

    def get_current_time(self):
        return self.slider.value()

    playback_time = Property(float, get_current_time, set_current_time)

    def set_total_time(self, sec: int):
        if not sec or sec < 0:
            return
        self.total_label.setText(trim_time_string(sec))
        self.slider.setRange(0, sec)

    def get_total_time(self):
        return self.slider.maximum()

    duration = Property(float, get_total_time, set_total_time)

    def toggle_pause(self):
        if self.is_paused:
            self.play_button.setIcon(FluentIcon.PAUSE_BOLD)
        else:
            self.play_button.setIcon(FluentIcon.PLAY_SOLID)

        self.is_paused = not self.is_paused

class PlayerSettings(KineticScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.container = QWidget(self)
        self.container_layout = QVBoxLayout(self.container)
        self.setWidgetResizable(True)
        self.setWidget(self.container)

        hwcodec = {hw.value.upper(): hw for hw in HwDecoding}
        audio_channels = {audio.value.upper(): audio in AudioChannels for audio in AudioChannels}

        self.reduce_debanding = ToggleCard(FluentIcon.INFO, "Reduce debanding", is_enabled=True, parent=self)
        self.smooth_scaling = ToggleCard(FluentIcon.INFO, "Smooth scaling", is_enabled=True, parent=self)
        self.subtitle_blending = ToggleCard(FluentIcon.INFO, "Subtitle blending", is_enabled=True, parent=self)
        self.hardware_decoding = OptionsCard(FluentIcon.INFO, list(hwcodec.keys()), 0, "Hardware Decoding", parent=self)
        self.audio_channels = OptionsCard(FluentIcon.INFO, list(audio_channels.keys()), 0, "Audio channels", parent=self)


        self.adjust_gamma = SpinCard(FluentIcon.INFO, "Gamma", parent=self)
        self.adjust_gamma.setRange(-100, 100)
        self.adjust_hue = SpinCard(FluentIcon.INFO, "Hue", parent=self)
        self.adjust_hue.setRange(-100, 100)
        self.adjust_contrast = SpinCard(FluentIcon.INFO, "Contrast", parent=self)
        self.adjust_contrast.setRange(-100, 100)
        self.adjust_saturation = SpinCard(FluentIcon.INFO, "Saturation", parent=self)
        self.adjust_saturation.setRange(-100, 100)
        self.adjust_bright = SpinCard(FluentIcon.INFO, "Brightness", parent=self)
        self.adjust_bright.setRange(-100, 100)

        self.setup_ui()

    def setup_ui(self):
        view_group = QGroupBox("View", self)
        view_layout = QVBoxLayout(view_group)
        filter_group = QGroupBox("Custom Filters", self)
        filter_layout = QVBoxLayout(filter_group)

        view_layout.addWidget(self.hardware_decoding)
        view_layout.addWidget(self.audio_channels)
        view_layout.addWidget(self.reduce_debanding)
        view_layout.addWidget(self.smooth_scaling)
        view_layout.addWidget(self.subtitle_blending)



        filter_layout.addWidget(self.adjust_gamma)
        filter_layout.addWidget(self.adjust_hue)
        filter_layout.addWidget(self.adjust_contrast)
        filter_layout.addWidget(self.adjust_saturation)
        filter_layout.addWidget(self.adjust_bright)

        self.container_layout.addWidget(view_group)
        self.container_layout.addWidget(filter_group)
        self.container_layout.addStretch()


class PlayerAnimationManager(QObject):
    def __init__(self, title_bar: QWidget, bottom_nav: QWidget, setting_widget: QWidget, parent: QObject = None):
        super().__init__(parent)
        self.title_bar = title_bar
        self.bottom_nav = bottom_nav
        self._is_nav_hide_ani = False
        self.setting_widget = setting_widget
        self._is_setting_hide_ani = False

        self.title_animation = QPropertyAnimation(self.title_bar, b"pos")
        self.navigation_animation = QPropertyAnimation(self.bottom_nav, b"pos")
        self.settings_animation = QPropertyAnimation(self.setting_widget, b"pos")

        for anim in (self.title_animation, self.navigation_animation, self.settings_animation):
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.title_animation)
        self.anim_group.addAnimation(self.navigation_animation)

        #finished
        self.anim_group.finished.connect(self._toggle_nav)
        self.settings_animation.finished.connect(self._toggle_settings)

    def hide_nav(self):
        logger.debug("Hiding Navigation")
        self.settings_animation.stop()
        self.anim_group.stop()

        self.title_animation.setStartValue(self.title_bar.pos())
        self.title_animation.setEndValue(QPoint(self.title_bar.x(), -self.title_bar.height()))

        self.navigation_animation.setStartValue(self.bottom_nav.pos())
        self.navigation_animation.setEndValue(QPoint(self.bottom_nav.x(), self.bottom_nav.height() + self.bottom_nav.y()))

        self._is_nav_hide_ani = True
        self.anim_group.start()

    def show_nav(self):
        self._is_nav_hide_ani = False
        self._toggle_nav()
        self.settings_animation.stop()
        self.anim_group.stop()

        self.title_animation.setStartValue(QPoint(self.title_bar.x(), -self.title_bar.height()))
        self.title_animation.setEndValue(self.title_bar.pos())


        self.navigation_animation.setStartValue(QPoint(self.bottom_nav.x(), self.bottom_nav.pos().y() + self.bottom_nav.height()))
        self.navigation_animation.setEndValue(self.bottom_nav.pos())

        logger.debug("Showing Navigation")
        self.anim_group.start()

    def show_settings(self, direction: int = 0):
        """direction 0 from left, 1 from right"""

        self.settings_animation.stop()
        if direction == 0:
            point = QPoint(-self.setting_widget.x() - self.setting_widget.width(), self.setting_widget.y())
        else:
            point = QPoint(self.setting_widget.x() + self.setting_widget.width(), self.setting_widget.y())

        self.setting_widget.setVisible(True)
        self.settings_animation.setStartValue(point)
        self.settings_animation.setEndValue(self.setting_widget.pos())

        self._is_setting_hide_ani = False
        self.settings_animation.start()

    def hide_settings(self, direction: int = 0):
        """direction 0 from left, 1 from right"""
        logger.debug("Hiding Settings")
        # self.settings_animation.stop()
        if direction == 0:
            point = QPoint(-self.setting_widget.x() - self.setting_widget.width(), self.setting_widget.y())
        else:
            point = QPoint(self.setting_widget.x() + self.setting_widget.width(), self.setting_widget.y())
        self.settings_animation.setStartValue(self.setting_widget.pos())
        self.settings_animation.setEndValue(point)

        self._is_setting_hide_ani = True
        self.settings_animation.start()

    def _toggle_nav(self):
        if self._is_nav_hide_ani:
            self.title_bar.setVisible(False)
            self.bottom_nav.setVisible(False)
        else:
            self.title_bar.setVisible(True)
            self.bottom_nav.setVisible(True)

    def _toggle_settings(self):

        if self._is_setting_hide_ani:
            self.setting_widget.setVisible(False)
        else:
            self.setting_widget.setVisible(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BottomNavigation()
    window.show()
    app.exec()