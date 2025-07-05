import sys
from typing import Union, List

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QIcon

from gui.common import AnimatedToggle
from qfluentwidgets import (SimpleCardWidget, BodyLabel, SubtitleLabel, ComboBox, Slider, SpinBox,
                            DoubleSpinBox, ExpandSettingCard, FluentIconBase, RadioButton, FluentIcon, SettingCard)
from PySide6.QtWidgets import QHBoxLayout, QApplication, QVBoxLayout, QButtonGroup, QWidget, QLabel


class HeaderSettingCard(SettingCard):
    """ Header setting card """
    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.hBoxLayout.addSpacing(8)
        self.titleLabel.setObjectName("titleLabel")



    def addWidget(self, widget: QWidget):
        """ add widget to tail """
        N = self.hBoxLayout.count()
        self.hBoxLayout.removeItem(self.hBoxLayout.itemAt(N - 1))
        self.hBoxLayout.addWidget(widget, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def addSpacing(self, spacing: int):
        self.hBoxLayout.addSpacing(spacing)


class ToggleCard(HeaderSettingCard):
    toggled = Signal(bool)
    def __init__(self, icon: Union[str, QIcon, FluentIconBase, None], title: str, content: str = None,
                 is_enabled: bool = False, parent=None):
        if icon is None:
            icon = FluentIcon.INFO
        super().__init__(icon, title, content, parent)
        self.toggle = AnimatedToggle(parent=self)
        self.toggle.setChecked(is_enabled)
        self.toggle.toggled.connect(self.toggled.emit)

        self.addWidget(self.toggle)

    def isChecked(self) -> bool:
        return self.toggle.isChecked()

    def setChecked(self, checked: bool):
        self.toggle.setChecked(checked)




class ComboBoxCard(HeaderSettingCard):
    def __init__(self, icon: Union[str, QIcon, FluentIconBase, None], title: str, content: str = None, parent=None):
        if icon is None:
            icon = FluentIcon.INFO
        super().__init__(icon, title, content, parent)

        self.combo = ComboBox(parent=self)
        self.addWidget(self.combo)

class SpinBoxCard(HeaderSettingCard):
    valueChanged = Signal(int)
    def __init__(self, icon: Union[str, QIcon, FluentIconBase, None], title: str, content: str = None,
                 parent=None):
        if icon is None:
            icon = FluentIcon.INFO
        super().__init__(icon, title, content, parent)

        self.spinBox = SpinBox(parent=self)
        self.spinBox.valueChanged.connect(self.valueChanged.emit)
        self.addWidget(self.spinBox)

    def value(self):
        return self.spinBox.value()

    def setValue(self, value):
        self.spinBox.setValue(value)

class DoubleSpinBoxCard(HeaderSettingCard):
    valueChanged = Signal(float)
    def __init__(self, icon: Union[str, QIcon, FluentIconBase, None], title: str, content: str = None,
                 parent=None):
        if icon is None:
            icon = FluentIcon.INFO
        super().__init__(icon, title, content, parent)
        self.doubleSpinBox = DoubleSpinBox(parent=self)
        self.doubleSpinBox.valueChanged.connect(self.valueChanged.emit)
        self.addWidget(self.doubleSpinBox)

    def value(self):
        return self.doubleSpinBox.value()

    def setValue(self, value):
        self.doubleSpinBox.setValue(value)


class SpinCard(ExpandSettingCard):
    valueChanged = Signal(int)
    def __init__(self, icon: Union[str, QIcon, FluentIconBase, None], title: str, content: str=None, parent=None):
        if icon is None:
            icon = FluentIcon.INFO
        super().__init__(icon, title, content, parent)
        self.slider = Slider(Qt.Orientation.Horizontal, parent=self)
        self.spinBox = SpinBox(parent=self)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spinBox.valueChanged.connect(self._on_spinbox_changed)

        self.addWidget(self.spinBox)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(self.slider)

        self._adjustViewSize()

    def value(self):
        return self.spinBox.value()

    def setValue(self, value):
        self.spinBox.setValue(value)

    def setRange(self, minimum: int, maximum: int):
        self.slider.setRange(minimum, maximum)
        self.spinBox.setRange(minimum, maximum)

    def _on_slider_changed(self, value: int):
        if self.spinBox.value() != value:
            self.valueChanged.emit(value)
            self.spinBox.blockSignals(True)
            self.spinBox.setValue(value)
            self.spinBox.blockSignals(False)

    def _on_spinbox_changed(self, value: int):
        if self.slider.value() != value:
            self.valueChanged.emit(value)
            self.slider.blockSignals(True)
            self.slider.setValue(value)
            self.slider.blockSignals(False)

    def setTitle(self, title: str):
        label = self.findChild(QLabel, name='titleLabel')
        if label is not None:
            label.setText(title)



class DoubleSpinCard(ExpandSettingCard):
    valueChanged = Signal(float)
    def __init__(self, icon: Union[str, QIcon, FluentIconBase, None], title: str, content: str = None, parent=None):
        if icon is None:
            icon = FluentIcon.INFO
        super().__init__(icon, title, content, parent)

        self._decimal_factor = 100  # Default factor, 2 decimal places

        self.slider = Slider(Qt.Orientation.Horizontal, parent=self)
        self.spinBox = DoubleSpinBox(parent=self)
        self.spinBox.setDecimals(2)
        self.spinBox.setSingleStep(0.01)

        self.spinBox.valueChanged.connect(self._on_spinbox_changed)
        self.slider.valueChanged.connect(self._on_slider_changed)

        self.addWidget(self.spinBox)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(self.slider)

        self._adjustViewSize()

    def value(self):
        return self.spinBox.value()

    def setValue(self, value):
        self.spinBox.setValue(value)

    def _on_spinbox_changed(self, value: float):
        self.valueChanged.emit(value)
        slider_value = int(round(value * self._decimal_factor))
        if self.slider.value() != slider_value:
            self.slider.blockSignals(True)
            self.slider.setValue(slider_value)
            self.slider.blockSignals(False)

    def _on_slider_changed(self, value: int):
        spin_value = value / self._decimal_factor
        if not self._float_equal(self.spinBox.value(), spin_value):
            self.spinBox.blockSignals(True)
            self.spinBox.setValue(spin_value)
            self.valueChanged.emit(spin_value)
            self.spinBox.blockSignals(False)

    def setRange(self, minimum: float, maximum: float):
        decimals = self.spinBox.decimals()
        self._decimal_factor = 10 ** decimals
        self.spinBox.setRange(minimum, maximum)
        self.slider.setRange(int(minimum * self._decimal_factor),
                             int(maximum * self._decimal_factor))

    def _float_equal(self, a: float, b: float, epsilon=1e-6):
        return abs(a - b) < epsilon

class OptionsCard(ExpandSettingCard):
    optionChanged = Signal(str)
    def __init__(self, icon: Union[str, QIcon, FluentIconBase], texts: List[str], selected: int,
                title: str, content: str = None, parent=None):
        if icon is None:
            icon = FluentIcon.INFO
        super().__init__(icon, title, content, parent)


        self.texts = texts or []
        self.choiceLabel = BodyLabel(self)
        self.buttonGroup = QButtonGroup(self)

        self.choiceLabel.setObjectName("titleLabel")
        self.addWidget(self.choiceLabel)

        # create buttons
        self.viewLayout.setSpacing(19)
        self.viewLayout.setContentsMargins(48, 18, 0, 18)
        for index, text in enumerate(texts):
            button = RadioButton(text, self.view)
            self.buttonGroup.addButton(button)
            self.viewLayout.addWidget(button)
            if index == selected:
                button.setChecked(True)
                self.choiceLabel.setText(text)
            # button.setProperty(self.configName, option)

        self._adjustViewSize()
        self.buttonGroup.buttonClicked.connect(self.__onButtonClicked)

    def __onButtonClicked(self, button: RadioButton):
        """ button clicked slot """
        if button.text() == self.choiceLabel.text():
            return


        self.choiceLabel.setText(button.text())
        self.choiceLabel.adjustSize()
        self.optionChanged.emit(button.text())

    def setValue(self, value):
        """ select button according to the value """
        for button in self.buttonGroup.buttons():
            isChecked = button.property(self.configName) == value
            button.setChecked(isChecked)

            if isChecked:
                self.choiceLabel.setText(button.text())
                self.choiceLabel.adjustSize()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # window = OptionsCard(FluentIcon.HOME,
    #                      ["1","2","3","4","5","6","7","8","9"],
    #                      2, "Options", "Select Options"
    #                      )
    # window = ToggleCard(FluentIcon.HOME, "Advance", "this is content")
    # window = ComboBoxCard(FluentIcon.HOME, "Advance", "this is content")
    window = DoubleSpinBoxCard(FluentIcon.HOME, "Advance", "this is content")
    window.valueChanged.connect(print)
    window.show()
    app.exec()