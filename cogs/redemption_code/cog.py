import re
import asyncio
import discord
import genshin
from discord.ext import commands
import genshin_py.client as genshin_py
import genshin_py.errors
from utility import EmbedTemplate, custom_log
from typing import Literal, Optional
from discord import app_commands
from discord.app_commands import Choice


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

    await interaction.response.defer()

    codes = codes[:5] if len(codes) > 5 else codes
    msg = ""
    invalid_cookie_msg = ""
    try:
        genshin_client = await genshin_py.get_client(user.id, game=game, check_uid=False)
    except Exception as e:
        await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        return

    for i, code in enumerate(codes):
        if i > 0:
            await interaction.edit_original_response(
                embed=discord.Embed(color=0xFCC766, description=f"{msg} Waiting for 5 seconds of cooling time to use redeem code {i+1}.....") # noqa
            )
            await asyncio.sleep(5)
        try:
            genshin_client = await genshin_py.get_client(user.id, game=game, check_uid=False)
            result = "✅ " + await genshin_py.redeem_code(user.id, genshin_client, code, game)
        except genshin_py.errors.GenshinAPIException as e:
            result = "❌ "
            if isinstance(e.origin, genshin.errors.InvalidCookies):
                result += "Invalid cookie"
                invalid_cookie_msg = str(e.origin)
            else:
                result += e.message
        except Exception as e:
            result = "❌ " + str(e)

        msg += f"{code} : {result}\n"

        embed = discord.Embed(color=0x8FCE00, description=msg)

        if len(invalid_cookie_msg) > 0:
            embed.description += f"\n{invalid_cookie_msg}"
        await interaction.edit_original_response(embed=embed)


class RedemptionCodeCog(commands.Cog, name="redeem-code"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="redeem-code", description="Redeem Code from Hoyolab")
    @app_commands.rename(code="code", game="game", user="user")
    @app_commands.describe(code="Please enter the redemption code to be used, support multiple sets of redemption codes at the same time input") # noqa
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
        await redeem(interaction, user or interaction.user, code, game_map[game])


async def setup(client: commands.Bot):
    await client.add_cog(RedemptionCodeCog(client))

    @client.tree.context_menu(name="Redeem Code Genshin Impact")
    @custom_log.ContextCommandLogger
    async def context_redeem_genshin(interaction: discord.Interaction, msg: discord.Message):
        await redeem(interaction, interaction.user, msg.content, genshin.Game.GENSHIN)

    @client.tree.context_menu(name="Redeem Code Starrail")
    @custom_log.ContextCommandLogger
    async def context_redeem_starrail(interaction: discord.Interaction, msg: discord.Message):
        await redeem(interaction, interaction.user, msg.content, genshin.Game.STARRAIL)
