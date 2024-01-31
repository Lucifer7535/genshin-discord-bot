from typing import List, Optional

from pydantic import BaseModel, Field, validator

from .base import GenshinDbBase, GenshinDbListBase


class Images(BaseModel):
    icon: str = Field(alias="filename_icon")


class Material(GenshinDbBase):
    name: str
    description: str
    rarity: Optional[int] = None
    category: str
    material_type: str = Field(alias="typeText")
    sources: List[str]
    images: Images

    drop_domain: Optional[str] = Field(None, alias="dropdomain")
    days_of_week: Optional[List[str]] = Field(None, alias="daysofweek")
    dupealias: Optional[str] = None
    version: Optional[str] = None

    @validator("version", pre=True)
    def remove_empty_version(cls, v: str) -> Optional[str]:
        return None if v == "" else v


class Materials(GenshinDbListBase[Material]):
    __root__: List[Material]
