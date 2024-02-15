import asyncio
from typing import Any, Callable, Optional, Union

import discord
import enkanetwork
import sentry_sdk

from database import Database, GenshinShowcase, User
from enka_network import Showcase, enka_assets
from utility import EmbedTemplate, config, emoji, get_app_command_mention
from utility.custom_log import LOG


class ShowcaseCharactersDropdown(discord.ui.Select):
    """Character Showcase Dropdown Menu"""

    showcase: Showcase

    def __init__(self, showcase: Showcase) -> None:
        self.showcase = showcase
        options = [discord.SelectOption(label="Player Overview", value="-1", emoji="📜")]
        for i, character in enumerate(showcase.data.player.characters_preview):  # type: ignore
            element = {
                enkanetwork.ElementType.Pyro: "pyro",
                enkanetwork.ElementType.Electro: "electro",
                enkanetwork.ElementType.Hydro: "hydro",
                enkanetwork.ElementType.Cryo: "cryo",
                enkanetwork.ElementType.Dendro: "dendro",
                enkanetwork.ElementType.Anemo: "anemo",
                enkanetwork.ElementType.Geo: "geo",
            }.get(character.element, "")
            _assets_character = enka_assets.character(character.id)
            _rarity = _assets_character.rarity if _assets_character else "?"

            options.append(
                discord.SelectOption(
                    label=f"{_rarity}★ Lv.{character.level} {character.name}",
                    value=str(i),
                    emoji=emoji.elements.get(element),
                )
            )
        options.append(discord.SelectOption(label="Delete Character Cache Data", value="-2", emoji="❌"))
        super().__init__(placeholder="Choose character to showcase:", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        index = int(self.values[0])
        if index >= 0:  # Character data
            await GenerateImageButton.handle_image_response(interaction, self.showcase, index)
            await interaction.edit_original_response(view=ShowcaseView(self.showcase, index))
        elif index == -1:  # Player Overview
            embed = self.showcase.get_player_overview_embed()
            await interaction.response.edit_message(
                embed=embed, view=ShowcaseView(self.showcase), attachments=[]
            )
        elif index == -2:  # Delete Cache Data
            # Check if the interaction user's UID matches the showcase UID
            user = await Database.select_one(User, User.discord_id.is_(interaction.user.id))
            if user is None or user.uid_genshin != self.showcase.uid:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("Not the owner of this UID, cannot delete data"), ephemeral=True
                )
            elif user.cookie_genshin is None:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("Cookie not set, unable to verify owner of this UID, cannot delete data"),
                    ephemeral=True,
                )
            else:
                embed = self.showcase.get_player_overview_embed()
                await Database.delete(
                    GenshinShowcase,
                    GenshinShowcase.uid.is_(self.showcase.uid),
                )
                await interaction.response.edit_message(embed=embed, view=None, attachments=[])


class ShowcaseButton(discord.ui.Button):
    """Character Showcase Button"""

    def __init__(self, label: str, function: Callable[..., discord.Embed], *args, **kwargs):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.callback_func = function
        self.callback_args = args
        self.callback_kwargs = kwargs

    async def callback(self, interaction: discord.Interaction) -> Any:
        embed = self.callback_func(*self.callback_args, **self.callback_kwargs)
        await interaction.response.edit_message(embed=embed, attachments=[])


class GenerateImageButton(discord.ui.Button):
    """Generate Image Button"""

    def __init__(self, showcase: Showcase, character_index: int):
        super().__init__(style=discord.ButtonStyle.primary, label="Image")
        self.showcase = showcase
        self.character_index = character_index

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.handle_image_response(interaction, self.showcase, self.character_index)

    @classmethod
    async def handle_image_response(
        cls, interaction: discord.Interaction, showcase: Showcase, character_index: int
    ) -> None:
        """Generate character image, handle discord interaction response by sending embed to the user"""
        embed = showcase.get_default_embed(character_index)
        _, image = await asyncio.gather(
            interaction.response.edit_message(embed=embed, attachments=[]),
            showcase.get_image(character_index),
        )
        if image is not None:
            embed.set_thumbnail(url=None)
            embed.set_image(url="attachment://image.jpeg")
            await interaction.edit_original_response(
                embed=embed, attachments=[discord.File(image, "image.jpeg")]
            )


class ShowcaseView(discord.ui.View):
    """Character Showcase View, display character panel image, artifact stat button, and character dropdown menu"""

    def __init__(self, showcase: Showcase, character_index: Optional[int] = None):
        super().__init__(timeout=config.discord_view_long_timeout)
        if character_index is not None:
            self.add_item(GenerateImageButton(showcase, character_index))
            self.add_item(ShowcaseButton("Character Stats", showcase.get_character_stat_embed, character_index))
            self.add_item(ShowcaseButton("Artifacts Stats", showcase.get_artifact_stat_embed, character_index))

        if showcase.data.player.characters_preview:  # type: ignore
            self.add_item(ShowcaseCharactersDropdown(showcase))


async def showcase(
    interaction: discord.Interaction,
    user: Union[discord.User, discord.Member],
    uid: Optional[int] = None,
):
    await interaction.response.defer()
    _user = await Database.select_one(User, User.discord_id.is_(user.id))
    uid = uid or (_user.uid_genshin if _user else None)
    if uid is None:
        await interaction.edit_original_response(
            embed=EmbedTemplate.error(
                f"Please use {get_app_command_mention('uid-settings')} first, or directly input the UID to be queried in the uid parameter of the command", # noqa
                title="UID not found",
            )
        )
    elif len(str(uid)) != 9 or str(uid)[0] not in ["1", "2", "5", "6", "7", "8", "9"]:
        await interaction.edit_original_response(embed=EmbedTemplate.error("Invalid UID format"))
    else:
        showcase = Showcase(uid)
        try:
            await showcase.load_data()
            view = ShowcaseView(showcase)
            embed = showcase.get_player_overview_embed()
            await interaction.edit_original_response(embed=embed, view=view)
        except Exception as e:
            LOG.ErrorLog(interaction, e)
            sentry_sdk.capture_exception(e)

            embed = EmbedTemplate.error(
                str(e) + f"\nYou can click [link]({showcase.url}) to check the website status", title=f"UID: {uid}"
            )
            await interaction.edit_original_response(embed=embed)
