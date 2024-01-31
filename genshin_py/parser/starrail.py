import discord
import genshin

from database import Database, User
from utility import get_day_of_week, get_server_name


async def parse_starrail_notes(
    notes: genshin.models.StarRailNote,
    user: discord.User | discord.Member | None = None,
    *,
    short_form: bool = False,
) -> discord.Embed:
    stamina_title = f"Current Stamina: {notes.current_stamina}/{notes.max_stamina}"
    if notes.current_reserve_stamina > 0:
        stamina_title += f" + {notes.current_reserve_stamina}"
    if notes.current_stamina >= notes.max_stamina:
        recovery_time = "Already Full!"
    else:
        day_msg = get_day_of_week(notes.stamina_recovery_time)
        recovery_time = f"{day_msg} {notes.stamina_recovery_time.strftime('%H:%M')}"
    stamina_msg = f"Recovery Time: {recovery_time}\n"

    stamina_msg += f"Daily Training: {notes.current_train_score} / {notes.max_train_score}\n"
    stamina_msg += f"Simulated Universe: {notes.current_rogue_score} / {notes.max_rogue_score}\n"
    stamina_msg += f"Echoing Conches: Remaining {notes.remaining_weekly_discounts} times\n"

    exped_finished = 0
    exped_msg = ""
    for expedition in notes.expeditions:
        exped_msg += f"． {expedition.name}："
        if expedition.finished is True:
            exped_finished += 1
            exped_msg += "Completed\n"
        else:
            day_msg = get_day_of_week(expedition.completion_time)
            exped_msg += f"{day_msg} {expedition.completion_time.strftime('%H:%M')}\n"
    if short_form is True and len(notes.expeditions) > 0:
        longest_expedition = max(notes.expeditions, key=lambda epd: epd.remaining_time)
        if longest_expedition.finished is True:
            exped_msg = "． Completion Time: Completed\n"
        else:
            day_msg = get_day_of_week(longest_expedition.completion_time)
            exped_msg = (
                f"． Completion Time: {day_msg} {longest_expedition.completion_time.strftime('%H:%M')}\n"
            )

    exped_title = f"Expedition finished: {exped_finished}/{len(notes.expeditions)}"

    stamina = notes.current_stamina
    max_half = notes.max_stamina / 2
    color = (
        0x28C828 + 0x010000 * int(0xA0 * stamina / max_half)
        if stamina < max_half
        else 0xC8C828 - 0x000100 * int(0xA0 * (stamina - max_half) / max_half)
    )

    embed = discord.Embed(color=color)
    embed.add_field(name=stamina_title, value=stamina_msg, inline=False)
    if exped_msg != "":
        embed.add_field(name=exped_title, value=exped_msg, inline=False)

    if user is not None:
        _u = await Database.select_one(User, User.discord_id.is_(user.id))
        uid = str(_u.uid_starrail if _u else "")
        embed.set_author(
            name=f"Star Rail {get_server_name(uid[0])} {uid}",
            icon_url=user.display_avatar.url,
        )
    return embed


def parse_starrail_diary(diary: genshin.models.StarRailDiary, month: int) -> discord.Embed:
    ...


def parse_starrail_character(character: genshin.models.StarRailDetailCharacter) -> discord.Embed:
    color = {
        "physical": 0xC5C5C5,
        "fire": 0xF4634E,
        "ice": 0x72C2E6,
        "lightning": 0xDC7CF4,
        "wind": 0x73D4A4,
        "quantum": 0x9590E4,
        "imaginary": 0xF7E54B,
    }
    embed = discord.Embed(color=color.get(character.element.lower()))
    embed.set_thumbnail(url=character.icon)
    embed.add_field(
        name=f"★{character.rarity} {character.name}",
        inline=True,
        value = f"Constellation: {character.rank}\nLevel: Lv. {character.level}"
    )
    if character.equip:
        lightcone = character.equip
        embed.add_field(
            name = f"Light Cone: {lightcone.name}",
            inline = True,
            value = f"Constellation: {lightcone.rank} Level\nLevel: Lv. {lightcone.level}"
        )

    if character.rank > 0:
        number = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6"}
        msg = "\n".join([f"Layer {number[rank.pos]}: {rank.name}" for rank in character.ranks if rank.is_unlocked])
        embed.add_field(name="Constellations", inline=False, value=msg)

    if len(character.relics) > 0:
        pos_name = {1: "Head", 2: "Hands", 3: "Torso", 4: "Legs"}
        msg = "\n".join(
            [
                f"{pos_name.get(relic.pos)}：★{relic.rarity} {relic.name}"
                for relic in character.relics
            ]
        )
        embed.add_field(name="Artifact", inline=False, value=msg)

    if len(character.ornaments) > 0:
        ornament_positions = {5: "Sub-Space Beacon", 6: "Link Loop"}
        msg = "\n".join(
            [
                f"{ornament_positions.get(ornament.pos)}: ★{ornament.rarity} {ornament.name}"
                for ornament in character.ornaments
            ]
        )
        embed.add_field(name="Ornaments", inline=False, value=msg)

    return embed


def parse_starrail_hall_overview(hall: genshin.models.StarRailChallenge) -> discord.Embed:
    has_crown: bool = hall.total_battles == 10 and hall.total_stars == 30
    desc: str = f"{hall.begin_time.datetime.strftime('%Y.%m.%d')} ~ {hall.end_time.datetime.strftime('%Y.%m.%d')}\n"
    desc += f"Progress: {hall.max_floor}\n"
    desc += f"Battles: {'👑 (10)' if has_crown else hall.total_battles} ★: {hall.total_stars}\n"
    embed = discord.Embed(description=desc, color=0x934151)
    return embed
