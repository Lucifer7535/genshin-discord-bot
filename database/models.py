import datetime
import json
import typing
import zlib

import genshin
import sqlalchemy
from mihomo import StarrailInfoParsed
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

from .dataclass import spiral_abyss


class Base(MappedAsDataclass, DeclarativeBase):
    """Base class for database tables, inherits from sqlalchemy `MappedAsDataclass`, `DeclarativeBase`"""

    type_annotation_map = {dict[str, str]: sqlalchemy.JSON}


class User(Base):
    """User database table"""

    __tablename__ = "users"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """User's Discord ID"""
    last_used_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """Time of the user's last successful use of the bot command"""

    cookie_default: Mapped[str | None] = mapped_column(default=None)
    """Cookie to use when the cookie for a specific game is not set"""
    cookie_genshin: Mapped[str | None] = mapped_column(default=None)
    """Cookie for using Genshin Impact commands on Hoyolab or Mihoyo website"""
    cookie_honkai3rd: Mapped[str | None] = mapped_column(default=None)
    """Cookie for using Honkai Impact 3rd commands on Hoyolab or Mihoyo website"""
    cookie_starrail: Mapped[str | None] = mapped_column(default=None)
    """Cookie for using Star Rail commands on Hoyolab or Mihoyo website"""
    cookie_themis: Mapped[str | None] = mapped_column(default=None)
    """Cookie used for tot commands on Hoyolab or miHoYo's website."""

    uid_genshin: Mapped[int | None] = mapped_column(default=None)
    """UID of Genshin Impact character"""
    uid_honkai3rd: Mapped[int | None] = mapped_column(default=None)
    """UID of Honkai Impact 3rd character"""
    uid_starrail: Mapped[int | None] = mapped_column(default=None)
    """UID of Star Rail character"""


class ScheduleDailyCheckin(Base):
    """Schedule for daily automatic check-in database table"""

    __tablename__ = "schedule_daily_checkin"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """User's Discord ID"""
    discord_channel_id: Mapped[int]
    """ID of the Discord channel to send notification messages"""
    is_mention: Mapped[bool]
    """Whether to tag the user when sending messages"""
    next_checkin_time: Mapped[datetime.datetime]
    """Next check-in time (user sets the daily check-in time)"""

    has_genshin: Mapped[bool] = mapped_column(default=False)
    """Whether to check-in Genshin Impact"""
    has_honkai3rd: Mapped[bool] = mapped_column(default=False)
    """Whether to check-in Honkai Impact 3rd"""
    has_starrail: Mapped[bool] = mapped_column(default=False)
    """Whether to check-in Star Rail"""
    has_themis: Mapped[bool] = mapped_column(default=False)
    """Whether to check in for Tears of Themis(GLOBAL)"""
    has_themis_tw: Mapped[bool] = mapped_column(default=False)
    """Whether to check in for Tears of Themis(TW)"""

    def update_next_checkin_time(self) -> None:
        """Update the next check-in time to tomorrow"""
        dt = datetime.datetime
        self.next_checkin_time = dt.combine(
            dt.now().date(), self.next_checkin_time.time()
        ) + datetime.timedelta(days=1)


class GeetestChallenge(Base):
    """Challenge values used in Geetest graphic verification for check-in"""

    __tablename__ = "geetest_challenge"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """User's Discord ID"""

    genshin: Mapped[dict[str, str] | None] = mapped_column(default=None)
    """Challenge value for Genshin Impact"""
    honkai3rd: Mapped[dict[str, str] | None] = mapped_column(default=None)
    """Challenge value for Honkai Impact 3rd"""
    starrail: Mapped[dict[str, str] | None] = mapped_column(default=None)
    """Challenge value for Star Rail"""


