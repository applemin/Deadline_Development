import os
import re
import sys
import json
import time
import requests
from pprint import pprint

from System.IO import *
from System.Text.RegularExpressions import *
from Deadline.Plugins import *
from Deadline.Scripting import *


_MAPPED_STATUSES = {
    0:  'system_unknown',
    1:  'deadline_rendering',
    2:  'deadline_suspended',
    3:  'deadline_completed',
    4:  'deadline_failed',
    5:  'system_requeue',
    6:  'deadline_pending',
    7:  'deadline_queued',
    8:  'client_uploading',
    9:  'system_uploaded',
    10: 'local_published',
    11: 'unzip_failed',
    12: 'download_failed',
    13: 'system_failed',
    14: 'failed_online',
    15: 'system_pending',
    16: 'local_queued',
    18: 'file_not_found',
    19: 'initializing',
    25: 'system_cancelled',
    50: 'system_deleted',
}


class RBStatus:

    system_unknown      = 0
    deadline_rendering  = 1
    deadline_suspended  = 2
    deadline_completed  = 3
    deadline_failed     = 4
    system_requeue      = 5
    deadline_pending    = 6
    deadline_queued     = 7
    client_uploading    = 8
    system_uploaded     = 9
    local_published     = 10
    unzip_failed        = 11
    download_failed     = 12
    system_failed       = 13
    failed_online       = 14
    system_pending      = 15
    local_queued        = 16
    file_not_found      = 18
    initializing        = 19
    system_cancelled    = 25
    system_deleted      = 50

    def __init__(self):
        self.status_dict = self._status_dict()

    def _status_dict(self):
        dict_status = {"system_unknown": self.system_unknown,
                       "deadline_rendering": self.deadline_rendering,
                       "deadline_suspended": self.deadline_suspended,
                       "deadline_completed": self.deadline_completed,
                       "deadline_failed": self.deadline_failed,
                       "system_requeue": self.system_requeue,
                       "deadline_pending": self.deadline_pending,
                       "deadline_queued": self.deadline_queued,
                       "client_uploading": self.client_uploading,
                       "system_uploaded": self.system_uploaded,
                       "local_published": self.local_published,
                       "unzip_failed": self.unzip_failed,
                       "download_failed": self.download_failed,
                       "system_failed": self.system_failed,
                       "failed_online": self.failed_online,
                       "system_pending": self.system_pending,
                       "local_queued": self.local_queued,
                       "file_not_found": self.file_not_found,
                       "initializing": self.initializing,
                       "system_cancelled": self.system_cancelled,
                       "system_deleted": self.system_deleted}

        return dict_status


class APIController:

    # API Links
    _api_base_link           = "https://api.renderboost.com/node/demand/"
    _update_status_link      = _api_base_link + "change-state"
    _update_progress_link    = _api_base_link + "percent"
    _validate_job_link       = _api_base_link + "valid-job"
    _update_line_id_link     = _api_base_link + "change-job-id"
    _submit_error_link       = _api_base_link + "set-error"
    _get_job_data_link       = _api_base_link + "job-data"
    _anim_task_update_link   = _api_base_link + "animation_task_time"

    def __init__(self):

        self.token = str()
        self.job_code = str()

    def set_data(self, token, job):
        self.token = token
        self.job_code = job

    def set_token(self, token):
        self.token = token

    def set_job_code(self, job_code):
        self.job_code = job_code

    def validate_job(self):
        url = self._validate_job_link
        params = {'jobcode': self.job_code}
        response = self.call_post(url, params)

        if not response["status"]:
            raise ValueError("Job is `Unknown`.")
        print _MAPPED_STATUSES[response["status"]]
        return _MAPPED_STATUSES[response["status"]]

    def get_job_data(self):
        url = self._get_job_data_link
        params = {'jobcode': self.job_code}
        response = self.call_post(url, params)

        if not response["status"]:
            raise ValueError(response["msg"])

        return response["data"]

    def update_status(self, new_status):
        url = self._update_status_link
        params = {'jobcode': self.job_code,
                  'state': new_status}
        response = self.call_post(url, params)

        if new_status not in _MAPPED_STATUSES.keys():
            raise ValueError("No status found for ID :`%s`." % new_status)

        if response["status"]:
            print "Job status changed to `%s` successfully." % _MAPPED_STATUSES[new_status]
        else:
            raise ValueError("Job status could not be changed to `%s` : `%s`" % (new_status, response["msg"]))

        return response["status"]

    def update_progress(self, value):
        url = self._update_progress_link
        params = {'jobcode': self.job_code,
                  'percent': value}
        response = self.call_post(url, params)

        if not isinstance(value, int):
            raise ValueError("Only `int` values are accepted: `%s`" % value)

        if response["status"]:
            print "Job progress changed to `%s` successfully." % value
        else:
            raise ValueError("Job progress could not be changed to `%s` : `%s`" % (value, response["msg"]))

        return response["status"]

    def update_line_id(self, _id):

        url = self._update_line_id_link
        params = {'jobcode': self.job_code,
                  'lineid': _id}
        response = self.call_post(url, params)

        if response["status"]:
            print "Line ID changed to `%s` successfully." % _id
        else:
            raise ValueError("Line ID could not be changed to `%s` : `%s`" % (_id, response["msg"]))

        return response["status"]

    def submit_error(self):
        pass

    def update_anim_task(self):
        pass

    def call_post(self, url, params):
        print "Token: %s" % self.token
        print "Params: %s" % params
        headers = {'token': self.token}
        request_data = requests.post(url, data=params, headers=headers)
        pprint(request_data.json())
        return request_data.json()


