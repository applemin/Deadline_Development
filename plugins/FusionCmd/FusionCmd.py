import os

from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return FusionCmdPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
######################################################################
## This is the main DeadlinePlugin class for the FusionCmd plugin.
######################################################################
class FusionCmdPlugin (DeadlinePlugin):
    FusionRenderExecutable = ""
    Version = -1
    
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
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple

        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = False
        self.StdoutHandling = True
        self.ImmediateTermination = True
        self.HideDosWindow = False # This needs to be off so that we can get stdout from ConsoleSlave
        
        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( "Rendered frame [0-9]+ \\(([0-9]+) of ([0-9]+)\\).*" ).HandleCallback += self.HandleStdoutProgress
        self.AddStdoutHandlerCallback( "Auto-exiting with errcode ([0-9]+)" ).HandleCallback += self.HandleStdoutExiting
        self.AddStdoutHandlerCallback( "FLEXnet Licensing error" ).HandleCallback += self.HandleLicensingError
        self.AddStdoutHandlerCallback( "This version of .* has expired" ).HandleCallback += self.HandleLicensingError
        self.AddStdoutHandlerCallback( "SCRIPT ERROR:" ).HandleCallback += self.HandleLicensingError
        
        # Set the popup ignorers.
        #self.AddPopupIgnorer( ".*Queue.*" )
        #self.AddPopupIgnorer( ".*Render Manager.*" )
        
        # Set the popup handlers.
        #self.AddPopupHandler( ".*Exception Handler.*", "No" )
        #self.AddPopupHandler( ".*Fusion Render Slave.*", "Close" )
    
    ## Called by Deadline before the renderer starts.
    def PreRenderTasks( self ):
        # Get the version of Fusion we're rendering with.
        self.Version = int( self.GetFloatPluginInfoEntry( "Version" ) )
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        # Get the executable to be used for rendering.
        renderExecutableList = self.GetConfigEntry( "Fusion%dRenderExecutable" % self.Version )
        
        if(SystemUtils.IsRunningOnWindows()):
            if build == "32bit":
                self.FusionRenderExecutable = FileUtils.SearchFileListFor32Bit( renderExecutableList )
                if( self.FusionRenderExecutable == "" ):
                    self.LogWarning( "32 bit Fusion %d render executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % (self.Version, renderExecutableList) )
            elif build == "64bit":
                self.FusionRenderExecutable = FileUtils.SearchFileListFor64Bit( renderExecutableList )
                if( self.FusionRenderExecutable == "" ):
                    self.LogWarning( "64 bit Fusion %d render executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % (self.Version, renderExecutableList) )
            
        if( self.FusionRenderExecutable == "" ):
            self.FusionRenderExecutable = FileUtils.SearchFileList( renderExecutableList )
            if( self.FusionRenderExecutable == "" ):
                self.FailRender( "Fusion %d render executable could not be found in the semicolon separated list \"%s\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." % (self.Version, renderExecutableList) )
        
        # Get the global preference file, if there is one specified.
        preferenceFile = self.GetConfigEntry( "Fusion%dSlavePreferenceFile" % self.Version )
        if preferenceFile != "":
            # Perform path mapping on preference file (Fusion 8 and later only).
            if self.Version >= 8:
                preferenceFile = RepositoryUtils.CheckPathMapping( preferenceFile )
                preferenceFile = PathUtils.ToPlatformIndependentPath( preferenceFile )
            
            if( not File.Exists( preferenceFile ) ):
                self.FailRender( "Render Slave preference file \"%s\" does not exist. The path to the Render Slave preference file can be configured from the Plugin Configuration in the Deadline Monitor." % preferenceFile )
            
            # Version 5 and later just needs to set an environment variable.
            self.LogInfo( "Updating FUSION_MasterPrefs environment variable to point to Render Slave preference file \"%s\"" % preferenceFile )
            self.SetEnvironmentVariable( "FUSION_MasterPrefs", preferenceFile )
            self.LogInfo( "Render Slave preference file set successfully" )
        
    ## Called by Deadline to get the render executable.
    def RenderExecutable( self ):
        # Fusion 8 and later does not require wine.
        if( self.Version <= 7 and SystemUtils.IsRunningOnLinux() ):
            winePath = PathUtils.GetApplicationPath( "wine" )
            if winePath == "" or not File.Exists( winePath ):
                self.FailRender( "Wine could not be found in the path on this machine, it is required to run the Linux version of Fusion" )
            return winePath
        else:
            return self.FusionRenderExecutable
    
    ## Called by Deadline to get the render arguments.
    def RenderArgument( self ):
        renderArguments = ""
        
        # Fusion 8 and later does not require wine.
        if( self.Version <= 7 and SystemUtils.IsRunningOnLinux() ):
            renderArguments += "\"" + self.FusionRenderExecutable + "\" "
        
        sceneFilename = self.GetPluginInfoEntryWithDefault( "FlowFile", self.GetDataFilename() )
        sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename )
        sceneFilename = PathUtils.ToPlatformIndependentPath( sceneFilename )
        
        # Perform path mapping on contents of comp file if it's enabled (Fusion 8 and later only).
        if self.Version >= 8 and self.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
            tempSceneDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )            
            tempSceneFileName = Path.Combine( tempSceneDirectory, Path.GetFileName( sceneFilename ) )
            tempSceneFileName = PathUtils.ToPlatformIndependentPath( tempSceneFileName )
            self.pathMappingWithFilePermissionFix( sceneFilename, tempSceneFileName )
            sceneFilename = tempSceneFileName
        
        renderArguments += "\"" + sceneFilename + "\""
        renderArguments += " /render /start " + str( self.GetStartFrame() ) + " /end " + str( self.GetEndFrame() )
        renderArguments += " /step 1 /verbose /quiet /quietlicense /clean /quit"
        
        return renderArguments
    
    ## Called by Deadline to check the exit code from the renderer.
    def CheckExitCode( self, exitCode ):
        if exitCode != 0:
            if exitCode == 10:
                self.FailRender( "Renderer returned error code 10. There was a problem with rendering the comp (see the render log for details), or the process was interrupted by a CTRL-C signal." )
            elif exitCode == 20:
                self.FailRender( "Renderer returned error code 20. There was some problem with the startup - DLLs may be missing, or a problem with a plugin was encountered, or there was a problem obtaining a licence. Check the console slave's output." )
            elif exitCode != -1073741819:
                self.FailRender( "Renderer returned non-zero error code %d. Check the console slave's output." % exitCode )

    def HandleStdoutProgress( self ):
        self.SetProgress( (int(self.GetRegexMatch(1)) / int(self.GetRegexMatch(2))) * 100 )
    
    def HandleStdoutExiting( self ):
        exitCode = int( self.GetRegexMatch(1) )
        self.CheckExitCode( exitCode )
    
    def HandleLicensingError( self ):
        self.FailRender( self.GetRegexMatch(0) )
    
    def pathMappingWithFilePermissionFix( self, inFileName, outFileName ):        
        RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator( inFileName, outFileName, "\\", "/" )
        if SystemUtils.IsRunningOnLinux() or SystemUtils.IsRunningOnMac():
            os.chmod( outFileName, os.stat( inFileName ).st_mode )
