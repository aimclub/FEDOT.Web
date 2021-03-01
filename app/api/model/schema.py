from marshmallow import fields, Schema


class ModelSchema(Schema):
    """Model schema"""

    modelId = fields.Number(attribute="model_id")
    label = fields.String(attribute="label")
    description = fields.String(attribute="description")
