import re

import discord
import genshin
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

from utility import EmbedTemplate, custom_log
from typing import Literal, Optional

class RedeemCode:
    @staticmethod
    async def redeem(
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
        code: str,
        game: genshin.Game,
    ):
        code = re.sub(r"(https://){0,1}genshin.hoyoverse.com(/.*){0,1}/gift\?code=", "", code)
        code = re.sub(r"(https://){0,1}hsr.hoyoverse.com(/.*){0,1}/gift\?code=", "", code)
        codes = re.findall(r"[A-Za-z0-9]{5,30}", code)
        if len(codes) == 0:
            await interaction.response.send_message(embed=EmbedTemplate.error("No redemption code detected. Please re-enter."))
            return
    
        codes = codes[:5] if len(codes) > 5 else codes
        msg = "Please click the following link to redeem code:\n> "
        for i, code in enumerate(codes):
            game_host = {genshin.Game.GENSHIN: "genshin", genshin.Game.STARRAIL: "hsr"}
            msg += f"{i+1}. [{code}](https://{game_host.get(game)}.hoyoverse.com/gift?code={code})\n"

        embed = discord.Embed(color=0x8FCE00, description=msg)
        await interaction.response.send_message(embed=embed)


class RedemptionCodeCog(commands.Cog, name="redeem-code"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="redeem-code", description="Redeem Code from Hoyolab")
    @app_commands.rename(code="code", game="game", user="user")
    @app_commands.describe(code="Please enter the redemption code to be used, support multiple sets of redemption codes at the same time input")
    @app_commands.choices(
        game=[
            Choice(name="Genshin Impact", value="GENSHIN"),
            Choice(name="Star Rail", value="STARRAIL"),
        ]
    )
    @custom_log.SlashCommandLogger
    async def slash_redeem(
        self,
        interaction: discord.Interaction,
        code: str,
        game: Literal["GENSHIN", "STARRAIL"],
        user: Optional[discord.User] = None,
    ):
        game_map = {"GENSHIN": genshin.Game.GENSHIN, "STARRAIL": genshin.Game.STARRAIL}
        await RedeemCode.redeem(interaction, user or interaction.user, code, game_map[game])


async def setup(client: commands.Bot):
    await client.add_cog(RedemptionCodeCog(client))

    @client.tree.context_menu(name="Redeem Code Genshin Impact")
    @custom_log.ContextCommandLogger
    async def context_redeem_genshin(interaction: discord.Interaction, msg: discord.Message):
        await RedeemCode.redeem(interaction, interaction.user, msg.content, genshin.Game.GENSHIN)

    @client.tree.context_menu(name="Redeem Code Starrail")
    @custom_log.ContextCommandLogger
    async def context_redeem_starrail(interaction: discord.Interaction, msg: discord.Message):
        await RedeemCode.redeem(interaction, interaction.user, msg.content, genshin.Game.STARRAIL)