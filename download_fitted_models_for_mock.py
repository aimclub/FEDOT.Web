import os

import pymongo
from bson import json_util

from utils import project_root

if __name__ == "__main__":
    database_name = "test_db"
    client = pymongo.MongoClient(os.getenv("MONGO_CONN_STRING"))
    db = client[database_name]

    chains = db.chains.find()
    with open(os.path.join(project_root(), "test/fixtures/chains.json"), "w") as f:
        f.write(json_util.dumps(chains))
        print("chains are mocked")

    dicts_fitted_operations = db.dict_fitted_operations.find()
    with open(os.path.join(project_root(), "test/fixtures/dict_fitted_operations.json"), "w") as f:
        f.write(json_util.dumps(dicts_fitted_operations))
        print("fitted operations are mocked")
