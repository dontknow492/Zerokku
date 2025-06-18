import sys
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QApplication
from qfluentwidgets import TransparentToolButton, BodyLabel, Slider, SimpleCardWidget, FluentIcon, FlyoutViewBase


class VolumeWidget(SimpleCardWidget):
    """A widget to control volume with mute functionality"""

    volumeChanged = Signal(int)
    muteStateChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._saved_volume = 50  # Store last non-zero volume
        self._is_muted = False

        # Initialize UI components
        self.volume_button = TransparentToolButton(FluentIcon.VOLUME)
        self.volume_slider = Slider(Qt.Orientation.Horizontal, self)
        self.volume_label = BodyLabel("50", self)

        # Configure components
        self.volume_button.setToolTip("Toggle mute")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setToolTip("Adjust volume")
        self.volume_label.setMinimumWidth(30)  # Prevent layout jumping
        self.volume_label.setAlignment(Qt.AlignCenter)

        # Setup layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.volume_button)
        layout.addWidget(self.volume_slider)
        layout.addWidget(self.volume_label)

        # Connect signals
        self.volume_slider.valueChanged.connect(self._on_volume_slider_changed)
        self.volume_button.clicked.connect(self.toggle_volume)

    def toggle_volume(self):
        """Toggle between muted and unmuted states"""
        self.set_mute(not self._is_muted)

    def _on_volume_slider_changed(self, value: int):
        """Handle volume slider changes"""
        if self._is_muted and value > 0:
            self.set_mute(False)

        self.set_volume(value)

    def set_volume(self, volume: int):
        """Set volume to specified value"""
        try:
            volume = max(0, min(100, volume))  # Clamp volume between 0-100
            self.volume_slider.blockSignals(True)

            self.volume_slider.setValue(volume)
            self.volume_label.setText(str(volume))

            if volume > 0:
                self._saved_volume = volume
                self._is_muted = False
                self.volume_button.setIcon(FluentIcon.VOLUME)
            else:
                self._is_muted = True
                self.volume_button.setIcon(FluentIcon.MUTE)

            self.volumeChanged.emit(volume)

        finally:
            self.volume_slider.blockSignals(False)

    def set_mute(self, mute: bool):
        """Set mute state"""
        if mute == self._is_muted:
            return

        self._is_muted = mute
        self.muteStateChanged.emit(mute)

        if mute:
            self.set_volume(0)
        else:
            self.set_volume(self._saved_volume)

    def volume(self) -> int:
        """Get current volume"""
        return self.volume_slider.value()

    def is_muted(self) -> bool:
        """Get mute state"""
        return self._is_muted

    def setEnabled(self, enabled: bool):
        """Override to ensure consistent state when enabled/disabled"""
        super().setEnabled(enabled)
        self.volume_button.setEnabled(enabled)
        self.volume_slider.setEnabled(enabled)
        self.volume_label.setEnabled(enabled)


class VolumeFlyoutWidget(FlyoutViewBase):
    """A widget to control volume with mute functionality"""
    volumeChanged = Signal(int)
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)

        self.slider = Slider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider_label = BodyLabel("50", self)

        self.slider.valueChanged.connect(self._on_volume_slider_changed)

        layout.addWidget(self.slider)
        layout.addWidget(self.slider_label)

    def _on_volume_slider_changed(self, value: int):
        """Handle volume slider changes"""
        self.slider_label.setText(str(value))
        self.volumeChanged.emit(value)

    def setVolume(self, volume: int):
        """Set volume to specified value"""
        self.blockSignals(True)
        self.slider.setValue(volume)
        self.slider_label.setText(str(volume))
        self.blockSignals(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    volume = VolumeFlyoutWidget(None)
    volume.show()
    sys.exit(app.exec())