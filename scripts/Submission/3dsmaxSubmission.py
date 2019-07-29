# -*- coding: utf-8 -*-
from __future__ import print_function

import imp # For Integration UI
import re
import traceback

from Deadline.Scripting import ClientUtils, FrameUtils, PathUtils, RepositoryUtils, StringUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

from System.IO import File, Path, StreamWriter
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
DraftRequested = False

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    
    scriptDialog.SetTitle( "Submit 3dsmax Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( '3dsmax' ) )

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
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 4, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job.", False )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 5, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 5, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 6, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 6, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 7, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 8, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 9, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 10, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 10, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 10, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "3dsmax Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "3dsmax File", 0, 0, "The scene file to render.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "MultiFileBrowserControl", "", "3dsmax Files (*.max)", 0, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 1, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Scene File With Job", 1, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering." )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 2, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 2, 1 )
    scriptDialog.AddSelectionControlToGrid( "ShowVfbBox", "CheckBoxControl", True, "Show Virtual Frame Buffer", 2, 2, "Enable the virtual frame buffer during rendering. " )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 3, 0, "The version of 3ds Max to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "2020", ( "2014", "2015", "2016", "2017", "2018", "2019", "2020" ), 3, 1 )
    versionBox.ValueModified.connect(VersionChanged)

    scriptDialog.AddSelectionControlToGrid( "IsMaxDesignBox", "CheckBoxControl", False, "Use Design Edition", 3, 2, "Enable this if you are rendering with the Design edition of 3ds Max." )

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 4, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ( "None", "32bit", "64bit" ), 4, 1 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Advanced Options")
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "CameraLabel", "LabelControl", "Camera", 0, 0, "The name of the camera to render, or leave blank to render the active viewport", False )
    scriptDialog.AddControlToGrid( "CameraBox", "TextControl", "", 0, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "PluginIniLabel", "LabelControl", "Alternate Plugin.ini", 1, 0, "By default, all slaves will launch 3ds Max using the default plugin.ini file found in their 3ds max root folders. You can specify an alternative plugin.ini file here.", False )
    scriptDialog.AddSelectionControlToGrid( "PluginIniBox", "FileBrowserControl", "", "Plugin Ini Files (*.ini)", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "PreLoadLabel", "LabelControl", "Pre-Load Script", 2, 0, "A MAXScript file that is executed before the 3ds Max scene is loaded for rendering by the Slave.", False )
    scriptDialog.AddSelectionControlToGrid( "PreLoadBox", "FileBrowserControl", "", "MAXScript Files (*.ms);;Encrypted MAXScript Files (*.mse)", 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "PostLoadLabel", "LabelControl", "Post-Load Script", 3, 0, "A MAXScript file that is executed after the 3ds Max scene is loaded for rendering by the Slave.", False )
    scriptDialog.AddSelectionControlToGrid( "PostLoadBox", "FileBrowserControl", "", "MAXScript Files (*.ms);;Encrypted MAXScript Files (*.mse)", 3, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "PreFrameLabel", "LabelControl", "Pre-Frame Script", 4, 0, "A MAXScript file that is executed before a frame is rendered by the Slave.", False )
    scriptDialog.AddSelectionControlToGrid( "PreFrameBox", "FileBrowserControl", "", "MAXScript Files (*.ms);;Encrypted MAXScript Files (*.mse)", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "PostFrameLabel", "LabelControl", "Post-Frame Script", 5, 0, "A MAXScript file that is executed after a frame is rendered by the Slave.", False )
    scriptDialog.AddSelectionControlToGrid( "PostFrameBox", "FileBrowserControl", "", "MAXScript Files (*.ms);;Encrypted MAXScript Files (*.mse)", 5, 1, colSpan=3 )


    workstationModeControl = scriptDialog.AddSelectionControlToGrid( "WorkstationModeBox", "CheckBoxControl", False, "Force Workstation Mode", 6, 0, "When checked, 3ds Max will be launched in full Interactive mode and will require a license. ", True, 1, 2 )
    workstationModeControl.ValueModified.connect(WorkstationModeValueChanged)

    scriptDialog.AddSelectionControlToGrid( "SilentModeBox", "CheckBoxControl", False, "Enable Silent Mode", 6, 2, "This option is only available when Force Workstation Mode is checked, and should help suppress some popups.", True, 1, 2 )

    scriptDialog.AddSelectionControlToGrid( "IgnoreMissingExternalFilesBox", "CheckBoxControl", True, "Ignore Missing External File Errors", 7, 0, "Enable this to ignore missing external files (like textures) during rendering.", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "IgnoreMissingUVWsBox", "CheckBoxControl", True, "Ignore Missing UVW Errors", 7, 2, "Enable this to ignore missing UVWs during rendering.", True, 1, 2 )

    scriptDialog.AddSelectionControlToGrid( "IgnoreMissingXREFsBox", "CheckBoxControl", True, "Ignore Missing XREF Errors", 8, 0, "Enable this to ignore missing XREFs during rendering.", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "IgnoreMissingDLLsBox", "CheckBoxControl", False, "Ignore Missing DLL Errors", 8, 2, "Enable this to ignore missing dlls (like plugins) during rendering.", True, 1, 2 )

    scriptDialog.AddSelectionControlToGrid( "LocalRenderingBox", "CheckBoxControl", True, "Enable Local Rendering", 9, 0, "If enabled, the frames will be rendered locally, and then copied to their final network location. ", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "DisableMultipassBox", "CheckBoxControl", False, "Disable Multipass Effects", 9, 2, "Enable this option to skip over multipass effects if they are enabled for the camera to be rendered. ", True, 1, 2 )

    scriptDialog.AddSelectionControlToGrid( "RestartRendererBox", "CheckBoxControl", False, "Restart Renderer Between Frames", 10, 0, "This option can be used to force Deadline to restart the renderer after each frame to avoid some potential problems in very rare cases. Normally, you should leave this option unchecked. ", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "RemovePaddingBox", "CheckBoxControl", False, "Remove Filename Padding", 10, 2, "If checked, the output filename will be (for example) 'output.tga' instead of 'output0000.tga'. This feature should only be used when rendering single frames.", True, 1, 2 )

    gammaBox = scriptDialog.AddSelectionControlToGrid( "GammaCorrectionBox", "CheckBoxControl", False, "Gamma Correction", 11, 0, "Enable to apply gamma correction during rendering. ", True, 1, 2 )
    gammaBox.ValueModified.connect(GammaChanged)

    scriptDialog.AddControlToGrid( "GammaInputLabel", "LabelControl", "Input Gamma", 12, 0, "The gamma input value.", False )
    scriptDialog.AddRangeControlToGrid( "GammaInputBox", "RangeControl", 1.0, 0.01, 5.0, 2, 0.1, 12, 1 )
    scriptDialog.AddControlToGrid( "GammaOutputLabel", "LabelControl", "Output Gamma", 12, 2, "The gamma output value.", False )
    scriptDialog.AddRangeControlToGrid( "GammaOutputBox", "RangeControl", 1.0, 0.01, 5.0, 2, 0.1, 12, 3 )

    overrideLanguageControl = scriptDialog.AddSelectionControlToGrid( "OverrideLanguageBox", "CheckBoxControl", False, "Override Language", 13, 0, "Choose the language of Max to render with, or just use the default." )
    overrideLanguageControl.ValueModified.connect(OverrideLanguageValueChanged)
    scriptDialog.AddComboControlToGrid( "LanguageBox", "ComboControl", "Default", ["Default","CHS","DEU","ENU","FRA","JPN","KOR"], 13, 1 )
    scriptDialog.AddSelectionControlToGrid( "OneCpuPerTaskBox", "CheckBoxControl", False, "One Cpu Per Task", 13, 2, "When checked, each task a slave renders will only use one cpu. This can be useful if you are rendering a single threaded job, and you have set Concurrent Tasks to a value greater than 1." )

    scriptDialog.AddControlToGrid( "PathConfigLabel", "LabelControl", "Alternate Path File", 14, 0, "Allows you to specify an alternate path file in the MXP format that the slaves can use to find bitmaps that are not found on the primary map paths.", False )
    scriptDialog.AddSelectionControlToGrid( "PathConfigBox", "FileBrowserControl", "", "Path Configuration Files (*.mxp);;All Files (*)", 14, 1, "", True , 1, 3 )

    scriptDialog.AddSelectionControlToGrid( "MergePathConfigBox", "CheckBoxControl", False, "Merge Path File", 15, 0, "If enabled, the path config file will be merged with the existing path configuration, instead of overwriting it." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator7", "SeparatorControl", "VRay DBR and Mental Ray Satellite", 0, 0 )
    scriptDialog.AddControlToGrid( "DBRLabel", "LabelControl", "Offloads a DBR or Satellite render to Deadline. This requires the VRay DBR or\nMental Ray Satellite rendering option to be enabled in your 3ds Max scene settings.\nIt also requires that the vray_dr.cfg, vrayrt_dr.cfg or max.rayhosts files be writable\non the render nodes. See the 3ds Max documentation for more information.", 1, 0 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "DBRModeLabel", "LabelControl", "Mode", 0, 0, "Select VRay DBR or Mental Ray Satellite mode, or leave disabled to do a normal render.", False, colSpan=4 )
    dbrModeBox = scriptDialog.AddComboControlToGrid( "DBRModeBox", "ComboControl", "Disabled", ("Disabled","Mental Ray Satellite","VRay DBR", "VRay RT DBR"), 0, 1, expand=True )
    dbrModeBox.ValueModified.connect(DBRModeChanged)

    scriptDialog.AddControlToGrid( "DBRServersLabel", "LabelControl", "Number of Slaves", 0, 2, "The number of Slaves to reserve for VRay DBR or Mental Ray Satellite rendering.", False )
    scriptDialog.AddRangeControlToGrid( "DBRServersBox", "RangeControl", 5, 1, 100, 0, 1, 0, 3, expand=True )

    scriptDialog.AddControlToGrid( "GPUSeparator", "SeparatorControl", "GPU Options", 1, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "GPUsPerTaskLabel", "LabelControl", "GPUs Per Task", 2, 0, "The number of GPUs to use per task. If set to 0, the default number of GPUs will be used, unless 'Select GPU Devices' Id's have been defined.", False )
    GPUsPerTaskBox = scriptDialog.AddRangeControlToGrid( "GPUsPerTaskBox", "RangeControl", 0, 0, 16, 0, 1, 2, 1 )
    GPUsPerTaskBox.ValueModified.connect(GPUsPerTaskChanged)

    scriptDialog.AddControlToGrid( "GPUsSelectDevicesLabel", "LabelControl", "Select GPU Devices", 2, 2, "A comma separated list of the GPU devices to use specified by device Id. 'GPUs Per Task' will be ignored.", False )
    GPUsSelectDevicesBox = scriptDialog.AddControlToGrid( "GPUsSelectDevicesBox", "TextControl", "", 2, 3 )
    GPUsSelectDevicesBox.ValueModified.connect(GPUsSelectDevicesChanged)
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "3dsMaxMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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
    
    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox",
    "LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","VersionBox","BuildBox","PluginIniBox","PathConfigBox","MergePathConfigBox","PreLoadBox",
    "PostLoadBox", "PreFrameBox", "PostFrameBox", "SubmitSceneBox","LocalRenderingBox","IsMaxDesignBox","OneCpuPerTaskBox","OverrideLanguageBox",
    "LanguageBox","GammaCorrectionBox", "GammaInputBox", "GammaOutputBox","DBRModeBox","DBRServersBox" )

    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    GammaChanged()
    VersionChanged()
    OverrideLanguageValueChanged()
    WorkstationModeValueChanged()
    PopulateLanguageDropDowns()
    GPUsPerTaskChanged()
    GPUsSelectDevicesChanged()
    DBRModeChanged()
    
    scriptDialog.ShowDialog( False )

