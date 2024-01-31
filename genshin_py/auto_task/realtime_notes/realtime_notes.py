import asyncio
from datetime import datetime
from typing import Awaitable, Callable, ClassVar

import discord
import sentry_sdk
import sqlalchemy
from discord.ext import commands

from database import Database, GenshinScheduleNotes, StarrailScheduleNotes
from utility import LOG, config

from .common import CheckResult, T_User
from .genshin import check_genshin_notes
from .starrail import check_starrail_notes


class RealtimeNotes:

    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _bot: commands.Bot

    @classmethod
    async def execute(cls, bot: commands.Bot):
        if cls._lock.locked():
            return
        await cls._lock.acquire()
        cls._bot = bot
        try:
            LOG.System("Automatically check the resins")
            await asyncio.gather(
                cls._check_games_note(GenshinScheduleNotes, "Genshin Impact", check_genshin_notes),
                cls._check_games_note(StarrailScheduleNotes, "Star Rail", check_starrail_notes),
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            LOG.Error(f"Automatic scheduling of RealtimeNotes encountered an error: {e}")
        finally:
            cls._lock.release()

    @classmethod
    async def _check_games_note(
        cls,
        game_orm: type[T_User],
        game_name: str,
        game_check_fucntion: Callable[[T_User], Awaitable[CheckResult | None]],
    ) -> None:
        count = 0
        stmt = sqlalchemy.select(game_orm.discord_id)
        async with Database.sessionmaker() as session:
            user_ids = (await session.execute(stmt)).scalars().all()
        for user_id in user_ids:
            user = await Database.select_one(game_orm, game_orm.discord_id.is_(user_id))
            if user is None or user.next_check_time and datetime.now() < user.next_check_time:
                continue
            r = await game_check_fucntion(user)
            if r is not None:
                count += 1
            if r and len(r.message) > 0:
                await cls._send_message(user, r.message, r.embed)
            await asyncio.sleep(config.schedule_loop_delay)
        LOG.System(f"Automatic check for real-time notes in {game_name} completed. {count}/{len(user_ids)} users have been checked.")

    @classmethod
    async def _send_message(cls, user: T_User, message: str, embed: discord.Embed) -> None:
        bot = cls._bot
        try:
            _id = user.discord_channel_id
            channel = bot.get_channel(_id) or await bot.fetch_channel(_id)
            discord_user = bot.get_user(user.discord_id) or await bot.fetch_user(user.discord_id)
            msg_sent = await channel.send(f"{discord_user.mention}，{message}", embed=embed)
        except (
            discord.Forbidden,
            discord.NotFound,
            discord.InvalidData,
        ) as e:  
            LOG.Except(f"Failed to send message during automatic check for real-time notes. Remove this user {LOG.User(user.discord_id)}: {e}")
            await Database.delete_instance(user)
        except Exception as e:
            sentry_sdk.capture_exception(e)
        else:  
            if discord_user.mentioned_in(msg_sent) is False:
                LOG.Except(f"The user is not in the channel during the automatic check for real-time notes. Remove this user {LOG.User(discord_user)}")
                await Database.delete_instance(user)
