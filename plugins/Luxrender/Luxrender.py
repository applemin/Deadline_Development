from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return LuxPlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()    

class LuxPlugin(DeadlinePlugin):
    frameCount=0
    finishedFrameCount=0
    
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
        self.PopupHandling=True
    
    def RenderExecutable(self):
        exeList = self.GetConfigEntry( "Luxrender_RenderExecutable" )
        exe = FileUtils.SearchFileList( exeList )
        if( exe == "" ):
            self.FailRender( "No luxrender.exe file found in the semicolon separated list \"" + exeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return exe
        
    def RenderArgument(self):
        threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if threads == 0:
            threads = Environment.ProcessorCount
        
        self.LogInfo( "Rendering with " + str(threads) +" thread(s)" )
        
        sceneFile = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        if SystemUtils.IsRunningOnWindows():
            sceneFile = sceneFile.replace( "/", "\\" )
        else:
            sceneFile = sceneFile.replace( "\\", "/" )
        
        return " -t " + str(threads) + " \"" + sceneFile + "\""
