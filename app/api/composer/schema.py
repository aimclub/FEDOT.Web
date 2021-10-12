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


class OperationMetaInfoSchema(Schema):
    """Operation meta info"""
    __model__ = OperationMetaInfo

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    allowed_positions = fields.List(fields.Str())
    id = fields.Str()
    input_types = fields.Function(
        lambda op: [enum.value for enum in op.input_types],
        lambda obj: [DataTypesEnum(enum_val) for enum_val in obj['input_types']]
    )
    output_types = fields.Function(
        lambda op: [enum.value for enum in op.output_types],
        lambda obj: [DataTypesEnum(enum_val) for enum_val in obj['output_types']]
    )
    tags = fields.List(fields.Str())
    task_type = fields.Function(
        lambda op: [enum.value for enum in op.task_type],
        lambda obj: [TaskTypesEnum(enum_val) for enum_val in obj['task_type']]
    )


class OperationTypesRepositorySchema(Schema):
    """Operations type repository"""
    __model__ = OperationTypesRepository

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    operations = fields.Nested(OperationMetaInfoSchema, many=True)
    repository_name = fields.Str()
    _repo = fields.Nested(OperationMetaInfoSchema, many=True)
    _tags_excluded_by_default = fields.List(fields.Str())


class SkLearnEvaluationStrategySchema(Schema):
    """SkLearn evaluation strategy"""
    __model__ = SkLearnEvaluationStrategy

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    implementation_info = fields.Str()
    log = fields.Raw()
    operation_id = fields.Str()
    operation_type = fields.Str()
    output_mode = fields.Str()
    params_for_fit = fields.Raw()  # TODO: what type?


class ModelSchema(Schema):
    """Model"""
    __model__ = Model

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    acceptable_task_types = fields.Function(
        lambda model: [enum.value for enum in model.acceptable_task_types],  # TODO: make fix in FEDOTs enums
        lambda obj: [TaskTypesEnum(enum_val) for enum_val in obj['acceptable_task_types']]
    )
    description = fields.Str()
    log = fields.Raw()
    metadata = fields.Nested(OperationMetaInfoSchema)
    operation_type = fields.Str()
    operations_repo = fields.Nested(OperationTypesRepositorySchema)
    params = fields.Str()
    _eval_strategy = fields.Nested(SkLearnEvaluationStrategySchema)


class UnionField(fields.Field):
    """Field that deserializes multi-type input data to app-level objects."""

    def __init__(self, val_types: List[fields.Field]):
        self.valid_types = val_types
        super().__init__()

    def _serialize(self, value: Any, attr: str, obj: Any, **kwargs):
        errors = []
        for field in self.valid_types:
            try:
                return field.serialize(value, attr, obj, **kwargs)
            except ValidationError as error:
                errors.append(error.messages)
                raise ValidationError(errors)

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


class NodeSchema(Schema):
    """Node"""
    __model__ = Node

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    content = fields.Nested(ModelSchema)
    # custom_params = fields.Str() TODO: problematic field
    # descriptive_id = fields.Str() TODO: problematic field
    distance_to_primary_level = fields.Int()
    fitted_operation = fields.Raw(allow_none=True)  # TODO: what type?
    log = fields.Raw()
    nodes_from = fields.Nested('SecondaryNodeSchema', many=True)  # TODO: maybe it's great to exclude that from children
    # operation = fields.Str() TODO: problematic field
    rating = fields.Raw(allow_none=True)  # TODO: what type?


class PrimaryNodeSchema(NodeSchema):
    """Primary node"""
    __model__ = PrimaryNode

    direct_set = fields.Bool(required=True)
    node_data = fields.Dict(fields.Str(), fields.Raw(), required=True)


class NodeOperatorSchema(Schema):
    """Node operator"""
    __model__ = NodeOperator

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    _node = fields.Nested('SecondaryNodeSchema', exclude=('_operator',))


class SecondaryNodeSchema(NodeSchema):
    """Secondary node"""
    __model__ = SecondaryNode

    _operator = fields.Nested(NodeOperatorSchema)


class OperationTemplateSchema(Schema):
    """Operation template"""
    __model__ = OperationTemplate

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

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


class GraphSchema(Schema):
    """Graph"""
    __model__ = Graph

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    uid = fields.UUID()
    nodes = fields.Raw()  # fields.List(UnionField([fields.Nested(PrimaryNodeSchema), fields.Nested(SecondaryNodeSchema)]))
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


class GraphOperatorSchema(Schema):
    """Graph operator"""
    __model__ = GraphOperator

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    _graph = fields.Nested(PipelineSchema)


class PipelineTemplateSchema(Schema):
    """Pipeline template"""
    __model__ = PipelineTemplate

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    computation_time = fields.Float(allow_nan=True)
    depth = fields.Int()
    link_to_empty_pipeline = fields.Nested(PipelineSchema)
    log = fields.Raw()
    operation_templates = fields.Nested(OperationTemplateSchema, many=True)
    struct_id = fields.Str()
    total_pipeline_operations = fields.Mapping(keys=fields.Str(), values=fields.Int())
    unique_pipeline_id = fields.UUID()  # TODO: str(uuid4()) if not pipeline.uid else pipeline.uid


class ParentOperatorSchema(Schema):
    """Parent operator"""
    __mode__ = ParentOperator

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    operator_name = fields.Str()
    operator_type = fields.Str()
    parent_objects = fields.Nested(PipelineTemplateSchema, many=True)
    uid = fields.UUID()


class IndividualSchema(Schema):
    """Individual"""
    __model__ = Individual

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    parent_operators = fields.Nested(ParentOperatorSchema, many=True)
    fitness = fields.Float()
    graph = fields.Nested(PipelineTemplateSchema)


class OptHistorySchema(Schema):
    """OptHistory"""
    __model__ = OptHistory

    @post_load
    def _deserialize(self, data, **kwargs):
        return type(self).__model__(**data)

    metrics = fields.Raw()  # TODO: store function call?!
    # individuals = fields.List(fields.Nested(IndividualSchema, many=True))
    # archive_history = fields.List(fields.Nested(IndividualSchema, many=True))
    pipelines_comp_time_history = fields.List(fields.Raw())
    archive_comp_time_history = fields.List(fields.Raw())
    parent_operators = fields.List(fields.List(fields.Nested(ParentOperatorSchema, many=True)))
    # self.save_folder: str = save_folder if save_folder \
    #    else f'composing_history_{datetime.datetime.now().timestamp()}'
