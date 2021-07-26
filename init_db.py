import os

import pymongo

from init.init_history import create_default_history

if __name__ == "__main__":
    env = os.getenv('MONGO_CONN_STRING')
    print(env)
    client = pymongo.MongoClient(env)
    db = client.get_default_database()
    # create_default_cases(db)
    # create_default_chains(db)
    create_default_history(db)
