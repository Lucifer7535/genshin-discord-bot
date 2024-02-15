import io
from datetime import datetime
from typing import Any

import discord
import enkanetwork

from database import Database, GenshinShowcase
from utility import emoji

from .api import EnkaAPI
from .enka_card import generate_image
from .request import fetch_enka_data

enka_assets = enkanetwork.Assets(lang=enkanetwork.Language.EN)


class Showcase:
    def __init__(self, uid: int) -> None:
        self.raw_data: dict[str, Any] | None = None
        self.data: enkanetwork.EnkaNetworkResponse
        self.uid: int = uid
        self.is_cached_data = False
        self.api_error_msg: str | None = None
        self.url: str = EnkaAPI.get_user_url(uid)
        self.image_buffers: list[io.BytesIO | None] = [None] * 25

    async def load_data(self) -> None:
        gshowcase = await Database.select_one(GenshinShowcase, GenshinShowcase.uid.is_(self.uid))
        if gshowcase is not None:
            self.raw_data = gshowcase.data

        if self.raw_data is None:
            self.raw_data = await fetch_enka_data(self.uid)
        else:
            refresh_timestamp = self.raw_data.get("timestamp", 0) + self.raw_data.get("ttl", 0)
            if datetime.now().timestamp() > refresh_timestamp:
                try:
                    self.raw_data = await fetch_enka_data(self.uid, self.raw_data)
                except Exception as e:
                    self.is_cached_data = True
                    self.api_error_msg = str(e)

        if self.is_cached_data is False:
            gshowcase = GenshinShowcase(self.uid, self.raw_data)
            await Database.insert_or_replace(gshowcase)

        self.data = enkanetwork.EnkaNetworkResponse.parse_obj(self.raw_data)

    def get_player_overview_embed(self) -> discord.Embed:
        player = self.data.player
        if self.raw_data is None or player is None:
            raise Exception("Player information does not exist")
        embed = discord.Embed(
            title=player.nickname,
            description=f"「{player.signature}」\n"
            f"Adventure Level: {player.level}\n"
            f"World Level: {player.world_level}\n"
            f"Achievements: {player.achievement}\n"
            f"Spiral Abyss: {player.abyss_floor}-{player.abyss_room}\n"
            f"Next Refresh Time: <t:{self.raw_data.get('timestamp', 0) + self.raw_data.get('ttl', 0)}:R>\n"
            + (f"({self.api_error_msg}, displayed data is cached)" if self.is_cached_data is True else ""),
        )

        if player.avatar and player.avatar.icon:
            embed.set_thumbnail(url=player.avatar.icon.url)

        if player.namecard.icon and player.namecard.banner:
            embed.set_image(url=player.namecard.banner.url)

        embed.set_footer(text=f"UID: {self.uid}")
        return embed

    def get_character_stat_embed(self, index: int) -> discord.Embed:
        embed = self.get_default_embed(index)
        embed.title = (embed.title + " Character panel") if embed.title is not None else "Character panel"
        if self.data.characters is None:
            return embed

        character = self.data.characters[index]

        skill_string = (
            f"{character.skills[0].level}/{character.skills[1].level}/{character.skills[-1].level}"
            if len(character.skills) >= 3
            else "?/?/?"
        )
        embed.add_field(
            name="Character Information",
            value=f"Constellations Unlocked: {character.constellations_unlocked}\n"
            f"Level: Lv. {character.level}\n"
            f"Talents: {skill_string}\n"
            f"Friendship Level: Lv. {character.friendship_level}",
        )

        weapon_list = [
            e for e in character.equipments if e.type == enkanetwork.EquipmentsType.WEAPON
        ]
        if len(weapon_list) > 0:
            weapon = weapon_list[0]
            embed.add_field(
                name=f"{weapon.detail.rarity}★ {weapon.detail.name}",
                value=f"Refinement: R{weapon.refinement}\n"
                f"Level: Lv. {weapon.level}\n"
                f"{self._get_statprop_sentence(weapon.detail.mainstats) if weapon.detail.mainstats else ''}\n"
                f"{self._get_statprop_sentence(weapon.detail.substats[0]) if len(weapon.detail.substats) > 0 else ''}",
            )

        stats = character.stats
        substat: str = "\n".join(
            [
                self._get_character_fightprop_sentence(stat_name, stat)
                for (stat_name, stat) in [
                    ("FIGHT_PROP_CRITICAL", stats.FIGHT_PROP_CRITICAL),
                    ("FIGHT_PROP_CRITICAL_HURT", stats.FIGHT_PROP_CRITICAL_HURT),
                    ("FIGHT_PROP_ELEMENT_MASTERY", stats.FIGHT_PROP_ELEMENT_MASTERY),
                    ("FIGHT_PROP_HEAL_ADD", stats.FIGHT_PROP_HEAL_ADD),
                    ("FIGHT_PROP_CHARGE_EFFICIENCY", stats.FIGHT_PROP_CHARGE_EFFICIENCY),
                    ("FIGHT_PROP_PHYSICAL_ADD_HURT", stats.FIGHT_PROP_PHYSICAL_ADD_HURT),
                    ("FIGHT_PROP_FIRE_ADD_HURT", stats.FIGHT_PROP_FIRE_ADD_HURT),
                    ("FIGHT_PROP_ELEC_ADD_HURT", stats.FIGHT_PROP_ELEC_ADD_HURT),
                    ("FIGHT_PROP_WATER_ADD_HURT", stats.FIGHT_PROP_WATER_ADD_HURT),
                    ("FIGHT_PROP_GRASS_ADD_HURT", stats.FIGHT_PROP_GRASS_ADD_HURT),
                    ("FIGHT_PROP_WIND_ADD_HURT", stats.FIGHT_PROP_WIND_ADD_HURT),
                    ("FIGHT_PROP_ROCK_ADD_HURT", stats.FIGHT_PROP_ROCK_ADD_HURT),
                    ("FIGHT_PROP_ICE_ADD_HURT", stats.FIGHT_PROP_ICE_ADD_HURT),
                ]
                if stat.value > 0
            ]
        )
        _hp = [
            round(stats.FIGHT_PROP_MAX_HP.value),
            round(stats.BASE_HP.value),
            round(stats.FIGHT_PROP_MAX_HP.value - stats.BASE_HP.value),
        ]
        _atk = [
            round(stats.FIGHT_PROP_CUR_ATTACK.value),
            round(stats.FIGHT_PROP_BASE_ATTACK.value),
            round(stats.FIGHT_PROP_CUR_ATTACK.value - stats.FIGHT_PROP_BASE_ATTACK.value),
        ]
        _def = [
            round(stats.FIGHT_PROP_CUR_DEFENSE.value),
            round(stats.FIGHT_PROP_BASE_DEFENSE.value),
            round(stats.FIGHT_PROP_CUR_DEFENSE.value - stats.FIGHT_PROP_BASE_DEFENSE.value),
        ]
        _emoji = {
            "HP": emoji.fightprop.get("FIGHT_PROP_HP", ""),
            "ATK": emoji.fightprop.get("FIGHT_PROP_ATTACK", ""),
            "DEF": emoji.fightprop.get("FIGHT_PROP_DEFENSE", ""),
        }
        embed.add_field(
            name="Stats Panel",
            value=(
                f"{_emoji['HP']}HP: {_hp[0]} ({_hp[1]} +{_hp[2]})\n"
                f"{_emoji['ATK']}Attack: {_atk[0]} ({_atk[1]} +{_atk[2]})\n"
                f"{_emoji['DEF']}Defense: {_def[0]} ({_def[1]} +{_def[2]})\n"
                f"{substat}"
            ),
            inline=False,
        )

        return embed

    def get_artifact_stat_embed(self, index: int) -> discord.Embed:
        embed = self.get_default_embed(index)
        embed.title = (embed.title + " Artifacts") if embed.title is not None else "Artifacts"

        if self.data.characters is None:
            return embed

        pos_name_map = {
            "EQUIP_BRACER": "Flower",
            "EQUIP_NECKLACE": "Feather",
            "EQUIP_SHOES": "Sands",
            "EQUIP_RING": "Goblet",
            "EQUIP_DRESS": "Circlet",
        }

        substat_sum: dict[str, float] = dict()
        crit_value: float = 0.0

        character = self.data.characters[index]
        for equip in character.equipments:
            if equip.type != enkanetwork.EquipmentsType.ARTIFACT:
                continue

            if (mainstats := equip.detail.mainstats) is None:
                continue
            embed_value = f"{self._get_statprop_sentence(mainstats)}\n"
            crit_value += (
                mainstats.value * 2
                if mainstats.prop_id == "FIGHT_PROP_CRITICAL"
                else mainstats.value
                if mainstats.prop_id == "FIGHT_PROP_CRITICAL_HURT"
                else 0
            )

            for substat in equip.detail.substats:
                substat_sum[substat.prop_id] = substat_sum.get(substat.prop_id, 0) + substat.value

            pos_name = pos_name_map.get(equip.detail.artifact_type.value, "Unknown")

            _artifact_emoji = emoji.artifact_type.get(pos_name, pos_name + "：")
            _artifact_set_name = equip.detail.artifact_name_set

            if pos_name not in ["Flower", "Feather"]:
                embed.add_field(
                    name=f"{_artifact_emoji}{_artifact_set_name}",
                    value=embed_value,
                    inline=False,
                )

        if "FIGHT_PROP_HP" in substat_sum.keys():
            substat_sum["FIGHT_PROP_HP_PERCENT"] = substat_sum.get("FIGHT_PROP_HP_PERCENT", 0) + (
                substat_sum["FIGHT_PROP_HP"] * 100 / character.stats.BASE_HP.value
            )
        if "FIGHT_PROP_ATTACK" in substat_sum.keys():
            substat_sum["FIGHT_PROP_ATTACK_PERCENT"] = substat_sum.get(
                "FIGHT_PROP_ATTACK_PERCENT", 0
            ) + (
                substat_sum["FIGHT_PROP_ATTACK"]
                * 100
                / character.stats.FIGHT_PROP_BASE_ATTACK.value
            )
        if "FIGHT_PROP_DEFENSE" in substat_sum.keys():
            substat_sum["FIGHT_PROP_DEFENSE_PERCENT"] = substat_sum.get(
                "FIGHT_PROP_DEFENSE_PERCENT", 0
            ) + (
                substat_sum["FIGHT_PROP_DEFENSE"]
                * 100
                / character.stats.FIGHT_PROP_BASE_DEFENSE.value
            )

        def substatSummary(prop: str, name: str, base: float) -> str:
            return (
                f"{emoji.fightprop.get(prop, '')}{name}：{round(value / base, 1)}\n"
                if (value := substat_sum.get(prop)) is not None
                else ""
            )

        embed_value = ""
        embed_value += substatSummary("FIGHT_PROP_ATTACK_PERCENT", "Attack Percentage", 5.0)
        embed_value += substatSummary("FIGHT_PROP_HP_PERCENT", "HP Percentage", 5.0)
        embed_value += substatSummary("FIGHT_PROP_DEFENSE_PERCENT", "Defense Percentage", 6.2)
        embed_value += substatSummary("FIGHT_PROP_CHARGE_EFFICIENCY", "Energy Recharge", 5.5)
        embed_value += substatSummary("FIGHT_PROP_ELEMENT_MASTERY", "Elemental Mastery", 20)
        embed_value += substatSummary("FIGHT_PROP_CRITICAL", "Critical Rate", 3.3)
        embed_value += substatSummary("FIGHT_PROP_CRITICAL_HURT", "Critical Damage", 6.6)

        if embed_value != "":
            crit_value += substat_sum.get("FIGHT_PROP_CRITICAL", 0) * 2 + substat_sum.get(
                "FIGHT_PROP_CRITICAL_HURT", 0
            )
            embed.add_field(
                name="Number of Affixes" + (f" (Double Crit {round(crit_value)})" if crit_value > 100 else ""),
                value=embed_value,
            )
        return embed

    async def get_image(self, index: int) -> io.BytesIO | None:
        if self.data.characters is None:
            return None

        if (image_buffer := self.image_buffers[index]) is not None:
            image = image_buffer
            image.seek(0)
        else:
            image = await generate_image(
                self.data,
                self.data.characters[index],
                enkanetwork.Language.EN,
                save_locally=False,
            )
            self.image_buffers[index] = image
        return image

    def get_default_embed(self, index: int) -> discord.Embed:
        character = self.data.player.characters_preview[index]
        color = {
            enkanetwork.ElementType.Pyro: 0xFB4120,
            enkanetwork.ElementType.Electro: 0xBF73E7,
            enkanetwork.ElementType.Hydro: 0x15B1FF,
            enkanetwork.ElementType.Cryo: 0x70DAF1,
            enkanetwork.ElementType.Dendro: 0xA0CA22,
            enkanetwork.ElementType.Anemo: 0x5CD4AC,
            enkanetwork.ElementType.Geo: 0xFAB632,
        }
        _assets_character = enka_assets.character(character.id)
        embed = discord.Embed(
            title=f"{_assets_character.rarity if _assets_character else '?'}★ {character.name}",
            color=color.get(character.element),
        )
        if character.icon:
            embed.set_thumbnail(url=character.icon.url)

        if (player := self.data.player) is not None:
            embed.set_author(
                name=f"{player.nickname}'s Characters Showcase",
                url=self.url,
                icon_url=player.avatar.icon.url if player.avatar and player.avatar.icon else None
            )
            embed.set_footer(text=f"{player.nickname}．Lv. {player.level}．UID: {self.uid}")

        if self.data.characters is None:
            embed.description = "Please allow 'Show Character Details' in your for more detailed character information."

        return embed

    def _get_character_fightprop_sentence(
        self, stat_name: str, stat: enkanetwork.Stats | enkanetwork.StatsPercentage
    ) -> str:
        emoji_str = emoji.fightprop.get(stat_name, "")
        prop_name = enka_assets.get_hash_map(stat_name)
        if isinstance(stat, enkanetwork.StatsPercentage):
            return f"{emoji_str}{prop_name}：{stat.to_percentage_symbol()}"
        return f"{emoji_str}{prop_name}：{stat.to_rounded()}"

    def _get_statprop_sentence(self, equip_stat: enkanetwork.EquipmentsStats) -> str:
        emoji_str = emoji.fightprop.get(equip_stat.prop_id, "")
        return f"{emoji_str}{equip_stat.name}+{equip_stat.value}" + (
            "%" if equip_stat.type == enkanetwork.DigitType.PERCENT else ""
        )
