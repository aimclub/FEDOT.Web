import datetime
import json

import jwt
from flask import current_app
from werkzeug.security import generate_password_hash

from app import db
from app.web.auth.model import User


def find_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    return user


def create_user(email, name=None, password=None):
    password_hash = None
    if not password is None:
        password_hash = generate_password_hash(password, method='sha256')
    new_user = User(email=email,
                    name=name,
                    password=password_hash)
    save_changes(new_user)
    return new_user


def get_user(user_data):
    email = user_data['email']
    user = find_user_by_email(email)
    if user is None:
        user = create_user(email)
    return user


def set_user_data(user, user_data, token):
    user.name = user_data['name']
    user.tokens = json.dumps(token)
    user.avatar = user_data['picture']
    save_changes(user)


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


def save_changes(data):
    db.session.add(data)
    db.session.commit()
