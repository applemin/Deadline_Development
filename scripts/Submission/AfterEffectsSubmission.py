import imp # For Integration UI
from collections import OrderedDict

from Deadline.Scripting import ClientUtils, FrameUtils, PathUtils, RepositoryUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

from System.IO import Directory, File, Path, StreamWriter
from System.Text import Encoding

imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
integration_dialog = None

ProjectManagementOptions = ["Shotgun","FTrack","NIM"]
DraftRequested = True

AFTER_EFFECTS_VERSIONS = OrderedDict([
    ("CS3", 8.0),
    ("CS4", 9.0),
    ("CS5", 10.0),
    ("CS5.5", 10.5),
    ("CS6", 11.0),
    ("CC", 12.0),
    ("CC2014", 13.0),
    ("CC2015", 13.5),
    ("CC2017", 14.0),
    ("CC2018", 15.0),
    ("CC2019", 16.0),
])

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global AFTER_EFFECTS_VERSIONS
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()

    scriptDialog.SetTitle("Submit After Effects Job To Deadline")
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'AfterEffects' ) )

    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 0, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 0, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 1, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 1, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 2, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 2, 1 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 0, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 0, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 1, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 1, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 2, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 2, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 3, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 3, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 4, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 4, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 5, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 5, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 6, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 6, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 7, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limit Groups", 8, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 9, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 10, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 10, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 10, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "After Effects Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "After Effects File", 0, 0, "The project file to render.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "After Effects Files (*.aep *.aepx)", 0, 1, colSpan=2 )

    scriptDialog.AddControlToGrid("CompLabel", "LabelControl", "Composition", 1, 0, "The composition in the project file to render. If left blank, the entire render queue will be rendered as a single task.", False)
    
    compBox = scriptDialog.AddControlToGrid("CompBox", "TextControl", "", 1, 1, colSpan=2 )
    compBox.ValueModified.connect(CompChanged)
    
    scriptDialog.AddControlToGrid("OutputLabel","LabelControl","Output (optional)", 2, 0, "Override the output path for the composition. This is optional, and can be left blank.", False)
    scriptDialog.AddSelectionControlToGrid("OutputBox","FileSaverControl","", "All Files (*)",2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 4, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "MultiProcess", "CheckBoxControl", False, "Use Multi-Process Rendering", 4, 2, "Enable to use multiple processes to render multiple frames simultaneously." )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 5, 0 , "The version of After Effects to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", next(reversed(AFTER_EFFECTS_VERSIONS)), AFTER_EFFECTS_VERSIONS.keys(), 5, 1 )
    versionBox.ValueModified.connect(VersionChanged)

    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Project File", 5, 2, "If this option is enabled, the project file you want to render will be submitted with the job, and then copied locally to the slave machine during rendering." )
    scriptDialog.EndGrid()
    
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage( "Advanced Options" )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator9", "SeparatorControl", "Multi-Machine Rendering", 0, 0, colSpan=4 )
    scriptDialog.AddControlToGrid( "MultiMachineLabel", "LabelControl", "Note that \"Skip existing frames\" must be enabled for each comp", 1, 0, colSpan=3)
    
    multiMachineCheckBox = scriptDialog.AddSelectionControlToGrid("MultiMachineBox", "CheckBoxControl", False, "Enable Multi-Machine Rendering", 2, 0, "This mode submits a special job where each task represents the full frame range. The slaves will all work on the same frame range, but because 'Skip existing frames' is enabled for the comps, they will skip frames that other slaves are already rendering.")
    multiMachineCheckBox.ValueModified.connect(MultiMachineChanged)

    scriptDialog.AddControlToGrid( "MultiMachineTasksLabel", "LabelControl", "Number Of Machines", 3, 0, "The number of slaves that can work on this job at the same time. Each slave gets a task, which represents the full frame range, and they will work together until all frames are complete.", False )
    scriptDialog.AddRangeControlToGrid("MultiMachineTasksBox", "RangeControl", 10, 1, 9999, 0, 1, 3, 1 )
    
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "Memory Management Options", 4, 0, colSpan=4 )

    memManageCheckBox = scriptDialog.AddSelectionControlToGrid("MemoryManagement", "CheckBoxControl", False, "Enable Memory Mangement", 5, 0, "Whether or not to use the memory management options. ", colSpan=3)
    memManageCheckBox.ValueModified.connect(MemoryManageChanged)

    scriptDialog.AddControlToGrid( "ImageCacheLabel", "LabelControl", "Image Cache %", 6, 0, "The maximum amount of memory after effects will use to cache frames. ", False )
    scriptDialog.AddRangeControlToGrid("ImageCachePercentage", "RangeControl", 100, 20, 100, 0, 1, 6, 1 )

    scriptDialog.AddControlToGrid( "MaxMemoryLabel", "LabelControl", "Max Memory %", 7, 0, "The maximum amount of memory After Effects can use overall. ", False )
    scriptDialog.AddRangeControlToGrid("MaxMemoryPercentage", "RangeControl", 100, 20, 100, 0, 1, 7, 1)
    
    scriptDialog.AddControlToGrid( "Separator6", "SeparatorControl", "Miscellaneous Options", 8, 0, colSpan=4 )
    scriptDialog.AddSelectionControlToGrid( "MissingLayers", "CheckBoxControl", False, "Ignore Missing Layer Dependencies", 9, 0, "If enabled, Deadline will ignore errors due to missing layer dependencies. ", colSpan=3)
    scriptDialog.AddSelectionControlToGrid( "MissingEffects", "CheckBoxControl", False, "Ignore Missing Effect References", 10, 0, "If enabled, Deadline will ignore errors due to missing effect references. ", colSpan=3)
    scriptDialog.AddSelectionControlToGrid( "MissingFootage", "CheckBoxControl", False, "Continue On Missing Footage", 11, 0, "If enabled, rendering will not stop when missing footage is detected (After Effects CS4 and later). ", colSpan=3)
    scriptDialog.AddSelectionControlToGrid( "FailOnWarnings", "CheckBoxControl", False, "Fail On Warning Messages", 12, 0, "If enabled, Deadline will fail the job whenever After Effects prints out a warning message. ", colSpan=3)
    scriptDialog.AddSelectionControlToGrid( "LocalRendering", "CheckBoxControl", False, "Enable Local Rendering", 13, 0, "If enabled, the frames will be rendered locally, and then copied to their final network location. This requires the Output to be overwritten.", colSpan=3)

    overrideButton = scriptDialog.AddSelectionControlToGrid( "OverrideFailOnExistingAEProcess", "CheckBoxControl", False, "Override Fail On Existing AE Process", 14, 0, "If enabled, the Fail On Existing AE Process Setting will be taken into account.", colSpan=2)
    overrideButton.ValueModified.connect(OverrideButtonPressed)
    scriptDialog.AddSelectionControlToGrid( "FailOnExistingAEProcess", "CheckBoxControl", False, "Fail On Existing AE Process", 14, 2, "If enabled, Deadline will fail the job whilst any After Effects instance is running.")

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "AfterEffectsMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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
    
    #might need to add some settings here for the memory management options
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","VersionBox","ArgsBox","MemoryManagement","ImageCachePercentage", "MaxMemoryPercentage", "CompBox", "MultiProcess", "SubmitSceneBox", "OutputBox", "MissingLayers", "MissingEffects", "MissingFootage", "FailOnWarnings", "LocalRendering", "OverrideFailOnExistingAEProcess", "FailOnExistingAEProcess")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    CompChanged(None)
    VersionChanged(None)
    MultiMachineChanged(None)
    OverrideButtonPressed(None)
    MemoryManageChanged(None)
    
    #check if memory management is enabled
    if(not bool(scriptDialog.GetValue("MemoryManagement"))):
        scriptDialog.SetEnabled("ImageCachePercentage", False)
        scriptDialog.SetEnabled("MaxMemoryPercentage", False)
    
    scriptDialog.ShowDialog(False)
    
