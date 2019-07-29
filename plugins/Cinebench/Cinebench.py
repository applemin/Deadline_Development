from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

import os

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return CinebenchPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class CinebenchPlugin( DeadlinePlugin ):
        
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
    
    def InitializeProcess( self ):
        self.SingleFramesOnly = True
        self.StdoutHandling = False
        self.PopupHandling = False
        
    def RenderExecutable( self ):
        version = self.GetPluginInfoEntryWithDefault( "Version", "15" )
        
        cinebenchExe = ""
        cinebenchExeList = self.GetConfigEntry( "RenderExecutable_" + version )
         
        cinebenchExe = FileUtils.SearchFileList( cinebenchExeList )
        if( cinebenchExe == "" ):
            self.FailRender( "Cinebench render (" + cinebenchExe + ") executable could not be found in the semicolon separated list \"%s\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." % cinebenchExeList )
        
        if(SystemUtils.IsRunningOnWindows()):
            cinebenchExe = cinebenchExe.replace( "/", "\\" )#This is required otherwise Cinebench will be unable to locate it's resources folder.
        else:
            cinebenchExe = cinebenchExe.replace( "\\", "/" )
        
        return cinebenchExe

    def RenderArgument( self ):
        doSingleCore = self.GetBooleanPluginInfoEntryWithDefault( "SingleCoreTest", False )
        doMultiCore = self.GetBooleanPluginInfoEntryWithDefault( "MultiCoreTest", False )
        doOpenGL = self.GetBooleanPluginInfoEntryWithDefault( "OpenglCoreTest", False )

        if not ( doSingleCore or doMultiCore or doOpenGL ):
            self.FailRender( "No test procedures defined." ) 

        arguments = ""
        if doSingleCore:
            arguments += " -cb_cpu1"

        if doMultiCore:
            arguments += " -cb_cpux"

        if doOpenGL:
            arguments += " -cb_opengl"

        return arguments
