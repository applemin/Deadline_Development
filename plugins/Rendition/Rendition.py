from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return RenditionPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class RenditionPlugin (DeadlinePlugin):
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.IsSingleFramesOnlyCallback += self.IsSingleFramesOnly
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.IsSingleFramesOnlyCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess( self ):
        self.StdoutHandling = True
        self.PopupHandling = True
        
        self.AddStdoutHandlerCallback( ".*" ).HandleCallback += self.HandleStdout
    
    def IsSingleFramesOnly( self ):
        outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip()
        return ( outputFile != "" )
    
    def RenderExecutable( self ):
        renderExeList = self.GetConfigEntry( "Rendition_RenderExecutable" )
        renderExe = ""
        
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        if SystemUtils.IsRunningOnWindows():
            if build == "32bit":
                renderExe = FileUtils.SearchFileListFor32Bit( renderExeList )
                if( renderExe == "" ):
                    self.LogWarning( "32 bit Rendition render executable was not found in the semicolon separated list \"" + renderExeList + "\". Checking for any executable that exists instead." )
            elif build == "64bit":
                renderExe = FileUtils.SearchFileListFor64Bit( renderExeList )
                if( renderExe == "" ):
                    self.LogWarning( "64 bit Rendition render executable was not found in the semicolon separated list \"" + renderExeList + "\". Checking for any executable that exists instead." )
            
        if( renderExe == "" ):
            renderExe = FileUtils.SearchFileList( renderExeList )
            if( renderExe == "" ):
                self.FailRender( "Rendition render executable was not found in the semicolon separated list \"" + renderExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return renderExe
    
    def RenderArgument( self ):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        outputFile = ""
        
        sceneFile = self.GetPluginInfoEntry( "SceneFile" )
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        if SystemUtils.IsRunningOnWindows():
            sceneFile = sceneFile.replace( "/", "\\" )
        else:
            sceneFile = sceneFile.replace( "\\", "/" )
        
        renderArgument = "-interactive"
        renderArgument += " -input_file_name \"" + sceneFile + "\""
        
        outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip()
        
        if outputFile != "":
            outputFile = RepositoryUtils.CheckPathMapping( outputFile )
            if SystemUtils.IsRunningOnWindows():
                outputFile = outputFile.replace( "/", "\\" )
            else:
                outputFile = outputFile.replace( "\\", "/" )
            
            directory = Path.GetDirectoryName( outputFile )
            prefix = Path.GetFileNameWithoutExtension( outputFile )
            padding = StringUtils.ToZeroPaddedString( startFrame, 4, False )
            extension = Path.GetExtension( outputFile )
            
            renderArgument += " -file_name \"" + Path.Combine( directory, prefix + padding + extension ) + "\""
        
        renderArgument += " -render " + str(startFrame) + " " + str(endFrame)
        
        if self.GetBooleanPluginInfoEntryWithDefault( "Skip", False ):
            renderArgument += " -skip"
        
        renderArgument += " " + self.GetPluginInfoEntryWithDefault( "CommandLineOptions", "" ).strip()
        
        return renderArgument
    
    def HandleStdout( self ):
        stdoutLine = self.GetRegexMatch(0).strip()
        if len( stdoutLine ) <= 0:
            self.SuppressThisLine()
