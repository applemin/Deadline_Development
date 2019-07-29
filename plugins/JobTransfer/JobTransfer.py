from System import *
from System.Collections.Specialized import *
from System.Diagnostics import *
from System.Globalization import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *

from FranticX.Processes import *

def GetDeadlinePlugin():
    return JobTransferPlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class JobTransferPlugin (DeadlinePlugin):
    submitCommand = None
    deleteCommand = None
    emailCommand = None
    
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
        
        if self.submitCommand:
            self.submitCommand.Cleanup()
            del self.submitCommand
            
        if self.deleteCommand:
            self.deleteCommand.Cleanup()
            del self.deleteCommand
            
        if self.emailCommand:
            self.emailCommand.Cleanup()
            del self.emailCommand
    
    def InitializeProcess( self ):
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Advanced
    
    def StartJob( self ):
        self.LogInfo( "Starting Transfer Job" )
    
    def RenderTasks( self ):
        self.SetStatusMessage( "Validating job to be transferred" )
        
        # Get the transfer information and load the job.
        transferRepository = RepositoryUtils.CheckPathMapping( self.GetPluginInfoEntry( "TransferRepository" ), True )
        transferJobId = self.GetPluginInfoEntry( "TransferJobID" )
        transferJob = RepositoryUtils.GetJob( transferJobId, True )
        
        self.LogInfo( "Attempting to transfer job \"" + transferJob.JobName + "\" with job ID " + transferJobId + " to " + transferRepository + "..." )
        
        # Ensure that the job is suspended before transferring. Fail the job if it isn't.
        if transferJob.JobStatus != "Suspended" and transferJob.JobStatus != "Completed" and transferJob.JobStatus != "Failed":
            self.AbortRender( "Cannot transfer this job because it is " + transferJob.JobStatus + ". Only completed, suspended, or failed jobs may be transferred.", ManagedProcess.AbortLevel.Fatal )
        
        self.LogInfo( "Creating job submission files" )
        
        tempJobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "transfer_job_info.job" )
        tempPluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "transfer_plugin_info.job" )
        
        # Override frame list and chunk size in job if necessary.
        frameList = self.GetPluginInfoEntryWithDefault( "TransferJobFrames", "" )
        if frameList == "":
            transferJob.FramesList = frameList
        
        chunkSize = self.GetIntegerPluginInfoEntryWithDefault( "TransferJobChunkSize", 0 )
        if chunkSize > 0:
            transferJob.ChunkSize = chunkSize
        
        # Create the submission files from the job.
        RepositoryUtils.CreateJobSubmissionFiles( transferJob, tempJobInfoFilename, tempPluginInfoFilename )
        
        # Add additional lines to the job info file so that the job is submitted to the correct repository.
        jobInfoLines = []
        proxy = self.GetPluginInfoEntry( "Proxy" )
        if proxy == "true":
            strippedTransferRepository = str(transferRepository).strip()
            if '\n' in strippedTransferRepository:
                address, certificate = strippedTransferRepository.split('\n')
                transferRepository = unicode(address + ';' + certificate + '\n')
            jobInfoLines.append( "ProxyRoot=" + transferRepository )
        else:
            jobInfoLines.append( "NetworkRoot=" + transferRepository )
        
        if self.GetBooleanPluginInfoEntry( "SuspendedAfterTransfer" ):
            jobInfoLines.append( "InitialStatus=Suspended" )
        
        File.AppendAllText( tempJobInfoFilename, "\n".join(jobInfoLines) )
        # Now submit the job.
        self.SetStatusMessage( "Transferring job" )
        self.LogInfo( "Transferring job" )
        
        arguments = " \"" + tempJobInfoFilename + "\" \"" + tempPluginInfoFilename + "\""
        
        auxPath = RepositoryUtils.GetJobAuxiliaryPath( transferJob )
        for auxFileName in transferJob.AuxiliarySubmissionFileNames:
            if not PathUtils.IsPathRooted( auxFileName ):
                rootedAuxFileName = Path.Combine( auxPath, auxFileName )
                arguments = arguments + " \"" + rootedAuxFileName + "\""
                self.LogInfo( rootedAuxFileName )
            else:
                arguments = arguments + " \"" + auxFileName + "\""
                self.LogInfo( auxFileName )
        
        self.submitCommand = DeadlineCommand( self, arguments, True )
        self.RunManagedProcess( self.submitCommand )
        submitResults = self.submitCommand.GetOutput()
        
        # Delete the local job after a successful transfer if necessary.
        deleteResults = ""
        if self.GetBooleanPluginInfoEntry( "RemoveLocalAfterTransfer" ):
            self.SetStatusMessage( "Deleting local job" )
            self.LogInfo( "Deleting local job" )
            
            # Run the command to delete the job.
            deleteArguments = "DeleteJob \"" + transferJobId + "\""
            self.deleteCommand = DeadlineCommand( self, deleteArguments, False )
            self.RunManagedProcess( self.deleteCommand )
            deleteResults = self.deleteCommand.GetOutput()
        
        # Send notification email after a successful transfer if necessary.
        notificationEmails = self.GetConfigEntry( "NotificationEmail" )
        emailResultsAfterTransfer = self.GetBooleanPluginInfoEntry( "EmailResultsAfterTransfer" )
        if emailResultsAfterTransfer or notificationEmails != "":
            self.SetStatusMessage( "Sending email notification of success" )
            self.LogInfo( "Sending email notification of success" )
            
            newJobId = ""
            newJobIdIndex = submitResults.find( "JobID=" )
            if newJobIdIndex != -1:
                newJobId = submitResults[newJobIdIndex+6:newJobIdIndex+27]
            
            message = StringBuilder()
            message.Append( transferJob.Name )
            message.Append( " was transferred successfully to " )
            message.AppendLine( transferRepository )
            message.AppendLine()
            
            message.AppendLine( "Transfer Results" )
            message.AppendLine( submitResults )
            if deleteResults != "":
                message.AppendLine( deleteResults )
            message.AppendLine()
            
            message.Append( "Job Details" )
            message.AppendLine()
            message.Append( "  name:   " )
            message.Append( transferJob.Name )
            message.AppendLine()
            message.Append( "  id:     " )
            message.AppendLine( newJobId )
            message.AppendLine()
            
            message.Append( "Submission Details" )
            message.AppendLine()
            message.Append( "  username:   ")
            message.Append( transferJob.UserName )
            message.AppendLine()
            message.Append( "  machine:    " )
            message.Append( transferJob.SubmitMachineName )
            message.AppendLine()
            message.Append( "  pool:   " )
            message.Append( transferJob.JobPool )
            message.AppendLine()
            message.Append( "  group:   " )
            message.Append( transferJob.JobGroup )
            message.AppendLine()
            message.Append( "  priority:   " )
            message.Append( transferJob.JobPriority )
            message.AppendLine()
            message.Append( "  department: " )
            message.Append( transferJob.Department )
            message.AppendLine()
            message.Append( "  time:       " )
            message.Append( transferJob.SubmitDateTime.ToString( "MMM dd/yy  HH:mm:ss" ) )
            
            toField = ""
            
            # Only send email to plugin notifications if not empty.
            if notificationEmails != "":
                for notificationEmail in notificationEmails.split( "," ):
                    toField = toField + notificationEmail + ","
            
            # Only send email to job targets if option is enabled.
            if emailResultsAfterTransfer:
                for target in transferJob.NotificationTargets:
                    targetUser = RepositoryUtils.GetUserInfo( target, True )
                    if targetUser.EmailAddress != "":
                        toField = toField + targetUser.EmailAddress + ","
                
                for notificationEmail in transferJob.NotificationEmails:
                    toField = toField + notificationEmail + ","
            
            toField = toField.rstrip( "," )
            if toField != "":
                subject = "Deadline: Job Transfer Completed: " + transferJob.Name
                
                messageFileName = Path.Combine( ClientUtils.GetDeadlineTempPath(), "transfer_job_email.txt" )
                File.WriteAllText( messageFileName, message.ToString() )
                
                emailArguments = "SendEmail -to \"" + toField + "\" -subject \"" + subject.replace( "\"", "'" ) + "\" -message \"" + messageFileName + "\""
                self.emailCommand = DeadlineCommand( self, emailArguments, False )
                self.RunManagedProcess( self.emailCommand )
            else:
                self.LogInfo( "Successful job transfer report not sent because there are no email addresses to send it to" )
    
    def EndJob( self ):
        self.LogInfo( "Finishing Transfer Job" )
    
