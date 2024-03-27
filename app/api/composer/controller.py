from typing import Any, Dict

from flask import redirect, url_for, request, jsonify, Blueprint
from flask_accepts import responds, accepts
from flask_restx import Namespace, Resource

from .history_convert_utils import history_to_graph
from .schema import ComposingHistoryGraphSchema, ComposingStartSchema
from .service import composer_history_for_case
from utils import clean_case_id
from ..pipelines.service import pipeline_by_uid
from ..showcase.service import create_new_case_async
from ..showcase.showcase_utils import showcase_item_from_db

api = Namespace("Composer",
                description="Operations with evolutionary composer")

async_composer = Blueprint('async_composer', __name__, url_prefix='/async_composer')


@api.route("/<string:case_id>")
class ComposerHistoryResource(Resource):
    """Composer history"""

    @responds(schema=ComposingHistoryGraphSchema, many=False)
    def get(self, case_id: str) -> Dict[str, Any]:
        """Get history of the composer for the specific dataset"""
        show_full = '_full' in case_id
        case_id = clean_case_id(case_id)
        graph_dict = history_to_graph(composer_history_for_case(case_id), show_full)
        return graph_dict


@api.route("/restart")
class ComposerRestartResource(Resource):
    """Composer restart"""

    @accepts(schema=ComposingStartSchema, api=api)
    def post(self):
        """Restart composer for the specific pipeline"""

        return redirect(url_for('async_composer.start_async'), code=307)


@async_composer.route('/start_async', methods=['POST'])
async def start_async():
    data = request.get_json()
    case_id = data['case_id']
    case_id = clean_case_id(case_id)
    initial_uid = data['initial_uid']
    gen_index = data.get('gen_index', None)
    original_uid = data.get('original_uid', None)

    case = showcase_item_from_db(case_id)
    if case is None:
        raise ValueError(f'Showcase item for case_id={case_id} is None but should exist')

    pipeline = pipeline_by_uid(initial_uid)

    new_case_id = f'restart_{case_id}-{initial_uid}'

    case_meta = {
        'task': case.metadata.task_name,
        'metric_name': case.metadata.metric_name,
        'dataset_name': case.metadata.dataset_name
    }

    if case.metadata.task_name == 'golem':
        is_golem_history = True
    else:
        is_golem_history = False

    if original_uid:
        original_history = composer_history_for_case(case_id)
    else:
        original_history = None
    await create_new_case_async(new_case_id, case_meta, None, initial_pipeline=pipeline,
                                original_history=original_history, modifed_generation_index=gen_index,
                                original_uid=original_uid, is_golem_history=is_golem_history)

    return jsonify(success=True)
