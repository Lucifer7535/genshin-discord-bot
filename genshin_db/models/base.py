from typing import Dict, Generic, List, TypeVar

from pydantic import BaseModel, PrivateAttr


class GenshinDbBase(BaseModel):

    name: str


T = TypeVar("T", bound=GenshinDbBase)


class GenshinDbListBase(BaseModel, Generic[T]):

    __root__: List[T]
    _name_item_dict: Dict[str, T] = PrivateAttr({})

    @property
    def list(self) -> List[T]:
        return self.__root__

    def find(self, name: str) -> T | None:
        if self._name_item_dict == {}:
            for item in self.list:
                self._name_item_dict[item.name] = item
        return self._name_item_dict.get(name)
