from enum import Enum
from typing import Sequence, Union, Optional, List

# from cachetools.func import lru_cache, lfu_cache
from functools import lru_cache

from cachetools import LFUCache
from loguru import logger
from sqlalchemy import select, and_, or_, func, between
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

    ### Create
    async def create(self, media: Union[Anime, Manga]) -> Union[Anime, Manga]:
        """Create a new media entry"""
        async with self.session_maker() as session:
            async with session.begin():  # Use async context manager for transaction
                # Create a list to hold the genres to be associated
                associated_genres = []
                associated_tags = []
                associated_studios = []

                # Check for existing genres and associate them
                for genre in media.genres:
                    existing_genre = await self.get_genre(genre.id)  # Use LRU cache
                    if existing_genre:
                        associated_genres.append(existing_genre)  # Associate existing genre
                    else:
                        # Create a new genre if it does not exist
                        new_genre = Genre(id=genre.id, name=genre.name)  # Ensure this ID is unique
                        session.add(new_genre)  # Add the new genre to the session
                        associated_genres.append(new_genre)  # Associate the new genre

                    # Check for existing tags and associate them
                for tag in media.tags:
                    existing_tag = await self.get_tag(tag.id)  # Use LRU cache
                    if existing_tag:
                        associated_tags.append(existing_tag)  # Associate existing tag
                    else:
                        # Create a new tag if it does not exist
                        new_tag = Tag(id=tag.id, name=tag.name)  # Ensure this ID is unique
                        session.add(new_tag)  # Add the new tag to the session
                        associated_tags.append(new_tag)  # Associate the new tag

                    # Check for existing studios and associate them
                for studio in media.studios:
                    existing_studio = await self.get_studio(studio.id)  # Use LRU cache
                    if existing_studio:
                        associated_studios.append(existing_studio)  # Associate existing studio
                    else:
                        # Create a new studio if it does not exist
                        new_studio = Studio(id=studio.id, name=studio.name)  # Ensure this ID is unique
                        session.add(new_studio)  # Add the new studio to the session
                        associated_studios.append(new_studio)  # Associate the new studio

                media.genres = associated_genres  # Update media's genres with the associated genres
                session.add(media)  # Add the media instance to the session
                await session.flush()  # Commit the transaction
                await session.refresh(media)  # Refresh the instance to get the latest data
            return media

    async def create_update_media(self, media: Union[Anime, Manga]) -> Union[Anime, Manga]:
        """Create or update a media entry"""
        async with self.session_maker() as session:
            # Check if media already exists
            existing_media = await session.execute(
                select(type(media)).filter_by(id=media.id)
            )
            existing_media = existing_media.scalar()

            if existing_media:
                # Update existing media
                for attr, value in media.__dict__.items():
                    if attr != "id" and value is not None:
                        setattr(existing_media, attr, value)
                session.add(existing_media)
                await session.flush()
                await session.refresh(media)
            else:
                # Create new media
                await self.create(media)


        return media



    ### Get
    async def get_by_id(self, media_id: int, media_type: MediaType) -> Optional[Union[Anime, Manga]]:
        """Get media by ID and type"""
        model = Anime if media_type == MediaType.ANIME else Manga
        async with self.session_maker() as session:
            result = await session.execute(select(model).filter(model.id == media_id))
            return result.scalars().first()

    async def get_by_title(self, title: str, media_type: MediaType) -> Sequence[Union[Anime, Manga]]:
        """Get media by title and type"""
        model = Anime if media_type == MediaType.ANIME else Manga
        async with self.session_maker() as session:
            result = await session.execute(select(model).filter(model.title_english.ilike(f"%{title}%")))
            return result.scalars().all()

    async def get_by_multiple_titles(self, titles: Sequence[str], media_type: MediaType) -> Sequence[Union[Anime, Manga]]:
        """Get media by multiple titles and type"""
        model = Anime if media_type == MediaType.ANIME else Manga
        async with self.session_maker() as session:
            result = await session.execute(select(model).filter(or_(*[model.title_english.ilike(f"%{title}%") for title in titles])))
            return result.scalars().all()

    async def search(self, query: str, media_type: MediaType, limit: int = 10) -> Sequence[Union[Anime, Manga]]:
        """Search media by query and type"""
        model = Anime if media_type == MediaType.ANIME else Manga
        async with self.session_maker() as session:
            result = await session.execute(
                select(model)
                .filter(
                    or_(
                        model.title_english.ilike(f"%{query}%"),
                        model.title_japanese.ilike(f"%{query}%"),
                    )
                )
                .limit(limit)
            )
            return result.scalars().all()

    ### Update
    async def update(self, media_id: int, update_data: Union[Anime, Manga], media_type: MediaType) -> Optional[
        Union[Anime, Manga]]:
        media = await self.get_by_id(media_id, media_type)
        if not media:
            return None
        for key, value in update_data.__dict__.items():
            if key != "id":  # ignore the id attribute
                setattr(media, key, value)
        async with self.session_maker() as session:
            await session.commit()
            return media

    ### Delete
    async def delete(self, media_id: int, media_type: MediaType) -> bool:
        """Delete media by ID and type"""
        media = await self.get_by_id(media_id, media_type)
        if not media:
            return False
        async with self.session_maker() as session:
            await session.delete(media)
            await session.commit()
            return True

    ### Additional Methods
    async def get_all(self, media_type: MediaType) -> Sequence[Union[Anime, Manga]]:
        """Get all media of a specific type"""
        model = Anime if media_type == MediaType.ANIME else Manga
        async with self.session_maker() as session:
            result = await session.execute(select(model))
            return result.scalars().all()

    async def count(self, media_type: MediaType) -> int:
        """Count media of a specific type"""
        model = Anime if media_type == MediaType.ANIME else Manga
        async with self.session_maker() as session:
            result = await session.execute(select(func.count(model.id)).select_from(model))
            return result.scalars().first()

    async def get_by_genres(self, genres: List[str], media_type: MediaType, limit: int = 10) -> Sequence[
        Union[Anime, Manga]]:
        """Get media by genres and type"""
        model = Anime if media_type == MediaType.ANIME else Manga
        async with self.session_maker() as session:
            result = await session.execute(
                select(model)
                .join(model.genres)
                .filter(model.genres.any(Genre.name.in_(genres)))
                .limit(limit)
            )
            return result.scalars().all()

    async def get_by_status(self, status_id: int, media_type: MediaType, limit: int = 10) -> Sequence[
        Union[Anime, Manga]]:
        """Get media by status and type"""
        model = Anime if media_type == MediaType.ANIME else Manga
        async with self.session_maker() as session:
            result = await session.execute(
                select(model)
                .filter(model.status_id == status_id)
                .limit(limit)
            )
            return result.scalars().all()

    async def get_sorted(self, media_type: MediaType, sort_by: SortBy = SortBy.POPULARITY,
                         order: SortOrder = SortOrder.DESC, limit: int = 10) -> Sequence[Union[Anime, Manga]]:
        """Get media sorted by specified criterion and order"""
        model = Anime if media_type == MediaType.ANIME else Manga

        # Validate sort_by for media type
        if media_type == MediaType.ANIME and sort_by in [SortBy.CHAPTERS, SortBy.VOLUMES]:
            return []
        if media_type == MediaType.MANGA and sort_by in [SortBy.EPISODES, SortBy.DURATION]:
            return []

        sort_column = {
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
        }[sort_by]

        if sort_column is None:
            return []

        order_expr = sort_column.asc() if order == SortOrder.ASC else sort_column.desc()
        async with self.session_maker() as session:
            result = await session.execute(
                select(model)
                .order_by(order_expr)
                .limit(limit)
            )
            return result.scalars().all()


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

    async def get_by_duration_range(self, media_type: MediaType, min_duration: int, max_duration: int,
                                    limit: int = 10) -> Sequence[Anime]:
        """Get anime by duration range (minutes)"""
        if media_type != MediaType.ANIME:
            return []
        async with self.session_maker() as session:
            result = await session.execute(
                select(Anime)
                .filter(between(Anime.duration, min_duration, max_duration))
                .limit(limit)
            )
            return result.scalars().all()

    async def get_by_year_range(self, media_type: MediaType, start_year: int, end_year: int, limit: int = 10) -> \
    Sequence[Union[Anime, Manga]]:
        """Get media by start year range"""
        model = Anime if media_type == MediaType.ANIME else Manga
        async with self.session_maker() as session:
            result = await session.execute(
                select(model)
                .filter(
                    and_(
                        model.start_date.isnot(None),
                        func.extract('year', model.start_date).between(start_year, end_year)
                    )
                )
                .limit(limit)
            )
            return result.scalars().all()

    async def get_by_score_range(self, media_type: MediaType, min_score: int, max_score: int, limit: int = 10) -> \
    Sequence[Union[Anime, Manga]]:
        """Get media by average score range"""
        model = Anime if media_type == MediaType.ANIME else Manga
        async with self.session_maker() as session:
            result = await session.execute(
                select(model)
                .filter(between(model.average_score, min_score, max_score))
                .limit(limit)
            )
            return result.scalars().all()

    async def get_by_episode_chapter_range(self, media_type: MediaType, min_count: int, max_count: int,
                                           limit: int = 10) -> Sequence[Union[Anime, Manga]]:
        """Get media by episode (Anime) or chapter (Manga) count range"""
        model = Anime if media_type == MediaType.ANIME else Manga
        count_column = Anime.episodes if media_type == MediaType.ANIME else Manga.chapters
        async with self.session_maker() as session:
            result = await session.execute(
                select(model)
                .filter(between(count_column, min_count, max_count))
                .limit(limit)
            )
            return result.scalars().all()

if __name__ == '__main__':
    session_maker = sessionmaker()