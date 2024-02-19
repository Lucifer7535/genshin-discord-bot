from typing import Sequence, Union, Tuple, List

import discord
import genshin

from database import Database, User
from utility import emoji, get_day_of_week, get_server_name


def parse_genshin_abyss_overview(abyss: genshin.models.SpiralAbyss) -> discord.Embed:
    result = discord.Embed(
        description=(
            f'Season {abyss.season}: {abyss.start_time.astimezone().strftime("%Y.%m.%d")} ~ '
            f'{abyss.end_time.astimezone().strftime("%Y.%m.%d")}'
        ),
        color=0x6959C1,
    )

    crowned: bool = (
        True
        if abyss.max_floor == "12-3" and abyss.total_stars == 36 and abyss.total_battles == 12
        else False
    )

    def get_character_rank(c: Sequence[genshin.models.AbyssRankCharacter]):
        return " " if len(c) == 0 else f"{c[0].name}：{c[0].value}"

    result.add_field(
        name=f'Max Floor Reached：{abyss.max_floor}　Battles：{"👑 (12)" if crowned else abyss.total_battles}　：{abyss.total_stars}★',
        value=f"[Most Kills] {get_character_rank(abyss.ranks.most_kills)}\n"
        f"[Strongest Strike] {get_character_rank(abyss.ranks.strongest_strike)}\n"
        f"[Most Damage Taken] {get_character_rank(abyss.ranks.most_damage_taken)}\n"
        f"[Most Bursts Used] {get_character_rank(abyss.ranks.most_bursts_used)}\n"
        f"[Most Skills Used] {get_character_rank(abyss.ranks.most_skills_used)}",
        inline=False,
    )
    return result


def parse_genshin_abyss_chamber(chamber: genshin.models.Chamber) -> str:
    chara_list: list[list[str]] = [[], []]
    for i, battle in enumerate(chamber.battles):
        for chara in battle.characters:
            chara_list[i].append(chara.name)
    return f'{".".join(chara_list[0])} ／\n{".".join(chara_list[1])}'


def parse_genshin_character(character: genshin.models.Character) -> discord.Embed:
    color = {
        "pyro": 0xFB4120,
        "electro": 0xBF73E7,
        "hydro": 0x15B1FF,
        "cryo": 0x70DAF1,
        "dendro": 0xA0CA22,
        "anemo": 0x5CD4AC,
        "geo": 0xFAB632,
    }
    embed = discord.Embed(color=color.get(character.element.lower()))
    embed.set_thumbnail(url=character.icon)
    embed.add_field(
        name=f"{character.rarity}★ {character.name}",
        inline=True,
        value=f"Constellation: {character.constellation}\nLevel: Lv.{character.level}\nFriendship: Lv.{character.friendship}"
    )

    weapon = character.weapon
    embed.add_field(
        name=f"{weapon.rarity}★ {weapon.name}",
        inline=True,
        value=f"Refinement: R{weapon.refinement}   Level: Lv.{weapon.level}"
    )

    if character.constellation > 0:
        number = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6"}
        msg = "\n".join(
            [
                f"C{number[constella.pos]} : {constella.name}"
                for constella in character.constellations
                if constella.activated
            ]
        )
        embed.add_field(name="Constellation", inline=False, value=msg)

    if len(character.artifacts) > 0:
        msg = "\n".join(
            [
                f"{artifact.pos_name}：{artifact.name} ({artifact.set.name})"
                for artifact in character.artifacts
            ]
        )
        embed.add_field(name="Artifacts", inline=False, value=msg)

    return embed


