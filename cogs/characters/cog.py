import asyncio
import io

import discord
import genshin
from discord import app_commands
from discord.ext import commands
from genshinpyrail.genshinpyrail import genshin_character_list, honkai_character_list
from genshinpyrail.src.tools.model import GenshinCharterList, StarRaillCharterList
from typing import Optional

import genshin_py
from utility import EmbedTemplate
from utility.custom_log import SlashCommandLogger

from .ui import DropdownView


class CharactersCog(commands.Cog, name="characters-list"):
    """Slash command"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="characters-list", description="Publicly display all my characters")
    @app_commands.rename(game="game", user="user")
    @app_commands.describe(game="Select a game", user="Query data of other members, leave blank to query own data.")
    @app_commands.choices(
        game=[
            app_commands.Choice(name="Genshin Impact", value="genshin"),
            app_commands.Choice(name="Star Rail", value="hkrpg"),
        ],
    )

    @SlashCommandLogger # noqa
    async def slash_characters(
        self,
        interaction: discord.Interaction,
        game: genshin.Game,
        user: Optional[discord.User] = None,
    ):
        user = user or interaction.user
        try:
            match game:
                case genshin.Game.GENSHIN:
                    defer, characters = await asyncio.gather(
                        interaction.response.defer(),
                        genshin_py.get_genshin_characters(user.id),
                    )
                case genshin.Game.STARRAIL:
                    defer, characters = await asyncio.gather(
                        interaction.response.defer(),
                        genshin_py.get_starrail_characters(user.id),
                    )
                case _:
                    return
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
            return

        try:
            match game:
                case genshin.Game.GENSHIN:
                    data = await genshin_character_list.Creat(characters).start()
                    image = GenshinCharterList(**data).card
                case genshin.Game.STARRAIL:
                    data = await honkai_character_list.Creat(characters).start()
                    image = StarRaillCharterList(**data).card
            if image is None:
                raise ValueError("Image Not Found")
        except Exception:
            view = DropdownView(user, characters)
            await interaction.edit_original_response(content="Please choose a character: ", view=view)
            return
        else:
            fp = io.BytesIO()
            image = image.convert("RGB")
            image.save(fp, "jpeg", optimize=True, quality=90)
            fp.seek(0)
            embed = EmbedTemplate.normal(f"{user.display_name}'s Characters Overview")
            embed.set_image(url="attachment://image.jpeg")
            await interaction.edit_original_response(
                embed=embed, attachments=[discord.File(fp, "image.jpeg")]
            )


async def setup(client: commands.Bot):
    await client.add_cog(CharactersCog(client))
