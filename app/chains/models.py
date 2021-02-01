from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource

from .chain import Chain, ChainResponse
from .schema import ChainResponseSchema, ChainSchema
from .service import chain_by_uid, create_chain_from_graph

api = Namespace("Chains", description="Operations with chains")


@api.route("/<string:uid>")
class ChainsIdResource(Resource):
    """Chains"""

    @responds(schema=ChainSchema, many=False)
    def get(self, uid) -> Chain:
        """Get chain with specific UID"""
        chain = chain_by_uid(uid)

        return Chain(uid=chain['uid'],
                     nodes=chain['nodes'])


@api.route("/add")
class ChainsAddResource(Resource):
    @accepts(schema=ChainSchema, api=api)
    @responds(schema=ChainResponseSchema)
    def post(self) -> ChainResponse:
        """Preserve new chain"""

        graph = request.parsed_obj
        uid, is_exists = create_chain_from_graph(graph)
        return ChainResponse(uid, is_exists)
