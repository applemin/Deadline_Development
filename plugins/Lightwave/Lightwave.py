from System.Diagnostics import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *

from FranticX.Processes import *

import os

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return LightwavePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Lightwave plugin.
######################################################################
class LightwavePlugin (DeadlinePlugin):
    Executable = ""
    Version = 9.0
    UseFPrime = False
    
    UseScreamerNet = False
    JobFilename = ""
    AckFilename = ""
    ProgramName = ""
    ThreadID = ""
    ScreamerNetProcess = None
    
    TempSceneFileName = ""
    
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
        
        if self.ScreamerNetProcess:
            self.ScreamerNetProcess.Cleanup()
            del self.ScreamerNetProcess
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings. Because this is an advanced plugin,
        # we do not need to set the process specific settings here.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Advanced
        
    ## Called by Deadline when the job is first loaded.
    def StartJob( self ):
        renderExecutableList = ""
        renderingApplication = ""
        
        # Get the Lightwave version.
        self.Version = self.GetFloatPluginInfoEntryWithDefault( "LW_Version", 9.0 )
        
        # Check if we are rendering with Lightwave or FPrime.
        self.UseFPrime = self.GetBooleanPluginInfoEntryWithDefault( "UseFPrime", False )
        if self.UseFPrime:
            self.LogInfo( "Using FPrime for rendering" )
            renderingApplication = "FPrime"
            renderExecutableList = self.GetConfigEntry( "FPrime_RenderExecutable" )
        else:
            renderingApplication = "Lightwave " + str(self.Version)
            renderExecutableList = self.GetConfigEntry( "LW" + str(int(self.Version)) + "_RenderExecutable" )
        
        # Check the build and find the correct render executable.
        build = self.GetPluginInfoEntryWithDefault( "LW_Build", "None" ).lower()
        
        if(SystemUtils.IsRunningOnWindows()):
            if build == "32bit":
                self.LogInfo( "Enforcing 32 bit build of " + renderingApplication )
                self.Executable = FileUtils.SearchFileListFor32Bit( renderExecutableList )
                if self.Executable == "":
                    self.LogWarning( "32 bit " + renderingApplication + " render executable was not found in the semicolon separated list \"" + renderExecutableList + "\". Checking for any executable that exists instead." )
            elif build == "64bit":
                self.LogInfo( "Enforcing 64 bit build of " + renderingApplication )
                self.Executable = FileUtils.SearchFileListFor64Bit( renderExecutableList )
                if self.Executable == "":
                    self.LogWarning( "64 bit " + renderingApplication + " render executable was not found in the semicolon separated list \"" + renderExecutableList + "\". Checking for any executable that exists instead." )
            
        if( self.Executable == ""):
            self.LogInfo( "Not enforcing a build of " + renderingApplication )
            self.Executable = FileUtils.SearchFileList( renderExecutableList )
            if self.Executable == "":
                self.FailRender( renderingApplication + " render executable was not found in the semicolon separated list \"" + renderExecutableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        # Check if we're rendering in ScreamerNet mode (Lightwave 8 and later).
        self.UseScreamerNet = self.GetBooleanPluginInfoEntryWithDefault( "UseScreamerNet", False )
        
        # If using the ScreamerNet method, we start Lightwave in server mode here.
        if self.UseScreamerNet:
            ##------------------------------------------------------------
            ##    Initialization process (once Lightwave is running):
            ##      1) Send init
            ##      2) Wait for Initializing
            ##      3) Send wait
            ##      4) Wait for Ready
            ##      5) Send load <scenefile>
            ##      6) Wait for Loading
            ##      7) Send wait
            ##      8) Wait for Ready
            ##------------------------------------------------------------
            
            self.LogInfo( "Starting Lightwave Initialization Phase..." )
            
            # Get the thread ID, which is used for creating the job and ack filenames.
            self.ThreadID = str( self.GetThreadNumber() )
            self.LogInfo( "Thread ID: " + self.ThreadID )
            
            # Create the job and ack filenames.
            self.JobFilename = Path.Combine( self.GetJobsDataDirectory(), "job" + self.ThreadID )
            self.LogInfo( "Job filename: " + self.JobFilename )
            if File.Exists( self.JobFilename ):
                self.LogInfo( "  cleaning up existing job file" )
                File.Delete( self.JobFilename )
            
            self.AckFilename = Path.Combine( self.GetJobsDataDirectory(), "ack" + self.ThreadID )
            self.LogInfo( "Ack filename: " + self.AckFilename )
            if File.Exists( self.AckFilename ):
                self.LogInfo( "  cleaning up existing ack file" )
                File.Delete( self.AckFilename )
            
            # Start the Lightwave monitored process.
            self.ProgramName = "Lightwave" + self.ThreadID
            self.LogInfo( "Starting monitored process: " + self.ProgramName )
            
            self.ScreamerNetProcess = LightwaveProcess( self, self.Executable, self.Version, True, self.JobFilename, self.AckFilename )
            self.StartMonitoredManagedProcess( self.ProgramName, self.ScreamerNetProcess )
            
            # Initialize the ScreamerNet process.
            self.SetStatusMessage( "Initializing Lightwave ScreamerNet..." )
            
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            self.SendCommandAndWait( "init", "Initializing" )
            self.SendCommandAndWait( "wait", "Ready" )
            
            # Load the scene file.
            sceneFilename = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
            if SystemUtils.IsRunningOnWindows():
                sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename ).replace( "/", "\\" )
            else:
                sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename ).replace( "\\", "/" )
            
            self.TempSceneFileName = self.CreateTempSceneFile( sceneFilename )
            
            self.SetStatusMessage( "Loading scene file..." )
            
            self.SendCommandAndWait( "load\n" + self.TempSceneFileName, "Loading" )
            self.SendCommandAndWait( "wait", "Ready" )
            
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            self.LogInfo( "Finished Lightwave Initialization Phase" )
    
    def RenderTasks( self ):
        if self.UseScreamerNet:
            ##------------------------------------------------------------
            ##    Rendering process:
            ##      1) Send render <s> <e> 1
            ##      2) Wait for Rendering Frame <s>
            ##      3) Send wait
            ##      4) Wait for Ready
            ##------------------------------------------------------------
            
            self.LogInfo( "Starting Lightwave Rendering Phase..." );
            
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            self.ScreamerNetProcess.ResetFrameCount()
            
            # Send the render command.
            self.SendCommandAndWait( "render\n" + str(self.GetStartFrame()) + " " + str(self.GetEndFrame()) + " 1", "Rendering" )
            self.SendCommandAndWait( "wait", "Ready" )
            
            self.SetProgress( 100.0 )
            self.SetStatusMessage( "Finished rendering " + str(self.ScreamerNetProcess.GetFrameCount()) + " frames" )
            
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            self.LogInfo( "Finished Lightwave Rendering Phase" )
        else:
            self.ScreamerNetProcess = LightwaveProcess( self, self.Executable, self.Version, False, "", "" )
            self.RunManagedProcess( self.ScreamerNetProcess )
    
    def EndJob( self ):
        # If using the ScreamerNet method, we shutdown Lightwave here.
        if self.UseScreamerNet:
            ##------------------------------------------------------------
            ##    Shutting down process:
            ##      1) Send quit
            ##      2) Wait for Offline
            ##------------------------------------------------------------
            
            self.LogInfo( "Starting Lightwave Shutting Down Phase..." )
            
            self.SetStatusMessage( "Shutting down Lightwave ScreamerNet..." )
            #self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            self.ShutdownMonitoredManagedProcess( self.ProgramName )
            
            self.LogInfo( "Finished Lightwave Shutting Down Phase" )
            
            if self.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
                File.Delete( self.TempSceneFileName )
        
    def SendCommand( self, command ):
        self.LogInfo( "Sending command: " + command )
        if SystemUtils.IsRunningOnWindows():
            self.CreateCommandFile( self.JobFilename, command )
        else:
            File.WriteAllText( self.JobFilename, command )
        
        SystemUtils.Sleep( 500 )
        
        while True:
            if self.IsCanceled():
                self.FailRender( "Received cancel task command from Deadline." )
            
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            response = self.WaitForCommandFile( self.AckFilename, True, 100 )
            
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            if response != "":
                self.LogInfo( "Received response: " + response )
                return response
        
        SystemUtils.Sleep( 500 )
        
    def SendCommandAndWait( self, command, waitFor ):
        self.LogInfo( "Sending command: " + command )
        File.WriteAllText( self.JobFilename, command )
        
        SystemUtils.Sleep( 500 )
        
        while True:
            if self.IsCanceled():
                self.FailRender( "Received cancel task command from Deadline." )
            
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            response = self.WaitForCommandFile( self.AckFilename, False, 100 )
            
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            if response.startswith( waitFor ):
                self.LogInfo( "Received response: " + response )
                return response
            else:
                SystemUtils.Sleep( 500 )

    def CreateTempSceneFile( self, sceneFilename ):
        tempSceneFilename = ""
        
        if self.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
            tempSceneDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
            tempSceneFilename = Path.Combine( tempSceneDirectory, Path.GetFileName( sceneFilename ) )
            
            if SystemUtils.IsRunningOnWindows():
                tempSceneFilename = tempSceneFilename.replace( "/", "\\" )
                if sceneFilename.startswith( "\\" ) and not sceneFilename.startswith( "\\\\" ):
                    sceneFilename = "\\" + sceneFilename
                if sceneFilename.startswith( "/" ) and not sceneFilename.startswith( "//" ):
                    sceneFilename = "/" + sceneFilename
                
                RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator( sceneFilename, tempSceneFilename, "/", "\\" )
            else:
                tempSceneFilename = tempSceneFilename.replace( "\\", "/" )
                RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator( sceneFilename, tempSceneFilename, "\\", "/" )
                os.chmod( tempSceneFilename, os.stat( sceneFilename ).st_mode )
        else:
            if SystemUtils.IsRunningOnWindows():
                tempSceneFilename = sceneFilename.replace( "/", "\\" )
            else:
                tempSceneFilename = sceneFilename.replace( "\\", "/" )
        
        return tempSceneFilename
######################################################################
## This is the class for running Lightwave process.
######################################################################
class LightwaveProcess (ManagedProcess):
    deadlinePlugin = None
    
    Executable = ""
    Version = 9.0
    FinishedFrameCount = 0
    Arch = "none"
    
    UseScreamerNet = False
    JobFilename = ""
    AckFilename = ""
    TempSceneFileName = ""
    
    def __init__( self, deadlinePlugin, executable, version, useScreamerNet, jobFilename, ackFilename ):
        self.deadlinePlugin = deadlinePlugin
        self.Executable = executable
        self.Version = version
        self.UseScreamerNet = useScreamerNet
        self.JobFilename = jobFilename
        self.AckFilename = ackFilename
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
    
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
        self.PopupHandling = True
        self.StdoutHandling = True
        
        self.AddPopupHandler( ".*Unable To Locate.*", "OK" )
        
        self.AddStdoutHandlerCallback( "Error:(.*)" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( r"Can't find \"(.*)?\"\..*" ).HandleCallback += self.HandleMissingContent
        self.AddStdoutHandlerCallback( "Can't open scene file" ).HandleCallback += self.HandleMissingConfig
        self.AddStdoutHandlerCallback( ".*bad magic number.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( ".*Unable to access the scene file.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( ".*Cannot create temporary config directory.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( ".*Layout is frozen or is not configured properly.*" ).HandleCallback += self.HandleError
        
        if self.UseScreamerNet:
            self.AddStdoutHandlerCallback( r"(Rendering frame [0-9]+).* pass ([0-9]+)[^0-9]+([0-9]+)\." ).HandleCallback += self.HandleProgress
        else:
            self.AddStdoutHandlerCallback( r"Frame [0-9]+ progress ([0-9]+)% done.*" ).HandleCallback += self.HandleProgressMode3
        
        self.AddStdoutHandlerCallback( "Frame completed" ).HandleCallback += self.HandleFrameComplete
    
    def PreRenderTasks( self ):
        if not self.UseScreamerNet:
            self.FinishedFrameCount = 0
    
    def PostRenderTasks( self ):
        if not self.UseScreamerNet:
            self.deadlinePlugin.SetProgress( 100.0 )
            self.deadlinePlugin.SetStatusMessage( "Finished rendering " + str(self.FinishedFrameCount) + " frames" )
            
            if self.deadlinePlugin.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
                File.Delete( self.TempSceneFileName )
    
    def RenderExecutable( self ):
        if SystemUtils.IsRunningOnMac():
            build = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "LW_Build", "None" ).lower()
            if build == "32bit":
                self.Arch = "i386"
            elif build == "64bit":
                self.Arch = "x86_64"
            
            if self.Arch == "i386" or self.Arch == "x86_64":
                archExe = DirectoryUtils.SearchPath( "arch" )
                if archExe == "":
                    self.deadlinePlugin.LogWarning( "Could not find 'arch' executable in the PATH to force " + build + " rendering, Lightwave will launched normally" )
                    self.Arch = "none"
                else:
                    return archExe
        
        return self.Executable
    
    def RenderArgument( self ):
        arguments = ""
        
        if SystemUtils.IsRunningOnMac() and self.Arch != "none":
            arguments += "-" + self.Arch + " \"" + self.Executable + "\" "
        
        # 2 represents ScreamerNet mode, 3 represents normal command line mode.
        if self.UseScreamerNet:
            arguments += "-2"
        else:
            arguments += "-3 -t5" # -t allows progress to be printed (mode 3 only)
        
        # If the using version 8 or greater, use quotation marks around paths and filenames.
        quote = "\""
        
        # Set the config and content directories. Make sure to remove any trailing slashes.
        configDir = self.deadlinePlugin.GetPluginInfoEntry( "ConfigDir" )
        
        # If using FPrime, and Local Config is enabled, we need to copy the network config locally and tell FPrime to use that instead.
        if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "UseFPrime", False ) and self.deadlinePlugin.GetBooleanConfigEntryWithDefault( "FPrime_LocalConfig", False ):
            self.deadlinePlugin.LogInfo( "Using local Config for FPrime" )
            configDir = RepositoryUtils.CheckPathMapping( configDir )
            localConfigDir = self.deadlinePlugin.CreateTempDirectory( "LocalFPrimeConfig" )
            DirectoryUtils.SynchronizeDirectories( configDir, localConfigDir, True )
            configDir = localConfigDir.replace( "\\", "/" ).rstrip( "/" )
        else:
            configDir = RepositoryUtils.CheckPathMapping( configDir ).replace( "\\", "/" ).rstrip( "/" )
        
        contentDir = self.deadlinePlugin.GetPluginInfoEntry( "ContentDir" )
        contentDir = RepositoryUtils.CheckPathMapping( contentDir ).replace( "\\", "/" ).rstrip( "/" )
        
        arguments += " -c" + quote + configDir + quote
        arguments += " -d" + quote + contentDir + quote
        
        if self.UseScreamerNet:
            arguments += " " + quote + self.JobFilename + quote + " " + quote + self.AckFilename + quote
        else:
            sceneFilename = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "SceneFile", self.deadlinePlugin.GetDataFilename() )
            if SystemUtils.IsRunningOnWindows():
                sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename ).replace( "/", "\\" )
            else:
                sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename ).replace( "\\", "/" )
            self.TempSceneFileName = self.deadlinePlugin.CreateTempSceneFile( sceneFilename )
            
            arguments += " " + quote + self.TempSceneFileName + quote
            arguments += " " + str(self.deadlinePlugin.GetStartFrame()) + " " + str(self.deadlinePlugin.GetEndFrame())
        
        return arguments

    def HandleError( self ):
        ## Safe to ignore errors, which Screamernet outputs that doesn't affect the rendering.
        ignoreError = False
        
        errorMessage = self.GetRegexMatch( 0 )
        previousMessage = self.GetPreviousStdoutLine()
        
        # Ignores error message about sliders not found. (also checking previous message as Screamernet reports this twice.)
        if ( errorMessage.find( "Sliders" ) != -1 or previousMessage.find( "Sliders" ) != -1 ):
            ignoreError = True
        # Ignores error message about LightWave's Buffer View not found, as this is an Image Filter only used with LightWave's internal viewer.
        if ( errorMessage.find( "LW_BufferView") != -1 ):
            ignoreError = True
        
        if( ignoreError ):
            self.deadlinePlugin.LogInfo("Ignored Error: \"" + errorMessage + "\", as this error doesn't affect the rendering.")
        else:
            self.deadlinePlugin.FailRender( self.GetRegexMatch( 0 ) )
    
    def HandleMissingContent( self ):
        self.deadlinePlugin.FailRender( "Could not find the file \""+ self.GetRegexMatch( 1 ) + "\" in the specified Content directory. If the Content directory specified is local, ensure that the missing object exists in the specified location on this slave." )
    
    def HandleMissingConfig( self ):
        self.deadlinePlugin.FailRender( self.GetRegexMatch( 0 ) + " It is likely that Lightwave cannot find the config files (.cfg) in the specified Config directory. If the Config directory is local, ensure the Lightwave config files are in the specified location on this slave." )
    
    def HandleProgress( self ):
        message = self.GetRegexMatch( 1 )
        passNumber = int(self.GetRegexMatch( 2 ))
        passTotal = int(self.GetRegexMatch( 3 ))
        passPercentage = ( ( float(passNumber) - 1.0 ) * 100.0 ) / float(passTotal)
        
        self.deadlinePlugin.SetStatusMessage( message + " - " + str(passPercentage) + "%" )
        
        startFrame = self.deadlinePlugin.GetStartFrame()
        endFrame = self.deadlinePlugin.GetEndFrame()
        totalFrames = endFrame - startFrame + 1
        
        if totalFrames != 0:
            self.deadlinePlugin.SetProgress( ( passPercentage * ( 1.0 / float(totalFrames) ) ) + ( ( float(self.FinishedFrameCount) / float(totalFrames) ) * 100.0 ) )
    
    def HandleProgressMode3( self ):
        message = self.GetRegexMatch( 0 )
        percentage = int(self.GetRegexMatch( 1 ))
        
        self.deadlinePlugin.SetStatusMessage( message )
        
        startFrame = self.deadlinePlugin.GetStartFrame()
        endFrame = self.deadlinePlugin.GetEndFrame()
        totalFrames = endFrame - startFrame + 1
        
        if totalFrames != 0:
            self.deadlinePlugin.SetProgress( ( percentage * ( 1.0 / float(totalFrames) ) ) + ( ( float(self.FinishedFrameCount) / float(totalFrames) ) * 100.0 ) )
        
    def HandleFrameComplete( self ):
        self.FinishedFrameCount += 1
        
        startFrame = self.deadlinePlugin.GetStartFrame()
        endFrame = self.deadlinePlugin.GetEndFrame()
        totalFrames = endFrame - startFrame + 1
        
        if totalFrames != 0:
            self.deadlinePlugin.SetProgress( ( float(self.FinishedFrameCount) / float(totalFrames) ) * 100.0 )
    
    def ResetFrameCount( self ):
        self.FinishedFrameCount = 0
    
    def GetFrameCount( self ):
        return self.FinishedFrameCount