def GetVersionNumber():
    """
    Grabs the currently selected After Effects version number from the associated version string
    :return: a float representing the currently selected After Effects version
    """
    global AFTER_EFFECTS_VERSIONS, scriptDialog
    
    versionStr = scriptDialog.GetValue( "VersionBox" )
    return AFTER_EFFECTS_VERSIONS[ versionStr ]

def IsMovieFormat( extension ):
    cleanExtension = extension.lstrip( '.' )
    if len( cleanExtension ) > 0:
        cleanExtension = cleanExtension.lower()
        # These formats are all the ones included in DFusion, as well
        # as all the formats in AE that don't contain [#####].
        if cleanExtension == "vdr" or cleanExtension == "wav" or cleanExtension == "dvs" or cleanExtension == "fb"  or cleanExtension == "omf" or cleanExtension == "omfi"or cleanExtension == "stm" or cleanExtension == "tar" or cleanExtension == "vpr" or cleanExtension == "gif" or cleanExtension == "img" or cleanExtension == "flc" or cleanExtension == "flm" or cleanExtension == "mp3" or cleanExtension == "mov" or cleanExtension == "rm"  or cleanExtension == "avi" or cleanExtension == "wmv" or cleanExtension == "mpg" or cleanExtension == "m4a" or cleanExtension == "mpeg":
            return True
    return False

