from enum import Enum
from typing import Sequence, Union, Optional, List

# from cachetools.func import lru_cache, lfu_cache
from functools import lru_cache

from cachetools import LFUCache
from loguru import logger
from sqlalchemy import select, and_, or_, func, between, not_
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from database.models import Anime, Manga, Genre, Tag, Studio

from AnillistPython import MediaType

class SortBy(str, Enum):
    ID = "id"
    ID_MAL = "idMal"
    TITLE_ENGLISH = "title_english"
    TITLE_ROMAJI = "title_romaji"
    TITLE_NATIVE = "title_native"
    START_DATE = "start_date"
    END_DATE = "end_date"
    MEAN_SCORE = "mean_score"
    AVERAGE_SCORE = "average_score"
    POPULARITY = "popularity"
    FAVOURITES = "favourites"
    IS_ADULT = "isAdult"
    EPISODES = "episodes"  # Anime only
    DURATION = "duration"  # Anime only
    CHAPTERS = "chapters"  # Manga only
    VOLUMES = "volumes"  # Manga only

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class GroupByField(str, Enum):
    STATUS = "status_id"
    SEASON = "season_id"
    FORMAT = "format_id"
    COUNTRY = "country_of_origin_id"
    SOURCE = "source_material_id"
    IS_ADULT = "isAdult"

