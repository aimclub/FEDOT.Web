import os
from multiprocessing import set_start_method

from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app, db, storage
from app.singletons.db_service import DBServiceSingleton
from app.api.pipelines.service import pipeline_by_uid

from flask import request, send_file, current_app, jsonify

import json

import pymongo

def check_mongo_connection():
    conn_string = os.getenv('MONGO_CONN_STRING')
    try:
        client = pymongo.MongoClient(conn_string)
        db_names = client.list_database_names()
        if 'test_db' in db_names:  # Замените 'test_db' на имя вашей базы данных
            return True
        else:
            return False
    except pymongo.errors.ConnectionFailure as e:
        return False

def check_existing_pipelines():
    pipeline_collection = db["pipelines"]
    pipelines = pipeline_collection.find()
    existing_uids = []
    for pipeline in pipelines:
        uid = pipeline["uid"]
        existing_uids.append(uid)
    return existing_uids

def download_pipeline():
    uid = request.json['uid']

    print('Received uid:', uid, 'Type:', type(uid))
    pipeline = pipeline_by_uid(uid) 
    if pipeline is None:
        return "Pipeline not found", 404
    
    # Сохранение пайплайна в формате JSON
    pipeline_json, _ = pipeline.save() 
    pipeline_data = json.loads(pipeline_json)

    return jsonify(pipeline_data)

if __name__ == "__main__":
    set_start_method("spawn")

    load_dotenv("oauth.env")
    load_dotenv("mongo_conn_string.env")

    env = os.getenv('MONGO_CONN_STRING')
    print(env)

    if check_mongo_connection():
        print("Connected to MongoDB")
    else:
        print("Failed to connect to MongoDB")

    app = create_app(os.getenv("FLASK_ENV") or "dev")
    app.add_url_rule('/download_pipeline', 'download_pipeline', download_pipeline, methods=['POST'])  # регистрация маршрута

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