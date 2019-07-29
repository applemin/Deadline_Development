from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return ShakePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Shake plugin.
######################################################################
class ShakePlugin(DeadlinePlugin):
    FrameStatus = ""
    
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
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        
        # Set the process specific settings.
        self.StdoutHandling = True
        self.PopupHandling = True
        
        self.AddStdoutHandlerCallback( "info: frame ([0-9]+) rendered in" ).HandleCallback += self.HandleProgress
        self.AddStdoutHandlerCallback( "info: rendering frame [0-9]+" ).HandleCallback += self.HandleRenderingFrame
        self.AddStdoutHandlerCallback( "info: processing: [0-9]+" ).HandleCallback += self.HandleProcessing
    
    def RenderExecutable(self):
        shakeExeList = self.GetConfigEntry( "Shake_RenderExecutable" )
        shakeExe = FileUtils.SearchFileList( shakeExeList )
        if( shakeExe == "" ):
            self.FailRender( "Shake executable was not found in the semicolon separated list \"" + shakeExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return shakeExe
    
    def RenderArgument(self):
        sceneFile = self.GetPluginInfoEntryWithDefault( "SceneFile" , self.GetDataFilename())
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        
        arguments = " -exec \"" + sceneFile + "\""
        arguments += "  -vv -t " + str(self.GetStartFrame()) + "-" + str(self.GetEndFrame())
        arguments += " -cpus " + self.GetPluginInfoEntryWithDefault( "Threads", "1" )
        arguments += " " + self.GetPluginInfoEntryWithDefault( "CommandLineOptions", "" )
        return arguments
    
    def HandleProgress(self):
        finishedFrame = float(self.GetRegexMatch(1))
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if( endFrame - startFrame + 1 != 0 ):
            progress = 100.0 * ( (finishedFrame - float(startFrame) + 1.0) / ( float(endFrame) - float(startFrame) + 1.0) )
            self.SetProgress( progress )
    
    def HandleRenderingFrame(self):
        self.FrameStatus = self.GetRegexMatch(0)
    
    def HandleProcessing(self):
        message = self.GetRegexMatch(0)
        if self.FrameStatus != "":
            message = self.FrameStatus + ": " + message
        self.SetStatusMessage( message )
