#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-11 18:40:03

# request schema
{
    'request': {
        'taskid': str,  # new, not changeable
        'project': str,  # new, not changeable
        'url': str,  # new, not changeable
        'result': str,  # json string
        'updatetime': int,
    }
}


class RequestDB(object):
    """
    database for request
    """
    def save(self,task,result):
        raise NotImplementedError

    def get(self,task ,fields=None):
        raise NotImplementedError
        
    def get_table_name(self,task):
        raise NotImplementedError
