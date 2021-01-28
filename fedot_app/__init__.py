from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

# init SQLAlchemy so we can use it later in our models
from fedot_app.config import config

db = SQLAlchemy()

socketio = SocketIO()

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    app.config.from_object(config['dev'])

    db.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .server import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api import api
    app.register_blueprint(api)

    socketio.init_app(app)

    return app
