#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:20:39

import socket

from six import iteritems, itervalues
from flask import render_template, request, json
from flask_cors import CORS

try:
    import flask_login as login
except ImportError:
    from flask.ext import login

from .app import app

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

index_fields = ['name', 'group', 'status', 'comments', 'rate', 'burst', 'updatetime']

cors_resp_header = {
        'Content-Type': 'application/json',
    }

@app.route('/')
def index():
    projectdb = app.config['projectdb']
    projects = sorted(projectdb.get_all(fields=index_fields),
                      key=lambda k: (0 if k['group'] else 1, k['group'] or '', k['name']))
    return render_template("index.html", projects=projects)


@app.route('/queues')
def get_queues():
    def try_get_qsize(queue):
        if queue is None:
            return 'None'
        try:
            return queue.qsize()
        except Exception as e:
            return "%r" % e

    result = {}
    queues = app.config.get('queues', {})
    for key in queues:
        result[key] = try_get_qsize(queues[key])
    return json.dumps(result), 200, {
        'Content-Type': 'application/json',
    }


@app.route('/update', methods=['POST', ])
def project_update():
    projectdb = app.config['projectdb']
    project = request.form['pk']
    name = request.form['name']
    value = request.form['value']

    project_info = projectdb.get(project, fields=('name', 'group'))
    if not project_info:
        return "no such project.", 404
    if 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return app.login_response

    if name not in ('comments','group', 'status', 'rate'):
        return 'unknown field: %s' % name, 400
    if name == 'rate':
        value = value.split('/')
        if len(value) != 2:
            return 'format error: rate/burst', 400
        rate = float(value[0])
        burst = float(value[1])
        update = {
            'rate': min(rate, app.config.get('max_rate', rate)),
            'burst': min(burst, app.config.get('max_burst', burst)),
        }
    else:
        update = {
            name: value
        }

    ret = projectdb.update(project, update)
    if ret:
        rpc = app.config['scheduler_rpc']
        if rpc is not None:
            try:
                rpc.update_project()
            except socket.error as e:
                app.logger.warning('connect to scheduler rpc error: %r', e)
                return 'rpc error', 200
        return 'ok', 200
    else:
        return 'update error', 500


@app.route('/counter')
def counter():
    rpc = app.config['scheduler_rpc']
    if rpc is None:
        return json.dumps({})

    result = {}
    try:
        data = rpc.webui_update()
        for type, counters in iteritems(data['counter']):
            for project, counter in iteritems(counters):
                result.setdefault(project, {})[type] = counter
        for project, paused in iteritems(data['pause_status']):
            result.setdefault(project, {})['paused'] = paused
    except socket.error as e:
        app.logger.warning('connect to scheduler rpc error: %r', e)
        return json.dumps({}), 200, {'Content-Type': 'application/json'}

    return json.dumps(result), 200, {'Content-Type': 'application/json'}


@app.route('/run', methods=['POST', ])
def runtask():
    rpc = app.config['scheduler_rpc']
    if rpc is None:
        return json.dumps({})

    projectdb = app.config['projectdb']
    project = request.form['project']
    project_info = projectdb.get(project, fields=('name', 'group'))
    if not project_info:
        return "no such project.", 404
    if 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return app.login_response

    newtask = {
        "project": project,
        "taskid": "on_start",
        "url": "data:,on_start",
        "process": {
            "callback": "on_start",
        },
        "schedule": {
            "age": 0,
            "priority": 9,
            "force_update": True,
        },
    }

    try:
        ret = rpc.newtask(newtask)
    except socket.error as e:
        app.logger.warning('connect to scheduler rpc error: %r', e)
        return json.dumps({"result": False}), 200, {'Content-Type': 'application/json'}
    return json.dumps({"result": ret}), 200, {'Content-Type': 'application/json'}


@app.route('/robots.txt')
def robots():
    return """User-agent: *
Disallow: /
Allow: /$
Allow: /debug
Disallow: /debug/*?taskid=*
""", 200, {'Content-Type': 'text/plain'}











@app.route('/api/projects')
def api_get_projects():
    projectdb = app.config['projectdb']
    projects = sorted(projectdb.get_all(fields=index_fields),
                      key=lambda k: (0 if k['group'] else 1, k['group'] or '', k['name']))
    return json.dumps({
            'Status':1,
            'Result':projects
        }), 200, cors_resp_header


