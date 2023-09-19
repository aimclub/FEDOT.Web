
import os
import pymongo


def check_mongo_connection(db_name):
    conn_string = os.getenv('MONGO_CONN_STRING')
    try:
        client = pymongo.MongoClient(conn_string)
        db_names = client.list_database_names()
        if db_name in db_names:
            return True
        else:
            return False
    except pymongo.errors.ConnectionFailure as e:
        return False
    