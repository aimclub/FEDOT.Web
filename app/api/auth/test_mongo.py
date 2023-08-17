
import os
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