from typing import Any, Dict

from app.interfaces import Serializable
from fedot.core.optimisers.opt_history import OptHistory


class HistorySerializer(Serializable):

    def to_json(obj: OptHistory) -> Dict[str, Any]:
        serialized = {}
        for var, value in vars(obj).items():
            if isinstance(value, Se)
        return serialized

    def from_json(json_obj: Dict[str, Any]) -> OptHistory:
        obj = OptHistory()
        vars(obj).update(json_obj)
        return obj
