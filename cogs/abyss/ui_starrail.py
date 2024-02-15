import enum
import typing

import discord

import genshin_py
from database import Database, StarrailForgottenHall, StarrailPureFiction, User
from utility import EmbedTemplate, config


class AbyssMode(str, enum.Enum):
    """Abyss modes for Star Rail"""

    FORGOTTEN_HALL = "forgotten_hall"
    """Forgotten Hall"""
    PURE_FICTION = "pure_fiction"
    """Pure Fiction"""


# Make a discord button to choose which mode
class ChooseAbyssModeButton(discord.ui.View):
    """Button to choose Abyss mode for Star Rail"""

    def __init__(self):
        super().__init__(timeout=config.discord_view_short_timeout)
        self.value = None

    @discord.ui.button(label="Forgotten Hall", style=discord.ButtonStyle.blurple)
    async def forgotten_hall(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = AbyssMode.FORGOTTEN_HALL
        self.stop()

    @discord.ui.button(label="Pure Fiction", style=discord.ButtonStyle.blurple)
    async def pure_fiction(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = AbyssMode.PURE_FICTION
        self.stop()


class HallRecordDropdown(discord.ui.Select):
    """Dropdown to select historical records for Forgotten Hall or Pure Fiction"""

    def __init__(
        self,
        user: discord.User | discord.Member,
        nickname: str,
        uid: int,
        hall_data_list: typing.Sequence[StarrailForgottenHall]
        | typing.Sequence[StarrailPureFiction],
    ):
        sorted_hall_data_list = sorted(
            hall_data_list, key=lambda x: x.data.begin_time.datetime, reverse=True
        )
        options = [
            discord.SelectOption(
                label=f"[{hall.data.begin_time.datetime.strftime('%Y.%m.%d')} ~ "
                f"{hall.data.end_time.datetime.strftime('%Y.%m.%d')}] {hall.data.total_stars}★",
                value=str(i),
            )
            for i, hall in enumerate(sorted_hall_data_list)
        ]
        super().__init__(placeholder="Select Season:", options=options)
        self.user = user
        self.nickname = nickname
        self.uid = uid
        self.hall_data_list = sorted_hall_data_list

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        index = int(self.values[0])
        await ForgottenHallUI.present(
            interaction,
            self.user,
            self.nickname,
            self.uid,
            self.hall_data_list[index],
            view_item=self,
        )


class HallFloorDropdown(discord.ui.Select):
    """Dropdown to select floors for Forgotten Hall or Pure Fiction"""

    def __init__(
        self,
        overview: discord.Embed,
        avatar: bytes,
        nickname: str,
        uid: int,
        hall_data: StarrailForgottenHall | StarrailPureFiction,
        save_or_remove: typing.Literal["SAVE", "REMOVE"],
    ):
        # The first option shows either Save or Remove based on the parameter
        _descr = "Save this record to database, can be viewed later" if save_or_remove == "SAVE" else "Delete from database"
        options = [
            discord.SelectOption(
                label=f"{'📁 Save Record' if save_or_remove == 'SAVE' else '❌ Remove Record'}",
                description=_descr,
                value=save_or_remove,
            )
        ]
        options += [
            discord.SelectOption(
                label=f"[{floor.star_num}★] {floor.name}",
                value=str(i),
            )
            for i, floor in enumerate(hall_data.data.floors)
        ]

        super().__init__(
            placeholder="Select Floor(s):",
            options=options,
            max_values=(min(3, len(hall_data.data.floors))),
        )
        self.embed = overview
        self.avatar = avatar
        self.nickname = nickname
        self.uid = uid
        self.hall_data = hall_data
        self.save_or_remove = save_or_remove

    async def callback(self, interaction: discord.Interaction):
        # Save or remove Forgotten Hall data
        if self.save_or_remove in self.values:
            # Check if the interacted user is the owner of the Forgotten Hall data
            if interaction.user.id == self.hall_data.discord_id:
                if self.save_or_remove == "SAVE":
                    await Database.insert_or_replace(self.hall_data)
                    await interaction.response.send_message(
                        embed=EmbedTemplate.normal("The challenge record has been saved"), ephemeral=True
                    )
                else:  # self.save_or_remove == 'REMOVE'
                    await Database.delete_instance(self.hall_data)
                    await interaction.response.send_message(
                        embed=EmbedTemplate.normal("The challenge record has been removed"), ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("Only the owner can perform this action"), ephemeral=True
                )
        else:  # Draw floor image
            await interaction.response.defer()
            values = sorted(self.values, key=lambda x: int(x))
            floors = [self.hall_data.data.floors[int(value)] for value in values]
            fp = await genshin_py.draw_starrail_forgottenhall_card(
                self.avatar, self.nickname, self.uid, self.hall_data.data, floors
            )
            fp.seek(0)
            self.embed.set_image(url="attachment://image.jpeg")
            await interaction.edit_original_response(
                embed=self.embed, attachments=[discord.File(fp, "image.jpeg")]
            )


class ForgottenHallUI:
    @staticmethod
    async def present(
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
        nickname: str,
        uid: int,
        hall_data: StarrailForgottenHall | StarrailPureFiction,
        *,
        view_item: discord.ui.Item | None = None,
    ):
        if isinstance(hall_data, StarrailForgottenHall):
            title = "Forgotten Hall"
        else:  # isinstance(hall_data, StarrailPureFiction)
            title = "Pure Fiction"
        hall = hall_data.data
        embed = genshin_py.parse_starrail_hall_overview(hall)
        embed.title = f"{user.display_name}'s {title} Records"
        embed.set_thumbnail(url=user.display_avatar.url)
        view = None
        if len(hall.floors) > 0:
            view = discord.ui.View(timeout=config.discord_view_short_timeout)
            avatar = await user.display_avatar.read()
            if view_item:  # Retrieve data from historical records, so the first option is to remove the record
                view.add_item(HallFloorDropdown(embed, avatar, nickname, uid, hall_data, "REMOVE"))
                view.add_item(view_item)
            else:  # Retrieve data from Hoyolab, so the first option is to save the record
                view.add_item(HallFloorDropdown(embed, avatar, nickname, uid, hall_data, "SAVE"))
        await interaction.edit_original_response(embed=embed, view=view, attachments=[])

    @staticmethod
    async def launch(
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
        mode: AbyssMode,
        season_choice: typing.Literal["THIS_SEASON", "PREVIOUS_SEASON", "HISTORICAL_RECORD"],
    ):
        try:
            userstats = await genshin_py.get_starrail_userstats(user.id)
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e), view=None)
            return

        nickname = userstats.info.nickname
        _u = await Database.select_one(User, User.discord_id == user.id)
        uid = _u.uid_starrail if _u else 0
        uid = uid or 0

        if season_choice == "HISTORICAL_RECORD":  # Query historical records
            if mode == AbyssMode.FORGOTTEN_HALL:
                hall_data_list = await Database.select_all(
                    StarrailForgottenHall,
                    StarrailForgottenHall.discord_id.is_(user.id),
                )
            else:  # mode == AbyssMode.PURE_FICTION
                hall_data_list = await Database.select_all(
                    StarrailPureFiction,
                    StarrailPureFiction.discord_id.is_(user.id),
                )
            if len(hall_data_list) == 0:
                await interaction.edit_original_response(
                    embed=EmbedTemplate.normal("This user has no saved historical records"),
                    view=None,
                )
            else:
                view = discord.ui.View(timeout=config.discord_view_short_timeout)
                view.add_item(HallRecordDropdown(user, nickname, uid, hall_data_list))
                await interaction.edit_original_response(view=view)
        else:  # Query Hoyolab records (THIS_SEASON, PREVIOUS_SEASON)
            try:
                if mode == AbyssMode.FORGOTTEN_HALL:
                    hall = await genshin_py.get_starrail_forgottenhall(
                        user.id, (season_choice == "PREVIOUS_SEASON")
                    )
                    hall_data = StarrailForgottenHall(user.id, hall.season, hall)
                else:  # mode == AbyssMode.PURE_FICTION
                    hall = await genshin_py.get_starrail_pure_fiction(
                        user.id, (season_choice == "PREVIOUS_SEASON")
                    )
                    hall_data = StarrailPureFiction(user.id, hall.season_id, hall)
            except Exception as e:
                await interaction.edit_original_response(embed=EmbedTemplate.error(e), view=None)
            else:
                await ForgottenHallUI.present(interaction, user, nickname, uid, hall_data)
