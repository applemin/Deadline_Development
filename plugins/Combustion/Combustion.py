from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return CombustionPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Combustion plugin.
######################################################################
class CombustionPlugin (DeadlinePlugin):
    TempSceneFilename = ""
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.CheckExitCodeCallback += self.CheckExitCode
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.CheckExitCodeCallback
    
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple
        
        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        # Removed for now do to some issues (not sure why they occur though)
        #self.PopupHandling = True
        
        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( ".*ERROR:.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( ".*Footage not found:.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( ".*Done frame ([0-9]+) of ([0-9]+).*" ).HandleCallback += self.HandleProgress
    
    def PreRenderTasks( self ):
        sceneFilename = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
        sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename )
        sceneFileLines = File.ReadAllLines( sceneFilename, Encoding.Default )
        
        # Attempt path replacement on every line in the file.
        for i in range(0,len(sceneFileLines)):
            tempSceneFileLine = RepositoryUtils.CheckPathMapping( sceneFileLines[i] )
            if tempSceneFileLine != sceneFileLines[i]:
                tempSceneFileLine = tempSceneFileLine.replace( "/", "\\" )
                sceneFileLines[i] = tempSceneFileLine
        
        #self.TempSceneFilename = Path.Combine( Path.GetTempPath(), Path.GetFileName( sceneFilename ) )
        self.TempSceneFilename = Path.Combine( Path.GetTempPath(), Path.GetFileNameWithoutExtension( sceneFilename ) + "_" + str(self.GetThreadNumber()) + Path.GetExtension( sceneFilename ) )
        
        File.WriteAllLines( self.TempSceneFilename, sceneFileLines, Encoding.Default )
    
    def RenderExecutable( self ):
        version = self.GetIntegerPluginInfoEntryWithDefault( "Version", 2008 )
        combExeList = self.GetConfigEntry( "RenderExecutable" + str(version) )
        combExe = FileUtils.SearchFileList( combExeList )
        if( combExe == "" ):
            self.FailRender( "Combustion " + str(version) + " render executable was not found in the semicolon separated list \"" + combExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return combExe
    
    def RenderArgument( self ):
        renderarguments = ""
        
        renderarguments += " -nobar -start " + str(self.GetStartFrame()) + " -end " + str(self.GetEndFrame())
        renderarguments += " -startnumber " + str(self.GetStartFrame()) + " -skip 1"
        renderarguments += " -output \"" + self.GetPluginInfoEntry( "OutputOperator" ) + "\""
        
        renderarguments += StringUtils.BlankIfEitherIsBlank( " -quality ", self.GetPluginInfoEntryWithDefault( "Quality", "" ).strip() )
        renderarguments += StringUtils.BlankIfEitherIsBlank( " -depth ", self.GetPluginInfoEntryWithDefault( "BitDepth", "" ).strip() )
        
        frameSize = self.GetPluginInfoEntryWithDefault( "FrameSize", "" ).strip().lower()
        if frameSize != "":
            # If frame size is custom, we need to include the custom resolution.
            if frameSize == "custom":
                renderarguments += StringUtils.BlankIfEitherIsBlank( " -width ", self.GetPluginInfoEntryWithDefault( "CustomWidth", "" ).strip() )
                renderarguments += StringUtils.BlankIfEitherIsBlank( " -height ", self.GetPluginInfoEntryWithDefault( "CustomHeight", "" ).strip() )
                if self.GetBooleanPluginInfoEntryWithDefault( "LockAspect", False ):
                    renderarguments += " -lockaspect"
            else:
                renderarguments += " -framesize " + frameSize
        
        if self.GetBooleanPluginInfoEntryWithDefault( "SkipExistingFrames", False ):
            renderarguments += " -skipexisting"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "UseSingleCpu", False ):
            renderarguments += " -singlecpu"
        
        renderarguments += " \"" + self.TempSceneFilename + "\""
        
        return renderarguments
    
    def CheckExitCode( self, exitCode ):
        if exitCode != 0 and exitCode != 139:
            self.FailRender( "Renderer returned non-zero error code, %s" % exitCode )
    
    def HandleError( self ):
        self.FailRender( self.GetRegexMatch( 0 ) )
    
    def HandleProgress( self ):
        currFrame = float( self.GetRegexMatch( 1 ) ) - 1
        totalFrames = self.GetEndFrame() - self.GetStartFrame() + 1
        if currFrame > 0 and totalFrames != 0:
            self.SetProgress( ( currFrame / float( totalFrames ) ) * 100.0 )
