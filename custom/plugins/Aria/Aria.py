import os
import json
import sys

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *

_deadline_repo = os.getenv("DEADLINE_REPOSITORY")
_socket_id = os.getenv("SOCKET_ID")
_callback_module = os.path.join(_deadline_repo, "custom/plugins/RBServer").replace("\\", "/")
sys.path.append(_callback_module)

import RBCallbacks

def GetDeadlinePlugin():
    return AriaPlugin()


def CleanupDeadlinePlugin(deadlinePlugin):
    deadlinePlugin.Cleanup()


class AriaPlugin(DeadlinePlugin):

    def __init__(self):

        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument

    def Cleanup(self):

        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess(self):

        self.PluginType = PluginType.Simple
        self.StdoutHandling = True
        
        self.version = int(self.GetPluginInfoEntryWithDefault("Version", "2"))
        
        self.AddStdoutHandlerCallback(r".*\(([0-9]+)%\).*").HandleCallback += self.HandleStdoutProgress
        self.AddStdoutHandlerCallback(".*download completed.*").HandleCallback += self.HandleJobCompleted

    def RenderExecutable(self):

        exe = str()
        exe_list = self.GetConfigEntry("Aria_RenderExecutable_" + str(self.version))
        exe = FileUtils.SearchFileList(exe_list)
        if exe == str():
            self.FailRender("Aria render executable was not found \"" + exe_list + "\". ")

        self.LogInfo("Aria executable : %s" % exe)
        return exe

    def HandlePathSeparators(self, path):

        if SystemUtils.IsRunningOnWindows():
            file_path = path.replace("/", "\\")
            if file_path.startswith("\\") and not file_path.startswith("\\\\"):
                file_path = "\\" + file_path
        else:
            file_path = path.replace("\\", "/")

        return file_path

    def RenderArgument(self):

        downloadFile = self.GetPluginInfoEntryWithDefault("DownloadLink", str())
        downloadFile = downloadFile.replace(" ", "%20")
        outputPath = self.GetPluginInfoEntryWithDefault("OutputDirectory", str())
        outputPath = self.HandlePathSeparators(outputPath)
        outputFilename = self.GetPluginInfoEntryWithDefault("OutputFilename", str())
        outputLog = self.GetPluginInfoEntryWithDefault("Log", str())
        serverConnections = self.GetIntegerPluginInfoEntryWithDefault("ServerConnections", 1)
        splitConnections = self.GetIntegerPluginInfoEntryWithDefault("SplitConnections", 5)
        serverTimeStamp = self.GetBooleanPluginInfoEntryWithDefault("ServerTimeStamp", True)
        timeOut = self.GetIntegerPluginInfoEntryWithDefault("Timeout", 60)
        dryRun = self.GetBooleanPluginInfoEntryWithDefault("DryRun", False)

        # deleting file if it's already downloaded
        dl_file = os.path.join(outputPath, outputFilename).replace("\\", "/")
        if os.path.exists(dl_file) and os.path.isfile(dl_file):
            self.LogWarning("File is already exists ,removing it. %s" % dl_file)
            os.remove(dl_file)

        renderArguments = " %s " % downloadFile
        if outputFilename:
            renderArguments += "--out=%s " % outputFilename
        if outputLog:
            renderArguments += "--log=%s " % outputLog
        renderArguments += "--split=%s " % splitConnections
        renderArguments += "--timeout=%s " % timeOut
        renderArguments += "--remote-time=%s " % str(serverTimeStamp).lower()
        renderArguments += "--dir=%s " % outputPath
        renderArguments += "--max-connection-per-server=%s " % serverConnections
        renderArguments += "%s " % self.GetPluginInfoEntryWithDefault("AdditionalOptions", str())
        
        return renderArguments

    def HandleStdoutProgress(self):
        value = float(self.GetRegexMatch(1))
        self.SetProgress(value)
        self.SetStatusMessage(self.GetRegexMatch(0))

        API = RBCallbacks.APIController(_socket_id, self.GetJobInfoEntry("Name"))

        if value and not int(value) % 10:
            API.update_progress(int(self.GetRegexMatch(1)))

    def HandleJobCompleted(self):
        self.LogInfo("Running Job Completion Handler.")

        file_date = self.GetPluginInfoEntry("FileDate")
        file_name = self.GetPluginInfoEntry("FileName")
        uid = self.GetPluginInfoEntry("UID")
        user_name = self.GetPluginInfoEntry("UserName")
        user_path = self.GetPluginInfoEntry("UserPath")
        outputPath = self.GetPluginInfoEntry("OutputDirectory")
        json_file_name = "_version_" + os.path.splitext(file_name)[0] + ".version"

        json_file = os.path.join(outputPath, json_file_name)

        dict_version_info = {"UserName": user_name,
                             "UID": uid,
                             "FileName": file_name,
                             "FileDate": file_date,
                             "UserPath": user_path}

        # if os.path.exists(json_file) and os.path.isfile(json_file):
        #     print "Version file is exists. : %s" % json_file
        #     with open(json_file, 'r') as json_file:
        #         loaded_data = json.load(json_file)
        #     if sorted(dict_version_info) == sorted(loaded_data):
        #         print "This file is already downloaded, returning the process. : %s" % file_name
        #         return False

        with open(json_file, 'w') as _json_file:
            print "Creating version file. : %s" % json_file
            json.dump(dict_version_info, _json_file, indent=4)

