from typing import List, Optional

from sqlalchemy import String, Boolean, ForeignKey, Integer, Float, Text, JSON, DateTime, Column, Table
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

class Base(AsyncAttrs, DeclarativeBase):
    pass

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

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=False)
    password_hash: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name})>"

class Status(Base):
    __tablename__ = 'status'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=False)

    #relationship
    animes: Mapped[List["Anime"]] = relationship("Anime", back_populates="status", cascade="all, delete-orphan")
    mangas: Mapped[List["Manga"]] = relationship("Manga", back_populates="status", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Status(id={self.id}, name={self.name})>"

class Season(Base):
    __tablename__ = 'seasons'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=False)

    #relationship
    animes: Mapped[List["Anime"]] = relationship("Anime", back_populates="season", cascade="all, delete-orphan")
    mangas: Mapped[List["Manga"]] = relationship("Manga", back_populates="season", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Season(id={self.id}, name={self.name})>"

class Format(Base):
    __tablename__ = 'formats'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=False)

    # relationship
    animes: Mapped[List["Anime"]] = relationship("Anime", back_populates="formats", cascade="all, delete-orphan")
    mangas: Mapped[List["Manga"]] = relationship("Manga", back_populates="formats", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Format(id={self.id}, name={self.name})>"

class CountryOfOrigin(Base):
    __tablename__ = 'country_of_origins'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=False)

    # relationship
    animes: Mapped[List["Anime"]] = relationship("Anime", back_populates="country_of_origins", cascade="all, delete-orphan")
    mangas: Mapped[List["Manga"]] = relationship("Manga", back_populates="country_of_origins", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CountryOfOrigin(id={self.id}, name={self.name})>"

class SourceMaterial(Base):
    __tablename__ = 'source_materials'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=False)

    # relationship
    animes: Mapped[List["Anime"]] = relationship("Anime", back_populates="source_materials", cascade="all, delete-orphan")
    mangas: Mapped[List["Manga"]] = relationship("Manga", back_populates="source_materials", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SourceMaterial(id={self.id}, name={self.name})>"

class Genre(Base):
    __tablename__ = 'genres'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=False)

    # relationship
    animes: Mapped[List["Anime"]] = relationship(
        "Anime",
        secondary=anime_genre_association,
        back_populates="tags"
    )
    mangas: Mapped[List["Manga"]] = relationship(
        "Manga",
        secondary=manga_genre_association,
        back_populates="tags"
    )

    def __repr__(self):
        return f"<Genre(id={self.id}, name={self.name})>"

# Tag model
class Tag(Base):
    __tablename__ = 'tags'  # Changed to avoid reserved keyword issues

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(String, unique=False)
    category: Mapped[str] = mapped_column(String, unique=False)
    isAdult: Mapped[bool] = mapped_column(Boolean, unique=False)

    #relationship
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

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"

class Studio(Base):
    __tablename__ = 'studios'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=False)

    # relationship
    animes: Mapped[List["Anime"]] = relationship(
        "Anime",
        secondary=anime_studio_association,
        back_populates="tags"
    )
    mangas: Mapped[List["Manga"]] = relationship(
        "Manga",
        secondary=manga_studio_association,
        back_populates="tags"
    )


    def __repr__(self):
        return f"<Studio(id={self.id}, name={self.name})>"

class RelationType(Base):
    __tablename__ = 'relation_types'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)  # e.g., 'PREQUEL', 'SEQUEL', 'ADAPTATION'

    def __repr__(self):
        return f"<RelationType(id={self.id}, name={self.name})>"


#anime/manga model
class Anime(Base):
    __tablename__ = 'anime'

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Titles
    title_english: Mapped[str] = mapped_column(String, nullable=True)
    title_romaji: Mapped[str] = mapped_column(String, nullable=True)
    title_native: Mapped[str] = mapped_column(String, nullable=True)

    # Content Info
    description: Mapped[str] = mapped_column(Text, nullable=True)
    cover_image: Mapped[str] = mapped_column(Text, nullable=True)
    banner_image: Mapped[str] = mapped_column(Text, nullable=True)
    synonyms: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    duration: Mapped[int] = mapped_column(Integer, nullable=True)

    # Foreign Keys
    format_id: Mapped[int] = mapped_column(ForeignKey('formats.id'), nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey('source_materials.id'), nullable=True)
    country_origin_id: Mapped[int] = mapped_column(ForeignKey('country_of_origins.id'), nullable=True)
    season_id: Mapped[int] = mapped_column(ForeignKey('seasons.id'), nullable=True)
    status_id: Mapped[int] = mapped_column(ForeignKey('status.id'), nullable=True)

    # Stats & Extras
    episodes: Mapped[int] = mapped_column(Integer, nullable=True)
    popularity: Mapped[int] = mapped_column(Integer, nullable=True)
    favorites: Mapped[int] = mapped_column(Integer, nullable=True)
    average_score: Mapped[int] = mapped_column(Integer, nullable=True)
    mean_score: Mapped[int] = mapped_column(Integer, nullable=True)

    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)


    #relationship one to many
    formats: Mapped["Format"] = relationship("Format", back_populates="animes")
    sources: Mapped["Source"] = relationship("Source", back_populates="animes")
    country_origins: Mapped["CountryOfOrigin"] = relationship("CountryOfOrigin", back_populates="animes")
    seasons: Mapped["Season"] = relationship("Season", back_populates="animes")
    status: Mapped["Status"] = relationship("Status", back_populates="animes")

    #relationship many to many
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=anime_tag_association,
        back_populates="animes"
    )

    genres: Mapped[List["Genre"]] = relationship(
        "Genre",
        secondary=anime_genre_association,
        back_populates="animes"
    )
    studios: Mapped[List["Genre"]] = relationship(
        "Studio",
        secondary=anime_studio_association,
        back_populates="animes"
    )

    anime_character_links: Mapped[List["AnimeCharacter"]] = relationship(back_populates="anime")
    characters: Mapped[List["Character"]] = relationship(
        secondary='anime_character_association',
        viewonly=True
    )
    relations: Mapped[List["AnimeRelation"]] = relationship("AnimeRelation",
                                                            back_populates="anime",
                                                            cascade="all, delete-orphan")


class Manga(Base):
    __tablename__ = 'mangas'

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Titles
    title_english: Mapped[str] = mapped_column(String, nullable=True)
    title_romaji: Mapped[str] = mapped_column(String, nullable=True)
    title_native: Mapped[str] = mapped_column(String, nullable=True)

    # Content Info
    description: Mapped[str] = mapped_column(Text, nullable=True)
    cover_image: Mapped[str] = mapped_column(Text, nullable=True)
    banner_image: Mapped[str] = mapped_column(Text, nullable=True)
    synonyms: Mapped[list[str]] = mapped_column(JSON, nullable=True)

    # Foreign Keys
    format_id: Mapped[int] = mapped_column(ForeignKey('formats.id'), nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey('source_materials.id'), nullable=True)
    country_origin_id: Mapped[int] = mapped_column(ForeignKey('country_of_origins.id'), nullable=True)
    season_id: Mapped[int] = mapped_column(ForeignKey('seasons.id'), nullable=True)
    status_id: Mapped[int] = mapped_column(ForeignKey('status.id'), nullable=True)

    # Stats & Extras
    chapters: Mapped[int] = mapped_column(Integer, nullable=True)
    volumes: Mapped[int] = mapped_column(Integer, nullable=True)
    popularity: Mapped[int] = mapped_column(Integer, nullable=True)
    favorites: Mapped[int] = mapped_column(Integer, nullable=True)
    average_score: Mapped[int] = mapped_column(Integer, nullable=True)
    mean_score: Mapped[int] = mapped_column(Integer, nullable=True)

    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # relationship
    formats: Mapped["Format"] = relationship("Format", back_populates="mangas")
    sources: Mapped["Source"] = relationship("Source", back_populates="mangas")
    country_origins: Mapped["CountryOfOrigin"] = relationship("CountryOfOrigin", back_populates="mangas")
    seasons: Mapped["Season"] = relationship("Season", back_populates="mangas")
    status: Mapped["Status"] = relationship("Status", back_populates="mangas")

    # relationship many to many
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=anime_tag_association,
        back_populates="mangas"
    )
    genres: Mapped[List["Genre"]] = relationship(
        "Genre",
        secondary=manga_genre_association,
        back_populates="mangas"
    )
    studios: Mapped[List["Genre"]] = relationship(
        "Studio",
        secondary=manga_studio_association,
        back_populates="mangas"
    )
    manga_character_links: Mapped[List["MangaCharacter"]] = relationship(back_populates="manga")
    characters: Mapped[List["Character"]] = relationship(
        secondary='manga_character_association',
        viewonly=True
    )
    relations: Mapped[List["MangaRelation"]] = relationship("MangaRelation",
                                                            back_populates="manga",
                                                            cascade="all, delete-orphan")


