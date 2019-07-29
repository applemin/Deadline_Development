import os
import time

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *

from FranticX.Processes import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return FusionPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
######################################################################
## This is the main DeadlinePlugin class for the FusionPlugin plugin.
######################################################################
class FusionPlugin (DeadlinePlugin):
    version = 0
    renderExecutable = ""
    scriptExecutable = ""
    waitForExecutable = ""
    loadFlowTimeout = 0
    scriptConnectTimeout = 0
    usingRenderSlave = False
    
    logPath = ""
    logFileValid = False
    logFileSize = 0
    logFilePostfix = ""
    logFileError = ""
    logLastLine = ""
    
    fusionProcess = None
    startJobProcess = None
    renderTasksProcess = None
    endJobProcess = None
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob
    
    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback
        
        if self.fusionProcess:
            self.fusionProcess.Cleanup()
            del self.fusionProcess
        
        if self.startJobProcess:
            self.startJobProcess.Cleanup()
            del self.startJobProcess
            
        if self.renderTasksProcess:
            self.renderTasksProcess.Cleanup()
            del self.renderTasksProcess
            
        if self.endJobProcess:
            self.endJobProcess.Cleanup()
            del self.endJobProcess
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings. Because this is an advanced plugin,
        # we do not need to set the process specific settings here.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Advanced
    
    ## Called by Deadline when the job is first loaded. This will start up Fusion
    ## and tell it to load the flow.
    def StartJob( self ):
        # Get the version of Fusion we're rendering with.
        self.version = int( self.GetFloatPluginInfoEntry( "Version" ) )
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        # Get the executable to be used for rendering.
        renderExecutableList = self.GetConfigEntry( "Fusion%dRenderExecutable" % self.version )
        
        isWindows = SystemUtils.IsRunningOnWindows()
        
        if isWindows:
            if build == "32bit":
                self.renderExecutable = FileUtils.SearchFileListFor32Bit( renderExecutableList )
                if( self.renderExecutable == "" ):
                    self.LogWarning( "32 bit Fusion %d render executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % (self.version, renderExecutableList) )
            elif build == "64bit":
                self.renderExecutable = FileUtils.SearchFileListFor64Bit( renderExecutableList )
                if( self.renderExecutable == "" ):
                    self.LogWarning( "64 bit Fusion %d render executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % (self.version, renderExecutableList) )
            
        if( self.renderExecutable == "" ):
            self.renderExecutable = FileUtils.SearchFileList( renderExecutableList )
            if( self.renderExecutable == "" ):
                self.FailRender( "Fusion %d render executable could not be found in the semicolon separated list \"%s\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." % (self.version, renderExecutableList) )
        
        self.usingRenderSlave = False
        exeFilename = Path.GetFileName( self.renderExecutable ).lower()
        if "renderslave" in exeFilename or "fusion.exe" in exeFilename or not exeFilename.endswith( "fusion" ):
            self.usingRenderSlave = True
        
        # Get the script executable name from the render executable.
        # In version 8+, it is called "FuScript", in previous versions it's called "eyeonScript".
        # It appears we can execute Fusion 8 comps on Fusion 7 nodes, so we use "FuScript" if it exists, but fall back on "eyeonScript" if it's not there (indicating an older version typically).
        scriptExecutableDir = Path.GetDirectoryName( self.renderExecutable )
        scriptExecutableExt = ""
        if isWindows:
            scriptExecutableExt = ".exe"
        fuScriptExecutable = Path.Combine( scriptExecutableDir, "fuscript" + scriptExecutableExt )
        eyeonScriptExecutable = Path.Combine( scriptExecutableDir, "eyeonScript" + scriptExecutableExt )

        if self.version >= 8:
            self.scriptExecutable = fuScriptExecutable
            if not File.Exists( fuScriptExecutable ) and File.Exists( eyeonScriptExecutable ):
                self.scriptExecutable = eyeonScriptExecutable
                self.LogWarning( "FuScript" + scriptExecutableExt + " was not found in the Fusion program directory. Falling back to using eyeonScript" + scriptExecutableExt + ". This indicates a possible version mismatch on the render node.")
        else:
            self.scriptExecutable = eyeonScriptExecutable
        
        # Get the name of the executable to wait for, if there is one.
        self.waitForExecutable = self.GetConfigEntryWithDefault( "Fusion%dWaitForExecutable" % self.version, "" )
        
        # Get the timeout for initially loading the Fusion flow.
        self.loadFlowTimeout = self.GetIntegerConfigEntryWithDefault( "LoadFlowTimeout", 120 )
        
        # Get the timeout for Fusion to startup and accept a script connection.
        self.scriptConnectTimeout = self.GetIntegerConfigEntryWithDefault( "ScriptConnectTimeout", 15 )
        
        # Get the timeout for Fusion to startup and start it's script System.
        self.loadScriptSystemTimeout = self.GetIntegerConfigEntryWithDefault( "LoadScriptSystemTimeout", 15 )
        
        # Get rid of any stranded fusion processes.
        if isWindows:
            if self.waitForExecutable != "":
                if ProcessUtils.IsProcessRunning( self.waitForExecutable ) and not ProcessUtils.KillProcesses( self.waitForExecutable ):
                    self.FailRender( "Could not terminate existing FusionWaitForExecutable process %s" % self.waitForExecutable )
        
            if ProcessUtils.IsProcessRunning( Path.GetFileName( self.renderExecutable ) ) and not ProcessUtils.KillProcesses( Path.GetFileName( self.renderExecutable ) ):
                self.FailRender( "Could not terminate existing FusionRenderExecutable process %s" % Path.GetFileName( self.renderExecutable ) )
            
            if ProcessUtils.IsProcessRunning( Path.GetFileName( self.scriptExecutable ) ) and not ProcessUtils.KillProcesses( Path.GetFileName( self.scriptExecutable ) ):
                self.FailRender( "Could not terminate existing ScriptExecutable process %s" % Path.GetFileName( self.scriptExecutable ) )
        
            # Don't allow render to continue if Fusion is currently running on the machine.
            if ProcessUtils.IsProcessRunning( "Fusion.exe" ):
                self.FailRender( "Fusion 5 or later is running on this machine - close it to allow network renders." )
        
        # Get the global preference file, if there is one specified.
        preferenceFile = self.GetConfigEntry( "Fusion%dSlavePreferenceFile" % self.version )
        if preferenceFile != "":
            # Perform path mapping on preference file (Fusion 8 and later only).
            if self.version >= 8:
                preferenceFile = RepositoryUtils.CheckPathMapping( preferenceFile )
                preferenceFile = PathUtils.ToPlatformIndependentPath( preferenceFile )
            
            if not File.Exists( preferenceFile ):
                self.FailRender( "Render Slave preference file \"%s\" does not exist. The path to the Render Slave preference file can be configured from the Plugin Configuration in the Deadline Monitor." % preferenceFile )
            
            # Version 5 and later just needs to set an environment variable.
            self.LogInfo( "Updating FUSION_MasterPrefs environment variable to point to Render Slave preference file \"%s\"" % preferenceFile )
            self.SetProcessEnvironmentVariable( "FUSION_MasterPrefs", preferenceFile )
            self.LogInfo( "Render Slave preference file set successfully" )
        
        # Set log path
        self.logPath = Path.Combine( self.CreateTempDirectory( "fusionLog" ), "fusion.log" )
        if File.Exists( self.logPath ):
            File.Delete( self.logPath )
        self.LogStart()
        
        self.FusionScriptingInitialized = False
        
        # Start up the fusion render slave.
        self.fusionProcess = FusionProcess(self)
        self.StartMonitoredManagedProcess( "Fusion", self.fusionProcess )
        
        # Wait for the WaitForExecutable to start, if necessary.
        if self.waitForExecutable != "" and not ProcessUtils.WaitForProcessToStart( self.waitForExecutable, 60000 ):
            self.FailFusionRender( "The FusionWaitForExecutable process %s failed to start after 60 seconds" % self.waitForExecutable )	

        # The "...scripting initialized..." stdout message does not appear on Fusion Studio for Linux
        scriptingInitializeCheckRequired = self.usingRenderSlave or not SystemUtils.IsRunningOnLinux()
        
        if scriptingInitializeCheckRequired:
            startTime = time.time()
            while scriptingInitializeCheckRequired and not self.FusionScriptingInitialized and self.logFileValid and ((time.time() - startTime) < self.loadScriptSystemTimeout):
                self.FlushFusionOutput( False )
                if self.IsCanceled():
                    self.FailFusionRender( "Received cancel task command" )
                time.sleep(1)
            else:
                if self.logFileValid:
                    if self.FusionScriptingInitialized:
                        self.LogInfo( "Fusion Scripting has been Initialized." )
                    else:
                        self.LogInfo( "Fusion Scripting has timed out." )
                else:
                    self.LogInfo( "Unable to connect to log file.  Attempting to render." )
        
        # Check if this is a Fusion Quicktime job.
        if self.GetBooleanPluginInfoEntryWithDefault( "QuicktimeJob", False ):
            self.LogInfo( "This is a Quicktime job" )
            
        else:
            # Now run the start job process which will communicate with the render slave application.
            self.startJobProcess = StartJobProcess(self)
            self.StartMonitoredManagedProcess( "StartJob", self.startJobProcess )
            self.SetMonitoredManagedProcessExitCheckingFlag( "StartJob", False )
            
            while not self.WaitForMonitoredManagedProcessToExit( "StartJob", 500 ):
                self.FlushMonitoredManagedProcessStdout( "StartJob" )
                
                blockingDialogMessage = self.CheckForMonitoredManagedProcessPopups( "StartJob" )
                if( blockingDialogMessage != "" ):
                    self.FailFusionRender( blockingDialogMessage )
                
                self.FlushFusionOutput( False )
                
                blockingDialogMessage = self.CheckForMonitoredManagedProcessPopups( "Fusion" )
                if( blockingDialogMessage != "" ):
                    self.FailFusionRender( blockingDialogMessage )
                
                self.VerifyMonitoredManagedProcess( "Fusion" )
                
                if self.IsCanceled():
                    self.FailFusionRender( "Received cancel task command" )
            
            self.FlushFusionOutput( False )
            
            startJobExitCode = self.GetMonitoredManagedProcessExitCode( "StartJob" )
            self.LogInfo( "StartJob returned exit code " + str(startJobExitCode ) )
            exitSuccess = self.startJobProcess.GetExitSuccess()
                
            if not exitSuccess:
                self.FailFusionRender( "StartJob Fusion script exited before finishing, it may have been terminated externally" )

        self.FlushFusionOutput( False )
    
    ## This is called by Deadline when a task is to be rendered. This will tell the already
    ## running instance of Fusion to render specific frames.
    def RenderTasks( self ):
        # Run the render tasks process which will communicate with the render slave application.
        self.renderTasksProcess = RenderTasksProcess(self)
        self.StartMonitoredManagedProcess( "RenderTasks", self.renderTasksProcess )
        self.SetMonitoredManagedProcessExitCheckingFlag( "RenderTasks", False )
        
        while( not self.WaitForMonitoredManagedProcessToExit( "RenderTasks", 500 ) ):
            self.FlushMonitoredManagedProcessStdout( "RenderTasks" )
            
            blockingDialogMessage = self.CheckForMonitoredManagedProcessPopups( "RenderTasks" )
            if( blockingDialogMessage != "" ):
                self.FailFusionRender( blockingDialogMessage )
            
            self.FlushFusionOutput( False )
            
            blockingDialogMessage = self.CheckForMonitoredManagedProcessPopups( "Fusion" )
            if( blockingDialogMessage != "" ):
                self.FailFusionRender( blockingDialogMessage )
            
            self.VerifyMonitoredManagedProcess( "Fusion" )
            
            if self.IsCanceled():
                self.FailFusionRender( "Received cancel task command" )
        
        self.FlushMonitoredManagedProcessStdout( "RenderTasks" )
        self.FlushFusionOutput( False )
        
        renderTasksExitCode = self.GetMonitoredManagedProcessExitCode( "RenderTasks" )
        self.LogInfo( "RenderTasks returned exit code " + str(renderTasksExitCode ) )
        
        exitSuccess = self.renderTasksProcess.GetExitSuccess()
            
        if not exitSuccess:
            self.FailFusionRender( "RenderTasks Fusion script exited before finishing, it may have been terminated externally")
        
        self.FlushFusionOutput( False )
    
    ## This is called by Deadline when a job is unloaded. This will tell the already
    ## running instance of Fusion to shut down.
    def EndJob( self ):
        # Flush the remaining stdout and then shutdown Fusion.
        self.FlushFusionOutput( True )
        
        # This doesn't always shutdown Fusion reliably, so we manually kill it if necessary.
        self.SetMonitoredManagedProcessExitCheckingFlag( "Fusion", False )
        
        self.endJobProcess = EndJobProcess(self)
        self.StartMonitoredManagedProcess( "EndJob", self.endJobProcess )
        self.SetMonitoredManagedProcessExitCheckingFlag( "EndJob", False )
        
        self.WaitForMonitoredManagedProcessToExit( "EndJob", 5000 )
        self.ShutdownMonitoredManagedProcess( "EndJob" )
        
        self.WaitForMonitoredManagedProcessToExit( "Fusion", 5000 )
        self.ShutdownMonitoredManagedProcess( "Fusion" )
    
    def MonitoredManagedProcessExit( self, name ):
        self.FailFusionRender( "Monitored managed process \"" + name + "\" has exited or been terminated." )
        
    def LogUpdate(self):
        self.logFileSize = 0
        if File.Exists( self.logPath ):
            self.logFileSize = FileUtils.GetFileSize( self.logPath )
            
        if( self.logFileSize > 0 ):
            stream = FileStream( self.logPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite )
            reader = StreamReader( stream )
            reader.BaseStream.Seek( max( self.logFileSize - 192, 0 ), SeekOrigin.Begin )
            self.logFilePostfix = reader.ReadToEnd()
            reader.Close()
            stream.Close()
        else:
            self.logFileSize = 0
            self.logFilePostfix = ""

    def LogStart(self):
        self.logFileValid = False
        self.logFileError = ""
        try:
            self.LogUpdate()
            self.logFileValid = True
        except IOException as e:
            self.LogWarning( "Cannot start Fusion log because: " + e.Message )
            self.logFileError = e.Message

    def LogFlush(self, inEndJob):
        if self.logFileValid:
            try:
                if File.Exists( self.logPath ):
                    stream = FileStream( self.logPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite )
                    reader = StreamReader( stream )
                    if( self.logFileSize >= 0 ):
                        reader.BaseStream.Seek( max( self.logFileSize - 2048, 0 ), SeekOrigin.Begin )
                    networkLog = reader.ReadToEnd()
                    reader.Close()
                    stream.Close()
                    
                    networkLogLines = None
                    
                    index = networkLog.find( self.logFilePostfix )
                    if( self.logFilePostfix == "" or index < 0 ):
                        networkLogLines = networkLog.splitlines()
                    else:
                        networkLogLines = networkLog[index + len( self.logFilePostfix ):].splitlines()
                    
                    for line in networkLogLines:
                        trimmedLine = line.strip()
                        if trimmedLine.startswith( "LOG:" ):
                            self.LogInfo( trimmedLine )
                        else:
                            self.LogInfo( "LOG: " + trimmedLine )
                        
                        if "Initialising Scripting Subsystem" in trimmedLine:
                            self.FusionScriptingInitialized = True
                            
                        # Don't check for errors when in EndJob
                        if not inEndJob:
                            if trimmedLine.startswith( "SCRIPT ERROR: " ):
                                self.FailFusionRenderInternal( trimmedLine, False )
                    
                    networkLogLineCount = len( networkLogLines )
                    if networkLogLineCount > 0:
                        self.logLastLine = networkLogLines[ networkLogLineCount - 1 ]
                else:
                    self.LogInfo( "Fusion log file does not exist yet: " + self.logPath )
                    #self.logFileValid = False
                
                self.LogUpdate()
                
            except IOException as e:
                self.LogWarning( "Cannot read from Fusion log because: " + e.Message )
                self.logFileValid = False

    def FlushFusionOutput(self, inEndJob):
        if self.usingRenderSlave:
            self.LogFlush( inEndJob )
        else:
            if inEndJob:
                self.FlushMonitoredManagedProcessStdoutNoHandling( "Fusion" )
            else:
                self.FlushMonitoredManagedProcessStdout( "Fusion" )

    def FailFusionRender(self, message):
        self.FailFusionRenderInternal( message, True )

    def FailFusionRenderInternal(self, message, flushOutput):
        # Check if the an error is occurring immediately after Fusion is checking for a license.
        if self.usingRenderSlave:
            if self.logLastLine.lower().find( "checking for licenses" ) != -1 or self.logLastLine.lower().find( "obtain license" ) != -1:
                message += " -- Based on the last line that was written to the Fusion log, this error appears to be the result of Fusion not being able to obtain a license."
        
        if flushOutput:
            self.FlushFusionOutput( False )
        
        self.FailRender( message )

######################################################################
## This is the class that starts up the Fusion process.
######################################################################
class FusionProcess (ManagedProcess):
    deadlinePlugin = None
    
    def __init__( self, deadlinePlugin ):
        self.deadlinePlugin = deadlinePlugin
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess( self ):
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        self.HideDosWindow = False # This needs to be off so that we can get stdout from ConsoleSlave
        
        self.AddPopupIgnorer( ".*Queue.*" )
        self.AddPopupIgnorer( ".*Render Manager.*" )
        self.AddPopupIgnorer( ".*Editor.*" )
        self.AddPopupIgnorer( ".*Precision.*" )
        self.AddPopupIgnorer( ".*Taper.*" )
        self.AddPopupIgnorer( "Ease" )
    
    def RenderExecutable( self ):
        if( self.deadlinePlugin.version <= 7 and SystemUtils.IsRunningOnLinux() ):
            winePath = PathUtils.GetApplicationPath( "wine" )
            if winePath == "" or not File.Exists( winePath ):
                self.deadlinePlugin.FailRender( "Wine could not be found in the path on this machine, it is required to run the Linux version of Fusion" )
            return winePath
        else:
            return self.deadlinePlugin.renderExecutable
    
    def RenderArgument( self ):
        argPrefix = ""
        if SystemUtils.IsRunningOnWindows():
            argPrefix = "/"
        else:
            argPrefix = "-"
        
        def formatArgument(argName, argValue=None):
            # Formats a command-line argument based on the Slave's OS
            result = argPrefix + argName
            if isinstance(argValue, basestring):
                result += ' "%s"' % argValue
            return result
        
        arguments = [formatArgument(arg) for arg in ('quiet', 'listen', 'verbose')]

        if self.deadlinePlugin.usingRenderSlave:
            arguments.append(formatArgument("log", self.deadlinePlugin.logPath))
        
        arguments = " ".join(arguments)
        
        if( self.deadlinePlugin.version <= 7 and SystemUtils.IsRunningOnLinux() ):
            return "\"" + self.deadlinePlugin.renderExecutable + "\" " + arguments
        else:
            return arguments

######################################################################
## This is the class that tells the Fusion process to load a flow.
######################################################################
class StartJobProcess (ManagedProcess):
    deadlinePlugin = None
    
    def __init__( self, deadlinePlugin ):
        self.deadlinePlugin = deadlinePlugin
        self.exitSuccess = False
        
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
    
    def InitializeProcess( self ):
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( "SCRIPT ERROR: (.*)" ).HandleCallback += self.HandleStartJobError
        self.AddStdoutHandlerCallback( "Start job complete.").HandleCallback += self.HandleCleanExit

    def RenderExecutable( self ):
        if( self.deadlinePlugin.version <= 7 and SystemUtils.IsRunningOnLinux() ):
            winePath = PathUtils.GetApplicationPath( "wine" )
            if winePath == "" or not File.Exists( winePath ):
                self.deadlinePlugin.FailFusionRender( "Wine could not be found in the path on this machine, it is required to run the Linux version of Fusion" )
            return winePath
        else:
            return self.deadlinePlugin.scriptExecutable
    
    def RenderArgument( self ):
        sceneFilename = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "FlowFile", self.deadlinePlugin.GetDataFilename() )
        sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename )
        sceneFilename = PathUtils.ToPlatformIndependentPath( sceneFilename )
        
        # Perform path mapping on contents of comp file if it's enabled (Fusion 8 and later only).
        if self.deadlinePlugin.version >= 8 and self.deadlinePlugin.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
            tempSceneDirectory = self.deadlinePlugin.CreateTempDirectory( "thread" + str(self.deadlinePlugin.GetThreadNumber()) )            
            tempSceneFileName = Path.Combine( tempSceneDirectory, Path.GetFileName( sceneFilename ) )
            tempSceneFileName = PathUtils.ToPlatformIndependentPath( tempSceneFileName )
            self.pathMappingWithFilePermissionFix( sceneFilename, tempSceneFileName )
            sceneFilename = tempSceneFileName
        
        renderArguments = "\""
        if( self.deadlinePlugin.version <= 7 and SystemUtils.IsRunningOnLinux() ):
            renderArguments = renderArguments + self.deadlinePlugin.scriptExecutable + "\" \""
            
        renderArguments = renderArguments + Path.Combine( self.deadlinePlugin.GetPluginDirectory(), "StartJob.eyeonscript" ) + "\""
        renderArguments = renderArguments + " \"" +sceneFilename + "\" " + str( self.deadlinePlugin.scriptConnectTimeout )
        
        return renderArguments
    
    def PreRenderTasks( self ):
        self.SetUpdateTimeout( self.deadlinePlugin.scriptConnectTimeout + self.deadlinePlugin.loadFlowTimeout )
    
    def HandleStartJobError( self ):
        self.deadlinePlugin.FailFusionRender( self.GetRegexMatch(1) )
        
    def HandleCleanExit( self ):
        self.exitSuccess = True
        
    def GetExitSuccess( self ):
        return self.exitSuccess
        
    def pathMappingWithFilePermissionFix( self, inFileName, outFileName ):        
        RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator( inFileName, outFileName, "\\", "/" )
        if SystemUtils.IsRunningOnLinux() or SystemUtils.IsRunningOnMac():
            os.chmod( outFileName, os.stat( inFileName ).st_mode )

