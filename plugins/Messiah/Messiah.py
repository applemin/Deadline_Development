
from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return MessiahPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class MessiahPlugin(DeadlinePlugin):
    HostLibrary = ""
    
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
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        self.PopupHandling = True
        
        # Stdout handlers
        self.AddStdoutHandlerCallback( "Rendering frame [0-9]+" ).HandleCallback += self.HandleStatus
        self.AddStdoutHandlerCallback( "Finished frame [0-9]+ \\(([0-9]+) of ([0-9]+)\\)" ).HandleCallback += self.HandleProgress
    
    def RenderExecutable(self):
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        version = int(self.GetPluginInfoEntryWithDefault( "Version", "5" ))
        
        executable = ""
        hostLibrary = ""
        hostLibraryList = self.GetConfigEntry( "Messiah" + str(version) + "_HostLibrary" )
        
        if(SystemUtils.IsRunningOnWindows()):
            if( build == "32bit" ):
                self.LogInfo( "Enforcing 32 bit build of messiah" )
                hostLibrary = FileUtils.SearchFileListFor32Bit( hostLibraryList )
                if hostLibrary == "":
                    self.LogWarning( "32 bit messiah host library was not found in the semicolon separated list \"" + hostLibraryList + "\". Checking for any executable that exists instead." )
                executable = Path.Combine( self.GetPluginDirectory(), "Render32.exe" )
                
            elif( build == "64bit" ):
                self.LogInfo( "Enforcing 64 bit build of messiah" )
                hostLibrary = FileUtils.SearchFileListFor64Bit( hostLibraryList )
                if hostLibrary == "":
                    self.LogWarning( "64 bit messiah host library was not found in the semicolon separated list \"" + hostLibraryList + "\". Checking for any executable that exists instead." )
                executable = Path.Combine( self.GetPluginDirectory(), "Render64.exe" )
                
        if( hostLibrary == "" ):
            self.LogInfo( "Not enforcing a build of messiah" )
            hostLibrary = FileUtils.SearchFileList( hostLibraryList )
            if hostLibrary == "":
                self.FailRender( "messiah host library was not found in the semicolon separated list \"" + hostLibraryList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
            
            if FileUtils.Is64BitDllOrExe( hostLibrary ):
                executable = Path.Combine( self.GetPluginDirectory(), "Render64.exe" )
            else:
                executable = Path.Combine( self.GetPluginDirectory(), "Render32.exe" )
            
        self.HostLibrary = hostLibrary
        return executable
        
    def RenderArgument(self):
        # Scene file
        sceneFile = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        renderArgument = " -f\"" + sceneFile.replace( "/", "\\" ) + "\""
        
        # Host library
        renderArgument += " -h\"" + self.HostLibrary.replace( "/", "\\" ) + "\""
        
        # Content folder
        contentFolder = self.GetPluginInfoEntryWithDefault( "ContentFolder", "" ).strip()
        if contentFolder != "":
            contentFolder = RepositoryUtils.CheckPathMapping( contentFolder )
            if not Directory.Exists( contentFolder ):
                self.FailRender( "Content folder \"" + contentFolder + "\" does not exist" )
            renderArgument += " -c\"" + contentFolder.replace( "/", "\\" ).rstrip( "\\" ) + "\""
        
        # Frame range
        renderArgument += " -b" + str(self.GetStartFrame()) + " -e" + str(self.GetEndFrame()) + " -s1"
        
        # Threads
        threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if threads == 0:
            self.LogInfo( "Using optimal number of threads for rendering" )
            threads = SystemUtils.GetCpuCount()
        renderArgument += " -t" + str(threads)
        
        # Resolution
        width = self.GetIntegerPluginInfoEntryWithDefault( "Width", 0 )
        if width > 0:
            renderArgument += " -x" + str(width)
        
        height = self.GetIntegerPluginInfoEntryWithDefault( "Height", 0 )
        if height > 0:
            renderArgument += " -y" + str(height)
        
        # Output folder
        outputFolder = self.GetPluginInfoEntryWithDefault( "OutputFolder", "" ).strip()
        if outputFolder != "":
            outputFolder = RepositoryUtils.CheckPathMapping( outputFolder )
            renderArgument += " -o\"" + outputFolder.replace( "/", "\\" ).rstrip( "\\" ) + "\""
        
        # Antialiasing
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideAntialiasing", False ):
            # Modes: 0=off, 1=adaptive, 2=enchanced
            aaModeNumber = "1"
            aaMode = self.GetPluginInfoEntryWithDefault( "AntialiasingMode", "adaptive" ).lower()
            if aaMode == "off":
                aaModeNumber = "0"
            elif aaMode == "adaptive":
                aaModeNumber = "1"
            elif aaMode == "enchanced":
                aaModeNumber = "2"
            
            renderArgument += " -am" + aaModeNumber
            renderArgument += " -al" + self.GetPluginInfoEntryWithDefault( "AntialiasingLevel", "1" )
        
        return renderArgument
    
    def HandleStatus( self ):
        self.SetStatusMessage( self.GetRegexMatch( 0 ) )
    
    def HandleProgress( self ):
        currFrame = int(self.GetRegexMatch( 1 ))
        totalFrames = int(self.GetRegexMatch( 2 ))
        self.SetProgress( (float(currFrame) * 100.0) / (float(totalFrames) ) )
