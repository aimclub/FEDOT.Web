from marshmallow import Schema, fields


class TaskSchema(Schema):
    """Task schema"""

    task = fields.String(attribute='task_name')


class ModelNameSchema(Schema):
    """Task schema"""

    model_name = fields.String(attribute='model_name')