def parse_genshin_diary(diary: genshin.models.Diary, month: int) -> discord.Embed:
    d = diary.data
    embed = discord.Embed(
        title=f"{diary.nickname}'s Traveler Diary: {month}th month",
        description=f'Primogems income is {"increased" if d.current_primogems >= d.last_primogems else "decreased"} by {abs(d.primogems_rate)}%,' # noqa
              f'Mora income is {"increased" if d.current_mora >= d.last_mora else "decreased"} by {abs(d.mora_rate)}%',
        color=0xFD96F4,

    )
    embed.add_field(
        name="Obtained this month",
        value=f"{emoji.items.primogem} Primogems: {d.current_primogems} ({round(d.current_primogems/160)} {emoji.items.intertwined_fate})\n" # noqa
        f'{emoji.items.mora} Mora: {format(d.current_mora, ",")}',
    )
    embed.add_field(
        name="Obtained Last month",
        value=f"{emoji.items.primogem}Primogems: {d.last_primogems} ({round(d.last_primogems/160)}{emoji.items.intertwined_fate})\n" # noqa
        f'{emoji.items.mora}Mora：{format(d.last_mora, ",")}',
    )
    embed.add_field(name="\u200b", value="\u200b")

    for i in range(0, 2):
        msg = ""
        length = len(d.categories)
        for j in range(round(length / 2 * i), round(length / 2 * (i + 1))):
            msg += f"{d.categories[j].name[0:15]}: {d.categories[j].amount} ({d.categories[j].percentage}%)\n"
        embed.add_field(name=f"Primogem Income Breakdown {i+1}", value=msg, inline=True)
    embed.add_field(name="\u200b", value="\u200b")

    return embed


async def parse_genshin_notes(
    notes: genshin.models.Notes,
    *,
    user: Union[discord.User, discord.Member, None] = None,
    short_form: bool = False,
) -> discord.Embed:
    resin_title = f"{emoji.notes.resin}Current Original Resin: {notes.current_resin}/{notes.max_resin}\n"
    if notes.current_resin >= notes.max_resin:
        recover_time = "Already full!"
    else:
        day_msg = get_day_of_week(notes.resin_recovery_time)
        recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'
    resin_msg = f"{emoji.notes.resin}Full recovery time: {recover_time}\n"
    resin_msg += f"{emoji.notes.commission}Daily commission tasks:"
    resin_msg += (
        " Rewards claimed\n"
        if notes.claimed_commission_reward is True
        else "**Rewards not claimed yet**\n"
        if notes.max_commissions == notes.completed_commissions
        else f"{notes.max_commissions - notes.completed_commissions} commissions remaining\n"
    )
    if not short_form:
        resin_msg += (
            f"{emoji.notes.enemies_of_note}Weekly Boss Resin Discount: Remaining {notes.remaining_resin_discounts} times\n"
        )
    resin_msg += f"{emoji.notes.realm_currency}Current Realm Currency: {notes.current_realm_currency}/{notes.max_realm_currency}\n" # noqa
    if not short_form and notes.max_realm_currency > 0:
        if notes.current_realm_currency >= notes.max_realm_currency:
            recover_time = "Already full!"
        else:
            day_msg = get_day_of_week(notes.realm_currency_recovery_time)
            recover_time = f'{day_msg} {notes.realm_currency_recovery_time.strftime("%H:%M")}'
        resin_msg += f"{emoji.notes.realm_currency}Realm Currency recovery time: {recover_time}\n"
    if (t := notes.remaining_transformer_recovery_time) is not None:
        if t.days > 0:
            recover_time = f"{t.days} days remaining"
        elif t.hours > 0:
            recover_time = f"{t.hours} hours remaining"
        elif t.minutes > 0:
            recover_time = f"{t.minutes} minutes remaining"
        elif t.seconds > 0:
            recover_time = f"{t.seconds} seconds remaining"
        else:
            recover_time = "Available"
        resin_msg += f"{emoji.notes.transformer}Parameteric Transformation Device: {recover_time}\n"

    exped_finished = 0
    exped_msg = ""
    i = 1
    for expedition in notes.expeditions:
        exped_msg += f"．Character {i} - "
        if expedition.finished:
            exped_finished += 1
            exped_msg += "Completed\n"
        else:
            i += 1
            day_msg = get_day_of_week(expedition.completion_time)
            exped_msg += f'{day_msg} {expedition.completion_time.strftime("%H:%M")}\n'

    exped_title = f"{emoji.notes.expedition}Expedition Results: {exped_finished}/{len(notes.expeditions)}\n"

    r = notes.current_resin
    color = (
        0x28C828 + 0x010000 * int(0xA0 * r / 80)
        if r < 80
        else 0xC8C828 - 0x000100 * int(0xA0 * (r - 80) / 80)
    )
    embed = discord.Embed(color=color)

    if (not short_form) and (exped_msg != ""):
        embed.add_field(name=resin_title, value=resin_msg)
        embed.add_field(name=exped_title, value=exped_msg)
    else:
        embed.add_field(name=resin_title, value=(resin_msg + exped_title))

    if user is not None:
        _u = await Database.select_one(User, User.discord_id.is_(user.id))
        uid = str(_u.uid_genshin if _u else "")
        embed.set_author(
            name=f"{get_server_name(uid[0])} {uid}",
            icon_url=user.display_avatar.url,
        )
    return embed