class GenshinScheduleNotes(Base):
    """Database table for Genshin Impact schedule auto-check notes"""

    __tablename__ = "genshin_schedule_notes"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """User's Discord ID"""
    discord_channel_id: Mapped[int]
    """ID of the Discord channel to send notification messages"""
    next_check_time: Mapped[datetime.datetime | None] = mapped_column(
        insert_default=sqlalchemy.func.now(), default=None
    )
    """Next check time; when checking, data will only be requested from Hoyolab if it exceeds this time"""

    threshold_resin: Mapped[int | None] = mapped_column(default=None)
    """Hours before resin is full to send a reminder"""
    threshold_currency: Mapped[int | None] = mapped_column(default=None)
    """Hours before Realm Currency is full to send a reminder"""
    threshold_transformer: Mapped[int | None] = mapped_column(default=None)
    """Hours before the Transformation Device is completed to send a reminder"""
    threshold_expedition: Mapped[int | None] = mapped_column(default=None)
    """Hours before all dispatches are completed to send a reminder"""
    check_commission_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """Time to check for unfinished daily commissions today"""


class GenshinSpiralAbyss(Base):
    """Database table for Genshin Impact Spiral Abyss"""

    __tablename__ = "genshin_spiral_abyss"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """User's Discord ID"""
    season: Mapped[int] = mapped_column(primary_key=True)
    """Spiral Abyss season"""
    _abyss_raw_data: Mapped[bytes] = mapped_column(init=False)
    """Spiral Abyss byte data"""
    _characters_raw_data: Mapped[bytes | None] = mapped_column(init=False, default=None)
    """Character byte data"""

    def __init__(
        self,
        discord_id: int,
        season: int,
        abyss: genshin.models.SpiralAbyss,
        characters: typing.Sequence[genshin.models.Character] | None = None,
    ):
        """
        Initialize the object of the Genshin Impact Spiral Abyss database table.

        Parameters
        ------
        discord_id: `int`
            User's Discord ID
        season: `int`
            Spiral Abyss season
        abyss: `genshin.models.SpiralAbyss`
            Genshin.py Spiral Abyss data.
        characters `Sequence[genshin.models.Character]` | `None`:
            Genshin.py character data. Default is None.
        """
        self.discord_id = discord_id
        self.season = season

        json_str = abyss.json(by_alias=True)
        self._abyss_raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

        if characters is not None:
            # Convert character data from genshin.py to a custom dataclass to reduce data size
            # Then convert to json -> byte -> compress -> save
            _characters = [spiral_abyss.CharacterData.from_orm(c) for c in characters]
            json_str = ",".join([c.json() for c in _characters])
            json_str = "[" + json_str + "]"
            self._characters_raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

    @property
    def abyss(self) -> genshin.models.SpiralAbyss:
        """Genshin.py Spiral Abyss data"""
        data = zlib.decompress(self._abyss_raw_data).decode("utf-8")
        return genshin.models.SpiralAbyss.parse_raw(data)

    @property
    def characters(self) -> list[spiral_abyss.CharacterData] | None:
        """Spiral Abyss character data"""
        if self._characters_raw_data is None:
            return None
        data = zlib.decompress(self._characters_raw_data).decode("utf-8")
        listobj: list = json.loads(data)
        return [spiral_abyss.CharacterData.parse_obj(c) for c in listobj]


class GenshinShowcase(Base):
    """Database table for Genshin Impact character showcase"""

    __tablename__ = "genshin_showcases"

    uid: Mapped[int] = mapped_column(primary_key=True)
    """Genshin Impact UID"""
    _raw_data: Mapped[bytes]
    """Showcase byte data"""

    def __init__(self, uid: int, data: dict[str, typing.Any]):
        """Initialize the object of the Genshin Impact character showcase database table

        Parameters
        ------
        uid: `int`
            Genshin Impact UID
        data: `dict[str, Any]`
            JSON format data from the Enka network API
        """
        # Convert dict object to json -> byte -> compress -> save
        json_str = json.dumps(data)
        self.uid = uid
        self._raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

    @property
    def data(self) -> dict[str, typing.Any]:
        """JSON format data from the Enka network API"""
        data = zlib.decompress(self._raw_data).decode("utf-8")
        return json.loads(data)


