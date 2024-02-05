from typing import Callable, Type

import discord

from utility import EmbedTemplate, emoji

from .api import API
from .models import Achievement, Character, Constellation, Food, Material, Talent, Weapon
from .models.artifacts import Artifact, PartDetail
from .models.tcg_cards import ActionCard, CharacterCard, DiceCost, Summon


def parse(model) -> discord.Embed:
    _map: dict[Type, Callable] = {
        CharacterCard: TCGCardParser.parse_character_card,
        ActionCard: TCGCardParser.parse_action_card,
        Summon: TCGCardParser.parse_summon,
        Achievement: AchievemntParser.parse_achievement,
        Artifact: EquipmentParser.parse_artifact,
        PartDetail: EquipmentParser.parse_artifact_part,
        Weapon: EquipmentParser.parse_weapon,
        Character: CharacterParser.parse_character,
        Talent: CharacterParser.parse_talent,
        Constellation: CharacterParser.parse_constellation,
        Food: MaterialParser.parse_food,
        Material: MaterialParser.parse_material,
    }
    parser = _map.get(type(model))
    if parser is not None:
        return parser(model)
    else:
        return EmbedTemplate.error("An error occurred, unable to parse data")


class TCGCardParser:

    @classmethod
    def _parse_costs(cls, costs: list[DiceCost]) -> str:

        if len(costs) == 0:
            return "None"
        cost_texts: list[str] = []
        for cost in costs:
            if _emoji := emoji.tcg_dice_cost_elements.get(cost.element.name):
                _text = _emoji
            else:
                _text = str(cost.element)
            cost_texts.append(f"{_text} ({cost.amount})")
        return " / ".join(cost_texts)

    @classmethod
    def parse_character_card(cls, card: CharacterCard) -> discord.Embed:

        embed = EmbedTemplate.normal(card.story_text or " ", title=card.name)
        embed.set_image(url=card.image_url)
        for talent in card.talents:
            _value = "Cost: " + cls._parse_costs(talent.costs) + "\n"
            _value += talent.effect
            embed.add_field(
                name=f"{talent.type}: {talent.name}",
                value=_value,
                inline=False,
            )
        if len(card.tags) > 0:
            embed.set_footer(text=f"Tags: {'、'.join([tag for tag in card.tags])}")
        return embed

    @classmethod
    def parse_action_card(cls, card: ActionCard) -> discord.Embed:

        description = ""
        if card.story_text is not None:
            description += f"{card.story_text}\n\n"
        description += f"Cost: {cls._parse_costs(card.costs)}\n{card.effect}"
        embed = EmbedTemplate.normal(description, title=f"{card.name} ({card.type})")
        embed.set_image(url=card.image_url)

        if len(card.tags) > 0:
            embed.set_footer(text=f"Tags: {'、'.join([tag for tag in card.tags])}")
        return embed

    @classmethod
    def parse_summon(cls, card: Summon) -> discord.Embed:

        embed = EmbedTemplate.normal(card.effect, title=f"{card.name} ({card.type})")
        embed.set_image(url=card.image_url)
        return embed


class AchievemntParser:

    @classmethod
    def parse_achievement(cls, achievement: Achievement) -> discord.Embed:

        description = f"Category: {achievement.group}\n"
        description += f"Type: {'Hidden Achievement' if achievement.ishidden else 'Normal Achievement'}\n"
        description += f"Stages: {achievement.stages}"
        embed = EmbedTemplate.normal(description, title=achievement.name)
        for i, stage in enumerate(achievement.stage_details):
            embed.add_field(name=f"Stage {i+1}", value=stage.description)
        embed.set_footer(text=f"Added in version {achievement.version}")
        return embed


class EquipmentParser:

    @classmethod
    def parse_artifact(cls, artifact: Artifact) -> discord.Embed:

        description = "Rarity: " + ", ".join([str(r) for r in artifact.rarity]) + "\n"
        if artifact.effect_1pc is not None:
            description += f"Effect: {artifact.effect_1pc}\n"
        if artifact.effect_2pc is not None:
            description += f"2-Piece Set: {artifact.effect_2pc}\n"
        if artifact.effect_4pc is not None:
            description += f"4-Piece Set: {artifact.effect_4pc}\n"
        embed = EmbedTemplate.normal(description, title=artifact.name)
        embed.set_thumbnail(url=artifact.images.flower_url or artifact.images.circlet_url)
        embed.set_footer(text=f"Added in version {artifact.version}")
        return embed

    @classmethod
    def parse_artifact_part(cls, part: PartDetail) -> discord.Embed:

        embed = EmbedTemplate.normal(part.description, title=part.name)
        embed.add_field(name="Story", value=part.story)
        embed.set_footer(text=part.relictype)
        return embed

    @classmethod
    def parse_weapon(cls, weapon: Weapon) -> discord.Embed:

        description = (
            f"Base Attack: {weapon.base_atk}\nMain Attribute: {weapon.mainstat}+{weapon.mainvalue}\n"
        )
        embed = EmbedTemplate.normal(description, title=f"{weapon.rarity}★ {weapon.name}")
        embed.add_field(name=weapon.effect_name, value=weapon.effect_desciption)
        embed.set_thumbnail(
            url=(
                weapon.images.awaken_icon_url
                or weapon.images.icon_url
                or API.get_image_url(weapon.images.icon)
            )
        )
        embed.set_footer(text=weapon.description)
        return embed


