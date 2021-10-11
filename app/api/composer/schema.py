from typing import Any, List, Mapping

from marshmallow import Schema, fields
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

    allowed_positions = fields.List(fields.Str())
    id = fields.Str()

    def get_enum_values(self, enums):
        return [enum.value for enum in enums]
    input_types = fields.Method("get_enum_values")
    output_types = fields.Method("get_enum_values")
    tags = fields.List(fields.Str())
    task_type = fields.Method("get_enum_values")


class OperationTypesRepository(Schema):
    """Operations type repository"""

    operations = fields.Nested(OperationMetaInfoSchema, many=True)
    repository_name = fields.Str()
    _repo = fields.Raw()  # fields.Nested(OperationMetaInfoSchema, many=True)
    _tags_excluded_by_default = fields.List(fields.Str())


class SkLearnEvaluationStrategySchema(Schema):
    """SkLearn evaluation strategy"""

    implementation_info = fields.Str()
    log = fields.Raw()
    operation_id = fields.Str()
    operation_type = fields.Str()
    output_mode = fields.Str()
    params_for_fit = fields.Raw()  # TODO: what type?


class ModelSchema(Schema):
    """Model"""

    acceptable_task_type = fields.Method("get_enum_values")

    def get_enum_values(self, enums):
        return [enum.value for enum in enums]
    description = fields.Str()
    log = fields.Raw()
    metadata = fields.Nested(OperationMetaInfoSchema)
    operation_type = fields.Str()
    operations_repo = fields.Nested(OperationTypesRepository)
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

    content = fields.Raw()  # fields.Nested(ModelSchema)
    custom_params = fields.Str()
    descriptive_id = fields.Str()
    distance_to_primary_level = fields.Int()
    fitted_operation = fields.Raw(allow_none=True)  # TODO: what type?
    log = fields.Raw()
    nodes_from = fields.Raw()  # fields.Nested('SecondaryNodeSchema', many=True, exclude=('nodes_from',))
    operation = fields.Str()
    rating = fields.Raw(allow_none=True)  # TODO: what type?


class PrimaryNodeSchema(NodeSchema):
    """Primary node"""

    direct_set = fields.Bool(required=True)
    node_data = fields.Dict(fields.Str(), fields.Raw(), required=True)


class NodeOperatorSchema(Schema):
    """Node operator"""

    _node = fields.Nested('SecondaryNodeSchema', exclude=('_operator',))


class SecondaryNodeSchema(NodeSchema):
    """Secondary node"""

    _operator = fields.Raw() # fields.Nested(NodeOperatorSchema)


class OperationTemplateSchema(Schema):
    """Operation template"""

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

    uid = fields.UUID()
    nodes = fields.Raw()  # fields.List(UnionField([fields.Nested(PrimaryNodeSchema), fields.Nested(SecondaryNodeSchema)]))
    operator = fields.Nested('GraphOperatorSchema', exclude=('_graph.operator',))


class OptGraph(GraphSchema):
    """Opt graph"""

    log = fields.Raw()


class PipelineSchema(GraphSchema):
    """Pipeline"""

    computation_time = fields.Float(allow_nan=True)
    depth = fields.Int()
    fitted_on_data = fields.Dict(fields.Str(), fields.Raw())
    is_fitted = fields.Bool()
    length = fields.Int()
    log = fields.Raw()
    root_node = fields.Nested(SecondaryNodeSchema)
    template = fields.Raw()  # fields.Nested(PipelineTemplateSchema, allow_none=True)


class GraphOperatorSchema(Schema):
    """Graph operator"""

    _graph = fields.Nested(PipelineSchema)


class PipelineTemplateSchema(Schema):
    """Pipeline template"""

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

    operator_name = fields.Str()
    operator_type = fields.Str()
    parent_objects = fields.Nested(PipelineTemplateSchema, many=True)
    uid = fields.Str()


class IndividualSchema(Schema):
    """Individual"""

    parent_operators = fields.Nested(ParentOperatorSchema, many=True)
    fitness = fields.List(fields.Float())
    graph = fields.Nested(PipelineTemplateSchema)


class OptHistorySchema(Schema):
    """OptHistory"""

    metrics = fields.Raw()
    # individuals = fields.List(fields.Nested(IndividualSchema, many=True))
    # archive_history = fields.List(fields.Nested(IndividualSchema, many=True))
    pipelines_comp_time_history = fields.List(fields.Raw())
    archive_comp_time_history = fields.List(fields.Raw())
    parent_operators = fields.List(fields.List(fields.Nested(ParentOperatorSchema, many=True)))
    # self.save_folder: str = save_folder if save_folder \
    #    else f'composing_history_{datetime.datetime.now().timestamp()}'
