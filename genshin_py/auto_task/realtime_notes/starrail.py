from datetime import datetime, timedelta

import genshin

from database import Database, StarrailScheduleNotes
from utility import EmbedTemplate

from ... import parse_starrail_notes
from .common import CheckResult, cal_next_check_time, get_realtime_notes


async def check_starrail_notes(user: StarrailScheduleNotes) -> CheckResult | None:
    try:
        notes = await get_realtime_notes(user)
    except Exception as e:
        return CheckResult("An error occurred during the automatic check for real-time notes on Star Rail. Expected to check again in 5 hours.", EmbedTemplate.error(e)) # noqa

    if not isinstance(notes, genshin.models.StarRailNote):
        return None

    msg = await check_threshold(user, notes)
    embed = await parse_starrail_notes(notes, short_form=True)
    return CheckResult(msg, embed)


async def check_threshold(user: StarrailScheduleNotes, notes: genshin.models.StarRailNote) -> str:
    msg = ""
    next_check_time: list[datetime] = [datetime.now() + timedelta(days=1)]

    if isinstance(user.threshold_power, int):
        if notes.stamina_recover_time <= timedelta(hours=user.threshold_power):
            msg += "Exploration power is full!" if notes.stamina_recover_time <= timedelta(0) else "Exploration power is about to be full!" # noqa
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if notes.current_stamina >= notes.max_stamina
            else cal_next_check_time(notes.stamina_recover_time, user.threshold_power)
        )
    if isinstance(user.threshold_expedition, int) and len(notes.expeditions) > 0:
        longest_expedition = max(notes.expeditions, key=lambda epd: epd.remaining_time)
        if longest_expedition.remaining_time <= timedelta(hours=user.threshold_expedition):
            msg += "The commission is already completed!" if longest_expedition.remaining_time <= timedelta(0) else "The commission is about to be completed!" # noqa
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if longest_expedition.finished is True
            else cal_next_check_time(longest_expedition.remaining_time, user.threshold_expedition)
        )
    if isinstance(user.check_daily_training_time, datetime):
        if datetime.now() >= user.check_daily_training_time:
            if notes.current_train_score < notes.max_train_score:
                msg += "Today's daily training is not yet completed!"
            user.check_daily_training_time += timedelta(days=1)
        next_check_time.append(user.check_daily_training_time)
    if isinstance(user.check_universe_time, datetime):
        if datetime.now() >= user.check_universe_time:
            if notes.current_rogue_score < notes.max_rogue_score:
                msg += "The simulation universe for this week has not been completed yet!"
            user.check_universe_time += timedelta(weeks=1)
        next_check_time.append(user.check_universe_time)
    if isinstance(user.check_echoofwar_time, datetime):
        if datetime.now() >= user.check_echoofwar_time:
            if notes.remaining_weekly_discounts > 0:
                msg += "The historical echoes for this week have not been completed yet!"
            user.check_echoofwar_time += timedelta(weeks=1)
        next_check_time.append(user.check_echoofwar_time)

    check_time = min(next_check_time)
    if len(msg) > 0:
        check_time = max(check_time, datetime.now() + timedelta(minutes=60))
    user.next_check_time = check_time
    await Database.insert_or_replace(user)

    return msg
