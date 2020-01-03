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
        self.OnJobReleasedCallback += self.OnJobReleased
        self.OnJobDeletedCallback += self.OnJobDeleted
        self.OnJobErrorCallback += self.OnJobError
        self.OnJobPurgedCallback += self.OnJobPurged

        self.OnHouseCleaningCallback += self.OnHouseCleaning
        self.OnRepositoryRepairCallback += self.OnRepositoryRepair

        self.OnSlaveStartedCallback += self.OnSlaveStarted
        self.OnSlaveStoppedCallback += self.OnSlaveStopped
        self.OnSlaveIdleCallback += self.OnSlaveIdle
        self.OnSlaveRenderingCallback += self.OnSlaveRendering
        self.OnSlaveStartingJobCallback += self.OnSlaveStartingJob
        self.OnSlaveStalledCallback += self.OnSlaveStalled

        self.OnIdleShutdownCallback += self.OnIdleShutdown
        self.OnMachineStartupCallback += self.OnMachineStartup
        self.OnThermalShutdownCallback += self.OnThermalShutdown
        self.OnMachineRestartCallback += self.OnMachineRestart

    def Cleanup(self):

        del self.OnJobSubmittedCallback
        del self.OnJobStartedCallback
        del self.OnJobFinishedCallback
        del self.OnJobRequeuedCallback
        del self.OnJobFailedCallback
        del self.OnJobSuspendedCallback
        del self.OnJobResumedCallback
        del self.OnJobPendedCallback
        del self.OnJobReleasedCallback
        del self.OnJobDeletedCallback
        del self.OnJobErrorCallback
        del self.OnJobPurgedCallback

        del self.OnHouseCleaningCallback
        del self.OnRepositoryRepairCallback

        del self.OnSlaveStartedCallback
        del self.OnSlaveStoppedCallback
        del self.OnSlaveIdleCallback
        del self.OnSlaveRenderingCallback
        del self.OnSlaveStartingJobCallback
        del self.OnSlaveStalledCallback

        del self.OnIdleShutdownCallback
        del self.OnMachineStartupCallback
        del self.OnThermalShutdownCallback
        del self.OnMachineRestartCallback

    def OnJobSubmitted(self, job):
        self.LogInfo("%s : %s" % (self.OnJobSubmitted.__name__, job.JobId))

    def OnJobStarted(self, job):
        self.LogInfo("%s : %s" % (self.OnJobStarted.__name__, job.JobId))

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

    def OnJobPended(self, job):
        self.LogInfo("%s : %s" % (self.OnJobPended.__name__, job.JobId))
        submit_job(self.OnJobStarted.__name__, job.JobName, job.JobId, job.JobStatus)

    def OnJobReleased(self, job):
        self.LogInfo("%s : %s" % (self.OnJobReleased.__name__, job.JobId))

    def OnJobDeleted(self, job):
        self.LogInfo("%s : %s" % (self.OnJobDeleted.__name__, job.JobId))

    def OnJobError(self, job, task, report):
        self.LogInfo("%s : %s : %s : %s : %s" % (self.OnJobDeleted.__name__, job.JobId, job, task, report))

    def OnJobPurged(self, job):
        self.LogInfo("%s : %s" % (self.OnJobPurged.__name__, job.JobId))

    def OnHouseCleaning(self):
        self.LogInfo("%s" % self.OnJobPurged.__name__)

    def OnRepositoryRepair(self, job):
        self.LogInfo("%s : %s" % (self.OnRepositoryRepair.__name__, job.JobId))

    def OnSlaveStarted(self, job):
        self.LogInfo("%s : %s" % (self.OnSlaveStarted.__name__, job.JobId))

    def OnSlaveStopped(self, job):
        self.LogInfo("%s : %s" % (self.OnSlaveStopped.__name__, job.JobId))

    def OnSlaveIdle(self, job):
        self.LogInfo("%s : %s" % (self.OnSlaveIdle.__name__, job.JobId))

    def OnSlaveRendering(self, slaveName, job):
        self.LogInfo("%s : %s : %s" % (self.OnSlaveRendering.__name__, job.JobId, slaveName))

    def OnSlaveStartingJob(self, slaveName, job):
        self.LogInfo("%s : %s : %s" % (self.OnSlaveStartingJob.__name__, job.JobId, slaveName))

    def OnSlaveStalled(self, slaveName, job):
        self.LogInfo("%s : %s : %s" % (self.OnSlaveStalled.__name__, job.JobId, slaveName))

    def OnIdleShutdown(self, job):
        self.LogInfo("%s : %s" % (self.OnIdleShutdown.__name__, job.JobId))

    def OnMachineStartup(self, job):
        self.LogInfo("%s : %s" % (self.OnMachineStartup.__name__, job.JobId))

    def OnThermalShutdown(self, job):
        self.LogInfo("%s : %s" % (self.OnThermalShutdown.__name__, job.JobId))

    def OnMachineRestart(self, job):
        self.LogInfo("%s : %s" % (self.OnMachineRestart.__name__, job.JobId))


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
                   "ScriptFile": script_file}

    body  = '{"JobInfo":' + json.dumps(job_info)
    body += ',"PluginInfo":' + json.dumps(plugin_info)
    body += ',"AuxFiles":' + json.dumps(list())
    body += ',"IdOnly":true}'

    request_data = requests.post(url, data=body)
    pprint(request_data.json())
