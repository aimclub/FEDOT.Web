from importlib import import_module
from inspect import isclass
from typing import Any, Dict

from app.interfaces.serializable import (CLASS_PATH_KEY, DELIMITER,
                                         Serializable, _get_class)


class Serializer(Serializable):

    def to_json(self) -> Dict[str, Any]:
        return super().to_json()

    @classmethod
    def from_json(cls, json_obj: Dict[str, Any]):
        return super().from_json(json_obj)


class OperationMetaInfoSerializer(Serializable):

    def to_json(self) -> Dict[str, Any]:
        basic_serialization = super().to_json()
        strategy = basic_serialization['supported_strategies']
        if isclass(strategy):
            basic_serialization['supported_strategies'] = f'\
                {strategy.__module__}{DELIMITER}{strategy.__qualname__}'
        return basic_serialization

    @classmethod
    def from_json(cls, json_obj: Dict[str, Any]):
        json_obj['supported_strategies'] = _get_class(json_obj['supported_strategies'])
        return super().from_json(json_obj)


class LogSerializer(Serializable):

    def to_json(self) -> Dict[str, Any]:
        basic_serialization = super().to_json()
        del basic_serialization['logger']  # cause it will be automatically generated in __init__
        return basic_serialization

    @classmethod
    def from_json(cls, json_obj: Dict[str, Any]):
        return super().from_json(json_obj)


class EnumSerializer(Serializable):

    def to_json(self):
        return {
            "value": self.value,
            CLASS_PATH_KEY: f'{self.__module__}{DELIMITER}{self.__class__.__qualname__}'
        }

    @classmethod
    def from_json(cls, json_obj: Dict[str, Any]):
        return cls(json_obj["value"])
