from __future__ import annotations

import logging
import os
import platform
import re
import time
from datetime import datetime as dt
from functools import wraps
from importlib.metadata import version
from typing import Any, Callable, List

import discord
import genshin
from discord.ext import commands


COLOR_CODE = re.compile(r"^[#]?[a-f0-9]{6}$")

if platform.system() == "Windows":
    os.system("")
elif platform.system() == "Linux":
    pass
elif platform.system() == "Java":
    pass
else:
    pass

logging.basicConfig(format="%(message)s", level=logging.INFO)


class ColorTool:
    def __init__(self, custom_colors: List[List[int | str | bool]] = []) -> None:
        for custom_color in custom_colors:
            if len(custom_color) != 0:
                color = ""
                if isinstance(custom_color[0], int):
                    font = bool(custom_color[3]) if len(custom_color) > 3 else True
                    color = self.RGB(
                        int(custom_color[0]), int(custom_color[1]), int(custom_color[2]), font
                    )
                else:
                    font = bool(custom_color[1]) if len(custom_color) > 1 else True
                    color = self.CODE(custom_color[0], font)
                if color != "":
                    self._CUSTOM.append(color)

    _STD_BLACK = "\033[30m"
    _STD_RED = "\033[31m"
    _STD_GREEN = "\033[32m"
    _STD_YELLOW = "\033[33m"
    _STD_BLUE = "\033[34m"
    _STD_MAGENTA = "\033[35m"
    _STD_CYAN = "\033[36m"
    _STD_LIGHT_GRAY = "\033[37m"

    _STD_DARK_GRAY = "\033[90m"
    _STD_LIGHT_RED = "\033[91m"
    _STD_LIGHT_GREEN = "\033[92m"
    _STD_LIGHT_YELLOW = "\033[93m"
    _STD_LIGHT_BLUE = "\033[94m"
    _STD_LIGHT_MAGENTA = "\033[95m"
    _STD_LIGHT_CYAN = "\033[96m"
    _STD_WHITE = "\033[97m"
    _BLACK = "\033[38;2;12;12;12m"
    _RED = "\033[38;2;197;15;31m"
    _GREEN = "\033[38;2;19;161;14m"
    _YELLOW = "\033[38;2;193;156;0m"
    _BLUE = "\033[38;2;0;52;218m"
    _MAGENTA = "\033[38;2;136;23;152m"
    _CYAN = "\033[38;2;58;150;221m"
    _LIGHT_GRAY = "\033[38;2;204;204;204m"
    _DARK_GRAY = "\033[38;2;118;118;118m"
    _LIGHT_RED = "\033[38;2;231;72;86m"
    _LIGHT_GREEN = "\033[38;2;22;198;12m"
    _LIGHT_YELLOW = "\033[38;2;249;241;165m"
    _LIGHT_BLUE = "\033[38;2;59;120;255m"
    _LIGHT_MAGENTA = "\033[38;2;180;0;158m"
    _LIGHT_CYAN = "\033[38;2;97;214;214m"
    _WHITE = "\033[38;2;242;242;242m"
    _GRAY_SCALE_1 = "\033[38;2;32;32;32m"
    _GRAY_SCALE_2 = "\033[38;2;64;64;64m"
    _GRAY_SCALE_3 = "\033[38;2;96;96;96m"
    _GRAY_SCALE_4 = "\033[38;2;128;128;128m"
    _GRAY_SCALE_5 = "\033[38;2;160;160;160m"
    _GRAY_SCALE_6 = "\033[38;2;192;192;192m"
    _GRAY_SCALE_7 = "\033[38;2;224;224;224m"
    _MIKU_GREEN = "\033[38;2;57;197;187m"
    _TIAN_YI_BLUE = "\033[38;2;102;204;255m"
    _DISCORD_DARK = "\033[48;2;54;57;63m"
    _ORANGE = "\033[38;2;255;102;0m"
    _LIME = "\033[38;2;170;255;85m"
    _GOLD = "\033[38;2;255;221;51m"
    _PINK = "\033[38;2;255;128;255m"
    _ORANGE_RED = "\033[38;2;255;102;102m"
    _WHEAT_YELLOW = "\033[38;2;238;255;85m"
    _GRASS_GREEN = "\033[38;2;102;255;102m"
    _BRIGHT_ORANGE = "\033[38;2;255;187;102m"
    _BRIGHT_CYAN_GREEN = "\033[38;2;136;255;255m"
    _BRIGHT_BLUE = "\033[38;2;51;204;255m"
    _BRIGHT_MAGENTA = "\033[38;2;221;51;221m"
    _BRIGHT_PURPLE = "\033[38;2;187;187;255m"
    _BRIGHT_GREEN = "\033[38;2;187;255;187m"
    _BRIGHT_RED = "\033[38;2;255;187;187m"
    _BRIGHT_CYAN = "\033[38;2;187;255;255m"
    _BRIGHT_PINK = "\033[38;2;255;187;255m"
    _BRIGHT_YELLOW = "\033[38;2;255;255;187m"

    RESET = f"\033[0m{_WHITE}"
    _REVERSE = "\033[30;47m"
    _BOLD = "\033[1m"
    _CUSTOM: List[str] = []

    SYSTEM = f"{_BRIGHT_PURPLE}【system】{RESET}"
    ERROR = f"{_RED}【error】{RESET}"
    OK = f"{_LIGHT_GREEN}【OK】{RESET}"
    EVENT = f"{_LIGHT_YELLOW}【event】{RESET}"
    COMMAND = f"{_BRIGHT_BLUE}【command】{RESET}"
    EXCEPTION = f"{_BRIGHT_MAGENTA}【exception】{RESET}"
    INFO = f"{_BRIGHT_CYAN_GREEN}【info】{RESET}"
    DEBUG = f"{_LIGHT_RED}【debug】{RESET}"
    TEST = f"{_GOLD}【test】{RESET}"
    WARN = f"{_ORANGE}【warn】{RESET}"
    INTERACTION = f"{_LIME}【interaction】{RESET}"

    def RGB(self, Red: int = 255, Green: int = 255, Blue: int = 255, font: bool = True) -> str:
        if (
            (isinstance(Red, int) and Red >= 0 and Red <= 255)
            and (isinstance(Green, int) and Green >= 0 and Green <= 255)
            and (isinstance(Blue, int) and Blue >= 0 and Blue <= 255)
        ):
            return f"\033[{38 if font else 48};2;{Red};{Green};{Blue}m"
        else:
            return ""

    def CODE(self, Color_Code: str = "#ffffff", font: bool = True) -> str:
        code = Color_Code.lstrip("#").lower()
        if COLOR_CODE.fullmatch(code) is not None:
            Red = int(code[0:2], 16)
            Green = int(code[2:4], 16)
            Blue = int(code[4:6], 16)
            return f"\033[{38 if font else 48};2;{Red};{Green};{Blue}m"
        else:
            return ""


