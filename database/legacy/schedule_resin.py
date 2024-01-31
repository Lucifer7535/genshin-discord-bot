from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import aiosqlite


@dataclass
class ScheduleResin:
    """Data class for the ScheduleResin table.

    Attributes
    -----
    id: `int`
        User's Discord ID
    channel_id: `int`
        ID of the Discord channel to send notification messages
    next_check_time: `Optional[datetime]`
        Next check-in time; data will be requested from Hoyolab only if the check-in time exceeds this time
    threshold_resin: `Optional[int]`
        Number of hours before notifying when resin is full
    threshold_currency: `Optional[int]`
        Number of hours before notifying when currency is full
    threshold_transformer: `Optional[int]`
        Number of hours before notifying when transformation materials are ready
    threshold_expedition: `Optional[int]`
        Number of hours before notifying when all dispatch missions are completed
    check_commission_time: `Optional[datetime]`
        Time each day to remind about incomplete commission missions
    """

    id: int
    channel_id: int
    next_check_time: Optional[datetime] = None
    threshold_resin: Optional[int] = None
    threshold_currency: Optional[int] = None
    threshold_transformer: Optional[int] = None
    threshold_expedition: Optional[int] = None
    check_commission_time: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> ScheduleResin:
        return cls(
            id=row["id"],
            channel_id=row["channel_id"],
            next_check_time=(
                datetime.fromisoformat(row["next_check_time"]) if row["next_check_time"] else None
            ),
            threshold_resin=row["threshold_resin"],
            threshold_currency=row["threshold_currency"],
            threshold_transformer=row["threshold_transformer"],
            threshold_expedition=row["threshold_expedition"],
            check_commission_time=(
                datetime.fromisoformat(row["check_commission_time"])
                if row["check_commission_time"]
                else None
            ),
        )


class ScheduleResinTable:
    """Table for ScheduleResin data."""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self) -> None:
        """Create the table in the database."""
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS schedule_resin (
                id int NOT NULL PRIMARY KEY,
                channel_id int NOT NULL,
                next_check_time text,
                threshold_resin int,
                threshold_currency int,
                threshold_transformer int,
                threshold_expedition int,
                check_commission_time text
            )"""
        )
        await self.db.commit()

    async def add(self, user: ScheduleResin) -> None:
        """Add a user to the table."""
        await self.db.execute(
            "INSERT OR REPLACE INTO schedule_resin VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            [
                user.id,
                user.channel_id,
                datetime.now().isoformat(),
                user.threshold_resin,
                user.threshold_currency,
                user.threshold_transformer,
                user.threshold_expedition,
                user.check_commission_time.isoformat() if user.check_commission_time else None,
            ],
        )
        await self.db.commit()

    async def remove(self, user_id: int) -> None:
        """Remove a specific user from the table."""
        await self.db.execute("DELETE FROM schedule_resin WHERE id=?", [user_id])
        await self.db.commit()

    async def update(
        self,
        user_id: int,
        *,
        next_check_time: Optional[datetime] = None,
        check_commission_time: Optional[datetime] = None,
    ) -> None:
        """Update specific user's column data."""
        if next_check_time:
            await self.db.execute(
                "UPDATE schedule_resin SET next_check_time=? WHERE id=?",
                [next_check_time.isoformat(), user_id],
            )
        if check_commission_time:
            await self.db.execute(
                "UPDATE schedule_resin SET check_commission_time=? WHERE id=?",
                [check_commission_time.isoformat(), user_id],
            )
        await self.db.commit()

    async def get(self, user_id: int) -> Optional[ScheduleResin]:
        """Get data for a specific user."""
        async with self.db.execute("SELECT * FROM schedule_resin WHERE id=?", [user_id]) as cursor:
            row = await cursor.fetchone()
            return ScheduleResin.from_row(row) if row else None

    async def get_all(self) -> List[ScheduleResin]:
        """Get data for all users."""
        async with self.db.execute("SELECT * FROM schedule_resin") as cursor:
            rows = await cursor.fetchall()
            return [ScheduleResin.from_row(row) for row in rows]
