from abc import ABC
from inspect import signature
from typing import Any, List, Mapping

from fedot.core.dag.graph import Graph
from fedot.core.dag.graph_operator import GraphOperator
from fedot.core.dag.node_operator import NodeOperator
from fedot.core.operations.evaluation.evaluation_interfaces import \
    SkLearnEvaluationStrategy
from fedot.core.operations.model import Model
from fedot.core.operations.operation_template import OperationTemplate
from fedot.core.optimisers.gp_comp.individual import Individual
from fedot.core.optimisers.graph import OptGraph
from fedot.core.optimisers.opt_history import OptHistory, ParentOperator
from fedot.core.pipelines.node import Node, PrimaryNode, SecondaryNode
from fedot.core.pipelines.pipeline import Pipeline
from fedot.core.pipelines.template import PipelineTemplate
from fedot.core.repository.dataset_types import DataTypesEnum
from fedot.core.repository.operation_types_repository import (
    OperationMetaInfo, OperationTypesRepository)
from fedot.core.repository.tasks import TaskTypesEnum
from marshmallow import Schema, fields
from marshmallow.decorators import post_load
from marshmallow.exceptions import ValidationError


class ComposingHistoryGraphSchema(Schema):
    """Composing history graph"""

    uid = fields.String(attribute='uid')
    nodes = fields.Dict(attribute='nodes')
    edges = fields.Dict(attribute='edges')
    dataset_name = fields.String(attribute='dataset_name')
    task_name = fields.String(attribute='task_name')
    is_finished = fields.Boolean(attribute='is_finished')


class SchemaLoader(Schema):

    @post_load
    def make_object(self, data, **kwargs):
        init_data = {
            k: v
            for k, v in data.items()
            if k in signature(type(self).__model__.__init__).parameters
        }
        obj = type(self).__model__(**init_data)
        vars(obj).update(data)
        return obj


class UnionField(fields.Field):
    """Field that deserializes multi-type input data to app-level objects."""

    def __init__(self, val_types: List[fields.Field]):
        self.valid_types = val_types
        super().__init__()

    def _serialize(self, value: Any, attr: str, obj: Any, **kwargs):
        for field in self.valid_types:
            if field.schema.__model__ == type(value):
                return field.serialize(attr, obj, **kwargs)
        raise ValidationError(f"There are no valid schemas to serialize {obj=}")

    def _deserialize(
        self, value: Any, attr: str = None, data: Mapping[str, Any] = None, **kwargs
    ):
        errors = []
        for field in self.valid_types:
            try:
                return field.deserialize(value, attr, data, **kwargs)
            except ValidationError as error:
                errors.append(error.messages)
                raise ValidationError(errors)


class OperationMetaInfoSchema(SchemaLoader):
    """Operation meta info"""
    __model__ = OperationMetaInfo

    supported_strategies = UnionField([
        fields.Dict(fields.Str(), fields.Raw()),
        fields.Nested('SkLearnEvaluationStrategySchema')
    ])
    allowed_positions = fields.List(fields.Str())
    id = fields.Str()
    input_types = fields.Function(
        lambda op: [enum.value for enum in op.input_types],
        lambda json_arr: [DataTypesEnum(enum_val) for enum_val in json_arr]
    )
    output_types = fields.Function(
        lambda op: [enum.value for enum in op.output_types],
        lambda json_arr: [DataTypesEnum(enum_val) for enum_val in json_arr]
    )
    tags = fields.List(fields.Str())
    task_type = fields.Function(
        lambda op: [enum.value for enum in op.task_type],
        lambda json_arr: [TaskTypesEnum(enum_val) for enum_val in json_arr]
    )


class OperationTypesRepositorySchema(SchemaLoader):
    """Operations type repository"""
    __model__ = OperationTypesRepository

    operations = fields.Nested(OperationMetaInfoSchema, many=True)
    repository_name = fields.Str()
    _repo = fields.Nested(OperationMetaInfoSchema, many=True)
    _tags_excluded_by_default = fields.List(fields.Str())


class EvaluationStrategySchema(SchemaLoader):
    """Evaluation strategy"""

    implementation_info = fields.Str()


class SkLearnEvaluationStrategySchema(EvaluationStrategySchema):
    """SkLearn evaluation strategy"""
    __model__ = SkLearnEvaluationStrategy

    log = fields.Raw()
    operation_id = fields.Str()
    operation_type = fields.Str()
    output_mode = fields.Str()
    params_for_fit = fields.Raw()  # TODO: what type?


class ModelSchema(SchemaLoader):
    """Model"""
    __model__ = Model

    acceptable_task_types = fields.Function(
        lambda model: [enum.value for enum in model.acceptable_task_types],  # TODO: make fix in FEDOTs enums
        lambda json_arr: [TaskTypesEnum(enum_val) for enum_val in json_arr]
    )
    description = fields.Str()
    log = fields.Raw()
    metadata = fields.Nested(OperationMetaInfoSchema)
    operation_type = fields.Str()
    operations_repo = fields.Nested(OperationTypesRepositorySchema)
    params = fields.Str()
    _eval_strategy = fields.Nested(SkLearnEvaluationStrategySchema)


