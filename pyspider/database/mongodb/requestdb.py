#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: https://github.com/LFreedomDev
# Created on 2018-06-10

import json
import time

from pymongo import MongoClient

from pyspider.database.base.requestdb import RequestDB as BaseRequestDB
from .mongodbbase import SplitTableMixin

import logging
logger = logging.getLogger('requestdb')

'''
配置
     'requestdb':{
           'table':string,      #存储表头
           'get':bool,          #启用获取缓存，缓存为空就重新爬取
           'force_get':bool,    #强制获取缓存，缓存为空不重新爬取
           'save':bool,         #是否保存到缓存
           'itag':int,          #缓存版本
           'disallow':{         #禁用缓存规则，response 各项字段
                'status_code':[503,502,501,500]        
           }
           'allow':{            #允许缓存规则，response 各项字段
                'status_code':[200]        
           }
       },   
'''
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
        collection_name = self._get_requestdb_cfg_tablename(task)
        cache_res = {
            "taskid":task.get('taskid'),
            "update_project":task.get('project'),
            "url":task.get('url'),
            "result":result,
            "itag":self._get_requestdb_cfg_itag(task),
            "update_time": time.time(),
        }
        if self._check_can_save(task,cache_res.get('result',{})) == False:
            return 'disallow save'
       
        return self.database[collection_name].update(
            {'taskid': taskid}, {"$set": cache_res }, upsert=True
        )

    def _get(self,task ,fields=None):

        taskid = task.get('taskid')
        itag = self._get_requestdb_cfg_itag(task)

        collection_name = self._get_requestdb_cfg_tablename(task)

        ret = self.database[collection_name].find_one({'taskid': taskid}, fields)
        res = ret
        if not ret:
            res = ret
        else:
            res = self._parse(ret)

        if res!=None:
            if self._check_can_save(task,res.get('result',{})) == False:
                return None

        return res

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

    def _check_can_save(self,task,result):
        for dis_key in self._get_requestdb_cfg_disallow(task):
            if dis_key in result:
                for keyword in self._get_requestdb_cfg_disallow(task)[dis_key]:
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
        res = True
        for allow_key in self._get_requestdb_cfg_allow(task):
            if res:
                if allow_key in result: 
                    res = result[allow_key] in self._get_requestdb_cfg_allow(task)[allow_key]
                else:
                    res = False

        return res


    def _get_requestdb_cfg_tablename(self,task):
        project = task.get('project')
        default_name = self._collection_name(project)
        result_name = task.get('fetch',{}).get('requestdb',{}).get('table',default_name) +'_'+self._get_fetch_type(task)
        if project not in self.projects:
            self._create_project(result_name)
        return result_name

    def _get_requestdb_cfg_itag(self,task):
        return str(task.get('fetch',{}).get('requestdb',{}).get('itag',''))
    def _get_requestdb_cfg_allow(self,task):
        return task.get('fetch',{}).get('requestdb',{}).get('allow',{})        
    def _get_requestdb_cfg_disallow(self,task):
        return task.get('fetch',{}).get('requestdb',{}).get('disallow',{})
    def _get_requestdb_cfg_force_get(self,task):
        return task.get('fetch',{}).get('requestdb',{}).get('force_get',False)
    def _get_requestdb_cfg_enable_get(self,task):
        return task.get('fetch',{}).get('requestdb',{}).get('get',False)
    def _get_requestdb_cfg_enable_save(self,task):
        return task.get('fetch',{}).get('requestdb',{}).get('save',True)  


    def get(self,task,fields=None):
        start_time = time.time()
        url = task.get('url', 'data:,')

        enable_get = self._get_requestdb_cfg_enable_get(task)
        force_get = self._get_requestdb_cfg_force_get(task)

        if url.startswith('data:') or enable_get ==False:
            return None


        task_itag = self._get_requestdb_cfg_itag(task)
        table_name = self._get_requestdb_cfg_tablename(task)
        cache_res = self._get(task,fields)

        if cache_res!=None:
            cache_itag = str(cache_res.get('itag',''))
            if task_itag == cache_itag:   
                logger.info("cache_fetch %s itag_c_n:[%s:%s] %s => %s",table_name,cache_itag,task_itag,cache_res['result']['status_code'],url)
                cache_res['result']['time'] = time.time() - start_time
                return cache_res
            else:
                if force_get == True:
                    logger.warn("cache_expired %s itag_c_n:[%s:%s] %s => %s",table_name,cache_itag,task_itag,cache_res['result']['status_code'],url)
                    return cache_res
                else:
                    logger.info("cache_expired %s itag_c_n:[%s:%s] %s => %s",table_name,cache_itag,task_itag,cache_res['result']['status_code'],url)

        
        if cache_res==None and force_get==True:
            cache_res = {
                "taskid":task.get('taskid'),
                "update_project":task.get('project'),
                "url":task.get('url'),
                "result":{},
                "itag":self._get_requestdb_cfg_itag(task),
                "update_time": time.time(),
            }
            result = {}
            result['orig_url'] = url
            result['content'] = None
            result['headers'] = None
            result['status_code'] = 404
            result['url'] = url
            result['time'] = time.time() - start_time
            result['cookies'] = None
            result['save'] = None
            result['error'] = "not found by requestdb"

            cache_res['result'] = result
            
            return cache_res
        return None

    def save(self,task,result):
        enable_save = self._get_requestdb_cfg_enable_save(task)

        url = task.get('url', 'data:,')
        if url.startswith('data:') or enable_save == False:
            return
        cache_res = self._save(task,result)
        table_name = self._get_requestdb_cfg_tablename(task)
        logger.info("cache_update %s async => %s => %s",table_name,url,cache_res)




