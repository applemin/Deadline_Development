from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *
from Deadline.Plugins import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog

    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Katana To Deadline" )
    scriptDialog.SetIcon( RepositoryUtils.GetRepositoryFilePath( "plugins/Katana/Katana.ico", True ) )

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "JobOptionsSeparator", "SeparatorControl", "Job Description", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1, colSpan=2 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 5, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 6, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 6, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 7, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 8, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 9, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 9, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 9, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()

    # ACTUAL KATANA SETTINGS
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Katana Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "FileLabel", "LabelControl", "Katana Scene File", 1, 0, "The file path to the .katana file to use.", False )
    scriptDialog.AddSelectionControlToGrid( "KatanaFileBox", "FileBrowserControl", "", "Katana Files (*.katana)", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "WorkingDirLabel", "LabelControl", "Working Dir (Optional)", 2, 0, "The working directory used during Katana rendering. This is required if your Katana project file contains relative paths.", False )
    scriptDialog.AddSelectionControlToGrid( "WorkingDirBox", "FolderBrowserControl", "", "", 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "RangeLabel", "LabelControl", "Frame List", 3, 0, "A comma-separated collection of single frames or frame ranges. ex: 1-2,3,4-6." )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Katana Scene File", 3, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering.", colSpan=2 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 4, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 4, 2, "The version of Katana to use for this render job.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "3", ("2","3"), 4, 3 )

    scriptDialog.AddControlToGrid( "RenderNodeLabel", "LabelControl", "Render Node (optional)", 5, 0, "The Katana scene node to render. This can be left blank to render the default render node.", False )
    scriptDialog.AddControlToGrid( "RenderNodeBox", "TextControl", "", 5, 1, colSpan=3 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid() # Submit and Close buttons
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 1 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 2, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 3, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    # sticky settings
    settings = ( "CategoryBox","DepartmentBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","LimitGroupBox","OnJobCompleteBox","MachineListBox","SubmitSuspendedBox","IsBlacklistBox","KatanaFileBox","WorkingDirBox","FramesBox","ChunkSizeBox","SubmitSceneBox","RenderNodeBox","VersionBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    scriptDialog.SetSize( 400, 100 )
    scriptDialog.ShowDialog( True )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "KatanaSettings.ini" )

def SubmitButtonPressed(*args):
    global scriptDialog

    # Katana (input) file
    katanaFile = scriptDialog.GetValue("KatanaFileBox").strip()

    if(len(katanaFile)==0):
        scriptDialog.ShowMessageBox("No Katana file specified","Error")
        return

    if not File.Exists(katanaFile):
        scriptDialog.ShowMessageBox( "Katana file %s does not exist" % katanaFile, "Error" )
        return
        
    if( PathUtils.IsPathLocal( katanaFile ) ):
        result = scriptDialog.ShowMessageBox( "The Katana file " + katanaFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    if( not katanaFile.endswith(".katana") ):
        result = scriptDialog.ShowMessageBox( "The Katana file " + katanaFile + " is not a supported format. Do you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return

    workingDir = scriptDialog.GetValue( "WorkingDirBox" ).strip()
    if workingDir != "":
        if( not Directory.Exists( workingDir ) ):
            scriptDialog.ShowMessageBox( "Working directory %s does not exist" % workingDir, "Error" )
            return
        elif( PathUtils.IsPathLocal( workingDir ) ):
            result = scriptDialog.ShowMessageBox( "Working directory " + workingDir + " is local, are you sure you want to continue", "Warning", ("Yes","No") )
            if( result == "No" ):
                return

    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return

    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "katana_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Katana" )
    writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "MachineLimit=1" )
    writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
    
    if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )

    writer.WriteLine( "Frames=%s" % frames )
    writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
    writer.Close()

    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "katana_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

    if( not bool(scriptDialog.GetValue( "SubmitSceneBox" )) ):
        writer.WriteLine( "KatanaFile=%s" % katanaFile )

    writer.WriteLine( "WorkingDirectory=%s" % workingDir )
    writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )

    renderNode = scriptDialog.GetValue( "RenderNodeBox" )
    if len( renderNode ) > 0:
        writer.WriteLine( "RenderNode=%s" % renderNode )

    writer.Close()

    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )

    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( katanaFile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )