import os
import re

from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog, settings

    scriptDialog = DeadlineScriptDialog()

    scriptDialog.SetTitle( "Setup V-Ray Swarm With Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'VraySwarm' ) )

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

    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "V-Ray Swarm Options", 14, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "MaximumServersLabel", "LabelControl", "Maximum Servers", 15, 0, "The maximum number of Slaves to reserve for distributed rendering.", False )
    scriptDialog.AddRangeControlToGrid( "MaximumServersBox", "RangeControl", 10, 1, 100, 0, 1, 15, 1 )

    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 1 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 2, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 3, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ( "DepartmentBox", "CategoryBox", "PoolBox", "SecondaryPoolBox", "GroupBox", "PriorityBox", "TaskTimeoutBox", "MachineLimitBox", "IsBlacklistBox", "MachineListBox", "LimitGroupBox", "IsInterruptible", "MaximumServersBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return os.path.join( ClientUtils.GetUsersSettingsDirectory(), "VraySwarmSettings.ini" )

def SubmitButtonPressed( *args ):
    global scriptDialog

    jobName = scriptDialog.GetValue( "NameBox" )

    # V-Ray Swarm only allows alpha-numeric characters in a tag
    if re.search( r'[^- \w]', jobName ) is not None: # Found something that's not alpha numeric (\w), hyphen, underscore or space
        scriptDialog.ShowMessageBox( 'Job Name "%s" contains invalid characters for V-Ray Swarm tags. Only Alpha-numeric (a-z, A-Z, 0-9), dashes, and spaces are allowed.' % jobName, "Invalid Submission" )
        return

    # Create job info file.
    jobInfoFilename = os.path.join( ClientUtils.GetDeadlineTempPath(), "vray_swarm_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )

    writer.WriteLine( "Plugin=VraySwarm" )
    writer.WriteLine( "Frames=0-%s\n" % (scriptDialog.GetValue( "MaximumServersBox" ) -1 ) )
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

    if bool( scriptDialog.GetValue( "IsBlacklistBox" ) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )

    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )

    if bool( scriptDialog.GetValue( "SubmitSuspendedBox" ) ):
        writer.WriteLine( "InitialStatus=Suspended" )

    writer.Close()

    # Create plugin info file.
    pluginInfoFilename = os.path.join( ClientUtils.GetDeadlineTempPath(), "vray_swarm_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    writer.Close()

    # Setup the command line arguments.
    arguments = StringCollection()
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )

    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )