import hashlib
import socket
import logging
import asyncio
import sys
from asyncio.exceptions import TimeoutError
from datetime import datetime, timedelta
from pathlib import Path
from ssl import SSLError
from typing import Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from PySide6.QtWidgets import QApplication
from loguru import logger
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QPixmap, QPixmapCache
from aiohttp import ClientConnectionError, ClientPayloadError, ClientResponseError, InvalidURL, ServerDisconnectedError, ClientSession
from httpcore import NetworkError

from cachetools import LRUCache

# Configure logging

VALID_IMAGE_FORMATS = {"png", "jpg", "jpeg", "bmp", "gif", "webp", "svg"}

class FileTooLargeError(Exception):
    def __init__(self, size: int, limit: int):
        super().__init__(f"File size {size} exceeds limit {limit}")

class ChecksumMismatchError(Exception):
    def __init__(self, expected: str, actual: str):
        super().__init__(f"Checksum mismatch: expected {expected}, got {actual}")

class CacheManager(QObject):
    _url_hash_cache = LRUCache(maxsize=200)
    def __init__(self, cache_dir: Path, max_size_mb: int = 100, expiry_days: int = 30):
        super().__init__()
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.expiry_days = expiry_days
        self.current_size_mb = 0
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        QPixmapCache.setCacheLimit(50 * 1024)  # 50MB in KB
        self._initialize_cache()


    def _initialize_cache(self):
        """Scan cache directory and build size metadata."""
        self.current_size_mb = sum(
            f.stat().st_size for f in self.cache_dir.glob('*')
            if f.is_file()
        ) / (1024 * 1024)

    def get_cache_path(self, url_hash: str, extension: str = "png") -> Path:
        """
            Returns the file path for a cached image with given extension.
        """
        return self.cache_dir / f"{url_hash}.{extension}"


    @staticmethod
    def hash_url(url: str) -> str:
        if url in CacheManager._url_hash_cache:
            return CacheManager._url_hash_cache[url]
        hashed = hashlib.sha256(url.encode()).hexdigest()
        CacheManager._url_hash_cache[url] = hashed
        return hashed

    async def store(self, url_hash: str, pixmap: QPixmap, extension: str, cache_in_memory: bool = True):
        """
        Store the pixmap in disk cache and update size metadata.
        """
        cache_path = self.get_cache_path(url_hash, extension)

        def _save():
            pixmap.save(str(cache_path), extension.upper(), quality=100)
            return cache_path.stat().st_size

        try:
            file_size = await asyncio.get_event_loop().run_in_executor(None, _save)
            self.current_size_mb += file_size / (1024 * 1024)
            logger.trace(f"Cached {cache_path} (Size: {file_size / 1024:.2f}KB)")

            if self.current_size_mb > self.max_size_mb * 0.9:
                await self.cleanup()

            if cache_in_memory:
                self.cache_to_memory(url_hash, pixmap)

        except Exception as e:
            logger.error(f"Cache store failed: {str(e)}")

    async def cleanup(self):
        """
        Cleanup expired files and enforce max cache size.
        """
        def _scan_files():
            files = []
            for f in self.cache_dir.glob('*'):
                if f.is_file():
                    stat = f.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    size_mb = stat.st_size / (1024 * 1024)
                    files.append((f, mtime, size_mb))
            return files

        files = await asyncio.get_event_loop().run_in_executor(None, _scan_files)
        expiry_cutoff = datetime.now() - timedelta(days=self.expiry_days)

        # Remove expired first
        for f, mtime, size in files[:]:
            if mtime < expiry_cutoff:
                try:
                    f.unlink()
                    self.current_size_mb -= size
                    files.remove((f, mtime, size))
                except OSError as e:
                    logger.warning(f"Failed to remove {f}: {str(e)}")

        # Enforce size limit (oldest first)
        files.sort(key=lambda x: x[1])
        while self.current_size_mb > self.max_size_mb and files:
            file, mtime, size = files.pop(0)
            try:
                file.unlink()
                self.current_size_mb -= size
            except OSError as e:
                logger.warning(f"Size limit cleanup failed for {file}: {str(e)}")

    def get_from_cache(self, url: str, cache_in_memory: bool = True) -> Optional[QPixmap]:
        """
        Try to retrieve pixmap from memory or disk cache.

        Returns:
            QPixmap or None if not found.
        """
        try:
            url_hash = self.hash_url(url)
            pixmap = QPixmap()

            # Memory cache
            pixmap =  self.get_from_memory(url_hash)
            if pixmap:
                return pixmap
            pixmap = QPixmap()
            # Disk cache
            for ext in VALID_IMAGE_FORMATS:
                cache_path = self.get_cache_path(url_hash, ext)
                if cache_path.exists() and pixmap.load(str(cache_path)):
                    if cache_in_memory:
                        self.cache_to_memory(url_hash, pixmap)  # Populate memory cache
                    logger.trace(f"Loaded from disk: {url}")
                    return pixmap
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve {url}: {str(e)}")
            return None

    # def get_cache_path(self, url: str):
    #     url_hash = self.hash_url(url)
    #     for ext in VALID_IMAGE_FORMATS:
    #         cache_path = self.get_from_cache(url_hash, ext)
    #         if cache_path.exists():
    #             return cache_path
    def check_in_cache(self, url: str) -> Optional[Path]:
        url_hash = self.hash_url(url)
        for ext in VALID_IMAGE_FORMATS:
            cache_path = self.get_cache_path(url_hash, ext)
            if cache_path.exists(): # Populate memory cache
                return cache_path

    @staticmethod
    def cache_to_memory(url_hash: str, pixmap: QPixmap):
        QPixmapCache.insert(url_hash, pixmap)
        logger.trace(f"Added {url_hash} to memory cache")

    @staticmethod
    def get_from_memory(url_hash: str)->Optional[QPixmap]:
        pixmap = QPixmap()
        if QPixmapCache.find(url_hash, pixmap):
            logger.trace(f"Found in memory {url_hash}")
            return pixmap
        else:
            return None



