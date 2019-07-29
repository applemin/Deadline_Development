import socket

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
portNumberInfoLabel = None
settings = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global scriptDialog
    global portNumberInfoLabel
    global settings
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Setup Nuke Frame Server Slaves With Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'NukeFrameServer' ) )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 4, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 5, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 5, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 6, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 6, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 7, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 7, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 8, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 8, 1 )
    
    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 9, 0, "The number of minutes a slave has to render a task for this job before it Completes it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 9, 1 )
    
    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 10, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 11, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 11, 1, colSpan=2 )

    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 12, 1, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 12, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )

    scriptDialog.AddSelectionControlToGrid( "IsInterruptible", "CheckBoxControl", False, "Job Is Interruptible", 13, 1, "If enabled, this job can be interrupted by a higher priority job during rendering. Note that if a slave moves to a higher priority job, it will not be able to join this render again." )

    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Nuke Studio Frame Server Options", 14, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "MaximumServersLabel", "LabelControl", "Maximum Servers", 15, 0, "The maximum number of Frame Server machines to reserve for distributed rendering.", False )
    scriptDialog.AddRangeControlToGrid( "MaximumServersBox", "RangeControl", 10, 1, 100, 0, 1, 15, 1 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 16, 0, "The version of the application.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "11.3", ("9.0","10.0","10.5","11.0","11.1","11.2","11.3"), 16, 1 )
    
    scriptDialog.AddControlToGrid("HostNameLabel", "LabelControl", "Host", 17, 0, "IP Address or the Host Name of the workstation that will start the render.", False )
    scriptDialog.AddControlToGrid("HostNameBox", "TextControl", "", 17, 1, colSpan=2)

    scriptDialog.AddControlToGrid( "PortNumberLabel", "LabelControl", "Port Number", 18, 0, "The TCP port to use. Defaults to 5560.", False )
    scriptDialog.AddRangeControlToGrid( "PortNumberBox", "RangeControl", 5560, 1024, 65535, 0, 1, 18, 1 )
    
    scriptDialog.AddControlToGrid( "WorkerLabel", "LabelControl", "Worker Count", 19, 0, "The number of workers to start on each machine.", False )
    scriptDialog.AddRangeControlToGrid("WorkerBox", "RangeControl", 2, 1, 100, 0, 1, 19, 1)
    
    scriptDialog.AddControlToGrid("WorkerThreadLabel", "LabelControl", "Worker Threads", 20, 0, "The number of threads to start for each worker.", False )
    scriptDialog.AddRangeControlToGrid("WorkerThreadBox", "RangeControl", 1, 1, 256, 0, 1, 20, 1)
    
    scriptDialog.AddControlToGrid("WorkerMemLabel", "LabelControl", "Worker Memory", 21, 0, "The amount of memory to reserve for each worker machine.", False )
    scriptDialog.AddRangeControlToGrid("WorkerMemBox", "RangeControl", 1024, 256, 65536, 0, 1, 21, 1)
    
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 1 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 2, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 3, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","TaskTimeoutBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","MaximumServersBox","VersionBox","PortNumberBox","IsInterruptible","HostNameBox","WorkerBox","WorkerThreadBox","WorkerMemBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    if scriptDialog.GetValue( "HostNameBox" ) == "":
        scriptDialog.SetValue( "HostNameBox", socket.getfqdn() )

    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "NukeFrameServerSettings.ini" )
    
def SubmitButtonPressed(*args):
    global scriptDialog

    if len(scriptDialog.GetValue("HostNameBox")) <=0:
        scriptDialog.ShowMessageBox( "Host Name must be specified.", "Invalid Submission" )
        return

    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "nuke_frame_server_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=NukeFrameServer" )
    writer.WriteLine( "Frames=0-%s\n" % (scriptDialog.GetValue( "MaximumServersBox" )-1) )
    
    jobName = scriptDialog.GetValue( "NameBox" )
            
    if jobName == "":
        jobName = "NukeFrameServerReserve"
            
    writer.WriteLine( "Name=%s" % jobName )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
    writer.WriteLine( "OnTaskTimeout=Complete" )
    writer.WriteLine( "Interruptible=%s" % scriptDialog.GetValue( "IsInterruptible" ) )
        
    if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    
    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "nuke_frame_server_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

    ver = scriptDialog.GetValue( "VersionBox" )
        
    writer.WriteLine( "Version=%s\n" % ver)
        
    writer.WriteLine( "FrameRenderHost=%s\n" % scriptDialog.GetValue("HostNameBox") )
    writer.WriteLine( "FrameRenderPort=%s\n" % scriptDialog.GetValue("PortNumberBox") )
    writer.WriteLine( "FrameRenderWorkers=%s\n" % scriptDialog.GetValue("WorkerBox") )
    writer.WriteLine( "FrameRenderWorkerThreads=%s\n" % scriptDialog.GetValue("WorkerThreadBox") )
    writer.WriteLine( "FrameRenderWorkerMem=%s\n" % scriptDialog.GetValue("WorkerMemBox") )

    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )