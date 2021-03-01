from flask import request
from flask_accepts import responds, accepts
from flask_restx import Namespace, Resource
from werkzeug.exceptions import Unauthorized, BadRequest
from werkzeug.security import check_password_hash

from .models import Token
from .schema import TokenSchema, UserSchema
from .service import find_user_by_email, generate_token, create_user

api = Namespace("Auth", description="Getting a token")


@api.route("/get_token")
class AuthTokenResource(Resource):
    """Auth"""

    @accepts(schema=UserSchema, api=api)
    @responds(schema=TokenSchema)
    @api.doc(responses={401: 'check login data'})
    def post(self) -> Token:
        """Get token by user login data"""
        obtained = request.parsed_obj
        email = obtained['email']
        password = obtained['password']
        user = find_user_by_email(email)
        if not user or not check_password_hash(user.password, password):
            raise Unauthorized("check login data")
        token = generate_token(user.id)
        print(token)

        return Token(token_value=token)


@api.route("/signup")
class RegisterResource(Resource):
    """Registration"""

    @accepts(schema=UserSchema, api=api)
    @api.doc(responses={200: 'registration successful'})
    @api.doc(responses={400: 'user already exists'})
    def post(self) -> Token:
        """User registration"""
        obtained = request.parsed_obj
        email = obtained['email']
        password = obtained['password']
        user = find_user_by_email(email)
        if not user:
            create_user(email, password=password)
        else:
            raise BadRequest("user already exists")

        return {"message": "registration successful"}
