from marshmallow import Schema, fields


class PlotDataSchema(Schema):
    """PlotData data schema"""

    x = fields.List(attribute='x', cls_or_instance=fields.Int)
    y = fields.List(attribute='y', cls_or_instance=fields.Float)
    meta = fields.Dict(attribute='meta')
