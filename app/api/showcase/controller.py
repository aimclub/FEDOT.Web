from typing import List, Optional

from flask import request
from flask_accepts import accepts, responds
from flask_cors import cross_origin
from flask_restx import Namespace, Resource

from .models import ShowcaseItem
from .schema import ShowcaseItemAddingSchema, ShowcaseItemSchema
from .service import all_showcase_items_ids, showcase_full_item_by_uid, create_new_case
from .showcase_utils import showcase_item_from_db

api = Namespace("Showcase", description="Operations with showcase")


@api.route("/items/<string:case_id>")
class ShowCaseItemResource(Resource):
    """Showcase item"""

    @responds(schema=ShowcaseItemSchema, many=False)
    def get(self, case_id: str) -> Optional[ShowcaseItem]:
        """Get detailed showcase item with specific case_id"""
        item = showcase_full_item_by_uid(case_id)
        return item


@api.route("/")
class ShowCaseResource(Resource):
    """Showcase"""

    @responds(schema=ShowcaseItemSchema, many=True)
    def get(self) -> List[ShowcaseItem]:
        """Get all available showcase items"""
        showcase_items = [showcase_item_from_db(case_id) for case_id in all_showcase_items_ids(with_custom=True)]
        return [item for item in showcase_items if item is not None]


@cross_origin()
@api.route("/add", methods=['POST', 'OPTIONS'])
class ShowCaseItemAddResource(Resource):
    """Showcase item"""

    @accepts(schema=ShowcaseItemAddingSchema, api=api)
    def post(self) -> bool:
        """Add case with specific case_id"""
        case_json = request.parsed_obj

        case_meta_json = case_json['case']
        opt_history_json = case_json['history']

        case_id = f"custom_{case_meta_json['case_id']}"

        if case_id in all_showcase_items_ids():
            return False

        create_new_case(case_id, case_meta_json, opt_history_json)

        return True

    def options(self):
        return True
