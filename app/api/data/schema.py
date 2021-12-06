from marshmallow import Schema, fields


class DatasetSchema(Schema):
    """Dataset info schema"""

    dataset_name = fields.String(attribute='dataset_name')


class DatasetAddingScheme(Schema):
    """Dataset adding schema"""

    dataset_name = fields.String(attribute='dataset_name')
    data_type = fields.String(attribute='data_type')
    content_train = fields.String(attribute='content_train')
    content_test = fields.String(attribute='content_test')
    content_format = fields.String(attribute='content_format')
