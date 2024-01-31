from typing import Union

import discord


class EmbedTemplate:
    @staticmethod
    def normal(message: str, **kwargs) -> discord.Embed:
        return discord.Embed(color=0x7289DA, description=message, **kwargs)

    @staticmethod
    def error(exception: Union[Exception, str], **kwargs) -> discord.Embed:
        embed = discord.Embed(color=0xB54031, **kwargs)
        embed.description = str(exception)

        if "title" not in kwargs:
            embed.title = "An error occurred!"

        return embed
