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

DisplayOptions = ["Use Scene Settings", "Render Full Resolution", "Render using Proxies"]
ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = False

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global scriptDialog
    global settings
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Nuke Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Nuke' ) )
    
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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Nuke Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Nuke File", 1, 0, "The Nuke script to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "MultiFileBrowserControl", "", "Nuke Files (*.nk *.nk4 *.nuke *.nuke4);;All Files (*)", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 2, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 3, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Nuke Script File With Job", 3, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering.", colSpan=2 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 4, 0, "The version of Nuke to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "11.3", ("6.0","6.1","6.2","6.3","6.4","7.0","7.1","7.2","7.3","7.4","8.0","8.1","8.2","8.3","8.4","9.0","10.0","10.5","11.0","11.1","11.2","11.3"), 4, 1 )
    versionBox.ValueModified.connect(VersionChanged)
    scriptDialog.EndGrid()

    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Advanced Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Options", 0, 0, colSpan=5 )

    scriptDialog.AddControlToGrid( "WriteNodeLabel", "LabelControl", "Write Node(s) To Render", 1, 0, "A comma separated list of the write node(s) to render. This is optional and left blank, ALL write nodes will be rendered.", False )
    scriptDialog.AddControlToGrid( "WriteNodeBox", "TextControl", "", 1, 1, colSpan=4 )

    scriptDialog.AddControlToGrid( "ViewsLabel", "LabelControl", "View(s) To Render", 2, 0, "A comma separated list of the views to render. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "ViewsBox", "TextControl", "", 2, 1, colSpan=4 )

    scriptDialog.AddControlToGrid( "RameUseLabel", "LabelControl", "Max RAM Usage (MB)", 3, 0, "The maximum RAM usage (in MB) to be used for rendering. Set to 0 to not enforce a maximum amount of RAM.", False )
    scriptDialog.AddRangeControlToGrid( "RamUseBox", "RangeControl", 0, 0, 64000, 0, 1, 3, 1 )
    scriptDialog.AddControlToGrid( "StackSizeLabel", "LabelControl", "Min Stack Size (MB)", 3, 2, "The minimum stack size (in MB) to be used for rendering. Set to 0 to not enforce a minimum stack size.", False )
    scriptDialog.AddRangeControlToGrid( "StackSizeBox", "RangeControl", 0, 0, 64000, 0, 1, 3, 3 )

    scriptDialog.AddControlToGrid( "ThreadsLabel", "LabelControl", "Threads", 4, 0, "The number of threads to use for rendering. Set to 0 to have Nuke automatically determine the optimal thread count.", False )
    scriptDialog.AddRangeControlToGrid( "ThreadsBox", "RangeControl", 0, 0, 256, 0, 1, 4, 1 )
    scriptDialog.AddControlToGrid( "RenderModeLabel", "LabelControl", "Render mode", 4, 2, "The mode used for rendering the nuke file.", False )
    scriptDialog.AddComboControlToGrid( "ResolutionModeBox", "ComboControl", "Use Scene Settings", DisplayOptions, 4, 3, expand = False, colSpan=3 )
    
    useGpuBox = scriptDialog.AddSelectionControlToGrid( "UseGpuBox", "CheckBoxControl", False, "Use GPU For Rendering", 5, 0, "If Nuke should also use the GPU for rendering.", False, colSpan=2 )
    useGpuBox.ValueModified.connect( UseGPUChanged )
    scriptDialog.AddControlToGrid( "GpuOverrideLabel", "LabelControl", "GPU Override", 5, 2, "The GPU that Nuke should use if you are using the GPU for rendering. ( Used for Nuke 8 and higher. ).", False )
    scriptDialog.AddRangeControlToGrid( "GpuOverrideBox", "RangeControl", 0, 0, 15, 0, 1, 5, 3 )
    
    batchCheckBox = scriptDialog.AddSelectionControlToGrid( "UseBatchModeBox", "CheckBoxControl", True, "Use Batch Mode", 6, 0, "This uses the Nuke plugin's Batch Mode. It keeps the Nuke script loaded in memory between frames, which reduces the overhead of rendering the job.","", colSpan=2)
    batchCheckBox.ValueModified.connect(BatchModeChanged)
    scriptDialog.AddSelectionControlToGrid( "UseNukeXBox", "CheckBoxControl", False, "Render With NukeX", 6, 2, "If checked, NukeX will be used instead of just Nuke.", False, colSpan=2 )
    
    scriptDialog.AddSelectionControlToGrid( "EnforceRenderOrderBox", "CheckBoxControl", False, "Enforce Render Order", 7, 0, "Forces Nuke to obey the render order of Write nodes.", False, colSpan=2 )
    scriptDialog.AddSelectionControlToGrid( "ContinueOnErrorBox", "CheckBoxControl", False, "Continue On Error", 7, 2, "Enable to allow Nuke to continue rendering if it encounters an error.", False, colSpan=2 )

    scriptDialog.AddSelectionControlToGrid( "IsMovieBox", "CheckBoxControl", False, "Is Movie Render", 8, 0, "If checked, Deadline will render as a single chunk in Batch Mode, instead of rendering each frame separately. This is necessary for movie renders, otherwise only the last frame is written to the output file.", False, colSpan=2 )
    scriptDialog.AddSelectionControlToGrid( "ForceReloadPluginBox", "CheckBoxControl", False, "Reload Plugin Between Tasks", 8, 2, "If checked, Nuke will force all memory to be released before starting the next task, but this can increase the overhead time between tasks.", False, colSpan=2 )
    
    PerformProfilerBox = scriptDialog.AddSelectionControlToGrid( "PerformanceProfilerBox", "CheckBoxControl", False, "Use Performance Profiler", 9, 0, "If checked, Nuke will profile the performance of the Nuke script whilst rendering and create a *.xml file for later analysis.", False, colSpan=2 )
    PerformProfilerBox.ValueModified.connect(PerformProfilerChanged)
    
    scriptDialog.AddControlToGrid( "PerformanceProfilerDirLabel", "LabelControl", "XML Directory", 10, 0, "The directory on the network where the performance profile *.xml files will be saved.", False, colSpan=1 )
    scriptDialog.AddSelectionControlToGrid( "PerformanceProfilerDirBox", "FolderBrowserControl", "", "", 10, 1, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "Separator7", "SeparatorControl", "Script Job Options", 11, 0, colSpan=5 )
    scriptDialog.AddControlToGrid( "ScriptJobLabel", "LabelControl", "Script Jobs use Batch Mode and do not force a particular render.", 12, 0, colSpan=5 )
    scriptJobBox = scriptDialog.AddSelectionControlToGrid( "ScriptJobBox", "CheckBoxControl", False, "Submit A Nuke Script Job (Python)", 13, 0, "Enable this option to submit a custom Python script job. This Python script will be executed with the Nuke scene file that is specified.", colSpan=5 )
    scriptJobBox.ValueModified.connect(ScriptJobChanged)

    scriptDialog.AddControlToGrid( "ScriptFileLabel", "LabelControl", "Python Script File", 14, 0, "The Python script file to use.", False )
    scriptDialog.AddSelectionControlToGrid( "ScriptFileBox", "FileBrowserControl", "", "Python Script Files (*.py)", 14, 1, colSpan=4 )
    
    scriptDialog.EndGrid()

    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "NukeMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","VersionBox","ThreadsBox","RamUseBox", "SubmitSceneBox","WriteNodeBox","ViewsBox","UseNukeXBox","StackSizeBox","UseBatchModeBox","ContinueOnErrorBox","ResolutionModeBox","ForceReloadPluginBox","EnforceRenderOrderBox","UseGpuBox", "GpuOverrideBox", "PerformanceProfilerBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
        
    UseGPUChanged(None)
    BatchModeChanged(None)
    VersionChanged(None)
    PerformProfilerChanged(None)
    ScriptJobChanged( None )
    
    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "NukeSettings.ini" )

