from flask_accepts import responds
from flask_restx import Namespace, Resource

from .models import ShowcaseItem, Showcase
from .schema import ShowcaseItemSchema, ShowcaseSchema
from .service import showcase_item_by_uid, all_showcase_items_ids

api = Namespace("Showcase", description="Operations with showcase")


@api.route("/items/<string:uid>")
class ShowCaseItemResource(Resource):
    """Showcase item"""

    @responds(schema=ShowcaseItemSchema, many=False)
    def get(self, uid: str) -> ShowcaseItem:
        """Get showcase item with specific UID"""
        item = showcase_item_by_uid(uid)
        return item


@api.route("/")
class ShowCaseResource(Resource):
    """Showcase"""

    @responds(schema=ShowcaseSchema, many=False)
    def get(self) -> Showcase:
        """Get all available showcase items"""
        showcase_items_ids = all_showcase_items_ids()
        return Showcase(items_uids=showcase_items_ids)
