from typing import Any, Dict

from flask import redirect, url_for, request, jsonify
from flask_accepts import responds, accepts
from flask_restx import Namespace, Resource

from .history_convert_utils import history_to_graph
from .schema import ComposingHistoryGraphSchema, ComposingStartSchema
from .service import composer_history_for_case
from ..pipelines.service import pipeline_by_uid
from ..showcase.service import create_new_case_async
from ..showcase.showcase_utils import showcase_item_from_db
from ... import app

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


@api.route("/restart")
class ComposerRestartResource(Resource):
    """Composer restart"""

    @accepts(schema=ComposingStartSchema, api=api)
    def post(self):
        """Restart composer for the specific pipeline"""

        return redirect(url_for('start_async'), code=307)


@app.route('/start_async', methods=['POST'])
async def start_async():
    data = request.get_json()
    case_id = data['case_id']
    initial_uid = data['initial_uid']

    case = showcase_item_from_db(case_id)
    if case is None:
        raise ValueError(f'Showcase item for case_id={case_id} is None but should exist')

    pipeline = pipeline_by_uid(initial_uid)

    new_case_id = f'{case_id}-{initial_uid}'

    case_meta = {
        'task': case.metadata.task_name,
        'metric_name': case.metadata.metric_name,
        'dataset_name': case.metadata.dataset_name
    }
    await create_new_case_async(new_case_id, case_meta, None, initial_pipeline=pipeline)

    return jsonify(success=True)
