import os

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *


def GetDeadlinePlugin():
    return ZipPlugin()


def CleanupDeadlinePlugin(deadlinePlugin):
    deadlinePlugin.Cleanup()


class ZipPlugin(DeadlinePlugin):

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


        #self.AddStdoutHandlerCallback(r".*\(([0-9]+)%\).*").HandleCallback += self.HandleStdoutProgress

    def RenderExecutable(self):

        exe = str()
        exe_list = self.GetConfigEntry("Zip_RenderExecutable_")
        exe = FileUtils.SearchFileList(exe_list)
        if exe == str():
            self.FailRender("7Zip render executable was not found \"" + exe_list + "\". ")

        self.LogInfo("Zip executable : %s" % exe)
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

        zipFile = self.GetPluginInfoEntryWithDefault("ZipFile", str())
        zipFile = self.HandlePathSeparators(zipFile)

        outputPath = self.GetPluginInfoEntryWithDefault("OutputDirectory", str())
        outputPath = self.HandlePathSeparators(outputPath)

        acceptQueries = self.GetBooleanPluginInfoEntryWithDefault("AcceptQueries", True)

        renderArguments = " x "
        renderArguments += '"%s" ' % zipFile
        renderArguments += "-o%s " % outputPath
        if acceptQueries:
            renderArguments += "-y "
        renderArguments += "%s " % self.GetPluginInfoEntryWithDefault("AdditionalOptions", str())

        return renderArguments

    def HandleStdoutProgress(self):
        self.SetProgress(float(self.GetRegexMatch(1)))
        self.SetStatusMessage(self.GetRegexMatch(0))
