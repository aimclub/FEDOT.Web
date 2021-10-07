import json
from abc import ABC, abstractmethod
from importlib import import_module
from typing import Any, Dict

DELIMITER = '/'


class Serializable(ABC):

    @abstractmethod
    def to_json(self, obj: Any) -> Dict[str, Any]:
        pass

    @abstractmethod
    def from_json(self, json_obj: Dict[str, Any]) -> Any:
        pass


def encoder(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, Serializable):
        return obj.to_json()
    raise TypeError(f"{obj=} can't be serialized!")


def _get_class_instance(class_path: str) -> Any:
    module_name, class_name = class_path.split(DELIMITER)
    obj = import_module(module_name)
    for sub in class_name.split('.'):
        obj = getattr(obj, sub)
    return obj()


def decoder(json_obj: Dict[str, Any]) -> Any:
    if 'class_path' in json_obj:
        class_instance = _get_class_instance(json_obj['class_path'])
        if isinstance(class_instance, Serializable):
            return class_instance.from_json(json_obj)
    return json_obj
