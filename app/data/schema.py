from marshmallow import Schema, fields


class DatasetSchema(Schema):
    """Composing history schema"""

    dataset_name = fields.String(attribute='dataset_name')
