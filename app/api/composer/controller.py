from typing import Any, Dict

from flask_accepts import responds
from flask_restx import Namespace, Resource

from .history_convert_utils import history_to_graph
from .schema import ComposingHistoryGraphSchema
from .service import composer_history_for_case

api = Namespace("Composer",
                description="Operations with evolutionary composer")


@api.route("/<string:case_id>")
class ComposerHistoryResource(Resource):
    """Composer history"""

    @responds(schema=ComposingHistoryGraphSchema, many=False)
    def get(self, case_id: str) -> Dict[str, Any]:
        """Get history of the composer for the specific dataset"""
        graph_dict = history_to_graph(composer_history_for_case(case_id))
        return graph_dict
