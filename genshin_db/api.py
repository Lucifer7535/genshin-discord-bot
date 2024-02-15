import enum
from typing import Any, ClassVar, Union

import aiohttp


class API:
    GENSHIN_DB_URL: ClassVar[str] = "https://genshin-db-api.vercel.app/api/v5/{folder}"
    IMAGE_URL: ClassVar[str] = (
        "https://res.cloudinary.com/genshin/image/upload/sprites/{image}.png"
    )

    class GenshinDBLang(enum.Enum):

        CHT = "ChineseTraditional"
        CHS = "ChineseSimplified"
        ENG = "English"

    class GenshinDBFolder(enum.Enum):

        TCG_ACTION_CARDS = "tcgactioncards"
        TCG_CHARACTER_CARDS = "tcgcharactercards"
        TCG_SUMMONS = "tcgsummons"

        CHARACTERS = "characters"
        CONSTELLATIONS = "constellations"
        TALENTS = "talents"

        ACHIEVEMENTS = "achievements"
        ARTIFACTS = "artifacts"
        FOODS = "foods"
        MATERIALS = "materials"
        WEAPONS = "weapons"

    @classmethod
    async def request_genshin_db(
        cls,
        folder: Union[GenshinDBFolder, str],
        query: str,
        *,
        dumpResult: bool = False,
        matchNames: bool = True,
        matchAltNames: bool = True,
        matchAliases: bool = False,
        matchCategories: bool = False,
        verboseCategories: bool = False,
        queryLanguages: str = GenshinDBLang.ENG.value,
        resultLanguage: str = GenshinDBLang.ENG.value,
    ) -> Any:

        folder_name = str(folder.value) if not isinstance(folder, str) else folder
        url = cls.GENSHIN_DB_URL.format(folder=folder_name)
        params = {
            "query": query,
            "dumpResult": str(dumpResult),
            "matchNames": str(matchNames),
            "matchAltNames": str(matchAltNames),
            "matchAliases": str(matchAliases),
            "matchCategories": str(matchCategories),
            "verboseCategories": str(verboseCategories),
            "queryLanguages": queryLanguages,
            "resultLanguage": resultLanguage,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(
                        f"Unable to retrieve content from the genshin-db API: url={url} params={str(params)}"
                    )
                data = await response.json(encoding="utf-8")
                return data

    @classmethod
    def get_image_url(cls, image_name: str) -> str:
        return cls.IMAGE_URL.format(image=image_name)
