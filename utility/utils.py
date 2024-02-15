import json
import logging
from datetime import datetime

from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)


def get_server_name(key: str) -> str:
    return {
        "cn_gf01": "Celestia",
        "cn_qd01": "Irminsul",
        "os_usa": "USA Server",
        "os_euro": "Europe Server",
        "os_asia": "Asia Server",
        "os_cht": "SEA Server",
        "1": "Celestia",
        "2": "Celestia",
        "5": "Irminsul",
        "6": "USA Server",
        "7": "Europe Server",
        "8": "Asia Server",
        "9": "SEA Server",
    }.get(key, "")


def get_day_of_week(time: datetime) -> str:
    delta = time.date() - datetime.now().astimezone().date()
    if delta.days == 0:
        return "today"
    elif delta.days == 1:
        return "tomorrow"
    return {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}.get(time.weekday(), "") # noqa


def get_app_command_mention(name: str) -> str:
    if not hasattr(get_app_command_mention, "appcmd_id"):
        try:
            with open("data/app_commands.json", "r", encoding="utf-8") as f:
                setattr(get_app_command_mention, "appcmd_id", json.load(f))
        except Exception:
            get_app_command_mention.appcmd_id = dict()
    id = get_app_command_mention.appcmd_id.get(name)
    return f"</{name}:{id}>" if id is not None else f"`/{name}`"
