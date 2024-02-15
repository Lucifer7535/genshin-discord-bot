from datetime import datetime

from pydantic import BaseSettings


class Config(BaseSettings):
    """Configuration of Bot"""

    application_id: int = 123
    """ Bot Application ID"""
    test_server_id: int = 123
    """ID of Test Server to test the commands. The administrator commands can only be used in this server"""
    bot_token: str = "abc"
    """Bot token, obtained from Discord Developer webpage"""
    enka_api_key: str | None = None
    """Send the key to the enka network API"""

    daily_reward_api_list: list[str] = []
    """The daily-checkin API url list"""

    schedule_daily_checkin_interval: int = 10
    """The interval between automatic sign -in (unit: minute)"""
    schedule_check_resin_interval: int = 10
    """Automatically check the interval of resins (unit: minute)"""
    schedule_loop_delay: float = 2.0
    """The waiting interval between each user during scheduling (unit: second)"""
    game_maintenance_time: tuple[datetime, datetime] | None = None
    """The maintenance time of the game (start, end), the automatic schedule will not be executed within this period"""

    expired_user_days: int = 180
    """The number of days expired users will delete users who have not used any instructions for this day."""

    slash_cmd_cooldown: float = 5.0
    """The cooldown time of the user using slash commands (unit: second)"""
    discord_view_long_timeout: float = 1800
    """Discord long-term interactive interface (example: drop -down menu) over time (unit: second)"""
    discord_view_short_timeout: float = 60
    """Discord short-term interactive interface (example: confirmation, selection button) over time (unit: second)"""

    sentry_sdk_dsn: str | None = None
    """Sentry DSN 位址設定"""
    prometheus_server_port: int | None = None
    """Portheus Server listened to the Port, if NONE indicates that the server will not start"""
    geetest_solver_url: str | None = None
    """Let users set the URL of graphical verification"""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()  # type: ignore