######################################################################
## This is the class that tells the Fusion process to render.
######################################################################
class RenderTasksProcess (ManagedProcess):
    deadlinePlugin = None
    Success = False
    
    def __init__( self, deadlinePlugin ):
        self.deadlinePlugin = deadlinePlugin
        self.exitSuccess = False
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
    
    def InitializeProcess( self ):
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( "SCRIPT ERROR: (.*)" ).HandleCallback += self.HandleRenderTasksError
        self.AddStdoutHandlerCallback( "Render succeeded" ).HandleCallback += self.HandleCleanExit
        
        if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "QuicktimeJob", False ) and self.deadlinePlugin.GetBooleanConfigEntryWithDefault( "ShowQuicktimeProgress", True ):
            self.AddStdoutHandlerCallback( "Progress: ([0-9]+) %" ).HandleCallback += self.HandleQuicktimeProgress
        
    def RenderExecutable( self ):
        if( self.deadlinePlugin.version <= 7 and SystemUtils.IsRunningOnLinux() ):
            winePath = PathUtils.GetApplicationPath( "wine" )
            if winePath == "" or not File.Exists( winePath ):
                self.deadlinePlugin.FailFusionRender( "Wine could not be found in the path on this machine, it is required to run the Linux version of Fusion" )
            return winePath
        else:
            return self.deadlinePlugin.scriptExecutable
    
    def RenderArgument( self ):
        job = self.deadlinePlugin.GetJob()
            
        # Save a temp file containing the plugin info for the job.
        pluginInfoFile = Path.Combine( self.deadlinePlugin.GetJobsDataDirectory(), "pluginInfo" + str(self.deadlinePlugin.GetThreadNumber()) + ".txt" )
        writer = StreamWriter( pluginInfoFile, False, Encoding.Default )
        try:
            pluginInfoTempDict = {}
            pluginInfoTempList = job.GetJobPluginInfoKeys()
            for key in pluginInfoTempList:
                pluginInfoTempDict[key] = RepositoryUtils.CheckPathMapping( job.GetJobPluginInfoKeyValue( key ) )
            
            # Some modifications for quicktime jobs.
            if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "QuicktimeJob", False ):
                artistName = pluginInfoTempDict["QuicktimeArtistName"]
                if len(artistName) == 0:
                    pluginInfoTempDict["QuicktimeArtistName"] = job.JobUserName
                    
                pluginInfoTempDict["QuicktimeComment"] = job.JobComment
                pluginInfoTempDict["QuicktimeDepartment"] = job.JobDepartment
                pluginInfoTempDict["QuicktimeProjectTitle"] = job.JobName
            
            for key in pluginInfoTempDict:
                writer.WriteLine( "%s=%s" % ( key, pluginInfoTempDict[ key ] ) )
        finally:
            writer.Close()
        
        # Get the version of Fusion to enforce, if there is one.
        fusionVersionToEnforce = self.deadlinePlugin.GetConfigEntryWithDefault( "Fusion%dVersionToEnforce" % self.deadlinePlugin.version, "" )
        if fusionVersionToEnforce == "":
            self.deadlinePlugin.LogInfo( "Not enforcing a Fusion version" )
        else:
            self.deadlinePlugin.LogInfo( "Enforcing Fusion version %s" % fusionVersionToEnforce )
        
        renderArguments = ""
        if( self.deadlinePlugin.version <= 7 and SystemUtils.IsRunningOnLinux() ):
            renderArguments = renderArguments + "\"" + self.deadlinePlugin.scriptExecutable + "\""
        
        if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "QuicktimeJob", False ):
            # Build the render arguments.
            renderArguments = renderArguments + " \"" + Path.Combine( self.deadlinePlugin.GetPluginDirectory(), "CreateQuicktime.eyeonscript" ) + "\""
            renderArguments = renderArguments + " " + str( self.deadlinePlugin.GetStartFrame() ) + " " + str( self.deadlinePlugin.GetEndFrame() )
            renderArguments += " " + str( self.deadlinePlugin.GetIntegerPluginInfoEntryWithDefault( "QuicktimeFrameOverride", self.deadlinePlugin.GetStartFrame() ) )
            renderArguments += " " + str( self.deadlinePlugin.GetBooleanConfigEntryWithDefault( "ShowQuicktimeProgress", True ) )
            renderArguments = renderArguments + " \"" + fusionVersionToEnforce + "\""
            renderArguments = renderArguments + " \"" + pluginInfoFile + "\""
            renderArguments = renderArguments + " " + str( self.deadlinePlugin.scriptConnectTimeout )
            
        else:
            # Get some settings.
            highQuality = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "HighQuality", "true" )
            proxy = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "Proxy", "1" )
            checkOutput = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "CheckOutput", "1" )
            
            # Get the auxiliary script, which is used for running Fusion script jobs.
            auxiliaryScript = ""
            auxiliaryFilenames = self.deadlinePlugin.GetAuxiliaryFilenames()
            if len( auxiliaryFilenames ) >= 2:
                auxiliaryScript = auxiliaryFilenames[1]
            
            # Build the render arguments.
            renderArguments = renderArguments + " \"" + Path.Combine( self.deadlinePlugin.GetPluginDirectory(), "RenderTasks.eyeonscript" ) + "\""
            renderArguments = renderArguments + " " + str( self.deadlinePlugin.GetStartFrame() ) + " " + str( self.deadlinePlugin.GetEndFrame() )
            renderArguments = renderArguments + " \"" + fusionVersionToEnforce + "\""
            renderArguments = renderArguments + " \"" + pluginInfoFile + "\""
            renderArguments = renderArguments + " \"" + auxiliaryScript + "\""
        
        return renderArguments
        
    def PreRenderTasks( self ):
        self.Success = False
        self.deadlinePlugin.FlushMonitoredManagedProcessStdout( "Fusion" )
        
    def PostRenderTasks( self ):
        self.deadlinePlugin.FlushMonitoredManagedProcessStdout( "Fusion" )
    
    def HandleQuicktimeProgress( self ):
        self.deadlinePlugin.SetProgress( int(self.GetRegexMatch(1)) )
        self.SuppressThisLine()
    
    def HandleRenderTasksError( self ):
        self.deadlinePlugin.FailFusionRender( self.GetRegexMatch(1) )
        
    def HandleCleanExit( self ):
        self.exitSuccess = True
        
    def GetExitSuccess( self ):
        return self.exitSuccess
    
