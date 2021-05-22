from flask_accepts import responds
from flask_restx import Namespace, Resource

from .history_convert_utils import history_to_graph
from .models import ComposingHistoryGraph
from .schema import ComposingHistoryGraphSchema
from .service import composer_history_for_case

api = Namespace("Composer",
                description="Operations with evolutionary composer")


@api.route("/<string:case_id>")
class ComposerHistoryResource(Resource):
    """Composer history"""

    @responds(schema=ComposingHistoryGraphSchema, many=False)
    def get(self, case_id) -> ComposingHistoryGraph:
        """Get history of the composer for the specific dataset"""
        history = history_to_graph(composer_history_for_case(case_id))
        return history
