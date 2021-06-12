import pymongo
import json
import os

from utils import project_root

if __name__ == "__main__":
    with open(os.path.join(project_root(), "data/mocked_jsons/chain.json"), 'r') as f:
        dict_chain = json.load(f)

    dict_fitted_operations = {}
    for op in dict_chain['nodes']:
        with open(os.path.join(project_root(), 'data/mocked_jsons/', op['fitted_operation_path']), 'rb') as f:
            op_pickle = f.read()
            dict_fitted_operations[op['fitted_operation_path']] = op_pickle
    dict_chain['uid'] = 'test'
    dict_fitted_operations['uid'] = 'test'

    database_name = 'test_db'
    client = pymongo.MongoClient(os.getenv('MONGO_CONN_STRING'))
    db = client[database_name]
    db.chains.create_index([('uid', pymongo.TEXT)], unique=True)
    db.chains.insert_one(dict_chain)  # deprecated, but it allows point in name
    db.dict_fitted_operations.insert(dict_fitted_operations, check_keys=False)
    print(db.chains.find_one())
    print(db.dict_fitted_operations.find_one())
