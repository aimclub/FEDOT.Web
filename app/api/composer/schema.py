from marshmallow import Schema, fields


class ComposingHistoryGraphSchema(Schema):
    """Composing history graph"""

    uid = fields.String(attribute='uid')
    nodes = fields.Dict(attribute='nodes')
    edges = fields.Dict(attribute='edges')
    dataset_name = fields.String(attribute='dataset_name')
    task_name = fields.String(attribute='task_name')
    is_finished = fields.Boolean(attribute='is_finished')
