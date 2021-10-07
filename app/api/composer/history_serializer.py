from typing import Any, Dict

from app.interfaces import Serializable
from fedot.core.optimisers.opt_history import OptHistory


class HistorySerializer(Serializable):

    def to_json(self, obj: OptHistory) -> Dict[str, Any]:
        serialized = vars(obj)
        serialized["class_path"] = f"{obj.__module__}{Serializable.DELIMITER}{obj.__class__.__qualname__}"
        return serialized

    def from_json(self, json_obj: Dict[str, Any]) -> OptHistory:
        obj = OptHistory()
        vars(obj).update(json_obj)
        return obj
