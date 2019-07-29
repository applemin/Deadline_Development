import re

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Plugins import *
from Deadline.Scripting import *

from FranticX.Processes import *

######################################################################
## This is the function that Deadline calls to get
## an instance of the main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return NukeFrameServerPlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the 
## NukeFrameServerPlugin plugin.
######################################################################
class NukeFrameServerPlugin( DeadlinePlugin ):
    Process = None
    ProcessName = "NukeFrameServer"

    def __init__( self ):
        self.NukeExecutable = ""
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob
        
    def Cleanup( self ):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback
        
        for process in self.Processes:
            process.Cleanup()
            del process
        self.Processes = []
        
    def InitializeProcess( self ):
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Advanced
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.ExeList = self.GetConfigEntryWithDefault( "RenderExecutable", "" )
        self.NukeExecutable = FileUtils.SearchFileList( self.ExeList )
        
    def StartJob( self ):
        # This fixes a library conflict issue on non-Windows systems.
        if not SystemUtils.IsRunningOnWindows():
            self.scrubLibPaths()
        
        if self.GetBooleanConfigEntryWithDefault( "PrepForOFX", True ):
            # Ensure that OFX plugins will work
            try:
                self.prepForOFX()
            except:
                self.LogWarning( "Prepping of OFX cache failed" )
        
        self.Version = float( self.GetPluginInfoEntry( "Version" ) )
        
        # Since we now support minor versions, we should default to the *.0 version if the *.X version they're using isn't supported yet.
        versionNotSupported = "this version is not supported yet"
        nukeExeList = self.GetConfigEntryWithDefault( "RenderExecutable" + str(self.Version).replace( ".", "_" ), versionNotSupported )
        if nukeExeList == versionNotSupported:
            oldVersion = self.Version
            self.Version = float(int(self.Version))
            
            nukeExeList = self.GetConfigEntryWithDefault( "RenderExecutable" + str(self.Version).replace( ".", "_" ), versionNotSupported )
            if nukeExeList == versionNotSupported:
                self.FailRender( "Nuke major version " + str(int(self.Version)) + " is currently not supported." )
            else:
                self.LogWarning( "Nuke minor version " + str(oldVersion) + " is currently not supported, so version " + str(self.Version) + " will be used instead." )
    
        #Get the args
        self.HostName = self.GetPluginInfoEntryWithDefault("FrameRenderHost", "127.0.0.1")
        self.Port = self.GetIntegerPluginInfoEntryWithDefault("FrameRenderPort", 5560)
        self.NumWorkers = self.GetIntegerPluginInfoEntryWithDefault("FrameRenderWorkers", 1)
        self.NumThreads = self.GetIntegerPluginInfoEntryWithDefault("FrameRenderWorkerThreads", 1)
        self.WorkerMem = self.GetIntegerPluginInfoEntryWithDefault("FrameRenderWorkerMem", 2048)
        
        #Check if the host machine is this machine or if this machine is already rendering. If so, fail the render
        jobID = self.GetJob().JobId
        slaveName = self.GetSlaveName()
        machineIP = SlaveUtils.GetMachineIPAddresses([RepositoryUtils.GetSlaveInfo(slaveName, False)])
        if len(machineIP) > 0:
            machineIP = machineIP[0]
        else:
            self.FailRender("No machine found for current Slave.")
        self.LogInfo( machineIP+" is the machine IP" )
        
        renderingSlaves = list(RepositoryUtils.GetSlavesRenderingJob(jobID))
        if slaveName in renderingSlaves:
            renderingSlaves.remove(slaveName)
        renderingSlaves = SlaveUtils.GetMachineIPAddresses(RepositoryUtils.GetSlaveInfos(renderingSlaves, False))
        for slave in renderingSlaves:
            self.LogInfo(slave+" a Slave IP")
        if machineIP == self.HostName:
            self.FailRender("This machine cannot render start a Frame Server for the host name as it is the same machine.")
        elif machineIP in renderingSlaves:
            self.FailRender("This Slave cannot start a frame server instance as there is already a Slave running on this machine that has started a Frame Server instance for this Job")
        
    def RenderTasks( self ):
        self.Process = FrameServerProcess( self, self.Version )
        self.StartMonitoredManagedProcess( self.ProcessName, self.Process )
        while(True):
            if self.IsCanceled():
                self.ShutdownMonitoredManagedProcess( self.ProcessName )
                self.FailRender( "Received cancel task command from Deadline." )
            
            self.VerifyMonitoredManagedProcess( self.ProcessName )
            self.FlushMonitoredManagedProcessStdout( self.ProcessName )
                
            SystemUtils.Sleep(1000)
        
    def EndJob( self ):
        self.LogInfo( "Ending Job" )
        self.ShutdownMonitoredManagedProcess( self.ProcessName )
            
    def scrubLibPath( self, envVar ):
        ldPaths = Environment.GetEnvironmentVariable(envVar)
        if ldPaths:
            ldPaths = ldPaths.split(":")
            newLDPaths = []
            for ldPath in ldPaths:
                if not re.search("Deadline",ldPath):
                    newLDPaths.append(ldPath)
            
            if len(newLDPaths):
                newLDPaths = ":".join(newLDPaths)
            else:
                newLDPaths = ""
            
            self.SetProcessEnvironmentVariable(envVar,newLDPaths)
            del ldPaths
            del newLDPaths
            
    def scrubLibPaths( self ):
        """This solves a library / plugin linking issue with Nuke that occurs
        when Nuke sees the IlmImf library included with Deadline.  It appears that library
        conflicts with the exrWriter and causes it to error out.  This solution
        removes the Deadline library paths from the LD and DYLD library paths
        before Deadline launches Nuke, so Nuke never sees that library.  It seems like
        this fixes the problem. Thanks to Matt Griffith for figuring this one out!"""
        
        self.LogInfo("Scrubbing the LD and DYLD LIBRARY paths")
        
        self.scrubLibPath("LD_LIBRARY_PATH")
        self.scrubLibPath("DYLD_LIBRARY_PATH")
        self.scrubLibPath("DYLD_FALLBACK_LIBRARY_PATH")
        self.scrubLibPath("DYLD_FRAMEWORK_PATH")
        self.scrubLibPath("DYLD_FALLBACK_FRAMEWORK_PATH")
            
    def prepForOFX( self ):
        """This solves an issue where Nuke can fail to create the ofxplugincache,
        which causes any script submited to Deadline that uses an OFX plugin to fail.
        Thanks to Matt Griffith for figuring this one out!"""
        
        self.LogInfo("Prepping OFX cache")
        nukeTempPath = ""
        
        # temp path for Nuke
        if SystemUtils.IsRunningOnWindows():
            # on windows, nuke temp path is [Temp]\nuke
            nukeTempPath = Path.Combine( Path.GetTempPath(), "nuke" )
        else:
            # on *nix, nuke temp path is "/var/tmp/nuke-u" + 'id -u'
            id = PathUtils.GetApplicationPath( "id" )
            if len(id) == 0:
                self.LogWarning( "Could not get path for 'id' process, skipping OFX cache prep" )
                return
            
            startInfo = ProcessStartInfo( id, "-u" )
            startInfo.RedirectStandardOutput = True
            startInfo.UseShellExecute = False
            
            idProcess = Process()
            idProcess.StartInfo = startInfo
            idProcess.Start()
            idProcess.WaitForExit()
            
            userId = idProcess.StandardOutput.ReadLine()
            
            idProcess.StandardOutput.Close();
            idProcess.StandardOutput.Dispose();
            idProcess.Close()
            idProcess.Dispose()
            
            if len(userId) == 0:
                self.LogWarning( "Failed to get user id, skipping OFX cache prep" )
                return
            
            nukeTempPath = "/var/tmp/nuke-u" + userId
        
        self.LogInfo( "Checking Nuke temp path: " + nukeTempPath)
        if Directory.Exists(nukeTempPath):
            self.LogInfo( "Path already exists" )
        else:
            self.LogInfo( "Path does not exist, creating it..." )
            Directory.CreateDirectory(nukeTempPath) #creating this level of the nuke temp directory seems to be enough to let the ofxplugincache get created -mg
            
            if Directory.Exists(nukeTempPath):
                self.LogInfo( "Path now exists" )
            else:
                self.LogWarning( "Unable to create path, skipping OFX cache prep" )
                return
        
        self.LogInfo("OFX cache prepped")
        
