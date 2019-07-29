import os
import sys

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return PuppetPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class PuppetPlugin (DeadlinePlugin):
    
    def __init__( self ):
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
        self.SingleFramesOnly = True
        
    
    def RenderExecutable( self ):
        exeList = self.GetConfigEntry("Puppet_Batch")
        exe = FileUtils.SearchFileList(exeList)

        if exe == "":
            self.FailRender("Puppet executable file was not found in the semicolon separated list \"" + exeList + "\". The path to the executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return exe

    def RenderArgument( self ):
        args = "agent -t"

        verbose = self.GetBooleanPluginInfoEntryWithDefault("Verbose", False)
        if verbose:
            args += " --verbose"

        return args