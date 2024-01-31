import discord

from utility import config


class ConfirmButton(discord.ui.View):
    """Confirmation button for clearing data"""

    def __init__(self):
        super().__init__(timeout=config.discord_view_short_timeout)
        self.value = None

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = False
        self.stop()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = True
        self.stop()
