import asyncio

import discord
import genshin
from discord import app_commands
from discord.ext import commands

import genshin_py
from utility import EmbedTemplate
from utility.custom_log import SlashCommandLogger

from .ui import Dropdown, View


class NoticesCog(commands.Cog, name="game-notices"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="game-notices", description="Display game and event announcements for Genshin Impact")
    @SlashCommandLogger
    async def slash_notices(self, interaction: discord.Interaction):
        try:
            defer, notices = await asyncio.gather(
                interaction.response.defer(), genshin_py.get_genshin_notices()
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            game: list[genshin.models.Announcement] = []
            event: list[genshin.models.Announcement] = []
            wish: list[genshin.models.Announcement] = []
            for notice in notices:
                if notice.type == 1:
                    if "Wish" in notice.subtitle:
                        wish.append(notice)
                    else:
                        event.append(notice)
                elif notice.type == 2:
                    game.append(notice)

            view = View()
            if len(game) > 0:
                view.add_item(Dropdown(game, "Game Announcements:"))
            if len(event) > 0:
                view.add_item(Dropdown(event, "Event Announcements:"))
            if len(wish) > 0:
                view.add_item(Dropdown(wish, "Wish Preview:"))
            await interaction.edit_original_response(view=view)


async def setup(client: commands.Bot):
    await client.add_cog(NoticesCog(client))
