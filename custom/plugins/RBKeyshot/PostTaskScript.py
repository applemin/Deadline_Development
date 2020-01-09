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

def get_callback_job(current_job):

    callback_job = None
    callback_job_id = None

    # get callback job id if exists
    callback_job_id = current_job.GetJobExtraInfoKeyValueWithDefault("CallbackJobID", str())
    if callback_job_id:
        callback_job = RepositoryUtils.GetJob(callback_job_id, True)
        print "Target job already set with ID : %s" % str(callback_job.JobId)
    else:
        jobs = RepositoryUtils.GetJobs(True)
        for job in jobs:
            if job.JobName == current_job.JobName + "_Callback":
                callback_job = RepositoryUtils.GetJob(job.JobId, True)
                callback_job_id = callback_job.JobId
                print "Target job found in database with ID : %s" % str(callback_job.JobId)
                print "Set callback job id as extra info"
                current_job.SetJobExtraInfoKeyValue("CallbackJobID", callback_job.JobId)
                RepositoryUtils.SaveJob(current_job)
                break

    return callback_job, callback_job_id


def update_callback_job(DeadlinePlugin, job):

    current_job = DeadlinePlugin.GetJob()
    current_task = DeadlinePlugin.GetCurrentTaskId()
    print "current_job : %s  | current_task : %s" % (current_job, current_task)

    callback_job, callback_job_id = get_callback_job(current_job)

    tasks = list(RepositoryUtils.GetJobTasks(callback_job, True).TaskCollectionAllTasks)
    print "Resume taks ID : %s" % current_task
    RepositoryUtils.ResumeTasks(callback_job, [tasks[int(current_task)]])


def __main__(*args):

    print " Running RBKeyshot Post Task Script"
    DeadlinePlugin = args[0]

    job = DeadlinePlugin.GetJob()
    update_callback_job(DeadlinePlugin, job)


