from marshmallow import Schema, fields


class ShowcaseItemSchema(Schema):
    """Showcase item schema"""

    case_id = fields.String(attribute='case_id')
    title = fields.String(attribute='title')
    description = fields.String(attribute='description')
    chain_id = fields.String(attribute='chain_id')
    icon_path = fields.String(attribute='icon_path')


class ShowcaseFullItemSchema(Schema):
    """Showcase item schema"""

    case_id = fields.String(attribute='case_id')
    title = fields.String(attribute='title')
    description = fields.String(attribute='description')
    chain_id = fields.String(attribute='chain_id')
    icon_path = fields.String(attribute='icon_path')
    details = fields.Dict(attribute='details')
