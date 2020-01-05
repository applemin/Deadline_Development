import os
import sys
import clr
import json
import requests
from pprint import pprint

from System import *
from System.Diagnostics import *
from Deadline.Scripting import *
from Deadline.Jobs import *
from System.IO import *
from Deadline.Plugins import *
from System.Collections.Specialized import StringCollection

def submit_job(DeadlinePlugin, job):

    job_name = job.JobName
    job_status = job.JobStatus
    job_id = job.JobId
    task_id = DeadlinePlugin.GetCurrentTaskId()

    host_name = os.getenv("DEADLINE_SERVER")
    port_number = os.getenv("DEADLIN_PORT")
    deadline_repo = os.getenv("DEADLINE_REPOSITORY")
    deadline_master = os.getenv("DEADLINE_MASTER")

    print "host_name: %s, port_number: %s, deadline_repo: %s, deadline_master: %s," % (host_name,
                                                                                       port_number,
                                                                                       deadline_repo,
                                                                                       deadline_master)

    url = 'http://{hostname}:{portnumber}/api/jobs'.format(hostname=host_name, portnumber=port_number)
    script_file = deadline_repo + r"\custom\plugins\RBServer\RBCallbacks.py"

    operation = "OnTaskFinished"
    job_info = {"BatchName": "%s_system_callbacks" % job_name,
                "Name": "%s_%s_callback" % (job_name, operation),
                "Frames": 1,
                "Priority": 90,
                "Whitelist": deadline_master,
                "Plugin": "RBServer"}

    plugin_info = {"Version": 2.7,
                   "JobName": job_name,
                   "JobStatus": job_status,
                   "JobId": job_id,
                   "Operation": operation,
                   "ScriptFile": script_file,
                   "TaskID": task_id
                   }

    body  = '{"JobInfo":' + json.dumps(job_info)
    body += ',"PluginInfo":' + json.dumps(plugin_info)
    body += ',"AuxFiles":' + json.dumps(list())
    body += ',"IdOnly":true}'

    request_data = requests.post(url, data=body)
    pprint(request_data.json())


def __main__(*args):

    print " Running RBKeyshot Post Task Script"
    DeadlinePlugin = args[0]

    job = DeadlinePlugin.GetJob()
    submit_job(DeadlinePlugin, job)


