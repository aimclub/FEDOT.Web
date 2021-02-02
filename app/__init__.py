from flask import Flask, jsonify, Blueprint
from flask_login import LoginManager
from flask_restx import Api
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

socketio = SocketIO()

login_manager = LoginManager()


def create_app(env=None):
    from app.config import config_by_name

    app = Flask(__name__)
    app.config.from_object(config_by_name[env or "test"])

    api_blueprint = Blueprint("api", __name__, url_prefix="/api")
    api = Api(api_blueprint, title="Fedot Web API", version="0.0.1")

    socketio.init_app(app)

    db.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @app.route("/health")
    def health():
        return jsonify("healthy")

    from app.mod_auth.model import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    from app.mod_auth.controller import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.mod_base.controller import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.mod_api import register_routes
    register_routes(api, app)
    app.register_blueprint(api_blueprint)

    return app
