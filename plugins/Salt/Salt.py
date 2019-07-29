import os
import sys

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return SaltPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class SaltPlugin (DeadlinePlugin):
    
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
        exeList = self.GetConfigEntry("Salt_exe")
        exe = FileUtils.SearchFileList(exeList)

        if exe == "":
            self.FailRender("Salt executable was not found in the semicolon separated list \"" + exeList + "\". The path to the executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return exe

    def RenderArgument( self ):
        args = " state.highstate"

        logging = self.GetPluginInfoEntry("Logging")
    
        args += " -l \"%s\"" % logging

        return args