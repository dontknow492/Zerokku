import os

import numpy as np
import sys
from pathlib import Path
from typing import List, Optional, Iterator, Union, Tuple

from PySide6.QtCore import QRect, Qt, QMargins, QSize, QPointF
from PySide6.QtGui import QPixmap, QPixmapCache, QImageReader, QColor, QPainter, QPen, QBrush, QGradient, \
    QLinearGradient, QImage
import re
import ctypes
from datetime import datetime
from AnillistPython import MediaSeason

import cv2
from PIL import Image, ImageOps, ImageDraw, ImageQt


def detect_faces_and_crop(image_path, target_ratio=16/9):
    # Load image with OpenCV
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(r"D:\Program\Zerokku\assets\lbpcascade_animeface.xml")
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    img_pil = Image.open(image_path)
    width, height = img_pil.size

    # Compute desired crop width
    crop_width = int(height * target_ratio)

    # Clamp crop width to image width to avoid black padding
    crop_width = min(crop_width, width)

    if len(faces) == 0:
        # No faces detected, fallback to center crop
        left = (width - crop_width) // 2
        right = left + crop_width
        return img_pil.crop((left, 0, right, height))

    # Get bounding box covering all detected faces
    x_min = min(x for (x, y, w, h) in faces)
    x_max = max(x + w for (x, y, w, h) in faces)
    crop_center_x = (x_min + x_max) // 2

    # Compute crop box
    left = crop_center_x - crop_width // 2
    left = max(0, min(left, width - crop_width))  # Keep in bounds
    right = left + crop_width

    return img_pil.crop((left, 0, right, height))

def add_padding(image: Image.Image, left: int = 0, top: int = 0, right: int = 0, bottom: int=0, color=(0, 0, 0, 0)) -> Image.Image:
    """
    Adds padding to a PIL image.

    Parameters:
        image (PIL.Image): The input image.
        left (int): Padding on the left.
        top (int): Padding on the top.
        right (int): Padding on the right.
        bottom (int): Padding on the bottom.
        color (tuple): Background color as an RGB tuple. Default is black.

    Returns:
        PIL.Image: New image with the specified padding.
    """
    return ImageOps.expand(image, border=(left, top, right, bottom), fill=color)

def apply_left_gradient(image: Image.Image, start_width: int = 300, end_width: int = 500,
                        start_color=(0, 0, 0, 255), end_color=(0, 0, 0, 0)) -> Image.Image:
    """
    Applies a hard fill up to start_width, then a horizontal gradient from start_width to end_width.

    Parameters:
        image (PIL.Image): The original image.
        start_width (int): X-position where gradient starts (everything before is solid fill).
        end_width (int): X-position where gradient ends.
        start_color (tuple): RGBA color used for solid fill and gradient start.
        end_color (tuple): RGBA color at the gradient end.

    Returns:
        PIL.Image: Modified image.
    """
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Step 1: Solid block from 0 to start_width
    draw.rectangle([(0, 0), (start_width, image.height)], fill=start_color)

    # Step 2: Gradient from start_width to end_width
    gradient_width = max(1, end_width - start_width)
    for x in range(start_width, end_width):
        alpha = (x - start_width) / gradient_width
        r = int(start_color[0] * (1 - alpha) + end_color[0] * alpha)
        g = int(start_color[1] * (1 - alpha) + end_color[1] * alpha)
        b = int(start_color[2] * (1 - alpha) + end_color[2] * alpha)
        a = int(start_color[3] * (1 - alpha) + end_color[3] * alpha)

        draw.line([(x, 0), (x, image.height)], fill=(r, g, b, a))

    result = Image.alpha_composite(image, overlay)
    return result.convert("RGB")  # or "RGBA" if transparency needed


def get_current_season_and_year()->Tuple[MediaSeason, int]:
    now = datetime.now()
    month = now.month
    year = now.year

    if month in [1, 2, 3]:
        season = MediaSeason.WINTER
    elif month in [4, 5, 6]:
        season = MediaSeason.SPRING
    elif month in [7, 8, 9]:
        season = MediaSeason.SUMMER
    else:
        season = MediaSeason.FALL

    return season, year

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

