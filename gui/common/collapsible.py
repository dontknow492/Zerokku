from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QApplication, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from qfluentwidgets import TransparentToggleToolButton


class CollapsibleBase(QWidget):
    """A collapsible widget with animated expand/collapse functionality."""

    def __init__(self, title: str, content_widget: QWidget = None, expanded: bool = False,
                 parent: QWidget = None, content_margins: tuple = (0, 0, 0, 0),
                 spacing: int = 0):
        """
        Initialize the collapsible widget.

        Args:
            title: The title displayed on the toggle button
            content_widget: The widget to be collapsed/expanded
            expanded: Initial state (True for expanded, False for collapsed)
            parent: Parent widget
            content_margins: Margins for the content area (left, top, right, bottom)
            spacing: Spacing between toggle button and content
        """
        super().__init__(parent)

        # Initialize main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(spacing)

        # Setup toggle button
        self.toggle_button = TransparentToggleToolButton(title)
        self.toggle_button.setChecked(expanded)
        self.toggle_button.setText(title)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow if not expanded else Qt.DownArrow)
        self.toggle_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toggle_button.clicked.connect(self.toggle)

        # Setup content area
        self.content_area = QWidget(self) if content_widget is None else content_widget
        self.content_area.setParent(self)
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_area.setVisible(expanded)

        # Setup content layout if no content widget provided
        if content_widget is None:
            self.content_layout = QVBoxLayout(self.content_area)
            self.content_layout.setContentsMargins(*content_margins)
            self.content_layout.setSpacing(spacing)

        # Setup animation
        self.toggle_animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.toggle_animation.setDuration(300)
        self.toggle_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.toggle_animation.finished.connect(self._on_animation_finished)

        # Add widgets to layout
        self._main_layout.addWidget(self.toggle_button)
        self._main_layout.addWidget(self.content_area)
        self._main_layout.addStretch(1)

        self._content_height = 0
        self._is_animating = False

        if expanded:
            self._update_content_height()
            self.content_area.setMaximumHeight(self._content_height)

    def toggle(self):
        """Toggle the collapsed/expanded state with animation."""
        if self._is_animating:
            return

        checked = self.toggle_button.isChecked()
        self._is_animating = True

        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.toggle_animation.stop()

        if checked:
            self._update_content_height()
            self.content_area.setVisible(True)
            self.toggle_animation.setStartValue(0)
            self.toggle_animation.setEndValue(self._content_height)
        else:
            self.toggle_animation.setStartValue(self.content_area.height())
            self.toggle_animation.setEndValue(0)

        self.toggle_animation.start()

    def _update_content_height(self):
        """Update the stored content height based on size hint."""
        if self.content_area:
            self.content_area.setMaximumHeight(16777215)  # Qt max height
            self._content_height = self.content_area.sizeHint().height()
            self.content_area.setMaximumHeight(0 if not self.toggle_button.isChecked() else self._content_height)

    def _on_animation_finished(self):
        """Handle animation completion."""
        self._is_animating = False
        if not self.toggle_button.isChecked():
            self.content_area.setVisible(False)

    def set_content_height(self, height: int):
        """Set the height for the content area when expanded."""
        self._content_height = height
        if self.toggle_button.isChecked():
            self.content_area.setMaximumHeight(height)

    def add_widget(self, widget: QWidget):
        """Add a widget to the content area if no content widget was provided."""
        if hasattr(self, 'content_area'):
            layout = self.content_area.layout()
            if layout:
                layout.addWidget(widget)
                self._update_content_height()

    def resizeEvent(self, event: QResizeEvent):
        """Update content height when widget is resized."""
        if self.toggle_button.isChecked() and not self._is_animating:
            self._update_content_height()
        super().resizeEvent(event)

    def set_animation_duration(self, duration: int):
        """Set the animation duration in milliseconds."""
        self.toggle_animation.setDuration(max(0, duration))

    def set_animation_curve(self, curve: QEasingCurve):
        """Set the animation easing curve."""
        self.toggle_animation.setEasingCurve(curve)

    def sizeHint(self) -> QSize:
        """Return the size hint for the widget."""
        button_height = self.toggle_button.sizeHint().height()
        content_height = self._content_height if self.toggle_button.isChecked() else 0
        return QSize(self.width(), button_height + content_height + self._main_layout.spacing())


if __name__ == "__main__":
    app = QApplication([])

    # Create main window
    main_window = QWidget()
    main_window.setStyleSheet("background-color: rgb(255, 255, 255);")
    main_layout = QVBoxLayout(main_window)

    # Create collapsible widget

    content_widget = QWidget(main_window)
    content_layout = QVBoxLayout(content_widget)
    content_widget.setStyleSheet("background-color: red")

    collapsible = CollapsibleBase("Advanced Settings", content_widget = content_widget,
                                  parent=main_window,
                                  content_margins=(10, 10, 10, 10), spacing=5)

    # Add content to collapsible widget
    collapsible.add_widget(QLabel("Option 1"))
    collapsible.add_widget(QLabel("Option 2"))
    collapsible.add_widget(QLabel("Option 3"))
    collapsible.add_widget(QLabel("Option 4"))

    # Add collapsible to main layout
    main_layout.addWidget(collapsible)
    main_layout.addStretch(1)

    main_window.resize(400, 300)
    main_window.show()
    app.exec()