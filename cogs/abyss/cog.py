from typing import Literal, Optional

import discord
import genshin
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from utility import EmbedTemplate, config, custom_log

from .ui_genshin import SpiralAbyssUI
from .ui_starrail import ChooseAbyssModeButton, ForgottenHallUI


class SpiralAbyssCog(commands.Cog, name="abyss-record"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="abyss-record", description="Check Spiral Abyss records")
    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown)
    @app_commands.rename(game="game", season="time", user="user")
    @app_commands.describe(season="Select THIS_SEASON, PREVIOUS_SEASON, or SAVED_RECORD", user="Check data of other users.")
    @app_commands.choices(
        game=[
            Choice(name="Genshin Impact", value="genshin"),
            Choice(name="Star Rail", value="hkrpg"),
        ],
        season=[
            Choice(name="This Season Record", value="THIS_SEASON"),
            Choice(name="Previous Season Record", value="PREVIOUS_SEASON"),
            Choice(name="Saved Record", value="HISTORICAL_RECORD"),
        ],
    )
    @custom_log.SlashCommandLogger
    async def slash_abyss(
        self,
        interaction: discord.Interaction,
        game: genshin.Game,
        season: Literal["THIS_SEASON", "PREVIOUS_SEASON", "HISTORICAL_RECORD"],
        user: Optional[discord.User] = None,
    ):
        match game:
            case genshin.Game.GENSHIN:
                await SpiralAbyssUI.abyss(interaction, user or interaction.user, season)
            case genshin.Game.STARRAIL:
                # Choose Forgotten Hall or Fictional Narrative
                view = ChooseAbyssModeButton()
                await interaction.response.send_message(view=view)
                await view.wait()

                if view.value is None:
                    return
                mode = view.value
                await ForgottenHallUI.launch(interaction, user or interaction.user, mode, season)
            case _:
                return

    @slash_abyss.error
    async def on_slash_abyss_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                embed=EmbedTemplate.error(f"Command cooldown is {config.slash_cmd_cooldown} seconds; please try again later~"),
                ephemeral=True,
            )


async def setup(client: commands.Bot):
    await client.add_cog(SpiralAbyssCog(client))

    # -------------------------------------------------------------
    # Below are Context Menu commands
    @client.tree.context_menu(name="Abyss Record (Previous Season)")
    @custom_log.ContextCommandLogger
    async def context_abyss_previous(interaction: discord.Interaction, user: discord.User):
        await SpiralAbyssUI.abyss(interaction, user, "PREVIOUS_SEASON")

    @client.tree.context_menu(name="Abyss Record (This Season)")
    @custom_log.ContextCommandLogger
    async def context_abyss(interaction: discord.Interaction, user: discord.User):
        await SpiralAbyssUI.abyss(interaction, user, "THIS_SEASON")