########################################################################
## Helper Functions
########################################################################
def GammaChanged( *args ):
    global scriptDialog
    gammaCorrection = scriptDialog.GetValue( "GammaCorrectionBox" )
    scriptDialog.SetEnabled( "GammaInputLabel", gammaCorrection )
    scriptDialog.SetEnabled( "GammaInputBox", gammaCorrection )
    scriptDialog.SetEnabled( "GammaOutputLabel", gammaCorrection )
    scriptDialog.SetEnabled( "GammaOutputBox", gammaCorrection )

def GPUsPerTaskChanged(*args):
    global scriptDialog

    perTaskEnabled = ( scriptDialog.GetValue( "GPUsPerTaskBox" ) == 0 )

    scriptDialog.SetEnabled( "GPUsSelectDevicesLabel", perTaskEnabled )
    scriptDialog.SetEnabled( "GPUsSelectDevicesBox", perTaskEnabled )

def GPUsSelectDevicesChanged(*args):
    global scriptDialog

    selectDeviceEnabled = ( scriptDialog.GetValue( "GPUsSelectDevicesBox" ) == "" )

    scriptDialog.SetEnabled( "GPUsPerTaskLabel", selectDeviceEnabled )
    scriptDialog.SetEnabled( "GPUsPerTaskBox", selectDeviceEnabled )

