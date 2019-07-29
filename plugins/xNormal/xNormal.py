from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return xNormalPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class xNormalPlugin(DeadlinePlugin):
    frameCount=0
    finishedFrameCount=0
    
    def __init__(self):
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.CheckExitCodeCallback += self.CheckExitCode
    
    def InitializeProcess(self):
        self.singleFramesOnly=True
        self.StdoutHandling=False
        self.PopupHandling=True
    
    def RenderExecutable(self):
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        executable = ""
        executableList = self.GetConfigEntry( "xNormal_RenderExecutable" )
        
        if SystemUtils.IsRunningOnWindows():
            if( build == "32bit" ):
                self.LogInfo( "Enforcing 32 bit build of xNormal" )
                executable = FileUtils.SearchFileListFor32Bit( executableList )
                if( executable == "" ):
                    self.LogWarning( "32 bit xNormal render executable was not found in the semicolon separated list \"" + executableList + "\". Checking for any executable that exists instead." )
            
            elif( build == "64bit" ):
                self.LogInfo( "Enforcing 64 bit build of xNormal" )
                executable = FileUtils.SearchFileListFor64Bit( executableList )
                if( executable == "" ):
                    self.LogWarning( "64 bit xNormal render executable was not found in the semicolon separated list \"" + executableList + "\". Checking for any executable that exists instead." )
            
        if( executable == "" ):
            self.LogInfo( "Not enforcing a build of xNormal" )
            executable = FileUtils.SearchFileList( executableList )
            if executable == "":
                self.FailRender( "xNormal render executable was not found in the semicolon separated list \"" + executableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return executable
        
    def RenderArgument(self):
        frameNumber = self.GetStartFrame()
        sceneFile = self.GetPluginInfoEntryWithDefault("File" + str(frameNumber), "")
        if(sceneFile == ""):
            sceneFile = self.GetAuxiliaryFilenames()[frameNumber]
        
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        
        if(not Path.IsPathRooted(sceneFile)):
            sceneFile = Path.Combine(self.GetJobsDataDirectory(), sceneFile)
        
        renderArgument = '"' + sceneFile + '"'
        
        return renderArgument
    
    def CheckExitCode( self, exitCode ):
        if exitCode != 0:
            self.FailRender( "Renderer returned non-zero error code %d. Check the renderer's output." % exitCode )
