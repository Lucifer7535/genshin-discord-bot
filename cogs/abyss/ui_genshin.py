import asyncio
from typing import Literal, Optional, Sequence, Union

import discord
import genshin

import genshin_py
from database import Database, GenshinSpiralAbyss
from utility import EmbedTemplate, config


class AbyssRecordDropdown(discord.ui.Select):
    """Dropdown menu for selecting historical Spiral Abyss records"""

    def __init__(
        self,
        user: Union[discord.User, discord.Member],
        abyss_data_list: Sequence[GenshinSpiralAbyss],
    ):
        def honor(abyss: genshin.models.SpiralAbyss) -> str:
            """Check for special records such as 12-3 clear, single clear, and double clear"""
            if abyss.total_stars == 36:
                if abyss.total_battles == 12:
                    return "(👑)"
                last_battles = abyss.floors[-1].chambers[-1].battles
                num_of_characters = max(
                    len(last_battles[0].characters), len(last_battles[1].characters)
                )
                if num_of_characters == 2:
                    return "(Double Clear)"
                if num_of_characters == 1:
                    return "(Single Clear)"
            return ""

        options = [
            discord.SelectOption(
                label=f"[Season {abyss.season}] {abyss.abyss.total_stars}★  {honor(abyss.abyss)}",
                description=(
                    f"{abyss.abyss.start_time.astimezone().strftime('%Y.%m.%d')} ~ "
                    f"{abyss.abyss.end_time.astimezone().strftime('%Y.%m.%d')}"
                ),
                value=str(i),
            )
            for i, abyss in enumerate(abyss_data_list)
        ]
        super().__init__(placeholder="Select Season:", options=options)
        self.user = user
        self.abyss_data_list = abyss_data_list

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        index = int(self.values[0])
        await SpiralAbyssUI.presentation(
            interaction, self.user, self.abyss_data_list[index], view_item=self
        )


class AbyssFloorDropdown(discord.ui.Select):
    """Dropdown menu for selecting Spiral Abyss floors"""

    def __init__(
        self,
        overview: discord.Embed,
        abyss_data: GenshinSpiralAbyss,
        save_or_remove: Literal["SAVE", "REMOVE"],
    ):
        # The first option is displayed as save or remove record based on the parameter
        _description = "Save this record to database, can be viewed later" if save_or_remove == "SAVE" else "Delete from database"
        option = [
            discord.SelectOption(
                label=f"{'📁 Save Record' if save_or_remove == 'SAVE' else '❌ Remove Record'}",
                description=_description,
                value=save_or_remove,
            )
        ]
        options = option + [
            discord.SelectOption(
                label=f"[{floor.stars}]★ Floor {floor.floor}",
                description=genshin_py.parse_genshin_abyss_chamber(floor.chambers[-1]),
                value=str(i),
            )
            for i, floor in enumerate(abyss_data.abyss.floors)
        ]
        super().__init__(placeholder="Select Floor:", options=options)
        self.embed = overview
        self.abyss_data = abyss_data
        self.save_or_remove = save_or_remove

    async def callback(self, interaction: discord.Interaction):
        # Save or remove Spiral Abyss data
        if self.values[0] == self.save_or_remove:
            # Check if the interactor is the owner of the Spiral Abyss data
            if interaction.user.id == self.abyss_data.discord_id:
                if self.save_or_remove == "SAVE":
                    await Database.insert_or_replace(self.abyss_data)
                    await interaction.response.send_message(
                        embed=EmbedTemplate.normal("Record saved successfully"), ephemeral=True
                    )
                else:  # self.save_or_remove == 'REMOVE'
                    await Database.delete_instance(self.abyss_data)
                    await interaction.response.send_message(
                        embed=EmbedTemplate.normal("Record deleted successfully"), ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("This action is limited to the owner only"), ephemeral=True
                )
        else:  # Draw floor image
            await interaction.response.defer()
            fp = await genshin_py.draw_abyss_card(
                self.abyss_data.abyss.floors[int(self.values[0])],
                self.abyss_data.characters,
            )
            fp.seek(0)
            self.embed.set_image(url="attachment://image.jpeg")
            await interaction.edit_original_response(
                embed=self.embed, attachments=[discord.File(fp, "image.jpeg")]
            )


class SpiralAbyssUI:
    """Spiral Abyss"""

    @staticmethod
    async def presentation(
        interaction: discord.Interaction,
        user: Union[discord.User, discord.Member],
        abyss_data: GenshinSpiralAbyss,
        *,
        view_item: Optional[discord.ui.Item] = None,
    ):
        embed = genshin_py.parse_genshin_abyss_overview(abyss_data.abyss)
        embed.title = f"{user.display_name}'s Spiral Abyss Record"
        embed.set_thumbnail(url=user.display_avatar.url)
        view = None
        if len(abyss_data.abyss.floors) > 0:
            view = discord.ui.View(timeout=config.discord_view_short_timeout)
            if view_item:  # Get data from historical records, so the first option is to delete the record
                view.add_item(AbyssFloorDropdown(embed, abyss_data, "REMOVE"))
                view.add_item(view_item)
            else:  # Get data from Hoyolab, so the first option is to save the record
                view.add_item(AbyssFloorDropdown(embed, abyss_data, "SAVE"))
        await interaction.edit_original_response(embed=embed, view=view, attachments=[])

    @staticmethod
    async def abyss(
        interaction: discord.Interaction,
        user: Union[discord.User, discord.Member],
        season_choice: Literal["THIS_SEASON", "PREVIOUS_SEASON", "HISTORICAL_RECORD"],
    ):
        if season_choice == "HISTORICAL_RECORD":  # Query historical records
            abyss_data_list = await Database.select_all(
                GenshinSpiralAbyss,
                GenshinSpiralAbyss.discord_id.is_(user.id),
            )
            if len(abyss_data_list) == 0:
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal("This user has no saved historical records")
                )
            else:
                abyss_data_list = sorted(abyss_data_list, key=lambda x: x.season, reverse=True)
                view = discord.ui.View(timeout=config.discord_view_short_timeout)
                # Display up to 25 data at a time, so display in batches
                for i in range(0, len(abyss_data_list), 25):
                    view.add_item(AbyssRecordDropdown(user, abyss_data_list[i : i + 25]))
                await interaction.response.send_message(view=view)
        else:  # Query Hoyolab records (THIS_SEASON, PREVIOUS_SEASON)
            try:
                defer, abyss_data = await asyncio.gather(
                    interaction.response.defer(),
                    genshin_py.get_genshin_spiral_abyss(
                        user.id, (season_choice == "PREVIOUS_SEASON")
                    ),
                )
            except Exception as e:
                await interaction.edit_original_response(embed=EmbedTemplate.error(e))
            else:
                await SpiralAbyssUI.presentation(interaction, user, abyss_data)
