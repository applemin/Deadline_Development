import os
import traceback
import mimetypes

from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

from FranticX.Processes import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return EpisodePlugin()

######################################################################
## This is the function that Deadline calls to clean up any
## resources held by the Plugin.
######################################################################
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Episode plugin.
######################################################################
class EpisodePlugin( DeadlinePlugin ):

    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob

    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback

    # Called By Deadline to initalize the process.
    def InitializeProcess( self ):
        self.LogInfo( "Episode Plugin Initializing..." )

        self.SingleFramesOnly = False
        self.StdoutHandling = True
        self.PluginType = PluginType.Advanced

        self.AddStdoutHandlerCallback( "\*\*\* Error: (.*)" ).HandleCallback += self.HandleGenericError

    ## Called by Deadline when the job is first loaded.
    def StartJob( self ):
        self.LogInfo( "Telestream Episode job starting..." )

        self.EpisodeExecutable = self.GetRenderExecutable()

        self.DemoVersion = self.GetBooleanConfigEntryWithDefault( "DemoVersion", False )
        self.LogInfo( "DEMO mode enabled (watermark): %s" % self.DemoVersion )

        self.StartEpisodeProcesses = self.GetBooleanConfigEntryWithDefault( "StartEpisodeProcesses", False )
        self.LogInfo( "Start Episode Processes: %s" % self.StartEpisodeProcesses )

        # Ensure Episode background processes are running.
        if self.StartEpisodeProcesses:
            self.LogInfo( "Starting Episode Background Processes..." )
            args = self.GetEpisodeLaunchArguments( "start" )
            self.EpisodeLaunchProcess( args )
            # Wait 5 seconds as Episode needs a moment to initialise/shutdown, otherwise it
            # raises this error "*** Error: Not connected to local IOServer, unable to share"
            self.TimeToInitialize = self.GetIntegerConfigEntryWithDefault( "TimeToInitialize", 5 )
            self.LogInfo( "Waiting %s seconds to allow Episode processes to initialize..."  % self.TimeToInitialize )
            self.TimeToInitialize = self.TimeToInitialize * 1000
            SystemUtils.Sleep( self.TimeToInitialize )

    ## Called by Deadline when a task is to be rendered.
    def RenderTasks( self ):
        self.LogInfo( "Render Tasks called" )

        # Execute render job by submitting to local episode instance via episodectl.
        arguments = self.GetRenderArguments()
        startupDir = os.path.dirname( self.EpisodeExecutable )

        self.LogInfo( "Submitting Episode workflow job..." )
        self.LogInfo( "Arguments: %s" % arguments )
        self.LogInfo( "StartupDir: %s" % startupDir )

        self.EpisodeSubmit = EpisodeSubmitProcess( self, self.EpisodeExecutable, arguments, startupDir )
        self.RunManagedProcess( self.EpisodeSubmit )
        workflowId = self.EpisodeSubmit.WorkflowId

        if workflowId == "":
            self.FailRender( "Submitted Episode Workflow Id is missing!" )
        else:
            self.LogInfo( "Episode Workflow Id: %s" % workflowId )            

        self.EpisodeStatus = EpisodeStatusProcess( self, self.EpisodeExecutable, workflowId )
        # While loop to check status of locally running Episode job and return success/failure depending on job state.
        while( True ):
            if self.IsCanceled():
                self.FailRender( "Received cancel task command from Deadline." )

            self.RunManagedProcess( self.EpisodeStatus )

            if self.EpisodeStatus.IsWorkflowCompleted():
                self.LogInfo( "Workflow Successfully Completed" )
                break

            # Sleep for 5 seconds between loops.
            SystemUtils.Sleep( 5000 )

    ## Called by Deadline when the job is unloaded.
    def EndJob( self ):
        if self.StartEpisodeProcesses:
            self.LogInfo( "Stopping Episode Background Processes..." )
            args = self.GetEpisodeLaunchArguments( "stop" )
            self.EpisodeLaunchProcess( args )

        self.LogInfo( "Telestream Episode job finished." )

    ##################################################################
    ## Helper functions
    ##################################################################
    def GetRenderExecutable( self ):
        exeList = self.GetConfigEntry( "Episode_InterpreterExecutable" )
        episodeExe = FileUtils.SearchFileList( exeList )

        if episodeExe == "":
            self.FailRender( "Episode executable was not found in the semicolon separated list \"" + exeList + "\". The path to the Episode executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return episodeExe

    def GetEpisodeLaunchArguments( self, command ):
        processList = self.GetConfigEntryWithDefault( "EpisodeRequiredProcesses", "" ).split( ";" )
        arguments = "launch " + command + " "
        for processName in processList:
            if not ( ProcessUtils.IsProcessRunning( processName ) ):
                if processName == "EpisodeNode":
                    arguments += "--node "
                elif processName == "EpisodeIOServer":
                    arguments += "--ioserver "
                elif processName == "EpisodeAssistant":
                    arguments += "--assistant "
                elif processName == "EpisodeClientProxy":
                    arguments += "--clientproxy "
                elif processName == "EpisodeXMLRPCServer":
                    arguments += "--xmlrpc "
                elif processName == "EpisodeJSONRPCServer":
                    arguments += "--jsonrpc "
        return arguments

    def EpisodeLaunchProcess( self, arguments ):
        executable = self.EpisodeExecutable
        startupDir = os.path.dirname( executable )
        exitCode = self.RunProcess( executable, arguments, startupDir, -1 )
        if exitCode != 0:
            self.FailRender( traceback.format_exc() )

    def GetRenderArguments( self ):
        sourceFile = self.GetPluginInfoEntryWithDefault( "SourceFile", "" )
        sourceFile = RepositoryUtils.CheckPathMapping( sourceFile )
        sourceFile = PathUtils.ToPlatformIndependentPath( sourceFile )

        encoderFile = self.GetDataFilename()
        if not encoderFile:
            encoderFile = self.GetPluginInfoEntryWithDefault( "EncoderFile", "" )
            encoderFile = RepositoryUtils.CheckPathMapping( encoderFile )
            encoderFile = PathUtils.ToPlatformIndependentPath( encoderFile )

        outputPath = self.GetPluginInfoEntryWithDefault( "OutputPath", "" )
        outputPath = RepositoryUtils.CheckPathMapping( outputPath )
        outputPath = PathUtils.ToPlatformIndependentPath( outputPath )

        customOutputName = self.GetPluginInfoEntryWithDefault( "CustomOutputName", "" )
        
        arguments = "ws "

        (mimeType, _) = mimetypes.guess_type( sourceFile )

        if mimeType != None and mimeType.startswith( 'video' ):
            #file appears to be a video
            arguments += "-f \"%s\" -e \"%s\" " % ( sourceFile, encoderFile )
        else:
            #file appears to be an image sequence
            arguments += "-f file+iseq:\"%s\" -e \"%s\" " % ( sourceFile, encoderFile )

        if outputPath != "":
            arguments += "-d \"%s/\" " % outputPath

        if customOutputName != "":
            arguments += "--naming \"%s\" " % customOutputName

        extraArgs = self.GetPluginInfoEntryWithDefault( "ExtraArguments", "" )
        if extraArgs != "":
            arguments += "%s " % extraArgs

        if self.DemoVersion:
            arguments += "--demo "

        splitEnabled = self.GetBooleanPluginInfoEntryWithDefault( "SplitEnabled", False )
        maxSplits = self.GetPluginInfoEntryWithDefault( "MaxSplits", "16" )
        minSplitTime = self.GetPluginInfoEntryWithDefault( "MinSplitTime", "30" )

        if splitEnabled:
            arguments += "--split --max-splits %s --min-split-time %s " % ( maxSplits, minSplitTime )

        arguments += "--id-out"

        return arguments

    def HandleGenericError( self ):
        errorMessage = self.GetRegexMatch( 1 )

        if errorMessage.startswith( "Failed to connect to" ): #ServiceNotStarted
            self.FailRender( "The Episode processes are not running on the slave machine. Please start the services on the slave machine." )
        
        elif errorMessage.startswith( "Failed to find cluster" ): #ClusterNotFound
            self.FailRender( "Bonjour could not find the specified cluster on the network." )
        
        else:
            self.FailRender( "Error: %s" % self.GetRegexMatch( 1 ) )

######################################################################
## This is the class that executes up the Episode Submit process.
######################################################################
class EpisodeSubmitProcess( ManagedProcess ):

    def __init__( self, deadlinePlugin, executable, arguments, startupDir ):
        self.deadlinePlugin = deadlinePlugin
        self.Executable = executable
        self.Arguments = arguments
        self.StartupDir = startupDir
        self.WorkflowId = ""
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.StartupDirectoryCallback += self.StartupDirectory

    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.StartupDirectoryCallback
    
    def InitializeProcess( self ):
        self.PopupHandling = True
        self.StdoutHandling = True
        self.HideDosWindow = True
        self.AsynchronousStdout = True

        self.AddStdoutHandlerCallback( ".*(WOFL-.*)" ).HandleCallback += self.HandleJobId
        self.AddStdoutHandlerCallback( ".*Error:.*" ).HandleCallback += self.HandleStdoutError
    
    def RenderExecutable( self ):
        return self.Executable
    
    def RenderArgument( self ):
        return self.Arguments
    
    def StartupDirectory( self ):
        return self.StartupDir

    def HandleStdoutError( self ):
        self.deadlinePlugin.FailRender( "Error submitting Episode workflow job: %s" % traceback.format_exc() )

    def HandleJobId( self ):
        self.WorkflowId = self.GetRegexMatch( 1 )

######################################################################
## This is the class that executes up the Episode Status process.
######################################################################
class EpisodeStatusProcess( ManagedProcess ):
    
    def __init__( self, deadlinePlugin, executable, workflowId ):
        self.deadlinePlugin = deadlinePlugin
        self.Executable = executable
        self.workflowId = workflowId

        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.workflowCompleted = False

    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def InitializeProcess( self ):
        self.PopupHandling = True
        self.StdoutHandling = True
        self.HideDosWindow = True

        # Episode initial status values
        self.workflowStatusCode = "0"
        self.workflowStatusText = ""
        self.taskStatusCode = "0"
        self.taskStatusText = ""
        self.taskProgess = "0"
        self.taskTypeName = ""
        self.taskName = ""

        self.AddStdoutHandlerCallback( "(.*)\|(.*)\|(.*)\|(.*)\|(.*)\|(.*)\|(.*)" ).HandleCallback += self.ParseStatus

    def RenderExecutable( self ):
        return self.Executable

    def RenderArgument( self ):
        arguments = "st --id %s " % self.workflowId
        arguments += "--out workflow.status.code workflow.status.text task.status.code task.status.text task.progress task.type-name task.name"
        return arguments

    def IsWorkflowCompleted( self ):
        return self.workflowCompleted

    def ParseStatus( self ):
        """
        workflow.status.code
        workflow.status.text

                Current status of the workflow as a status code or text. 

                Notice: This differs from the status of command status workflows,
                the reason is that the status is used as a program exit code in that
                command and therefore needs to be altered, while that is not the
                case here.

                Statuses:

                     Status code    Text string
                     --------------------------
                     0              "Idle"
                     1              "Running"
                     2              "Succeeded"
                     3              "Failed"

        task.type-name

                The type name of the task. Here is the current list of task type
                names:

                        Localize
                        Encode
                        MBR
                        Transfer
                        Move
                        Delete
                        YouTube
                        Execute
                        Mail

        task.status.code
        task.status.text

                Current status code of the task as a number or as text, here is a
                list of each status:

                     Status code    Text string
                     --------------------------
                     0              "Idle"
                     1              "Queued"
                     2              "Submitted"
                     3              "PreStartFail"
                     4              "Running"
                     5              "Cancelled"
                     6              "Succeeded"
                     7              "Failed"
                     8              "Redundant"

        task.progress

                Current progress of the task as a integer value from 0 to 100

        task.name

                The name of the task. In case of Split-and-Stitch or EDL tasks
                (dynamically created tasks), this name is a dynamically generated
                name suitable for human readbility, i.e a GUI. To identify a
                dynamically created task by (user defined) name, use task.user-name.
        """
        self.workflowStatusCode = self.GetRegexMatch( 1 )
        self.workflowStatusText = self.GetRegexMatch( 2 )
        self.taskStatusCode = self.GetRegexMatch( 3 )
        self.taskStatusText = self.GetRegexMatch( 4 )
        self.taskProgess = self.GetRegexMatch( 5 )
        self.taskTypeName = self.GetRegexMatch( 6 )
        self.taskName = self.GetRegexMatch( 7 )

        if self.workflowStatusCode == "0" or self.workflowStatusCode == "1": # 0:Idle, 1:Running
            if self.taskStatusCode == "5":
                self.deadlinePlugin.FailRender( "Task: Cancelled" )
            elif self.taskStatusCode == "7":
                self.deadlinePlugin.FailRender( "Task: Failed" )
            elif self.taskStatusCode == "4": # 4:Running
                msg = "Workflow:[%s] - Task:[%s : %s : %s : %s]" % ( self.workflowStatusText, self.taskTypeName, self.taskStatusText, self.taskProgess, self.taskName )
                self.deadlinePlugin.SetStatusMessage( msg )
                progress = float( self.taskProgess )
                self.deadlinePlugin.SetProgress( progress )
            else:
                pass
        elif self.workflowStatusCode == "2": # 2:Succeeded
            self.deadlinePlugin.LogInfo( "Workflow: Succeeded - Status Code: 2" )
            self.workflowCompleted = True        
        elif self.workflowStatusCode == "3": # 3:Failed
            self.deadlinePlugin.FailRender( "Workflow: Failed - Status Code: 3" )
        else:
            pass
