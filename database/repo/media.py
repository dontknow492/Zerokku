from enum import Enum
from typing import Sequence, Union, Optional, List

# from cachetools.func import lru_cache, lfu_cache
from functools import lru_cache

from cachetools import LFUCache
from loguru import logger
from sqlalchemy import select, and_, or_, func, between, not_, asc, desc
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError, DatabaseError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload

from database import get_enum_index
from database.models import Anime, Manga, Genre, Tag, Studio

from AnillistPython import MediaType, MediaStatus, MediaFormat, MediaSource, MediaSeason


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
    ASC = "ascending"
    DESC = "descending"

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

    async def get_by_advanced_filters(
            self,
            media_type: MediaType,
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
            media_ids: Optional[List[int]] = None,
            sort_by: Optional[SortBy] = SortBy.POPULARITY,
            order: SortOrder = SortOrder.DESC,
            limit: int = 10,
            offset: int = 0
    ) -> Union[List[Anime], List[Manga]]:
        logger.info(f"Applying advanced filters for {media_type.value}")
        logger.debug(f"Active filters: query={query}, score={min_score}-{max_score}, count={min_count}-{max_count}, "
                     f"duration={min_duration}-{max_duration}, year={start_year}-{end_year}, genres={genres}, "
                     f"status={status}, format={format}, season={season}, source={source_material}, "
                     f"sort_by={sort_by}, order={order}, limit={limit}, offset={offset}")
        model = Anime if media_type == MediaType.ANIME else Manga
        filters = []

        # Input validation
        if limit <= 0:
            logger.warning("Invalid limit value, defaulting to None")
            limit = None
        if offset <= 0:
            logger.warning("Invalid offset value, defaulting to 0")
            offset = 0
        if min_score is not None and max_score is not None and min_score > max_score:
            logger.warning("min_score cannot be greater than max_score, swapping values")
            min_score, max_score = max_score, min_score

        # Query filter
        if query:
            filters.append(
                or_(
                    model.title_english.ilike(f"%{query}%"),
                    model.title_romaji.ilike(f"%{query}%"),
                    model.title_native.ilike(f"%{query}%"),
                    model.description.ilike(f"%{query}%"),
                    model.synonyms.ilike(f"%{query}%")  # if synonyms is a searchable text field
                )
            )

        # Score filter
        if min_score is not None or max_score is not None:
            score_conditions = []
            if min_score is not None:
                score_conditions.append(or_(
                    model.average_score >= min_score,
                    model.mean_score >= min_score,
                    model.average_score.is_(None)
                ))
            if max_score is not None:
                score_conditions.append(or_(
                    model.average_score <= max_score,
                    model.mean_score <= max_score,
                    model.average_score.is_(None)
                ))
            filters.append(and_(*score_conditions))

        # Episode or chapter count
        # count_column_map = {MediaType.ANIME: , MediaType.MANGA: model.chapters}
        count_column = model.episodes if media_type == MediaType.ANIME else model.chapters
        if min_count is not None or max_count is not None:
            if min_count is not None and max_count is not None:
                filters.append(count_column.between(min_count, max_count))
            elif min_count is not None:
                filters.append(count_column >= min_count)
            elif max_count is not None:
                filters.append(count_column <= max_count)

        # Duration (Anime only)
        if media_type == MediaType.ANIME and (min_duration is not None or max_duration is not None):
            if min_duration is not None and max_duration is not None:
                filters.append(Anime.duration.between(min_duration, max_duration))
            elif min_duration is not None:
                filters.append(Anime.duration >= min_duration)
            elif max_duration is not None:
                filters.append(Anime.duration <= max_duration)

        # Start year
        if start_year is not None or end_year is not None:
            if start_year is not None and end_year is not None:
                filters.append(
                    and_(
                        model.start_date.isnot(None),
                        func.extract('year', model.start_date).between(start_year, end_year)
                    )
                )
            elif start_year is not None:
                filters.append(
                    and_(
                        model.start_date.isnot(None),
                        func.extract('year', model.start_date) >= start_year
                    )
                )
            elif end_year is not None:
                filters.append(
                    and_(
                        model.start_date.isnot(None),
                        func.extract('year', model.start_date) <= end_year
                    )
                )

        # Genre filter
        query = select(model)
        if genres:
            genre_conditions = [Genre.name.ilike(f"%{genre}%") for genre in genres]
            filters.append(or_(*genre_conditions))
            query = query.join(model.genres)

        # Media ID filter
        if media_ids:
            filters.append(model.id.in_(media_ids))

        # Enum-based filters
        def apply_enum_filter(enum_class, enum_value, column):
            enum_id = get_enum_index(enum_class, enum_value)
            if enum_id is not None:
                filters.append(column.in_([enum_id, None]))
            else:
                logger.warning(f"Skipping {enum_class.__name__} filter due to invalid value")

        if status:
            apply_enum_filter(MediaStatus, status, model.status_id)
        if format:
            apply_enum_filter(MediaFormat, format, model.format_id)
        if source_material:
            apply_enum_filter(MediaSource, source_material, model.source_material_id)
        if season:
            apply_enum_filter(MediaSeason, season, model.season_id)

        if filters:
            query = query.filter(and_(*filters))

        # Sorting
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
            SortBy.EPISODES: model.episodes if media_type == MediaType.ANIME else None,
            SortBy.DURATION: model.duration if media_type == MediaType.ANIME else None,
            SortBy.CHAPTERS: model.chapters if media_type == MediaType.MANGA else None,
            SortBy.VOLUMES: model.volumes if media_type == MediaType.MANGA else None,
        }
        sort_column = sort_column_map.get(sort_by)
        if sort_column is None:
            logger.warning(f"Invalid sort column {sort_by} for {media_type.value}, defaulting to popularity")
            sort_column = model.popularity
        query = query.order_by(asc(sort_column) if order == SortOrder.ASC else desc(sort_column))

        # Limit and offset
        query = query.limit(limit).offset(offset)

        async with self.session_maker() as session:
            try:
                # count_query = select(func.count()).select_from(query.subquery())
                # count_result = await session.execute(count_query)
                # total_count = count_result.scalar()
                query = query.options(selectinload(model.genres))

                result = await session.execute(query)
                media_items = result.scalars().unique().all()
                logger.success(
                    f"Retrieved {len(media_items)} - {media_type.value}(s) with advanced filters.")
                return media_items
            except ProgrammingError as e:
                logger.error(f"Invalid query error: {e}", exc_info=True)
                return []

            except DatabaseError as e:
                logger.error(f"Database connection error: {e}", exc_info=True)
                raise

            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                return []

