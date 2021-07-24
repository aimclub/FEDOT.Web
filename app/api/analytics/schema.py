from marshmallow import Schema, fields


class PlotDataSchema(Schema):
    """PlotData data schema"""

    series = fields.List(attribute='series', cls_or_instance=fields.Dict)
    options = fields.Dict(attribute='options')


class BoxPlotDataSchema(Schema):
    """PlotData data schema"""

    series = fields.List(attribute='series', cls_or_instance=fields.Dict)
