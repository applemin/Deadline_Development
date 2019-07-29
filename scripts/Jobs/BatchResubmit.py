"""
BatchResubmit.py - Batch Resubmit Selected 'Normal' Jobs in queue with custom Task/ChunkSize or Frame/ChunkSize sequence or as 'Maintenance' Jobs
Thinkbox Software 2014
"""
from System import *
from System.Collections.Specialized import *
from System.Diagnostics import *
from System.Globalization import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *
from Deadline.Jobs import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None

jobType = "Normal"
framesTasksSelect = "Frames"

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global progressBar

    progressBar = None
    dialogWidth = 500
    dialogHeight = 800
    controlWidth = 152
    labelWidth = 100
    radioButtonWidth = 220
    indentWidth = 50
    indentRadioButtonWidth = 20
    spinnerWidth = 80
    spacer = "    "
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.AllowResizingDialog(False)

    scriptDialog.SetTitle( "Batch Resubmit Jobs To Deadline" )

    scriptDialog.AddGrid()
    jobTypeRC1 = scriptDialog.AddRadioControlToGrid( "Normal", "RadioControl", True, "Resubmit as a Normal Job", "RadioGroupJobType", 0, 0, colSpan=4 )
    jobTypeRC1.ValueModified.connect( JobTypeSelectionChanged )

    scriptDialog.AddControlToGrid( "DummyLabel1", "LabelControl", spacer, 1, 0 ,"", False)
    FramesTasksRC1 = scriptDialog.AddRadioControlToGrid( "Frames", "RadioControl", True, "Frames", "RadioGroupFramesTasks", 1, 1, colSpan=3 )
    FramesTasksRC1.ValueModified.connect( FramesTasksSelectionChanged )
 
    scriptDialog.AddControlToGrid( "DummyLabel2", "LabelControl", spacer+spacer, 2, 0,"", False )
    scriptDialog.AddControlToGrid( "DummyLabel21", "LabelControl", spacer+spacer, 2, 1,"", False )    
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 2, 2, "The list of frames to render.", expand=False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 2, 3 )

    #scriptDialog.AddControlToGrid( "DummyLabel3", "LabelControl", "", indentWidth, -1 )  
    scriptDialog.AddControlToGrid( "FramesChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 2, "This is the number of frames that will be rendered at a time for each job task.",expand=False )
    scriptDialog.AddRangeControlToGrid( "FramesChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 3,3, expand=False )
    #scriptDialog.AddHorizontalSpacerToGrid("HSpacer1", 3, 4)

    scriptDialog.AddControlToGrid( "DummyLabel4", "LabelControl", spacer, 4,0,"", False )  
    FramesTasksRC2 = scriptDialog.AddRadioControlToGrid( "Tasks", "RadioControl", False, "Tasks", "RadioGroupFramesTasks", 4, 1, colSpan=3 )
    FramesTasksRC2.ValueModified.connect( FramesTasksSelectionChanged )

    scriptDialog.AddControlToGrid( "DummyLabel5", "LabelControl", spacer+spacer, 5, 0, "", False )
    scriptDialog.AddControlToGrid( "DummyLabel51", "LabelControl", spacer+spacer, 5, 1, "", False )
    scriptDialog.AddControlToGrid( "TasksLabel", "LabelControl", "Task ID's", 5, 2, "The list of tasks to render.", False )
    scriptDialog.AddControlToGrid( "TasksBox", "TextControl", "", 5, 3 )

    scriptDialog.AddControlToGrid( "DummyLabel6", "LabelControl", spacer+spacer, 6,0, "", False )  
    scriptDialog.AddControlToGrid( "DummyLabel61", "LabelControl", spacer+spacer, 6,1, "", False )  
    scriptDialog.AddControlToGrid( "TasksChunkSizeLabel", "LabelControl", "Frames Per Task", 6, 2, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "TasksChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 6, 3 )

    jobTypeRC2 = scriptDialog.AddRadioControlToGrid( "Maintenance", "RadioControl", False, "Resubmit as a Maintenance Job", "RadioGroupJobType", 7, 0, colSpan=4 )
    jobTypeRC2.ValueModified.connect( JobTypeSelectionChanged )    

    scriptDialog.AddControlToGrid( "DummyLabel7", "LabelControl", spacer, 8, 0, "", False )
    scriptDialog.AddControlToGrid( "MainStartFrameLabel", "LabelControl", "Start Frame", 8, 1, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "MainStartFrameBox", "RangeControl", 1, 1, 1000000, 0, 1, 8, 2 )

    #scriptDialog.AddControlToGrid( "DummyLabel8", "LabelControl", "", indentWidth, -1 )    
    scriptDialog.AddControlToGrid( "MainEndFrameLabel", "LabelControl", "End Frame", 9, 1, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "MainEndFrameBox", "RangeControl", 1, 1, 1000000, 0, 1, 9, 2 )
    #scriptDialog.AddHorizontalSpacerToGrid("HSpacer3", 9, 3)

    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Suspend Job On Submission", 10, 0, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.", colSpan=4 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "DummyLabel9", 0, 0 )
    progressBar = scriptDialog.AddRangeControlToGrid( "SubmissionProgress", "ProgressBarControl", 0, 0, 100, 0, 0, 0, 1 ,expand=False )
    okButton = scriptDialog.AddControlToGrid( "OkButton", "ButtonControl", "OK", 0, 2, expand=False )
    okButton.ValueModified.connect(OkButtonPressed)
    cancelButton = scriptDialog.AddControlToGrid( "CancelButton", "ButtonControl", "Cancel", 0, 3, expand=False )
    cancelButton.ValueModified.connect(CancelButtonPressed)
    scriptDialog.EndGrid()
    
    scriptDialog.Shown.connect( InitializeDialog )

    scriptDialog.ShowDialog( True )

def InitializeDialog( *args ):
    global scriptDialog

    JobTypeChanged()
    FramesTasksChanged()

def CloseDialog():
    global scriptDialog

    scriptDialog.CloseDialog()

def CancelButtonPressed():
    CloseDialog()

def JobTypeSelectionChanged( *args ):
    global scriptDialog
    global jobType

    radioControl = args[0]

    if( bool(radioControl.TheValue) == True ):
        jobType = radioControl.Name

    JobTypeChanged( jobType )

def JobTypeChanged(*args):
    global scriptDialog
    global jobType
    global framesTasksSelect

    if jobType == "Normal" and framesTasksSelect == "Frames":
        scriptDialog.SetEnabled( "Frames", True )
        scriptDialog.SetEnabled( "FramesLabel", True )
        scriptDialog.SetEnabled( "FramesBox", True )
        scriptDialog.SetEnabled( "FramesChunkSizeLabel", True )
        scriptDialog.SetEnabled( "FramesChunkSizeBox", True )
        scriptDialog.SetEnabled( "Tasks", True )
        scriptDialog.SetEnabled( "TasksLabel", False )
        scriptDialog.SetEnabled( "TasksBox", False )
        scriptDialog.SetEnabled( "TasksChunkSizeLabel", False )
        scriptDialog.SetEnabled( "TasksChunkSizeBox", False )
        scriptDialog.SetEnabled( "MainStartFrameLabel", False )
        scriptDialog.SetEnabled( "MainStartFrameBox", False )
        scriptDialog.SetEnabled( "MainEndFrameLabel", False )
        scriptDialog.SetEnabled( "MainEndFrameBox", False )

    elif jobType == "Normal" and framesTasksSelect == "Tasks":
        scriptDialog.SetEnabled( "Frames", True )
        scriptDialog.SetEnabled( "FramesLabel", False )
        scriptDialog.SetEnabled( "FramesBox", False )
        scriptDialog.SetEnabled( "FramesChunkSizeLabel", False )
        scriptDialog.SetEnabled( "FramesChunkSizeBox", False )
        scriptDialog.SetEnabled( "Tasks", True )
        scriptDialog.SetEnabled( "TasksLabel", True )
        scriptDialog.SetEnabled( "TasksBox", True )
        scriptDialog.SetEnabled( "TasksChunkSizeLabel", True )
        scriptDialog.SetEnabled( "TasksChunkSizeBox", True )
        scriptDialog.SetEnabled( "MainStartFrameLabel", False )
        scriptDialog.SetEnabled( "MainStartFrameBox", False )
        scriptDialog.SetEnabled( "MainEndFrameLabel", False )
        scriptDialog.SetEnabled( "MainEndFrameBox", False )
    
    else:
        scriptDialog.SetEnabled( "Frames", False )
        scriptDialog.SetEnabled( "FramesLabel", False )
        scriptDialog.SetEnabled( "FramesBox", False )
        scriptDialog.SetEnabled( "FramesChunkSizeLabel", False )
        scriptDialog.SetEnabled( "FramesChunkSizeBox", False )
        scriptDialog.SetEnabled( "Tasks", False )
        scriptDialog.SetEnabled( "TasksLabel", False )
        scriptDialog.SetEnabled( "TasksBox", False )
        scriptDialog.SetEnabled( "TasksChunkSizeLabel", False )
        scriptDialog.SetEnabled( "TasksChunkSizeBox", False )
        scriptDialog.SetEnabled( "MainStartFrameLabel", True )
        scriptDialog.SetEnabled( "MainStartFrameBox", True )
        scriptDialog.SetEnabled( "MainEndFrameLabel", True )
        scriptDialog.SetEnabled( "MainEndFrameBox", True )

def FramesTasksSelectionChanged( *args ):
    global scriptDialog
    global framesTasksSelect

    radioControl = args[0]

    if( bool(radioControl.TheValue) == True ):
        framesTasksSelect = radioControl.Name

    FramesTasksChanged( framesTasksSelect )

def FramesTasksChanged( *args ):
    global scriptDialog
    global framesTasksSelect

    if framesTasksSelect == "Frames":
        scriptDialog.SetEnabled( "FramesLabel", True )
        scriptDialog.SetEnabled( "FramesBox", True )
        scriptDialog.SetEnabled( "FramesChunkSizeLabel", True )
        scriptDialog.SetEnabled( "FramesChunkSizeBox", True )
        scriptDialog.SetEnabled( "TasksLabel", False )
        scriptDialog.SetEnabled( "TasksBox", False )
        scriptDialog.SetEnabled( "TasksChunkSizeLabel", False )
        scriptDialog.SetEnabled( "TasksChunkSizeBox", False )

    else:
        scriptDialog.SetEnabled( "FramesLabel", False )
        scriptDialog.SetEnabled( "FramesBox", False )
        scriptDialog.SetEnabled( "FramesChunkSizeLabel", False )
        scriptDialog.SetEnabled( "FramesChunkSizeBox", False )
        scriptDialog.SetEnabled( "TasksLabel", True )
        scriptDialog.SetEnabled( "TasksBox", True )
        scriptDialog.SetEnabled( "TasksChunkSizeLabel", True )
        scriptDialog.SetEnabled( "TasksChunkSizeBox", True )
    
def OkButtonPressed( *args ):
    global scriptDialog
    global progressBar
    global jobType
    global framesTasksSelect

    if jobType == "Normal":
        
        # FRAMES submission
        if framesTasksSelect == "Frames":
            resubmitFrames = scriptDialog.GetValue( "FramesBox" )
            if resubmitFrames != "":
                if not ( FrameUtils.FrameRangeValid( resubmitFrames ) ):
                    scriptDialog.ShowMessageBox( "Invalid Frame Range!", "Error" )
                    return
        
        # TASKS submission
        if framesTasksSelect == "Tasks":
            resubmitTasks = scriptDialog.GetValue( "TasksBox" )
            if not ( FrameUtils.FrameRangeValid( resubmitTasks ) ):
                scriptDialog.ShowMessageBox( "Invalid Task Range!", "Error" )
                return

    selectedJobs = MonitorUtils.GetSelectedJobs()

    jobCount = len( selectedJobs )
    scriptDialog.SetValue( "SubmissionProgress", 0 )

    currJob = 0
    successes = 0
    failures = 0

    if jobCount > 0:
        for job in selectedJobs:

            # Create the job info file to be used during submission.
            jobInfoFile = Path.Combine( ClientUtils.GetDeadlineTempPath(), "batch_job_info.job" )
            writer = File.CreateText( jobInfoFile )

            writer.WriteLine( "Plugin=" + str( job.JobPlugin ) )

            if jobType == "Normal":

                # FRAMES based submission
                if framesTasksSelect == "Frames":
                    resubmitFrames = scriptDialog.GetValue( "FramesBox" )
                    if resubmitFrames != "":
                        writer.WriteLine( "Frames=" + resubmitFrames )
                    else:
                        writer.WriteLine( "Frames=" + str( job.JobFrames ) )
                    
                    writer.WriteLine( "ChunkSize=" + str( scriptDialog.GetValue( "FramesChunkSizeBox" ) ) )

                # TASKS based submission
                if framesTasksSelect == "Tasks":

                    UniqueTaskIDs = []
                    resubmitFrames = []

                    resubmitTasks = FrameUtils.Parse( scriptDialog.GetValue( "TasksBox" ), True )

                    tasks = RepositoryUtils.GetJobTasks( job, True )

                    for task in tasks:
                        for resubmitTask in resubmitTasks:
                            if str(resubmitTask) == task.TaskId:
                                if not str(resubmitTask) in UniqueTaskIDs:
                                    UniqueTaskIDs.append( int(resubmitTask) )

                    for task in tasks:
                        if int(task.TaskId) in UniqueTaskIDs:
                            for frame in task.TaskFrameList:
                                resubmitFrames.append( str(frame) )

                    resubmitFrames = ",".join(resubmitFrames)

                    writer.WriteLine( "Frames=" + str( resubmitFrames ) )
                    writer.WriteLine( "ChunkSize=" + str( scriptDialog.GetValue( "TasksChunkSizeBox" ) ) )

            if jobType == "Maintenance":
                writer.WriteLine( "MaintenanceJob=True" )
                writer.WriteLine( "MaintenanceJobStartFrame=" + str( scriptDialog.GetValue( "MainStartFrameBox" ) ) )
                writer.WriteLine( "MaintenanceJobEndFrame=" + str( scriptDialog.GetValue( "MainEndFrameBox" ) ) )
            elif job.MaintenanceJob:
                writer.WriteLine( "MaintenanceJob=" + str( job.JobMaintenanceJob ) )
                writer.WriteLine( "MaintenanceJobStartFrame=" + str( job.JobMaintenanceJobStartFrame ) )
                writer.WriteLine( "MaintenanceJobEndFrame=" + str( job.JobMaintenanceJobEndFrame ) )

            tempName = str( job.JobName ) + " [resubmitted]"
            writer.WriteLine( "Name=" + str( tempName ) )
            writer.WriteLine( "UserName=" + str( job.JobUserName ) )
            writer.WriteLine( "Department=" + str( job.JobDepartment ) )
            writer.WriteLine( "Comment=" + str( job.JobComment ) )
            writer.WriteLine( "Group=" + str( job.JobGroup ) )
            writer.WriteLine( "Pool=" + str( job.JobPool ) )
            writer.WriteLine( "SecondaryPool=" + str( job.JobSecondaryPool ) )
            writer.WriteLine( "Priority=" + str( job.JobPriority ) )
            writer.WriteLine( "ForceReloadPlugin=" + str( job.JobForceReloadPlugin ) )
            writer.WriteLine( "SynchronizeAllAuxiliaryFiles=" + str( job.JobSynchronizeAllAuxiliaryFiles ) )

            if( bool( scriptDialog.GetValue( "SubmitSuspendedBox" ) ) ):
                writer.WriteLine( "InitialStatus=Suspended" )

            writer.WriteLine( "LimitGroups=" + StringUtils.ToCommaSeparatedString( job.JobLimitGroups, False ) )
            writer.WriteLine( "MachineLimit=" + str( job.JobMachineLimit ) )
            writer.WriteLine( "MachineLimitProgress=" + str( job.JobMachineLimitProgress ) )

            if len( job.JobListedSlaves ) > 0:
                if job.JobWhitelistFlag:
                    writer.WriteLine( "Whitelist=" + StringUtils.ToCommaSeparatedString( job.JobListedSlaves, False ) )
                else:
                    writer.WriteLine( "Blacklist=" + StringUtils.ToCommaSeparatedString( job.JobListedSlaves, False ) )

            if job.JobOnJobComplete == "Delete":
                writer.WriteLine( "DeleteOnComplete=true" )
            elif job.JobOnJobComplete == "Archive":
                writer.WriteLine( "ArchiveOnComplete=true" )
            
            writer.WriteLine( "ConcurrentTasks=" + str( job.JobConcurrentTasks ) )
            writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=" + str( job.JobLimitTasksToNumberOfCpus ) )
            writer.WriteLine( "Sequential=" + str( job.JobSequentialJob ) )
            writer.WriteLine( "Interruptible=" + str( job.JobInterruptible ) )
            writer.WriteLine( "SuppressEvents=" + str( job.JobSuppressEvents ) ) 

            envIndex = 0
            envTempList = job.GetJobEnvironmentKeys()
            for key in envTempList:
                writer.WriteLine( "EnvironmentKeyValue%d=%s=%s" % ( envIndex, key, job.GetJobEnvironmentKeyValue( key ) ) )
                envIndex += 1

            writer.WriteLine( "UseJobEnvironmentOnly=" + str( job.JobUseJobEnvironmentOnly ) )
            writer.WriteLine( "CustomPluginDirectory=" + str( job.JobCustomPluginDirectory ) )
            writer.WriteLine( "OverrideJobFailureDetection=" + str( job.JobOverrideJobFailureDetection ) )
            writer.WriteLine( "FailureDetectionJobErrors=" + str( job.JobFailureDetectionJobErrors ) )
            writer.WriteLine( "OverrideTaskFailureDetection=" + str( job.JobOverrideTaskFailureDetection ) )
            writer.WriteLine( "FailureDetectionTaskErrors=" + str( job.JobFailureDetectionTaskErrors ) )
            writer.WriteLine( "IgnoreBadJobDetection=" + str( job.JobIgnoreBadSlaveDetection ) )
            writer.WriteLine( "SendJobErrorWarning=" + str( job.JobSendJobErrorWarning ) )
            writer.WriteLine( "MinRenderTimeSeconds=" + str( job.JobMinRenderTimeSeconds ) )
            writer.WriteLine( "TaskTimeoutSeconds=" + str( job.JobTaskTimeoutSeconds ) )
            writer.WriteLine( "OnTaskTimeout=" + str( job.JobOnTaskTimeout ) )
            writer.WriteLine( "EnableAutoTimeout=" + str( job.JobEnableAutoTimeout ) )
            writer.WriteLine( "EnableTimeoutsForScriptTasks=" + str( job.JobEnableTimeoutsForScriptTasks ) )
            
            #Job Dependencies
            dependencies = job.JobDependencies
            current = 0
            for dependency in dependencies:
                writer.WriteLine( "JobDependency" + str(current) + "=" + str(dependency.JobID) )
                
                if dependency.Notes != None and dependency.Notes != "":
                    writer.WriteLine( "JobDependencyNotes" + str(current) + "=" + str(dependency.Notes) )
                    
                if dependency.OverrideFrameOffsets:
                    writer.WriteLine( "JobDependencyFrameOffsetOverride" + str(current) + "=" + str(dependency.StartOffset) + "," + str(dependency.EndOffset) )
                
                if dependency.OverrideResumeOn:
                    overrides = ""
                    
                    if dependency.ResumeOnComplete:
                        overrides += "complete"
                    if dependency.ResumeOnDeleted:
                        if overrides != "":
                            overrides += ","
                        overrides += "deleted"
                    if dependency.ResumeOnFailed:
                        if overrides != "":
                            overrides += ","
                        overrides += "failed"
                    if dependency.ResumeOnPercentageCompleted:
                        if overrides != "":
                            overrides += ","
                        overrides += str(dependency.ResumeOnPercentageValue)
                        
                    writer.WriteLine( "JobDependencyResumeOnOverride" + str(current) + "=" + overrides )
                
                current += 1
            
            writer.WriteLine( "JobDependencyPercentage=" + str( job.JobDependencyPercentageValue ) )
            writer.WriteLine( "IsFrameDependent=" + str( job.JobIsFrameDependent ) )
            writer.WriteLine( "FrameDependencyOffsetStart=" + str( job.JobFrameDependencyOffsetStart ) )
            writer.WriteLine( "FrameDependencyOffsetEnd=" + str( job.JobFrameDependencyOffsetEnd ) )
            writer.WriteLine( "ResumeOnCompleteDependencies=" + str( job.JobResumeOnCompleteDependencies ) )
            writer.WriteLine( "ResumeOnDeletedDependencies=" + str( job.JobResumeOnDeletedDependencies ) )
            writer.WriteLine( "ResumeOnFailedDependencies=" + str( job.JobResumeOnFailedDependencies ) )

            #Asset Dependencies
            assets = job.RequiredAssets
            current = 0
            for asset in assets:
                writer.WriteLine( "AssetDependency" + str(current) + "=" + str(asset.FileName) )
                
                if asset.Notes != None and asset.Notes != "":
                    writer.WriteLine( "AssetDependencyNotes" + str(current) + "=" + str(asset.Notes) )
                if asset.OverrideFrameOffsets:
                    writer.WriteLine( "AssetDependencyFrameOffsetOverride" + str(current) + "=" + str(asset.StartOffset) + "," + str(asset.EndOffset) )
                    
                current += 1
            
            #Script Dependencies
            scripts = job.JobScriptDependencies
            current = 0
            for script in scripts:
                writer.WriteLine( "ScriptDependency" + str(current) + "=" + str(script.FileName) )
                
                if script.Notes != None and script.Notes != "":
                    writer.WriteLine( "ScriptDependencyNotes" + str(current) + "=" + str(script.Notes) )
                    
                current += 1
            
            writer.WriteLine( "ScheduledType=" + str( job.JobScheduledType ) )
            
            if job.JobScheduledType != "None":
                writer.WriteLine( "ScheduledStartDateTime=" + str( job.JobScheduledStartDateTime ) )
                writer.WriteLine( "ScheduledDays=" + str( job.JobScheduledDays ) )

            for i in range( 0, len(job.JobOutputFileNames) ):
                tempOutputFilename = str( job.JobOutputFileNames[i] ).replace( "\\", "/" )
                writer.WriteLine( "OutputFilename" + str( i ) + "=" + tempOutputFilename )

            for i in range( 0, len(job.JobOutputDirectories) ):
                tempOutputDirectory = str( job.JobOutputDirectories[i] ).replace( "\\", "/" )
                writer.WriteLine( "OutputDirectory" + str( i ) + "=" + tempOutputDirectory )

            Targets = list( job.JobNotificationTargets )
            if job.JobUserName in Targets: Targets.remove( job.JobUserName )
            if len( Targets ) > 0:
                Targets = StringUtils.ToCommaSeparatedString( Targets, False )
                writer.WriteLine( "NotificationTargets=" + str( Targets ) )

            writer.WriteLine( "NotificationEmails=" + StringUtils.ToCommaSeparatedString( job.JobNotificationEmails, False ) )            
            writer.WriteLine( "OverrideNotificationMethod=" + str( job.JobOverrideNotificationMethod ) )
            writer.WriteLine( "EmailNotification=" + str( job.JobEmailNotification ) )
            writer.WriteLine( "PopupNotification=" + str( job.JobPopupNotification ) )
            writer.WriteLine( "NotificationNote=" + str( job.JobNotificationNote ) )
            writer.WriteLine( "PreJobScript=" + str( job.JobPreJobScript ) )
            writer.WriteLine( "PostJobScript=" + str( job.JobPostJobScript) )
            writer.WriteLine( "PreTaskScript=" + str( job.JobPreTaskScript) )
            writer.WriteLine( "PostTaskScript=" + str( job.JobPostTaskScript) )
            
            if job.JobTileJob:
                writer.WriteLine( "TileJob=" + str( job.JobTileJob ) )
                writer.WriteLine( "TileJobFrame=" + str( job.JobTileJobFrame ) )
                writer.WriteLine( "TileJobTilesInX=" + str( job.JobTileJobTilesInX ) )
                writer.WriteLine( "TileJobTilesInY=" + str( job.JobTileJobTilesInY ) )
                writer.WriteLine( "TileJobTileCount=" + str( job.JobTileJobTileCount ) )

            writer.WriteLine( "ExtraInfo0=" + str( job.JobExtraInfo0 ) )
            writer.WriteLine( "ExtraInfo1=" + str( job.JobExtraInfo1 ) )
            writer.WriteLine( "ExtraInfo2=" + str( job.JobExtraInfo2 ) )
            writer.WriteLine( "ExtraInfo3=" + str( job.JobExtraInfo3 ) )
            writer.WriteLine( "ExtraInfo4=" + str( job.JobExtraInfo4 ) )
            writer.WriteLine( "ExtraInfo5=" + str( job.JobExtraInfo5 ) )
            writer.WriteLine( "ExtraInfo6=" + str( job.JobExtraInfo6 ) )
            writer.WriteLine( "ExtraInfo7=" + str( job.JobExtraInfo7 ) )
            writer.WriteLine( "ExtraInfo8=" + str( job.JobExtraInfo8 ) )
            writer.WriteLine( "ExtraInfo9=" + str( job.JobExtraInfo9 ) )

            extraIndex = 0
            extraTempList = job.GetJobExtraInfoKeys()
            for key in extraTempList:
                writer.WriteLine( "ExtraInfoKeyValue%d=%s=%s" % ( extraIndex, key, job.GetJobExtraInfoKeyValue( key ) ) )
                extraIndex += 1

            writer.Close()

            # Create the plugin info file to be used during submission.
            pluginInfoFile = Path.Combine( ClientUtils.GetDeadlineTempPath(), "batch_plugin_info.job" )
            writer = File.CreateText( pluginInfoFile )

            pluginInfoTempList = job.GetJobPluginInfoKeys()
            for key in pluginInfoTempList:
                writer.WriteLine( "%s=%s" % ( key, job.GetJobPluginInfoKeyValue( key ) ) )

            writer.Close()

            arguments = StringCollection()
            arguments.Add( jobInfoFile )
            arguments.Add( pluginInfoFile )

            ## Get the current job's aux files and reference from the network for re-submission
            auxPath = RepositoryUtils.GetJobAuxiliaryPath( job )
            for auxFileName in job.JobAuxiliarySubmissionFileNames:
                if not PathUtils.IsPathRooted( auxFileName ):
                    rootedAuxFileName = Path.Combine( auxPath, auxFileName )
                    arguments.Add( rootedAuxFileName )
                else:
                    arguments.Add( auxFileName )

            ## Submit the Batch Job
            exitCode = ClientUtils.ExecuteCommand( arguments )
            if( exitCode == 0 ):
                successes = successes + 1
            else:
                failures = failures + 1

            currJob += 1
            scriptDialog.SetValue( "SubmissionProgress", ( ( 100 * currJob ) / jobCount ) )

    scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % ( successes, failures ), "Submission Results" )

    CloseDialog()
