import json
from datetime import datetime
from enum import EnumType, Enum
from typing import Union, List, Dict, Type, Optional

from pywin.dialogs import status

from AnillistPython import AnilistMedia, AnilistTitle, AnilistTag, AnilistStudio, AnilistCharacter, AnilistScore, \
    AnilistMediaInfo, MediaSeason, MediaStatus, MediaSource, MediaFormat, AnilistMediaCharacter, MediaType, MediaGenre, \
    MediaRelation
from AnillistPython.models import CharacterRole, AnilistStudio
from AnillistPython.models.media import AnilistMediaTrailer, MediaCoverImage
from database.models import Anime, Manga, Tag, Studio, Trailer, Character, MediaCharacter, Genre, Format, Status, \
    Season, SourceMaterial, CharacterRole as DbCharacterRole, RelationType as RelationType

tags_data: List[Dict] = []

def read_tag(tag_path: str):
    global tags_data
    with open(tag_path, "r", encoding="utf-8") as f:
        tags_data = json.load(f)



media_enum_to_index = {
    MediaFormat: {
        MediaFormat.TV: 0,
        MediaFormat.TV_SHORT: 1,
        MediaFormat.MOVIE: 2,
        MediaFormat.SPECIAL: 3,
        MediaFormat.OVA: 4,
        MediaFormat.ONA: 5,
        MediaFormat.MUSIC: 6,
        MediaFormat.MANGA: 7,
        MediaFormat.NOVEL: 8,
        MediaFormat.ONE_SHOT: 9
    },
    MediaStatus: {
        MediaStatus.FINISHED: 0,
        MediaStatus.RELEASING: 1,
        MediaStatus.NOT_YET_RELEASED: 2,
        MediaStatus.CANCELLED: 3,
        MediaStatus.HIATUS: 4
    },
    MediaSeason: {
        MediaSeason.WINTER: 0,
        MediaSeason.SPRING: 1,
        MediaSeason.SUMMER: 2,
        MediaSeason.FALL: 3
    },
    MediaSource: {
        MediaSource.ORIGINAL: 0,
        MediaSource.MANGA: 1,
        MediaSource.LIGHT_NOVEL: 2,
        MediaSource.VISUAL_NOVEL: 3,
        MediaSource.VIDEO_GAME: 4,
        MediaSource.OTHER: 5,
        MediaSource.NOVEL: 6,
        MediaSource.DOUJINSHI: 7,
        MediaSource.ANIME: 8,
        MediaSource.WEB_NOVEL: 9,
        MediaSource.LIVE_ACTION: 10,
        MediaSource.GAME: 11,
        MediaSource.COMIC: 12,
        MediaSource.MULTIMEDIA_PROJECT: 13,
        MediaSource.PICTURE_BOOK: 14
    },
    CharacterRole: {
        CharacterRole.MAIN: 0,
        CharacterRole.SUPPORTING: 1,
        CharacterRole.BACKGROUND: 2
    },
    MediaRelation: {
        MediaRelation.ADAPTATION: 0,
        MediaRelation.PREQUEL: 1,
        MediaRelation.SEQUEL: 2,
        MediaRelation.PARENT: 3,
        MediaRelation.SIDE_STORY: 4,
        MediaRelation.CHARACTER: 5,
        MediaRelation.SUMMARY: 6,
        MediaRelation.ALTERNATIVE: 7,
        MediaRelation.SPIN_OFF: 8,
        MediaRelation.OTHER: 9,
        MediaRelation.SOURCE: 10,
        MediaRelation.COMPILATION: 11,
        MediaRelation.CONTAINS: 12
    },
    MediaGenre: {
        MediaGenre.ACTION: 0,
        MediaGenre.ADVENTURE: 1,
        MediaGenre.COMEDY: 2,
        MediaGenre.DRAMA: 3,
        MediaGenre.ECCHI: 4,
        MediaGenre.FANTASY: 5,
        MediaGenre.HENTAI: 6,
        MediaGenre.HORROR: 7,
        MediaGenre.MAHOU_SHOUJO: 8,
        MediaGenre.MECHA: 9,
        MediaGenre.MUSIC: 10,
        MediaGenre.MYSTERY: 11,
        MediaGenre.PSYCHOLOGICAL: 12,
        MediaGenre.ROMANCE: 13,
        MediaGenre.SCI_FI: 14,
        MediaGenre.SLICE_OF_LIFE: 15,
        MediaGenre.SPORTS: 16,
        MediaGenre.SUPERNATURAL: 17,
        MediaGenre.THRILLER: 18
    }
}


def get_enum_index(enum_class: type[Enum], enum_value: Enum) -> int | None:
    """
    Returns the index of an enum value from the specified enum class.

    Args:
        enum_class: The enum class (e.g., MediaFormat, MediaGenre).
        enum_value: The enum value (e.g., MediaFormat.TV, MediaGenre.ACTION).

    Returns:
        The index of the enum value if found, otherwise None.

    Raises:
        TypeError: If enum_class is not a subclass of Enum or enum_value is not an instance of enum_class.
    """
    if not isinstance(enum_class, type) or not issubclass(enum_class, Enum):
        raise TypeError(f"enum_class must be a subclass of Enum, got {enum_class}")
    if not isinstance(enum_value, enum_class):
        raise TypeError(f"enum_value must be an instance of {enum_class}, got {type(enum_value)}")

    return media_enum_to_index.get(enum_class, {}).get(enum_value)

