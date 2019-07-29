
from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return MetaFuzePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class MetaFuzePlugin(DeadlinePlugin):
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
        self.singleFramesOnly=False
        self.StdoutHandling=True
        
        self.AddStdoutHandlerCallback( ".*[eE]rror.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( ".*[fF]ailed.*" ).HandleCallback += self.HandleFailed
    
    def RenderExecutable(self):
        metaFuzeExeList = self.GetConfigEntry("MetaFuze_RenderExecutable")
        metaFuzeExe = FileUtils.SearchFileList( metaFuzeExeList )
        
        if( metaFuzeExe == "" ):
            self.FailRender( "No file found in the semicolon separated list \"" + metaFuzeExeList+ "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return metaFuzeExe
    
    def RenderArgument(self):
        sceneFile = self.GetDataFilename()
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        
        return "\"" + sceneFile + "\""
    
    def HandleError( self ):
        self.LogInfo( "Error: an unknown error occurred." )
        self.FailRender( "An error occurred." )
    
    def HandleFailed( self ):
        self.LogInfo( "Error: image files could be missing." )
        self.FailRender( "An error occurred." )
