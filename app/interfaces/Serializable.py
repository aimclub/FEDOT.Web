import json
from abc import ABC, abstractmethod
from typing import Any, Dict


class Serializable(ABC):

    @abstractmethod
    def to_json(obj: Any) -> Dict[str, Any]:
        pass

    @abstractmethod
    def from_json(json_obj: Dict[str, Any]) -> Any:
        pass


def encoder(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, Serializable):
        return obj.to_json()
    raise TypeError(f"{obj=} can't be serialized!")


def decoder(json_obj: Dict[str, Any]) -> Any:
    print(json_obj)
    return json_obj
