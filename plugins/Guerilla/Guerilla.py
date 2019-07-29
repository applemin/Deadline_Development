from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return GuerillaPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Guerilla plugin.
######################################################################
class GuerillaPlugin (DeadlinePlugin):
    luaScriptFile = ""
    
    def __init__( self ):
        self.InitializeProcessCallback += self.initializeProcess
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.RenderExecutableCallback += self.renderExecutable
        self.RenderArgumentCallback += self.renderArgument
        self.StartupDirectoryCallback += self.startupDirectory
    
    def cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.PreRenderTasksCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.StartupDirectoryCallback
    
    ## Called by Deadline to initialize the process.
    def initializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Simple
        
        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        
        # Stdout handlers
        self.AddStdoutHandlerCallback( "PROGRESS: ([0-9]+)%" ).HandleCallback += self.handleProgress
    
    def PreRenderTasks( self ):
        self.luaScriptFile = self.GetPluginInfoEntry( "ScriptFile" ).strip()
        self.luaScriptFile = RepositoryUtils.CheckPathMapping( self.luaScriptFile )
        self.luaScriptFile = self.fixPath( self.luaScriptFile )
        
        currPadding = FrameUtils.GetFrameStringFromFilename( self.luaScriptFile )
        
        paddingSize = len( currPadding )
        if paddingSize > 0:
            newPadding = StringUtils.ToZeroPaddedString( self.GetStartFrame(), paddingSize, False )
            self.luaScriptFile = FrameUtils.SubstituteFrameNumber( self.luaScriptFile, newPadding )
    
    ## Called by Deadline to get the render executable.
    def renderExecutable( self ):
        renderExeList = self.GetConfigEntry( "Guerilla_Executable" )
        renderExe = FileUtils.SearchFileList( renderExeList )
        if( renderExe == "" ):
            self.FailRender( "Guerilla render executable was not found in the semicolon separated list \"" + renderExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        # Set the GUERILLA environment variable to the Guerilla install directory
        guerillaDir = Path.GetDirectoryName( renderExe )
        self.LogInfo( "Setting GUERILLA environment variable to " + guerillaDir )
        self.SetEnvironmentVariable( "GUERILLA", guerillaDir )
            
        return renderExe
    
    ## Called by Deadline to get the render arguments.
    def renderArgument( self ):
        arguments = "\"" + self.luaScriptFile + "\" \"--progress=PROGRESS: %d%%\""
        
        scriptArgs = self.GetPluginInfoEntryWithDefault( "ScriptArgs", "" )
        if scriptArgs != "":
            arguments += " " + scriptArgs
        
        return arguments
    
    def startupDirectory( self ):
        return Path.GetDirectoryName( self.luaScriptFile )
    
    def fixPath( self, path ):
        if SystemUtils.IsRunningOnWindows():
            path = path.replace( "/", "\\" )
            if path.startswith( "\\" ) and not path.startswith( "\\\\" ):
                path = "\\" + path
        else:
            path = path.replace( "\\", "/" )
        
        return path

    def handleProgress( self ):
        self.SetProgress( float(self.GetRegexMatch(1)) )