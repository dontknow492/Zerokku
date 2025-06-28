import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QSizePolicy, QColorDialog
)
from PySide6.QtCore import Qt, QEasingCurve, QPoint
from PySide6.QtGui import QColor
from animation_manager import AnimationManager, AnimationDirection


class AnimationDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Animation Manager Playground")
        self.setGeometry(100, 100, 800, 600)

        self.anim_manager = AnimationManager()
        self.demo_widgets = []

        self.init_ui()
        self.create_demo_widgets()

    def init_ui(self):
        """Initialize the main UI components"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Left panel - controls
        control_panel = QGroupBox("Animation Controls")
        control_panel.setFixedWidth(300)
        control_layout = QVBoxLayout(control_panel)

        # Animation type selector
        self.animation_type = QComboBox()
        self.animation_type.addItems([
            "Fade In", "Fade Out",
            "Slide In", "Slide Out",
            "Unfold Horizontal", "Unfold Vertical",
            "Pop", "Shake", "Pulse",
            "Add Shadow", "Remove Shadow"
        ])
        control_layout.addWidget(QLabel("Animation Type:"))
        control_layout.addWidget(self.animation_type)

        # Direction selector (for slide animations)
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Left", "Right", "Top", "Bottom"])
        control_layout.addWidget(QLabel("Direction:"))
        control_layout.addWidget(self.direction_combo)

        # Common parameters
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(100, 5000)
        self.duration_spin.setValue(500)
        control_layout.addWidget(QLabel("Duration (ms):"))
        control_layout.addWidget(self.duration_spin)

        self.distance_spin = QSpinBox()
        self.distance_spin.setRange(10, 500)
        self.distance_spin.setValue(100)
        control_layout.addWidget(QLabel("Distance:"))
        control_layout.addWidget(self.distance_spin)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(1.0, 3.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setValue(1.2)
        control_layout.addWidget(QLabel("Scale Factor:"))
        control_layout.addWidget(self.scale_spin)

        self.intensity_spin = QSpinBox()
        self.intensity_spin.setRange(1, 50)
        self.intensity_spin.setValue(10)
        control_layout.addWidget(QLabel("Shake Intensity:"))
        control_layout.addWidget(self.intensity_spin)

        # Checkboxes
        self.fade_check = QCheckBox("With Fade")
        self.fade_check.setChecked(True)
        control_layout.addWidget(self.fade_check)

        self.hide_check = QCheckBox("Hide on Finish")
        self.hide_check.setChecked(False)
        control_layout.addWidget(self.hide_check)

        # Shadow color button
        self.shadow_color = QColor(0, 0, 0, 150)
        self.color_btn = QPushButton("Shadow Color")
        self.color_btn.clicked.connect(self.choose_shadow_color)
        control_layout.addWidget(self.color_btn)

        # Easing curve selector
        self.easing_combo = QComboBox()
        self.easing_combo.addItems([
            "Linear", "InQuad", "OutQuad", "InOutQuad",
            "OutInQuad", "InCubic", "OutCubic", "InOutCubic",
            "OutInCubic", "InQuart", "OutQuart", "InOutQuart",
            "OutInQuart", "InQuint", "OutQuint", "InOutQuint",
            "OutInQuint", "InSine", "OutSine", "InOutSine",
            "OutInSine", "InExpo", "OutExpo", "InOutExpo",
            "OutInExpo", "InCirc", "OutCirc", "InOutCirc",
            "OutInCirc", "InElastic", "OutElastic", "InOutElastic",
            "OutInElastic", "InBack", "OutBack", "InOutBack",
            "OutInBack", "InBounce", "OutBounce", "InOutBounce",
            "OutInBounce"
        ])
        self.easing_combo.setCurrentText("OutCubic")
        control_layout.addWidget(QLabel("Easing Curve:"))
        control_layout.addWidget(self.easing_combo)

        # Execute button
        execute_btn = QPushButton("Run Animation")
        execute_btn.clicked.connect(self.execute_animation)
        control_layout.addWidget(execute_btn)

        # Reset button
        reset_btn = QPushButton("Reset Widgets")
        reset_btn.clicked.connect(self.reset_widgets)
        control_layout.addWidget(reset_btn)

        # Stop button
        stop_btn = QPushButton("Stop All Animations")
        stop_btn.clicked.connect(self.anim_manager.stop_all)
        control_layout.addWidget(stop_btn)

        control_layout.addStretch()

        # Right panel - demo area
        demo_panel = QGroupBox("Animation Preview")
        self.demo_layout = QVBoxLayout(demo_panel)
        self.demo_layout.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(control_panel)
        main_layout.addWidget(demo_panel)

        # Update UI based on selected animation
        self.animation_type.currentTextChanged.connect(self.update_ui)
        self.update_ui()

    def update_ui(self):
        """Update UI controls based on selected animation type"""
        anim_type = self.animation_type.currentText()

        # Show/hide relevant controls
        self.direction_combo.setVisible(anim_type in ["Slide In", "Slide Out"])
        self.distance_spin.setVisible(anim_type in ["Slide In", "Slide Out"])
        self.scale_spin.setVisible(anim_type in ["Pop", "Pulse"])
        self.intensity_spin.setVisible(anim_type == "Shake")
        self.fade_check.setVisible(anim_type in ["Slide In", "Slide Out", "Unfold Horizontal", "Unfold Vertical"])
        self.hide_check.setVisible(anim_type in ["Fade Out", "Slide Out"])
        self.color_btn.setVisible(anim_type in ["Add Shadow", "Remove Shadow"])

    def choose_shadow_color(self):
        """Open color dialog for shadow color selection"""
        color = QColorDialog.getColor(self.shadow_color, self, "Select Shadow Color")
        if color.isValid():
            self.shadow_color = color

    def create_demo_widgets(self):
        """Create widgets for animation demonstration"""
        # Clear existing widgets
        for widget in self.demo_widgets:
            widget.deleteLater()
        self.demo_widgets.clear()

        # Create 3 demo widgets with different colors
        colors = [QColor(255, 100, 100), QColor(100, 255, 100), QColor(100, 100, 255)]
        texts = ["Widget 1", "Widget 2", "Widget 3"]

        for i, (color, text) in enumerate(zip(colors, texts)):
            widget = QLabel(text)
            widget.setAlignment(Qt.AlignCenter)
            widget.setStyleSheet(f"""
                background-color: {color.name()};
                color: white;
                font-weight: bold;
                border-radius: 10px;
                padding: 20px;
            """)
            widget.setFixedSize(200, 100)
            widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            self.demo_layout.addWidget(widget, alignment=Qt.AlignCenter)
            self.demo_widgets.append(widget)

        # Add some spacing between widgets
        self.demo_layout.addSpacing(20)

    def reset_widgets(self):
        """Reset all demo widgets to their initial state"""
        self.anim_manager.stop_all()

        for widget in self.demo_widgets:
            widget.show()
            widget.setGraphicsEffect(None)
            widget.setGeometry(0, 0, 200, 100)

            # Center widgets
            parent = widget.parent()
            if parent:
                x = (parent.width() - widget.width()) // 2
                y = (parent.height() - widget.height()) // 3 + (widget.height() + 20) * self.demo_widgets.index(widget)
                widget.move(x, y)

    def get_easing_curve(self):
        """Get easing curve from combo box selection"""
        text = self.easing_combo.currentText()
        return getattr(QEasingCurve, text)

    def get_direction(self):
        """Get direction from combo box selection"""
        text = self.direction_combo.currentText()
        return getattr(AnimationDirection, text.upper())

    def execute_animation(self):
        """Execute the selected animation on all demo widgets"""
        anim_type = self.animation_type.currentText()
        duration = self.duration_spin.value()
        easing = self.get_easing_curve()

        # Reset widgets before animation if needed
        if anim_type in ["Fade In", "Slide In", "Unfold Horizontal", "Unfold Vertical"]:
            self.reset_widgets()

        if anim_type == "Fade In":
            self.anim_manager.fade_in(
                self.demo_widgets,
                duration=duration,
                easing=easing
            )
        elif anim_type == "Fade Out":
            self.anim_manager.fade_out(
                self.demo_widgets,
                duration=duration,
                easing=easing,
                hide_on_finish=self.hide_check.isChecked()
            )
        elif anim_type == "Slide In":
            self.anim_manager.slide_in(
                self.demo_widgets,
                direction=self.get_direction(),
                distance=self.distance_spin.value(),
                duration=duration,
                easing=easing,
                fade=self.fade_check.isChecked()
            )
        elif anim_type == "Slide Out":
            self.anim_manager.slide_out(
                self.demo_widgets,
                direction=self.get_direction(),
                distance=self.distance_spin.value(),
                duration=duration,
                easing=easing,
                fade=self.fade_check.isChecked(),
                hide_on_finish=self.hide_check.isChecked()
            )
        elif anim_type == "Unfold Horizontal":
            self.anim_manager.unfold_horizontal(
                self.demo_widgets,
                duration=duration,
                easing=easing,
                fade=self.fade_check.isChecked()
            )
        elif anim_type == "Unfold Vertical":
            self.anim_manager.unfold_vertical(
                self.demo_widgets,
                duration=duration,
                easing=easing,
                fade=self.fade_check.isChecked()
            )
        elif anim_type == "Pop":
            self.anim_manager.pop(
                self.demo_widgets,
                scale_factor=self.scale_spin.value(),
                duration=duration,
                easing=easing
            )
        elif anim_type == "Shake":
            self.anim_manager.shake(
                self.demo_widgets,
                intensity=self.intensity_spin.value(),
                duration=duration
            )
        elif anim_type == "Pulse":
            self.anim_manager.pulse(
                self.demo_widgets,
                scale_factor=self.scale_spin.value(),
                duration=duration
            )
        elif anim_type == "Add Shadow":
            self.anim_manager.add_shadow(
                self.demo_widgets,
                color=self.shadow_color,
                blur_radius=15.0,
                offset=QPoint(3, 3),
                duration=duration
            )
        elif anim_type == "Remove Shadow":
            self.anim_manager.remove_shadow(
                self.demo_widgets,
                duration=duration
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = AnimationDemo()
    demo.show()
    sys.exit(app.exec())