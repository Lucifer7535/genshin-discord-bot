import typing
from http.cookies import SimpleCookie

import discord
import genshin

import genshin_py
from utility import LOG, EmbedTemplate, get_app_command_mention


class GameSelectionView(discord.ui.View):
    """Select which games to submit Cookies for"""

    @discord.ui.select(
        cls=discord.ui.Select,
        options=[
            discord.SelectOption(label="Genshin Impact", value="genshin"),
            discord.SelectOption(label="Honkai Impact 3rd", value="honkai3rd"),
            discord.SelectOption(label="Starrail", value="hkrpg"),
            discord.SelectOption(label="Tears of Themis", value="tot"),
        ],
        min_values=1,
        max_values=4,
        placeholder="Please choose games (multiple choices allowed):",
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        modal = CookieModal([genshin.Game(v) for v in select.values])
        await interaction.response.send_modal(modal)


class CookieModal(discord.ui.Modal, title="Submit Cookie"):
    """Form to submit Cookie"""

    ltuid_v2: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="ltuid_v2",
        placeholder="Paste the obtained ltuid_v2",
        style=discord.TextStyle.short,
        required=False,
        min_length=5,
        max_length=20,
    )

    account_id_v2: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="account_id_v2",
        placeholder="Paste the obtained account_id_v2",
        style=discord.TextStyle.short,
        required=False,
        min_length=5,
        max_length=20,
    )

    ltmid_v2: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="ltmid_v2",
        placeholder="Paste the obtained ltmid_v2",
        style=discord.TextStyle.short,
        required=False,
        min_length=5,
        max_length=20,
    )

    ltoken_v2: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="ltoken_v2",
        placeholder="Paste the obtained ltoken_v2",
        style=discord.TextStyle.short,
        required=False,
        min_length=30,
        max_length=150,
    )

    cookie_token_v2: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="cookie_token_v2",
        placeholder="Paste the obtained cookie_token_v2.",
        style=discord.TextStyle.long,
        required=False,
        min_length=50,
        max_length=2000,
    )

    def __init__(self, games: list[genshin.Game]):
        self.games: list[genshin.Game] = games
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=EmbedTemplate.normal("Setting up, please wait..."), ephemeral=True
        )

        v2_str = ""
        cookie = ""
        if len(self.ltoken_v2.value) > 0:
            if self.ltoken_v2.value.startswith("v2"):
                v2_str = "_v2"
            cookie += f" ltoken{v2_str}={self.ltoken_v2.value};"
        if len(self.ltuid_v2.value) > 0:
            if self.ltuid_v2.value.isdigit() is True:
                cookie += f" ltuid{v2_str}={self.ltuid_v2.value};"
        if len(self.account_id_v2.value) > 0:
            if self.account_id_v2.value.isdigit() is True:
                cookie += f" account_id{v2_str}={self.account_id_v2.value};"
        if len(self.ltmid_v2.value) > 0:
            cookie += f" ltmid_v2={self.ltmid_v2.value};"
        if len(self.cookie_token_v2.value) > 0:
            cookie += f" cookie_token_v2={self.cookie_token_v2.value};"

        LOG.Info(f"Setting up {LOG.User(interaction.user)}'s Cookie: {cookie}")
        try:
            trimmed_cookie = await self._trim_cookies(cookie)
            if trimmed_cookie is None:
                raise Exception(
                    f"Invalid or incorrect Cookie. Please re-enter using {get_app_command_mention('cookie-login')} for instructions." # noqa
                )
            msg = await genshin_py.set_cookie(interaction.user.id, trimmed_cookie, self.games)
        except Exception as e:
            embed = EmbedTemplate.error(e)
            if embed.description is not None:
                embed.description += (
                    "Click [>>tutorial link<<](https://hackmd.io/66fq-6NsT1Kqxqbpkj1xTA) for solutions.\n"
                )
            await interaction.edit_original_response(embed=embed)
        else:
            await interaction.edit_original_response(embed=EmbedTemplate.normal(msg))

    async def _trim_cookies(self, cookie_string: str) -> str | None:
        """Remove unnecessary parts from the submitted Cookie content"""
        ALLOWED_COOKIES = (
            "cookie_token",
            "account_id",
            "ltoken",
            "ltuid",
            "cookie_token_v2",
            "account_id_v2",
            "ltoken_v2",
            "ltuid_v2",
            "ltmid_v2",
            "account_mid_v2",
        )
        origin: SimpleCookie[typing.Any] = SimpleCookie(cookie_string)
        cookie: SimpleCookie[typing.Any] = SimpleCookie(
            {k: v for (k, v) in origin.items() if k in ALLOWED_COOKIES}
        )
        if "cookie_token" in cookie and "account_id" in cookie:
            try:
                r = await genshin.complete_cookies(cookie, refresh=True)
                cookie.update(SimpleCookie(r))
            except Exception:
                pass

        if len(cookie) == 0:
            return None
        return cookie.output(header="", sep=" ")
