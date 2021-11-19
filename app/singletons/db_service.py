from typing import Any, Dict, Optional

import gridfs
import pymongo
from bson import json_util
from gridfs import GridFS
from gridfs.grid_file import GridOut
from pymongo.cursor import Cursor
from pymongo.database import Database
from pymongo.errors import CollectionInvalid, DuplicateKeyError


def singleton(cls):
    instances = {}

    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return getinstance


@singleton
class DBServiceSingleton:
    def __init__(self, db: Optional[Database] = None):
        self._db: Optional[Database] = db
        self._fs = None
        if db is not None and isinstance(db, Database):
            self._fs: Optional[GridFS] = gridfs.GridFS(self._db)

    def exists(self) -> bool:
        return self._db is not None

    def find_all(self, collection: str) -> Cursor:
        if self.exists():
            return self._db[collection].find()

    def try_find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict]:
        if self.exists():
            return self._db[collection].find_one(query)

    def try_create_collection(self, collection_name: str, id_name: str) -> None:
        if self.exists():
            try:
                self._db.create_collection(collection_name)
                self._db[collection_name].create_index([(id_name, pymongo.TEXT)], unique=True)
            except CollectionInvalid:
                from sys import stderr
                print(f'{collection_name} collection already exists', file=stderr)

    def try_insert_one(self, collection: str, obj_to_add: Dict) -> None:
        if self.exists():
            try:
                self._db[collection].insert_one(obj_to_add)
            except DuplicateKeyError as ex:
                from sys import stderr
                print(f'{collection} item already exists: {ex}', file=stderr)

    def try_reinsert_one(self, collection: str, old_obj_query: Dict[str, Any], obj_to_add: Dict[str, Any]) -> None:
        if self.exists():
            self._db[collection].remove(old_obj_query)
            self._db[collection].insert_one(obj_to_add)

    def try_delete_one(self, collection: str, query: Dict[str, Any]) -> None:
        if self.exists():
            self._db[collection].delete_one(query)

    def try_find_one_file(self, query: Dict[str, Any]) -> Optional[GridOut]:
        if self.exists():
            return self._fs.find_one(query)

    def try_reinsert_file(self, query: Dict[str, Any], obj_to_add: Any) -> None:
        if self.exists():
            file = self._fs.find_one(query)
            if file:
                self._fs.delete(file._id)
            self._fs.put(json_util.dumps(obj_to_add), encoding='utf-8', **query)
