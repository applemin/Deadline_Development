import sys
import os
import json
import requests
import traceback
from pprint import pprint

import Deadline.Events

#
#
# _MAPPED_STATUSES = {
#     0:  'system_unknown',
#     1:  'deadline_rendering',
#     2:  'deadline_suspended',
#     3:  'deadline_completed',
#     4:  'deadline_failed',
#     5:  'system_requeue',
#     6:  'deadline_pending',
#     7:  'deadline_queued',
#     8:  'client_uploading',
#     9:  'system_uploaded',
#     10: 'local_published',
#     11: 'unzip_failed',
#     12: 'download_failed',
#     13: 'system_failed',
#     14: 'failed_online',
#     15: 'system_pending',
#     16: 'local_queued',
#     18: 'file_not_found',
#     19: 'initializing',
#     25: 'system_cancelled',
#     50: 'system_deleted',
# }
#
# class RBStatus:
#
#     system_unknown      = 0
#     deadline_rendering  = 1
#     deadline_suspended  = 2
#     deadline_completed  = 3
#     deadline_failed     = 4
#     system_requeue      = 5
#     deadline_pending    = 6
#     deadline_queued     = 7
#     client_uploading    = 8
#     system_uploaded     = 9
#     local_published     = 10
#     unzip_failed        = 11
#     download_failed     = 12
#     system_failed       = 13
#     failed_online       = 14
#     system_pending      = 15
#     local_queued        = 16
#     file_not_found      = 18
#     initializing        = 19
#     system_cancelled    = 25
#     system_deleted      = 50
#
#     def __init__(self):
#         self.status_dict = self._status_dict()
#
#     def _status_dict(self):
#         dict_status = {"system_unknown": self.system_unknown,
#                        "deadline_rendering": self.deadline_rendering,
#                        "deadline_suspended": self.deadline_suspended,
#                        "deadline_completed": self.deadline_completed,
#                        "deadline_failed": self.deadline_failed,
#                        "system_requeue": self.system_requeue,
#                        "deadline_pending": self.deadline_pending,
#                        "deadline_queued": self.deadline_queued,
#                        "client_uploading": self.client_uploading,
#                        "system_uploaded": self.system_uploaded,
#                        "local_published": self.local_published,
#                        "unzip_failed": self.unzip_failed,
#                        "download_failed": self.download_failed,
#                        "system_failed": self.system_failed,
#                        "failed_online": self.failed_online,
#                        "system_pending": self.system_pending,
#                        "local_queued": self.local_queued,
#                        "file_not_found": self.file_not_found,
#                        "initializing": self.initializing,
#                        "system_cancelled": self.system_cancelled,
#                        "system_deleted": self.system_deleted}
#
#         return dict_status
#
#
# class APIController:
#
#     # API Links
#     _api_base_link           = "https://api.renderboost.com/node/demand/"
#     _update_status_link      = _api_base_link + "change-state"
#     _update_progress_link    = _api_base_link + "percent"
#     _validate_job_link       = _api_base_link + "valid-job"
#     _update_line_id_link     = _api_base_link + "change-job-id"
#     _submit_error_link       = _api_base_link + "set-error"
#     _get_job_data_link       = _api_base_link + "job-data"
#     _anim_task_update_link   = _api_base_link + "animation_task_time"
#
#     def __init__(self, token, job_code):
#
#         self.token = token
#         self.job_code = job_code
#
#     def validate_job(self):
#         url = self._validate_job_link
#         params = {'jobcode': self.job_code}
#         response = self.call_post(url, params)
#
#         if not response["status"]:
#             raise ValueError(response["msg"])
#
#         return _MAPPED_STATUSES[response["status"]]
#
#     def get_job_data(self):
#         url = self._get_job_data_link
#         params = {'jobcode': self.job_code}
#         response = self.call_post(url, params)
#
#         if not response["status"]:
#             raise ValueError(response["msg"])
#
#         return response["data"]
#
#     def update_status(self, new_status):
#         url = self._update_status_link
#         params = {'jobcode': self.job_code,
#                   'state': new_status}
#         response = self.call_post(url, params)
#
#         if new_status not in _MAPPED_STATUSES.keys():
#             raise ValueError("No status found for ID :`%s`." % new_status)
#
#         if response["status"]:
#             print "Job status changed to `%s` successfully." % _MAPPED_STATUSES[new_status]
#         else:
#             raise ValueError("Job status could not be changed to `%s` : `%s`" % (new_status, response["msg"]))
#
#         return response["status"]
#
#     def update_progress(self, value):
#         url = self._update_progress_link
#         params = {'jobcode': self.job_code,
#                   'percent': value}
#         response = self.call_post(url, params)
#
#         if not isinstance(value, int):
#             raise ValueError("Only `int` values are accepted: `%s`" % value)
#
#         if response["status"]:
#             print "Job progress changed to `%s` successfully." % value
#         else:
#             raise ValueError("Job progress could not be changed to `%s` : `%s`" % (value, response["msg"]))
#
#         return response["status"]
#
#     def update_line_id(self, _id):
#
#         url = self._update_line_id_link
#         params = {'jobcode': self.job_code,
#                   'lineid': _id}
#         response = self.call_post(url, params)
#
#         if response["status"]:
#             print "Line ID changed to `%s` successfully." % _id
#         else:
#             raise ValueError("Line ID could not be changed to `%s` : `%s`" % (_id, response["msg"]))
#
#         return response["status"]
#
#     def submit_error(self):
#         pass
#
#     def update_anim_task(self):
#         pass
#
#     def call_post(self, url, params):
#         headers = {'token': self.token}
#         request_data = requests.post(url, data=params, headers=headers)
#         pprint(request_data.json())
#         return request_data.json()


# api = APIController("194.225.172.50", "RENDERTEST51841")

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

        # self.import_rb_callbacks()

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
        print "Importing `RBCallbacks`"
        rb_callbacks = RepositoryUtils.GetPluginDirectory()
        sys.path.append(rb_callbacks)
        for path in sys.path:
            print path
        import RBCallbacks

    def run_script(self, *args):
        print args

    def OnJobSubmitted(self, job):

        self.run_script("OnJobSubmitted", job)

    def OnJobStarted(self, job):

        self.run_script("OnJobStarted", job)

    def OnJobFinished(self, job):

        self.run_script("OnJobFinished", job)

    def OnJobRequeued(self, job):

        self.run_script("OnJobRequeued", job)

    def OnJobFailed(self, job):

        self.run_script("OnJobFailed", job)

    def OnJobSuspended(self, job):

        self.run_script("OnJobSuspended", job)

    def OnJobResumed(self, job):

        self.run_script("OnJobResumed", job)

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
