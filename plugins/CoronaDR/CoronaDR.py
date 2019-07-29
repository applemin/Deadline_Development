from System import *
from System.IO import *
from System.Diagnostics import *

from Deadline.Scripting import *
from Deadline.Plugins import *

from FranticX.Processes import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return CoronaDRPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the CoronaDR plugin.
######################################################################
class CoronaDRPlugin( DeadlinePlugin ):

    def __init__( self ):
        self.Executable = ""
        self.CoronaProcess = None
        self.ProcessName = "CoronaDr"
        self.ExistingDRProcess = "Fail On Existing Process"
        self.DRAutoClose = False
        self.DRCloseTimeoutBeforeRender = 900

        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob

    def Cleanup( self ):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback

        if self.CoronaProcess:
            self.CoronaProcess.Cleanup()
            del self.CoronaProcess

    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        self.LogInfo( "Corona DR Plugin Initializing..." )
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Advanced
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.HideDosWindow = True

    def StartJob( self ):
        coronaDrExeList = self.GetConfigEntry( "CoronaDrServerExecutable" )
        self.Executable = FileUtils.SearchFileList( coronaDrExeList )
        if( self.Executable == "" ):
            self.FailRender( "Corona DrServer executable was not found in the semicolon separated list \"" + coronaDrExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        else:
            self.LogInfo( "Executable: %s" % self.Executable )

        self.ExistingDRProcess = self.GetConfigEntryWithDefault( "ExistingDRProcess", "Fail On Existing Process" )
        self.LogInfo( "Existing DR Process: %s" % self.ExistingDRProcess )

        processName = Path.GetFileNameWithoutExtension( self.Executable )
        if( ProcessUtils.IsProcessRunning( processName ) ):
            processes = Process.GetProcessesByName( processName )
            
            if len( processes ) > 0:
                self.LogWarning( "Found existing '%s' process" % processName )
                process = processes[ 0 ]

                if( self.ExistingDRProcess == "Fail On Existing Process" ):
                    if process != None:
                        self.FailRender( "Fail On Existing Process is enabled, and a process '%s' with pid '%d' exists - shut down this copy of Corona DrServer. Ensure DrServer is NOT already running!" % (processName, process.Id) )

                if( self.ExistingDRProcess == "Kill On Existing Process" ):
                    if( ProcessUtils.KillProcesses( processName ) ):
                        if process != None:
                            self.LogInfo( "Successfully Killed Corona DrServer process: '%s' with pid: '%d'" % (processName, process.Id) )

                        SystemUtils.Sleep(5000)

                        if( ProcessUtils.IsProcessRunning( processName ) ):
                            self.LogWarning( "Corona DrServer is still running: '%s' process, perhaps due to it being automatically restarted after the previous kill command. Ensure Corona DrServer is NOT already running!" % processName )
                            process = Process.GetProcessesByName( processName )[ 0 ]
                            if process != None:
                                self.FailRender( "Kill On Existing Process is enabled, and a process '%s' with pid '%d' still exists after executing a kill command. Ensure Corona DrServer is NOT already running!" % (processName, process.Id) )

        self.DRAutoClose = self.GetBooleanConfigEntryWithDefault( "DRAutoClose", False )
        self.LogInfo( "DR Auto Close: %s" % self.DRAutoClose )

        self.DRCloseTimeoutBeforeRender = self.GetIntegerConfigEntryWithDefault( "DRCloseTimeoutBeforeRender", 15 ) * 60 # The UI is in minutes, the code is still in seconds.
        self.LogInfo( "DR Close Timeout Before Render: %s seconds" % self.DRCloseTimeoutBeforeRender )

        self.DRCloseTimeoutAfterRender = self.GetIntegerConfigEntryWithDefault( "DRCloseTimeoutAfterRender", 15 ) * 60 # The UI is in minutes, the code is still in seconds.
        self.LogInfo( "DR Close Timeout After Render: %s seconds" % self.DRCloseTimeoutAfterRender )

        self.DROnJobComplete = self.GetConfigEntryWithDefault( "DROnJobComplete", "Do Nothing" )

        currentJob = self.GetJob()

        if self.DROnJobComplete != "Do Nothing":
            self.LogInfo( "Setting DR Job On Complete to: %s" % self.DROnJobComplete )
            currentJob.JobOnJobComplete = self.DROnJobComplete
            RepositoryUtils.SaveJob( currentJob )

    def RenderTasks( self ):
        waitforRender = self.GetBooleanConfigEntryWithDefault( "DRCloseWaitForRender", True )
        self.LogInfo( "DR Auto Timeout: Wait for first render: %s" % waitforRender )

        self.CoronaProcess = CoronaDrProcess( self, self.Executable, waitforRender )
 
        # Start process and then enter loop below.
        self.StartMonitoredManagedProcess( self.ProcessName, self.CoronaProcess )

        timeout = 0

        while( True ):
            if self.IsCanceled():
                self.FailRender( "Received cancel task command from Deadline." )
               
            self.VerifyMonitoredManagedProcess( self.ProcessName )
            self.FlushMonitoredManagedProcessStdout( self.ProcessName )
            
            if self.DRAutoClose:
                # Reset the timeout if Corona is active.
                if not self.CoronaProcess.IsDRActive():
                    # Corona is inactive, so increase the timer by 1 (because we sleep for 1 second each loop).                    
                    # If the timeout is reached, break out of the loop so that RenderTasks can exit, which means the task is complete.
                    if self.CoronaProcess.CheckRenderOccurred() and self.CoronaProcess.CheckTimeout( self.DRCloseTimeoutAfterRender ):
                        self.LogInfo( "Exiting DR Process and marking task as completed due to Deadline DR Session Auto After Render Timeout: %s seconds." % self.DRCloseTimeoutAfterRender )
                        break
                    elif not self.CoronaProcess.CheckRenderOccurred() and self.CoronaProcess.CheckTimeout( self.DRCloseTimeoutBeforeRender ):
                        self.LogInfo( "Exiting DR Process and marking task as completed due to Deadline DR Session Auto Before Render Timeout: %s seconds." % self.DRCloseTimeoutBeforeRender )
                        break

            # Sleep for 1 second between loops.
            SystemUtils.Sleep( 1000 )

    def EndJob( self ):
        self.LogInfo( "Ending Corona DrServer Job" )
        self.ShutdownMonitoredManagedProcess( self.ProcessName )

######################################################################
## This is the class that starts up the Corona DrServer process.
######################################################################
class CoronaDrProcess( ManagedProcess ):

    def __init__( self, deadlinePlugin, executable, startActive ):
        self.deadlinePlugin = deadlinePlugin
        self.Executable = executable
        self.DRActive = startActive
        self.DRTimeoutStartTime = None
        self.RenderOccurred = False

        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks

    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.PreRenderTasksCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PostRenderTasksCallback

    def InitializeProcess( self ):
        # Set the process specific settings.
        self.SingleFramesOnly = True
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        self.HideDosWindow = True

        # Set the stdout handlers.
        self.AddStdoutHandlerCallback(".*Accepted remote connection.*").HandleCallback += self.HandleDRSessionStarted
        self.AddStdoutHandlerCallback(".*Ready for new connection.*").HandleCallback += self.HandleDRSessionClosed

        # Ignore 3dsMax MAXScript Debugger Popup (ENU, FRA, DEU, JPN, CHS, KOR, PTB)
        self.AddPopupIgnorer( "MAXScript .*" ) #ENU #JPN #CHS #KOR
        self.AddPopupIgnorer( ".* MAXScript" ) #FRA #PTB
        self.AddPopupIgnorer( "MAXScript-Debugger" ) #DEU

        # Handle Corona VFB Saving Options
        self.AddPopupIgnorer( ".*Save Image.*" )
        self.AddPopupIgnorer( ".*Confirmation.*" )
        self.AddPopupIgnorer( ".*Save as.*" )
        self.AddPopupIgnorer( ".*Select file.*" )
        self.AddPopupIgnorer( ".*File Exists.*" )
        self.AddPopupIgnorer( ".*Curve Editor.*" )

        # Handle Corona Error Message dialog
        self.AddPopupIgnorer( "Corona Error Message(s)" )

        # For Maxwell
        self.AddPopupIgnorer( ".*Maxwell Translation Window.*" )
        self.AddPopupIgnorer( ".*Import Multilight.*" )

        # Handle Program Compatibility Assistant dialog
        self.AddPopupHandler( "Program Compatibility Assistant", "Close" )

    def PreRenderTasks( self ):
        self.deadlinePlugin.LogInfo( "Corona DrServer job starting..." )

    ## Called by Deadline to get the render executable.
    def RenderExecutable( self ):
        return self.Executable

    ## Called by Deadline to get the render arguments.
    def RenderArgument( self ):
        arguments = ""

        drServerNoGui = self.deadlinePlugin.GetBooleanConfigEntryWithDefault( "DRServerNoGui", False )
        if drServerNoGui:
            arguments += "--noGui"

        return arguments

    def CheckTimeout( self, timeoutLength ):
        if not self.DRTimeoutStartTime:
            self.DRTimeoutStartTime = DateTime.Now
            return False
        
        timeDifference = DateTime.Now.Subtract( self.DRTimeoutStartTime ).TotalSeconds
        
        return ( timeDifference >= timeoutLength )

    def CheckRenderOccurred( self ):
        return self.RenderOccurred

    def PostRenderTasks( self ):
        self.deadlinePlugin.LogInfo( "Corona DrServer job finished." )

    def HandleDRSessionStarted( self ):
        self.DRActive = True
        self.deadlinePlugin.LogInfo( "Deadline DR Session has started." )
        self.DRTimeoutStartTime = None

    def HandleDRSessionClosed( self ):
        self.DRActive = False
        self.deadlinePlugin.LogInfo( "Deadline DR Session has closed." )
        self.RenderOccurred = True

    def IsDRActive( self ):
        return self.DRActive