class LogTool(ColorTool):
    VERSION = "3.1"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.indent = "\n                　　　　"
        self.indent_noTag = "\n                "
        #   The following paragraph is used to see the effect. Remember to adjust the color yourself
        print(
            f"\n              {self._MIKU_GREEN}Genshin Bot{self.RESET}              System : {self._LIGHT_CYAN}{platform.system()}\n" # noqa
            f" {self._LIGHT_RED}Python {self._GRAY_SCALE_6}v{platform.python_version()}"
            f"   {self._BRIGHT_BLUE}discord.py {self._GRAY_SCALE_6}v{version('discord.py')}"
            f"   {self._WHEAT_YELLOW}genshin.py {self._GRAY_SCALE_6}v{version('genshin')}"
            f"   {self._PINK}LogTool {self._GRAY_SCALE_6}v{self.VERSION}{self.RESET}\n"
        )
        #   f" {self._STD_WHITE}-------------------- Color example --------------------{self.RESET}\n"
        #   f"  {self._BRIGHT_PINK}Custom message{self.RESET}:{self._BRIGHT_PINK}Example text{self.RESET}\n"
        #   f"  {self._ORANGE_RED}Example instruction set{self.RESET}({self._BRIGHT_RED}Example{self.RESET})\n"
        #   f"  {self._LIGHT_MAGENTA}Exception{self.RESET}({self._LIGHT_MAGENTA}Error.ExampleException{self.RESET})\n"
        #   f"  {self._RED}error message{self.RESET}:{self._RED}Error Message...{self.RESET}\n"
        #   f"  {self._GRASS_GREEN}server{self.RESET}({self._BRIGHT_GREEN}Guild_ID{self.RESET})\n"
        #   f"  {self._TIAN_YI_BLUE}#Channel{self.RESET}({self._BRIGHT_CYAN}Channel ID{self.RESET})\n"
        #   f"  {self._BRIGHT_ORANGE}@user{self.RESET}({self._BRIGHT_YELLOW}User ID{self.RESET})\n"
        #   f" {self._STD_WHITE}-------------------- Label --------------------{self.RESET}\n"
        #   f"  {self.SYSTEM}{self.OK}{self.EVENT}{self.COMMAND}{self.INTERACTION}{self.TEST}\n"
        #   f"  {self.DEBUG}{self.INFO}{self.WARN}{self.EXCEPTION}{self.ERROR}\n")

    def __get_timestamp__(self, display: bool = True) -> str:
        time_stamp = dt.now().strftime("%m-%d %H:%M:%S")
        if display:
            return f"{self._STD_DARK_GRAY}[{time_stamp}]{self.RESET}"
        else:
            return f"{self._STD_BLACK}[{time_stamp}]{self.RESET}"

    def __print_with_tag__(
        self,
        tag: str | None,
        logging_level: int = logging.INFO,
        message: str = "",
        show_timestamp: bool = True,
    ) -> None:
        message = message[:-1] if (len(message) > 0 and message[-1] == "\n") else message
        msg = str(message).replace("\n", (self.indent if tag is not None else self.indent_noTag))
        msg = f'{self.__get_timestamp__(show_timestamp)}{(tag if tag != None else " ")}{msg}'
        for level, func in zip(
            [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL],
            [logging.debug, logging.info, logging.warning, logging.error, logging.critical],
        ):
            if logging_level == level:
                func(msg)
                break

    def System(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.SYSTEM, logging.INFO, message, show_timestamp)

    def Ok(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.OK, logging.INFO, message, show_timestamp)

    def Event(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.EVENT, logging.INFO, message, show_timestamp)

    def Cmd(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.COMMAND, logging.INFO, message, show_timestamp)

    def Interact(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.INTERACTION, logging.INFO, message, show_timestamp)

    def Debug(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.DEBUG, logging.DEBUG, message, show_timestamp)

    def Info(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.INFO, logging.INFO, message, show_timestamp)

    def Warn(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.WARN, logging.WARN, message, show_timestamp)

    def Error(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.ERROR, logging.WARN, message, show_timestamp)

    def Except(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.EXCEPTION, logging.INFO, message, show_timestamp)

    def Test(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(self.DEBUG, logging.DEBUG, message, show_timestamp)

    def NoTag(self, message: str = "", show_timestamp: bool = True) -> None:
        self.__print_with_tag__(None, logging.INFO, message, show_timestamp)

    def User(self, user: discord.User | discord.Member | str | int):
        if isinstance(user, (str, int)):
            return f"{self._BRIGHT_YELLOW}@{user}{self.RESET}"

        return (
            f"{self._BRIGHT_ORANGE}@{user.name}{self.RESET}"
            f"({self._BRIGHT_YELLOW}{user.id}{self.RESET})"
        )

    def Server(self, server: discord.Guild | None):
        if server:
            server_name = server.name if len(server.name) <= 15 else f"{server.name[:13]}..."
            return f"{self._GRASS_GREEN}{server_name}{self.RESET}({self._BRIGHT_GREEN}{server.id}{self.RESET})"
        return ""

    def Channel(
        self,
        channel: discord.TextChannel | discord.ForumChannel | discord.Thread | discord.DMChannel,
    ) -> str:
        if isinstance(channel, discord.TextChannel):
            return f"{self._MIKU_GREEN}#{channel.name}{self.RESET}({self._BRIGHT_CYAN}{channel.id}{self.RESET})"
        if isinstance(channel, discord.ForumChannel):
            return f"{self._MIKU_GREEN}#{channel.name}{self.RESET}({self._BRIGHT_CYAN}{channel.id}{self.RESET})"
        elif isinstance(channel, discord.Thread):
            if channel.parent is not None:
                return (
                    f"{self._MIKU_GREEN}#{channel.parent.name}({self._BRIGHT_CYAN}{channel.parent.id}{self.RESET})"
                    f" => Channel: {channel.name}{self.RESET}({self._BRIGHT_CYAN}{channel.id}{self.RESET})"
                )
            return "channel.parent is None"
        else:
            return (
                f"{self._MIKU_GREEN}#Private message channel{self.RESET}({self._BRIGHT_CYAN}{channel.id}{self.RESET})"
            )

    def CostTime(self, start_time: float) -> str:
        end_time = time.perf_counter()
        return f" {self._PINK}{(end_time-start_time)*1000:.0f}{self.RESET} millisecond(ms)"

    def Cog(self, id: str, name: str = "", enabled: bool = True):
        if enabled:
            return (
                f"{self._ORANGE_RED}{name}{self.RESET}({self._BRIGHT_RED}{id}{self.RESET})"
                if name != ""
                else f"{self._ORANGE_RED}{id}{self.RESET}"
            )
        else:
            return (
                f"{self._GRAY_SCALE_4}{name}{self.RESET}({self._GRAY_SCALE_4}{id}{self.RESET})"
                if name != ""
                else f"{self._GRAY_SCALE_4}{id}{self.RESET}"
            )

    def ErrorType(self, error: discord.DiscordException | Exception) -> str:
        if isinstance(error, commands.CommandInvokeError):
            return (
                f"({self._LIGHT_MAGENTA}{type(error).__qualname__}{self.RESET} -> "
                f"{self._LIGHT_MAGENTA}{type(error.original).__qualname__}{self.RESET})"
            )
        else:
            return f"({self._LIGHT_MAGENTA}{type(error).__qualname__}{self.RESET})"

    def CmdCall(self, ctx: discord.Interaction, *args, **kwargs) -> None:
        cmd_name = (
            f"/{ctx.command.name}"
            if isinstance(ctx.command, discord.app_commands.Command)
            else f"\u200b{ctx.command.name}"
            if isinstance(ctx.command, discord.app_commands.ContextMenu)
            else "(Command Not Found)"
        )

        def parse_argument(arg: Any) -> str:
            return (
                self.User(arg)
                if isinstance(arg, (discord.User, discord.Member))
                else arg.content
                if isinstance(arg, discord.Message)
                else str(arg)
            )

        arg_list = [parse_argument(arg) for arg in args]
        for name, argument in kwargs.items():
            arg_list.append(f"{self.__ParameterName__(name)}={parse_argument(argument)}")
        log = f"{self.User(ctx.user)} used {self.__CmdName__(cmd_name)}：{', '.join(arg_list)}"
        self.Cmd(log)

    def CmdResult(
        self,
        ctx: commands.Context | discord.Interaction,
        start_time: float | None = None,
        message: str | None = None,
        command_name: str | None = None,
        success: bool | None = True,
        show_timestamp: bool = True,
    ) -> None:

        if isinstance(ctx, commands.Context):
            if command_name is not None:
                cmd_name = command_name
            else:
                cmd_name = (
                    f"{ctx.prefix if ctx.prefix else ''}{ctx.command.name if ctx.command else ''}"
                )
            log = (
                f"{self.User(ctx.author)} used {self.__CmdName__(cmd_name)} "
                f"{('' if success == None else 'success' if success else 'fail')}。"
            )
        else:  # discord.Interaction
            cmd_name = (
                command_name
                if command_name is not None
                else f"/{ctx.command.name}"
                if isinstance(ctx.command, discord.app_commands.Command)
                else f"\u200b{ctx.command.name}"
                if isinstance(ctx.command, discord.app_commands.ContextMenu)
                else "(Command Not Found)"
            )
            log = (
                f"{self.User(ctx.user)} used {self.__CmdName__(cmd_name)} "
                f"{('' if success == None else 'success' if success else 'fail')}。"
            )
        cost_time = f"time used: {self.CostTime(start_time)}" if start_time is not None else ""
        postition = (
            f"\n Server:{self.Server(ctx.guild)} Channel:{self.Channel(ctx.channel)}\n"
            if isinstance(
                ctx.channel,
                (discord.TextChannel, discord.ForumChannel, discord.Thread, discord.DMChannel),
            )
            else ""
        )
        msg = (
            f"\n messages:{self._BRIGHT_PINK}{message}{self.RESET}\n"
            if message is not None and message != ""
            else ""
        )
        self.Cmd("⤷ " + log + cost_time + postition + msg, show_timestamp)

    def ErrorLog(
        self,
        ctx: commands.Context | discord.Interaction,
        error: commands.CommandInvokeError
        | commands.CommandError
        | discord.app_commands.AppCommandError
        | Exception,
    ) -> None:
        """LOG template when errors occur in the commands"""
        msg = ""
        if isinstance(ctx, commands.Context):
            if isinstance(error, commands.CommandInvokeError):
                msg = f"{self.User(ctx.author)} An error occurred during the execution of the command {self.ErrorType(error)}：\n error message:{self.__ErrorMsg__(error.original)}" # noqa
            elif isinstance(error, commands.CommandError):
                msg = f"{self.User(ctx.author)} command caused error {self.ErrorType(error)}：\n error message:{self.__ErrorMsg__(error)}" # noqa
            else:
                msg = f"{self.User(ctx.author)} An error occurred during the execution of the command {self.ErrorType(error)}：\n error message:{self.__ErrorMsg__(error)}" # noqa
        elif isinstance(ctx, discord.Interaction):
            if isinstance(error, discord.app_commands.AppCommandError):
                msg = f"{self.User(ctx.user)}, command caused error {self.ErrorType(error)}：\n error message：{self.__ErrorMsg__(error)}" # noqa
            else:
                msg = f"{self.User(ctx.user)} An error occurred during the execution of the command {self.ErrorType(error)}：\n error message:{self.__ErrorMsg__(error)}" # noqa
        self.Error(msg)

    def FuncExceptionLog(
        self, user: str | int, func_name: str, error: genshin.GenshinException | Exception
    ) -> None:
        """LOG template"""
        msg = f"{self.User(user)} executed command {self.__FuncName__(func_name)}, error occured during the execution:\n"
        if isinstance(error, genshin.GenshinException):
            msg = msg + (
                f"retcode：{self.__ErrorMsg__(error.retcode)}、"
                f"Original content:{self.__ErrorMsg__(error.original)}\n"
                f"error message:{self.__ErrorMsg__(error.msg)}"
            )
        else:  # Exception
            msg = msg + f"error message:{self.__ErrorMsg__(error)}"
        self.Except(msg)

    def HighLight(self, message: str) -> str:
        return f"{self._WHEAT_YELLOW}{message}{self.RESET}"

    def Note(self, message: str) -> str:
        return f"{self._GRAY_SCALE_4}{message}{self.RESET}"

    def __CmdName__(self, command_name: str) -> str:
        return f"{self._BRIGHT_BLUE}{command_name}{self.RESET}"

    def __FuncName__(self, func_name: str) -> str:
        return f"{self._BRIGHT_BLUE}{func_name}{self.RESET}"

    def __ParameterName__(self, parameter_name: str) -> str:
        return f"{self._WHEAT_YELLOW}{parameter_name}{self.RESET}"

    def __ErrorMsg__(self, error: Exception | str | int) -> str:
        return f"{self._RED}{error}{self.RESET}"


LOG = LogTool()


def SlashCommandLogger(func: Callable):
    @wraps(func)
    async def inner(self, ctx: discord.Interaction, *args, **kwargs):
        LOG.CmdCall(ctx, *args, **kwargs)
        start_time = time.perf_counter()
        res = await func(self, ctx, *args, **kwargs)
        LOG.CmdResult(ctx, start_time)
        return res

    return inner


def ContextCommandLogger(func: Callable):
    @wraps(func)
    async def inner(ctx: discord.Interaction, *args, **kwargs):
        LOG.CmdCall(ctx, *args, **kwargs)
        start_time = time.perf_counter()
        res = await func(ctx, *args, **kwargs)
        LOG.CmdResult(ctx, start_time)
        return res

    return inner
