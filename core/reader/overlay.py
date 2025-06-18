import math
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, Dict
from typing import Union

from PySide6.QtCore import QUrl, QEvent, QPoint, QRect, QPointF, QObject, QPropertyAnimation, \
    QEasingCurve, QParallelAnimationGroup, QSize, Slot, QTimer, QAbstractAnimation
from PySide6.QtCore import Qt, Signal, QSettings, Property
from PySide6.QtGui import QPixmap, QImage, QColor, QPalette
from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWidgets import QFrame, QStackedLayout, QSlider, QStackedWidget, QGraphicsOpacityEffect
from PySide6.QtWidgets import QGroupBox, QApplication, QWidget, QVBoxLayout, QHBoxLayout
from loguru import logger
from qfluentwidgets import PushButton, ExpandSettingCard, FluentIcon, SpinBox, Slider, BodyLabel, StrongBodyLabel, \
    SubtitleLabel, SimpleCardWidget, CardWidget
from qfluentwidgets import TitleLabel, TransparentToolButton, setCustomStyleSheet

from gui.common import KineticScrollArea, AnimatedToggle
# zerokku
from gui.common import SlideAniStackedWidget, MyImageLabel, MySlider
from gui.components import ToggleCard, ComboBoxCard, SpinCard, DoubleSpinCard, OptionsCard, SpinBoxCard
# from gui.common.page import PageLabel


class ReadMode(Enum):
    LEFT2RIGHT = "Left to Right"
    RIGHT2LEFT = "Right to Left"
    CONTINUOUS_VERTICAL = "Continuous Vertical"
    CONTINUOUS_VERTICAL_GAPS = "Continuous Vertical Gaps"

class FitMode(Enum):
    DEFAULT = "Default"
    FULLSCREEN = "Fullscreen" #FitWidth
    ORIGINAL = "Original"
    PAGED = "Paged" #One page at a Screen

    def is_scaled(self):
        return self != FitMode.ORIGINAL

class PositionFlags(Enum):
    LEFT = "Left"
    RIGHT = "Right"


class ZoomWidget(SimpleCardWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.value = 1

        layout = QHBoxLayout(self)
        self.label = SubtitleLabel("100%", self)
        layout.addWidget(self.label)

        # Set up opacity effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        # Fade-out animation
        self.fade_out_ani = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_ani.setDuration(300)
        self.fade_out_ani.setStartValue(1.0)
        self.fade_out_ani.setEndValue(0.0)
        self.fade_out_ani.finished.connect(self.hide)
        self.fade_out_ani.setEasingCurve(QEasingCurve.InOutQuad)

        # Fade-in animation
        self.fade_in_ani = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_ani.setDuration(300)
        self.fade_in_ani.setStartValue(0.0)
        self.fade_in_ani.setEndValue(1.0)
        self.fade_in_ani.setEasingCurve(QEasingCurve.InOutQuad)

    def setZoom(self, zoom: float):
        self.value = zoom
        value = int(zoom * 100)
        self.label.setText(f"{value}%")
        self.adjustSize()

        # Restart fade animation
        if self.opacity_effect.opacity != 1.0 or  not self.fade_in_ani.state() == QAbstractAnimation.State.Running:
            self.fade_in()

    def getZoom(self):
        return self.value

    def fade_in(self, duration: int = 300):
        self.setVisible(True)
        self.fade_out_ani.stop()
        self.fade_in_ani.setDuration(duration)
        self.fade_in_ani.start()

    def fade_out(self, duration: int = 300):
        self.fade_in_ani.stop()
        self.fade_out_ani.setDuration(duration)
        self.fade_out_ani.start()

class ReaderNavigation(SimpleCardWidget):
    zoomInSignal = Signal()
    zoomOutSignal = Signal()
    chaptersSignal = Signal()
    settingsSignal = Signal()
    openInWebSignal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.create_button(FluentIcon.ZOOM_IN, "Zoom in", Qt.CursorShape.PointingHandCursor,
                           self.zoomInSignal.emit)
        self.create_button(FluentIcon.ALIGNMENT, "Chapters", Qt.CursorShape.PointingHandCursor,
                           self.chaptersSignal.emit)
        self.create_button(FluentIcon.GLOBE, "Open in Web", Qt.CursorShape.PointingHandCursor,
                           self.openInWebSignal.emit)
        self.create_button(FluentIcon.SETTING, "Settings", Qt.CursorShape.PointingHandCursor,
                           self.settingsSignal.emit)
        self.create_button(FluentIcon.ZOOM_OUT, "Zoom out", Qt.CursorShape.PointingHandCursor,
                           self.zoomOutSignal.emit)

    def create_button(self, icon, tooltip, cursor, on_click):
        button = TransparentToolButton(icon, self)
        button.setToolTip(tooltip)
        button.setCursor(cursor)
        button.clicked.connect(on_click)

        self.layout.addWidget(button)

    def setBackgroundColor(self, color: QColor):
        self.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})")