class FrameServerProcess( ManagedProcess ):
    deadlinePlugin = None
    Version = -1.0
    
    def __init__( self, deadlinePlugin, version ):
        self.deadlinePlugin = deadlinePlugin
        self.Version = version
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
    
    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
    
    def InitializeProcess( self ):
        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( "WARNING:.*" ).HandleCallback += self.HandleStdoutWarning
        self.AddStdoutHandlerCallback( "ERROR:(.*)" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "INFO:.*").HandleCallback += self.HandleInfo
        
    def PreRenderTasks( self ):
        self.deadlinePlugin.LogInfo( "Nuke Studio Frame Server job starting..." )
        
    def PostRenderTasks( self ):
        self.deadlinePlugin.LogInfo( "Nuke Studio Frame Server job finished." )
        
    ## Called by Deadline to get the render executable.
    def RenderExecutable( self ):
        nukeExeList = self.deadlinePlugin.GetConfigEntry( "RenderExecutable" + str(self.Version).replace( ".", "_" ) )
        nukeExe = FileUtils.SearchFileList( nukeExeList )
        if( nukeExe == "" ):
            self.deadlinePlugin.FailRender( "Nuke %s render executable could not be found in the semicolon separated list \"%s\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." % (self.Version, nukeExeList) )
        
        return nukeExe

    ## Called by Deadline to get the render arguments.
    def RenderArgument( self ):
        renderArguments = ""
        
        isInteractiveSlave = False
        thisSlave = self.deadlinePlugin.GetSlaveName().lower()
        interactiveSlaves = self.deadlinePlugin.GetConfigEntryWithDefault( "InteractiveSlaves", "" ).split( ',' )
        for slave in interactiveSlaves:
            if slave.lower().strip() == thisSlave:
                self.deadlinePlugin.LogInfo( "This Slave is in the interactive license list - an interactive license will be used instead of a render license" )
                renderArguments += " -i"
                isInteractiveSlave=True
        
        executable = self.RenderExecutable()
        directory = Path.GetDirectoryName( executable )
        frameServerScript = PathUtils.ToPlatformIndependentPath(Path.Combine(directory,"pythonextensions\\site-packages\\foundry\\frameserver\\nuke\\runframeserver.py"))
        
        renderArguments += ' -t "'+frameServerScript + '" '
        
        renderArguments += "--numworkers="+str(self.deadlinePlugin.NumWorkers)
        
        renderArguments += " --nukeworkerthreads="+str(self.deadlinePlugin.NumThreads)
        
        renderArguments += " --nukeworkermemory="+str(self.deadlinePlugin.WorkerMem)
        
        renderArguments += " --workerconnecturl=tcp://"+str(self.deadlinePlugin.HostName)+":"+str(self.deadlinePlugin.Port)
        
        if isInteractiveSlave:
            renderArguments += " --useInteractiveLicense"
        
        renderArguments += ' --nukepath="'+str(executable)+'"'
        
        return renderArguments
        
    def HandleStdoutWarning( self ):
        self.deadlinePlugin.LogWarning( self.GetRegexMatch(0) )

    def HandleStdoutError( self ):
        self.deadlinePlugin.FailRender( "Detected an error: " + self.GetRegexMatch(1) )
        
    def HandleInfo( self ):
        self.deadlinePlugin.LogWarning( self.GetRegexMatch(0) )
