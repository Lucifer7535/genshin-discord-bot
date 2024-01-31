from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

import aiosqlite


@dataclass
class ScheduleDaily:
    """Data class for the ScheduleDaily table.

    Attributes
    -----
    id: `int`
        User's Discord ID
    channel_id: `int`
        ID of the Discord channel to send notification messages
    is_mention: `bool`
        Whether to tag the user when sending messages
    has_genshin: `bool`
        Whether to check in for Genshin Impact
    has_honkai: `bool`
        Whether to check in for Honkai Impact 3rd
    has_starrail: `bool`
        Whether to check in for Starrail
    last_checkin_date: `Optional[date]`
        Record of the last check-in date to avoid duplicate check-ins in special cases
    """

    id: int
    channel_id: int
    is_mention: bool = False
    has_genshin: bool = False
    has_honkai: bool = False
    has_starrail: bool = False
    last_checkin_date: Optional[date] = None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> ScheduleDaily:
        return cls(
            id=row["id"],
            channel_id=row["channel_id"],
            is_mention=bool(row["is_mention"]),
            has_genshin=bool(row["has_genshin"]),
            has_honkai=bool(row["has_honkai"]),
            has_starrail=bool(row["has_starrail"]),
            last_checkin_date=(
                None
                if row["last_checkin_date"] is None
                else date.fromisoformat(row["last_checkin_date"])
            ),
        )


class ScheduleDailyTable:
    """Table for ScheduleDaily data."""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self) -> None:
        """Create the table in the database."""
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS schedule_daily (
                id int NOT NULL PRIMARY KEY,
                channel_id int NOT NULL,
                is_mention int NOT NULL,
                has_genshin int NOT NULL,
                has_honkai int NOT NULL,
                has_starrail int NOT NULL,
                last_checkin_date text
            )"""
        )
        cursor = await self.db.execute("PRAGMA table_info(schedule_daily)")
        columns = [column[1] for column in await cursor.fetchall()]

        if "has_genshin" not in columns:
            await self.db.execute(
                "ALTER TABLE schedule_daily ADD COLUMN has_genshin int NOT NULL DEFAULT '1'"
            )
        if "has_starrail" not in columns:
            await self.db.execute(
                "ALTER TABLE schedule_daily ADD COLUMN has_starrail int NOT NULL DEFAULT '0'"
            )
        await self.db.commit()

    async def add(self, user: ScheduleDaily) -> None:
        """Add a user to the table."""
        if (await self.get(user.id)) is not None:  # When the user already exists
            await self.db.execute(
                "UPDATE schedule_daily SET "
                "channel_id=?, is_mention=?, has_genshin=?, has_honkai=?, has_starrail=? WHERE id=?",
                [
                    user.channel_id,
                    int(user.is_mention),
                    int(user.has_genshin),
                    int(user.has_honkai),
                    int(user.has_starrail),
                    user.id,
                ],
            )
        else:
            await self.db.execute(
                "INSERT OR REPLACE INTO schedule_daily"
                "(id, channel_id, is_mention, has_genshin, has_honkai, has_starrail, last_checkin_date) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                [
                    user.id,
                    user.channel_id,
                    int(user.is_mention),
                    int(user.has_genshin),
                    int(user.has_honkai),
                    int(user.has_starrail),
                    user.last_checkin_date,
                ],
            )
        await self.db.commit()

    async def remove(self, user_id: int) -> None:
        """Remove a specific user from the table."""
        await self.db.execute("DELETE FROM schedule_daily WHERE id=?", [user_id])
        await self.db.commit()

    async def update(self, user_id: int, *, last_checkin_date: bool = False) -> None:
        """Update specific user's column data."""
        if last_checkin_date:
            await self.db.execute(
                "UPDATE schedule_daily SET last_checkin_date=? WHERE id=?",
                [date.today().isoformat(), user_id],
            )
        await self.db.commit()

    async def get(self, user_id: int) -> Optional[ScheduleDaily]:
        """Get data for a specific user."""
        async with self.db.execute("SELECT * FROM schedule_daily WHERE id=?", [user_id]) as cursor:
            row = await cursor.fetchone()
            return ScheduleDaily.from_row(row) if row else None

    async def get_all(self) -> List[ScheduleDaily]:
        """Get data for all users."""
        async with self.db.execute("SELECT * FROM schedule_daily") as cursor:
            rows = await cursor.fetchall()
            return [ScheduleDaily.from_row(row) for row in rows]

    async def get_total_number(self) -> int:
        """Get the total number of records in the table."""
        async with self.db.execute("SELECT COUNT(id) FROM schedule_daily") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
