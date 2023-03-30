from marshmallow import Schema, fields


class PipelineGraphSchema(Schema):
    """Pipeline schema"""

    uid = fields.String(attribute='uid')
    nodes = fields.List(cls_or_instance=fields.Dict,
                        attribute='nodes')
    edges = fields.List(cls_or_instance=fields.Dict,
                        attribute='edges')
    is_new = fields.Boolean(attribute='is_new', default=False)


class PipelineValidationResponseSchema(Schema):
    """Pipeline validation results schema"""

    is_valid = fields.Boolean(attribute='is_valid')
    error_desc = fields.String(attribute='error_desc')


class PipelineResponseSchema(Schema):
    """Pipeline schema"""

    uid = fields.String(attribute='uid')
    is_new = fields.Bool(attribute='is_new')


class PipelineImageSchema(Schema):
    """Pipeline schema"""

    uid = fields.String(attribute='uid')
    image_url = fields.String(attribute='image_url')
