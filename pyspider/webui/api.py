import socket
import logging

from six import iteritems, itervalues
from flask import render_template, request, json
from flask_cors import CORS

try:
    import flask_login as login
except ImportError:
    from flask.ext import login

from pyspider.libs import utils, sample_handler, dataurl, result_dump
from pyspider.libs.response import rebuild_response
from pyspider.processor.project_module import ProjectManager, ProjectFinder

from .app import app


logger = logging.getLogger('web')
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
index_fields = ['name', 'group', 'status', 'comments', 'rate', 'burst', 'updatetime']
cors_resp_header = {
    'Content-Type': 'application/json',
}

###########################################

@app.route('/robots.txt')
def robots():
    return """User-agent: *
Disallow: /
Allow: /$
Allow: /debug
Disallow: /debug/*?taskid=*
""", 200, {'Content-Type': 'text/plain'}

###########################################

@app.route('/api/project/list')
def api_project_list():
    projectdb = app.config['projectdb']
    projects = sorted(projectdb.get_all(fields=index_fields),
                      key=lambda k: (0 if k['group'] else 1, k['group'] or '', k['name']))
    return json.dumps({
            'Status':1,
            'Result':projects
        }), 200, cors_resp_header

@app.route('/api/project/queues')
def api_project_queues():
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

@app.route('/api/project/counter')
def api_project_counter():
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

@app.route('/api/project/run', methods=['POST', ])
def api_project_runtask():
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

@app.route('/api/project/update', methods=['POST', ])
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

###########################################

@app.route('/api/project/result')
def api_project_result():
    resultdb = app.config['resultdb']
    project = request.args.get('project')
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 20))

    count = resultdb.count(project)
    results = list(resultdb.select(project, offset=offset, limit=limit))

    return render_template(
        "result.html", count=count, results=results,
        result_formater=result_dump.result_formater,
        project=project, offset=offset, limit=limit, json=json
    )

@app.route('/api/project/result_dump/<project>.<_format>')
def api_project_result_dump(project, _format):
    resultdb = app.config['resultdb']
    # force update project list
    resultdb.get(project, 'any')
    if project not in resultdb.projects:
        return "no such project.", 404

    offset = int(request.args.get('offset', 0)) or None
    limit = int(request.args.get('limit', 0)) or None
    results = resultdb.select(project, offset=offset, limit=limit)

    if _format == 'json':
        valid = request.args.get('style', 'rows') == 'full'
        return Response(result_dump.dump_as_json(results, valid),
                        mimetype='application/json')
    elif _format == 'txt':
        return Response(result_dump.dump_as_txt(results),
                        mimetype='text/plain')
    elif _format == 'csv':
        return Response(result_dump.dump_as_csv(results),
                        mimetype='text/csv')

###########################################

@app.route('/api/task/active_list')
def api_task_active_list():
    rpc = app.config['scheduler_rpc']
    taskdb = app.config['taskdb']
    project = request.args.get('project', "")
    limit = int(request.args.get('limit', 100))

    try:
        updatetime_tasks = rpc.get_active_tasks(project, limit)
    except socket.error as e:
        app.logger.warning('connect to scheduler rpc error: %r', e)
        return json.dumps({
                    'Status':3,
                    'Message':'connect to scheduler rpc error'
                }), 200, cors_resp_header

    tasks = {}
    result = []

    for updatetime, task in sorted(updatetime_tasks, key=lambda x: x[0]):
        key = '%(project)s:%(taskid)s' % task
        task['updatetime'] = updatetime
        task['updatetime_text'] = utils.format_date(updatetime)

        if key in tasks and tasks[key].get('status', None) != taskdb.ACTIVE:
            result.append(tasks[key])
        tasks[key] = task
    result.extend(tasks.values())

    return json.dumps({
            'Status':1,
            'Result':result
        }), 200, cors_resp_header

@app.route('/api/task/<taskid>')
def api_task_detail(taskid):
    if ':' not in taskid:
        return json.dumps({
            'Status':3,
            'Message':"bad project:task_id format"
        }), 200, cors_resp_header

    project, taskid = taskid.split(':', 1)

    taskdb = app.config['taskdb']
    task = taskdb.get_task(project, taskid)

    if not task:
        return json.dumps({
            'Status':3,
            'Message':"task not found"
        }), 200, cors_resp_header
    task['status_string'] = app.config['taskdb'].status_to_string(task['status'])


    if "lastcrawltime" in task.keys():
        task["lastcrawltime_text"] =utils.format_date(task["lastcrawltime"]) 
    if "updatetime" in task.keys():
        task["updatetime_text"] =utils.format_date(task["updatetime"]) 
    if "exetime" in task.get("schedule",{}).keys():
        task["schedule"]["exetime_text"] =utils.format_date(task["schedule"]["exetime"]) 


    resultdb = app.config['resultdb']
    result = {}
    if resultdb:
        result = resultdb.get(project, taskid)

    if "result" in task.get("track",{}).get("process",{}).keys():
        task["result"]= result

    return json.dumps({
            'Status':1,
            'Result':task
        }), 200, cors_resp_header

###########################################





