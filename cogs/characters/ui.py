from typing import Sequence, Union

import discord
import genshin

import genshin_py
from utility import config, emoji


class Dropdown(discord.ui.Select):
    """Dropdown menu for selecting characters"""

    def __init__(
        self,
        user: Union[discord.User, discord.Member],
        characters: Sequence[genshin.models.Character]
        | Sequence[genshin.models.StarRailDetailCharacter],
        index: int = 1,
    ):
        options: list[discord.SelectOption] = []
        for i, c in enumerate(characters):
            if isinstance(c, genshin.models.Character):
                option = discord.SelectOption(
                    label=f"{c.rarity}★ C{c.constellation} Lv.{c.level} {c.name}",
                    description=(
                        f"{c.weapon.rarity}★ R{c.weapon.refinement} "
                        f"Lv.{c.weapon.level} {c.weapon.name}"
                    ),
                    value=str(i),
                    emoji=emoji.elements.get(c.element.lower()),
                )
                options.append(option)
            elif isinstance(c, genshin.models.StarRailDetailCharacter):
                option = discord.SelectOption(
                    label=f"{c.rarity}★ E{c.rank} Lv.{c.level} {c.name}", value=str(i)
                )
                if c.equip is not None:
                    option.description = f"Photon Cone: S{c.equip.rank} Lv.{c.equip.level} {c.equip.name}"
                options.append(option)

        super().__init__(
            placeholder=f"Select a character (from {index} to {index + len(characters) - 1})",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.user = user
        self.characters = characters

    async def callback(self, interaction: discord.Interaction):
        c = self.characters[int(self.values[0])]
        if isinstance(c, genshin.models.Character):
            embed = genshin_py.parse_genshin_character(c)
        else:
            embed = genshin_py.parse_starrail_character(c)
        embed.set_author(
            name=f"{self.user.display_name}'s Character Overview",
            icon_url=self.user.display_avatar.url,
        )
        await interaction.response.edit_message(content=None, embed=embed)


class DropdownView(discord.ui.View):
    """View displaying a dropdown menu of characters, divided based on the limit of menu items (25)"""

    def __init__(
        self,
        user: Union[discord.User, discord.Member],
        characters: Sequence[genshin.models.Character]
        | Sequence[genshin.models.StarRailDetailCharacter],
    ):
        super().__init__(timeout=config.discord_view_long_timeout)
        max_row = 25
        for i in range(0, len(characters), max_row):
            self.add_item(Dropdown(user, characters[i : i + max_row], i + 1))
