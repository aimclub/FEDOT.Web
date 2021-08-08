from marshmallow import Schema, fields


class ShowcaseItemSchema(Schema):
    """Showcase item schema"""

    case_id = fields.String(attribute='case_id')
    title = fields.String(attribute='title')
    description = fields.String(attribute='description')
    pipeline_id = fields.String(attribute='pipeline_id')
    icon_path = fields.String(attribute='icon_path')
    details = fields.Dict(attribute='details')