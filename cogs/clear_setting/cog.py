import discord
from discord import app_commands
from discord.ext import commands

from database import Database
from utility import custom_log

from .ui import ConfirmButton


class ClearSettingCog(commands.Cog, name="clear-user-data"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="clear-user-data", description="Delete all user data saved in the bot")
    @custom_log.SlashCommandLogger
    async def slash_clear(self, interaction: discord.Interaction):
        view = ConfirmButton()
        await interaction.response.send_message("Are you sure you want to delete all data?", view=view, ephemeral=True)

        await view.wait()
        if view.value is True:
            await Database.delete_all(interaction.user.id)
            await interaction.edit_original_response(content="All user data has been deleted", view=None)
        else:
            await interaction.edit_original_response(content="Command canceled", view=None)


async def setup(client: commands.Bot):
    await client.add_cog(ClearSettingCog(client))
