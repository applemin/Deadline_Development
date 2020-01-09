import sys
import os
import json
import time
import requests
import traceback
from pprint import pprint

import Deadline.Events
import Deadline.Scripting
import Deadline.Plugins

def GetDeadlineEventListener():
    return EventScriptListener()


def CleanupDeadlineEventListener(eventListener):
    eventListener.Cleanup()


class EventScriptListener(Deadline.Events.DeadlineEventListener):

    def __init__(self):

        self.OnJobSubmittedCallback += self.OnJobSubmitted
        self.OnJobStartedCallback += self.OnJobStarted
        self.OnJobFinishedCallback += self.OnJobFinished
        self.OnJobRequeuedCallback += self.OnJobRequeued
        self.OnJobFailedCallback += self.OnJobFailed
        self.OnJobSuspendedCallback += self.OnJobSuspended
        self.OnJobResumedCallback += self.OnJobResumed
        self.OnJobPendedCallback += self.OnJobPended

        # self.OnJobReleasedCallback += self.OnJobReleased
        # self.OnJobDeletedCallback += self.OnJobDeleted
        # self.OnJobErrorCallback += self.OnJobError
        # self.OnJobPurgedCallback += self.OnJobPurged

        self.OnHouseCleaningCallback += self.OnHouseCleaning
        # self.OnRepositoryRepairCallback += self.OnRepositoryRepair
        #
        # self.OnSlaveStartedCallback += self.OnSlaveStarted
        # self.OnSlaveStoppedCallback += self.OnSlaveStopped
        # self.OnSlaveIdleCallback += self.OnSlaveIdle
        # self.OnSlaveRenderingCallback += self.OnSlaveRendering
        # self.OnSlaveStartingJobCallback += self.OnSlaveStartingJob
        # self.OnSlaveStalledCallback += self.OnSlaveStalled
        #
        # self.OnIdleShutdownCallback += self.OnIdleShutdown
        # self.OnMachineStartupCallback += self.OnMachineStartup
        # self.OnThermalShutdownCallback += self.OnThermalShutdown
        # self.OnMachineRestartCallback += self.OnMachineRestart

    def Cleanup(self):

        del self.OnJobSubmittedCallback
        del self.OnJobStartedCallback
        del self.OnJobFinishedCallback
        del self.OnJobRequeuedCallback
        del self.OnJobFailedCallback
        del self.OnJobSuspendedCallback
        del self.OnJobResumedCallback
        del self.OnJobPendedCallback
        del self.OnHouseCleaningCallback

        # del self.OnJobReleasedCallback
        # del self.OnJobDeletedCallback
        # del self.OnJobErrorCallback
        # del self.OnJobPurgedCallback
        #
        # del self.OnRepositoryRepairCallback
        #
        # del self.OnSlaveStartedCallback
        # del self.OnSlaveStoppedCallback
        # del self.OnSlaveIdleCallback
        # del self.OnSlaveRenderingCallback
        # del self.OnSlaveStartingJobCallback
        # del self.OnSlaveStalledCallback
        #
        # del self.OnIdleShutdownCallback
        # del self.OnMachineStartupCallback
        # del self.OnThermalShutdownCallback
        # del self.OnMachineRestartCallback

    def OnJobSubmitted(self, job):
        self.LogInfo("%s : %s" % (self.OnJobSubmitted.__name__, job.JobId))

    def OnJobStarted(self, job):
        self.LogInfo("%s : %s" % (self.OnJobStarted.__name__, job.JobId))
        submit_job(self.OnJobStarted.__name__, job.JobName, job.JobId, job.JobStatus)

    def OnJobFinished(self, job):
        self.LogInfo("%s : %s" % (self.OnJobFinished.__name__, job.JobId))
        submit_job(self.OnJobFinished.__name__, job.JobName, job.JobId, job.JobStatus)

    def OnJobRequeued(self, job):
        self.LogInfo("%s : %s" % (self.OnJobRequeued.__name__, job.JobId))
        submit_job(self.OnJobRequeued.__name__, job.JobName, job.JobId, job.JobStatus)

    def OnJobFailed(self, job):
        self.LogInfo("%s : %s" % (self.OnJobFailed.__name__, job.JobId))
        submit_job(self.OnJobFailed.__name__, job.JobName, job.JobId, job.JobStatus)

    def OnJobSuspended(self, job):
        self.LogInfo("%s : %s" % (self.OnJobSuspended.__name__, job.JobId))
        submit_job(self.OnJobSuspended.__name__, job.JobName, job.JobId, job.JobStatus)

    def OnJobResumed(self, job):
        self.LogInfo("%s : %s" % (self.OnJobResumed.__name__, job.JobId))
        submit_job(self.OnJobResumed.__name__, job.JobName, job.JobId, job.JobStatus)

    def OnJobPended(self, job):
        self.LogInfo("%s : %s" % (self.OnJobPended.__name__, job.JobId))
        submit_job(self.OnJobPended.__name__, job.JobName, job.JobId, job.JobStatus)

    # def OnJobReleased(self, job):
    #     self.LogInfo("%s : %s" % (self.OnJobReleased.__name__, job.JobId))

    # def OnJobDeleted(self, job):
    #     self.LogInfo("%s : %s" % (self.OnJobDeleted.__name__, job.JobId))

    # def OnJobError(self, job, task, report):
    #     self.LogInfo("%s : %s : %s : %s : %s" % (self.OnJobError.__name__, job.JobId, job, task, report))

    # def OnJobPurged(self, job):
    #     self.LogInfo("%s : %s" % (self.OnJobPurged.__name__, job.JobId))

    def OnHouseCleaning(self):
        self.LogInfo("OnHouseCleaning")
        still_frame_updater()

    # def OnRepositoryRepair(self, job):
    #     self.LogInfo("%s : %s" % (self.OnRepositoryRepair.__name__, job.JobId))
    #
    # def OnSlaveStarted(self, job):
    #     self.LogInfo("%s : %s" % (self.OnSlaveStarted.__name__, job.JobId))
    #
    # def OnSlaveStopped(self, job):
    #     self.LogInfo("%s : %s" % (self.OnSlaveStopped.__name__, job.JobId))

    # def OnSlaveIdle(self, job):
    #     self.LogInfo("%s : %s" % (self.OnSlaveIdle.__name__, job.JobId))

    # def OnSlaveRendering(self, slaveName, job):
    #     self.LogInfo("%s : %s : %s" % (self.OnSlaveRendering.__name__, job.JobId, slaveName))
    #
    # def OnSlaveStartingJob(self, slaveName, job):
    #     self.LogInfo("%s : %s : %s" % (self.OnSlaveStartingJob.__name__, job.JobId, slaveName))
    #
    # def OnSlaveStalled(self, slaveName, job):
    #     self.LogInfo("%s : %s : %s" % (self.OnSlaveStalled.__name__, job.JobId, slaveName))
    #
    # def OnIdleShutdown(self, job):
    #     self.LogInfo("%s : %s" % (self.OnIdleShutdown.__name__, job.JobId))
    #
    # def OnMachineStartup(self, job):
    #     self.LogInfo("%s : %s" % (self.OnMachineStartup.__name__, job.JobId))
    #
    # def OnThermalShutdown(self, job):
    #     self.LogInfo("%s : %s" % (self.OnThermalShutdown.__name__, job.JobId))
    #
    # def OnMachineRestart(self, job):
    #     self.LogInfo("%s : %s" % (self.OnMachineRestart.__name__, job.JobId))


