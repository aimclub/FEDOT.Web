from typing import List

from flask_accepts import responds
from flask_cors import cross_origin
from flask_restx import Namespace, Resource

from .models import ChainEpochMapping, SandboxDefaultParams
from .schema import ChainEpochMappingSchema, SandboxDefaultParamsSchema
from .service import (chains_ids_for_epochs_in_case,
                      default_params_for_case)

api = Namespace("Sandbox", description="Data for sandbox")


@cross_origin()
@api.route("/epoch/<string:case_id>")
class SandBoxItemResource(Resource):
    """Showcase item"""

    @responds(schema=ChainEpochMappingSchema, many=True)
    def get(self, case_id: str) -> List[ChainEpochMapping]:
        """Get showcase item with specific case_id"""
        item = chains_ids_for_epochs_in_case(case_id)
        return item


@cross_origin()
@api.route("/params/<string:case_id>")
class SandBoxItemResource(Resource):
    """Showcase item"""

    @responds(schema=SandboxDefaultParamsSchema, many=False)
    def get(self, case_id: str) -> SandboxDefaultParams:
        """Get default params for specific case"""
        item = default_params_for_case(case_id)
        return item
