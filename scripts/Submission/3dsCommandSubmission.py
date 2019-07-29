# -*- coding: utf-8 -*-
from __future__ import print_function

import imp # For Integration UI
import os
import re
import traceback

from Deadline.Scripting import ClientUtils, FrameUtils, PathUtils, RepositoryUtils, StringUtils
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
    
    scriptDialog.SetTitle( "Submit 3ds Command Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( '3dsCmd' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)

    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 0, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", expand=False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 0, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 1, 0, "A simple description of your job. This is optional and can be left blank.", expand=False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 1, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 2, 0, "The department you belong to. This is optional and can be left blank.", expand=False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 2, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 0, 0, "The pool that your job will be submitted to.", expand=False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 0, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 1, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", expand=False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 1, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 2, 0, "The group that your job will be submitted to.", expand=False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 2, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 3, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", expand=False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 3, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 4, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", expand=False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 4, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job.", True, 1, 2 )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 5, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 5, 2,"If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator.", True, 1, 2 )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 6, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 6, 2,"You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist.", True, 1, 2 )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 7, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 7, 1,"", True, 1, 3 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 8, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 8, 1,"", True, 1, 3 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 9, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 9, 1,"", True, 1, 3 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 10, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 10, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 10, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "3ds Command Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Scene File", 0, 0, "The scene file to render.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "MultiFileBrowserControl", "", "3dsmax Files (*.max);;All Files (*)", 0, 1,"", True, 1, 2 )

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output File (Optional)", 1,0, "Override the output path in the scene. This is optional, and can be left blank.", False)
    scriptDialog.AddSelectionControlToGrid("OutputBox", "FileSaverControl", "", "Avi File (*.avi);;BMP Image File (*.bmp);;Kodak Cineon (*.cin);;Encapsulated PostScript File (*.eps *.ps);;Autodesk Flic Image File (*.flc *.fli *.cel);;Radiance Image File (HDRI) (*.hdr *.pic);;JPEG File (*.jpg *.jpe *.jpeg);;PNG Image File (*.png);;MOV QuickTime File (*.mov);;SGI's Image File Format (*.rgb *.sgi);;RLA Image File (*.rla);;RPF Image File (*.rpf);;Targe Image File (*.tga *.vda *.icb *.vst);;TIF Image File (*.tif);;All Files (*)", 1, 1,"", True, 1, 2)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 2, 0, "The list of frames to render.", False )
    FramesBox = scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 2, 1 )
    FramesBox.ValueModified.connect(FramesChanged)
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Scene File With Job", 2, 2,"If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering." )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 3, 1 )

    scriptDialog.AddSelectionControlToGrid( "IsMaxDesignBox", "CheckBoxControl", False, "Use Design Edition", 3, 2, "Enable this if you are rendering with the Design edition of 3ds Max." )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 4, 0, "The version of 3dsmax to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "2020", ( "2014", "2015", "2016", "2017", "2018", "2019", "2020" ), 4, 1 )
    versionBox.ValueModified.connect(VersionChanged)

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 5, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ( "None", "32bit", "64bit" ), 5, 1 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Advanced Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Advanced Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "CameraLabel", "LabelControl", "Camera", 0, 0, "The name of the camera to render, or leave blank to render the active viewport.", expand=False )
    scriptDialog.AddControlToGrid( "CameraBox", "TextControl", "", 0, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "RenderPresetLabel", "LabelControl", "Render Preset File", 1, 0, "Uses a render preset file where <filename> is the name of the preset (*.rps) file.", expand=False )
    scriptDialog.AddSelectionControlToGrid( "RenderPresetBox", "FileBrowserControl", "", "Render Preset Settings Files (*.rps);;All Files (*)", 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "PreRenderScriptLabel", "LabelControl", "Pre Render Script File", 2, 0, "Uses a pre-render script where <filename> is the name of the maxscript (*.ms) file.", expand=False )
    scriptDialog.AddSelectionControlToGrid( "PreRenderScriptBox", "FileBrowserControl", "", "MAXScript File (*.ms);;All Files (*)", 2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "PostRenderScriptLabel", "LabelControl", "Post Render Script File", 3, 0, "Uses a post-render script where <filename> is the name of the maxscript (*.ms) file.", expand=False )
    scriptDialog.AddSelectionControlToGrid( "PostRenderScriptBox", "FileBrowserControl", "", "MAXScript File (*.ms);;All Files (*)", 3, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "SceneStateLabel", "LabelControl", "Scene State", 4, 0, "Loads the specified scene state in the 3ds Max scene file before rendering the image.", expand=False )
    scriptDialog.AddControlToGrid( "SceneStateBox", "TextControl", "", 4, 1, colSpan=2 )

    batchRenderBox = scriptDialog.AddSelectionControlToGrid( "BatchRenderBox", "CheckBoxControl", False, "Batch Render (ALL Views)", 5, 0, "Renders all enabled tasks in the Batch Render dialog. Default: Render ALL tasks in Batch Render dialog.", expand=False )
    batchRenderBox.ValueModified.connect(BatchRenderChanged)

    scriptDialog.AddControlToGrid( "BatchRenderNameLabel", "LabelControl", "Batch Render Name", 6, 0, "Allows you to specify a Batch Render Name (optional) present in the 3ds Max scene file.", expand=False )
    batchRenderNameBox = scriptDialog.AddControlToGrid( "BatchRenderNameBox", "TextControl", "", 6, 1, colSpan=2 )
    batchRenderNameBox.ValueModified.connect(BatchRenderNameChanged)

    scriptDialog.AddControlToGrid( "PathConfigLabel", "LabelControl", "Path Config File", 7, 0, "Allows you to specify an alternate path file in the MXP format that the slaves can use to find bitmaps that are not found on the primary map paths.", expand=False )
    scriptDialog.AddSelectionControlToGrid( "PathConfigBox", "FileBrowserControl", "", "Path Configuration Files (*.mxp);;All Files (*)", 7, 1, colSpan=2 )

    StripRenderingBox = scriptDialog.AddSelectionControlToGrid( "StripRenderingBox", "CheckBoxControl", False, "Split Rendering", 8, 0, "Enable Split Rendering.", expand=False )
    StripRenderingBox.ValueModified.connect(StripRenderingChanged)
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "StripCountLabel", "LabelControl", "Strips", 0, 0, "Number of strips (Min: 2).", expand=False )
    scriptDialog.AddRangeControlToGrid( "StripCountBox", "RangeControl", 2, 2, 1000, 0, 1, 0, 1 )
    scriptDialog.AddControlToGrid( "StripOverlapLabel", "LabelControl", "Overlap", 0, 2, "Overlap amount (Default: 0.", expand=False )
    scriptDialog.AddRangeControlToGrid( "StripOverlapBox", "RangeControl", 0, 0, 5000, 0, 1, 0, 3 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "VRay DBR and Mental Ray Satellite", 0, 0 )
    scriptDialog.AddControlToGrid( "DBRLabel", "LabelControl", "Offloads a DBR or Satellite render to Deadline. This requires the VRay DBR or Mental Ray Satellite\nrendering option to be enabled in your 3ds Max scene settings. It also requires that the vray_dr.cfg,\nvrayrt_dr.cfg or max.rayhosts files be writable on the render nodes. See the 3ds Cmd documentation\nfor more information.", 1, 0 )
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

    scriptDialog.AddTabPage("Render Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator6", "SeparatorControl", "Render Parameters", 0, 0 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    overrideResolutionBox = scriptDialog.AddSelectionControlToGrid( "OverrideResolutionBox", "CheckBoxControl", False, "Override Resolution (Leave unchecked to respect scene's resolution settings)", 0, 0, "Enable to override render resolution.", True, 1, 2 )
    overrideResolutionBox.ValueModified.connect(OverrideResolutionChanged)
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "WidthLabel", "LabelControl", "Width", 1, 0, "Sets the output width in pixels.", expand=False )
    scriptDialog.AddRangeControlToGrid( "WidthBox", "RangeControl", 640, 1, 32768, 0, 1, 1, 1 )
    
    scriptDialog.AddControlToGrid( "HeightLabel", "LabelControl", "Height", 1, 2, "Sets the output height in pixels.", expand=False )
    scriptDialog.AddRangeControlToGrid( "HeightBox", "RangeControl", 480, 1, 32768, 0, 1, 1, 3 )
    
    scriptDialog.AddControlToGrid( "PixelAspectLabel", "LabelControl", "Pixel Aspect", 1, 4, "Sets the pixel aspect ratio.", expand=False )
    scriptDialog.AddRangeControlToGrid( "PixelAspectBox", "RangeControl", 1.0, 0.001, 1000.0, 3, 0.001, 1, 5 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddSelectionControlToGrid( "ContinueBox", "CheckBoxControl", True, "Continue on Error", 0, 0, "Enable to have the 3ds command line renderer ignore errors during rendering.", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "LocalRenderingBox", "CheckBoxControl", False, "Enable Local Rendering", 0, 2, "If enabled, the frames will be rendered locally, and then copied to their final network location.", True, 1, 2 )

    scriptDialog.AddSelectionControlToGrid( "StillFrameBox", "CheckBoxControl", False, "Remove Padding (Single Frame Only)", 1, 0, "Indicates that this is a still-frame render; no frame suffix will be added.", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "VideoPostBox", "CheckBoxControl", False, "Apply VideoPost To Scene", 1, 2, "Whether or not to use VideoPost during rendering.", True, 1, 2 )

    scriptDialog.AddControlToGrid( "ImageSequenceFileLabel", "LabelControl", "Image Sequence File Creation", 2, 0, "Image-sequence file creation: 0=none; 1=.imsq; 2=.ifl.", True, 1, 2 )
    scriptDialog.AddComboControlToGrid( "ImageSequenceFileBox", "ComboControl", "none", ("none",".imsq",".ifl"), 2, 2, expand=True )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    gammaBox = scriptDialog.AddSelectionControlToGrid( "GammaCorrectionBox", "CheckBoxControl", False, "Gamma Correction", 2, 0, "Enable to apply gamma correction during rendering.", True, 1, 2 )
    gammaBox.ValueModified.connect(GammaChanged)
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "GammaInputLabel", "LabelControl", "Input Gamma", 5, 0, "The gamma input value.", False )
    scriptDialog.AddRangeControlToGrid( "GammaInputBox", "RangeControl", 1.0, 0.01, 5.0, 2, 0.1, 5, 1 )
    scriptDialog.AddControlToGrid( "GammaOutputLabel", "LabelControl", "Output Gamma", 5, 2, "The gamma output value.", False )
    scriptDialog.AddRangeControlToGrid( "GammaOutputBox", "RangeControl", 1.0, 0.01, 5.0, 2, 0.1, 5, 3 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator6", "SeparatorControl", "Render Flags", 0, 0 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddSelectionControlToGrid( "ShowVfbBox", "CheckBoxControl", True, "Show Rendered Frame Window", 0, 0, "Enable the virtual frame buffer during rendering.", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "SkipRenderedFramesBox", "CheckBoxControl", False, "Skip Rendered Frames", 0, 2, "Toggle skip existing images.", True, 1, 2 )

    scriptDialog.AddSelectionControlToGrid( "ColorCheckBox", "CheckBoxControl", False, "Perform Color Check", 1, 0, "Toggle video Color Check.", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "TwoSidedBox", "CheckBoxControl", False, "Force Two-Sided", 1, 2, "Toggle force 2 sided.", True, 1, 2 )
    
    scriptDialog.AddSelectionControlToGrid( "HiddenGeometryBox", "CheckBoxControl", False, "Render Hidden Objects", 2, 0, "Toggle render hidden.", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "AtmosphericsBox", "CheckBoxControl", False, "Use Atmospherics Effects", 2, 2, "Toggle atmospherics.", True, 1, 2 )
    
    scriptDialog.AddSelectionControlToGrid( "SuperBlackBox", "CheckBoxControl", False, "Use Super Black", 3, 0, "Toggle super black.", True, 1, 2 )
    renderToFieldsBox = scriptDialog.AddSelectionControlToGrid( "RenderToFieldsBox", "CheckBoxControl", False, "Render To Fields", 3, 2, "Toggle render to fields.", True, 1, 2 )
    renderToFieldsBox.ValueModified.connect(RenderToFieldsChanged)

    scriptDialog.AddControlToGrid( "FieldOrderLabel", "LabelControl", "Field Order", 4, 0, "Toggles Field Order.", True, 1, 2 )
    scriptDialog.AddComboControlToGrid( "FieldOrderBox", "ComboControl", "Odd", ("Odd","Even"), 4, 2 )

    scriptDialog.AddSelectionControlToGrid( "ElementsBox", "CheckBoxControl", True, "Output Render Elements", 5, 0, "Output render elements. Must be explicitly enabled for 3ds Max 2013 or earlier to create render elements.", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "DisplacementBox", "CheckBoxControl", False, "Perform Displacement Mapping", 5, 2, "Toggle displacement mapping.", True, 1, 2 )

    scriptDialog.AddSelectionControlToGrid( "EffectsBox", "CheckBoxControl", False, "Perform Render Effects", 6, 0, "Toggle render effects.", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "AreaLightsBox", "CheckBoxControl", False, "Convert Area Lights To Point Sources", 6, 2, "Toggle area lights/shadows.", True, 1, 2 )

    scriptDialog.AddSelectionControlToGrid( "UseAdvLightBox", "CheckBoxControl", False, "Use Advanced Lighting", 7, 0, "Toggles use advanced lighting.", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "ComputeAdvLightBox", "CheckBoxControl", False, "Compute Advanced Lighting", 7, 2, "Toggles compute advanced lighting.", True, 1, 2 )

    scriptDialog.AddSelectionControlToGrid( "DitherPalettedBox", "CheckBoxControl", False, "Toggles Output Dithering (paletted)", 8, 0, "Toggles Output Dithering (paletted).", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "DitherTrueColorBox", "CheckBoxControl", False, "Toggles Output Dithering (true-color)", 8, 2, "Toggles Output Dithering (true-color).", True, 1, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Bitmap Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator7", "SeparatorControl", "Bitmap Parameters", 0, 0 )
    scriptDialog.AddControlToGrid( "BitmapOptionsLabel", "LabelControl", "Here you can OVERRIDE certain Bitmap Options and ignore the equivalent setting in your Max scene file.", 1, 0 )
    scriptDialog.EndGrid()

    scriptDialog.AddGroupBox("GroupBox1", "BMP Options", True).toggled.connect(GroupBox1Toggled)
    scriptDialog.AddGrid()
    
    BMP_TYPE_Enable = scriptDialog.AddSelectionControlToGrid( "BMP_TYPE_EnableBox", "CheckBoxControl", False, "Override BMP_TYPE", 0, 0, "Sets the type of BMP file being rendered. '2'=paletted, '8'=true 24-bit.", colSpan=1 )
    BMP_TYPE_Enable.ValueModified.connect(BMP_TYPE_Changed)
    scriptDialog.AddComboControlToGrid( "BMP_TYPE_Box", "ComboControl", "paletted", ("paletted","true 24-bit"), 0, 1 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox(True)

    scriptDialog.AddGroupBox("GroupBox2", "JPEG Options", True).toggled.connect(GroupBox2Toggled)
    scriptDialog.AddGrid()

    jpgSelectAllButton = scriptDialog.AddControlToGrid( "jpgSelectAllButton", "ButtonControl", "Select All", 0, 0, expand=True )
    jpgSelectAllButton.ValueModified.connect(jpgSelectAllChanged)
    jpgSelectNoneButton = scriptDialog.AddControlToGrid( "jpgSelectNoneButton", "ButtonControl", "Select None", 0, 1, expand=True )
    jpgSelectNoneButton.ValueModified.connect(jpgSelectNoneChanged)
    jpgInvertSelectionButton = scriptDialog.AddControlToGrid( "jpgInvertSelectionButton", "ButtonControl", "Invert Selection", 0, 2, expand=True )
    jpgInvertSelectionButton.ValueModified.connect(jpgInvertSelectionChanged)
    
    JPEG_QUALITY_Enable = scriptDialog.AddSelectionControlToGrid( "JPEG_QUALITY_EnableBox", "CheckBoxControl", False, "Override JPEG_QUALITY", 1, 0, "Sets the JPG quality value. Ranges from 1 to 100.", colSpan=1 )
    JPEG_QUALITY_Enable.ValueModified.connect(JPEG_QUALITY_Changed)
    scriptDialog.AddRangeControlToGrid( "JPEG_QUALITY_Box", "RangeControl", 100, 1, 100, 0, 1, 1, 1 )

    JPEG_SMOOTHING_Enable = scriptDialog.AddSelectionControlToGrid( "JPEG_SMOOTHING_EnableBox", "CheckBoxControl", False, "Override JPEG_SMOOTHING", 2, 0, "Sets the JPG smoothing value. Ranges from 1 to 100.", True, 1, 0 )
    JPEG_SMOOTHING_Enable.ValueModified.connect(JPEG_SMOOTHING_Changed)
    scriptDialog.AddRangeControlToGrid( "JPEG_SMOOTHING_Box", "RangeControl", 100, 1, 100, 0, 1, 2, 1 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox(True)

    scriptDialog.AddGroupBox("GroupBox3", "TGA Options", True).toggled.connect(GroupBox3Toggled)
    scriptDialog.AddGrid()

    tgaSelectAllButton = scriptDialog.AddControlToGrid( "tgaSelectAllButton", "ButtonControl", "Select All", 0, 0, expand=True )
    tgaSelectAllButton.ValueModified.connect(tgaSelectAllChanged)
    tgaSelectNoneButton = scriptDialog.AddControlToGrid( "tgaSelectNoneButton", "ButtonControl", "Select None", 0, 1, expand=True )
    tgaSelectNoneButton.ValueModified.connect(tgaSelectNoneChanged)
    tgaInvertSelectionButton = scriptDialog.AddControlToGrid( "tgaInvertSelectionButton", "ButtonControl", "Invert Selection", 0, 2, expand=True )
    tgaInvertSelectionButton.ValueModified.connect(tgaInvertSelectionChanged)
    
    TARGA_COLORDEPTH_Enable = scriptDialog.AddSelectionControlToGrid( "TARGA_COLORDEPTH_EnableBox", "CheckBoxControl", False, "Override TARGA_COLORDEPTH", 1, 0, "Sets the color depth for TGA files.", True, 1, 0 )
    TARGA_COLORDEPTH_Enable.ValueModified.connect(TARGA_COLORDEPTH_Changed)
    scriptDialog.AddComboControlToGrid( "TARGA_COLORDEPTH_Box", "ComboControl", "32", ("16","24","32"), 1, 1 )

    TARGA_COMPRESSED_Enable = scriptDialog.AddSelectionControlToGrid( "TARGA_COMPRESSED_EnableBox", "CheckBoxControl", False, "Override TARGA_COMPRESSED", 2, 0, "Toggles TGA Compression. “1”=On, “0”=Off.", True, 1, 0 )
    TARGA_COMPRESSED_Enable.ValueModified.connect(TARGA_COMPRESSED_Changed)
    scriptDialog.AddSelectionControlToGrid( "TARGA_COMPRESSED_Box", "CheckBoxControl", False, "Enabled", 2, 1, "", True, 1, 2 )

    TARGA_ALPHASPLIT_Enable = scriptDialog.AddSelectionControlToGrid( "TARGA_ALPHASPLIT_EnableBox", "CheckBoxControl", False, "Override TARGA_ALPHASPLIT", 3, 0, "Toggles TGA Alpha Split. “1”=On, “0”=Off.", True, 1, 0 )
    TARGA_ALPHASPLIT_Enable.ValueModified.connect(TARGA_ALPHASPLIT_Changed)
    scriptDialog.AddSelectionControlToGrid( "TARGA_ALPHASPLIT_Box", "CheckBoxControl", False, "Enabled", 3, 1, "", True, 1, 2 )

    TARGA_PREMULTALPHA_Enable = scriptDialog.AddSelectionControlToGrid( "TARGA_PREMULTALPHA_EnableBox", "CheckBoxControl", False, "Override TARGA_PREMULTALPHA", 4, 0, "Toggles TGA Pre-Multiplied Alpha. “1”=On, “0”=Off.", True, 1, 0 )
    TARGA_PREMULTALPHA_Enable.ValueModified.connect(TARGA_PREMULTALPHA_Changed)
    scriptDialog.AddSelectionControlToGrid( "TARGA_PREMULTALPHA_Box", "CheckBoxControl", False, "Enabled", 4, 1, "", True, 1, 2 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox(True)

    scriptDialog.AddGroupBox("GroupBox4", "TIF Options", True).toggled.connect(GroupBox4Toggled)
    scriptDialog.AddGrid()

    tifSelectAllButton = scriptDialog.AddControlToGrid( "tifSelectAllButton", "ButtonControl", "Select All", 0, 0, expand=True )
    tifSelectAllButton.ValueModified.connect(tifSelectAllChanged)
    tifSelectNoneButton = scriptDialog.AddControlToGrid( "tifSelectNoneButton", "ButtonControl", "Select None", 0, 1, expand=True )
    tifSelectNoneButton.ValueModified.connect(tifSelectNoneChanged)
    tifInvertSelectionButton = scriptDialog.AddControlToGrid( "tifInvertSelectionButton", "ButtonControl", "Invert Selection", 0, 2, expand=True )
    tifInvertSelectionButton.ValueModified.connect(tifInvertSelectionChanged)

    TIF_TYPE_Enable = scriptDialog.AddSelectionControlToGrid( "TIF_TYPE_EnableBox", "CheckBoxControl", False, "Override TIF_TYPE", 1, 0, "Sets the TIF type. “0”=mono, “1”=color, “2”=logl, “3”=logluv, “4”=16-bit color.", True, 1, 0 )
    TIF_TYPE_Enable.ValueModified.connect(TIF_TYPE_Changed)
    scriptDialog.AddComboControlToGrid( "TIF_TYPE_Box", "ComboControl", "16-bit color", ("mono","color","logl","logluv","16-bit color"), 1, 1 )

    TIF_ALPHA_Enable = scriptDialog.AddSelectionControlToGrid( "TIF_ALPHA_EnableBox", "CheckBoxControl", False, "Override TIF_ALPHA", 2, 0, "Toggles TIF file alpha. “1”=On, “0”=Off.", True, 1, 0 )
    TIF_ALPHA_Enable.ValueModified.connect(TIF_ALPHA_Changed)
    scriptDialog.AddSelectionControlToGrid( "TIF_ALPHA_Box", "CheckBoxControl", False, "Enabled", 2, 1, "", True, 1, 2 )

    TIF_COMPRESSION_Enable = scriptDialog.AddSelectionControlToGrid( "TIF_COMPRESSION_EnableBox", "CheckBoxControl", False, "Override TIF_COMPRESSION", 3, 0, "Toggles TIF Compression. “1”=On, “0”=Off.", True, 1, 0 )
    TIF_COMPRESSION_Enable.ValueModified.connect(TIF_COMPRESSION_Changed)
    scriptDialog.AddSelectionControlToGrid( "TIF_COMPRESSION_Box", "CheckBoxControl", False, "Enabled", 3, 1, "", True, 1, 2 )

    TIF_DPI_Enable = scriptDialog.AddSelectionControlToGrid( "TIF_DPI_EnableBox", "CheckBoxControl", False, "Override TIF_DPI", 4, 0, "Sets the dots-per-inch value for TIF files.", colSpan=1 )
    TIF_DPI_Enable.ValueModified.connect(TIF_DPI_Changed)
    scriptDialog.AddRangeControlToGrid( "TIF_DPI_Box", "RangeControl", 200, 72, 999, 0, 1, 4, 1 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox(True)

    scriptDialog.AddGroupBox("GroupBox5", "RLA Options", True).toggled.connect(GroupBox5Toggled)
    scriptDialog.AddGrid()

    rlaSelectAllButton = scriptDialog.AddControlToGrid( "rlaSelectAllButton", "ButtonControl", "Select All", 0, 0, expand=True )
    rlaSelectAllButton.ValueModified.connect(rlaSelectAllChanged)
    rlaSelectNoneButton = scriptDialog.AddControlToGrid( "rlaSelectNoneButton", "ButtonControl", "Select None", 0, 1, expand=True )
    rlaSelectNoneButton.ValueModified.connect(rlaSelectNoneChanged)
    rlaInvertSelectionButton = scriptDialog.AddControlToGrid( "rlaInvertSelectionButton", "ButtonControl", "Invert Selection", 0, 2, expand=True )
    rlaInvertSelectionButton.ValueModified.connect(rlaInvertSelectionChanged)

    RLA_COLORDEPTH_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_COLORDEPTH_EnableBox", "CheckBoxControl", False, "Override RLA_COLORDEPTH", 1, 0, "Sets the RLA color bitdepth.", colSpan=1 )
    RLA_COLORDEPTH_Enable.ValueModified.connect(RLA_COLORDEPTH_Changed)
    scriptDialog.AddComboControlToGrid( "RLA_COLORDEPTH_Box", "ComboControl", "32", ("8","16","32"), 1, 1 )

    RLA_ALPHA_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_ALPHA_EnableBox", "CheckBoxControl", False, "Override RLA_ALPHA", 2, 0, "Toggles RLA Alpha. “1”=On, “0”=Off.", colSpan=1 )
    RLA_ALPHA_Enable.ValueModified.connect(RLA_ALPHA_Changed)
    scriptDialog.AddSelectionControlToGrid( "RLA_ALPHA_Box", "CheckBoxControl", False, "Enabled", 2, 1, "", True, 1, 2 )

    RLA_PREMULTALPHA_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_PREMULTALPHA_EnableBox", "CheckBoxControl", False, "Override RLA_PREMULTALPHA", 3, 0, "Toggles RLA Premultiplied Alpha. “1”=On, “0”=Off.", colSpan=1 )
    RLA_PREMULTALPHA_Enable.ValueModified.connect(RLA_PREMULTALPHA_Changed)
    scriptDialog.AddSelectionControlToGrid( "RLA_PREMULTALPHA_Box", "CheckBoxControl", False, "Enabled", 3, 1, "", True, 1, 2 )

    RLA_DESCRIPTION_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_DESCRIPTION_EnableBox", "CheckBoxControl", False, "Override RLA_DESCRIPTION", 4, 0, "Lets you specify an RLA description.", colSpan=1 )
    RLA_DESCRIPTION_Enable.ValueModified.connect(RLA_DESCRIPTION_Changed)
    scriptDialog.AddControlToGrid( "RLA_DESCRIPTION_Box", "TextControl", "", 4, 1, colSpan=2 )

    RLA_AUTHOR_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_AUTHOR_EnableBox", "CheckBoxControl", False, "Override RLA_AUTHOR", 5, 0, "Lets you specify an RLA author name.", colSpan=1 )
    RLA_AUTHOR_Enable.ValueModified.connect(RLA_AUTHOR_Changed)
    scriptDialog.AddControlToGrid( "RLA_AUTHOR_Box", "TextControl", "", 5, 1, colSpan=2 )

    RLA_ZDEPTHCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_ZDEPTHCHANNEL_EnableBox", "CheckBoxControl", False, "Override RLA_ZDEPTHCHANNEL", 6, 0, "Toggles RLA Z-Depth Channel. “1”=On, “0”=Off.", colSpan=1 )
    RLA_ZDEPTHCHANNEL_Enable.ValueModified.connect(RLA_ZDEPTHCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RLA_ZDEPTHCHANNEL_Box", "CheckBoxControl", False, "Enabled", 6, 1, "", True, 1, 2 )

    RLA_MTLIDCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_MTLIDCHANNEL_EnableBox", "CheckBoxControl", False, "Override RLA_MTLIDCHANNEL", 7, 0, "Toggles RLA Material ID Channel. “1”=On, “0”=Off.", colSpan=1 )
    RLA_MTLIDCHANNEL_Enable.ValueModified.connect(RLA_MTLIDCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RLA_MTLIDCHANNEL_Box", "CheckBoxControl", False, "Enabled", 7, 1, "", True, 1, 2 )

    RLA_OBJECTIDCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_OBJECTIDCHANNEL_EnableBox", "CheckBoxControl", False, "Override RLA_OBJECTIDCHANNEL", 8, 0, "Toggles RLA Object Channel. “1”=On, “0”=Off.", colSpan=1 )
    RLA_OBJECTIDCHANNEL_Enable.ValueModified.connect(RLA_OBJECTIDCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RLA_OBJECTIDCHANNEL_Box", "CheckBoxControl", False, "Enabled", 8, 1, "", True, 1, 2 )

    RLA_UVCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_UVCHANNEL_EnableBox", "CheckBoxControl", False, "Override RLA_UVCHANNEL", 9, 0, "Toggles RLA UV Coordinates Channel. “1”=On, “0”=Off.", colSpan=1 )
    RLA_UVCHANNEL_Enable.ValueModified.connect(RLA_UVCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RLA_UVCHANNEL_Box", "CheckBoxControl", False, "Enabled", 9, 1, "", True, 1, 2 )

    RLA_NORMALCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_NORMALCHANNEL_EnableBox", "CheckBoxControl", False, "Override RLA_NORMALCHANNEL", 10, 0, "Toggles RLA Surface Normals Channel. “1”=On, “0”=Off.", colSpan=1 )
    RLA_NORMALCHANNEL_Enable.ValueModified.connect(RLA_NORMALCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RLA_NORMALCHANNEL_Box", "CheckBoxControl", False, "Enabled", 10, 1, "", True, 1, 2 )

    RLA_NONCLAMPEDCOLORCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_NONCLAMPEDCOLORCHANNEL_EnableBox", "CheckBoxControl", False, "Override RLA_NONCLAMPEDCOLORCHANNEL", 11, 0, "Toggles RLA Non-Clamped Color Channel. “1”=On, “0”=Off.", colSpan=1 )
    RLA_NONCLAMPEDCOLORCHANNEL_Enable.ValueModified.connect(RLA_NONCLAMPEDCOLORCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RLA_NONCLAMPEDCOLORCHANNEL_Box", "CheckBoxControl", False, "Enabled", 11, 1, "", True, 1, 2 )

    RLA_COVERAGECHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RLA_COVERAGECHANNEL_EnableBox", "CheckBoxControl", False, "Override RLA_COVERAGECHANNEL", 12, 0, "Toggles RLA Coverage Channel. “1”=On, “0”=Off.", colSpan=1 )
    RLA_COVERAGECHANNEL_Enable.ValueModified.connect(RLA_COVERAGECHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RLA_COVERAGECHANNEL_Box", "CheckBoxControl", False, "Enabled", 12, 1, "", True, 1, 2 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox(True)

    scriptDialog.AddGroupBox("GroupBox6", "RPF Options", True).toggled.connect(GroupBox6Toggled)
    scriptDialog.AddGrid()

    rpfSelectAllButton = scriptDialog.AddControlToGrid( "rpfSelectAllButton", "ButtonControl", "Select All", 0, 0, expand=True )
    rpfSelectAllButton.ValueModified.connect(rpfSelectAllChanged)
    rpfSelectNoneButton = scriptDialog.AddControlToGrid( "rpfSelectNoneButton", "ButtonControl", "Select None", 0, 1, expand=True )
    rpfSelectNoneButton.ValueModified.connect(rpfSelectNoneChanged)
    rpfInvertSelectionButton = scriptDialog.AddControlToGrid( "rpfInvertSelectionButton", "ButtonControl", "Invert Selection", 0, 2, expand=True )
    rpfInvertSelectionButton.ValueModified.connect(rpfInvertSelectionChanged)

    RPF_COLORDEPTH_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_COLORDEPTH_EnableBox", "CheckBoxControl", False, "Override RPF_COLORDEPTH", 1, 0, "Sets the RPF color bitdepth.", colSpan=1 )
    RPF_COLORDEPTH_Enable.ValueModified.connect(RPF_COLORDEPTH_Changed)
    scriptDialog.AddComboControlToGrid( "RPF_COLORDEPTH_Box", "ComboControl", "32", ("8","16","32"), 1, 1 )

    RPF_ALPHA_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_ALPHA_EnableBox", "CheckBoxControl", False, "Override RPF_ALPHA", 2, 0, "Toggles RPF Alpha. “1”=On, “0”=Off.", colSpan=1 )
    RPF_ALPHA_Enable.ValueModified.connect(RPF_ALPHA_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_ALPHA_Box", "CheckBoxControl", False, "Enabled", 2, 1, "", True, 1, 2 )

    RPF_PREMULTALPHA_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_PREMULTALPHA_EnableBox", "CheckBoxControl", False, "Override RPF_PREMULTALPHA", 3, 0, "Toggles RPF Premultiplied Alpha. “1”=On, “0”=Off.", colSpan=1 )
    RPF_PREMULTALPHA_Enable.ValueModified.connect(RPF_PREMULTALPHA_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_PREMULTALPHA_Box", "CheckBoxControl", False, "Enabled", 3, 1, "", True, 1, 2 )

    RPF_DESCRIPTION_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_DESCRIPTION_EnableBox", "CheckBoxControl", False, "Override RPF_DESCRIPTION", 4, 0, "Lets you specify an RPF description.", colSpan=1 )
    RPF_DESCRIPTION_Enable.ValueModified.connect(RPF_DESCRIPTION_Changed)
    scriptDialog.AddControlToGrid( "RPF_DESCRIPTION_Box", "TextControl", "", 4, 1, colSpan=2 )

    RPF_AUTHOR_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_AUTHOR_EnableBox", "CheckBoxControl", False, "Override RPF_AUTHOR", 5, 0, "Lets you specify an RPF author name.", colSpan=1 )
    RPF_AUTHOR_Enable.ValueModified.connect(RPF_AUTHOR_Changed)
    scriptDialog.AddControlToGrid( "RPF_AUTHOR_Box", "TextControl", "", 5, 1, colSpan=2 )

    RPF_ZDEPTHCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_ZDEPTHCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_ZDEPTHCHANNEL", 6, 0, "Toggles RPF Z-Depth Channel. “1”=On, “0”=Off.", colSpan=1 )
    RPF_ZDEPTHCHANNEL_Enable.ValueModified.connect(RPF_ZDEPTHCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_ZDEPTHCHANNEL_Box", "CheckBoxControl", False, "Enabled", 6, 1, "", True, 1, 2 )

    RPF_MTLIDCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_MTLIDCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_MTLIDCHANNEL", 7, 0, "Toggles RPF Material ID Channel. “1”=On, “0”=Off.", colSpan=1 )
    RPF_MTLIDCHANNEL_Enable.ValueModified.connect(RPF_MTLIDCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_MTLIDCHANNEL_Box", "CheckBoxControl", False, "Enabled", 7, 1, "", True, 1, 2 )

    RPF_OBJECTIDCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_OBJECTIDCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_OBJECTIDCHANNEL", 8, 0, "Toggles RPF Object Channel. “1”=On, “0”=Off.", colSpan=1 )
    RPF_OBJECTIDCHANNEL_Enable.ValueModified.connect(RPF_OBJECTIDCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_OBJECTIDCHANNEL_Box", "CheckBoxControl", False, "Enabled", 8, 1, "", True, 1, 2 )

    RPF_UVCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_UVCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_UVCHANNEL", 9, 0, "Toggles RPF UV Coordinates Channel. “1”=On, “0”=Off.", colSpan=1 )
    RPF_UVCHANNEL_Enable.ValueModified.connect(RPF_UVCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_UVCHANNEL_Box", "CheckBoxControl", False, "Enabled", 9, 1, "", True, 1, 2 )

    RPF_NORMALCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_NORMALCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_NORMALCHANNEL", 10, 0, "Toggles RPF Surface Normals Channel. “1”=On, “0”=Off.", colSpan=1 )
    RPF_NORMALCHANNEL_Enable.ValueModified.connect(RPF_NORMALCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_NORMALCHANNEL_Box", "CheckBoxControl", False, "Enabled", 10, 1, "", True, 1, 2 )

    RPF_NONCLAMPEDCOLORCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_NONCLAMPEDCOLORCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_NONCLAMPEDCOLORCHANNEL", 11, 0, "Toggles RPF Non-Clamped Color Channel. “1”=On, “0”=Off.", colSpan=1 )
    RPF_NONCLAMPEDCOLORCHANNEL_Enable.ValueModified.connect(RPF_NONCLAMPEDCOLORCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_NONCLAMPEDCOLORCHANNEL_Box", "CheckBoxControl", False, "Enabled", 11, 1, "", True, 1, 2 )

    RPF_COVERAGECHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_COVERAGECHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_COVERAGECHANNEL", 12, 0, "Toggles RPF Coverage Channel. “1”=On, “0”=Off.", colSpan=1 )
    RPF_COVERAGECHANNEL_Enable.ValueModified.connect(RPF_COVERAGECHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_COVERAGECHANNEL_Box", "CheckBoxControl", False, "Enabled", 12, 1, "", True, 1, 2 )

    RPF_NODERENDERIDCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_NODERENDERIDCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_NODERENDERIDCHANNEL", 13, 0, "Turns on RPF Node Render ID Channel.", colSpan=1 )
    RPF_NODERENDERIDCHANNEL_Enable.ValueModified.connect(RPF_NODERENDERIDCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_NODERENDERIDCHANNEL_Box", "CheckBoxControl", False, "Enabled", 13, 1, "", True, 1, 2 )

    RPF_COLORCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_COLORCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_COLORCHANNEL", 14, 0, "Turns on RPF Color Channel.", colSpan=1 )
    RPF_COLORCHANNEL_Enable.ValueModified.connect(RPF_COLORCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_COLORCHANNEL_Box", "CheckBoxControl", False, "Enabled", 14, 1, "", True, 1, 2 )

    RPF_TRANSPCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_TRANSPCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_TRANSPCHANNEL", 15, 0, "Turns on RPF Transparency Channel.", colSpan=1 )
    RPF_TRANSPCHANNEL_Enable.ValueModified.connect(RPF_TRANSPCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_TRANSPCHANNEL_Box", "CheckBoxControl", False, "Enabled", 15, 1, "", True, 1, 2 )

    RPF_VELOCCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_VELOCCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_VELOCCHANNEL", 16, 0, "Turns on RPF Velocity Channel.", colSpan=1 )
    RPF_VELOCCHANNEL_Enable.ValueModified.connect(RPF_VELOCCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_VELOCCHANNEL_Box", "CheckBoxControl", False, "Enabled", 16, 1, "", True, 1, 2 )

    RPF_WEIGHTCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_WEIGHTCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_WEIGHTCHANNEL", 17, 0, "Turns on RPF Sub-Pixel Weight Channel.", colSpan=1 )
    RPF_WEIGHTCHANNEL_Enable.ValueModified.connect(RPF_WEIGHTCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_WEIGHTCHANNEL_Box", "CheckBoxControl", False, "Enabled", 17, 1, "", True, 1, 2 )

    RPF_MASKCHANNEL_Enable = scriptDialog.AddSelectionControlToGrid( "RPF_MASKCHANNEL_EnableBox", "CheckBoxControl", False, "Override RPF_MASKCHANNEL", 18, 0, "Turns on RPF Sub-Pixel Mask Channel.", colSpan=1 )
    RPF_MASKCHANNEL_Enable.ValueModified.connect(RPF_MASKCHANNEL_Changed)
    scriptDialog.AddSelectionControlToGrid( "RPF_MASKCHANNEL_Box", "CheckBoxControl", False, "Enabled", 18, 1, "", True, 1, 2 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox(True)

    scriptDialog.AddGroupBox("GroupBox7", "EXR Options", True).toggled.connect(GroupBox7Toggled)
    scriptDialog.AddGrid()

    exrSelectAllButton = scriptDialog.AddControlToGrid( "exrSelectAllButton", "ButtonControl", "Select All", 0, 0, expand=True )
    exrSelectAllButton.ValueModified.connect(exrSelectAllChanged)
    exrSelectNoneButton = scriptDialog.AddControlToGrid( "exrSelectNoneButton", "ButtonControl", "Select None", 0, 1, expand=True )
    exrSelectNoneButton.ValueModified.connect(exrSelectNoneChanged)
    exrInvertSelectionButton = scriptDialog.AddControlToGrid( "exrInvertSelectionButton", "ButtonControl", "Invert Selection", 0, 2, expand=True )
    exrInvertSelectionButton.ValueModified.connect(exrInvertSelectionChanged)

    EXR_USEEXPONENT_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_USEEXPONENT_EnableBox", "CheckBoxControl", False, "Override EXR_USEEXPONENT", 1, 0, "EXR use exponent on/off.", colSpan=1 )
    EXR_USEEXPONENT_Enable.ValueModified.connect(EXR_USEEXPONENT_Changed)
    scriptDialog.AddSelectionControlToGrid( "EXR_USEEXPONENT_Box", "CheckBoxControl", False, "Enabled", 1, 1, "", True, 1, 2 )

    EXR_EXPONENT_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_EXPONENT_EnableBox", "CheckBoxControl", False, "Override EXR_EXPONENT", 2, 0, "EXR exponent value (decimal).", colSpan=1 )
    EXR_EXPONENT_Enable.ValueModified.connect(EXR_EXPONENT_Changed)
    scriptDialog.AddRangeControlToGrid( "EXR_EXPONENT_Box", "RangeControl", 1.0, 0, 9999, 1, 1, 2, 1 )

    EXR_PREMULTALPHA_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_PREMULTALPHA_EnableBox", "CheckBoxControl", False, "Override EXR_PREMULTALPHA", 3, 0, "EXR premultiplied alpha on/off.", colSpan=1 )
    EXR_PREMULTALPHA_Enable.ValueModified.connect(EXR_PREMULTALPHA_Changed)
    scriptDialog.AddSelectionControlToGrid( "EXR_PREMULTALPHA_Box", "CheckBoxControl", False, "Enabled", 3, 1, "", True, 1, 2 )

    EXR_ALPHA_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_ALPHA_EnableBox", "CheckBoxControl", False, "Override EXR_ALPHA", 4, 0, "EXR save alpha component on/off.", colSpan=1 )
    EXR_ALPHA_Enable.ValueModified.connect(EXR_ALPHA_Changed)
    scriptDialog.AddSelectionControlToGrid( "EXR_ALPHA_Box", "CheckBoxControl", False, "Enabled", 4, 1, "", True, 1, 2 )

    EXR_RED_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_RED_EnableBox", "CheckBoxControl", False, "Override EXR_RED", 5, 0, "EXR save red component on/off.", colSpan=1 )
    EXR_RED_Enable.ValueModified.connect(EXR_RED_Changed)
    scriptDialog.AddSelectionControlToGrid( "EXR_RED_Box", "CheckBoxControl", False, "Enabled", 5, 1, "", True, 1, 2 )

    EXR_GREEN_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_GREEN_EnableBox", "CheckBoxControl", False, "Override EXR_GREEN", 6, 0, "EXR save green component on/off.", colSpan=1 )
    EXR_GREEN_Enable.ValueModified.connect(EXR_GREEN_Changed)
    scriptDialog.AddSelectionControlToGrid( "EXR_GREEN_Box", "CheckBoxControl", False, "Enabled", 6, 1, "", True, 1, 2 )

    EXR_BLUE_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_BLUE_EnableBox", "CheckBoxControl", False, "Override EXR_BLUE", 7, 0, "EXR save blue component on/off.", colSpan=1 )
    EXR_BLUE_Enable.ValueModified.connect(EXR_BLUE_Changed)
    scriptDialog.AddSelectionControlToGrid( "EXR_BLUE_Box", "CheckBoxControl", False, "Enabled", 7, 1, "", True, 1, 2 )

    EXR_BITDEPTH_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_BITDEPTH_EnableBox", "CheckBoxControl", False, "Override EXR_BITDEPTH", 8, 0, "EXR bit depth: 0=8-bit integers; 1=half float; 2=float.", colSpan=1 )
    EXR_BITDEPTH_Enable.ValueModified.connect(EXR_BITDEPTH_Changed)
    scriptDialog.AddComboControlToGrid( "EXR_BITDEPTH_Box", "ComboControl", "float", ("8-bit integers","half float","float"), 8, 1 )

    EXR_USEFRAMENUMDIGITS_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_USEFRAMENUMDIGITS_EnableBox", "CheckBoxControl", False, "Override EXR_USEFRAMENUMDIGITS", 9, 0, "EXR use number of frame digits on/off.", colSpan=1 )
    EXR_USEFRAMENUMDIGITS_Enable.ValueModified.connect(EXR_USEFRAMENUMDIGITS_Changed)
    scriptDialog.AddSelectionControlToGrid( "EXR_USEFRAMENUMDIGITS_Box", "CheckBoxControl", False, "Enabled", 9, 1, "", True, 1, 2 )

    EXR_FRAMENUMDIGITS_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_FRAMENUMDIGITS_EnableBox", "CheckBoxControl", False, "Override EXR_FRAMENUMDIGITS", 10, 0, "EXR number of frame digits (integer).", colSpan=1 )
    EXR_FRAMENUMDIGITS_Enable.ValueModified.connect(EXR_FRAMENUMDIGITS_Changed)
    scriptDialog.AddRangeControlToGrid( "EXR_FRAMENUMDIGITS_Box", "RangeControl", 4, 4, 99, 0, 1, 10, 1 )

    EXR_COMPRESSIONTYPE_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_COMPRESSIONTYPE_EnableBox", "CheckBoxControl", False, "Override EXR_COMPRESSIONTYPE", 11, 0, "EXR compression type: 0=no compression; 1=RLE; 2=ZIP (1 scanline); 3=ZIP (16 scanlines); 4=PIZ.", colSpan=1 )
    EXR_COMPRESSIONTYPE_Enable.ValueModified.connect(EXR_COMPRESSIONTYPE_Changed)
    scriptDialog.AddComboControlToGrid( "EXR_COMPRESSIONTYPE_Box", "ComboControl", "ZIP (1 scanline)", ("no compression","RLE","ZIP (1 scanline)","ZIP (16 scanlines)","PIZ"), 11, 1 )

    EXR_USEREALPIX_Enable = scriptDialog.AddSelectionControlToGrid( "EXR_USEREALPIX_EnableBox", "CheckBoxControl", False, "Override EXR_USEREALPIX", 12, 0, "EXR use RealPix RGB data on/off.", colSpan=1 )
    EXR_USEREALPIX_Enable.ValueModified.connect(EXR_USEREALPIX_Changed)
    scriptDialog.AddSelectionControlToGrid( "EXR_USEREALPIX_Box", "CheckBoxControl", False, "Enabled", 12, 1, "", True, 1, 2 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox(True)
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "3dsCommandMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    # Add Project Management and Draft Tabs
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer2", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(CloseButtonPressed)
    scriptDialog.EndGrid()
    
    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox",
    "LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","IsMaxDesignBox","VersionBox","BuildBox","OutputBox","SubmitSceneBox","CameraBox","RenderPresetBox","PreRenderScriptBox",
    "PostRenderScriptBox","SceneStateBox","BatchRenderBox","BatchRenderNameBox","PathConfigBox","StripRenderingBox","StripCountBox","StripOverlapBox","DBRModeBox",
    "DBRServersBox","OverrideResolutionBox","WidthBox","HeightBox","PixelAspectBox","ContinueBox","LocalRenderingBox","StillFrameBox","VideoPostBox","ImageSequenceFileBox",
    "GammaCorrectionBox","GammaInputBox","GammaOutputBox","ShowVfbBox","SkipRenderedFramesBox","ColorCheckBox","TwoSidedBox","HiddenGeometryBox","AtmosphericsBox","SuperBlackBox",
    "RenderToFieldsBox","ElementsBox","DisplacementBox","EffectsBox","AreaLightsBox","UseAdvLightBox","ComputeAdvLightBox","DitherPalettedBox","DitherTrueColorBox",
    "FieldOrderBox" )

    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    FramesChanged()
    VersionChanged()
    BatchRenderChanged()
    BatchRenderNameChanged()
    StripRenderingChanged()
    OverrideResolutionChanged()
    GammaChanged()
    RenderToFieldsChanged()
    GPUsPerTaskChanged()
    GPUsSelectDevicesChanged()
    DBRModeChanged()

    # Bitmap Options
    BMP_TYPE_Changed()
    
    JPEG_QUALITY_Changed()
    JPEG_SMOOTHING_Changed()
    
    TARGA_COLORDEPTH_Changed()
    TARGA_COMPRESSED_Changed()
    TARGA_ALPHASPLIT_Changed()
    TARGA_PREMULTALPHA_Changed()
    
    TIF_TYPE_Changed()
    TIF_ALPHA_Changed()
    TIF_COMPRESSION_Changed()
    TIF_DPI_Changed()

    RLA_COLORDEPTH_Changed()
    RLA_ALPHA_Changed()
    RLA_PREMULTALPHA_Changed()
    RLA_DESCRIPTION_Changed()
    RLA_AUTHOR_Changed()
    RLA_ZDEPTHCHANNEL_Changed()
    RLA_MTLIDCHANNEL_Changed()
    RLA_OBJECTIDCHANNEL_Changed()
    RLA_UVCHANNEL_Changed()
    RLA_NORMALCHANNEL_Changed()
    RLA_NONCLAMPEDCOLORCHANNEL_Changed()
    RLA_COVERAGECHANNEL_Changed()

    RPF_COLORDEPTH_Changed()
    RPF_ALPHA_Changed()
    RPF_PREMULTALPHA_Changed()
    RPF_DESCRIPTION_Changed()
    RPF_AUTHOR_Changed()
    RPF_ZDEPTHCHANNEL_Changed()
    RPF_MTLIDCHANNEL_Changed()
    RPF_OBJECTIDCHANNEL_Changed()
    RPF_UVCHANNEL_Changed()
    RPF_NORMALCHANNEL_Changed()
    RPF_NONCLAMPEDCOLORCHANNEL_Changed()
    RPF_COVERAGECHANNEL_Changed()

    RPF_NODERENDERIDCHANNEL_Changed()
    RPF_COLORCHANNEL_Changed()
    RPF_TRANSPCHANNEL_Changed()
    RPF_VELOCCHANNEL_Changed()
    RPF_WEIGHTCHANNEL_Changed()
    RPF_MASKCHANNEL_Changed()

    EXR_USEEXPONENT_Changed()
    EXR_EXPONENT_Changed()
    EXR_PREMULTALPHA_Changed()
    EXR_ALPHA_Changed()
    EXR_RED_Changed()
    EXR_GREEN_Changed()
    EXR_BLUE_Changed()
    EXR_BITDEPTH_Changed()
    EXR_USEFRAMENUMDIGITS_Changed()
    EXR_FRAMENUMDIGITS_Changed()
    EXR_COMPRESSIONTYPE_Changed()
    EXR_USEREALPIX_Changed()
    
    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "3dsCommandSettings.ini" )

def ToggleOtherLoadGroupBoxes(name):
    if name != "GroupBox1":
        scriptDialog.SetCollapsed("GroupBox1", True)
    if name != "GroupBox2":
        scriptDialog.SetCollapsed("GroupBox2", True)
    if name != "GroupBox3":
        scriptDialog.SetCollapsed("GroupBox3", True)
    if name != "GroupBox4":
        scriptDialog.SetCollapsed("GroupBox4", True)
    if name != "GroupBox5":
        scriptDialog.SetCollapsed("GroupBox5", True)
    if name != "GroupBox6":
        scriptDialog.SetCollapsed("GroupBox6", True)
    if name != "GroupBox7":
        scriptDialog.SetCollapsed("GroupBox7", True)

def GroupBox1Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBox1")

def GroupBox2Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBox2")
        
def GroupBox3Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBox3")
        
def GroupBox4Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBox4")
        
def GroupBox5Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBox5")
        
def GroupBox6Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBox6")

def GroupBox7Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBox7")
 
def CloseDialog():
    global scriptDialog
    global settings
    scriptDialog.SaveSettings( GetSettingsFilename(), settings )
    scriptDialog.CloseDialog()

def VersionChanged( *args ):
    global scriptDialog
    
    version = int(scriptDialog.GetValue( "VersionBox" ))
    scriptDialog.SetEnabled( "IsMaxDesignBox", 2010 <= version <= 2015 )
    
    buildEnabled = version < 2014
    scriptDialog.SetEnabled( "BuildLabel", buildEnabled )
    scriptDialog.SetEnabled( "BuildBox", buildEnabled )

def FramesChanged( *args ):
    global scriptDialog
    frames = scriptDialog.GetValue( "FramesBox" )
    if frames != "" and FrameUtils.FrameRangeValid( frames ):
        frameArray = FrameUtils.Parse( frames )
        if len(frameArray) == 1:
            scriptDialog.SetEnabled( "StillFrameBox", True )
            scriptDialog.SetEnabled( "ImageSequenceFileLabel", False )
            scriptDialog.SetEnabled( "ImageSequenceFileBox", False )
        else:
            scriptDialog.SetEnabled( "StillFrameBox", False )
            scriptDialog.SetEnabled( "ImageSequenceFileLabel", True )
            scriptDialog.SetEnabled( "ImageSequenceFileBox", True )
    else:
        scriptDialog.SetEnabled( "StillFrameBox", False )
        scriptDialog.SetEnabled( "ImageSequenceFileLabel", False )
        scriptDialog.SetEnabled( "ImageSequenceFileBox", False )

def BatchRenderChanged( *args ):
    global scriptDialog
    batchRender = scriptDialog.GetValue( "BatchRenderBox" )
    scriptDialog.SetEnabled( "BatchRenderNameLabel", (not batchRender) )
    scriptDialog.SetEnabled( "BatchRenderNameBox", (not batchRender) )

def BatchRenderNameChanged( *args ):
    global scriptDialog
    batchRenderName = scriptDialog.GetValue( "BatchRenderNameBox" )
    scriptDialog.SetEnabled( "BatchRenderBox", (batchRenderName == "") )

def StripRenderingChanged( *args ):
    global scriptDialog
    stripRender = scriptDialog.GetValue( "StripRenderingBox" )
    scriptDialog.SetEnabled( "StripCountLabel", stripRender )
    scriptDialog.SetEnabled( "StripCountBox", stripRender )
    scriptDialog.SetEnabled( "StripOverlapLabel", stripRender )
    scriptDialog.SetEnabled( "StripOverlapBox", stripRender )

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

def OverrideResolutionChanged( *args ):
    global scriptDialog
    overrideResolution = scriptDialog.GetValue( "OverrideResolutionBox" )
    scriptDialog.SetEnabled( "WidthLabel", overrideResolution )
    scriptDialog.SetEnabled( "WidthBox", overrideResolution )
    scriptDialog.SetEnabled( "HeightLabel", overrideResolution )
    scriptDialog.SetEnabled( "HeightBox", overrideResolution )
    scriptDialog.SetEnabled( "PixelAspectLabel", overrideResolution )
    scriptDialog.SetEnabled( "PixelAspectBox", overrideResolution )

def GammaChanged( *args ):
    global scriptDialog
    gammaCorrection = scriptDialog.GetValue( "GammaCorrectionBox" )
    scriptDialog.SetEnabled( "GammaInputLabel", gammaCorrection )
    scriptDialog.SetEnabled( "GammaInputBox", gammaCorrection )
    scriptDialog.SetEnabled( "GammaOutputLabel", gammaCorrection )
    scriptDialog.SetEnabled( "GammaOutputBox", gammaCorrection )

def RenderToFieldsChanged( *args ):
    global scriptDialog
    renderToFields = scriptDialog.GetValue( "RenderToFieldsBox" )
    scriptDialog.SetEnabled( "FieldOrderLabel", renderToFields )
    scriptDialog.SetEnabled( "FieldOrderBox", renderToFields )

def BMP_TYPE_Changed( *args ):
    global scriptDialog
    BMP_TYPE = scriptDialog.GetValue( "BMP_TYPE_EnableBox" )
    scriptDialog.SetEnabled( "BMP_TYPE_Box", BMP_TYPE )

def jpgSelectAllChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "JPEG_QUALITY_EnableBox", True )
    scriptDialog.SetValue( "JPEG_SMOOTHING_EnableBox", True )

def jpgSelectNoneChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "JPEG_QUALITY_EnableBox", False )
    scriptDialog.SetValue( "JPEG_SMOOTHING_EnableBox", False )

def jpgInvertSelectionChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "JPEG_QUALITY_EnableBox", not (scriptDialog.GetValue("JPEG_QUALITY_EnableBox") ) )
    scriptDialog.SetValue( "JPEG_SMOOTHING_EnableBox", not (scriptDialog.GetValue("JPEG_SMOOTHING_EnableBox") ) )

def JPEG_QUALITY_Changed( *args ):
    global scriptDialog
    JPEG_QUALITY = scriptDialog.GetValue( "JPEG_QUALITY_EnableBox" )
    scriptDialog.SetEnabled( "JPEG_QUALITY_Box", JPEG_QUALITY )

def JPEG_SMOOTHING_Changed( *args ):
    global scriptDialog
    JPEG_SMOOTHING = scriptDialog.GetValue( "JPEG_SMOOTHING_EnableBox" )
    scriptDialog.SetEnabled( "JPEG_SMOOTHING_Box", JPEG_SMOOTHING )

def tgaSelectAllChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "TARGA_COLORDEPTH_EnableBox", True )
    scriptDialog.SetValue( "TARGA_COMPRESSED_EnableBox", True )
    scriptDialog.SetValue( "TARGA_ALPHASPLIT_EnableBox", True )
    scriptDialog.SetValue( "TARGA_PREMULTALPHA_EnableBox", True )

def tgaSelectNoneChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "TARGA_COLORDEPTH_EnableBox", False )
    scriptDialog.SetValue( "TARGA_COMPRESSED_EnableBox", False )
    scriptDialog.SetValue( "TARGA_ALPHASPLIT_EnableBox", False )
    scriptDialog.SetValue( "TARGA_PREMULTALPHA_EnableBox", False )

def tgaInvertSelectionChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "TARGA_COLORDEPTH_EnableBox", not (scriptDialog.GetValue("TARGA_COLORDEPTH_EnableBox") ) )
    scriptDialog.SetValue( "TARGA_COMPRESSED_EnableBox", not (scriptDialog.GetValue("TARGA_COMPRESSED_EnableBox") ) )
    scriptDialog.SetValue( "TARGA_ALPHASPLIT_EnableBox", not (scriptDialog.GetValue("TARGA_ALPHASPLIT_EnableBox") ) )
    scriptDialog.SetValue( "TARGA_PREMULTALPHA_EnableBox", not (scriptDialog.GetValue("TARGA_PREMULTALPHA_EnableBox") ) )

def TARGA_COLORDEPTH_Changed( *args ):
    global scriptDialog
    TARGA_COLORDEPTH = scriptDialog.GetValue( "TARGA_COLORDEPTH_EnableBox" )
    scriptDialog.SetEnabled( "TARGA_COLORDEPTH_Box", TARGA_COLORDEPTH )

def TARGA_COMPRESSED_Changed( *args ):
    global scriptDialog
    TARGA_COMPRESSED = scriptDialog.GetValue( "TARGA_COMPRESSED_EnableBox" )
    scriptDialog.SetEnabled( "TARGA_COMPRESSED_Box", TARGA_COMPRESSED )

def TARGA_ALPHASPLIT_Changed( *args ):
    global scriptDialog
    TARGA_ALPHASPLIT = scriptDialog.GetValue( "TARGA_ALPHASPLIT_EnableBox" )
    scriptDialog.SetEnabled( "TARGA_ALPHASPLIT_Box", TARGA_ALPHASPLIT )

def TARGA_PREMULTALPHA_Changed( *args ):
    global scriptDialog
    TARGA_PREMULTALPHA = scriptDialog.GetValue("TARGA_PREMULTALPHA_EnableBox" )
    scriptDialog.SetEnabled( "TARGA_PREMULTALPHA_Box", TARGA_PREMULTALPHA )

def tifSelectAllChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "TIF_TYPE_EnableBox", True )
    scriptDialog.SetValue( "TIF_ALPHA_EnableBox", True )
    scriptDialog.SetValue( "TIF_COMPRESSION_EnableBox", True )
    scriptDialog.SetValue( "TIF_DPI_EnableBox", True )

def tifSelectNoneChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "TIF_TYPE_EnableBox", False )
    scriptDialog.SetValue( "TIF_ALPHA_EnableBox", False )
    scriptDialog.SetValue( "TIF_COMPRESSION_EnableBox", False )
    scriptDialog.SetValue( "TIF_DPI_EnableBox", False )

def tifInvertSelectionChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "TIF_TYPE_EnableBox", not (scriptDialog.GetValue("TIF_TYPE_EnableBox") ) )
    scriptDialog.SetValue( "TIF_ALPHA_EnableBox", not (scriptDialog.GetValue("TIF_ALPHA_EnableBox") ) )
    scriptDialog.SetValue( "TIF_COMPRESSION_EnableBox", not (scriptDialog.GetValue("TIF_COMPRESSION_EnableBox") ) )
    scriptDialog.SetValue( "TIF_DPI_EnableBox", not (scriptDialog.GetValue("TIF_DPI_EnableBox") ) )

def TIF_TYPE_Changed( *args ):
    global scriptDialog
    TIF_TYPE = scriptDialog.GetValue("TIF_TYPE_EnableBox")
    scriptDialog.SetEnabled( "TIF_TYPE_Box", TIF_TYPE )

def TIF_ALPHA_Changed( *args ):
    global scriptDialog
    TIF_ALPHA = scriptDialog.GetValue("TIF_ALPHA_EnableBox")
    scriptDialog.SetEnabled( "TIF_ALPHA_Box", TIF_ALPHA )

def TIF_COMPRESSION_Changed( *args ):
    global scriptDialog
    TIF_COMPRESSION = scriptDialog.GetValue("TIF_COMPRESSION_EnableBox")
    scriptDialog.SetEnabled( "TIF_COMPRESSION_Box", TIF_COMPRESSION )

def TIF_DPI_Changed( *args ):
    global scriptDialog
    TIF_DPI = scriptDialog.GetValue("TIF_DPI_EnableBox")
    scriptDialog.SetEnabled( "TIF_DPI_Box", TIF_DPI )

def RLA_COLORDEPTH_Changed( *args ):
    global scriptDialog
    RLA_COLORDEPTH = scriptDialog.GetValue("RLA_COLORDEPTH_EnableBox")
    scriptDialog.SetEnabled( "RLA_COLORDEPTH_Box", RLA_COLORDEPTH )

def rlaSelectAllChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "RLA_COLORDEPTH_EnableBox", True )
    scriptDialog.SetValue( "RLA_ALPHA_EnableBox", True )
    scriptDialog.SetValue( "RLA_PREMULTALPHA_EnableBox", True )
    scriptDialog.SetValue( "RLA_DESCRIPTION_EnableBox", True )
    scriptDialog.SetValue( "RLA_AUTHOR_EnableBox", True )
    scriptDialog.SetValue( "RLA_ZDEPTHCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RLA_MTLIDCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RLA_OBJECTIDCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RLA_UVCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RLA_NORMALCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RLA_NONCLAMPEDCOLORCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RLA_COVERAGECHANNEL_EnableBox", True )

def rlaSelectNoneChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "RLA_COLORDEPTH_EnableBox", False )
    scriptDialog.SetValue( "RLA_ALPHA_EnableBox", False )
    scriptDialog.SetValue( "RLA_PREMULTALPHA_EnableBox", False )
    scriptDialog.SetValue( "RLA_DESCRIPTION_EnableBox", False )
    scriptDialog.SetValue( "RLA_AUTHOR_EnableBox", False )
    scriptDialog.SetValue( "RLA_ZDEPTHCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RLA_MTLIDCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RLA_OBJECTIDCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RLA_UVCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RLA_NORMALCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RLA_NONCLAMPEDCOLORCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RLA_COVERAGECHANNEL_EnableBox", False )

def rlaInvertSelectionChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "RLA_COLORDEPTH_EnableBox", not (scriptDialog.GetValue("RLA_COLORDEPTH_EnableBox") ) )
    scriptDialog.SetValue( "RLA_ALPHA_EnableBox", not (scriptDialog.GetValue("RLA_ALPHA_EnableBox") ) )
    scriptDialog.SetValue( "RLA_PREMULTALPHA_EnableBox", not (scriptDialog.GetValue("RLA_PREMULTALPHA_EnableBox") ) )
    scriptDialog.SetValue( "RLA_DESCRIPTION_EnableBox", not (scriptDialog.GetValue("RLA_DESCRIPTION_EnableBox") ) )
    scriptDialog.SetValue( "RLA_AUTHOR_EnableBox", not (scriptDialog.GetValue("RLA_AUTHOR_EnableBox") ) )
    scriptDialog.SetValue( "RLA_ZDEPTHCHANNEL_EnableBox", not (scriptDialog.GetValue("RLA_ZDEPTHCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RLA_MTLIDCHANNEL_EnableBox", not (scriptDialog.GetValue("RLA_MTLIDCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RLA_OBJECTIDCHANNEL_EnableBox", not (scriptDialog.GetValue("RLA_OBJECTIDCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RLA_UVCHANNEL_EnableBox", not (scriptDialog.GetValue("RLA_UVCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RLA_NORMALCHANNEL_EnableBox", not (scriptDialog.GetValue("RLA_NORMALCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RLA_NONCLAMPEDCOLORCHANNEL_EnableBox", not (scriptDialog.GetValue("RLA_NONCLAMPEDCOLORCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RLA_COVERAGECHANNEL_EnableBox", not (scriptDialog.GetValue("RLA_COVERAGECHANNEL_EnableBox") ) )

def RLA_ALPHA_Changed( *args ):
    global scriptDialog
    RLA_ALPHA = scriptDialog.GetValue("RLA_ALPHA_EnableBox")
    scriptDialog.SetEnabled( "RLA_ALPHA_Box", RLA_ALPHA )

def RLA_PREMULTALPHA_Changed( *args ):
    global scriptDialog
    RLA_PREMULTALPHA = scriptDialog.GetValue("RLA_PREMULTALPHA_EnableBox")
    scriptDialog.SetEnabled( "RLA_PREMULTALPHA_Box", RLA_PREMULTALPHA )

def RLA_DESCRIPTION_Changed( *args ):
    global scriptDialog
    RLA_DESCRIPTION = scriptDialog.GetValue("RLA_DESCRIPTION_EnableBox")
    scriptDialog.SetEnabled( "RLA_DESCRIPTION_Box", RLA_DESCRIPTION )

def RLA_AUTHOR_Changed( *args ):
    global scriptDialog
    RLA_AUTHOR = scriptDialog.GetValue("RLA_AUTHOR_EnableBox")
    scriptDialog.SetEnabled( "RLA_AUTHOR_Box", RLA_AUTHOR )

def RLA_ZDEPTHCHANNEL_Changed( *args ):
    global scriptDialog
    RLA_ZDEPTHCHANNEL = scriptDialog.GetValue("RLA_ZDEPTHCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RLA_ZDEPTHCHANNEL_Box", RLA_ZDEPTHCHANNEL )

def RLA_MTLIDCHANNEL_Changed( *args ):
    global scriptDialog
    RLA_MTLIDCHANNEL = scriptDialog.GetValue("RLA_MTLIDCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RLA_MTLIDCHANNEL_Box", RLA_MTLIDCHANNEL )

def RLA_OBJECTIDCHANNEL_Changed( *args ):
    global scriptDialog
    RLA_OBJECTIDCHANNEL = scriptDialog.GetValue("RLA_OBJECTIDCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RLA_OBJECTIDCHANNEL_Box", RLA_OBJECTIDCHANNEL )

def RLA_UVCHANNEL_Changed( *args ):
    global scriptDialog
    RLA_UVCHANNEL = scriptDialog.GetValue("RLA_UVCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RLA_UVCHANNEL_Box", RLA_UVCHANNEL )

def RLA_NORMALCHANNEL_Changed( *args ):
    global scriptDialog
    RLA_NORMALCHANNEL = scriptDialog.GetValue("RLA_NORMALCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RLA_NORMALCHANNEL_Box", RLA_NORMALCHANNEL )

def RLA_NONCLAMPEDCOLORCHANNEL_Changed( *args ):
    global scriptDialog
    RLA_NONCLAMPEDCOLORCHANNEL = scriptDialog.GetValue("RLA_NONCLAMPEDCOLORCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RLA_NONCLAMPEDCOLORCHANNEL_Box", RLA_NONCLAMPEDCOLORCHANNEL )

def RLA_COVERAGECHANNEL_Changed( *args ):
    global scriptDialog
    RLA_COVERAGECHANNEL = scriptDialog.GetValue("RLA_COVERAGECHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RLA_COVERAGECHANNEL_Box", RLA_COVERAGECHANNEL )

def rpfSelectAllChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "RPF_COLORDEPTH_EnableBox", True )
    scriptDialog.SetValue( "RPF_ALPHA_EnableBox", True )
    scriptDialog.SetValue( "RPF_PREMULTALPHA_EnableBox", True )
    scriptDialog.SetValue( "RPF_DESCRIPTION_EnableBox", True )
    scriptDialog.SetValue( "RPF_AUTHOR_EnableBox", True )
    scriptDialog.SetValue( "RPF_ZDEPTHCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_MTLIDCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_OBJECTIDCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_UVCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_NORMALCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_NONCLAMPEDCOLORCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_COVERAGECHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_NODERENDERIDCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_COLORCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_TRANSPCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_VELOCCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_WEIGHTCHANNEL_EnableBox", True )
    scriptDialog.SetValue( "RPF_MASKCHANNEL_EnableBox", True )

def rpfSelectNoneChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "RPF_COLORDEPTH_EnableBox", False )
    scriptDialog.SetValue( "RPF_ALPHA_EnableBox", False )
    scriptDialog.SetValue( "RPF_PREMULTALPHA_EnableBox", False )
    scriptDialog.SetValue( "RPF_DESCRIPTION_EnableBox", False )
    scriptDialog.SetValue( "RPF_AUTHOR_EnableBox", False )
    scriptDialog.SetValue( "RPF_ZDEPTHCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_MTLIDCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_OBJECTIDCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_UVCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_NORMALCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_NONCLAMPEDCOLORCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_COVERAGECHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_NODERENDERIDCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_COLORCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_TRANSPCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_VELOCCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_WEIGHTCHANNEL_EnableBox", False )
    scriptDialog.SetValue( "RPF_MASKCHANNEL_EnableBox", False )

def rpfInvertSelectionChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "RPF_COLORDEPTH_EnableBox", not (scriptDialog.GetValue("RPF_COLORDEPTH_EnableBox") ) )
    scriptDialog.SetValue( "RPF_ALPHA_EnableBox", not (scriptDialog.GetValue("RPF_ALPHA_EnableBox") ) )
    scriptDialog.SetValue( "RPF_PREMULTALPHA_EnableBox", not (scriptDialog.GetValue("RPF_PREMULTALPHA_EnableBox") ) )
    scriptDialog.SetValue( "RPF_DESCRIPTION_EnableBox", not (scriptDialog.GetValue("RPF_DESCRIPTION_EnableBox") ) )
    scriptDialog.SetValue( "RPF_AUTHOR_EnableBox", not (scriptDialog.GetValue("RPF_AUTHOR_EnableBox") ) )
    scriptDialog.SetValue( "RPF_ZDEPTHCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_ZDEPTHCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_MTLIDCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_MTLIDCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_OBJECTIDCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_OBJECTIDCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_UVCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_UVCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_NORMALCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_NORMALCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_NONCLAMPEDCOLORCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_NONCLAMPEDCOLORCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_COVERAGECHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_COVERAGECHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_NODERENDERIDCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_NODERENDERIDCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_COLORCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_COLORCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_TRANSPCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_TRANSPCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_VELOCCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_VELOCCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_WEIGHTCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_WEIGHTCHANNEL_EnableBox") ) )
    scriptDialog.SetValue( "RPF_MASKCHANNEL_EnableBox", not (scriptDialog.GetValue("RPF_MASKCHANNEL_EnableBox") ) )

def RPF_COLORDEPTH_Changed( *args ):
    global scriptDialog
    RPF_COLORDEPTH = scriptDialog.GetValue("RPF_COLORDEPTH_EnableBox")
    scriptDialog.SetEnabled( "RPF_COLORDEPTH_Box", RPF_COLORDEPTH )

def RPF_ALPHA_Changed( *args ):
    global scriptDialog
    RPF_ALPHA = scriptDialog.GetValue("RPF_ALPHA_EnableBox")
    scriptDialog.SetEnabled( "RPF_ALPHA_Box", RPF_ALPHA )

def RPF_PREMULTALPHA_Changed( *args ):
    global scriptDialog
    RPF_PREMULTALPHA = scriptDialog.GetValue("RPF_PREMULTALPHA_EnableBox")
    scriptDialog.SetEnabled( "RPF_PREMULTALPHA_Box", RPF_PREMULTALPHA )

def RPF_DESCRIPTION_Changed( *args ):
    global scriptDialog
    RPF_DESCRIPTION = scriptDialog.GetValue("RPF_DESCRIPTION_EnableBox")
    scriptDialog.SetEnabled( "RPF_DESCRIPTION_Box", RPF_DESCRIPTION )

def RPF_AUTHOR_Changed( *args ):
    global scriptDialog
    RPF_AUTHOR = scriptDialog.GetValue("RPF_AUTHOR_EnableBox")
    scriptDialog.SetEnabled( "RPF_AUTHOR_Box", RPF_AUTHOR )

def RPF_ZDEPTHCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_ZDEPTHCHANNEL = scriptDialog.GetValue("RPF_ZDEPTHCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_ZDEPTHCHANNEL_Box", RPF_ZDEPTHCHANNEL )

def RPF_MTLIDCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_MTLIDCHANNEL = scriptDialog.GetValue("RPF_MTLIDCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_MTLIDCHANNEL_Box", RPF_MTLIDCHANNEL )

def RPF_OBJECTIDCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_OBJECTIDCHANNEL = scriptDialog.GetValue("RPF_OBJECTIDCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_OBJECTIDCHANNEL_Box", RPF_OBJECTIDCHANNEL )

def RPF_UVCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_UVCHANNEL = scriptDialog.GetValue("RPF_UVCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_UVCHANNEL_Box", RPF_UVCHANNEL )

def RPF_NORMALCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_NORMALCHANNEL = scriptDialog.GetValue("RPF_NORMALCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_NORMALCHANNEL_Box", RPF_NORMALCHANNEL )

def RPF_NONCLAMPEDCOLORCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_NONCLAMPEDCOLORCHANNEL = scriptDialog.GetValue("RPF_NONCLAMPEDCOLORCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_NONCLAMPEDCOLORCHANNEL_Box", RPF_NONCLAMPEDCOLORCHANNEL )

def RPF_COVERAGECHANNEL_Changed( *args ):
    global scriptDialog
    RPF_COVERAGECHANNEL = scriptDialog.GetValue("RPF_COVERAGECHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_COVERAGECHANNEL_Box", RPF_COVERAGECHANNEL )

def RPF_NODERENDERIDCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_NODERENDERIDCHANNEL = scriptDialog.GetValue("RPF_NODERENDERIDCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_NODERENDERIDCHANNEL_Box", RPF_NODERENDERIDCHANNEL )

def RPF_COLORCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_COLORCHANNEL = scriptDialog.GetValue("RPF_COLORCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_COLORCHANNEL_Box", RPF_COLORCHANNEL )

def RPF_TRANSPCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_TRANSPCHANNEL = scriptDialog.GetValue("RPF_TRANSPCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_TRANSPCHANNEL_Box", RPF_TRANSPCHANNEL )

def RPF_VELOCCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_VELOCCHANNEL = scriptDialog.GetValue("RPF_VELOCCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_VELOCCHANNEL_Box", RPF_VELOCCHANNEL )

def RPF_WEIGHTCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_WEIGHTCHANNEL = scriptDialog.GetValue("RPF_WEIGHTCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_WEIGHTCHANNEL_Box", RPF_WEIGHTCHANNEL )

def RPF_MASKCHANNEL_Changed( *args ):
    global scriptDialog
    RPF_MASKCHANNEL = scriptDialog.GetValue("RPF_MASKCHANNEL_EnableBox")
    scriptDialog.SetEnabled( "RPF_MASKCHANNEL_Box", RPF_MASKCHANNEL )

def exrSelectAllChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "EXR_USEEXPONENT_EnableBox", True )
    scriptDialog.SetValue( "EXR_EXPONENT_EnableBox", True )
    scriptDialog.SetValue( "EXR_PREMULTALPHA_EnableBox", True )
    scriptDialog.SetValue( "EXR_ALPHA_EnableBox", True )
    scriptDialog.SetValue( "EXR_RED_EnableBox", True )
    scriptDialog.SetValue( "EXR_GREEN_EnableBox", True )
    scriptDialog.SetValue( "EXR_BLUE_EnableBox", True )
    scriptDialog.SetValue( "EXR_BITDEPTH_EnableBox", True )
    scriptDialog.SetValue( "EXR_USEFRAMENUMDIGITS_EnableBox", True )
    scriptDialog.SetValue( "EXR_FRAMENUMDIGITS_EnableBox", True )
    scriptDialog.SetValue( "EXR_COMPRESSIONTYPE_EnableBox", True )
    scriptDialog.SetValue( "EXR_USEREALPIX_EnableBox", True )

def exrSelectNoneChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "EXR_USEEXPONENT_EnableBox", False )
    scriptDialog.SetValue( "EXR_EXPONENT_EnableBox", False )
    scriptDialog.SetValue( "EXR_PREMULTALPHA_EnableBox", False )
    scriptDialog.SetValue( "EXR_ALPHA_EnableBox", False )
    scriptDialog.SetValue( "EXR_RED_EnableBox", False )
    scriptDialog.SetValue( "EXR_GREEN_EnableBox", False )
    scriptDialog.SetValue( "EXR_BLUE_EnableBox", False )
    scriptDialog.SetValue( "EXR_BITDEPTH_EnableBox", False )
    scriptDialog.SetValue( "EXR_USEFRAMENUMDIGITS_EnableBox", False )
    scriptDialog.SetValue( "EXR_FRAMENUMDIGITS_EnableBox", False )
    scriptDialog.SetValue( "EXR_COMPRESSIONTYPE_EnableBox", False )
    scriptDialog.SetValue( "EXR_USEREALPIX_EnableBox", False )

def exrInvertSelectionChanged( *args ):
    global scriptDialog
    scriptDialog.SetValue( "EXR_USEEXPONENT_EnableBox", not (scriptDialog.GetValue("EXR_USEEXPONENT_EnableBox") ) )
    scriptDialog.SetValue( "EXR_EXPONENT_EnableBox", not (scriptDialog.GetValue("EXR_EXPONENT_EnableBox") ) )
    scriptDialog.SetValue( "EXR_PREMULTALPHA_EnableBox", not (scriptDialog.GetValue("EXR_PREMULTALPHA_EnableBox") ) )
    scriptDialog.SetValue( "EXR_ALPHA_EnableBox", not (scriptDialog.GetValue("EXR_ALPHA_EnableBox") ) )
    scriptDialog.SetValue( "EXR_RED_EnableBox", not (scriptDialog.GetValue("EXR_RED_EnableBox") ) )
    scriptDialog.SetValue( "EXR_GREEN_EnableBox", not (scriptDialog.GetValue("EXR_GREEN_EnableBox") ) )
    scriptDialog.SetValue( "EXR_BLUE_EnableBox", not (scriptDialog.GetValue("EXR_BLUE_EnableBox") ) )
    scriptDialog.SetValue( "EXR_BITDEPTH_EnableBox", not (scriptDialog.GetValue("EXR_BITDEPTH_EnableBox") ) )
    scriptDialog.SetValue( "EXR_USEFRAMENUMDIGITS_EnableBox", not (scriptDialog.GetValue("EXR_USEFRAMENUMDIGITS_EnableBox") ) )
    scriptDialog.SetValue( "EXR_FRAMENUMDIGITS_EnableBox", not (scriptDialog.GetValue("EXR_FRAMENUMDIGITS_EnableBox") ) )
    scriptDialog.SetValue( "EXR_COMPRESSIONTYPE_EnableBox", not (scriptDialog.GetValue("EXR_COMPRESSIONTYPE_EnableBox") ) )
    scriptDialog.SetValue( "EXR_USEREALPIX_EnableBox", not (scriptDialog.GetValue("EXR_USEREALPIX_EnableBox") ) )

def EXR_USEEXPONENT_Changed( *args ):
    global scriptDialog
    EXR_USEEXPONENT = scriptDialog.GetValue("EXR_USEEXPONENT_EnableBox")
    scriptDialog.SetEnabled( "EXR_USEEXPONENT_Box", EXR_USEEXPONENT )

def EXR_EXPONENT_Changed( *args ):
    global scriptDialog
    EXR_EXPONENT = scriptDialog.GetValue("EXR_EXPONENT_EnableBox")
    scriptDialog.SetEnabled( "EXR_EXPONENT_Box", EXR_EXPONENT )

def EXR_PREMULTALPHA_Changed( *args ):
    global scriptDialog
    EXR_PREMULTALPHA = scriptDialog.GetValue("EXR_PREMULTALPHA_EnableBox")
    scriptDialog.SetEnabled( "EXR_PREMULTALPHA_Box", EXR_PREMULTALPHA )

def EXR_ALPHA_Changed( *args ):
    global scriptDialog
    EXR_ALPHA = scriptDialog.GetValue("EXR_ALPHA_EnableBox")
    scriptDialog.SetEnabled( "EXR_ALPHA_Box", EXR_ALPHA )

def EXR_RED_Changed( *args ):
    global scriptDialog
    EXR_RED = scriptDialog.GetValue("EXR_RED_EnableBox")
    scriptDialog.SetEnabled( "EXR_RED_Box", EXR_RED )

def EXR_GREEN_Changed( *args ):
    global scriptDialog
    EXR_GREEN = scriptDialog.GetValue("EXR_GREEN_EnableBox")
    scriptDialog.SetEnabled( "EXR_GREEN_Box", EXR_GREEN )

def EXR_BLUE_Changed( *args ):
    global scriptDialog
    EXR_BLUE = scriptDialog.GetValue("EXR_BLUE_EnableBox")
    scriptDialog.SetEnabled( "EXR_BLUE_Box", EXR_BLUE )

def EXR_BITDEPTH_Changed( *args ):
    global scriptDialog
    EXR_BITDEPTH = scriptDialog.GetValue("EXR_BITDEPTH_EnableBox")
    scriptDialog.SetEnabled( "EXR_BITDEPTH_Box", EXR_BITDEPTH )

def EXR_USEFRAMENUMDIGITS_Changed( *args ):
    global scriptDialog
    EXR_USEFRAMENUMDIGITS = scriptDialog.GetValue("EXR_USEFRAMENUMDIGITS_EnableBox")
    scriptDialog.SetEnabled( "EXR_USEFRAMENUMDIGITS_Box", EXR_USEFRAMENUMDIGITS )

def EXR_FRAMENUMDIGITS_Changed( *args ):
    global scriptDialog
    EXR_FRAMENUMDIGITS = scriptDialog.GetValue("EXR_FRAMENUMDIGITS_EnableBox")
    scriptDialog.SetEnabled( "EXR_FRAMENUMDIGITS_Box", EXR_FRAMENUMDIGITS )

def EXR_COMPRESSIONTYPE_Changed( *args ):
    global scriptDialog
    EXR_COMPRESSIONTYPE = scriptDialog.GetValue("EXR_COMPRESSIONTYPE_EnableBox")
    scriptDialog.SetEnabled( "EXR_COMPRESSIONTYPE_Box", EXR_COMPRESSIONTYPE )

def EXR_USEREALPIX_Changed( *args ):
    global scriptDialog
    EXR_USEREALPIX = scriptDialog.GetValue("EXR_USEREALPIX_EnableBox")
    scriptDialog.SetEnabled( "EXR_USEREALPIX_Box", EXR_USEREALPIX )

def CloseButtonPressed( *args ):
    CloseDialog()

def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    
    try:
        submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
        outFile = scriptDialog.GetValue( "OutputBox" )
        
        # Check if Integration options are valid
        if not integration_dialog.CheckIntegrationSanity( outFile ):
            return

        warnings = []
        errors = []

        # Check if max files exist.
        sceneFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "SceneBox" ), False )
        if len( sceneFiles ) == 0:
            errors.append( "No 3ds Max scene file specified" )
        
        for sceneFile in sceneFiles:
            if not os.path.isfile( sceneFile ):
                errors.append( "3ds Max scene file: %s does not exist" % sceneFile )
            elif not submitScene and PathUtils.IsPathLocal( sceneFile ):
                warnings.append( "The 3ds Max scene file: " + sceneFile + " is local and is not being submitted with the job, are you sure you want to continue?" )
        
        # Check output file.
        if outFile:
            index = outFile.find(".")
            if index == -1:
                errors.append( "Output file does not contain an extension." )
            elif not Directory.Exists( Path.GetDirectoryName( outFile ) ):
                errors.append( "Path for the output file: " + outFile + " does not exist." )
            elif PathUtils.IsPathLocal( outFile ):
                warnings.append( "The output file: " + outFile + " is local, are you sure you want to continue?" )
        
        # Check if render preset file exists.
        renderPresetFile = scriptDialog.GetValue( "RenderPresetBox" ).strip()
        if renderPresetFile:
            if not os.path.isfile( renderPresetFile ):
                errors.append( "Render Preset file: %s does not exist" % renderPresetFile )

        # Check if pre-render maxscript file exists.
        preRenderScript = scriptDialog.GetValue( "PreRenderScriptBox" ).strip()
        if preRenderScript:
            if not os.path.isfile( preRenderScript ):
                errors.append( "Pre-Render MAXScript file: %s does not exist" % preRenderScript )

        # Check if post-render maxscript file exists.
        postRenderScript = scriptDialog.GetValue( "PostRenderScriptBox" ).strip()
        if postRenderScript:
            if not os.path.isfile( postRenderScript ):
                errors.append( "Post-Render MAXScript file: %s does not exist" % postRenderScript )

        # Check if path config file exists.
        pathConfigFile = scriptDialog.GetValue( "PathConfigBox" ).strip()
        if pathConfigFile:
            if not os.path.isfile( pathConfigFile ):
                errors.append( "Path configuration file: %s does not exist" % pathConfigFile )
        
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

        # Check Render Elements enabled for Max 2013 or earlier?
        if int(scriptDialog.GetValue( "VersionBox" )) < 2014 and not scriptDialog.GetValue( "ElementsBox" ):
            warnings.append( "Max 2013 or earler requires Render Elements to be explicity enabled if they are required. Are you sure you want to continue?" )

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
            jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "maxcmd_job_info.job" )
            writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "Plugin=3dsCmd" )
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
            
            removePadding = scriptDialog.GetValue( "StillFrameBox" )
            if outFile and not removePadding:
                index = outFile.rfind( "." )
                writer.WriteLine( "OutputFilename0=%s####%s" % (outFile[0:index], outFile[index:]) )
            
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
            pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "maxcmd_plugin_info.job" )
            writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

            if not submitScene:
                writer.WriteLine( "SceneFile=%s" % sceneFile )
            
            writer.WriteLine("Version=" + scriptDialog.GetValue("VersionBox"))
            if int(scriptDialog.GetValue( "VersionBox" )) < 2014:
                writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
            writer.WriteLine( "IsMaxDesign=%s" % scriptDialog.GetValue( "IsMaxDesignBox" ) )
            writer.WriteLine( "RenderOutput=%s" % scriptDialog.GetValue("OutputBox"))

            camera = scriptDialog.GetValue("CameraBox")
            if camera:
                writer.WriteLine( "Camera=%s" % camera )
                writer.WriteLine( "Camera0=" )
                writer.WriteLine( "Camera1=%s" % camera )

            if renderPresetFile:
                writer.WriteLine( "RenderPresetFile=%s" % Path.GetFileName( renderPresetFile ) )

            if preRenderScript:
                writer.WriteLine( "PreRenderScript=%s" % Path.GetFileName( preRenderScript ) )

            if postRenderScript:
                writer.WriteLine( "PostRenderScript=%s" % Path.GetFileName( postRenderScript ) )

            writer.WriteLine( "SceneState=%s" % scriptDialog.GetValue("SceneStateBox") )

            writer.WriteLine( "BatchRender=%s" % scriptDialog.GetValue( "BatchRenderBox" ) )
            writer.WriteLine( "BatchRenderName=%s" % scriptDialog.GetValue( "BatchRenderNameBox" ) )

            if pathConfigFile:
                writer.WriteLine( "PathConfigFile=%s" % Path.GetFileName( pathConfigFile ) )

            writer.WriteLine( "StripRendering=%s" % scriptDialog.GetValue( "StripRenderingBox" ) )
            writer.WriteLine( "StripCount=%s" % scriptDialog.GetValue( "StripCountBox" ) )
            writer.WriteLine( "StripOverlap=%s" % scriptDialog.GetValue( "StripOverlapBox" ) )

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

            overrideResolution = scriptDialog.GetValue( "OverrideResolutionBox" )
            writer.WriteLine( "OverrideResolution=%s" % overrideResolution )
            if scriptDialog.GetValue( "OverrideResolutionBox" ):
                writer.WriteLine( "ImageWidth=%s" % scriptDialog.GetValue( "WidthBox" ) )
                writer.WriteLine( "ImageHeight=%s" % scriptDialog.GetValue( "HeightBox" ) )
                writer.WriteLine( "PixelAspect=%s" % scriptDialog.GetValue( "PixelAspectBox" ) )

            writer.WriteLine( "ContinueOnError=%s" % scriptDialog.GetValue( "ContinueBox" ) )
            writer.WriteLine( "LocalRendering=%s" % scriptDialog.GetValue( "LocalRenderingBox" ) )

            writer.WriteLine( "StillFrame=%s" % scriptDialog.GetValue( "StillFrameBox" ) )
            writer.WriteLine( "VideoPost=%s" % scriptDialog.GetValue( "VideoPostBox" ) )
            
            writer.WriteLine( "ImageSequenceFile=%s" % scriptDialog.GetValue( "ImageSequenceFileBox" ) )
            writer.WriteLine( "ImageSequenceFile0=none" )
            writer.WriteLine( "ImageSequenceFile1=.imsq" )
            writer.WriteLine( "ImageSequenceFile2=.ifl" )

            writer.WriteLine( "GammaCorrection=%s" % scriptDialog.GetValue( "GammaCorrectionBox" ) )
            writer.WriteLine( "GammaInput=%s" % scriptDialog.GetValue( "GammaInputBox" ) )
            writer.WriteLine( "GammaOutput=%s" % scriptDialog.GetValue( "GammaOutputBox" ) )

            writer.WriteLine( "ShowVFB=%s" % scriptDialog.GetValue( "ShowVfbBox" ) )
            writer.WriteLine( "SkipRenderedFrames=%s" % scriptDialog.GetValue( "SkipRenderedFramesBox" ) )

            writer.WriteLine( "VideoColorCheck=%s" % scriptDialog.GetValue( "ColorCheckBox" ) )
            writer.WriteLine( "TwoSided=%s" % scriptDialog.GetValue( "TwoSidedBox" ) )

            writer.WriteLine( "HiddenGeometry=%s" % scriptDialog.GetValue( "HiddenGeometryBox" ) )
            writer.WriteLine( "Atmospherics=%s" % scriptDialog.GetValue( "AtmosphericsBox" ) )

            writer.WriteLine( "SuperBlack=%s" % scriptDialog.GetValue( "SuperBlackBox" ) )
            writer.WriteLine( "RenderToFields=%s" % scriptDialog.GetValue( "RenderToFieldsBox" ) )

            writer.WriteLine( "FieldOrder=%s" % scriptDialog.GetValue( "FieldOrderBox" ) )
            writer.WriteLine( "FieldOrder0=Odd" )
            writer.WriteLine( "FieldOrder1=Even" )

            writer.WriteLine( "RenderElements=%s" % scriptDialog.GetValue( "ElementsBox" ) ) # must be explicitly declared if Max 2013 or earlier
            writer.WriteLine( "Displacements=%s" % scriptDialog.GetValue( "DisplacementBox" ) )

            writer.WriteLine( "Effects=%s" % scriptDialog.GetValue( "EffectsBox" ) )
            writer.WriteLine( "AreaLights=%s" % scriptDialog.GetValue( "AreaLightsBox" ) )

            writer.WriteLine( "UseAdvLighting=%s" % scriptDialog.GetValue( "UseAdvLightBox" ) )
            writer.WriteLine( "ComputeAdvLighting=%s" % scriptDialog.GetValue( "ComputeAdvLightBox" ) )

            writer.WriteLine( "DitherPaletted=%s" % scriptDialog.GetValue( "DitherPalettedBox" ) )
            writer.WriteLine( "DitherTrueColor=%s" % scriptDialog.GetValue( "DitherTrueColorBox" ) )

            if scriptDialog.GetValue( "BMP_TYPE_EnableBox" ):
                writer.WriteLine( "BMP_TYPE=%s" % scriptDialog.GetValue( "BMP_TYPE_Box" ) )
                writer.WriteLine( "BMP_TYPE0=paletted" )
                writer.WriteLine( "BMP_TYPE1=true 24-bit" )

            if scriptDialog.GetValue( "JPEG_QUALITY_EnableBox" ):
                writer.WriteLine( "JPEG_QUALITY=%s" % scriptDialog.GetValue( "JPEG_QUALITY_Box" ) )
            if scriptDialog.GetValue( "JPEG_SMOOTHING_EnableBox" ):
                writer.WriteLine( "JPEG_SMOOTHING=%s" % scriptDialog.GetValue( "JPEG_SMOOTHING_Box" ) )

            if scriptDialog.GetValue( "TARGA_COLORDEPTH_EnableBox" ):
                writer.WriteLine( "TARGA_COLORDEPTH=%s" % scriptDialog.GetValue( "TARGA_COLORDEPTH_Box" ) )
                writer.WriteLine( "TARGA_COLORDEPTH0=16" )
                writer.WriteLine( "TARGA_COLORDEPTH1=24" )
                writer.WriteLine( "TARGA_COLORDEPTH2=32" )
            if scriptDialog.GetValue( "TARGA_COMPRESSED_EnableBox" ):
                writer.WriteLine( "TARGA_COMPRESSED=%s" % scriptDialog.GetValue( "TARGA_COMPRESSED_Box" ) )
            if scriptDialog.GetValue( "TARGA_ALPHASPLIT_EnableBox" ):
                writer.WriteLine( "TARGA_ALPHASPLIT=%s" % scriptDialog.GetValue( "TARGA_ALPHASPLIT_Box" ) )
            if scriptDialog.GetValue( "TARGA_PREMULTALPHA_EnableBox" ):
                writer.WriteLine( "TARGA_PREMULTALPHA=%s" % scriptDialog.GetValue( "TARGA_PREMULTALPHA_Box" ) )

            if scriptDialog.GetValue( "TIF_TYPE_EnableBox" ):
                writer.WriteLine( "TIF_TYPE=%s" % scriptDialog.GetValue( "TIF_TYPE_Box" ) )
                writer.WriteLine( "TIF_TYPE0=mono" )
                writer.WriteLine( "TIF_TYPE1=color" )
                writer.WriteLine( "TIF_TYPE2=logl" )
                writer.WriteLine( "TIF_TYPE3=logluv" )
                writer.WriteLine( "TIF_TYPE4=16-bit color" )
            if scriptDialog.GetValue( "TIF_ALPHA_EnableBox" ):
                writer.WriteLine( "TIF_ALPHA=%s" % scriptDialog.GetValue( "TIF_ALPHA_Box" ) )
            if scriptDialog.GetValue( "TIF_COMPRESSION_EnableBox" ):
                writer.WriteLine( "TIF_COMPRESSION=%s" % scriptDialog.GetValue( "TIF_COMPRESSION_Box" ) )
            if scriptDialog.GetValue( "TIF_DPI_EnableBox" ):
                writer.WriteLine( "TIF_DPI=%s" % scriptDialog.GetValue( "TIF_DPI_Box" ) )

            if scriptDialog.GetValue( "RLA_COLORDEPTH_EnableBox" ):
                writer.WriteLine( "RLA_COLORDEPTH=%s" % scriptDialog.GetValue( "RLA_COLORDEPTH_Box" ) )
                writer.WriteLine( "RLA_COLORDEPTH0=8" )
                writer.WriteLine( "RLA_COLORDEPTH1=16" )
                writer.WriteLine( "RLA_COLORDEPTH2=32" )
            if scriptDialog.GetValue( "RLA_ALPHA_EnableBox" ):
                writer.WriteLine( "RLA_ALPHA=%s" % scriptDialog.GetValue( "RLA_ALPHA_Box" ) )
            if scriptDialog.GetValue( "RLA_PREMULTALPHA_EnableBox" ):
                writer.WriteLine( "RLA_PREMULTALPHA=%s" % scriptDialog.GetValue( "RLA_PREMULTALPHA_Box" ) )
            if scriptDialog.GetValue( "RLA_DESCRIPTION_EnableBox" ):
                writer.WriteLine( "RLA_DESCRIPTION=%s" % scriptDialog.GetValue( "RLA_DESCRIPTION_Box" ) )
            if scriptDialog.GetValue( "RLA_AUTHOR_EnableBox" ):
                writer.WriteLine( "RLA_AUTHOR=%s" % scriptDialog.GetValue( "RLA_AUTHOR_Box" ) )
            if scriptDialog.GetValue( "RLA_ZDEPTHCHANNEL_EnableBox" ):
                writer.WriteLine( "RLA_ZDEPTHCHANNEL=%s" % scriptDialog.GetValue( "RLA_ZDEPTHCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RLA_MTLIDCHANNEL_EnableBox" ):
                writer.WriteLine( "RLA_MTLIDCHANNEL=%s" % scriptDialog.GetValue( "RLA_MTLIDCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RLA_OBJECTIDCHANNEL_EnableBox" ):
                writer.WriteLine( "RLA_OBJECTIDCHANNEL=%s" % scriptDialog.GetValue( "RLA_OBJECTIDCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RLA_UVCHANNEL_EnableBox" ):
                writer.WriteLine( "RLA_UVCHANNEL=%s" % scriptDialog.GetValue( "RLA_UVCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RLA_NORMALCHANNEL_EnableBox" ):
                writer.WriteLine( "RLA_NORMALCHANNEL=%s" % scriptDialog.GetValue( "RLA_NORMALCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RLA_NONCLAMPEDCOLORCHANNEL_EnableBox" ):
                writer.WriteLine( "RLA_NONCLAMPEDCOLORCHANNEL=%s" % scriptDialog.GetValue( "RLA_NONCLAMPEDCOLORCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RLA_COVERAGECHANNEL_EnableBox" ):
                writer.WriteLine( "RLA_COVERAGECHANNEL=%s" % scriptDialog.GetValue( "RLA_COVERAGECHANNEL_Box" ) )

            if scriptDialog.GetValue( "RPF_COLORDEPTH_EnableBox" ):
                writer.WriteLine( "RPF_COLORDEPTH=%s" % scriptDialog.GetValue( "RPF_COLORDEPTH_Box" ) )
                writer.WriteLine( "RPF_COLORDEPTH0=8" )
                writer.WriteLine( "RPF_COLORDEPTH1=16" )
                writer.WriteLine( "RPF_COLORDEPTH2=32" )
            if scriptDialog.GetValue( "RPF_ALPHA_EnableBox" ):
                writer.WriteLine( "RPF_ALPHA=%s" % scriptDialog.GetValue( "RPF_ALPHA_Box" ) )
            if scriptDialog.GetValue( "RPF_PREMULTALPHA_EnableBox" ):
                writer.WriteLine( "RPF_PREMULTALPHA=%s" % scriptDialog.GetValue( "RPF_PREMULTALPHA_Box" ) )
            if scriptDialog.GetValue( "RPF_DESCRIPTION_EnableBox" ):
                writer.WriteLine( "RPF_DESCRIPTION=%s" % scriptDialog.GetValue( "RPF_DESCRIPTION_Box" ) )
            if scriptDialog.GetValue( "RPF_AUTHOR_EnableBox" ):
                writer.WriteLine( "RPF_AUTHOR=%s" % scriptDialog.GetValue( "RPF_AUTHOR_Box" ) )
            if scriptDialog.GetValue( "RPF_ZDEPTHCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_ZDEPTHCHANNEL=%s" % scriptDialog.GetValue( "RPF_ZDEPTHCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_MTLIDCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_MTLIDCHANNEL=%s" % scriptDialog.GetValue( "RPF_MTLIDCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_OBJECTIDCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_OBJECTIDCHANNEL=%s" % scriptDialog.GetValue( "RPF_OBJECTIDCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_UVCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_UVCHANNEL=%s" % scriptDialog.GetValue( "RPF_UVCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_NORMALCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_NORMALCHANNEL=%s" % scriptDialog.GetValue( "RPF_NORMALCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_NONCLAMPEDCOLORCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_NONCLAMPEDCOLORCHANNEL=%s" % scriptDialog.GetValue( "RPF_NONCLAMPEDCOLORCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_COVERAGECHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_COVERAGECHANNEL=%s" % scriptDialog.GetValue( "RPF_COVERAGECHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_NODERENDERIDCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_NODERENDERIDCHANNEL=%s" % scriptDialog.GetValue( "RPF_NODERENDERIDCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_COLORCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_COLORCHANNEL=%s" % scriptDialog.GetValue( "RPF_COLORCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_TRANSPCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_TRANSPCHANNEL=%s" % scriptDialog.GetValue( "RPF_TRANSPCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_VELOCCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_VELOCCHANNEL=%s" % scriptDialog.GetValue( "RPF_VELOCCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_WEIGHTCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_WEIGHTCHANNEL=%s" % scriptDialog.GetValue( "RPF_WEIGHTCHANNEL_Box" ) )
            if scriptDialog.GetValue( "RPF_MASKCHANNEL_EnableBox" ):
                writer.WriteLine( "RPF_MASKCHANNEL=%s" % scriptDialog.GetValue( "RPF_MASKCHANNEL_Box" ) )

            if scriptDialog.GetValue( "EXR_USEEXPONENT_EnableBox" ):
                writer.WriteLine( "EXR_USEEXPONENT=%s" % scriptDialog.GetValue( "EXR_USEEXPONENT_Box" ) )
            if scriptDialog.GetValue( "EXR_EXPONENT_EnableBox" ):
                writer.WriteLine( "EXR_EXPONENT=%s" % scriptDialog.GetValue( "EXR_EXPONENT_Box" ) )
            if scriptDialog.GetValue( "EXR_PREMULTALPHA_EnableBox" ):
                writer.WriteLine( "EXR_PREMULTALPHA=%s" % scriptDialog.GetValue( "EXR_PREMULTALPHA_Box" ) )
            if scriptDialog.GetValue( "EXR_ALPHA_EnableBox" ):
                writer.WriteLine( "EXR_ALPHA=%s" % scriptDialog.GetValue( "EXR_ALPHA_Box" ) )
            if scriptDialog.GetValue( "EXR_RED_EnableBox" ):
                writer.WriteLine( "EXR_RED=%s" % scriptDialog.GetValue( "EXR_RED_Box" ) )
            if scriptDialog.GetValue( "EXR_GREEN_EnableBox" ):
                writer.WriteLine( "EXR_GREEN=%s" % scriptDialog.GetValue( "EXR_GREEN_Box" ) )
            if scriptDialog.GetValue( "EXR_BLUE_EnableBox" ):
                writer.WriteLine( "EXR_BLUE=%s" % scriptDialog.GetValue( "EXR_BLUE_Box" ) )
            if scriptDialog.GetValue( "EXR_BITDEPTH_EnableBox" ):
                writer.WriteLine( "EXR_BITDEPTH=%s" % scriptDialog.GetValue( "EXR_BITDEPTH_Box" ) )
                writer.WriteLine( "EXR_BITDEPTH0=8-bit integers" )
                writer.WriteLine( "EXR_BITDEPTH1=half float" )
                writer.WriteLine( "EXR_BITDEPTH2=float" )
            if scriptDialog.GetValue( "EXR_USEFRAMENUMDIGITS_EnableBox" ):
                writer.WriteLine( "EXR_USEFRAMENUMDIGITS=%s" % scriptDialog.GetValue( "EXR_USEFRAMENUMDIGITS_Box" ) )
            if scriptDialog.GetValue( "EXR_FRAMENUMDIGITS_EnableBox" ):
                writer.WriteLine( "EXR_FRAMENUMDIGITS=%s" % scriptDialog.GetValue( "EXR_FRAMENUMDIGITS_Box" ) )
            if scriptDialog.GetValue( "EXR_COMPRESSIONTYPE_EnableBox" ):
                writer.WriteLine( "EXR_COMPRESSIONTYPE=%s" % scriptDialog.GetValue( "EXR_COMPRESSIONTYPE_Box" ) )
                writer.WriteLine( "EXR_COMPRESSIONTYPE0=no compression" )
                writer.WriteLine( "EXR_COMPRESSIONTYPE1=RLE" )
                writer.WriteLine( "EXR_COMPRESSIONTYPE2=ZIP (1 scanline)" )
                writer.WriteLine( "EXR_COMPRESSIONTYPE3=ZIP (16 scanlines)" )
                writer.WriteLine( "EXR_COMPRESSIONTYPE3=PIZ" )
            if scriptDialog.GetValue( "EXR_USEREALPIX_EnableBox" ):
                writer.WriteLine( "EXR_USEREALPIX=%s" % scriptDialog.GetValue( "EXR_USEREALPIX_Box" ) )

            writer.Close()
            
            # Setup the command line arguments.
            arguments = [ jobInfoFilename, pluginInfoFilename ]
            if scriptDialog.GetValue( "SubmitSceneBox" ):
                arguments.append( sceneFile )
            if pathConfigFile:
                arguments.append( pathConfigFile )
            if renderPresetFile:
                arguments.append( renderPresetFile )
            if preRenderScript:
                arguments.append( preRenderScript )
            if postRenderScript:
                arguments.append( postRenderScript )

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
