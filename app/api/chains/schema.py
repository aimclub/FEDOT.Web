from marshmallow import Schema, fields


class ChainSchema(Schema):
    """Chain schema"""

    uid = fields.String(attribute='uid')
    nodes = fields.Dict(attribute='nodes')


class ChainResponseSchema(Schema):
    """Chain schema"""

    uid = fields.String(attribute='uid')
    is_new = fields.Bool(attribute='is_new')
