import datetime
import json
from typing import Any, Dict, Optional

import jwt
from app import db
from app.web.auth.model import User
from flask import current_app
from werkzeug.security import generate_password_hash


def find_user_by_email(email: str) -> Optional[User]:
    user = User.query.filter_by(email=email).first()
    return user


def create_user(email: str, name: Optional[str] = None, password: Optional[str] = None) -> User:
    password_hash: Optional[str] = None
    if password:
        password_hash = generate_password_hash(password, method='sha256')
    new_user = User(email=email,
                    name=name,
                    password=password_hash)
    save_changes(new_user)
    return new_user


def set_user_data(user: User, user_data: Dict[str, Any], token: Dict[str, Any]) -> None:
    user.name = user_data['name']
    user.tokens = json.dumps(token)
    user.avatar = user_data['picture']
    save_changes(user)


def generate_token(user_id: int) -> str:
    payload: Dict[str, Any] = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=5),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(
        payload,
        current_app.config.get('SECRET_KEY'),
        algorithm='HS256'
    )


def save_changes(data: Optional[Any] = None) -> None:
    if data:
        db.session.add(data)
    db.session.commit()
