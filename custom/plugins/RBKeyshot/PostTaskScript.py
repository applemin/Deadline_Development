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

    target_callback_job = RepositoryUtils.GetJob(callback_job_id, True)
    tasks = list(RepositoryUtils.GetJobTasks(job, True).TaskCollectionAllTasks)

    # do not create callback job if it's already submitted
    callback_job_id = job.GetJobExtraInfoKeyValueWithDefault("CallbackID", str())
    print "callback_job_id: %s" % callback_job_id
    if callback_job_id:
        print "Callback job has already been created with ID : %s" % callback_job_id
        callback_job = RepositoryUtils.GetJob(callback_job_id, True)
        tasks = list(RepositoryUtils.GetJobTasks(callback_job, True).TaskCollectionAllTasks)
        print "Resume taks ID : %s" % task_id
        RepositoryUtils.ResumeTasks(callback_job, [tasks[int(task_id)]])
        return

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
    job_info = {"BatchName": "%s_Batch" % job_name,
                "Name": "%s_Callback" % job_name,
                "Frames": job.GetJobInfoKeyValue("Frames"),
                "Priority": 80,
                "Group": "callbacks",
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
    _id = request_data.json()["_id"]

    # suspend submitted callback job to make sure it's not send any task data
    callback_job = RepositoryUtils.GetJob(_id, True)
    RepositoryUtils.SuspendJob(callback_job)

    # register callback job id in current render job
    job.SetJobExtraInfoKeyValue("CallbackID", _id)
    RepositoryUtils.SaveJob(job)

    # TODO:this needs to be re implemented in main job
    # resume current task
    _tasks = list(RepositoryUtils.GetJobTasks(callback_job, True).TaskCollectionAllTasks)
    RepositoryUtils.ResumeTasks(callback_job, [_tasks[int(task_id)]])

def __main__(*args):

    print " Running RBKeyshot Post Task Script"
    DeadlinePlugin = args[0]

    job = DeadlinePlugin.GetJob()
    submit_job(DeadlinePlugin, job)


