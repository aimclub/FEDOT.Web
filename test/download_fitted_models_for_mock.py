import os

import gridfs
import pymongo
from bson import json_util
from dotenv import load_dotenv

from utils import project_root

if __name__ == '__main__':
    load_dotenv("mongo_conn_string.env")
    database_name = 'test_db'

    client = pymongo.MongoClient(os.getenv('MONGO_CONN_STRING'))
    db = client[database_name]
    fs = gridfs.GridFS(db)

    pipelines = db.pipelines.find()
    with open(os.path.join(project_root(), 'test/fixtures/pipelines.json'), 'w') as f:
        f.write(json_util.dumps(pipelines))
        print('pipelines are mocked')

    dicts_fitted_operations = fs.find({'type': 'dict_fitted_operations'})
    with open(os.path.join(project_root(), 'test/fixtures/dict_fitted_operations.json'), 'w') as f:
        f.write(json_util.dumps(dicts_fitted_operations))
        print('fitted operations are mocked')

    histories = fs.find({'type': 'history'})
    with open(os.path.join(project_root(), 'test/fixtures/history.json'), 'w') as f:
        f.write(json_util.dumps(histories))
        print('histories are mocked')
