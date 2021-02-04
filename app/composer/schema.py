from marshmallow import Schema, fields


class ComposingHistorySchema(Schema):
    """Composing history schema"""

    populations = fields.Dict(attribute='populations')
    dataset_name = fields.String(attribute='dataset_name')
    task_name = fields.String(attribute='task_name')
    is_finished = fields.Boolean(attribute='is_finished')
