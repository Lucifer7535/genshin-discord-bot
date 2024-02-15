import asyncio
import datetime

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import genshin_py
from utility import EmbedTemplate
from utility.custom_log import SlashCommandLogger


class TravelerDiary:
    @staticmethod
    async def diary(
        interaction: discord.Interaction, user: discord.User | discord.Member, month: int
    ):
        try:
            defer, diary = await asyncio.gather(
                interaction.response.defer(),
                genshin_py.get_genshin_traveler_diary(user.id, month),
            )
            embed = genshin_py.parse_genshin_diary(diary, month)
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.edit_original_response(embed=embed)


class DiaryCog(commands.Cog, name="Traveler's Diary/Exploration Calendar"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="diary_notes", description="Query Traveler's Diary (Primogems, Mora income)")
    @app_commands.rename(month="month")
    @app_commands.describe(month="Select the month to query")
    @app_commands.choices(
        month=[
            Choice(name="This Month", value=0),
            Choice(name="Last Month", value=-1),
            Choice(name="Month Before Last Month", value=-2),
        ]
    )

    @SlashCommandLogger # noqa
    async def slash_diary(self, interaction: discord.Interaction, month: int):
        month = datetime.datetime.now().month + month
        month = month + 12 if month < 1 else month
        await TravelerDiary.diary(interaction, interaction.user, month)


async def setup(client: commands.Bot):
    await client.add_cog(DiaryCog(client))
