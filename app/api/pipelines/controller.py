from typing import Optional
from uuid import uuid4

from app import storage
from flask import request
from flask_accepts import accepts, responds
from flask_cors import cross_origin
from flask_restx import Namespace, Resource

from ..data.service import get_input_data
from .models import (PipelineGraph, PipelineImage, PipelineResponse,
                     PipelineValidationResponse)
from .pipeline_convert_utils import graph_to_pipeline, pipeline_to_graph
from .schema import (PipelineGraphSchema, PipelineImageSchema,
                     PipelineResponseSchema, PipelineValidationResponseSchema)
from .service import (create_pipeline, get_image_url, pipeline_by_uid,
                      validate_pipeline)

api = Namespace("Pipelines", description="Operations with pipelines")


@cross_origin()
@api.route("/<string:uid>")
class PipelinesIdResource(Resource):
    """Pipelines"""

    @responds(schema=PipelineGraphSchema, many=False)
    def get(self, uid: str) -> Optional[PipelineGraph]:
        """Get pipeline with specific UID"""
        pipeline = pipeline_by_uid(uid)
        if pipeline is None:
            return None
        pipeline_graph = pipeline_to_graph(pipeline)
        pipeline_graph.uid = uid

        return pipeline_graph


@cross_origin()
@api.route("/validate", methods=['POST', 'OPTIONS'])
class PipelinesValidateResource(Resource):
    """Pipeline validation"""

    @accepts(schema=PipelineGraphSchema, api=api)
    @responds(schema=PipelineValidationResponseSchema, many=False)
    def post(self) -> PipelineValidationResponse:
        """Validate pipeline with specific structure"""

        try:
            graph_dict = request.parsed_obj
            pipeline = graph_to_pipeline(graph_dict)
            is_valid, msg = validate_pipeline(pipeline)
        except Exception as _:
            is_valid = False
            msg = 'Incorrect pipeline'

        return PipelineValidationResponse(is_valid, msg)

    def options(self):
        return True


@cross_origin()
@api.route("/add", methods=['POST', 'OPTIONS'])
class PipelinesAddResource(Resource):
    @accepts(schema=PipelineGraphSchema, api=api)
    @responds(schema=PipelineResponseSchema)
    def post(self) -> PipelineResponse:
        """Preserve new pipeline"""

        graph = request.parsed_obj
        pipeline = graph_to_pipeline(graph)
        is_correct = validate_pipeline(pipeline)

        new_uid = str(uuid4())
        if is_correct:
            uid, is_exists = create_pipeline(new_uid, pipeline)
            return PipelineResponse(uid, is_exists)
        else:
            return PipelineResponse(None, False)

    def options(self):
        return True


@cross_origin()
@api.route("/image/<string:uid>")
class PipelinesIdImage(Resource):
    """Pipelines"""

    @responds(schema=PipelineImageSchema, many=False)
    def get(self, uid: str) -> PipelineImage:
        """Get image of pipeline with specific UID"""

        pipeline = pipeline_by_uid(uid)
        filename = f'{uid}.png'
        image_url = get_image_url(filename, pipeline)

        return PipelineImage(uid, image_url)