class Character(Base):
    __tablename__ = 'characters'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    name_native: Mapped[str] = mapped_column(String, nullable=True)
    image: Mapped[str] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    dob: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    #relationship
    anime_character_links: Mapped[List["AnimeCharacter"]] = relationship(back_populates="character")
    animes: Mapped[List["Anime"]] = relationship(
        secondary='anime_character_association',
        viewonly=True
    )
    manga_character_links: Mapped[List["MangaCharacter"]] = relationship(back_populates="character")
    mangas: Mapped[List["Manga"]] = relationship(
        secondary='manga_character_association',
        viewonly=True
    )

    def __repr__(self):
        return f"<Character(id={self.id}, name={self.name}, name_native={self.name_native})>"

class AnimeCharacter(Base):
    __tablename__ = 'anime_character_association'

    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id'), primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey('characters.id'), primary_key=True)

    role: Mapped[str] = mapped_column(String)  # e.g., 'Main', 'Supporting'
    # possibly more fields, e.g., voice_actor_id, order, etc.

    #relationship
    anime: Mapped["Anime"] = relationship(back_populates="anime_character_links")
    character: Mapped["Character"] = relationship(back_populates="anime_character_links")

class MangaCharacter(Base):
    __tablename__ = 'manga_character_association'

    manga_id: Mapped[int] = mapped_column(ForeignKey('manga.id'), primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey('characters.id'), primary_key=True)

    role: Mapped[str] = mapped_column(String)

    #relationship
    manga: Mapped["Manga"] = relationship(back_populates="manga_character_links")
    character: Mapped["Character"] = relationship(back_populates="manga_character_links")


class Relation(Base):
    __tablename__ = 'relations'

    id: Mapped[int] = mapped_column(primary_key=True)

    title_english: Mapped[Optional[str]] = mapped_column(String)
    title_romaji: Mapped[Optional[str]] = mapped_column(String)
    title_native: Mapped[Optional[str]] = mapped_column(String)
    cover_image: Mapped[Optional[str]] = mapped_column(Text)

    # Optional: Add relationship to backref relations
    anime_relations: Mapped[List["AnimeRelation"]] = relationship("AnimeRelation", back_populates="relation", cascade="all, delete-orphan")
    manga_relations: Mapped[List["MangaRelation"]] = relationship("MangaRelation", back_populates="relation", cascade="all, delete-orphan")


class AnimeRelation(Base):
    __tablename__ = 'anime_relations'

    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id'), primary_key=True)
    relation_id: Mapped[int] = mapped_column(ForeignKey('relations.id'), primary_key=True)
    relation_type_id: Mapped[int] = mapped_column(ForeignKey('relation_types.id'))

    anime: Mapped["Anime"] = relationship("Anime", back_populates="relations")
    relation: Mapped["Relation"] = relationship("Relation", back_populates="anime_relations")
    relation_type: Mapped["RelationType"] = relationship("RelationType")


class MangaRelation(Base):
    __tablename__ = 'manga_relations'

    manga_id: Mapped[int] = mapped_column(ForeignKey('manga.id'), primary_key=True)
    relation_id: Mapped[int] = mapped_column(ForeignKey('relations.id'), primary_key=True)
    relation_type_id: Mapped[int] = mapped_column(ForeignKey('relation_types.id'))

    manga: Mapped["Manga"] = relationship("Manga", back_populates="relations")
    relation: Mapped["Relation"] = relationship("Relation", back_populates="manga_relations")
    relation_type: Mapped["RelationType"] = relationship("RelationType")



class UserCategory(Base):
    __tablename__ = 'user_categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, default=None, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class AnimeLibrary(Base):
    __tablename__ = 'anime_libraries'

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id'), primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey('characters.id'), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    #todo link with category one to many

class MangaLibrary(Base):
    __tablename__ = 'manga_libraries'
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    manga_id: Mapped[int] = mapped_column(ForeignKey('manga.id'), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('manga_categories.id'), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # todo link with category one to many

class AnimeWatchHistory(Base):
    __tablename__ = 'anime_watch_history'
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id'), primary_key=True)
    duration: Mapped[int] = mapped_column(Integer)
    watched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class MangaWatchHistory(Base):
    __tablename__ = 'manga_watch_history'
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    manga_id: Mapped[int] = mapped_column(ForeignKey('manga.id'), primary_key=True)
    pages: Mapped[int] = mapped_column(Integer)
    watched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

#create tables
async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)