class ReaderTitle(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


        self._titleLabel = SubtitleLabel(self)
        self._contentLabel = BodyLabel(self)
        self._backButton = TransparentToolButton(FluentIcon.LEFT_ARROW, self)
        self._downloadButton = TransparentToolButton(FluentIcon.DOWNLOAD, self)
        self._bookmarkButton = TransparentToolButton(FluentIcon.TAG, self)

        self._setup_ui()



    def _setup_ui(self):
        qss = "SubtitleLabel {background-color: rgba(0, 0, 0, 0)}"
        setCustomStyleSheet(self._titleLabel, qss, qss)
        qss = "BodyLabel {background-color: rgba(0, 0, 0, 0)}"
        setCustomStyleSheet(self._contentLabel, qss, qss)

        vlayout = QVBoxLayout()
        vlayout.setSpacing(0)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.addWidget(self._titleLabel)
        vlayout.addWidget(self._contentLabel)

        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.addWidget(self._backButton)
        layout.addSpacing(6)
        layout.addLayout(vlayout)
        layout.addWidget(self._downloadButton)
        layout.addWidget(self._bookmarkButton)

    def setTitle(self, title):
        self._titleLabel.setText(title)

    def setDescription(self, description):
        self._contentLabel.setText(description)

    def setBackgroundColor(self, color: QColor):
        self.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})")


class AutoScrollCard(ExpandSettingCard):
    speedChanged = Signal(int)
    toggled = Signal(bool)
    speedToggled = Signal(bool, int)
    def __init__(self, is_enabled: bool, parent: QWidget):
        super().__init__(FluentIcon.STOP_WATCH, "Auto Scroll", None, parent)

        self.toggle = AnimatedToggle(self)
        self.toggle.toggled.connect(self._on_toggled)
        self.addWidget(self.toggle)

        self.slider = Slider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(1, 100)
        self.spinbox = SpinBox(self)
        self.spinbox.setRange(1, 100)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        self.slider.valueChanged.connect(self._on_slider_changed)

        layout = QHBoxLayout()
        layout.addSpacing(36)
        layout.addWidget(BodyLabel(text="Speed"), stretch=1)
        layout.addWidget(self.slider, stretch=1)
        layout.addWidget(self.spinbox, alignment=Qt.AlignmentFlag.AlignRight)

        self.viewLayout.addLayout(layout)

        self._adjustViewSize()

    def _on_toggled(self, checked: bool):
        # self.toggled.emit(checked)
        self.speedToggled.emit(checked, self.slider.value())

    def _on_slider_changed(self, value: int):
        self.speedChanged.emit(value)
        if self.spinbox.value() != value:
            self.spinbox.blockSignals(True)
            self.spinbox.setValue(value)
            self.spinbox.blockSignals(False)

    def _on_spinbox_changed(self, value: int):
        self.speedChanged.emit(value)
        if self.slider.value() != value:
            self.slider.blockSignals(True)
            self.slider.setValue(value)
            self.slider.blockSignals(False)


