from System.IO import *
from System.Text.RegularExpressions import *

from Deadline.Plugins import *
from Deadline.Scripting import *

import os
import sys
import re
import requests

def GetDeadlinePlugin():
    return PythonPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
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
        
        self.SingleFramesOnly = self.GetBooleanPluginInfoEntryWithDefault( "SingleFramesOnly", False )
        self.LogInfo( "Single Frames Only: %s" % self.SingleFramesOnly )

        self.AddStdoutHandlerCallback( ".*Progress: (\d+)%.*" ).HandleCallback += self.HandleProgress
        
        pythonPath = self.GetEnvironmentVariable( "PYTHONPATH" ).strip()
        addingPaths = self.GetConfigEntryWithDefault( "PythonSearchPaths", "" ).strip()
        
        if addingPaths != "":
            addingPaths.replace( ';', os.pathsep )
            
            if pythonPath != "":
                pythonPath = pythonPath + os.pathsep + addingPaths
            else:
                pythonPath = addingPaths
            
            self.LogInfo( "Setting PYTHONPATH to: " + pythonPath )
            self.SetEnvironmentVariable( "PYTHONPATH", pythonPath )
    
    def RenderExecutable( self ):
        version = self.GetPluginInfoEntry( "Version" )
        
        exeList = self.GetConfigEntry( "Python_Executable_" + version.replace( ".", "_" ) )
        exe = FileUtils.SearchFileList( exeList )
        if exe == "":
            self.FailRender( "Python " + version + " executable was not found in the semicolon separated list \"" + exeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return exe
    
    def RenderArgument( self ):
        scriptFile = self.GetPluginInfoEntryWithDefault("ScriptFile", self.GetDataFilename())
        scriptFile = RepositoryUtils.CheckPathMapping(scriptFile)

        JID = self.GetPluginInfoEntry("jid")
        job_type = self.GetJobInfoEntry("ExtraInfo0")
        
        arguments = self.GetPluginInfoEntryWithDefault("Arguments", "")
        arguments += " %s" % self.currentJob.JobId
        arguments += " %s" % job_type
        arguments = RepositoryUtils.CheckPathMapping(arguments)

        if SystemUtils.IsRunningOnWindows():
            scriptFile = scriptFile.replace("/", "\\")
        else:
            scriptFile = scriptFile.replace("\\", "/")

        return "-u \"" + scriptFile + "\" " + JID + arguments

    def ReplacePaddedFrame(self, arguments, pattern, frame):
        frameRegex = Regex(pattern)
        while True:
            frameMatch = frameRegex.Match(arguments)
            if frameMatch.Success:
                paddingSize = int(frameMatch.Groups[1].Value)
                if paddingSize > 0:
                    padding = StringUtils.ToZeroPaddedString(frame, paddingSize, False)
                else:
                    padding = str(frame)
                arguments = arguments.replace(frameMatch.Groups[0].Value, padding)
            else:
                break
        
        return arguments

    def HandleProgress( self ):
        progress = float( self.GetRegexMatch(1) )
        self.SetProgress( progress )

    def PreRenderTasks(self):
        self.LogInfo("Running PreRenderTasks")
        self.currentJob = self.GetJob()
        self.LogInfo("Current Job ID : %s" % self.currentJob.JobId)


    def PostRenderTasks(self):
        self.LogInfo("Running PostRenderTasks")
