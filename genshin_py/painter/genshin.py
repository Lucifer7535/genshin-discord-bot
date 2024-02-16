import random
from io import BytesIO
from pathlib import Path
from typing import Sequence

import aiohttp
import enkanetwork
import genshin
from PIL import Image, ImageDraw

from database.dataclass import spiral_abyss
from utility import get_server_name

from .common import draw_avatar, draw_text

__all__ = ["draw_abyss_card", "draw_exploration_card", "draw_record_card"]


def draw_rounded_rect(img: Image.Image, pos: tuple[float, float, float, float], **kwargs):
    transparent = Image.new("RGBA", img.size, 0)
    draw = ImageDraw.Draw(transparent, "RGBA")
    draw.rounded_rectangle(pos, **kwargs)
    img.paste(Image.alpha_composite(img, transparent))


def draw_basic_card(
    avatar_bytes: bytes, uid: int, user_stats: genshin.models.PartialGenshinUserStats
) -> Image.Image:
    img: Image.Image = Image.open(f"data/image/record_card/{random.randint(1, 12)}.jpg")
    img = img.convert("RGBA")

    avatar: Image.Image = Image.open(BytesIO(avatar_bytes)).resize((250, 250))
    draw_avatar(img, avatar, (70, 210))

    draw_rounded_rect(img, (340, 270, 990, 460), radius=30, fill=(0, 0, 0, 120))
    draw_rounded_rect(img, (90, 520, 990, 1810), radius=30, fill=(0, 0, 0, 120))

    info = user_stats.info
    draw_text(
        img, (665, 335), info.nickname, "SourceHanSerifTC-Bold.otf", 88, (255, 255, 255, 255), "mm"
    )
    draw_text(
        img,
        (665, 415),
        f"{get_server_name(info.server)}  Lv.{info.level}  UID:{uid}",
        "SourceHanSansTC-Medium.otf",
        40,
        (255, 255, 255, 255),
        "mm",
    )

    return img


def draw_record_card(
    avatar_bytes: bytes, uid: int, user_stats: genshin.models.PartialGenshinUserStats
) -> BytesIO:
    img = draw_basic_card(avatar_bytes, uid, user_stats)

    white = (255, 255, 255, 255)
    grey = (230, 230, 230, 255)

    s = user_stats.stats
    stat_list = [
        (s.days_active, "Active Days"),
        (s.achievements, "Achievements"),
        (s.characters, "Number of\n   Characters"),
        (s.anemoculi, "Anemoculi"),
        (s.geoculi, "Geoculi"),
        (s.electroculi, "Electroculi"),
        (s.dendroculi, "Dendroculi"),
        (s.hydroculi, "Hydroculi"),
        (s.unlocked_waypoints, '\nUnlocked\nWaypoints'),
        (s.unlocked_domains, "\nUnlocked\nDomains"),
        (s.spiral_abyss, "\nSpiral\nAbyss"),
        (s.luxurious_chests, "\nLuxurious\nChests"),
        (s.precious_chests, "\nPrecious\nChests"),
        (s.exquisite_chests, "\nExquisite\nChests"),
        (s.common_chests, "\nCommon\nChests"),
        (s.remarkable_chests, "\nRemarkable\nChests"),
    ]

    for n, stat in enumerate(stat_list):
        column = int(n % 3)
        row = int(n / 3)
        draw_text(
            img,
            (245 + column * 295, 630 + row * 200),
            str(stat[0]),
            "SourceHanSansTC-Bold.otf",
            80,
            white,
            "mm",
        )
        draw_text(
            img,
            (245 + column * 295, 700 + row * 200),
            str(stat[1]),
            "SourceHanSansTC-Regular.otf",
            40,
            grey,
            "mm",
        )

    img = img.convert("RGB")
    fp = BytesIO()
    img.save(fp, "jpeg", optimize=True, quality=50)
    return fp


