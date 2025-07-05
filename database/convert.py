from datetime import datetime
from typing import Union

from scipy.cluster.hierarchy import average

from AnillistPython import AnilistMedia, AnilistTitle, AnilistTag, AnilistStudio, AnilistCharacter, AnilistScore, \
    AnilistMediaInfo, MediaSeason, MediaStatus, MediaSource, MediaFormat, AnilistMediaCharacter, MediaType
from AnillistPython.models import CharacterRole, AnilistStudio
from AnillistPython.models.media import AnilistMediaTrailer, MediaCoverImage
from database.models import Anime, Manga, Tag, Studio, Trailer, Character, MediaCharacter


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

    return {
        "id": data.id,
        "title_english": title.english if title else None,
        "title_romaji": title.romaji if title else None,
        "title_native": title.native if title else None,
        "description": data.description,
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
        "tags": [anilist_to_tags(tag) for tag in data.tags],
        "trailers": [anilist_to_trailer(data.trailer)],
    }


def anilist_to_anime(data: AnilistMedia) -> Anime:
    fields = extract_common_media_fields(data)
    fields.update({
        "episodes": data.episodes,
        "duration": data.duration,
        "media_character_links": [link_character(character, MediaType.ANIME, data.id) for character in data.characters],
    })
    return Anime(**fields)


def anilist_to_manga(data: AnilistMedia) -> Manga:
    fields = extract_common_media_fields(data)
    fields.update({
        "chapters": data.chapters,
        "volumes": data.volumes,
    })
    return Manga(**fields)


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
        genres=["Action", "Fantasy"],
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
    # anime = Anime(id=1)
    # pprint(vars(tag))
    # pprint(vars(studio))
    # pprint(vars(char))
    # pprint(vars(trailer))