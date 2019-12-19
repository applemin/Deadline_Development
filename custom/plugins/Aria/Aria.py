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

        outputLog = self.GetBooleanPluginInfoEntryWithDefault("Log", False)

        logFile = self.GetPluginInfoEntryWithDefault("LogFile", str())
        logFile = self.HandlePathSeparators(logFile)

        renderArguments = " %s " % downloadFile

        renderArguments += "-log "
        
        dryRun = self.GetPluginInfoEntryWithDefault("DryRun", False)
        if dryRun:
            renderArguments += "--dry-run=%s " % str(dryRun).lower()

        if not dryRun:
            renderArguments += "-d %s " % outputPath
            if outputLog:
                arg = "-"
                if logFile:
                    arg = logFile
                renderArguments += "-l %s " % arg

        renderArguments += " %s " % self.GetPluginInfoEntryWithDefault("AdditionalOptions", str())
        
        return renderArguments

    def HandleStdoutProgress(self):
        self.SetProgress(float(self.GetRegexMatch(1)))