class NodeOperatorSchema(SchemaLoader):
    """Node operator"""
    __model__ = NodeOperator

    _node = UnionField([
        fields.Nested('PrimaryNodeSchema', exclude=('_operator',)),
        fields.Nested('SecondaryNodeSchema', exclude=('_operator',))
    ])


class NodeSchema(SchemaLoader):
    """Node"""
    __model__ = Node

    content = fields.Nested(ModelSchema)
    # custom_params = fields.Str() TODO: problematic field
    # descriptive_id = fields.Str() TODO: problematic field
    distance_to_primary_level = fields.Int()
    fitted_operation = fields.Raw(allow_none=True)  # TODO: what type?
    log = fields.Raw()
    nodes_from = fields.List(
        UnionField([
            fields.Nested('PrimaryNodeSchema', exclude=("nodes_from",)),
            fields.Nested('SecondaryNodeSchema', exclude=("nodes_from",))
        ])
    )  # TODO: maybe it's great to exclude that from children
    _operator = fields.Nested(NodeOperatorSchema)
    # operation = fields.Str() TODO: problematic field
    rating = fields.Raw(allow_none=True)  # TODO: what type?


class PrimaryNodeSchema(NodeSchema):
    """Primary node"""
    __model__ = PrimaryNode

    direct_set = fields.Bool(required=True)
    node_data = fields.Dict(fields.Str(), fields.Raw(), required=True)


class SecondaryNodeSchema(NodeSchema):
    """Secondary node"""
    __model__ = SecondaryNode


class OperationTemplateSchema(SchemaLoader):
    """Operation template"""
    __model__ = OperationTemplate

    custom_params = fields.Str()
    fitted_operation = fields.Raw(allow_none=True)  # TODO: what type?
    fitted_operation_path = fields.Str(allow_none=True)
    log = fields.Raw()
    nodes_from = fields.List(fields.Int())
    operation_id = fields.Int()
    operation_name = fields.Str(allow_none=True)
    operation_type = fields.Str()
    params = fields.Dict(fields.Str(), fields.Raw())
    rating = fields.Raw(allow_nan=True)  # TODO: what type?


class GraphSchema(SchemaLoader):
    """Graph"""
    __model__ = Graph

    uid = fields.UUID()
    nodes = fields.List(UnionField([fields.Nested(PrimaryNodeSchema), fields.Nested(SecondaryNodeSchema)]))
    operator = fields.Nested('GraphOperatorSchema', exclude=('_graph.operator',))


class OptGraphSchema(GraphSchema):
    """Opt graph"""
    __model__ = OptGraph

    log = fields.Raw()


class PipelineSchema(GraphSchema):
    """Pipeline"""
    __model__ = Pipeline

    computation_time = fields.Float(allow_nan=True)
    depth = fields.Int()
    fitted_on_data = fields.Dict(fields.Str(), fields.Raw())
    is_fitted = fields.Bool()
    length = fields.Int()
    log = fields.Raw()
    root_node = fields.Nested(SecondaryNodeSchema)
    template = fields.Nested('PipelineTemplateSchema', allow_none=True)  # TODO: probably not that schema


class GraphOperatorSchema(SchemaLoader):
    """Graph operator"""
    __model__ = GraphOperator

    _graph = fields.Nested(PipelineSchema)


class PipelineTemplateSchema(SchemaLoader):
    """Pipeline template"""
    __model__ = PipelineTemplate

    computation_time = fields.Float(allow_nan=True)
    depth = fields.Int()
    link_to_empty_pipeline = fields.Nested(PipelineSchema)
    log = fields.Raw()
    operation_templates = fields.Nested(OperationTemplateSchema, many=True)
    struct_id = fields.Str()
    total_pipeline_operations = fields.Mapping(keys=fields.Str(), values=fields.Int())
    unique_pipeline_id = fields.UUID()  # TODO: str(uuid4()) if not pipeline.uid else pipeline.uid


class ParentOperatorSchema(SchemaLoader):
    """Parent operator"""
    __mode__ = ParentOperator

    operator_name = fields.Str()
    operator_type = fields.Str()
    parent_objects = fields.Nested(PipelineTemplateSchema, many=True)
    uid = fields.UUID()


class IndividualSchema(SchemaLoader):
    """Individual"""
    __model__ = Individual

    parent_operators = fields.Nested(ParentOperatorSchema, many=True)
    fitness = fields.Float()
    graph = fields.Nested(PipelineTemplateSchema)


class OptHistorySchema(SchemaLoader):
    """OptHistory"""
    __model__ = OptHistory

    metrics = fields.Raw()  # TODO: store function call?!
    individuals = fields.List(fields.Nested(IndividualSchema, many=True))
    archive_history = fields.List(fields.Nested(IndividualSchema, many=True))
    pipelines_comp_time_history = fields.List(fields.Raw())
    archive_comp_time_history = fields.List(fields.Raw())
    parent_operators = fields.List(fields.List(fields.Nested(ParentOperatorSchema, many=True)))
    # self.save_folder: str = save_folder if save_folder \
    #    else f'composing_history_{datetime.datetime.now().timestamp()}'