def GetDeadlinePlugin():
    return PythonPlugin()


def CleanupDeadlinePlugin(deadlinePlugin):
    deadlinePlugin.Cleanup()


class PythonPlugin (DeadlinePlugin):

    def __init__(self):

        self.currentJob = str()

        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks

    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
    
    def InitializeProcess(self):

        self.PluginType = PluginType.Simple
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback(".*Progress: (\d+)%.*").HandleCallback += self.HandleProgress
        
        pythonPath = self.GetEnvironmentVariable("PYTHONPATH").strip()
        addingPaths = self.GetConfigEntryWithDefault("PythonSearchPaths", "").strip()
        
        if addingPaths != "":
            addingPaths.replace(';', os.pathsep)
            
            if pythonPath != "":
                pythonPath = pythonPath + os.pathsep + addingPaths
            else:
                pythonPath = addingPaths
            
            self.LogInfo("Setting PYTHONPATH to: " + pythonPath)
            self.SetEnvironmentVariable("PYTHONPATH", pythonPath)
    
    def RenderExecutable( self ):
        version = self.GetPluginInfoEntry("Version")
        
        exeList = self.GetConfigEntry("Python_Executable_" + version.replace(".", "_"))
        exe = FileUtils.SearchFileList(exeList)
        if exe == "":
            self.FailRender("Python " + version + " executable was not found \"" + exeList + "\".")
        return exe
    
    def RenderArgument(self):

        scriptFile = self.GetPluginInfoEntryWithDefault("ScriptFile", self.GetDataFilename())
        scriptFile = RepositoryUtils.CheckPathMapping(scriptFile)

        job_name = self.GetPluginInfoEntry("JobName")
        job_status = self.GetPluginInfoEntry("JobStatus")
        job_id = self.GetPluginInfoEntry("JobId")
        
        arguments = self.GetPluginInfoEntryWithDefault("Arguments", "")
        arguments = RepositoryUtils.CheckPathMapping(arguments)

        arguments += "-job_id %s " % job_id
        arguments += "-job_name %s " % job_name
        arguments += "-job_status %s " % job_status

        if SystemUtils.IsRunningOnWindows():
            scriptFile = scriptFile.replace("/", "\\")
        else:
            scriptFile = scriptFile.replace("\\", "/")

        return "-u \"" + scriptFile + "\" " + arguments

    def HandleProgress(self):
        progress = float(self.GetRegexMatch(1))
        self.SetProgress(progress)

    def PreRenderTasks(self):
        self.LogInfo("Running PreRenderTasks")
        self.currentJob = self.GetJob()
        self.LogInfo("Current Job ID : %s" % self.currentJob.JobId)

    def PostRenderTasks(self):
        self.LogInfo("Running PostRenderTasks")
