from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Plugins import *
from Deadline.Scripting import *

import os
######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return RenderManPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the RenderMan plugin.
######################################################################
class RenderManPlugin (DeadlinePlugin):
    RibFile = ""
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.StartupDirectoryCallback += self.StartupDirectory
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.StartupDirectoryCallback
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Simple
        
        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        
        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( r"ERROR.*|error.*|RIB error.*|.*Unable to find shader.*|.*Unable to find out device.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( r"R90000\s*([0-9]+)%" ).HandleCallback += self.HandleProgress
    
    ## Called by Deadline to get the render executable.
    def RenderExecutable( self ):
        renderExeList = self.GetConfigEntry( "RenderMan_Executable" )
        renderExe = FileUtils.SearchFileList( renderExeList )
        if( renderExe == "" ):
            self.FailRender( "RenderMan render executable was not found in the semicolon separated list \"" + renderExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return renderExe
    
    ## Called by Deadline to get the render arguments.
    def RenderArgument( self ):
        arguments = self.GetPluginInfoEntryWithDefault( "CommandLineOptions", "" )
        arguments += " -Progress -t:" + self.GetPluginInfoEntryWithDefault( "Threads", "0" )
        
        initialRibFilename = self.GetPluginInfoEntry( "RibFile" ).strip()
        initialRibFilename = RepositoryUtils.CheckPathMapping( initialRibFilename )
        initialRibFilename = self.SubstituteFrameFolderNumber( initialRibFilename, self.GetStartFrame() )
        
        if SystemUtils.IsRunningOnWindows():
            initialRibFilename = initialRibFilename.replace( "/", "\\" )
            if initialRibFilename.startswith( "\\" ) and not initialRibFilename.startswith( "\\\\" ):
                initialRibFilename = "\\" + initialRibFilename
        else:
            initialRibFilename = initialRibFilename.replace( "\\", "/" )
        
        self.LogInfo( "Rendering file: " + initialRibFilename )
        self.RibFile = initialRibFilename
        
        arguments += " \"" + initialRibFilename.replace( "\\", "/" ) + "\""
        
        return arguments
    
    def StartupDirectory( self ):
        workingDirectory = self.GetPluginInfoEntryWithDefault( "WorkingDirectory", "" ).strip()
        if workingDirectory != "":
            workingDirectory = RepositoryUtils.CheckPathMapping( workingDirectory )
            if SystemUtils.IsRunningOnWindows():
                workingDirectory = workingDirectory.replace( "/", "\\" )
            else:
                workingDirectory = workingDirectory.replace( "\\", "/" )
        else:
            workingDirectory = Path.GetDirectoryName( self.RibFile )
        return workingDirectory
    
    def SubstituteFrameFolderNumber( self, filename, frame ):
        # Renderman rib files are split into separate folders, and the folder name represents the frame. For example:
        #   - base/path/0000/0000.rib
        #   - base/path/0000/0000_layerName.rib
        
        modifyFolder = False
        # Make sure the frame folder is valid.
        frameFolder = os.path.dirname( filename )
        if not frameFolder:
            return filename
        
        # Make sure the frame folder name is actually a number.
        frameFolderName = os.path.basename( frameFolder )
        if Regex.Match( frameFolderName, "^[0-9]+$" ).Success:
            # Make sure the base folder is valid.
            baseFolder = os.path.dirname( frameFolder )
            if baseFolder:
                modifyFolder = True
        
        if modifyFolder:
            # Build up the new frame folder for the current frame.
            paddingSize = len( frameFolderName )
            paddedFrameNumber = StringUtils.ToZeroPaddedString( frame, paddingSize, False )
            frameFolder = Path.Combine( baseFolder, paddedFrameNumber )
        
        # Build up the new frame file name for the current frame.
        frameFilename = Path.GetFileName( filename )
        match = Regex.Match( frameFilename, "[0-9]+" )
        if match.Success:
            paddingSize = match.Length
            paddedFrameNumber = StringUtils.ToZeroPaddedString( frame, paddingSize, False )
            frameFilename = frameFilename.replace( match.Value, paddedFrameNumber )
            
        return Path.Combine( frameFolder, frameFilename )
    
    def HandleError( self ):
        self.FailRender( self.GetRegexMatch( 0 ) )
    
    def HandleProgress( self ):
        self.SetStatusMessage( self.GetRegexMatch( 0 ) )
        self.SetProgress( float(self.GetRegexMatch(1)) )
        #self.SuppressThisLine()