class AsyncMediaRepository:
    def __init__(self, session: sessionmaker):
        self.session_maker = session
        self.genre_cache = LFUCache(maxsize=100)
        self.tag_cache = LFUCache(maxsize=100)
        self.studio_cache = LFUCache(maxsize=100)

    async def get_genre(self, genre_id):
        # Check if the genre is in the cache
        if genre_id in self.genre_cache:
            return self.genre_cache[genre_id]

        async with self.session_maker() as session:
            genre = await session.get(Genre, genre_id)
            if genre:
                self.genre_cache[genre_id] = genre  # Cache the genre
            return genre

    async def get_tag(self, tag_id):
        # Check if the tag is in the cache
        if tag_id in self.tag_cache:
            return self.tag_cache[tag_id]

        async with self.session_maker() as session:
            tag = await session.get(Tag, tag_id)
            if tag:
                self.tag_cache[tag_id] = tag  # Cache the tag
            return tag

    async def get_studio(self, studio_id):
        # Check if the studio is in the cache
        if studio_id in self.studio_cache:
            return self.studio_cache[studio_id]

        async with self.session_maker() as session:
            studio = await session.get(Studio, studio_id)
            if studio:
                self.studio_cache[studio_id] = studio  # Cache the studio
            return studio

    async def get_associated(self, session: AsyncSession, media: Union[Anime, Manga]) -> Union[Anime, Manga]:
        # async with self.session_maker() as session:
        # async with session.begin():
        associated_genres = []
        associated_tags = []
        associated_studios = []

        try:
            for genre in media.genres:
                existing_genre = await self.get_genre(genre.id)
                if existing_genre:
                    associated_genres.append(existing_genre)
                else:
                    new_genre = Genre(id=genre.id, name=genre.name)
                    session.add(new_genre)
                    associated_genres.append(new_genre)

            for tag in media.tags:
                existing_tag = await self.get_tag(tag.id)
                if existing_tag:
                    associated_tags.append(existing_tag)
                else:
                    new_tag = Tag(id=tag.id, name=tag.name, isAdult= tag.isAdult,
                                description=tag.description or "", category=tag.category)
                    session.add(new_tag)
                    associated_tags.append(new_tag)

            for studio in media.studios:
                existing_studio = await self.get_studio(studio.id)
                if existing_studio:
                    associated_studios.append(existing_studio)
                else:
                    new_studio = Studio(id=studio.id, name=studio.name)
                    session.add(new_studio)
                    associated_studios.append(new_studio)

            media.genres = associated_genres
            media.studios = associated_studios
            media.tags = associated_tags

            return media

        except SQLAlchemyError as e:
            logger.error(f"Error associating media entities: {e}")
            raise



    ### Create
    async def create(self, media: Union[Anime, Manga]) -> Union[Anime, Manga]:
        """Create a new media entry"""
        async with self.session_maker() as session:
            async with session.begin():
                try:
                    media = await self.get_associated(session, media)
                    session.add(media)
                    await session.flush()
                    await session.refresh(media)
                    logger.success(f"Media '{media.id}' created.")
                except SQLAlchemyError as e:
                    logger.error(f"Error creating media: {e}")
                    raise
            return media

    async def create_update_media(self, media: Union[Anime, Manga]) -> Union[Anime, Manga]:
        """Create or update a media entry with associated genres, tags, and studios."""
        async with self.session_maker() as session:
            async with session.begin():
                try:
                    # Check if media already exists
                    existing_media = await session.execute(
                        select(type(media)).filter_by(id=media.id)
                    )
                    existing_media = existing_media.scalar()

                    if existing_media:
                        # Update existing media with defined fields
                        updatable_fields = [
                            'idMal', 'site_url', 'title_english', 'title_romaji', 'title_native',
                            'description', 'cover_image_extra_large', 'cover_image_large',
                            'cover_image_medium', 'cover_image_color', 'banner_image',
                            'start_date', 'end_date', 'mean_score', 'average_score',
                            'popularity', 'favourites', 'isAdult', 'synonyms', 'status_id',
                            'season_id', 'format_id', 'country_of_origin_id', 'source_material_id'
                        ]
                        for attr in updatable_fields:
                            value = getattr(media, attr, None)
                            if value is not None:
                                setattr(existing_media, attr, value)
                                logger.success(f"Updated field '{attr}' to '{value}' on existing media ID {media.id}")
                        existing_media = await self.get_associated(session, existing_media)
                        session.add(existing_media)
                        await session.flush()
                        await session.refresh(existing_media)
                        logger.success(
                            f"Successfully updated media: ID={existing_media.id},"
                            f" Title='{existing_media.title_english or existing_media.title_romaji}'")
                        return existing_media
                    else:
                        logger.info(f"Media with ID {media.id} not found. Creating new entry.")

                        # Create new media
                        media = await self.get_associated(session, media)
                        session.add(media)
                        await session.flush()
                        await session.refresh(media)
                        logger.success(
                            f"Successfully created new media: ID={media.id},"
                            f" Title='{media.title_english or media.title_romaji}'")
                        return media
                except SQLAlchemyError as e:
                    logger.error(f"Error creating/updating media: {e}")
                    raise



    ### Get
    async def get_by_id(self, media_id: int, media_type: MediaType) -> Optional[Union[Anime, Manga]]:
        """
        Get media by ID and type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            media_id: The ID of the media to retrieve.
            media_type: The type of media (Anime or Manga).

        Returns:
            The Anime or Manga object if found, otherwise None.
        """
        logger.info(f"Attempting to retrieve {media_type.value} with ID: {media_id}")

        # Determine the model based on media_type
        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                result = await session.execute(select(model).filter(model.id == media_id))
                media_item = result.scalars().first()

                if media_item:
                    logger.success(f"Successfully retrieved {media_type.value} with ID {media_id}.")
                    logger.debug(f"Retrieved media details: {media_item}")
                else:
                    logger.info(f"{media_type.value} with ID {media_id} not found.")
                return media_item
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error while retrieving {media_type.value} with ID {media_id}: {e}",
                             exc_info=True)
                raise  # Re-raise the exception after logging

    async def get_by_title(self, title: str, media_type: MediaType) -> Sequence[Union[Anime, Manga]]:
        """
        Get media by title and type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            title: The title (or part of the title) to search for.
            media_type: The type of media (Anime or Manga).

        Returns:
            A list of Anime or Manga objects matching the title, or an empty list.
        """
        logger.info(f"Attempting to retrieve {media_type.value} by title: '{title}'")

        # Determine the model based on media_type
        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        # This 'self.session_maker()' would typically be an async_sessionmaker instance
        # from SQLAlchemy, which creates an AsyncSession.
        # For this function to run, 'self' must have a 'session_maker' attribute
        # that returns an AsyncSession context manager.
        async with self.session_maker() as session:
            try:
                # Build the query to search across multiple title fields using case-insensitive LIKE
                query = select(model).filter(
                    or_(
                        model.title_english.ilike(f"%{title}%"),
                        model.title_native.ilike(f"%{title}%"),
                        model.title_romaji.ilike(f"%{title}%"),
                        # func.json_each(model.synonyms).ilike(f"%{title}%"), # This line is commented out in original
                    )
                )
                logger.debug(f"Executing query for {media_type.value} with title '{title}'")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.success(f"Found {len(media_items)} {media_type.value}(s) matching title '{title}'.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found matching title '{title}'.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error while retrieving {media_type.value} by title '{title}': {e}",
                             exc_info=True)
                raise  # Re-raise the exception after logging

    async def get_by_multiple_titles(
            self,
            titles: Sequence[str],
            media_type: MediaType,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Get media by multiple titles and type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            titles: A sequence of titles (or parts of titles) to search for.
            media_type: The type of media (Anime or Manga).
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects matching any of the titles,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(f"Attempting to retrieve {media_type.value} by multiple titles: {titles}")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        # Determine the model based on media_type
        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                # Build the OR clause for multiple title searches
                title_filters = [model.title_english.ilike(f"%{title}%") for title in titles]
                query = select(model).filter(or_(*title_filters))
                logger.debug(f"Initial query built with {len(title_filters)} title filters.")

                # Apply media_ids filter if provided
                if media_ids:
                    query = query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                # Apply limit
                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug(f"Executing final query for {media_type.value}.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.success(f"Found {len(media_items)} {media_type.value}(s) matching titles.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found matching the provided titles and filters.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error while retrieving {media_type.value} by multiple titles '{titles}': {e}",
                             exc_info=True)
                raise  # Re-raise the exception after logging

    async def search(
            self,
            query: str,
            media_type: MediaType,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Search media by query and type, including synonyms in the search, with logging.

        Args:
            self: The instance of the class containing the session_maker.
            query: The search string.
            media_type: The type of media (Anime or Manga).
            limit: The maximum number of results to return. Defaults to 10.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects matching the query,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(f"Initiating search for {media_type.name} with query: '{query}'")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                # Build the base query with OR conditions for various title fields and description
                # For synonyms, assuming it's a string field that can be searched with LIKE.
                # If synonyms is a JSON array in your DB, you'd need `func.json_each` or similar
                # as commented out in your original code, which is database-specific.
                base_query = select(model).filter(
                    or_(
                        model.title_english.ilike(f"%{query}%"),
                        model.title_native.ilike(f"%{query}%"),
                        model.title_romaji.ilike(f"%{query}%"),
                        model.description.ilike(f"%{query}%"),
                        model.synonyms.ilike(f"%{query}%")  # Assuming synonyms is a searchable string field
                    )
                )
                logger.debug("Base query constructed with title, description, and synonyms filters.")

                # Apply the limit to the query
                if limit > 0:
                    base_query = base_query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                # Apply media_ids filter if provided
                if media_ids:
                    base_query = base_query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                logger.debug(f"Executing final search query for {media_type.value}.")
                result = await session.execute(base_query)
                media_items = result.scalars().all()

                if media_items:
                    logger.success(f"Found {len(media_items)} {media_type.value}(s) matching query '{query}'.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found matching query '{query}'.")
                return media_items

            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error during search for {media_type.value} with query '{query}': {e}",
                             exc_info=True)
                # Re-raise the exception if you want calling code to handle it,
                # or return an empty list as per original code's error handling.
                # Returning empty list as per original function's error handling.
                return []

            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during search for {media_type.value} with query '{query}': {e}",
                    exc_info=True)
                # Returning empty list as per original function's error handling.
                return []

    ### Update
    async def update(
            self,
            media_id: int,
            update_data: Union[Anime, Manga],
            media_type: MediaType
    ) -> Optional[Union[Anime, Manga]]:
        """
        Update media by ID and type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            media_id: The ID of the media to update.
            update_data: An object (Anime or Manga) containing the fields to update.
                         Only non-None attributes from update_data will be applied.
            media_type: The type of media (Anime or Manga).

        Returns:
            The updated Anime or Manga object if successful, otherwise None.
        """
        logger.info(f"Attempting to update {media_type.value} with ID: {media_id}")
        logger.debug(f"Update data provided: {update_data.__dict__}")

        media = await self.get_by_id(media_id, media_type)
        if not media:
            logger.warning(f"Update failed: {media_type.value} with ID {media_id} not found.")
            return None

        logger.debug(f"Found existing media: {media}")

        # Start a new session for the update operation.
        # It's crucial to perform updates within a transaction.
        async with self.session_maker() as session:
            try:
                # Re-attach the media object to the new session if it came from a different session
                # or if it's a detached instance.
                # The get_by_id method implicitly uses a new session, so 'media' might be detached.
                # Using session.merge() is a safe way to re-attach or get a managed instance.
                media = await session.merge(media)
                logger.debug(f"Media object merged into current session for update: {media.id}")

                updated_fields_count = 0
                for key, value in update_data.__dict__.items():
                    # Ignore 'id' and any attributes that are None in update_data
                    # Also, avoid updating internal SQLAlchemy state attributes (start with '_sa_')
                    if key != "id" and value is not None and not key.startswith('_sa_'):
                        current_value = getattr(media, key, None)
                        if current_value != value:  # Only update if value has changed
                            setattr(media, key, value)
                            updated_fields_count += 1
                            logger.debug(f"Updated field '{key}' from '{current_value}' to '{value}'")

                if updated_fields_count == 0:
                    logger.info(
                        f"No fields to update for {media_type.value} with ID {media_id}. Returning original media.")
                    return media  # No changes were made

                await session.commit()  # Commit the changes to the database
                await session.refresh(
                    media)  # Refresh the object to get any database-generated updates (e.g., updated_at)
                logger.info(f"Successfully updated {media_type.value} with ID {media_id}.")
                return media
            except SQLAlchemyError as e:
                await session.rollback()  # Rollback on error
                logger.error(f"SQLAlchemy Error during update for {media_type.value} with ID {media_id}: {e}",
                             exc_info=True)
                return None
            except Exception as e:
                await session.rollback()  # Rollback on other errors
                logger.error(
                    f"An unexpected error occurred during update for {media_type.value} with ID {media_id}: {e}",
                    exc_info=True)
                return None

    async def delete(self, media_id: int, media_type: MediaType) -> bool:
        """
        Delete media by ID and type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            media_id: The ID of the media to delete.
            media_type: The type of media (Anime or Manga).

        Returns:
            True if the media was successfully deleted, False otherwise.
        """
        logger.info(f"Attempting to delete {media_type.value} with ID: {media_id}")

        media = await self.get_by_id(media_id, media_type)
        if not media:
            logger.warning(f"Delete failed: {media_type.value} with ID {media_id} not found.")
            return False

        logger.debug(f"Found media for deletion: {media}")

        async with self.session_maker() as session:
            try:
                # Re-attach the media object to the new session if it came from a different session
                media = await session.merge(media)
                logger.debug(f"Media object merged into current session for deletion: {media.id}")

                await session.delete(media)
                await session.commit()  # Commit the deletion
                logger.info(f"Successfully deleted {media_type.value} with ID {media_id}.")
                return True
            except SQLAlchemyError as e:
                await session.rollback()  # Rollback on error
                logger.error(f"SQLAlchemy Error during delete for {media_type.value} with ID {media_id}: {e}",
                             exc_info=True)
                return False
            except Exception as e:
                await session.rollback()  # Rollback on other errors
                logger.error(
                    f"An unexpected error occurred during delete for {media_type.value} with ID {media_id}: {e}",
                    exc_info=True)
                return False

    async def get_all(self, media_type: MediaType) -> Sequence[Union[Anime, Manga]]:
        """
        Get all media of a specific type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            media_type: The type of media (Anime or Manga).

        Returns:
            A list of all Anime or Manga objects of the specified type.
        """
        logger.info(f"Attempting to retrieve all {media_type.value} entries.")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                query = select(model)
                logger.debug(f"Executing query to get all {media_type.value}.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                logger.info(f"Retrieved {len(media_items)} {media_type.value}(s).")
                return media_items
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error during get_all for {media_type.value}: {e}", exc_info=True)
                return []
            except Exception as e:
                logger.error(f"An unexpected error occurred during get_all for {media_type.value}: {e}", exc_info=True)
                return []

    async def count(self, media_type: MediaType) -> int:
        """
        Count media of a specific type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            media_type: The type of media (Anime or Manga).

        Returns:
            The count of Anime or Manga objects of the specified type.
        """
        logger.info(f"Attempting to count {media_type.value} entries.")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                query = select(func.count(model.id)).select_from(model)
                logger.debug(f"Executing count query for {media_type.value}.")
                result = await session.execute(query)
                count_result = result.scalars().first()

                logger.info(f"Counted {count_result} {media_type.value}(s).")
                return count_result if count_result is not None else 0
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error during count for {media_type.value}: {e}", exc_info=True)
                return 0
            except Exception as e:
                logger.error(f"An unexpected error occurred during count for {media_type.value}: {e}", exc_info=True)
                return 0

    async def get_by_genres(
            self,
            genres: List[str],
            media_type: MediaType,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Get media by genres and type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            genres: A list of genre names to filter by.
            media_type: The type of media (Anime or Manga).
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects matching the genres,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(f"Attempting to retrieve {media_type.value} by genres: {genres}")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                # Join with the genres relationship and filter by genre names
                query = select(model).join(model.genres).filter(Genre.name.in_(genres))
                logger.debug(f"Initial query built with genre filter: {genres}")

                # Apply media_ids filter if provided
                if media_ids:
                    query = query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                # Apply limit
                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug(f"Executing final query for {media_type.value}.")
                result = await session.execute(query)
                media_items = result.scalars().unique().all()  # Use unique() to avoid duplicates from joins

                if media_items:
                    logger.success(f"Found {len(media_items)} {media_type.value}(s) matching genres.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found matching genres '{genres}'.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(
                    f"SQLAlchemy Error during get_by_genres for {media_type.value} with genres '{genres}': {e}",
                    exc_info=True)
                return []
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during get_by_genres for {media_type.value} with genres '{genres}': {e}",
                    exc_info=True)
                return []

    async def get_by_status(
            self,
            status_id: int,
            media_type: MediaType,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Get media by status and type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            status_id: The ID of the status to filter by.
            media_type: The type of media (Anime or Manga).
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects matching the status,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(f"Attempting to retrieve {media_type.value} by status ID: {status_id}")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                query = select(model).filter(model.status_id == status_id)
                logger.debug(f"Initial query built with status_id: {status_id}")

                if media_ids:
                    query = query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug(f"Executing final query for {media_type.value}.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.success(f"Found {len(media_items)} {media_type.value}(s) with status ID {status_id}.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found with status ID {status_id}.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(
                    f"SQLAlchemy Error during get_by_status for {media_type.value} with status ID {status_id}: {e}",
                    exc_info=True)
                return []
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during get_by_status for {media_type.value} with status ID {status_id}: {e}",
                    exc_info=True)
                return []

    async def get_by_format(
            self,
            format_id: int,
            media_type: MediaType,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Get media by format and type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            format_id: The ID of the format to filter by.
            media_type: The type of media (Anime or Manga).
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects matching the format,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(f"Attempting to retrieve {media_type.value} by format ID: {format_id}")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                query = select(model).filter(model.format_id == format_id)
                logger.debug(f"Initial query built with format_id: {format_id}")

                if media_ids:
                    query = query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug(f"Executing final query for {media_type.value}.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.success(f"Found {len(media_items)} {media_type.value}(s) with format ID {format_id}.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found with format ID {format_id}.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(
                    f"SQLAlchemy Error during get_by_format for {media_type.value} with format ID {format_id}: {e}",
                    exc_info=True)
                return []
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during get_by_format for {media_type.value} with format ID {format_id}: {e}",
                    exc_info=True)
                return []

    async def get_by_season(
            self,
            season_id: int,
            media_type: MediaType,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Get media by season and type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            season_id: The ID of the season to filter by.
            media_type: The type of media (Anime or Manga).
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects matching the season,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(f"Attempting to retrieve {media_type.value} by season ID: {season_id}")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                query = select(model).filter(model.season_id == season_id)
                logger.debug(f"Initial query built with season_id: {season_id}")

                if media_ids:
                    query = query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug(f"Executing final query for {media_type.value}.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.success(f"Found {len(media_items)} {media_type.value}(s) with season ID {season_id}.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found with season ID {season_id}.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(
                    f"SQLAlchemy Error during get_by_season for {media_type.value} with season ID {season_id}: {e}",
                    exc_info=True)
                return []
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during get_by_season for {media_type.value} with season ID {season_id}: {e}",
                    exc_info=True)
                return []

    async def get_by_source_material(
            self,
            source_material_id: int,
            media_type: MediaType,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Get media by source material and type with logging.

        Args:
            self: The instance of the class containing the session_maker.
            source_material_id: The ID of the source material to filter by.
            media_type: The type of media (Anime or Manga).
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects matching the source material,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(f"Attempting to retrieve {media_type.value} by source material ID: {source_material_id}")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                query = select(model).filter(model.source_material_id == source_material_id)
                logger.debug(f"Initial query built with source_material_id: {source_material_id}")

                if media_ids:
                    query = query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug(f"Executing final query for {media_type.value}.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.info(
                        f"Found {len(media_items)} {media_type.value}(s) with source material ID {source_material_id}.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found with source material ID {source_material_id}.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(
                    f"SQLAlchemy Error during get_by_source_material for {media_type.value} with source material ID {source_material_id}: {e}",
                    exc_info=True)
                return []
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during get_by_source_material for {media_type.value} with source material ID {source_material_id}: {e}",
                    exc_info=True)
                return []

    async def get_sorted(
            self,
            media_type: MediaType,
            sort_by: SortBy = SortBy.POPULARITY,
            order: SortOrder = SortOrder.DESC,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Get media sorted by specified criterion and order with logging.

        Args:
            self: The instance of the class containing the session_maker.
            media_type: The type of media (Anime or Manga).
            sort_by: The criterion to sort by (e.g., POPULARITY, START_DATE).
            order: The sort order (ASC or DESC).
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects sorted as specified,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(f"Attempting to retrieve sorted {media_type.value} entries.")
        logger.debug(
            f"Sort parameters: sort_by={sort_by.name}, order={order.name}, limit={limit}, media_ids={media_ids}")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        # Validate sort_by for media type
        if media_type == MediaType.ANIME and sort_by in [SortBy.CHAPTERS, SortBy.VOLUMES]:
            logger.warning(f"Invalid sort_by '{sort_by.name}' for Anime. Returning empty list.")
            return []
        if media_type == MediaType.MANGA and sort_by in [SortBy.EPISODES, SortBy.DURATION]:
            logger.warning(f"Invalid sort_by '{sort_by.name}' for Manga. Returning empty list.")
            return []

        sort_column_map = {
            SortBy.ID: model.id,
            SortBy.ID_MAL: model.idMal,
            SortBy.TITLE_ENGLISH: model.title_english,
            SortBy.TITLE_ROMAJI: model.title_romaji,
            SortBy.TITLE_NATIVE: model.title_native,
            SortBy.START_DATE: model.start_date,
            SortBy.END_DATE: model.end_date,
            SortBy.MEAN_SCORE: model.mean_score,
            SortBy.AVERAGE_SCORE: model.average_score,
            SortBy.POPULARITY: model.popularity,
            SortBy.FAVOURITES: model.favourites,
            SortBy.IS_ADULT: model.isAdult,
            SortBy.EPISODES: getattr(model, 'episodes', None),
            SortBy.DURATION: getattr(model, 'duration', None),
            SortBy.CHAPTERS: getattr(model, 'chapters', None),
            SortBy.VOLUMES: getattr(model, 'volumes', None)
        }

        sort_column = sort_column_map.get(sort_by)

        if sort_column is None:
            logger.error(
                f"Sort column for '{sort_by.name}' not found or not applicable to model {model.__name__}. Returning empty list.")
            return []

        order_expr = sort_column.asc() if order == SortOrder.ASC else sort_column.desc()
        logger.debug(f"Sorting by column '{sort_by.name}' in {order.name} order.")

        async with self.session_maker() as session:
            try:
                query = select(model).order_by(order_expr)
                logger.debug("Initial query built with order_by clause.")

                if media_ids:
                    query = query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug(f"Executing final query for sorted {media_type.value}.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.info(f"Retrieved {len(media_items)} sorted {media_type.value}(s).")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found for the given criteria.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error during get_sorted for {media_type.value} (sort_by={sort_by.name}): {e}",
                             exc_info=True)
                return []
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during get_sorted for {media_type.value} (sort_by={sort_by.name}): {e}",
                    exc_info=True)
                return []


    async def get_paginated(self, media_type: MediaType, page: int = 1, per_page: int = 10) -> Sequence[
        Union[Anime, Manga]]:
        """Get paginated media results"""
        model = Anime if media_type == MediaType.ANIME else Manga
        offset = (page - 1) * per_page
        async with self.session_maker() as session:
            result = await session.execute(
                select(model)
                .offset(offset)
                .limit(per_page)
            )
            return result.scalars().all()

    async def get_by_duration_range(
            self,
            media_type: MediaType,
            min_duration: int,
            max_duration: int,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Anime]:
        """
        Get anime by duration range (minutes) with logging.

        Args:
            self: The instance of the class containing the session_maker.
            media_type: The type of media (must be MediaType.ANIME).
            min_duration: The minimum duration in minutes.
            max_duration: The maximum duration in minutes.
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime objects matching the duration range,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(
            f"Attempting to retrieve {media_type.value} by duration range: {min_duration}-{max_duration} minutes.")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        if media_type != MediaType.ANIME:
            logger.warning(
                f"Invalid media_type '{media_type.name}' for duration range search. Only Anime is supported. Returning empty list.")
            return []

        async with self.session_maker() as session:
            try:
                query = select(Anime).filter(between(Anime.duration, min_duration, max_duration))
                logger.debug(f"Initial query built for Anime duration between {min_duration} and {max_duration}.")

                if media_ids:
                    query = query.filter(Anime.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                # Corrected limit application: limit if limit > 0 else None
                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug("Executing final query for duration range.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.success(f"Found {len(media_items)} Anime(s) within duration range.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.info("No Anime found within the specified duration range.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error during get_by_duration_range: {e}", exc_info=True)
                return []
            except Exception as e:
                logger.error(f"An unexpected error occurred during get_by_duration_range: {e}", exc_info=True)
                return []

    async def get_by_year_range(
            self,
            media_type: MediaType,
            start_year: int,
            end_year: int,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Get media by start year range with logging.

        Args:
            self: The instance of the class containing the session_maker.
            media_type: The type of media (Anime or Manga).
            start_year: The minimum start year.
            end_year: The maximum start year.
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects matching the year range,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(f"Attempting to retrieve {media_type.value} by start year range: {start_year}-{end_year}.")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                query = select(model).filter(
                    and_(
                        model.start_date.isnot(None),
                        func.extract('year', model.start_date).between(start_year, end_year)
                    )
                )
                logger.debug(
                    f"Initial query built for {model.__name__} start year between {start_year} and {end_year}.")

                if media_ids:
                    query = query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                # Corrected limit application: limit if limit > 0 else None
                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug(f"Executing final query for {media_type.value} by year range.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.success(f"Found {len(media_items)} {media_type.value}(s) within year range.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found within the specified year range.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error during get_by_year_range for {media_type.value}: {e}", exc_info=True)
                return []
            except Exception as e:
                logger.error(f"An unexpected error occurred during get_by_year_range for {media_type.value}: {e}",
                             exc_info=True)
                return []

    async def get_by_score_range(
            self,
            media_type: MediaType,
            min_score: int,
            max_score: int,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Get media by average score range with logging.

        Args:
            self: The instance of the class containing the session_maker.
            media_type: The type of media (Anime or Manga).
            min_score: The minimum average/mean score.
            max_score: The maximum average/mean score.
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects matching the score range,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(f"Attempting to retrieve {media_type.value} by score range: {min_score}-{max_score}.")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        async with self.session_maker() as session:
            try:
                query = select(model).filter(
                    or_(
                        model.average_score.between(min_score, max_score),
                        model.mean_score.between(min_score, max_score)
                    )
                )
                logger.debug(f"Initial query built for {model.__name__} score between {min_score} and {max_score}.")

                if media_ids:
                    query = query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                # Corrected limit application: limit if limit > 0 else None
                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug(f"Executing final query for {media_type.value} by score range.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.success(f"Found {len(media_items)} {media_type.value}(s) within score range.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found within the specified score range.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error during get_by_score_range for {media_type.value}: {e}", exc_info=True)
                return []
            except Exception as e:
                logger.error(f"An unexpected error occurred during get_by_score_range for {media_type.value}: {e}",
                             exc_info=True)
                return []

    async def get_by_episode_chapter_range(
            self,
            media_type: MediaType,
            min_count: int,
            max_count: int,
            limit: int = 10,
            media_ids: Optional[List[int]] = None
    ) -> Sequence[Union[Anime, Manga]]:
        """
        Get media by episode (Anime) or chapter (Manga) count range with logging.

        Args:
            self: The instance of the class containing the session_maker.
            media_type: The type of media (Anime or Manga).
            min_count: The minimum episode/chapter count.
            max_count: The maximum episode/chapter count.
            limit: The maximum number of results to return. Defaults to 10.
                   If 0 or less, no limit is applied.
            media_ids: An optional list of media IDs to filter the results by.

        Returns:
            A list of Anime or Manga objects matching the count range,
            optionally filtered by IDs and limited, or an empty list.
        """
        logger.info(
            f"Attempting to retrieve {media_type.value} by episode/chapter count range: {min_count}-{max_count}.")
        logger.debug(f"Search parameters: limit={limit}, media_ids={media_ids}")

        model = Anime if media_type == MediaType.ANIME else Manga
        logger.debug(f"Using model: {model.__name__} for media type: {media_type.value}")

        # Determine the correct column based on media_type
        if media_type == MediaType.ANIME:
            count_column = Anime.episodes
            logger.debug("Filtering by Anime.episodes.")
        elif media_type == MediaType.MANGA:
            count_column = Manga.chapters
            logger.debug("Filtering by Manga.chapters.")
        else:
            logger.warning(
                f"Unsupported media_type '{media_type.name}' for episode/chapter range. Returning empty list.")
            return []

        async with self.session_maker() as session:
            try:
                query = (
                    select(model)
                    .filter(count_column.between(min_count, max_count))
                )
                logger.debug(f"Initial query built for {model.__name__} count between {min_count} and {max_count}.")

                if media_ids:
                    query = query.filter(model.id.in_(media_ids))
                    logger.debug(f"Applied media_ids filter: {media_ids}")

                # Corrected limit application: limit if limit > 0 else None
                if limit > 0:
                    query = query.limit(limit)
                    logger.debug(f"Applied limit: {limit}")
                else:
                    logger.debug("No limit applied (limit <= 0).")

                logger.debug(f"Executing final query for {media_type.value} by episode/chapter range.")
                result = await session.execute(query)
                media_items = result.scalars().all()

                if media_items:
                    logger.success(f"Found {len(media_items)} {media_type.value}(s) within episode/chapter count range.")
                    for item in media_items:
                        logger.debug(f"  - Found: {item}")
                else:
                    logger.warning(f"No {media_type.value}(s) found within the specified episode/chapter count range.")
                return media_items
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy Error during get_by_episode_chapter_range for {media_type.value}: {e}",
                             exc_info=True)
                return []
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during get_by_episode_chapter_range for {media_type.value}: {e}",
                    exc_info=True)
                return []