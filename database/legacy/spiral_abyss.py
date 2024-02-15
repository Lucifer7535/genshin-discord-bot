from __future__ import annotations

import pickle
import zlib
from typing import Optional, Sequence, Union

import aiosqlite
import genshin


class CharacterData:
    id: int
    level: int
    friendship: int
    constellation: int
    weapon: Weapon
    artifacts: Sequence[Artifact]

    def __init__(self, character: genshin.models.Character) -> None:
        self.id = character.id
        self.level = character.level
        self.friendship = character.friendship
        self.constellation = character.constellation
        self.weapon = self.Weapon(character.weapon)
        self.artifacts = [self.Artifact(artifact) for artifact in character.artifacts]

    class Weapon:
        id: int
        level: int
        refinement: int

        def __init__(self, weapon: genshin.models.CharacterWeapon) -> None:
            self.id = weapon.id
            self.level = weapon.level
            self.refinement = weapon.refinement

    class Artifact:
        id: int
        pos: int
        level: int

        def __init__(self, artifact: genshin.models.Artifact) -> None:
            self.id = artifact.id
            self.pos = artifact.pos
            self.level = artifact.level


class SpiralAbyssData:
    id: int
    season: int
    abyss: genshin.models.SpiralAbyss
    characters: Optional[Sequence[CharacterData]] = None

    def __init__(
        self,
        id: int,
        abyss: genshin.models.SpiralAbyss,
        *,
        characters: Union[
            Sequence[genshin.models.Character], Sequence[CharacterData], None
        ] = None,
    ):
        self.id = id
        self.season = abyss.season
        self.abyss = abyss
        if characters is not None:
            self.characters = []
            for c in characters:
                self.characters.append(
                    CharacterData(c) if isinstance(c, genshin.models.Character) else c
                )

    @classmethod
    def fromRow(cls, row: aiosqlite.Row) -> SpiralAbyssData:
        abyss: genshin.models.SpiralAbyss = pickle.loads(zlib.decompress(row["abyss"]))
        characters: Optional[Sequence[CharacterData]] = (
            pickle.loads(zlib.decompress(row["characters"]))
            if row["characters"] is not None
            else None
        )
        return cls(row["id"], abyss=abyss, characters=characters)


class SpiralAbyssTable:

    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db

    async def create(self) -> None:
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS spiral_abyss (
                id int NOT NULL,
                season int NOT NULL,
                abyss blob NOT NULL,
                characters blob,
                PRIMARY KEY (id, season)
            )"""
        )
        await self.db.commit()

    async def add(self, data: SpiralAbyssData) -> None:
        abyss = zlib.compress(pickle.dumps(data.abyss), level=5)
        characters = (
            zlib.compress(pickle.dumps(data.characters), level=5)
            if data.characters is not None
            else None
        )
        await self.db.execute(
            "INSERT OR REPLACE INTO spiral_abyss VALUES(?, ?, ?, ?)",
            [data.id, data.season, abyss, characters],
        )
        await self.db.commit()

    async def remove(self, user_id: int, season: Optional[int] = None) -> None:
        if season:
            await self.db.execute(
                "DELETE FROM spiral_abyss WHERE id=? AND season=?", [user_id, season]
            )
        else:
            await self.db.execute("DELETE FROM spiral_abyss WHERE id=?", [user_id])
        await self.db.commit()

    async def get(self, user_id: int) -> Sequence[SpiralAbyssData]:
        async with self.db.execute(
            "SELECT * FROM spiral_abyss WHERE id=? ORDER BY season DESC", [user_id]
        ) as cursor:
            rows = await cursor.fetchall()
            return [SpiralAbyssData.fromRow(row) for row in rows]
