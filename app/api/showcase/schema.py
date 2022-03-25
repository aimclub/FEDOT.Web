from marshmallow import Schema, fields


class ShowcaseItemSchema(Schema):
    """Showcase item schema"""

    case_id = fields.String(attribute='case_id')
    title = fields.String(attribute='title')
    description = fields.String(attribute='description')
    individual_id = fields.String(attribute='individual_id')
    icon_path = fields.String(attribute='icon_path')
    details = fields.Dict(attribute='details')


class ShowcaseItemAddingSchema(Schema):
    """Showcase items adding schema"""

    case = fields.Dict(attribute='case')
    history = fields.Dict(attribute='history')