def get_index_enum(enum_class: type[Enum], enum_idx: int) -> Enum | None:
    """
    Returns the enum value from the specified enum class by its index,
    using the media_enum_to_index mapping.

    Args:
        enum_class: The enum class (e.g., MediaGenre).
        enum_idx: The index of the enum value.

    Returns:
        The enum value if found, otherwise None.

    Raises:
        TypeError: If enum_class is not a subclass of Enum.
    """
    if not isinstance(enum_class, type) or not issubclass(enum_class, Enum):
        raise TypeError(f"enum_class must be a subclass of Enum, got {enum_class}")

    enum_map = media_enum_to_index.get(enum_class)
    if not enum_map:
        return None

    # Reverse lookup: index → enum
    for enum_value, idx in enum_map.items():
        if idx == enum_idx:
            return enum_value

    return None




def anilist_to_genre(genre: MediaGenre) -> Genre:
    if genre is None:
        return None
    return Genre(
        id=get_enum_index(MediaGenre, genre),
        name=genre.value,
    )


def anilist_to_format(format: MediaFormat):
    if not format:
        return None
    return Format(
        id = get_enum_index(MediaFormat, format),
        name = format.value,
    )

def anilist_to_status(status: MediaStatus):
    if not status:
        return None
    return Status(
        id = get_enum_index(MediaStatus, status),
        name = status.value,
    )

def anilist_to_season(season: MediaSeason):
    if not season:
        return None
    return Season(
        id = get_enum_index(MediaSeason, season),
        name = season.value,
    )

def anilist_to_source(source: MediaSource):
    if not source:
        return None
    return SourceMaterial(
        id = get_enum_index(MediaSource, source),
        name = source.value,
    )

def anilist_to_character_role(character_role: CharacterRole):
    if not character_role:
        return None
    return DbCharacterRole(
        id = get_enum_index(CharacterRole, character_role),
        name = character_role.value,
    )

def anilist_to_relation_type(relation_type: MediaRelation):
    if not relation_type:
        return None
    return RelationType(
        id = get_enum_index(MediaRelation, relation_type),
        name = relation_type.value,
    )

def get_all_genres() -> List[Genre]:
    return [anilist_to_genre(genre) for genre in MediaGenre]

def get_all_formats() -> List[Format]:
    return [anilist_to_format(format) for format in MediaFormat]

def get_all_statuses() -> List[Status]:
    return [anilist_to_status(status) for status in MediaStatus]

def get_all_seasons() -> List[Season]:
    return [anilist_to_season(season) for season in MediaSeason]

def get_all_sources() -> List[SourceMaterial]:
    return [anilist_to_source(source) for source in MediaSource]

def get_all_character_roles() -> List[DbCharacterRole]:
    return [anilist_to_character_role(character_role) for character_role in CharacterRole]

def get_all_relation_types() -> List[RelationType]:
    return [anilist_to_relation_type(relation) for relation in MediaRelation]

def anilist_to_tags(data: AnilistTag):
    return Tag(
        id = data.id,
        name = data.name,
        category = data.category,
        isAdult = data.isAdult,
        description = data.description,
    )

def anilist_to_studio(data: AnilistStudio):
    return Studio(
        id = data.id,
        name = data.name,
    )

def anilist_to_trailer(data: AnilistMediaTrailer):
    return Trailer(
        video_id = data.video_id,
        site = data.site,
        thumbnail=data.thumbnail,
    )

def anilist_to_character(data: AnilistCharacter):
    return Character(
        id = data.id,
        description = data.description,
        age = data.age,
        dob = data.dob,
        image=data.image,
        name_native= data.name.native if data.name else None,
        name = (data.name.romaji or data.name.english) if data.name else None,
    )

def link_character(character: Union[Character, AnilistCharacter], media_type: MediaType, media_id: int):
    if isinstance(character, AnilistCharacter):
        character = anilist_to_character(character)
    return MediaCharacter(
        character_id = character.id,
        character=character,
        anime_id= media_id if media_type == MediaType.ANIME else None,
        manga_id=media_id if media_type == MediaType.MANGA else None,
    )

