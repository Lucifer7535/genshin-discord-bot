import io
import json
from typing import Tuple

import discord
from honkairail.src.tools.modalV2 import StarRailApiDataV2
from hsrcard.hsr import HonkaiCard
from mihomo import MihomoAPI, StarrailInfoParsed
from mihomo import tools as mihomo_tools

from database import Database, StarrailShowcase


class Showcase:
    def __init__(self, uid: int) -> None:
        self.uid = uid
        self.client = MihomoAPI()
        self.data: StarrailInfoParsed
        self.is_cached_data: bool = False

    async def load_data(self) -> None:
        srshowcase = await Database.select_one(
            StarrailShowcase, StarrailShowcase.uid.is_(self.uid)
        )
        cached_data: StarrailInfoParsed | None = None
        if srshowcase:
            cached_data = srshowcase.data
        try:
            new_data = await self.client.fetch_user(self.uid)
        except Exception as e:
            if cached_data is None:
                raise e from e
            else:
                self.data = cached_data
                self.is_cached_data = True
        else:
            if cached_data is not None:
                new_data = mihomo_tools.merge_character_data(new_data, cached_data)
            self.data = mihomo_tools.remove_duplicate_character(new_data)
            await Database.insert_or_replace(StarrailShowcase(self.uid, self.data))

    def get_player_overview_embed(self) -> discord.Embed:
        player = self.data.player

        description = (
            f"「{player.signature}」\n"
            f"Player's level:{player.level}\n"
            f"Characters: {player.characters}\n"
            f"Achievements achieved: {player.achievements}\n"
        )

        if self.is_cached_data is True:
            description += "(Currently, the API cannot be connected.)\n"

        embed = discord.Embed(title=player.name, description=description)
        embed.set_thumbnail(url=self.client.get_icon_url(player.avatar.icon))

        if len(self.data.characters) > 0:
            icon = self.data.characters[0].portrait
            embed.set_image(url=self.client.get_icon_url(icon))

        embed.set_footer(text=f"UID：{player.uid}")

        return embed

    async def get_character_card_embed_file(
        self, index: int
    ) -> Tuple[discord.Embed, discord.File]:
        """Retrieve character card data."""

        embed = self.get_default_embed(index)
        embed.set_thumbnail(url=None)

        data_dict = self.data.dict(by_alias=True)
        data_dict["player"]["space_info"] = {}
        data_hsrcard = StarRailApiDataV2.parse_raw(json.dumps(data_dict, ensure_ascii=False))

        async with HonkaiCard(lang="cht") as card_creater:
            result = await card_creater.creat(self.uid, data_hsrcard, index)
            image = result.card[0].card

        fp = io.BytesIO()
        image = image.convert("RGB")
        image.save(fp, "jpeg", optimize=True, quality=90)
        fp.seek(0)

        embed.set_image(url="attachment://image.jpeg")
        file = discord.File(fp, "image.jpeg")
        return (embed, file)

    def get_character_stat_embed(self, index: int) -> discord.Embed:
        embed = self.get_default_embed(index)
        embed.title = (embed.title + " Character panel") if embed.title is not None else "Character panel"

        character = self.data.characters[index]

        embed.add_field(
            name="Role information",
            value=f"Star Soul:{character.eidolon}\n" + f"Level: LV. {character.level}\n",
        )

        if character.light_cone is not None:
            light_cone = character.light_cone
            embed.add_field(
                name=f"{light_cone.rarity}★ {light_cone.name}",
                value=f"Shadowing:{light_cone.superimpose} Floors\nlevel：Lv. {light_cone.level}",
            )

        embed.add_field(
            name="Skill",
            value="\n".join(
                f"{trace.type_text}：Lv. {trace.level}"
                for trace in character.traces
                if trace.type_text != "" and trace.type_text != "Secret Technique"
            ),
            inline=False,
        )

        attr_dict = {
            "Health": [0.0, 0.0],
            "Attack": [0.0, 0.0],
            "Defense": [0.0, 0.0],
            "Speed": [0.0, 0.0],
            "Critical Rate": [5.0, 0.0],
            "Critical Damage": [50.0, 0.0],
            "Energy Recovery Efficiency": [100.0, 0.0],
        }
        for stat in character.attributes:
            if stat.name not in attr_dict:
                attr_dict[stat.name] = [0.0, 0.0]
            attr_dict[stat.name][0] += stat.value * 100 if stat.is_percent else stat.value

        for stat in character.additions:
            if stat.name not in attr_dict:
                attr_dict[stat.name] = [0.0, 0.0]
            attr_dict[stat.name][1] += stat.value * 100 if stat.is_percent else stat.value

        # Apply damage increase to all damage increase attributes
        if "Damage Increase" in attr_dict:
            v = attr_dict["Damage Increase"][0] + attr_dict["Damage Increase"][1]
            del attr_dict["Damage Increase"]
            for key in attr_dict:
                if "Damage Increase" in key:
                    attr_dict[key][1] += v

        value = ""
        for k, v in attr_dict.items():
            value += f"{k}: {round(v[0] + v[1], 1)}\n"

        embed.add_field(name="Attribute panel", value=value, inline=False)

        return embed

    def get_relic_stat_embed(self, index: int) -> discord.Embed:

        embed = self.get_default_embed(index)
        embed.title = (embed.title + " Relic") if embed.title is not None else "Relic"

        character = self.data.characters[index]
        if character.relics is None:
            return embed

        for relic in character.relics:
            name = (
                relic.main_affix.name.removesuffix("Damage Increase").removesuffix("Efficiency").removesuffix("Bonus")
            )
            value = f"★{relic.rarity}{name}+{relic.main_affix.displayed_value}\n"
            for prop in relic.sub_affixes:
                value += f"{prop.name}+{prop.displayed_value}\n"

            embed.add_field(name=relic.name, value=value)

        return embed

    def get_relic_score_embed(self, index: int) -> discord.Embed:
        embed = self.get_default_embed(index)
        embed.title = (embed.title + "Number of entry") if embed.title is not None else "Number of entry"

        character = self.data.characters[index]
        relics = character.relics
        if relics is None:
            return embed

        substat_sum: dict[str, float] = {
            "Attack power": 0.0,
            "life value": 0.0,
            "Defense": 0.0,
            "speed": 0.0,
            "Crit rate": 0.0,
            "Crit damage": 0.0,
            "Effect hit": 0.0,
            "Effect": 0.0,
            "Broken special attack": 0.0,
        }
        crit_value: float = 0.0

        base_hp = float(
            next(s.value for s in character.attributes if s.name == "life value")
        )  # Base health value
        base_atk = float(
            next(s.value for s in character.attributes if s.name == "Attack power")
        )  # Base attack value
        base_def = float(
            next(s.value for s in character.attributes if s.name == "Defense")
        )  # Base defense value

        for relic in relics:
            main = relic.main_affix
            if main.name == "Crit rate":
                crit_value += float(main.value) * 100 * 2
            if main.name == "Crit damage":
                crit_value += float(main.value) * 100
            for prop in relic.sub_affixes:
                v = prop.displayed_value
                if v is None:
                    continue
                match prop.name:
                    case "life value":
                        p = float(v.removesuffix("%")) if v.endswith("%") else float(v) / base_hp
                        substat_sum["life value"] += p / 3.89
                    case "Attack power":
                        p = float(v.removesuffix("%")) if v.endswith("%") else float(v) / base_atk
                        substat_sum["Attack power"] += p / 3.89
                    case "Defense":
                        p = float(v.removesuffix("%")) if v.endswith("%") else float(v) / base_def
                        substat_sum["Defense"] += p / 4.86
                    case "speed":
                        substat_sum["speed"] += float(v) / 2.3
                    case "Crit rate":
                        p = float(v.removesuffix("%"))
                        crit_value += p * 2.0
                        substat_sum["Crit rate"] += p / 2.92
                    case "Crit damage":
                        p = float(v.removesuffix("%"))
                        crit_value += p
                        substat_sum["Crit damage"] += p / 5.83
                    case "Effect hit":
                        substat_sum["Effect hit"] += float(v.removesuffix("%")) / 3.89
                    case "Effect":
                        substat_sum["Effect"] += float(v.removesuffix("%")) / 3.89
                    case "Broken special attack":
                        substat_sum["Broken special attack"] += float(v.removesuffix("%")) / 5.83
        embed.add_field(
            name="Number of entry",
            value="\n".join(
                [f"{k.ljust(4, '　')}：{round(v, 1)}" for k, v in substat_sum.items() if v > 0]
            ),
        )

        def sum_substat(name: str, *args: str) -> str:
            total = 0.0
            for arg in args:
                total += substat_sum[arg]
            return f"{name.ljust(4, '　')}：{round(total, 1)}\n" if total > 4 * len(args) else ""

        embed_value = f"Double violence {round(crit_value)} 分\n"
        embed_value += sum_substat("Bilateral violence", "Attack power", "Crit rate", "Crit damage")
        embed_value += sum_substat("Double Storm", "Attack power", "speed", "Crit rate", "Crit damage")
        embed_value += sum_substat("Offensive", "Attack power", "Effect hit", "Crit rate", "Crit damage")
        embed_value += sum_substat("Bilateral storm", "life value", "speed", "Crit rate", "Crit damage")
        embed_value += sum_substat("Species", "life value", "Attack power", "speed", "Crit rate", "Crit damage")
        embed_value += sum_substat("Speed resistance", "life value", "speed", "Effect")
        embed_value += sum_substat("Live speed", "life value", "Defense", "speed")
        embed_value += sum_substat("Anti -speed resistance", "Defense", "speed", "Effect")
        embed_value += sum_substat("Anti -speed resistance", "Defense", "speed", "Effect hit", "Effect")

        embed.add_field(name="General Cord Statistics", value=embed_value)

        return embed

    def get_default_embed(self, index: int) -> discord.Embed:

        character = self.data.characters[index]
        color = {
            "physics": 0xC5C5C5,
            "fire": 0xF4634E,
            "ice": 0x72C2E6,
            "thunder": 0xDC7CF4,
            "Wind": 0x73D4A4,
            "quantum": 0x9590E4,
            "Virtual number": 0xF7E54B,
        }
        embed = discord.Embed(
            title=f"{character.rarity}★ {character.name}",
            color=color.get(character.element.name),
        )
        embed.set_thumbnail(url=self.client.get_icon_url(character.icon))

        player = self.data.player
        embed.set_author(
            name=f"{player.name} Role display cabinet",
            icon_url=self.client.get_icon_url(player.avatar.icon),
        )
        embed.set_footer(text=f"{player.name}．Lv. {player.level}．UID: {player.uid}")

        return embed
