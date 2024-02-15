from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple, Union

import aiosqlite

from utility.utils import get_app_command_mention


class User:
    id: int
    cookie: str
    uid: Optional[int]
    uid_starrail: Optional[int]
    last_used_time: Optional[datetime]
    invalid_cookie: int

    def __init__(
        self,
        id: int,
        cookie: str = "",
        *,
        uid: Optional[int] = None,
        uid_starrail: Optional[int] = None,
        last_used_time: Optional[Union[datetime, str]] = None,
        invalid_cookie: int = 0,
    ):
        self.id = id
        self.cookie = cookie
        self.uid = uid
        self.uid_starrail = uid_starrail
        self.last_used_time = (
            datetime.fromisoformat(last_used_time)
            if isinstance(last_used_time, str)
            else last_used_time
        )
        self.invalid_cookie = invalid_cookie

    @classmethod
    def fromRow(cls, row: aiosqlite.Row) -> User:
        return cls(
            id=row["id"],
            cookie=row["cookie"],
            uid=row["uid"],
            uid_starrail=row["uid_starrail"],
            last_used_time=row["last_used_time"],
            invalid_cookie=row["invalid_cookie"],
        )


class UsersTable:

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self) -> None:
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id int NOT NULL PRIMARY KEY,
                cookie text NOT NULL,
                uid int,
                uid_starrail int,
                last_used_time text,
                invalid_cookie int NOT NULL
            )"""
        )
        cursor = await self.db.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in await cursor.fetchall()]
        if "invalid_cookie" not in columns:
            await self.db.execute(
                "ALTER TABLE users ADD COLUMN invalid_cookie int NOT NULL DEFAULT '0'"
            )
        if "uid_starrail" not in columns:
            await self.db.execute("ALTER TABLE users ADD COLUMN uid_starrail int")
        await self.db.commit()

    async def add(self, user: User) -> None:
        await self.db.execute(
            "INSERT OR REPLACE INTO users "
            "(id, cookie, uid, uid_starrail, last_used_time, invalid_cookie) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                user.id,
                user.cookie,
                user.uid,
                user.uid_starrail,
                user.last_used_time or datetime.now().isoformat(),
                user.invalid_cookie,
            ],
        )
        await self.db.commit()

    async def get(self, user_id: int) -> Optional[User]:
        async with self.db.execute("SELECT * FROM users WHERE id=?", [user_id]) as cursor:
            row = await cursor.fetchone()
            return User.fromRow(row) if row else None

    async def getAll(self) -> List[User]:
        async with self.db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            return [User.fromRow(row) for row in rows]

    async def remove(self, user_id: int) -> None:
        await self.db.execute("DELETE FROM users WHERE id=?", [user_id])
        await self.db.commit()

    async def update(
        self,
        user_id: int,
        *,
        cookie: Optional[str] = None,
        uid: Optional[int] = None,
        uid_starrail: Optional[int] = None,
        last_used_time: bool = False,
        invalid_cookie: bool = False,
    ) -> None:
        if cookie:
            await self.db.execute("UPDATE users SET cookie=? WHERE id=?", [cookie, user_id])
        if uid:
            await self.db.execute("UPDATE users SET uid=? WHERE id=?", [uid, user_id])
        if uid_starrail:
            await self.db.execute(
                "UPDATE users SET uid_starrail=? WHERE id=?", [uid_starrail, user_id]
            )
        if last_used_time:
            await self.db.execute(
                "UPDATE users SET last_used_time=? WHERE id=?",
                [datetime.now().isoformat(), user_id],
            )
        if invalid_cookie:
            await self.db.execute(
                "UPDATE users SET invalid_cookie=invalid_cookie+1 WHERE id=?", [user_id]
            )
        await self.db.commit()

    async def exist(
        self,
        user: Optional[User],
        *,
        check_cookie=True,
        check_uid=True,
    ) -> Tuple[bool, Optional[str]]:
        if user is None:
            return False, f'User not found. Please set the Cookie (use {get_app_command_mention("cookie-login")} for instructions).' # noqa
        if check_cookie and not user.cookie:
            return False, f'Cookie not found. Please set the Cookie (use {get_app_command_mention("cookie-login")} for instructions).' # noqa
        if check_uid and user.uid is None:
            return False, f'UID for Genshin Impact not found. Please set the UID using {get_app_command_mention("uid-settings")}.'
        await self.update(user.id, last_used_time=True)
        return True, None
