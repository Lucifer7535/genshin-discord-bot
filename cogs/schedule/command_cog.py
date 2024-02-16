from datetime import datetime, time
from typing import Literal

import discord
import genshin
import sqlalchemy
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import database
from database import Database, GenshinScheduleNotes, ScheduleDailyCheckin, StarrailScheduleNotes
from utility import EmbedTemplate, get_app_command_mention
from utility.custom_log import SlashCommandLogger

from .ui import (
    DailyRewardOptionsView,
    GenshinNotesThresholdModal,
    StarrailCheckNotesThresholdModal,
)


class ScheduleCommandCog(commands.Cog, name="schedule-settings"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Set up slash commands for automatic scheduling functions
    @app_commands.command(name="schedule", description="Set up scheduling functions (Hoyolab daily check-in, resin full reminder)") # noqa
    @app_commands.rename(function="function", switch="switch")
    @app_commands.describe(function="Choose the function to execute in the schedule", switch="Choose to turn on or off this function") # noqa
    @app_commands.choices(
        function=[
            Choice(name="① Display Usage Instructions", value="HELP"),
            Choice(name="② Message Push Test", value="TEST"),
            Choice(name="★ Daily Auto Check-in", value="DAILY"),
            Choice(name="★ Instant Note Reminder (Genshin Impact)", value="GENSHIN_NOTES"),
            Choice(name="★ Instant Note Reminder (Star Rail)", value="STARRAIL_NOTES"),
        ],
        switch=[Choice(name="Turn On or Update Settings", value="ON"), Choice(name="Turn Off Function", value="OFF")],
    )
    @SlashCommandLogger
    async def slash_schedule(
        self,
        interaction: discord.Interaction,
        function: Literal["HELP", "TEST", "DAILY", "GENSHIN_NOTES", "STARRAIL_NOTES"],
        switch: Literal["ON", "OFF"],
    ):
        msg: str | None  # Message to be sent to the user
        if function == "HELP":  # Explanation of scheduling functions
            msg = (
                "· The schedule will execute functions at specific times, and the results will be pushed to the channel where the command is set.\n" # noqa
                "· Before setting, please make sure the bot has permission to speak in that channel. If the message push fails, the bot will automatically remove the schedule setting.\n" # noqa
                "· If you want to change the push channel, please reset the command in the new channel.\n\n"
                f"· Daily Auto Check-in: Automatically check-in every day according to the time you set. "
                f'Before setting, please use the {get_app_command_mention("daily-checkin")} command to check if the bot can check in for you.\n' # noqa
                f'· Instant Note Reminder: Sends a reminder when it exceeds the set value. Before setting, use {get_app_command_mention("notes")} ' # noqa
                f"to confirm that the bot can read your instant note information.\n\n"
                f"· Check-in Captcha Problem: Now there is a captcha problem with Genshin Impact check-in. You need to use "
                f"{get_app_command_mention('daily-checkin')} command, select 'Set Captcha' in the options."
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(msg, title="Explanation of Scheduling Functions"), ephemeral=True
            )
            return

        if function == "TEST":  # Test if the bot can push messages in the channel
            try:
                msg_sent = await interaction.channel.send(embed=EmbedTemplate.normal("Testing message push..."))  # type: ignore
            except Exception:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("The bot cannot push messages in this channel. Please check if the bot or this channel has 'Send Messages' and 'Embed Links' permissions.") # noqa
                )
            else:
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal("Test completed. The bot can push messages in this channel.")
                )
                await msg_sent.delete()
            return

        # Check if the user has Cookie data before setting
        user = await Database.select_one(
            database.User, database.User.discord_id.is_(interaction.user.id)
        )
        match function:
            case "DAILY":
                check, msg = await database.Tool.check_user(user)
            case "GENSHIN_NOTES":
                check, msg = await database.Tool.check_user(
                    user, check_uid=True, game=genshin.Game.GENSHIN
                )
            case "STARRAIL_NOTES":
                check, msg = await database.Tool.check_user(
                    user, check_uid=True, game=genshin.Game.STARRAIL
                )

        if check is False:
            await interaction.response.send_message(embed=EmbedTemplate.error(msg))
            return

        if function == "DAILY":  # Daily auto check-in
            if switch == "ON":  # Enable check-in function
                # Use a dropdown menu for the user to choose the game and check-in time
                options_view = DailyRewardOptionsView(interaction.user)
                await interaction.response.send_message(
                    "Please choose in order:\n"
                    "1. Games for Check-in (Multiple Selection Possible)\n"
                    "2. Check-in time\n"
                    f"3. Do you want the bot to tag you ({interaction.user.mention}) when checking in?",
                    view=options_view,
                )
                await options_view.wait()
                if options_view.selected_games is None or options_view.is_mention is None:
                    await interaction.edit_original_response(
                        embed=EmbedTemplate.normal("Cancelled"), content=None, view=None
                    )
                    return

                # Add the user
                checkin_time = datetime.combine(
                    datetime.now().date(), time(options_view.hour, options_view.minute)
                )
                checkin_user = ScheduleDailyCheckin(
                    discord_id=interaction.user.id,
                    discord_channel_id=interaction.channel_id or 0,
                    is_mention=options_view.is_mention,
                    next_checkin_time=checkin_time,
                    has_genshin=options_view.has_genshin,
                    has_honkai3rd=options_view.has_honkai3rd,
                    has_starrail=options_view.has_starrail,
                    has_themis=options_view.has_themis,
                    has_themis_tw=options_view.has_themis_tw,
                )
                if checkin_user.next_checkin_time < datetime.now():
                    checkin_user.update_next_checkin_time()
                await Database.insert_or_replace(checkin_user)

                await interaction.edit_original_response(
                    embed=EmbedTemplate.normal(
                        f"Daily auto check-in for {options_view.selected_games} has been enabled. "
                        f'The bot {"will" if options_view.is_mention else "will not"} tag you when checking in. '
                        f"The check-in time is around {options_view.hour:02d}:{options_view.minute:02d} every day."
                    ),
                    content=None,
                    view=None,
                )

            elif switch == "OFF":  # Disable check-in function
                await Database.delete(
                    ScheduleDailyCheckin, ScheduleDailyCheckin.discord_id.is_(interaction.user.id)
                )
                await interaction.response.send_message(embed=EmbedTemplate.normal("Daily auto check-in has been disabled"))

        elif function == "GENSHIN_NOTES":  # Genshin Impact instant note check reminder
            if switch == "ON":  # Enable instant note check function
                genshin_setting = await Database.select_one(
                    GenshinScheduleNotes,
                    GenshinScheduleNotes.discord_id.is_(interaction.user.id),
                )
                await interaction.response.send_modal(GenshinNotesThresholdModal(genshin_setting))
            elif switch == "OFF":  # Disable instant note check function
                await Database.delete(
                    GenshinScheduleNotes,
                    GenshinScheduleNotes.discord_id.is_(interaction.user.id),
                )
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal("Genshin Impact instant note check reminder has been disabled")
                )

        elif function == "STARRAIL_NOTES":  # Star Rail instant note check reminder
            if switch == "ON":  # Enable instant note check function
                starrail_setting = await Database.select_one(
                    StarrailScheduleNotes,
                    StarrailScheduleNotes.discord_id.is_(interaction.user.id),
                )
                await interaction.response.send_modal(
                    StarrailCheckNotesThresholdModal(starrail_setting)
                )
            elif switch == "OFF":  # Disable instant note check function
                await Database.delete(
                    StarrailScheduleNotes,
                    StarrailScheduleNotes.discord_id.is_(interaction.user.id),
                )
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal("Star Rail instant note check reminder has been disabled")
                )

    @app_commands.command(name="remove-schedule-settings", description="For administrators only, remove the schedule settings for a specific user") # noqa
    @app_commands.rename(function="function", user="user")
    @app_commands.describe(function="Choose the function to remove")
    @app_commands.choices(
        function=[
            Choice(name="Daily Auto Check-in", value="DAILY"),
            Choice(name="Instant Note Reminder (Genshin Impact)", value="GENSHIN_NOTES"),
            Choice(name="Instant Note Reminder (Star Rail)", value="STARRAIL_NOTES"),
        ]
    )
    @app_commands.default_permissions(manage_messages=True)
    @SlashCommandLogger
    async def slash_remove_user(
        self,
        interaction: discord.Interaction,
        function: Literal["DAILY", "GENSHIN_NOTES", "STARRAIL_NOTES"],
        user: discord.User,
    ):
        channel_id = interaction.channel_id
        if function == "DAILY":
            await Database.delete(
                ScheduleDailyCheckin,
                ScheduleDailyCheckin.discord_id.is_(user.id)
                & ScheduleDailyCheckin.discord_channel_id.is_(channel_id),
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(f"Daily auto check-in for {user.name} has been disabled")
            )
        elif function == "GENSHIN_NOTES":
            await Database.delete(
                GenshinScheduleNotes,
                GenshinScheduleNotes.discord_id.is_(user.id)
                & GenshinScheduleNotes.discord_channel_id.is_(channel_id),
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(f"Genshin Impact instant note check reminder for {user.name} has been disabled")
            )
        elif function == "STARRAIL_NOTES":
            await Database.delete(
                StarrailScheduleNotes,
                StarrailScheduleNotes.discord_id.is_(user.id)
                & StarrailScheduleNotes.discord_channel_id.is_(channel_id),
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(f"Star Rail instant note check reminder for {user.name} has been disabled")
            )

    @app_commands.command(name="move-schedule-messages", description="For administrators only, move the messages of all scheduled users in this channel to another channel") # noqa
    @app_commands.rename(function="function", dest_channel="destination_channel")
    @app_commands.describe(function="Choose the function to move", dest_channel="Choose the channel where you want to move the user messages notification") # noqa
    @app_commands.choices(
        function=[
            Choice(name="All", value="ALL"),
            Choice(name="Daily Auto Check-in", value="DAILY"),
            Choice(name="Instant Note Reminder (Genshin Impact)", value="GENSHIN_NOTES"),
            Choice(name="Instant Note Reminder (Star Rail)", value="STARRAIL_NOTES"),
        ]
    )
    @app_commands.default_permissions(manage_messages=True)
    @SlashCommandLogger
    async def slash_move_users(
        self,
        interaction: discord.Interaction,
        function: Literal["ALL", "DAILY", "GENSHIN_NOTES", "STARRAIL_NOTES"],
        dest_channel: discord.TextChannel | discord.Thread,
    ):
        src_channel = interaction.channel
        if src_channel is None:
            await interaction.response.send_message(embed=EmbedTemplate.error("Channel does not exist"))
            return

        stmt_daily = (
            sqlalchemy.update(ScheduleDailyCheckin)
            .where(ScheduleDailyCheckin.discord_channel_id.is_(src_channel.id))
            .values({ScheduleDailyCheckin.discord_channel_id: dest_channel.id})
        )
        stmt_gs_notes = (
            sqlalchemy.update(GenshinScheduleNotes)
            .where(GenshinScheduleNotes.discord_channel_id.is_(src_channel.id))
            .values({GenshinScheduleNotes.discord_channel_id: dest_channel.id})
        )
        stmt_st_notes = (
            sqlalchemy.update(StarrailScheduleNotes)
            .where(StarrailScheduleNotes.discord_channel_id.is_(src_channel.id))
            .values({StarrailScheduleNotes.discord_channel_id: dest_channel.id})
        )
        async with Database.sessionmaker() as session:
            if function == "ALL" or function == "DAILY":
                await session.execute(stmt_daily)
            if function == "ALL" or function == "GENSHIN_NOTES":
                await session.execute(stmt_gs_notes)
            if function == "ALL" or function == "STARRAIL_NOTES":
                await session.execute(stmt_st_notes)
            await session.commit()

        await interaction.response.send_message(
            embed=EmbedTemplate.normal(
                f"All user {function} notification messages in this channel have been successfully moved to {dest_channel.mention} channel" # noqa
            )
        )


async def setup(client: commands.Bot):
    await client.add_cog(ScheduleCommandCog(client))
