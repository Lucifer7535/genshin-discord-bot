import asyncio
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import genshin_py
from utility import EmbedTemplate, custom_log


class DailyCheckinCog(commands.Cog, name="daily-checkin"):
    """Slash Command"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="daily-checkin", description="Claim daily check-in rewards from Hoyolab")
    @app_commands.rename(game="game", is_geetest="enable-captcha", user="user")
    @app_commands.choices(
        game=[
            Choice(name="Genshin Impact", value="Genshin Impact"),
            Choice(name="Honkai Impact 3", value="Honkai Impact 3"),
            Choice(name="Starrail", value="Starrail"),
            Choice(name="Tears of Themis(TW)", value="Tears of Themis(TW)"),
            Choice(name="Tears of Themis(GLOBAL)", value="Tears of Themis(GLOBAL)"),
        ]
    )
    @app_commands.choices(
        is_geetest=[
            Choice(name="Yes", value="Yes"),
            Choice(name="No", value="No"),
        ]
    )
    @custom_log.SlashCommandLogger
    async def slash_daily(
        self,
        interaction: discord.Interaction,
        game: Literal["Genshin Impact", "Honkai Impact 3", "Starrail", "Tears of Themis(TW)", "Tears of Themis(GLOBAL)"],
        is_geetest: Literal["Yes", "No"] = "No",
        user: Optional[discord.User] = None,
    ):
        choice = {
            "has_genshin": True if game == "Genshin Impact" else False,
            "has_honkai3rd": True if game == "Honkai Impact 3" else False,
            "has_starrail": True if game == "Starrail" else False,
            "has_themis": True if game == "Tears of Themis(GLOBAL)" else False,
            "has_themis_tw": True if game == "Tears of Themis(TW)" else False,
            "is_geetest": True if is_geetest == "Yes" else False,
        }

        _user = user or interaction.user
        if _user.id == self.bot.application_id:
            _user = interaction.user

        defer, result = await asyncio.gather(
            interaction.response.defer(ephemeral=(is_geetest == "Yes")),
            genshin_py.claim_daily_reward(_user.id, **choice),
        )
        await interaction.edit_original_response(embed=EmbedTemplate.normal(result))


async def setup(client: commands.Bot):
    await client.add_cog(DailyCheckinCog(client))
