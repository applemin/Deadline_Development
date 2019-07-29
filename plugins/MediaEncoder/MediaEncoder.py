import os
import httplib
import subprocess
import signal
import socket

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

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
    return MediaEncoderPlugin()

######################################################################
## This is the function that Deadline calls to clean up any
## resources held by the Plugin.
######################################################################
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Media Encoder plugin.
######################################################################
class MediaEncoderPlugin( DeadlinePlugin ):

    def __init__( self ):
        self.AME_Executable = ""
        self.AME_Version = 13.0
        self.AME_Process = None
        self.AME_ProcessName = "Media Encoder Web Service"
        self.AME_Port = 8080

        # String constants for AME's Job Statuses.
        self.AME_NOT_FOUND = "Not Found"
        self.AME_QUEUED = "Queued"
        self.AME_ENCODING = "Encoding"
        self.AME_SUCCESS = "Success"
        self.AME_COMPLETE_WARN = "Completed with warnings"
        self.AME_FAILED = "Failed"
        self.AME_STOPPED = "Stopped"
        self.AME_PAUSED = "Paused"

        # String constants for Server Status.
        self.AME_ONLINE = "Online"
        self.AME_OFFLINE = "Offline"

        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob

    def Cleanup( self ):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback

        if self.AME_Process:
            self.AME_Process.Cleanup()
            del self.AME_Process

    ## Called By Deadline to initalize the process.
    def InitializeProcess( self ):
        #Set the plugin-specific settings.
        self.LogInfo( "Media Encoder Plugin Initializing..." )
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Advanced
        self.UseProcessTree = True

    def GetAmeHostAddress( self ):
        ameHost = socket.gethostbyname( socket.gethostname() )

        altMacIPLookup = self.GetBooleanConfigEntryWithDefault( "AltMacIPLookup", False )

        if SystemUtils.IsRunningOnMac() and altMacIPLookup:
            # OS X 'sometimes' has issues with using the above method of getting the IP address and using
            # the loopback address gets rejected, so use command line to grab a public IP address instead.
            # grep removes IPv6 and local loopback addresses.
            command = "/sbin/ifconfig -a | grep inet | cut -d' ' -f2 | sort -n | grep -vE '::|127.0.0.1'"
            proc = subprocess.Popen( [command], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True )
            output, errors = proc.communicate()

            output = output.strip()
            outputLines = output.splitlines()

            for ipAddress in outputLines:
                try:
                    if ipAddress.split( "." )[3] != "1":
                        # return first IPv4 address where 4th octet is not equal to .1 (possible gateway)
                        ameHost = ipAddress
                        break
                except:
                    pass

        return ameHost

    def GetEncoderExecutable( self ):
        self.AME_Version = self.GetFloatPluginInfoEntry( "Version" )

        if self.AME_Version >= 13.5 and self.AME_Version < 14:
            self.ExeList = self.GetConfigEntry( "MediaEncoder_ServiceExecutable13_5")
        else:
            # For now, we are only supporting the major versions of CC
            self.ExeList = self.GetConfigEntry( "MediaEncoder_ServiceExecutable" + str(float(int(self.AME_Version))).replace( ".", "_" ) )
        
        meExe = FileUtils.SearchFileList( self.ExeList )

        return meExe

    def getVersionNumber( self ):
        ver = self.AME_Version
        if ver == 13.0:
            return "2014"
        elif ver == 13.5:
            return "2015"
        elif ver == 14.0:
            return "2017"
        else:
            return str(ver + 2003)

    ## Called by Deadline when the job is first loaded.
    def StartJob( self ):
        self.AME_Host = self.GetAmeHostAddress()
        self.AME_Executable = self.GetEncoderExecutable()

        ccVersion = self.getVersionNumber()
        self.AME_ExeName = "Adobe Media Encoder CC " + ccVersion
        self.LogInfo( "Media Encoder Exe Name: %s" % self.AME_ExeName )

        self.ExistingAMEProcess = self.GetConfigEntryWithDefault( "ExistingAMEProcess", "Fail On Existing Process" )
        self.LogInfo( "Existing Adobe Media Encoder Process: %s" % self.ExistingAMEProcess )

        if( self.ExistingAMEProcess == "Fail On Existing Process" ):
            if( ProcessUtils.IsProcessRunning( self.AME_ExeName ) ):
                processes = Process.GetProcessesByName( self.AME_ExeName )
                if len( processes ) > 0:
                    self.LogWarning( "Found existing '%s' process" % self.AME_ExeName )
                    
                    process = processes[ 0 ]
                    if process != None:
                        self.FailRender( "Fail On Existing Process is enabled, and a process '%s' with pid '%d' exists! AME Web Service only works if Media Encoder application is not already running." % (self.AME_ExeName, process.Id) )

        if( self.ExistingAMEProcess == "Kill On Existing Process" ):
            if( ProcessUtils.IsProcessRunning( self.AME_ExeName ) ):
                processes = Process.GetProcessesByName( self.AME_ExeName )
                if len( processes ) > 0:
                    self.LogWarning( "Found existing '%s' process" % self.AME_ExeName )
                    
                    process = processes[ 0 ]
                    processId = process.Id
                    if( ProcessUtils.KillProcesses( self.AME_ExeName ) ):
                        if process != None:
                            self.LogInfo( "Successfully killed Adobe Media Encoder process: '%s' with pid: '%d'" % (self.AME_ExeName, processId) )

                        SystemUtils.Sleep( 5000 )

                        if( ProcessUtils.IsProcessRunning( self.AME_ExeName ) ):
                            self.LogWarning( "Adobe Media Encoder is still running after kill command: '%s' process." % self.AME_ExeName )
                            process = Process.GetProcessesByName( self.AME_ExeName )[ 0 ]
                            if process != None:
                                self.FailRender( "Kill On Existing Process is enabled, and a process '%s' with pid '%d' still exists after executing a kill command." % (self.AME_ExeName, process.Id) )

        self.AMEAutoShutdown = self.GetBooleanConfigEntryWithDefault( "AMEAutoShutdown", True )
        self.LogInfo( "Auto Shutdown Adobe Media Encoder: %s" % self.AMEAutoShutdown )

        self.AMEOnJobComplete = self.GetConfigEntryWithDefault( "AMEOnJobComplete", "Do Nothing" )

        currentJob = self.GetJob()

        if self.AMEOnJobComplete != "Do Nothing":
            self.LogInfo( "Setting AME Job On Complete to: %s" % self.AMEOnJobComplete )
            currentJob.JobOnJobComplete = self.AMEOnJobComplete
            RepositoryUtils.SaveJob( currentJob )

        self.LogInfo( "Checking for an existing AME Web Service at {0}:{1}...".format( self.AME_Host, self.AME_Port ) )

        # First, check if AME is already running.
        hConn = httplib.HTTPConnection( self.AME_Host, self.AME_Port )
        try: 
            reqSuccess = True
            try:
                # Request the Server Status from the webservice.
                hConn.request( 'GET', "/server" )
            except:
                reqSuccess = False
                self.LogInfo( "Unable to connect to an existing AME Web Service at {0}:{1}.".format( self.AME_Host, self.AME_Port ) )

            if reqSuccess:
                # Request succeeded, get the response.
                response = hConn.getresponse()
                serverXML = response.read()

                if response.status == httplib.OK:
                    # Parse the status from the response content.
                    xRoot = ET.fromstring( serverXML )
                    xStatus = xRoot.find( "ServerStatus" )

                    if xStatus != None:
                        if xStatus.text.strip() == self.AME_ONLINE:
                            # Already online, nothing else needed.
                            self.LogInfo( "AME Web Service is responding and Online." )
                            return
                        else:
                            # Responding, but offline, restart it.
                            self.LogInfo( "AME Web Service is responding but Offline, restarting server..." )
                            self.RestartServer()
                else:
                    # Weird status.
                    self.FailRender( "Got unexpected response from AME Web Service: ({0}: {1})".format( response.status, response.reason ) )
            else:
                # Request failed, web service must not be running.
                self.LogInfo( "Starting AME Web Service..." )
                self.StartWebService()
        finally:
            hConn.close()

    ## Starts the ame_webservice_console.exe (Windows) or ame_webservice_agent (OSX), and waits for it to report itself online
    def StartWebService( self ):
        if not self.AME_Executable:
            self.FailRender( "Media Encoder Web Service executable could not be found in the semicolon separated list '{0}'. The path to the service executable can be configured from the Plugin Configuration in the Deadline Monitor.".format( self.ExeList ) )
        
        # We can get the ini file directory by using the AME_Executable path.
        directoryPos = self.AME_Executable.rfind("\\")
        if directoryPos == -1:
            directoryPos = self.AME_Executable.rfind("/")
            
        iniFolder = self.AME_Executable[:directoryPos+1]
        iniFile = iniFolder+"ame_webservice_config.ini"
        iniFile = str(PathUtils.ToPlatformIndependentPath(str(iniFile)))
        
        # Check if ini file exists.
        if os.path.isfile( iniFile ):
            self.LogInfo( "Looking for hostname/ip and port override in config ini file: %s" % iniFile )
            # Use the port and host name from the file.
            content = []
            with open(iniFile) as f:
                content = f.readlines()
            for line in content:
                if "ip =" in line and "#" not in line:
                    tokens = line.split(" = ")
                    if len(tokens) > 1:
                        self.AME_Host = tokens[1].strip()
                elif "port =" in line and "#" not in line:
                    tokens = line.split(" = ")
                    if len(tokens) > 1:
                        self.AME_Port = int(tokens[1].strip())

        self.LogInfo( "Executable: %s" % self.AME_Executable )
        self.LogInfo( "Host: %s" % self.AME_Host )
        self.LogInfo( "Port: %s" % self.AME_Port )
        
        self.AME_Process = MediaEncoderService( self, self.AME_Executable )
        self.StartMonitoredManagedProcess( self.AME_ProcessName, self.AME_Process )

        # Allow time for the Web Service to start.
        SystemUtils.Sleep( 5000 )
        
        hConn = httplib.HTTPConnection( self.AME_Host, self.AME_Port )
        try:
            # Poll Server Status until it's online.
            hConn.request( 'GET', "/server" )
            response = hConn.getresponse()
            while ( response.status == httplib.OK or response.status == httplib.ACCEPTED ):
                
                SystemUtils.Sleep( 2000 )

                # Make sure to check for render task being canceled.
                if self.IsCanceled():
                    self.Shutdown()
                    self.FailRender( "Received cancel task command" )

                self.VerifyMonitoredManagedProcess( self.AME_ProcessName )
                self.FlushMonitoredManagedProcessStdout( self.AME_ProcessName )

                hConn.request( 'GET', "/server" )
                response = hConn.getresponse()
                xmlBody = response.read()
                xRoot = ET.fromstring( xmlBody )
                xStatus = xRoot.find( "ServerStatus" )

                if xStatus != None:
                    if xStatus.text.strip() == self.AME_ONLINE:
                        # We're online!
                        self.LogInfo( "AME Web Service started." )
                        break
        finally:
            hConn.close()

    ## Sends a restart command to the webserver, and waits for it to complete
    ## NOTE: This does NOT seem to *restart* an already-Online Server. Only
    ##       use this function on a Server whose status is 'Offline'
    def RestartServer( self ):
        # Sending a POST to /server is a restart.
        hConn = httplib.HTTPConnection( self.AME_Host, self.AME_Port )
        try:
            hConn.request( 'POST', "/server" )
            response = hConn.getresponse()

            # Poll Server Status until it's online.
            while ( response.status == httplib.OK or response.status == httplib.ACCEPTED ):
                
                SystemUtils.Sleep( 2000 )

                # Make sure to check for render task being canceled.
                if self.IsCanceled():
                    self.Shutdown()
                    self.FailRender( "Received cancel task command" )

                hConn.request( 'GET', "/server" )
                response = hConn.getresponse()
                xmlBody = response.read()
                xRoot = ET.fromstring( xmlBody )
                xStatus = xRoot.find( "ServerStatus" )

                if xStatus != None:
                    if xStatus.text.strip() == self.AME_ONLINE:
                        # We're online!
                        break
        finally:
            hConn.close()

    ## Called by Deadline when a task is to be rendered.
    def RenderTasks( self ):
        jobURI = "{0}:{1}/job".format( self.AME_Host, self.AME_Port )

        # Get mandatory & optional plugin info.
        inputPath = self.handleFilePath( self.GetPluginInfoEntry( "InputPath" ) ) # Mandatory
        outputPath = self.handleFilePath( self.GetPluginInfoEntry( "OutputPath" ) ) # Mandatory

        # Check if output directory exists, create if otherwise. AME will fail if the directory doesn't exist.
        directory = os.path.dirname( outputPath )
        
        if not os.path.exists( directory ):
            self.LogWarning( 'The output folder does not exist: "%s", trying to create it...' % directory )
            try:
                os.makedirs( directory )
            except Exception as e:
                self.FailRender( 'Failed to create the directory: "%s", please ensure the directory is created and accessible before trying again.\n%s' % ( directory, e ) )
        elif not os.path.isdir( directory ):
            self.FailRender( '"%s" exists but it is not a directory. Choose a different destination and ensure it exists and is accessible.' % directory )

        overwrite = self.GetBooleanPluginInfoEntryWithDefault( "OverwriteOutput", True ) # Optional

        # Check if we have an .EPR file as a data file.
        presetPath = self.GetDataFilename()
        if not presetPath:
            presetPath = self.handleFilePath( self.GetPluginInfoEntry( "PresetFile" ) )

        args = {}
        args["SourceFilePath"] = inputPath
        args["DestinationPath"] = outputPath
        args["SourcePresetPath"] = presetPath

        if overwrite:
            args["OverwriteDestinationIfPresent"] = "true"
        else:
            args["OverwriteDestinationIfPresent"] = "false"

        data = self.buildManifest( args )

        hConn = httplib.HTTPConnection( self.AME_Host, self.AME_Port )
        try:
            headers = { "Content-type" : "text/xml; charset=UTF-8" }
            hConn.request( 'POST', "/job", data, headers )
            response = hConn.getresponse()
            jobStatusXML = response.read()

            breaknext = False

            if response.status == httplib.ACCEPTED or response.status == httplib.OK:
                # Poll for status of job.
                while response.status == httplib.OK or response.status == httplib.ACCEPTED:
                    # Parse the response body into XML.
                    xRoot = ET.fromstring( jobStatusXML )

                    # Get the Job's Status and Progress from the response.
                    xProg = xRoot.find( "JobProgress" )
                    xStatus = xRoot.find( "JobStatus" )
                    
                    if breaknext:
                        break
                    
                    if ( xStatus != None ):
                    
                        if xStatus.text.strip().lower() == "success":
                            break
                            
                        elif "completed" in xStatus.text.strip().lower():
                            breaknext = True

                        self.SetStatusMessage( xStatus.text.strip() )

                        if xStatus.text.strip() in [ self.AME_FAILED, self.AME_NOT_FOUND ]:
                            self.Shutdown()
                            self.FailRender( 'Render failed because the AME job status is "%s". Please check the AME logs located in the Adobe documents folder.' % xStatus.text.strip() )
                            break

                        if ( xProg != None and xProg.text != None ):
                            self.SetProgress( float(xProg.text.strip()) )
                            # self.LogInfo( "{0} Progress: {1}%".format( xStatus.text, xProg.text ) )
                    else:
                        self.LogInfo( "Received empty status from web service." )

                    SystemUtils.Sleep( 1000 )

                    # Make sure to check for render task being canceled.
                    if self.IsCanceled():
                        self.Shutdown()
                        self.FailRender( "Received cancel task command" )

                    if self.AME_Process:
                        self.VerifyMonitoredManagedProcess( self.AME_ProcessName )
                        self.FlushMonitoredManagedProcessStdout( self.AME_ProcessName )

                    # Query the status of the job.
                    hConn.request( 'GET', "/job", "", headers )
                    response = hConn.getresponse()
                    jobStatusXML = response.read()
                    
            else:
                errorMsg = str(response.status)
                if response.status == httplib.INTERNAL_SERVER_ERROR:
                    errorMsg = 'Media Encoder responded with "Internal Server Error". Please ensure that the Input Path, Output Path and Preset File locations are valid and are the correct formats.'
                self.Shutdown()
                self.FailRender( errorMsg )

        finally:
            hConn.close()

    ## Shutdown AME web server and Media Encoder instance.
    def Shutdown( self ):
        if self.AME_Process:
            self.LogInfo( "Closing Media Encoder..." )
            hConn = httplib.HTTPConnection( self.AME_Host, self.AME_Port )
            hConn.request( 'DELETE', "/server" ) # Shut down the actual Adobe Media Encoder instance.
            hConn.close()
            
            if self.AMEAutoShutdown:
                if ProcessUtils.KillProcesses( self.AME_ExeName ):
                    self.LogInfo( "Successfully shutdown: %s" % self.AME_ExeName )
            
            self.LogInfo( "Closing Web Service Process..." )
            self.ShutdownMonitoredManagedProcess( self.AME_ProcessName )
        else:
            self.LogInfo( "Slave did not start the AME Web Service, leaving it running." )

    ## Called by Deadline when the Job is unloaded.
    def EndJob( self ):
        self.Shutdown()

    def handleFilePath( self, filePath ):
        filePath = RepositoryUtils.CheckPathMapping( filePath ).replace( "\\", "/" )
        
        if SystemUtils.IsRunningOnWindows() and filePath.startswith( "/" ) and not filePath.startswith( "//" ):
            filePath = "/" + filePath

        return filePath

    def buildManifest( self, kvps ):
        lines = []
        lines.append( '<?xml version="1.0" encoding="UTF-8"?>' )
        lines.append( '<!DOCTYPE manifest>' )
        lines.append( '<manifest version="1.0">' )

        for key, value in kvps.iteritems():
            lines.append( u'\t<{0}>{1}</{0}>'.format( key, value ).encode( 'utf-8' ) ) # Encode in utf-8 in case any of the KVPs were unicode.

        lines.append( '</manifest>' )

        return "\n".join( lines )

######################################################################
## This is the class that starts up the Media Encoder Web Service.
######################################################################
class MediaEncoderService( ManagedProcess ):

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
        self.PopupHandling = True
        self.StdoutHandling = True
        self.HideDosWindow = True
        self.UseProcessTree = True

    def PreRenderTasks( self ):
        self.deadlinePlugin.LogInfo( "Media Encoder Web Service starting..." )

    def RenderExecutable( self ):
        return self.Executable

    def RenderArgument( self ):
        return ""

    def PostRenderTasks( self ):
        self.deadlinePlugin.LogInfo( "Media Encoder Web Service stopped." )
