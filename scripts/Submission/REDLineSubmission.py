import re

from System.Collections.Specialized import *
from System.Globalization import *
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
    global scriptDialog
    global settings
    
    settings = []
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit REDLine Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'REDLine' ) )
    scriptDialog.setMinimumSize( 990, 400 )
    
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
    settings.append("DepartmentBox")
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )
    settings.append("PoolBox")

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )
    settings.append("SecondaryPoolBox")

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )
    settings.append("GroupBox")

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )
    settings.append("PriorityBox")

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job.", False )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    settings.append("MachineLimitBox")
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )
    settings.append("IsBlacklistBox")

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )
    settings.append("MachineListBox")

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )
    settings.append("LimitGroupBox")

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    #### File Settings ####
    scriptDialog.AddTabPage( "File, Frame, Misc" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "REDLine File and Frame Options", 0, 0, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "DirFileChooserLabel", "LabelControl", "Selection Method", 1, 0, "Choose the selection method by file or by directory.", False )
    DirFileChooserRC1 = scriptDialog.AddRadioControlToGrid( "DirChooser", "RadioControl", False, "Select by Directory", "SelectMethodRadioCtrl", 1, 1, "Choose a root directory to scan for all *.R3D files." )
    DirFileChooserRC1.ValueModified.connect(DirFileChooserChanged)
    DirFileChooserRC2 = scriptDialog.AddRadioControlToGrid( "FileChooser", "RadioControl", True, "Select by File", "SelectMethodRadioCtrl", 1, 2, "Choose by individual *.R3D file selection." )
    DirFileChooserRC2.ValueModified.connect(DirFileChooserChanged)
    scriptDialog.AddSelectionControlToGrid( "SubDirectoriesBox", "CheckBoxControl", True, "Process Sub-Directories",  1, 3, "Optionally choose to scan sub-directories as well for *.R3D files." )
    scriptDialog.SetEnabled( "SubDirectoriesBox", False )

    scriptDialog.AddControlToGrid( "R3DDirectoryLabel", "LabelControl", "R3D Directory", 2, 0, "Choose a root directory to scan for all *.R3D files.", False )
    scriptDialog.AddSelectionControlToGrid( "R3DDirectoryBox", "FolderBrowserControl", "", "", 2, 1, colSpan=3 )
    scriptDialog.SetEnabled( "R3DDirectoryLabel", False )
    scriptDialog.SetEnabled( "R3DDirectoryBox", False )

    scriptDialog.AddControlToGrid( "ViewTypeChooserLabel", "LabelControl", "View Type", 3, 0, "Choose single view or stereo views to transcode.", False )
    ViewChooserRC1 = scriptDialog.AddRadioControlToGrid( "ViewChooserSingle", "RadioControl", True, "Single", "SelectViewRadioCtrl", 3, 1, "Choose a single view file." )
    ViewChooserRC1.ValueModified.connect(ViewTypeChooserChanged)
    ViewChooserRC2 = scriptDialog.AddRadioControlToGrid( "ViewChooserStereo", "RadioControl", False, "Stereo (L/R)", "SelectViewRadioCtrl", 3, 2, "Choose matching stereo view files." )
    ViewChooserRC2.ValueModified.connect(ViewTypeChooserChanged)

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Input R3D Files", 4, 0, "Specify the R3D file(s) you want to render.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "MultiFileBrowserControl", "", "R3D Files (*.R3D)", 4, 1, colSpan=3 )
    settings.append("SceneBox")
    sceneBox.ValueModified.connect(SceneChanged)

    scriptDialog.AddControlToGrid( "LeftEyeLabel", "LabelControl", "LEFT Eye R3D File", 5, 0, "Specify the LEFT EYE R3D file you want to render.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "LeftEyeFileBox", "FileBrowserControl", "", "R3D File (*.R3D)", 5, 1, colSpan=3 )
    settings.append("LeftEyeFileBox")
    sceneBox.ValueModified.connect(InputFileChanged)

    scriptDialog.AddControlToGrid( "RightEyeLabel", "LabelControl", "RIGHT Eye R3D File", 6, 0, "Specify the RIGHT EYE R3D file you want to render.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "RightEyeFileBox", "FileBrowserControl", "", "R3D File (*.R3D)", 6, 1, colSpan=3 )
    settings.append("RightEyeFileBox")
    sceneBox.ValueModified.connect(InputFileChanged)

    scriptDialog.AddControlToGrid( "AudioFileLabel", "LabelControl", "Audio File (Optional)", 7, 0, "Optionally, specify an input audio file.", False )
    scriptDialog.AddSelectionControlToGrid( "AudioFileBox", "FileBrowserControl", "", "Audio File (*)", 7, 1, colSpan=3 )
    settings.append("AudioFileBox")

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Folder" , 8, 0, "The folder where the output files will be saved.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox", "FolderBrowserControl", "", "", 8, 1, colSpan=3 )
    settings.append("OutputBox")

    scriptDialog.AddControlToGrid( "OutputBaseLabel", "LabelControl", "Output Filename", 9, 0, "The prefix portion of the output filename. It is not necessary to specify the extension.", False )
    scriptDialog.AddControlToGrid( "OutputBaseBox", "TextControl", "", 9, 1 )
    settings.append("OutputBaseBox")

    #### Format Settings ####
    scriptDialog.AddControlToGrid( "OutputFormatLabel", "LabelControl", "Output Format", 9, 2, "The output format. This will determine the filename extension.", False )
    scriptDialog.AddComboControlToGrid( "OutputFormatBox", "ComboControl", "DPX", ("DPX","Tiff","OpenEXR","SGI","QT Wrappers","QT Transcode","R3D Trim","REDray","Apple ProRes","Avid DNX"), 9, 3 )
    settings.append("OutputFormatBox")

    scriptDialog.AddControlToGrid( "ResolutionLabel", "LabelControl", "Render Resolution", 10, 0, "The resolution to render at.", False )
    scriptDialog.AddComboControlToGrid( "ResolutionBox", "ComboControl", "Full", ("Full","Half High","Half Standard","Quarter","Eighth"), 10, 1 )
    scriptDialog.AddControlToGrid( "OutputPaddingLabel", "LabelControl", "Output Padding", 10, 2, "The output padding size.", False )
    scriptDialog.AddRangeControlToGrid( "OutputPaddingBox", "RangeControl", 6, 1, 10, 0, 1, 10, 3 )
    settings.append("OutputPaddingBox")

    scriptDialog.AddControlToGrid( "ColorVersionLabel", "LabelControl", "Color Science Version", 11, 0, "The color science version.", False )
    scriptDialog.AddComboControlToGrid( "ColorVersionBox", "ComboControl", "Current Version", ("Current Version","Version 1","Version 2"), 11, 1 )
    settings.append("ColorVersionBox")
    scriptDialog.AddSelectionControlToGrid( "MakeSubfolderBox", "CheckBoxControl", False, "Make Output Subfolder", 11, 2, "Makes subdirectory for each output.", False )
    settings.append("MakeSubfolderBox")

    #### Frame Settings ####
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 12, 0, "The list of frames to render if rendering an animation.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 12, 1 )
    settings.append("FramesBox")
    scriptDialog.AddControlToGrid( "RenumberLabel", "LabelControl", "Renumber Start Frame", 12, 2, "The new start frame number (optional).", False )
    scriptDialog.AddControlToGrid( "RenumberBox", "TextControl", "", 12, 3 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 13, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 13, 1 )
    settings.append("ChunkSizeBox")
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit R3D File(s) With Job", 13, 2, "If this option is enabled, the input file(s) will be submitted with the job, and then copied locally to the slave machine during rendering.", colSpan=2 )
    settings.append("SubmitSceneBox")

    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Export Preset Options", 14, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "ExportPresetLabel", "LabelControl", "Export Preset Name", 15, 0, "Optionally, load settings from an export preset: [default = none].", False )
    scriptDialog.AddControlToGrid( "ExportPresetBox", "TextControl", "", 15, 1, colSpan=3 )
    settings.append("ExportPresetBox")
    scriptDialog.AddControlToGrid( "ExportPresetFileLabel", "LabelControl", "Export Preset File", 16, 0, "Optionally, the file to load export presets from: [default = /Users/$USER/Library/Application Support/Red/RedCineX/Presets/UserExportPresets.xml].", False )
    scriptDialog.AddSelectionControlToGrid( "ExportPresetFileBox", "FileBrowserControl", "", "Export Preset File (*.xml)", 16, 1, colSpan=3 )
    settings.append("ExportPresetFileBox")

    #### Misc Settings ####
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "Misc Settings", 17, 0, colSpan=4 )

    advLutRenderBox = scriptDialog.AddSelectionControlToGrid( "OverrideAdvLutRenderBox", "CheckBoxControl", False, "Adv Lut Render", 18, 0, "Override the Adv Lut Render.", False )
    advLutRenderBox.ValueModified.connect(AdvLutRenderChanged)
    scriptDialog.AddComboControlToGrid( "AdvLutRenderBox", "ComboControl", "Assimilate 16bit LUT", ("Assimilate 16bit LUT","Shake 12bit LUT","CSP 1D (0.0-1.0)"), 18, 1 )
    settings.append("AdvLutRenderBox")

    scriptDialog.AddSelectionControlToGrid( "NoRenderBox", "CheckBoxControl", False, "No Render", 19, 0, "Forces redline to abort before any rendering occurs.", False )
    scriptDialog.AddSelectionControlToGrid( "NoAudioBox", "CheckBoxControl", False, "No Audio", 19, 1, "Disable all audio output.", False )

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage( "Stereo, Metadata, Crop, Scale, QT" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator6", "SeparatorControl", "Stereo 3D Mode", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "3dModeLabel", "LabelControl", "3D Mode", 1, 0, "3D Export Mode.", False )
    scriptDialog.AddComboControlToGrid( "3dModeBox", "ComboControl", "PixelInterleave", ("PixelInterleave","Side By Side","Right Top, Left Bottom","Left Top, Right Bottom","Row Interleave"), 1, 1, expand=True )
    settings.append("3dModeBox")

    offset3dCheckBox = scriptDialog.AddSelectionControlToGrid( "Offset3dCheckBox", "CheckBoxControl", False, "3D Offset", 1, 2, "Offset in frames of the left eye from the right (or right eye from the left if negative) [default = 0].", False )
    offset3dCheckBox.ValueModified.connect(Offset3dCheckChanged)
    scriptDialog.AddRangeControlToGrid( "Offset3dBox", "RangeControl", 0, 0, 1000, 0, 1, 1, 3 )
    settings.append("Offset3dBox")

    #### Metadata Settings ####
    scriptDialog.AddControlToGrid( "Separator7", "SeparatorControl", "Metadata Settings", 3, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "RSXLabel", "LabelControl", "Load RSX File", 4, 0, "Use look metadata in REDLine RSX file.", False )
    scriptDialog.AddSelectionControlToGrid( "RSXBox", "FileBrowserControl", "", "RSX Files (*.RSX);;All Files (*)", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "UseRSXLabel", "LabelControl", "Use RSX Defaults For", 5, 0, "What to use RSX defaults for.", False )
    scriptDialog.AddComboControlToGrid( "UseRSXBox", "ComboControl", "Color & In/Out", ("Color & In/Out","Color Only"), 5, 1, expand=True )
    
    scriptDialog.AddControlToGrid( "RMDLabel", "LabelControl", "Load RMD File", 6, 0, "Use look metadata in REDLine RMD file.", False )
    scriptDialog.AddSelectionControlToGrid( "RMDBox", "FileBrowserControl", "", "RMD Files (*.RMD);;All Files (*)", 6, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "UseRMDLabel", "LabelControl", "Use RMD Defaults For", 7, 0, "What to use RMD defaults for.", False )
    scriptDialog.AddComboControlToGrid( "UseRMDBox", "ComboControl", "Color & In/Out", ("Color & In/Out","Color Only"), 7, 1, expand=True )
    
    useMeta = scriptDialog.AddSelectionControlToGrid( "UseMetaBox", "CheckBoxControl", False, "Use Metadata In R3D File", 7, 2, "Use look metadata in R3D as defaults (overridden for each value explicitly set)." )
    useMeta.ValueModified.connect(UseMetaChanged)
    scriptDialog.AddSelectionControlToGrid( "MetaIgnoreFrameGuideBox", "CheckBoxControl", False, "Ignore Frame Guides", 7, 3, "Use in conjunction with Use Metadata checkbox. Ignores frame guides." )
    
    #### Print Meta Settings ####
    overridePrintMeta = scriptDialog.AddSelectionControlToGrid( "OverridePrintMetaCheckBox", "CheckBoxControl", False, "Print Meta", 8, 0, "Override Print Meta." )
    overridePrintMeta.ValueModified.connect(OverridePrintMetaChanged)
    scriptDialog.AddComboControlToGrid( "PrintMetaBox", "ComboControl", "normal", ("header","normal","csv","header+csv","3D rig","per-frame lens+acc+gyro"), 8, 1, expand=True )

    scriptDialog.AddControlToGrid( "ALEFileLabel", "LabelControl", "ALE File", 9, 0, "Save an ALE file with the given filename.", False )
    scriptDialog.AddSelectionControlToGrid( "ALEFileBox", "FileSaverControl", "", "ALE File (*)", 9, 1, colSpan=3 )

    overrideReelID = scriptDialog.AddSelectionControlToGrid( "OverrideReelIDCheckBox", "CheckBoxControl", False, "Reel ID", 10, 0, "Override Reel ID file naming convention." )
    overrideReelID.ValueModified.connect(OverrideReelIDChanged)
    scriptDialog.AddComboControlToGrid( "ReelIDBox", "ComboControl", "full name", ("full name","FCP 8 Character"), 10, 1, expand=True )
    
    overrideClipFrameRate = scriptDialog.AddSelectionControlToGrid( "OverrideClipFrameRateCheckBox", "CheckBoxControl", False, "Clip Frame Rate", 10, 2, "Override Clip Frame Rate.", False )
    overrideClipFrameRate.ValueModified.connect(OverrideClipFrameRateChanged)
    scriptDialog.AddComboControlToGrid( "ClipFrameRateBox", "ComboControl", "24fps", ("23.976fps","24fps","25fps","29.97fps","30fps","47.952fps","48fps","50fps","59.94fps","60fps","71.928fps","72fps"), 10, 3, expand=True )
    scriptDialog.EndGrid()
    
    #### Crop and Scale Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator8", "SeparatorControl", "Crop and Scale Settings", 0, 0, colSpan=4 )
    cropBox = scriptDialog.AddSelectionControlToGrid( "CropBox", "CheckBoxControl", False, "Crop", 1, 0, "If cropping should be enabled.", False )
    cropBox.ValueModified.connect(CropChanged)

    scriptDialog.AddControlToGrid( "CropWidthLabel", "LabelControl", "Width", 2, 0, "Crop demosaiced source before resize using Width.", False )
    scriptDialog.AddControlToGrid( "CropWidthBox", "TextControl", "", 2, 1 )
    scriptDialog.AddControlToGrid( "CropHeightLabel", "LabelControl", "Height", 2, 2, "Crop demosaiced source before resize using Height.", False )
    scriptDialog.AddControlToGrid( "CropHeightBox", "TextControl", "", 2, 3 )

    scriptDialog.AddControlToGrid( "CropOriginXLabel", "LabelControl", "Origin X", 3, 0, "Crop demosaiced source before resize using origin X.", False )
    scriptDialog.AddControlToGrid( "CropOriginXBox", "TextControl", "", 3, 1 )
    scriptDialog.AddControlToGrid( "CropOriginYLabel", "LabelControl", "Origin Y", 3, 2, "Crop demosaiced source before resize using origin Y.", False )
    scriptDialog.AddControlToGrid( "CropOriginYBox", "TextControl", "", 3, 3 )

    scaleBox = scriptDialog.AddSelectionControlToGrid( "ScaleBox", "CheckBoxControl", False, "Scale", 4, 0, "If scaling should be enabled.", False )
    scaleBox.ValueModified.connect(ScaleChanged)

    scriptDialog.AddControlToGrid( "ScaleWidthLabel", "LabelControl", "Width", 5, 0, "Resize to X dimension.", False )
    scriptDialog.AddControlToGrid( "ScaleWidthBox", "TextControl", "", 5, 1 )
    scriptDialog.AddControlToGrid( "ScaleHeightLabel", "LabelControl", "Height", 5, 2, "Resize to Y dimension.", False )
    scriptDialog.AddControlToGrid( "ScaleHeightBox", "TextControl", "", 5, 3 )

    scriptDialog.AddControlToGrid( "ScaleFitLabel", "LabelControl", "Fit/Stretch", 6, 0, "Fit source to destination.", False )
    scriptDialog.AddComboControlToGrid( "ScaleFitBox", "ComboControl", "Fit Width", ("Fit Width","Fit Height","Stretch","Fit Width 2x","Fit Width .9x","Fit Height .9x","Fit Width 1.46x","Fit Width 1.09x","Fit Width 0.5x","Fit Height 0.5x","Fit Width 1.3x","Fit Height 1.3x","Fit Width 1.25x"), 6, 1 )
    scriptDialog.AddControlToGrid( "ScaleFilterLabel", "LabelControl", "Resample Filter", 6, 2, "Filter using the selected option.", False )
    scriptDialog.AddComboControlToGrid( "ScaleFilterBox", "ComboControl", "CatmulRom (sharp)", ("Bilinear (fastest)","Bell (smoother)","Lanczos (sharper)","Quadratic (smoother)","Cubic-bspline (smoother)","CatmulRom (sharper)","Mitchell (smoother)","Gauss (smoother)","WideGauss (smoothest)","Sinc (sharpest)","Keys (sharper)","Rocket (sharper)"), 6, 3 )

    forceFlipHBox = scriptDialog.AddSelectionControlToGrid( "ForceFlipHorizontalCheckBox", "CheckBoxControl", False, "Override Flip H", 7, 0, "Override Force Flip Horizontal.", False )
    forceFlipHBox.ValueModified.connect(ForceFlipHChanged)
    scriptDialog.AddSelectionControlToGrid( "ForceFlipHorizontalBox", "CheckBoxControl", False, "Force Flip Horizontal", 7, 1, "0 = Disables any horizontal flip setting in metadata, 1 = Forces the image to be flipped horizontally.", False )
    
    forceFlipVBox = scriptDialog.AddSelectionControlToGrid( "ForceFlipVerticalCheckBox", "CheckBoxControl", False, "Override Flip V", 7, 2, "Override Force Flip Vertical.", False )
    forceFlipVBox.ValueModified.connect(ForceFlipVChanged)
    scriptDialog.AddSelectionControlToGrid( "ForceFlipVerticalBox", "CheckBoxControl", False, "Force Flip Vertical", 7, 3, "0 = Disables any vertical flip setting in metadata, 1 = Forces the image to be flipped vertically.", False )

    overrideRotateBox = scriptDialog.AddSelectionControlToGrid( "OverrideRotateCheckBox", "CheckBoxControl", False, "Override Rotate", 8, 0, "Rotates the image only 0.0, -90.0 and 90.0 degrees are currently accepted.", False )
    overrideRotateBox.ValueModified.connect(OverrideRotateChanged)
    scriptDialog.AddComboControlToGrid( "RotateBox", "ComboControl", "0.0", ("0.0","-90.0","90.0"), 8, 1 )

    overridePreventNegPixelsBox = scriptDialog.AddSelectionControlToGrid( "OverridePreventNegPixelsCheckBox", "CheckBoxControl", False, "Override Neg Pixels", 8, 2, "Override Prevent Negative Pixels.", False )
    overridePreventNegPixelsBox.ValueModified.connect(OverridePreventNegPixelsChanged)
    scriptDialog.AddSelectionControlToGrid( "PreventNegPixelsBox", "CheckBoxControl", False, "Prevent Negative Pixels", 8, 3, "Prevents the scaler from generating negative pixel values. 0=off 1=on [default = 1].", False )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    #### Quicktime Transcode Settings ####
    scriptDialog.AddTabPage( "QT Transcode, Burn-In" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator9", "SeparatorControl", "Quicktime Transcode Settings", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "QTCodecLabel", "LabelControl", "Codec", 1, 0, "QT codec to output.", False )
    scriptDialog.AddComboControlToGrid( "QTCodecBox", "ComboControl", "Apple ProRes 422 (HQ)", ("Apple ProRes 422 (HQ)","Apple ProRes 422","H.264","MJPEG A","MJPEG B","JPEG","Component","H.263","None","Pixlet","DVCPRO720","Animation/RLE","Uncompressed 8-bit 4:2:2","Uncompressed 10-bit 4:2:2","AVID DNxHD","BlackMagic RGB 10bit","AJA Kona 10bit Log RGB","AJA Kona 10bit RGB","AVID 1080P DNxHD 36 8-bit (23.98, 24, 25)","AVID 1080P DNxHD 115/120 8-bit (23.98, 24, 25)","AVID 1080P DNxHD 175/185 8-bit (23.98, 24, 25)","AVID 1080P DNxHD 175/185 10-bit (23.98, 24, 25)","AVID 720P DNxHD 60/75 8-bit (23.98, 25, 29.97)","AVID 720P DNxHD 90/110 8-bit (23.98, 29.97)","AVID 720P DNxHD 90/110 10-bit (23.98, 29.97)","AVID 720P DNxHD 120/145 8-bit (50, 59.94)","AVID 720P DNxHD 185/220 8-bit (50, 59.94)","AVID 720P DNxHD 185/220 10-bit (50, 59.94)","Apple ProRes 4444","Apple ProRes 422 LT","Apple ProRes 422 Proxy"), 1, 1, expand=False )
    settings.append("QTCodecBox")
    scriptDialog.AddSelectionControlToGrid( "QTClobberBox", "CheckBoxControl", True, "Clobber Existing QT File", 1, 2, "Do clobber an existing QT file. If disabled, '_Sxxx' will be added for each new file." )
    scriptDialog.EndGrid()

    #### Burn-In Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator10", "SeparatorControl", "Burn-In Settings", 0, 0, colSpan=4 )
    
    burnBox = scriptDialog.AddSelectionControlToGrid( "BurnBox", "CheckBoxControl", False, "Burn In", 1, 0, "Turn on burn in.", colSpan=3 )
    burnBox.ValueModified.connect(BurnChanged)

    scriptDialog.AddControlToGrid( "BurnFramesLabel", "LabelControl", "Frames", 2, 0, "Do burn in for the specified frames.", False )
    burnFramesBox = scriptDialog.AddComboControlToGrid( "BurnFramesBox", "ComboControl", "All", ("All","First","First & Last","Last","Count"), 2, 1 )
    burnFramesBox.ValueModified.connect(BurnFramesChanged)
    scriptDialog.AddControlToGrid( "BurnFramesCountLabel", "LabelControl", "Frames Count", 2, 2, "Number of frames to burn in [default = 1].", False )
    scriptDialog.AddRangeControlToGrid( "BurnFramesCountBox", "RangeControl", 1, 1, 1000, 0, 1, 2, 3 )

    scriptDialog.AddControlToGrid( "BurnFontLabel", "LabelControl", "Font", 3, 0, "The burn in font.", False )
    scriptDialog.AddComboControlToGrid( "BurnFontBox", "ComboControl", "Letter Gothic", ("Letter Gothic","Monaco","Courier","Lucida Type","Andale Mono","OCRA","Orator Std"), 3, 1 )

    scriptDialog.AddControlToGrid( "BurnSizeLabel", "LabelControl", "Text Height %", 4, 0, "Height of text in percent of output height.", False )
    scriptDialog.AddRangeControlToGrid( "BurnSizeBox", "RangeControl", 20.0, 0.0, 100.0, 6, 1, 4, 1 )
    scriptDialog.AddControlToGrid( "BurnBaseLabel", "LabelControl", "Text Origin Y %", 4, 2, "Burn in Y location in percent of output height.", False )
    scriptDialog.AddRangeControlToGrid( "BurnBaseBox", "RangeControl", 20.0, 0.0, 100.0, 6, 1, 4, 3 )

    scriptDialog.AddControlToGrid( "BurnLowerLeftLabel", "LabelControl", "Lower Left", 5, 0, "The burn in for the lower left.", False )
    scriptDialog.AddComboControlToGrid( "BurnLowerLeftBox", "ComboControl", "Reel/Filename", ("Reel/Filename","Frames","Frames In Edit","Frames In Source","Edge Code","EXT/TOD Time Code"), 5, 1 )
    scriptDialog.AddControlToGrid( "BurnLowerRightLabel", "LabelControl", "Lower Right", 5, 2, "The burn in for the lower right.", False )
    scriptDialog.AddComboControlToGrid( "BurnLowerRightBox", "ComboControl", "Reel/Filename", ("Reel/Filename","Frames","Frames In Edit","Frames In Source","Edge Code","EXT/TOD Time Code"), 5, 3 )

    scriptDialog.AddControlToGrid( "BurnUpperLeftLabel", "LabelControl", "Upper Left", 6, 0, "The burn in for the upper left.", False )
    scriptDialog.AddComboControlToGrid( "BurnUpperLeftBox", "ComboControl", "Reel/Filename", ("Reel/Filename","Frames","Frames In Edit","Frames In Source","Edge Code","EXT/TOD Time Code"), 6, 1 )
    scriptDialog.AddControlToGrid( "BurnUpperRightLabel", "LabelControl", "Upper Right", 6, 2, "The burn in for the upper right.", False )
    scriptDialog.AddComboControlToGrid( "BurnUpperRightBox", "ComboControl", "Reel/Filename", ("Reel/Filename","Frames","Frames In Edit","Frames In Source","Edge Code","EXT/TOD Time Code"), 6, 3 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "BurnTextLabel", "LabelControl", "Text RGBA", 0, 0, "Text channels (red, green, blue, and alpha respectively).", False )
    scriptDialog.AddRangeControlToGrid( "BurnTextRBox", "RangeControl", 0.0, 0.0, 1.0, 6, 0.1, 0, 1 )
    scriptDialog.AddRangeControlToGrid( "BurnTextGBox", "RangeControl", 0.0, 0.0, 1.0, 6, 0.1, 0, 2 )
    scriptDialog.AddRangeControlToGrid( "BurnTextBBox", "RangeControl", 0.0, 0.0, 1.0, 6, 0.1, 0, 3 )
    scriptDialog.AddRangeControlToGrid( "BurnTextABox", "RangeControl", 1.0, 0.0, 1.0, 6, 0.1, 0, 4 )

    scriptDialog.AddControlToGrid( "BurnBackgroundLabel", "LabelControl", "Background RGBA", 1, 0, "Background channels (red, green, blue, and alpha respectively).", False )
    scriptDialog.AddRangeControlToGrid( "BurnBackgroundRBox", "RangeControl", 0.0, 0.0, 1.0, 6, 0.1, 1, 1 )
    scriptDialog.AddRangeControlToGrid( "BurnBackgroundGBox", "RangeControl", 0.0, 0.0, 1.0, 6, 0.1, 1, 2 )
    scriptDialog.AddRangeControlToGrid( "BurnBackgroundBBox", "RangeControl", 0.0, 0.0, 1.0, 6, 0.1, 1, 3 )
    scriptDialog.AddRangeControlToGrid( "BurnBackgroundABox", "RangeControl", 1.0, 0.0, 1.0, 6, 0.1, 1, 4 )
    scriptDialog.EndGrid()

    #### Watermark Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator11", "SeparatorControl", "Watermark Settings", 0, 0, colSpan=4 )

    watermarkBox = scriptDialog.AddSelectionControlToGrid( "WatermarkBox", "CheckBoxControl", False, "Watermarking", 1, 0, "Turn on watermarking.", colSpan=4 )
    watermarkBox.ValueModified.connect(WatermarkChanged)
    
    scriptDialog.AddControlToGrid( "WatermarkFontLabel", "LabelControl", "Font", 2, 0, "The watermark font to use.", False )
    scriptDialog.AddComboControlToGrid( "WatermarkFontBox", "ComboControl", "Letter Gothic", ("Letter Gothic","Andale Mono","OCRA","DejaVu Sans Mono"), 2, 1 )
    scriptDialog.AddControlToGrid( "WatermarkTextLabel", "LabelControl", "Text", 2, 2, "Enter the text to be displayed in the watermark.", False )
    scriptDialog.AddControlToGrid( "WatermarkTextBox", "TextControl", "", 2, 3, colSpan=1 )

    scriptDialog.AddControlToGrid( "WatermarkSzLabel", "LabelControl", "Size %", 4, 0, "Height of text in percent of output height [default = 5].", False )
    scriptDialog.AddRangeControlToGrid( "WatermarkSzBox", "RangeControl", 5.0, 0.0, 100.0, 1, 1.0, 4, 1 )
    scriptDialog.AddControlToGrid( "WatermarkBaseLabel", "LabelControl", "Base %", 4, 2, "Watermark Y location in percent of height [default = 20].", False )
    scriptDialog.AddRangeControlToGrid( "WatermarkBaseBox", "RangeControl", 20.0, 0.0, 100.0, 1, 1.0, 4, 3 )

    scriptDialog.AddControlToGrid( "WatermarkTxtRLabel", "LabelControl", "Text R", 5, 0, "Text red channel (0-1.0) [default = 1.0].", False )
    scriptDialog.AddRangeControlToGrid( "WatermarkTxtRBox", "RangeControl", 1.0, 0.0, 1.0, 1, 0.1, 5, 1 )
    scriptDialog.AddControlToGrid( "WatermarkTxtGLabel", "LabelControl", "Text G", 5, 2, "Text green channel (0-1.0) [default = 1.0].", False )
    scriptDialog.AddRangeControlToGrid( "WatermarkTxtGBox", "RangeControl", 1.0, 0.0, 1.0, 1, 0.1, 5, 3 )

    scriptDialog.AddControlToGrid( "WatermarkTxtBLabel", "LabelControl", "Text B", 6, 0, "Text blue channel (0-1.0) [default = 1.0].", False )
    scriptDialog.AddRangeControlToGrid( "WatermarkTxtBBox", "RangeControl", 1.0, 0.0, 1.0, 1, 0.1, 6, 1 )
    scriptDialog.AddControlToGrid( "WatermarkTxtALabel", "LabelControl", "Text Alpha", 6, 2, "Text alpha channel (0-1.0) [default = 0.8].", False )
    scriptDialog.AddRangeControlToGrid( "WatermarkTxtABox", "RangeControl", 0.8, 0.0, 1.0, 1, 0.1, 6, 3 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    #### Color/Gamma Space Settings ####
    scriptDialog.AddTabPage( "Color, Gamma, Curve" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator12", "SeparatorControl", "Color/Gamma Space Settings", 0, 0, colSpan=4 )

    colorSpaceBox = scriptDialog.AddSelectionControlToGrid( "ColorSpaceCheckBox", "CheckBoxControl", False, "Color Space", 1, 0, "Override the color space option.", False )
    colorSpaceBox.ValueModified.connect(ColorSpaceChanged)
    scriptDialog.AddComboControlToGrid( "ColorSpaceBox", "ComboControl", "REDspace", ("REDspace","Camera RGB","REC709","REDcolor","sRGB","Adobe1998","REDcolor2","REDcolor3","DRAGONcolor","XYZ","REDcolor4","DRAGONcolor2","rec2020","REDWideGamutRGB"), 1, 1 )

    gammaCurveBox = scriptDialog.AddSelectionControlToGrid( "GammaCurveCheckBox", "CheckBoxControl", False, "LUT/Gamma Curve", 1, 2, "Override the gamma curve.", False )
    gammaCurveBox.ValueModified.connect(GammaCurveChanged)
    scriptDialog.AddComboControlToGrid( "GammaCurveBox", "ComboControl", "REDspace", ("Linear Light","REC709","sRGB","REDlog","PDlog 985","PDlog 685","PDLogCustom","REDspace","REDgamma","REDLogFilm","REDgamma2","REDgamma3","REDgamma4","HDR-2084","BT1886","Log3G12","Log3G10"), 1, 3 )

    noiseReductionBox = scriptDialog.AddSelectionControlToGrid( "NoiseReductionCheckBox", "CheckBoxControl", False, "Chroma Denoise", 2, 0, "Override the noise reduction.", False )
    noiseReductionBox.ValueModified.connect(NoiseReductionChanged)
    scriptDialog.AddComboControlToGrid( "NoiseReductionBox", "ComboControl", "Mild", ("Off","Very Mild","Milder","Mild","Medium","Strong","Max"), 2, 1 )

    detailBox = scriptDialog.AddSelectionControlToGrid( "DetailCheckBox", "CheckBoxControl", False, "Debayer Detail", 2, 2, "Override the detail.", False )
    detailBox.ValueModified.connect(DetailChanged)
    scriptDialog.AddComboControlToGrid( "DetailBox", "ComboControl", "High", ("Leading Lady","Medium","High"), 2, 3 )

    olpfBox = scriptDialog.AddSelectionControlToGrid( "OLPFCompensationCheckBox", "CheckBoxControl", False, "OLPF Compensation", 3, 0, "Override the post sharpen.", False)
    olpfBox.ValueModified.connect(OLPFCompensationChanged)
    scriptDialog.AddComboControlToGrid( "OLPFCompensationBox", "ComboControl", "Off", ("Off","Low","Medium","High"), 3, 1 )

    smpteColorBox = scriptDialog.AddSelectionControlToGrid( "SMPTEColorRangeCheckBox", "CheckBoxControl", False, "SMPTE Color Range", 3, 2, "Override the SMPTE color range.", False )
    smpteColorBox.ValueModified.connect(SMPTEColorRangeChanged)
    scriptDialog.AddComboControlToGrid( "SMPTEColorRangeBox", "ComboControl", "Off", ("On","Off"), 3, 3 )

    #### Color Settings ####
    scriptDialog.AddControlToGrid( "Separator13", "SeparatorControl", "Color Settings", 4, 0, colSpan=4 )

    # ISO
    isoBox = scriptDialog.AddSelectionControlToGrid( "ISOCheckBox", "CheckBoxControl", False, "ISO", 5, 0, "Override ISO.", False )
    isoBox.ValueModified.connect(ISOChanged)
    scriptDialog.AddRangeControlToGrid( "ISOBox", "RangeControl", 320, 100, 2000, 0, 10, 5, 1 )

    # FLUT ***NEW***
    flutBox = scriptDialog.AddSelectionControlToGrid( "FlutCheckBox", "CheckBoxControl", False, "Flut", 5, 2, "Override Flut.", False )
    flutBox.ValueModified.connect(FlutChanged)
    scriptDialog.AddRangeControlToGrid( "FlutBox", "RangeControl", 0.0, -8.0, 8.0, 1, 0.1, 5, 3 )

    # SHADOW ***NEW***
    shadowBox = scriptDialog.AddSelectionControlToGrid( "ShadowCheckBox", "CheckBoxControl", False, "Shadow", 6, 0, "Override Shadow.", False )
    shadowBox.ValueModified.connect(ShadowChanged)
    scriptDialog.AddRangeControlToGrid( "ShadowBox", "RangeControl", 0.0, -2.0, 2.0, 1, 0.1, 6, 1 )

    # KELVIN
    kelvinBox = scriptDialog.AddSelectionControlToGrid( "KelvinCheckBox", "CheckBoxControl", False, "Kelvin", 6, 2, "Override kelvin.", False )
    kelvinBox.ValueModified.connect(KelvinChanged)
    scriptDialog.AddRangeControlToGrid( "KelvinBox", "RangeControl", 5600, 1700, 50000, 0, 100, 6, 3 )

    # TINT
    tintBox = scriptDialog.AddSelectionControlToGrid( "TintCheckBox", "CheckBoxControl", False, "Tint", 7, 0, "Override tint.", False )
    tintBox.ValueModified.connect(TintChanged)
    scriptDialog.AddRangeControlToGrid( "TintBox", "RangeControl", 0.0, -100.0, 100.0, 6, 1.0, 7, 1 )

    # EXPOSURE
    exposureBox = scriptDialog.AddSelectionControlToGrid( "ExposureCheckBox", "CheckBoxControl", False, "Exposure", 7, 2, "Override exposure.", False )
    exposureBox.ValueModified.connect(ExposureChanged)
    scriptDialog.AddRangeControlToGrid( "ExposureBox", "RangeControl", 0.0, -12.0, 12.0, 6, 1.0, 7, 3 )    

    # SATURATION
    saturationBox = scriptDialog.AddSelectionControlToGrid( "SaturationCheckBox", "CheckBoxControl", False, "Saturation", 8, 0, "Override saturation.", False )
    saturationBox.ValueModified.connect(SaturationChanged)
    scriptDialog.AddRangeControlToGrid( "SaturationBox", "RangeControl", 1.0, 0.0, 2.0, 6, 0.1, 8, 1 )

    # CONTRAST
    contrastBox = scriptDialog.AddSelectionControlToGrid( "ContrastCheckBox", "CheckBoxControl", False, "Contrast", 8, 2, "Override constrast.", False )
    contrastBox.ValueModified.connect(ContrastChanged)
    scriptDialog.AddRangeControlToGrid( "ContrastBox", "RangeControl", 0.0, -1.0, 1.0, 6, 0.1, 8, 3 )

    # BRIGHTNESS
    brightnessBox = scriptDialog.AddSelectionControlToGrid( "BrightnessCheckBox", "CheckBoxControl", False, "Brightness", 9, 0, "Override brightness.", False )
    brightnessBox.ValueModified.connect(BrightnessChanged)
    scriptDialog.AddRangeControlToGrid( "BrightnessBox", "RangeControl", 0.0, -10.0, 50.0, 6, 1.0, 9, 1 )    

    # RED GAIN
    redBox = scriptDialog.AddSelectionControlToGrid( "RedCheckBox", "CheckBoxControl", False, "Red", 9, 2, "Override reg gain.", False )
    redBox.ValueModified.connect(RedChanged)
    scriptDialog.AddRangeControlToGrid( "RedBox", "RangeControl", 1.0, 0.0, 4.0, 6, 0.1, 9, 3 )    

    # GREEN GAIN
    greenBox = scriptDialog.AddSelectionControlToGrid( "GreenCheckBox", "CheckBoxControl", False, "Green", 10, 0, "Override green gain.", False )
    greenBox.ValueModified.connect(GreenChanged)
    scriptDialog.AddRangeControlToGrid( "GreenBox", "RangeControl", 1.0, 0.0, 4.0, 6, 0.1, 10, 1 )

    # BLUE GAIN
    blueBox = scriptDialog.AddSelectionControlToGrid( "BlueCheckBox", "CheckBoxControl", False, "Blue", 10, 2, "Override blue gain.", False )
    blueBox.ValueModified.connect(BlueChanged)
    scriptDialog.AddRangeControlToGrid( "BlueBox", "RangeControl", 1.0, 0.0, 4.0, 6, 0.1, 10, 3 )

    # DRX
    drxBox = scriptDialog.AddSelectionControlToGrid( "DRXCheckBox", "CheckBoxControl", False, "DRX", 11, 0, "Override dynamic range extender.", False )
    drxBox.ValueModified.connect(DRXChanged)
    scriptDialog.AddRangeControlToGrid( "DRXBox", "RangeControl", 0.5, 0.0, 1.0, 6, 0.1, 11, 1 )

    # DEB ***NEW***
    debBox = scriptDialog.AddSelectionControlToGrid( "DEBCheckBox","CheckBoxControl", False, "DEB", 11, 2, "Override dragon enhanced blacks.", False )
    debBox.ValueModified.connect(DEBChanged)
    scriptDialog.AddComboControlToGrid( "DEBBox", "ComboControl", "Off", ("Off","On"), 11, 3 )
    scriptDialog.EndGrid()

    #### Lift Gamma Gain Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator14", "SeparatorControl", "Lift Gamma Gain Settings", 0, 0, colSpan=6 )

    # LIFT
    redLiftBox = scriptDialog.AddSelectionControlToGrid( "RedLiftCheckBox", "CheckBoxControl", False, "Red Lift", 1, 0, "Override Red Lift.", False )
    redLiftBox.ValueModified.connect(RedLiftChanged)
    scriptDialog.AddRangeControlToGrid( "RedLiftBox", "RangeControl", 0.0, -1.0, 1.0, 1, 0.1, 1, 1 )

    greenLiftBox = scriptDialog.AddSelectionControlToGrid( "GreenLiftCheckBox", "CheckBoxControl", False, "Green Lift", 1, 2, "Override Green Lift.", False )
    greenLiftBox.ValueModified.connect(GreenLiftChanged)
    scriptDialog.AddRangeControlToGrid( "GreenLiftBox", "RangeControl", 0.0, -1.0, 1.0, 1, 0.1, 1, 3 )

    blueLiftBox = scriptDialog.AddSelectionControlToGrid( "BlueLiftCheckBox", "CheckBoxControl", False, "Blue Lift", 1, 4, "Override Blue Lift.", False )
    blueLiftBox.ValueModified.connect(BlueLiftChanged)
    scriptDialog.AddRangeControlToGrid( "BlueLiftBox", "RangeControl", 0.0, -1.0, 1.0, 1, 0.1, 1, 5 )

    # GAMMA
    redGammaBox = scriptDialog.AddSelectionControlToGrid( "RedGammaCheckBox", "CheckBoxControl", False, "Red Gamma", 2, 0, "Override Red Gamma.", False )
    redGammaBox.ValueModified.connect(RedGammaChanged)
    scriptDialog.AddRangeControlToGrid( "RedGammaBox", "RangeControl", 1.0, 0.0, 4.0, 1, 0.1, 2, 1 )

    greenGammaBox = scriptDialog.AddSelectionControlToGrid( "GreenGammaCheckBox", "CheckBoxControl", False, "Green Gamma", 2, 2, "Override Green Gamma.", False )
    greenGammaBox.ValueModified.connect(GreenGammaChanged)
    scriptDialog.AddRangeControlToGrid( "GreenGammaBox", "RangeControl", 1.0, 0.0, 4.0, 1, 0.1, 2, 3 )

    blueGammaBox = scriptDialog.AddSelectionControlToGrid( "BlueGammaCheckBox", "CheckBoxControl", False, "Blue Gamma", 2, 4, "Override Blue Gamma.", False )
    blueGammaBox.ValueModified.connect(BlueGammaChanged)
    scriptDialog.AddRangeControlToGrid( "BlueGammaBox", "RangeControl", 1.0, 0.0, 4.0, 1, 0.1, 2, 5 )

    # GAIN
    redGainBox = scriptDialog.AddSelectionControlToGrid( "RedGainCheckBox", "CheckBoxControl", False, "Red Gain", 3, 0, "Override Red Gain.", False )
    redGainBox.ValueModified.connect(RedGainChanged)
    scriptDialog.AddRangeControlToGrid( "RedGainBox", "RangeControl", 1.0, 0.0, 2.0, 1, 0.1, 3, 1 )

    greenGainBox = scriptDialog.AddSelectionControlToGrid( "GreenGainCheckBox", "CheckBoxControl", False, "Green Gain", 3, 2, "Override Green Gain.", False )
    greenGainBox.ValueModified.connect(GreenGainChanged)
    scriptDialog.AddRangeControlToGrid( "GreenGainBox", "RangeControl", 1.0, 0.0, 2.0, 1, 0.1, 3, 3 )

    blueGainBox = scriptDialog.AddSelectionControlToGrid( "BlueGainCheckBox", "CheckBoxControl", False, "Blue Gain", 3, 4, "Override Blue Gain.", False )
    blueGainBox.ValueModified.connect(BlueGainChanged)
    scriptDialog.AddRangeControlToGrid( "BlueGainBox", "RangeControl", 1.0, 0.0, 2.0, 1, 0.1, 3, 5 )

    #### Print Density Settings ####
    scriptDialog.AddControlToGrid( "Separator15", "SeparatorControl", "Print Density Settings", 4, 0, colSpan=6 )

    pdBlackBox = scriptDialog.AddSelectionControlToGrid( "PdBlackCheckBox", "CheckBoxControl", False, "PD Black", 5, 0, "Override Print Density Black.", False )
    pdBlackBox.ValueModified.connect(PdBlackChanged)
    scriptDialog.AddRangeControlToGrid( "PdBlackBox", "RangeControl", 95, 0, 511, 0, 1, 5, 1 )

    pdWhiteBox = scriptDialog.AddSelectionControlToGrid( "PdWhiteCheckBox", "CheckBoxControl", False, "PD White", 5, 2, "Override Print Density White.", False )
    pdWhiteBox.ValueModified.connect(PdWhiteChanged)
    scriptDialog.AddRangeControlToGrid( "PdWhiteBox", "RangeControl", 685, 512, 1023, 0, 1, 5, 3 )

    pdGammaBox = scriptDialog.AddSelectionControlToGrid( "PdGammaCheckBox", "CheckBoxControl", False, "PD Gamma", 5, 4, "Override Print Density Gamma.", False )
    pdGammaBox.ValueModified.connect(PdGammaChanged)
    scriptDialog.AddRangeControlToGrid( "PdGammaBox", "RangeControl", 0.6, 0.0, 2.0, 1, 0.1, 5, 5 )

    #### Curve Settings ####
    scriptDialog.AddControlToGrid( "Separator16", "SeparatorControl", "Curve Settings", 6, 0, colSpan=6 )

    blackBox = scriptDialog.AddSelectionControlToGrid( "BlackCheckBox", "CheckBoxControl", False, "Black", 7, 0, "Override Black Curve.", False )
    blackBox.ValueModified.connect(BlackChanged)
    scriptDialog.AddRangeControlToGrid( "BlackBox", "RangeControl", 0, 0, 100, 0, 1, 7, 1 )

    whiteBox = scriptDialog.AddSelectionControlToGrid( "WhiteCheckBox", "CheckBoxControl", False, "White", 7, 2, "Override White Curve.", False )
    whiteBox.ValueModified.connect(WhiteChanged)
    scriptDialog.AddRangeControlToGrid( "WhiteBox", "RangeControl", 100, 0, 100, 0, 1, 7, 3 )

    #### New Curve Point Values ####
    lumaCurveBox = scriptDialog.AddSelectionControlToGrid( "LumaCurveCheckBox", "CheckBoxControl", False, "Luma Curve", 8, 0, "Override Luma Curve. Enter 10 integer values separated by colon character.", False )
    lumaCurveBox.ValueModified.connect(LumaCurveChanged)
    scriptDialog.AddControlToGrid( "LumaCurveBox", "TextControl", "0:0:25:25:50:50:75:75:100:100", 8, 1, colSpan=2 )

    redCurveBox = scriptDialog.AddSelectionControlToGrid( "RedCurveCheckBox", "CheckBoxControl", False, "Red Curve", 8, 3, "Override Red Curve. Enter 10 integer values separated by colon character.", False )
    redCurveBox.ValueModified.connect(RedCurveChanged)
    scriptDialog.AddControlToGrid( "RedCurveBox", "TextControl", "0:0:25:25:50:50:75:75:100:100", 8, 4, colSpan=2 )

    greenBox = scriptDialog.AddSelectionControlToGrid( "GreenCurveCheckBox", "CheckBoxControl", False, "Green Curve", 9, 0, "Override Green Curve. Enter 10 integer values separated by colon character.", False )
    greenBox.ValueModified.connect(GreenCurveChanged)
    scriptDialog.AddControlToGrid( "GreenCurveBox", "TextControl", "0:0:25:25:50:50:75:75:100:100", 9, 1, colSpan=2 )

    blueBox = scriptDialog.AddSelectionControlToGrid( "BlueCurveCheckBox", "CheckBoxControl", False, "Blue Curve", 9, 3, "Override Blue Curve. Enter 10 integer values separated by colon character.", False )
    blueBox.ValueModified.connect(BlueCurveChanged)
    scriptDialog.AddControlToGrid( "BlueCurveBox", "TextControl", "0:0:25:25:50:50:75:75:100:100", 9, 4, colSpan=2 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.AddTabPage( "File Format" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator17", "SeparatorControl", "HDR Settings", 0, 0, colSpan=4 )
    
    #### HDR Settings ####
    hdrMode = scriptDialog.AddSelectionControlToGrid( "HdrModeCheckBox", "CheckBoxControl", False, "HDR Mode", 1, 0, "Override the HDR mode.", False )
    hdrMode.ValueModified.connect(HdrModeChanged)
    hdrModeChoice = scriptDialog.AddComboControlToGrid( "HdrModeBox", "ComboControl", "A Frame", ("A Frame","X Frame","Simple Blend","Magic Motion"), 1, 1 )
    hdrModeChoice.ValueModified.connect(HdrModeChoiceChanged)
    scriptDialog.AddControlToGrid( "HdrBiasLabel", "LabelControl", "HDR Bias", 1, 2, "HDR Bias (for Simple Blend and Magic Motion modes only) [default=0.0, range = -1.0 to 1.0].", False )
    scriptDialog.AddRangeControlToGrid( "HdrBiasBox", "RangeControl", 0.0, -1.0, 1.0, 1, 0.1, 1, 3 )
    scriptDialog.EndGrid()

    #### DPX Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator18", "SeparatorControl", "DPX Settings", 0, 0, colSpan=6 )

    dpxByteOrder = scriptDialog.AddSelectionControlToGrid( "DpxByteOrderCheckBox", "CheckBoxControl", False, "Byte Order", 1, 0, "Override DPX Byte Order.", False )
    dpxByteOrder.ValueModified.connect(DpxByteOrderChanged)
    scriptDialog.AddComboControlToGrid( "DpxByteOrderBox", "ComboControl", "LSB", ("LSB","MSB"), 1, 1 )

    dpxBitDepth = scriptDialog.AddSelectionControlToGrid( "DpxBitDepthCheckBox", "CheckBoxControl", False, "Bit Depth", 1, 2, "Override DPX Bit Depth.", False )
    dpxBitDepth.ValueModified.connect(DpxBitDepthChanged)
    scriptDialog.AddComboControlToGrid( "DpxBitDepthBox", "ComboControl", "10", ("10","16"), 1, 3 )

    dpxMaxWriters = scriptDialog.AddSelectionControlToGrid( "DpxMaxWritersCheckBox", "CheckBoxControl", False, "Max Writers", 1, 4, "Override DPX Max Simultaneous Writers.", False )
    dpxMaxWriters.ValueModified.connect(DpxMaxWritersChanged)
    scriptDialog.AddRangeControlToGrid( "DpxMaxWritersBox", "RangeControl", 10, 1, 64, 0, 1, 1, 5 )
    scriptDialog.EndGrid()

    #### OpenEXR Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator19", "SeparatorControl", "EXR Settings", 0, 0, colSpan=4 )

    exrCompression = scriptDialog.AddSelectionControlToGrid( "ExrCompressionCheckBox", "CheckBoxControl", False, "Compression", 1, 0, "Override EXR compression.", False )
    exrCompression.ValueModified.connect(ExrCompressionChanged)
    exrCompressionChoice = scriptDialog.AddComboControlToGrid( "ExrCompressionBox", "ComboControl", "NONE", ("NONE","RLE","ZIPS","ZIP","PIZ","PXR24","B44","B44A","DWAA","DWAB"), 1, 1 )
    exrCompressionChoice.ValueModified.connect(ExrCompressionChoiceChanged)
    scriptDialog.AddControlToGrid( "ExrCompressionDwaaLabel", "LabelControl", "DWAA Compression", 1, 2, "OpenEXR DWA Compression Level [default = 45, range 25 - 100].", False )
    scriptDialog.AddRangeControlToGrid( "ExrCompressionDwaaBox", "RangeControl", 45, 25, 100, 0, 1, 1, 3 )

    exrMultiView = scriptDialog.AddSelectionControlToGrid( "ExrMultiViewCheckBox", "CheckBoxControl", False, "Multi View", 2, 0, "Override OpenEXR MultiView: Dual Channel=1, Single Channel=0 [default=0].", False )
    exrMultiView.ValueModified.connect(ExrMultiViewChanged)
    scriptDialog.AddComboControlToGrid( "ExrMultiViewBox", "ComboControl", "Single Channel", ("Single Channel","Dual Channel"), 2, 1 )

    exrMaxWriters = scriptDialog.AddSelectionControlToGrid( "ExrMaxWritersCheckBox", "CheckBoxControl", False, "Max Writers", 2, 2, "Override OpenEXR Max Simultaneous Writers [default = 10, range = 1 - 64].", False )
    exrMaxWriters.ValueModified.connect(ExrMaxWritersChanged)
    scriptDialog.AddRangeControlToGrid( "ExrMaxWritersBox", "RangeControl", 10, 1, 64, 0, 1, 2, 3 )

    exrAces = scriptDialog.AddSelectionControlToGrid( "ExrAcesCheckBox", "CheckBoxControl", False, "ACES", 3, 0, "Override OpenEXR ACES: On=1, Off=0 [default=0].", False )
    exrAces.ValueModified.connect(ExrAcesChanged)
    scriptDialog.AddComboControlToGrid( "ExrAcesBox", "ComboControl", "Off", ("Off","On"), 3, 1 )

    exrSoftClamp = scriptDialog.AddSelectionControlToGrid( "ExrSoftClampCheckBox", "CheckBoxControl", False, "Soft Clamp", 3, 2, "Override OpenEXR Soft Clamp: On=1, Off=0 [default=0].", False )
    exrSoftClamp.ValueModified.connect(ExrSoftClampChanged)
    scriptDialog.AddComboControlToGrid( "ExrSoftClampBox", "ComboControl", "Off", ("Off","On"), 3, 3 )
    scriptDialog.EndGrid()

    #### R3D Trim Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator20", "SeparatorControl", "R3D Trim Settings", 0, 0, colSpan=4 )

    scriptDialog.AddSelectionControlToGrid( "R3dTrimRmdSidecarBox", "CheckBoxControl", False, "Include RMD Sidecar", 1, 0, "Include RMD sidecar.", False )
    scriptDialog.AddSelectionControlToGrid( "R3dTrimQtWrappersBox", "CheckBoxControl", False, "Include QT Wrappers", 1, 1, "Include Qt Wrappers.", False )
    
    r3dTrimFcpXml = scriptDialog.AddSelectionControlToGrid( "R3dTrimFcpXmlCheckBox", "CheckBoxControl", False, "Include FCP XML", 1, 2, "Override Include FCP XML.", False )
    r3dTrimFcpXml.ValueModified.connect(R3dTrimFcpXmlChanged)
    scriptDialog.AddComboControlToGrid( "R3dTrimFcpXmlBox", "ComboControl", "No FCP XML", ("No FCP XML","Full","Half","Quarter","Eighth"), 1, 3 )

    scriptDialog.AddSelectionControlToGrid( "R3dTrimAudioBox", "CheckBoxControl", False, "Include Audio", 2, 0, "Include Audio in R3D Trim.", False )
    
    r3dTrimChangeFrameRate = scriptDialog.AddSelectionControlToGrid( "R3dTrimChangeFrameRateCheckBox", "CheckBoxControl", False, "Clip Framerate", 2, 1, "Change Clip Framerate.", False )
    r3dTrimChangeFrameRate.ValueModified.connect(R3dTrimChangeFrameRateChanged)
    scriptDialog.AddComboControlToGrid( "R3dTrimChangeFrameRateBox", "ComboControl", "24fps", ("23.976fps","24fps","25fps","29.97fps","30fps","47.952fps","48fps","50fps","59.94fps","60fps","71.928fps","72fps"), 2, 2 )

    r3dTrimChangeOLPF = scriptDialog.AddSelectionControlToGrid( "R3dTrimChangeOLPFCheckBox", "CheckBoxControl", False, "Clip's OLPF", 3, 0, "Change the clip's OLPF.  Use --olpfLookup to get available OLPF IDs for a clip.", False )
    r3dTrimChangeOLPF.ValueModified.connect(R3dTrimChangeOLPFChanged)
    scriptDialog.AddRangeControlToGrid( "R3dTrimChangeOLPFBox", "RangeControl", 1, 1, 1000, 0, 1, 3, 1 )
    scriptDialog.EndGrid()

    #### Avid DNX Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator21", "SeparatorControl", "Avid DNX Settings", 0, 0, colSpan=4 )

    dnxCodec = scriptDialog.AddSelectionControlToGrid( "DnxCodecCheckBox", "CheckBoxControl", False, "DNX Codec", 1, 0, "Avid DNX Codec to output [default = DNxHR HQ].", False )
    dnxCodec.ValueModified.connect(DnxCodecChanged)
    scriptDialog.AddComboControlToGrid( "DnxCodecBox", "ComboControl", "Avid DNxHR HQ", ("Avid DNxHR 444","Avid DNxHR HQX","Avid DNxHR HQ","Avid DNxHR SQ","Avid DNxHR LB"), 1, 1 )

    dnxFrameRate = scriptDialog.AddSelectionControlToGrid( "DnxFrameRateCheckBox", "CheckBoxControl", False, "Media Framerate", 1, 2, "Avid Media Framerate [default = 23.98].", False )
    dnxFrameRate.ValueModified.connect(DnxFrameRateChanged)
    scriptDialog.AddComboControlToGrid( "DnxFrameRateBox", "ComboControl", "23.976", ("23.976","24","25","29.97","30","50","59.94","60"), 1, 3 )
    scriptDialog.EndGrid()
    
    #### REDray Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator22", "SeparatorControl", "REDray Settings", 0, 0, colSpan=4 )

    rrContentTitle = scriptDialog.AddSelectionControlToGrid( "RrContentTitleCheckBox", "CheckBoxControl", False, "Content Title", 1, 0, "Content Title.", False )
    rrContentTitle.ValueModified.connect(RrContentTitleChanged)
    scriptDialog.AddControlToGrid( "RrContentTitleBox", "TextControl", "", 1, 1, colSpan=1 )

    rrPosterFrame = scriptDialog.AddSelectionControlToGrid( "RrPosterFrameCheckBox", "CheckBoxControl", False, "Poster Frame", 1, 2, "Poster Frame.", False )
    rrPosterFrame.ValueModified.connect(RrPosterFrameChanged)
    scriptDialog.AddRangeControlToGrid( "RrPosterFrameBox", "RangeControl", 1, 1, 10000, 0, 1, 1, 3 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    #### Rocket Settings ####
    scriptDialog.AddTabPage( "Rocket, GPU, ADD" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator23", "SeparatorControl", "Rocket Settings", 0, 0, colSpan=5 )

    scriptDialog.AddSelectionControlToGrid( "RedrayNoRocketBox", "CheckBoxControl", False, "Disable Rocket", 1, 0, "Turn rocket support off even if it's available.", False )
    scriptDialog.AddSelectionControlToGrid( "RedraySingleRocketBox", "CheckBoxControl", False, "Single Rocket", 1, 1, "Limit REDline to a maximum of one Rocket.", False )
    
    scriptDialog.AddSelectionControlToGrid( "RedrayForceRocketBox", "CheckBoxControl", False, "Force Rocket", 1, 2, "Forces the use of Red Rocket. If NO rockets are available the export will abort.", False )
    useRocket = scriptDialog.AddSelectionControlToGrid( "UseRocketCheckBox", "CheckBoxControl", False, "Specify Rocket Devices", 1, 3, "Choose which Rocket(s) to use (for example: 0,2). Comma separated string.", False )
    useRocket.ValueModified.connect(UseRocketChanged)
    scriptDialog.AddControlToGrid( "UseRocketBox", "TextControl", "", 1, 4, colSpan=1 )
    scriptDialog.EndGrid()

    #### Graph Processing/OpenCL/CUDA Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator24", "SeparatorControl", "Processing Settings", 0, 0, colSpan=4 )

    gpuPlatform = scriptDialog.AddSelectionControlToGrid( "GpuPlatformCheckBox", "CheckBoxControl", False, "GPU Platform", 1, 0, "Override if GPU should be enabled.", False )
    gpuPlatform.ValueModified.connect(GpuPlatformChanged)
    
    gpuPlatformChoice = scriptDialog.AddComboControlToGrid( "GpuPlatformBox", "ComboControl", "No GPU", ("No GPU","OpenCL","CUDA"), 1, 1 )
    gpuPlatformChoice.ValueModified.connect(GpuPlatformChoiceChanged)
    
    scriptDialog.AddControlToGrid( "GPUsSelectDevicesLabel", "LabelControl", "Specific GPUs (Optional)", 1, 2, "Optionally, specify which GPU devices to use by device index. Comma separated string such as 0 or 0,1 or 0,1,2.", False )
    scriptDialog.AddControlToGrid( "GPUsSelectDevicesBox", "TextControl", "", 1, 3, colSpan=1 )

    decodeThreads = scriptDialog.AddSelectionControlToGrid( "DecodeThreadsCheckBox", "CheckBoxControl", False, "Decode Threads", 2, 0, "Number of simultaneous decompression threads (Default 7).", False )
    decodeThreads.ValueModified.connect(DecodeThreadsChanged)
    scriptDialog.AddRangeControlToGrid( "DecodeThreadsBox", "RangeControl", 7, 1, 100, 0, 1, 2, 1 )

    numGraphs = scriptDialog.AddSelectionControlToGrid( "NumGraphsCheckBox", "CheckBoxControl", False, "Num Graphs", 3, 0, "Number of simultaneous graphs to process.", False )
    numGraphs.ValueModified.connect(NumGraphsChanged)
    scriptDialog.AddRangeControlToGrid( "NumGraphsBox", "RangeControl", 1, 0, 10, 0, 1, 3, 1 )

    numOclStreams = scriptDialog.AddSelectionControlToGrid( "NumOclStreamsCheckBox", "CheckBoxControl", False, "Num of GPU proc streams", 3, 2, "Number of GPU processing streams.", False )
    numOclStreams.ValueModified.connect(NumOclStreamsChanged)
    scriptDialog.AddRangeControlToGrid( "NumOclStreamsBox", "RangeControl", 1, 0, 10, 0, 1, 3, 3 )
    scriptDialog.EndGrid()

    #### Advanced Dragon Debayer (A.D.D.) ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator25", "SeparatorControl", "Advanced Dragon Debayer (A.D.D.) Settings", 0, 0, colSpan=4 )

    enableAdd = scriptDialog.AddSelectionControlToGrid( "AddEnableCheckBox", "CheckBoxControl", False, "Enable A.D.D.", 1, 0, "Enable A.D.D.", False )
    enableAdd.ValueModified.connect(EnableAddChanged)
    
    AddUsmAmount = scriptDialog.AddSelectionControlToGrid( "AddUsmAmountCheckBox", "CheckBoxControl", False, "Unsharp Mask Amount", 2, 0, "A.D.D. Unsharp Mask Amount. (Default: 200).", False )
    AddUsmAmount.ValueModified.connect(AddUsmAmountChanged)
    scriptDialog.AddRangeControlToGrid( "AddUsmAmountBox", "RangeControl", 200, 0.0, 1000.0, 1, 1.0, 2, 1 )

    AddUsmRadius = scriptDialog.AddSelectionControlToGrid( "AddUsmRadiusCheckBox", "CheckBoxControl", False, "Unsharp Mask Radius", 2, 2, "A.D.D. Unsharp Mask Radius. (Default: 0.6).", False )
    AddUsmRadius.ValueModified.connect(AddUsmRadiusChanged)
    scriptDialog.AddRangeControlToGrid( "AddUsmRadiusBox", "RangeControl", 0.6, 0.0, 100.0, 1, 0.1, 2, 3 )

    AddUsmThreshold = scriptDialog.AddSelectionControlToGrid( "AddUsmThresholdCheckBox", "CheckBoxControl", False, "Unsharp Mask Threshold", 3, 0, "A.D.D. Unsharp Mask Threshold. (Default: 1.0).", False )
    AddUsmThreshold.ValueModified.connect(AddUsmThresholdChanged)
    scriptDialog.AddRangeControlToGrid( "AddUsmThresholdBox", "RangeControl", 1.0, 0.0, 100.0, 1, 0.1, 3, 1 )

    AddDisable = scriptDialog.AddSelectionControlToGrid( "AddUsmDisableBox", "CheckBoxControl", False, "Disable Unsharp Mask for A.D.D.", 3, 2, "Disable Unsharp Mask for A.D.D. Processing.", False )
    AddDisable.ValueModified.connect(AddDisableChanged)
    scriptDialog.EndGrid()

    #### 3D LUT Settings ####
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator26", "SeparatorControl", "3D LUT Settings", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "LutFileLabel", "LabelControl", "LUT File", 1, 0, "Load a 3D LUT from file.", False )
    lutFile = scriptDialog.AddSelectionControlToGrid( "LutFileBox", "FileBrowserControl", "", "3DL File (*.3dl);;CUBE File (*.cube);;All Files (*)", 1, 1, colSpan=3 )
    lutFile.ValueModified.connect(LutFileChanged)

    lutEdgeLength = scriptDialog.AddSelectionControlToGrid( "LutEdgeLengthCheckBox", "CheckBoxControl", False, "Edge length of LUT File", 2, 0, "Edge length of the 3D LUT.", False )
    lutEdgeLength.ValueModified.connect(LutEdgeLengthChanged)
    scriptDialog.AddRangeControlToGrid( "LutEdgeLengthBox", "RangeControl", 1, 1, 100, 0, 1, 2, 1 )
    
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
    
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    #### File Settings ####
    DirFileChooserChanged()
    SceneChanged()
    ViewTypeChooserChanged()
    InputFileChanged()
    
    #### Frame Settings ####
    AdvLutRenderChanged()
    Offset3dCheckChanged()

    #### Print Meta Settings ####
    UseMetaChanged()
    OverridePrintMetaChanged()
    OverrideReelIDChanged()
    OverrideClipFrameRateChanged()

    #### Crop and Scale Settings ####
    CropChanged()
    ScaleChanged()
    ForceFlipHChanged()
    ForceFlipVChanged()
    OverrideRotateChanged()
    OverridePreventNegPixelsChanged()
    
    #### Burn-In Settings ####
    BurnChanged()
    BurnFramesChanged()

    #### Watermark Settings ####
    WatermarkChanged()

    #### Color/Gamma Space Settings ####
    ColorSpaceChanged()
    GammaCurveChanged()
    NoiseReductionChanged()
    DetailChanged()
    OLPFCompensationChanged()
    SMPTEColorRangeChanged()
    
    #### Color Settings ####
    ISOChanged()
    ExposureChanged()
    ContrastChanged()
    BrightnessChanged()
    DRXChanged()
    KelvinChanged()
    TintChanged()
    SaturationChanged()
    RedChanged()
    GreenChanged()
    BlueChanged()
    FlutChanged()
    ShadowChanged()
    DEBChanged()

    #### Lift Gamma Gain Settings ####
    RedLiftChanged()
    GreenLiftChanged()
    BlueLiftChanged()
    RedGammaChanged()
    GreenGammaChanged()
    BlueGammaChanged()
    RedGainChanged()
    GreenGainChanged()
    BlueGainChanged()

    #### Print Density Settings ####
    PdBlackChanged()
    PdWhiteChanged()
    PdGammaChanged()

    #### Curve Settings ####
    BlackChanged()
    WhiteChanged()

    #### New Curve Point Values ####
    LumaCurveChanged()
    RedCurveChanged()
    GreenCurveChanged()
    BlueCurveChanged()

    #### HDR Settings ####
    HdrModeChanged()
    HdrModeChoiceChanged()

    #### DPX Settings ####
    DpxByteOrderChanged()
    DpxBitDepthChanged()
    DpxMaxWritersChanged()

    #### OpenEXR Settings ####
    ExrCompressionChanged()
    ExrCompressionChoiceChanged()
    ExrMultiViewChanged()
    ExrMaxWritersChanged()
    ExrAcesChanged()
    ExrSoftClampChanged()

    #### R3D Trim Settings ####
    R3dTrimFcpXmlChanged()
    R3dTrimChangeFrameRateChanged()
    R3dTrimChangeOLPFChanged()

    #### Avid DNX Settings ####
    DnxCodecChanged()
    DnxFrameRateChanged()
    
    #### REDray Settings ####
    RrContentTitleChanged()
    RrPosterFrameChanged()

    #### Rocket Settings ####
    UseRocketChanged()

    #### Graph Processing/OpenCL/CUDA Settings ####
    GpuPlatformChanged()
    GpuPlatformChoiceChanged()
    DecodeThreadsChanged()
    NumGraphsChanged()
    NumOclStreamsChanged()

    #### Advanced Dragon Debayer (A.D.D.) ####
    EnableAddChanged()
    AddUsmAmountChanged()
    AddUsmRadiusChanged()
    AddUsmThresholdChanged()

    #### 3D LUT Settings ####
    LutFileChanged()
    LutEdgeLengthChanged()

    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "REDLineSettings.ini" )

def IsNumber( str ):
    try:
        dummy = int(str)
        return True
    except:
        return False

def IsValidOrdinalString( ordString ):
    '''
    Checks for valid comma separated string with integer ordinals 0-15 only
    '''
    result = False
    if ordString != "":
        ordRegex = re.compile( "^(([0-9]|1[0-5]),)*([0-9]|1[0-5])$" )
        m = re.match( ordRegex, ordString )
        if( m != None ):
            ordList = ordString.split(",")
            if len(ordList) == len(set(ordList)):
                result = True
    return result

def DirFileChooserChanged( *args ):
    global scriptDialog
    dirSelect = scriptDialog.GetValue( "DirChooser" )
    fileSelect = scriptDialog.GetValue( "FileChooser" )

    scriptDialog.SetEnabled( "SubDirectoriesBox", dirSelect )
    scriptDialog.SetEnabled( "R3DDirectoryLabel", dirSelect )
    scriptDialog.SetEnabled( "R3DDirectoryBox", dirSelect )
    scriptDialog.SetEnabled( "SceneLabel", fileSelect )
    scriptDialog.SetEnabled( "SceneBox", fileSelect )
    scriptDialog.SetEnabled( "ViewTypeChooserLabel", fileSelect )
    scriptDialog.SetEnabled( "ViewChooserSingle", fileSelect )
    scriptDialog.SetEnabled( "ViewChooserStereo", fileSelect )
    ViewTypeChooserChanged()

def SceneChanged( *args ):
    global scriptDialog
    sceneFilename = scriptDialog.GetValue( "SceneBox" ).strip()
    if sceneFilename != "":
        baseFilename = Path.GetFileNameWithoutExtension( sceneFilename )
        scriptDialog.SetValue( "NameBox", baseFilename )
        scriptDialog.SetValue( "OutputBaseBox", baseFilename )
    else:
        scriptDialog.SetValue( "NameBox", "" )
        scriptDialog.SetValue( "OutputBaseBox", "" )

def ViewTypeChooserChanged( *args ):
    global scriptDialog
    fileSelect = scriptDialog.GetValue( "FileChooser" )
    single = scriptDialog.GetValue( "ViewChooserSingle" )
    stereo = scriptDialog.GetValue( "ViewChooserStereo" )

    scriptDialog.SetEnabled( "SceneLabel", fileSelect and single )
    scriptDialog.SetEnabled( "SceneBox", fileSelect and single )
    
    scriptDialog.SetEnabled( "LeftEyeLabel", fileSelect and stereo )
    scriptDialog.SetEnabled( "LeftEyeFileBox", fileSelect and stereo )
    scriptDialog.SetEnabled( "RightEyeLabel", fileSelect and stereo )
    scriptDialog.SetEnabled( "RightEyeFileBox", fileSelect and stereo )

    scriptDialog.SetEnabled( "3dModeLabel", fileSelect and stereo )
    scriptDialog.SetEnabled( "3dModeBox", fileSelect and stereo )
    scriptDialog.SetEnabled( "Offset3dCheckBox", fileSelect and stereo )
    scriptDialog.SetEnabled( "Offset3dBox", fileSelect and stereo )

def InputFileChanged( *args ):
    global scriptDialog
    inputFile = scriptDialog.GetValue( "LeftEyeFileBox" ).strip()
    if inputFile != "":
        baseFilename = Path.GetFileNameWithoutExtension( inputFile )
        scriptDialog.SetValue( "NameBox", baseFilename )
        scriptDialog.SetValue( "OutputBaseBox", baseFilename )
    else:
        scriptDialog.SetValue( "NameBox", "" )
        scriptDialog.SetValue( "OutputBaseBox", "" )

def AdvLutRenderChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled("AdvLutRenderBox", scriptDialog.GetValue("OverrideAdvLutRenderBox") )

def Offset3dCheckChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "Offset3dBox", scriptDialog.GetValue( "Offset3dCheckBox" ) )

def UseMetaChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "MetaIgnoreFrameGuideBox", scriptDialog.GetValue( "UseMetaBox" ) )

def OverridePrintMetaChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "PrintMetaBox", scriptDialog.GetValue( "OverridePrintMetaCheckBox" ) )

def OverrideReelIDChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ReelIDBox", scriptDialog.GetValue( "OverrideReelIDCheckBox" ) )

def OverrideClipFrameRateChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ClipFrameRateBox", scriptDialog.GetValue( "OverrideClipFrameRateCheckBox" ) )

def CropChanged( *args ):
    global scriptDialog
    cropEnabled = scriptDialog.GetValue( "CropBox" )
    scriptDialog.SetEnabled( "CropWidthLabel", cropEnabled )
    scriptDialog.SetEnabled( "CropWidthBox", cropEnabled )
    scriptDialog.SetEnabled( "CropHeightLabel", cropEnabled )
    scriptDialog.SetEnabled( "CropHeightBox", cropEnabled )
    scriptDialog.SetEnabled( "CropOriginXLabel", cropEnabled )
    scriptDialog.SetEnabled( "CropOriginXBox", cropEnabled )
    scriptDialog.SetEnabled( "CropOriginYLabel", cropEnabled )
    scriptDialog.SetEnabled( "CropOriginYBox", cropEnabled )  
    
def ScaleChanged( *args ):
    global scriptDialog
    scaleEnabled = scriptDialog.GetValue( "ScaleBox" )
    scriptDialog.SetEnabled( "ScaleWidthLabel", scaleEnabled )
    scriptDialog.SetEnabled( "ScaleWidthBox", scaleEnabled )
    scriptDialog.SetEnabled( "ScaleHeightLabel", scaleEnabled )
    scriptDialog.SetEnabled( "ScaleHeightBox", scaleEnabled )
    scriptDialog.SetEnabled( "ScaleFitLabel", scaleEnabled )
    scriptDialog.SetEnabled( "ScaleFitBox", scaleEnabled )
    scriptDialog.SetEnabled( "ScaleFilterLabel", scaleEnabled )
    scriptDialog.SetEnabled( "ScaleFilterBox", scaleEnabled )  

def ForceFlipHChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ForceFlipHorizontalBox", scriptDialog.GetValue( "ForceFlipHorizontalCheckBox" ) )

def ForceFlipVChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ForceFlipVerticalBox", scriptDialog.GetValue( "ForceFlipVerticalCheckBox" ) )

def OverrideRotateChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "RotateBox", scriptDialog.GetValue( "OverrideRotateCheckBox" ) )

def OverridePreventNegPixelsChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "PreventNegPixelsBox", scriptDialog.GetValue( "OverridePreventNegPixelsCheckBox" ) )

#### Text Burn-In Settings ####
def BurnChanged( *args ):
    global scriptDialog
    burnEnabled = scriptDialog.GetValue( "BurnBox" )
    burnCountEnabled = ( scriptDialog.GetValue( "BurnFramesBox" ) == "Count" )
    scriptDialog.SetEnabled( "BurnFramesLabel", burnEnabled )
    scriptDialog.SetEnabled( "BurnFramesBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnFramesCountLabel", burnEnabled and burnCountEnabled )
    scriptDialog.SetEnabled( "BurnFramesCountBox", burnEnabled and burnCountEnabled )
    scriptDialog.SetEnabled( "BurnFontLabel", burnEnabled )
    scriptDialog.SetEnabled( "BurnFontBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnSizeLabel", burnEnabled )
    scriptDialog.SetEnabled( "BurnSizeBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnBaseLabel", burnEnabled )
    scriptDialog.SetEnabled( "BurnBaseBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnLowerLeftLabel", burnEnabled )
    scriptDialog.SetEnabled( "BurnLowerLeftBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnLowerRightLabel", burnEnabled )
    scriptDialog.SetEnabled( "BurnLowerRightBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnUpperLeftLabel", burnEnabled )
    scriptDialog.SetEnabled( "BurnUpperLeftBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnUpperRightLabel", burnEnabled )
    scriptDialog.SetEnabled( "BurnUpperRightBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnTextLabel", burnEnabled )
    scriptDialog.SetEnabled( "BurnTextRBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnTextGBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnTextBBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnTextABox", burnEnabled )
    
    scriptDialog.SetEnabled( "BurnBackgroundLabel", burnEnabled )
    scriptDialog.SetEnabled( "BurnBackgroundRBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnBackgroundGBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnBackgroundBBox", burnEnabled )
    scriptDialog.SetEnabled( "BurnBackgroundABox", burnEnabled )

def BurnFramesChanged( *args ):
    global scriptDialog
    burnCountEnabled = ( scriptDialog.GetValue( "BurnFramesBox" ) == "Count" )
    scriptDialog.SetEnabled( "BurnFramesCountLabel", burnCountEnabled )
    scriptDialog.SetEnabled( "BurnFramesCountBox", burnCountEnabled )

#### Watermark Settings ####
def WatermarkChanged( *args ):
    global scriptDialog
    watermarkEnabled = scriptDialog.GetValue( "WatermarkBox" )
    scriptDialog.SetEnabled( "WatermarkFontLabel", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkFontBox", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkTextLabel", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkTextBox", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkSzLabel", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkSzBox", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkBaseLabel", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkBaseBox", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkTxtRLabel", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkTxtRBox", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkTxtGLabel", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkTxtGBox", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkTxtBLabel", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkTxtBBox", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkTxtALabel", watermarkEnabled )
    scriptDialog.SetEnabled( "WatermarkTxtABox", watermarkEnabled )

#### Color/Gamma Space Settings ####
def ColorSpaceChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ColorSpaceBox", scriptDialog.GetValue( "ColorSpaceCheckBox" ) )
    
def GammaCurveChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "GammaCurveBox", scriptDialog.GetValue( "GammaCurveCheckBox" ) )
    
def NoiseReductionChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "NoiseReductionBox", scriptDialog.GetValue( "NoiseReductionCheckBox" ) )
    
def DetailChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DetailBox", scriptDialog.GetValue( "DetailCheckBox" ) )
    
def OLPFCompensationChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "OLPFCompensationBox", scriptDialog.GetValue( "OLPFCompensationCheckBox" ) )

def SMPTEColorRangeChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "SMPTEColorRangeBox", scriptDialog.GetValue( "SMPTEColorRangeCheckBox" ) )

#### Color Settings ####
def ISOChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ISOBox", scriptDialog.GetValue( "ISOCheckBox" ) )

def ExposureChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ExposureBox", scriptDialog.GetValue( "ExposureCheckBox" ) )

def ContrastChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ContrastBox", scriptDialog.GetValue( "ContrastCheckBox" ) )

def BrightnessChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "BrightnessBox", scriptDialog.GetValue( "BrightnessCheckBox" ) )

def DRXChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DRXBox", scriptDialog.GetValue( "DRXCheckBox" ) )

def KelvinChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "KelvinBox", scriptDialog.GetValue( "KelvinCheckBox" ) )

def TintChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "TintBox", scriptDialog.GetValue( "TintCheckBox" ) )

def SaturationChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "SaturationBox", scriptDialog.GetValue( "SaturationCheckBox" ) )

def RedChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "RedBox", scriptDialog.GetValue( "RedCheckBox" ) )

def GreenChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "GreenBox", scriptDialog.GetValue( "GreenCheckBox" ) )

def BlueChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "BlueBox", scriptDialog.GetValue( "BlueCheckBox" ) )

def FlutChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "FlutBox", scriptDialog.GetValue( "FlutCheckBox" ) )

def ShadowChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ShadowBox", scriptDialog.GetValue( "ShadowCheckBox" ) )

def DEBChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DEBBox", scriptDialog.GetValue( "DEBCheckBox" ) )

#### Lift Gamma Gain Settings ####
def RedLiftChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "RedLiftBox", scriptDialog.GetValue( "RedLiftCheckBox" ) )

def GreenLiftChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "GreenLiftBox", scriptDialog.GetValue( "GreenLiftCheckBox" ) )

def BlueLiftChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "BlueLiftBox", scriptDialog.GetValue( "BlueLiftCheckBox" ) )

def RedGammaChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "RedGammaBox", scriptDialog.GetValue( "RedGammaCheckBox" ) )

def GreenGammaChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "GreenGammaBox", scriptDialog.GetValue( "GreenGammaCheckBox" ) )

def BlueGammaChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "BlueGammaBox", scriptDialog.GetValue( "BlueGammaCheckBox" ) )

def RedGainChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "RedGainBox", scriptDialog.GetValue( "RedGainCheckBox" ) )

def GreenGainChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "GreenGainBox", scriptDialog.GetValue( "GreenGainCheckBox" ) )

def BlueGainChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "BlueGainBox", scriptDialog.GetValue( "BlueGainCheckBox" ) )

#### Print Density Settings ####
def PdBlackChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "PdBlackBox", scriptDialog.GetValue( "PdBlackCheckBox" ) )

def PdWhiteChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "PdWhiteBox", scriptDialog.GetValue( "PdWhiteCheckBox" ) )

def PdGammaChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "PdGammaBox", scriptDialog.GetValue( "PdGammaCheckBox" ) )

#### Curve Settings ####
def BlackChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "BlackBox", scriptDialog.GetValue( "BlackCheckBox" ) )

def WhiteChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "WhiteBox", scriptDialog.GetValue( "WhiteCheckBox" ) )

#### New Curve Point Values ####
def LumaCurveChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "LumaCurveBox", scriptDialog.GetValue( "LumaCurveCheckBox" ) )

def RedCurveChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "RedCurveBox", scriptDialog.GetValue( "RedCurveCheckBox" ) )

def GreenCurveChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "GreenCurveBox", scriptDialog.GetValue( "GreenCurveCheckBox" ) )

def BlueCurveChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "BlueCurveBox", scriptDialog.GetValue( "BlueCurveCheckBox" ) )

#### HDR Settings ####
def HdrModeChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "HdrModeBox", scriptDialog.GetValue( "HdrModeCheckBox" ) )
    HdrModeChoiceChanged()

