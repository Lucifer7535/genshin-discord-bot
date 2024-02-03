import asyncio
from datetime import datetime
from typing import Any, ClassVar, Final

import aiohttp
import discord
import sentry_sdk
from discord.ext import commands

import database
from database import Database, GeetestChallenge, ScheduleDailyCheckin, User
from utility import LOG, EmbedTemplate, config

from .. import claim_daily_reward


class DailyReward:
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _total: ClassVar[dict[str, int]] = {}
    _honkai_count: ClassVar[dict[str, int]] = {}
    _starrail_count: ClassVar[dict[str, int]] = {}

    @classmethod
    async def execute(cls, bot: commands.Bot):
        if cls._lock.locked():
            return
        await cls._lock.acquire()
        try:
            LOG.System("Daily automatic sign-in started")

            queue: asyncio.Queue[ScheduleDailyCheckin] = asyncio.Queue()
            cls._total = {}
            cls._honkai_count = {}
            cls._starrail_count = {}
            daily_users = await Database.select_all(ScheduleDailyCheckin)

            for user in daily_users:
                if user.next_checkin_time < datetime.now():
                    await queue.put(user)

            tasks = [asyncio.create_task(cls._claim_daily_reward_task(queue, "LOCAL", bot))]
            for host in config.daily_reward_api_list:
                tasks.append(asyncio.create_task(cls._claim_daily_reward_task(queue, host, bot)))

            await queue.join()
            for task in tasks:
                task.cancel()

            _log_message = (
                f"Automatic sign-in completed: {sum(cls._total.values())} people signed in, "
                + f"including {sum(cls._honkai_count.values())} for Honkai Impact 3 and {sum(cls._starrail_count.values())} for Star Rail.\n"
            )
            for host in cls._total.keys():
                _log_message += f"- {host}：{cls._total.get(host)}、{cls._honkai_count.get(host)}、{cls._starrail_count.get(host)}\n"
            LOG.System(_log_message)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            LOG.Error(f"Automatic scheduling for Daily Rewards encountered an error: {e}")
        finally:
            cls._lock.release()

    @classmethod
    async def _claim_daily_reward_task(
        cls, queue: asyncio.Queue[ScheduleDailyCheckin], host: str, bot: commands.Bot
    ):
        LOG.Info(f"Automatic scheduling for sign-in tasks started: {host}")
        if host != "LOCAL":
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(host) as resp:
                        if resp.status != 200:
                            raise Exception(f"HTTP status code {resp.status}")
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    LOG.Error(f"Error occurred during testing API {host} for DailyReward automatic scheduling: {e}")
                    return

        cls._total[host] = 0  
        cls._honkai_count[host] = 0  
        cls._starrail_count[host] = 0  
        MAX_API_ERROR_COUNT: Final[int] = 20  
        api_error_count = 0  

        while True:
            user = await queue.get()
            try:
                message = await cls._claim_daily_reward(host, user)
            except Exception as e:
                await queue.put(user)  
                api_error_count += 1
                LOG.Error(f"Remote API: Error occurred at {host} ({api_error_count}/{MAX_API_ERROR_COUNT})")
                if api_error_count >= MAX_API_ERROR_COUNT:
                    sentry_sdk.capture_exception(e)
                    return
            else:
                user.update_next_checkin_time()
                await Database.insert_or_replace(user)
                if message is not None:
                    await cls._send_message(bot, user, message)
                    cls._total[host] += 1
                    cls._honkai_count[host] += int(user.has_honkai3rd)
                    cls._starrail_count[host] += int(user.has_starrail)
                    await asyncio.sleep(config.schedule_loop_delay)
            finally:
                queue.task_done()

    @classmethod
    async def _claim_daily_reward(cls, host: str, user: ScheduleDailyCheckin) -> str | None:
        if host == "LOCAL":
            message = await claim_daily_reward(
                user.discord_id,
                has_genshin=user.has_genshin,
                has_honkai3rd=user.has_honkai3rd,
                has_starrail=user.has_starrail,
            )
            return message
        else:
            user_data = await Database.select_one(User, User.discord_id.is_(user.discord_id))
            gt_challenge = await Database.select_one(
                GeetestChallenge, GeetestChallenge.discord_id.is_(user.discord_id)
            )
            if user_data is None:
                return None
            check, msg = await database.Tool.check_user(user_data)
            if check is False:
                return msg
            payload: dict[str, Any] = {
                "discord_id": user.discord_id,
                "uid": 0,
                "cookie": user_data.cookie_default,
                "cookie_genshin": user_data.cookie_genshin,
                "cookie_honkai3rd": user_data.cookie_honkai3rd,
                "cookie_starrail": user_data.cookie_starrail,
                "has_genshin": "true" if user.has_genshin else "false",
                "has_honkai": "true" if user.has_honkai3rd else "false",
                "has_starrail": "true" if user.has_starrail else "false",
            }
            if gt_challenge is not None:
                payload.update(
                    {
                        "geetest_genshin": gt_challenge.genshin,
                        "geetest_honkai3rd": gt_challenge.honkai3rd,
                        "geetest_starrail": gt_challenge.starrail,
                    }
                )
            async with aiohttp.ClientSession() as session:
                async with session.post(url=host + "/daily-reward", json=payload) as resp:
                    if resp.status == 200:
                        result: dict[str, str] = await resp.json()
                        message = result.get("message", "Remote API sign-in failed")
                        return message
                    else:
                        raise Exception(f"Sign-in failed for {host}, HTTP status code: {resp.status}")

    @classmethod
    async def _send_message(cls, bot: commands.Bot, user: ScheduleDailyCheckin, message: str):
        try:
            _id = user.discord_channel_id
            channel = bot.get_channel(_id) or await bot.fetch_channel(_id)
            if user.is_mention is False and "Cookie has expired" not in message:
                _user = await bot.fetch_user(user.discord_id)
                await channel.send(embed=EmbedTemplate.normal(f"[Automatic Sign-in] {_user.name}: {message}"))
            else:
                await channel.send(f"<@{user.discord_id}>", embed=EmbedTemplate.normal(f"[Automatic Sign-in] {message}"))
        except (
            discord.Forbidden,
            discord.NotFound,
            discord.InvalidData,
        ) as e:
            LOG.Except(f"Failed to send message during automatic sign-in. Remove this user {LOG.User(user.discord_id)}: {e}")
            await Database.delete_instance(user)
        except Exception as e:
            sentry_sdk.capture_exception(e)
