from typing import List, Optional

from flask_accepts import responds
from flask_restx import Namespace, Resource

from .models import ShowcaseItem
from .schema import ShowcaseItemSchema
from .service import all_showcase_items_ids, showcase_full_item_by_uid
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
        showcase_items = [showcase_item_from_db(case_id) for case_id in all_showcase_items_ids()]
        return [item for item in showcase_items if item is not None]
