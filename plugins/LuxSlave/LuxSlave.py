from System import *
from System.IO import *
from System.Diagnostics import *
from System.Text.RegularExpressions import *

import re

from Deadline.Scripting import *
from Deadline.Plugins import *

from FranticX.Processes import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return LuxSlavePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the LuxSlave plugin.
######################################################################
class LuxSlavePlugin( DeadlinePlugin ):

    Executable = ""
    LuxProcess = None
    ProcessName = "LuxSlave"
    ExistingSlaveProcess = "Fail On Existing Process"
    SlaveAutoClose = False
    SlaveCloseTimeout = 10

    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob        

    def Cleanup( self ):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback

        if self.LuxSlaveProcess:
            self.LuxSlaveProcess.Cleanup()
            del self.LuxSlaveProcess

    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        self.LogInfo( "Lux Slave Plugin Initializing..." )
        self.SingleFramesOnly=True
        self.PluginType = PluginType.Advanced
        self.ProcessPriority = ProcessPriorityClass.Idle
        self.HideDosWindow = True

    def StartJob( self ):
        exeList = self.GetConfigEntry( "Luxconsole_ConsoleExecutable" )
        self.Executable = FileUtils.SearchFileList( exeList )
        if( self.Executable == "" ):
            self.FailRender( "No luxconsole.exe file found in the semicolon separated list \"" + exeList + "\". The path to the console executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        else:
            self.LogInfo( "Executable: %s" % self.Executable )

        self.ExistingSlaveProcess = self.GetConfigEntryWithDefault( "ExistingSlaveProcess", "Fail On Existing Process" )
        self.LogInfo( "Existing Slave Process: %s" % self.ExistingSlaveProcess )

        processName = Path.GetFileNameWithoutExtension( self.Executable )
        if( ProcessUtils.IsProcessRunning( processName ) ):
            processes = Process.GetProcessesByName( processName )
            
            if len( processes ) > 0:
                self.LogWarning( "Found existing '%s' process" % processName )
                process = processes[ 0 ]

                if( self.ExistingSlaveProcess == "Fail On Existing Process" ):
                    if process != None:
                        self.FailRender( "Fail On Existing Process is enabled, and a process '%s' with pid '%d' exists - shut down this copy of luxconsole -slave. Ensure luxconsole is NOT already running! (GUI or Service Mode)" % (processName, process.Id) )

                if( self.ExistingSlaveProcess == "Kill On Existing Process" ):
                    if( ProcessUtils.KillProcesses( processName ) ):
                        if process != None:
                            self.LogInfo( "Successfully Killed luxconsole process: '%s' with pid: '%d'" % (processName, process.Id) )

                        SystemUtils.Sleep(5000)

                        if( ProcessUtils.IsProcessRunning( processName ) ):
                            self.LogWarning( "Luxconsole slave is still running: '%s' process, perhaps due to it being automatically restarted after the previous kill command. Ensure Luxconsole is NOT already running! (GUI or Service Mode)" % processName )
                            process = Process.GetProcessesByName( processName )[ 0 ]
                            if process != None:
                                self.FailRender( "Kill On Existing Process is enabled, and a process '%s' with pid '%d' still exists after executing a kill command. Ensure Luxconsole -slave is NOT already running! (GUI or Service Mode)" % (processName, process.Id) )

        self.SlaveAutoClose = self.GetBooleanConfigEntryWithDefault( "SlaveAutoClose", False )
        self.LogInfo( "Slave Auto Close: %s" % self.SlaveAutoClose )

        self.SlaveCloseTimeout = self.GetIntegerConfigEntryWithDefault( "SlaveCloseTimeout", 10 )
        self.LogInfo( "Slave Close Timeout: %s seconds" % self.SlaveCloseTimeout )

    def RenderTasks( self ):
        self.LuxProcess = LuxSlaveProcess( self, self.Executable )
 
        if self.SlaveAutoClose:

            # When doing auto-closing, start process and then enter loop below.
            self.StartMonitoredManagedProcess( self.ProcessName, self.LuxProcess )

            timeout = 0
            while( True ):
                if self.IsCanceled():
                    self.FailRender( "Received cancel task command from Deadline." )
                   
                self.VerifyMonitoredManagedProcess( self.ProcessName )
                self.FlushMonitoredManagedProcessStdout( self.ProcessName )
               
                # Reset the timeout if Luxconsole -slave is active.
                if self.LuxProcess.IsSlaveActive():
                    timeout = 0
                else:
                    # Luxconsole -slave is inactive, so increase the timer by 1 (because we sleep for 1 second each loop).
                    timeout = timeout + 1
                    
                    # If the timeout is reached, break out of the loop so that RenderTasks can exit, which means the task is complete.
                    if timeout >= self.SlaveCloseTimeout:
                        self.LogInfo( "Exiting Luxconsole application and marking task as completed due to Session Auto Timeout: %s seconds." % self.SlaveCloseTimeout )
                        break
                   
                # Sleep for 1 second between loops.
                SystemUtils.Sleep(1000)
        else:
            # Not doing auto closing, so just run indefinitely.
            self.RunManagedProcess( self.LuxProcess )

    def EndJob( self ):
        self.LogInfo( "Ending Lux Slave Job" )
        self.ShutdownMonitoredManagedProcess( self.ProcessName )

######################################################################
## This is the class that starts up the LuxConsoleSlave process.
######################################################################
class LuxSlaveProcess( ManagedProcess ):
    deadlinePlugin = None
    Executable = ""
    SlaveActive = True

    def __init__( self, deadlinePlugin, executable ):
        self.deadlinePlugin = deadlinePlugin
        self.Executable = executable

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
        self.ProcessPriority = ProcessPriorityClass.Idle
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        self.HideDosWindow = True

        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( ".*New session ID.*" ).HandleCallback += self.HandleSlaveSessionStarted
        self.AddStdoutHandlerCallback( ".*Master ended session.*" ).HandleCallback += self.HandleSlaveSessionClosed
        threadId = self.deadlinePlugin.GetThreadNumber()
        self.AddStdoutHandlerCallback( ".*INFO : %s\\] (.*)" % threadId ).HandleCallback += self.HandleRenderStatusProgress
        self.AddStdoutHandlerCallback( ".*INFO : %s\e\\[%sm\\] (.*)" % (threadId, threadId) ).HandleCallback += self.HandleRenderStatusProgress

    def PreRenderTasks( self ):
        self.deadlinePlugin.LogInfo( "Lux Slave Job Starting..." )

    ## Called by Deadline to get the console executable.
    def RenderExecutable( self ):
        return self.Executable

    ## Called by Deadline to get the console arguments.
    def RenderArgument( self ):
        arguments = "--server"

        portNumber = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "PortNumber", "18018" )
        if portNumber != "":
            arguments += " --serverport %s" % portNumber
        self.deadlinePlugin.LogInfo( "Server Port: %s" % portNumber )

        serverWriteFlm = self.deadlinePlugin.GetBooleanConfigEntryWithDefault( "ServerWriteFlm", False )
        if serverWriteFlm:
            arguments += " --serverwriteflm"
        self.deadlinePlugin.LogInfo( "Server Write Flm: %s" % serverWriteFlm )

        cacheDir = self.deadlinePlugin.GetConfigEntryWithDefault( "CacheDir", "" )
        if cacheDir != "":
            arguments += " --cachedir \"%s\"" % cacheDir
            self.deadlinePlugin.LogInfo( "Cache Directory: %s" % cacheDir )
        else:
            self.deadlinePlugin.LogInfo( "Cache Directory: DEFAULT" )

        threads = self.deadlinePlugin.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if threads == 0:
            threads = Environment.ProcessorCount
        arguments += " --threads " + str(threads)
        self.deadlinePlugin.LogInfo( "Rendering with " + str(threads) +" thread(s)" )

        verbosity = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "Verbosity", "None" )
        if verbosity == "Verbose (Debug)":
            arguments += " --verbose"
        self.deadlinePlugin.LogInfo( "Verbosity Level set to: %s" % verbosity )

        return arguments

    def PostRenderTasks( self ):
        self.deadlinePlugin.LogInfo( "Lux Slave Job Finished." )

    def HandleSlaveSessionStarted( self ):
        self.SlaveActive = True
        self.deadlinePlugin.LogInfo( "Deadline Luxconsole Slave Session has Started." )

    def HandleSlaveSessionClosed( self ):
        self.SlaveActive = False
        self.deadlinePlugin.LogInfo( "Deadline Luxconsole Slave Session has Ended." )

    def IsSlaveActive( self ):
        return self.SlaveActive

    def HandleRenderStatusProgress( self ):
        if re.match( r"", self.GetRegexMatch( 0 ) ):
            msg = self.GetRegexMatch( 1 )
            self.deadlinePlugin.SetStatusMessage( msg )
