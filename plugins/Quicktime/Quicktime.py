from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return QuicktimePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Quicktime plugin.
######################################################################
class QuicktimePlugin (DeadlinePlugin):
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.CheckExitCodeCallback += self.CheckExitCode
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.CheckExitCodeCallback
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple
    
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( "Error:.*" ).HandleCallback += self.HandleRenderTasksError
        self.AddStdoutHandlerCallback( "Progress: ([0-9]+\.*[0-9]*)" ).HandleCallback += self.HandleRenderTasksProgress
    
    def RenderExecutable( self ):
        if SystemUtils.IsRunningOnMac():
            generatorExe = Path.Combine( ClientUtils.GetBinDirectory(), "deadlinequicktimegenerator" )
        else:
            generatorExe = Path.Combine( ClientUtils.GetBinDirectory(), "deadlinequicktimegenerator.exe" )
        
        return generatorExe
    
    def RenderArgument( self ):
        # Read in settings from plugin info file.
        inputImages = self.GetPluginInfoEntry( "InputImages" ).strip()
        inputImages = RepositoryUtils.CheckPathMapping( inputImages )
        if SystemUtils.IsRunningOnWindows():
            inputImages = inputImages.replace( "/", "\\" )
            if inputImages.startswith( "\\" ) and not inputImages.startswith( "\\\\" ):
                inputImages = "\\" + inputImages
        else:
            inputImages = inputImages.replace( "\\", "/" )
        
        outputFile = self.GetPluginInfoEntry( "OutputFile" ).strip()
        outputFile = RepositoryUtils.CheckPathMapping( outputFile )
        if SystemUtils.IsRunningOnWindows():
            outputFile = outputFile.replace( "/", "\\" )
            if outputFile.startswith( "\\" ) and not outputFile.startswith( "\\\\" ):
                outputFile = "\\" + outputFile
        else:
            outputFile = outputFile.replace( "\\", "/" )
        
        audioFile = self.GetPluginInfoEntryWithDefault( "AudioFile", "" ).strip()
        audioFile = RepositoryUtils.CheckPathMapping( audioFile )
        if SystemUtils.IsRunningOnWindows():
            audioFile = audioFile.replace( "/", "\\" )
            if audioFile.startswith( "\\" ) and not audioFile.startswith( "\\\\" ):
                audioFile = "\\" + audioFile
        else:
            audioFile = audioFile.replace( "\\", "/" )
        
        frameRate = self.GetPluginInfoEntry( "FrameRate" )
        codec = self.GetPluginInfoEntryWithDefault( "Codec", "QuickTime Movie" )
        
        # Build the render arguments.
        renderArguments = ""
        if len( audioFile ) > 0:
            renderArguments = "-CreateMovieWithAudio \"" + inputImages + "\" \"" + audioFile + "\""
        else:
            renderArguments = "-CreateMovie \"" + inputImages + "\""
        
        # Figure out wich OS the settings file was created on, and fail the job if it's from the wrong OS.
        settingsFile = self.GetDataFilename()
        if settingsFile == None:
            self.FailRender( "No Quicktime settings file was submitted with the job." )
        settings = File.ReadAllLines( settingsFile )
        
        settingsFromWindows = False
        if len( settings ) > 0 and settings[0].find( "<?xml" ) >= 0:
            settingsFromWindows = True
        
        if SystemUtils.IsRunningOnWindows() and not settingsFromWindows:
            self.FailRender( "The Quicktime settings file submitted with this job (" + Path.GetFileName( settingsFile ) + ") was created on OSX, so it cannot render on a Windows machine." )
        if SystemUtils.IsRunningOnMac() and settingsFromWindows:
            self.FailRender( "The Quicktime settings file submitted with this job (" + Path.GetFileName( settingsFile ) + ") was created on Windows, so it cannot render on an OSX machine." )
        
        renderArguments += " \"" + settingsFile + "\" \"" + codec + "\""
        renderArguments += " " + str(self.GetStartFrame()) + " " + str(self.GetEndFrame())
        renderArguments += " " + frameRate + " \"" + outputFile + "\""
        
        return renderArguments
    
    def CheckExitCode( self, exitCode ):
        if exitCode != 0 and exitCode != 128:
            self.FailRender( "DeadlineQuicktimeGenerator returned a non-zero error code of %d" % exitCode )
    
    def HandleRenderTasksError( self ):
        self.FailRender( self.GetRegexMatch(0) )
    
    def HandleRenderTasksProgress( self ):
        self.SetProgress( float(self.GetRegexMatch(1)) )
        #self.SuppressThisLine()