def extract_common_media_fields(data: AnilistMedia) -> dict:
    title = data.title or {}
    score = data.score or {}
    info = data.info or {}
    studios = data.studios or []
    genres = data.genres or []
    tags = data.tags or []

    cover_image = data.coverImage or {}

    return {
        "id": data.id,

        "title_english": title.english if title else None,
        "title_romaji": title.romaji if title else None,
        "title_native": title.native if title else None,

        "description": data.description,

        "cover_image_extra_large": cover_image.extraLarge if cover_image else None,
        "cover_image_large": cover_image.large if cover_image else None,
        "cover_image_medium": cover_image.medium if cover_image else None,
        "cover_image_color": cover_image.color if cover_image else None,
        "banner_image": data.bannerImage,

        "status_id": get_enum_index(type(info.status), info.status) if status else None,
        "format_id": get_enum_index(type(info.format), info.format) if info else None,
        "season_id": get_enum_index(type(info.season), info.season) if info else None,
        "source_material_id": get_enum_index(type(info.source), info.source) if info else None,

        "synonyms": data.synonyms or [],
        "start_date": data.startDate,
        "end_date": data.endDate,
        "average_score": score.average_score if score else None,
        "mean_score": score.mean_score if score else None,
        "popularity": score.popularity if score else None,
        "favourites": score.favourites if score else None,
        "isAdult": data.isAdult or False,
        "site_url": data.siteUrl,
        "idMal": data.idMal,
        "tags": filter_none_values([anilist_to_tags(tag) for tag in tags]),
        "trailers": filter_none_values([anilist_to_trailer(data.trailer)] if data.trailer else None),
        "studios": filter_none_values([anilist_to_studio(studio) for studio in studios]),
        "genres": filter_none_values([anilist_to_genre(genre) for genre in genres]),
    }


def anilist_to_anime(data: AnilistMedia) -> Anime:
    characters = data.characters or []
    genres = data.genres or []
    fields = extract_common_media_fields(data)
    fields.update({
        "episodes": data.episodes,
        "duration": data.duration,
        "media_character_links": filter_none_values([link_character(character, MediaType.ANIME, data.id) for character in characters])
    })
    return Anime(**fields)
    # anime.genres.extend(filter_none_values([anilist_to_genre(genre) for genre in genres]))



def anilist_to_manga(data: AnilistMedia) -> Manga:
    characters = data.characters or []
    fields = extract_common_media_fields(data)
    fields.update({
        "chapters": data.chapters,
        "volumes": data.volumes,
        "media_character_links": filter_none_values([link_character(character, MediaType.MANGA, data.id) for character in characters])
    })
    return Manga(**fields)

def filter_none_values(data: list) -> list:
    if data is None:
        return []
    return [item for item in data if item is not None]


if __name__ == '__main__':
    from pprint import pprint
    sample_title = AnilistTitle(
        romaji="Shingeki no Kyojin",
        english="Attack on Titan",
        native="進撃の巨人"
    )

    sample_character = AnilistCharacter(
        id=101,
        name=AnilistTitle(
            romaji="Eren Yeager",
            english="Eren Yeager",
            native="エレン・イェーガー"
        ),
        image="https://example.com/eren.jpg",
        age=15,
        dob=datetime(2003, 3, 30),
        description="The protagonist of Attack on Titan."
    )

    sample_tag = AnilistTag(
        id=5,
        name="Action",
        description="Action-packed sequences and battles.",
        category="Genre",
        isAdult=False
    )

    sample_studio = AnilistStudio(
        id=10,
        name="Wit Studio"
    )

    sample_cover = MediaCoverImage(
            extraLarge="https://example.com/cover_xl.jpg",
            large="https://example.com/cover_l.jpg",
            medium="https://example.com/cover_m.jpg",
            color="#1A1A1A"
        )

    sample_score = AnilistScore(id=101, average_score=85, popularity=98.7, favourites=150000)

    sample_info = AnilistMediaInfo(
            id=101,
            format=MediaFormat.TV,
            source=MediaSource.MANGA,
            country_origin="JP",
            season=MediaSeason.SPRING,
            status=MediaStatus.FINISHED
        )

    sample_trailer = AnilistMediaTrailer(
        video_id= "1223",
        site = "https://example.com",
        thumbnail = "https://example.com/thumbnail.jpg",
    )

    sample_media = AnilistMedia(
        id=101,
        title=sample_title,
        description="After his hometown is destroyed and his mother is killed, young Eren Yeager joins the Survey Corps...",
        coverImage= sample_cover,
        bannerImage="https://example.com/banner.jpg",
        synonyms=["AoT", "Shingeki"],
        tags=[sample_tag, sample_tag],
        genres=[MediaGenre.ACTION, MediaGenre.ADVENTURE, MediaGenre.ROMANCE],
        studios=[AnilistStudio(name="Wit Studio", id=1)],
        score=sample_score,
        info= sample_info,
        startDate=datetime(2013, 4, 6),
        endDate=datetime(2013, 9, 28),
        characters=[sample_character, sample_character],
        duration=24,
        episodes=25,
        isAdult=False,
        trailer=sample_trailer,
        siteUrl="https://anilist.co/anime/101",
        idMal=16498,
        media_type=MediaType.ANIME,
        relations=[],
        recommendations=[]
    )

    tag = anilist_to_tags(sample_tag)
    studio = anilist_to_studio(sample_studio)
    trailer = anilist_to_trailer(sample_trailer)
    char = anilist_to_character(sample_character)

    anime = anilist_to_anime(sample_media)
    pprint(vars(anime))

    pprint(vars(get_all_sources()[0]))
    # anime = Anime(id=1)
    # pprint(vars(tag))
    # pprint(vars(studio))
    # pprint(vars(char))
    # pprint(vars(trailer))