from typing import Final

from prometheus_client import Counter, Gauge


class Metrics:

    PREFIX: Final[str] = "discordbot_"

    IS_CONNECTED: Final[Gauge] = Gauge(PREFIX + "connected", "Whether the Bot is connected to Discord", ["shard"])

    LATENCY: Final[Gauge] = Gauge(PREFIX + "latency_seconds", "Bot's Latency'", ["shard"])

    GUILDS: Final[Gauge] = Gauge(PREFIX + "guilds_total", "The total number of servers where the bot is used.")

    CHANNELS: Final[Gauge] = Gauge(PREFIX + "channels_total", "The total number of channels where the bot is used.")

    USERS: Final[Gauge] = Gauge(PREFIX + "users_total", "The total number of users registered by bot.")

    COMMANDS: Final[Gauge] = Gauge(PREFIX + "commands_total", "The total number of commands that the bot can use.")

    INTERACTION_EVENTS: Final[Counter] = Counter(
        PREFIX + "on_interaction_events",
        "Number of times the (Interaction) command was called",
        ["shard", "interaction", "command"],
    )

    COMMAND_EVENTS: Final[Counter] = Counter(
        PREFIX + "on_command_events", "Number of times text commands are called", ["shard", "command"]
    )

    CPU_USAGE: Final[Gauge] = Gauge(PREFIX + "cpu_usage_percent", "System CPU usage rate")

    MEMORY_USAGE: Final[Gauge] = Gauge(PREFIX + "memory_usage_percent", "Memory usage rate of bot")

    PROCESS_START_TIME: Final[Gauge] = Gauge(
        PREFIX + "process_start_time_seconds", "The current time when the bot started"
    )
