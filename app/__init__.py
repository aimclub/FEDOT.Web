import os

from flask import Flask, jsonify, Blueprint
from flask_cors import CORS, cross_origin
from flask_login import LoginManager
from flask_restx import Api
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import PyMongo

db = SQLAlchemy()

storage = PyMongo()

socketio = SocketIO()

login_manager = LoginManager()


def create_app(env=None):
    from app.config import config_by_name

    template_dir = os.path.abspath('app/web/templates')
    static_dir = os.path.abspath('app/web/static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'

    app.config.from_object(config_by_name[env or "test"])

    api_blueprint = Blueprint("api", __name__, url_prefix="/api")
    api = Api(api_blueprint, title="Fedot Web API", version="0.0.1")

    socketio.init_app(app)

    db.init_app(app)

    storage.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @app.route("/health")
    @cross_origin()
    def health():
        return jsonify("healthy")

    from app.web.auth.controller import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.web.mod_base.controller import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.api.routes import register_routes
    register_routes(api, app)
    app.register_blueprint(api_blueprint)

    return app
