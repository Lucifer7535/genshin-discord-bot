import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from utility import EmbedTemplate, custom_log, get_app_command_mention

from .ui import GameSelectionView


class CookieSettingCog(commands.Cog, name="cookie-login"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="cookie-login", description="Login using cookie to use the bot.")
    @app_commands.rename(option="option")
    @app_commands.choices(
        option=[
            Choice(name="① Show instructions on how to get Cookie", value=0),
            Choice(name="② Submit obtained Cookie to the bot", value=1),
            Choice(name="③ Show bot's Cookie usage and storage information", value=2),
        ]
    )
    @custom_log.SlashCommandLogger
    async def slash_cookie(self, interaction: discord.Interaction, option: int):
        if option == 0:  # Show instructions on how to get Cookie
            embed1 = EmbedTemplate.normal(
                "**1.** Open [HoYoLAB official website](https://www.hoyolab.com) in an **incognito window** using your **computer** browser and log in to your account.\n" # noqa
                "**2.** Press **F12** to open the browser developer tools.\n"
                "**3.** Switch to the **Application** tab (refer to the image below).\n"
                "**4.** Click on the URL under Cookies on the left, and you will see your Cookie on the right.\n"
                "**5.** Find **ltuid_v2**, **ltoken_v2**, **ltmid_v2**, and copy the values of these three fields.\n"
                f"**6.** Use the command {get_app_command_mention('cookie-login')} here and paste the values into the corresponding fields.", # noqa
                title="Genshin Helper Bot | Instructions for Obtaining Cookies",
            )
            embed1.set_image(url="https://i.imgur.com/2JVM3ub.png")
            await interaction.response.send_message(embed=embed1)
            embed2 = EmbedTemplate.normal(
                "**7.** If you don't have access to a computer/laptop, you can use [Kiwi browser](https://play.google.com/store/apps/details?id=com.kiwibrowser.browser&hl=en&gl=US&pli=1) and do the steps as shown below:", # noqa
                title="Genshin Helper Bot | Instructions for Obtaining Cookies (Kiwi Browser)",
            )
            embed2.set_image(url="https://i.imgur.com/wceWJvG.png")
            await interaction.followup.send(embed=embed2)

        elif option == 1:  # Submit obtained Cookie to the bot
            view = GameSelectionView()
            await interaction.response.send_message(
                embed=EmbedTemplate.normal("Please choose the game to set the Cookie, different games can have different account Cookies."), # noqa
                view=view,
                ephemeral=True,
            )

        elif option == 2:  # Show bot's Cookie usage and storage information
            msg = (
                "· The content of the Cookie includes your personal identification code and does not include your account and password\n" # noqa
                "· Therefore, it cannot be used to log in to the game or change the account password. The content of the Cookie looks like this:\n" # noqa
                "ltoken_v2=xxxx ltuid_v2=1234 ltmid_v2=yyyy"
                "· The bot saves and uses the Cookie to get your Genshin data on the Hoyolab website and provide services\n"
                "· The bot stores data in a cloud-hosted environment, only connecting to Discord and Hoyolab servers\n"
                "If you still have concerns, please refrain from using the bot\n"
                "· When you submit the Cookie to the bot, you agree to the bot storing and using your data\n"
                f'· You can delete the data stored in the bot at any time. Please use the command {get_app_command_mention("clear-user-data")}\n' # noqa
            )
            embed = EmbedTemplate.normal(msg, title="Genshin Helper Bot | Cookie Usage and Storage Information")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot):
    await client.add_cog(CookieSettingCog(client))