class NetworkClient(QObject): # url, QPixmap
    downloadProgress = Signal(str, float)
    def __init__(self, max_retries: int = 3, timeout: int = 30, max_bytes_per_sec: int = -1, parent = None):
        super().__init__(parent)
        self.max_retries = max_retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        self.max_bytes_per_sec = max_bytes_per_sec

        logger.info("Network client initialized")

    async def download_image(self, url: str) -> Tuple[Optional[bytes], str, int]:
        """
        Downloads the image from the given URL and caches it.

        :param url: The image URL.
        """
        retry_delay = 1  # Initial delay in seconds
        logger.trace(f"Starting download for URL: url")

        for attempt in range(self.max_retries):
            try:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        logger.error("HTTP error for %s: status=%d", url, response.status)
                        return None, "", response.status

                    content_length = response.content_length or 0
                    content_type = response.headers.get('Content-Type', 'image/png')
                    extension = self._get_extension_from_content_type(content_type)


                    max_length = 10 * 1024 * 1024
                    if content_length and content_length > max_length:
                        logger.error("File exceeds size limit")
                        raise FileTooLargeError(content_length, max_length)

                    bytes_received = 0
                    chunks = []
                    async for chunk in response.content.iter_chunked(1024):
                        chunks.append(chunk)
                        bytes_received += len(chunk)
                        if bytes_received > max_length:
                            logger.error("File exceeds size limit")
                            raise FileTooLargeError(bytes_received, max_length)

                        if content_length > 0:
                            progress = round((bytes_received / content_length) * 100, 2)
                            self.downloadProgress.emit(url, progress)

                    return b''.join(chunks), extension, response.status

            except (ClientConnectionError, ServerDisconnectedError, TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                    continue
                raise NetworkError(f"Connection failed after {self.max_retries} retries") from e

            except Exception as e:
                logger.exception(f"Unhandled error during download of {url}, {str(e)}")
                raise

    @staticmethod
    def _get_extension_from_content_type(content_type: str) -> str:
        if not content_type or '/' not in content_type:
            return "png"

        subtype = content_type.split('/')[-1].lower()
        subtype = {
            'jpeg': 'jpg',
            'svg+xml': 'svg',
        }.get(subtype, subtype)

        return subtype if subtype in VALID_IMAGE_FORMATS else "png"

    async def close(self):
        if self.session:
            a = await self.session.close()
            if self.session.closed:
                logger.debug("Session closed successfully")
            else:
                logger.debug("Session closing unsuccessful")
        else:
            logger.warning("No session to close.")

    def __del__(self):
        if not self.session.closed:
            logger.warning("NetworkClient session not closed properly, Closing Now ")
            # Schedule async close without blocking
            try:
                if loop := asyncio.get_event_loop():
                    loop.create_task(self._safe_close())
            except:
                pass  # No loop available

    async def _safe_close(self):
        """Async close handler for __del__"""
        try:
            await self.close()

        except Exception as e:
            logger.debug(f"Background close failed: {e}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()


class ImageDownloader(QObject):
    imageDownloaded = Signal(str, QPixmap, Path) #url, pixmap, path
    downloadProgress = Signal(str, float)
    downloadError = Signal(str, int, str)

    def __init__(self,
                 cache_dir: Path = Path(".cache"),
                 max_concurrent: int = 5,
                 max_cache_mb: int = 100,
                 cache_expiry: int = 30,
                 max_retries: int = 3,
                 timeout: int = 30,
                 parent=None):
        super().__init__(parent)
        logger.info(f"Initializing ImageDownloader with max_concurrent={max_concurrent} ")
        self.cache = CacheManager(cache_dir, max_cache_mb, cache_expiry)
        self.network = NetworkClient(max_retries, timeout)
        self.network.downloadProgress.connect(self.downloadProgress.emit)
        self.semaphore = asyncio.Semaphore(max_concurrent)

    @staticmethod
    def is_valid_image_url(url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)

    async def fetch(self, url: str, cache_in_memory: bool = True) ->Optional[Path]:
        if not self.is_valid_image_url(url):
            logger.debug(f"Invalid image url: {url}")
            self.downloadError.emit(url, 0, "Invalid URL")
            return None

        # Check cache first
        if pixmap := self.cache.get_from_cache(url, cache_in_memory):
            path = self.cache.check_in_cache(url)
            self.imageDownloaded.emit(url, pixmap, path)
            return path

        logger.debug(f"Downloading {url}")
        async with self.semaphore:
            path = await self._download_and_cache(url, cache_in_memory)
            return path

    async def _download_and_cache(self, url: str, cache_in_memory: bool)->Optional[Path]:
        try:
            image_data, extension, status = await self.network.download_image(url)
            if not image_data:
                self.downloadError.emit(url, status, f"HTTP {status} error")
                return None

            pixmap = QPixmap()
            if not pixmap.loadFromData(image_data):
                raise ValueError("Invalid image data")

            url_hash = CacheManager.hash_url(url)
            path = self.cache.get_cache_path(url, extension)
            await self.cache.store(url_hash, pixmap, extension, cache_in_memory)

            self.imageDownloaded.emit(url, pixmap, path)
            return path

        except InvalidURL:
            self.downloadError.emit(url, 0, "Invalid URL. Please check the link.")
            logger.error("Invalid URL: %s", url)
            return None

        except ClientResponseError as e:
            self.downloadError.emit(url, e.status, f"Server error (HTTP {e.status}). Please try again later.")
            logger.error("ClientResponseError for %s: %s (status=%d)", url, str(e), e.status)
            return None

        except ClientPayloadError:
            self.downloadError.emit(url, 0, "Image data is corrupted or incomplete.")
            logger.error("ClientPayloadError for %s", url)
            return None

        except SSLError:
            self.downloadError.emit(url, 0,
                                    "Secure connection failed. The server’s security certificate may be invalid.")
            logger.error("SSLError for %s", url)
            return None

        except socket.gaierror:
            self.downloadError.emit(url, 0, "Couldn’t find the server. Please check your internet or URL.")
            logger.error("Socket.gaierror for %s", url)
            return None

        except OSError as e:
            self.downloadError.emit(url, 0, "A system error occurred while downloading the image.")
            logger.error("OSError for %s: %s", url, str(e))
            return None

        except aiohttp.ClientError as e:
            self.downloadError.emit(url, 0, "A network error occurred. Please try again later.")
            logger.error("ClientError for %s: %s", url, str(e))
            return None

        except Exception as e:
            self.downloadError.emit(url, 0, "An unexpected error occurred. Please try again.")
            logger.exception("Unexpected error for %s: %s", url, str(e))
            return None

    async def close(self) -> None:
        await self.network.close()

    def __del__(self) -> None:
        del self.network

if __name__ == "__main__":
    app = QApplication(sys.argv)
    async def main():
        url = "https://s4.anilist.co/file/anilistcdn/media/anime/banner/101922-33MtJGsUSxga.jpg"
        downloader = ImageDownloader()
        downloader.downloadProgress.connect(print)
        downloader.imageDownloaded.connect(lambda url, pixmap, path: print("path", url, path))
        await downloader.fetch(url, cache_in_memory=False)

    asyncio.run(main())
    sys.exit(app.exec())

