import re

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
def __main__():
    global scriptDialog
    global settings
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Harmony Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Harmony' ) )
    
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
    scriptDialog.EndTabPage()

    scriptDialog.AddTabPage("Harmony Options")
    scriptDialog.AddGrid()
    
    useDbBox = scriptDialog.AddSelectionControlToGrid("UseDatabaseBox","CheckBoxControl",False,"Use Database Scene",1, 0, "If this option is enabled, Harmony use a scene from the Database it is connected to.",colSpan=2)
    useDbBox.ValueModified.connect(UseDatabaseChanged)
    scriptDialog.AddSelectionControlToGrid("SubmitSceneBox","CheckBoxControl",False,"Submit Harmony Scene",1, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering.",colSpan=2)
    
    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Harmony File", 2, 0, "The scene file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Harmony Files (*.xstage)", 2, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "EnvironmentLabel", "LabelControl", "Environment", 3, 0, "The environment of the scene you want to render.", False )
    scriptDialog.AddControlToGrid( "EnvironmentBox", "TextControl", "", 3, 1 )
    scriptDialog.AddControlToGrid( "JobLabel", "LabelControl", "Job", 3, 2, "The Job that the scene you wish to render is part of.", False )
    scriptDialog.AddControlToGrid( "JobBox", "TextControl", "", 3, 3 )
    
    scriptDialog.AddControlToGrid( "SceneNameLabel", "LabelControl", "Scene", 4, 0, "The scene that you want to render.", False )
    scriptDialog.AddControlToGrid( "SceneNameBox", "TextControl", "", 4, 1 )
    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 4, 2, "The version of the scene that you want to render.", False )
    scriptDialog.AddControlToGrid( "SceneVersionBox", "TextControl", "", 4, 3 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 5, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 5, 1 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 5, 2, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 5, 3 )

    scriptDialog.AddControlToGrid("VersionLabel","LabelControl","Harmony Version", 6, 0, "The version of Harmony to render with.", False)
    scriptDialog.AddComboControlToGrid("VersionBox","ComboControl","15",("10","11","12","14","15"), 6, 1)
    scriptDialog.AddControlToGrid("CameraLabel", "LabelControl", "Camera", 6, 2,
                                  "The Camera to render with. If Blank, the scene will be rendered with the current Camera.",
                                  False)
    scriptDialog.AddControlToGrid("CameraBox", "TextControl", "", 6, 3)

    useResNameBox = scriptDialog.AddSelectionControlToGrid("UseResolutionNameBox", "CheckBoxControl", False, "Use Resolution Preset",
                                                      7, 0,
                                                      "If this option is enabled, Harmony uses the specified resolution preset in the box below.",
                                                      colSpan=2)
    useResNameBox.ValueModified.connect(UseResolutionName)

    scriptDialog.AddControlToGrid("PresetLabel", "LabelControl", "Resolution Preset", 8, 0, "The resolution preset to use.", False)
    resolutionPresetBox = scriptDialog.AddComboControlToGrid("ResolutionPresetBox", "ComboControl", "HDTV_1080p24", ("HDTV_1080p24","HDTV_1080p25","HDTV_720p24","4K_UHD","8K_UHD","DCI_2K","DCI_4K","film-2K","film-4K",
                                                                                               "film-1.33_H","film-1.66_H","film-1.66_V","Cineon","NTSC","PAL","2160p","1440p","1080p","720p","480p",
                                                                                               "360p","240p","low","Web_Video","Game_512","Game_512_Ortho","WebCC_Preview","Custom"), 8, 1)
    resolutionPresetBox.ValueModified.connect(ResPresetChanged)
    scriptDialog.AddControlToGrid("PresetNameLabel", "LabelControl", "Preset Name", 8, 2, "The name of the custom resolution preset that will be used.", False)
    scriptDialog.AddControlToGrid("PresetName", "TextControl", "", 8, 3)

    scriptDialog.AddControlToGrid( "ResolutionXLabel", "LabelControl", "Resolution X", 9, 0, "The X resolution of the render image. If 0, then the current resolution and Field of view will be used.", False )
    scriptDialog.AddRangeControlToGrid( "ResolutionXBox", "RangeControl", 1920, 0, 100000, 0, 1, 9, 1 )
    scriptDialog.AddControlToGrid( "ResolutionYLabel", "LabelControl", "Resolution Y", 9, 2, "The Y resolution of the render image. If 0, then the current resolution and Field of view will be used.", False )
    scriptDialog.AddRangeControlToGrid( "ResolutionYBox", "RangeControl", 1080, 0, 100000, 0, 1, 9, 3 )
    
    scriptDialog.AddControlToGrid( "FieldOfViewLabel", "LabelControl", "Field of View", 10, 0, "The Field of view of the render image. If 0, then the current resolution and Field of view will be used.", False )
    scriptDialog.AddRangeControlToGrid( "FieldOfViewBox", "RangeControl", 41.11, 0, 89, 2, 0.1, 10, 1 )

    scriptDialog.SetEnabled("ResolutionPresetBox", False)
    scriptDialog.SetEnabled("PresetName", False)
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
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox", "FramesBox", "ChunkSizeBox", "VersionBox", "SubmitSceneBox", "ResolutionXBox", "ResolutionYBox", "FieldOfViewBox", "UseDatabaseBox", "EnvironmentBox", "JobBox", "SceneNameBox", "SceneVersionBox" )	
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    UseDatabaseChanged()
    
    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "HarmonySettings.ini" )

