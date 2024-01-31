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
            embed = EmbedTemplate.normal(
                "**1.** Copy the entire code at the bottom of this message\n"
                "**2.** Open [Hoyolab Official Website](https://www.hoyolab.com) on **Chrome** on PC or mobile, log in, go to Toolbox, and then Records to view your character page\n"
                "**3.** Paste the code into the address bar after entering `java`, as shown below\n"
                "**4.** Press Enter, the webpage will display your Cookie, select all and copy\n"
                f"**5.** Use the command {get_app_command_mention('cookie-login')} here to submit the obtained Cookie\n"
                "． https://imgur.com/a/C4l67BW\n",
                title="Genshin Helper | Instructions to Obtain Cookie",
            )
            #embed.set_image(url="https://i.imgur.com/OQ8arx0.gif")
            code_msg = "script: document.write(document.cookie)"
            await interaction.response.send_message(embed=embed)
            await interaction.followup.send(content=code_msg)

        elif option == 1:  # Submit obtained Cookie to the bot
            view = GameSelectionView()
            await interaction.response.send_message(
                embed=EmbedTemplate.normal("Please choose the game to set the Cookie, different games can have different account Cookies"),
                view=view,
                ephemeral=True,
            )

        elif option == 2:  # Show bot's Cookie usage and storage information
            msg = (
                "· The content of the Cookie includes your personal identification code and does not include your account and password\n"
                "· Therefore, it cannot be used to log in to the game or change the account password. The content of the Cookie looks like this:\n"
                "`ltoken=xxxx ltuid=1234 cookie_token=yyyy account_id=1234`\n"
                "· The bot saves and uses the Cookie to get your Genshin data on the Hoyolab website and provide services\n"
                "· The bot stores data in a cloud-hosted environment, only connecting to Discord and Hoyolab servers\n"
                "· For more detailed information, you can check the [Bahamut Forum Post (in Chinese)](https://forum.gamer.com.tw/Co.php?bsn=36730&sn=162433)."
                "If you still have concerns, please refrain from using the bot\n"
                "· When you submit the Cookie to the bot, you agree to the bot storing and using your data\n"
                f'· You can delete the data stored in the bot at any time. Please use the command {get_app_command_mention("clear-data")}\n'
            )
            embed = EmbedTemplate.normal(msg, title="Genshin Helper | Cookie Usage and Storage Information")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot):
    await client.add_cog(CookieSettingCog(client))
