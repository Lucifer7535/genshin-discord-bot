import asyncio
from typing import Literal, Optional, Union

import discord
import sentry_sdk
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import genshin_py
from utility import EmbedTemplate, config
from utility.custom_log import LOG, ContextCommandLogger, SlashCommandLogger


class RecordCard:
    @staticmethod
    async def card(
        interaction: discord.Interaction,
        user: Union[discord.User, discord.Member],
        option: Literal["RECORD", "EXPLORATION"],
    ):
        try:
            defer, (uid, userstats) = await asyncio.gather(
                interaction.response.defer(), genshin_py.get_genshin_record_card(user.id)
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
            return

        try:
            avatar_bytes = await user.display_avatar.read()
            if option == "RECORD":
                fp = genshin_py.draw_record_card(avatar_bytes, uid, userstats)
            elif option == "EXPLORATION":
                fp = genshin_py.draw_exploration_card(avatar_bytes, uid, userstats)
        except Exception as e:
            LOG.ErrorLog(interaction, e)
            sentry_sdk.capture_exception(e)
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            fp.seek(0)
            await interaction.edit_original_response(
                attachments=[discord.File(fp=fp, filename="image.jpeg")]
            )
            fp.close()


class RecordCardCog(commands.Cog, name="record-card"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="record-card", description="Generate Genshin Impact personal game record card")
    @app_commands.rename(option="option", user="user")
    @app_commands.describe(option="Select whether to view data overview or world exploration", user="View data for other members; leave blank to view your own data") # noqa
    @app_commands.choices(
        option=[
            Choice(name="Data Overview", value="RECORD"),
            Choice(name="World Exploration", value="EXPLORATION"),
        ]
    )

    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown) # noqa
    @SlashCommandLogger
    async def slash_card(
        self,
        interaction: discord.Interaction,
        option: Literal["RECORD", "EXPLORATION"],
        user: Optional[discord.User] = None,
    ):
        await RecordCard.card(interaction, user or interaction.user, option)

    @slash_card.error
    async def on_slash_card_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                embed=EmbedTemplate.error(f"Card generation cooldown is {config.slash_cmd_cooldown} seconds. Please wait before using it again."), # noqa
                ephemeral=True,
            )


async def setup(client: commands.Bot):
    await client.add_cog(RecordCardCog(client))

    @client.tree.context_menu(name="Game Record Card")
    @ContextCommandLogger
    async def context_card(interaction: discord.Interaction, user: discord.User):
        await RecordCard.card(interaction, user, "RECORD")
