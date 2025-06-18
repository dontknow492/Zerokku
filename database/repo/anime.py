from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Anime


class AsyncAnimeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, anime_data: dict) -> Anime:
        anime = Anime(**anime_data)
        self.session.add(anime)
        await self.session.commit()
        await self.session.refresh(anime)
        return anime

    async def get_by_id(self, anime_id: int) -> Anime | None:
        result = await self.session.execute(select(Anime).filter(Anime.id == anime_id))
        return result.scalars().first()

    async def get_by_title(self, title: str) -> Sequence[Anime]:
        result = await self.session.execute(select(Anime).filter(Anime.title_english.ilike(f"%{title}%")))
        return result.scalars().all()

    async def update(self, anime_id: int, update_data: dict) -> Anime | None:
        anime = await self.get_by_id(anime_id)
        if not anime:
            return None
        for key, value in update_data.items():
            setattr(anime, key, value)
        await self.session.commit()
        return anime

    async def delete(self, anime_id: int) -> bool:
        anime = await self.get_by_id(anime_id)
        if not anime:
            return False
        await self.session.delete(anime)
        await self.session.commit()
        return True
