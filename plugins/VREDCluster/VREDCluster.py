from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return VREDClusterPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the VREDCluster plugin.
######################################################################
class VREDClusterPlugin(DeadlinePlugin):

    Version = ""

    def __init__(self):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback

    def InitializeProcess(self):
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Simple

        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True

        # Set the stdout handlers.
        self.AddStdoutHandlerCallback(".*No valid license found.*").HandleCallback += self.HandleFatalError
    
    def PreRenderTasks( self ):
        if self.IsRunningAsService():
            self.LogWarning( "VRED can sometimes crash when running as a service. If VRED appears crashed, try running the Slave as a normal application instead of as a service to see if that fixes the problem." ) 
    
    def RenderExecutable(self):
        version = self.GetPluginInfoEntryWithDefault( "Version", "9.0" ).strip() #default to empty string (this should match pre-versioning config entries)
        
        self.LogInfo( "VRED Version: %s" % version )

        vredExeList = self.GetConfigEntry( "ClusterExecutable%s" %  version.replace( ".", "_" ) )
        vredExe = FileUtils.SearchFileList( vredExeList )
        if( vredExe == "" ):
            self.FailRender( "VRED cluster service executable was not found in the semicolon separated list \"" + vredExeList + "\". The path to the cluster executable can be configured from the Plugin Configuration in the Deadline Monitor." )
            
        processName = Path.GetFileNameWithoutExtension( vredExe )
        if( ProcessUtils.IsProcessRunning( processName ) ):
            self.LogWarning( "Found existing %s process" % processName )
            process = Process.GetProcessesByName( processName )[ 0 ]
            if process != None:
                self.FailRender( "A process %s with pid %d exists - shut down this copy of VRED Cluster Service. Ensure VRED cluster service is NOT already running!" % (processName, process.Id) )
            
        return vredExe

    def RenderArgument(self):
        arguments = ""

        arguments += "-exec"

        portNumber = self.GetPluginInfoEntryWithDefault( "Port", "" )
        if portNumber != "":
            arguments += " -p %s" % portNumber

        return arguments

    def HandleFatalError( self ):
        self.FailRender( self.GetRegexMatch(0) )
