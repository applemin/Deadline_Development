from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

import os

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return ArnoldPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class ArnoldPlugin( DeadlinePlugin ):
    
    LocalRendering = False
    NetworkFilePath = ""
    LocalFilePath = ""
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PostRenderTasksCallback += self.PostRenderTasks
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PostRenderTasksCallback
    
    def InitializeProcess( self ):
        self.SingleFramesOnly = True
        self.StdoutHandling = True
        self.PopupHandling = True
        
        self.AddStdoutHandlerCallback( ".*ERROR +\\|.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "([0-9]+)% done" ).HandleCallback += self.HandleProgress

    def RenderExecutable( self ):
        version = self.GetPluginInfoEntryWithDefault( "Version", "Release" )
        
        arnoldExe = ""
        arnoldExeList = self.GetConfigEntry( "Arnold_RenderExecutable_" + version )
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
         
        if(SystemUtils.IsRunningOnWindows()):
            if build == "32bit":
                arnoldExe = FileUtils.SearchFileListFor32Bit( arnoldExeList )
                if( arnoldExe == "" ):
                    self.LogWarning( "32 bit Arnold (" + version + ") render executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % arnoldExeList)
            elif build == "64bit":
                arnoldExe = FileUtils.SearchFileListFor64Bit( arnoldExeList )
                if( arnoldExe == "" ):
                    self.LogWarning( "64 bit Arnold (" + version + ") render executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % arnoldExeList)
            
        if( arnoldExe == "" ):
            arnoldExe = FileUtils.SearchFileList( arnoldExeList )
            if( arnoldExe == "" ):
                self.FailRender( "Arnold render (" + version + ") executable could not be found in the semicolon separated list \"%s\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." % arnoldExeList )
        
        return arnoldExe

    def RenderArgument( self ):
        # Disable the render window (-dw), disable progressive mode to speed renders up by 10% (-dp) and disable crash popups to avoid user interaction.
        arguments = "-nstdin -dw -dp"
        if SystemUtils.IsRunningOnWindows():
            arguments += " -nocrashpopup"

        # Get the input .ass file and swap out the frame number.
        filename = self.GetPluginInfoEntry( "InputFile" )
        filename = RepositoryUtils.CheckPathMapping( filename )
        filename = self.FixPath( filename )
        
        paddingSize = 0
        if not self.GetBooleanPluginInfoEntryWithDefault( "DisableFrameInterpretation", False ):
            currPadding = FrameUtils.GetFrameStringFromFilename( filename )
            paddingSize = len( currPadding )
        
        if not self.GetBooleanPluginInfoEntryWithDefault( "SingleAss", False ):
            if paddingSize > 0:
                newPadding = StringUtils.ToZeroPaddedString( self.GetStartFrame(), paddingSize, False )
                filename = FrameUtils.SubstituteFrameNumber( filename, newPadding )
        else:
            if paddingSize > 0:
                newPadding = StringUtils.ToZeroPaddedString( self.GetPluginInfoEntryWithDefault( "SingleRegionFrame", "" ), paddingSize, False )
                filename = FrameUtils.SubstituteFrameNumber( filename, newPadding )
        
        # Check if we should be doing path mapping on the contents of the .ass file.
        if self.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
            localDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
            localFilename = Path.Combine( localDirectory, Path.GetFileName( filename ) )

            # The .ass files need the paths to use '/' as the separator.
            RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator( filename, localFilename, "\\", "/" )
            if SystemUtils.IsRunningOnLinux() or SystemUtils.IsRunningOnMac():
                os.chmod( localFilename, os.stat( filename ).st_mode )
            filename = localFilename
        
        arguments += " -i \"" + filename + "\""
        regionJob = self.GetBooleanPluginInfoEntryWithDefault( "RegionJob", False )
        
        self.LocalRendering = False
        singleAss = self.GetBooleanPluginInfoEntryWithDefault( "SingleAss", False )
        if not singleAss:
            if regionJob:
                outputFile = self.GetPluginInfoEntryWithDefault( "RegionFilename"+str(self.GetStartFrame()), "" ).strip()
            else:
                outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip()
            if len(outputFile) > 0:
                outputFile = RepositoryUtils.CheckPathMapping( outputFile )
                outputFile = self.FixPath( outputFile )
                if not regionJob:
                    if paddingSize > 0:
                        outputPath = Path.GetDirectoryName( outputFile )
                        outputFileName = Path.GetFileNameWithoutExtension( outputFile )
                        outputExtension = Path.GetExtension( outputFile )
                        
                        newPadding = StringUtils.ToZeroPaddedString( self.GetStartFrame(), paddingSize, False )
                        outputFile = Path.Combine( outputPath, outputFileName + newPadding + outputExtension )
                
                self.LocalRendering = self.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False )
                if self.LocalRendering:
                    outputDir = Path.GetDirectoryName( outputFile )
                    self.NetworkFilePath = outputDir
                    
                    outputDir = self.CreateTempDirectory( "ArnoldOutput" )
                    self.LocalFilePath = outputDir
                    
                    outputFile = Path.Combine( outputDir, Path.GetFileName( outputFile ) )
                    
                    self.LogInfo( "Rendering to local drive, will copy files and folders to final location after render is complete" )
                else:
                    self.LogInfo( "Rendering to network drive" )
                
                arguments += " -o \"" + outputFile + "\""
        else:
            outputFile = self.GetPluginInfoEntryWithDefault( "RegionFilename"+self.GetCurrentTaskId(), "" ).strip()
            if len(outputFile) > 0:
                outputFile = RepositoryUtils.CheckPathMapping( outputFile )
                outputFile = self.FixPath( outputFile )
                
                self.LocalRendering = self.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False )
                if self.LocalRendering:
                    outputDir = Path.GetDirectoryName( outputFile )
                    self.NetworkFilePath = outputDir
                    
                    outputDir = self.CreateTempDirectory( "ArnoldOutput" )
                    self.LocalFilePath = outputDir
                    
                    outputFile = Path.Combine( outputDir, Path.GetFileName( outputFile ) )
                    
                    self.LogInfo( "Rendering to local drive, will copy files and folders to final location after render is complete" )
                else:
                    self.LogInfo( "Rendering to network drive" )
                
                arguments += " -o \"" + outputFile + "\""
        
        
        if regionJob:
            left = "0"
            right = "0"
            top = "0"
            bot = "0"
            if singleAss:
                left = self.GetPluginInfoEntryWithDefault( "RegionLeft"+self.GetCurrentTaskId(), "0" )
                right = self.GetPluginInfoEntryWithDefault( "RegionRight"+self.GetCurrentTaskId(), "0" )
                top = self.GetPluginInfoEntryWithDefault( "RegionTop"+self.GetCurrentTaskId(), "0" )
                bot = self.GetPluginInfoEntryWithDefault( "RegionBottom"+self.GetCurrentTaskId(), "0" )
            else:
                left = self.GetPluginInfoEntryWithDefault( "RegionLeft", "0" )
                right = self.GetPluginInfoEntryWithDefault( "RegionRight", "0" )
                top = self.GetPluginInfoEntryWithDefault( "RegionTop", "0" )
                bot = self.GetPluginInfoEntryWithDefault( "RegionBottom", "0" )
            arguments += " -rg "+left+" "+top+" "+right+" "+bot
        
            hasAOVs = self.GetBooleanPluginInfoEntryWithDefault( "HasAOVs", False )
            if hasAOVs:
                curAOV = 0
                while True:
                    assAOVName = self.GetPluginInfoEntryWithDefault( "ASSAOV"+str(curAOV)+"Name", "" )
                    if assAOVName == "":
                        break
                    aovFileName = self.GetPluginInfoEntryWithDefault( "AOV"+str(curAOV)+"Filename"+self.GetCurrentTaskId(), "" )
                    
                    arguments+= " -set "+assAOVName+" "+aovFileName
                    
                    curAOV += 1
        
        # Set the verbosity level
        arguments += " -v " + self.GetPluginInfoEntryWithDefault( "Verbose", "4" ) 
        
        # If threads specified is 0, then just use the default number of threads.
        threads = self.GetThreadCount()
        if threads > 0:
            arguments += " -t " + str(threads)
        
        # If enabled, add command to fail if no license is found, to avoid watermarked images.
        arguments += " -set options.abort_on_license_fail "
        if self.GetBooleanConfigEntryWithDefault( "AbortOnLicenseFail", True ):
            arguments += "true"
        else:
            arguments += "false"

        # Check CPU affinity, if already set then disable Arnold's CPU default CPU affinity
        if self.OverrideCpuAffinity():
            arguments += " -set options.pin_threads off "
        
        # Get the additional plugin folder(s) if specified.
        pluginFolder = self.GetPluginInfoEntryWithDefault( "PluginFolder1", "" )
        if pluginFolder != "":
            pluginFolder = RepositoryUtils.CheckPathMapping( pluginFolder )
            pluginFolder = self.FixPath( pluginFolder )
            pluginFolder = pluginFolder.rstrip("/\\")
            arguments += " -l \"" + pluginFolder + "\""
        pluginFolder = self.GetPluginInfoEntryWithDefault( "PluginFolder2", "" )
        if pluginFolder != "":
            pluginFolder = RepositoryUtils.CheckPathMapping( pluginFolder )
            pluginFolder = self.FixPath( pluginFolder )
            pluginFolder = pluginFolder.rstrip("/\\")
            arguments += " -l \"" + pluginFolder + "\""
        pluginFolder = self.GetPluginInfoEntryWithDefault( "PluginFolder3", "" )
        if pluginFolder != "":
            pluginFolder = RepositoryUtils.CheckPathMapping( pluginFolder )
            pluginFolder = self.FixPath( pluginFolder )
            pluginFolder = pluginFolder.rstrip("/\\")
            arguments += " -l \"" + pluginFolder + "\""
        
        # Add any additional command line arguments to the end.
        additionalArguments = self.GetPluginInfoEntryWithDefault( "CommandLineOptions", "" )
        if additionalArguments != "":
            arguments += " " + additionalArguments
        
        return arguments;
    
    def GetThreadCount( self ):
        threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if self.OverrideCpuAffinity() and self.GetBooleanConfigEntryWithDefault( "LimitThreadsToCPUAffinity", False ):
            affinity = len( self.CpuAffinity() )
            if threads == 0:
                threads = affinity
            else:
                threads = min( affinity, threads )
                
        return threads    
    
    def PostRenderTasks( self ):
        if( self.LocalRendering ):
            self.LogInfo( "Moving output files and folders from " + self.LocalFilePath + " to " + self.NetworkFilePath )
            self.VerifyAndMoveDirectory( self.LocalFilePath, self.NetworkFilePath, False, -1 )
    
    def FixPath( self, path ):
        if SystemUtils.IsRunningOnWindows():
            path = path.replace( "/", "\\" )
            if path.startswith( "\\" ) and not path.startswith( "\\\\" ):
                path = "\\" + path
        else:
            path = path.replace( "\\", "/" )
        
        return path
    
    def HandleStdoutError(self):
        self.FailRender(self.GetRegexMatch(0))

    def HandleProgress( self ):
        self.SetProgress( float(self.GetRegexMatch(1)) )
