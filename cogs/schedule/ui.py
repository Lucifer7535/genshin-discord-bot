from datetime import date, datetime, time, timedelta
from typing import overload

import discord

from database import Database, GenshinScheduleNotes, StarrailScheduleNotes
from utility import EmbedTemplate, config


class DailyRewardOptionsView(discord.ui.View):

    def __init__(self, author: discord.User | discord.Member):
        super().__init__(timeout=config.discord_view_short_timeout)
        self.selected_games: str | None = None
        self.has_genshin: bool = False
        self.has_honkai3rd: bool = False
        self.has_starrail: bool = False
        self.has_themis: bool = False
        self.has_themis_tw: bool = False
        self.hour: int = 8
        self.minute: int = 0
        self.is_mention: bool | None = None
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    @discord.ui.select(
        cls=discord.ui.Select,
        options=[
            discord.SelectOption(label="Genshin Impact", value="Genshin Impact"),
            discord.SelectOption(label="Honkai Impact 3", value="Honkai Impact 3"),
            discord.SelectOption(label="Star Rail", value="Star Rail"),
            discord.SelectOption(label="Tears of Themis(GLOBAL)", value="Tears of Themis(GLOBAL)"),
            discord.SelectOption(label="Tears of Themis(TW)", value="Tears of Themis(TW)"),
        ],

        min_values=1,
        max_values=5,
        placeholder="Please choose the game(s) to sign in (multiple selections allowed):"
    )
    async def select_games_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()
        self.selected_games = " + ".join(select.values)
        if "Genshin Impact" in self.selected_games:
            self.has_genshin = True
        if "Honkai Impact 3" in self.selected_games:
            self.has_honkai3rd = True
        if "Star Rail" in self.selected_games:
            self.has_starrail = True
        if "Tears of Themis(GLOBAL)" in self.selected_games:
            self.has_themis = True
        if "Tears of Themis(TW)" in self.selected_games:
            self.has_themis_tw = True

    @discord.ui.select(
        cls=discord.ui.Select,
        options=[discord.SelectOption(label=str(i).zfill(2), value=str(i)) for i in range(0, 24)],
        min_values=0,
        max_values=1,
        placeholder="Please choose the signin time (hour):"
    )
    async def select_hour_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()
        if len(select.values) > 0:
            self.hour = int(select.values[0])

    @discord.ui.select(
        cls=discord.ui.Select,
        options=[
            discord.SelectOption(label=str(i).zfill(2), value=str(i)) for i in range(0, 60, 5)
        ],
        min_values=0,
        max_values=1,
        placeholder="Please choose the signin time (minute):"
    )
    async def select_minute_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()
        if len(select.values) > 0:
            self.minute = int(select.values[0])

    @discord.ui.button(label="Request Tag", style=discord.ButtonStyle.blurple)
    async def button1_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.is_mention = True
        self.stop()

    @discord.ui.button(label="No Tag Needed", style=discord.ButtonStyle.blurple)
    async def button2_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.is_mention = False
        self.stop()


class BaseNotesThresholdModal(discord.ui.Modal):
    def _int_to_str(self, value: int | None) -> str | None:
        return str(value) if isinstance(value, int) else None

    def _str_to_int(self, value: str) -> int | None:
        return int(value) if len(value) > 0 else None

    @overload
    def _to_msg(self, title: str, value: int | None, date_frequency: str = "Everyday") -> str:
        ...

    @overload
    def _to_msg(self, title: str, value: datetime | None, date_frequency: str = "Everyday") -> str:
        ...

    def _to_msg(self, title: str, value: int | datetime | None, date_frequency: str = "Everyday") -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return f". {title}: {date_frequency} {value.strftime('%H:%M')} Check\n"
        if value == 0:
            return f". {title}: Reminder upon completion\n"
        else:
            return f". {title}: Reminder {value} hours before completion\n"


