import pathlib
from typing import Sequence, TypeVar

import sqlalchemy
from alembic import command as alembic_cmd
from alembic.config import Config as alembic_config
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.sql._typing import ColumnExpressionArgument

from .models import (
    Base,
    GenshinScheduleNotes,
    GenshinShowcase,
    GenshinSpiralAbyss,
    ScheduleDailyCheckin,
    StarrailShowcase,
    User,
)

DatabaseModel = Base
T_DatabaseModel = TypeVar("T_DatabaseModel", bound=Base)


_engine = create_async_engine("sqlite+aiosqlite:///data/bot/bot.db")
_sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)


class Database:
    """Database class providing class methods to operate on the database, including: initialize, close, insert, select, delete."""

    engine = _engine
    sessionmaker = _sessionmaker

    @classmethod
    async def init(cls) -> None:
        """Initialize the database; call this once when the bot starts."""
        alembic_cfg = alembic_config("database/alembic/alembic.ini")
        if pathlib.Path("data/bot/bot.db").exists():
            # If the database file exists, run the Alembic upgrade command
            alembic_cmd.upgrade(alembic_cfg, "head")
        else:
            # If the database file doesn't exist, create all tables and set the version to "head"
            async with cls.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            alembic_cmd.stamp(alembic_cfg, "head")

    @classmethod
    async def close(cls) -> None:
        """Close the database; call this once before the bot shuts down."""
        await cls.engine.dispose()

    @classmethod
    async def insert_or_replace(cls, instance: DatabaseModel) -> None:
        """Insert an object into the database, replacing the old object if the same Primary Key exists.
        Example: `Database.insert_or_replace(User(discord_id=123))`

        Parameters:
        ------
        instance: `DatabaseModel`
            Instance object of the database table (ORM).
        """
        async with cls.sessionmaker() as session:
            await session.merge(instance)
            await session.commit()

    @classmethod
    async def select_one(
        cls,
        table: type[T_DatabaseModel],
        whereclause: ColumnExpressionArgument[bool] | None = None,
    ) -> T_DatabaseModel | None:
        """Specify a database table and a selection condition, select one object from the database.
        Example: `Database.select_one(User, User.discord_id.is_(id))`

        Parameters:
        ------
        table: `type[T_DatabaseModel]`
            Database table (ORM) class to select, e.g., `User`.
        whereclause: `ColumnExpressionArgument[bool]` | `None`
            Where selection condition of the ORM column, e.g., `User.discord_id.is_(123456)`.

        Returns:
        ------
        `T_DatabaseModel` | `None`:
            The object from the table that matches the conditions, or `None` if no match is found.
        """
        async with cls.sessionmaker() as session:
            stmt = sqlalchemy.select(table)
            if whereclause is not None:
                stmt = stmt.where(whereclause)
            result = await session.execute(stmt)
            return result.scalar()

    @classmethod
    async def select_all(
        cls,
        table: type[T_DatabaseModel],
        whereclause: ColumnExpressionArgument[bool] | None = None,
    ) -> Sequence[T_DatabaseModel]:
        """Specify a database table and a selection condition, select all objects from the database that match the conditions.

        Parameters:
        ------
        table: `type[T_DatabaseModel]`
            Database table (ORM) class to select, e.g., `GenshinSpiralAbyss`.
        whereclause: `ColumnExpressionArgument[bool]` | `None`
            - Where selection condition of the ORM column. If `None`, select all data from the table.
            - e.g., `GenshinSpiralAbyss.discord_id.is_(123456)`.

        Returns:
        ------
        `Sequence[T_DatabaseModel]`:
            All objects from the table that match the conditions specified.
        """
        async with cls.sessionmaker() as session:
            stmt = sqlalchemy.select(table)
            if whereclause is not None:
                stmt = stmt.where(whereclause)
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def delete_instance(cls, instance: DatabaseModel) -> None:
        """Delete the object from the database. To use, first use the `select_one` or `select_all` methods to get the object instance, then pass it to this method for deletion.  # noqa

        Parameters:
        ------
        instance: `DatabaseModel`
            Instance object of the database table (ORM).
        """
        async with cls.sessionmaker() as session:
            await session.delete(instance)
            await session.commit()

    @classmethod
    async def delete(
        cls, table: type[T_DatabaseModel], whereclause: ColumnExpressionArgument[bool]
    ) -> None:
        """Specify a database table and a where condition, delete objects from the database that match the conditions.
        Example: `Database.delete(User, User.discord_id.is_(id))`

        Parameters:
        ------
        table: `type[T_DatabaseModel]`
            Database table (ORM) class to select, e.g., `User`.
        whereclause: `ColumnExpressionArgument[bool]` | `None`
            Where selection condition of the ORM column, e.g., `User.discord_id.is_(123456)`.
        """
        instances = await cls.select_all(table, whereclause)
        for instance in instances:
            await cls.delete_instance(instance)

    @classmethod
    async def delete_all(cls, discord_id: int) -> None:
        """Specify a user's discord_id, delete all data of this user from the database.

        Parameters:
        ------
        discord_id: `int`
            User's Discord ID.
        """
        user = await cls.select_one(User, User.discord_id.is_(discord_id))
        if user is None:
            return
        await cls.delete(User, User.discord_id.is_(discord_id))
        await cls.delete(ScheduleDailyCheckin, ScheduleDailyCheckin.discord_id.is_(discord_id))
        await cls.delete(GenshinScheduleNotes, GenshinScheduleNotes.discord_id.is_(discord_id))
        await cls.delete(GenshinSpiralAbyss, GenshinSpiralAbyss.discord_id.is_(discord_id))
        await cls.delete(GenshinShowcase, GenshinShowcase.uid.is_(user.uid_genshin))
        await cls.delete(StarrailShowcase, StarrailShowcase.uid.is_(user.uid_starrail))
        await cls.delete(User, User.discord_id.is_(discord_id))