class ReaderSettings(KineticScrollArea):
    #view
    viewModeChanged = Signal(ReadMode)
    fitModeChanged = Signal(FitMode)
    zoomStepChanged = Signal(float)
    pageGapChanged = Signal(int)
    autoCropBorderToggled = Signal(bool)
    backgroundColorChanged = Signal(QColor)
    #navigation
    autoScrollChanged = Signal(bool, int) #enable, speed
    scrollSensitivityChanged = Signal(float)
    pageSnappingToggled = Signal(bool)
    pageTurnAnimationToggled = Signal(bool)
    showPageNumToggled = Signal(bool)
    #advance
    cacheImageToggled = Signal(bool)
    smoothScrollToggled = Signal(bool)
    grayScaleToggled = Signal(bool)
    invertToggled = Signal(bool)
    settingPositionChanged = Signal(PositionFlags)
    settingWidthChanged = Signal(int)
    forceHorizontalSliderToggled = Signal(bool)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("Ghost", "Zerokku")
        screen_geometry = QApplication.primaryScreen().geometry()

        container = QWidget(parent=self)
        self.container_layout = QVBoxLayout(container)

        self.setWidget(container)
        self.setWidgetResizable(True)

        self.read_modes = {mode.value: mode for mode in ReadMode}
        self.fit_modes = {mode.value: mode for mode in FitMode}
        self.positions = {pos.value: pos for pos in PositionFlags}

        # setting items
        # view
        self._view_mode = OptionsCard(FluentIcon.VIEW, texts=list(self.read_modes.keys()),
                                      selected=2, title="View", parent=self)
        self._fit_mode = OptionsCard(FluentIcon.FULL_SCREEN, texts=list(self.fit_modes.keys()), selected=0,
                                     title="Fit mode", parent=self)
        self._zoom_level = DoubleSpinCard(FluentIcon.ZOOM, title="Zoom steps", parent=self)
        self._zoom_level.setValue(0.15)
        self._page_gaps = SpinCard(FluentIcon.ALIGNMENT, title="Page Gap", parent=self)
        self._page_gaps.setValue(10)
        self._auto_crop_border = ToggleCard(FluentIcon.MINIMIZE, title="Auto crop border", parent=self)
        self._auto_crop_border.setChecked(True)
        self._gray_scale = ToggleCard(FluentIcon.BRUSH, title="Grayscale filter", parent=self)
        self._gray_scale.setChecked(False)
        self._invert_filter = ToggleCard(FluentIcon.CONSTRACT, title="Invert filter", parent=self)
        self._invert_filter.setChecked(False)
        self._background_color = PushButton("Background color")
        # navigation
        self._auto_scroll = AutoScrollCard(True, self)
        self._scroll_sensitivity = DoubleSpinCard(FluentIcon.SPEED_MEDIUM, title="Scroll sensitivity", parent=self)
        self._scroll_sensitivity.setRange(0, 1)
        self._scroll_sensitivity.setValue(0.80)
        self._page_snapping = ToggleCard(icon=None, title="Page snapping", parent=self)
        self._page_snapping.setChecked(True)
        self._page_turn_animation = ToggleCard(FluentIcon.CERTIFICATE, title="Page turn animation", parent=self)
        self._page_turn_animation.setChecked(True)
        self._show_page_numbers = ToggleCard(FluentIcon.UNIT, title="Show page numbers", parent=self)
        self._show_page_numbers.setChecked(True)
        # advance
        self._cache_image = ToggleCard(FluentIcon.CLOUD, title="Cache image", parent=self)
        self._cache_image.setChecked(True)
        self._smooth_scrolling = ToggleCard(FluentIcon.SCROLL, title="Smooth scrolling", parent=self)
        self._smooth_scrolling.setChecked(True)
        self._horizontal_slider = ToggleCard(FluentIcon.SKIP_FORWARD, title="Force horizontal slider", parent=self)
        self._setting_position = OptionsCard(FluentIcon.LAYOUT, texts=list(self.positions.keys()),
                                             selected=0, title= "Settings position", parent=self)
        self._setting_width = SpinBoxCard(FluentIcon.FULL_SCREEN, "Settings width", parent=self)
        self._setting_width.spinBox.setRange(int(screen_geometry.width() * 0.28), int(screen_geometry.width() * 0.5))
        self.setFixedWidth(self._setting_width.spinBox.value())

        self._setup_ui()

        self.setStyleSheet("QGroupBox {font-size: 16px;}")
        # self.setStyleSheet("background: transparent; border: none;")

        # palette = self.viewport().palette()
        # palette.setColor(self.viewport().backgroundRole(), Qt.transparent)
        # self.viewport().setPalette(palette)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._signal_handler()

    def _setup_ui(self):
        view_groupbox = QGroupBox("View", parent=self)
        view_layout = QVBoxLayout(view_groupbox)
        navigation_groupbox = QGroupBox("Navigations", parent=self)
        navigation_layout = QVBoxLayout(navigation_groupbox)
        advanced_groupbox = QGroupBox("Advance", parent=self)
        advanced_layout = QVBoxLayout(advanced_groupbox)

        view_layout.addWidget(self._view_mode)
        view_layout.addWidget(self._fit_mode)
        view_layout.addWidget(self._zoom_level)
        view_layout.addWidget(self._page_gaps)
        view_layout.addWidget(self._auto_crop_border)
        view_layout.addWidget(self._gray_scale)
        view_layout.addWidget(self._invert_filter)
        view_layout.addWidget(self._background_color)

        navigation_layout.addWidget(self._auto_scroll)
        navigation_layout.addWidget(self._scroll_sensitivity)
        navigation_layout.addWidget(self._page_turn_animation)
        navigation_layout.addWidget(self._show_page_numbers)
        navigation_layout.addWidget(self._page_snapping)
        navigation_layout.addWidget(self._horizontal_slider)
        # navigation_layout.addWidget(self._scroll_sensitivity)


        advanced_layout.addWidget(self._cache_image)
        advanced_layout.addWidget(self._smooth_scrolling)
        advanced_layout.addWidget(self._setting_position)
        advanced_layout.addWidget(self._setting_width)

        self.container_layout.addWidget(view_groupbox)
        self.container_layout.addWidget(navigation_groupbox)
        self.container_layout.addWidget(advanced_groupbox)

    def _signal_handler(self):
        self._view_mode.optionChanged.connect(self._on_view_mode_changed)
        self._fit_mode.optionChanged.connect(self._on_fit_mode_changed)
        self._zoom_level.valueChanged.connect(self.zoomStepChanged.emit)
        self._page_gaps.valueChanged.connect(self.pageGapChanged.emit)
        self._auto_crop_border.toggled.connect(self.autoCropBorderToggled.emit)

        self._auto_scroll.speedToggled.connect(self.autoScrollChanged.emit)
        self._scroll_sensitivity.valueChanged.connect(self.scrollSensitivityChanged.emit)
        self._page_snapping.toggled.connect(self.pageSnappingToggled.emit)
        self._page_turn_animation.toggled.connect(self.pageTurnAnimationToggled.emit)
        self._show_page_numbers.toggled.connect(self.showPageNumToggled.emit)
        self._horizontal_slider.toggled.connect(self.forceHorizontalSliderToggled.emit)

        self._cache_image.toggled.connect(self.cacheImageToggled.emit)
        self._smooth_scrolling.toggled.connect(self.smoothScrollToggled.emit)
        self._gray_scale.toggled.connect(self.grayScaleToggled.emit)
        self._invert_filter.toggled.connect(self.invertToggled.emit)
        self._setting_width.valueChanged.connect(self.settingWidthChanged.emit)
        self._setting_position.optionChanged.connect(self._on_position_changed)


    def _on_view_mode_changed(self, value):
        mode = self.read_modes.get(value)
        self.viewModeChanged.emit(mode)

    def _on_fit_mode_changed(self, value):
        mode = self.fit_modes.get(value)
        self.fitModeChanged.emit(mode)

    def _on_position_changed(self, value):
        pos = self.positions.get(value)
        self.settingPositionChanged.emit(pos)

    def setBackgroundColor(self, color: QColor):
        self.setStyleSheet(f"""
        
        QWidget {{  background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()}); }}
        QGroupBox {{ background-color: transparent; font-size: 16px; }}
        QScrollArea {{background: transparent;}}
""")

    def save_settings(self):
        pass
        # self.settings.setValue("view_mode", self._view_mode.selectedIndex())
        # self.settings.setValue("fit_mode", self._fit_mode.selectedIndex())
        # self.settings.setValue("zoom_level", self._zoom_level.value())
        # self.settings.setValue("page_gaps", self._page_gaps.value())
        # self.settings.setValue("auto_crop_border", self._auto_crop_border.isChecked())

    def load_settings(self):
        pass
        # self._view_mode.setSelectedIndex(int(self.settings.value("view_mode", 1)))
        # self._fit_mode.setSelectedIndex(int(self.settings.value("fit_mode", 1)))
        # self._zoom_level.setValue(float(self.settings.value("zoom_level", 1.0)))
        # self._page_gaps.setValue(int(self.settings.value("page_gaps", 0)))
        # self._auto_crop_border.setChecked(self.settings.value("auto_crop_border", False, type=bool))