def still_frame_updater():
    print "Running still frame updater"

    _deadline_repo = os.getenv("DEADLINE_REPOSITORY")
    _socket_id = os.getenv("SOCKET_ID")
    _callback_module = os.path.join(_deadline_repo, "custom/plugins/RBServer").replace("\\", "/")
    sys.path.append(_callback_module)
    import RBCallbacks

    jobs = Deadline.Scripting.RepositoryUtils.GetJobs(True)
    print "%s Jobs found in deadline" % len(jobs)
    for job in jobs:
        if job.GetJobExtraInfoKeyValue("Job_Type") == RBCallbacks.JobType.still_frame:
            print "GetJobExtraInfoKeyValue", job.GetJobExtraInfoKeyValue("Job_Type")
            job_id = job.JobId
            job_name = job.JobName
            job_status = job.JobStatus
            print "Still frame job found Job: %s ID: %s Status: %s" % (job_name, job_id,job_status)
            tasks = list(Deadline.Scripting.RepositoryUtils.GetJobTasks(job, True).TaskCollectionAllTasks)
            cpu_usage = tasks[0].TaskCpuUtilisation
            print "Task Cpu Utilisation : %s" % cpu_usage

            print "Calling single frame update API"
            # API = RBCallbacks.APIController(_socket_id, job_name)
            # API.update_still_task("1", "1", "1", cpu_usage)

def submit_job(operation, job_name, job_id, job_status):

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

    def job_code(_job_name):
        if "_Submitter" in _job_name:
            return _job_name.split("_Submitter")[0]
        elif "_Extractor" in _job_name:
            return _job_name.split("_Extractor")[0]
        elif "_Downloader" in _job_name:
            return _job_name.split("_Downloader")[0]
        else:
            return _job_name

    job_info = {"BatchName": "%s_system_callbacks" % job_code(job_name),
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
                   "TaskID": -1}

    body  = '{"JobInfo":' + json.dumps(job_info)
    body += ',"PluginInfo":' + json.dumps(plugin_info)
    body += ',"AuxFiles":' + json.dumps(list())
    body += ',"IdOnly":true}'

    request_data = requests.post(url, data=body)
    pprint(request_data.json())
