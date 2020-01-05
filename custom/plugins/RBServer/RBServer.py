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
    
    def RenderExecutable(self):
        version = self.GetPluginInfoEntry("Version")
        
        exeList = self.GetConfigEntry("Python_Executable_" + version.replace(".", "_"))
        exe = FileUtils.SearchFileList(exeList)
        if exe == "":
            self.FailRender("Python " + version + " executable was not found \"" + exeList + "\".")
        return exe
    
    def RenderArgument(self):

        scriptFile = self.GetPluginInfoEntryWithDefault("ScriptFile", self.GetDataFilename())
        scriptFile = RepositoryUtils.CheckPathMapping(scriptFile)

        job_name = self.GetPluginInfoEntryWithDefault("JobName", str())
        job_status = self.GetPluginInfoEntryWithDefault("JobStatus", str())
        job_id = self.GetPluginInfoEntryWithDefault("JobId", str())
        operation = self.GetPluginInfoEntryWithDefault("Operation", str())
        task_id = self.GetPluginInfoEntryWithDefault("TaskID", str())

        arguments = self.GetPluginInfoEntryWithDefault("Arguments", "")
        arguments = RepositoryUtils.CheckPathMapping(arguments)

        arguments += " %s  %s %s %s " % (job_id, job_name, job_status, operation, task_id)

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
