
from pymongo import MongoClient

from pyspider.database.base.pretaskdb import PreTaskDB as BasePreTaskDB
from .mongodbbase import SplitTableMixin

import logging
logger = logging.getLogger('pretaskdb')


class PreTaskDB(SplitTableMixin,BasePreTaskDB):
    collection_prefix = ''

    def __init__(self, url, database='pretaskdb'):
        self.conn = MongoClient(url)
        self.conn.admin.command("ismaster")
        self.database = self.conn[database]
        self.projects = set()
        self._list_project()
        pass

    def insert(self,pretask):
        collection_name = self._collection_name(pretask.get('project'))
        self.database[collection_name].insert(pretask)

    def select(self,project):
        collection_name = self._collection_name(project)
        for item in self.database[collection_name].find({ },None):
            yield item

    def delete(self,taskid):
        collection_name = self._collection_name(project)
        self.database[collection_name].remove({'taskid': taskid})