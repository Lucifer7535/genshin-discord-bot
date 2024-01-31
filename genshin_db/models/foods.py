from typing import List, Optional

from pydantic import BaseModel, Field

from .base import GenshinDbBase, GenshinDbListBase


class Cooking(BaseModel):
    effect: str
    description: str


class Ingredient(BaseModel):
    name: str
    count: int


class Images(BaseModel):
    icon: str = Field(alias="filename_icon")


class Food(GenshinDbBase):
    name: str
    rarity: int
    food_type: str = Field(alias="filterText")
    description: str

    effect: str
    suspicious: Optional[Cooking] = None
    normal: Optional[Cooking] = None
    delici: Optional[Cooking] = None

    ingredients: List[Ingredient]
    images: Images
    version: str
    basedish: Optional[str] = None
    character: Optional[str] = None


class Foods(GenshinDbListBase[Food]):
    __root__: List[Food]
