import os

from fedot.core.repository.operation_types_repository import OperationTypesRepository
from flask import Flask, jsonify, Blueprint
from flask_cors import CORS, cross_origin
from flask_login import LoginManager
from flask_pymongo import PyMongo
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

from app.api.data.service import load_datasets_from_file_system

db = SQLAlchemy()

storage = PyMongo()

login_manager = LoginManager()


def create_app(env=None):
    OperationTypesRepository()
    print('Create app')
    from app.config import config_by_name

    template_dir = os.path.abspath('frontend/build')
    static_dir = os.path.abspath('frontend/build/static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.config['CORS_HEADERS'] = 'Content-Type'

    app.config.from_object(config_by_name[env or "dev"])

    api_blueprint = Blueprint("api", __name__, url_prefix="/api")
    api = Api(api_blueprint, title="Fedot Web API", version="0.1.0")

    db.init_app(app)

    storage.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @app.route("/health")
    @cross_origin()
    def health():
        return jsonify("healthy")

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.before_first_request
    def create_default_user():
        from app.api.auth.service import find_user_by_email, create_user

        login = 'guest'
        password = 'guest'
        user = find_user_by_email(login)
        if not user:
            create_user(login, password=password)

    from app.web.auth.controller import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.web.mod_base.controller import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.api.routes import register_routes
    register_routes(api, app)
    app.register_blueprint(api_blueprint)

    load_datasets_from_file_system()

    return app
