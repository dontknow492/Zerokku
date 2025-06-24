import os
import sys
from pathlib import Path
from typing import List, Optional, Iterator, Union, Tuple
from PySide6.QtGui import QPixmap, QPixmapCache, QImageReader
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

if __name__ == "__main__":
    try:
        # Test seconds to time string
        print(trim_time_string(69.3))  # Output: 01:01:01
        print(seconds_to_time_string(865.4))  # Output: 23:59:59

        # Test time string to seconds
        print(time_string_to_seconds("01:01:01"))  # Output: 3661
        print(time_string_to_seconds("23:59:59"))  # Output: 86399

        # Test invalid inputs
        # print(seconds_to_time_string(-1))  # Raises ValueError
        # print(time_string_to_seconds("25:60:00"))  # Raises ValueError
        # print(time_string_to_seconds("invalid"))  # Raises ValueError

        print(get_physical_screen_size(), get_screen_size(), get_scale_factor())

    except ValueError as e:
        print(f"Error: {e}")

