#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: https://github.com/LFreedomDev
# Created on 2018-08-31

# pretask schema
{
    'pretask': {
        'taskid':str,
        'project': str, 
        'url': str, 
    }
}


class PreTaskDB(object):
    """
    database for pretask
    """

    def insert(self,pretask):
        raise NotImplementedError

    def select(self,project):
        raise NotImplementedError

    def delete(self,taskid):
        raise NotImplementedError
