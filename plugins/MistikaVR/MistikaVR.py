import os

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return MistikaVRPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Mistika VR plugin.
######################################################################
class MistikaVRPlugin( DeadlinePlugin ):
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.CheckExitCodeCallback += self.CheckExitCode
        self.renderSize = -1
    
    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.CheckExitCodeCallback

    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.PluginType = PluginType.Simple
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        self.PopupHandling = True
        self.HandleQtPopups = True
        self.SetEnvironmentVariable( "QT_USE_NATIVE_WINDOWS", "1" )

        self.AddPopupIgnorer( "BackGround render of.*" )
        # this closes the popup for a license error
        self.AddPopupHandler( "vr", "[X]" )

        self.AddStdoutHandlerCallback( "render error:(.*)" ).HandleCallback += self.HandleRenderError
        self.AddStdoutHandlerCallback( "Check your license server for available licenses." ).HandleCallback += self.HandleLicenseError
        self.AddStdoutHandlerCallback( "^SIZE ([0-9]+)$" ).HandleCallback += self.HandleRenderSize
        self.AddStdoutHandlerCallback( "Waited [0-9]+ ms to write frame ([0-9]+).*" ).HandleCallback += self.HandleProgress
        self.AddStdoutHandlerCallback( "Done: ([0-9]+).*" ).HandleCallback += self.HandleProgress

    def RenderExecutable( self ):
        executableList = self.GetConfigEntry( "MistikaExecutable" )
        executable = FileUtils.SearchFileList( executableList )

        if not executable:
            self.FailRender( "Mistika VR render executable was not found in the semicolon separated list \"" + executableList + "\". The path to the Mistika VR render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return executable

    def HandlePathSeparators( self, filePath ):
        if os.name == "nt":
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
        
        # Path map the contents of the Mistika VR render file
        if self.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
            tempSceneDirectory = self.CreateTempDirectory( "thread" + str( self.GetThreadNumber() ) )
            tempSceneFile = os.path.join( tempSceneDirectory, os.path.basename( sceneFile ) )

            if os.name == "nt":
                RepositoryUtils.CheckPathMappingInFile( sceneFile, tempSceneFile )
            else:
                tempSceneFile = tempSceneFile.replace( "\\", "/" )
                RepositoryUtils.CheckPathMappingInFile( sceneFile, tempSceneFile )
                os.chmod( tempSceneFile, os.stat( sceneFile ).st_mode )

            sceneFile = tempSceneFile

        renderArguments = "-r \"" + sceneFile + "\" "

        startFrame = str( self.GetStartFrame() )
        endFrame = str( self.GetEndFrame() )

        renderArguments += "-s " + startFrame + " -e " + endFrame

        return renderArguments

    def CheckExitCode( self, exitCode ):
        # SGO previously used exit code 2 as a different way to signal a success, and will not be used for any error code in the future
        if exitCode not in ( 0, 2 ):
            self.FailRender( "Process exit code: %s" % exitCode )

    def HandleRenderError( self ):
        errorMessage = self.GetRegexMatch( 1 )
        self.FailRender( "Detected a render error: %s" % ( errorMessage.strip() ) )

    def HandleLicenseError( self ):
        self.FailRender( "Invalid Mistika VR license. %s" % self.GetRegexMatch( 0 ) )

    def HandleRenderSize( self ):
        self.renderSize = float( self.GetRegexMatch( 1 ) )

    def HandleProgress( self ):
        progress = 0
        # strip leading 0s so Python doesn't think the frame number is an octal
        currentFrame = int( self.GetRegexMatch( 1 ).lstrip( "0" ) )
        imageRender = self.GetBooleanPluginInfoEntry( "ImageRender" )

        if imageRender:
            framesCompletedInTask = currentFrame - self.GetStartFrame() + 1
            totalFrames = int( self.GetEndFrame() ) - int( self.GetStartFrame() ) + 1
            progress = float( framesCompletedInTask ) / float( totalFrames ) * 100
        else:
            if self.renderSize == -1:
                # callback to set renderSize hasn't kicked in yet
                return
            progress = float( currentFrame ) / self.renderSize * 100

        self.SetProgress( progress )
