import pymongo
from bson import json_util
import os

from app.api.chains.service import replace_symbols_in_dct_keys
from utils import project_root

if __name__ == "__main__":
    database_name = "test_db"
    client = pymongo.MongoClient(os.getenv("MONGO_CONN_STRING"))
    db = client[database_name]
    resp = db.dict_fitted_operations.find_one({"uid": "best_scoring_chain"})
    resp = replace_symbols_in_dct_keys(resp, ".", "-")

    with open(os.path.join(project_root(), "test/fixtures/dict_fitted_operations.json"), "w") as f:
        f.write(json_util.dumps([resp]))
