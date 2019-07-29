import unicodedata

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

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
startup = True
updatingInput1File = False
updatingInput2File = False

sourceDialog = None
currSelectedSource = ""

sourceDictionary = {}
ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = True

outputCodecs = {}
audioCodecs = {}

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global sourceDialog
    global settings
    global startup
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    sourceDialog = DeadlineScriptDialog()
    
    sourceDialog.SetSize( 400, 70 )
    sourceDialog.AllowResizingDialog( False )
    
    sourceDialog.SetTitle( "Specify Name To Uniquely Identify Source" )
    sourceDialog.SetIcon( sourceDialog.GetIcon( 'RVIO' ) )
    
    sourceDialog.AddGrid()
    sourceDialog.AddControlToGrid( "SourceTitleLabel", "LabelControl", "Specify Name To Uniquely Identify Source", 0, 0,colSpan=4, expand=False )
    
    sourceDialog.AddControlToGrid( "SourceNameLabel", "LabelControl", "Name", 1, 0, expand=False )
    sourceDialog.AddControlToGrid( "SourceNameBox", "TextControl", "Untitled", 1, 1, colSpan=3 )
    
    sourceOKButton = sourceDialog.AddControlToGrid( "SourceOKButton", "ButtonControl", "OK", 2, 2, expand=False )
    sourceOKButton.ValueModified.connect(SourceOKPressed)

    sourceCancelButton = sourceDialog.AddControlToGrid( "SourceCancelButton", "ButtonControl", "Cancel", 2, 3, expand=False )
    sourceCancelButton.ValueModified.connect(SourceCancelPressed)

    sourceDialog.EndGrid()
    
    scriptDialog = DeadlineScriptDialog()	
    scriptDialog.SetTitle( "Submit RVIO Job To Deadline" )
    scriptDialog.SetIcon( RepositoryUtils.GetRepositoryFilePath( "plugins/RVIO/RVIO.ico", True ) )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 2, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 2, 1 )
    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 2, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 3, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 3, 1 )
    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 3, 2, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 3, 3 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 4, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 4, 1 )
    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 4, 2, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 4, 3 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 5, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 5, 1 )
    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 5, 2, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering. ", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 5, 3 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 6, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 6, 1 )
    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 6, 2, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 6, 3 )

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 7, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist.", False )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 8, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 8, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 8, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render. ", False )
    scriptDialog.EndGrid()
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    scriptDialog.AddTabPage( "Layers" )

    scriptDialog.AddGrid()
    AddButton = scriptDialog.AddControlToGrid( "AddButton", "ButtonControl", "New", 0, 0, "Add a new layer.", False )
    RenameButton = scriptDialog.AddControlToGrid( "RenameButton", "ButtonControl", "Rename", 0, 1, "Rename the selected layer.", False )
    RemoveButton = scriptDialog.AddControlToGrid( "RemoveButton", "ButtonControl", "Remove", 0, 2, "Remove the selected layer.", False )
    ClearButton = scriptDialog.AddControlToGrid( "ClearButton", "ButtonControl", "Clear", 0, 3, "Clear all current layers.", False )
    scriptDialog.AddHorizontalSpacerToGrid( "DummySourceLabel", 0, 4 )
    LoadButton = scriptDialog.AddControlToGrid( "LoadButton", "ButtonControl", "Load Layers", 0, 5, "Load saved layers from disk.", False )
    SaveButton = scriptDialog.AddControlToGrid( "SaveButton", "ButtonControl", "Save Layers", 0, 6, "Save the current layers to disk.", False )

    SourceBox = scriptDialog.AddComboControlToGrid( "SourceBox", "ListControl", " ", [], 1, 0, colSpan=7 )
    scriptDialog.EndGrid()
    
    LoadButton.ValueModified.connect(LoadPressed)
    SaveButton.ValueModified.connect(SavePressed)
    AddButton.ValueModified.connect(AddPressed)
    RenameButton.ValueModified.connect(RenamePressed)
    RemoveButton.ValueModified.connect(RemovePressed)
    ClearButton.ValueModified.connect(ClearPressed)
    SourceBox.ValueModified.connect(SelectedSourceChanged)

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SourceInput1Label", "LabelControl", "Source 1 (Required)", 0, 0, "The first source file (required). If specifying a sequence, you can set the range to the right of the file name.", False )
    SourceInput1Box = scriptDialog.AddSelectionControlToGrid( "SourceInput1Box", "FileBrowserControl", "", "All Files (*)", 0, 1, colSpan=3 )
    scriptDialog.AddRangeControlToGrid( "SourceStart1Box", "RangeControl", 0, -99999999, 99999999, 0, 1, 0, 4, expand=False )
    scriptDialog.AddControlToGrid( "SourceRange1Label", "LabelControl", "To", 0, 5, expand=False )
    scriptDialog.AddRangeControlToGrid( "SourceEnd1Box", "RangeControl", 0, -99999999, 99999999, 0, 1, 0, 6, expand=False )

    scriptDialog.AddControlToGrid( "SourceInput2Label", "LabelControl", "Source 2 (Optional)", 1, 0, "The second source file (optional). If specifying a sequence, you can set the range to the right of the file name.", False )
    SourceInput2Box = scriptDialog.AddSelectionControlToGrid( "SourceInput2Box", "FileBrowserControl", "", "All Files (*)", 1, 1, colSpan=3 )
    scriptDialog.AddRangeControlToGrid( "SourceStart2Box", "RangeControl", 0, -99999999, 99999999, 0, 1, 1, 4, expand=False )
    scriptDialog.AddControlToGrid( "SourceRange2Label", "LabelControl", "To", 1, 5, expand=False )
    scriptDialog.AddRangeControlToGrid( "SourceEnd2Box", "RangeControl", 0, -99999999, 99999999, 0, 1, 1, 6, expand=False )

    scriptDialog.AddControlToGrid( "SourceAudioLabel", "LabelControl", "Audio Files (Optional)", 2, 0, "A commana separatedl list of audio file (optional).", False )
    scriptDialog.AddSelectionControlToGrid( "SourceAudioBox", "MultiFileBrowserControl", "", "All Files (*)", 2, 1, colSpan=3 )
    scriptDialog.AddSelectionControlToGrid( "NoMovieAudioBox", "CheckBoxControl", False, "Disable Movie Audio", 2, 4, "Disable source movies baked-in audio", colSpan=3 )
    scriptDialog.EndGrid()
    
    SourceInput1Box.ValueModified.connect(Input1Changed)
    SourceInput2Box.ValueModified.connect(Input2Changed)
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "OverridesSeparator", "SeparatorControl", "Source Overrides (Optional)", 0, 0, colSpan=7)

    OverrideAspectRatioBox = scriptDialog.AddSelectionControlToGrid( "OverrideAspectRatioBox", "CheckBoxControl", False, "Pixel Aspect Ratio", 1, 0, "Set the Pixel Aspec Ratio.", False )
    scriptDialog.AddRangeControlToGrid( "AspectRatioBox", "RangeControl", 1.3333, -1000, 1000, 4, 1, 1, 1 )
    OverrideFileLutBox = scriptDialog.AddSelectionControlToGrid( "OverrideFileLutBox", "CheckBoxControl", False, "File LUT", 1, 2, "Associate a file LUT with the source.", False )
    scriptDialog.AddSelectionControlToGrid( "FileLutBox", "FileBrowserControl", "", "All Files (*)", 1, 3, colSpan=4 )

    OverrideRangeOffsetBox = scriptDialog.AddSelectionControlToGrid( "OverrideRangeOffsetBox", "CheckBoxControl", False, "Start Frame Offset", 2, 0, "Shifts first and last frames in the source range.", False )
    scriptDialog.AddRangeControlToGrid( "RangeOffsetBox", "RangeControl", 0, -99999, 99999, 0, 1, 2, 1 )
    OverrideLookLutBox = scriptDialog.AddSelectionControlToGrid( "OverrideLookLutBox", "CheckBoxControl", False, "Look LUT", 2, 2, "Associate a look LUT with the source.", False )
    scriptDialog.AddSelectionControlToGrid( "LookLutBox", "FileBrowserControl", "", "All Files (*)", 2, 3, colSpan=4 )

    OverrideFPSBox = scriptDialog.AddSelectionControlToGrid( "OverrideFPSBox", "CheckBoxControl", False, "Frames Per Second", 3, 0, "Frames per second.", False )
    scriptDialog.AddRangeControlToGrid( "FPSBox", "RangeControl", 24.00, 0, 99999, 2, 1, 3, 1 )
    OverridePreCacheLutBox = scriptDialog.AddSelectionControlToGrid( "OverridePreCacheLutBox", "CheckBoxControl", False, "Pre-Cache LUT", 3, 2, "Associate a pre-cache software LUT with the source.", False )
    scriptDialog.AddSelectionControlToGrid( "PreCacheLutBox", "FileBrowserControl", "", "All Files (*)", 3, 3, colSpan=4 )

    OverrideAudioOffsetBox = scriptDialog.AddSelectionControlToGrid( "OverrideAudioOffsetBox", "CheckBoxControl", False, "Audio Offset", 4, 0, "Shifts audio in seconds.", False )
    scriptDialog.AddRangeControlToGrid( "AudioOffsetBox", "RangeControl", 0, -99999, 99999, 2, 1, 4, 1 )
    OverrideChannelsBox = scriptDialog.AddSelectionControlToGrid( "OverrideChannelsBox", "CheckBoxControl", False, "Remap Channels", 4, 2, "Remap color channesl for this source (channel names separated by commas).", False )
    scriptDialog.AddControlToGrid( "ChannelsBox", "TextControl", "", 4, 3, colSpan=4 )

    OverrideStereoOffsetBox = scriptDialog.AddSelectionControlToGrid( "OverrideStereoOffsetBox", "CheckBoxControl", False, "Stereo Eye Offset", 5, 0, "Set the Stereo Eye Relative Offset.", False )
    scriptDialog.AddRangeControlToGrid( "StereoOffsetBox", "RangeControl", 0, -99999, 99999, 2, 1, 5, 1 )
    OverrideCropBox = scriptDialog.AddSelectionControlToGrid( "OverrideCropBox", "CheckBoxControl", False, "Crop (X0 Y0 X1 Y1)", 5, 2, "Crop image to box.", False )
    scriptDialog.AddRangeControlToGrid( "CropX0Box", "RangeControl", 0, -99999, 99999, 0, 1, 5, 3 )
    scriptDialog.AddRangeControlToGrid( "CropY0Box", "RangeControl", 0, -99999, 99999, 0, 1, 5, 4 )
    scriptDialog.AddRangeControlToGrid( "CropX1Box", "RangeControl", 0, -99999, 99999, 0, 1, 5, 5 )
    scriptDialog.AddRangeControlToGrid( "CropY1Box", "RangeControl", 0, -99999, 99999, 0, 1, 5, 6 )

    OverrideVolumeBox = scriptDialog.AddSelectionControlToGrid( "OverrideVolumeBox", "CheckBoxControl", False, "Audio Volume", 6, 0, "Audio volume override.", False )
    scriptDialog.AddRangeControlToGrid( "VolumeBox", "RangeControl", 1.00, -99999, 99999, 2, 1, 6, 1 )
    OverrideUnCropBox = scriptDialog.AddSelectionControlToGrid( "OverrideUnCropBox", "CheckBoxControl", False, "Un-Crop (W H X Y)", 6, 2, "Inset image into larger virtual image.", False )
    scriptDialog.AddRangeControlToGrid( "UnCropWBox", "RangeControl", 0, -99999, 99999, 0, 1, 6, 3 )
    scriptDialog.AddRangeControlToGrid( "UnCropHBox", "RangeControl", 0, -99999, 99999, 0, 1, 6, 4 )
    scriptDialog.AddRangeControlToGrid( "UnCropXBox", "RangeControl", 0, -99999, 99999, 0, 1, 6, 5 )
    scriptDialog.AddRangeControlToGrid( "UnCropYBox", "RangeControl", 0, -99999, 99999, 0, 1, 6, 6 )
    scriptDialog.EndGrid()
    
    OverrideAspectRatioBox.ValueModified.connect(OverrideAspectRatioPressed)
    OverrideFileLutBox.ValueModified.connect(OverrideFileLutPressed)
    OverrideRangeOffsetBox.ValueModified.connect(OverrideRangeOffsetPressed)
    OverrideLookLutBox.ValueModified.connect(OverrideLookLutPressed)
    OverrideFPSBox.ValueModified.connect(OverrideFPSPressed)
    OverridePreCacheLutBox.ValueModified.connect(OverridePreCacheLutPressed)
    OverrideAudioOffsetBox.ValueModified.connect(OverrideAudioOffsetPressed)
    OverrideChannelsBox.ValueModified.connect(OverrideChannelsPressed)
    OverrideStereoOffsetBox.ValueModified.connect(OverrideStereoOffsetPressed)
    OverrideCropBox.ValueModified.connect(OverrideCropPressed)
    OverrideVolumeBox.ValueModified.connect(OverrideVolumePressed)
    OverrideUnCropBox.ValueModified.connect(OverrideUnCropPressed)
    
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage( "Options" )
    
    scriptDialog.AddGrid()
    scriptDialog.AddSelectionControlToGrid( "ConvertLogBox", "CheckBoxControl", False, "Convert Input To Linear Space Via Cineon Log->Lin", 0, 0, "Convert input to linear space via Cineon Log->Lin ", colSpan=2 )
    OverrideGammaBox = scriptDialog.AddSelectionControlToGrid( "OverrideGammaBox", "CheckBoxControl", False, "Convert Input Using Gamma Correction To Linear Space", 0, 2, "Convert input using gamma correction to linear space ", colSpan=2 )
    scriptDialog.AddRangeControlToGrid( "GammaBox", "RangeControl", 1.8, 0.0, 5.0, 1, 0.2, 0, 4 )

    scriptDialog.AddSelectionControlToGrid( "ConvertSRGBBox", "CheckBoxControl", False, "Convert Input To Linear Space From sRGB Space", 1, 0, "Convert input to linear space from sRGB space ", colSpan=2 )
    OverrideExposureBox = scriptDialog.AddSelectionControlToGrid( "OverrideExposureBox", "CheckBoxControl", False, "Apply Relative Exposure Change (In Stops)", 1, 2, "Apply relative exposure change (in stops) ", colSpan=2 )
    scriptDialog.AddRangeControlToGrid( "ExposureBox", "RangeControl", 0.000, -3.000, 3.000, 3, 0.500, 1, 4 )

    scriptDialog.AddSelectionControlToGrid( "Convert709Box", "CheckBoxControl", False, "Convert Input To Linear Space From Rec-709 Space", 2, 0, "Convert input to linear space from Rec-709 space ", colSpan=2 )
    OverrideScaleBox = scriptDialog.AddSelectionControlToGrid( "OverrideScaleBox", "CheckBoxControl", False, "Scale Input Image Geometry", 2, 2, "Scale input image geometry ", colSpan=2 )
    scriptDialog.AddRangeControlToGrid( "ScaleBox", "RangeControl", 1.00, 0.01, 10.00, 2, 0.25, 2, 4 )

    scriptDialog.AddSelectionControlToGrid( "PremultiplyBox", "CheckBoxControl", False, "Premultiply Input Alpha and Color", 3, 0, "Premultiply alpha and color ", False )
    ResizeInputBox = scriptDialog.AddSelectionControlToGrid( "ResizeInputBox", "CheckBoxControl", False, "Resize Input Image Geometry To Exact Size On Input", 3, 2, "Resize input image geometry to exact size on input (0 = maintain image aspect) ", colSpan=2 )
    scriptDialog.AddRangeControlToGrid( "ResizeInputWidthBox", "RangeControl", 640, 1, 99999, 0, 1, 3, 4 )
    scriptDialog.AddRangeControlToGrid( "ResizeInputHeightBox", "RangeControl", 480, 0, 99999, 0, 1, 3, 5 )

    scriptDialog.AddSelectionControlToGrid( "UnpremultiplyBox", "CheckBoxControl", False, "Un-premultiply Input Alpha and Color", 4, 0, "Un-premultiply alpha and color ", colSpan=2 )
    OverrideResampleBox = scriptDialog.AddSelectionControlToGrid( "OverrideResampleBox", "CheckBoxControl", False, "Resample Method", 4, 2, "Resampling method", False)
    scriptDialog.AddHorizontalSpacerToGrid("OptionsHSpacer2", 4, 3 )
    scriptDialog.AddComboControlToGrid( "ResampleBox", "ComboControl", "area", ("area", "linear", "cubic", "nearest"), 4, 4, colSpan=2 )

    scriptDialog.AddSelectionControlToGrid( "FlipBox", "CheckBoxControl", False, "Flip Image (Vertical)", 5, 0, "Flip image (flip vertical) (keep orientation flags the same) ", False )
    scriptDialog.AddHorizontalSpacerToGrid("OptionsHSpacer2", 5, 1 )
    OverrideThreadsBox = scriptDialog.AddSelectionControlToGrid( "OverrideThreadsBox", "CheckBoxControl", False, "Number Of Reader/Render Threads", 5, 2, "Number of reader/render threads", colSpan=2 )
    scriptDialog.AddRangeControlToGrid( "ThreadsBox", "RangeControl", 1, 1, 16, 0, 1, 5, 4 )

    scriptDialog.AddSelectionControlToGrid( "FlopBox", "CheckBoxControl", False, "Flop Image (Horizontal)", 6, 0, "Flop image (flip horizontal) (keep orientation flags the same) ", False )
    OverrideLeaderFramesBox = scriptDialog.AddSelectionControlToGrid( "OverrideLeaderFramesBox", "CheckBoxControl", False, "Number Of Leader Frames", 6, 2, "Number of leader frames", False )
    scriptDialog.AddRangeControlToGrid( "LeaderFramesBox", "RangeControl", 1, 1, 99999, 0, 1, 6, 4 )

    scriptDialog.AddSelectionControlToGrid( "QualityBox", "CheckBoxControl", False, "Best Quality Color Conversions", 7, 0, "Best quality for color conversions (slower  mostly unnecessary) ", colSpan=2 )
    MapInputChannelsBox = scriptDialog.AddSelectionControlToGrid( "MapInputChannelsBox", "CheckBoxControl", False, "Map Input Channels", 7, 2, "Map input channels ", False )
    scriptDialog.AddControlToGrid( "InputChannelsBox", "TextControl", "R G B", 7, 3, colSpan=3 )

    scriptDialog.AddSelectionControlToGrid( "NoPrerenderBox", "CheckBoxControl", False, "Turn Off Prerendering Optimization", 8, 0, "Turn off prerendering optimization ", colSpan=2 )
    OverrideFlagsBox = scriptDialog.AddSelectionControlToGrid( "OverrideFlagsBox", "CheckBoxControl", False, "Arbitrary Flags For Mu", 8, 2, "Arbitrary flags (flag, or name=value) for Mu ", False )
    scriptDialog.AddControlToGrid( "FlagsBox", "TextControl", "", 8, 3, colSpan=3 )

    OverrideInitScriptBox = scriptDialog.AddSelectionControlToGrid( "OverrideInitScriptBox", "CheckBoxControl", False, "Init Script", 9, 0, "Override init script ", False )
    scriptDialog.AddControlToGrid( "InitScriptBox", "TextControl", "", 9, 1, colSpan=5 )

    InsertLeaderBox = scriptDialog.AddSelectionControlToGrid( "InsertLeaderBox", "CheckBoxControl", False, "Insert Leader/Slate", 10, 0, "Insert leader/slate", False )
    scriptDialog.AddControlToGrid( "LeaderBox", "TextControl", "", 10, 1, colSpan=5 )

    InsertOverlayBox = scriptDialog.AddSelectionControlToGrid( "InsertOverlayBox", "CheckBoxControl", False, "Visual Overlay", 11, 0, "Visual overlay", False )
    scriptDialog.AddControlToGrid( "OverlayBox", "TextControl", "", 11, 1, colSpan=5 )

    scriptDialog.AddControlToGrid( "CommandLineLabel", "LabelControl", "Additional Command Line Options", 12, 0, "Additional commnad line options.", colSpan=6 )
    scriptDialog.AddControlToGrid( "CommandLineBox", "TextControl", "", 13, 0, colSpan=6 )
    scriptDialog.EndGrid()
        
    OverrideGammaBox.ValueModified.connect(OverrideGammaBoxPressed)
    OverrideExposureBox.ValueModified.connect(OverrideExposureBoxPressed)
    OverrideScaleBox.ValueModified.connect(OverrideScaleBoxPressed)
    ResizeInputBox.ValueModified.connect(ResizeInputBoxPressed)
    OverrideResampleBox.ValueModified.connect(OverrideResampleBoxPressed)
    OverrideThreadsBox.ValueModified.connect(OverrideThreadsBoxPressed)
    OverrideLeaderFramesBox.ValueModified.connect(OverrideLeaderFramesBoxPressed)
    MapInputChannelsBox.ValueModified.connect(MapInputChannelsBoxPressed)
    OverrideFlagsBox.ValueModified.connect(OverrideFlagsBoxPressed)
    OverrideInitScriptBox.ValueModified.connect(OverrideInitScriptBoxPressed)
    InsertLeaderBox.ValueModified.connect(InsertLeaderBoxPressed)
    InsertOverlayBox.ValueModified.connect(InsertOverlayBoxPressed)

    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage( "Output" )
    buffer = 12
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "OutputFileLabel", "LabelControl", "Output File (Required)", 0, 0, "The output file name (required).", False )
    OutputFileBox = scriptDialog.AddSelectionControlToGrid( "OutputFileBox", "FileSaverControl", "", "All Files (*)", 0, 1, colSpan=6 )

    ApplyDisplayLutBox = scriptDialog.AddSelectionControlToGrid( "ApplyDisplayLutBox", "CheckBoxControl", False, "Display LUT", 1, 0, "Apply display LUT ", False )
    scriptDialog.AddSelectionControlToGrid( "DisplayLutBox", "FileBrowserControl", "", "All Files (*)", 1, 1, colSpan=6 )

    scriptDialog.AddSelectionControlToGrid( "ConvertOutputLogBox", "CheckBoxControl", False, "Convert Output To Log Space Via Cineon Lin->Log", 2, 0, "Convert output to log space via Cineon Lin->Log ", colSpan=2 )
    OverrideOutputFPSBox = scriptDialog.AddSelectionControlToGrid( "OverrideOutputFPSBox", "CheckBoxControl", False, "Frames Per Second", 2, 2, "Output frames per second", False )
    scriptDialog.AddRangeControlToGrid( "OutputFPSBox", "RangeControl", 24.00, 0, 99999, 2, 1, 2, 3 )
    OverrideResolutionBox = scriptDialog.AddSelectionControlToGrid( "OverrideResolutionBox", "CheckBoxControl", False, "Output Resolution", 2, 4, "Output resolution (image will be fit, not stretched) ", False )
    scriptDialog.AddRangeControlToGrid( "ResolutionWidthBox", "RangeControl", 640, 1, 99999, 0, 1, 2, 5 )
    scriptDialog.AddRangeControlToGrid( "ResolutionHeightBox", "RangeControl", 480, 1, 99999, 0, 1, 2, 6 )

    scriptDialog.AddSelectionControlToGrid( "ConvertOutputSRGBBox", "CheckBoxControl", False, "Convert Output To sRGB ColorSpace", 3, 0, "Convert output to sRGB ColorSpace ", colSpan=2 )
    OverrideOutputGammaBox = scriptDialog.AddSelectionControlToGrid( "OverrideOutputGammaBox", "CheckBoxControl", False, "Apply Gamma To Output", 3, 2, "Apply gamma to output ", False )
    scriptDialog.AddRangeControlToGrid( "OutputGammaBox", "RangeControl", 1.8, 0.0, 5.0, 1, 0.2, 3, 3 )
    OverrideOutputFormatBox = scriptDialog.AddSelectionControlToGrid( "OverrideOutputFormatBox", "CheckBoxControl", False, "Output Bits and Format", 3, 4, "Output bits and format", False )
    scriptDialog.AddComboControlToGrid( "OutputFormatBitsBox", "ComboControl", "16", ("8", "16", "32"), 3, 5 )
    scriptDialog.AddComboControlToGrid( "OutputFormatBox", "ComboControl", "float", ("float","int"), 3, 6 )

    scriptDialog.AddSelectionControlToGrid( "ConvertOutput709Box", "CheckBoxControl", False, "Convert Output To Rec-709 ColorSpace", 4, 0, "Convert output to Rec-709 ColorSpace ", colSpan=2 )
    OutputCodecBox = scriptDialog.AddSelectionControlToGrid( "OutputCodecBox", "CheckBoxControl", False, "Output Codec", 4, 2, "Type the codec code in the text box, or use the drop down to select from a list of known codecs", False )
    CodecComboBox = scriptDialog.AddComboControlToGrid( "CodecComboBox", "ComboControl", "", ("",), 4, 3, colSpan=3 )
    scriptDialog.AddControlToGrid( "CodecBox", "TextControl", "", 4, 6 )

    scriptDialog.AddSelectionControlToGrid( "PremultiplyOutputBox", "CheckBoxControl", False, "Premultiply Output Alpha and Color", 5, 0, "Premultiply alpha and color ", colSpan=2 )
    OverrideCodecQualityBox = scriptDialog.AddSelectionControlToGrid( "OverrideCodecQualityBox", "CheckBoxControl", False, "Output Codec Quality", 5, 2, "Output codec quality 0.0 -> 1.0 (use varies with file format and codec default=0.900000) ", False )
    scriptDialog.AddRangeControlToGrid( "CodecQualityBox", "RangeControl", 0.9, 0.0, 1.0, 1, 0.1, 5, 3 )

    scriptDialog.AddSelectionControlToGrid( "UnPremultiplyOutputBox", "CheckBoxControl", False, "Un-premultiply Output Alpha and Color", 6, 0, "Un-premultiply alpha and color ", colSpan=2 )
    OverrideKeyIntervalBox = scriptDialog.AddSelectionControlToGrid( "OverrideKeyIntervalBox", "CheckBoxControl", False, "Video Key Interval", 6, 2, "Output video key interval (H.264 and similar) ", False )
    scriptDialog.AddRangeControlToGrid( "KeyIntervalBox", "RangeControl", 1, 0, 99999, 0, 1, 6, 3 )
    OverrideDataRateBox = scriptDialog.AddSelectionControlToGrid( "OverrideDataRateBox", "CheckBoxControl", False, "Max Video Data Rate", 6, 4, "Maximum output video data rate (H.264 and similar) ", False )
    scriptDialog.AddRangeControlToGrid( "DataRateBox", "RangeControl", 1, 0, 99999, 0, 1, 6, 5 )

    scriptDialog.AddSelectionControlToGrid( "OutputStereoBox", "CheckBoxControl", False, "Output Stereo Image Pairs if Possible", 7, 0, "Output stereo", colSpan=2 )
    OverrideOutputChannelMapBox = scriptDialog.AddSelectionControlToGrid( "OverrideOutputChannelMapBox", "CheckBoxControl", False, "Map Output Channels", 7, 2, "Map output channels ", False )
    scriptDialog.AddControlToGrid( "OutputChannelMapBox", "TextControl", "R G B", 7, 3, colSpan=4 )

    scriptDialog.AddSelectionControlToGrid( "OutputRVTimeRangeBox", "CheckBoxControl", False, "Output Time Range From .rv File's In/Out Points", 8, 0, "Output time range from rv session files in/out points ", colSpan=2 )
    OverrideOutputTimeRangeBox = scriptDialog.AddSelectionControlToGrid( "OverrideOutputTimeRangeBox", "CheckBoxControl", False, "Output Time Range", 8, 2, "Output time range (default=input time range) ", False )
    scriptDialog.AddControlToGrid( "OutputTimeRangeBox", "TextControl", "", 8, 3, colSpan=4 )

    OverrideOutputCommentBox = scriptDialog.AddSelectionControlToGrid( "OverrideOutputCommentBox", "CheckBoxControl", False, "Output Comment (Movie Files)", 9, 0, "Output comment (movie files, default="") ", False )
    scriptDialog.AddHorizontalSpacerToGrid("OutputHSpacer1", 9, 1 )
    scriptDialog.AddControlToGrid( "OutputCommentBox", "TextControl", "", 9, 2, colSpan=5 )

    OverrideOutputCopyrightBox = scriptDialog.AddSelectionControlToGrid( "OverrideOutputCopyrightBox", "CheckBoxControl", False, "Output Copyright (Movie Files)", 10, 0, "Output copyright (movie files, default="") ", False )
    scriptDialog.AddControlToGrid( "OutputCopyrightBox", "TextControl", "", 10, 2, colSpan=5 )

    OverrideAudioCodecBox = scriptDialog.AddSelectionControlToGrid( "OverrideAudioCodecBox", "CheckBoxControl", False, "Audio Codec", 11, 2, "Type the codec code in the text box, or use the drop down to select from a list of known codecs", False )
    AudioCodecComboBox = scriptDialog.AddComboControlToGrid( "AudioCodecComboBox", "ComboControl", "", ("",), 11, 3, colSpan=3 )
    scriptDialog.AddControlToGrid( "AudioCodecBox", "TextControl", "", 11, 6 )

    OverrideAudioRateBox = scriptDialog.AddSelectionControlToGrid( "OverrideAudioRateBox", "CheckBoxControl", False, "Audio Sample Rate", 12, 2, "Output audio sample rate (default from input) ", False )
    scriptDialog.AddRangeControlToGrid( "AudioRateBox", "RangeControl", 22050, 1, 99999, 0, 1, 12, 3 )
    OverrideAudioFormatBox = scriptDialog.AddSelectionControlToGrid( "OverrideAudioFormatBox", "CheckBoxControl", False, "Audio Bits and Format", 12, 4, "Output audio bits (8, 16, 32) and type (int, float) ", False )
    scriptDialog.AddComboControlToGrid( "AudioFormatBitsBox", "ComboControl", "16", ("8", "16", "32"), 12, 5 )
    scriptDialog.AddComboControlToGrid( "AudioFormatBox", "ComboControl", "float", ("float","int"), 12, 6 )

    OverrideAudioQualityBox = scriptDialog.AddSelectionControlToGrid( "OverrideAudioQualityBox", "CheckBoxControl", False, "Audio Quality", 13, 2, "Output audio quality (for lossy compression codecs) [0, 1] default = 0.500000 ", False )
    scriptDialog.AddRangeControlToGrid( "AudioQualityBox", "RangeControl", 0.5, 0.0, 1.0, 1, 0.1, 13, 3 )
    OverrideAudioChannelsBox = scriptDialog.AddSelectionControlToGrid( "OverrideAudioChannelsBox", "CheckBoxControl", False, "Audio Channels", 13, 4, "Output audio channels (default from input) ", False )
    scriptDialog.AddRangeControlToGrid( "AudioChannelsBox", "RangeControl", 2, 1, 99999, 0, 1, 13, 5 )
    scriptDialog.EndGrid()
    #~ scriptDialog.AddRow()
    #~ scriptDialog.AddSelectionControl( "ExrNoOneChannelBox", "CheckBoxControl", False, "EXR Never Use One Channel Planar Images", controlWidth + controlWidth, -1, "EXR never use one channel planar images (default=false) " )
    #~ scriptDialog.AddSelectionControl( "ExrInheritBox", "CheckBoxControl", False, "EXR Guess Channel Inheritance", labelWidth + buffer + 56, -1, "EXR guess channel inheritance (default=false) " )
    #~ OverrideExrCPUsBox = scriptDialog.AddSelectionControl( "OverrideExrCPUsBox", "CheckBoxControl", False, "EXR Thread Count", labelWidth + buffer, -1, "EXR thread count (default=platform dependant) " )
    #~ scriptDialog.AddRangeControl( "ExrCPUsBox", "RangeControl", 1, 1, 16, 0, 1, 50, -1 )
    #~ scriptDialog.EndRow()
    #~ scriptDialog.AddRow()
    #~ OverrideCinPixelBox = scriptDialog.AddSelectionControl( "OverrideCinPixelBox", "CheckBoxControl", False, "Cineon/DPX Format", labelWidth, -1, "Cineon/DPX pixel format (default=RGB16) " )
    #~ scriptDialog.AddControl( "CinPixelBox", "TextControl", "RGB16", controlWidth + 16, -1 )
    #~ scriptDialog.EndRow()
    
    OutputFileBox.ValueModified.connect(OutputFileBoxChanged)
    OverrideOutputFPSBox.ValueModified.connect(OverrideOutputFPSBoxPressed)
    OverrideResolutionBox.ValueModified.connect(OverrideResolutionBoxPressed)
    OverrideOutputGammaBox.ValueModified.connect(OverrideOutputGammaBoxPressed)
    OverrideOutputFormatBox.ValueModified.connect(OverrideOutputFormatBoxPressed)
    OverrideCodecQualityBox.ValueModified.connect(OverrideCodecQualityBoxPressed)
    OutputCodecBox.ValueModified.connect(OutputCodecBoxPressed)
    CodecComboBox.ValueModified.connect(CodecComboBoxChanged)
    OverrideKeyIntervalBox.ValueModified.connect(OverrideKeyIntervalBoxPressed)
    OverrideDataRateBox.ValueModified.connect(OverrideDataRateBoxPressed)
    ApplyDisplayLutBox.ValueModified.connect(ApplyDisplayLutBoxPressed)
    OverrideOutputChannelMapBox.ValueModified.connect(OverrideOutputChannelMapBoxPressed)
    OverrideOutputTimeRangeBox.ValueModified.connect(OverrideOutputTimeRangeBoxPressed)
    OverrideOutputCommentBox.ValueModified.connect(OverrideOutputCommentBoxPressed)
    OverrideOutputCopyrightBox.ValueModified.connect(OverrideOutputCopyrightBoxPressed)
    OverrideAudioCodecBox.ValueModified.connect(OverrideAudioCodecBoxPressed)
    AudioCodecComboBox.ValueModified.connect(AudioCodecComboBoxChanged)
    OverrideAudioRateBox.ValueModified.connect(OverrideAudioRateBoxPressed)
    OverrideAudioFormatBox.ValueModified.connect(OverrideAudioFormatBoxPressed)
    OverrideAudioQualityBox.ValueModified.connect(OverrideAudioQualityBoxPressed)
    OverrideAudioChannelsBox.ValueModified.connect(OverrideAudioChannelsBoxPressed)
    #OverrideExrCPUsBox.ValueModified.connect(OverrideExrCPUsBoxPressed)
    #OverrideCinPixelBox.ValueModified.connect(OverrideCinPixelBoxPressed)

    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "RVIOMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(CloseButtonPressed)
    scriptDialog.EndGrid()
    
    settingsList = []
    settingsList.append("DepartmentBox")
    settingsList.append("PoolBox")
    settingsList.append("SecondaryPoolBox")
    settingsList.append("IsBlacklistBox")
    settingsList.append("GroupBox")
    settingsList.append("MachineListBox")
    settingsList.append("PriorityBox")
    settingsList.append("LimitGroupBox")
    settingsList.append("BuildBox")
    settingsList.append("SubmitSuspendedBox")
    settingsList.append("ConvertLogBox")
    settingsList.append("OverrideGammaBox")
    settingsList.append("GammaBox")
    settingsList.append("ConvertSRGBBox")
    settingsList.append("OverrideExposureBox")
    settingsList.append("ExposureBox")
    settingsList.append("Convert709Box")
    settingsList.append("OverrideScaleBox")
    settingsList.append("ScaleBox")
    settingsList.append("PremultiplyBox")
    settingsList.append("ResizeInputBox")
    settingsList.append("ResizeInputWidthBox")
    settingsList.append("ResizeInputHeightBox")
    settingsList.append("UnpremultiplyBox")
    settingsList.append("OverrideResampleBox")
    settingsList.append("ResampleBox")
    settingsList.append("FlipBox")
    settingsList.append("OverrideThreadsBox")
    settingsList.append("ThreadsBox")
    settingsList.append("FlopBox")
    settingsList.append("OverrideLeaderFramesBox")
    settingsList.append("LeaderFramesBox")
    settingsList.append("QualityBox")
    settingsList.append("MapInputChannelsBox")
    settingsList.append("InputChannelsBox")
    settingsList.append("NoPrerenderBox")
    settingsList.append("OverrideFlagsBox")
    settingsList.append("FlagsBox")
    settingsList.append("OverrideInitScriptBox")
    settingsList.append("InitScriptBox")
    settingsList.append("InsertLeaderBox")
    settingsList.append("LeaderBox")
    settingsList.append("InsertOverlayBox")
    settingsList.append("OverlayBox")
    settingsList.append("CommandLineBox")
    settingsList.append("OutputFileBox")
    settingsList.append("ConvertOutputLogBox")
    settingsList.append("OverrideOutputFPSBox")
    settingsList.append("OutputFPSBox")
    settingsList.append("OverrideResolutionBox")
    settingsList.append("ResolutionWidthBox")
    settingsList.append("ResolutionHeightBox")
    settingsList.append("ConvertOutputSRGBBox")
    settingsList.append("OverrideOutputGammaBox")
    settingsList.append("OutputGammaBox")
    settingsList.append("OverrideOutputFormatBox")
    settingsList.append("OutputFormatBitsBox")
    settingsList.append("OutputFormatBox")
    settingsList.append("ConvertOutput709Box")
    settingsList.append("OverrideCodecQualityBox")
    settingsList.append("CodecQualityBox")
    settingsList.append("OutputCodecBox")
    settingsList.append("CodecBox")
    settingsList.append("PremultiplyOutputBox")
    settingsList.append("OverrideKeyIntervalBox")
    settingsList.append("KeyIntervalBox")
    settingsList.append("OverrideDataRateBox")
    settingsList.append("DataRateBox")
    settingsList.append("UnPremultiplyOutputBox")
    settingsList.append("ApplyDisplayLutBox")
    settingsList.append("DisplayLutBox")
    settingsList.append("OutputStereoBox")
    settingsList.append("OverrideOutputChannelMapBox")
    settingsList.append("OutputChannelMapBox")
    settingsList.append("OutputRVTimeRangeBox")
    settingsList.append("OverrideOutputTimeRangeBox")
    settingsList.append("OutputTimeRangeBox")
    settingsList.append("OverrideOutputCommentBox")
    settingsList.append("OutputCommentBox")
    settingsList.append("OverrideOutputCopyrightBox")
    settingsList.append("OutputCopyrightBox")
    settingsList.append("OverrideAudioCodecBox")
    settingsList.append("AudioCodecBox")
    settingsList.append("OverrideAudioRateBox")
    settingsList.append("AudioRateBox")
    settingsList.append("OverrideAudioFormatBox")
    settingsList.append("AudioFormatBitsBox")
    settingsList.append("AudioFormatBox")
    settingsList.append("OverrideAudioQualityBox")
    settingsList.append("AudioQualityBox")
    settingsList.append("OverrideAudioChannelsBox")
    settingsList.append("AudioChannelsBox")
    #settingsList.append("ExrNoOneChannelBox")
    #settingsList.append("ExrInheritBox")
    #settingsList.append("OverrideExrCPUsBox")
    #settingsList.append("ExrCPUsBox")
    #settingsList.append("OverrideCinPixelBox")
    #settingsList.append("CinPixelBox")
    
    settings = tuple(settingsList)
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    
    InitializeCodecs()
    
    if len( args ) > 0:
        filename = args[0]
        
        defaultSourceName = "Default"
        defaultSource = Source( defaultSourceName )
        AddSource( defaultSourceName, defaultSource )
        
        scriptDialog.SetValue( "SourceBox", defaultSourceName )
        scriptDialog.SetValue( "SourceInput1Box", filename )
        Input1Changed()
        
        try:
            if filename != "":
                outputFilename = ""
                
                paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
                if paddingSize > 0:
                    outputFilename = Path.ChangeExtension( FrameUtils.GetFilenameWithoutPadding( filename ), ".mov" )
                else:
                    outputFilename = Path.ChangeExtension( filename, ".mov" )
                
                while outputFilename.find( "..mov" ) >= 0:
                    outputFilename = outputFilename.replace( "..mov", ".mov" )
                
                scriptDialog.SetValue( "OutputFileBox", outputFilename )
                scriptDialog.SetValue( "NameBox", Path.GetFileNameWithoutExtension( outputFilename ) )
            
        except Exception as e:
            #if not startup:
            #	scriptDialog.ShowMessageBox( e.Message, "Error Parsing Input Images" )
            pass
    
    SelectedSourceChanged()
    
    OverrideGammaBoxPressed()
    OverrideExposureBoxPressed()
    OverrideScaleBoxPressed()
    ResizeInputBoxPressed()
    OverrideResampleBoxPressed()
    OverrideThreadsBoxPressed()
    OverrideLeaderFramesBoxPressed()
    MapInputChannelsBoxPressed()
    OverrideFlagsBoxPressed()
    OverrideInitScriptBoxPressed()
    InsertLeaderBoxPressed()
    InsertOverlayBoxPressed()
    
    OutputFileBoxChanged()
    OverrideOutputFPSBoxPressed()
    OverrideResolutionBoxPressed()
    OverrideOutputGammaBoxPressed()
    OverrideOutputFormatBoxPressed()
    OverrideCodecQualityBoxPressed()
    OutputCodecBoxPressed()
    OverrideKeyIntervalBoxPressed()
    OverrideDataRateBoxPressed()
    ApplyDisplayLutBoxPressed()
    OverrideOutputChannelMapBoxPressed()
    OverrideOutputTimeRangeBoxPressed()
    OverrideOutputCommentBoxPressed()
    OverrideOutputCopyrightBoxPressed()
    OverrideAudioCodecBoxPressed()
    OverrideAudioRateBoxPressed()
    OverrideAudioFormatBoxPressed()
    OverrideAudioQualityBoxPressed()
    OverrideAudioChannelsBoxPressed()
    #OverrideExrCPUsBoxPressed()
    #OverrideCinPixelBoxPressed()
    
    startup = False
    
    scriptDialog.ShowDialog( len( args ) > 0 )

