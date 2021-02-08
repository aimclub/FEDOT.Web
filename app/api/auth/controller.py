from flask_accepts import responds
from flask_restx import Namespace, Resource
from werkzeug.security import check_password_hash

from .models import Token
from .schema import TokenSchema
from .service import find_user_by_email, generate_token, dummy_user

api = Namespace("Auth", description="Getting a token")


@api.route("/get_token&<string:email>&<string:password>")
class DataSetsResource(Resource):
    """Auth"""

    @responds(schema=TokenSchema)
    def get(self, email, password) -> Token:
        """Get token by user login data"""

        user = find_user_by_email(email)
        if not user or not check_password_hash(user.password, password):
            user = dummy_user(email, password)

        token = generate_token(user.id)
        print(token)

        return Token(token_value=token)
