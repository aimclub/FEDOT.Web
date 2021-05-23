from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource

from .chain_convert_utils import chain_to_graph, graph_to_chain
from .models import ChainGraph, ChainResponse, ChainValidationResponse, ChainImage
from .schema import (ChainGraphSchema, ChainResponseSchema,
                     ChainValidationResponseSchema, ChainImageSchema)
from .service import chain_by_uid, create_chain, validate_chain

from app.api.showcase.service import generate_image, get_image_url

api = Namespace("Chains", description="Operations with chains")


@api.route("/<string:uid>")
class ChainsIdResource(Resource):
    """Chains"""

    @responds(schema=ChainGraphSchema, many=False)
    def get(self, uid) -> ChainGraph:
        """Get chain with specific UID"""
        chain = chain_by_uid(uid)
        chain_graph = chain_to_graph(chain)
        chain_graph.uid = uid

        return chain_graph


@api.route("/validate")
class ChainsValidateResource(Resource):
    """Chain validation"""

    @accepts(schema=ChainGraphSchema, api=api)
    @responds(schema=ChainValidationResponseSchema, many=False)
    def post(self) -> ChainValidationResponse:
        """Validate chain with specific structure"""

        try:
            graph_dict = request.parsed_obj
            chain = graph_to_chain(graph_dict)
            is_valid, msg = validate_chain(chain)
        except Exception as _:
            is_valid = False
            msg = 'Incorrect chain'

        return ChainValidationResponse(is_valid, msg)


@api.route("/add")
class ChainsAddResource(Resource):
    @accepts(schema=ChainGraphSchema, api=api)
    @responds(schema=ChainResponseSchema)
    def post(self) -> ChainResponse:
        """Preserve new chain"""

        graph = request.parsed_obj
        chain = graph_to_chain(graph)
        is_correct = validate_chain(chain)
        if is_correct:
            uid, is_exists = create_chain(graph['uid'], chain)
            return ChainResponse(uid, is_exists)
        else:
            return ChainResponse(None, False)


@api.route("/image/<string:uid>")
class ChainsIdImage(Resource):
    """Chains"""

    @responds(schema=ChainImageSchema, many=False)
    def get(self, uid) -> ChainGraph:
        """Get image of chain with specific UID"""

        chain = chain_by_uid(uid)
        filename = uid + '.png'
        generate_image(filename, chain)
        image_url = get_image_url(filename)

        return ChainImage(uid, image_url)
