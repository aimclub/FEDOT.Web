from marshmallow import Schema, fields


class DatasetSchema(Schema):
    """Dataset info schema"""

    dataset_name = fields.String(attribute='dataset_name')