########################################################################
## Helper Functions
########################################################################
def InitializeCodecs():
    global scriptDialog
    global outputCodecs
    global audioCodecs
    
    try:
        rawCodecContents = GetRawCodecText()
        rawCodecContents = unicodedata.normalize('NFKD', rawCodecContents).encode('ascii','ignore')
        
        codecContents = rawCodecContents.splitlines()
            
        currFormat = ""
        currCodecs = None
        inImageCodecs = False
        currAudioCodecs = None
        inAudioCodecs = False
        
        formatRegex = Regex( "format \"(.*)\"" )
        imageCodecsRegex = Regex( "image codecs:" )
        audioCodecsRegex = Regex( "audio codecs:" )
        codecRegex = Regex( "([^\\(]*) \\(.*" )
        
        for line in codecContents:
            #asciiLine = str(line)
            #currLine = asciiLine.strip()
            currLine = line.strip()
            if currLine == "":
                if currFormat != "" and currCodecs != None:
                    currCodecs.insert( 0, "" )
                    outputCodecs[ currFormat ] = currCodecs
                
                if currFormat != "" and currAudioCodecs != None:
                    currAudioCodecs.insert( 0, "" )
                    audioCodecs[ currFormat ] = currAudioCodecs
                    
                currCodecs = None
                inImageCodecs = False
                currAudioCodecs = None
                inAudioCodecs = False
                
                continue
            
            formatMatch = formatRegex.Match( currLine )
            if formatMatch.Success:
                currFormat = formatMatch.Groups[1].Value.lower()
                continue
            
            imageCodecsMatch = imageCodecsRegex.Match( currLine )
            if imageCodecsMatch.Success:
                inImageCodecs = True
                currCodecs = []
                continue
            
            audioCodecsMatch = audioCodecsRegex.Match( currLine )
            if audioCodecsMatch.Success:
                inAudioCodecs = True
                currAudioCodecs = []
                continue
            
            if currFormat != "":
                codecMatch = codecRegex.Match( currLine )
                if codecMatch.Success and codecMatch.Groups[1].Value.find( " " ) == -1:
                    if inImageCodecs:
                        currCodecs.append( codecMatch.Groups[0].Value )
                    elif inAudioCodecs:
                        currAudioCodecs.append( codecMatch.Groups[0].Value )
                continue
    except Exception as e:
        scriptDialog.ShowMessageBox( e.Message, "Error Initializing Codecs" )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "RVIOSettings.ini" )

def GetSourceDirectory():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "RVIOSources" )

def GetSourceFileName( sourceName ):
    return Path.Combine( GetSourceDirectory(), sourceName + ".ini" )

def IsNumber( str ):
    try:
        dummy = int(str)
        return True
    except:
        return False

def OnlyAlphaNumericAndSpacesAndUnderScores( value ):
    for c in value:
        if not c.isalnum() and c != " " and c != "_":
            return False
    return True

def StringToBool( str ):
    return str.lower() in ["true", "1"]

def SourceExists( newSource ):
    global scriptDialog
    
    for source in scriptDialog.GetItems( "SourceBox" ):
        if newSource.lower() == source.lower():
            return True
    return False

def AddSource( newSourceName, newSource ):
    global scriptDialog
    global sourceDictionary
    
    sourceDictionary[ newSourceName ] = newSource
    
    sources = []
    for source in scriptDialog.GetItems( "SourceBox" ):
        sources.append( source )
    sources.append( newSourceName )
    sources.sort()
    
    scriptDialog.SetItems( "SourceBox", tuple(sources) )

def RemoveSource( oldSource ):
    global scriptDialog
    global sourceDictionary
    
    if oldSource in sourceDictionary:
        del sourceDictionary[ oldSource ]
        
    sources = []
    for source in scriptDialog.GetItems( "SourceBox" ):
        if oldSource.lower() != source.lower():
            sources.append( source )
    sources.sort()
    
    scriptDialog.SetItems( "SourceBox", tuple(sources) )

def ClearSources():
    global scriptDialog
    global sourceDictionary
    
    sourceDictionary.clear()
    scriptDialog.SetItems( "SourceBox", () )

def SetSourceFilesEnabled():
    global currSelectedSource
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "SourceInput1Label", sourceSelected )
    scriptDialog.SetEnabled( "SourceInput1Box", sourceSelected )
    scriptDialog.SetEnabled( "SourceStart1Box", sourceSelected )
    scriptDialog.SetEnabled( "SourceRange1Label", sourceSelected )
    scriptDialog.SetEnabled( "SourceEnd1Box", sourceSelected )
    scriptDialog.SetEnabled( "SourceInput2Label", sourceSelected )
    scriptDialog.SetEnabled( "SourceInput2Box", sourceSelected )
    scriptDialog.SetEnabled( "SourceStart2Box", sourceSelected )
    scriptDialog.SetEnabled( "SourceRange2Label", sourceSelected )
    scriptDialog.SetEnabled( "SourceEnd2Box", sourceSelected )
    scriptDialog.SetEnabled( "SourceAudioLabel", sourceSelected )
    scriptDialog.SetEnabled( "SourceAudioBox", sourceSelected )
    scriptDialog.SetEnabled( "NoMovieAudioBox", sourceSelected )

def SetOverrideSeparatorEnabled():
    global currSelectedSource
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverridesSeparator", sourceSelected )

def SetPixelAspectRatioEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideAspectRatioBox", sourceSelected )
    scriptDialog.SetEnabled( "AspectRatioBox", sourceSelected and scriptDialog.GetValue( "OverrideAspectRatioBox" ) )

def SetFileLutEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideFileLutBox", sourceSelected )
    scriptDialog.SetEnabled( "FileLutBox", sourceSelected and scriptDialog.GetValue( "OverrideFileLutBox" ) )

def SetRangeOffsetEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideRangeOffsetBox", sourceSelected )
    scriptDialog.SetEnabled( "RangeOffsetBox", sourceSelected and scriptDialog.GetValue( "OverrideRangeOffsetBox" ) )

def SetLookLutEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideLookLutBox", sourceSelected )
    scriptDialog.SetEnabled( "LookLutBox", sourceSelected and scriptDialog.GetValue( "OverrideLookLutBox" ) )

def SetFPSEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideFPSBox", sourceSelected )
    scriptDialog.SetEnabled( "FPSBox", sourceSelected and scriptDialog.GetValue( "OverrideFPSBox" ) )

def SetPreCacheLutEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverridePreCacheLutBox", sourceSelected )
    scriptDialog.SetEnabled( "PreCacheLutBox", sourceSelected and scriptDialog.GetValue( "OverridePreCacheLutBox" ) )

def SetAudioOffsetEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideAudioOffsetBox", sourceSelected )
    scriptDialog.SetEnabled( "AudioOffsetBox", sourceSelected and scriptDialog.GetValue( "OverrideAudioOffsetBox" ) )

def SetChannelsEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideChannelsBox", sourceSelected )
    scriptDialog.SetEnabled( "ChannelsBox", sourceSelected and scriptDialog.GetValue( "OverrideChannelsBox" ) )

def SetStereoOffsetEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideStereoOffsetBox", sourceSelected )
    scriptDialog.SetEnabled( "StereoOffsetBox", sourceSelected and scriptDialog.GetValue( "OverrideStereoOffsetBox" ) )

def SetCropEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideCropBox", sourceSelected )
    
    overrideEnabled = sourceSelected and scriptDialog.GetValue( "OverrideCropBox" )
    scriptDialog.SetEnabled( "CropX0Box", overrideEnabled )
    scriptDialog.SetEnabled( "CropY0Box", overrideEnabled )
    scriptDialog.SetEnabled( "CropX1Box", overrideEnabled )
    scriptDialog.SetEnabled( "CropY1Box", overrideEnabled )

def SetVolumeEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideVolumeBox", sourceSelected )
    scriptDialog.SetEnabled( "VolumeBox", sourceSelected and scriptDialog.GetValue( "OverrideVolumeBox" ) )

def SetUnCropEnabled():
    global scriptDialog
    global currSelectedSource
    
    sourceSelected = (currSelectedSource != "" and currSelectedSource != "0")
    scriptDialog.SetEnabled( "OverrideUnCropBox", sourceSelected )
    
    overrideEnabled = sourceSelected and scriptDialog.GetValue( "OverrideUnCropBox" )
    scriptDialog.SetEnabled( "UnCropWBox", overrideEnabled )
    scriptDialog.SetEnabled( "UnCropHBox", overrideEnabled )
    scriptDialog.SetEnabled( "UnCropXBox", overrideEnabled )
    scriptDialog.SetEnabled( "UnCropYBox", overrideEnabled )

def UpdateSourceFromUI( source ):
    global scriptDialog
    
    source.Input1 = scriptDialog.GetValue( "SourceInput1Box" ).strip()
    source.Input1StartFrame = scriptDialog.GetValue( "SourceStart1Box" )
    source.Input1EndFrame = scriptDialog.GetValue( "SourceEnd1Box" )
    
    source.Input2 = scriptDialog.GetValue( "SourceInput2Box" ).strip()
    source.Input2StartFrame = scriptDialog.GetValue( "SourceStart2Box" )
    source.Input2EndFrame = scriptDialog.GetValue( "SourceEnd2Box" )
    
    source.AudioFiles = scriptDialog.GetValue( "SourceAudioBox" ).strip()
    source.DisableAudio = scriptDialog.GetValue( "NoMovieAudioBox" )
    
    source.OverridePixelAspectRatio = scriptDialog.GetValue( "OverrideAspectRatioBox" )
    source.PixelAspectRatio = scriptDialog.GetValue( "AspectRatioBox" )
    
    source.OverrideFileLut = scriptDialog.GetValue( "OverrideFileLutBox" )
    source.FileLut = scriptDialog.GetValue( "FileLutBox" ).strip()
    
    source.OverrideRangeOffset = scriptDialog.GetValue( "OverrideRangeOffsetBox" )
    source.RangeOffset = scriptDialog.GetValue( "RangeOffsetBox" )
    
    source.OverrideLookLut = scriptDialog.GetValue( "OverrideLookLutBox" )
    source.LookLut = scriptDialog.GetValue( "LookLutBox" ).strip()
    
    source.OverrideFPS = scriptDialog.GetValue( "OverrideFPSBox" )
    source.FPS = scriptDialog.GetValue( "FPSBox" )
    
    source.OverridePreCacheLut = scriptDialog.GetValue( "OverridePreCacheLutBox" )
    source.PreCacheLut = scriptDialog.GetValue( "PreCacheLutBox" ).strip()
    
    source.OverrideAudioOffset = scriptDialog.GetValue( "OverrideAudioOffsetBox" )
    source.AudioOffset = scriptDialog.GetValue( "AudioOffsetBox" )
    
    source.OverrideChannels = scriptDialog.GetValue( "OverrideChannelsBox" )
    source.Channels = scriptDialog.GetValue( "ChannelsBox" ).strip()
    
    source.OverrideStereoOffset = scriptDialog.GetValue( "OverrideStereoOffsetBox" )
    source.StereoOffset = scriptDialog.GetValue( "StereoOffsetBox" )
    
    source.OverrideCrop = scriptDialog.GetValue( "OverrideCropBox" )
    source.CropX0 = scriptDialog.GetValue( "CropX0Box" )
    source.CropY0 = scriptDialog.GetValue( "CropY0Box" )
    source.CropX1 = scriptDialog.GetValue( "CropX1Box" )
    source.CropY1 = scriptDialog.GetValue( "CropY1Box" )
    
    source.OverrideVolume = scriptDialog.GetValue( "OverrideVolumeBox" )
    source.Volume = scriptDialog.GetValue( "VolumeBox" )
    
    source.OverrideUnCrop = scriptDialog.GetValue( "OverrideUnCropBox" )
    source.UnCropW = scriptDialog.GetValue( "UnCropWBox" )
    source.UnCropH = scriptDialog.GetValue( "UnCropHBox" )
    source.UnCropX = scriptDialog.GetValue( "UnCropXBox" )
    source.UnCropY = scriptDialog.GetValue( "UnCropYBox" )
    
    return source
    
def UpdateUIFromSource( source ):
    global scriptDialog
    
    scriptDialog.SetValue( "SourceInput1Box", source.Input1 )
    scriptDialog.SetValue( "SourceStart1Box", source.Input1StartFrame )
    scriptDialog.SetValue( "SourceEnd1Box", source.Input1EndFrame )
    
    scriptDialog.SetValue( "SourceInput2Box", source.Input2 )
    scriptDialog.SetValue( "SourceStart2Box", source.Input2StartFrame )
    scriptDialog.SetValue( "SourceEnd2Box", source.Input2EndFrame )
    
    scriptDialog.SetValue( "SourceAudioBox", source.AudioFiles )
    scriptDialog.SetValue( "NoMovieAudioBox", source.DisableAudio )
    
    scriptDialog.SetValue( "OverrideAspectRatioBox", source.OverridePixelAspectRatio )
    scriptDialog.SetValue( "AspectRatioBox", source.PixelAspectRatio )
    
    scriptDialog.SetValue( "OverrideFileLutBox", source.OverrideFileLut )
    scriptDialog.SetValue( "FileLutBox", source.FileLut )
    
    scriptDialog.SetValue( "OverrideRangeOffsetBox", source.OverrideRangeOffset )
    scriptDialog.SetValue( "RangeOffsetBox", source.RangeOffset )
    
    scriptDialog.SetValue( "OverrideLookLutBox", source.OverrideLookLut )
    scriptDialog.SetValue( "LookLutBox", source.LookLut )
    
    scriptDialog.SetValue( "OverrideFPSBox", source.OverrideFPS )
    scriptDialog.SetValue( "FPSBox", source.FPS )
    
    scriptDialog.SetValue( "OverridePreCacheLutBox", source.OverridePreCacheLut )
    scriptDialog.SetValue( "PreCacheLutBox", source.PreCacheLut )
    
    scriptDialog.SetValue( "OverrideAudioOffsetBox", source.OverrideAudioOffset )
    scriptDialog.SetValue( "AudioOffsetBox", source.AudioOffset )
    
    scriptDialog.SetValue( "OverrideChannelsBox", source.OverrideChannels )
    scriptDialog.SetValue( "ChannelsBox", source.Channels )
    
    scriptDialog.SetValue( "OverrideStereoOffsetBox", source.OverrideStereoOffset )
    scriptDialog.SetValue( "StereoOffsetBox", source.StereoOffset )
    
    scriptDialog.SetValue( "OverrideCropBox", source.OverrideCrop )
    scriptDialog.SetValue( "CropX0Box", source.CropX0 )
    scriptDialog.SetValue( "CropY0Box", source.CropY0 )
    scriptDialog.SetValue( "CropX1Box", source.CropX1 )
    scriptDialog.SetValue( "CropY1Box", source.CropY1 )
    
    scriptDialog.SetValue( "OverrideVolumeBox", source.OverrideVolume )
    scriptDialog.SetValue( "VolumeBox", source.Volume )
    
    scriptDialog.SetValue( "OverrideUnCropBox", source.OverrideUnCrop )
    scriptDialog.SetValue( "UnCropWBox", source.UnCropW )
    scriptDialog.SetValue( "UnCropHBox", source.UnCropH )
    scriptDialog.SetValue( "UnCropXBox", source.UnCropX )
    scriptDialog.SetValue( "UnCropYBox", source.UnCropY )

def CloseDialog():
    global scriptDialog
    global settings
    scriptDialog.SaveSettings( GetSettingsFilename(), settings )
    scriptDialog.CloseDialog()

########################################################################
## Source Dialog Events
########################################################################
def SourceOKPressed( *args ):
    global scriptDialog
    global sourceDialog
    global currSelectedSource
    global sourceDictionary
    
    newSourceName = sourceDialog.GetValue( "SourceNameBox" ).strip()
    if newSourceName == "":
        sourceDialog.ShowMessageBox( "Please specify a name for this layer.", "Error" )
    elif not OnlyAlphaNumericAndSpacesAndUnderScores( newSourceName ):
        sourceDialog.ShowMessageBox( "The layer name can only contain alphanumeric characters, underscores, or spaces.", "Error" )
    elif SourceExists( newSourceName ):
        sourceDialog.ShowMessageBox( "There is already a layer named '" + newSourceName + "' in the source list.", "Error" )
    else:
        title = str(sourceDialog.windowTitle())
        if title == "Specify Name To Uniquely Identify Source":
            AddSource( newSourceName, Source( newSourceName ) )
            scriptDialog.SetValue( "SourceBox", newSourceName )
        else:
            source = sourceDictionary[ currSelectedSource ]
            source.Name = newSourceName
            RemoveSource( currSelectedSource )
            AddSource( newSourceName, source )
            scriptDialog.SetValue( "SourceBox", newSourceName )
        
        SelectedSourceChanged( None )
        sourceDialog.CloseDialog()

def SourceCancelPressed( *args ):
    global sourceDialog
    sourceDialog.CloseDialog()

########################################################################
## Script Dialog Events
########################################################################
def Input1Changed( *args ):
    global scriptDialog
    global startup
    global updatingInput1File
    
    if not updatingInput1File:
        success = False
        
        try:
            filename = scriptDialog.GetValue( "SourceInput1Box" )
            if filename != "":
                startFrame = 0
                endFrame = 0
                
                initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
                paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
                #if initFrame >= 0 and paddingSize > 0:
                if paddingSize > 0:
                    filename = FrameUtils.GetLowerFrameFilename( filename, initFrame, paddingSize )
                    
                    updatingInput1File = True
                    scriptDialog.SetValue( "SourceInput1Box", filename )
                    updatingInput1File = False
                    
                    startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
                    endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
                
                scriptDialog.SetValue( "SourceStart1Box", startFrame )
                scriptDialog.SetValue( "SourceEnd1Box", endFrame )
                
                success = True
            
        except Exception as e:
            if not startup:
                scriptDialog.ShowMessageBox( e.Message, "Error Parsing Source 1 Files" )
        
        if not success:
            scriptDialog.SetValue( "SourceInput1Box", "" )
            scriptDialog.SetValue( "SourceStart1Box", 0 )
            scriptDialog.SetValue( "SourceEnd1Box", 0 )

def Input2Changed( *args ):
    global scriptDialog
    global startup
    global updatingInput2File
    
    if not updatingInput2File:
        success = False
        
        try:
            filename = scriptDialog.GetValue( "SourceInput2Box" )
            if filename != "":
                startFrame = 0
                endFrame = 0
                
                initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
                paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
                #if initFrame >= 0 and paddingSize > 0:
                if paddingSize > 0:
                    filename = FrameUtils.GetLowerFrameFilename( filename, initFrame, paddingSize )
                    
                    updatingInput2File = True
                    scriptDialog.SetValue( "SourceInput2Box", filename )
                    updatingInput2File = False
                    
                    startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
                    endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
                
                scriptDialog.SetValue( "SourceStart2Box", startFrame )
                scriptDialog.SetValue( "SourceEnd2Box", endFrame )
                
                success = True
            
        except Exception as e:
            if not startup:
                scriptDialog.ShowMessageBox( e.Message, "Error Parsing Source 2 Files" )
        
        if not success:
            scriptDialog.SetValue( "SourceInput2Box", "" )
            scriptDialog.SetValue( "SourceStart2Box", 0 )
            scriptDialog.SetValue( "SourceEnd2Box", 0 )

def SelectedSourceChanged( *args ):
    global scriptDialog
    global currSelectedSource
    global sourceDictionary
    
    hasSelection = ( currSelectedSource != "" and currSelectedSource != "0" )
    
    if hasSelection:
        source = None
        if currSelectedSource in sourceDictionary:
            source = sourceDictionary[ currSelectedSource ]
            source = UpdateSourceFromUI( source )
            sourceDictionary[ currSelectedSource ] = source
    
    currSelectedSource = scriptDialog.GetValue( "SourceBox" )
    hasSelection = ( currSelectedSource != "" and currSelectedSource != "0")
    if hasSelection:
        source = None
        if currSelectedSource in sourceDictionary:
            source = sourceDictionary[ currSelectedSource ]
        else:
            source = Source( currSelectedSource )
        
        UpdateUIFromSource( source )
    
    # make sure we have items for SourceBox
    sourceItems = scriptDialog.GetItems( "SourceBox" )
    if sourceItems == None: sourceItems = []
    
    scriptDialog.SetEnabled( "RenameButton", (hasSelection) )
    scriptDialog.SetEnabled( "RemoveButton", (hasSelection) )
    scriptDialog.SetEnabled( "ClearButton", (len(sourceItems) > 0 ) )
    scriptDialog.SetEnabled( "SaveButton", (len(sourceItems) > 0 ) )
    
    SetSourceFilesEnabled()
    SetOverrideSeparatorEnabled()
    SetPixelAspectRatioEnabled()
    SetFileLutEnabled()
    SetRangeOffsetEnabled()
    SetLookLutEnabled()
    SetFPSEnabled()
    SetPreCacheLutEnabled()
    SetAudioOffsetEnabled()
    SetChannelsEnabled()
    SetStereoOffsetEnabled()
    SetCropEnabled()
    SetVolumeEnabled()
    SetUnCropEnabled()
    
def OverrideAspectRatioPressed( *args ):
    SetPixelAspectRatioEnabled()

def OverrideFileLutPressed( *args ):
    SetFileLutEnabled()

def OverrideRangeOffsetPressed( *args ):
    SetRangeOffsetEnabled()

def OverrideLookLutPressed( *args ):
    SetLookLutEnabled()

def OverrideFPSPressed( *args ):
    SetFPSEnabled()

def OverridePreCacheLutPressed( *args ):
    SetPreCacheLutEnabled()

def OverrideAudioOffsetPressed( *args ):
    SetAudioOffsetEnabled()

def OverrideChannelsPressed( *args ):
    SetChannelsEnabled()

def OverrideStereoOffsetPressed( *args ):
    SetStereoOffsetEnabled()

def OverrideCropPressed( *args ):
    SetCropEnabled()

def OverrideVolumePressed( *args ):
    SetVolumeEnabled()

def OverrideUnCropPressed( *args ):
    SetUnCropEnabled()

def AddPressed( *args ):
    global sourceDialog
    
    sourceDialog.SetTitle( "Specify Name To Uniquely Identify Source" )
    sourceDialog.SetValue( "SourceTitleLabel", "Specify Name To Uniquely Identify Source")
    sourceDialog.ShowDialog( False )

def RenamePressed( *args ):
    global sourceDialog
    global currSelectedSource
    
    if currSelectedSource != "" and currSelectedSource != "0" :
        sourceDialog.SetTitle( "Specify New Name To Uniquely Identify Source" )
        sourceDialog.SetValue( "SourceTitleLabel", "Specify Name To Uniquely Identify Source")
        sourceDialog.SetValue( "SourceNameBox", currSelectedSource )
        sourceDialog.ShowDialog( False )
    
    SelectedSourceChanged( None )

def RemovePressed( *args ):
    global currSelectedSource
    
    if currSelectedSource != "" and currSelectedSource != "0":
        result = scriptDialog.ShowMessageBox( "Are you sure you would like to remove " + currSelectedSource + "?", "RVIO Submission", ("Yes","No") )
        if result == "No":
            return
        RemoveSource( currSelectedSource )
        currSelectedSource = ""
    
    SelectedSourceChanged( None )

def ClearPressed( *args ):
    global currSelectedSource
    
    result = scriptDialog.ShowMessageBox( "Are you sure you would like to clear the layers?", "RVIO Submission", ("Yes","No") )
    if result == "No":
        return
    
    ClearSources()
    currSelectedSource = ""
    SelectedSourceChanged( None )

def LoadPressed( *args ):
    global scriptDialog
    global sourceDictionary
    
    sourceDirectory = GetSourceDirectory()
    if not Directory.Exists( sourceDirectory ):
        Directory.CreateDirectory( sourceDirectory )
    
    selectedFiles = scriptDialog.ShowMultiOpenFileBrowser( sourceDirectory, "INI Files (*.ini)" )
    for file in selectedFiles:
        sourceName = Path.GetFileNameWithoutExtension( file )
        source = Source( sourceName )
        source.LoadFromFile( file )
        
        RemoveSource( sourceName )
        AddSource( sourceName, source )
    
    # Ensure that all source objects have been saved.
    SelectedSourceChanged( None )

