import asyncio
import os
from pathlib import Path
from typing import List, Optional, Dict, Union, Callable, Awaitable, Coroutine, Any

import httpx
import portalocker
import time
from PySide6.QtCore import Signal, QObject, QTimer
from gql.transport.exceptions import TransportError
from graphql import GraphQLError
from qasync import asyncSlot

from AnillistPython import (
    AniListClient, MediaType, AnilistMedia, MediaQueryBuilder, SearchQueryBuilder, AnilistSearchResult
)
import pickle
from loguru import logger


import asyncio
import time
import pickle
import hashlib
from typing import List, Optional
from pathlib import Path

from PySide6.QtCore import Signal, QObject, QTimer
from qasync import asyncSlot

from AnillistPython import (
    AniListClient, MediaType, AnilistMedia, MediaQueryBuilder
)
from loguru import logger

class AnilistHelper:
    TTL_RULES = {
        "popular": 7 * 24 * 3600,    # 1 week
        "top_rated": 7 * 24 * 3600,  # 1 week
        "hero_banner": 24 * 3600,    # 1 day
        "trending": 24 * 3600,       # 1 day
        "latest": 2 * 3600,          # 2 hours
    }

    def __init__(self, url: str = "https://graphql.anilist.co", cache_dir: str = "./anilist_joblib_cache"):
        try:
            self.client = AniListClient(url)
        except Exception as e:
            raise e
        self.cache_dir = Path(cache_dir)
        self.cache_dir = self.cache_dir.joinpath("anilist_helper")
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            if not self.cache_dir.is_dir() or not os.access(self.cache_dir, os.W_OK):
                raise PermissionError(f"Cache directory {self.cache_dir} is not writable")
        except Exception as e:
            logger.error(f"Failed to initialize cache directory: {e}")
            raise

    @asyncSlot()
    async def connect(self):
        try:
            await self.client.connect()
            logger.info("Connected to AniList")
        except Exception as e:
            logger.error(f"Failed to connect to AniList: {e}")
            raise

    async def _safe_call(self, coro: Coroutine, *, context: str = "", raise_on_fail: bool = True) -> Optional[Any]:
        try:
            return await coro
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            logger.error(f"{context}: Connection error - {e}")
            if raise_on_fail:
                raise ConnectionError(f"{context}: Unable to connect to AniList API") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"{context}: HTTP error {e.response.status_code} - {e.response.text}")
            if raise_on_fail:
                raise
        except httpx.RequestError as e:
            logger.error(f"{context}: Request error - {e}")
            if raise_on_fail:
                raise
        except TransportError as e:
            logger.error(f"{context}: Transport error - {e}")
            if raise_on_fail:
                raise
        except GraphQLError as e:
            logger.error(f"{context}: GraphQL error - {e.message}")
            if raise_on_fail:
                raise
        except Exception as e:
            logger.exception(f"{context}: Unexpected error - {e}")
            if raise_on_fail:
                raise

        return None

    def _is_expired(self, cached_at: float, ttl_seconds: int) -> bool:
        return (time.time() - cached_at) > ttl_seconds

    def _make_cache_filename(self, prefix: str, builder: Union[MediaQueryBuilder, SearchQueryBuilder],
                            media_type: MediaType, page: int, per_page: int) -> Path:
        key = f"{prefix}_{hash(builder)}_{media_type.value}_{page}_{per_page}"
        logger.critical(f"Cache key: {key}, hash: {hash(builder)}")
        filename = hashlib.sha256(key.encode()).hexdigest() + ".pkl"
        return self.cache_dir / filename

    async def _load_or_fetch(self, filename: Path, ttl: int, fetch_fn: Callable[[], Awaitable[dict]]) -> dict:
        if filename.exists():
            try:
                with portalocker.Lock(filename, "rb", timeout=1) as f:
                    cached = pickle.load(f)
                if not self._is_expired(cached["cached_at"], ttl):
                    logger.debug(f"Cache HIT: {filename.name}")
                    return cached
                else:
                    logger.debug(f"Cache EXPIRED: {filename.name}")
            except Exception as e:
                logger.warning(f"Failed to load cache {filename.name}: {e}")

        logger.debug(f"Cache MISS: {filename.name}, fetching from API")
        try:
            data = await fetch_fn()
        except Exception as e:
            logger.error(f"API fetch failed: {e}")
            raise
        cached = {"data": data, "cached_at": time.time()}
        try:
            with portalocker.Lock(filename, "wb", timeout=1) as f:
                pickle.dump(cached, f)
        except Exception as e:
            logger.warning(f"Failed to write cache {filename.name}: {e}")
        return cached

    async def get_hero_banner(self, fields: MediaQueryBuilder, search_filter: SearchQueryBuilder,
                              media_type: MediaType, pages: int) -> Optional[AnilistSearchResult]:
        ttl = self.TTL_RULES["hero_banner"]
        filename = self._make_cache_filename("hero_banner", fields, media_type, 1, pages)

        if media_type == MediaType.MANGA:
            result = await self._safe_call(
                self._load_or_fetch(filename, ttl, lambda: self.client.search_manga(fields, search_filter, None)),
                context="get_hero_banner (MANGA)"
            )
        elif media_type == MediaType.ANIME:
            result = await self._safe_call(
                self._load_or_fetch(filename, ttl, lambda: self.client.search_anime(fields, search_filter, None)),
                context="get_hero_banner (ANIME)"
            )
        else:
            return None

        return result["data"] if result else None

    async def get_trending(self, fields: MediaQueryBuilder, media_type: MediaType, page: int = 1, per_page: int = 5) -> \
    Optional[AnilistSearchResult]:
        ttl = self.TTL_RULES["trending"]
        filename = self._make_cache_filename("trending", fields, media_type, page, per_page)

        result = await self._safe_call(
            self._load_or_fetch(filename, ttl, lambda: self.client.get_trending(fields, media_type, page, per_page)),
            context="get_trending"
        )
        return result["data"] if result else None

    async def get_top_popular(self, fields: MediaQueryBuilder, media_type: MediaType, page: int = 1,
                              per_page: int = 5) -> Optional[AnilistSearchResult]:
        ttl = self.TTL_RULES["popular"]
        filename = self._make_cache_filename("popular", fields, media_type, page, per_page)

        result = await self._safe_call(
            self._load_or_fetch(filename, ttl, lambda: self.client.get_top_popular(fields, media_type, page, per_page)),
            context="get_top_popular"
        )
        return result["data"] if result else None

    async def get_latest(self, fields: MediaQueryBuilder, media_type: MediaType, page: int = 1, per_page: int = 5) -> \
    Optional[AnilistSearchResult]:
        ttl = self.TTL_RULES["latest"]
        filename = self._make_cache_filename("latest", fields, media_type, page, per_page)

        result = await self._safe_call(
            self._load_or_fetch(filename, ttl, lambda: self.client.get_latest(fields, media_type, page, per_page)),
            context="get_latest"
        )

    async def get_top_rated(self, fields: MediaQueryBuilder, media_type: MediaType, page: int = 1, per_page: int = 5) -> \
    Optional[AnilistSearchResult]:
        ttl = self.TTL_RULES["top_rated"]
        filename = self._make_cache_filename("top_rated", fields, media_type, page, per_page)

        return (await self._safe_call(
            self._load_or_fetch(filename, ttl, lambda: self.client.get_top_rated(fields, media_type, page, per_page)),
            context="get_top_rated"
        ))["data"] if self else None


    async def search(self, media_type: MediaType, fields: MediaQueryBuilder, filters: SearchQueryBuilder, query,
                     page: int, per_page: int) -> Optional[AnilistSearchResult]:
        if media_type == MediaType.MANGA:
            return await self._safe_call(
                self.client.search_manga(fields, filters, query, page, per_page),
                context="search_manga"
            )
        elif media_type == MediaType.ANIME:
            return await self._safe_call(
                self.client.search_anime(fields, filters, query, page, per_page),
                context="search_anime"
            )
        return None

    def clear_cache(self, prefix: Optional[str] = None) -> None:
        """Clear all cache files or those matching a specific prefix."""
        try:
            for file in self.cache_dir.glob("*.pkl"):
                if prefix is None or file.name.startswith(hashlib.sha256(prefix.encode()).hexdigest()):
                    file.unlink()
                    logger.debug(f"Deleted cache file: {file.name}")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")

async def main():
    helper = AnilistHelper()
    await helper.connect()

    # Define the fields you want to query
    fields = MediaQueryBuilder().include_title()
    search = SearchQueryBuilder()
    media_type = MediaType.MANGA
    pages = 1

    # Example: Get trending anime page 1 (should cache for 1 day)
    # trending_anime = await helper.get_trending(fields, MediaType.ANIME, page=1, per_page=1)
    trending_anime = await helper.get_hero_banner(fields, search, media_type, pages)
    print(trending_anime)


if __name__ == "__main__":
    asyncio.run(main())