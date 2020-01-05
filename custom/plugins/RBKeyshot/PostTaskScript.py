import os
import sys
import clr

from System import *
from System.Diagnostics import *
from Deadline.Scripting import *
from Deadline.Jobs import *
from System.IO import *
from Deadline.Plugins import *
from System.Collections.Specialized import StringCollection

_deadline_repo = os.getenv("DEADLINE_REPOSITORY")
_socket_id = os.getenv("SOCKET_ID")
_callback_module = os.path.join(_deadline_repo, "custom/plugins/RBServer").replace("\\", "/")
sys.path.append(_callback_module)

import RBCallbacks

def __main__(*args):

    print " Running RBKeyshot Post Task Script"
    DeadlinePlugin = args[0]

    _job = DeadlinePlugin.GetJob()

    job = RepositoryUtils.GetJob(_job.ID, True)
    tasks = RepositoryUtils.GetJobTasks(job, True)

    for task in tasks:
        print "tasks", task, type(task)

    tasks_collection = list(RepositoryUtils.GetJobTasks(job, True).TaskCollectionAllTasks)

    for task in tasks_collection:
        print "tasks_collection", task, type(task)

    target_task = tasks_collection[int(DeadlinePlugin.GetCurrentTaskId())]
    print "TaskFrameList", target_task.TaskFrameList, type(target_task.TaskFrameList)
    print "TaskFrameString", target_task.TaskFrameString, type(target_task.TaskFrameString)
    print "TaskStatus", target_task.TaskStatus, type(target_task.TaskStatus)
    print "TaskCpuUtilisation", target_task.TaskCpuUtilisation, type(target_task.TaskCpuUtilisation)
    print "TaskNormalizedRenderTime", target_task.TaskNormalizedRenderTime, type(target_task.TaskNormalizedRenderTime)
    print "TaskRenderTime", target_task.TaskRenderTime, type(target_task.TaskRenderTime)

    # stats = JobUtils.CalculateJobStatistics(job, tasks)

    job_name = job.JobName
    task_id = DeadlinePlugin.GetCurrentTaskId()
    frame_number = None
    render_time = None
    cpu_usage = None

    # API = RBCallbacks.APIController(_socket_id, job_name)
    # API.update_anim_task(task_id, frame_number, render_time, cpu_usage)

    # jobAverageFrameRenderTime = stats.AverageFrameRenderTime
    # jobPeakRamUsage = stats.PeakRamUsage / 1024 / 1024
    #
    # timeSpan = jobAverageFrameRenderTime
    # timeSpan = "%02dd:%02dh:%02dm:%02ds" % (timeSpan.Days, timeSpan.Hours, timeSpan.Minutes, timeSpan.Seconds)

    # TODO:update job progress based on completed tasks


    args = StringCollection()
    args.Add("GetJobTaskTotalTime")
    args.Add(job.ID)

    totalTimeString = ClientUtils.ExecuteCommandAndGetOutput(args)
    print totalTimeString