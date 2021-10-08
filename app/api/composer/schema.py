from marshmallow import Schema, fields


class ComposingHistoryGraphSchema(Schema):
    """Composing history graph"""

    uid = fields.String(attribute='uid')
    nodes = fields.Dict(attribute='nodes')
    edges = fields.Dict(attribute='edges')
    dataset_name = fields.String(attribute='dataset_name')
    task_name = fields.String(attribute='task_name')
    is_finished = fields.Boolean(attribute='is_finished')


class OperationTemplateSchema(Schema):
    """Operation template"""

    pass


class PipelineSchema(Schema):
    """Pipeline"""

    pass


class PipelineTemplateSchema(Schema):
    """Pipeline template"""

    computation_time = fields.Float()
    depth = fields.Int()
    link_to_empty_pipeline = fields.Nested(PipelineSchema)
    log = fields.Raw()
    operation_templates = fields.Nested(OperationTemplateSchema, many=True)
    struct_id = fields.Str()
    total_pipeline_operations = fields.Dict(keys=fields.Str(), values=fields.Int())
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
    fitness = fields.Float()
    graph = fields.Nested(PipelineTemplateSchema)


class OptHistorySchema(Schema):
    """OptHistory"""

    metrics = fields.Method('get_metrics')

    def get_metrics(self, obj):
        return str(obj.metrics)
    individuals = fields.List(fields.Nested(IndividualSchema, many=True))
    archive_history = fields.List(fields.Nested(IndividualSchema, many=True))
    pipelines_comp_time_history = fields.List(fields.Raw())
    archive_comp_time_history = fields.List(fields.Raw())
    parent_operators = fields.List(fields.List(fields.Nested(ParentOperatorSchema, many=True)))
    # self.save_folder: str = save_folder if save_folder \
    #    else f'composing_history_{datetime.datetime.now().timestamp()}'