def UseGPUChanged( *args ):
    global scriptDialog
    
    version = float( scriptDialog.GetValue( "VersionBox" ) )
    enabled = scriptDialog.GetValue( "UseGpuBox" ) and version >= 8
    
    scriptDialog.SetEnabled( "GpuOverrideLabel", enabled )
    scriptDialog.SetEnabled( "GpuOverrideBox", enabled )
    
def BatchModeChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "IsMovieBox", scriptDialog.GetValue( "UseBatchModeBox" ) )

def VersionChanged( *args ):
    global scriptDialog
    version = float( scriptDialog.GetValue( "VersionBox" ) )
            
    scriptDialog.SetEnabled( "PerformanceProfilerBox", ( version >= 9.0 ) )
    PerformProfilerChanged()

    scriptDialog.SetEnabled( "UseGpuBox", (version >= 7.0) )
    enabled = scriptDialog.GetValue( "UseGpuBox" ) and version >= 8
    scriptDialog.SetEnabled( "GpuOverrideLabel", enabled )
    scriptDialog.SetEnabled( "GpuOverrideBox", enabled )

def PerformProfilerChanged( *args ):
    global scriptDialog
    version = float( scriptDialog.GetValue( "VersionBox" ) )
    ppEnabled = bool( scriptDialog.GetValue( "PerformanceProfilerBox" ) )
    scriptDialog.SetEnabled( "PerformanceProfilerDirLabel", ( version >= 9.0 and ppEnabled ) )
    scriptDialog.SetEnabled( "PerformanceProfilerDirBox", ( version >= 9.0 and ppEnabled ) )

