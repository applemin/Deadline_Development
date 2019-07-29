from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.Diagnostics import *
from System.Text.RegularExpressions import *

from Deadline.Scripting import *
from Deadline.Plugins import *

import os

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return CoronaPlugin()
    
######################################################################
## This is the function that Deadline calls to clean up any
## resources held by the Plugin.
######################################################################
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Corona plugin.
######################################################################
class CoronaPlugin( DeadlinePlugin ):
    DEFAULT_CORONA_VERSION = "1.4"

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
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        self.PopupHandling = True
        
        self.AddStdoutHandlerCallback( "(Error: .*)" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "Pass ([0-9]+)\/([0-9]+)" ).HandleCallback += self.HandleProgress

    @property
    def CoronaStringVersion(self):
        """
        A string representation of the dotted version number of Corona to use for the render job (e.g. "1.4")

        This is obtained from the "Version" plugin info entry with a default fallback to "1.4"

        :return: A string representation of the Corona version to use for the render job
        """
        return self.GetPluginInfoEntryWithDefault( "Version", self.DEFAULT_CORONA_VERSION )

    @property
    def CoronaVersion(self):
        """
        A tuple of ints representing the components of the version number. This is a good way to represent semantic
        version numbers since they respect lexicographic ordering when comparing two such tuples.

        The value is obtained from the "Version" plugin info entry with a default fallback value of (1, 4).

        :return: A tuple of ints representing the version number of Corona to be used for the render job
        """
        return tuple( int(part) for part in self.CoronaStringVersion.split('.') )
        
    def HandleStdoutError( self ):
        self.FailRender( self.GetRegexMatch(0) )

    def HandleProgress( self ):
        msg = "Corona Rendering: Pass %s/%s" % ( self.GetRegexMatch(1), self.GetRegexMatch(2) )
        self.SetStatusMessage( msg )

        #Single frame render progress.
        if self.GetEndFrame() - self.GetStartFrame() == 0:
            progress = float(self.GetRegexMatch(1)) / float(self.GetRegexMatch(2))
            progress = progress * 100.0
            self.SetProgress( progress )

    def RenderExecutable( self ):
        """
        A function that determines which executable to invoke for the Corona render job. This uses the Corona version
        specified in the job's plugin info submission parameter. The corresponding list of candidate render executables
        from the Corona plugin settings is scanned in order and the first one found is returned.

        :return: A string containing the path to the render executable to use for the current job.
        """

        versionKey = self.CoronaStringVersion.replace(".", "_")
        configKey = "CoronaRenderExecutable" + versionKey
        coronaExeList = self.GetConfigEntry( configKey )

        coronaExe = FileUtils.SearchFileList( coronaExeList )
        if coronaExe == "":
            self.FailRender( "Corona %s render executable could not be found in the semicolon separated "
                             "list \"%s\". The path to the render executable can be configured from the Plugin "
                             "Configuration in the Deadline Monitor." % ( self.CoronaStringVersion, coronaExeList ) )
        
        return coronaExe
        
    def RenderArgument( self ):
        """
        A function that determines what command-line arguments will be passed to the render executable. This list of
        arguments is determined based on the job submission parameters.

        This function has the side-effect of generating a temporary directory and config file. The path to this config
        file is passed as part of the command-line arguments.

        :return: A string containing the command-line arguments to pass to the render executable.
        """

        #Get the scene file.
        scene = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
        scene = RepositoryUtils.CheckPathMapping( scene )
        
        #Get the output file.
        outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" )
        outputFile = RepositoryUtils.CheckPathMapping( outputFile )
        
        singleFrame = self.GetBooleanPluginInfoEntryWithDefault( "SingleFrame", False )
        filename = scene
        if not singleFrame:
            currPadding = FrameUtils.GetFrameStringFromFilename( filename )
            paddingSize = len( currPadding )
            newPadding = StringUtils.ToZeroPaddedString( self.GetStartFrame(), paddingSize, False )
            filename = FrameUtils.SubstituteFrameNumber( filename, newPadding )
            currPadding = FrameUtils.GetFrameStringFromFilename( filename )
            outputFile = outputFile + currPadding

        arguments = "\"" + filename + "\""

        if outputFile != "":
            if self.CoronaVersion >= (1, 5):
                alpha = self.GetBooleanPluginInfoEntryWithDefault( "OutputAlpha", False )
                raw = self.GetBooleanPluginInfoEntryWithDefault( "OutputRaw", False )
                
                outputArgs = " -o"
                
                if alpha:
                    outputArgs += "A"
                if raw:
                    outputArgs += "R"

                arguments += outputArgs + " \"" + outputFile + "\""
            else:
                arguments += " \"" + outputFile + "\""
        
        #Get the configuration files.
        configFiles = self.GetPluginInfoEntryWithDefault( "ConfigFiles", "" )
        cFiles = []
        configFiles = configFiles.split(",")
        for configFile in configFiles:
            cFiles.append(RepositoryUtils.CheckPathMapping( configFile ))
           
        configurationFileName = ""
        for cFile in cFiles:
            if cFile != "" and cFile != None:
                configurationFileName = configurationFileName + " \"" + cFile + "\""

        #Write the additional args to a config file.
        tempDir = self.CreateTempDirectory("corona_render")
        deadlineConfig = Path.Combine( tempDir, "argument.conf" )
        
        writer = StreamWriter( deadlineConfig, False, Encoding.ASCII )

        if self.CoronaVersion == (1, 4):
            writer.Write( "int vfb.type = 0\n" )
        
        #Check if we are overwriting passes.
        if self.GetBooleanPluginInfoEntryWithDefault( "OverridePasses", False ):
            passes = self.GetIntegerPluginInfoEntryWithDefault( "MaxPasses", 0 )
            if self.CoronaVersion == (1, 4):
                writer.Write( "int progressive.maxPasses = " + str(passes) + "\n" )
            elif self.CoronaVersion >= (1, 5):
                writer.Write( "int progressive.passLimit = " + str(passes) + "\n" )
            else:
                self.LogWarning( "Unable to override max pass limit" )
            
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideRenderTime", False ):
            hours = ( self.GetIntegerPluginInfoEntryWithDefault( "RenderHourTime", 0 )*60*60 )
            minutes = ( self.GetIntegerPluginInfoEntryWithDefault( "RenderMinuteTime", 0 )*60 )
            seconds = self.GetIntegerPluginInfoEntryWithDefault( "RenderSecTime", 0 )
            #time is declared in milliseconds, so multiply by 1000.
            time = (hours+minutes+seconds)*1000
            writer.Write( "int progressive.timeLimit = " + str(time) + "\n" )

        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideThreads", False ):
            threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
            if self.CoronaVersion == (1, 4):
                writer.Write( "int numThreads = " + str(threads) + "\n" )
            elif self.CoronaVersion >= (1, 5):
                writer.Write( "int system.numThreads = " + str(threads) + "\n" )
            else:
                self.LogWarning( "Unable to override threads" )
        
        writer.Close()
        
        #Appends the deadline configuration file to the end of the configuration list so that it's settings get precedence.
        if len(configurationFileName) == 0:
            configurationFileName = " \"" + deadlineConfig + "\""
        else:
            configurationFileName = " " + configurationFileName + " \"" + deadlineConfig + "\""

        arguments += " -c" + configurationFileName

        if self.CoronaVersion >= (1, 5):
            arguments += " -silent"

        #Corona.exe scene.scn [-o output.jpg] [-oAR output.exr] [-c file.conf] [-silent]
        return arguments