class StarrailScheduleNotes(Base):
    """Database table for Star Rail schedule auto-check notes"""

    __tablename__ = "starrail_schedule_notes"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """User's Discord ID"""
    discord_channel_id: Mapped[int]
    """ID of the Discord channel to send notification messages"""
    next_check_time: Mapped[datetime.datetime | None] = mapped_column(
        insert_default=sqlalchemy.func.now(), default=None
    )
    """Next check time; when checking, data will only be requested from Hoyolab if it exceeds this time"""

    threshold_power: Mapped[int | None] = mapped_column(default=None)
    """Hours before power is full to send a reminder"""
    threshold_expedition: Mapped[int | None] = mapped_column(default=None)
    """Hours before all dispatches are completed to send a reminder"""
    check_daily_training_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """Time to check for unfinished daily training today"""
    check_universe_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """Time to check for unfinished weekly Simulated Universe today"""
    check_echoofwar_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """Time to check for unfinished weekly Echo of War today"""


class StarrailForgottenHall(Base):
    """Database table for Star Rail Forgotten Hall"""

    __tablename__ = "starrail_forgotten_hall"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """User's Discord ID"""
    season: Mapped[int] = mapped_column(primary_key=True)
    """Forgotten Hall season"""
    _raw_data: Mapped[bytes] = mapped_column()
    """Forgotten Hall byte data"""

    def __init__(self, discord_id: int, season: int, data: genshin.models.StarRailChallenge):
        """Initialize the object of the Star Rail Forgotten Hall database table.

        Parameters:
        ------
        discord_id: `int`
            User's Discord ID.
        season: `int`
            Forgotten Hall season.
        data: `genshin.models.StarRailChallenge`
            Genshin.py Forgotten Hall data.
        """
        json_str = data.json(by_alias=True, ensure_ascii=False)
        self.discord_id = discord_id
        self.season = season
        self._raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

    @property
    def data(self) -> genshin.models.StarRailChallenge:
        """Genshin.py Forgotten Hall data"""
        data = zlib.decompress(self._raw_data).decode("utf-8")
        return genshin.models.StarRailChallenge.parse_raw(data)


class StarrailPureFiction(Base):
    """Star Rail Pure Fiction Database Table"""

    __tablename__ = "starrail_pure_fiction"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """User Discord ID"""
    season: Mapped[int] = mapped_column(primary_key=True)
    """Pure Fiction season"""
    _raw_data: Mapped[bytes] = mapped_column()
    """Pure Fiction data stored as bytes"""

    def __init__(self, discord_id: int, season: int, data: genshin.models.StarRailPureFiction):
        """Initialize an object for the Star Rail Pure Fiction database table.

        Parameters:
        ------
        discord_id: `int`
            User Discord ID.
        season: `int`
            Pure Fiction season.
        data: `genshin.models.StarRailPureFiction`
            Genshin.py Pure Fiction data.
        """
        json_str = data.json(by_alias=True, ensure_ascii=False)
        self.discord_id = discord_id
        self.season = season
        self._raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

    @property
    def data(self) -> genshin.models.StarRailPureFiction:
        """Genshin.py Pure Fiction data"""
        data = zlib.decompress(self._raw_data).decode("utf-8")
        return genshin.models.StarRailPureFiction.parse_raw(data)


class StarrailShowcase(Base):
    """Database table for Star Rail character showcase"""

    __tablename__ = "starrail_showcases"

    uid: Mapped[int] = mapped_column(primary_key=True)
    """Star Rail UID"""
    _raw_data: Mapped[bytes]
    """Showcase byte data"""

    def __init__(self, uid: int, data: StarrailInfoParsed):
        """Initialize the object of the Star Rail character showcase database table.

        Parameters:
        ------
        uid: `int`
            Star Rail UID.
        data: `StarrailInfoParsed`
            Mihomo API data.
        """
        json_str = data.json(by_alias=True)
        self.uid = uid
        self._raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

    @property
    def data(self) -> StarrailInfoParsed:
        """Mihomo API data"""
        data = zlib.decompress(self._raw_data).decode("utf-8")
        return StarrailInfoParsed.parse_raw(data)