######################################################################
## This is the class that tells the Fusion process to shut down.
######################################################################
class EndJobProcess (ManagedProcess):
    deadlinePlugin = None
    
    def __init__( self, deadlinePlugin ):
        self.deadlinePlugin = deadlinePlugin
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.CheckExitCodeCallback += self.CheckExitCode
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.CheckExitCodeCallback
    
    def InitializeProcess( self ):
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        
    def RenderExecutable( self ):
        if( self.deadlinePlugin.version <= 7 and SystemUtils.IsRunningOnLinux() ):
            winePath = PathUtils.GetApplicationPath( "wine" )
            if winePath == "" or not File.Exists( winePath ):
                self.deadlinePlugin.FailFusionRender( "Wine could not be found in the path on this machine, it is required to run the Linux version of Fusion" )
            return winePath
        else:
            return self.deadlinePlugin.scriptExecutable
    
    def RenderArgument( self ):
        renderArguments = "\""
        if( self.deadlinePlugin.version <= 7 and SystemUtils.IsRunningOnLinux() ):
            renderArguments = renderArguments + self.deadlinePlugin.scriptExecutable + "\" \""
        
        renderArguments = renderArguments + Path.Combine( self.deadlinePlugin.GetPluginDirectory(), "EndJob.eyeonscript" ) + "\""
        
        return renderArguments
    
    def CheckExitCode( self, exitCode ):
        self.deadlinePlugin.LogInfo( "EndJob Fusion script returned a return code of %d" % exitCode )
