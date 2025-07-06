from numpy.random.mtrand import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, String
from sqlalchemy.orm import selectinload, Mapped, mapped_column, sessionmaker
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Union
from datetime import datetime, timezone
from enum import Enum

from AnillistPython import MediaType
from database.models import UserLibrary, UserCategory, library_category, Manga, Anime
from database.repo.media import AsyncMediaRepository


class AsyncLibraryRepository:
    def __init__(self, session_maker: sessionmaker, media_repo: AsyncMediaRepository):
        self.session_maker = session_maker
        self.media_repo = media_repo

    def get_library_entry_type(self, entry: UserLibrary)->Optional[MediaType]:
        anime_id = entry.anime_id
        if anime_id is not None:
            return MediaType.ANIME
        manga_id = entry.manga_id
        if manga_id is not None:
            return MediaType.MANGA
        return None

    def get_library_entry_id(self, entry: UserLibrary)->Optional[int]:
        anime_id = entry.anime_id
        manga_id = entry.manga_id
        return manga_id or anime_id or None

    async def get_media_data(self, entry: UserLibrary)->Optional[Union[Anime, Manga]]:
        media_id = self.get_library_entry_id(entry)
        if media_id is None:
            return None
        media_type = self.get_library_entry_type(entry)
        if media_type is None:
            return None

        return await self.media_repo.get_by_id(media_id, media_type)



    async def add_library_entry(
            self,
            user_id: int,
            media_id: int,
            media_type: MediaType,
            status_id: Optional[int] = None,
            progress: int = 0,
            categories: List[UserCategory] = None,
    ) -> UserLibrary:
        """Add a new library entry for a user (anime or manga)."""

        library_entry = UserLibrary(
            user_id=user_id,
            manga_id=media_id if media_type == MediaType.ANIME else None,
            anime_id=media_id if media_type == MediaType.ANIME else None,
            status_id=status_id,
            progress=progress,
            categories=categories,
        )
        async with self.session_maker() as session:
            session.add(library_entry)
            await session.commit()
            await session.refresh(library_entry)
            return library_entry

    async def create_category(
            self, user_id: int, name: str, description: str = "", hidden: bool = False
    ) -> UserCategory:
        """Create a new category for a user."""
        category = UserCategory(
            user_id=user_id,
            name=name,
            description=description,
            hidden=hidden,
            created_at=datetime.now(timezone.utc)
        )
        async with self.session_maker() as session:
            session.add(category)
            await session.commit()
            await session.refresh(category)
            return category

    async def get_library_entry(self, library_id: int) -> Optional[UserLibrary]:
        """Retrieve a specific library entry by its ID, including related categories."""
        query = (
            select(UserLibrary)
            .options(selectinload(UserLibrary.categories))
            .where(UserLibrary.id == library_id)
        )
        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_user_library(
            self, user_id: int, include_categories: bool = True
    ) -> Sequence[UserLibrary]:
        """Retrieve all library entries for a user, optionally including categories."""
        query = select(UserLibrary).where(UserLibrary.user_id == user_id)
        if include_categories:
            query = query.options(selectinload(UserLibrary.categories))

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def update_library_entry(
            self,
            library_id: int,
            status_id: Optional[int] = None,
            progress: Optional[int] = None
    ) -> Optional[UserLibrary]:
        """Update a library entry's status or progress."""
        library_entry = await self.get_library_entry(library_id)
        if not library_entry:
            return None
        if status_id is not None:
            library_entry.status_id = status_id
        if progress is not None:
            library_entry.progress = progress
        async with self.session_maker() as session:
            await session.commit()
            await session.refresh(library_entry)
            return library_entry

    async def delete_library_entry(self, library_id: int) -> bool:
        """Delete a library entry by its ID."""
        query = delete(UserLibrary).where(UserLibrary.id == library_id)
        async with self.session_maker() as session:
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0

    async def add_category_to_library_entry(self, library_id: int, category_id: int) -> bool:
        """Add a category to a library entry."""
        library_entry = await self.get_library_entry(library_id)
        if not library_entry:
            return False
        async with self.session_maker() as session:
            category = await session.get(UserCategory, category_id)
            if not category:
                return False
            if category not in library_entry.categories:
                library_entry.categories.append(category)
                await session.commit()
                return True
            return False

    async def remove_category_from_library_entry(self, library_id: int, category_id: int) -> bool:
        """Remove a category from a library entry."""
        library_entry = await self.get_library_entry(library_id)
        if not library_entry:
            return False
        async with self.session_maker() as session:
            category = await session.get(UserCategory, category_id)
            if not category:
                return False
            if category in library_entry.categories:
                library_entry.categories.remove(category)
                await session.commit()
                return True
            return False

    async def get_library_entries_by_category(
            self, user_id: int, category_id: int, media_type: Optional[MediaType] = None
    ) -> Sequence[UserLibrary]:
        """Retrieve all library entries for a user in a specific category, optionally filtered by media type."""
        query = (
            select(UserLibrary)
            .join(library_category)
            .where(
                UserLibrary.user_id == user_id,
                library_category.c.category_id == category_id
            )
        )
        if media_type:
            media_filter = UserLibrary.anime_id.is_not(None) if media_type == MediaType.ANIME else UserLibrary.manga_id.is_not(None)
            query = query.where(media_filter)
        query = query.options(selectinload(UserLibrary.categories))
        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def get_all_categories(self, user_id: int) -> Sequence[UserCategory]:
        """Retrieve all categories for a user."""
        query = select(UserCategory).where(UserCategory.user_id == user_id)
        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def count_all_library_items(self, user_id: int, media_type: MediaType) -> int:
        """Count all library entries for a user by media type."""
        media_filter = UserLibrary.anime_id.is_not(None) if media_type == MediaType.ANIME else UserLibrary.manga_id.is_not(None)
        query = (
            select(func.count())
            .select_from(UserLibrary)
            .where(
                UserLibrary.user_id == user_id,
                media_filter
            )
        )
        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalar_one()

    async def count_library_items_by_category(self, user_id: int, media_type: MediaType) -> Dict[int, int]:
        """Count library entries per category for a user by media type."""
        media_filter = UserLibrary.anime_id.is_not(None) if media_type == MediaType.ANIME else UserLibrary.manga_id.is_not(None)
        query = (
            select(library_category.c.category_id, func.count(library_category.c.library_id))
            .join(UserLibrary, library_category.c.library_id == UserLibrary.id)
            .where(
                UserLibrary.user_id == user_id,
                media_filter
            )
            .group_by(library_category.c.category_id)
        )
        async with self.session_maker() as session:
            result = await session.execute(query)
            return {category_id: count for category_id, count in result.all()}

    async def get_all_library(self, media_type: MediaType, include_categories: bool = True) -> Sequence[UserLibrary]:
        """Retrieve all library entries across all users by media type, optionally including categories."""
        media_filter = UserLibrary.anime_id.is_not(None) if media_type == MediaType.ANIME else UserLibrary.manga_id.is_not(None)
        query = select(UserLibrary).where(media_filter)
        if include_categories:
            query = query.options(selectinload(UserLibrary.categories))
        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()