def CompChanged(*args):
    global scriptDialog
    
    enabled = (scriptDialog.GetValue( "CompBox" ) != "" and not scriptDialog.GetValue( "MultiMachineBox" ))
    scriptDialog.SetEnabled( "OutputLabel", enabled )
    scriptDialog.SetEnabled( "OutputBox", enabled )
    scriptDialog.SetEnabled( "FramesLabel", enabled )
    scriptDialog.SetEnabled( "FramesBox", enabled )
    scriptDialog.SetEnabled( "ChunkSizeLabel", enabled )
    scriptDialog.SetEnabled( "ChunkSizeBox", enabled )
    
def VersionChanged(*args):
    global scriptDialog
    
    version = GetVersionNumber()
    scriptDialog.SetEnabled( "MissingFootage", (version > 8 ) )
    
def MultiMachineChanged(*args):
    global scriptDialog
    
    enabled = scriptDialog.GetValue( "MultiMachineBox" ) 
    scriptDialog.SetEnabled( "MultiMachineTasksBox" ,enabled )
    
    framesEnabled = not enabled and (scriptDialog.GetValue( "CompBox" ) != "")
    scriptDialog.SetEnabled( "OutputLabel", framesEnabled )
    scriptDialog.SetEnabled( "OutputBox", framesEnabled )
    scriptDialog.SetEnabled( "FramesLabel", framesEnabled )
    scriptDialog.SetEnabled( "FramesBox", framesEnabled )
    scriptDialog.SetEnabled( "ChunkSizeLabel", framesEnabled )
    scriptDialog.SetEnabled( "ChunkSizeBox", framesEnabled )
    scriptDialog.SetEnabled( "LocalRendering", framesEnabled )

def OverrideButtonPressed(*args):
    global scriptDialog

    enabled = scriptDialog.GetValue( "OverrideFailOnExistingAEProcess" )

    scriptDialog.SetEnabled( "FailOnExistingAEProcess" ,enabled )
    
def MemoryManageChanged(*args):
    global scriptDialog
    
    enabled = scriptDialog.GetValue( "MemoryManagement" ) 
    
    scriptDialog.SetEnabled( "ImageCacheLabel" ,enabled )
    scriptDialog.SetEnabled( "ImageCachePercentage" ,enabled )
    scriptDialog.SetEnabled( "MaxMemoryLabel" , enabled )
    scriptDialog.SetEnabled( "MaxMemoryPercentage" , enabled )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "AfterEffectsSettings.ini" )
      
