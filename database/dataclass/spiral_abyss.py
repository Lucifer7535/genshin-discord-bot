from pydantic import BaseModel


class Weapon(BaseModel):
    """Weapon Data

    Attributes
    -----
    id: `int`
        Weapon ID
    level: `int`
        Weapon level
    refinement: `int`
        Weapon refinement
    """

    id: int
    """Weapon ID"""
    level: int
    """Weapon level"""
    refinement: int
    """Weapon refinement"""

    class Config:
        orm_mode = True


class Artifact(BaseModel):
    """Artifact Data

    Attributes
    -----
    id: `int`
        Artifact ID
    pos: `int`
        Artifact equipment position
    level: `int`
        Artifact level
    """

    id: int
    """Artifact ID"""
    pos: int
    """Artifact equipment position"""
    level: int
    """Artifact level"""

    class Config:
        orm_mode = True


class CharacterData(BaseModel):
    """Custom Abyss character data to be stored in the database

    Attributes
    -----
    id: `int`
        Character ID
    level: `int`
        Character level
    friendship: `int`
        Character friendship level
    constellation: `int`
        Character constellation
    weapon: `Weapon`
        Weapon equipped by the character
    artifacts: `list[Artifact]`
        Artifacts equipped by the character
    """

    id: int
    """Character ID"""
    level: int
    """Character level"""
    friendship: int
    """Character friendship level"""
    constellation: int
    """Character constellation"""
    weapon: Weapon
    """Weapon equipped by the character"""
    artifacts: list[Artifact]
    """Artifacts equipped by the character"""

    class Config:
        orm_mode = True
