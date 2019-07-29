from System.IO import *
from System.Text.RegularExpressions import *
from System import *
from System.Diagnostics import *

from Deadline.Plugins import *
from Deadline.Scripting import *

import os


def GetDeadlinePlugin():
    return MantraPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class MantraPlugin(DeadlinePlugin):
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
        self.SingleFramesOnly=True
        self.StdoutHandling=True
        self.PopupHandling=True
        
        self.AddStdoutHandlerCallback("ALF_PROGRESS ([0-9]+)").HandleCallback += self.HandleStdoutProgress
        self.AddStdoutHandlerCallback("Error:(.*)").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback("mantra: Bad Alembic Archive.*").HandleCallback += self.HandleStdoutError
        
        self.AddPopupHandler( ".*Houdini DSO Error.*", "OK" )
    
    def RenderExecutable(self):
        version = self.GetPluginInfoEntry("Version")
        
        renderExeList = self.GetConfigEntry("Mantra" + version.replace( ".", "_" ) + "_Executable")
        renderExe = FileUtils.SearchFileList(renderExeList)
        
        if(renderExe == ""):
            self.FailRender( "Mantra " + version + " render executable was not found in the semicolon separated list \"" + renderExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return renderExe
        
    def RenderArgument(self):
        #Get additional command line optins.
        arguments = self.GetPluginInfoEntryWithDefault( "CommandLineOptions", "" )
        
        regionRendering = self.GetBooleanPluginInfoEntryWithDefault( "RegionRendering", False )
        singleRegionJob = self.IsTileJob()
        singleRegionFrame = str(self.GetStartFrame())
        singleRegionIndex = self.GetCurrentTaskId()
        
        frame = self.GetStartFrame()
        
        ifdFile = self.GetPluginInfoEntryWithDefault( "SceneFile",self.GetDataFilename())
        ifdFile = RepositoryUtils.CheckPathMapping( ifdFile )
        ifdFile = ifdFile.replace( "\\", "/" )
        
        ifdPaddingLength = FrameUtils.GetPaddingSizeFromFilename( ifdFile )
        if( ifdPaddingLength > 0 ):
            ifdFile = FrameUtils.SubstituteFrameNumber(ifdFile, StringUtils.ToZeroPaddedString(frame,ifdPaddingLength,False))
        
        if SystemUtils.IsRunningOnWindows():
            ifdFile = ifdFile.replace( "/", "\\" )
            if ifdFile.startswith( "\\" ) and not ifdFile.startswith( "\\\\" ):
                ifdFile = "\\" + ifdFile
        else:
            ifdFile = ifdFile.replace( "\\", "/" )
        
        if self.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
            tempIfdDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
            tempIfdFileName = Path.Combine( tempIfdDirectory, Path.GetFileName( ifdFile ) )
            tempIfdFileName = tempIfdFileName.replace( "\\", "/" )
            
            # Specifying 'True' for the last argument so that the file can be read in byte by byte, since IFDs can contain binary data.
            # This is known to have problems with UTF16 and UTF32 files though. However, if we specify 'False', every line of the file
            # is read in as a string, and then written back out, which messes up the binary data.
            RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator( ifdFile, tempIfdFileName, "\\", "/", True )
            ifdFile = tempIfdFileName
        
        self.LogInfo( "Rendering IFD file: " + ifdFile )
        ifdPaddingLength = FrameUtils.GetPaddingSizeFromFilename( ifdFile )
        
        if(self.GetFloatPluginInfoEntry("Version") >= 9):
            #Get thread count.
            threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads",0)
            if( threads == 0 ):
                self.LogInfo( "Rendering with maximum threads" )
            elif( threads == 1 ):
                self.LogInfo( "Rendering with 1 thread" )
            else:
                self.LogInfo( "Rendering with " + str(threads) + " threads" )
        
        # Get output file.
        outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" )
        outputFile = RepositoryUtils.CheckPathMapping( outputFile )
        if( len(outputFile) > 0 ):
            paddedNumberRegex = Regex( "\\$F([0-9]+)" )
            if paddedNumberRegex.IsMatch( outputFile ):
                paddingSize = int(paddedNumberRegex.Match( outputFile ).Groups[1].Value)
                padding = StringUtils.ToZeroPaddedString( frame, paddingSize, False )
                outputFile = paddedNumberRegex.Replace( outputFile, padding )
            elif outputFile.find( "$F" ) >= 0:
                outputFile = outputFile.replace( "$F", str(frame) )
            else:
                outputPaddingLength = FrameUtils.GetPaddingSizeFromFilename( outputFile )
                if( outputPaddingLength > 0 ):
                    outputFile = FrameUtils.SubstituteFrameNumber( outputFile, StringUtils.ToZeroPaddedString(frame,outputPaddingLength,False))
                elif( ifdPaddingLength > 0 ):
                    outputFolder = Path.GetDirectoryName( outputFile )
                    outputPrefix = Path.GetFileNameWithoutExtension( outputFile )
                    outputNumber = StringUtils.ToZeroPaddedString( frame, ifdPaddingLength, False )
                    outputExt = Path.GetExtension( outputFile )
                    outputFile = Path.Combine( outputFolder,(outputPrefix + outputNumber + outputExt) )
            
            if SystemUtils.IsRunningOnWindows():
                outputFile = outputFile.replace( "/", "\\" )
                if outputFile.startswith( "\\" ) and not outputFile.startswith( "\\\\" ):
                    outputFile = "\\" + outputFile
            else:
                outputFile = outputFile.replace( "\\", "/" )
            
            self.LogInfo( "Rendering output to " + outputFile )
        else:
            self.LogInfo( "Rendering output to location specified in IFD file" )
        
        # The 'a' in the verbosity option displays friendly progress output that we can easily parse.
        arguments += " -V 4a"
        
        #The -j argument is only used in versions 9 and above
        if(self.GetFloatPluginInfoEntry("Version") >= 9):
            arguments += " -j " + str(threads)
        
        if regionRendering:
            currentTile = 0
            regionLeft = 0
            regionRight = 0
            regionTop = 0
            regionBottom = 0
            
            if singleRegionJob:
                currentTile = singleRegionIndex
                regionLeft = self.GetFloatPluginInfoEntryWithDefault("RegionLeft"+str(singleRegionIndex),0)
                regionRight = self.GetFloatPluginInfoEntryWithDefault("RegionRight"+str(singleRegionIndex),0)
                regionTop = self.GetFloatPluginInfoEntryWithDefault("RegionTop"+str(singleRegionIndex),0)
                regionBottom = self.GetFloatPluginInfoEntryWithDefault("RegionBottom"+str(singleRegionIndex),0)
                
            else:
                currentTile = self.GetIntegerPluginInfoEntryWithDefault( "CurrentTile", 0 )
                regionLeft = self.GetFloatPluginInfoEntryWithDefault( "RegionLeft", 0 )
                regionRight = self.GetFloatPluginInfoEntryWithDefault( "RegionRight", 0 )
                regionTop = self.GetFloatPluginInfoEntryWithDefault( "RegionTop", 0 )
                regionBottom = self.GetFloatPluginInfoEntryWithDefault( "RegionBottom", 0 )
            
            tileScript = Path.Combine( self.GetPluginDirectory(), "mantra_tile_render.py" )
            tileScript = tileScript.replace("\\","/")
            
            arguments += " -P \"" + tileScript + " -l " + str(regionLeft) + " -r " + str(regionRight) + " -b " + str(regionBottom) + " -t " + str(regionTop) + " -n " + str(currentTile) + "\""
            
        arguments += " -f \"" + ifdFile + "\""
        arguments += StringUtils.BlankIfEitherIsBlank( StringUtils.BlankIfEitherIsBlank( " \"", outputFile ), "\"" )
        
        return arguments
        
    def HandleStdoutProgress(self):
        self.SetStatusMessage(self.GetRegexMatch(0))
        self.SetProgress(float(self.GetRegexMatch(1)))
        #self.SuppressThisLine()
        
    def HandleStdoutError(self):
        self.FailRender(self.GetRegexMatch(0))
