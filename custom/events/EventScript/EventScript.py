import sys
import os
import json
import requests
import traceback
from pprint import pprint

import Deadline.Events
import Deadline.Scripting
import Deadline.Plugins

SOCKET_ID = os.getenv("SOCKET_ID")

def GetDeadlineEventListener():
    return EventScriptListener()


def CleanupDeadlineEventListener(eventListener):
    eventListener.Cleanup()


class EventScriptListener(Deadline.Events.DeadlineEventListener):

    def __init__(self):

        self.import_rb_callbacks()

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

    def import_rb_callbacks(self):
        rb_callbacks = r"A:\DeadlineRepository10\plugins"
        print "rb_callbacks path : %s " % rb_callbacks
        sys.path.append(rb_callbacks)
        for path in sys.path:print path
        import RBCallbacks
        self.RBStatus = RBCallbacks.RBStatus
        self.API = RBCallbacks.APIController(socket_id)

    def get_job_code(self, job_name):
        if "_Submitter" in job_name:
            return job_name.split("_Submitter")[0]
        elif "_Extractor" in job_name:
            return job_name.split("_Extractor")[0]
        elif "_Downloader" in job_name:
            return job_name.split("_Downloader")[0]
        else:
            return job_name


    def run_script(self, *args):
        print args

    def OnJobSubmitted(self, job):

        self.run_script("OnJobSubmitted", job)

    def OnJobStarted(self, job):
        self.LogInfo("OnJobStarted : %s" % job.JobId)
        job_name = self.get_job_code(str(job.JobName))
        self.API.set_job_code(job_name)
        self.API.set_token(SOCKET_ID)
        self.API.validate_job()
        self.API.update_status(self.RBStatus.initializing)

    def OnJobFinished(self, job):

        self.run_script("OnJobFinished", job)

    def OnJobRequeued(self, job):
        self.run_script("OnJobRequeued", job)

    def OnJobFailed(self, job):

        self.run_script("OnJobFailed", job)

    def OnJobSuspended(self, job):

        self.run_script("OnJobSuspended", job)

    def OnJobResumed(self, job):
        self.LogInfo("OnJobResumed : %s" % job.JobId)
        job_name = self.get_job_code(str(job.JobName))
        self.API.set_job_code(job_name)
        self.API.set_token(SOCKET_ID)
        self.API.validate_job()
        # self.API.update_status(self.RBStatus.initializing)

    def OnJobPended(self, job):

        self.run_script("OnJobPended", job)

    def OnJobReleased(self, job):

        self.run_script("OnJobReleased", job)

    def OnJobDeleted(self, job):

        self.run_script("OnJobDeleted", job)

    def OnJobError(self, job, task, report):

        self.run_script("OnJobError", job, task, report)

    def OnJobPurged(self, job):

        self.run_script("OnJobPurged", job)

    def OnHouseCleaning(self):

        self.run_script("OnHouseCleaning")

    def OnRepositoryRepair(self, job):

        self.run_script("OnRepositoryRepair", job)

    def OnSlaveStarted(self, job):

        self.run_script("OnSlaveStarted", job)

    def OnSlaveStopped(self, job):

        self.run_script("OnSlaveStopped", job)

    def OnSlaveIdle(self, job):

        self.run_script("OnSlaveIdle", job)

    def OnSlaveRendering(self, slaveName, job):

        self.run_script("OnSlaveRendering", job, slaveName)

    def OnSlaveStartingJob(self, slaveName, job):

        self.run_script("OnSlaveStartingJob", job, slaveName)

    def OnSlaveStalled(self, slaveName, job):

        self.run_script("OnSlaveStalled", job, slaveName)

    def OnIdleShutdown(self, job):

        self.run_script("OnIdleShutdown", job)

    def OnMachineStartup(self, job):

        self.run_script("OnMachineStartup", job)

    def OnThermalShutdown(self, job):

        self.run_script("OnThermalShutdown", job)

    def OnMachineRestart(self, job):

        self.run_script("OnMachineRestart", job)
