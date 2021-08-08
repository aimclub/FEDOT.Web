from typing import List

from flask_accepts import responds
from flask_restx import Namespace, Resource

from .models import PipelineEpochMapping, SandboxDefaultParams
from .schema import PipelineEpochMappingSchema, SandboxDefaultParamsSchema
from .service import (pipelines_ids_for_epochs_in_case,
                      default_params_for_case)

api = Namespace("Sandbox", description="Data for sandbox")


@api.route("/epoch/<string:case_id>")
class SandBoxItemResource(Resource):
    """Showcase item"""

    @responds(schema=PipelineEpochMappingSchema, many=True)
    def get(self, case_id: str) -> List[PipelineEpochMapping]:
        """Get showcase item with specific case_id"""
        item = pipelines_ids_for_epochs_in_case(case_id)
        return item


@api.route("/params/<string:case_id>")
class SandBoxItemResource(Resource):
    """Showcase item"""

    @responds(schema=SandboxDefaultParamsSchema, many=False)
    def get(self, case_id: str) -> SandboxDefaultParams:
        """Get default params for specific case"""
        item = default_params_for_case(case_id)
        return item
