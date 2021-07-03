from typing import List

from flask_accepts import responds
from flask_restx import Namespace, Resource

from .models import ShowcaseItem
from .schema import ShowcaseItemSchema
from .service import all_showcase_items_ids, showcase_full_item_by_uid, showcase_item_by_uid

api = Namespace("Showcase", description="Operations with showcase")


@api.route("/items/<string:case_id>")
class ShowCaseItemResource(Resource):
    """Showcase item"""

    @responds(schema=ShowcaseItemSchema, many=False)
    def get(self, case_id: str) -> ShowcaseItem:
        """Get detailed showcase item with specific case_id"""
        item = showcase_full_item_by_uid(case_id)
        return item


@api.route("/")
class ShowCaseResource(Resource):
    """Showcase"""

    @responds(schema=ShowcaseItemSchema, many=True)
    def get(self) -> List[ShowcaseItem]:
        """Get all available showcase items"""
        showcase_items_ids = all_showcase_items_ids()
        return [showcase_item_by_uid(case_id) for case_id in showcase_items_ids]
