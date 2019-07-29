from System import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

import os

def GetDeadlinePlugin():
    return TerragenPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class TerragenPlugin (DeadlinePlugin):
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PostRenderTasksCallback += self.PostRenderTasks

        self.Version = 0
        self.LocalRendering = False
        self.NetworkFilePath = ""
        self.LocalFilePath = ""
        self.NetworkExtraFilePath = ""
        self.LocalExtraFilePath = ""
    
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
        
        # Get the version we're rendering with.
        self.Version = self.GetIntegerPluginInfoEntryWithDefault( "Version", 2 )
        
        self.AddStdoutHandlerCallback( "ERROR: .*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( "Warning: Unable to find a valid license key" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( "Warning: Exception caught in juRenderNode::FinishRender" ).HandleCallback += self.HandleError

        self.AddStdoutHandlerCallback( "Starting .*" ).HandleCallback += self.HandleStatus
        if self.Version > 2:
            self.AddStdoutHandlerCallback( ".* ([0-9]+)% of final pass.*" ).HandleCallback += self.HandleProgress
        else:
            self.AddStdoutHandlerCallback( "Rendering .*" ).HandleCallback += self.HandleRendering
    
    def RenderExecutable( self ):
        # Get custom exe
        customExe = self.GetPluginInfoEntryWithDefault( "CustomExe", "" )
        customExe = RepositoryUtils.CheckPathMapping( customExe )
        if SystemUtils.IsRunningOnWindows():
            customExe = customExe.replace( "/", "\\" )
        else:
            customExe = customExe.replace( "\\", "/" )
        
        if (customExe != ""):
            terragenExe = customExe
            self.LogInfo ( 'Using custom Terragen exe "' + terragenExe + '"' )
        else:
            # Get terragen exe from plugin config
            terragenExeList = self.GetConfigEntry( "Terragen"+str(self.Version)+"_RenderExecutable" )

            terragenExe = FileUtils.SearchFileList( terragenExeList )
            if( terragenExe == "" ):
                self.FailRender( "No file found in the semicolon separated list \"" + terragenExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return terragenExe
        
    def RenderArgument( self ):
        regionRendering = self.GetBooleanPluginInfoEntryWithDefault( "RegionRendering", False )
        singleRegionJob = self.IsTileJob()
        singleRegionIndex = self.GetCurrentTaskId()
        curTile = 0
        
        # Get project file
        projectFile = self.GetPluginInfoEntryWithDefault( "ProjectFile", self.GetDataFilename() )
        projectFile = RepositoryUtils.CheckPathMapping( projectFile )
        if SystemUtils.IsRunningOnWindows():
            projectFile = projectFile.replace( "/", "\\" )
        else:
            projectFile = projectFile.replace( "\\", "/" )
        
        arguments = "-p \"" + projectFile + "\""
        
        # Get render node (if specified)
        renderNode = self.GetPluginInfoEntryWithDefault( "RenderNode", "" )
        arguments += StringUtils.BlankIfEitherIsBlank( StringUtils.BlankIfEitherIsBlank( " -rendernode \"", renderNode ), "\"" )
        
        # Set frame and other flags
        arguments += " -hide -exit -r -f " + str( self.GetStartFrame() )
        
        # Get output file
        outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip()
        outputFile = RepositoryUtils.CheckPathMapping( outputFile )
        if SystemUtils.IsRunningOnWindows():
            outputFile = outputFile.replace( "/", "\\" )
        else:
            outputFile = outputFile.replace( "\\", "/" )
        
        # Get extra output file
        extraOutputFile = self.GetPluginInfoEntryWithDefault( "ExtraOutputFile", "" ).strip()
        extraOutputFile = RepositoryUtils.CheckPathMapping( extraOutputFile )
        if SystemUtils.IsRunningOnWindows():
            extraOutputFile = extraOutputFile.replace( "/", "\\" )
        else:
            extraOutputFile = extraOutputFile.replace( "\\", "/" )
        
        if regionRendering:
            xStart = 0
            xEnd = 0
            yStart = 0
            yEnd = 0
            if singleRegionJob:
                currTile = singleRegionIndex
                xStart = self.GetFloatPluginInfoEntryWithDefault( "RegionLeft"+str(singleRegionIndex), 0 )
                xEnd = self.GetFloatPluginInfoEntryWithDefault( "RegionRight"+str(singleRegionIndex), 0 )
                yStart = self.GetFloatPluginInfoEntryWithDefault( "RegionBottom"+str(singleRegionIndex), 0 )
                yEnd = self.GetFloatPluginInfoEntryWithDefault( "RegionTop"+str(singleRegionIndex), 0 )
            else:
                currTile = self.GetIntegerPluginInfoEntryWithDefault( "CurrentTile", 1 )
                xStart = self.GetFloatPluginInfoEntryWithDefault( "RegionLeft", 0 )
                xEnd = self.GetFloatPluginInfoEntryWithDefault( "RegionRight", 0 )
                yStart = self.GetFloatPluginInfoEntryWithDefault( "RegionBottom", 0 )
                yEnd = self.GetFloatPluginInfoEntryWithDefault( "RegionTop", 0 )
            
            arguments += " -tilex %s %s" % ( xStart, xEnd )
            arguments += " -tiley %s %s" % ( yStart, yEnd )
        
        # Check if local rendering is disabled
        self.LocalRendering = False
        if outputFile != "" or extraOutputFile != "":
            self.LocalRendering = self.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False )
            if self.LocalRendering:
                self.LogInfo( "Rendering to local drive, will copy files and folders to final location after render is complete" )
                
                if outputFile != "":
                    outputDir = Path.GetDirectoryName( outputFile )
                    self.NetworkFilePath = outputDir
                    
                    outputDir = self.CreateTempDirectory( "TerragenOutput" )
                    self.LocalFilePath = outputDir
                    
                    outputFile = Path.Combine( outputDir, Path.GetFileName( outputFile ) )
                
                if extraOutputFile != "":
                    extraOutputDir = Path.GetDirectoryName( extraOutputFile )
                    self.NetworkExtraFilePath = extraOutputDir
                    
                    extraOutputDir = self.CreateTempDirectory( "TerragenExtraOutput" )
                    self.LocalExtraFilePath = extraOutputDir
                    
                    extraOutputFile = Path.Combine( extraOutputDir, Path.GetFileName( extraOutputFile ) )
            else:
                self.LogInfo( "Rendering to network drive" )
                
        if regionRendering:
            if outputFile != "":
                path, ext = os.path.splitext( outputFile )
                outputFile = path + "_tile" + str(currTile) + ext
                
            if extraOutputFile != "":
                path, ext = os.path.splitext( extraOutputFile )
                extraOutputFile = path + "_tile" + str(currTile) + ext
            
        arguments += StringUtils.BlankIfEitherIsBlank( StringUtils.BlankIfEitherIsBlank( " -o \"", outputFile ), "\"" )
        arguments += StringUtils.BlankIfEitherIsBlank( StringUtils.BlankIfEitherIsBlank( " -ox \"", extraOutputFile ), "\"" )
        
        return arguments
    
    def PostRenderTasks( self ):
        if( self.LocalRendering ):
            if self.NetworkFilePath != "":
                self.LogInfo( "Moving output files and folders from " + self.LocalFilePath + " to " + self.NetworkFilePath )
                self.VerifyAndMoveDirectory( self.LocalFilePath, self.NetworkFilePath, False, -1 )
            if self.NetworkExtraFilePath != "":
                self.LogInfo( "Moving output files and folders from " + self.LocalExtraFilePath + " to " + self.NetworkExtraFilePath )
                self.VerifyAndMoveDirectory( self.LocalExtraFilePath, self.NetworkExtraFilePath, False, -1 )
    
    def HandleError( self ):
        self.FailRender( self.GetRegexMatch( 0 ) )
    
    def HandleStatus( self ):
        self.SetStatusMessage( self.GetRegexMatch( 0 ) )

    def HandleRendering( self ):
        self.SetStatusMessage( self.GetRegexMatch( 0 ) )
        self.SetProgress( 1.0 )
        
    def HandleProgress( self ):
        self.SetStatusMessage( self.GetRegexMatch( 0 ) )
        progress = float(self.GetRegexMatch( 1 ))
        self.SetProgress( progress )