def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog
    
    submitScene = bool(scriptDialog.GetValue("SubmitSceneBox"))
    multiMachine = bool(scriptDialog.GetValue("MultiMachineBox"))
    
    # Check if scene file exists
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox("Project file %s does not exist." % sceneFile, "Error" )
        return
    elif(not submitScene and PathUtils.IsPathLocal(sceneFile)):
        result = scriptDialog.ShowMessageBox("The project file " + sceneFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    concurrentTasks = scriptDialog.GetValue( "ConcurrentTasksBox" )
    if concurrentTasks > 1:
        result = scriptDialog.ShowMessageBox("The concurrent tasks is set to a value greater than 1.  This can cause Jobs to hang when rendering, are you sure you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    outputFile = ""
    frames = ""
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Get the comp
    comp = scriptDialog.GetValue("CompBox")
    if comp != "":
        # Check that the output is valid
        outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
        if len(outputFile) > 0:
            if not Directory.Exists( Path.GetDirectoryName(outputFile) ):
                scriptDialog.ShowMessageBox( "The directory of the output file does not exist:\n" + Path.GetDirectoryName(outputFile), "Error" )
                return
            elif(PathUtils.IsPathLocal(outputFile)):
                result = scriptDialog.ShowMessageBox("The output file " + outputFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
                if( result == "No" ):
                    return
            
            extension = Path.GetExtension( outputFile )
            if not IsMovieFormat( extension ):
                if outputFile.find( "[#" ) < 0 and outputFile.find( "#]" ) < 0:
                    directory = Path.GetDirectoryName( outputFile )
                    filename = Path.GetFileNameWithoutExtension( outputFile )
                    outputFile = Path.Combine( directory, filename + "[#####]" + extension )
        
        #Since we don't specify ranges for multi-machine rendering, don't check frame range when Multi-Machine Rendering = True
        if not multiMachine:
            # Check if a valid frame range has been specified.
            frames = scriptDialog.GetValue( "FramesBox" )
            if( not FrameUtils.FrameRangeValid( frames ) ):
                scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
                return
    else:
        jobName = jobName + " - Entire Render Queue"
    
    if multiMachine:
        jobName = jobName + " (multi-machine rendering)"
    
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( outputFile ):
        return
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "ae_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=AfterEffects" )
    writer.WriteLine( "Name=%s" % jobName )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
    writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
    writer.WriteLine( "ConcurrentTasks=%s" % concurrentTasks )
    writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
    
    if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    
    if multiMachine:
        writer.WriteLine( "MachineLimit=0" )
        writer.WriteLine( "Frames=1-%s" % scriptDialog.GetValue( "MultiMachineTasksBox" ) )
        writer.WriteLine( "ChunkSize=1" )
    else:
        if comp != "":
            writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
            writer.WriteLine( "Frames=%s" % frames )
            writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        else:
            writer.WriteLine( "MachineLimit=1" )
            writer.WriteLine( "Frames=0" )
            writer.WriteLine( "ChunkSize=1" )
    
    if len(outputFile) > 0:
        writer.WriteLine( "OutputFilename0=%s" % outputFile.replace( "[#####]", "#####" ) )
    
    extraKVPIndex = 0
    groupBatch = False
    if integration_dialog.IntegrationProcessingRequested():
        extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
        groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()
        
    if groupBatch:
        writer.WriteLine( "BatchName=%s\n" % ( jobName ) ) 
    writer.Close()
    # Create plugin info file.
    version = GetVersionNumber()
    
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "ae_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    if(not bool(scriptDialog.GetValue("SubmitSceneBox"))):
        writer.WriteLine("SceneFile=%s" % scriptDialog.GetValue("SceneBox").replace("\\","/").strip())
        
    writer.WriteLine("Comp=%s" % scriptDialog.GetValue("CompBox"))
    writer.WriteLine("Version=%s" % str(version) )
    writer.WriteLine("IgnoreMissingLayerDependenciesErrors=%s" % scriptDialog.GetValue("MissingLayers"))
    writer.WriteLine("IgnoreMissingEffectReferencesErrors=%s" % scriptDialog.GetValue("MissingEffects"))
    writer.WriteLine("FailOnWarnings=%s" % scriptDialog.GetValue("FailOnWarnings"))
    
    if multiMachine:
        writer.WriteLine("MultiMachineMode=True")
    else:
        writer.WriteLine("LocalRendering=%s" % scriptDialog.GetValue("LocalRendering"))
    
    writer.WriteLine("OverrideFailOnExistingAEProcess=%s" % scriptDialog.GetValue("OverrideFailOnExistingAEProcess"))
    writer.WriteLine("FailOnExistingAEProcess=%s" % scriptDialog.GetValue("OverrideFailOnExistingAEProcess"))

    writer.WriteLine("MemoryManagement=%s" % scriptDialog.GetValue("MemoryManagement"))
    writer.WriteLine("ImageCachePercentage=%s" % scriptDialog.GetValue("ImageCachePercentage"))
    writer.WriteLine("MaxMemoryPercentage=%s" % scriptDialog.GetValue("MaxMemoryPercentage"))
    
    writer.WriteLine("MultiProcess=%s" % scriptDialog.GetValue("MultiProcess"))
    if version > 8:
        writer.WriteLine("ContinueOnMissingFootage=%s" % scriptDialog.GetValue("MissingFootage"))
    
    if len(outputFile) > 0:
        writer.WriteLine("Output=%s" % outputFile)
    
    writer.Close()
    
    # Setup the command line arguments.
    arguments = [ jobInfoFilename, pluginInfoFilename ]
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.append( sceneFile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
