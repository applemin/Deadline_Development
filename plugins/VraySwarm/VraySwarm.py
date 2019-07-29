import json
import re
import requests

from System import DateTime
from System.Diagnostics import *
from System.IO import *

from Deadline.Scripting import *
from Deadline.Plugins import *
from FranticX.Processes import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return VraySwarmPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the VraySwarm plugin.
######################################################################
class VraySwarmPlugin( DeadlinePlugin ):
    def __init__( self ):
        self.Executable = ''
        self.ProcessName = ''
        self.SwarmInterface = None
        self.VraySwarmProcess = None

        self.RenderOccurred = False
        self.TimeoutStartTime = None

        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks

    def Cleanup( self ):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback

        if self.VraySwarmProcess:
            self.VraySwarmProcess.Cleanup()
            del self.VraySwarmProcess

    def InitializeProcess( self ):
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Advanced
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.HideDosWindow = True

    def StartJob( self ):
        jobName = self.GetJob().JobName
        if re.search( r'[^- \w]', jobName ) is not None: # Found something that's not alpha numeric (\w), hyphen, or space
            self.FailRender( 'Job Name "%s" contains invalid characters for V-Ray Swarm tags. Only Alpha-numeric (a-z, A-Z, 0-9), underscores, dashes, and spaces are allowed.' % jobName )
        else:
            self.jobTag = jobName + ' - ' + self.GetJob().JobId

        swarmList = self.GetConfigEntry( 'VRaySwarmExecutable' )
        self.Executable = FileUtils.SearchFileList( swarmList )
        if self.Executable == '':
            self.FailRender( 'V-Ray Swarm executable was not found in the semicolon separated list "%s". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor.' % swarmList )

        # Try to kill V-Ray Swarm Process if running
        self.ProcessName = Path.GetFileNameWithoutExtension( self.Executable )
        if ProcessUtils.IsProcessRunning( self.ProcessName ):
            self.LogWarning( 'Found existing "%s" process' % self.ProcessName )

            if ProcessUtils.KillProcesses( self.ProcessName, 3 ):
                SystemUtils.Sleep( 3000 )
                if ProcessUtils.IsProcessRunning( self.ProcessName ):
                    self.LogWarning( 'V-Ray Swarm is still running: "%s" process. This can be due to the "V-Ray Swarm" service restarting the process.  Will use existing process to render but will have no output for the logs.' % self.ProcessName )
                else:
                    self.LogInfo( 'Successfully killed V-Ray Swarm process: "%s"' % self.ProcessName )
                    self.VraySwarmProcess = VraySwarmProcess( self, self.Executable )
            else:
                self.LogWarning( 'Failed to kill "%s" process.' % self.ProcessName )
        else:
            self.VraySwarmProcess = VraySwarmProcess( self, self.Executable )

        self.AutoClose = self.GetBooleanConfigEntryWithDefault( 'AutoClose', False )
        self.LogInfo( 'Swarm Auto Close: %s' % self.AutoClose )

        self.IsRenderActive = self.GetBooleanConfigEntryWithDefault( 'WaitForRender', True )
        self.LogInfo( 'Swarm Auto Timeout - Wait for first render: %s' % self.IsRenderActive )

        self.TimeoutBeforeRender = self.GetIntegerConfigEntryWithDefault( 'TimeoutBeforeRender', 15 ) * 60 # The UI is in minutes, the code is still in seconds.
        self.LogInfo( 'Swarm Timeout Before Render: %s seconds' % self.TimeoutBeforeRender )

        self.TimeoutAfterRender = self.GetIntegerConfigEntryWithDefault( 'TimeoutAfterRender', 15 ) * 60 # The UI is in minutes, the code is still in seconds.
        self.LogInfo( 'Swarm Timeout After Render: %s seconds' % self.TimeoutAfterRender )

        OnJobComplete = self.GetConfigEntryWithDefault( 'OnJobComplete', 'Do Nothing' )
        if OnJobComplete != 'Do Nothing':
            self.LogInfo( 'Swarm Job On Complete: %s' % OnJobComplete )
            currentJob = self.GetJob()
            currentJob.JobOnJobComplete = OnJobComplete
            RepositoryUtils.SaveJob( currentJob )

        if self.VraySwarmProcess:
            self.StartMonitoredManagedProcess( self.ProcessName, self.VraySwarmProcess )
            SystemUtils.Sleep( 5000 ) # Tries to ensure there's output before using interface

    def RenderTasks( self ):
        if self.VraySwarmProcess:
            self.VerifyMonitoredManagedProcess( self.ProcessName )
            self.FlushMonitoredManagedProcessStdout( self.ProcessName )
            self.LogInfo( 'V-Ray Swarm is running from the executable')
        else:
            self.LogInfo( 'V-Ray Swarm is running as a service' )

        self.SwarmInterface = SwarmInterface( self )
        self.SwarmInterface.clearLogs()
        self.SwarmInterface.addTag( self.jobTag ) # Add tag for this job. Also handles enabling/disabling Swarm instance

        # Loop until render is complete
        while True:
            if self.IsCanceled():
                break

            if self.VraySwarmProcess:
                self.VerifyMonitoredManagedProcess( self.ProcessName )
                self.FlushMonitoredManagedProcessStdout( self.ProcessName )

            # Process doesn't receive all relevant output... so both process and output need to read from logs
            self.SwarmInterface.loadLogs()

            if self.AutoClose:
                if not self.IsRenderActive:
                    # If the timeout is reached, break out of the loop so that RenderTasks can exit, which means the task is complete.
                    if self.RenderOccurred and self.CheckTimeout( self.TimeoutAfterRender ):
                        self.LogInfo( 'Exiting V-Ray Swarm Process and marking task as completed due to plugin option - Auto After Render Timeout: %s seconds.' % self.TimeoutAfterRender )
                        break
                    elif not self.RenderOccurred and self.CheckTimeout( self.TimeoutBeforeRender ):
                        self.LogInfo( 'Exiting V-Ray Swarm Process and marking task as completed due to plugin option - Auto Before Render Timeout: %s seconds.' % self.TimeoutBeforeRender )
                        break

            # Sleep 10 seconds between loops
            SystemUtils.Sleep( 10000 )

        self.LogInfo("Job done. Cleaning up")
            
        # Clean up and end job
        if self.SwarmInterface:
            self.SwarmInterface.removeTag( self.jobTag )

        if self.VraySwarmProcess:
            self.LogInfo( 'Shutting down "%s" process' % self.ProcessName )
            self.ShutdownMonitoredManagedProcess( self.ProcessName )

    def CheckTimeout( self, timeoutLength ):
        if not self.TimeoutStartTime:
            self.TimeoutStartTime = DateTime.Now
            return False
        
        timeDifference = DateTime.Now.Subtract( self.TimeoutStartTime ).TotalSeconds
        
        return timeDifference >= timeoutLength

    def RenderStarted( self ):
        self.IsRenderActive = True
        self.LogInfo( 'Swarm render has started.' )
        self.TimeoutStartTime = None

    def RenderStopped( self ):
        self.IsRenderActive = False
        self.LogInfo( 'Swarm render has stopped.' )
        self.RenderOccurred = True

