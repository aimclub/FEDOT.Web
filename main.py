import os
from multiprocessing import set_start_method

from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app, db, storage
from app.singletons.db_service import DBServiceSingleton

from app.api.sandbox.download import download_pipeline
from app.api.auth.check_mongo import check_mongo_connection
import pymongo

if __name__ == "__main__":
    set_start_method("spawn")

    load_dotenv("oauth.env")
    load_dotenv("mongo_conn_string.env")

    env = os.getenv('MONGO_CONN_STRING')
    print(env)

    if check_mongo_connection('test_db'):  # Change 'test_db' to your database name
        print("Connected to MongoDB")
    else:
        print("Failed to connect to MongoDB")

    app = create_app(os.getenv("FLASK_ENV") or "dev")
    app.add_url_rule('/download_pipeline', 'download_pipeline',
                        download_pipeline, methods=['POST'])  # Route registration

    app.wsgi_app = ProxyFix(app.wsgi_app)

    with app.app_context():
        db.create_all()

    DBServiceSingleton(storage.db)
    host = os.getenv("FLASK_HOST")
    port = os.getenv("FLASK_PORT")
    if not host:
        app.run(use_reloader=False)
    else:
        app.run(use_reloader=False, host=host, port=port)
