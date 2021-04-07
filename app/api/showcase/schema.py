from marshmallow import Schema, fields


class ShowcaseItemSchema(Schema):
    """Showcase item schema"""

    case_id = fields.String(attribute='case_id')
    description = fields.String(attribute='description')
    chain_id = fields.String(attribute='chain_id')
    icon_path = fields.String(attribute='icon_path')


class ShowcaseSchema(Schema):
    """Showcase content request results schema"""
    items_uids = fields.List(cls_or_instance=fields.String, attribute='items_uids')
