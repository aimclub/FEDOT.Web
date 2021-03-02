from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource

from .models import ChainGraph, ChainResponse
from .schema import ChainResponseSchema, ChainGraphSchema
from .service import chain_by_uid, create_chain_from_graph

api = Namespace("Chains", description="Operations with chains")


def _chain_to_graph(chain):
    output_graph = dict()
    nodes = []
    links = []

    local_id = 0
    for chain_node in chain.nodes:
        node = dict()

        node['id'] = local_id
        chain_node.tmp_id = local_id
        node['display_name'] = chain_node.model.model_type
        node['model_name'] = chain_node.model.model_type
        node['class'] = 'model'
        node['params'] = chain_node.custom_params
        node['chain_node'] = chain_node

        nodes.append(node)
        local_id += 1

    for node in nodes:
        node['parents'] = []
        if node['chain_node'].nodes_from is not None:
            for chain_node_parent in node['chain_node'].nodes_from:
                node['parents'].append(chain_node_parent.tmp_id)
                link = dict()
                link['source'] = chain_node_parent.tmp_id
                link['target'] = node['id']
                links.append(link)
        else:
            node['class'] = 'preprocessing'  # TODO remove later
        del node['chain_node']

    output_graph['nodes'] = nodes
    output_graph['edges'] = links

    return output_graph


@api.route("/<string:uid>")
class ChainsIdResource(Resource):
    """Chains"""

    @responds(schema=ChainGraphSchema, many=False)
    def get(self, uid) -> ChainGraph:
        """Get chain with specific UID"""
        chain = chain_by_uid(uid)

        chain_graph = _chain_to_graph(chain)

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
