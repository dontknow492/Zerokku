from core import BaseExtension, SPage, SAnime, SEpisode, ExtensionMeta, ExtensionType
from pydantic import HttpUrl

import requests

anime_pahe_meta = ExtensionMeta(
    id = "123x",
    name = "Animepahe",
    version = "1.0",
    author = "Ghost",
    lang = 'en',
    icon = HttpUrl("https://animepahe.ru/web-app-manifest-512x512.png"),
    extension_type=ExtensionType.ANIME,
    website = HttpUrl("https://animepahe.ru/"),
    nsfw = False,
    requires_login=False
)

class AnimePahe(BaseExtension):
    meta = anime_pahe_meta

    def search(self, query: str):
        url = f"{self.meta.website}/api?m=search&q={query}"
        response_id = self.requestHandler.fetch(url)



if __name__ == '__main__':
    print(anime_pahe_meta.model_dump())
