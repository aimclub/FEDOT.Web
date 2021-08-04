import os

import pymongo

from init.init_cases import create_default_cases
from init.init_history import create_default_history
from init.init_pipelines import create_default_pipelines

if __name__ == "__main__":
    env = os.getenv('MONGO_CONN_STRING')
    print(env)
    client = pymongo.MongoClient(env)
    db = client.get_default_database()
    create_default_cases(db)
    create_default_pipelines(db)
    create_default_history(db)
