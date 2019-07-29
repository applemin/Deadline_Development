from System import *
from System.Diagnostics import ProcessPriorityClass
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

from FranticX.Net import *

import os
import sys
import tempfile
import time

from collections import deque
from threading import Thread, Lock

from FranticX.Processes import *

MSOP_SaveMultipleImages = "Save Multiple Images"
MSOP_Export = "File Export"
MSOP_SingleView = "Single View Render"
MSOP_Animation = "Animation Render"
MSOP_Print = "Print"
MSOP_Script = "Run Script"

EX_Luxology = "Luxology"
EX_Visible_Edges = "Visible Edges"
EX_Autodesk = "DWG / DXF"
EX_SAT = "ACIS SAT"
EX_FlatDGN = "Flat DGN"

#The lightning Major.Minor version that this plugin is compatible with
LIGHTING_VERSION = ["1","0"]

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return MicroStationPlugin()

######################################################################
## This is the function that Deadline calls to clean up any
## resources held by the Plugin.
######################################################################
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the MicroStation plugin.
######################################################################
class MicroStationPlugin( DeadlinePlugin ):
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob
        self.MonitoredManagedProcessExitCallback += self.MonitoredManagedProcessExit

        self.CommSocket = None
        self.MS_Process = None
        self.MS_LogTail = None
        self.Exiting = False

    def Cleanup( self ):
        if self.MS_LogTail != None:
            self.MS_LogTail.Dispose()
            self.MS_LogTail = None

        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback
        del self.MonitoredManagedProcessExitCallback

    ## Called By Deadline to initalize the process.
    def InitializeProcess( self ):
        #Set the plugin-specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Advanced

    ## Called by Deadline when the job is first loaded.
    def StartJob( self ):
        self.StartMicroStation()
        self.FlushMSLog()

        operation = self.GetPluginInfoEntryWithDefault( "Operation", "" ).strip()

        # Grab the path to the Design file
        designFile = self.GetDataFilename()
        if not designFile or not self.CheckIfDesignFile( designFile ):
            designFile = self.GetPluginInfoEntryWithDefault( "DesignFile", "" ).strip()
            designFile = RepositoryUtils.CheckPathMapping( designFile, True )

        # Load the Design File, if present (and needed)
        if operation != MSOP_SaveMultipleImages:
            if designFile:
                readOnly = self.GetBooleanPluginInfoEntryWithDefault( "DesignFileReadOnly", True )
                response = self.SendMessageToLightning( "LoadDesignFile;{0};{1}".format( designFile, readOnly ), True )
                self.ValidateResponse( response )
            else:
                self.FailRender( "Operation type '{0}' requires a Design File, but there wasn't one specified or submitted with the Job.".format( operation ) )

        self.FlushMSLog()


    def CheckIfDesignFile( self, filePath ):
        fileName, fileExt = os.path.splitext( filePath )

        fileExt = fileExt.lower().strip()

        return (fileExt == ".dgn" or fileExt == ".dgnlib")


    ## Called by Deadline when a task is to be rendered.
    def RenderTasks( self ):
        
        # Loop through any CExpressions we have and send those over
        exprIndex = 0
        key = "CExpression"
        value = self.GetPluginInfoEntryWithDefault( key + str(exprIndex), None )

        while value is not None:
            exprIndex += 1
            tokens = value.split( '=', 1 )

            if ( len( tokens ) > 1 ):
                self.SendMessageToLightning( "SetOption;{0};{1}".format( tokens[0].strip(), tokens[1].strip() ) )
            else:
                self.LogWarning( "CExpression '{0}' was incorrectly formatted. Expected '<CExpression>=<value>' format." )

            value = self.GetPluginInfoEntryWithDefault( key + str(exprIndex), None )


        # Check what kind of operation we're performing.
        operation = self.GetPluginInfoEntryWithDefault( "Operation", "" ).strip()
        if operation == MSOP_Animation:
            # Mandatory values.
            viewNum = self.GetPluginInfoEntry( "View" ).strip()
            renderMode = self.GetPluginInfoEntry( "RenderMode" ).strip()
            outputPath = self.GetPluginInfoEntry( "OutputPath" ).strip()
            outputPath = RepositoryUtils.CheckPathMapping( outputPath, True )

            # Optional values.
            colorModel =  self.GetPluginInfoEntryWithDefault( "ColorModel", "" ).strip()
            renderSetup = self.GetPluginInfoEntryWithDefault( "RenderSetup", "" ).strip()
            envSetup = self.GetPluginInfoEntryWithDefault( "Environment", "" ).strip()
            lightSetup = self.GetPluginInfoEntryWithDefault( "LightSetup", "" ).strip()
            x = self.GetPluginInfoEntryWithDefault( "OutputSizeX", "0" ).strip()
            y = self.GetPluginInfoEntryWithDefault( "OutputSizeY", "0" ).strip()

            response = self.SendMessageToLightning( "AnimationRender;{0};{1};{2};{3};{4};{5};{6};{7};{8};{9};{10}".format( 
                viewNum, renderMode, colorModel, envSetup, renderSetup, lightSetup, self.GetStartFrame(), self.GetEndFrame(), x, y, outputPath ), True )

            self.ValidateResponse( response )

        elif operation == MSOP_SaveMultipleImages:
            smFile = self.GetPluginInfoEntryWithDefault( "SMIFile", "" )
            for fileName in self.GetAuxiliaryFilenames():
                file, ext = os.path.splitext( fileName )
                if ext.lower().strip() == ".sm":
                    smFile = fileName
                    break

            tempSMFile = self.CreateTempSMFile( smFile, self.GetStartFrame(), self.GetEndFrame() )

            response = None
            if tempSMFile:
                response = self.SendMessageToLightning( "SaveMultipleImages;{0}".format( tempSMFile ), True )

                self.ValidateResponse( response )
            else:
                self.LogWarning( "Could not find SMI entries appropriate for this Task." )

        elif operation == MSOP_Export:
            # Mandatory.
            exportMode = self.GetPluginInfoEntry( "ExportMode" ).strip()
            outputPath = self.GetPluginInfoEntry( "OutputPath" ).strip()
            outputPath = RepositoryUtils.CheckPathMapping( outputPath, True )

            # Rest of args are different based on the Mode.
            if exportMode == EX_Visible_Edges:
                # Visible Edges needs viewport stuff
                viewNum = self.GetPluginInfoEntry( "View" ).strip()

                # Optional args.
                savedView = self.GetPluginInfoEntryWithDefault( "SavedView", "" ).strip()

                response = self.SendMessageToLightning( "Export;{0};{1};{2};{3}".format( exportMode, viewNum, savedView, outputPath ) )
            elif exportMode == EX_Autodesk:
                # Autodesk has an extra config file for settings, find it in aux files
                settingsFile = self.GetPluginInfoEntryWithDefault( "DWSFile", "" )
                for fileName in self.GetAuxiliaryFilenames():
                    file, ext = os.path.splitext( fileName )
                    if ext.lower().strip() == ".dws":
                        settingsFile = fileName
                        break

                response = self.SendMessageToLightning( "Export;{0};{1};{2}".format( exportMode, settingsFile, outputPath ) )
            else:
                # Assume the rest are like LXO/SAT/DGN exports, let Lightning decide if it can handle it.
                response = self.SendMessageToLightning( "Export;{0};{1}".format( exportMode, outputPath ) )

            self.ValidateResponse( response )

        elif operation == MSOP_SingleView:
            # Mandatory.
            viewNum = self.GetPluginInfoEntry( "View" ).strip()
            outputPath = self.GetPluginInfoEntry( "OutputPath" ).strip()
            outputPath = RepositoryUtils.CheckPathMapping( outputPath, True )
            renderMode = self.GetPluginInfoEntry( "RenderMode" ).strip()

            # Optional.
            colorModel =  self.GetPluginInfoEntryWithDefault( "ColorModel", "" ).strip()
            savedView = self.GetPluginInfoEntryWithDefault( "SavedView", "" ).strip()
            renderSetup = self.GetPluginInfoEntryWithDefault( "RenderSetup", "" ).strip()
            lightSetup = self.GetPluginInfoEntryWithDefault( "LightSetup", "" ).strip()
            envSetup = self.GetPluginInfoEntryWithDefault( "Environment", "" ).strip()
            x = self.GetPluginInfoEntryWithDefault( "OutputSizeX", "0" ).strip()
            y = self.GetPluginInfoEntryWithDefault( "OutputSizeY", "0" ).strip()

            response = self.SendMessageToLightning( "RenderView;{0};{1};{2};{3};{4};{5};{6};{7};{8};{9}".format( 
                viewNum, savedView, renderMode, colorModel, envSetup, renderSetup, lightSetup, x, y, outputPath ) )

            self.ValidateResponse( response )

        elif operation == MSOP_Print:
            settingsFile = self.GetPluginInfoEntryWithDefault( "PSETFile", "" )
            for fileName in self.GetAuxiliaryFilenames():
                file, ext = os.path.splitext( fileName )
                if ext.lower().strip() == ".pset":
                    settingsFile = fileName
                    break

            #Optional
            outputPath = self.GetPluginInfoEntryWithDefault( "OutputPath", "" ).strip()
            outputPath = RepositoryUtils.CheckPathMapping( outputPath, True )

            response = self.SendMessageToLightning( "Print;{0};{1}".format( settingsFile, outputPath ) )

            self.ValidateResponse( response )
        elif operation == MSOP_Script:
            scriptFile = self.GetPluginInfoEntryWithDefault( "ScriptFile", "" )
            writeBack = self.GetBooleanConfigEntryWithDefault( "WriteScriptToLog", False )
            module = self.GetPluginInfoEntryWithDefault( "Module", "" )
            submodule = self.GetPluginInfoEntryWithDefault( "Submodule", "" )
            keyinArgs = self.GetPluginInfoEntryWithDefault( "KeyinArgs", "" )

            response = self.SendMessageToLightning( "RunScript;{0};{1};{2};{3};{4}".format( scriptFile, writeBack, module, submodule, keyinArgs ) )
            self.ValidateResponse( response )
        else:
            self.FlushMSLog( True )
            self.FailRender( "Invalid operation '{0}' specified in Plugin Info.".format( operation ) )

        #wait for the Lightning log to 'catch up' to make sure we have everything relevant in the Task Log
        time.sleep( 0.25 ) 

        self.FlushMSLog( True )

    def SendMessageToLightning( self, message, waitForResponse=True ):
        if self.CommSocket is None:
            self.FlushMSLog( True )
            self.FailRender( "Attempted to send message to Lightning before initializing communication socket." )
        
        self.DebugMessage( "Sending command '{0}' to Lightning".format( message ) )
        self.CommSocket.Send( message )

        if waitForResponse:
            return self.WaitForResponse()

    def WaitForResponse( self, failOnError=True ):
        self.DebugMessage( "Waiting for response from Lightning..." )
        consecutiveTimeouts = 0
        while not self.Exiting:
            if self.IsCanceled():
                self.FlushMSLog( True )
                self.FailRender( "Task was canceled by Deadline." )
                break

            self.VerifyMonitoredManagedProcess( "MicroStation" )
            self.FlushMSLog()

            response = None
            try:
                response = self.CommSocket.Receive( 1000 )
                consecutiveTimeouts = 0
            except SimpleSocketTimeoutException:
                consecutiveTimeouts += 1

                if consecutiveTimeouts >= 30:
                    self.FlushMSLog( True )
                    self.FailRender( "Received too many consecutive timeouts while waiting for Lightning." )

            if response == "HEARTBEAT":
                #self.DebugMessage( "Received HEARTBEAT from Lightning" )
                pass
            elif response != None:
                return response;

    ## Validates a response from MicroStation. Will log it appropriately, and fail the render if necessary.
    def ValidateResponse( self, response ):
        self.DebugMessage( "Received response '{0}' from Lightning.".format( response ) )

        tokens = response.split( ';', 1 )

        if tokens[0].startswith( "ERROR" ):
            #An error occurred
            error = tokens[1] if len(tokens) > 1 else ""
            self.FailRender( "Lightning for MicroStation responded with an error: {0}".format( error ) )
        elif tokens[0].startswith( "WARNING" ):
            warn = tokens[1] if len(tokens) > 1 else ""
            self.LogWarning( warn )
        elif tokens[0].startswith( "CHECKLOG" ):
            #An error should be present in the Lightning log
            time.sleep( 0.5 ) #Give log some time to 'catch up'
            self.FlushMSLog( True )

            #if the render hasn't failed, there wasn't an error in there... Check again in a sec
            time.sleep( 1 )
            self.FlushMSLog( True )

            #Still no error in there... weird.
            self.LogWarning( "Lightning signalled failure, but no associated error was found in the Log." )

    ## Called by Deadline when the Job is unloaded.
    def EndJob( self ):
        self.Exiting = True
        self.SendMessageToLightning( "Shutdown", True )
        self.ShutdownMonitoredManagedProcess( "MicroStation" )
        self.FlushMSLog( True )

    def MonitoredManagedProcessExit( self, name ):
        if name == "MicroStation" and not self.Exiting:
            self.FailRender( "MicroStation exited unexpectedly." )

    def StartMicroStation( self ):
        self.CommSocket = ListeningSocket()
        self.CommSocket.StartListening( 0, True, True, 10 )

        listeningPort = -1
        if not self.CommSocket.IsListening:
            self.FlushMSLog( True )
            self.FailRender( "Socket for communication with Lightning has failed to start listening." )
        else:
            listeningPort = self.CommSocket.Port

        arguments = ""
        version = self.GetPluginInfoEntryWithDefault( "Version", "8.0" )
        if version == "8.0":
            arguments = arguments + " -waLightning "
        else:
            arguments = arguments + " -waLightning_CONNECT "

        exeList = self.GetConfigEntry( "MicroStationExecutable" + version.split( '.', 1 )[0] )
        executable = FileUtils.SearchFileList( exeList )

        self.LogInfo( "Using port '{0}' for communication with Lightning.".format( listeningPort ) )

        localPluginDir = self.GetPluginDirectory()
        tempFileName = "MSlog_{0}.txt".format( self.GetThreadNumber() )
        logFilePath = os.path.join( localPluginDir, tempFileName )

        # Clear out the log file/make sure it exists.
        open( logFilePath, 'w' ).close()

        self.MS_Process = MicroStationProcess( executable, arguments, localPluginDir, listeningPort, logFilePath )
        self.MS_LogTail = LogTail( logFilePath, startAtEnd=False )
        self.StartMonitoredManagedProcess( "MicroStation", self.MS_Process )
        
        self.WaitForLightning()

    def WaitForLightning( self ):
        if self.CommSocket is None or not self.CommSocket.IsListening:
            self.FlushMSLog( True )
            self.FailRender( "The communication socket with Lightning has been disposed or is no longer listening.")

        # Poll until we get a connection.
        timeoutSecs = 300
        startTime = time.time()
        while self.CommSocket.IsListening and not self.CommSocket.IsConnected:
            if self.IsCanceled():
                self.FlushMSLog( True )
                self.FailRender( "Rendering was canceled by Deadline." )
            elif (time.time() - startTime) > timeoutSecs:
                self.FlushMSLog( True )
                self.FailRender( "Timed out while waiting for MicroStation and Lightning to start." )

            self.VerifyMonitoredManagedProcess( "MicroStation" )
            self.FlushMSLog()
            time.sleep( 0.1 )

        if not self.CommSocket.IsConnected:
            self.FlushMSLog( True )
            self.FailRender( "The communication socket with Lightning is no longer connected!" )

    def FlushMSLog( self, flushPartialLine=False ):
        if ( self.MS_LogTail != None and self.MS_LogTail.NewLinesReady( flushPartialLine ) ):
            lines = self.MS_LogTail.GetNewLines( flushPartialLine )

            errors = []
            for line in lines:
                # Not *actually* StdOut, but log it as such anyways.
                # Since MS doesn't really produce StdOut normally.
                self.LogStdout( line.rstrip() )

                if line.startswith( "ERROR" ):
                    # Need to fail the render, but finish processing lines first.
                    errors.append( line )

            if len( errors ) > 0:
                self.FailRender( "An error occurred in MicroStation while rendering: {0}".format( errors[0] ) )

    def CreateTempSMFile( self, sourceFile, firstEntry, lastEntry ):
        entryLines = []

        betweenEntries = True
        currEntry = -1
        
        inFile = open( sourceFile, 'r' )
        try:
            line = inFile.readline()

            while line:
                line = RepositoryUtils.CheckPathMapping( line, True )
                # Check if this is the beginning of a new entry.
                if line.strip().lower().startswith( "designfile" ):
                    currEntry += 1
                    betweenEntries = False
                
                if betweenEntries or (firstEntry <= currEntry and currEntry <= lastEntry):
                    # This is an entry we need.
                    entryLines.append( line )

                if not betweenEntries and line.strip().lower() == "end":
                    betweenEntries = True  

                line = inFile.readline()
        finally:
            inFile.close()

        if len( entryLines ) == 0:
            self.FailRender( "SMI Script '{0}' does not contain enough entries for this Task.\nFound {1} entries, but expected at least {2}.".format( sourceFile, currEntry + 1, firstEntry + 1 ) )
            return None
        else:
            tempPath = self.GetJobsDataDirectory()
            tempFileName = "MS_SMI_{0}_temp.sm".format( self.GetThreadNumber() )
            tempFilePath = os.path.join( tempPath, tempFileName )
            tempFile = open( tempFilePath, 'w' )
            try:
                for outLine in entryLines:
                    tempFile.write( outLine )
            finally:
                tempFile.close()

            return tempFilePath

