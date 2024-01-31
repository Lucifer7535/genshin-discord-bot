import asyncio

import discord
import genshin
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import genshin_py
from database import Database, User
from utility import EmbedTemplate, config, custom_log

from .ui import UidDropdown, UIDModal


class UIDSettingCog(commands.Cog, name="UID Settings"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="uid-settings", description="Save the specified UID")
    @app_commands.rename(game="game")
    @app_commands.choices(
        game=[
            Choice(name="Genshin Impact", value="genshin"),
            Choice(name="Honkai Impact 3", value="honkai3rd"),
            Choice(name="Star Rail", value="hkrpg"),
        ]
    )
    @custom_log.SlashCommandLogger
    async def slash_uid(
        self,
        interaction: discord.Interaction,
        game: genshin.Game,
    ):
        user = await Database.select_one(User, User.discord_id.is_(interaction.user.id))
        cookie = None
        if user is not None:
            match game:
                case genshin.Game.GENSHIN:
                    cookie = user.cookie_genshin
                case genshin.Game.HONKAI:
                    cookie = user.cookie_honkai3rd
                case genshin.Game.STARRAIL:
                    cookie = user.cookie_starrail

        if user is None or cookie is None:
            await interaction.response.send_modal(UIDModal(game))
        else:
            try:
                defer, accounts = await asyncio.gather(
                    interaction.response.defer(ephemeral=True),
                    genshin_py.get_game_accounts(interaction.user.id, game),
                )
                if len(accounts) == 0:
                    raise Exception("There is no role in this account")
            except Exception as e:
                await interaction.edit_original_response(embed=EmbedTemplate.error(e))
            else:
                view = discord.ui.View(timeout=config.discord_view_short_timeout)
                view.add_item(UidDropdown(accounts, game))
                await interaction.edit_original_response(view=view)


async def setup(client: commands.Bot):
    await client.add_cog(UIDSettingCog(client))
