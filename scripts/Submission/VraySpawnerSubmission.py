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
portNumberLabel = None
portNumberBox = None
settings = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global portNumberInfoLabel
    global portNumberLabel
    global portNumberBox
    global settings
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Setup V-Ray DBR With Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'VraySpawner' ) )
    
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

    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "V-Ray Spawner/Standalone Options", 14, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "MaximumServersLabel", "LabelControl", "Maximum Servers", 15, 0, "The maximum number of V-Ray Servers to reserve for distributed rendering.", False )
    scriptDialog.AddRangeControlToGrid( "MaximumServersBox", "RangeControl", 10, 1, 100, 0, 1, 15, 1 )

    scriptDialog.AddControlToGrid( "ApplicationLabel", "LabelControl", "Application", 16, 0, "The plugin application that will be used.", False )
    applicationBox = scriptDialog.AddComboControlToGrid( "ApplicationBox", "ComboControl", "Select One", ["Select One","3ds Max", "3ds Max (RT)", "Cinema 4D", "Maya", "Modo", "Rhino","SketchUp","Softimage","Standalone"], 16, 1 )
    applicationBox.ValueModified.connect(PopulateDropDowns)

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 17, 0, "The version of the application.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "Select an Application First... ", ["Select an Application First... "], 17, 1 )

    portNumberLabel = scriptDialog.AddControlToGrid( "PortNumberLabel", "LabelControl", "Port Number", 18, 0, "Where available, override the default TCP Port Number used. V-Ray Standalone Default: 20207.", False )
    portNumberBox = scriptDialog.AddRangeControlToGrid( "PortNumberBox", "RangeControl", 20207, 1024, 65535, 0, 1, 18, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    portNumberInfoLabel = scriptDialog.AddControlToGrid( "PortNumberInfoLabel", "LabelControl", "", 0, 0, "Where available, override the default TCP Port Number used. V-Ray Standalone Default: 20207.", False )
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 1 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 2, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 3, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    PopulateDropDowns( None )

    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","TaskTimeoutBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","MaximumServersBox","ApplicationBox","VersionBox","PortNumberBox","IsInterruptible")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "VraySpawnerSettings.ini" )

def PopulateDropDowns( *args ):
    global scriptDialog
    global portNumberInfoLabel
    global portNumberLabel
    global portNumberBox

    selectedPlugin = scriptDialog.GetValue( "ApplicationBox" )
    
    if selectedPlugin == "Select One":
        scriptDialog.SetEnabled( "VersionLabel", False )
        scriptDialog.SetEnabled( "VersionBox", False )
        scriptDialog.SetItems( "VersionBox", [ "Select an Application First... " ] )

        portNumberLabel.setVisible( False )
        portNumberBox.setVisible( False )
        scriptDialog.SetValue( "PortNumberInfoLabel", "" )
        portNumberInfoLabel.setVisible( False )
    
    elif selectedPlugin == "3ds Max":
        scriptDialog.SetEnabled( "VersionLabel", True )
        scriptDialog.SetEnabled( "VersionBox", True )
        scriptDialog.SetItems( "VersionBox", [ "Select One", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019" ] )

        portNumberLabel.setVisible( False )
        portNumberBox.setVisible( False )
        scriptDialog.SetValue( "PortNumberInfoLabel", "TCP Port: Not Available" )
        portNumberInfoLabel.setVisible( True )

    elif selectedPlugin == "3ds Max (RT)":
        scriptDialog.SetEnabled( "VersionLabel", True )
        scriptDialog.SetEnabled( "VersionBox", True )
        scriptDialog.SetItems( "VersionBox", [ "Select One", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019" ] )

        portNumberLabel.setVisible( True )
        portNumberBox.setVisible( True )
        scriptDialog.SetValue( "PortNumberInfoLabel", "Default TCP Port: 20206" )
        scriptDialog.SetValue( "PortNumberBox", 20206 )
        portNumberInfoLabel.setVisible( True )

    elif selectedPlugin == "Maya":
        scriptDialog.SetEnabled( "VersionLabel", True )
        scriptDialog.SetEnabled( "VersionBox", True )
        scriptDialog.SetItems( "VersionBox", [ "Select One", "2012", "2013", "2014", "2015", "2016", "2017", "2018" ] )

        portNumberLabel.setVisible( True )
        portNumberBox.setVisible( True )
        scriptDialog.SetValue( "PortNumberInfoLabel", "TCP Ports: Maya:20207 / Standalone:20207" )
        scriptDialog.SetValue( "PortNumberBox", 20207 )
        portNumberInfoLabel.setVisible( True )

    elif selectedPlugin == "Softimage":
        scriptDialog.SetEnabled( "VersionLabel", True )
        scriptDialog.SetEnabled( "VersionBox", True )
        scriptDialog.SetItems( "VersionBox", ["Select One","2012","2013","2014","2015"] )

        portNumberLabel.setVisible(True)
        portNumberBox.setVisible(True)
        scriptDialog.SetValue( "PortNumberInfoLabel", "TCP Ports: Softimage:20207 / Standalone:20204" )
        scriptDialog.SetValue( "PortNumberBox", 20207 )
        portNumberInfoLabel.setVisible(True)
    
    elif selectedPlugin == "Cinema 4D":
        scriptDialog.SetEnabled( "VersionLabel", True )
        scriptDialog.SetEnabled( "VersionBox", True )
        scriptDialog.SetItems( "VersionBox", ["Select One","12","13","14","15","16","17","18"] )

        portNumberLabel.setVisible(True)
        portNumberBox.setVisible(True)
        scriptDialog.SetValue( "PortNumberInfoLabel", "TCP Ports: Standalone:20207" )
        scriptDialog.SetValue( "PortNumberBox", 20207 )
        portNumberInfoLabel.setVisible(True)

    elif selectedPlugin == "Modo":
        scriptDialog.SetEnabled( "VersionLabel", False )
        scriptDialog.SetEnabled( "VersionBox", False )
        scriptDialog.SetItems( "VersionBox", ["N/A"] )

        portNumberLabel.setVisible(True)
        portNumberBox.setVisible(True)
        scriptDialog.SetValue( "PortNumberInfoLabel", "TCP Ports Modo:20207" )
        scriptDialog.SetValue( "PortNumberBox", 20207 )
        portNumberInfoLabel.setVisible(True)

    elif selectedPlugin == "Standalone":
        scriptDialog.SetEnabled( "VersionLabel", False )
        scriptDialog.SetEnabled( "VersionBox", False )
        scriptDialog.SetItems( "VersionBox", ["N/A"] )

        portNumberLabel.setVisible(True)
        portNumberBox.setVisible(True)
        scriptDialog.SetValue( "PortNumberInfoLabel", "TCP Ports: Standalone:20207" )
        scriptDialog.SetValue( "PortNumberBox", 20207 )
        portNumberInfoLabel.setVisible(True)
    
    else:
        scriptDialog.SetEnabled( "VersionLabel", False )
        scriptDialog.SetEnabled( "VersionBox", False )
        scriptDialog.SetItems( "VersionBox", ["N/A"] )

        portNumberLabel.setVisible(False)
        portNumberBox.setVisible(False)
        scriptDialog.SetValue( "PortNumberInfoLabel", "" )
        portNumberInfoLabel.setVisible(False)

def SubmitButtonPressed( *args ):
    global scriptDialog

    selectedApp = scriptDialog.GetValue( "ApplicationBox" )
    selectedVer = scriptDialog.GetValue( "VersionBox" )

    if selectedApp == "Select One":
       scriptDialog.ShowMessageBox( "Application must be selected!", "Invalid Submission" )
       return

    versionedApps = ["3ds Max","3ds Max (RT)","Maya","Softimage","Cinema 4D"]
    if selectedApp != "Select One" and (selectedApp in versionedApps):
        if selectedVer == "Select One":
            scriptDialog.ShowMessageBox( "Version must be selected!", "Invalid Submission" )
            return

    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "vray_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=VraySpawner" )
    writer.WriteLine( "Frames=0-%s\n" % (scriptDialog.GetValue( "MaximumServersBox" )-1) )
    
    jobName = scriptDialog.GetValue( "NameBox" )
    if (selectedApp in versionedApps):
        appNameVer = "V-Ray DBR Job (" + selectedApp + " " + selectedVer + ")"
    else:
        appNameVer = "V-Ray DBR Job (" + selectedApp + ")"
            
    if jobName != "":
        jobName = jobName + " - " + appNameVer
    else:
        jobName = appNameVer
            
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "vray_spawner_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
    app = scriptDialog.GetValue( "ApplicationBox" )
    if app == "3ds Max":
        app = "Max"
    elif app == "3ds Max (RT)":
        app = "MaxRT"
    elif app == "Cinema 4D":
        app = "Cinema4D"
    ver = scriptDialog.GetValue( "VersionBox" )
        
    if ver == "N/A":
        writer.WriteLine( "Version=%s\n" % app)
    else:
        writer.WriteLine( "Version={0}{1}\n".format(app,ver))

    if app == "MaxRT" or app == "Softimage" or app == "Maya" or app == "Cinema4D" or app == "Standalone":
        writer.WriteLine( "PortNumber=%s" % scriptDialog.GetValue( "PortNumberBox" ) )

    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )