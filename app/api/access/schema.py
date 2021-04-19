from marshmallow import Schema, fields


class ChainEpochMappingSchema(Schema):
    """Chain-epoch mapping schema"""

    epoch_num = fields.Int(attribute='epoch_num')
    chain_id = fields.String(attribute='chain_id')


class SandboxDefaultParamsSchema(Schema):
    """Showcase param set schema"""

    task_id = fields.String(attribute='task_id')
    dataset_name = fields.String(attribute='dataset_name')
    metric_id = fields.String(attribute='metric_id')