class ReaderSlider(QStackedWidget):
    # Signals for chapter navigation
    previousChapterRequested = Signal()
    nextChapterRequested = Signal()
    pageChanged = Signal(int)
    pageIndexChanged = Signal(int)

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal, parent=None):
        super().__init__(parent)

        # Initialize widgets for horizontal layout
        self._previous_chapter_h = TransparentToolButton(FluentIcon.LEFT_ARROW, self)
        self._next_chapter_h = TransparentToolButton(FluentIcon.RIGHT_ARROW, self)
        self.current_page_h = StrongBodyLabel("1", self)
        self.total_pages_h = StrongBodyLabel("100", self)
        self.slider_h = MySlider(Qt.Orientation.Horizontal, self)
        self.slider_h.setTickInterval(1)
        self.slider_h.setGrooveThickness(10)
        self.slider_h.setTickRadius(3)
        # self.slider_h.setHandleRadius(10)

        # Initialize widgets for vertical layout
        self._previous_chapter_v = TransparentToolButton(FluentIcon.UP, self)
        self._next_chapter_v = TransparentToolButton(FluentIcon.DOWN, self)
        self.current_page_v = BodyLabel("1", self)
        self.total_pages_v = BodyLabel("100", self)
        self.slider_v = MySlider(Qt.Orientation.Vertical, self)
        self.slider_v.setGrooveThickness(10)
        # self.slider_v.setHandleRadius(6)
        self.slider_v.setTickInterval(1)
        self.slider_v.setFixedWidth(self.slider_v.handle.width())

        # Create horizontal layout widget
        self.h_widget = SimpleCardWidget(self)
        h_layout = QHBoxLayout(self.h_widget)
        h_layout.addWidget(self._previous_chapter_h)
        h_layout.addWidget(self.current_page_h)
        h_layout.addWidget(self.slider_h)
        h_layout.addWidget(self.total_pages_h)
        h_layout.addWidget(self._next_chapter_h)
        h_layout.setSpacing(6)
        h_layout.setContentsMargins(10, 10, 10, 10)

        # Create vertical layout widget
        self.v_widget = SimpleCardWidget(self)
        v_layout = QVBoxLayout(self.v_widget)
        v_layout.addWidget(self._previous_chapter_v, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        v_layout.addWidget(self.current_page_v, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        v_layout.addWidget(self.slider_v, alignment=Qt.AlignmentFlag.AlignHCenter, stretch=1)
        v_layout.addWidget(self.total_pages_v, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        v_layout.addWidget(self._next_chapter_v, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        v_layout.setSpacing(6)
        v_layout.setContentsMargins(10, 10, 10, 10)

        # Create QStackedWidget

        self.addWidget(self.h_widget)
        self.addWidget(self.v_widget)


        # Connect signals
        self._previous_chapter_h.clicked.connect(self.previousChapterRequested)
        self._next_chapter_h.clicked.connect(self.nextChapterRequested)
        self._previous_chapter_v.clicked.connect(self.previousChapterRequested)
        self._next_chapter_v.clicked.connect(self.nextChapterRequested)
        self.slider_h.valueChanged.connect(self._update_current_page)
        self.slider_v.valueChanged.connect(self._update_current_page)

        # Set initial orientation
        self.setOrientation(orientation)

        # Set up opacity effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        # Fade-out animation
        self.fade_out_ani = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_ani.setDuration(150)
        self.fade_out_ani.setStartValue(1.0)
        self.fade_out_ani.setEndValue(0.0)
        self.fade_out_ani.finished.connect(self.hide)
        self.fade_out_ani.setEasingCurve(QEasingCurve.InOutQuad)

        # Fade-in animation
        self.fade_in_ani = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_ani.setDuration(150)
        self.fade_in_ani.setStartValue(0.0)
        self.fade_in_ani.setEndValue(1.0)
        self.fade_in_ani.setEasingCurve(QEasingCurve.InOutQuad)

    def _get_previous_icon(self, orientation: Qt.Orientation):
        return FluentIcon.LEFT_ARROW if orientation == Qt.Orientation.Horizontal else FluentIcon.UP

    def _get_next_icon(self, orientation: Qt.Orientation):
        return FluentIcon.RIGHT_ARROW if orientation == Qt.Orientation.Horizontal else FluentIcon.DOWN

    def setOrientation(self, orientation: Qt.Orientation):
        """Set the orientation and update the stacked widget."""
        # Update slider orientations
        self.slider_h.setOrientation(Qt.Orientation.Horizontal)
        self.slider_v.setOrientation(Qt.Orientation.Vertical)

        # Update button icons
        self._previous_chapter_h.setIcon(self._get_previous_icon(Qt.Orientation.Horizontal))
        self._next_chapter_h.setIcon(self._get_next_icon(Qt.Orientation.Horizontal))
        self._previous_chapter_v.setIcon(self._get_previous_icon(Qt.Orientation.Vertical))
        self._next_chapter_v.setIcon(self._get_next_icon(Qt.Orientation.Vertical))

        # Synchronize slider values and page labels
        self.current_page_v.setText(self.current_page_h.text())
        self.total_pages_v.setText(self.total_pages_h.text())
        self.slider_v.setValue(self.slider_h.value())

        # Switch to the appropriate widget
        if orientation == Qt.Orientation.Horizontal:
            self.setCurrentWidget(self.h_widget)
        else:
            self.setCurrentWidget(self.v_widget)

    def getOrientation(self)->Qt.Orientation:
        return Qt.Orientation.Horizontal if self.currentWidget()==self.h_widget else Qt.Orientation.Vertical

    @Slot(int)
    def _update_current_page(self, value: int):
        """Update the current page labels for both layouts."""
        self.current_page_h.setText(str(value))
        self.current_page_v.setText(str(value))
        self.pageChanged.emit(value)
        self.pageIndexChanged.emit(value - self.slider_v.minimum())

    def setTotalPages(self, total: int):
        """Set the total number of pages and update slider range."""
        self.blockSignals(True)
        self.total_pages_h.setText(f"{total}")
        self.total_pages_v.setText(f"{total}")
        self.slider_h.setRange(1, total)
        self.slider_v.setRange(1, total)
        self.blockSignals(False)

    def setCurrentPage(self, page: int):
        """Set the current page and update sliders."""
        self.blockSignals(True)
        self.slider_h.setValue(page)
        self.slider_v.setValue(page)
        self.current_page_h.setText(str(page))
        self.current_page_v.setText(str(page))
        self.blockSignals(False)

    def setCurrentPageIndex(self, index: int):
        """Set the current page and update sliders."""
        self.setCurrentPage(index + self.slider_v.minimum())

    def setBackgroundColor(self, color: QColor):
        """Set the background color."""
        self.h_widget.setBackgroundColor(color)
        self.v_widget.setBackgroundColor(color)

    def fade_in(self, duration: int = 300):
        self.setVisible(True)
        self.fade_out_ani.stop()
        self.fade_in_ani.setDuration(duration)
        self.fade_in_ani.start()

    def fade_out(self, duration: int = 300):
        self.fade_in_ani.stop()
        self.fade_out_ani.setDuration(duration)
        self.fade_out_ani.start()


class ReaderAnimationManager(QObject):
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
        self.navigation_animation.setEndValue(QPoint(self.bottom_nav.x(), self.bottom_nav.parent().height()))

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

    def show_settings(self, direction: PositionFlags = PositionFlags.LEFT):
        """direction 0 from left, 1 from right"""

        self.settings_animation.stop()
        if direction == PositionFlags.LEFT:
            point = QPoint(-self.setting_widget.x() - self.setting_widget.width(), self.setting_widget.y())
        else:
            point = QPoint(self.setting_widget.x() + self.setting_widget.width(), self.setting_widget.y())

        self.setting_widget.setVisible(True)
        self.settings_animation.setStartValue(point)
        self.settings_animation.setEndValue(self.setting_widget.pos())

        self._is_setting_hide_ani = False
        self.settings_animation.start()

    def hide_settings(self, direction: PositionFlags = PositionFlags.LEFT):
        """direction 0 from left, 1 from right"""
        logger.debug("Hiding Settings")
        # self.settings_animation.stop()
        if direction == PositionFlags.LEFT:
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


class ReaderChapters(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ReaderSlider()
    color = QColor.fromRgb(255, 0, 0,100)
    window.setBackgroundColor(color)
    window.show()
    window.fade_in(800)
    app.exec()