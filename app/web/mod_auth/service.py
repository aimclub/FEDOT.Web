import json

from app import db
from app.api.auth.service import find_user_by_email
from app.web.mod_auth.model import User


def create_user(user_data):
    user = User()
    user.email = user_data['email']
    return user


def get_user(user_data):
    email = user_data['email']
    user = find_user_by_email(email)
    if user is None:
        user = create_user(user_data)
    return user


def set_user_data(user, user_data, token):
    user.name = user_data['name']
    print(token)
    user.tokens = json.dumps(token)
    user.avatar = user_data['picture']


def save_changes(data):
    db.session.add(data)
    db.session.commit()