######################################################################
## This is the class that starts up the VraySwarm process.
######################################################################
class VraySwarmProcess( ManagedProcess ):
    def __init__( self, deadlinePlugin, executable ):
        self.deadlinePlugin = deadlinePlugin
        self.executable = executable

        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument

        self.AddStdoutHandlerCallback( r'"url": "(.*)"' ).HandleCallback += self.HandleSwarmUrl

    def Cleanup( self ):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

    def InitializeProcess( self ):
        self.SingleFramesOnly = True
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        self.HideDosWindow = True

    def RenderExecutable( self ):
        return self.executable

    def RenderArgument( self ):
        return ''

    def HandleSwarmUrl( self ):
        if SwarmInterface.publicUrl == '':
            SwarmInterface.publicUrl = self.GetRegexMatch( 1 )


######################################################################
## This is the class used to interact with V-Ray Swarm on localhost
######################################################################
class SwarmInterface:
    publicUrl = ''
    versionList = [ 'v1', '1.3' ] # left to right, newest to oldest url
    versionMap = { '1':[ 'v1', '1.3' ] }

    def __init__( self, deadlinePlugin ):
        self.deadlinePlugin = deadlinePlugin
        self.requestId = 0
        self.logIndex = 0

        self.headers = { 'content-type': 'application/json' }
        self.url = 'http://localhost:24267/vray-swarm/'

        # These requests are all to the machine the code is running on, so the timeouts could probably be a lot lower that than this.
        # It's unlikely, but the timeouts are to ensure that the code doesn't hang forever, waiting for a response from V-Ray Swarm.
        self.timeout = ( 16, 16 ) # ( connect_timeout, read_timeout )

        # If we found the url from stdout, use it. Otherwise try pinging known addresses until we find one that works (chances are process is already running as a service)
        if SwarmInterface.publicUrl != '':
            self.url = SwarmInterface.publicUrl
        else:
            for version in SwarmInterface.versionList:
                try:
                    testUrl = self.url + version
                    if self.pingSwarm( testUrl ):
                        self.deadlinePlugin.LogInfo( 'Found V-Ray Swarm url: "%s"' % testUrl )
                        self.url = testUrl
                        self.url = self.getStatus()[ 'url' ] # Swaps out 'localhost' for actual IP of machine. Needed for enableNode
                        break
                except:
                    pass
            else:
                self.deadlinePlugin.FailRender( 'Unable to find url for V-Ray Swarm' )

    # Builds up the payload we send to V-Ray Swarm.
    def getRequestData( self, method, params ):
        if not isinstance( params, list ):
            raise TypeError( 'params must be a list' )

        requestData = { 'jsonrpc':'2.0', 'id':self.requestId, 'method':method, 'params':params }
        self.requestId += 1

        return requestData

    # If we can't grab the url from starting the process, then we should try the known urls until one works
    def pingSwarm( self, testUrl ):
        data = self.getRequestData( 'getStatus', [] )

        self.deadlinePlugin.LogInfo( 'pinging "%s"' % testUrl )
        response = requests.post( testUrl, headers=self.headers, data=json.dumps( data ), timeout=self.timeout )
        self.deadlinePlugin.LogInfo( 'response: %d' % response.status_code )

        return response.status_code == 200

    # Enables and disables the local instance of V-Ray Swarm. Need to disable to update the configuration, and needs to be enabled to render.
    def enableNode( self, enable ):
        data = self.getRequestData( 'drnodes.enableNode', [ self.url, enable ] ) # url can't be localhost, needs IP
        response = requests.post( self.url, headers=self.headers, data=json.dumps( data ), timeout=self.timeout )

    # Grabs the Swarm status of localhost (ie. Render status, url, etc.)
    def getStatus( self ):
        data = self.getRequestData( 'getStatus', [] )
        response = requests.post( self.url, headers=self.headers, data=json.dumps( data ), timeout=self.timeout )

        return response.json()[ 'result' ]

    # Clears the WHOLE log for V-Ray Swarm.
    def clearLogs( self ):
        data = self.getRequestData( 'vray.clearLogs', [] )

        self.deadlinePlugin.LogInfo( 'Clearing the V-Ray Swarm log...' )
        try:
            # As of V-Ray Swarm 1.4.1, this is the only request that doesn't send back ANY response (it should at least acknowledge the request). No timeout means it hangs indefinitely.
            requests.post( self.url, headers=self.headers, data=json.dumps( data ), timeout=1 )
        except requests.exceptions.Timeout:
            pass

        self.logIndex = 0

    # Grabs the output log from V-Ray Swarm. This is potentially expensive, as it receives the WHOLE log each time.
    def loadLogs( self ):
        data = self.getRequestData( 'vray.loadLogs', [] )
        response = requests.post( self.url, headers=self.headers, data=json.dumps( data ) )

        log = response.json()[ 'result' ]
        while self.logIndex < len( log ):
            line = self.sanitizeLogLine( log[ self.logIndex ] )
            if 'starting dr session' in line.lower():
                self.deadlinePlugin.RenderStarted()
            elif 'closing dr session' in line.lower():
                self.deadlinePlugin.RenderStopped()

            self.deadlinePlugin.LogInfo( line )
            self.logIndex += 1

    # This cleans each line from the logs since they've got some mess in them
    def sanitizeLogLine( self, line ):
        line = line.strip()
        line = line.replace( '&quot;', '"' ) # This is how V-Ray handles quotes in JSON

        # Random lines have spans... ie. <span style="color: #eee">[2017/Jul/19|14:41:33]</span> <span style="color: #eee">Stopping V-Ray...</span>
        line = re.sub( r'<span.*>', '', line ) 
        line = line.replace( '</span>', '' )

        return line.strip()

    # Gets the Swarm configuration of localhost
    def getConfig( self ):
        data = self.getRequestData( 'config.get', [] )
        response = requests.post( self.url, headers=self.headers, data=json.dumps( data ), timeout=self.timeout )

        return response.json()[ 'result' ]

    # Updates the localhost Swam configuration. ie. To add/remove tags
    def updateConfig( self, config ):
        # The configuration, a dictionary of settings, is the only item in the list we pass
        data = self.getRequestData( 'config.update', [ config ] )

        # Need to disable the local Swarm instance to update the configuration
        self.enableNode( False )
        response = requests.post( self.url, headers=self.headers, data=json.dumps( data ), timeout=self.timeout )
        self.enableNode( True )

    # Add tag to localhost Swarm instance. ie. JobName - JobID
    def addTag( self, tag ):
        config = self.getConfig()

        tags = config.get( 'tags', [] )
        if tag not in tags:
            tags.append( tag )
            config[ 'tags' ] = tags
            self.updateConfig( config )

    # Remove tag from localhost Swarm instance. Must have at least 1 tag after removal
    def removeTag( self, tag ):
        config = self.getConfig()

        tags = config.get( 'tags', [] )
        if tag in tags:
            self.deadlinePlugin.LogInfo( 'Removing tag "%s" from Swarm instance' % tag )
            tags.remove( tag )

        if len( tags ) == 0:
            self.deadlinePlugin.LogInfo( 'There are no tags left, need at least 1. Adding "Default" tag to Swarm instance' )
            tags.append( 'Default' )

        config[ 'tags' ] = tags
        self.updateConfig( config )
