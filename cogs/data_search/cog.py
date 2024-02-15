import random
from typing import Iterable, List, Literal

import discord
import sentry_sdk
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import genshin_db
from utility import EmbedTemplate, config, custom_log

from .ui import SearchResultsDropdown

StrCategory = Literal["Character", "Weapon", "Artifact", "Item/Food", "Achievements", "TCG-cards"]


class Search(commands.Cog, name="search-data"):
    def __init__(self, bot: commands.Bot, genshin_db_data: genshin_db.GenshinDbAllData):
        self.bot = bot
        self.db = genshin_db_data

    @app_commands.command(name="search-data", description="Search the Genshin Impact database")
    @app_commands.rename(category="category", item_name="name")
    @app_commands.describe(category="Select the category to search")
    @app_commands.choices(
        category=[
            Choice(name="Character", value="Character"),
            Choice(name="Weapon", value="Weapon"),
            Choice(name="Artifact", value="Artifact"),
            Choice(name="Item/Food", value="Item/Food"),
            Choice(name="Achievement", value="Achievement"),
            Choice(name="TCG-cards", value="TCG-cards"),
        ]
    )
    @custom_log.SlashCommandLogger
    async def slash_search(
        self,
        interaction: discord.Interaction,
        category: StrCategory,
        item_name: str,
    ):
        """Search genshin-db database with a slash command"""
        titles: list[str] = []
        embeds: list[discord.Embed] = []
        match category:
            case "Character":
                character = self.db.characters.find(item_name)
                titles.append("Basic Information")
                embeds.append(genshin_db.parse(character))

                # Special handling for Traveler with multiple elements
                if "Traveler" in item_name:
                    for element in ["Anemo", "Geo", "Electro", "Dendro", "Hydro"]:
                        talent = self.db.talents.find(f"Traveler ({element})")
                        titles.append(f"Talent: {element}")
                        embeds.append(genshin_db.parse(talent))
                    for element in ["Anemo", "Geo", "Electro", "Dendro", "Hydro"]:
                        constell = self.db.constellations.find(f"Traveler ({element})")
                        titles.append(f"Constellation: {element}")
                        embeds.append(genshin_db.parse(constell))
                else:
                    talent = self.db.talents.find(item_name)
                    titles.append("Talent")
                    embeds.append(genshin_db.parse(talent))
                    constell = self.db.constellations.find(item_name)
                    titles.append("Constellation")
                    embeds.append(genshin_db.parse(constell))
            case "Artifact":
                artifact = self.db.artifacts.find(item_name)
                if artifact is None:
                    return
                titles = ["Overview"]
                embeds = [genshin_db.parse(artifact)]
                _titles = ["Flower", "Plume", "Sands", "Goblet", "Circlet"]
                _parts = [
                    artifact.flower,
                    artifact.plume,
                    artifact.sands,
                    artifact.goblet,
                    artifact.circlet,
                ]
                for i, _part in enumerate(_parts):
                    if _part is not None:
                        titles.append(_titles[i])
                        embeds.append(genshin_db.parse(_part))
            case _:
                item = self.db.find(item_name)
                embeds.append(genshin_db.parse(item))

        match len(embeds):
            case 0:
                _embed = EmbedTemplate.error("Error occurred, cannot find this item")
                await interaction.response.send_message(embed=_embed)
            case 1:
                await interaction.response.send_message(embed=embeds[0])
            case n if n > 1:
                view = discord.ui.View(timeout=config.discord_view_long_timeout)
                view.add_item(SearchResultsDropdown(titles, embeds))
                await interaction.response.send_message(embed=embeds[0], view=view)

    @slash_search.autocomplete("item_name")
    async def autocomplete_search_item_name(
        self, interaction: discord.Interaction, current: str
    ) -> List[Choice[str]]:
        """Autocomplete for the item_name parameter of the slash_search command"""

        category: StrCategory | None = interaction.namespace.category
        if category is None:
            return []

        item_list: Iterable[genshin_db.GenshinDbBase] = {
            "Character": self.db.characters.list,
            "Weapon": self.db.weapons.list,
            "Artifact": self.db.artifacts.list,
            "Item/Food": self.db.materials.list + self.db.foods.list,
            "Achievement": self.db.achievements.list,
            "TCG-cards": self.db.tcg_cards.list,
        }.get(category, [])

        choices: List[Choice[str]] = []
        for item in item_list:
            if current.lower() in item.name.lower():
                choices.append(Choice(name=item.name, value=item.name))
        # Randomly select 25 if the user didn't input anything
        if current == "":
            choices = random.sample(choices, k=25)

        choices = choices[:25]
        choices.sort(key=lambda choice: choice.name)
        return choices


async def setup(client: commands.Bot):
    try:
        gdb_data = await genshin_db.fetch_all()
    except Exception as e:
        custom_log.LOG.Error(str(e))
        sentry_sdk.capture_exception(e)
    else:
        await client.add_cog(Search(client, gdb_data))
