from datetime import datetime

import aiosqlite

from .schedule_daily import ScheduleDailyTable
from .schedule_resin import ScheduleResinTable
from .showcase import ShowcaseTable
from .spiral_abyss import SpiralAbyssTable
from .starrail_showcase import StarrailShowcaseTable
from .users import UsersTable

# from utility.custom_log import LOG


class Database:
    """Main class for managing all tables in the database.

    Attributes
    -----
    db: `aiosqlite.Connection`
        Connection to the database, allows direct database operations using this variable.
    users: `UsersTable`
        Table for user data.
    schedule_daily: `ScheduleDailyTable`
        Table for daily check-in data.
    schedule_resin: `ScheduleResinTable`
        Table for real-time resin check data.
    spiral_abyss: `SpiralAbyssTable`
        Table for Spiral Abyss data.
    showcase: `ShowcaseTable`
        Table for showcase data.
    starrail_showcase: `StarrailShowcaseTable`
        Table for Stardust Rail Showcase data.
    """

    db: aiosqlite.Connection

    async def create(self, filepath: str) -> None:
        """Initialize the database. Needs to be called once when the bot is first run."""
        self.db = await aiosqlite.connect(filepath)
        self.db.row_factory = aiosqlite.Row

        self.users = UsersTable(self.db)
        self.schedule_daily = ScheduleDailyTable(self.db)
        self.schedule_resin = ScheduleResinTable(self.db)
        self.spiral_abyss = SpiralAbyssTable(self.db)
        self.showcase = ShowcaseTable(self.db)
        self.starrail_showcase = StarrailShowcaseTable(self.db)

        await self.users.create()
        await self.schedule_daily.create()
        await self.schedule_resin.create()
        await self.spiral_abyss.create()
        await self.showcase.create()
        await self.starrail_showcase.create()

    async def close(self) -> None:
        """Close the database. Needs to be called once before the bot closes."""
        await self.db.close()

    async def remove_user(self, user_id: int) -> None:
        """Remove all data for a specific user."""
        await self.users.remove(user_id)
        await self.schedule_daily.remove(user_id)
        await self.schedule_resin.remove(user_id)
        await self.spiral_abyss.remove(user_id)

    async def remove_expired_users(self, diff_days: int = 30, invalid_cookie: int = 30) -> None:
        """Remove users who haven't used the bot for a specified number of days or have too many invalid cookies.

        Parameters:
        ------
        diff_days: `int`
            Remove users who haven't used the bot for more than this number of days.
        invalid_cookie: `int`
            Remove users with more than this number of invalid cookie attempts.
        """
        now = datetime.now()
        count = 0
        users = await self.users.get_all()
        for user in users:
            interval = now - (now if user.last_used_time is None else user.last_used_time)
            if interval.days > diff_days or user.invalid_cookie > invalid_cookie:
                await self.remove_user(user.id)
                count += 1


db = Database()
