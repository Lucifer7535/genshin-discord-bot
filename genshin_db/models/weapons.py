import re
from typing import List, Optional

from pydantic import BaseModel, Field

from .base import GenshinDbBase, GenshinDbListBase


class AscendItem(BaseModel):
    name: str
    count: Optional[int] = None


class AscendCosts(BaseModel):
    ascend1: List[AscendItem]
    ascend2: List[AscendItem]
    ascend3: List[AscendItem]
    ascend4: List[AscendItem]
    ascend5: Optional[List[AscendItem]] = None
    ascend6: Optional[List[AscendItem]] = None


class Refine(BaseModel):
    description: str
    values: List[str]


class Images(BaseModel):
    icon_url: Optional[str] = Field(None, alias="icon")
    awaken_icon_url: Optional[str] = Field(None, alias="awakenicon")

    icon: str = Field(alias="filename_icon")
    gacha: str = Field(alias="filename_gacha")
    awakenicon: str = Field(alias="filename_awakenIcon")


class Weapon(GenshinDbBase):
    name: str
    description: str
    weapontype: str = Field(alias="weaponText")
    rarity: int
    story: str

    base_atk: int = Field(alias="baseAtkValue")
    mainstat: Optional[str] = Field(None, alias="mainStatText")
    mainvalue: Optional[str] = Field(None, alias="baseStatText")

    effect_name: Optional[str] = Field(None, alias="effectName")
    effect_template: Optional[str] = Field(None, alias="effectTemplateRaw")
    r1: Optional[Refine] = None
    r2: Optional[Refine] = None
    r3: Optional[Refine] = None
    r4: Optional[Refine] = None
    r5: Optional[Refine] = None

    ascend_costs: AscendCosts = Field(alias="costs")
    images: Images
    version: str

    @property
    def effect_desciption(self) -> str:
        if self.r1 is None or self.effect_template is None:
            return ""
        refines = [self.r1.values, [], [], [], []]
        if self.r2:
            refines[1] = self.r2.values
        if self.r3:
            refines[2] = self.r3.values
        if self.r4:
            refines[3] = self.r4.values
        if self.r5:
            refines[4] = self.r5.values

        nums = len(self.r1.values)
        refine_values: List[str] = []
        for i in range(nums):
            refine_values.append(str(refines[0][i]))
            for j in range(1, 5):
                if i < len(refines[j]):
                    refine_values[i] += f"/{refines[j][i]}"

        result = re.sub(r"<[^>]+>", "", self.effect_template)
        for i in range(nums):
            result = result.replace(f"{{{i}}}", refine_values[i])
        return result


class Weapons(GenshinDbListBase[Weapon]):
    __root__: List[Weapon]
