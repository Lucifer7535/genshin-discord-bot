from datetime import datetime, timedelta

import genshin

from database import Database, GenshinScheduleNotes
from utility import EmbedTemplate

from ... import parse_genshin_notes
from .common import CheckResult, cal_next_check_time, get_realtime_notes


async def check_genshin_notes(user: GenshinScheduleNotes) -> CheckResult | None:
    try:
        notes = await get_realtime_notes(user)
    except Exception as e:
        return CheckResult("An error occurred when bot automatically checked instant notes. Please check again after some time.", EmbedTemplate.error(e))  # noqa

    if not isinstance(notes, genshin.models.Notes):
        return None

    msg = await check_threshold(user, notes)
    embed = await parse_genshin_notes(notes, short_form=True)
    return CheckResult(msg, embed)


async def check_threshold(user: GenshinScheduleNotes, notes: genshin.models.Notes) -> str:
    msg = ""
    next_check_time: list[datetime] = [datetime.now() + timedelta(days=1)]

    if isinstance(user.threshold_resin, int):
        if notes.remaining_resin_recovery_time <= timedelta(
            hours=user.threshold_resin, seconds=10
        ):
            msg += (
                "The resin is full!\n" if notes.remaining_resin_recovery_time <= timedelta(0) else "The resin is almost full!\n"
            )
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if notes.current_resin >= notes.max_resin
            else cal_next_check_time(notes.remaining_resin_recovery_time, user.threshold_resin)
        )
    if isinstance(user.threshold_currency, int):
        if notes.remaining_realm_currency_recovery_time <= timedelta(
            hours=user.threshold_currency, seconds=10
        ):
            msg += (
                "Realm currency is full!\n"
                if notes.remaining_realm_currency_recovery_time <= timedelta(0)
                else "Realm currency is almost full!\n"
            )
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if notes.current_realm_currency >= notes.max_realm_currency
            else cal_next_check_time(
                notes.remaining_realm_currency_recovery_time,
                user.threshold_currency,
            )
        )
    if (
        isinstance(user.threshold_transformer, int)
        and notes.remaining_transformer_recovery_time is not None
    ):
        if notes.remaining_transformer_recovery_time <= timedelta(
            hours=user.threshold_transformer, seconds=10
        ):
            msg += (
                "The parametric transformer has been reset!\n"
                if notes.remaining_transformer_recovery_time <= timedelta(0)
                else "The parametric transformer is about to be reset!\n"
            )
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if notes.remaining_transformer_recovery_time.total_seconds() <= 5
            else cal_next_check_time(
                notes.remaining_transformer_recovery_time,
                user.threshold_transformer,
            )
        )
    if isinstance(user.threshold_expedition, int) and len(notes.expeditions) > 0:
        longest_expedition = max(notes.expeditions, key=lambda epd: epd.remaining_time)
        if longest_expedition.remaining_time <= timedelta(
            hours=user.threshold_expedition, seconds=10
        ):
            msg += (
                "Exploration and dispatch are finished!\n" if longest_expedition.remaining_time <= timedelta(0) else "Exploartion and dispatch is about to be completed!\n" # noqa
            )
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if longest_expedition.finished is True
            else cal_next_check_time(longest_expedition.remaining_time, user.threshold_expedition)
        )
    if isinstance(user.check_commission_time, datetime):
        if datetime.now() >= user.check_commission_time:
            if not notes.claimed_commission_reward:
                msg += "Today's commission tasks has not been completed!\n"
            user.check_commission_time += timedelta(days=1)
        next_check_time.append(user.check_commission_time)

    check_time = min(next_check_time)
    if len(msg) > 0:
        check_time = max(check_time, datetime.now() + timedelta(minutes=60))
    user.next_check_time = check_time
    await Database.insert_or_replace(user)

    return msg
