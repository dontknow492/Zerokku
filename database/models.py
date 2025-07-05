import os
from datetime import datetime, timezone
from typing import List, Optional

from loguru import logger
from sqlalchemy import Engine, event, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.schema import Table, ForeignKey, Column, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.types import String, Boolean, Integer, Text, DateTime, Date, JSON


class Base(AsyncAttrs, DeclarativeBase):
    pass


# Association Tables
anime_tag_association = Table(
    "anime_tag_association",
    Base.metadata,
    Column("anime_id", ForeignKey("anime.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

manga_tag_association = Table(
    "manga_tag_association",
    Base.metadata,
    Column("manga_id", ForeignKey("manga.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

anime_genre_association = Table(
    "anime_genre_association",
    Base.metadata,
    Column("anime_id", ForeignKey("anime.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True)
)

manga_genre_association = Table(
    "manga_genre_association",
    Base.metadata,
    Column("manga_id", ForeignKey("manga.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True)
)

anime_studio_association = Table(
    "anime_studio_association",
    Base.metadata,
    Column("anime_id", ForeignKey("anime.id"), primary_key=True),
    Column("studio_id", ForeignKey("studios.id"), primary_key=True)
)

manga_studio_association = Table(
    "manga_studio_association",
    Base.metadata,
    Column("manga_id", ForeignKey("manga.id"), primary_key=True),
    Column("studio_id", ForeignKey("studios.id"), primary_key=True)
)

anime_character_association = Table(
    "anime_character_association",
    Base.metadata,
    Column("anime_id", ForeignKey("anime.id"), primary_key=True),
    Column("character_id", ForeignKey("characters.id"), primary_key=True)
)

manga_character_association = Table(
    "manga_character_association",
    Base.metadata,
    Column("manga_id", ForeignKey("manga.id"), primary_key=True),
    Column("character_id", ForeignKey("characters.id"), primary_key=True)
)


class User(Base):
    """Represents a registered user in the system."""
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    categories: Mapped[List["UserCategory"]] = relationship("UserCategory", back_populates="user")
    profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user")
    library_entries: Mapped[List["UserLibrary"]] = relationship("UserLibrary", back_populates="user")


class UserProfile(Base):
    """Represents a registered user profile in the system."""
    __tablename__ = 'user_profiles'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user: Mapped['User'] = relationship("User", back_populates="profile")


class Status(Base):
    """Represents a Status of anime or manga in the system."""
    __tablename__ = 'status'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)

    animes: Mapped[List["Anime"]] = relationship("Anime", back_populates="status", cascade="all, delete-orphan")
    mangas: Mapped[List["Manga"]] = relationship("Manga", back_populates="status", cascade="all, delete-orphan")


class Season(Base):
    """Represents a Season of anime in the system."""
    __tablename__ = 'seasons'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)

    animes: Mapped[List["Anime"]] = relationship("Anime", back_populates="season", cascade="all, delete-orphan")
    mangas: Mapped[List["Manga"]] = relationship("Manga", back_populates="season", cascade="all, delete-orphan")


class Format(Base):
    """Represents a Format of anime/manga in the system."""
    __tablename__ = 'formats'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)

    animes: Mapped[List["Anime"]] = relationship("Anime", back_populates="format", cascade="all, delete-orphan")
    mangas: Mapped[List["Manga"]] = relationship("Manga", back_populates="format", cascade="all, delete-orphan")


class CountryOfOrigin(Base):
    """Represents a Country of Origin of anime/manga in the system."""
    __tablename__ = 'country_of_origins'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)

    animes: Mapped[List["Anime"]] = relationship("Anime", back_populates="country_of_origins",
                                                 cascade="all, delete-orphan")
    mangas: Mapped[List["Manga"]] = relationship("Manga", back_populates="country_of_origins",
                                                 cascade="all, delete-orphan")


class SourceMaterial(Base):
    """Represents a Source Material of anime/manga in the system."""
    __tablename__ = 'source_materials'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)

    animes: Mapped[List["Anime"]] = relationship("Anime", back_populates="source_material",
                                                 cascade="all, delete-orphan")
    mangas: Mapped[List["Manga"]] = relationship("Manga", back_populates="source_material",
                                                 cascade="all, delete-orphan")


class Genre(Base):
    """Represents a Genre of anime/manga in the system."""
    __tablename__ = 'genres'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)

    animes: Mapped[List["Anime"]] = relationship(
        "Anime",
        secondary=anime_genre_association,
        back_populates="genres"
    )
    mangas: Mapped[List["Manga"]] = relationship(
        "Manga",
        secondary=manga_genre_association,
        back_populates="genres"
    )


class Tag(Base):
    """Represents a Tag of anime/manga in the system."""
    __tablename__ = 'tags'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    isAdult: Mapped[bool] = mapped_column(Boolean)

    animes: Mapped[List["Anime"]] = relationship(
        "Anime",
        secondary=anime_tag_association,
        back_populates="tags"
    )
    mangas: Mapped[List["Manga"]] = relationship(
        "Manga",
        secondary=manga_tag_association,
        back_populates="tags"
    )


class Studio(Base):
    """Represents a Studio of anime/manga in the system."""
    __tablename__ = 'studios'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)

    animes: Mapped[List["Anime"]] = relationship(
        "Anime",
        secondary=anime_studio_association,
        back_populates="studios"
    )
    mangas: Mapped[List["Manga"]] = relationship(
        "Manga",
        secondary=manga_studio_association,
        back_populates="studios"
    )


class RelationType(Base):
    """Represents a Relation between anime/manga in the system."""
    __tablename__ = 'relation_types'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)


class Trailer(Base):
    """Represents a Trailer of anime/manga in the system."""
    __tablename__ = 'trailers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    anime_id: Mapped[Optional[int]] = mapped_column(ForeignKey('anime.id'), nullable=True, index=True)
    manga_id: Mapped[Optional[int]] = mapped_column(ForeignKey('manga.id'), nullable=True, index=True)
    site: Mapped[str] = mapped_column(String)  # e.g., "YouTube"
    video_id: Mapped[str] = mapped_column(String)  # e.g., YouTube video ID
    thumbnail: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    anime: Mapped[Optional['Anime']] = relationship("Anime", back_populates="trailers")
    manga: Mapped[Optional['Manga']] = relationship("Manga", back_populates="trailers")

    __table_args__ = (
        CheckConstraint('anime_id IS NOT NULL OR manga_id IS NOT NULL', name='check_media_id'),
    )


class Character(Base):
    """Represents a Character of anime/manga in the system."""
    __tablename__ = 'characters'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_native: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dob: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    media_character_links: Mapped[List["MediaCharacter"]] = relationship("MediaCharacter", back_populates="character")

    animes: Mapped[List["Anime"]] = relationship(
        "Anime",
        secondary="media_characters",
        primaryjoin="and_(Character.id == MediaCharacter.character_id, MediaCharacter.anime_id != None)",
        secondaryjoin="Anime.id == MediaCharacter.anime_id",
        viewonly=True,
    )
    mangas: Mapped[List["Manga"]] = relationship(
        "Manga",
        secondary="media_characters",
        primaryjoin="and_(Character.id == MediaCharacter.character_id, MediaCharacter.manga_id != None)",
        secondaryjoin="Manga.id == MediaCharacter.manga_id",
        viewonly=True,
    )


class MediaCharacter(Base):
    __tablename__ = "media_characters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    anime_id: Mapped[Optional[int]] = mapped_column(ForeignKey("anime.id"), nullable=True)
    manga_id: Mapped[Optional[int]] = mapped_column(ForeignKey("manga.id"), nullable=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), nullable=False)

    role: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    character: Mapped["Character"] = relationship("Character", back_populates="media_character_links")
    anime: Mapped[Optional["Anime"]] = relationship("Anime", back_populates="media_character_links")
    manga: Mapped[Optional["Manga"]] = relationship("Manga", back_populates="media_character_links")

    __table_args__ = (
        CheckConstraint(
            "(anime_id IS NOT NULL AND manga_id IS NULL) OR (anime_id IS NULL AND manga_id IS NOT NULL)",
            name="chk_one_media_id_not_null"
        ),
    )


class MediaRelation(Base):
    """Represents a MediaRelation between anime/manga in the system."""
    __tablename__ = 'media_relations'
    id: Mapped[int] = mapped_column(primary_key=True)
    from_anime_id: Mapped[Optional[int]] = mapped_column(ForeignKey('anime.id'), nullable=True)
    to_anime_id: Mapped[Optional[int]] = mapped_column(ForeignKey('anime.id'), nullable=True)
    from_manga_id: Mapped[Optional[int]] = mapped_column(ForeignKey('manga.id'), nullable=True)
    to_manga_id: Mapped[Optional[int]] = mapped_column(ForeignKey('manga.id'), nullable=True)
    relation_type_id: Mapped[int] = mapped_column(ForeignKey('relation_types.id'))

    from_anime: Mapped[Optional['Anime']] = relationship("Anime", foreign_keys=[from_anime_id],
                                                        back_populates="outgoing_relations")
    to_anime: Mapped[Optional['Anime']] = relationship("Anime", foreign_keys=[to_anime_id],
                                                    back_populates="incoming_relations")
    from_manga: Mapped[Optional['Manga']] = relationship("Manga", foreign_keys=[from_manga_id],
                                                        back_populates="outgoing_relations")
    to_manga: Mapped[Optional['Manga']] = relationship("Manga", foreign_keys=[to_manga_id],
                                                    back_populates="incoming_relations")
    relation_type: Mapped['RelationType'] = relationship("RelationType")

    __table_args__ = (
        CheckConstraint(
            'from_anime_id IS NOT NULL OR to_anime_id IS NOT NULL OR '
            'from_manga_id IS NOT NULL OR to_manga_id IS NOT NULL',
            name='check_media_id'
        ),
    )


class UserCategory(Base):
    """Represents a UserCategory created by user in the system."""
    __tablename__ = 'user_categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    user: Mapped["User"] = relationship("User", back_populates="categories")


class UserLibrary(Base):
    """Represents a Anime/Manga user saved/store."""
    __tablename__ = "user_libraries"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey("anime.id"), nullable=True, index=True)
    manga_id: Mapped[int] = mapped_column(ForeignKey("manga.id"), nullable=True, index=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="library_entries")
    anime: Mapped["Anime"] = relationship("Anime")
    manga: Mapped["Manga"] = relationship("Manga")
    status: Mapped["Status"] = relationship("Status")

    __table_args__ = (
        CheckConstraint('anime_id IS NOT NULL OR manga_id IS NOT NULL', name='check_media_id'),
    )