def HdrModeChoiceChanged( *args ):
    global scriptDialog
    hdrModeEnabled = scriptDialog.GetValue( "HdrModeCheckBox" )
    biasModeEnabled = ( scriptDialog.GetValue("HdrModeBox") == "Simple Blend" or scriptDialog.GetValue("HdrModeBox") == "Magic Motion" )
    scriptDialog.SetEnabled( "HdrBiasLabel", (hdrModeEnabled and biasModeEnabled) )
    scriptDialog.SetEnabled( "HdrBiasBox", (hdrModeEnabled and biasModeEnabled) )

#### DPX Settings ####
def DpxByteOrderChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DpxByteOrderBox", scriptDialog.GetValue( "DpxByteOrderCheckBox" ) )

def DpxBitDepthChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DpxBitDepthBox", scriptDialog.GetValue( "DpxBitDepthCheckBox" ) )

def DpxMaxWritersChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DpxMaxWritersBox", scriptDialog.GetValue( "DpxMaxWritersCheckBox" ) )

#### OpenEXR Settings ####
def ExrCompressionChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ExrCompressionBox", scriptDialog.GetValue( "ExrCompressionCheckBox" ) )
    ExrCompressionChoiceChanged()

def ExrCompressionChoiceChanged( *args ):
    global scriptDialog
    exrCompressionEnabled = scriptDialog.GetValue( "ExrCompressionCheckBox" )
    exrCompressionChoice = ( scriptDialog.GetValue( "ExrCompressionBox" ) == "DWAA" )
    scriptDialog.SetEnabled( "ExrCompressionDwaaLabel", (exrCompressionEnabled and exrCompressionChoice) )
    scriptDialog.SetEnabled( "ExrCompressionDwaaBox", (exrCompressionEnabled and exrCompressionChoice) )

def ExrMultiViewChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ExrMultiViewBox", scriptDialog.GetValue( "ExrMultiViewCheckBox" ) )

def ExrMaxWritersChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ExrMaxWritersBox", scriptDialog.GetValue( "ExrMaxWritersCheckBox" ) )

def ExrAcesChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ExrAcesBox", scriptDialog.GetValue( "ExrAcesCheckBox" ) )

def ExrSoftClampChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ExrSoftClampBox", scriptDialog.GetValue( "ExrSoftClampCheckBox" ) )

#### R3D Trim Settings ####
def R3dTrimFcpXmlChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "R3dTrimFcpXmlBox", scriptDialog.GetValue( "R3dTrimFcpXmlCheckBox" ) )

def R3dTrimChangeFrameRateChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "R3dTrimChangeFrameRateBox", scriptDialog.GetValue( "R3dTrimChangeFrameRateCheckBox" ) )

def R3dTrimChangeOLPFChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "R3dTrimChangeOLPFBox", scriptDialog.GetValue( "R3dTrimChangeOLPFCheckBox" ) )

#### Avid DNX Settings ####
def DnxCodecChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DnxCodecBox", scriptDialog.GetValue( "DnxCodecCheckBox" ) )

def DnxFrameRateChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DnxFrameRateBox", scriptDialog.GetValue( "DnxFrameRateCheckBox" ) )

#### REDray Settings ####
def RrContentTitleChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "RrContentTitleBox", scriptDialog.GetValue( "RrContentTitleCheckBox" ) )

def RrPosterFrameChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "RrPosterFrameBox", scriptDialog.GetValue( "RrPosterFrameCheckBox" ) )

#### Rocket Settings ####
def UseRocketChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "UseRocketBox", scriptDialog.GetValue( "UseRocketCheckBox" ) )

#### Graph Processing/OpenCL/CUDA Settings ####
def GpuPlatformChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "GpuPlatformBox", scriptDialog.GetValue( "GpuPlatformCheckBox" ) )
    GpuPlatformChoiceChanged()

def GpuPlatformChoiceChanged( *args ):
    global scriptDialog
    gpuEnabled = scriptDialog.GetValue( "GpuPlatformCheckBox" )
    gpuSelected = ( scriptDialog.GetValue( "GpuPlatformBox" ) != "No GPU" )
    scriptDialog.SetEnabled( "GPUsSelectDevicesLabel", (gpuEnabled and gpuSelected) )
    scriptDialog.SetEnabled( "GPUsSelectDevicesBox", (gpuEnabled and gpuSelected) )

def DecodeThreadsChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DecodeThreadsBox", scriptDialog.GetValue( "DecodeThreadsCheckBox" ) )

def NumGraphsChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "NumGraphsBox", scriptDialog.GetValue( "NumGraphsCheckBox" ) )

def NumOclStreamsChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "NumOclStreamsBox", scriptDialog.GetValue( "NumOclStreamsCheckBox" ) )

#### Advanced Dragon Debayer (A.D.D.) ####
def EnableAddChanged( *args ):
    global scriptDialog
    enableAddEnabled = scriptDialog.GetValue( "AddEnableCheckBox" )
    scriptDialog.SetEnabled( "AddUsmAmountCheckBox", enableAddEnabled )
    scriptDialog.SetEnabled( "AddUsmAmountBox", enableAddEnabled )
    scriptDialog.SetEnabled( "AddUsmRadiusCheckBox", enableAddEnabled )
    scriptDialog.SetEnabled( "AddUsmRadiusBox", enableAddEnabled )
    scriptDialog.SetEnabled( "AddUsmThresholdCheckBox", enableAddEnabled )
    scriptDialog.SetEnabled( "AddUsmThresholdBox", enableAddEnabled )
    scriptDialog.SetEnabled( "AddUsmDisableBox", enableAddEnabled )
    AddDisableChanged()

def AddUsmAmountChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "AddUsmAmountBox", scriptDialog.GetValue( "AddUsmAmountCheckBox" ) )

def AddUsmRadiusChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "AddUsmRadiusBox", scriptDialog.GetValue( "AddUsmRadiusCheckBox" ) )

def AddUsmThresholdChanged( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "AddUsmThresholdBox", scriptDialog.GetValue( "AddUsmThresholdCheckBox" ) )

def AddDisableChanged( *args ):
    global scriptDialog
    addDisabled = scriptDialog.GetValue( "AddUsmDisableBox" )
    scriptDialog.SetEnabled( "AddUsmAmountCheckBox", not addDisabled )
    scriptDialog.SetEnabled( "AddUsmAmountBox", not addDisabled )
    scriptDialog.SetEnabled( "AddUsmRadiusCheckBox", not addDisabled )
    scriptDialog.SetEnabled( "AddUsmRadiusBox", not addDisabled )
    scriptDialog.SetEnabled( "AddUsmThresholdCheckBox", not addDisabled )
    scriptDialog.SetEnabled( "AddUsmThresholdBox", not addDisabled )

#### 3D LUT Settings ####
def LutFileChanged( *args ):
    global scriptDialog
    lutFileEnabled = ( scriptDialog.GetValue( "LutFileBox" ).strip() != "" )
    scriptDialog.SetEnabled( "LutEdgeLengthCheckBox", lutFileEnabled )
    LutEdgeLengthChanged()

def LutEdgeLengthChanged( *args ):
    global scriptDialog
    lutFileEnabled = ( scriptDialog.GetValue( "LutFileBox" ).strip() != "" )
    lutEdgeLengthEnabled = scriptDialog.GetValue( "LutEdgeLengthCheckBox" )
    scriptDialog.SetEnabled( "LutEdgeLengthBox", ( lutFileEnabled and lutEdgeLengthEnabled ) )

def WriteEnum( writer, key, enums ):
    enumCount = 0
    for enumType in enums:
        writer.WriteLine( "%s%s=%s" % (key, enumCount, enumType) )
        enumCount = enumCount + 1

def SubmitButtonPressed( *args ):
    global scriptDialog

    fileSelect = scriptDialog.GetValue( "FileChooser" )
    dirSelect = scriptDialog.GetValue( "DirChooser" )

    viewSingle = scriptDialog.GetValue( "ViewChooserSingle" )
    viewStereo = scriptDialog.GetValue( "ViewChooserStereo" )
    
    if fileSelect and viewSingle:
        sceneFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "SceneBox" ), False )
    
    elif fileSelect and viewStereo:
        leftEyeFile = scriptDialog.GetValue( "LeftEyeFileBox" )
        rightEyeFile = scriptDialog.GetValue( "RightEyeFileBox" )
        sceneFiles = StringUtils.FromSemicolonSeparatedString( leftEyeFile, False )
    
    elif dirSelect:
        rootDirectory = scriptDialog.GetValue( "R3DDirectoryBox" )
        
        if scriptDialog.GetValue( "SubDirectoriesBox" ):
            searchOption = SearchOption.AllDirectories
        else:
            searchOption = SearchOption.TopDirectoryOnly
        
        try:
            sceneFiles = Directory.GetFiles( rootDirectory, "*.R3D", searchOption )
        except:
            scriptDialog.ShowMessageBox( "Do not select symbolic path shortcuts or UNC paths", "Error" )
            return
    
    submitScene = scriptDialog.GetValue( "SubmitSceneBox" )

    # Check if R3D files exist.
    if (fileSelect and viewSingle) or dirSelect:
        if len( sceneFiles ) == 0 :
            scriptDialog.ShowMessageBox( "Please select an R3D file to submit!", "Error" )
            return
    elif fileSelect and viewStereo:
        if leftEyeFile == "" or rightEyeFile == "":
            scriptDialog.ShowMessageBox( "Please ensure you select both a left and right eye R3D file!", "Error" )
            return
    
    if (fileSelect and viewSingle) or dirSelect:
        for sceneFile in sceneFiles:
            if not File.Exists( sceneFile ):
                scriptDialog.ShowMessageBox( "R3D file '" + sceneFile + "' does not exist", "Error" )
                return
            elif not submitScene and PathUtils.IsPathLocal( sceneFile ):
                result = scriptDialog.ShowMessageBox( "The R3D file '" + sceneFile + "' is local and is not being submitted with the job, are you sure you want to continue?","Warning", ("Yes","No") )
                if result == "No":
                    return
    elif fileSelect and viewStereo:
        if not File.Exists( leftEyeFile ):
            scriptDialog.ShowMessageBox( "R3D left eye file '" + leftEyeFile + "' does not exist", "Error" )
            return
        elif not submitScene and PathUtils.IsPathLocal( leftEyeFile ):
            result = scriptDialog.ShowMessageBox( "The R3D left eye file '" + leftEyeFile + "' is local and is not being submitted with the job, are you sure you want to continue?","Warning", ("Yes","No") )
            if result == "No":
                return
        if not File.Exists( rightEyeFile ):
            scriptDialog.ShowMessageBox( "R3D right eye file '" + rightEyeFile + "' does not exist", "Error" )
        elif not submitScene and PathUtils.IsPathLocal( rightEyeFile ):
            result = scriptDialog.ShowMessageBox( "The R3D right eye file '" + rightEyeFile + "' is local and is not being submitted with the job, are you sure you want to continue?","Warning", ("Yes","No") )
            if result == "No":
                return

    # Check output.
    outputFolder = scriptDialog.GetValue( "OutputBox" )
    if not Directory.Exists( outputFolder ):
        scriptDialog.ShowMessageBox( "Output folder '" + outputFolder + "' does not exist.", "Error" )
        return
    elif PathUtils.IsPathLocal( outputFolder ):
        result = scriptDialog.ShowMessageBox( "The output folder '" + outputFolder + "' is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if result == "No":
            return
    
    outputPadding = scriptDialog.GetValue( "OutputPaddingBox" )
    
    baseFilename  = scriptDialog.GetValue( "OutputBaseBox" ).strip()
    if baseFilename  == "":
        scriptDialog.ShowMessageBox( "Please specify an output filename", "Error" )
        return
    
    outputFormat = scriptDialog.GetValue( "OutputFormatBox" )
    isMovie = False
    if outputFormat == "DPX":
        outputBaseName = Path.ChangeExtension( baseFilename, ".dpx" )
    elif outputFormat == "Tiff":
        outputBaseName = Path.ChangeExtension( baseFilename, ".tif" )
    elif outputFormat == "OpenEXR":
        outputBaseName = Path.ChangeExtension( baseFilename, ".exr" )
    elif outputFormat == "SGI":
        outputBaseName = Path.ChangeExtension( baseFilename, ".rgb" )
    elif outputFormat == "QT Wrappers":
        outputBaseName = Path.ChangeExtension( baseFilename, ".mov" )
        isMovie = True
    elif outputFormat == "QT Transcode":
        outputBaseName = Path.ChangeExtension( baseFilename, ".mov" )
        isMovie = True
    elif outputFormat == "R3D Trim":
        outputBaseName = ""
        isMovie = True
    elif outputFormat == "REDray":
        outputBaseName = ""
        isMovie = True
    elif outputFormat == "Apple ProRes":
        outputBaseName = Path.ChangeExtension( baseFilename, ".mov" )
        isMovie = True
    elif outputFormat == "Avid DNX":
        outputBaseName = ""
        isMovie = True
    
    # Check RSX File.
    rsxFile = scriptDialog.GetValue( "RSXBox" ).strip()
    if rsxFile != "":
        if not File.Exists( rsxFile ):
            scriptDialog.ShowMessageBox( "RSX file '" + rsxFile + "' does not exist", "Error" )
            return
        elif PathUtils.IsPathLocal( rsxFile ):
            result = scriptDialog.ShowMessageBox( "The RSX file '" + rsxFile + "' is local, are you sure you want to continue?","Warning", ("Yes","No") )
            if result == "No":
                return
                
    # Check RMD File.
    rmdFile = scriptDialog.GetValue( "RMDBox" ).strip()
    if rmdFile != "":
        if not File.Exists( rmdFile ):
            scriptDialog.ShowMessageBox( "RMD file '" + rmdFile + "' does not exist", "Error" )
            return
        elif PathUtils.IsPathLocal( rmdFile ):
            result = scriptDialog.ShowMessageBox( "The RMD file '" + rmdFile + "' is local, are you sure you want to continue?","Warning", ("Yes","No") )
            if result == "No":
                return
    
    # Check if a valid frame range has been specified.
    renderAllFrames = False
    frames = scriptDialog.GetValue( "FramesBox" ).strip()
    if frames != "":
        if not FrameUtils.FrameRangeValid( frames ):
            scriptDialog.ShowMessageBox( "Frame range " + frames + " is not valid", "Error" )
            return
    else:
        renderAllFrames = True
    
    # Check optional numerical values.
    renumberStartFrame = scriptDialog.GetValue( "RenumberBox" ).strip()
    if renumberStartFrame != "" and not IsNumber( renumberStartFrame ):
        scriptDialog.ShowMessageBox( "Renumber Start Frame value '" + renumberStartFrame + "' is not a valid number", "Error" )
        return
    
    cropWidth = scriptDialog.GetValue( "CropWidthBox" ).strip()
    if cropWidth != "" and not IsNumber( cropWidth ):
        scriptDialog.ShowMessageBox( "Crop Width value '" + cropWidth + "' is not a valid number", "Error" )
        return
    
    cropHeight = scriptDialog.GetValue( "CropHeightBox" ).strip()
    if cropHeight != "" and not IsNumber( cropHeight ):
        scriptDialog.ShowMessageBox( "Crop Height value '" + cropHeight + "' is not a valid number", "Error" )
        return
    
    cropOriginX = scriptDialog.GetValue( "CropOriginXBox" ).strip()
    if cropOriginX != "" and not IsNumber( cropOriginX ):
        scriptDialog.ShowMessageBox( "Crop Origin X value '" + cropOriginX + "' is not a valid number", "Error" )
        return
    
    cropOriginY = scriptDialog.GetValue( "CropOriginYBox" ).strip()
    if cropOriginY != "" and not IsNumber( cropOriginY ):
        scriptDialog.ShowMessageBox( "Crop Origin Y value '" + cropOriginY + "' is not a valid number", "Error" )
        return
    
    scaleWidth = scriptDialog.GetValue( "ScaleWidthBox" ).strip()
    if scaleWidth != "" and not IsNumber( scaleWidth ):
        scriptDialog.ShowMessageBox( "Scale Width value '" + scaleWidth + "' is not a valid number", "Error" )
        return
    
    scaleHeight = scriptDialog.GetValue( "ScaleHeightBox" ).strip()
    if scaleHeight != "" and not IsNumber( scaleHeight ):
        scriptDialog.ShowMessageBox( "Scale Height value '" + scaleHeight + "' is not a valid number", "Error" )
        return

    # Check REDrocket values are valid.
    if scriptDialog.GetValue( "UseRocketCheckBox" ):
        deviceString = scriptDialog.GetValue( "UseRocketBox" )
        if deviceString == "":
            scriptDialog.ShowMessageBox( "Missing any declared RED Rocket(s) IDs to Use", "Error" )
            return
        elif not IsValidOrdinalString( deviceString ):
            scriptDialog.ShowMessageBox( "Invalid RED Rocket comma-separated string provided.", "Error" )
            return

    # Check GPU select devices are valid.
    if scriptDialog.GetValue( "GpuPlatformCheckBox" ):
        gpuPlatform = scriptDialog.GetValue( "GpuPlatformBox" )
        if gpuPlatform != "No GPU":
            deviceString = scriptDialog.GetValue( "GPUsSelectDevicesBox" )
            if deviceString == "":
                scriptDialog.ShowMessageBox( "Missing any declared GPU device IDs to Use", "Error" )
                return
            elif not IsValidOrdinalString( deviceString ):
                scriptDialog.ShowMessageBox( "Invalid GPU comma-separated string provided.", "Error" )
                return

    successes = 0
    failures = 0
    
    # Submit each scene file separately.
    for sceneFile in sceneFiles:
        jobName = scriptDialog.GetValue( "NameBox" )
        if len(sceneFiles) > 1:
            jobName = Path.GetFileNameWithoutExtension( sceneFile )
        if renderAllFrames:
            jobName = jobName + " [All Frames]"
        if fileSelect and viewStereo:
            jobName += " [Stereo]"
        if len(sceneFiles) > 1 and outputBaseName != "":
            baseFilename = Path.GetFileNameWithoutExtension( sceneFile )
            outputBaseName = Path.ChangeExtension( baseFilename, Path.GetExtension( outputBaseName ) )
        
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "redline_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=REDLine" )
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
        
        if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        if renderAllFrames:
            writer.WriteLine( "Frames=0" )
        else:
            writer.WriteLine( "Frames=%s" % frames )
        
        if isMovie:
            if renderAllFrames:
                writer.WriteLine( "ChunkSize=1" )
            else:
                writer.WriteLine( "ChunkSize=1000000" )
            writer.WriteLine( "MachineLimit=1" )
            if outputBaseName == "":
                writer.WriteLine( "OutputDirectory0=%s" % outputFolder )
            else:
                writer.WriteLine( "OutputFilename0=%s" % Path.Combine( outputFolder, outputBaseName ) )
        else:
            if renderAllFrames:
                writer.WriteLine( "ChunkSize=1" )
                writer.WriteLine( "MachineLimit=1" )
            else:
                writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
                writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
            
            if outputBaseName == "":
                writer.WriteLine( "OutputDirectory0=%s" % outputFolder )
            else:
                paddingString = "#"
                while len(paddingString) < outputPadding:
                    paddingString += "#"
                writer.WriteLine( "OutputFilename0=%s" % Path.Combine( outputFolder, Path.ChangeExtension( outputBaseName, "." + paddingString + Path.GetExtension( outputBaseName ) ) ) )

        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "redline_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
        if( not submitScene ):
            if (fileSelect and viewSingle) or dirSelect:
                writer.WriteLine( "SceneFile=%s" % sceneFile.replace( "\\", "/" ) )
            
            elif fileSelect and viewStereo:
                writer.WriteLine( "LeftEyeFile=%s" % leftEyeFile.replace( "\\", "/") )
                writer.WriteLine( "RightEyeFile=%s" % rightEyeFile.replace( "\\", "/") )

        #### File Settings ####
        writer.WriteLine( "RenderAllFrames=%s" % renderAllFrames )
        writer.WriteLine( "OutputFolder=%s" % outputFolder.replace( "\\", "/" ) )
        writer.WriteLine( "OutputBaseName=%s" % baseFilename  )
        writer.WriteLine( "AudioFile=%s" % scriptDialog.GetValue( "AudioFileBox" ) )

        #### Format Settings ####
        writer.WriteLine( "OutputFormat=%s" % outputFormat )
        WriteEnum( writer, "OutputFormat", scriptDialog.GetItems( "OutputFormatBox" ) )
        writer.WriteLine( "OutputPadding=%s" % outputPadding )
        writer.WriteLine( "Resolution=%s" % scriptDialog.GetValue( "ResolutionBox" ) )
        WriteEnum( writer, "Resolution", scriptDialog.GetItems( "ResolutionBox" ) )
        writer.WriteLine( "ColorSciVersion=%s" % scriptDialog.GetValue( "ColorVersionBox" ) )
        WriteEnum( writer, "ColorSciVersion", scriptDialog.GetItems( "ColorVersionBox" ) )
        writer.WriteLine( "MakeSubfolder=%s" % scriptDialog.GetValue( "MakeSubfolderBox" ) )

        #### Frame Settings ####
        writer.WriteLine( "Renumber=%s" % renumberStartFrame )
        writer.WriteLine( "ExportPreset=%s" % scriptDialog.GetValue( "ExportPresetBox" ) )
        writer.WriteLine( "PresetFile=%s" % scriptDialog.GetValue( "ExportPresetFileBox" ) )

        #### Misc Settings ####
        writer.WriteLine( "3DMode=%s" % scriptDialog.GetValue( "3dModeBox" ) )
        WriteEnum( writer, "3DMode", scriptDialog.GetItems( "3dModeBox" ) )
        writer.WriteLine( "OverrideAdvLutRender=%s" % scriptDialog.GetValue( "OverrideAdvLutRenderBox" ) )
        writer.WriteLine( "AdvLutRender=%s" % scriptDialog.GetValue( "AdvLutRenderBox" ) )
        WriteEnum( writer, "AdvLutRender", scriptDialog.GetItems( "AdvLutRenderBox" ) )
        writer.WriteLine( "NoRender=%s" % scriptDialog.GetValue( "NoRenderBox" ) )
        writer.WriteLine( "NoAudio=%s" % scriptDialog.GetValue( "NoAudioBox" ) )
        writer.WriteLine( "3DOffset=%s" % scriptDialog.GetValue( "Offset3dBox" ) )

        #### Metadata Settings ####
        writer.WriteLine( "RSXFile=%s" % rsxFile.replace( "\\", "/" ) )
        writer.WriteLine( "UseRSX=%s" % scriptDialog.GetValue( "UseRSXBox" ) )
        WriteEnum( writer, "UseRSX", scriptDialog.GetItems( "UseRSXBox" ) )
        writer.WriteLine( "RMDFile=%s" % rmdFile.replace( "\\", "/" ) )
        writer.WriteLine( "UseRMD=%s" % scriptDialog.GetValue( "UseRMDBox" ) )
        WriteEnum( writer, "UseRMD", scriptDialog.GetItems( "UseRMDBox" ) )
        writer.WriteLine( "UseMeta=%s" % scriptDialog.GetValue( "UseMetaBox" ) )
        writer.WriteLine( "MetaIgnoreFrameGuide=%s" % scriptDialog.GetValue( "MetaIgnoreFrameGuideBox" ) )

        #### Print Meta Settings ####
        writer.WriteLine( "OverridePrintMeta=%s" % scriptDialog.GetValue( "OverridePrintMetaCheckBox" ) )
        writer.WriteLine( "PrintMeta=%s" % scriptDialog.GetValue( "PrintMetaBox" ) )
        WriteEnum( writer, "PrintMeta", scriptDialog.GetItems( "PrintMetaBox" ) )
        writer.WriteLine( "ALEFile=%s" % scriptDialog.GetValue( "ALEFileBox" ) )
        writer.WriteLine( "OverrideReelID=%s" % scriptDialog.GetValue( "OverrideReelIDCheckBox" ) )
        writer.WriteLine( "ReelID=%s" % scriptDialog.GetValue( "ReelIDBox" ) )
        WriteEnum( writer, "ReelID", scriptDialog.GetItems( "ReelIDBox" ) )
        writer.WriteLine( "OverrideClipFrameRate=%s" % scriptDialog.GetValue( "OverrideClipFrameRateCheckBox" ) )
        writer.WriteLine( "ClipFrameRate=%s" % scriptDialog.GetValue( "ClipFrameRateBox" ) )
        WriteEnum( writer, "ClipFrameRate", scriptDialog.GetItems( "ClipFrameRateBox" ) )

        #### Crop and Scale Settings ####
        writer.WriteLine( "Crop=%s" % scriptDialog.GetValue( "CropBox" ) )
        writer.WriteLine( "CropWidth=%s" % cropWidth )
        writer.WriteLine( "CropHeight=%s" % cropHeight )
        writer.WriteLine( "CropOriginX=%s" % cropOriginX )
        writer.WriteLine( "CropOriginY=%s" % cropOriginY )
        writer.WriteLine( "Scale=%s" % scriptDialog.GetValue( "ScaleBox" ) )
        writer.WriteLine( "ScaleWidth=%s" % scaleWidth )
        writer.WriteLine( "ScaleHeight=%s" % scaleHeight )
        writer.WriteLine( "ScaleFit=%s" % scriptDialog.GetValue( "ScaleFitBox" ) )
        WriteEnum( writer, "ScaleFit", scriptDialog.GetItems( "ScaleFitBox" ) )
        writer.WriteLine( "ScaleFilter=%s" % scriptDialog.GetValue( "ScaleFilterBox" ) )
        WriteEnum( writer, "ScaleFilter", scriptDialog.GetItems( "ScaleFilterBox" ) )
        
        writer.WriteLine( "OverrideForceFlipHorizontal=%s" % scriptDialog.GetValue( "ForceFlipHorizontalCheckBox" ) )
        writer.WriteLine( "ForceFlipHorizontal=%s" % scriptDialog.GetValue( "ForceFlipHorizontalBox" ) )
        writer.WriteLine( "OverrideForceFlipVertical=%s" % scriptDialog.GetValue( "ForceFlipVerticalCheckBox" ) )
        writer.WriteLine( "ForceFlipVertical=%s" % scriptDialog.GetValue( "ForceFlipVerticalBox" ) )
        writer.WriteLine( "OverrideRotate=%s" % scriptDialog.GetValue( "OverrideRotateCheckBox" ) )
        writer.WriteLine( "Rotate=%s" % scriptDialog.GetValue( "RotateBox" ) )
        WriteEnum( writer, "Rotate", scriptDialog.GetItems( "RotateBox" ) )
        writer.WriteLine( "OverridePreventNegativePixels=%s" % scriptDialog.GetValue( "OverridePreventNegPixelsCheckBox" ) )
        writer.WriteLine( "PreventNegativePixels=%s" % scriptDialog.GetValue( "PreventNegPixelsBox" ) )

        #### Quicktime Transcode Settings ####
        writer.WriteLine( "QTCodec=%s" % scriptDialog.GetValue( "QTCodecBox" ) )
        WriteEnum( writer, "QTCodec", scriptDialog.GetItems( "QTCodecBox" ) )
        writer.WriteLine( "QTClobber=%s" % scriptDialog.GetValue( "QTClobberBox" ) )

        #### Burn-In Settings ####
        writer.WriteLine( "Burn=%s" % scriptDialog.GetValue( "BurnBox" ) )
        writer.WriteLine( "BurnFrames=%s" % scriptDialog.GetValue( "BurnFramesBox" ) )
        WriteEnum( writer, "BurnFrames", scriptDialog.GetItems( "BurnFramesBox" ) )
        writer.WriteLine( "BurnFont=%s" % scriptDialog.GetValue( "BurnFontBox" ) )
        WriteEnum( writer, "BurnFont", scriptDialog.GetItems( "BurnFontBox" ) )
        writer.WriteLine( "BurnSize=%s" % scriptDialog.GetValue( "BurnSizeBox" ) )
        writer.WriteLine( "BurnBase=%s" % scriptDialog.GetValue( "BurnBaseBox" ) )
        writer.WriteLine( "BurnLowerLeft=%s" % scriptDialog.GetValue( "BurnLowerLeftBox" ) )
        WriteEnum( writer, "BurnLowerLeft", scriptDialog.GetItems( "BurnLowerLeftBox" ) )
        writer.WriteLine( "BurnLowerRight=%s" % scriptDialog.GetValue( "BurnLowerRightBox" ) )
        WriteEnum( writer, "BurnLowerRight", scriptDialog.GetItems( "BurnLowerRightBox" ) )
        writer.WriteLine( "BurnUpperLeft=%s" % scriptDialog.GetValue( "BurnUpperLeftBox" ) )
        WriteEnum( writer, "BurnUpperLeft", scriptDialog.GetItems( "BurnUpperLeftBox" ) )
        writer.WriteLine( "BurnUpperRight=%s" % scriptDialog.GetValue( "BurnUpperRightBox" ) )
        WriteEnum( writer, "BurnUpperRight", scriptDialog.GetItems( "BurnUpperRightBox" ) )
        writer.WriteLine( "BurnTextR=%s" % scriptDialog.GetValue( "BurnTextRBox" ) )
        writer.WriteLine( "BurnTextG=%s" % scriptDialog.GetValue( "BurnTextGBox" ) )
        writer.WriteLine( "BurnTextB=%s" % scriptDialog.GetValue( "BurnTextBBox" ) )
        writer.WriteLine( "BurnTextA=%s" % scriptDialog.GetValue( "BurnTextABox" ) )
        writer.WriteLine( "BurnBackgroundR=%s" % scriptDialog.GetValue( "BurnBackgroundRBox" ) )
        writer.WriteLine( "BurnBackgroundG=%s" % scriptDialog.GetValue( "BurnBackgroundGBox" ) )
        writer.WriteLine( "BurnBackgroundB=%s" % scriptDialog.GetValue( "BurnBackgroundBBox" ) )
        writer.WriteLine( "BurnBackgroundA=%s" % scriptDialog.GetValue( "BurnBackgroundABox" ) )
        writer.WriteLine( "BurnFramesCount=%s" % scriptDialog.GetValue( "BurnFramesCountBox" ) )

        #### Watermark Settings ####
        writer.WriteLine( "OverrideWatermark=%s" % scriptDialog.GetValue( "WatermarkBox" ) )
        writer.WriteLine( "WatermarkFont=%s" % scriptDialog.GetValue( "WatermarkFontBox" ) )
        WriteEnum( writer, "WatermarkFont", scriptDialog.GetItems( "WatermarkFontBox" ) )
        writer.WriteLine( "WatermarkText=%s" % scriptDialog.GetValue( "WatermarkTextBox" ) )
        writer.WriteLine( "WatermarkSz=%s" % scriptDialog.GetValue( "WatermarkSzBox" ) )
        writer.WriteLine( "WatermarkBase=%s" % scriptDialog.GetValue( "WatermarkBaseBox" ) )
        writer.WriteLine( "WatermarkTxtR=%s" % scriptDialog.GetValue( "WatermarkTxtRBox" ) )
        writer.WriteLine( "WatermarkTxtG=%s" % scriptDialog.GetValue( "WatermarkTxtGBox" ) )
        writer.WriteLine( "WatermarkTxtB=%s" % scriptDialog.GetValue( "WatermarkTxtBBox" ) )
        writer.WriteLine( "WatermarkTxtA=%s" % scriptDialog.GetValue( "WatermarkTxtABox" ) )

        #### Color/Gamma Space Settings ####
        writer.WriteLine( "OverrideColorSpace=%s" % scriptDialog.GetValue( "ColorSpaceCheckBox" ) )
        writer.WriteLine( "ColorSpace=%s" % scriptDialog.GetValue( "ColorSpaceBox" ) )
        WriteEnum( writer, "ColorSpace", scriptDialog.GetItems( "ColorSpaceBox" ) )
        writer.WriteLine( "OverrideGammaCurve=%s" % scriptDialog.GetValue( "GammaCurveCheckBox" ) )
        writer.WriteLine( "GammaCurve=%s" % scriptDialog.GetValue( "GammaCurveBox" ) )
        WriteEnum( writer, "GammaCurve", scriptDialog.GetItems( "GammaCurveBox" ) )
        writer.WriteLine( "OverrideNoiseReduction=%s" % scriptDialog.GetValue( "NoiseReductionCheckBox" ) )
        writer.WriteLine( "NoiseReduction=%s" % scriptDialog.GetValue( "NoiseReductionBox" ) )
        WriteEnum( writer, "NoiseReduction", scriptDialog.GetItems( "NoiseReductionBox" ) )
        writer.WriteLine( "OverrideDetail=%s" % scriptDialog.GetValue( "DetailCheckBox" ) )
        writer.WriteLine( "Detail=%s" % scriptDialog.GetValue( "DetailBox" ) )
        WriteEnum( writer, "Detail", scriptDialog.GetItems( "DetailBox" ) )
        writer.WriteLine( "OverrideOLPFCompensation=%s" % scriptDialog.GetValue( "OLPFCompensationCheckBox" ) )
        writer.WriteLine( "OLPFCompensation=%s" % scriptDialog.GetValue( "OLPFCompensationBox" ) )
        WriteEnum( writer, "OLPFCompensation", scriptDialog.GetItems( "OLPFCompensationBox" ) )
        writer.WriteLine( "OverrideSMPTEColorRange=%s" % scriptDialog.GetValue( "SMPTEColorRangeCheckBox" ) )
        writer.WriteLine( "SMPTEColorRange=%s" % scriptDialog.GetValue( "SMPTEColorRangeBox" ) )
        WriteEnum( writer, "SMPTEColorRange", scriptDialog.GetItems( "SMPTEColorRangeBox" ) )

        #### Color Settings ####
        writer.WriteLine( "OverrideISO=%s" % scriptDialog.GetValue( "ISOCheckBox" ) )
        writer.WriteLine( "ISO=%s" % scriptDialog.GetValue( "ISOBox" ) )
        writer.WriteLine( "OverrideFlut=%s" % scriptDialog.GetValue( "FlutCheckBox" ) )
        writer.WriteLine( "Flut=%s" % scriptDialog.GetValue( "FlutBox" ) )
        writer.WriteLine( "OverrideShadow=%s" % scriptDialog.GetValue( "ShadowCheckBox" ) )
        writer.WriteLine( "Shadow=%s" % scriptDialog.GetValue( "ShadowBox" ) )
        writer.WriteLine( "OverrideKelvin=%s" % scriptDialog.GetValue( "KelvinCheckBox" ) )
        writer.WriteLine( "Kelvin=%s" % scriptDialog.GetValue( "KelvinBox" ) )
        writer.WriteLine( "OverrideTint=%s" % scriptDialog.GetValue( "TintCheckBox" ) )
        writer.WriteLine( "Tint=%s" % scriptDialog.GetValue( "TintBox" ) )
        writer.WriteLine( "OverrideExposure=%s" % scriptDialog.GetValue( "ExposureCheckBox" ) )
        writer.WriteLine( "Exposure=%s" % scriptDialog.GetValue( "ExposureBox" ) )
        writer.WriteLine( "OverrideSaturation=%s" % scriptDialog.GetValue( "SaturationCheckBox" ) )
        writer.WriteLine( "Saturation=%s" % scriptDialog.GetValue( "SaturationBox" ) )
        writer.WriteLine( "OverrideContrast=%s" % scriptDialog.GetValue( "ContrastCheckBox" ) )
        writer.WriteLine( "Contrast=%s" % scriptDialog.GetValue( "ContrastBox" ) )
        writer.WriteLine( "OverrideBrightness=%s" % scriptDialog.GetValue( "BrightnessCheckBox" ) )
        writer.WriteLine( "Brightness=%s" % scriptDialog.GetValue( "BrightnessBox" ) )
        writer.WriteLine( "OverrideRed=%s" % scriptDialog.GetValue( "RedCheckBox" ) )
        writer.WriteLine( "Red=%s" % scriptDialog.GetValue( "RedBox" ) )
        writer.WriteLine( "OverrideGreen=%s" % scriptDialog.GetValue( "GreenCheckBox" ) )
        writer.WriteLine( "Green=%s" % scriptDialog.GetValue( "GreenBox" ) )
        writer.WriteLine( "OverrideBlue=%s" % scriptDialog.GetValue( "BlueCheckBox" ) )
        writer.WriteLine( "Blue=%s" % scriptDialog.GetValue( "BlueBox" ) )
        writer.WriteLine( "OverrideDRX=%s" % scriptDialog.GetValue( "DRXCheckBox" ) )
        writer.WriteLine( "DRX=%s" % scriptDialog.GetValue( "DRXBox" ) )
        writer.WriteLine( "OverrideDEB=%s" % scriptDialog.GetValue( "DEBCheckBox" ) )
        writer.WriteLine( "DEB=%s" % scriptDialog.GetValue( "DEBBox" ) )
        WriteEnum( writer, "DEB", scriptDialog.GetItems( "DEBBox" ) )

        #### Lift Gamma Gain Settings ####
        writer.WriteLine( "OverrideRedLift=%s" % scriptDialog.GetValue( "RedLiftCheckBox" ) )
        writer.WriteLine( "RedLift=%s" % scriptDialog.GetValue( "RedLiftBox" ) )
        writer.WriteLine( "OverrideGreenLift=%s" % scriptDialog.GetValue( "GreenLiftCheckBox" ) )
        writer.WriteLine( "GreenLift=%s" % scriptDialog.GetValue( "GreenLiftBox" ) )
        writer.WriteLine( "OverrideBlueLift=%s" % scriptDialog.GetValue( "BlueLiftCheckBox" ) )
        writer.WriteLine( "BlueLift=%s" % scriptDialog.GetValue( "BlueLiftBox" ) )
        writer.WriteLine( "OverrideRedGamma=%s" % scriptDialog.GetValue( "RedGammaCheckBox" ) )
        writer.WriteLine( "RedGamma=%s" % scriptDialog.GetValue( "RedGammaBox" ) )
        writer.WriteLine( "OverrideGreenGamma=%s" % scriptDialog.GetValue( "GreenGammaCheckBox" ) )
        writer.WriteLine( "GreenGamma=%s" % scriptDialog.GetValue( "GreenGammaBox" ) )
        writer.WriteLine( "OverrideBlueGamma=%s" % scriptDialog.GetValue( "BlueGammaCheckBox" ) )
        writer.WriteLine( "BlueGamma=%s" % scriptDialog.GetValue( "BlueGammaBox" ) )
        writer.WriteLine( "OverrideRedGain=%s" % scriptDialog.GetValue( "RedGainCheckBox" ) )
        writer.WriteLine( "RedGain=%s" % scriptDialog.GetValue( "RedGainBox" ) )
        writer.WriteLine( "OverrideGreenGain=%s" % scriptDialog.GetValue( "GreenGainCheckBox" ) )
        writer.WriteLine( "GreenGain=%s" % scriptDialog.GetValue( "GreenGainBox" ) )
        writer.WriteLine( "OverrideBlueGain=%s" % scriptDialog.GetValue( "BlueGainCheckBox" ) )
        writer.WriteLine( "BlueGain=%s" % scriptDialog.GetValue( "BlueGainBox" ) )

        #### Print Density Settings ####
        writer.WriteLine( "OverridePdBlack=%s" % scriptDialog.GetValue( "PdBlackCheckBox" ) )
        writer.WriteLine( "PdBlack=%s" % scriptDialog.GetValue( "PdBlackBox" ) )
        writer.WriteLine( "OverridePdWhite=%s" % scriptDialog.GetValue( "PdWhiteCheckBox" ) )
        writer.WriteLine( "PdWhite=%s" % scriptDialog.GetValue( "PdWhiteBox" ) )
        writer.WriteLine( "OverridePdGamma=%s" % scriptDialog.GetValue( "PdGammaCheckBox" ) )
        writer.WriteLine( "PdGamma=%s" % scriptDialog.GetValue( "PdGammaBox" ) )

        #### Curve Settings ####
        writer.WriteLine( "OverrideBlack=%s" % scriptDialog.GetValue( "BlackCheckBox" ) )
        writer.WriteLine( "Black=%s" % scriptDialog.GetValue( "BlackBox" ) )
        writer.WriteLine( "OverrideWhite=%s" % scriptDialog.GetValue( "WhiteCheckBox" ) )
        writer.WriteLine( "White=%s" % scriptDialog.GetValue( "WhiteBox" ) )

        #### New Curve Point Values ####
        writer.WriteLine( "OverrideLumaCurve=%s" % scriptDialog.GetValue( "LumaCurveCheckBox" ) )
        writer.WriteLine( "LumaCurve=%s" % scriptDialog.GetValue( "LumaCurveBox" ) )
        writer.WriteLine( "OverrideRedCurve=%s" % scriptDialog.GetValue( "RedCurveCheckBox" ) )
        writer.WriteLine( "RedCurve=%s" % scriptDialog.GetValue( "RedCurveBox" ) )
        writer.WriteLine( "OverrideGreenCurve=%s" % scriptDialog.GetValue( "GreenCurveCheckBox" ) )
        writer.WriteLine( "GreenCurve=%s" % scriptDialog.GetValue( "GreenCurveBox" ) )
        writer.WriteLine( "OverrideBlueCurve=%s" % scriptDialog.GetValue( "BlueCurveCheckBox" ) )
        writer.WriteLine( "BlueCurve=%s" % scriptDialog.GetValue( "BlueCurveBox" ) )

        #### HDR Settings ####
        writer.WriteLine( "OverrideHdrMode=%s" % scriptDialog.GetValue( "HdrModeCheckBox" ) )
        writer.WriteLine( "HdrMode=%s" % scriptDialog.GetValue( "HdrModeBox" ) )
        WriteEnum( writer, "HdrMode", scriptDialog.GetItems( "HdrModeBox" ) )
        writer.WriteLine( "HdrBias=%s" % scriptDialog.GetValue( "HdrBiasBox" ) )

        #### DPX Settings ####
        writer.WriteLine( "OverrideDpxByteOrder=%s" % scriptDialog.GetValue( "DpxByteOrderCheckBox" ) )
        writer.WriteLine( "DpxByteOrder=%s" % scriptDialog.GetValue( "DpxByteOrderBox" ) )
        WriteEnum( writer, "DpxByteOrder", scriptDialog.GetItems( "DpxByteOrderBox" ) )
        writer.WriteLine( "OverrideDpxBitDepth=%s" % scriptDialog.GetValue( "DpxBitDepthCheckBox" ) )
        writer.WriteLine( "DpxBitDepth=%s" % scriptDialog.GetValue( "DpxBitDepthBox" ) )
        WriteEnum( writer, "DpxBitDepth", scriptDialog.GetItems( "DpxBitDepthBox" ) )
        writer.WriteLine( "OverrideDpxMaxWriters=%s" % scriptDialog.GetValue( "DpxMaxWritersCheckBox" ) )
        writer.WriteLine( "DpxMaxWriters=%s" % scriptDialog.GetValue( "DpxMaxWritersBox" ) )

        #### OpenEXR Settings ####
        writer.WriteLine( "OverrideExrCompression=%s" % scriptDialog.GetValue( "ExrCompressionCheckBox" ) )
        writer.WriteLine( "ExrCompression=%s" % scriptDialog.GetValue( "ExrCompressionBox" ) )
        WriteEnum( writer, "ExrCompression", scriptDialog.GetItems( "ExrCompressionBox" ) )
        writer.WriteLine( "ExrDWACompression=%s" % scriptDialog.GetValue( "ExrCompressionDwaaBox" ) )
        writer.WriteLine( "OverrideExrMultiView=%s" % scriptDialog.GetValue( "ExrMultiViewCheckBox" ) )
        writer.WriteLine( "ExrMultiView=%s" % scriptDialog.GetValue( "ExrMultiViewBox" ) )
        WriteEnum( writer, "ExrMultiView", scriptDialog.GetItems( "ExrMultiViewBox" ) )
        writer.WriteLine( "OverrideExrWriters=%s" % scriptDialog.GetValue( "ExrMaxWritersCheckBox" ) )
        writer.WriteLine( "ExrWriters=%s" % scriptDialog.GetValue( "ExrMaxWritersBox" ) )
        writer.WriteLine( "OverrideExrACES=%s" % scriptDialog.GetValue( "ExrAcesCheckBox" ) )
        writer.WriteLine( "ExrACES=%s" % scriptDialog.GetValue( "ExrAcesBox" ) )
        WriteEnum( writer, "ExrACES", scriptDialog.GetItems( "ExrAcesBox" ) )
        writer.WriteLine( "OverrideExrSoftClamp=%s" % scriptDialog.GetValue( "ExrSoftClampCheckBox" ) )
        writer.WriteLine( "ExrSoftClamp=%s" % scriptDialog.GetValue( "ExrSoftClampBox" ) )
        WriteEnum( writer, "ExrSoftClamp", scriptDialog.GetItems( "ExrSoftClampBox" ) )

        #### R3D Trim Settings ####
        writer.WriteLine( "TrimRmdSidecar=%s" % scriptDialog.GetValue( "R3dTrimRmdSidecarBox" ) )
        writer.WriteLine( "TrimQtWrappers=%s" % scriptDialog.GetValue( "R3dTrimQtWrappersBox" ) )
        writer.WriteLine( "OverrideTrimFcpXml=%s" % scriptDialog.GetValue( "R3dTrimFcpXmlCheckBox" ) )
        writer.WriteLine( "TrimFcpXml=%s" % scriptDialog.GetValue( "R3dTrimFcpXmlBox" ) )
        WriteEnum( writer, "TrimFcpXml", scriptDialog.GetItems( "R3dTrimFcpXmlBox" ) )
        writer.WriteLine( "TrimAudio=%s" % scriptDialog.GetValue( "R3dTrimAudioBox" ) )
        writer.WriteLine( "OverrideTrimChangeFrameRate=%s" % scriptDialog.GetValue( "R3dTrimChangeFrameRateCheckBox" ) )
        writer.WriteLine( "TrimChangeFrameRate=%s" % scriptDialog.GetValue( "R3dTrimChangeFrameRateBox" ) )
        WriteEnum( writer, "TrimChangeFrameRate", scriptDialog.GetItems( "R3dTrimChangeFrameRateBox" ) )
        writer.WriteLine( "OverrideTrimChangeOLPF=%s" % scriptDialog.GetValue( "R3dTrimChangeOLPFCheckBox" ) )
        writer.WriteLine( "TrimChangeOLPF=%s" % scriptDialog.GetValue( "R3dTrimChangeOLPFBox" ) )

        #### Avid DNX Settings ####
        writer.WriteLine( "OverrideDnxCodec=%s" % scriptDialog.GetValue( "DnxCodecCheckBox" ) )
        writer.WriteLine( "DnxCodec=%s" % scriptDialog.GetValue( "DnxCodecBox" ) )
        WriteEnum( writer, "DnxCodec", scriptDialog.GetItems( "DnxCodecBox" ) )
        writer.WriteLine( "OverrideDnxFrameRate=%s" % scriptDialog.GetValue( "DnxFrameRateCheckBox" ) )
        writer.WriteLine( "DnxFrameRate=%s" % scriptDialog.GetValue( "DnxFrameRateBox" ) )
        WriteEnum( writer, "DnxFrameRate", scriptDialog.GetItems( "DnxFrameRateBox" ) )

        #### REDray Settings ####
        writer.WriteLine( "OverrideRrContentTitle=%s" % scriptDialog.GetValue( "RrContentTitleCheckBox" ) )
        writer.WriteLine( "RrContentTitle=%s" % scriptDialog.GetValue( "RrContentTitleBox" ) )
        writer.WriteLine( "OverrideRrPosterFrame=%s" % scriptDialog.GetValue( "RrPosterFrameCheckBox" ) )
        writer.WriteLine( "RrPosterFrame=%s" % scriptDialog.GetValue( "RrPosterFrameBox" ) )

        #### Rocket Settings ####
        writer.WriteLine( "NoRocket=%s" % scriptDialog.GetValue( "RedrayNoRocketBox" ) )
        writer.WriteLine( "SingleRocket=%s" % scriptDialog.GetValue( "RedraySingleRocketBox" ) )
        writer.WriteLine( "ForceRocket=%s" % scriptDialog.GetValue( "RedrayForceRocketBox" ) )
        writer.WriteLine( "OverrideUseRocket=%s" % scriptDialog.GetValue( "UseRocketCheckBox" ) )
        writer.WriteLine( "UseRocket=%s" % scriptDialog.GetValue( "UseRocketBox" ) )

        #### Graph Processing/OpenCL/CUDA Settings ####
        writer.WriteLine( "OverrideGpuPlatform=%s" % scriptDialog.GetValue( "GpuPlatformCheckBox" ) )
        writer.WriteLine( "GpuPlatform=%s" % scriptDialog.GetValue( "GpuPlatformBox" ) )
        WriteEnum( writer, "GpuPlatform", scriptDialog.GetItems( "GpuPlatformBox" ) )
        writer.WriteLine( "GPUsSelectDevices=%s" % scriptDialog.GetValue( "GPUsSelectDevicesBox" ) )
        writer.WriteLine( "OverrideDecodeThreads=%s" % scriptDialog.GetValue( "DecodeThreadsCheckBox" ) )
        writer.WriteLine( "DecodeThreads=%s" % scriptDialog.GetValue( "DecodeThreadsBox" ) )
        writer.WriteLine( "OverrideNumGraphs=%s" % scriptDialog.GetValue( "NumGraphsCheckBox" ) )
        writer.WriteLine( "NumGraphs=%s" % scriptDialog.GetValue( "NumGraphsBox" ) )
        writer.WriteLine( "OverrideNumOclStreams=%s" % scriptDialog.GetValue( "NumOclStreamsCheckBox" ) )
        writer.WriteLine( "NumOclStreams=%s" % scriptDialog.GetValue( "NumOclStreamsBox" ) )

        #### Advanced Dragon Debayer (A.D.D.) ####
        writer.WriteLine( "EnableADD=%s" % scriptDialog.GetValue( "AddEnableCheckBox" ) )
        writer.WriteLine( "OverrideADDUsmAmount=%s" % scriptDialog.GetValue( "AddUsmAmountCheckBox" ) )
        writer.WriteLine( "ADDUsmAmount=%s" % scriptDialog.GetValue( "AddUsmAmountBox" ) )
        writer.WriteLine( "OverrideADDUsmRadius=%s" % scriptDialog.GetValue( "AddUsmRadiusCheckBox" ) )
        writer.WriteLine( "ADDUsmRadius=%s" % scriptDialog.GetValue( "AddUsmRadiusBox" ) )
        writer.WriteLine( "OverrideADDUsmThreshold=%s" % scriptDialog.GetValue( "AddUsmThresholdCheckBox" ) )
        writer.WriteLine( "ADDUsmThreshold=%s" % scriptDialog.GetValue( "AddUsmThresholdBox" ) )
        writer.WriteLine( "ADDUsmDisable=%s" % scriptDialog.GetValue( "AddUsmDisableBox" ) )

        #### 3D LUT Settings ####
        writer.WriteLine( "LutFile=%s" % scriptDialog.GetValue( "LutFileBox" ) )
        writer.WriteLine( "OverrideLutEdgeLength=%s" % scriptDialog.GetValue( "LutEdgeLengthCheckBox" ) )
        writer.WriteLine( "LutEdgeLength=%s" % scriptDialog.GetValue( "LutEdgeLengthBox" ) )

        writer.Close()
        
        # Setup the command line arguments.
        arguments = StringCollection()
        if( len( sceneFiles ) == 1 ):
            arguments.Add( "-notify" )
        
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        
        if( submitScene ):
            if (fileSelect and viewSingle) or dirSelect:
                arguments.Add( sceneFile )
            
            elif fileSelect and viewStereo:
                arguments.Add( leftEyeFile )
                arguments.Add( rightEyeFile )
        
        # Now submit the job.
        exitCode = ClientUtils.ExecuteCommand( arguments )
        if( exitCode == 0 ):
            successes = successes + 1
        else:
            failures = failures + 1
        
    if( len( sceneFiles ) > 1 ):
        scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )
