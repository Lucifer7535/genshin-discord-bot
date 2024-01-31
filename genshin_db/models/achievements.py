from typing import Any, Dict, List

from pydantic import BaseModel, Field, root_validator

from .base import GenshinDbBase, GenshinDbListBase


class Reward(BaseModel):
    name: str
    count: int


class StageDetail(BaseModel):
    title: str
    progress: int
    raw_description: str = Field(alias="description")
    reward: Reward

    @property
    def description(self) -> str:
        return self.raw_description.replace("{param0}", str(self.progress))


class Achievement(GenshinDbBase):
    id: list[int]
    name: str
    group: str = Field(alias="achievementGroupName")
    sort_order: int = Field(alias="sortOrder")
    stages: int
    stage_details: List[StageDetail]

    ishidden: bool = Field(False, alias="isHidden")
    version: str

    @root_validator(pre=True)
    def combine_stage(cls, data: Dict[str, Any]) -> Dict[str, Any]:

        stage_details = [data["stage1"]]
        if (stage2 := data.get("stage2")) is not None:
            stage_details.append(stage2)
        if (stage3 := data.get("stage3")) is not None:
            stage_details.append(stage3)
        data["stage_details"] = stage_details
        return data


class Achievements(GenshinDbListBase[Achievement]):
    __root__: List[Achievement]
