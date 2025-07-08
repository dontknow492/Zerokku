import asyncio

from loguru import logger
from numpy.random.mtrand import Sequence
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, String, and_
from sqlalchemy.orm import selectinload, Mapped, mapped_column, sessionmaker
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Union, Tuple
from datetime import datetime, timezone
from enum import Enum

from AnillistPython import MediaType, MediaStatus, MediaFormat, MediaSource, MediaSeason
from database.models import UserLibrary, UserCategory, library_category, Manga, Anime
from database.repo.media import AsyncMediaRepository, SortBy, SortOrder


class AsyncLibraryRepository:
    def __init__(self, session_maker: sessionmaker, media_repo: AsyncMediaRepository, user_id: int):
        self.session_maker = session_maker
        self.media_repo = media_repo

        self.user_id = user_id
        self.categories: Dict[str, UserCategory] = {}



        # asyncio.ensure_future(self._post_init())

    async def _post_init(self):
        logger.info(f"Starting _post_init for user_id: {self.user_id}")
        try:
            categories = await self.get_all_categories(self.user_id)
            for category in categories:
                self.categories[category.name] = category
                logger.debug(f"Loaded category: {category.name}")
            logger.success(
                f"_post_init completed. Loaded {len(self.categories)} categories for user_id: {self.user_id}")
        except Exception as e:
            logger.error(f"Error during _post_init for user_id {self.user_id}: {e}", exc_info=True)

    def get_categories(self) -> Dict[str, UserCategory]:
        logger.debug(f"Retrieving categories for user_id: {self.user_id}")
        return self.categories

    def _get_category_from_cache(self, category_id: int) -> Optional[UserCategory]:
        logger.debug(f"Retrieving category for user_id: {self.user_id}")
        for category in self.categories.values():
            if category.id == category_id:
                return category
        return None

    def get_library_entry_type(self, entry: UserLibrary) -> Optional[MediaType]:
        logger.debug(f"Determining media type for library entry ID: {entry.id}")
        anime_id = entry.anime_id
        if anime_id is not None:
            logger.debug(f"Entry {entry.id} is ANIME (anime_id: {anime_id})")
            return MediaType.ANIME
        manga_id = entry.manga_id
        if manga_id is not None:
            logger.debug(f"Entry {entry.id} is MANGA (manga_id: {manga_id})")
            return MediaType.MANGA
        logger.warning(f"Entry {entry.id} has no associated media type (anime_id and manga_id are None).")
        return None

    def get_library_entry_id(self, entry: UserLibrary) -> Optional[int]:
        logger.debug(f"Extracting media ID for library entry ID: {entry.id}")
        anime_id = entry.anime_id
        manga_id = entry.manga_id
        media_id = manga_id or anime_id or None
        if media_id:
            logger.debug(f"Media ID for entry {entry.id}: {media_id}")
        else:
            logger.warning(f"No media ID found for library entry ID: {entry.id}")
        return media_id

    def get_library_entry_id_type(self, entry: UserLibrary) -> Optional[Tuple[int, MediaType]]:
        logger.debug(f"Extracting media ID and type for library entry ID: {entry.id}")
        return self.get_library_entry_id(entry), self.get_library_entry_type(entry)

    async def get_media_data(self, entry: UserLibrary) -> Optional[Union[Anime, Manga]]:
        logger.info(f"Fetching media data for library entry ID: {entry.id}")
        media_id = self.get_library_entry_id(entry)
        if media_id is None:
            logger.warning(f"Cannot get media data: No media ID found for entry {entry.id}.")
            return None
        media_type = self.get_library_entry_type(entry)
        if media_type is None:
            logger.warning(f"Cannot get media data: No media type found for entry {entry.id}.")
            return None

        try:
            media_data = await self.media_repo.get_by_id(media_id, media_type)
            if media_data:
                logger.success(
                    f"Successfully retrieved media data for entry {entry.id}: {media_data.title_english or media_data.id}")
            else:
                logger.warning(
                    f"Media data not found for {media_type.value} ID {media_id} (linked to entry {entry.id}).")
            return media_data
        except Exception as e:
            logger.error(f"Error fetching media data for entry {entry.id} ({media_type.value} ID {media_id}): {e}",
                         exc_info=True)
            return None

    async def add_library_entry(
            self,
            user_id: int,
            media_id: int,
            media_type: MediaType,
            status_id: Optional[int] = None,
            progress: int = 0,
            categories: Optional[List[UserCategory]] = None,  # Changed to Optional as it can be None
    ) -> Optional[UserLibrary]:  # Changed return type to Optional as it can return None on error
        """Add a new library entry for a user (anime or manga)."""
        logger.info(
            f"Attempting to add library entry for user {user_id} (Media Type: {media_type.name}, Media ID: {media_id})")
        logger.debug(
            f"Initial status_id: {status_id}, progress: {progress}, categories: {[c.name for c in categories] if categories else 'None'}")

        # Ensure categories is an empty list if None, to avoid issues with relationship assignment
        if categories is None:
            categories = []

        # Determine which ID to set based on media_type
        anime_id = media_id if media_type == MediaType.ANIME else None
        manga_id = media_id if media_type == MediaType.MANGA else None

        # Basic validation to prevent adding both anime_id and manga_id or neither
        if anime_id is None and manga_id is None:
            logger.warning(
                f"Failed to add library entry: Neither anime_id nor manga_id could be set for media_type {media_type.name}.")
            return None

        library_entry = UserLibrary(
            user_id=user_id,
            manga_id=manga_id,
            anime_id=anime_id,
            status_id=status_id,
            progress=progress,
            categories=categories,
        )
        async with self.session_maker() as session:
            try:
                session.add(library_entry)
                await session.commit()
                await session.refresh(library_entry)
                logger.success(f"Successfully added library entry ID {library_entry.id} for user {user_id}.")
                return library_entry
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Error adding library entry for user {user_id}, media {media_id} ({media_type.name}): {e}",
                    exc_info=True)
                return None

    async def create_category(
            self, user_id: int, name: str, description: str = "", hidden: bool = False
    ) -> Optional[UserCategory]:
        """Create a new category for a user."""
        logger.info(f"Attempting to create category '{name}' for user {user_id}.")
        logger.debug(f"Description: '{description}', Hidden: {hidden}")

        async with self.session_maker() as session:
            try:
                # Check for existing category with the same name for this user
                existing_category_stmt = select(UserCategory).where(
                    UserCategory.user_id == user_id,
                    UserCategory.name == name
                )
                existing_category_result = await session.execute(existing_category_stmt)
                if existing_category_result.scalar_one_or_none():
                    logger.warning(f"Category '{name}' already exists for user {user_id}. Cannot create duplicate.")
                    return None

                category = UserCategory(
                    user_id=user_id,
                    name=name,
                    description=description,
                    hidden=hidden,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(category)
                await session.commit()
                await session.refresh(category)
                self.categories[name] = category  # Update in-memory cache
                logger.success(f"Successfully created category '{name}' (ID: {category.id}) for user {user_id}.")
                return category
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating category '{name}' for user {user_id}: {e}", exc_info=True)
                return None

    async def get_category_from_id(self, category_id: int) -> Optional[UserCategory]:
        """Get a category by its ID, optionally from cache."""
        async with self.session_maker() as session:
            async with session.begin():
                category = self._get_category_from_cache(category_id)
                if category is not None:
                    return category

                stmt = select(UserCategory).where(UserCategory.id == category_id)
                result = await session.execute(stmt)
                category = result.scalar_one_or_none()

                if category is None:
                    logger.warning(f"Category with ID {category_id} not found.")
                    return None

                return category

    async def get_category_from_name(self, category_name: str, user_id: int) -> Optional[UserCategory]:
        """Get a category by its name and user ID, optionally from in-memory cache."""
        async with self.session_maker() as session:
            async with session.begin():
                category = self.categories.get(category_name)
                if category is not None:
                    return category

                stmt = select(UserCategory).where(
                    and_(UserCategory.name == category_name, UserCategory.user_id == user_id)
                )
                result = await session.execute(stmt)
                category = result.scalar_one_or_none()

                if category is None:
                    logger.warning(f"Category with name '{category_name}' not found for user ID {user_id}.")
                    return None

                return category



    async def get_library_entry(self, library_id: int) -> Optional[UserLibrary]:
        """Retrieve a specific library entry by its ID, including related categories."""
        logger.info(f"Attempting to retrieve library entry with ID: {library_id}")
        query = (
            select(UserLibrary)
            .options(selectinload(UserLibrary.categories))
            .where(UserLibrary.id == library_id)
        )
        async with self.session_maker() as session:
            try:
                result = await session.execute(query)
                entry = result.scalar_one_or_none()
                if entry:
                    logger.success(f"Successfully retrieved library entry ID: {library_id}.")
                    logger.debug(f"Retrieved entry: {entry}")
                else:
                    logger.warning(f"Library entry with ID {library_id} not found.")
                return entry
            except Exception as e:
                logger.error(f"Error retrieving library entry with ID {library_id}: {e}", exc_info=True)
                return None

    async def get_user_library(
            self, user_id: int, include_categories: bool = True
    ) -> Sequence[UserLibrary]:
        """Retrieve all library entries for a user, optionally including categories."""
        logger.info(f"Attempting to retrieve all library entries for user {user_id}.")
        logger.debug(f"Include categories: {include_categories}")
        query = select(UserLibrary).where(UserLibrary.user_id == user_id)
        if include_categories:
            query = query.options(selectinload(UserLibrary.categories))

        async with self.session_maker() as session:
            try:
                result = await session.execute(query)
                entries = result.scalars().all()
                logger.success(f"Successfully retrieved {len(entries)} library entries for user {user_id}.")
                return entries
            except Exception as e:
                logger.error(f"Error retrieving user library for user {user_id}: {e}", exc_info=True)
                return []

    async def update_library_entry(
            self,
            library_id: int,
            status_id: Optional[int] = None,
            progress: Optional[int] = None
    ) -> Optional[UserLibrary]:
        """Update a library entry's status or progress."""
        logger.info(f"Attempting to update library entry ID: {library_id}.")
        logger.debug(f"Update parameters: status_id={status_id}, progress={progress}")

        library_entry = await self.get_library_entry(library_id)
        if not library_entry:
            logger.warning(f"Update failed: Library entry with ID {library_id} not found.")
            return None

        updated_fields = []
        if status_id is not None and library_entry.status_id != status_id:
            library_entry.status_id = status_id
            updated_fields.append(f"status_id to {status_id}")
        if progress is not None and library_entry.progress != progress:
            library_entry.progress = progress
            updated_fields.append(f"progress to {progress}")

        if not updated_fields:
            logger.info(f"No changes detected for library entry ID {library_id}. No update performed.")
            return library_entry  # Return the original entry if no changes

        async with self.session_maker() as session:
            try:
                # Merge the detached object into the current session
                session.add(library_entry)  # This will either add or merge if already exists by primary key
                await session.commit()
                await session.refresh(library_entry)
                logger.success(f"Successfully updated library entry ID {library_id}: {', '.join(updated_fields)}.")
                return library_entry
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating library entry ID {library_id}: {e}", exc_info=True)
                return None

    async def delete_library_entry(self, library_id: int) -> bool:
        """Delete a library entry by its ID."""
        logger.info(f"Attempting to delete library entry with ID: {library_id}.")

        # First, check if the entry exists to provide better logging
        existing_entry = await self.get_library_entry(library_id)
        if not existing_entry:
            logger.warning(f"Delete failed: Library entry with ID {library_id} not found.")
            return False

        async with self.session_maker() as session:
            try:
                # Merge the existing entry to the session in case it's detached
                merged_entry = await session.merge(existing_entry)
                await session.delete(merged_entry)
                await session.commit()

                # Verify deletion using async-compatible select
                result = await session.execute(select(UserLibrary).filter_by(id=library_id))
                if result.scalar_one_or_none() is None:
                    logger.success(f"Successfully deleted library entry ID: {library_id}.")
                    return True
                else:
                    logger.warning(f"Deletion of library entry ID {library_id} seemed to fail, entry still exists.")
                    return False

            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error deleting library entry ID {library_id}: {e}", exc_info=True)
                return False
            except:
                raise

    async def delete_category(self, category_id: int) -> bool:
        """Delete a category by its ID."""
        logger.info(f"Attempting to delete category with ID: {category_id}.")
        category = await self.get_category_from_id(category_id)
        if not category:
            logger.warning(f"Delete failed: Category with ID {category_id} not found.")
            return False

        async with self.session_maker() as session:
            try:
                async with session.begin():
                    await session.delete(category)
                    self.categories.pop(category.name, None)

                    return True

            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error deleting category ID {category_id}: {e}", exc_info=True)
                return False
            except:
                raise

    async def add_category_to_library_entry(self, library_id: int, category_id: int) -> bool:
        """Add a category to a library entry."""
        logger.info(f"Attempting to add category {category_id} to library entry {library_id}.")
        async with self.session_maker() as session:
            async with session.begin():
                try:
                    library_entry = await session.get(
                        UserLibrary,
                        library_id,
                        options=[selectinload(UserLibrary.categories)]
                    )
                    if not library_entry:
                        logger.warning(f"Failed to add category: Library entry {library_id} not found.")
                        return False

                    category = await session.get(UserCategory, category_id)
                    if not category:
                        logger.warning(f"Failed to add category: Category {category_id} not found.")
                        return False

                    if category in library_entry.categories:
                        logger.info(f"Category {category_id} already associated with library entry {library_id}.")
                        return False

                    library_entry.categories.append(category)
                    logger.success(f"Successfully added category {category_id} to library entry {library_id}.")
                    return True

                except Exception as e:
                    logger.error(f"Error adding category {category_id} to library entry {library_id}: {e}",
                                 exc_info=True)
                    return False

    async def remove_category_from_library_entry(self, library_id: int, category_id: int) -> bool:
        """Remove a category from a library entry."""
        logger.info(f"Attempting to remove category {category_id} from library entry {library_id}.")
        async with self.session_maker() as session:
            async with session.begin():
                try:
                    library_entry = await session.get(UserLibrary, library_id,
                                                      options=[selectinload(UserLibrary.categories)])
                    if not library_entry:
                        logger.warning(f"Failed to remove category: Library entry {library_id} not found.")
                        return False

                    category = await session.get(UserCategory, category_id)
                    if not category:
                        logger.warning(f"Failed to remove category: Category {category_id} not found.")
                        return False

                    if category not in library_entry.categories:
                        logger.info(f"Category {category_id} is not associated with library entry {library_id}.")
                        return False  # Not associated

                    library_entry.categories.remove(category)
                    # await session.commit()
                    logger.success(f"Successfully removed category {category_id} from library entry {library_id}.")
                    return True
                except Exception as e:
                    logger.error(f"Error removing category {category_id} from library entry {library_id}: {e}",
                                 exc_info=True)
                    return False

    async def get_library_entries_by_category(
            self, user_id: int, category_id: int, media_type: Optional[MediaType] = None
    ) -> Sequence[UserLibrary]:
        """Retrieve all library entries for a user in a specific category, optionally filtered by media type."""
        logger.info(f"Attempting to get library entries for user {user_id} in category {category_id}.")
        logger.debug(f"Filter by media_type: {media_type.name if media_type else 'None'}")

        query = (
            select(UserLibrary)
            .join(library_category)
            .where(
                UserLibrary.user_id == user_id,
                library_category.c.category_id == category_id
            )
        )
        if media_type:
            media_filter = UserLibrary.anime_id.is_not(
                None) if media_type == MediaType.ANIME else UserLibrary.manga_id.is_not(None)
            query = query.where(media_filter)
        query = query.options(selectinload(UserLibrary.categories))

        async with self.session_maker() as session:
            try:
                result = await session.execute(query)
                entries = result.scalars().unique().all()  # Use unique() to prevent duplicates from join
                logger.success(f"Found {len(entries)} library entries for user {user_id} in category {category_id}.")
                return entries
            except Exception as e:
                logger.error(f"Error getting library entries for user {user_id} in category {category_id}: {e}",
                             exc_info=True)
                return []

    async def get_all_categories(self, user_id: int) -> Sequence[UserCategory]:
        """Retrieve all categories for a user."""
        logger.info(f"Attempting to retrieve all categories for user {user_id}.")
        query = select(UserCategory).where(UserCategory.user_id == user_id)
        async with self.session_maker() as session:
            try:
                result = await session.execute(query)
                categories = result.scalars().all()
                logger.success(f"Retrieved {len(categories)} categories for user {user_id}.")
                self.categories.clear()
                self.categories = {category.name: category for category in categories}
                return categories
            except Exception as e:
                logger.error(f"Error retrieving all categories for user {user_id}: {e}", exc_info=True)
                return []

    async def count_all_library_items(self, user_id: int, media_type: MediaType) -> int:
        """Count all library entries for a user by media type."""
        logger.info(f"Attempting to count all {media_type.name} library items for user {user_id}.")
        media_filter = UserLibrary.anime_id.is_not(
            None) if media_type == MediaType.ANIME else UserLibrary.manga_id.is_not(None)
        query = (
            select(func.count())
            .select_from(UserLibrary)
            .where(
                UserLibrary.user_id == user_id,
                media_filter
            )
        )
        async with self.session_maker() as session:
            try:
                result = await session.execute(query)
                count_result = result.scalar_one()
                logger.success(f"Counted {count_result} {media_type.name} library items for user {user_id}.")
                return count_result
            except Exception as e:
                logger.error(f"Error counting all {media_type.name} library items for user {user_id}: {e}",
                             exc_info=True)
                return 0

    async def count_library_items_by_category(self, user_id: int, media_type: MediaType) -> Dict[int, int]:
        """Count library entries per category for a user by media type."""
        logger.info(f"Attempting to count {media_type.name} library items per category for user {user_id}.")
        media_filter = UserLibrary.anime_id.is_not(
            None) if media_type == MediaType.ANIME else UserLibrary.manga_id.is_not(None)
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
            try:
                result = await session.execute(query)
                counts = {category_id: count for category_id, count in result.all()}
                logger.success(f"Counted {len(counts)} categories with {media_type.name} items for user {user_id}.")
                logger.debug(f"Category counts: {counts}")
                return counts
            except Exception as e:
                logger.error(f"Error counting {media_type.name} library items by category for user {user_id}: {e}",
                             exc_info=True)
                return {}

    async def get_all_library(self, media_type: MediaType, include_categories: bool = True) -> Sequence[UserLibrary]:
        """Retrieve all library entries across all users by media type, optionally including categories."""
        logger.info(f"Attempting to retrieve all {media_type.name} library entries across all users.")
        logger.debug(f"Include categories: {include_categories}")
        media_filter = UserLibrary.anime_id.is_not(
            None) if media_type == MediaType.ANIME else UserLibrary.manga_id.is_not(None)
        query = select(UserLibrary).where(media_filter)
        if include_categories:
            query = query.options(selectinload(UserLibrary.categories))
        async with self.session_maker() as session:
            try:
                result = await session.execute(query)
                entries = result.scalars().all()
                logger.success(f"Retrieved {len(entries)} {media_type.name} library entries across all users.")
                return entries
            except Exception as e:
                logger.error(f"Error retrieving all {media_type.name} library entries across all users: {e}",
                             exc_info=True)
                return []

    async def get_user_library_entries(self, user_id: int, media_type: MediaType) -> Sequence[UserLibrary]:
        logger.info(f"Fetching {media_type.name} library entries for user {user_id}.")
        media_filter = UserLibrary.anime_id.is_not(
            None) if media_type == MediaType.ANIME else UserLibrary.manga_id.is_not(None)

        query = select(UserLibrary).where(
            UserLibrary.user_id == user_id,
            media_filter
        )

        async with self.session_maker() as session:
            try:
                async with session.begin():
                    result = await session.execute(query)
                    entries = result.scalars().all()
                    logger.success(f"Found {len(entries)} {media_type.name} entries.")
                    return entries
            except Exception as e:
                logger.error(f"Error fetching library entries: {e}", exc_info=True)
                return []

    async def get_by_advanced_filters(
            self,
            media_type: MediaType,
            user_id: int,
            category_id: Optional[int] = None,
            query: Optional[str] = None,
            min_score: Optional[int] = None,
            max_score: Optional[int] = None,
            min_count: Optional[int] = None,
            max_count: Optional[int] = None,
            min_duration: Optional[int] = None,
            max_duration: Optional[int] = None,
            start_year: Optional[int] = None,
            end_year: Optional[int] = None,
            genres: Optional[List[str]] = None,
            status: Optional[MediaStatus] = None,
            format: Optional[MediaFormat] = None,
            source_material: Optional[MediaSource] = None,
            season: Optional[MediaSeason] = None,
            sort_by: Optional[SortBy] = SortBy.POPULARITY,
            order: SortOrder = SortOrder.DESC,
            limit: int = 10,
            offset: int = 0
    ) -> Union[List[Anime], List[Manga]]:
        logger.info(f"Filtering {media_type.name} results for user {user_id}'s library.")
        library_entries = []
        if category_id:
            library_entries = await self.get_library_entries_by_category(user_id, category_id, media_type)
        else:
            library_entries = await self.get_user_library_entries(user_id, media_type)
        media_ids = list(filter(None, map(self.get_library_entry_id, library_entries)))

        if not media_ids:
            logger.info(f"No {media_type.name} entries found in user {user_id}'s library.")
            return []

        logger.debug(f"Applying filters with {len(media_ids)} scoped media_ids for user {user_id}.")

        return await self.media_repo.get_by_advanced_filters(
            media_type=media_type,
            query=query,
            min_score=min_score,
            max_score=max_score,
            min_count=min_count,
            max_count=max_count,
            min_duration=min_duration,
            max_duration=max_duration,
            start_year=start_year,
            end_year=end_year,
            genres=genres,
            status=status,
            format=format,
            season=season,
            source_material=source_material,
            media_ids=media_ids,
            sort_by=sort_by,
            order=order,
            limit=limit,
            offset=offset
        )



