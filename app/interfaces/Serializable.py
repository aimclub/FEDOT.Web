import json
from abc import ABC, abstractmethod
from dataclasses import is_dataclass
from importlib import import_module
from typing import Any, Dict

DELIMITER = '/'
CLASS_PATH_KEY = '_class_path'


class Serializable(ABC):

    @abstractmethod
    def to_json(self):
        return {
            **vars(self),
            CLASS_PATH_KEY: f'{self.__module__}{DELIMITER}{self.__class__.__qualname__}'
        }

    @classmethod
    @abstractmethod
    def from_json(cls, json_obj: Dict[str, Any]):
        obj = cls()
        del json_obj[CLASS_PATH_KEY]
        vars(obj).update(json_obj)
        return obj


def encoder(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, Serializable):
        return obj.to_json()
    raise TypeError(f'{obj=} can\'t be serialized!')


def _get_class(class_path: str) -> Any:
    module_name, class_name = class_path.split(DELIMITER)
    obj = import_module(module_name)
    for sub in class_name.split('.'):
        obj = getattr(obj, sub)
    return obj


def decoder(json_obj: Dict[str, Any]) -> Any:
    if CLASS_PATH_KEY in json_obj:
        cls_obj = _get_class(json_obj[CLASS_PATH_KEY])
        if issubclass(cls_obj, Serializable):
            return cls_obj.from_json(json_obj)
        raise TypeError(f'Parsed {cls_obj=} is not serializable, but should be')
    return json_obj
