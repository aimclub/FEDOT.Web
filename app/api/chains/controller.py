from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource

from .chain_convert_utils import chain_to_graph
from .models import ChainGraph, ChainResponse
from .schema import ChainGraphSchema, ChainResponseSchema
from .service import chain_by_uid, create_chain_from_graph

api = Namespace("Chains", description="Operations with chains")


@api.route("/<string:uid>")
class ChainsIdResource(Resource):
    """Chains"""

    @responds(schema=ChainGraphSchema, many=False)
    def get(self, uid) -> ChainGraph:
        """Get chain with specific UID"""
        chain = chain_by_uid(uid)

        chain_graph = chain_to_graph(chain)

        return ChainGraph(uid=uid,
                          nodes=chain_graph['nodes'],
                          edges=chain_graph['edges'])


@api.route("/add")
class ChainsAddResource(Resource):
    @accepts(schema=ChainGraphSchema, api=api)
    @responds(schema=ChainResponseSchema)
    def post(self) -> ChainResponse:
        """Preserve new chain"""

        graph = request.parsed_obj
        uid, is_exists = create_chain_from_graph(graph)
        return ChainResponse(uid, is_exists)
