import os

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Aria Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Aria' ) )
    
    scriptDialog.AddTabControl( "Tabs", 0, 0 )
    
    scriptDialog.AddTabPage( "Job Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )
    
    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
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
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job." )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "" )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Aria Options", 0, 0, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Aria File", 1, 0, "The project file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Aria Files (*.sfx)", 1, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "VersionLabel","LabelControl","Aria Version", 2, 0, "The version of Aria to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox","ComboControl","6",("5","6"), 2, 1 )
    versionBox.ValueModified.connect( VersionChanged )
    
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox","CheckBoxControl",False,"Submit Aria File",2, 2, "If this option is enabled, the project file will be submitted with the job, and then copied locally to the slave machine during rendering." )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 2, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 3, 3 )

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage( "Advanced Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Render Overrides", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "SessionLabel", "LabelControl", "Session", 1, 0, "Make the specified session active in the project. If empty the currently selected session will be used to render.", False )
    scriptDialog.AddControlToGrid( "SessionBox", "TextControl", "", 1, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "NodeLabel", "LabelControl", "Node", 2, 0, "The specified node in the active session to render. If empty the currently selected node will be used to render.", False )
    scriptDialog.AddControlToGrid( "NodeBox", "TextControl", "", 2, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "OutputDirectoryLabel", "LabelControl", "Output Directory", 3, 0, "The output directory to use. If empty the output directory defined in the session will be used.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputDirectoryBox", "FolderBrowserControl", "", "", 3, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "OutputFilenameLabel", "LabelControl", "Output Filename", 4, 0, "The output prefix to use. If empty the output prefix defined in the session will be used.", False )
    scriptDialog.AddControlToGrid( "OutputFilenameBox", "TextControl", "", 4, 1, colSpan=3 )

    overrideFormatBox = scriptDialog.AddSelectionControlToGrid( "FormatCheck", "CheckBoxControl", False, "Override Format", 5, 0, "Override the image file format to be rendered." )
    overrideFormatBox.ValueModified.connect( OverrideFormatChanged )
    scriptDialog.AddComboControlToGrid( "FormatBox","ComboControl","OpenEXR",( "Cineon","DPX","IFF","JPEG","OpenEXR","PNG","SGI","TIFF","Targa" ), 5, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ResolutionLabel","LabelControl","Resolution", 6, 0, "The resolution to render with.", False )
    scriptDialog.AddComboControlToGrid( "ResolutionBox", "ComboControl", "full",( "full","half","third","quarter" ), 6, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "FieldsLabel","LabelControl","Fields", 7, 0, "Various options to handle fields.", False )
    fields = scriptDialog.AddComboControlToGrid( "FieldsBox", "ComboControl", "none",( "none","interlace","aa","bb","bc","cd","dd" ), 7, 1, colSpan=3 )
    fields.ValueModified.connect( FieldsChanged )

    scriptDialog.AddControlToGrid( "DominanceLabel","LabelControl","Dominance", 8, 0, "Various options to handle fields.", False )
    scriptDialog.AddComboControlToGrid( "DominanceBox", "ComboControl", "even",( "even","odd" ), 8, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "AdditionalOptionsLabel", "LabelControl", "Additional Options", 9, 0, "Any additional options to use while rendering.", False )
    scriptDialog.AddControlToGrid( "AdditionalOptionsBox", "TextControl", "", 9, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "Script Options", 10, 0, colSpan=4 )

    runScriptBox = scriptDialog.AddSelectionControlToGrid( "RunScript", "CheckBoxControl", False, "Run Script", 11, 0, "Run Python script after loading the project." )
    runScriptBox.ValueModified.connect( RunScriptChanged )
    scriptDialog.AddSelectionControlToGrid( "DisableRender", "CheckBoxControl", False, "Disable Rendering", 11, 1, "If this option is enabled, rendering will be disabled, which might be useful for certain Python script jobs." )
    scriptDialog.AddSelectionControlToGrid( "SubmitScriptBox", "CheckBoxControl", False, "Submit Python Script File", 11, 2, "If this option is enabled, the Python script file will be submitted with the job to the Deadline Repository." )
    
    scriptDialog.AddControlToGrid( "ScriptFileLabel", "LabelControl", "Python Script File", 12, 0, "The Python script file to be executed.", False )
    scriptDialog.AddSelectionControlToGrid( "ScriptFileBox", "FileBrowserControl", "", "Python Files (*.py)", 12, 1, colSpan=3 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","VersionBox","SubmitSceneBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    VersionChanged( None )
    OverrideFormatChanged( None )
    FieldsChanged( None )
    RunScriptChanged( None )
    
    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "AriaSettings.ini" )

def OverrideFormatChanged( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "FormatCheck" ) and scriptDialog.GetEnabled( "FormatCheck" )
    scriptDialog.SetEnabled( "FormatBox", enabled )

def FieldsChanged( *args ):
    global scriptDialog
    selectedField = scriptDialog.GetValue( "FieldsBox" )
    enabled = ( selectedField != "none" )
    scriptDialog.SetEnabled( "DominanceLabel", enabled )
    scriptDialog.SetEnabled( "DominanceBox", enabled )

def RunScriptChanged( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "RunScript" )
    scriptDialog.SetEnabled( "DisableRender", enabled )
    scriptDialog.SetEnabled( "ScriptFileLabel", enabled )
    scriptDialog.SetEnabled( "ScriptFileBox", enabled )
    scriptDialog.SetEnabled( "SubmitScriptBox", enabled )
    
def VersionChanged( *args ):
    global scriptDialog
    
    version = int( scriptDialog.GetValue( "VersionBox" ) )
    
    preSix = version < 6
    
    scriptDialog.SetEnabled( "OutputDirectoryLabel", preSix )
    scriptDialog.SetEnabled( "OutputDirectoryBox", preSix )
    scriptDialog.SetEnabled( "OutputFilenameLabel", preSix )
    scriptDialog.SetEnabled( "OutputFilenameBox", preSix )
    scriptDialog.SetEnabled( "FormatCheck", preSix )
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    
    paddedNumberRegex = Regex( "\\$F([0-9]+)" )
    
    # Check if Aria files exist.
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    sceneFileName = Path.GetFileName( sceneFile )

    if not os.path.exists( sceneFile ):
        scriptDialog.ShowMessageBox( "Aria file: %s does not exist" % sceneFile, "Error" )
        return
    elif sceneFileName == "project.sfx":
        scriptDialog.ShowMessageBox( "Please ensure you select the top-level Aria *.sfx file and NOT the underlying 'project.sfx' file", "Error" )
        return
    elif (PathUtils.IsPathLocal( sceneFile ) and not scriptDialog.GetValue( "SubmitSceneBox" ) ):
        result = scriptDialog.ShowMessageBox( "Aria file: " + sceneFile + " is local.  Are you sure you want to continue?", "Warning",("Yes","No") )
        if( result=="No" ):
            return

    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return

    # Check script
    runScript = scriptDialog.GetValue( "RunScript" )
    disableRender = scriptDialog.GetValue( "DisableRender" )
    scriptFile = (scriptDialog.GetValue( "ScriptFileBox" )).strip()
    submitScript = scriptDialog.GetValue( "SubmitScriptBox" )

    if( runScript ):
        if not os.path.exists( scriptFile ):
            scriptDialog.ShowMessageBox( "Script file %s does not exist" % scriptFile, "Error" )
            return
        elif ( PathUtils.IsPathLocal( scriptFile ) and not submitScript ):
            result = scriptDialog.ShowMessageBox( "Python script file: " + scriptFile + " is local.  Are you sure you want to continue?\n(Hint: Submit Python script File with job?)", "Warning",("Yes","No") )
            if( result=="No" ):
                return

    jobName = scriptDialog.GetValue( "NameBox" ) + ( " [%s]" % sceneFileName )
    
    if runScript and disableRender:
        jobName = jobName + " [Script Job]"

    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "Aria_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Aria" )
    writer.WriteLine( "Name=%s" % jobName )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
    writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
    writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "ConcurrentTasksBox" ) )
    writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
        
    writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
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
    writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox") )

    outputDirectory = scriptDialog.GetValue( "OutputDirectoryBox" )
    if not outputDirectory == "":
        writer.WriteLine( "OutputDirectory0=%s" % outputDirectory )

    writer.Close()
        
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "Aria_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

    dataFile = Path.Combine( sceneFile, "project.sfx" )

    if(not scriptDialog.GetValue( "SubmitSceneBox" ) ):
        writer.WriteLine( "SceneFile=%s" % dataFile )
    
    writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ))
    writer.WriteLine( "Session=%s" % scriptDialog.GetValue( "SessionBox" ) )
    writer.WriteLine( "Node=%s" % scriptDialog.GetValue( "NodeBox" ) )
    writer.WriteLine( "OutputDirectory=%s" % outputDirectory )
    writer.WriteLine( "OutputFilename=%s" % scriptDialog.GetValue( "OutputFilenameBox" ) )
    
    if scriptDialog.GetValue( "FormatCheck" ):
        writer.WriteLine( "OutputFormat=%s" % scriptDialog.GetValue( "FormatBox") )
    else:
        writer.WriteLine( "OutputFormat=" )
    
    writer.WriteLine( "AdditionalOptions=%s" % scriptDialog.GetValue( "AdditionalOptionsBox" ) )

    writer.WriteLine( "Resolution=%s" % scriptDialog.GetValue( "ResolutionBox" ) )
    writer.WriteLine( "Fields=%s" % scriptDialog.GetValue( "FieldsBox" ) )
    writer.WriteLine( "Dominance=%s" % scriptDialog.GetValue( "DominanceBox" ) )

    writer.WriteLine( "RunScript=%s" % runScript )
    writer.WriteLine( "DisableRender=%s" % disableRender )
    
    if submitScript:
        writer.WriteLine( "ScriptFile=%s" % Path.GetFileName( scriptFile ) )
    else:
        writer.WriteLine( "ScriptFile=%s" % scriptFile )

    writer.Close()
    
    arguments = StringCollection()

    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( dataFile )
    
    if runScript and submitScript:
        arguments.Add( scriptFile )
            
    jobResult = ClientUtils.ExecuteCommandAndGetOutput( arguments )

    scriptDialog.ShowMessageBox( jobResult, "Submission Results" )
    