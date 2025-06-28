import os
import sys
from pathlib import Path
from typing import List, Optional, Iterator, Union, Tuple

from PySide6.QtCore import QRect, Qt, QMargins, QSize, QPointF
from PySide6.QtGui import QPixmap, QPixmapCache, QImageReader, QColor, QPainter, QPen, QBrush, QGradient, \
    QLinearGradient
import re
import ctypes

def get_cache_pixmap(self, path: Path) -> Optional[QPixmap]:
    key = str(path)  # Use string as key
    pixmap = QPixmap()

    # Try to find in cache
    found = QPixmapCache.find(key, pixmap)
    if found and not pixmap.isNull():
        return pixmap

    # Try to load from disk
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    image = reader.read()
    if image.isNull():
        return None

    pixmap = QPixmap.fromImage(image)
    if not pixmap.isNull():
        QPixmapCache.insert(key, pixmap)
        return pixmap

    return None

def delete_cache_pixmap(self, path: Path) -> None:
    key = str(path)
    QPixmapCache.remove(key)





def seconds_to_time_string(seconds: Union[int, float]) -> str:
    """
    Convert seconds to time string in HH:MM:SS format.

    Args:
        seconds (int): Non-negative integer representing seconds

    Returns:
        str: Time string in HH:MM:SS format

    Raises:
        ValueError: If input is not a non-negative integer
    """
    if not isinstance(seconds, (int, float)) or seconds < 0:
        raise ValueError("Input must be a non-negative number (int or float).")

    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def time_string_to_seconds(time_string: str) -> int:
    """
    Convert time string in HH:MM:SS format to seconds.

    Args:
        time_string (str): Time string in HH:MM:SS format

    Returns:
        int: Total number of seconds

    Raises:
        ValueError: If input format is invalid or values are out of range
    """
    if not isinstance(time_string, str):
        raise ValueError("Input must be a string")

    pattern = r"^(\d{2}):(\d{2}):(\d{2})$"
    match = re.match(pattern, time_string)

    if not match:
        raise ValueError("Invalid time format. Use HH:MM:SS")

    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = int(match.group(3))

    if minutes > 59 or seconds > 59:
        raise ValueError("Minutes and seconds must be less than 60")

    return (hours * 3600) + (minutes * 60) + seconds


def trim_time_string(seconds: Union[int, float]) -> str:
    """
    Convert seconds to a trimmed time string, removing unnecessary leading zeros and hours if zero.

    Args:
        seconds (int): Non-negative integer representing seconds

    Returns:
        str: Trimmed time string (e.g., '1:00' for 60 seconds, '1:01:01' for 3661 seconds)

    Raises:
        ValueError: If input is not a non-negative integer
    """
    if not isinstance(seconds, (int, float)) or seconds < 0:
        raise ValueError("Input must be a non-negative integer")

    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    if hours == 0:
        if minutes == 0:
            return f"00:{remaining_seconds:02}"
        return f"{minutes:02}:{remaining_seconds:02}"
    return f"{hours}:{minutes:02}:{remaining_seconds:02}"


def resource_path(relative_path):
    """Return absolute path to resource. Compatible with dev and bundled modes."""
    if hasattr(sys, "_MEIPASS"):  # PyInstaller
        base_path = sys._MEIPASS
    elif getattr(sys, 'frozen', False):  # Nuitka
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_screen_size() -> Tuple[int, int]:
    user32 = ctypes.windll.user32
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    return width, height

def get_physical_screen_size() -> Tuple[int, int]:
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    # Get device context of the entire screen
    hdc = user32.GetDC(0)

    # Constants for GetDeviceCaps
    DESKTOPHORZRES = 118
    DESKTOPVERTRES = 117

    width = gdi32.GetDeviceCaps(hdc, DESKTOPHORZRES)
    height = gdi32.GetDeviceCaps(hdc, DESKTOPVERTRES)

    # Release the device context
    user32.ReleaseDC(0, hdc)

    return width, height


reference_size = (1463, 823)# your base resolution for design

def get_scale_factor() -> float:
    current_size = get_screen_size()

    scale_factor_w = current_size[0] / reference_size[0]
    scale_factor_h = current_size[1] / reference_size[1]

    scale_factor = max(scale_factor_w, scale_factor_h)

    # Clamp scale factor to reasonable bounds if needed
    scale_factor = max(0.5, min(scale_factor, 3.0))  # for example: min 0.5x, max 3x

    return scale_factor

def add_margins_pixmap(pixmap: QPixmap, margins: QMargins, fill_color=Qt.transparent) -> QPixmap:
    new_width = pixmap.width() + margins.left() + margins.right()
    new_height = pixmap.height() + margins.top() + margins.bottom()

    padded = QPixmap(new_width, new_height)
    padded.fill(QColor(fill_color))

    painter = QPainter(padded)
    painter.drawPixmap(margins.left(), margins.top(), pixmap)
    painter.end()

    return padded

def apply_gradient_overlay_pixmap(pixmap: QPixmap, gradient: QGradient, rect: QRect = None) -> QPixmap:
    result = QPixmap(pixmap.size())
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.drawPixmap(0, 0, pixmap)

    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
    if rect is None:
        rect = pixmap.rect()
    painter.fillRect(rect, QBrush(gradient))

    painter.end()
    return result

def create_left_gradient_pixmap(pixmap: QPixmap, gradient_color: QColor, padding: int, offset: int) -> QPixmap:
    linearGrad = QLinearGradient(QPointF(padding+30, 0), QPointF(padding+offset, 0))
    linearGrad.setColorAt(0, gradient_color)
    linearGrad.setColorAt(1, Qt.GlobalColor.transparent)
    linearGrad.setInterpolationMode(QGradient.InterpolationMode.ColorInterpolation)

    if padding > 0:
        padded_pixmap = add_margins_pixmap(pixmap, QMargins(padding, 0, 0, 0))
    else:
        padded_pixmap = pixmap
    gradient_rect = QRect(0, 0, offset+padding, padded_pixmap.height())
    gradient_pixmap = apply_gradient_overlay_pixmap(padded_pixmap, linearGrad, gradient_rect)

    return gradient_pixmap

def create_gradient_pixmap(pixmap: QPixmap, gradient_color: QColor, width: int, strong_width: int) -> QPixmap:
    strong = round(strong_width/width, 2)
    # print(strong)
    linearGrad = QLinearGradient(QPointF(0, 0), QPointF(width, 0))
    linearGrad.setColorAt(0, gradient_color)
    linearGrad.setColorAt(strong, gradient_color)
    linearGrad.setColorAt(1, Qt.GlobalColor.transparent)
    linearGrad.setInterpolationMode(QGradient.InterpolationMode.ColorInterpolation)

    gradient_rect = QRect(0, 0, width, pixmap.height())
    gradient_pixmap = apply_gradient_overlay_pixmap(pixmap, linearGrad, gradient_rect)

    return gradient_pixmap

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QLabel
    app = QApplication(sys.argv)
    label = QLabel()
    input_path = "banners/banner.jpg"
    output_path = "output.png"
    org_pixmap = QPixmap(input_path)
    pad_pixmap = add_margins_pixmap(org_pixmap, QMargins(100, 0, 0, 0), Qt.GlobalColor.transparent)

    gradient = QLinearGradient(0, 100, 500, 200)  # from x=50 to x=150

    gradient.setColorAt(0.0, QColor(100, 20, 80, 255))
    gradient.setColorAt(0.5, QColor(200, 0, 0, 0))
    # gradient.setColorAt(0.7, QColor(0, 0, 0, 0))
    gradient.setColorAt(1.0, QColor(200, 0, 0, 250))

    grad_pixmap = apply_gradient_overlay_pixmap(pad_pixmap, gradient, QRect(0, 0, 500, pad_pixmap.height()))

    grad_pixmap.save(output_path)
    # pixmap.save(output_path)

    label.setPixmap(grad_pixmap.scaled(QSize(500, 500), Qt.KeepAspectRatio))
    label.show()
    app.exec()

