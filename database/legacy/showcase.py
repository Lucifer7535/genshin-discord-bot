import json
import zlib
from typing import Any, Dict, Optional

import aiosqlite


class ShowcaseTable:
    """Table for character showcase data."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db

    async def create(self) -> None:
        """Create the table in the database."""
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS showcase (
                uid int NOT NULL PRIMARY KEY,
                data blob
            )"""
        )
        await self.db.commit()

    async def add(self, uid: int, data: Optional[Dict[str, Any]] = None) -> None:
        """Add a user to the table."""
        json_data = json.dumps(data, ensure_ascii=False)
        compressed_data = zlib.compress(json_data.encode(encoding="utf8"), level=5)
        await self.db.execute(
            "INSERT OR REPLACE INTO showcase VALUES(?, ?)", [uid, compressed_data]
        )
        await self.db.commit()

    async def remove(self, uid: int) -> None:
        """Remove a specific user from the table."""
        await self.db.execute("DELETE FROM showcase WHERE uid=?", [uid])
        await self.db.commit()

    async def get(self, uid: int) -> Optional[Dict[str, Any]]:
        """Get data for a specific user."""
        async with self.db.execute("SELECT * FROM showcase WHERE uid=?", [uid]) as cursor:
            row = await cursor.fetchone()
            if row is not None:
                data = zlib.decompress(row["data"]).decode(encoding="utf8")
                return json.loads(data)
            return None
