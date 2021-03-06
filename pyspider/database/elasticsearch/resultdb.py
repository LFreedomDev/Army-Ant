#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2016-01-18 19:41:24


import time

import elasticsearch.helpers
from elasticsearch import Elasticsearch
from pyspider.database.base.resultdb import ResultDB as BaseResultDB

import logging
logger = logging.getLogger('resultdb')

class ResultDB(BaseResultDB):
    __type__ = 'result'

    def __init__(self, hosts, index='pyspider'):
        self.index = index
        self.es = Elasticsearch(hosts=hosts)

        self.es.indices.create(index=self.index,body={
            "settings" : {
                "index" : {
                    "analysis.analyzer.default.type": "ik_max_word"
                }
            }
        }, ignore=400)
        
        logger.info("==========update settings=========")

        # _map = self.es.indices.get_mapping(index=self.index, doc_type=self.__type__, ignore=404)
        # if _map.get(u'status',404) == 404:
        #     _map = self.es.indices.put_mapping(index=self.index, doc_type=self.__type__, body={
        #         #"_all": {"enabled": True},
        #         "properties": {
        #             "taskid": {
        #                 "type": "text", 
        #             },
        #             "project": {
        #                 "type": "text", 
        #             },
        #             "url": {
        #                 "type": "text", 
        #             },
        #         }
        #     })


    @property
    def projects(self):
        ret = self.es.search(index=self.index, doc_type=self.__type__,
                             body={"aggs": {"projects": {
                                 "terms": {"field": "project"}
                             }}}, _source=False)
        return [each['key'] for each in ret['aggregations']['projects'].get('buckets', [])]

    def save(self, project, taskid, url, result, task):
        obj = {
            'taskid': taskid,
            'project': project,
            'url': url,
            'result': result,
            'updatetime': time.time(),
        }
        return self.es.index(index=self.index, doc_type=self.__type__,
                             body=obj, id='%s:%s' % (project, taskid))

    def select(self, project, fields=None, offset=0, limit=0):
        offset = offset or 0
        limit = limit or 0
        if not limit:
            for record in elasticsearch.helpers.scan(self.es, index=self.index, doc_type=self.__type__,
                                                     query={'query': {'term': {'project': project}}},
                                                     _source_include=fields or [], from_=offset,
                                                     sort="updatetime:desc"):
                yield record['_source']
        else:
            for record in self.es.search(index=self.index, doc_type=self.__type__,
                                         body={'query': {'term': {'project': project}}},
                                         #q="project:"+project,
                                         _source_include=fields or [], from_=offset, size=limit,
                                         sort="updatetime:desc"
                                         ).get('hits', {}).get('hits', []):
                yield record['_source']


    def count(self, project):
        return self.es.count(index=self.index, doc_type=self.__type__,
            #body={'query': {'term': {'project': project}}} 
            q="project:"+project
            ).get('count', 0)

    def get(self, project, taskid, fields=None):
        ret = self.es.get(index=self.index, doc_type=self.__type__, id="%s:%s" % (project, taskid),
                          _source_include=fields or [], ignore=404)
        return ret.get('_source', None)

    def drop(self, project):
        self.refresh()
        for record in elasticsearch.helpers.scan(self.es, index=self.index, doc_type=self.__type__,
                                                 query={'query': {'term': {'project': project}}},
                                                 _source=False):
            self.es.delete(index=self.index, doc_type=self.__type__, id=record['_id'])

    def refresh(self):
        """
        Explicitly refresh one or more index, making all operations
        performed since the last refresh available for search.
        """
        self.es.indices.refresh(index=self.index)
