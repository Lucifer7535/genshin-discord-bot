import datetime
from typing import Optional, Sequence

import discord
import genshin

from genshin_py import parser
from utility import EmbedTemplate, config


class Dropdown(discord.ui.Select):

    def __init__(self, notices: Sequence[genshin.models.Announcement], placeholder: str):
        self.notices = notices
        options = [
            discord.SelectOption(label=notice.subtitle[:96] + "...", description=notice.title[:96] + "...", value=str(i))
            for i, notice in enumerate(notices)
        ]
        super().__init__(placeholder=placeholder, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        notice = self.notices[int(self.values[0])]
        embed = EmbedTemplate.normal(parser.parse_html_content(notice.content), title=notice.title)
        embed.set_image(url=notice.banner)
        await interaction.response.edit_message(content=None, embed=embed)


class View(discord.ui.View):
    def __init__(self):
        self.last_response_time: Optional[datetime.datetime] = None
        super().__init__(timeout=config.discord_view_long_timeout)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (
            self.last_response_time is not None
            and (interaction.created_at - self.last_response_time).seconds < 3
        ):
            await interaction.response.send_message(
                embed=EmbedTemplate.normal("For a short time (too many people), please try it for a few seconds later ..."), ephemeral=True # noqa
            )
            return False
        else:
            self.last_response_time = interaction.created_at
            return True
