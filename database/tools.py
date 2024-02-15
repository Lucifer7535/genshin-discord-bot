from datetime import datetime

import genshin

from utility.custom_log import LOG
from utility.utils import get_app_command_mention

from .app import Database
from .models import User


class Tool:
    @classmethod
    async def check_user(
        cls,
        user: User | None,
        *,
        check_cookie: bool = True,
        check_uid: bool = False,
        game: genshin.Game | None = None,
    ) -> tuple[bool, str]:
        """Check if specific user data is already saved in the database

        Parameters
        ------
        user: `database.User | None`
            User data class from the database
        check_cookie: `bool`
            Whether to check the cookie
        check_uid: `bool`
            Whether to check the UID (game parameter must be set)
        game: `genshin.Game | None = None`
            Game to check (only used when checking UID)

        Returns
        ------
        (`bool`, `str`):
            - `True` if the check is successful, data exists in the database; `False` if the check fails, data does not exist in the database # noqa
            - Error message when the check fails
        """
        if user is None:
            return False, f"User not found, please set the cookie first (use {get_app_command_mention('cookie-login')} for instructions)" # noqa

        if check_cookie is True and user.cookie_default is None:
            return False, f"Cookie not found, please set the cookie first (use {get_app_command_mention('cookie-login')} for instructions)" # noqa

        if check_uid is True and game is not None:
            if (
                (game == genshin.Game.GENSHIN and user.uid_genshin is None)
                or (game == genshin.Game.HONKAI and user.uid_honkai3rd is None)
                or (game == genshin.Game.STARRAIL and user.uid_starrail is None)
            ):
                return False, f"UID not found, please set the UID using {get_app_command_mention('uid-settings')}"

        return True, ""

    @classmethod
    async def remove_expired_user(cls, diff_days=60):
        """Remove users who have not used commands for more than a certain number of days

        Parameters
        ------
        diff_days: `int`
            Remove users who have not used commands for more than this number of days
        """
        now = datetime.now()
        count = 0
        users = await Database.select_all(User)
        for user in users:
            if user.last_used_time is None:
                continue
            interval = now - user.last_used_time
            if interval.days > diff_days:
                await Database.delete_instance(user)
                count += 1
        LOG.System(f"Checking expired users: {len(users)} users checked, {count} expired users have been removed")