def ScriptJobChanged(*args):
    global scriptDialog
    
    enabled = scriptDialog.GetValue( "ScriptJobBox" )
    scriptDialog.SetEnabled( "ScriptFileLabel", enabled )
    scriptDialog.SetEnabled( "ScriptFileBox", enabled )
        
def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    
    version = float( scriptDialog.GetValue( "VersionBox" ) )
    
    ScriptJob = scriptDialog.GetValue( "ScriptJobBox" )
    ScriptFile = scriptDialog.GetValue( "ScriptFileBox" )
    # Check the Nuke files.
    sceneFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "SceneBox" ), False )
    if( len( sceneFiles ) == 0 ):
        scriptDialog.ShowMessageBox( "No Nuke file specified", "Error" )
        return
    
    for sceneFile in sceneFiles:
        if( not File.Exists( sceneFile ) ):
            scriptDialog.ShowMessageBox( "Nuke file %s does not exist" % sceneFile, "Error" )
            return
        # If the submit scene box is checked check if they are local, if they are warn the user
        elif( not bool( scriptDialog.GetValue("SubmitSceneBox") ) and PathUtils.IsPathLocal( sceneFile ) ):
            result = scriptDialog.ShowMessageBox( "The Nuke file " + sceneFile + " is local.\n\nAre you sure you want to continue?", "Warning", ("Yes","No") )
            if( result == "No" ):
                return
        else:
            fileContents = File.ReadAllText( sceneFile )
            if fileContents.find( "proxy true" ) != -1 and ( not scriptDialog.GetValue( "ResolutionModeBox" ) == "Render using Proxies" ):
                result = scriptDialog.ShowMessageBox( "The Nuke file " + sceneFile + " has proxy mode enabled, which may cause problems when rendering through Deadline.\n\nDo you wish to continue?", "Warning", ("Yes","No") )
                if( result == "No" ):
                    return
    
    if ScriptJob:
        if( not File.Exists( ScriptFile ) ):
            scriptDialog.ShowMessageBox( "Script file %s does not exist" % ScriptFile, "Error" )
            return
        elif( PathUtils.IsPathLocal( ScriptFile ) ):
            result = scriptDialog.ShowMessageBox( "The Script file " + ScriptFile + " is local.\n\nAre you sure you want to continue?", "Warning", ("Yes","No") )
            if( result == "No" ):
                return
                
    # Check valid Performance Profiler Dir has been defined if Performance Profiler is enabled (Nuke v9.0 or later)
    if version >= 9.0:
        if bool(scriptDialog.GetValue( "PerformanceProfilerBox" ) ):

            PPDir = scriptDialog.GetValue( "PerformanceProfilerDirBox" )
            if PPDir == "":
                scriptDialog.ShowMessageBox( "Performance Profiler is Enabled, but Performance Profiler Directory is empty!", "Error" )
                return

            if( not Directory.Exists( PPDir ) ):
                scriptDialog.ShowMessageBox( "Performance Profiler is Enabled, but Performance Profiler Directory does not exist!", "Error" )
                return

            if( PathUtils.IsPathLocal( PPDir ) ):
                result = scriptDialog.ShowMessageBox( "Performance Profiler Directory is on a local drive!\n\nThe Deadline job will FAIL! Are you sure you want to continue?", "Warning", ("Yes","No") )
                if(result == "No" ):
                    return

    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return
    
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( ):
        return
    
    successes = 0
    failures = 0
        
    # Submit each scene file separately.
    for sceneFile in sceneFiles:
        jobName = scriptDialog.GetValue( "NameBox" )
        if len(sceneFiles) > 1:
            jobName = jobName + " [" + Path.GetFileName( sceneFile ) + "]"
        
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "nuke_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Nuke" )
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
        writer.WriteLine( "ForceReloadPlugin=%s" % scriptDialog.GetValue( "ForceReloadPluginBox" ) )
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
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        
        #Shotgun
        extraKVPIndex = 0
        groupBatch = False
        
        if integration_dialog.IntegrationProcessingRequested():
            extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()
       
        if groupBatch:
            writer.WriteLine( "BatchName=%s\n" % (jobName ) ) 
        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "nuke_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
        if( not bool(scriptDialog.GetValue( "SubmitSceneBox" )) ):
            writer.WriteLine( "SceneFile=%s" % sceneFile )
        
        
        BatchMode = ( scriptDialog.GetValue( "UseBatchModeBox" ) or ScriptJob )
        
        writer.WriteLine( "Version=%s" % version )
        writer.WriteLine( "Threads=%s" % scriptDialog.GetValue( "ThreadsBox" ) )
        writer.WriteLine( "RamUse=%s" % scriptDialog.GetValue( "RamUseBox" ) )
        writer.WriteLine( "NukeX=%s" % scriptDialog.GetValue( "UseNukeXBox" ) )
        writer.WriteLine( "BatchMode=%s" % BatchMode )
        writer.WriteLine( "BatchModeIsMovie=%s" % scriptDialog.GetValue( "IsMovieBox" ) )
        writer.WriteLine( "ContinueOnError=%s" % scriptDialog.GetValue( "ContinueOnErrorBox" ) )
        writer.WriteLine( "RenderMode=%s" % scriptDialog.GetValue( "ResolutionModeBox" ) )
        writer.WriteLine( "EnforceRenderOrder=%s" % scriptDialog.GetValue( "EnforceRenderOrderBox" ) )
        writer.WriteLine( "Views=%s" % scriptDialog.GetValue( "ViewsBox" ) )
        writer.WriteLine( "WriteNode=%s" % scriptDialog.GetValue( "WriteNodeBox" ) )
        writer.WriteLine( "StackSize=%s" % scriptDialog.GetValue( "StackSizeBox" ) )
       
        if version >= 7.0:
            writer.WriteLine( "UseGpu=%s" % scriptDialog.GetValue( "UseGpuBox" ) )
        
        if version >= 8.0:
            writer.WriteLine( "GpuOverride=%s" % scriptDialog.GetValue( "GpuOverrideBox" ) )
        
        if version >= 9.0:
            writer.WriteLine( "PerformanceProfiler=%s" % scriptDialog.GetValue( "PerformanceProfilerBox" ) )
            writer.WriteLine( "PerformanceProfilerDir=%s" % scriptDialog.GetValue( "PerformanceProfilerDirBox" ) )
        
        writer.WriteLine( "ScriptJob=%s" % ScriptJob )
        writer.WriteLine( "ScriptFilename=%s" % ScriptFile )
        
        writer.Close()
        
        # Setup the command line arguments.
        arguments = StringCollection()
        
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        if scriptDialog.GetValue( "SubmitSceneBox" ):
            arguments.Add( sceneFile )
        
        if( len( sceneFiles ) == 1 ):
            results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
            scriptDialog.ShowMessageBox( results, "Submission Results" )
        else:
            # Now submit the job.
            exitCode = ClientUtils.ExecuteCommand( arguments )
            if( exitCode == 0 ):
                successes = successes + 1
            else:
                failures = failures + 1
        
    if( len( sceneFiles ) > 1 ):
        scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )
