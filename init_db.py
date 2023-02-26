import os

import pymongo
from dotenv import load_dotenv

from app import load_datasets_from_file_system
from app.singletons.db_service import DBServiceSingleton
from init.init_cases import create_default_cases
from init.init_history import create_default_history
from init.init_pipelines import create_default_pipelines

if __name__ == "__main__":
    load_dotenv("mongo_conn_string.env")
    env = os.getenv('MONGO_CONN_STRING')
    print(env)
    client = pymongo.MongoClient(env)
    db = client.get_default_database()
    load_datasets_from_file_system()
    DBServiceSingleton(db)
    create_default_cases()
    create_default_pipelines()
    create_default_history([5, 3, 3])
