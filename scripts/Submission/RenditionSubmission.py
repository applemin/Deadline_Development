from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

# For Integration UI
import imp
import os
imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = True

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Rendition Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Rendition' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)

    scriptDialog.AddTabPage("Job Options")
    
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
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

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

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering. ", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render. " )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Rendition Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Input MI File", 1, 0, "This needs to be on a network location, since Rendition often saves the output file(s) relative to the input MI file location.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Mental Image Files (*.mi *.mi2);;All Files (*)", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid("OutputLabel","LabelControl","Output File (Optional)", 2, 0, "Optionally override the output file.", False)
    outputBox = scriptDialog.AddSelectionControlToGrid("OutputBox","FileSaverControl","", "Bitmap (*.bmp);;EXR (*.exr);;GIF (*.gif);;IFF (*.iff);;JPG (*.jpg);;PNG (*.png);;Targa (*.tga);;TIFF (*.tif);;All Files (*)", 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "1", 3, 1 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 2, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 100000, 0, 1, 3, 3 )

    scriptDialog.AddControlToGrid("BuildLabel","LabelControl","Build to Force", 4, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid("BuildBox","ComboControl","None",("None","32bit","64bit"), 4, 1 )
    scriptDialog.AddSelectionControlToGrid("SkipBox","CheckBoxControl",True,"Skip Existing Frames", 4, 2, "Enable to skip existing frames." )

    scriptDialog.AddControlToGrid("CommandLabel","LabelControl","Command Line Args", 5, 0, "Additional command line arguments to pass to Rendition during rendering. ", False )
    scriptDialog.AddControlToGrid("CommandBox","TextControl","", 5, 1, colSpan=3)
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "RenditionMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","OutputBox","FramesBox","ChunkSizeBox","SkipBox","BuildBox","CommandBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "RenditionSettings.ini" )
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    
    # Check if mi files exist.
    sceneFile = scriptDialog.GetValue( "SceneBox" ).strip()
    if not File.Exists( sceneFile ):
        scriptDialog.ShowMessageBox( "MI file %s does not exist" % sceneFile, "Error" )
        return
    elif PathUtils.IsPathLocal( sceneFile ):
        result = scriptDialog.ShowMessageBox( "MI file " + sceneFile + " is local. Are you sure you want to continue?", "Warning", ("Yes","No") )
        if result == "No":
            return
    
    # Check the output file.
    outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
    if outputFile != "":
        if not Directory.Exists( Path.GetDirectoryName( outputFile ) ):
            scriptDialog.ShowMessageBox( "The directory of the output file does not exist:\n" + Path.GetDirectoryName( outputFile ), "Error" )
            return
        elif PathUtils.IsPathLocal( outputFile ):
            result = scriptDialog.ShowMessageBox( "Output file " + outputFile + " is local. Are you sure you want to continue?", "Warning", ("Yes","No") )
            if result == "No":
                return

    # Check if Integration options are valid.
    if not integration_dialog.CheckIntegrationSanity( outputFile ):
        return
    
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if not FrameUtils.FrameRangeValid( frames ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid." % frames, "Error" )
        return
    
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "rendition_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Rendition" )
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
    
    if outputFile != "":
        directory = Path.GetDirectoryName( outputFile )
        filename = Path.GetFileNameWithoutExtension( outputFile )
        extension = Path.GetExtension( outputFile )
        
        padding = "####"
        writer.WriteLine( "OutputFilename0=%s" % Path.Combine( directory, filename + padding + extension ) )
    else:
        writer.WriteLine( "OutputDirectory0=%s" % Path.GetDirectoryName( sceneFile ) )
    
    writer.WriteLine( "Frames=%s" % frames )
    writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
    
    # Integration
    extraKVPIndex = 0
    groupBatch = False

    if integration_dialog.IntegrationProcessingRequested():
        extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
        groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

    if groupBatch:
        writer.WriteLine( "BatchName=%s\n" % ( jobName ) ) 
    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "rendition_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "SceneFile=" + sceneFile.replace( "\\", "/" ) )
    writer.WriteLine( "OutputFile=" + outputFile.replace( "\\", "/" ) )
    writer.WriteLine( "Build=" + scriptDialog.GetValue( "BuildBox" ) )
    writer.WriteLine( "Skip=" + str(scriptDialog.GetValue( "SkipBox" )) )
    writer.WriteLine( "CommandLineOptions=" + str(scriptDialog.GetValue( "CommandBox" )).strip() )
    
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
