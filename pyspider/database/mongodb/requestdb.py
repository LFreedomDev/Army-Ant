#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: https://github.com/LFreedomDev
# Created on 2018-06-10

import json
import time
import logging

from pymongo import MongoClient

from pyspider.database.base.requestdb import RequestDB as BaseRequestDB
from .mongodbbase import SplitTableMixin

logger = logging.getLogger('requestdb')

class RequestDB(SplitTableMixin, BaseRequestDB):
    collection_prefix = ''

    def __init__(self, url, database='requestdb'):
        self.conn = MongoClient(url)
        self.conn.admin.command("ismaster")
        self.database = self.conn[database]
        self.projects = set()
        self._list_project()
        pass

    def _create_project(self, project):
        collection_name = self._collection_name(project)
        self.database[collection_name].ensure_index('taskid')
        self._list_project()
    
    def _parse(self, data):
        data['_id'] = str(data['_id'])
        data['result'] = data['result']
        return data

    def _save(self, task, result):
        project = task.get('project') +'_'+self._get_fetch_type(task)
        taskid = task.get('taskid')

        if project not in self.projects:
            self._create_project(project)

        collection_name = self._get_custom_collection_name(task)
        
        cache_res = {
            "taskid":task.get('taskid'),
            "update_project":task.get('project'),
            "url":task.get('url'),
            "result":result,
            "itag":self._get_requestdb_itag(task),
            "update_time": time.time(),
        }

        if self._check(task,cache_res.get('result',{})) == False:
            return 'disallow save'
       
        return self.database[collection_name].update(
            {'taskid': taskid}, {"$set": cache_res }, upsert=True
        )

    def _get(self,task ,fields=None):

        taskid = task.get('taskid')
        itag = self._get_requestdb_itag(task)
        project = task.get('project') +'_'+self._get_fetch_type(task)
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._get_custom_collection_name(task)
        ret = self.database[collection_name].find_one({'taskid': taskid}, fields)
        res = ret
        if not ret:
            res = ret
        else:
            res = self._parse(ret)

        if res!=None:
            if self._check(task,res.get('result',{})) == False:
                return None

        return res

    def _get_custom_collection_name(self,task):
        project = task.get('project')
        default_name = self._collection_name(project)
        result_name = task.get('fetch',{}).get('requestdb',{}).get('table',default_name) +'_'+self._get_fetch_type(task)
        return result_name

    def _get_fetch_type(self,task):
        url = task.get('url', 'data:,')
        type = ''
        if url.startswith('data:'):
            type = 'data'
        elif task.get('fetch', {}).get('fetch_type') in ('js', 'phantomjs'):
            type = 'phantomjs'
        elif task.get('fetch', {}).get('fetch_type') in ('splash', ):
            type = 'splash'
        else:
            type = 'http'
        return type

    def _check(self,task,result):
        for dis_key in self._get_disallow(task):
            if result.has_key(dis_key):
                for keyword in self._get_disallow(task)[dis_key]:
                    if type(result[dis_key]) == type(u''):
                        if result[dis_key].find(keyword)>-1:
                            return False
                    if type(result[dis_key]) == type(''):
                        if result[dis_key].find(keyword.encode(encoding="UTF-8"))>-1:
                            return False
                    if type(result[dis_key]) == type(1):
                        if result[dis_key]==keyword:
                            return False
                    if type(result[dis_key]) == type({}):
                        if json.dumps(result[dis_key]).find(keyword)>-1:
                            return False
        return True

    def _get_disallow(self,task):
        return task.get('fetch',{}).get('requestdb',{}).get('disallow',{})
        
    def _get_allow(self,task):
        return task.get('fetch',{}).get('requestdb',{}).get('allow',{})

    def _get_requestdb_itag(self,task):
        return str(task.get('fetch',{}).get('requestdb',{}).get('itag',''))

    def _get_requestdb_force(self,task):
        return str(task.get('fetch',{}).get('requestdb',{}).get('force',False))

    def _get_requestdb_save(self,task):
        return str(task.get('fetch',{}).get('requestdb',{}).get('save',None))

    def get_table_name(self,task):
        return self._get_custom_collection_name(task)

    def get(self,task,fields=None):
        url = task.get('url', 'data:,')
        if url.startswith('data:'):
            return
        task_itag = self._get_requestdb_itag(task)
        table_name = self.get_table_name(task)
        cache_res = self._get(task,fields)
        if cache_res!=None:
            cache_itag = str(cache_res.get('itag',''))
            if task_itag == cache_itag:   
                logger.info("cache_fetch %s itag_c_n:[%s:%s] %s => %s",table_name,cache_itag,task_itag,cache_res['result']['status_code'],url)
                return cache_res
            else:
                logger.info("cache_expired %s itag_c_n:[%s:%s] %s => %s",table_name,cache_itag,task_itag,cache_res['result']['status_code'],url)
        if self._get_requestdb_force(task):
            cache_res = {
                "taskid":task.get('taskid'),
                "update_project":task.get('project'),
                "url":task.get('url'),
                "result":{},
                "itag":self._get_requestdb_itag(task),
                "update_time": time.time(),
            }

            result = {}
            result['orig_url'] = url
            result['content'] = None
            result['headers'] = None
            result['status_code'] = 404
            result['url'] = url
            result['time'] = None
            result['cookies'] = None
            result['save'] = self._get_requestdb_save(task)
            result['error'] = "requestdb not found"

            cache_res['result'] = result
            
            return cache_res
        return None

    def save(self,task,result):
        url = task.get('url', 'data:,')
        if url.startswith('data:'):
            return
        cache_res = self._save(task,result)
        table_name = self.get_table_name(task)
        logger.info("cache_update %s async => %s => %s",table_name,url,cache_res)