def DBRModeChanged( *args ):
    global scriptDialog
    dbrEnabled = (scriptDialog.GetValue( "DBRModeBox" ) != "Disabled")
    scriptDialog.SetEnabled( "DBRServersLabel", dbrEnabled )
    scriptDialog.SetEnabled( "DBRServersBox", dbrEnabled )

    scriptDialog.SetEnabled( "GPUsPerTaskLabel", not dbrEnabled )
    scriptDialog.SetEnabled( "GPUsPerTaskBox", not dbrEnabled )
    scriptDialog.SetEnabled( "GPUsSelectDevicesLabel", not dbrEnabled )
    scriptDialog.SetEnabled( "GPUsSelectDevicesBox", not dbrEnabled )

def VersionChanged( *args ):
    global scriptDialog
    
    version = int(scriptDialog.GetValue( "VersionBox" ))
    scriptDialog.SetEnabled( "IsMaxDesignBox", 2010 <= version <= 2015 )
    
    languageEnabled = version >= 2013
    scriptDialog.SetEnabled( "OverrideLanguageBox", languageEnabled )
    scriptDialog.SetEnabled( "LanguageBox", languageEnabled and scriptDialog.GetValue( "OverrideLanguageBox" ) )

    PopulateLanguageDropDowns( None )
    
    buildEnabled = version < 2014
    scriptDialog.SetEnabled( "BuildLabel", buildEnabled )
    scriptDialog.SetEnabled( "BuildBox", buildEnabled )
    
