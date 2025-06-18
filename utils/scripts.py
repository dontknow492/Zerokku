from pathlib import Path
from typing import List, Optional, Iterator, Union
from PySide6.QtGui import QPixmap, QPixmapCache, QImageReader
import re

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
        print(time_string_to_seconds("invalid"))  # Raises ValueError

    except ValueError as e:
        print(f"Error: {e}")

