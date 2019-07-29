from __future__ import print_function
from System.Collections.Specialized import *
from System.IO import *

from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import ScriptRepositorySelectionDialog

scriptDialog = None
settings = None

def __main__():
    global scriptDialog
    global settings
    scriptDialog = DeadlineScriptDialog()
    selectedJobs = MonitorUtils.GetSelectedJobs()

    if len(selectedJobs) > 1:
        scriptDialog.ShowMessageBox( "Only one job can be selected at a time.", "Multiple Jobs Selected" )
        return

    job = selectedJobs[0]
    if job.JobStatus != "Suspended" and job.JobStatus != "Completed" and job.JobStatus != "Failed":
        scriptDialog.ShowMessageBox( "Cannot transfer this job because it is " + job.JobStatus + ". Only completed, suspended, or failed jobs may be transferred.", "Error" )
        return  
    
    transferJobID = job.JobId
    transferJobName = job.JobName
    frameList = job.JobFrames
    chunkSize = job.JobFramesPerTask
    
    scriptDialog.SetTitle( "Transfer Job" )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "JobOptionsSeparator", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0 , "The name of your job.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Transfer of " + transferJobName, 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0 ,  "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0 , "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0 , "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0 , "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0 , "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 5, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 6, 0 , "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 6, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 7, 0 , "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 8, 0 , "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 9, 0 , "If desired, you can automatically archive or delete the job when it completes.", False)
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 9, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 9, 2 , "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.")
    
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 10, 0 , "The list of frames to render.", False)
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", frameList, 10, 1 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 11, 0 , "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", chunkSize, 1, 1000000, 0, 1, 11, 1)
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Transfer Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "RepositoryLabel", "LabelControl", "New Repository", 1, 0 , "The repository root path, or the proxy server and port (in the format proxy:port).", False )
    scriptDialog.AddSelectionControlToGrid( "RepositoryBox", "TextControl", "", "", 1, 1, colSpan=2 )
    scriptDialog.AddControlToGrid( "RepositoryLabel", "LabelControl", "New Certificate", 2, 0 , "The path to the certificate if using a proxy server that requires it.", False )
    scriptDialog.AddSelectionControlToGrid( "CertificateBox", "TextControl", "", "", 2, 1, colSpan=2 )
    changeRepoButton = scriptDialog.AddControlToGrid( "ChangeRepoButton", "ButtonControl", "Change Repository", 1, 3, expand=False )
    changeRepoButton.ValueModified.connect(ChangeRepoButtonPressed)
    
    scriptDialog.AddSelectionControlToGrid( "CompressBox", "CheckBoxControl", False, "Compress Files During Transfer", 3, 1)
    scriptDialog.AddSelectionControlToGrid( "SuspendBox", "CheckBoxControl", False, "Suspend Remote Job After Transfer", 3, 2 )

    scriptDialog.AddSelectionControlToGrid( "EmailBox", "CheckBoxControl", False, "Email Results After Transfer", 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "RemoveBox", "CheckBoxControl", False, "Remove Local Job After Transfer", 4, 2 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "DummyLabel1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ("DepartmentBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineListBox","LimitGroupBox","OnJobCompleteBox","SubmitSuspendedBox","RepositoryBox", "CertificateBox", "SuspendBox","RemoveBox","EmailBox","CompressBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    scriptDialog.ShowDialog( True )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "JobTransferSettings.ini" )
    
def ChangeRepoButtonPressed(*args):
    repoSelectionDialog = ScriptRepositorySelectionDialog()
    repoSelectionDialog.ShowDialog()
    scriptDialog.SetValue("RepositoryBox", repoSelectionDialog.GetConnectionSettings())
    scriptDialog.SetValue("CertificateBox", repoSelectionDialog.GetCertificate())

def SubmitButtonPressed(*args):
    global scriptDialog
    selectedJobs = MonitorUtils.GetSelectedJobs()
    job = selectedJobs[0]
    proxyEnabled = False
    print('submit to', scriptDialog.GetValue( "RepositoryBox" ))
    transferJobID = job.JobId
    transferJobName = job.JobName
    
    transferRepository = scriptDialog.GetValue( "RepositoryBox" )
    certificate  = scriptDialog.GetValue( "CertificateBox" )
    # try parase proxy root
    if ':' in transferRepository:
        try:
            (ip, port) = transferRepository.split(':')
            int(port)
            proxyEnabled = True
        except Exception as e:
            print('Provided repository is not a proxy')

    if certificate != "":
        transferRepository = transferRepository + ';' + certificate
    # Removing checking for the repository to exist because it may not always be reachable from the submitting machine
    # Ensure the repository exists.
    #if not Directory.Exists( transferRepository ):
        #scriptDialog.ShowMessageBox( "A repository at  \"" + transferRepository + "\" does not exist.", "Error" )
        #return
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "job_transfer_info.job" )
    writer = File.CreateText( jobInfoFilename )
    

    writer.WriteLine( "Plugin=JobTransfer" )
    writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
   
    if scriptDialog.GetValue( "IsBlacklistBox" ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    
    if scriptDialog.GetValue( "SubmitSuspendedBox" ):
        writer.WriteLine( "InitialStatus=Suspended" )
        
    writer.WriteLine( "Frames=0" )
    writer.WriteLine( "ChunkSize=1" )
    
    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "job_transfer_plugin.job" )
    writer = File.CreateText( pluginInfoFilename )
    if proxyEnabled:
        writer.WriteLine( "Proxy=true" )
    else:
        writer.WriteLine( "Proxy=false" )
    writer.WriteLine( "TransferJobID=%s" % transferJobID )
    writer.WriteLine( "TransferRepository=%s" % transferRepository )
    writer.WriteLine( "TransferJobFrames=%s" % scriptDialog.GetValue( "FramesBox" ) )
    writer.WriteLine( "TransferJobChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
    writer.WriteLine( "SuspendedAfterTransfer=%s" % scriptDialog.GetValue( "SuspendBox" ) )
    writer.WriteLine( "RemoveLocalAfterTransfer=%s" % scriptDialog.GetValue( "RemoveBox" ) )
    writer.WriteLine( "EmailResultsAfterTransfer=%s" % scriptDialog.GetValue( "EmailBox" ) )
    writer.WriteLine( "CompressFiles=%s" % scriptDialog.GetValue( "CompressBox" ) )
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    arguments.Add( "-notify" )
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    ClientUtils.ExecuteCommand( arguments )