def OverrideLanguageValueChanged( *args ):
    global scriptDialog
    
    version = scriptDialog.GetValue( "VersionBox" )
    languageEnabled = (int( version ) >= 2013)
    scriptDialog.SetEnabled( "LanguageBox", languageEnabled and scriptDialog.GetValue( "OverrideLanguageBox" ) )

def PopulateLanguageDropDowns( *args ):
    global scriptDialog

    version = int(scriptDialog.GetValue( "VersionBox" ))
    if version >= 2016:
        scriptDialog.SetItems( "LanguageBox", ["Default","CHS","DEU","ENU","FRA","JPN","KOR","PTB"] )
    else:
        scriptDialog.SetItems( "LanguageBox", ["Default","CHS","DEU","ENU","FRA","JPN","KOR"] )

def WorkstationModeValueChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "SilentModeBox", scriptDialog.GetValue( "WorkstationModeBox" ) )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "3dsmaxSettings.ini" )
   
def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    
    try:
        submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
        
        # Check if Integration options are valid
        if not integration_dialog.CheckIntegrationSanity( ):
            return

        warnings = []
        errors = []
        
        # Check if max files exist.
        sceneFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "SceneBox" ), False )
        if not sceneFiles:
            errors.append( "No 3dsmax file specified" )
        
        for sceneFile in sceneFiles:
            if not File.Exists( sceneFile ):
                errors.append( "3dsmax file %s does not exist" % sceneFile )
                return
            elif not submitScene and PathUtils.IsPathLocal( sceneFile ):
                warnings.append( "The scene file " + sceneFile + " is local and is not being submitted with the job, are you sure you want to continue?" )
        
        # Check if path config file exists.
        pathConfigFile = scriptDialog.GetValue( "PathConfigBox" ).strip()
        if pathConfigFile:
            if not File.Exists( pathConfigFile ):
                errors.append( "Path configuration file %s does not exist" % pathConfigFile )
        
        # Check if PreLoad script file exists.
        preLoadFile = scriptDialog.GetValue( "PreLoadBox" ).strip()
        if preLoadFile:
            if not File.Exists( preLoadFile ):
                errors.append( "PreLoad MAXScript file %s does not exist" % preLoadFile )
        
        # Check if PostLoad script file exists.
        postLoadFile = scriptDialog.GetValue( "PostLoadBox" ).strip()
        if postLoadFile:
            if not File.Exists( postLoadFile ):
                errors.append( "PostLoad MAXScript file %s does not exist" % postLoadFile )

        # Check if PreFrame script file exists.
        preFrameFile = scriptDialog.GetValue( "PreFrameBox" ).strip()
        if preFrameFile:
            if not File.Exists( preFrameFile ):
                errors.append( "PreFrame MAXScript file %s does not exist" % preFrameFile )

        # Check if PostFrame script file exists.
        postFrameFile = scriptDialog.GetValue( "PostFrameBox" ).strip()
        if postFrameFile:
            if not File.Exists( postFrameFile ):
                errors.append( "PostFrame MAXScript file %s does not exist" % postFrameFile )
        
        # Check if a valid frame range has been specified.
        frames = scriptDialog.GetValue( "FramesBox" )
        if scriptDialog.GetValue( "DBRModeBox" ) != "Disabled":
            frameArray = FrameUtils.Parse( frames )
            if len(frameArray) != 1:
                errors.append( "Please specify a single frame for distributed rendering in the Frame List." )
            elif not FrameUtils.FrameRangeValid( frames ):
                errors.append( "Please specify a valid single frame for distributed rendering in the Frame List." )
            
            frames = "0-" + str(scriptDialog.GetValue( "DBRServersBox" ) - 1)
        else:
            if not FrameUtils.FrameRangeValid( frames ):
                errors.append( "Frame range %s is not valid" % frames )

        # If using 'select GPU device Ids' then check device Id syntax is valid
        if scriptDialog.GetValue( "GPUsPerTaskBox" ) == 0 and scriptDialog.GetValue( "GPUsSelectDevicesBox" ):
            regex = re.compile( "^(\d{1,2}(,\d{1,2})*)?$" )
            validSyntax = regex.match( scriptDialog.GetValue( "GPUsSelectDevicesBox" ) )
            if not validSyntax:
                errors.append( "'Select GPU Devices' syntax is invalid!\nTrailing 'commas' if present, should be removed.\nValid Examples: 0 or 2 or 0,1,2 or 0,3,4 etc" )

            # Check if concurrent threads > 1
            if scriptDialog.GetValue( "ConcurrentTasksBox" ) > 1:
                errors.append( "If using 'Select GPU Devices', then 'Concurrent Tasks' must be set to 1" )

        if errors:
            scriptDialog.ShowMessageBox( "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % ( "\n\n".join( errors ) ), "Errors" )
            return

        if warnings:
            result = scriptDialog.ShowMessageBox( "Warnings:\n\n%s\n\nDo you still want to continue?" % ( "\n\n".join( warnings ) ), "Warnings", ( "Yes","No" ) )
            if result == "No":
                return

        successes = 0
        failures = 0
        
        # Submit each scene file separately.
        for sceneFile in sceneFiles:
            jobName = scriptDialog.GetValue( "NameBox" )
            if len(sceneFiles) > 1:
                jobName = jobName + " [" + Path.GetFileName( sceneFile ) + "]"
            
            # Create job info file.
            jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "max_job_info.job" )
            writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "Plugin=3dsmax" )
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
            if scriptDialog.GetValue( "IsBlacklistBox" ):
                writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            else:
                writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            
            writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
            writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
            writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
            
            if scriptDialog.GetValue( "SubmitSuspendedBox" ):
                writer.WriteLine( "InitialStatus=Suspended" )
            
            writer.WriteLine( "Frames=%s" % frames )
            if scriptDialog.GetValue( "DBRModeBox" ) == "Disabled":
                writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
            
            # Integration
            extraKVPIndex = 0
            groupBatch = False
            
            if integration_dialog.IntegrationProcessingRequested():
                extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
                groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()
            
            if groupBatch:
                writer.WriteLine( "BatchName=%s\n" % jobName )
                    
            writer.Close()
            
            # Create plugin info file.
            pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "max_plugin_info.job" )
            writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
            
            writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )
            writer.WriteLine( "IsMaxDesign=%s" % scriptDialog.GetValue( "IsMaxDesignBox" ) )
            
            if int(scriptDialog.GetValue( "VersionBox" )) < 2014:
                writer.WriteLine( "MaxVersionToForce=%s" % scriptDialog.GetValue( "BuildBox" ) )
                writer.WriteLine( "MaxVersionToForce0=None" )
                writer.WriteLine( "MaxVersionToForce1=32bit" )
                writer.WriteLine( "MaxVersionToForce2=64bit" )
                
            writer.WriteLine( "UseSlaveMode=%d" % ( not scriptDialog.GetValue( "WorkstationModeBox" ) ) )
            if scriptDialog.GetValue( "WorkstationModeBox" ):
                writer.WriteLine( "UseSilentMode=%s" % (scriptDialog.GetValue( "SilentModeBox" ) ) )
            else:
                writer.WriteLine( "UseSilentMode=False" )
            
            writer.WriteLine( "ShowFrameBuffer=%s" % scriptDialog.GetValue( "ShowVfbBox" ) )
            writer.WriteLine( "RemovePadding=%s" % scriptDialog.GetValue( "RemovePaddingBox" ) )
            writer.WriteLine( "RestartRendererMode=%s" % scriptDialog.GetValue( "RestartRendererBox" ) )
            writer.WriteLine( "IgnoreMissingExternalFiles=%s" % scriptDialog.GetValue( "IgnoreMissingExternalFilesBox" ) )
            writer.WriteLine( "IgnoreMissingUVWs=%s" % scriptDialog.GetValue( "IgnoreMissingUVWsBox" ) )
            writer.WriteLine( "IgnoreMissingXREFs=%s" % scriptDialog.GetValue( "IgnoreMissingXREFsBox" ) )
            writer.WriteLine( "IgnoreMissingDLLs=%s" % scriptDialog.GetValue( "IgnoreMissingDLLsBox" ) )
            writer.WriteLine( "LocalRendering=%s" % scriptDialog.GetValue( "LocalRenderingBox" ) )
            writer.WriteLine( "DisableMultipass=%s" % scriptDialog.GetValue( "DisableMultipassBox" ) )
            writer.WriteLine( "OneCpuPerTask=%s" % scriptDialog.GetValue( "OneCpuPerTaskBox" ) )
            
            if pathConfigFile:
                writer.WriteLine( "PathConfigFile=%s" % Path.GetFileName( pathConfigFile ) )
                writer.WriteLine( "MergePathConfigFile=%s" % scriptDialog.GetValue( "MergePathConfigBox" ) )
            
            if preLoadFile:
                writer.WriteLine( "PreLoadScript=%s" % Path.GetFileName( preLoadFile ) )

            if postLoadFile:
                writer.WriteLine( "PostLoadScript=%s" % Path.GetFileName( postLoadFile ) )
            
            if preFrameFile:
                writer.WriteLine( "PreFrameScript=%s" % Path.GetFileName( preFrameFile ) )

            if postFrameFile:
                writer.WriteLine( "PostFrameScript=%s" % Path.GetFileName( postFrameFile ) )
            
            pluginIniOverride = scriptDialog.GetValue( "PluginIniBox" ).strip()
            if pluginIniOverride:
                writer.WriteLine( "OverridePluginIni=%s" % pluginIniOverride )
            
            writer.WriteLine( "GammaCorrection=%s" % scriptDialog.GetValue( "GammaCorrectionBox" ) )
            writer.WriteLine( "GammaInput=%s" % scriptDialog.GetValue( "GammaInputBox" ) )
            writer.WriteLine( "GammaOutput=%s" % scriptDialog.GetValue( "GammaOutputBox" ) )

            if int(scriptDialog.GetValue( "VersionBox" )) >= 2013:
                if scriptDialog.GetValue( "OverrideLanguageBox" ):
                    writer.WriteLine( "Language=%s" % scriptDialog.GetValue( "LanguageBox" ) )
                else:
                    writer.WriteLine( "Language=Default" )
            
            camera = scriptDialog.GetValue("CameraBox")
            if camera:
                writer.WriteLine( "Camera=%s" % camera)
                writer.WriteLine( "Camera0=")
                writer.WriteLine( "Camera1=%s" % camera)
            
            if not submitScene:
                writer.WriteLine( "SceneFile=%s" % sceneFile )
            
            if scriptDialog.GetValue( "DBRModeBox" ) != "Disabled":
                if scriptDialog.GetValue( "DBRModeBox" ) == "VRay DBR":
                    writer.WriteLine( "VRayDBRJob=True")
                elif scriptDialog.GetValue( "DBRModeBox" ) == "Mental Ray Satellite":
                    writer.WriteLine( "MentalRayDBRJob=True")
                elif scriptDialog.GetValue( "DBRModeBox" ) == "VRay RT DBR":
                    writer.WriteLine( "VRayRtDBRJob=True")
                writer.WriteLine( "DBRJobFrame=%s" % scriptDialog.GetValue( "FramesBox" ) )

            if scriptDialog.GetValue( "DBRModeBox" ) == "Disabled":
                writer.WriteLine( "GPUsPerTask=%s" % scriptDialog.GetValue( "GPUsPerTaskBox" ) )
                writer.WriteLine( "GPUsSelectDevices=%s" % scriptDialog.GetValue( "GPUsSelectDevicesBox" ) )
            
            writer.Close()
            
            # Setup the command line arguments.
            arguments = [ jobInfoFilename, pluginInfoFilename ]
            if scriptDialog.GetValue( "SubmitSceneBox" ):
                arguments.append( sceneFile )
            
            if pathConfigFile:
                arguments.append( pathConfigFile )
            if preLoadFile:
                arguments.append( preLoadFile )
            if postLoadFile:
                arguments.append( postLoadFile )
            if preFrameFile:
                arguments.append( preFrameFile )
            if postFrameFile:
                arguments.append( postFrameFile )
            
            if len( sceneFiles ) == 1:
                results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
                scriptDialog.ShowMessageBox( results, "Submission Results" )
            else:
                # Now submit the job.
                exitCode = ClientUtils.ExecuteCommand( arguments )
                if exitCode == 0:
                    successes += 1
                else:
                    failures += 1
            
        if len( sceneFiles ) > 1:
            scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )
    except:
        scriptDialog.ShowMessageBox(traceback.format_exc(), "")
