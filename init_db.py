import os

import pymongo

from init.init_cases import create_default_cases
from init.init_chains import create_default_chains

if __name__ == "__main__":
    client = pymongo.MongoClient(os.getenv('MONGO_CONN_STRING'))
    db = client.get_default_database()
    create_default_cases(db)
    create_default_chains(db)