class GenshinNotesThresholdModal(BaseNotesThresholdModal, title="Set Genshin Impact Instant Reminder"):
    resin: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Original Resin",
        placeholder="Please enter an integer between 0 and 8",
        required=False,
        max_length=1,

    )
    realm_currency: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Realm Currency",
        placeholder="Please enter an integer between 0 and 24",
        required=False,
        max_length=2,
    )
    transformer: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Parametric Transformer",
        placeholder="Please enter an integer between 0 and 5",
        required=False,
        max_length=1,
    )

    expedition: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Expedition",
        placeholder="Please enter an integer between 0 and 5",
        required=False,
        max_length=1,
    )

    commission: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Daily Commissions",
        placeholder="Please enter a time between 0000 and 2359, for example, 0200, 2135",
        required=False,
        max_length=4,
        min_length=4,
    )

    def __init__(self, user_setting: GenshinScheduleNotes | None = None) -> None:
        self.resin.default = "1"
        self.realm_currency.default = None
        self.transformer.default = None
        self.expedition.default = None
        self.commission.default = None

        if user_setting:
            self.resin.default = self._int_to_str(user_setting.threshold_resin)
            self.realm_currency.default = self._int_to_str(user_setting.threshold_currency)
            self.transformer.default = self._int_to_str(user_setting.threshold_transformer)
            self.expedition.default = self._int_to_str(user_setting.threshold_expedition)
            self.commission.default = (
                user_setting.check_commission_time.strftime("%H%M")
                if user_setting.check_commission_time
                else None
            )
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            resin = self._str_to_int(self.resin.value)
            realm_currency = self._str_to_int(self.realm_currency.value)
            transformer = self._str_to_int(self.transformer.value)
            expedition = self._str_to_int(self.expedition.value)
            commission = self._str_to_int(self.commission.value)

            if (
                resin is None
                and realm_currency is None
                and transformer is None
                and expedition is None
                and commission is None
            ):
                raise ValueError()
            if (
                (isinstance(resin, int) and not (0 <= resin <= 8))
                or (isinstance(realm_currency, int) and not (0 <= realm_currency <= 24))
                or (isinstance(transformer, int) and not (0 <= transformer <= 5))
                or (isinstance(expedition, int) and not (0 <= expedition <= 5))
            ):
                raise ValueError()
            commission_time = None
            if isinstance(commission, int):
                _time = time(commission // 100, commission % 100)
                _date = date.today()
                commission_time = datetime.combine(_date, _time)
                if commission_time < datetime.now():
                    commission_time += timedelta(days=1)
        except Exception:
            await interaction.response.send_message(
                embed=EmbedTemplate.error("Input value is incorrect. Please make sure the input is an integer within the specified range."), # noqa
                ephemeral=True,
            )
        else:
            await Database.insert_or_replace(
                GenshinScheduleNotes(
                    discord_id=interaction.user.id,
                    discord_channel_id=interaction.channel_id or 0,
                    threshold_resin=resin,
                    threshold_currency=realm_currency,
                    threshold_transformer=transformer,
                    threshold_expedition=expedition,
                    check_commission_time=commission_time,
                )
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(
                f"Genshin settings are configured. You will receive reminder messages when the following thresholds are reached:\n" # noqa
                f"{self._to_msg('Original Resin', resin)}" # noqa
                f"{self._to_msg('Realm Currency', realm_currency)}" # noqa
                f"{self._to_msg('Transformer', transformer)}" # noqa
                f"{self._to_msg('Expedition', expedition)}" # noqa
                f"{self._to_msg('Daily Commission', commission_time)}" # noqa
            ) # noqa

            )


class StarrailCheckNotesThresholdModal(BaseNotesThresholdModal, title="Set Starrail Check Instant Reminder"):

    power: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Development Power: Set hours before full power for reminder (Leave blank for no reminder)",
        placeholder="Please enter an integer between 0 and 8",
        required=False,
        max_length=1,
    )

    expedition: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Missions: Set hours before all missions are completed for reminder (Leave blank for no reminder)",
        placeholder="Please enter an integer between 0 and 5",
        required=False,
        max_length=1,
    )

    dailytraining: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Daily Training: Set the time to remind about incomplete daily training (Leave blank for no reminder)",
        placeholder="Please enter a time between 0000 and 2359, for example, 0200, 2135",
        required=False,
        max_length=4,
        min_length=4,
    )

    universe: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Simulated Universe: Set the time on Sundays to remind about incomplete weekly simulated universe (Leave blank for no reminder)", # noqa
        placeholder="Please enter a time between 0000 and 2359, for example, 0200, 2135",
        required=False,
        max_length=4,
        min_length=4,
    )

    echoofwar: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Echo of War: Set the time on Sundays to remind about incomplete weekly echo of war (Leave blank for no reminder)",
        placeholder="Please enter a time between 0000 and 2359, for example, 0200, 2135",
        required=False,
        max_length=4,
        min_length=4,
    )

    def __init__(self, user_setting: StarrailScheduleNotes | None = None):
        self.power.default = "1"
        self.expedition.default = None
        self.dailytraining.default = None

        if user_setting:
            self.power.default = self._int_to_str(user_setting.threshold_power)
            self.expedition.default = self._int_to_str(user_setting.threshold_expedition)
            self.dailytraining.default = (
                user_setting.check_daily_training_time.strftime("%H%M")
                if user_setting.check_daily_training_time
                else None
            )
            self.universe.default = (
                user_setting.check_universe_time.strftime("%H%M")
                if user_setting.check_universe_time
                else None
            )
            self.echoofwar.default = (
                user_setting.check_echoofwar_time.strftime("%H%M")
                if user_setting.check_echoofwar_time
                else None
            )
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            power = self._str_to_int(self.power.value)
            expedition = self._str_to_int(self.expedition.value)
            dailytraining = self._str_to_int(self.dailytraining.value)
            universe = self._str_to_int(self.universe.value)
            echoofwar = self._str_to_int(self.echoofwar.value)

            if (
                power is None
                and expedition is None
                and dailytraining is None
                and universe is None
                and echoofwar is None
            ):
                raise ValueError()
            if (isinstance(power, int) and not (0 <= power <= 8)) or (
                isinstance(expedition, int) and not (0 <= expedition <= 5)
            ):
                raise ValueError()

            dailytraining_time: datetime | None = None
            if isinstance(dailytraining, int):
                _time = time(dailytraining // 100, dailytraining % 100)
                _date = date.today()
                dailytraining_time = datetime.combine(_date, _time)
                if dailytraining_time < datetime.now():
                    dailytraining_time += timedelta(days=1)

            universe_time: datetime | None = None
            echoofwar_time: datetime | None = None
            if isinstance(universe, int) or isinstance(echoofwar, int):
                _date = date.today() + timedelta(days=6 - date.today().weekday())
                if isinstance(universe, int):
                    universe_time = datetime.combine(_date, time(universe // 100, universe % 100))
                    if universe_time < datetime.now():
                        universe_time += timedelta(days=7)
                if isinstance(echoofwar, int):
                    echoofwar_time = datetime.combine(
                        _date, time(echoofwar // 100, echoofwar % 100)
                    )
                    if echoofwar_time < datetime.now():
                        echoofwar_time += timedelta(days=7)

        except Exception:
            await interaction.response.send_message(
                embed = EmbedTemplate.error("Input value is incorrect. Please make sure the input is an integer within the specified range."), # noqa
                ephemeral=True,
            )
        else:
            await Database.insert_or_replace(
                StarrailScheduleNotes(
                    discord_id=interaction.user.id,
                    discord_channel_id=interaction.channel_id or 0,
                    threshold_power=power,
                    threshold_expedition=expedition,
                    check_daily_training_time=dailytraining_time,
                    check_universe_time=universe_time,
                    check_echoofwar_time=echoofwar_time,
                )
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(
                f"Starrail Check settings are configured. You will receive reminder messages when the following thresholds are reached:\n" # noqa
                f"{self._to_msg('Development Power', power)}" # noqa
                f"{self._to_msg('Mission Execution', expedition)}" # noqa
                f"{self._to_msg('Daily Training', dailytraining_time)}" # noqa
                f"{self._to_msg('Simulated Universe', universe_time, 'Sunday')}" # noqa
                f"{self._to_msg('Echo of War', echoofwar_time, 'Sunday')}" # noqa
            ) # noqa
            )
