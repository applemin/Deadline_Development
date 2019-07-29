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
    return AutopanoVideoPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.cleanup()

######################################################################
## This is the main DeadlinePlugin class for the AutopanoVideo plugin.
######################################################################
class AutopanoVideoPlugin( DeadlinePlugin ):

    def __init__( self ):
        self.InitializeProcessCallback += self.initializeProcess
        self.RenderExecutableCallback += self.renderExecutable
        self.RenderArgumentCallback += self.renderArgument

    def cleanup( self ):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def initializeProcess( self ):
        self.PluginType = PluginType.Simple
        self.UseProcessTree = False
        self.SingleFramesOnly = True

    def renderExecutable( self ):
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        versionString = self.GetPluginInfoEntryWithDefault( "Version", "2" )

        self.LogInfo( "Rendering with Autopano Video version: %s" % versionString )
        
        executable = ""
        executableList = self.GetConfigEntry( "AutopanoVideo_Executable" + versionString )

        if(SystemUtils.IsRunningOnWindows()):
            if( build == "32bit" ):
                self.LogInfo( "Enforcing 32 bit build of Autopano Video" )
                executable = FileUtils.SearchFileListFor32Bit( executableList )
                if( executable == "" ):
                    self.LogWarning( "32 bit Autopano Video executable was not found in the semicolon separated list \"" + executableList + "\". Checking for any executable that exists instead." )
            
            elif( build == "64bit" ):
                self.LogInfo( "Enforcing 64 bit build of Autopano Video" )
                executable = FileUtils.SearchFileListFor64Bit( executableList )
                if( executable == "" ):
                    self.LogWarning( "64 bit Autopano Video executable was not found in the semicolon separated list \"" + executableList + "\". Checking for any executable that exists instead." )
            
        if( executable == "" ):
            self.LogInfo( "Not enforcing a build of Autopano Video" )
            executable = FileUtils.SearchFileList( executableList )
            if executable == "":
                self.FailRender( "Autopano Video executable was not found in the semicolon separated list \"" + executableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return executable

    def renderArgument( self ):
        kavaFile = self.GetPluginInfoEntryWithDefault( "KavaFile", "" )
        kavaFile = RepositoryUtils.CheckPathMapping( kavaFile )
        kavaFile = PathUtils.ToPlatformIndependentPath( kavaFile )

        if not os.path.isfile( kavaFile ):
            self.FailRender( "Kava file does not exist: %s" % kavaFile )

        arguments = "-batch \"" + kavaFile + "\""
        
        return arguments
