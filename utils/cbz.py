import shutil
import tempfile
import time
import zipfile
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from typing import Optional, List

from PIL.ImageQt import QPixmap
from loguru import logger

class CBZArchive:
    """A class to handle CBZ (Comic Book Zip) archive operations with optimized image handling."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    TEMP_DIR_PREFIX = "cbz_"

    def __init__(self, cbz_path: Path, temp_dir: Path) -> None:
        """
        Initialize CBZ archive with path validation and temporary directory setup.

        Args:
            cbz_path: Path to the CBZ file

        Raises:
            FileNotFoundError: If CBZ file doesn't exist
            zipfile.BadZipFile: If file is not a valid ZIP archive
        """
        self._cleaned_up: bool = False
        self.cbz_path = Path(cbz_path).resolve()
        if not self.cbz_path.exists():
            raise FileNotFoundError(f"CBZ file not found: {self.cbz_path}")

        # Use context manager for zip file to ensure proper closure
        self._zip: Optional[zipfile.ZipFile] = None
        # self.temp_dir = Path(r"D:\Program\Zerokku\.temp\cbz_")
        self.temp_dir = Path(tempfile.mkdtemp(prefix=self.TEMP_DIR_PREFIX, dir=temp_dir))
        self._image_entries: List[str] = []

        try:
            self._initialize_archive()
        except Exception as e:
            self.cleanup()
            raise e

    def _initialize_archive(self) -> None:
        """Initialize archive by opening zip and extracting image entries."""
        self._zip = zipfile.ZipFile(self.cbz_path, 'r')
        self._image_entries = self._get_sorted_images()
        if not self._image_entries:
            raise ValueError("No valid images found in CBZ archive")
        self._extract_to_temp()

    def _get_sorted_images(self) -> List[str]:
        """
        Get sorted list of image files from archive.

        Returns:
            List of image file names sorted case-insensitively
        """
        return sorted(
            (name for name in self._zip.namelist()
             if Path(name).suffix.lower() in self.SUPPORTED_EXTENSIONS),
            key=str.lower
        )

    def _extract_to_temp(self) -> None:
        """Extract image files to temporary directory with error handling."""
        try:
            for name in self._image_entries:
                # Create parent directories if needed
                target_path = self.temp_dir / name
                target_path.parent.mkdir(parents=True, exist_ok=True)
                self._zip.extract(name, self.temp_dir)

        except Exception as e:
            logger.error(f"Failed to extract images: {e}")
            raise
        finally:
            self._cleaned_up = False

    def page_count(self) -> int:
        """Return total number of pages in the archive."""
        return len(self._image_entries)

    def get_path(self, index: int) -> Path:
        """
        Get filesystem path for image at given index.

        Args:
            index: Page index

        Returns:
            Path to extracted image

        Raises:
            IndexError: If index is out of range
        """
        if not 0 <= index < len(self._image_entries):
            raise IndexError(f"Page index {index} out of range")
        return self.temp_dir / self._image_entries[index]

    def get_data(self, index: int) -> bytes:
        """
        Get raw image data from archive.

        Args:
            index: Page index

        Returns:
            Image data as bytes

        Raises:
            IndexError: If index is out of range
        """
        if not 0 <= index < len(self._image_entries):
            raise IndexError(f"Page index {index} out of range")
        return self._zip.read(self._image_entries[index])

    @lru_cache(maxsize=32)
    def get_pixmap(self, index: int) -> Optional[QPixmap]:
        """
        Get QPixmap for image at given index with caching.

        Args:
            index: Page index

        Returns:
            QPixmap object or None if image is invalid
        """
        try:
            path = self.get_path(index)
            pixmap = QPixmap(str(path))
            return pixmap if not pixmap.isNull() else None
        except Exception as e:
            logger.warning(f"Failed to load pixmap at index {index}: {e}")
            return None

    def get_pixmap_from_path(self, path: Path) -> Optional[QPixmap]:
        """
        Get QPixmap from specific path with caching and proper path resolution.

        Args:
            path: Path to image file

        Returns:
            QPixmap object or None if image is invalid
        """
        try:
            resolved_path = Path(path).resolve()
            if not resolved_path.exists():
                return None
            pixmap = QPixmap(str(resolved_path))
            return pixmap if not pixmap.isNull() else None
        except Exception as e:
            logger.warning(f"Failed to load pixmap from {path}: {e}")
            return None

    def cleanup(self) -> None:
        """Robust cleanup of temporary directory and zip file with retry logic."""
        if self._cleaned_up:
            return  # Prevent redundant cleanup

        try:
            # Close zip file safely
            with suppress(Exception):
                if self._zip:
                    self._zip.close()
                    self._zip = None

            # Clean up temporary directory with retries
            self._cleaned_up = self.remove(self.temp_dir, 3, 0.5)

        except Exception as e:
            logger.error(f"Unexpected error in cleanup: {e}")

    def remove(self, path: Path, max_retries:int=3, retry_delay:float=0.5) -> bool:
        if path.exists():
            for attempt in range(max_retries):
                try:
                    shutil.rmtree(self.temp_dir, ignore_errors=False)
                    break
                except (OSError, PermissionError) as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Failed to delete temporary directory {self.temp_dir} after {max_retries} attempts: {e}")
                    else:
                        logger.warning(f"Attempt {attempt + 1} to delete {self.temp_dir} failed: {e}. Retrying...")
                        time.sleep(retry_delay)
                except Exception as e:
                    logger.error(f"Unexpected error during cleanup of {self.temp_dir}: {e}")
                    break
        return True


    def __enter__(self) -> 'CBZArchive':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with cleanup."""
        self.cleanup()

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        self.cleanup()


if __name__ == "__main__":
    path = Path(r"D:\Program\Zerokku\demo\Chapter 44.cbz")
    cbz = CBZArchive(path)
    print(cbz.page_count())

