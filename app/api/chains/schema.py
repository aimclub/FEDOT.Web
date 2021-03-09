from marshmallow import Schema, fields


class ChainGraphSchema(Schema):
    """Chain schema"""

    uid = fields.String(attribute='uid')
    nodes = fields.Dict(attribute='nodes')
    edges = fields.Dict(attribute='edges')


class ChainValidationResultSchema(Schema):
    """Chain validation results schema"""

    is_valid = fields.Boolean(attribute='is_valid')
    error_desc = fields.String(attribute='error_desc')


class ChainResponseSchema(Schema):
    """Chain schema"""

    uid = fields.String(attribute='uid')
    is_new = fields.Bool(attribute='is_new')
