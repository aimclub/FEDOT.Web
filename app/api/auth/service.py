import datetime

import jwt
from flask import current_app
from werkzeug.security import generate_password_hash

from app.web.mod_auth.model import User


def find_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    return user


def dummy_user(email, password):
    new_user = User(email=email, name="name", password=generate_password_hash(password, method='sha256'))
    return new_user


def generate_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=5),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(
        payload,
        current_app.config.get('SECRET_KEY'),
        algorithm='HS256'
    )