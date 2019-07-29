from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return MetaRenderPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the MetaRender plugin.
######################################################################
class MetaRenderPlugin (DeadlinePlugin):
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
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( r"\[(#*)(\.*)\].*" ).HandleCallback += self.HandleRenderProgress
    
    def RenderExecutable( self ):
        exeList = self.GetConfigEntry( "MetaRender_Executable" )
        executable = FileUtils.SearchFileList( exeList )
        if( executable == "" ):
            self.FailRender( "MetaRender executable was not found in the semicolon separated list \"" + exeList + "\". The path to the executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return executable
    
    def RenderArgument( self ):
        inputFile = self.GetPluginInfoEntry( "InputFile" ).strip()
        inputFile = RepositoryUtils.CheckPathMapping( inputFile )
        if SystemUtils.IsRunningOnWindows():
            inputFile = inputFile.replace( "/", "\\" )
        else:
            inputFile = inputFile.replace( "\\", "/" )
        
        outputFile = self.GetPluginInfoEntry( "OutputFile" ).strip()
        outputFile = RepositoryUtils.CheckPathMapping( outputFile )
        if SystemUtils.IsRunningOnWindows():
            outputFile = outputFile.replace( "/", "\\" )
        else:
            outputFile = outputFile.replace( "\\", "/" )
        
        encodingFile = self.GetDataFilename()
        
        # Build the initial command line, including the additional core args.
        arguments = "\"" + outputFile + "\" \"" + encodingFile + "\" \"" + inputFile + "\""
        arguments += " " + self.GetPluginInfoEntryWithDefault( "CoreCommandLine", "" ).strip()
        
        # Figure out the rendering mode and add the necessary arguments.
        renderingMode = self.GetPluginInfoEntryWithDefault( "RenderingMode", "CPU" ).strip()
        if renderingMode == "GPU":
            arguments += " -gpu"
            if self.GetBooleanPluginInfoEntryWithDefault( "DraftMode", False ):
                arguments += " -draft"
                if self.GetBooleanPluginInfoEntryWithDefault( "CPUMasks", False ):
                    arguments += " -cpumasks"
        else:
            arguments += " -cpu -threads " + str(self.GetIntegerPluginInfoEntryWithDefault( "Threads", 1 ))
        
        # Check if we should strip the alpha channel from the render.
        if self.GetBooleanPluginInfoEntryWithDefault( "StripAlpha", False ):
            arguments += " -rgb"
        
        # Check if we are superimposing a burn-in template file.
        auxiliaryFilenames = self.GetAuxiliaryFilenames()
        if len(auxiliaryFilenames) > 1:
            burnFile = auxiliaryFilenames[0]
            arguments += " -burn \"" + burnFile + "\""
        
        # Check if we are writing out to a Flex file.
        if self.GetBooleanPluginInfoEntryWithDefault( "Flex", False ):
            arguments += " -flex"
            if self.GetBooleanPluginInfoEntryWithDefault( "Takes", False ):
                arguments += " -takes"
        
        # Finally add on the additional meta render args.
        arguments += " " + self.GetPluginInfoEntryWithDefault( "CommandLine", "" ).strip()
        
        return arguments
    
    def CheckExitCode( self, exitCode ):
        if exitCode != 0:
            if exitCode == -1:
                self.FailRender( "MetaRender returned an error code of -1, which could indicate that MetaRender could not find a valid license" )
            else:
                self.FailRender( "MetaRender returned a non-zero error code of %d" % exitCode )
    
    def HandleRenderProgress( self ):
        poundCount = float(len(self.GetRegexMatch(1)))
        dotCount = float(len(self.GetRegexMatch(2)))
        
        total = poundCount + dotCount
        if total > 0:
            progress = 100.0 * poundCount / total
            self.SetProgress( progress )