def draw_exploration_card(
    avatar_bytes: bytes, uid: int, user_stats: genshin.models.PartialGenshinUserStats
) -> BytesIO:
    img = draw_basic_card(avatar_bytes, uid, user_stats)

    white = (255, 255, 255, 255)
    grey = (230, 230, 230, 255)

    explored_list = {
        1: ["Mondstadt", 0],
        2: ["Liyue", 0],
        3: ["Dragonspine", 0],
        4: ["Inazuma", 0],
        5: ["Enkanomiya", 0],
        6: ["The Chasm", 0],
        7: ["          The Chasm:\n   Underground Mines", 0],
        8: ["Sumeru", 0],
        9: ["Fontaine", 0],
        10: ["     Chenyu Vale:\n       Upper Vale", 0],
        11: ["         Chenyu Vale:\n    Southern Mountain", 0]
    }
    offering_list = [["  Frostbearing\n         Tree", 0], ["  Sacred Sakura's\n           Favor", 0], ["  Lumenstone\n     Adjuvant", 0], ["Tree of Dreams", 0], ["Fountain of Lucine", 0]] # noqa
    large_font_size = 35
    for e in user_stats.explorations:
        if e.id not in explored_list:
            continue
        explored_list[e.id][1] = e.explored

        if e.id == 3 and len(e.offerings) >= 1:
            offering_list[0][1] = e.offerings[0].level
        if e.id == 4 and len(e.offerings) >= 2:
            offering_list[1][1] = e.offerings[0].level
        if e.id == 6 and len(e.offerings) >= 1:
            offering_list[2][1] = e.offerings[0].level
        if e.id == 8 and len(e.offerings) >= 2:
            offering_list[3][1] = e.offerings[0].level
        if e.id == 9 and len(e.offerings) >= 2:
            offering_list[4][1] = e.offerings[0].level

    stat_list: list[tuple[str, float, str]] = []
    for id, e in explored_list.items():
        if len(e[0]) > 12:
            font_size = large_font_size
        else:
            font_size = 41
        stat_list.append(("Exploration", e[1], e[0], font_size))
    for o in offering_list:
        if len(o[0]) > 12:
            font_size = large_font_size
        else:
            font_size = 37
        stat_list.append(("Level", o[1], o[0], font_size))

    for n, stat in enumerate(stat_list):
        column = int(n % 3)
        row = int(n / 3)
        draw_text(
            img,
            (245 + column * 295, 590 + row * 205),
            stat[0],
            "SourceHanSansTC-Bold.otf",
            30,
            grey,
            "mm",
        )
        draw_text(
            img,
            (245 + column * 295, 639 + row * 205),
            f"{stat[1]:g}",
            "SourceHanSansTC-Bold.otf",
            80,
            white,
            "mm",
        )
        draw_text(
            img,
            (245 + column * 295, 720 + row * 205),
            stat[2],
            "SourceHanSansTC-Regular.otf",
            stat[3],
            grey,
            "mm",
        )

    img = img.convert("RGB")
    fp = BytesIO()
    img.save(fp, "jpeg", optimize=True, quality=50)
    return fp


async def draw_character(
    img: Image.Image,
    character: genshin.models.AbyssCharacter,
    size: tuple[int, int],
    pos: tuple[int, int],
):
    background = (
        Image.open(f"data/image/character/char_{character.rarity}star_bg.png")
        .convert("RGBA")
        .resize(size)
    )
    avatar_file = Path(f"data/image/character/{character.id}.png")
    if avatar_file.exists() is False:
        avatar_img: bytes | None = None
        async with aiohttp.ClientSession() as session:
            try:
                enka_cdn = enkanetwork.Assets.character(character.id).images.icon.url  # type: ignore
            except Exception:
                pass
            else:
                async with session.get(enka_cdn) as resp:
                    if resp.status == 200:
                        avatar_img = await resp.read()
            if avatar_img is None:
                icon_name = character.icon.split("/")[-1]
                ambr_url = "https://api.ambr.top/assets/UI/" + icon_name
                async with session.get(ambr_url) as resp:
                    if resp.status == 200:
                        avatar_img = await resp.read()
        if avatar_img is None:
            return
        else:
            with open(avatar_file, "wb") as fp:
                fp.write(avatar_img)
    avatar = Image.open(avatar_file).convert("RGBA").resize((size[0], size[0]))
    img.paste(background, pos, background)
    img.paste(avatar, pos, avatar)


def draw_abyss_star(
    img: Image.Image, number: int, size: tuple[int, int], pos: tuple[float, float]
):
    star = Image.open("data/image/spiral_abyss/star.png").convert("RGBA").resize(size)
    pad = 5
    upper_left = (pos[0] - number / 2 * size[0] - (number - 1) * pad, pos[1] - size[1] / 2)
    for i in range(0, number):
        img.paste(star, (int(upper_left[0] + i * (size[0] + 2 * pad)), int(upper_left[1])), star)


async def draw_abyss_card(
    abyss_floor: genshin.models.Floor,
    characters: Sequence[spiral_abyss.CharacterData] | None = None,
) -> BytesIO:
    img = Image.open("data/image/spiral_abyss/background_blur.jpg")
    img = img.convert("RGBA")

    character_size = (172, 210)
    character_pad = 8
    draw_text(
        img,
        (1050, 145),
        f"{abyss_floor.floor}",
        "SourceHanSansTC-Bold.otf",
        85,
        (50, 50, 50),
        "mm",
    )
    for i, chamber in enumerate(abyss_floor.chambers):
        draw_abyss_star(img, chamber.stars, (70, 70), (1050, 500 + i * 400))
        for j, battle in enumerate(chamber.battles):
            middle = 453 + j * 1196
            left_upper = (
                int(
                    middle
                    - len(battle.characters) / 2 * character_size[0]
                    - (len(battle.characters) - 1) * character_pad
                ),
                395 + i * 400,
            )
            for k, character in enumerate(battle.characters):
                x = left_upper[0] + k * (character_size[0] + 2 * character_pad)
                y = left_upper[1]
                await draw_character(img, character, (172, 210), (x, y))
                if characters is not None:
                    constellation = next(
                        (c.constellation for c in characters if c.id == character.id), 0
                    )
                    text = f"C{constellation} Lv. {character.level}"
                else:
                    text = f"Lv. {character.level}"
                draw_text(
                    img,
                    (x + character_size[0] / 2, y + character_size[1] * 0.90),
                    text,
                    "SourceHanSansTC-Regular.otf",
                    30,
                    (50, 50, 50),
                    "mm",
                )
    img = img.convert("RGB")
    fp = BytesIO()
    img.save(fp, "jpeg", optimize=True, quality=40)
    return fp
