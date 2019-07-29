import tempfile
import os
import re

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
    return VraySpawnerPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the VraySpawner plugin.
######################################################################
class VraySpawnerPlugin( DeadlinePlugin ):

    def __init__( self ):
        self.Version = ""
        self.Executable = ""
        self.VrayProcess = None
        self.ProcessName = "VraySpawner"
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

        if self.VrayProcess:
            self.VrayProcess.Cleanup()
            del self.VrayProcess

    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        self.LogInfo( "V-Ray Spawner Plugin Initializing..." )
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Advanced
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.HideDosWindow = True

    def StartJob( self ):
        self.Version = self.GetPluginInfoEntryWithDefault( "Version", "" )
        self.LogInfo( "Application - Version: %s" % self.Version )

        vrayExeList = self.GetConfigEntry("VRaySpawnerExecutable_" + self.Version)
        self.Executable = FileUtils.SearchFileList( vrayExeList )
        if( self.Executable == "" ):
            self.FailRender( self.Version + " V-Ray Spawner or Slave or Standalone executable was not found in the semicolon separated list \"" + vrayExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        else:
            self.LogInfo( "Executable: %s" % self.Executable )

        if( SystemUtils.IsRunningOnWindows() ):
            try:
                vrayExeVersion = FileVersionInfo.GetVersionInfo( self.Executable )
                self.LogInfo( "Executable version: %s" % vrayExeVersion.FileVersion )
            except:
                self.LogWarning( "Executable version could not be retrieved." )

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
                        self.FailRender( "Fail On Existing Process is enabled, and a process '%s' with pid '%d' exists - shut down this copy of V-Ray Slave/Spawner. Ensure V-Ray Spawner is NOT already running! (GUI or Service Mode)" % (processName, process.Id) )

                if( self.ExistingDRProcess == "Kill On Existing Process" ):
                    if( ProcessUtils.KillProcesses( processName ) ):
                        if process != None:
                            self.LogInfo( "Successfully killed V-Ray Slave/Spawner process: '%s' with pid: '%d'" % (processName, process.Id) )

                        SystemUtils.Sleep( 5000 )

                        if( ProcessUtils.IsProcessRunning( processName ) ):
                            self.LogWarning( "V-Ray Spawner is still running: '%s' process, perhaps due to it being automatically restarted after the previous kill command. Ensure V-Ray Spawner is NOT already running! (GUI or Service Mode)" % processName )
                            process = Process.GetProcessesByName( processName )[ 0 ]
                            if process != None:
                                self.FailRender( "Kill On Existing Process is enabled, and a process '%s' with pid '%d' still exists after executing a kill command. Ensure V-Ray Spawner is NOT already running! (GUI or Service Mode)" % (processName, process.Id) )

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
        
        self.VrayProcess = VraySpawnerProcess( self, self.Executable, self.Version, waitforRender )

        # Start process and then enter loop below.
        self.StartMonitoredManagedProcess( self.ProcessName, self.VrayProcess )

        timeout = 0
        logFileLoc = 0 # Each new V-Ray DBR process purges the log file's contents, so always start read from beginning of file

        if self.Version[:3] == "Max":
            spawnerLogFile, spawnerLogFileLoc = self.GetSpawnerLogFile() # Retrieve name of spawner log file and the starting byte to read from.
            logFile = self.GetLogFile() # Retrieve name of log file.

        while( True ):
            if self.IsCanceled():
                self.FailRender( "Received cancel task command from Deadline." )
               
            self.VerifyMonitoredManagedProcess( self.ProcessName )
            self.FlushMonitoredManagedProcessStdout( self.ProcessName )
            
            if self.DRAutoClose:
                # Reset the timeout if V-Ray is active.
                if not self.VrayProcess.IsDRActive():
                    # V-Ray is inactive, so increase the timer by 1 (because we sleep for 1 second each loop).                    
                    # If the timeout is reached, break out of the loop so that RenderTasks can exit, which means the task is complete.
                    if self.VrayProcess.CheckRenderOccurred() and self.VrayProcess.CheckTimeout( self.DRCloseTimeoutAfterRender ):
                        self.LogInfo( "Exiting DR Process and marking task as completed due to Deadline DR Session Auto After Render Timeout: %s seconds." % self.DRCloseTimeoutAfterRender )
                        break
                    elif not self.VrayProcess.CheckRenderOccurred() and self.VrayProcess.CheckTimeout( self.DRCloseTimeoutBeforeRender ):
                        self.LogInfo( "Exiting DR Process and marking task as completed due to Deadline DR Session Auto Before Render Timeout: %s seconds." % self.DRCloseTimeoutBeforeRender )
                        break
            
            if self.Version[:3] == "Max":
                spawnerLogFileLoc = self.GetSpawnerLog( spawnerLogFile, spawnerLogFileLoc )
                logFileLoc = self.GetVrayLog( logFile, logFileLoc )

            # Sleep for 1 second between loops.
            SystemUtils.Sleep( 1000 )

    def GetSpawnerLog( self, filename, location ):
        READ_BUFFER = 1024
        newLoc = location
        logContents = ""
        fileSize = os.path.getsize( filename )

        with open( filename, "rb" ) as f:
            f.seek( location )
            logContents = f.read( READ_BUFFER )

            while True:
                if "\n" in logContents: # At least one complete line was parsed in.
                    lines = logContents.split( "\n" )
                    for i in range( len( lines ) - 1 ):
                        self.LogStdout( "SPAWNER: " + re.sub('.*\[.*\]\s{4}', '', lines[i], 1 ) + "\n" )

                    logContents = lines[len(lines)-1]

                remSize = fileSize - newLoc # Remaining bytes in the file as of right now.
                # If nothing is left in the file at all, we need to stop reading right away.
                if remSize == 0:
                    break
                elif remSize < READ_BUFFER:  # Are there 'READ_BUFFER' bytes of data left in the file? If not, don't go past EOF!
                    logContents += f.read( remSize )
                    newLoc += remSize
                else:
                    logContents += f.read( READ_BUFFER )
                    newLoc += READ_BUFFER

        return newLoc

    def GetVrayLog( self, filename, location ):
        READ_BUFFER = 1024
        newLoc = location
        logContents = ""
        fileSize = os.path.getsize( filename )
        
        with open( filename, "rb" ) as f:
            f.seek( location )
            logContents = f.read( READ_BUFFER )

            while True:
                if "\n" in logContents: # At least one complete line was parsed in.

                    # Check to see if this was a start/stop command.
                    if "Starting DR" in logContents:
                        self.VrayProcess.HandleDRSessionStarted()
                    elif "Closing DR" in logContents or "Exiting thread procedure" in logContents:
                        self.VrayProcess.HandleDRSessionClosed()

                    # Break up contents by line breaks
                    lines = logContents.split( "\n" )
                    for i in range(len(lines)-1): # Dump all complete lines found, except the last line.
                        self.LogStdout( "VRAY: " + re.sub('\[.*\]\s{1}', '', lines[i], 1) + "\n" ) # This doesn't get passed to the stdout handlers in the vray spawner class. That is what the checks above are for.

                    logContents = lines[len(lines)-1] # Save everything after the last line break. This will either be an empty string or an incomplete line.

                remSize = fileSize - newLoc # Remaining bytes in the file as of right now.
                # If nothing is left in the file at all, we need to stop reading right away.
                if remSize == 0:
                    break
                elif remSize < READ_BUFFER:  # Are there 'READ_BUFFER' bytes of data left in the file? If not, don't go past EOF!
                    logContents += f.read( remSize )
                    newLoc += remSize
                else:
                    logContents += f.read( READ_BUFFER )
                    newLoc += READ_BUFFER

        return newLoc

    def GetSpawnerLogFile( self ):
        spawnerLogFile = tempfile.gettempdir()
        spawnerLogFile += r"\VRSpawner.log"

        try:
            spawnerLogFileLoc = os.path.getsize( spawnerLogFile )
        except: # Log file not yet generated.
            spawnerLogFileLoc = 0
            open( spawnerLogFile, 'a' ) # Create a blank log file, its contents will be written to by vrayspawnerYYYY.exe.

        return spawnerLogFile, spawnerLogFileLoc

    def GetLogFile( self ):
        logFile = tempfile.gettempdir() # %temp%, robust to OS.
        logFile += r"\vraylog.txt"
        
        if not File.Exists( logFile ):
            open( logFile, 'a' ) # Create a blank log file, its contents will be written to by V-Ray later.

        return logFile

    def EndJob( self ):
        self.LogInfo( "Ending V-Ray Spawner/Standalone Job" )
        self.ShutdownMonitoredManagedProcess( self.ProcessName )

######################################################################
## This is the class that starts up the VraySpawner process.
######################################################################
class VraySpawnerProcess( ManagedProcess ):
    
    def __init__( self, deadlinePlugin, executable, version, startActive ):
        self.deadlinePlugin = deadlinePlugin
        self.Executable = executable
        self.Version = version
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
        self.AddStdoutHandlerCallback(".*Starting DR.*").HandleCallback += self.HandleDRSessionStarted
        self.AddStdoutHandlerCallback(".*Closing DR.*").HandleCallback += self.HandleDRSessionClosed
        self.AddStdoutHandlerCallback(".*Exiting thread procedure.*").HandleCallback += self.HandleDRSessionClosed

        # Ignore 3dsMax MAXScript Debugger Popup (ENU, FRA, DEU, JPN, CHS, KOR, PTB)
        self.AddPopupIgnorer( "MAXScript .*" ) #ENU #JPN #CHS #KOR
        self.AddPopupIgnorer( ".* MAXScript" ) #FRA #PTB
        self.AddPopupIgnorer( "MAXScript-Debugger" ) #DEU

        # For Maxwell
        self.AddPopupIgnorer( ".*Maxwell Translation Window.*" )
        self.AddPopupIgnorer( ".*Import Multilight.*" )

        # Handle Program Compatibility Assistant dialog
        self.AddPopupHandler( "Program Compatibility Assistant", "Close" )

        # If we're overriding CPU Affinity, ensure it works for V-Ray by setting their environment variable
        if self.deadlinePlugin.OverrideCpuAffinity():
            self.deadlinePlugin.LogInfo( "Setting VRAY_USE_THREAD_AFFINITY to 0 to ensure CPU Affinity works." )
            self.SetEnvironmentVariable( "VRAY_USE_THREAD_AFFINITY", "0" )

        # Only V-Ray RT uses the GPU
        if self.Version.startswith( "MaxRT" ):
            # Check if we are overriding GPU affinity
            if self.deadlinePlugin.OverrideGpuAffinity():
                selectedGPUs = self.deadlinePlugin.GpuAffinity()
                
                if len(selectedGPUs) > 0:
                    vrayGpus = "index" + ";index".join( [ str( gpu ) for gpu in selectedGPUs ] ) # "index0;index1"
                    self.deadlinePlugin.LogInfo( "This Slave is overriding its GPU affinity, so the following GPUs will be used by V-Ray RT: %s" % vrayGpus )
                    self.SetEnvironmentVariable( "VRAY_OPENCL_PLATFORMS_x64", vrayGpus )

    def PreRenderTasks( self ):
        self.deadlinePlugin.LogInfo( "V-Ray Spawner/Standalone job starting..." )

    ## Called by Deadline to get the render executable.
    def RenderExecutable( self ):
        return self.Executable

    ## Called by Deadline to get the render arguments.
    def RenderArgument( self ):
        arguments = ""

        if Path.GetFileNameWithoutExtension( self.Executable ) == "vray":

            # Newer versions of V-Ray Standalone do not require this switch when in "-server" mode.
            # However, it doesn't cause any harm and is left in to support older versions of V-Ray Standalone.
            if self.Version.startswith( "MaxRT" ):
                arguments += "-rtEngine=1 "

            arguments += "-server "

            portNumber = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "PortNumber", "" )
            if portNumber != "":
                arguments += "-portNumber=%s " % portNumber

            verbosity = self.deadlinePlugin.GetConfigEntryWithDefault( "VerboseLevel", "3" ).split(' ')[0]
            arguments += "-verboseLevel=%s" % verbosity

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
        self.deadlinePlugin.LogInfo( "V-Ray Spawner/Standalone job finished." )

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
