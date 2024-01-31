from typing import List, Optional

from pydantic import BaseModel, Field

from .base import GenshinDbBase, GenshinDbListBase


class PartDetail(BaseModel):
    name: str
    relictype: str = Field(alias="relicText")
    description: str
    story: str


class Images(BaseModel):
    flower_url: Optional[str] = Field(None, alias="flower")
    plume_url: Optional[str] = Field(None, alias="plume")
    sands_url: Optional[str] = Field(None, alias="sands")
    goblet_url: Optional[str] = Field(None, alias="goblet")
    circlet_url: str = Field(alias="circlet")


class Artifact(GenshinDbBase):
    name: str
    rarity: List[int] = Field(alias="rarityList")
    effect_1pc: Optional[str] = Field(None, alias="effect1Pc")
    effect_2pc: Optional[str] = Field(None, alias="effect2Pc")
    effect_4pc: Optional[str] = Field(None, alias="effect4Pc")

    flower: Optional[PartDetail] = None
    plume: Optional[PartDetail] = None
    sands: Optional[PartDetail] = None
    goblet: Optional[PartDetail] = None
    circlet: PartDetail
    images: Images
    version: str


class Artifacts(GenshinDbListBase[Artifact]):
    __root__: List[Artifact]
