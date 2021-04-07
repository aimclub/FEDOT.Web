from flask_accepts import responds
from flask_restx import Namespace, Resource

from .models import Showcase, ShowcaseItem
from .schema import ShowcaseItemSchema, ShowcaseSchema
from .service import all_showcase_items_ids, showcase_item_by_uid

api = Namespace("Showcase", description="Operations with showcase")


@api.route("/items/<string:case_id>")
class ShowCaseItemResource(Resource):
    """Showcase item"""

    @responds(schema=ShowcaseItemSchema, many=False)
    def get(self, case_id: str) -> ShowcaseItem:
        """Get showcase item with specific case_id"""
        item = showcase_item_by_uid(case_id)
        return item


@api.route("/")
class ShowCaseResource(Resource):
    """Showcase"""

    @responds(schema=ShowcaseSchema, many=False)
    def get(self) -> Showcase:
        """Get all available showcase items"""
        showcase_items_ids = all_showcase_items_ids()
        return Showcase(items_uids=showcase_items_ids)
