from marshmallow import Schema, fields


class TokenSchema(Schema):
    """Token schema"""

    token_value = fields.String(attribute='token_value')


class UserSchema(Schema):
    """User schema"""
    email = fields.String(attribute='email')
    password = fields.String(attribute='password')