def SavePressed( *args ):
    global scriptDialog
    global sourceDictionary
    
    sourceDirectory = GetSourceDirectory()
    if not Directory.Exists( sourceDirectory ):
        Directory.CreateDirectory( sourceDirectory )
    
    # Ensure that all source objects have been saved.
    SelectedSourceChanged( None )
    
    warnings = ""
    for sourceName in sourceDictionary:
        sourceFileName = GetSourceFileName( sourceName )
        if File.Exists( sourceFileName ):
            warnings = warnings + Path.GetFileName( sourceFileName ) + "\n"
    
    if warnings != "":
        warnings = "The following layer ini files already exist and will be overwritten.\n\n" + warnings + "\nDo you wish to continue?"
        result = scriptDialog.ShowMessageBox( warnings, "Warning", ("Yes","No") )
        if result == "No":
            return
    
    for sourceName in sourceDictionary:
        source = sourceDictionary[ sourceName ]
        sourceFileName = GetSourceFileName( sourceName )
        source.SaveToFile( sourceFileName )

def OverrideGammaBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "GammaBox", scriptDialog.GetValue( "OverrideGammaBox" ) )

def OverrideExposureBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ExposureBox", scriptDialog.GetValue( "OverrideExposureBox" ) )

def OverrideScaleBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ScaleBox", scriptDialog.GetValue( "OverrideScaleBox" ) )

def ResizeInputBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ResizeInputWidthBox", scriptDialog.GetValue( "ResizeInputBox" ) )
    scriptDialog.SetEnabled( "ResizeInputHeightBox", scriptDialog.GetValue( "ResizeInputBox" ) )

def OverrideResampleBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ResampleBox", scriptDialog.GetValue( "OverrideResampleBox" ) )

def OverrideThreadsBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ThreadsBox", scriptDialog.GetValue( "OverrideThreadsBox" ) )

def OverrideLeaderFramesBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "LeaderFramesBox", scriptDialog.GetValue( "OverrideLeaderFramesBox" ) )

def MapInputChannelsBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "InputChannelsBox", scriptDialog.GetValue( "MapInputChannelsBox" ) )

def OverrideFlagsBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "FlagsBox", scriptDialog.GetValue( "OverrideFlagsBox" ) )

def OverrideInitScriptBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "InitScriptBox", scriptDialog.GetValue( "OverrideInitScriptBox" ) )

def InsertLeaderBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "LeaderBox", scriptDialog.GetValue( "InsertLeaderBox" ) )

def InsertOverlayBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "OverlayBox", scriptDialog.GetValue( "InsertOverlayBox" ) )

def OutputFileBoxChanged( *args ):
    global scriptDialog
    global outputCodecs
    global audioCodecs
    
    outputFilename = scriptDialog.GetValue( "OutputFileBox" )
    format = Path.GetExtension( outputFilename ).strip( "." ).lower()
    
    codecs = None
    if outputCodecs.has_key( format ):
        codecs = outputCodecs[ format ]
    if codecs == None:
        codecs = []
        codecs.append( "" )
    
    scriptDialog.SetValue( "CodecComboBox", "" )
    scriptDialog.SetItems( "CodecComboBox", tuple(codecs) )
    
    codecs = None
    if audioCodecs.has_key( format ):
        codecs = audioCodecs[ format ]
    if codecs == None:
        codecs = []
        codecs.append( "" )
        
    scriptDialog.SetValue( "AudioCodecComboBox", "" )
    scriptDialog.SetItems( "AudioCodecComboBox", tuple(codecs) )

def CodecComboBoxChanged( *args ):
    global scriptDialog
    
    codec = scriptDialog.GetValue( "CodecComboBox" )
    spaceIndex = codec.find( " " )
    if spaceIndex != -1:
        scriptDialog.SetValue( "CodecBox", codec[:spaceIndex] )

def AudioCodecComboBoxChanged( *args ):
    global scriptDialog
    
    codec = scriptDialog.GetValue( "AudioCodecComboBox" )
    spaceIndex = codec.find( " " )
    if spaceIndex != -1:
        scriptDialog.SetValue( "AudioCodecBox", codec[:spaceIndex] )

def OverrideOutputFPSBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "OutputFPSBox", scriptDialog.GetValue( "OverrideOutputFPSBox" ) )

def OverrideResolutionBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ResolutionWidthBox", scriptDialog.GetValue( "OverrideResolutionBox" ) )
    scriptDialog.SetEnabled( "ResolutionHeightBox", scriptDialog.GetValue( "OverrideResolutionBox" ) )

def OverrideOutputGammaBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "OutputGammaBox", scriptDialog.GetValue( "OverrideOutputGammaBox" ) )

def OverrideOutputFormatBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "OutputFormatBitsBox", scriptDialog.GetValue( "OverrideOutputFormatBox" ) )
    scriptDialog.SetEnabled( "OutputFormatBox", scriptDialog.GetValue( "OverrideOutputFormatBox" ) )

def OverrideCodecQualityBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "CodecQualityBox", scriptDialog.GetValue( "OverrideCodecQualityBox" ) )

def OutputCodecBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "CodecBox", scriptDialog.GetValue( "OutputCodecBox" ) )
    scriptDialog.SetEnabled( "CodecComboBox", scriptDialog.GetValue( "OutputCodecBox" ) )

def OverrideKeyIntervalBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "KeyIntervalBox", scriptDialog.GetValue( "OverrideKeyIntervalBox" ) )

def OverrideDataRateBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DataRateBox", scriptDialog.GetValue( "OverrideDataRateBox" ) )

def ApplyDisplayLutBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "DisplayLutBox", scriptDialog.GetValue( "ApplyDisplayLutBox" ) )

def OverrideOutputChannelMapBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "OutputChannelMapBox", scriptDialog.GetValue( "OverrideOutputChannelMapBox" ) )

def OverrideOutputTimeRangeBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "OutputTimeRangeBox", scriptDialog.GetValue( "OverrideOutputTimeRangeBox" ) )

def OverrideOutputCommentBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "OutputCommentBox", scriptDialog.GetValue( "OverrideOutputCommentBox" ) )

def OverrideOutputCopyrightBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "OutputCopyrightBox", scriptDialog.GetValue( "OverrideOutputCopyrightBox" ) )

def OverrideAudioCodecBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "AudioCodecBox", scriptDialog.GetValue( "OverrideAudioCodecBox" ) )
    scriptDialog.SetEnabled( "AudioCodecComboBox", scriptDialog.GetValue( "OverrideAudioCodecBox" ) )

def OverrideAudioRateBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "AudioRateBox", scriptDialog.GetValue( "OverrideAudioRateBox" ) )

def OverrideAudioFormatBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "AudioFormatBitsBox", scriptDialog.GetValue( "OverrideAudioFormatBox" ) )
    scriptDialog.SetEnabled( "AudioFormatBox", scriptDialog.GetValue( "OverrideAudioFormatBox" ) )

def OverrideAudioQualityBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "AudioQualityBox", scriptDialog.GetValue( "OverrideAudioQualityBox" ) )

def OverrideAudioChannelsBoxPressed( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "AudioChannelsBox", scriptDialog.GetValue( "OverrideAudioChannelsBox" ) )

#~ def OverrideExrCPUsBoxPressed( *args ):
    #~ global scriptDialog
    #~ scriptDialog.SetEnabled( "ExrCPUsBox", scriptDialog.GetValue( "OverrideExrCPUsBox" ) )

#~ def OverrideCinPixelBoxPressed( *args ):
    #~ global scriptDialog
    #~ scriptDialog.SetEnabled( "CinPixelBox", scriptDialog.GetValue( "OverrideCinPixelBox" ) )
 
def CloseButtonPressed( *args ):
    CloseDialog()

def SubmitButtonPressed( *args ):
    global scriptDialog
    global sourceDictionary
    global integration_dialog
    
    # Ensure that all source objects have been saved.
    SelectedSourceChanged( None )
    
    errors = ""
    warnings = ""
    
    # Check each layer to ensure that all files specified exist.
    if len(sourceDictionary) == 0:
        errors += "- No layers have been created\n"
    else:
        for sourceName in sourceDictionary:
            source = sourceDictionary[ sourceName ]
            
            if source.Input1 == "":
                errors += "- " + sourceName + ": A Source 1 file must be specified\n"
            elif not File.Exists( source.Input1 ):
                errors += "- " + sourceName + ": Source 1 file '" + source.Input1 + "' does not exist\n"
            elif PathUtils.IsPathLocal( source.Input1 ):
                warnings += "- " + sourceName + ": Source 1 file '" + source.Input1 + "' is local\n"
                
            if source.Input2 != "":
                if not File.Exists( source.Input2 ):
                    errors += "- " + sourceName + ": Source 2 file '" + source.Input2 + "' does not exist\n"
                elif PathUtils.IsPathLocal( source.Input2 ):
                    warnings += "- " + sourceName + ": Source 2 file '" + source.Input2 + "' is local\n"
            
            if source.AudioFiles != "":
                for audioFile in source.AudioFiles.split( "," ):
                    if not File.Exists( audioFile ):
                        errors += "- " + sourceName + ": Audio file '" + source.Input2 + "' does not exist\n"
                    elif PathUtils.IsPathLocal( audioFile ):
                        warnings += "- " + sourceName + ": Audio file '" + source.Input2 + "' is local\n"
            
            if source.OverrideFileLut:
                if source.FileLut == "":
                    errors += "- " + sourceName + ": File LUT override is enabled, but no value is specified\n"
                elif not File.Exists( source.FileLut ):
                    errors += "- " + sourceName + ": File LUT file '" + source.FileLut + "' does not exist\n"
                elif PathUtils.IsPathLocal( source.FileLut ):
                    warnings += "- " + sourceName + ": File LUT file '" + source.FileLut + "' is local\n"
            
            if source.OverrideLookLut:
                if source.LookLut == "":
                    errors += "- " + sourceName + ": Look LUT override is enabled, but no value is specified\n"
                elif not File.Exists( source.LookLut ):
                    errors += "- " + sourceName + ": Look LUT file '" + source.LookLut + "' does not exist\n"
                elif PathUtils.IsPathLocal( source.LookLut ):
                    warnings += "- " + sourceName + ": Look LUT file '" + source.LookLut + "' is local\n"
            
            if source.OverridePreCacheLut:
                if source.PreCacheLut == "":
                    errors += "- " + sourceName + ": Pre-Cache LUT override is enabled, but no value is specified\n"
                elif not File.Exists( source.PreCacheLut ):
                    errors += "- " + sourceName + ": Pre-Cache LUT file '" + source.PreCacheLut + "' does not exist\n"
                elif PathUtils.IsPathLocal( source.PreCacheLut ):
                    warnings += "- " + sourceName + ": Pre-Cache LUT file '" + source.PreCacheLut + "' is local\n"
            
            if source.OverrideChannels and source.Channels == "":
                errors += "- " + sourceName + ": Remap Channels override is enabled, but no value is specified\n"
        
    if scriptDialog.GetValue( "MapInputChannelsBox" ) and scriptDialog.GetValue( "InputChannelsBox" ).strip() == "":
        errors += "- Map Input Channels override is enabled, but no value is specified\n"
    
    if scriptDialog.GetValue( "OverrideFlagsBox" ) and scriptDialog.GetValue( "FlagsBox" ).strip() == "":
        errors += "- Arbitrary Flags For Mu override is enabled, but no value is specified\n"
    
    if scriptDialog.GetValue( "OverrideInitScriptBox" ) and scriptDialog.GetValue( "InitScriptBox" ).strip() == "":
        errors += "- Init Script override is enabled, but no value is specified\n"
    
    if scriptDialog.GetValue( "InsertLeaderBox" ) and scriptDialog.GetValue( "LeaderBox" ).strip() == "":
        errors += "- Insert Leader/Slate override is enabled, but no value is specified\n"
    
    if scriptDialog.GetValue( "InsertOverlayBox" ) and scriptDialog.GetValue( "OverlayBox" ).strip() == "":
        errors += "- Visual Overlay override is enabled, but no value is specified\n"
    
    if scriptDialog.GetValue( "OutputCodecBox" ) and scriptDialog.GetValue( "CodecBox" ).strip() == "":
        errors += "- Output Codec override is enabled, but no value is specified\n"
    
    if scriptDialog.GetValue( "OverrideOutputChannelMapBox" ) and scriptDialog.GetValue( "OutputChannelMapBox" ).strip() == "":
        errors += "- Map Output Channels override is enabled, but no value is specified\n"
    
    if scriptDialog.GetValue( "OverrideOutputTimeRangeBox" ) and scriptDialog.GetValue( "OutputTimeRangeBox" ).strip() == "":
        errors += "- Output Time Range override is enabled, but no value is specified\n"
    
    if scriptDialog.GetValue( "OverrideOutputCommentBox" ) and scriptDialog.GetValue( "OutputCommentBox" ).strip() == "":
        errors += "- Output Comment override is enabled, but no value is specified\n"
    
    if scriptDialog.GetValue( "OverrideOutputCopyrightBox" ) and scriptDialog.GetValue( "OutputCopyrightBox" ).strip() == "":
        errors += "- Output Copyright override is enabled, but no value is specified\n"
    
    if scriptDialog.GetValue( "OverrideAudioCodecBox" ) and scriptDialog.GetValue( "AudioCodecBox" ).strip() == "":
        errors += "- Audio Codec override is enabled, but no value is specified\n"
    
    #~ if scriptDialog.GetValue( "OverrideCinPixelBox" ) and scriptDialog.GetValue( "CinPixelBox" ).strip() == "":
        #~ errors += "- Cineon/DPX Format override is enabled, but no value is specified\n"
    
    displayLut = scriptDialog.GetValue( "DisplayLutBox" ).strip()
    if scriptDialog.GetValue( "ApplyDisplayLutBox" ):
        if displayLut == "":
            errors += "- " + sourceName + ": Display LUT override is enabled, but no value is specified\n"
        elif not File.Exists( displayLut ):
            errors += "- " + sourceName + ": Display LUT file '" + displayLut + "' does not exist\n"
        elif PathUtils.IsPathLocal( displayLut ):
            warnings += "- " + sourceName + ": Display LUT file '" + displayLut + "' is local\n"
    
    outputFile = scriptDialog.GetValue( "OutputFileBox" ).strip()
    if outputFile == "":
        errors += "- An output file must be specified\n"
    elif not Directory.Exists( Path.GetDirectoryName( outputFile ) ):
        errors += "- The directory for the output file '" + outputFile + "' does not exist\n"
    elif PathUtils.IsPathLocal( outputFile ):
        warnings += "- Output file '" + outputFile + "' is local\n"

    # Check if Integration options are valid.
    if not integration_dialog.CheckIntegrationSanity( outputFile ):
        return
    
    if errors != "":
        scriptDialog.ShowMessageBox( "The following errors were detected:\n\n" + errors + "\nPlease fix these before submitting the job.", "Error" )
        return
    if warnings != "":
        result = scriptDialog.ShowMessageBox( "The following warnings were detected:\n\n" + warnings + "\nAre you sure you want to submit this job?", "Warning", ("Yes","No") )
        if result == "No":
            return
    
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "rvio_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=RVIO" )
    writer.WriteLine( "Name=%s" % jobName )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
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
    
    writer.WriteLine( "Frames=0" )
    writer.WriteLine( "ChunkSize=1" )
    
    # Only set output filename if it's a movie file
    if outputFile.find( "#" ) == -1:
        writer.WriteLine( "OutputFilename0=%s" % outputFile )
    else:
        writer.WriteLine( "OutputDirectory0=%s" % Path.GetDirectoryName( outputFile ) )
    
    # Only do production tracking for movie file.
    if outputFile.find( "#" ) == -1:
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "rvio_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
    writer.WriteLine( "LayerCount=%s" % len(sourceDictionary) )
    
    layerCount = 0
    for sourceName in sourceDictionary:
        source = sourceDictionary[ sourceName ]
        writer.WriteLine( "Layer" + str(layerCount) + ("Name=%s" % source.Name) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("Input1=%s" % source.Input1) )
        writer.WriteLine( "Layer" + str(layerCount) + ("Input1StartFrame=%s" % source.Input1StartFrame) )
        writer.WriteLine( "Layer" + str(layerCount) + ("Input1EndFrame=%s" % source.Input1EndFrame) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("Input2=%s" % source.Input2) )
        writer.WriteLine( "Layer" + str(layerCount) + ("Input2StartFrame=%s" % source.Input2StartFrame) )
        writer.WriteLine( "Layer" + str(layerCount) + ("Input2EndFrame=%s" % source.Input2EndFrame) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("AudioFiles=%s" % source.AudioFiles) )
        writer.WriteLine( "Layer" + str(layerCount) + ("DisableAudio=%s" % source.DisableAudio) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverridePixelAspectRatio=%s" % source.OverridePixelAspectRatio) )
        writer.WriteLine( "Layer" + str(layerCount) + ("PixelAspectRatio=%s" % source.PixelAspectRatio) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverrideFileLut=%s" % source.OverrideFileLut) )
        writer.WriteLine( "Layer" + str(layerCount) + ("FileLut=%s" % source.FileLut) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverrideRangeOffset=%s" % source.OverrideRangeOffset) )
        writer.WriteLine( "Layer" + str(layerCount) + ("RangeOffset=%s" % source.RangeOffset) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverrideLookLut=%s" % source.OverrideLookLut) )
        writer.WriteLine( "Layer" + str(layerCount) + ("LookLut=%s" % source.LookLut) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverrideFPS=%s" % source.OverrideFPS) )
        writer.WriteLine( "Layer" + str(layerCount) + ("FPS=%s" % source.FPS) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverridePreCacheLut=%s" % source.OverridePreCacheLut) )
        writer.WriteLine( "Layer" + str(layerCount) + ("PreCacheLut=%s" % source.PreCacheLut) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverrideAudioOffset=%s" % source.OverrideAudioOffset) )
        writer.WriteLine( "Layer" + str(layerCount) + ("AudioOffset=%s" % source.AudioOffset) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverrideChannels=%s" % source.OverrideChannels) )
        writer.WriteLine( "Layer" + str(layerCount) + ("Channels=%s" % source.Channels) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverrideStereoOffset=%s" % source.OverrideStereoOffset) )
        writer.WriteLine( "Layer" + str(layerCount) + ("StereoOffset=%s" % source.StereoOffset) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverrideCrop=%s" % source.OverrideCrop) )
        writer.WriteLine( "Layer" + str(layerCount) + ("CropX0=%s" % source.CropX0) )
        writer.WriteLine( "Layer" + str(layerCount) + ("CropY0=%s" % source.CropY0) )
        writer.WriteLine( "Layer" + str(layerCount) + ("CropX1=%s" % source.CropX1) )
        writer.WriteLine( "Layer" + str(layerCount) + ("CropY1=%s" % source.CropY1) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverrideVolume=%s" % source.OverrideVolume) )
        writer.WriteLine( "Layer" + str(layerCount) + ("Volume=%s" % source.Volume) )
        
        writer.WriteLine( "Layer" + str(layerCount) + ("OverrideUnCrop=%s" % source.OverrideUnCrop) )
        writer.WriteLine( "Layer" + str(layerCount) + ("UnCropW=%s" % source.UnCropW) )
        writer.WriteLine( "Layer" + str(layerCount) + ("UnCropH=%s" % source.UnCropH) )
        writer.WriteLine( "Layer" + str(layerCount) + ("UnCropX=%s" % source.UnCropX) )
        writer.WriteLine( "Layer" + str(layerCount) + ("UnCropY=%s" % source.UnCropY) )
        
        layerCount = layerCount + 1
        
    writer.WriteLine( "InputConvertLog=%s" % scriptDialog.GetValue( "ConvertLogBox" ) )
    writer.WriteLine( "InputConvertSRGB=%s" % scriptDialog.GetValue( "ConvertSRGBBox" ) )
    writer.WriteLine( "InputConvert709=%s" % scriptDialog.GetValue( "Convert709Box" ) )
    writer.WriteLine( "InputPremultiply=%s" % scriptDialog.GetValue( "PremultiplyBox" ) )
    writer.WriteLine( "InputUnpremultiply=%s" % scriptDialog.GetValue( "UnpremultiplyBox" ) )
    writer.WriteLine( "InputFlip=%s" % scriptDialog.GetValue( "FlipBox" ) )
    writer.WriteLine( "InputFlop=%s" % scriptDialog.GetValue( "FlopBox" ) )
    writer.WriteLine( "BestQuality=%s" % scriptDialog.GetValue( "QualityBox" ) )
    writer.WriteLine( "NoPrerender=%s" % scriptDialog.GetValue( "NoPrerenderBox" ) )
    
    writer.WriteLine( "InputOverrideGamma=%s" % scriptDialog.GetValue( "OverrideGammaBox" ) )
    writer.WriteLine( "InputGamma=%s" % scriptDialog.GetValue( "GammaBox" ) )
    writer.WriteLine( "InputOverrideExposure=%s" % scriptDialog.GetValue( "OverrideExposureBox" ) )
    writer.WriteLine( "InputExposure=%s" % scriptDialog.GetValue( "ExposureBox" ) )
    writer.WriteLine( "InputOverrideScale=%s" % scriptDialog.GetValue( "OverrideScaleBox" ) )
    writer.WriteLine( "InputScale=%s" % scriptDialog.GetValue( "ScaleBox" ) )
    writer.WriteLine( "InputOverrideResize=%s" % scriptDialog.GetValue( "ResizeInputBox" ) )
    writer.WriteLine( "InputResizeWidth=%s" % scriptDialog.GetValue( "ResizeInputWidthBox" ) )
    writer.WriteLine( "InputResizeHeight=%s" % scriptDialog.GetValue( "ResizeInputHeightBox" ) )
    
    writer.WriteLine( "OverrideResample=%s" % scriptDialog.GetValue( "OverrideResampleBox" ) )
    writer.WriteLine( "Resample=%s" % scriptDialog.GetValue( "ResampleBox" ) )
    writer.WriteLine( "OverrideThreads=%s" % scriptDialog.GetValue( "OverrideThreadsBox" ) )
    writer.WriteLine( "Threads=%s" % scriptDialog.GetValue( "ThreadsBox" ) )
    writer.WriteLine( "OverrideLeaderFrames=%s" % scriptDialog.GetValue( "OverrideLeaderFramesBox" ) )
    writer.WriteLine( "LeaderFrames=%s" % scriptDialog.GetValue( "LeaderFramesBox" ) )
    
    writer.WriteLine( "OverrideInputChannels=%s" % scriptDialog.GetValue( "MapInputChannelsBox" ) )
    writer.WriteLine( "InputChannels=%s" % scriptDialog.GetValue( "InputChannelsBox" ).strip() )
    writer.WriteLine( "OverrideFlags=%s" % scriptDialog.GetValue( "OverrideFlagsBox" ) )
    writer.WriteLine( "Flags=%s" % scriptDialog.GetValue( "FlagsBox" ).strip() )
    
    writer.WriteLine( "OverrideInitScript=%s" % scriptDialog.GetValue( "OverrideInitScriptBox" ) )
    writer.WriteLine( "InitScript=%s" % scriptDialog.GetValue( "InitScriptBox" ).strip() )
    writer.WriteLine( "OverrideLeaderScript=%s" % scriptDialog.GetValue( "InsertLeaderBox" ) )
    writer.WriteLine( "LeaderScript=%s" % scriptDialog.GetValue( "LeaderBox" ).strip() )
    writer.WriteLine( "OverrideOverlayScript=%s" % scriptDialog.GetValue( "InsertOverlayBox" ) )
    writer.WriteLine( "OverlayScript=%s" % scriptDialog.GetValue( "OverlayBox" ).strip() )
    
    writer.WriteLine( "CommandLine=%s" % scriptDialog.GetValue( "CommandLineBox" ) )
    
    writer.WriteLine( "OutputFile=%s" % outputFile )
    
    writer.WriteLine( "OutputConvertLog=%s" % scriptDialog.GetValue( "ConvertOutputLogBox" ) )
    writer.WriteLine( "OutputConvertSRGB=%s" % scriptDialog.GetValue( "ConvertOutputSRGBBox" ) )
    writer.WriteLine( "OutputConvert709=%s" % scriptDialog.GetValue( "ConvertOutput709Box" ) )
    writer.WriteLine( "OutputPremultiply=%s" % scriptDialog.GetValue( "PremultiplyOutputBox" ) )
    writer.WriteLine( "OutputUnpremultiply=%s" % scriptDialog.GetValue( "UnPremultiplyOutputBox" ) )
    writer.WriteLine( "OutputStereo=%s" % scriptDialog.GetValue( "OutputStereoBox" ) )
    writer.WriteLine( "OutputTimeFromRV=%s" % scriptDialog.GetValue( "OutputRVTimeRangeBox" ) )
    
    writer.WriteLine( "OutputOverrideFPS=%s" % scriptDialog.GetValue( "OverrideOutputFPSBox" ) )
    writer.WriteLine( "OutputFPS=%s" % scriptDialog.GetValue( "OutputFPSBox" ) )
    writer.WriteLine( "OutputOverrideResolution=%s" % scriptDialog.GetValue( "OverrideResolutionBox" ) )
    writer.WriteLine( "OutputResolutionWidth=%s" % scriptDialog.GetValue( "ResolutionWidthBox" ) )
    writer.WriteLine( "OutputResolutionHeight=%s" % scriptDialog.GetValue( "ResolutionHeightBox" ) )
    
    writer.WriteLine( "OutputOverrideGamma=%s" % scriptDialog.GetValue( "OverrideOutputGammaBox" ) )
    writer.WriteLine( "OutputGamma=%s" % scriptDialog.GetValue( "OutputGammaBox" ) )
    writer.WriteLine( "OutputOverrideFormat=%s" % scriptDialog.GetValue( "OverrideOutputFormatBox" ) )
    writer.WriteLine( "OutputFormatBits=%s" % scriptDialog.GetValue( "OutputFormatBitsBox" ) )
    writer.WriteLine( "OutputFormat=%s" % scriptDialog.GetValue( "OutputFormatBox" ) )
    
    writer.WriteLine( "OutputOverrideCodecQuality=%s" % scriptDialog.GetValue( "OverrideCodecQualityBox" ) )
    writer.WriteLine( "OutputCodecQuality=%s" % scriptDialog.GetValue( "CodecQualityBox" ) )
    writer.WriteLine( "OutputOverrideCodec=%s" % scriptDialog.GetValue( "OutputCodecBox" ) )
    writer.WriteLine( "OutputCodec=%s" % scriptDialog.GetValue( "CodecBox" ).strip() )
    
    writer.WriteLine( "OutputOverrideKeyInterval=%s" % scriptDialog.GetValue( "OverrideKeyIntervalBox" ) )
    writer.WriteLine( "OutputKeyInterval=%s" % scriptDialog.GetValue( "KeyIntervalBox" ) )
    writer.WriteLine( "OutputOverrideDataRate=%s" % scriptDialog.GetValue( "OverrideDataRateBox" ) )
    writer.WriteLine( "OutputDataRate=%s" % scriptDialog.GetValue( "DataRateBox" ) )
    
    writer.WriteLine( "OutputOverrideDLut=%s" % scriptDialog.GetValue( "ApplyDisplayLutBox" ) )
    writer.WriteLine( "OutputDLut=%s" % displayLut )
    writer.WriteLine( "OutputOverrideChannels=%s" % scriptDialog.GetValue( "OverrideOutputChannelMapBox" ) )
    writer.WriteLine( "OutputChannels=%s" % scriptDialog.GetValue( "OutputChannelMapBox" ).strip() )
    writer.WriteLine( "OutputOverrideTimeRange=%s" % scriptDialog.GetValue( "OverrideOutputTimeRangeBox" ) )
    writer.WriteLine( "OutputTimeRange=%s" % scriptDialog.GetValue( "OutputTimeRangeBox" ).strip() )
    
    writer.WriteLine( "OutputOverrideComment=%s" % scriptDialog.GetValue( "OverrideOutputCommentBox" ) )
    writer.WriteLine( "OutputComment=%s" % scriptDialog.GetValue( "OutputCommentBox" ).strip() )
    writer.WriteLine( "OutputOverrideCopyright=%s" % scriptDialog.GetValue( "OverrideOutputCopyrightBox" ) )
    writer.WriteLine( "OutputCopyright=%s" % scriptDialog.GetValue( "OutputCopyrightBox" ).strip() )
    
    writer.WriteLine( "AudioOverrideCodec=%s" % scriptDialog.GetValue( "OverrideAudioCodecBox" ) )
    writer.WriteLine( "AudioCodec=%s" % scriptDialog.GetValue( "AudioCodecBox" ).strip() )
    writer.WriteLine( "AudioOverrideRate=%s" % scriptDialog.GetValue( "OverrideAudioRateBox" ) )
    writer.WriteLine( "AudioRate=%s" % scriptDialog.GetValue( "AudioRateBox" ) )
    writer.WriteLine( "AudioOverrideFormat=%s" % scriptDialog.GetValue( "OverrideAudioFormatBox" ) )
    writer.WriteLine( "AudioFormatBits=%s" % scriptDialog.GetValue( "AudioFormatBitsBox" ) )
    writer.WriteLine( "AudioFormat=%s" % scriptDialog.GetValue( "AudioFormatBox" ) )
    writer.WriteLine( "AudioOverrideQuality=%s" % scriptDialog.GetValue( "OverrideAudioQualityBox" ) )
    writer.WriteLine( "AudioQuality=%s" % scriptDialog.GetValue( "AudioQualityBox" ) )
    writer.WriteLine( "AudioOverrideChannels=%s" % scriptDialog.GetValue( "OverrideAudioChannelsBox" ) )
    writer.WriteLine( "AudioChannels=%s" % scriptDialog.GetValue( "AudioChannelsBox" ) )
    
    #~ writer.WriteLine( "ExrNoOneChannel=%s" % scriptDialog.GetValue( "ExrNoOneChannelBox" ) )
    #~ writer.WriteLine( "ExrInherit=%s" % scriptDialog.GetValue( "ExrInheritBox" ) )
    #~ writer.WriteLine( "ExrOverrideCPUs=%s" % scriptDialog.GetValue( "OverrideExrCPUsBox" ) )
    #~ writer.WriteLine( "ExrCPUs=%s" % scriptDialog.GetValue( "ExrCPUsBox" ) )
    
    #~ writer.WriteLine( "CinOverrideFormat=%s" % scriptDialog.GetValue( "OverrideCinPixelBox" ) )
    #~ writer.WriteLine( "CinFormat=%s" % scriptDialog.GetValue( "CinPixelBox" ).strip() )
    
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )

########################################################################
## A class for storing information about sources
########################################################################
class Source( object ):
    Name = ""
    
    Input1 = ""
    Input1StartFrame = 0
    Input1EndFrame = 0
    
    Input2 = ""
    Input2StartFrame = 0
    Input2EndFrame = 0
    
    AudioFiles = ""
    DisableAudio = False
    
    OverridePixelAspectRatio = False
    PixelAspectRatio = 1.3333
    
    OverrideFileLut = False
    FileLut = ""
    
    OverrideRangeOffset = False
    RangeOffset = 0
    
    OverrideLookLut = False
    LookLut = ""
    
    OverrideFPS = False
    FPS = 24.0
    
    OverridePreCacheLut = False
    PreCacheLut = ""
    
    OverrideAudioOffset = False
    AudioOffset = 0.00
    
    OverrideChannels = False
    Channels = ""
    
    OverrideStereoOffset = False
    StereoOffset = 0.00
    
    OverrideCrop = False
    CropX0 = 0
    CropY0 = 0
    CropX1 = 0
    CropY1 = 0
    
    OverrideVolume = False
    Volume = 1.00
    
    OverrideUnCrop = False
    UnCropW = 0
    UnCropH = 0
    UnCropX = 0
    UnCropY = 0
    
    def __init__( self, name ):
        self.Name = name
        
    def SaveToFile( self, fileName ):
        FileUtils.SetIniFileSetting( fileName, "Source", "Name", self.Name )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "Input1", self.Input1 )
        FileUtils.SetIniFileSetting( fileName, "Source", "Input1StartFrame", str(self.Input1StartFrame) )
        FileUtils.SetIniFileSetting( fileName, "Source", "Input1EndFrame", str(self.Input1EndFrame) )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "Input2", self.Input2 )
        FileUtils.SetIniFileSetting( fileName, "Source", "Input2StartFrame", str(self.Input2StartFrame) )
        FileUtils.SetIniFileSetting( fileName, "Source", "Input2EndFrame", str(self.Input2EndFrame) )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "AudioFiles", self.AudioFiles )
        FileUtils.SetIniFileSetting( fileName, "Source", "DisableAudio", str(self.DisableAudio) )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverridePixelAspectRatio", str(self.OverridePixelAspectRatio) )
        FileUtils.SetIniFileSetting( fileName, "Source", "PixelAspectRatio", str(self.PixelAspectRatio) )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverrideFileLut", str(self.OverrideFileLut) )
        FileUtils.SetIniFileSetting( fileName, "Source", "FileLut", self.FileLut )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverrideRangeOffset", str(self.OverrideRangeOffset) )
        FileUtils.SetIniFileSetting( fileName, "Source", "RangeOffset", str(self.RangeOffset) )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverrideLookLut", str(self.OverrideLookLut) )
        FileUtils.SetIniFileSetting( fileName, "Source", "LookLut", self.LookLut )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverrideFPS", str(self.OverrideFPS) )
        FileUtils.SetIniFileSetting( fileName, "Source", "FPS", str(self.FPS) )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverridePreCacheLut", str(self.OverridePreCacheLut) )
        FileUtils.SetIniFileSetting( fileName, "Source", "PreCacheLut", self.PreCacheLut )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverrideAudioOffset", str(self.OverrideAudioOffset) )
        FileUtils.SetIniFileSetting( fileName, "Source", "AudioOffset", str(self.AudioOffset) )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverrideChannels", str(self.OverrideChannels) )
        FileUtils.SetIniFileSetting( fileName, "Source", "Channels", self.Channels )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverrideStereoOffset", str(self.OverrideStereoOffset) )
        FileUtils.SetIniFileSetting( fileName, "Source", "StereoOffset", str(self.StereoOffset) )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverrideCrop", str(self.OverrideCrop) )
        FileUtils.SetIniFileSetting( fileName, "Source", "CropX0", str(self.CropX0) )
        FileUtils.SetIniFileSetting( fileName, "Source", "CropY0", str(self.CropY0) )
        FileUtils.SetIniFileSetting( fileName, "Source", "CropX1", str(self.CropX1) )
        FileUtils.SetIniFileSetting( fileName, "Source", "CropY1", str(self.CropY1) )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverrideVolume", str(self.OverrideVolume) )
        FileUtils.SetIniFileSetting( fileName, "Source", "Volume", str(self.Volume) )
        
        FileUtils.SetIniFileSetting( fileName, "Source", "OverrideUnCrop", str(self.OverrideUnCrop) )
        FileUtils.SetIniFileSetting( fileName, "Source", "UnCropW", str(self.UnCropW) )
        FileUtils.SetIniFileSetting( fileName, "Source", "UnCropH", str(self.UnCropH) )
        FileUtils.SetIniFileSetting( fileName, "Source", "UnCropX", str(self.UnCropX) )
        FileUtils.SetIniFileSetting( fileName, "Source", "UnCropY", str(self.UnCropY) )
        
    def LoadFromFile( self, fileName ):
        self.Name = FileUtils.GetIniFileSetting( fileName, "Source", "Name", "" )
        
        self.Input1 = FileUtils.GetIniFileSetting( fileName, "Source", "Input1", "" )
        self.Input1StartFrame = int(FileUtils.GetIniFileSetting( fileName, "Source", "Input1StartFrame", "0" ))
        self.Input1EndFrame = int(FileUtils.GetIniFileSetting( fileName, "Source", "Input1EndFrame", "0" ))
        
        self.Input2 = FileUtils.GetIniFileSetting( fileName, "Source", "Input2", "" )
        self.Input2StartFrame = int(FileUtils.GetIniFileSetting( fileName, "Source", "Input2StartFrame", "0" ))
        self.Input2EndFrame = int(FileUtils.GetIniFileSetting( fileName, "Source", "Input2EndFrame", "0" ))
        
        self.AudioFiles = FileUtils.GetIniFileSetting( fileName, "Source", "AudioFiles", "" )
        self.DisableAudio = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "DisableAudio", "False" ))
        
        self.OverridePixelAspectRatio = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverridePixelAspectRatio", "False" ))
        self.PixelAspectRatio = float(FileUtils.GetIniFileSetting( fileName, "Source", "PixelAspectRatio", "1.3333" ))
        
        self.OverrideFileLut = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverrideFileLut", "False" ))
        self.FileLut = FileUtils.GetIniFileSetting( fileName, "Source", "FileLut", "" )
        
        self.OverrideRangeOffset = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverrideRangeOffset", "False" ))
        self.RangeOffset = int(FileUtils.GetIniFileSetting( fileName, "Source", "RangeOffset", "0" ))
        
        self.OverrideLookLut = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverrideLookLut", "False" ))
        self.LookLut = FileUtils.GetIniFileSetting( fileName, "Source", "LookLut", "" )
        
        self.OverrideFPS = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverrideFPS", "False" ))
        self.FPS = float(FileUtils.GetIniFileSetting( fileName, "Source", "FPS", "24.00" ))
        
        self.OverridePreCacheLut = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverridePreCacheLut", "False" ))
        self.PreCacheLut = FileUtils.GetIniFileSetting( fileName, "Source", "PreCacheLut", "" )
        
        self.OverrideAudioOffset = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverrideAudioOffset", "False" ))
        self.AudioOffset = float(FileUtils.GetIniFileSetting( fileName, "Source", "AudioOffset", "0.00" ))
        
        self.OverrideChannels = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverrideChannels", "False" ))
        self.Channels = FileUtils.GetIniFileSetting( fileName, "Source", "Channels", "" )
        
        self.OverrideStereoOffset = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverrideStereoOffset", "False" ))
        self.StereoOffset = float(FileUtils.GetIniFileSetting( fileName, "Source", "StereoOffset", "0.00" ))
        
        self.OverrideCrop = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverrideCrop", "False" ))
        self.CropX0 = int(FileUtils.GetIniFileSetting( fileName, "Source", "CropX0", "0" ))
        self.CropY0 = int(FileUtils.GetIniFileSetting( fileName, "Source", "CropY0", "0" ))
        self.CropX1 = int(FileUtils.GetIniFileSetting( fileName, "Source", "CropX1", "0" ))
        self.CropY1 = int(FileUtils.GetIniFileSetting( fileName, "Source", "CropY1", "0" ))
        
        self.OverrideVolume = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverrideVolume", "False" ))
        self.Volume = float(FileUtils.GetIniFileSetting( fileName, "Source", "Volume", "1.00" ))
        
        self.OverrideUnCrop = StringToBool(FileUtils.GetIniFileSetting( fileName, "Source", "OverrideUnCrop", "False" ))
        self.UnCropW = int(FileUtils.GetIniFileSetting( fileName, "Source", "UnCropW", "0" ))
        self.UnCropH = int(FileUtils.GetIniFileSetting( fileName, "Source", "UnCropH", "0" ))
        self.UnCropX = int(FileUtils.GetIniFileSetting( fileName, "Source", "UnCropX", "0" ))
        self.UnCropY = int(FileUtils.GetIniFileSetting( fileName, "Source", "UnCropY", "0" ))

def GetRawCodecText():
    #This is the raw output from rvio.
    return u"""\
rvio
Version 3.10.13, built on Apr  7 2011 at 15:41:22 (32bit). (L)
Copyright (c) 2008-2011 Tweak Software. All rights reserved.
format "rv" - Tweak RV file (Read, AudioRead)
format "movieproc" - Procedurally Generated Image/Movie (AttributeRead, Read)
format "null" - Null I/O (AttributeWrite, Write, AudioWrite)
   image codecs: 
      default (No overhead test)
      copy (Copy test)

format "exr" - OpenEXR Image (Read, Write)
   image codecs: 
      PIZ (piz-based wavelet compression)
      ZIP (zlib compression, in blocks of 16 scan lines)
      ZIPS (zlib compression, one scan line at a time)
      RLE (run length encoding)
      PXR24 (lossy 24-bit float compression)
      B44 (lossy 4-by-4 pixel block compression, fixed compression rate)
      B44A (lossy 4-by-4 pixel block compression, flat fields are comressed more)
      NONE (uncompressed)

format "openexr" - OpenEXR Image (Read, Write)
   image codecs: 
      PIZ (piz-based wavelet compression)
      ZIP (zlib compression, in blocks of 16 scan lines)
      ZIPS (zlib compression, one scan line at a time)
      RLE (run length encoding)
      PXR24 (lossy 24-bit float compression)
      B44 (lossy 4-by-4 pixel block compression, fixed compression rate)
      B44A (lossy 4-by-4 pixel block compression, flat fields are comressed more)
      NONE (uncompressed)

format "sxr" - Stereo/Multiview OpenEXR Image (Read, Write)
   image codecs: 
      PIZ (piz-based wavelet compression)
      ZIP (zlib compression, in blocks of 16 scan lines)
      ZIPS (zlib compression, one scan line at a time)
      RLE (run length encoding)
      PXR24 (lossy 24-bit float compression)
      B44 (lossy 4-by-4 pixel block compression, fixed compression rate)
      B44A (lossy 4-by-4 pixel block compression, flat fields are comressed more)
      NONE (uncompressed)

format "tif" - TIFF Image (Read, Write)
   image codecs: 
      NONE (No compression)
      DEFLATE (Deflate compression)
      LZW (Lempel-Ziv  & Welch)
      PACKBITS (Macintosh RLE)
      ADOBE_DEFLATE (Deflate compression as recognized by Adobe)
      CCITTRLE (CCITT modified Huffman RLE)
      CCITTFAX3 (CCITT Group 3 fax encoding)
      CCITT_T4 (CCITT T.4 (TIFF 6 name))
      CCITTFAX4 (CCITT Group 4 fax encoding)
      CCITT_T6 (CCITT T.6 (TIFF 6 name))
      JPEG (%JPEG DCT compression)
      NEXT (NeXT 2-bit RLE)
      CCITTRLEW (#1 w/ word alignment)
      THUNDERSCAN (ThunderScan RLE)
      IT8CTPAD (IT8 CT w/padding)
      IT8LW (IT8 Linework RLE)
      IT8BL (IT8 Binary line art)
      PIXARFILM (Pixar companded 10bit LZW)
      PIXARLOG (Pixar companded 11bit ZIP)
      DCS (Kodak DCS encoding)
      JBIG (ISO JBIG)
      SGILOG (SGI Log Luminance RLE)
      SGILOG24 (SGI Log 24-bit packed)
      JP2000 (Leadtools JPEG2000)

format "tiff" - TIFF Image (Read, Write)
   image codecs: 
      NONE (No compression)
      DEFLATE (Deflate compression)
      LZW (Lempel-Ziv  & Welch)
      PACKBITS (Macintosh RLE)
      ADOBE_DEFLATE (Deflate compression as recognized by Adobe)
      CCITTRLE (CCITT modified Huffman RLE)
      CCITTFAX3 (CCITT Group 3 fax encoding)
      CCITT_T4 (CCITT T.4 (TIFF 6 name))
      CCITTFAX4 (CCITT Group 4 fax encoding)
      CCITT_T6 (CCITT T.6 (TIFF 6 name))
      JPEG (%JPEG DCT compression)
      NEXT (NeXT 2-bit RLE)
      CCITTRLEW (#1 w/ word alignment)
      THUNDERSCAN (ThunderScan RLE)
      IT8CTPAD (IT8 CT w/padding)
      IT8LW (IT8 Linework RLE)
      IT8BL (IT8 Binary line art)
      PIXARFILM (Pixar companded 10bit LZW)
      PIXARLOG (Pixar companded 11bit ZIP)
      DCS (Kodak DCS encoding)
      JBIG (ISO JBIG)
      SGILOG (SGI Log Luminance RLE)
      SGILOG24 (SGI Log 24-bit packed)
      JP2000 (Leadtools JPEG2000)

format "sm" - Entropy (TIFF) Shadow Map (Read)
   image codecs: 
      NONE (No compression)
      DEFLATE (Deflate compression)
      LZW (Lempel-Ziv  & Welch)
      PACKBITS (Macintosh RLE)
      ADOBE_DEFLATE (Deflate compression as recognized by Adobe)
      CCITTRLE (CCITT modified Huffman RLE)
      CCITTFAX3 (CCITT Group 3 fax encoding)
      CCITT_T4 (CCITT T.4 (TIFF 6 name))
      CCITTFAX4 (CCITT Group 4 fax encoding)
      CCITT_T6 (CCITT T.6 (TIFF 6 name))
      JPEG (%JPEG DCT compression)
      NEXT (NeXT 2-bit RLE)
      CCITTRLEW (#1 w/ word alignment)
      THUNDERSCAN (ThunderScan RLE)
      IT8CTPAD (IT8 CT w/padding)
      IT8LW (IT8 Linework RLE)
      IT8BL (IT8 Binary line art)
      PIXARFILM (Pixar companded 10bit LZW)
      PIXARLOG (Pixar companded 11bit ZIP)
      DCS (Kodak DCS encoding)
      JBIG (ISO JBIG)
      SGILOG (SGI Log Luminance RLE)
      SGILOG24 (SGI Log 24-bit packed)
      JP2000 (Leadtools JPEG2000)

format "tex" - RenderMan (TIFF) Texture Map (Read)
   image codecs: 
      NONE (No compression)
      DEFLATE (Deflate compression)
      LZW (Lempel-Ziv  & Welch)
      PACKBITS (Macintosh RLE)
      ADOBE_DEFLATE (Deflate compression as recognized by Adobe)
      CCITTRLE (CCITT modified Huffman RLE)
      CCITTFAX3 (CCITT Group 3 fax encoding)
      CCITT_T4 (CCITT T.4 (TIFF 6 name))
      CCITTFAX4 (CCITT Group 4 fax encoding)
      CCITT_T6 (CCITT T.6 (TIFF 6 name))
      JPEG (%JPEG DCT compression)
      NEXT (NeXT 2-bit RLE)
      CCITTRLEW (#1 w/ word alignment)
      THUNDERSCAN (ThunderScan RLE)
      IT8CTPAD (IT8 CT w/padding)
      IT8LW (IT8 Linework RLE)
      IT8BL (IT8 Binary line art)
      PIXARFILM (Pixar companded 10bit LZW)
      PIXARLOG (Pixar companded 11bit ZIP)
      DCS (Kodak DCS encoding)
      JBIG (ISO JBIG)
      SGILOG (SGI Log Luminance RLE)
      SGILOG24 (SGI Log 24-bit packed)
      JP2000 (Leadtools JPEG2000)

format "tx" - RenderMan (TIFF) Texture Map (Read)
   image codecs: 
      NONE (No compression)
      DEFLATE (Deflate compression)
      LZW (Lempel-Ziv  & Welch)
      PACKBITS (Macintosh RLE)
      ADOBE_DEFLATE (Deflate compression as recognized by Adobe)
      CCITTRLE (CCITT modified Huffman RLE)
      CCITTFAX3 (CCITT Group 3 fax encoding)
      CCITT_T4 (CCITT T.4 (TIFF 6 name))
      CCITTFAX4 (CCITT Group 4 fax encoding)
      CCITT_T6 (CCITT T.6 (TIFF 6 name))
      JPEG (%JPEG DCT compression)
      NEXT (NeXT 2-bit RLE)
      CCITTRLEW (#1 w/ word alignment)
      THUNDERSCAN (ThunderScan RLE)
      IT8CTPAD (IT8 CT w/padding)
      IT8LW (IT8 Linework RLE)
      IT8BL (IT8 Binary line art)
      PIXARFILM (Pixar companded 10bit LZW)
      PIXARLOG (Pixar companded 11bit ZIP)
      DCS (Kodak DCS encoding)
      JBIG (ISO JBIG)
      SGILOG (SGI Log Luminance RLE)
      SGILOG24 (SGI Log 24-bit packed)
      JP2000 (Leadtools JPEG2000)

format "tdl" - 3delight (TIFF) Mip-Mapped Texture (Read)
   image codecs: 
      NONE (No compression)
      DEFLATE (Deflate compression)
      LZW (Lempel-Ziv  & Welch)
      PACKBITS (Macintosh RLE)
      ADOBE_DEFLATE (Deflate compression as recognized by Adobe)
      CCITTRLE (CCITT modified Huffman RLE)
      CCITTFAX3 (CCITT Group 3 fax encoding)
      CCITT_T4 (CCITT T.4 (TIFF 6 name))
      CCITTFAX4 (CCITT Group 4 fax encoding)
      CCITT_T6 (CCITT T.6 (TIFF 6 name))
      JPEG (%JPEG DCT compression)
      NEXT (NeXT 2-bit RLE)
      CCITTRLEW (#1 w/ word alignment)
      THUNDERSCAN (ThunderScan RLE)
      IT8CTPAD (IT8 CT w/padding)
      IT8LW (IT8 Linework RLE)
      IT8BL (IT8 Binary line art)
      PIXARFILM (Pixar companded 10bit LZW)
      PIXARLOG (Pixar companded 11bit ZIP)
      DCS (Kodak DCS encoding)
      JBIG (ISO JBIG)
      SGILOG (SGI Log Luminance RLE)
      SGILOG24 (SGI Log 24-bit packed)
      JP2000 (Leadtools JPEG2000)

format "shd" - 3delight (TIFF) Shadow Map (Read)
   image codecs: 
      NONE (No compression)
      DEFLATE (Deflate compression)
      LZW (Lempel-Ziv  & Welch)
      PACKBITS (Macintosh RLE)
      ADOBE_DEFLATE (Deflate compression as recognized by Adobe)
      CCITTRLE (CCITT modified Huffman RLE)
      CCITTFAX3 (CCITT Group 3 fax encoding)
      CCITT_T4 (CCITT T.4 (TIFF 6 name))
      CCITTFAX4 (CCITT Group 4 fax encoding)
      CCITT_T6 (CCITT T.6 (TIFF 6 name))
      JPEG (%JPEG DCT compression)
      NEXT (NeXT 2-bit RLE)
      CCITTRLEW (#1 w/ word alignment)
      THUNDERSCAN (ThunderScan RLE)
      IT8CTPAD (IT8 CT w/padding)
      IT8LW (IT8 Linework RLE)
      IT8BL (IT8 Binary line art)
      PIXARFILM (Pixar companded 10bit LZW)
      PIXARLOG (Pixar companded 11bit ZIP)
      DCS (Kodak DCS encoding)
      JBIG (ISO JBIG)
      SGILOG (SGI Log Luminance RLE)
      SGILOG24 (SGI Log 24-bit packed)
      JP2000 (Leadtools JPEG2000)

format "jpeg" - JPEG Image (Read, Write)
format "jpg" - JPEG Image (Read, Write)
format "dpx" - Digital Picture Exchange Image (Read, Write)
         encode parameters
            transfer Transfer function (LOG, DENSITY, REC709, USER, VIDEO, SMPTE274M, REC601-625, REC601-525, NTSC, PAL, or number)
            colorimetric Colorimetric specification (REC709, USER, VIDEO, SMPTE274M, REC601-625, REC601-525, NTSC, PAL, or number)
            creator ASCII string
            copyright ASCII string
            project ASCII string
            orientation Pixel Origin string or int (TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT, ROTATED_TOP_LEFT, ROTATED_TOP_RIGHT, ROTATED_BOTTOM_LEFT, ROTATED_BOTTOM_RIGHT)
            create_time ISO 8601 ASCII string: YYYY:MM:DD:hh:mm:ssTZ 
            film/mfg_id 2 digit manufacturer ID edge code
            film/type 2 digit film type edge code
            film/offset 2 digit film offset in perfs edge code
            film/prefix 6 digit film prefix edge code
            film/count 4 digit film count edge code
            film/format 32 char film format (e.g. Academy)
            film/frame_position Frame position in sequence
            film/sequence_len Sequence length
            film/frame_rate Frame rate (frames per second)
            film/shutter_angle Shutter angle in degrees
            film/frame_id 32 character frame identification
            film/slate_info 100 character slate info
            tv/time_code SMPTE time code
            tv/user_bits SMPTE user bits
            tv/interlace Interlace (0=no, 1=2:1)
            tv/field_num Field number
            tv/video_signal Video signal standard 0-254 (see DPX spec)
            tv/horizontal_sample_rate Horizontal sampling rate in Hz
            tv/vertical_sample_rate Vertical sampling rate in Hz
            tv/frame_rate Temporal sampling rate or frame rate in Hz
            tv/time_offset Time offset from sync to first pixel in ms
            tv/gamma Gamma
            tv/black_level Black level
            tv/black_gain Black gain
            tv/break_point Breakpoint
            tv/white_level White level
            tv/integration_times Integration times
            source/x_offset X offset
            source/y_offset X offset
            source/x_center X center
            source/y_center Y center
            source/x_original_size X original size
            source/y_original_size Y original size
            source/file_name Source file name
            source/creation_time Source creation time YYYY:MM:DD:hh:mm:ssTZ
            source/input_dev Input device name
            source/input_dev Input device serial number
            source/border_XL Border validity left
            source/border_XR Border validity right
            source/border_YT Border validity top
            source/border_YB Border validity bottom
            source/pixel_aspect_H Pixel aspect ratio horizonal component
            source/pixel_aspect_V Pixel aspect ratio vertical component
   image codecs: 
      NONE (uncompressed)

format "cin" - Kodak Cineon Digital Film Image (Read, Write)
format "cineon" - Kodak Cineon Digital Film Image (Read, Write)
format "targa" - TARGA Image (Read, Write)
   image codecs: 
      RLE (Run Length Encoding)
      RAW (Raw (no compression))

format "tga" - TARGA Image (Read, Write)
   image codecs: 
      RLE (Run Length Encoding)
      RAW (Raw (no compression))

format "tpic" - TARGA Image (Read, Write)
   image codecs: 
      RLE (Run Length Encoding)
      RAW (Raw (no compression))

format "png" - Portable Network Graphics Image (Read, Write)
format "iff" - Interchange File Format (Read)
format "rla" - Wavefront/3DStudio Image (Read)
format "rpf" - 3DStudio Image (Read)
format "sgi" - Silicon Graphics RGB Image (Read)
format "bw" - Silicon Graphics Monochrome Image (Read)
format "rgb" - Silicon Graphics RGB Image (Read)
format "rgba" - Silicon Graphics RGBA Image (Read)
format "yuv" - YCbCr raw image file (Read)
format "j2k" - JPEG-2000 Codestream (Read)
format "jpt" - JPT-stream (JPEG 2000, JPIP) (Read)
format "jp2" - JPEG-2000 Image (Read)
format "*mraysubfile*" - Mental Ray Stub File Reader (Read)
format "rgbe" - Radiance HDR RGB + Exponent Image (Read, Write)
format "hdr" - Radiance HDR RGB + Exponent Image (Read, Write)
format "z" - Pixar Z-Depth (Read)
format "zfile" - Pixar Z-Depth (Read)
format "bmp" - Windows Bitmap (Read, Write)
format "cut" - Dr. Halo Cut File (Read)
format "dds" - DirectDraw Surface (Read, Write)
format "gif" - Graphics Interchange Format (Read)
format "ico" - Palette (Read)
format "cur" - Palette (Read)
format "lbm" - Interlaced Bitmap (Read)
format "lif" - Homeworld File (Read)
format "lmp" - Doom Walls/Flats (Read)
format "mdl" - Half-Life Model (Read)
format "pcd" - PhotoCD (Read)
format "pcx" - ZSoft PCX (Read, Write)
format "pic" - PIC (Read)
format "pbm" - Portable Network Graphics (Read, Write)
format "pgm" - Portable Network Graphics (Read, Write)
format "ppm" - Portable Network Graphics (Read, Write)
format "psd" - PhotoShop (Read)
format "sgi" - Silicon Graphics (Read, Write)
format "rgb" - Silicon Graphics (Read, Write)
format "bw" - Silicon Graphics (Read, Write)
format "rgba" - Silicon Graphics (Read, Write)
format "tga" - Targa (Read, Write)
format "wal" - Quake2 Texture (Read)
format "mov" - Quicktime Movie (AttributeRead, Read, Write, AudioRead, AudioWrite)
         encode parameters
            timescale quicktime playback timescale override
            duration quicktime playback duration override
   image codecs: 
      8BPS (Apple Planar RGB)
      SVQ1 (Sorenson Video(TM) Compressor)
      SVQ3 (Sorenson Video 3 Compressor)
      WRLE (Apple BMP)
      apch (Apple ProRes)
      avc1 (H.264)
      cvid (Apple Cinepak)
      dvc  (Apple DV/DVCPRO - NTSC)
      dvcp (Apple DV - PAL)
      dvpp (Apple DVCPRO - PAL)
      h261 (Apple H.261)
      h263 (H.263)
      jpeg (Apple Photo - JPEG)
         encode parameters
            gama include gama atom in output movie (default=false)
      mjp2 (JPEG 2000 Encoder)
      mjpa (Apple Motion JPEG A)
      mjpb (Apple Motion JPEG B)
      mp4v (Apple MPEG4 Compressor)
      png  (Apple PNG)
      raw  (Apple None)
      rle  (Apple Animation)
      rpza (Apple Video)
      smc  (Apple Graphics)
      tga  (Apple TGA)
      tiff (Apple TIFF)
      yuv2 (Apple Component Video - YUV422)

   audio codecs: 
      lpcm (Linear PCM)
      alaw (A-Law 2:1)
      aac  (AAC)
      samr (AMR Narrowband)
      alac (Apple Lossless)
      ima4 (IMA 4:1)
      MAC3 (MACE 3:1)
      MAC6 (MACE 6:1)
      QDM2 (QDesign Music 2)
      Qclp (Qualcomm PureVoiceâ¢)
      ilbc (iLBC)
      ulaw (Âµ-Law 2:1)

format "qt" - Quicktime Movie (AttributeRead, Read, Write, AudioRead, AudioWrite)
         encode parameters
            timescale quicktime playback timescale override
            duration quicktime playback duration override
   image codecs: 
      8BPS (Apple Planar RGB)
      SVQ1 (Sorenson Video(TM) Compressor)
      SVQ3 (Sorenson Video 3 Compressor)
      WRLE (Apple BMP)
      apch (Apple ProRes)
      avc1 (H.264)
      cvid (Apple Cinepak)
      dvc  (Apple DV/DVCPRO - NTSC)
      dvcp (Apple DV - PAL)
      dvpp (Apple DVCPRO - PAL)
      h261 (Apple H.261)
      h263 (H.263)
      jpeg (Apple Photo - JPEG)
         encode parameters
            gama include gama atom in output movie (default=false)
      mjp2 (JPEG 2000 Encoder)
      mjpa (Apple Motion JPEG A)
      mjpb (Apple Motion JPEG B)
      mp4v (Apple MPEG4 Compressor)
      png  (Apple PNG)
      raw  (Apple None)
      rle  (Apple Animation)
      rpza (Apple Video)
      smc  (Apple Graphics)
      tga  (Apple TGA)
      tiff (Apple TIFF)
      yuv2 (Apple Component Video - YUV422)

   audio codecs: 
      lpcm (Linear PCM)
      alaw (A-Law 2:1)
      aac  (AAC)
      samr (AMR Narrowband)
      alac (Apple Lossless)
      ima4 (IMA 4:1)
      MAC3 (MACE 3:1)
      MAC6 (MACE 6:1)
      QDM2 (QDesign Music 2)
      Qclp (Qualcomm PureVoiceâ¢)
      ilbc (iLBC)
      ulaw (Âµ-Law 2:1)

format "avi" - Windows Movie (AttributeRead, Read, Write, AudioRead, AudioWrite)
   image codecs: 
      8BPS (Apple Planar RGB)
      SVQ1 (Sorenson Video(TM) Compressor)
      SVQ3 (Sorenson Video 3 Compressor)
      WRLE (Apple BMP)
      avc1 (H.264)
      cvid (Apple Cinepak)
      dvc  (Apple DV/DVCPRO - NTSC)
      dvcp (Apple DV - PAL)
      dvpp (Apple DVCPRO - PAL)
      h261 (Apple H.261)
      h263 (H.263)
      jpeg (Apple Photo - JPEG)
      mjp2 (JPEG 2000 Encoder)
      mjpa (Apple Motion JPEG A)
      mjpb (Apple Motion JPEG B)
      mp4v (Apple MPEG4 Compressor)
      png  (Apple PNG)
      raw  (Apple None)
      rle  (Apple Animation)
      rpza (Apple Video)
      smc  (Apple Graphics)
      tga  (Apple TGA)
      tiff (Apple TIFF)
      yuv2 (Apple Component Video - YUV422)

   audio codecs: 
      lpcm (Linear PCM)
      alaw (A-Law 2:1)
      aac  (AAC)
      samr (AMR Narrowband)
      alac (Apple Lossless)
      ima4 (IMA 4:1)
      MAC3 (MACE 3:1)
      MAC6 (MACE 6:1)
      QDM2 (QDesign Music 2)
      Qclp (Qualcomm PureVoiceâ¢)
      ilbc (iLBC)
      ulaw (Âµ-Law 2:1)

format "mp4" - MPEG-4 Movie (AttributeRead, Read, Write, AudioRead, AudioWrite)
   image codecs: 
      8BPS (Apple Planar RGB)
      SVQ1 (Sorenson Video(TM) Compressor)
      SVQ3 (Sorenson Video 3 Compressor)
      WRLE (Apple BMP)
      avc1 (H.264)
      cvid (Apple Cinepak)
      dvc  (Apple DV/DVCPRO - NTSC)
      dvcp (Apple DV - PAL)
      dvpp (Apple DVCPRO - PAL)
      h261 (Apple H.261)
      h263 (H.263)
      jpeg (Apple Photo - JPEG)
      mjp2 (JPEG 2000 Encoder)
      mjpa (Apple Motion JPEG A)
      mjpb (Apple Motion JPEG B)
      mp4v (Apple MPEG4 Compressor)
      png  (Apple PNG)
      raw  (Apple None)
      rle  (Apple Animation)
      rpza (Apple Video)
      smc  (Apple Graphics)
      tga  (Apple TGA)
      tiff (Apple TIFF)
      yuv2 (Apple Component Video - YUV422)

   audio codecs: 
      lpcm (Linear PCM)
      alaw (A-Law 2:1)
      aac  (AAC)
      samr (AMR Narrowband)
      alac (Apple Lossless)
      ima4 (IMA 4:1)
      MAC3 (MACE 3:1)
      MAC6 (MACE 6:1)
      QDM2 (QDesign Music 2)
      Qclp (Qualcomm PureVoiceâ¢)
      ilbc (iLBC)
      ulaw (Âµ-Law 2:1)

format "dv" - Digial Video (DV) Movie (AttributeRead, Read, Write, AudioRead, AudioWrite)
   image codecs: 
      8BPS (Apple Planar RGB)
      SVQ1 (Sorenson Video(TM) Compressor)
      SVQ3 (Sorenson Video 3 Compressor)
      WRLE (Apple BMP)
      avc1 (H.264)
      cvid (Apple Cinepak)
      dvc  (Apple DV/DVCPRO - NTSC)
      dvcp (Apple DV - PAL)
      dvpp (Apple DVCPRO - PAL)
      h261 (Apple H.261)
      h263 (H.263)
      jpeg (Apple Photo - JPEG)
      mjp2 (JPEG 2000 Encoder)
      mjpa (Apple Motion JPEG A)
      mjpb (Apple Motion JPEG B)
      mp4v (Apple MPEG4 Compressor)
      png  (Apple PNG)
      raw  (Apple None)
      rle  (Apple Animation)
      rpza (Apple Video)
      smc  (Apple Graphics)
      tga  (Apple TGA)
      tiff (Apple TIFF)
      yuv2 (Apple Component Video - YUV422)

   audio codecs: 
      lpcm (Linear PCM)
      alaw (A-Law 2:1)
      aac  (AAC)
      samr (AMR Narrowband)
      alac (Apple Lossless)
      ima4 (IMA 4:1)
      MAC3 (MACE 3:1)
      MAC6 (MACE 6:1)
      QDM2 (QDesign Music 2)
      Qclp (Qualcomm PureVoiceâ¢)
      ilbc (iLBC)
      ulaw (Âµ-Law 2:1)

format "3gp" - 3GP Phone Movie (AttributeRead, Read, Write, AudioRead, AudioWrite)
   image codecs: 
      8BPS (Apple Planar RGB)
      SVQ1 (Sorenson Video(TM) Compressor)
      SVQ3 (Sorenson Video 3 Compressor)
      WRLE (Apple BMP)
      avc1 (H.264)
      cvid (Apple Cinepak)
      dvc  (Apple DV/DVCPRO - NTSC)
      dvcp (Apple DV - PAL)
      dvpp (Apple DVCPRO - PAL)
      h261 (Apple H.261)
      h263 (H.263)
      jpeg (Apple Photo - JPEG)
      mjp2 (JPEG 2000 Encoder)
      mjpa (Apple Motion JPEG A)
      mjpb (Apple Motion JPEG B)
      mp4v (Apple MPEG4 Compressor)
      png  (Apple PNG)
      raw  (Apple None)
      rle  (Apple Animation)
      rpza (Apple Video)
      smc  (Apple Graphics)
      tga  (Apple TGA)
      tiff (Apple TIFF)
      yuv2 (Apple Component Video - YUV422)

   audio codecs: 
      lpcm (Linear PCM)
      alaw (A-Law 2:1)
      aac  (AAC)
      samr (AMR Narrowband)
      alac (Apple Lossless)
      ima4 (IMA 4:1)
      MAC3 (MACE 3:1)
      MAC6 (MACE 6:1)
      QDM2 (QDesign Music 2)
      Qclp (Qualcomm PureVoiceâ¢)
      ilbc (iLBC)
      ulaw (Âµ-Law 2:1)

format "pdf" -  (AttributeRead, Read)
format "gif" -  (AttributeRead, Read)
format "aiff" - Apple AIFF audio file (AudioRead, AudioWrite)
format "aif" - Apple AIFF audio file (AudioRead, AudioWrite)
format "aifc" - Apple AIFC compressed audio file (AudioRead, AudioWrite)
format "wav" - Microsoft WAVE audio file (AudioRead, AudioWrite)
format "snd" - NeXT audio file (AudioRead, AudioWrite)
format "au" - SUN Micosystems audio file (AudioRead, AudioWrite)
format "stdinfb" -  (AttributeRead, Read)
"""