class WatchHistory(Base):
    """Represents a WatchHistory of user."""
    __tablename__ = 'watch_history'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), index=True)
    anime_id: Mapped[Optional[int]] = mapped_column(ForeignKey('anime.id'), nullable=True, index=True)
    manga_id: Mapped[Optional[int]] = mapped_column(ForeignKey('manga.id'), nullable=True, index=True)
    current_episode: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_chapter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    watched_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User")
    anime: Mapped[Optional["Anime"]] = relationship("Anime")
    manga: Mapped[Optional["Manga"]] = relationship("Manga")

    __table_args__ = (
        CheckConstraint('anime_id IS NOT NULL OR manga_id IS NOT NULL', name='check_media_id'),
    )


class Bookmark(Base):
    """Store Bookmark of episode/chapter of user."""
    __tablename__ = 'bookmarks'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    episode_id: Mapped[Optional[int]] = mapped_column(ForeignKey('episodes.id'), nullable=True, index=True)
    chapter_id: Mapped[Optional[int]] = mapped_column(ForeignKey('chapters.id'), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped['User'] = relationship("User")
    episode: Mapped[Optional['Episode']] = relationship("Episode")
    chapter: Mapped[Optional['Chapter']] = relationship("Chapter")

    __table_args__ = (
        CheckConstraint('episode_id IS NOT NULL OR chapter_id IS NOT NULL', name='check_episode_chapter_id'),
    )


class Episode(Base):
    """Represents Episodes of anime."""
    __tablename__ = 'episodes'
    id: Mapped[int] = mapped_column(primary_key=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id'), index=True)
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    air_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    anime: Mapped["Anime"] = relationship("Anime", back_populates="episodes_list")


class Chapter(Base):
    """Represents Chapters of manga."""
    __tablename__ = 'chapters'
    id: Mapped[int] = mapped_column(primary_key=True)
    manga_id: Mapped[int] = mapped_column(ForeignKey('manga.id'), index=True)
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    manga: Mapped['Manga'] = relationship("Manga", back_populates="chapters_list")




class MediaBase:
    id: Mapped[int] = mapped_column(primary_key=True)
    idMal: Mapped[int] = mapped_column(Integer, unique=True, nullable=True)
    site_url: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    
    title_english: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    title_romaji: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    title_native: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    #image
    cover_image_extra_large: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cover_image_large: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cover_image_medium: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cover_image_color: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    banner_image: Mapped[Optional[str]] = mapped_column(String, nullable=True)


    # date
    start_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    
    #score
    mean_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    popularity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    favourites: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    
    isAdult: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    synonyms: Mapped[Optional[List[str]]] = mapped_column(JSON, default=[])

    # Foreign keys
    status_id: Mapped[Optional[int]] = mapped_column(ForeignKey("status.id"), nullable=True, index=True)
    season_id: Mapped[Optional[int]] = mapped_column(ForeignKey("seasons.id"), nullable=True, index=True)
    format_id: Mapped[Optional[int]] = mapped_column(ForeignKey("formats.id"), nullable=True, index=True)
    country_of_origin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("country_of_origins.id"), nullable=True,
                                                                index=True)
    source_material_id: Mapped[Optional[int]] = mapped_column(ForeignKey("source_materials.id"), nullable=True,
                                                              index=True)

class Anime(MediaBase, Base):
    __tablename__ = "anime"
    
    
    episodes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    status: Mapped[Optional["Status"]] = relationship("Status", back_populates="animes")
    season: Mapped[Optional["Season"]] = relationship("Season", back_populates="animes")
    format: Mapped[Optional["Format"]] = relationship("Format", back_populates="animes")
    country_of_origins: Mapped[Optional["CountryOfOrigin"]] = relationship("CountryOfOrigin", back_populates="animes")
    source_material: Mapped[Optional["SourceMaterial"]] = relationship("SourceMaterial", back_populates="animes")

    genres: Mapped[List["Genre"]] = relationship(
        "Genre",
        secondary=anime_genre_association,
        back_populates="animes"
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=anime_tag_association,
        back_populates="animes"
    )
    studios: Mapped[List["Studio"]] = relationship(
        "Studio",
        secondary=anime_studio_association,
        back_populates="animes"
    )

    media_character_links: Mapped[List["MediaCharacter"]] = relationship(back_populates="anime")
    trailers: Mapped[List["Trailer"]] = relationship("Trailer", back_populates="anime")

    episodes_list: Mapped[List["Episode"]] = relationship("Episode", back_populates="anime")

    outgoing_relations: Mapped[List["MediaRelation"]] = relationship(
        "MediaRelation", foreign_keys="[MediaRelation.from_anime_id]", back_populates="from_anime"
    )
    incoming_relations: Mapped[List["MediaRelation"]] = relationship(
        "MediaRelation", foreign_keys="[MediaRelation.to_anime_id]", back_populates="to_anime"
    )

    __table_args__ = (
        UniqueConstraint("title_english", name="uq_anime_title_english"),
        UniqueConstraint("title_romaji", name="uq_anime_title_romaji"),
        Index("ix_anime_popularity", "popularity"),
        Index("ix_anime_average_score", "average_score"),
    )


class Manga(MediaBase, Base):
    __tablename__ = "manga"
    
    chapters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    volumes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    status: Mapped[Optional["Status"]] = relationship("Status", back_populates="mangas")
    season: Mapped[Optional["Season"]] = relationship("Season", back_populates="mangas")
    format: Mapped[Optional["Format"]] = relationship("Format", back_populates="mangas")
    country_of_origins: Mapped[Optional["CountryOfOrigin"]] = relationship("CountryOfOrigin", back_populates="mangas")
    source_material: Mapped[Optional["SourceMaterial"]] = relationship("SourceMaterial", back_populates="mangas")

    genres: Mapped[List["Genre"]] = relationship(
        "Genre",
        secondary=manga_genre_association,
        back_populates="mangas"
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=manga_tag_association,
        back_populates="mangas"
    )
    studios: Mapped[List["Studio"]] = relationship(  # maybe "publishers" would be better for manga?
        "Studio",
        secondary=manga_studio_association,
        back_populates="mangas"
    )

    media_character_links: Mapped[List["MediaCharacter"]] = relationship(back_populates="manga")
    trailers: Mapped[List["Trailer"]] = relationship("Trailer", back_populates="manga")

    chapters_list: Mapped[List["Chapter"]] = relationship("Chapter", back_populates="manga")

    outgoing_relations: Mapped[List["MediaRelation"]] = relationship(
        "MediaRelation", foreign_keys="[MediaRelation.from_manga_id]", back_populates="from_manga"
    )
    incoming_relations: Mapped[List["MediaRelation"]] = relationship(
        "MediaRelation", foreign_keys="[MediaRelation.to_manga_id]", back_populates="to_manga"
    )

    __table_args__ = (
        UniqueConstraint("title_english", name="uq_manga_title_english"),
        UniqueConstraint("title_romaji", name="uq_manga_title_romaji"),
        Index("ix_manga_popularity", "popularity"),
        Index("ix_manga_average_score", "average_score"),
    )


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def sync_init_db(engine: Engine) -> None:
    """
    Initialize the database by creating all tables defined in Base.metadata.

    Args:
        engine: SQLAlchemy Engine instance for database connection.

    Raises:
        SQLAlchemyError: If database initialization fails.
    """
    try:
        # Enable foreign key support for SQLite
        if engine.dialect.name == "sqlite":
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        with engine.begin() as conn:
            logger.info("Creating database tables...")
            Base.metadata.create_all(conn)
            logger.info("Database tables created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    # Load database URL from environment variable or default to SQLite
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///mydatabase.db")

    try:
        # Create synchronous engine
        engine = create_engine(DATABASE_URL, echo=False)
        sync_init_db(engine)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise