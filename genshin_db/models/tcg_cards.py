from pydantic import BaseModel, Field, validator

from ..api import API
from .base import GenshinDbBase, GenshinDbListBase
from .enums import CostElement


class DiceCost(BaseModel):

    amount: int = Field(alias="count")
    element: CostElement = Field(alias="costtype")


class Images(BaseModel):
    normal: str = Field(alias="filename_cardface")
    golden: str = Field(alias="filename_cardface_golden")
    image: str = Field(alias="filename_cardface_HD")


class Talent(BaseModel):
    id: int
    name: str
    effect: str = Field(alias="description")
    type: str
    costs: list[DiceCost] = Field(alias="playcost")


class CharacterCard(GenshinDbBase):
    id: int
    name: str
    hp: int
    max_energy: int = Field(alias="maxenergy")
    tags: list[str] = Field(alias="tagstext")
    story_title: str | None = Field(alias="storytitle")
    story_text: str | None = Field(alias="storytext")
    source: str | None
    talents: list[Talent] = Field(alias="skills")
    images: Images
    version: str

    @validator("story_text", pre=True)
    def remove_gender_tag(cls, v: str) -> str:
        return v.replace("{F#妳}{M#你}", "你")

    @property
    def image_url(self) -> str:
        return API.get_image_url(self.images.image)


class CharacterCards(GenshinDbListBase[CharacterCard]):
    __root__: list[CharacterCard]


class ActionCard(GenshinDbBase):

    id: int
    name: str
    type: str = Field(..., alias="cardtypetext")
    tags: list[str] = Field(alias="tagstext")
    effect: str = Field(alias="description")
    story_title: str | None = Field(alias="storytitle")
    story_text: str | None = Field(alias="storytext")
    source: str | None
    costs: list[DiceCost] = Field(alias="playcost")
    images: Images
    version: str

    @validator("story_text", pre=True)
    def remove_gender_tag(cls, v: str) -> str:
        return v.replace("{F#妳}{M#你}", "你")

    @property
    def image_url(self) -> str:
        return API.get_image_url(self.images.image)


class ActionCards(GenshinDbListBase[ActionCard]):
    __root__: list[ActionCard]


class Summon(GenshinDbBase):
    id: int
    name: str
    type: str = Field(alias="cardtypetext")
    effect: str = Field(alias="description")
    images: Images
    version: str

    @property
    def image_url(self) -> str:
        return API.get_image_url(self.images.image)


class Summons(GenshinDbListBase[Summon]):
    __root__: list[Summon]


class TCGCards:

    actions: ActionCards
    characters: CharacterCards
    summons: Summons

    def __init__(self, action_cards, character_cards, summons) -> None:
        self.actions = ActionCards.parse_obj(action_cards)
        self.characters = CharacterCards.parse_obj(character_cards)
        self.summons = Summons.parse_obj(summons)

    @property
    def list(self) -> list[ActionCard | CharacterCard | Summon]:
        return self.actions.list + self.characters.list + self.summons.list

    def find(self, item_name: str) -> ActionCard | CharacterCard | Summon | None:
        return (
            self.actions.find(item_name)
            or self.characters.find(item_name)
            or self.summons.find(item_name)
        )