async def parse_genshin_notes_command(
    notes: genshin.models.Notes,
    *,
    user: Union[discord.User, discord.Member, None] = None,
    short_form: bool = False,
) -> Tuple[discord.Embed, List[discord.Embed]]:
    main_embed = None
    expedition_embeds = []

    resin_title = f"{emoji.notes.resin}Current Original Resin: {notes.current_resin}/{notes.max_resin}\n"
    if notes.current_resin >= notes.max_resin:
        recover_time = "Already full!"
    else:
        day_msg = get_day_of_week(notes.resin_recovery_time)
        recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'
    resin_msg = f"{emoji.notes.resin}Full recovery time: {recover_time}\n"
    resin_msg += f"{emoji.notes.commission}Daily commission tasks:"
    resin_msg += (
        " Rewards claimed\n"
        if notes.claimed_commission_reward is True
        else "**Rewards not claimed yet**\n"
        if notes.max_commissions == notes.completed_commissions
        else f"{notes.max_commissions - notes.completed_commissions} commissions remaining\n"
    )
    if not short_form:
        resin_msg += (
            f"{emoji.notes.enemies_of_note}Weekly Boss Resin Discount: Remaining {notes.remaining_resin_discounts} times\n"
        )
    resin_msg += f"{emoji.notes.realm_currency}Current Realm Currency: {notes.current_realm_currency}/{notes.max_realm_currency}\n" # noqa
    if not short_form and notes.max_realm_currency > 0:
        if notes.current_realm_currency >= notes.max_realm_currency:
            recover_time = "Already full!"
        else:
            day_msg = get_day_of_week(notes.realm_currency_recovery_time)
            recover_time = f'{day_msg} {notes.realm_currency_recovery_time.strftime("%H:%M")}'
        resin_msg += f"{emoji.notes.realm_currency}Realm Currency recovery time: {recover_time}\n"
    if (t := notes.remaining_transformer_recovery_time) is not None:
        if t.days > 0:
            recover_time = f"{t.days} days remaining"
        elif t.hours > 0:
            recover_time = f"{t.hours} hours remaining"
        elif t.minutes > 0:
            recover_time = f"{t.minutes} minutes remaining"
        elif t.seconds > 0:
            recover_time = f"{t.seconds} seconds remaining"
        else:
            recover_time = "Available"
        resin_msg += f"{emoji.notes.transformer}Parameteric Transformation Device: {recover_time}\n"

    exped_finished = 0
    expedition_summary = ""
    expedition_embeds = []

    for expedition in notes.expeditions:
        if expedition.finished:
            exped_finished += 1
        else:
            character_icon_url = expedition.character_icon
            expedition_embed = discord.Embed(color=0xFF0000)
            expedition_embed.add_field(
                name=f"{emoji.notes.expedition} Expedition Remaining Time",
                value=f"Completion Time: {expedition.completion_time.strftime('%A %H:%M')}",
                inline=False,
            )
            expedition_embed.set_thumbnail(url=character_icon_url)
            expedition_embeds.append(expedition_embed)

    expedition_summary = discord.Embed(color=0x28C828)
    value = "Characters currently on expedition." if exped_finished == 0 else "Collect rewards in-game."
    expedition_summary.add_field(
        name=f"{emoji.notes.expedition} Expedition Completed：{exped_finished}/{len(notes.expeditions)}",
        value=value,
        inline=False,
    )

    all_embeds = [expedition_summary] + expedition_embeds

    r = notes.current_resin
    color = (
        0x28C828 + 0x010000 * int(0xA0 * r / 80)
        if r < 80
        else 0xC8C828 - 0x000100 * int(0xA0 * (r - 80) / 80)
    )
    main_embed = discord.Embed(color=color)

    main_embed.add_field(name=resin_title, value=(resin_msg))

    if user is not None:
        _u = await Database.select_one(User, User.discord_id.is_(user.id))
        uid = str(_u.uid_genshin if _u else "")
        main_embed.set_author(
            name=f"{get_server_name(uid[0])} {uid}",
            icon_url=user.display_avatar.url,
        )

    return main_embed, all_embeds