def UseDatabaseChanged(*args):
    useDB = scriptDialog.GetValue( "UseDatabaseBox" )
    
    scriptDialog.SetEnabled( "SubmitSceneBox", not useDB )
    scriptDialog.SetEnabled( "SceneBox", not useDB )
    
    scriptDialog.SetEnabled( "EnvironmentBox", useDB )
    scriptDialog.SetEnabled( "JobBox", useDB )
    scriptDialog.SetEnabled( "SceneNameBox", useDB )
    scriptDialog.SetEnabled( "SceneVersionBox", useDB )

def UseResolutionName(*args):
    useResName = scriptDialog.GetValue( "UseResolutionNameBox" )

    scriptDialog.SetEnabled( "ResolutionXBox", not useResName )
    scriptDialog.SetEnabled( "ResolutionYBox", not useResName )
    scriptDialog.SetEnabled( "FieldOfViewBox", not useResName )

    scriptDialog.SetEnabled( "ResolutionPresetBox", useResName )
    scriptDialog.SetEnabled( "PresetName", useResName and scriptDialog.GetValue( "ResolutionPresetBox" ) == "Custom" )

def ResPresetChanged(*args):
    scriptDialog.SetEnabled( "PresetName", scriptDialog.GetValue( "ResolutionPresetBox" ) == "Custom" )

def SubmitButtonPressed(*args):
    global scriptDialog
    global shotgunSettings
    
    paddedNumberRegex = Regex( "\\$F([0-9]+)" )
    
    # Check if harmony files exist.
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "Harmony file %s does not exist" % sceneFile, "Error" )
        return
    elif (PathUtils.IsPathLocal(sceneFile) and not scriptDialog.GetValue("SubmitSceneBox")):
        result = scriptDialog.ShowMessageBox("Harmony file " + sceneFile + " is local.  Are you sure you want to continue?", "Warning",("Yes","No"))
        if(result=="No"):
            return

    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return
    # Check if custom preset name is specified.
    usingResName = scriptDialog.GetValue( "UseResolutionNameBox" )
    resPresetBox = scriptDialog.GetValue( "ResolutionPresetBox" )
    presetName = scriptDialog.GetValue( "PresetName" ).strip()
    if usingResName and resPresetBox == "Custom" and re.match( r"^[\w-]+$", presetName ) is None:
        scriptDialog.ShowMessageBox( "Your custom resolution preset may only contain alphanumeric characters, hyphens, and underscores.", "Error" )
        return

    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "harmony_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Harmony" )
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
    writer.WriteLine( "ChunkSize=%s" %  scriptDialog.GetValue( "ChunkSizeBox" ) )
    writer.Close()
        
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "harmony_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    if scriptDialog.GetValue("UseDatabaseBox"):
        writer.WriteLine("IsDatabase=True");
        writer.WriteLine("Environment=%s" % scriptDialog.GetValue("EnvironmentBox"))
        writer.WriteLine("Job=%s" % scriptDialog.GetValue("JobBox"))
        writer.WriteLine("SceneName=%s" % scriptDialog.GetValue("SceneNameBox"))
        writer.WriteLine("SceneVersion=%s" % scriptDialog.GetValue("SceneVersionBox"))
    else:
        writer.WriteLine("IsDatabase=False");
        if(not scriptDialog.GetValue("SubmitSceneBox")):
            writer.WriteLine("SceneFile=%s" % sceneFile.replace("\\","/"))

    writer.WriteLine("Version=%s" % scriptDialog.GetValue("VersionBox"))
    writer.WriteLine("UsingResPreset=%s" % usingResName)
    if usingResName:
        writer.WriteLine("ResolutionName=%s" % resPresetBox)
        if resPresetBox == "Custom":
            writer.WriteLine("PresetName=%s" % presetName)
    else:
        writer.WriteLine("ResolutionX=%s" % scriptDialog.GetValue("ResolutionXBox"))
        writer.WriteLine("ResolutionY=%s" % scriptDialog.GetValue("ResolutionYBox"))
        writer.WriteLine("FieldOfView=%s" % scriptDialog.GetValue("FieldOfViewBox"))
    writer.WriteLine("Camera=%s" % scriptDialog.GetValue("CameraBox"))
    writer.Close()

    arguments = []
    arguments.append( jobInfoFilename )
    arguments.append( pluginInfoFilename )
    if scriptDialog.GetValue( "SubmitSceneBox" ) and not scriptDialog.GetValue("UseDatabaseBox"):
        arguments.append( sceneFile )
            
    jobResult = ClientUtils.ExecuteCommandAndGetOutput( arguments )

    scriptDialog.ShowMessageBox( jobResult, "Submission Results" )
    