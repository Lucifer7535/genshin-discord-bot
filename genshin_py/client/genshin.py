import asyncio
from typing import Sequence, Tuple

import genshin

from database import GenshinSpiralAbyss

from ..errors_decorator import generalErrorHandler
from .common import get_client


@generalErrorHandler
async def get_genshin_notes(user_id: int) -> genshin.models.Notes:
    client = await get_client(user_id)
    return await client.get_genshin_notes(client.uid)


@generalErrorHandler
async def get_genshin_spiral_abyss(user_id: int, previous: bool = False) -> GenshinSpiralAbyss:
    client = await get_client(user_id)
    await client.get_record_cards()
    abyss, characters = await asyncio.gather(
        client.get_genshin_spiral_abyss(client.uid or 0, previous=previous),
        client.get_genshin_characters(client.uid or 0),
        return_exceptions=True,
    )
    if isinstance(abyss, BaseException):
        raise abyss
    if isinstance(characters, BaseException):
        return GenshinSpiralAbyss(user_id, abyss.season, abyss, None)
    return GenshinSpiralAbyss(user_id, abyss.season, abyss, characters)


@generalErrorHandler
async def get_genshin_traveler_diary(user_id: int, month: int) -> genshin.models.Diary:
    client = await get_client(user_id)
    diary = await client.get_diary(client.uid, month=month)
    return diary


@generalErrorHandler
async def get_genshin_record_card(
    user_id: int,
) -> Tuple[int, genshin.models.PartialGenshinUserStats]:
    client = await get_client(user_id)
    userstats = await client.get_partial_genshin_user(client.uid or 0)
    return (client.uid or 0, userstats)


@generalErrorHandler
async def get_genshin_characters(user_id: int) -> Sequence[genshin.models.Character]:
    client = await get_client(user_id)
    return await client.get_genshin_characters(client.uid or 0)


@generalErrorHandler
async def get_genshin_notices() -> Sequence[genshin.models.Announcement]:
    client = genshin.Client(lang="en-us")
    notices = await client.get_genshin_announcements()
    return notices
