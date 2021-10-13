from typing import Any, Dict

from app.interfaces.serializable import CLASS_PATH_KEY, DELIMITER, Serializable


class Serializer(Serializable):

    def to_json(self) -> Dict[str, Any]:
        return super().to_json()

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


class HistorySerializer(Serializable):

    def to_json(self) -> Dict[str, Any]:
        return super().to_json()

    @classmethod
    def from_json(cls, json_obj: Dict[str, Any]):
        return super().from_json(json_obj)


class IndividualSerializer(Serializable):

    def to_json(self) -> Dict[str, Any]:
        return super().to_json()

    @classmethod
    def from_json(cls, json_obj: Dict[str, Any]):
        return super().from_json(json_obj)
