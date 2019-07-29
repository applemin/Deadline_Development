import os

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return SilhouettePlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class SilhouettePlugin( DeadlinePlugin ):

    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument

    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess( self ):
        self.PluginType = PluginType.Simple
        self.StdoutHandling = True
        self.PopupHandling = True
        
        self.version = int( self.GetPluginInfoEntryWithDefault( "Version", "5" ) )
        
        self.AddStdoutHandlerCallback( r".*\(([0-9]+)%\).*" ).HandleCallback += self.HandleStdoutProgress

    def RenderExecutable( self ):
        exe = ""
        exeList = self.GetConfigEntry( "Silhouette_RenderExecutable_" + str(self.version) )
        exe = FileUtils.SearchFileList( exeList )
        if( exe == "" ):
            self.FailRender( "Silhouette render executable was not found in the configured separated list \"" + exeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return exe

    def HandlePathSeparators( self, filePath ):
        if SystemUtils.IsRunningOnWindows():
            filePath = filePath.replace( "/", "\\" )
            if filePath.startswith( "\\" ) and not filePath.startswith( "\\\\" ):
                filePath = "\\" + filePath
        else:
            filePath = filePath.replace( "\\", "/" )

        return filePath

    def RenderArgument( self ):
        sceneFile = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        sceneFile = self.HandlePathSeparators( sceneFile )
        
        # Path map the contents of the Silhouette FX project file called "project.sfx"
        if self.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
            tempSceneDirectory = self.CreateTempDirectory( "thread" + str( self.GetThreadNumber() ) )
            tempSceneFile = Path.Combine( tempSceneDirectory, Path.GetFileName( sceneFile ) )

            if SystemUtils.IsRunningOnWindows():
                RepositoryUtils.CheckPathMappingInFile( sceneFile, tempSceneFile )
            else:
                tempSceneFile = tempSceneFile.replace( "\\", "/" )
                RepositoryUtils.CheckPathMappingInFile( sceneFile, tempSceneFile )
                os.chmod( tempSceneFile, os.stat( sceneFile ).st_mode )

            sceneFile = tempSceneFile

        renderArguments = "\"" + sceneFile + "\" "

        renderArguments += "-log "
        
        # Check if we are running a Python script.
        runScript = self.GetBooleanPluginInfoEntryWithDefault( "RunScript", False )
        if runScript:
            
            scriptFile = self.GetPluginInfoEntryWithDefault( "ScriptFile", "" )
            
            if not Path.IsPathRooted( scriptFile ):
                scriptFile = Path.Combine( self.GetJobsDataDirectory(), scriptFile )
            else:
                scriptFile = RepositoryUtils.CheckPathMapping( scriptFile )
                scriptFile = self.HandlePathSeparators( scriptFile )

            if( not File.Exists( scriptFile ) ):
                self.FailRender( "Python Script File is missing: %s" % scriptFile )
            
            self.LogInfo( "Python Script to be executed: \"%s\"" % scriptFile )

            renderArguments += "-script \"%s\" " % scriptFile

            disableRender = self.GetBooleanPluginInfoEntryWithDefault( "DisableRender", False )
            if disableRender:
                renderArguments += "-render 0 "

        resolution = self.GetPluginInfoEntryWithDefault( "Resolution", "full" )
        renderArguments += "-resolution %s " % resolution

        fields = self.GetPluginInfoEntryWithDefault( "Fields", "none" )
        renderArguments += "-fields %s " % fields

        if fields != "none":
            dominance = self.GetPluginInfoEntryWithDefault( "Dominance", "even" )
            renderArguments += "-dominance %s " % dominance

        session = self.GetPluginInfoEntryWithDefault( "Session", "" )
        if not session == "":
            #For whatever reason session requires a = while every other command does not
            renderArguments += "-session=%s " % session
        
        node = self.GetPluginInfoEntryWithDefault( "Node", "" )
        if not node == "":
            renderArguments += "-node %s " % node
            
        if self.version < 6:
            outputDirectory = self.GetPluginInfoEntryWithDefault( "OutputDirectory", "" )
            if not outputDirectory == "":
                outputDirectory = RepositoryUtils.CheckPathMapping( outputDirectory )
                outputDirectory = self.HandlePathSeparators( outputDirectory )
                # remove trailing slash if present
                outputDirectory = outputDirectory.rstrip("/\\")
                renderArguments += "-dir \"%s\" " % outputDirectory
                
            outputFilename = self.GetPluginInfoEntryWithDefault( "OutputFilename", "" )
            if not outputFilename == "":
                renderArguments += "-file %s " % outputFilename
            
            outputFormat = self.GetPluginInfoEntryWithDefault( "OutputFormat", "" )
            if not outputFormat == "":
                renderArguments += "-format %s " % outputFormat
        
        startFrame = str( self.GetStartFrame() )
        endFrame = str( self.GetEndFrame() )
        
        renderArguments += "-range %s-%s " % ( startFrame, endFrame )
        if self.version > 5:
            renderArguments += "-start %s " % startFrame
            
        renderArguments += "%s" % self.GetPluginInfoEntryWithDefault( "AdditionalOptions", "" )
        
        return renderArguments

    def HandleStdoutProgress( self ):
        self.SetProgress( float( self.GetRegexMatch( 1 ) ) )
        self.SetStatusMessage( self.GetRegexMatch( 0 ) )