@app.route('/api/queues')
def api_get_queues():
    def try_get_qsize(queue):
        if queue is None:
            return 'None'
        try:
            return queue.qsize()
        except Exception as e:
            return "%r" % e

    result = {}
    queues = app.config.get('queues', {})
    for key in queues:
        result[key] = try_get_qsize(queues[key])

    return json.dumps({
            'Status':1,
            'Result':result
        }), 200, cors_resp_header


@app.route('/api/counter')
def api_counter():
    rpc = app.config['scheduler_rpc']
    if rpc is None:
        return json.dumps({
                'Status':3,
                'Message':'connect to scheduler rpc error'
            }), 200, cors_resp_header

    result = {}
    result2 = []
    type_maps = {
        "1d":"one_day",
        "1h":"one_hour",
        "5m":"five_min",
        "all":"all",
        "5m_time":"five_min_time"
    }
    try:
        data = rpc.webui_update()
        for type, counters in iteritems(data['counter']):
            for project, counter in iteritems(counters):
                ncounter ={
                        "pending":counter.get("pending",0),
                        "success":counter.get("success",0),
                        "retry":counter.get("retry",0),
                        "failed":counter.get("failed",0),
                        "fetch_time":counter.get("fetch_time",0),
                        "process_time":counter.get("process_time",0),
                }
                if type in type_maps.keys():
                    result.setdefault(project, {})[type_maps[type]] = ncounter 
                else:
                    result.setdefault(project, {})[type] = ncounter

        for project, paused in iteritems(data['pause_status']):
            result.setdefault(project, {})['paused'] = paused
        
        for project in result.keys():
            result2.append({
                    "project":project,
                    "counters":result[project]      
                })

    except socket.error as e:
        app.logger.warning('connect to scheduler rpc error: %r', e)
        return json.dumps({
                'Status':3,
                'Message':'connect to scheduler rpc error'
            }), 200, cors_resp_header

    return json.dumps({
            'Status':1,
            'Result':result2
        }), 200, cors_resp_header


@app.route('/api/run', methods=['POST', ])
def api_runtask():
    rpc = app.config['scheduler_rpc']
    if rpc is None:
        return json.dumps({})

    projectdb = app.config['projectdb']
    project = request.form['project']
    project_info = projectdb.get(project, fields=('name', 'group'))
    if not project_info:
        return json.dumps({
                'Status':3,
                'Message':'project not found'
            }), 200, cors_resp_header

    if 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return app.login_response

    newtask = {
        "project": project,
        "taskid": "on_start",
        "url": "data:,on_start",
        "process": {
            "callback": "on_start",
        },
        "schedule": {
            "age": 0,
            "priority": 9,
            "force_update": True,
        },
    }

    try:
        ret = rpc.newtask(newtask)
    except socket.error as e:
        app.logger.warning('connect to scheduler rpc error: %r', e)
        return json.dumps({
                'Status':3,
                'Message':'connect to scheduler rpc error'
            }), 200, cors_resp_header


    return json.dumps({
                'Status':1,
                'Result':ret
            }), 200, cors_resp_header


@app.route('/api/update', methods=['POST', ])
def api_project_update():
    projectdb = app.config['projectdb']
    project = request.form['pk']
    name = request.form['name']
    value = request.form['value']

    project_info = projectdb.get(project, fields=('name', 'group'))
    if not project_info:
        return json.dumps({
                'Status':3,
                'Message':'project not found'
            }), 200, cors_resp_header
    if 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return app.login_response

    if name not in ('comments','group', 'status', 'rate'):
        return json.dumps({
                'Status':3,
                'Message':'unknown field: %s' % name
            }), 200, cors_resp_header

    if name == 'rate':
        value = value.split('/')
        if len(value) != 2:
            return json.dumps({
                'Status':3,
                'Message':'format error: rate/burst'
            }), 200, cors_resp_header
        rate = float(value[0])
        burst = float(value[1])
        update = {
            'rate': min(rate, app.config.get('max_rate', rate)),
            'burst': min(burst, app.config.get('max_burst', burst)),
        }
    else:
        update = {
            name: value
        }

    ret = projectdb.update(project, update)
    if ret:
        rpc = app.config['scheduler_rpc']
        if rpc is not None:
            try:
                rpc.update_project()
            except socket.error as e:
                app.logger.warning('connect to scheduler rpc error: %r', e)
                return json.dumps({
                    'Status':3,
                    'Message':'connect to scheduler rpc error'
                }), 200, cors_resp_header
        return json.dumps({
                    'Status':1,
                }), 200, cors_resp_header
    else:
        return json.dumps({
                    'Status':3,
                    'Message':'update error'
                }), 200, cors_resp_header