class DeadlineCommand (ManagedProcess):
    Plugin = None
    Arguments = ""
    FailOnNonZeroExitCode = True
    OutputCollection = StringCollection()
    
    def __init__( self, plugin, arguments, failOnNonZeroExitCode ):
        self.Plugin = plugin
        self.Arguments = arguments
        self.FailOnNonZeroExitCode = failOnNonZeroExitCode
        
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
        self.PopupHandling = True
        self.StdoutHandling = True
        self.AddStdoutHandlerCallback( ".*").HandleCallback += self.GatherOutput
    
    def RenderExecutable( self ):
        return Path.Combine( ClientUtils.GetBinDirectory(), "deadlinecommand.exe" )
        
    def RenderArgument( self ):
        return self.Arguments
    
    def CheckExitCode( self, exitCode ):
        if exitCode != 0:
            message = "DeadlineCommand returned a non-zero exit code of " + str(exitCode) + ". Check the log for more details."
            if self.FailOnNonZeroExitCode:
                self.Plugin.FailRender( message )
            else:
                self.OutputCollection.Add( "Warning: " + message )
                self.Plugin.LogWarning( message )
    
    def GatherOutput( self ):
        self.OutputCollection.Add( self.GetRegexMatch(0) )
    
    def GetOutput( self ):
        outputBuilder = StringBuilder()
        for i in range( 0, self.OutputCollection.Count ):
            outputBuilder.AppendLine( "  " + self.OutputCollection[ i ] )
        return outputBuilder.ToString()
