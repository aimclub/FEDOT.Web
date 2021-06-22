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
    metric_name = fields.String(attribute='metric_name')
    metric_value = fields.String(attribute='metric_value')
    nmodels = fields.String(attribute='nmodels')
    nlevels = fields.String(attribute='nlevels')
    nfeatures = fields.String(attribute='nfeatures')
    n_rows = fields.String(attribute='n_rows')
