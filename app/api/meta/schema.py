from marshmallow import Schema, fields


class TaskInfoSchema(Schema):
    """Task metainfo schema"""

    task_name = fields.String(attribute='task_name')
    display_name = fields.String(attribute='display_name')


class ModelInfoSchema(Schema):
    """Model metainfo schema"""

    model_name = fields.String(attribute='model_name')
    display_name = fields.String(attribute='display_name')
    type = fields.String(attribute='type')


class MetricInfoSchema(Schema):
    """Metric metainfo schema"""

    metric_name = fields.String(attribute='metric_name')
    display_name = fields.String(attribute='display_name')
