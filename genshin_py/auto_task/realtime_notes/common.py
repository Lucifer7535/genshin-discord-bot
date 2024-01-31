from datetime import datetime, timedelta
from typing import NamedTuple, TypeVar

import discord
import genshin

from database import Database, GenshinScheduleNotes, StarrailScheduleNotes

from ... import errors, get_genshin_notes, get_starrail_notes

T_User = TypeVar("T_User", GenshinScheduleNotes, StarrailScheduleNotes)


class CheckResult(NamedTuple):
    """`tuple[str, embed]`: The return result of the check_xxx_notes function"""

    message: str
    embed: discord.Embed


async def get_realtime_notes(
    user: T_User,
) -> genshin.models.Notes | genshin.models.StarRailNote | None:
    notes = None
    try:
        if isinstance(user, GenshinScheduleNotes):
            notes = await get_genshin_notes(user.discord_id)
        if isinstance(user, StarrailScheduleNotes):
            notes = await get_starrail_notes(user.discord_id)
    except Exception as e:
        if isinstance(e, errors.GenshinAPIException) and isinstance(
            e.origin, genshin.errors.InternalDatabaseError
        ):
            user.next_check_time = datetime.now() + timedelta(hours=1)
            await Database.insert_or_replace(user)
        else:  
            user.next_check_time = datetime.now() + timedelta(hours=5)
            await Database.insert_or_replace(user)
            raise e
    return notes


def cal_next_check_time(remaining: timedelta, user_threshold: int) -> datetime:
    remaining_hours: float = remaining.total_seconds() / 3600
    if remaining_hours > user_threshold:
        return datetime.now() + remaining - timedelta(hours=user_threshold)
    else:  
        interval: float = float(user_threshold / 3)
        user_threshold_f: float = float(user_threshold)
        if interval > 0.0:
            while remaining_hours <= user_threshold_f:
                user_threshold_f -= interval
        return datetime.now() + remaining - timedelta(hours=user_threshold_f)
