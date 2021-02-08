from marshmallow import Schema, fields


class TokenSchema(Schema):
    """Token schema"""

    token_value = fields.String(attribute='token_value')
