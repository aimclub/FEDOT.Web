from marshmallow import Schema, fields


class PipelineEpochMappingSchema(Schema):
    """Pipeline-epoch mapping schema"""

    epoch_num = fields.Int(attribute='epoch_num')
    individual_id = fields.String(attribute='individual_id')


class SandboxDefaultParamsSchema(Schema):
    """Showcase param set schema"""

    task_id = fields.String(attribute='task_id')
    dataset_name = fields.String(attribute='dataset_name')
    metric_id = fields.String(attribute='metric_id')
