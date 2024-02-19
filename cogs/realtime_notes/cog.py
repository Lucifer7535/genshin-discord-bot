import asyncio
import typing

import discord
import genshin
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import genshin_py
from utility import EmbedTemplate
from utility.custom_log import ContextCommandLogger, SlashCommandLogger


class RealtimeNotes:
    @staticmethod
    async def notes(
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
        game: genshin.Game,
        *,
        short_form: bool = False,
    ):
        try:
            match game:
                case genshin.Game.GENSHIN:
                    defer, notes = await asyncio.gather(
                        interaction.response.defer(), genshin_py.get_genshin_notes(user.id)
                    )
                    main_embed, expedition_embeds = await genshin_py.parse_genshin_notes_command(
                        notes, user=user, short_form=short_form
                    )
                case genshin.Game.STARRAIL:
                    defer, notes = await asyncio.gather(
                        interaction.response.defer(), genshin_py.get_starrail_notes(user.id)
                    )
                    main_embed = await genshin_py.parse_starrail_notes(
                        notes, user, short_form=short_form
                    )
                case _:
                    return
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            embeds = [main_embed] + expedition_embeds
            await interaction.edit_original_response(embeds=embeds)


class RealtimeNotesCog(commands.Cog, name="instant-notes"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="instant-notes", description="Query instant notes, including resin, realm currency, expedition... etc.") # noqa
    @app_commands.rename(game="game", short_form="display_format", user="user")
    @app_commands.describe(short_form="Choose between displaying in complete or simplified format (omitting daily, weekly, exploration dispatch)", user="View data for other members; leave blank to view your own data") # noqa
    @app_commands.choices(
        game=[
            Choice(name="Genshin Impact", value="genshin"),
            Choice(name="Starrail Check", value="hkrpg"),
        ],
        short_form=[Choice(name="Complete", value="complete"), Choice(name="Simplified", value="simplified")],
    )

    @SlashCommandLogger # noqa
    async def slash_notes(
        self,
        interaction: discord.Interaction,
        game: genshin.Game,
        short_form: typing.Literal["Complete", "Simplified"] = "Complete",
        user: discord.User | None = None,
    ):
        await RealtimeNotes.notes(
            interaction, user or interaction.user, game, short_form=(short_form == "Simplified")
        )


async def setup(client: commands.Bot):
    await client.add_cog(RealtimeNotesCog(client))

    @client.tree.context_menu(name="Instant Notes (Genshin Impact)")
    @ContextCommandLogger
    async def context_notes(interaction: discord.Interaction, user: discord.User):
        await RealtimeNotes.notes(interaction, user, genshin.Game.GENSHIN)