class MicroStationProcess( ManagedProcess ):
    def __init__( self, executable, args, lightningPath, commPort, logFile ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.StartupDirectoryCallback += self.StartupDirectory

        self.Executable = executable
        self.Arguments = args
        self.StartupDir = Path.GetDirectoryName( executable )

        # Set the environment variable to tell the MS process which port we're listening on.
        self.SetEnvironmentVariable( "LIGHTNING_COMM_PORT", str( commPort ) )
        self.SetEnvironmentVariable( "LIGHTNING_LOG_FILE", logFile )
        self.SetEnvironmentVariable( "MS_ADDINPATH", lightningPath ) # Tells MS where to load addins from.
        self.SetEnvironmentVariable( "MS_MDLAPPS", lightningPath )


        #self.DebugLogging = True

    def InitializeProcess( self ):
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True

    def RenderExecutable( self ):
        return self.Executable

    def RenderArgument( self ):
        return self.Arguments

    def StartupDirectory( self ):
        return self.StartupDir

##############################################################################
### Class that will tail a log file, caching newly appended lines
### NOTE: Dispose should be called on this class to properly clean up stuff
##############################################################################
class LogTail( object ):
    SLEEP_TIME_SEC = 0.5 # The sleep time between checks, in seconds.
    TIMEOUT = 60 # Timeout between UpdateCache calls where we'll stop reading the file until the next call.

    def __init__( self, logPath, startAtEnd=True ):
        # Member declaration/instantiation.
        self.logPath = logPath # The path to the log file.
        self.fileHandle = open( self.logPath, 'rb' ) # File handle (persists for the lifetime of the object).
        self.logLines = deque() # Cached lines (using a deque for thread-safe atomic ops).
        self.exitThread = False # Sentinel flag to tell the monitoring thread to exit.
        self.lastQuery = time.time()

        self.incompleteLine = False

        # Read through the current file contents.
        fileContents = self.fileHandle.read()

        if not startAtEnd:
            # We want the current contents too, so add those.
            fileLines = fileContents.splitlines( True )
            for line in fileLines:
                self.logLines.append( line )

            # Keep track of whether the last line ends in a newline char.
            if len(fileLines) > 0:
                self.incompleteLine = not fileLines[-1].endswith( "\n" )

        # Keep track of the current seek position, in case we need to reopen the file or something.
        self.filePos = self.fileHandle.tell()
        self.lastQuery = time.time() # Update timestamp.

        self.threadLock = Lock()

        # Starts the monitoring thread.
        self.monitoringThread = Thread( target=self._updateThread, args=( LogTail.SLEEP_TIME_SEC, ) )
        self.monitoringThread.start()

    ### Function that periodically polls the log file for new changes
    def _updateThread( self, sleepTime ):
        while not self.exitThread:
            # If it's been longer than our timeout, break out and close the file.
            if time.time() - self.lastQuery > LogTail.TIMEOUT:
                break

            time.sleep( sleepTime )

            self.UpdateCache()

        # Acquire lock os we don't close this while we're updating.
        if self.threadLock.acquire():
            try:
                self.fileHandle.close()
                self.fileHandle = None
            finally:
                self.threadLock.release()

    ### Updates the last query time so our update thread doesn't time out.
    ### Also restarts the Thread if it's already died.
    def _kickWatchdog( self ):
        self.lastQuery = time.time()

        # Check if thread is running
        if not self.exitThread and self.monitoringThread != None and not self.monitoringThread.isAlive():
            # Update cache synchronously.
            self.UpdateCache()

            # Restart the thread.
            self.monitoringThread = Thread( target=self._updateThread, args=( LogTail.SLEEP_TIME_SEC, ) )
            self.monitoringThread.start()

    ### Updates the cache with new log file contents (if any)
    def UpdateCache( self ):
        # Make sure this is only run once at a time.
        if self.threadLock.acquire():
            try: # Critical section.
                if self.fileHandle == None:
                    self.fileHandle = open( self.logPath, 'rb' ) # Binary mode is important for seeking.
                    self.fileHandle.seek( self.filePos )

                # Read in any 'new' content.
                fileContents = self.fileHandle.read()

                # Split into lines.
                fileLines = fileContents.splitlines( True )
                for line in fileLines:
                    self.logLines.append( line )

                # Update cur pos in case we need to reopen.
                self.filePos = self.fileHandle.tell()
            finally:
                self.threadLock.release()

    ### Returns True if there are some cached lines available
    def NewLinesReady( self, includePartialLine=False ):
        self._kickWatchdog()

        if len( self.logLines ) == 0:
            return False
        else:
            return includePartialLine or self.logLines[0].endswith( "\n" )

    ### Returns any new lines that have been read from the file since the last call
    def GetNewLines( self, allowPartialLine=False ):
        self._kickWatchdog()

        newLines = []

        try:
            # Rely on the deque's IndexError to break out of the loop.
            while True:
                currLine = self.logLines.popleft()

                # Check whether or not we need to combine with the previous line, if it didn't have a newline char.
                if ( len(newLines) > 0 and not newLines[-1].endswith("\n") ):
                    newLines[-1] += currLine
                else:
                    newLines.append( currLine )
        except IndexError:
            # Deque is empty.
            pass

        # Remove the last line if it's incomplete and the caller wants complete lines only.
        if ( not allowPartialLine and len(newLines) > 0 and not newLines[-1].endswith("\n") ):
            self.logLines.appendleft( newLines.pop() )

        return newLines

    def __del__( self ):
        self.Dispose()

    ### Cleans up resources that might still be kicking around
    def Dispose( self ):
        self.exitThread = True
        try:
            # Wait for the thread to terminate (w/ 2 sec timeout).
            if self.monitoringThread != None:
                self.monitoringThread.join( 2.0 )
                self.monitoringThread = None
        except:
            pass
        
        try:
            # Try to close the file handle, in case the thread had died.
            if self.fileHandle != None:
                self.fileHandle.close()
                self.fileHandle = None
        except:
            pass
