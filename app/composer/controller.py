from flask_accepts import responds
from flask_restx import Namespace, Resource

from .entities import ComposingHistory
from .schema import ComposingHistorySchema
from .service import composer_history_for_experiment

api = Namespace("Composer",
                description="Operations with evolutionary composer")


@api.route("/<string:dataset_id>")
class ComposerHistoryResource(Resource):
    """Chains"""

    @responds(schema=ComposingHistorySchema, many=False)
    def get(self, dataset_id) -> ComposingHistory:
        """Get chain for specific dataset"""
        history = composer_history_for_experiment(dataset_id)

        return ComposingHistory(history)
