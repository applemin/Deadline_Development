import os

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *


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

        downloadFile = self.GetPluginInfoEntryWithDefault("DownloadLink", self.GetDataFilename())
        outputPath = self.GetPluginInfoEntryWithDefault("OutputDirectory", str())
        outputPath = self.HandlePathSeparators(outputPath)
        outputFilename = self.GetPluginInfoEntryWithDefault("OutputFilename", str())
        outputLog = self.GetPluginInfoEntryWithDefault("Log", str())
        serverConnections = self.GetIntegerPluginInfoEntryWithDefault("ServerConnections", 1)
        splitConnections = self.GetIntegerPluginInfoEntryWithDefault("SplitConnections", 5)
        serverTimeStamp = self.GetBooleanPluginInfoEntryWithDefault("ServerTimeStamp", True)
        timeOut = self.GetIntegerPluginInfoEntryWithDefault("Timeout", 60)
        dryRun = self.GetBooleanPluginInfoEntryWithDefault("DryRun", False)

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
        self.SetProgress(float(self.GetRegexMatch(1)))
        self.SetStatusMessage(self.GetRegexMatch(0))
