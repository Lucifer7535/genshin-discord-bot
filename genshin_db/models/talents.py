from typing import List, Optional

from pydantic import BaseModel

from .base import GenshinDbBase, GenshinDbListBase


class Parameters(BaseModel):

    param1: Optional[List[float]] = None
    param2: Optional[List[float]] = None
    param3: Optional[List[float]] = None
    param4: Optional[List[float]] = None
    param5: Optional[List[float]] = None
    param6: Optional[List[float]] = None
    param7: Optional[List[float]] = None
    param8: Optional[List[float]] = None
    param9: Optional[List[float]] = None
    param10: Optional[List[float]] = None
    param11: Optional[List[float]] = None
    param12: Optional[List[float]] = None


class Attributes(BaseModel):
    labels: List[str]
    parameters: Parameters


class Combat(BaseModel):
    name: str
    description: str
    attributes: Attributes


class Passive(BaseModel):
    name: str
    description: str


class CostItem(BaseModel):
    name: str
    count: int


class Costs(BaseModel):
    lvl2: List[CostItem]
    lvl3: List[CostItem]
    lvl4: List[CostItem]
    lvl5: List[CostItem]
    lvl6: List[CostItem]
    lvl7: List[CostItem]
    lvl8: List[CostItem]
    lvl9: List[CostItem]
    lvl10: List[CostItem]


class Talent(GenshinDbBase):
    name: str
    combat1: Combat
    combat2: Combat
    combat3: Combat
    combatsp: Optional[Combat] = None
    passive1: Passive
    passive2: Passive
    passive3: Optional[Passive] = None
    costs: Costs
    version: str


class Talents(GenshinDbListBase[Talent]):
    __root__: List[Talent]
