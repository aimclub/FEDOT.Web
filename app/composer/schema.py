from marshmallow import Schema, fields


class ComposingHistorySchema(Schema):
    """Composing history schema"""

    history = fields.String(attribute='history')