class CharacterParser:

    @classmethod
    def parse_character(cls, character: Character) -> discord.Embed:
        embed = EmbedTemplate.normal(
            character.description, title=f"{character.rarity}★ {character.name}"
        )
        if character.images is not None:
            embed.set_thumbnail(url=character.images.icon_url)
            if character.images.cover1_url is not None:
                embed.set_image(url=character.images.cover1_url)

        embed.add_field(
            name="Attributes",
            value=(
                f"Element: {character.element}\n"
                + f"Weapon: {character.weapontype}\n"
                + f"Ascension: {character.substat}\n"
            ),
        )
        _text = f"Gender: {character.gender}\n" + f"Constellation: {character.constellation}\n"
        if character.affiliation is not None:
            _text += f"Affiliation: {character.affiliation}\n"
        if character.birthday is not None:
            _text += f"Birthday: {character.birthday}\n"
        embed.add_field(name="Basic Information", value=_text)

        _cv = character.character_voice
        embed.add_field(
            name="Voice Actor",
            value=f"Chinese: {_cv.chinese}\n"
            + f"Japanese: {_cv.japanese}\n"
            + f"English: {_cv.english}\n"
            + f"Korean: {_cv.korean}\n",
            inline=False,
        )
        return embed

    @classmethod
    def parse_talent(cls, talent: Talent) -> discord.Embed:
        embed = EmbedTemplate.normal("", title=talent.name)
        embed.add_field(name=talent.combat1.name, value=talent.combat1.description)
        embed.add_field(name="E: " + talent.combat2.name, value=talent.combat2.description)
        embed.add_field(name="Q: " + talent.combat3.name, value=talent.combat3.description)
        embed.add_field(name="talent 1: " + talent.passive1.name, value=talent.passive1.description)
        embed.add_field(name="talent 2: " + talent.passive2.name, value=talent.passive2.description)
        if talent.passive3 is not None:
            embed.add_field(
                name="talent 3：" + talent.passive3.name, value=talent.passive3.description
            )
        return embed

    @classmethod
    def parse_constellation(cls, constellation: Constellation) -> discord.Embed:

        cst = constellation
        embed = EmbedTemplate.normal("", title=cst.name)
        csts = [cst.c1, cst.c2, cst.c3, cst.c4, cst.c5, cst.c6]
        for i, _cst in enumerate(csts):
            embed.add_field(name=f"Constellation{i+1}: {_cst.name}", value=_cst.description)
        return embed


class MaterialParser:

    @classmethod
    def parse_food(cls, food: Food) -> discord.Embed:

        embed = EmbedTemplate.normal(food.description, title=food.name)
        embed.set_thumbnail(url=API.get_image_url(food.images.icon))
        if food.suspicious is not None:
            embed.add_field(name="Failed Dish", value=food.suspicious.effect)
        if food.normal is not None:
            embed.add_field(name="Normal Dish", value=food.normal.effect)
        if food.delicious is not None:
            embed.add_field(name="Perfect Dish", value=food.delicious.effect)
        embed.add_field(
            name="Attributes",
            value=f"Rarity：{food.rarity}\n"
            + f"Type：{food.food_type}\n"
            + f"Effect：{food.effect}\n",
        )
        embed.add_field(
            name="Ingredients",
            value="\n".join([f"{ingred.name}: {ingred.count}" for ingred in food.ingredients]),
        )
        embed.set_footer(text=f"Added in version {food.version}")
        return embed

    @classmethod
    def parse_material(cls, material: Material) -> discord.Embed:

        embed = EmbedTemplate.normal(material.description, title=material.name)
        embed.set_thumbnail(url=API.get_image_url(material.images.icon))

        embed.add_field(
            name="Attributes",
            value=f"Type: {material.material_type}\n"
            + (f"Rarity: {material.rarity}\n" if material.rarity else "")
            + f"Source: {'、'.join([s for s in material.sources])}\n",
        )

        if material.drop_domain is not None and material.days_of_week is not None:
            embed.add_field(
                name=material.drop_domain, value="\n".join([d for d in material.days_of_week])
            )
        if material.version is not None:
            embed.set_footer(text=f"Added in version {material.version}")

        return embed
