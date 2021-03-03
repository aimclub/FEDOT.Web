from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource

from .models import ChainGraph, ChainResponse
from .schema import ChainGraphSchema, ChainResponseSchema
from .service import chain_by_uid, create_chain_from_graph

api = Namespace("Chains", description="Operations with chains")


def _chain_to_graph(chain):
    output_graph = {}
    nodes = []
    edges = []

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
        node['children'] = []
        if node['chain_node'].nodes_from is not None:
            for chain_node_parent in node['chain_node'].nodes_from:
                # fill parents field
                node['parents'].append(chain_node_parent.tmp_id)

                # create edge
                edge = dict()
                edge['source'] = chain_node_parent.tmp_id
                edge['target'] = node['id']
                edges.append(edge)

            childs = chain.node_childs(node['chain_node'])
            if childs is not None:
                # fill childs field
                for chain_node_child in childs:
                    node['children'].append(chain_node_child.tmp_id)
        else:
            node['class'] = 'preprocessing'  # TODO remove later
        del node['chain_node']

    output_graph['nodes'] = nodes
    output_graph['edges'] = edges

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
