import sys
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QStackedWidget, QHBoxLayout, QVBoxLayout, QWidget, QApplication
from qfluentwidgets import BodyLabel, TransparentToolButton, FluentIcon

from gui.common import MySlider


# Assuming MySlider is a custom slider class

class ReaderSlider(QStackedWidget):
    # Signals for chapter navigation
    previousChapterRequested = Signal()
    nextChapterRequested = Signal()

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal, parent=None):
        super().__init__(parent)

        # Initialize widgets for horizontal layout
        self._previous_chapter_h = TransparentToolButton(FluentIcon.LEFT_ARROW, self)
        self._next_chapter_h = TransparentToolButton(FluentIcon.RIGHT_ARROW, self)
        self.current_page_h = BodyLabel("1", self)
        self.total_pages_h = BodyLabel("100", self)
        self.slider_h = MySlider(Qt.Orientation.Horizontal, self)
        self.slider_h.setTickInterval(1)

        # Initialize widgets for vertical layout
        self._previous_chapter_v = TransparentToolButton(FluentIcon.UP, self)
        self._next_chapter_v = TransparentToolButton(FluentIcon.DOWN, self)
        self.current_page_v = BodyLabel("1", self)
        self.total_pages_v = BodyLabel("100", self)
        self.slider_v = MySlider(Qt.Orientation.Vertical, self)
        self.slider_v.setTickInterval(1)

        # Create horizontal layout widget
        self.h_widget = QWidget(self)
        h_layout = QHBoxLayout(self.h_widget)
        h_layout.addWidget(self._previous_chapter_h)
        h_layout.addWidget(self.current_page_h)
        h_layout.addWidget(self.slider_h)
        h_layout.addWidget(self.total_pages_h)
        h_layout.addWidget(self._next_chapter_h)
        h_layout.setSpacing(6)
        h_layout.setContentsMargins(10, 10, 10, 10)

        # Create vertical layout widget
        self.v_widget = QWidget(self)
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

    @Slot(int)
    def _update_current_page(self, value: int):
        """Update the current page labels for both layouts."""
        self.current_page_h.setText(str(value))
        self.current_page_v.setText(str(value))

    def setTotalPages(self, total: int):
        """Set the total number of pages and update slider range."""
        self.total_pages_h.setText(f"{total}")
        self.total_pages_v.setText(f"{total}")
        self.slider_h.setRange(1, total)
        self.slider_v.setRange(1, total)

    def setCurrentPage(self, page: int):
        """Set the current page and update sliders."""
        self.slider_h.setValue(page)
        self.slider_v.setValue(page)
        self.current_page_h.setText(str(page))
        self.current_page_v.setText(str(page))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    slider = ReaderSlider(orientation=Qt.Orientation.Vertical)
    slider.setTotalPages(100)  # Example: set total pages
    slider.setCurrentPage(1)   # Example: set initial page
    slider.show()
    # slider.setFixedHeight(40)

    # Example: Switch orientation after 2 seconds to test
    # from PySide6.QtCore import QTimer
    # QTimer.singleShot(2000, lambda: slider.setOrientation(Qt.Orientation.Vertical))

    sys.exit(app.exec())