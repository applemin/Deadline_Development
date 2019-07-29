## ------------------------------------------------------------
## DJVSubmission.py
## Created March 06, 2011
## Updated June 29, 2015
## 
## DJV Job Submission to Deadline Queue System
## Command Line Utility to convert image sequences and create QuickTime Movies from image sequences including RPF & OpenEXR File Formats
## Tested with Windows 7 and potentially 'compatible' with any other Windows OS
## ------------------------------------------------------------
## NOTES:
## "-io openexr thread count (value)" General OpenEXR Option does not work, so have disabled it for now.
## ------------------------------------------------------------
import clr
import os

from System.Collections.Specialized import *
from System.IO import *
from System import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

# For Integration UI
import imp
imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
startup = True
DJVJob = False

ProjectManagementOptions = ["Shotgun","FTrack","NIM"]
DraftRequested = True

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global startup
    global DJVJob
    global DJVJobName
    global DJVJobFrames
    global integration_dialog
    
    tabHeight = 445
    tabWidth = 640
    GroupBoxWidth = 32
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit DJV Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'DJV' ) )
    
    scriptDialog.AddTabControl( "Tabs", tabWidth, tabHeight )
    
    scriptDialog.AddTabPage( "Job Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0,0, colSpan=4 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "DJV Job", 2, 1 )
    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 2, 2, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 2, 3 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )
    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 1, 2, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 1, 3 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )
    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 2, 2, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 2, 3 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 3, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 3, 1 )
    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 3, 2, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering. ", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 3, 3 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 4, 0, "The number of minutes a slave has to render a task for this job before it re-queues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 4, 2, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 4, 3 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 5, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 5, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist.", False )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "DJV Version", 6, 0, "The version of djv_convert.exe to process with.", False )
    VersionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "110", ("082","083","090","101","110"), 6, 1 )
    VersionBox.ValueModified.connect(VersionModified)
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 6, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render. ", False )

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 7, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 7, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Input / Output Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input Images / Movie", 1, 0, "The frames you would like to generate an image sequence or QuickTime from. If a sequence of frames exist in the same folder, Deadline will automatically collect the range of the frames and will set the Frame Range accordingly.", False )
    inputBox = scriptDialog.AddSelectionControlToGrid( "InputBox", "FileBrowserControl", "All Files (*)", "All Files (*);;Cineon (.cin);;DPX (.dpx);;IFF (.iff);;Z (.z);;IFL (.ifl);;LUT (.lut);;1DL (.1dl);;PIC (.pic);;PPM (.ppm);;PNM (.pnm);;PGM (.pgm);;PBM (.pbm);;RLA (.rla);;RPF (.rpf);;SGI (.sgi);;RGBA (.rgba);;RGB (.rgb);;BW (.bw);;Targa (.tga);;JPEG (.jpeg);;JPG (.jpg);;JFIF (.jfif);;OpenEXR (.exr);;PNG (.png);;QuickTime (.qt);;QuickTime (.mov);;QuickTime (.avi)|*.avi|QuickTime (.mp4);;TIFF (.tiff);;TIF (.tif);;VLUT (.vlut)", 1, 1, colSpan=3 )
    inputBox.ValueModified.connect(InputImagesModified)

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Images / Movie", 2, 0, "The name of the output image sequence or QuickTime to be generated.", False )
    outputBox = scriptDialog.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "All Files (*)", "All Files (*);;Cineon (.cin);;DPX (.dpx);;IFF (.iff);;IFL (.ifl);;LUT (.lut);;1DL (.1dl);;PIC (.pic);;PPM (.ppm);;PNM (.pnm);;PGM (.pgm);;PBM (.pbm);;RLA (.rla);;RPF (.rpf);;SGI (.sgi);;RGBA (.rgba);;RGB (.rgb);;BW (.bw);;Targa (.tga);;JPEG (.jpeg);;JPG (.jpg);;JFIF (.jfif);;OpenEXR (.exr);;PNG (.png);;QuickTime (.qt);;QuickTime (.mov);;Windows AVI (.avi);;MPEG-4 (.mp4);;TIFF (.tiff);;TIF (.tif);;VLUT (.vlut)", 2, 1, colSpan=3 )
    outputBox.ValueModified.connect(OutputImagesModified)

    scriptDialog.AddControlToGrid( "StartFrameLabel", "LabelControl", "Start Frame", 3, 0, "The first frame of the input sequence. Default: 0", False )
    startFrameBox = scriptDialog.AddRangeControlToGrid( "StartFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 1 )
    startFrameBox.ValueModified.connect(FrameRangeModified)
    scriptDialog.AddControlToGrid( "EndFrameLabel", "LabelControl", "End Frame", 3, 2, "The last frame of the input sequence. Default: 0", False )
    endFrameBox = scriptDialog.AddRangeControlToGrid( "EndFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 3 )
    endFrameBox.ValueModified.connect(FrameRangeModified)

    scriptDialog.EndGrid()
    
    ## General Image Options:
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SeparatorGIO", "SeparatorControl", "General Image Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "TimeUnitsLabel", "LabelControl", "Time Units", 1, 0, "Choose to use either Frames or Timecode as the units of Time. Default: frames", False )
    scriptDialog.AddComboControlToGrid( "TimeUnitsBox", "ComboControl", "frames", ("timecode","frames"), 1, 1 )
    scriptDialog.AddControlToGrid( "FrameRateLabel", "LabelControl", "Frame Rate (seconds)", 1, 2, "The frame rate of the image output or QuickTime. Default: default", False )
    scriptDialog.AddComboControlToGrid( "FrameRateBox", "ComboControl", "default", ("default","1","3","6","12","15","16","18","23.98","24","25","29.97","30","50","59.94","60","120"), 1, 3 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    ## Input Options:
    scriptDialog.AddTabPage( "Input Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Input", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "InputLayerLabel", "LabelControl", "Input Layer", 1, 0, "Specify an input layer (EXR - Choose a particular channel as the input). Default: none", False )
    scriptDialog.AddControlToGrid( "InputLayerBox", "TextControl", "", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ProxyScaleLabel", "LabelControl", "Proxy Scale", 2, 0, "Choose the Proxy scale of the input footage. Default: none", False )
    scriptDialog.AddComboControlToGrid( "ProxyScaleBox", "ComboControl", "none", ("none","1/2","1/4","1/8"), 2, 1 )

    scriptDialog.AddControlToGrid( "InputStartFrameLabel", "LabelControl", "Input Start Frame", 3, 0, "Choose the Start Frame of the Input Footage. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "InputStartFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 1 )
    scriptDialog.AddControlToGrid( "InputEndFrameLabel", "LabelControl", "Input End Frame", 3, 2, "Choose the End Frame of the Input Footage. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "InputEndFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 3 )	

    scriptDialog.AddControlToGrid( "SlateInputLabel", "LabelControl", "Slate Input File", 4, 0, "Choose an Image file to be used as the Slate. Default: none", False )
    SlateInputFile = scriptDialog.AddSelectionControlToGrid( "SlateInputBox", "FileBrowserControl", "", "All Files (*)", 4, 1, colSpan=3 )
    SlateInputFile.ValueModified.connect(SlateInputFileModified)

    scriptDialog.AddControlToGrid( "SlateFrameLabel", "LabelControl", "Slate Input Frame", 5, 0, "Specify the Start Frame of the Slate File if declared. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "SlateFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 5, 1 )	

    scriptDialog.AddControlToGrid( "InputImageTimeoutLabel", "LabelControl", "Input Image Timeout", 6, 0, "Maximum number of seconds to wait for each input frame. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "InputImageTimeoutBox", "RangeControl", 0, 0, 1000, 0, 1, 6, 1 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    ## Output Options:
    scriptDialog.AddTabPage( "Output Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Output", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PixelTypeLabel", "LabelControl", "Pixel Type", 1, 0, "Convert pixel type (rgba f32 = RGBA, float 32bit image). Default: default", False )
    scriptDialog.AddComboControlToGrid( "PixelTypeBox", "ComboControl", "default", ("default","l u8","l u16","l f16","l f32","la u8","la u16","la f16","la f32","rgb u8","rgb u10","rgb u16","rgb f16","rgb f32","rgba u8","rgba u16","rgba f16","rgba f32"), 1, 1 )
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 1, 2 )

    scriptDialog.AddControlToGrid( "OutputFrameRateLabel", "LabelControl", "Frame Rate (seconds)", 2, 0, "Force an Output Frame Rate. Default: default", False )
    scriptDialog.AddComboControlToGrid( "OutputFrameRateBox", "ComboControl", "default", ("default","1","3","6","12","15","16","18","23.98","24","25","29.97","30","50","59.94","60","120"), 2, 1 )

    scriptDialog.AddControlToGrid( "SeparatorImageTag", "SeparatorControl", "Custom Image Tag", 3, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "ImageTagNameLabel", "LabelControl", "Image Tag Name", 4, 0, "Generate an Image Tag(s). Default: none", False )
    scriptDialog.AddControlToGrid( "ImageTagNameBox", "TextControl", "", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ImageTagValueLabel", "LabelControl", "Image Tag Value", 5, 0, "Assign an Image Tag(s) Value per Image Tag(s). Default: none", False )
    scriptDialog.AddControlToGrid( "ImageTagValueBox", "TextControl", "", 5, 1, colSpan=3 )

    scriptDialog.AddSelectionControlToGrid( "AutoGenerateTagsBox", "CheckBoxControl", False, "Automatically Generate Image Tags (timecode)", 6, 0, "Automatically generate image tags (e.g., timecode). Default: False", colSpan=3 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    ## LOAD File Format Options:
    scriptDialog.AddTabPage( "LOAD" )
    
    ## OpenGL
    scriptDialog.AddGroupBox( "GroupBoxL1", "OpenGL Options", True ).toggled.connect(GroupBoxL1Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "RendererLabel", "LabelControl", "Renderer", 0, 0, "OpenGL Renderer Version to Use. Default: opengl 2.0", False )
    scriptDialog.AddComboControlToGrid( "RendererBox", "ComboControl", "opengl 2.0", ("opengl 2.0","opengl 1.2"), 0, 1 )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer1", 0, 2 )

    scriptDialog.AddControlToGrid( "SeparatorRenderFilter", "SeparatorControl", "Render Filter", 1, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "RenderFilterMinLabel", "LabelControl", "Minify", 2, 0, "Render Filter - Minify. Default: linear", False )
    scriptDialog.AddComboControlToGrid( "RenderFilterMinBox", "ComboControl", "linear", ("nearest","linear","box","triangle","bell","b-spline","lanczos3","cubic","mitchell"), 2, 1 )
    scriptDialog.AddControlToGrid( "RenderFilterMagLabel", "LabelControl", "Magnify", 2, 2, "Render Filter - Magnify. Default: nearest", False )
    scriptDialog.AddComboControlToGrid( "RenderFilterMagBox", "ComboControl", "nearest", ("nearest","linear","box","triangle","bell","b-spline","lanczos3","cubic","mitchell"), 2, 3 )

    scriptDialog.AddControlToGrid( "OffscreenBufferLabel", "LabelControl", "Offscreen Buffer", 3, 0, "Render Offscreen Buffer. Default: fbo", False )
    scriptDialog.AddComboControlToGrid( "OffscreenBufferBox", "ComboControl", "fbo", ("pbuffer","fbo"), 3, 1 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )
    
    ## OpenEXR
    scriptDialog.AddGroupBox( "GroupBoxL2", "OpenEXR Options", True ).toggled.connect(GroupBoxL2Toggled)
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "ColorProfileLabel", "LabelControl", "Color Profile", 0, 0, "Load OpenEXR Color Profile. Default: gamma", False )
    scriptDialog.AddComboControlToGrid( "ColorProfileBox", "ComboControl", "gamma", ("none","gamma","exposure"), 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupEXRHSpacer1", 0, 2 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "EXRGammaLabel", "LabelControl", "Gamma Value", 0, 0, "Load OpenEXR Gamma Value. Default: 2.2", False )
    scriptDialog.AddRangeControlToGrid( "EXRGammaBox", "SliderControl", 2.2, 0.1, 4, 1, 0.1, 0, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "SeparatorExposure", "SeparatorControl", "Exposure", 1, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "EXRValueLabel", "LabelControl", "Value", 2, 0, "Load OpenEXR Exposure Value. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "EXRValueBox", "SliderControl", 0, -10, 10, 3, 0.1, 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "EXRDefogLabel", "LabelControl", "Defog", 3, 0, "Load OpenEXR Exposure Value - Defog. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "EXRDefogBox", "SliderControl", 0, 0, 0.01, 3, 0.001, 3, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "EXRKneeLowLabel", "LabelControl", "Knee low", 4, 0, "Load OpenEXR Exposure Value - Knee Low. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "EXRKneeLowBox", "SliderControl", 0, -3, 3, 3, 0.1, 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "EXRKneeHighLabel", "LabelControl", "Knee high", 5, 0, "Load OpenEXR Exposure Value - Knee High. Default: 5", False )
    scriptDialog.AddRangeControlToGrid( "EXRKneeHighBox", "SliderControl", 5, 3.5, 7.5, 3, 0.1, 5, 1, colSpan=3 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "EXRChannelsLabel", "LabelControl", "EXR Channels", 0, 0, "Load OpenEXR Channels. Default: group known", False )
    scriptDialog.AddComboControlToGrid( "EXRChannelsBox", "ComboControl", "group known", ("group none","group known","group all"), 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupEXRHSpacer2", 0, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )
    
    ## Cineon
    scriptDialog.AddGroupBox( "GroupBoxL3", "Cineon Options", True ).toggled.connect(GroupBoxL3Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "CineonLoadColorProfileLabel", "LabelControl", "Color Profile", 0, 0, "Load Cineon Color Profile. Default: auto", False )
    scriptDialog.AddComboControlToGrid( "CineonLoadColorProfileBox", "ComboControl", "auto", ("auto","none","film print"), 0, 1, expand=False )	
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer2", 0, 2 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SeparatorCineonLoadFilmPrint", "SeparatorControl", "Film Print", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "CineonLoadBlackLabel", "LabelControl", "Black", 1, 0, "Load Cineon Film Print - Black. Default: 95", False )
    scriptDialog.AddRangeControlToGrid( "CineonLoadBlackBox", "SliderControl", 95, 0, 1023, 0, 1, 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "CineonLoadWhiteLabel", "LabelControl", "White", 2, 0, "Load Cineon Film Print - White. Default: 685", False )
    scriptDialog.AddRangeControlToGrid( "CineonLoadWhiteBox", "SliderControl", 685, 0, 1023, 0, 1, 2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "CineonLoadGammaLabel", "LabelControl", "Gamma", 3, 0, "Load Cineon Film Print - Gamma. Default: 1.7", False )
    scriptDialog.AddRangeControlToGrid( "CineonLoadGammaBox", "SliderControl", 1.7, 0.1, 4, 1, 0.1, 3, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "CineonLoadSoftClipLabel", "LabelControl", "Soft Clip", 4, 0, "Load Cineon Film Print - Soft Clip. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "CineonLoadSoftClipBox", "SliderControl", 0, 0, 50, 0, 1, 4, 1, colSpan=2 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "CineonLoadConvertLabel", "LabelControl", "Convert", 0, 0, "Load Cineon Conversion. Default: none", False )
    scriptDialog.AddComboControlToGrid( "CineonLoadConvertBox", "ComboControl", "none", ("none","u8","u16"), 0, 1, expand=False )	
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer3", 0, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )	

    ## DPX
    scriptDialog.AddGroupBox( "GroupBoxL4", "DPX Options", True ).toggled.connect(GroupBoxL4Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "DPXColorProfileLabel", "LabelControl", "Color Profile", 0, 0, "Load DPX Color Profile. Default: auto", False )
    scriptDialog.AddComboControlToGrid( "DPXColorProfileBox", "ComboControl", "auto", ("auto","none","film print"), 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer4", 0, 2 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SeparatorDPXFilmPrint", "SeparatorControl", "Film Print", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "DPXBlackLabel", "LabelControl", "Black", 1, 0, "Load DPX Film Print - Black. Default: 95", False )
    scriptDialog.AddRangeControlToGrid( "DPXBlackBox", "SliderControl", 95, 0, 1023, 0, 1, 1, 1 )

    scriptDialog.AddControlToGrid( "DPXWhiteLabel", "LabelControl", "White", 2, 0, "Load DPX Film Print - White. Default: 685", False )
    scriptDialog.AddRangeControlToGrid( "DPXWhiteBox", "SliderControl", 685, 0, 1023, 0, 1, 2, 1 )

    scriptDialog.AddControlToGrid( "DPXGammaLabel", "LabelControl", "Gamma", 3, 0, "Load DPX Film Print - Gamma. Default: 1.7", False )
    scriptDialog.AddRangeControlToGrid( "DPXGammaBox", "SliderControl", 1.7, 0.1, 4, 1, 0.1, 3, 1 )

    scriptDialog.AddControlToGrid( "DPXSoftClipLabel", "LabelControl", "Soft Clip", 4, 0, "Load DPX Film Print - Soft Clip. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "DPXSoftClipBox", "SliderControl", 0, 0, 50, 0, 1, 4, 1 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "DPXConvertLabel", "LabelControl", "Convert", 0, 0, "Load DPX Conversion. Default:  none", False )
    scriptDialog.AddComboControlToGrid( "DPXConvertBox", "ComboControl", "none", ("none","u8","u16"), 0, 1, expand=False)
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer5", 0, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )
    
    ## LUT
    scriptDialog.AddGroupBox( "GroupBoxL5", "LUT Options", True ).toggled.connect(GroupBoxL5Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "LUTFileLoadFormatLabel", "LabelControl", "File Format", 0, 0, "Load LUT File format. Default: auto", False )
    scriptDialog.AddComboControlToGrid( "LUTFileLoadFormatBox", "ComboControl", "auto", ("auto","inferno","kodak"), 0, 1, expand=False )	
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer6", 0, 2 )
    
    scriptDialog.AddControlToGrid( "LUTFileLoadTypeLabel", "LabelControl", "File Type", 1, 0, "Load LUT File Type. Default: auto", False )
    scriptDialog.AddComboControlToGrid( "LUTFileLoadTypeBox", "ComboControl", "auto", ("auto","u8","u10","u16"), 1, 1, expand=False )	
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )	
    
    ## QuickTime
    scriptDialog.AddGroupBox( "GroupBoxL6", "QuickTime Options", True ).toggled.connect(GroupBoxL6Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "QTStartFrameLabel", "LabelControl", "Start Frame", 0, 0, "Load QuickTime Start Frame. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "QTStartFrameBox", "RangeControl", 0, 0, 1000000, 0, 1, 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer7", 0, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )
    scriptDialog.EndTabPage()
    
    ## SAVE File Format Options:
    scriptDialog.AddTabPage( "SAVE" )
    
    ## OpenEXR
    scriptDialog.AddGroupBox( "GroupBoxS1", "OpenEXR Options", True ).toggled.connect(GroupBoxS1Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "EXRFileCompressionLabel", "LabelControl", "Compression Type", 0, 0, "Save OpenEXR Compression. Default: none", False )
    EXRCompressionTypeBox = scriptDialog.AddComboControlToGrid( "EXRCompressionTypeBox", "ComboControl", "none", ("none","rle", "zips", "zip", "piz", "pxr24", "b44", "b44a", "dwaa", "dwab"), 0, 1, expand=False )
    EXRCompressionTypeBox.ValueModified.connect(EXRCompressionTypeModified)
    scriptDialog.AddControlToGrid( "EXRFileCompressionLevelLabel", "LabelControl", "DWA Compression Level", 1, 0, "Dreamworks Animation DWAA/DWAB Compression Level", False)
    scriptDialog.AddRangeControlToGrid( "EXRCompressionLevelBox", "RangeControl", 45, 0, 100, 0, 1, 1, 1 )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer8", 1, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )
    
    ## Cineon
    scriptDialog.AddGroupBox( "GroupBoxS2", "Cineon Options", True ).toggled.connect(GroupBoxS2Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "CineonSaveColorProfileLabel", "LabelControl", "Cineon Color Profile", 0, 0, "Save Cineon Color Profile. Default: film print", False )
    scriptDialog.AddComboControlToGrid( "CineonSaveColorProfileBox", "ComboControl", "film print", ("film print","auto", "none"), 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer9", 0, 2 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SeparatorCineonSaveFilmPrint", "SeparatorControl", "Film Print", 0, 0, colSpan=2)

    scriptDialog.AddControlToGrid( "CineonSaveBlackLabel", "LabelControl", "Black", 1, 0, "Save Cineon Film Print - Black. Default: 95", False )
    scriptDialog.AddRangeControlToGrid( "CineonSaveBlackBox", "SliderControl", 95, 0, 1023, 0, 1, 1, 1 )

    scriptDialog.AddControlToGrid( "CineonSaveWhiteLabel", "LabelControl", "White", 2, 0, "Save Cineon Film Print - White. Default: 685", False )
    scriptDialog.AddRangeControlToGrid( "CineonSaveWhiteBox", "SliderControl", 685, 0, 1023, 0, 1, 2, 1 )

    scriptDialog.AddControlToGrid( "CineonSaveGammaLabel", "LabelControl", "Gamma", 3, 0, "Save Cineon Film Print - Gamma. Default: 1.7", False )
    scriptDialog.AddRangeControlToGrid( "CineonSaveGammaBox", "SliderControl", 1.7, 0.1, 4, 1, 0.1, 3, 1 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )	

    ## DPX
    scriptDialog.AddGroupBox( "GroupBoxS3", "DPX Options", True ).toggled.connect(GroupBoxS3Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "DPXSaveColorProfileLabel", "LabelControl", "DPX Color Profile", 0, 0, "Save DPX Color Profile. Default: film print", False )
    scriptDialog.AddComboControlToGrid( "DPXSaveColorProfileBox", "ComboControl", "film print", ("film print","auto", "none"), 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer10", 0, 2 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SeparatorDPXSaveFilmPrint", "SeparatorControl", "Film Print", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "DPXSaveBlackLabel", "LabelControl", "Black", 1, 0, "Save DPX Film Print - Black. Default: 95", False )
    scriptDialog.AddRangeControlToGrid( "DPXSaveBlackBox", "SliderControl", 95, 0, 1023, 0, 1, 1, 1 )

    scriptDialog.AddControlToGrid( "DPXSaveWhiteLabel", "LabelControl", "White", 2, 0, "Save DPX Film Print - White. Default: 685", False )
    scriptDialog.AddRangeControlToGrid( "DPXSaveWhiteBox", "SliderControl", 685, 0, 1023, 0, 1, 2, 1 )

    scriptDialog.AddControlToGrid( "DPXSaveGammaLabel", "LabelControl", "Gamma", 3, 0, "Save DPX Film Print - Gamma. Default: 1.7", False )
    scriptDialog.AddRangeControlToGrid( "DPXSaveGammaBox", "SliderControl", 1.7, 0.1, 4, 1, 0.1, 3, 1 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "DPXSaveFileVersionLabel", "LabelControl", "DPX File Version", 0, 0, "Save DPX File Version. Default: 2.0", False )
    scriptDialog.AddComboControlToGrid( "DPXSaveFileVersionBox", "ComboControl", "2.0", ("1.0","2.0"), 0, 1 )
    scriptDialog.AddControlToGrid( "DPXSaveFileTypeLabel", "LabelControl", "DPX File Type", 0, 2, "Save DPX File Type. Default: u10", False )
    scriptDialog.AddComboControlToGrid( "DPXSaveFileTypeBox", "ComboControl", "u10", ("auto","u10"), 0, 3 )
	
    scriptDialog.AddControlToGrid( "DPXSaveFileEndianLabel", "LabelControl", "DPX File Endian", 1, 0, "Save DPX File Endian. Default: msb", False )
    scriptDialog.AddComboControlToGrid( "DPXSaveFileEndianBox", "ComboControl", "msb", ("auto","msb","lsb"), 1, 1 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )

    ## IFF
    scriptDialog.AddGroupBox( "GroupBoxS4", "IFF Options", True ).toggled.connect(GroupBoxS4Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "IFFFileCompressionLabel", "LabelControl", "Compression Type", 0, 0, "Save IFF Compression. Default: rle", False )
    scriptDialog.AddComboControlToGrid( "IFFCompressionTypeBox", "ComboControl", "rle", ("none","rle"), 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer11", 0, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )	

    ## LUT
    scriptDialog.AddGroupBox( "GroupBoxS5", "LUT Options", True ).toggled.connect(GroupBoxS5Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "LUTFileSaveFormatLabel", "LabelControl", "File Format", 0, 0, "Save LUT File Format. Default: auto", False )
    scriptDialog.AddComboControlToGrid( "LUTFileSaveFormatBox", "ComboControl", "auto", ("auto","inferno","kodak"), 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer12", 0, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )	
    
    ## PPM
    scriptDialog.AddGroupBox( "GroupBoxS6", "PPM Options", True ).toggled.connect(GroupBoxS6Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "PPMFileTypeLabel", "LabelControl", "File Type", 0, 0, "Save PPM File Type. Default: auto", False )
    scriptDialog.AddComboControlToGrid( "PPMFileTypeBox", "ComboControl", "auto", ("auto","u1"), 0, 1 )
    scriptDialog.AddControlToGrid( "PPMFileDataLabel", "LabelControl", "File Data", 0, 2, "Save PPM File Data. Default: binary", False )
    scriptDialog.AddComboControlToGrid( "PPMFileDataBox", "ComboControl", "binary", ("ascii","binary"), 0, 3 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )	

    ## SGI
    scriptDialog.AddGroupBox( "GroupBoxS7", "SGI Options", True ).toggled.connect(GroupBoxS7Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SGIFileCompressionLabel", "LabelControl", "Compression Type", 0, 0, "Save SGI Compression. Default: none", expand=False )
    scriptDialog.AddComboControlToGrid( "SGICompressionTypeBox", "ComboControl", "none", ("none","rle"), 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer13", 0, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )	
    
    ## Targa
    scriptDialog.AddGroupBox( "GroupBoxS8", "Targa Options", True ).toggled.connect(GroupBoxS8Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "TGAFileCompressionLabel", "LabelControl", "Compression Type", 0, 0, "Save Targa Compression. Default: none", False )
    scriptDialog.AddComboControlToGrid( "TGACompressionTypeBox", "ComboControl", "none", ("none","rle"), 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer14", 0, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )	
    
    ## JPEG
    scriptDialog.AddGroupBox( "GroupBoxS9", "JPEG Options", True ).toggled.connect(GroupBoxS9Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "JPEGQualityLabel", "LabelControl", "Quality ( 0-100 )", 0, 0, "Save JPEG Quality [0 (lowest quality) - 100 (highest quality)]. Default: 100", False )
    scriptDialog.AddRangeControlToGrid( "JPEGQualityBox", "RangeControl", 100, 0, 100, 0, 1, 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer15", 0, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )	

    ## QuickTime
    scriptDialog.AddGroupBox( "GroupBoxS10", "QuickTime Options", True ).toggled.connect(GroupBoxS10Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "QTCodecLabel", "LabelControl", "QT Codec", 0, 0, "Save QuickTime Codec. Default: jpeg", False )
    scriptDialog.AddComboControlToGrid( "QTcodec", "ComboControl", "mjpeg-a", ("raw","jpeg","mjpeg-a","mjpeg-b","h263","h264","dvc-ntsc","dvc-pal"), 0, 1 )

    scriptDialog.AddControlToGrid( "QTLibQTCodecLabel", "LabelControl", "QT Lib Quicktime Codec (Linux only)", 1, 0, "QuickTime Codec using LibQuicktime (Linux Only). Default: mjpa", False )
    scriptDialog.AddComboControlToGrid( "QTLibQuicktimeCodecBox", "ComboControl", "mjpa", ( "rtjpeg", "raw", "rawalpha", "v308", "v408", "v410", "yuv2", "yuv4",
    "yv12", "2vuy", "v210", "yuvs", "jpeg", "mjpa", "png", "pngalpha", "ffmpeg_mpg4", "ffmpeg_msmpeg4v3", "ffmpeg_msmpeg4v3_wmp", "ffmpeg_h263", "ffmpeg_h263p", "ffmpeg_mjpg", "ffmpeg_rle",
    "ffmpeg_dv", "ffmpeg_dvcpro", "ffmpeg_dv50", "ffmpeg_ffvhuff", "ffmpeg_ffv1", "ffmpeg_dnxhd", "ffmpeg_imx" ), 1, 1 )

    scriptDialog.AddControlToGrid( "QTqualityLabel", "LabelControl", "QT Quality", 2, 0, "Save QuickTime Quality. Default: normal", False )
    scriptDialog.AddComboControlToGrid( "QTquality", "ComboControl", "normal", ("lossless","min","max","low","normal","high"), 2, 1 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )
    
    ## TIFF
    scriptDialog.AddGroupBox( "GroupBoxS11", "TIFF Options", True ).toggled.connect(GroupBoxS11Toggled)
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "TIFFFileCompressionLabel", "LabelControl", "Compression Type", 0, 0, "Save TIFF Compression. Default: none", expand=False )
    scriptDialog.AddComboControlToGrid( "TIFFCompressionTypeBox", "ComboControl", "none", ("none","rle","lzw"), 0, 1, expand=False )
    scriptDialog.AddHorizontalSpacerToGrid("GroupHSpacer16", 0, 2 )
    scriptDialog.EndGrid()
    scriptDialog.EndGroupBox( True, tabWidth - GroupBoxWidth )
    scriptDialog.EndTabPage()

    ## Image Transform Options:
    scriptDialog.AddTabPage( "Image Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SeparatorMirror", "SeparatorControl", "Mirror Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "MirrorImageLabel", "LabelControl", "Mirror Image", 1, 0, "Mirror the image horizontally or vertically. Default: none", False )
    scriptDialog.AddComboControlToGrid( "MirrorImage", "ComboControl", "none", ("none","mirror_h","mirror_v"), 1, 1 )

    scriptDialog.AddControlToGrid( "SeparatorScale", "SeparatorControl", "Scale Options", 2, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "ImageScalePercentageLabel", "LabelControl", "Scale Image %", 3, 0, "Scale the image by Percentage %. Default: 0", False )
    scriptDialog.AddComboControlToGrid( "ImageScalePercentage", "ComboControl", "0", ("0","10","20","30","40","50","60","70","80","90","100","200","300","400","500"), 3, 1 )

    scriptDialog.AddControlToGrid( "ImageScaleXLabel", "LabelControl", "Scale X", 4, 0, "Scale the image in X. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "ImageScaleXBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddControlToGrid( "ImageScaleYLabel", "LabelControl", "Scale Y", 4, 2, "Scale the image in Y. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "ImageScaleYBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 4, 3 )

    scriptDialog.AddControlToGrid( "SeparatorReSize", "SeparatorControl", "ReSize Options", 5, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "ImageReSizeWLabel", "LabelControl", "ReSize Width", 6, 0, "Resize the Image (Width). Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "ImageReSizeWBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 6, 1 )
    scriptDialog.AddControlToGrid( "ImageReSizeHLabel", "LabelControl", "ReSize Height", 6, 2, "Resize the Image (Height). Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "ImageReSizeHBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 6, 3 )

    scriptDialog.AddSelectionControlToGrid( "MaintainAspectRatioBox", "CheckBoxControl", False, "Maintain Aspect Ratio", 7, 0, "Maintain the Aspect Ration during ReSize. Default: False", False )

    scriptDialog.AddControlToGrid( "SeparatorCrop", "SeparatorControl", "Crop Options (DJV v1.0.1 or later)", 8, 0, colSpan=4)

    scriptDialog.AddControlToGrid( "ImageCropXLabel", "LabelControl", "Crop X", 9, 0, "Crop the image in X. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "ImageCropXBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 9, 1 )
    scriptDialog.AddControlToGrid( "ImageCropYLabel", "LabelControl", "Crop Y", 9, 2, "Crop the image in Y. Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "ImageCropYBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 9, 3 )

    scriptDialog.AddControlToGrid( "ImageCropWLabel", "LabelControl", "Crop Width", 10, 0, "Crop the Image (Width). Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "ImageCropWBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 10, 1 )
    scriptDialog.AddControlToGrid( "ImageCropHLabel", "LabelControl", "Crop Height", 10, 2, "Crop the Image (Height). Default: 0", False )
    scriptDialog.AddRangeControlToGrid( "ImageCropHBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 10, 3 )
    
    scriptDialog.AddSelectionControlToGrid( "CropPercentageBox", "CheckBoxControl", False, "Crop as Percentage", 11, 0, "Crop Image as Percentage. Default: False", False )

    scriptDialog.AddControlToGrid( "SeparatorImageChannels", "SeparatorControl", "Image Channels", 12, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "ImageChannelsLabel", "LabelControl", "Show Specific Channel", 13, 0, "Show only specific image channels. Default: default", False )
    scriptDialog.AddComboControlToGrid( "ImageChannels", "ComboControl", "default", ("default","red","green","blue","alpha"), 13, 1 )

    scriptDialog.AddControlToGrid( "SeparatorFileSequence", "SeparatorControl", "File Sequence Options (DJV v1.0.1 or later)", 14, 0, colSpan=4)

    scriptDialog.AddSelectionControlToGrid( "FileSequenceBox", "CheckBoxControl", False, "File Sequencing", 15, 0, "Set whether File Sequencing is Enabled. Default: False", False )

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "DJVMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()

    ResetButton = scriptDialog.AddControlToGrid("ResetButton","ButtonControl","Reset Settings", 0, 0, expand=False)
    ResetButton.ValueModified.connect(ResetButtonPressed)

    SaveButton = scriptDialog.AddControlToGrid( "SaveSettingsButton", "ButtonControl", "Save Settings", 0, 1, expand=False )
    SaveButton.ValueModified.connect(SaveSettingsButtonPressed)

    LoadButton = scriptDialog.AddControlToGrid( "LoadSettingsButton", "ButtonControl", "Load Settings", 0, 2, expand=False )
    LoadButton.ValueModified.connect(LoadSettingsButtonPressed)

    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer2", 0, 3 )

    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 4, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 5, expand=False )
    closeButton.ValueModified.connect(CloseButtonPressed)

    scriptDialog.EndGrid()
    
    settings = ("CategoryBox","CommentBox","DepartmentBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","LimitGroupBox","OnJobCompleteBox","MachineListBox","SubmitSuspendedBox","IsBlacklistBox",
    "VersionBox","TimeUnitsBox","FrameRateBox","InputLayerBox","ProxyScaleBox","InputStartFrameBox","InputEndFrameBox","SlateInputBox", "SlateFrameBox", "InputImageTimeoutBox",
    "PixelTypeBox", "OutputFrameRateBox","ImageTagNameBox","ImageTagValueBox", "AutoGenerateTagsBox","RendererBox", "RenderFilterMinBox", "RenderFilterMagBox",
    "OffscreenBufferBox","ColorProfileBox","EXRGammaBox","EXRValueBox", "EXRDefogBox", "EXRKneeLowBox","EXRKneeHighBox","EXRChannelsBox",
    "CineonLoadColorProfileBox","CineonLoadBlackBox","CineonLoadWhiteBox","CineonLoadGammaBox","CineonLoadSoftClipBox","CineonLoadConvertBox","DPXColorProfileBox",
    "DPXBlackBox","DPXWhiteBox","DPXGammaBox","DPXSoftClipBox","DPXConvertBox","LUTFileLoadFormatBox","LUTFileLoadTypeBox","QTStartFrameBox","EXRCompressionTypeBox","EXRCompressionLevelBox",
    "CineonSaveColorProfileBox","CineonSaveBlackBox","CineonSaveWhiteBox","CineonSaveGammaBox","DPXSaveColorProfileBox","DPXSaveBlackBox","DPXSaveWhiteBox",
    "DPXSaveGammaBox","DPXSaveFileVersionBox","DPXSaveFileTypeBox","DPXSaveFileEndianBox","IFFCompressionTypeBox","LUTFileSaveFormatBox","PPMFileTypeBox",
    "PPMFileDataBox","SGICompressionTypeBox","TGACompressionTypeBox","JPEGQualityBox", "QTcodec","QTquality","TIFFCompressionTypeBox", "MirrorImage","ImageScalePercentage",
    "ImageScaleXBox","ImageScaleYBox","ImageReSizeWBox","ImageReSizeHBox","MaintainAspectRatioBox","ImageCropXBox","ImageCropYBox",
    "ImageCropWBox","ImageCropHBox","CropPercentageBox","ImageChannels","FileSequenceBox","DraftTemplateBox", "DraftUserBox", "DraftEntityBox", "DraftVersionBox")
    
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    if len( args ) > 0:
        scriptDialog.SetValue( "InputBox", args[0] )
        scriptDialog.SetValue( "OutputBox", args[1] )
        scriptDialog.SetValue( "DependencyBox", args[2] )
        DJVJobName = args[3]
        DJVJobFrames = args[4]
        DJVJob = True
    
    VersionModified()
    InputImagesModified()
    OutputImagesModified()
    EXRCompressionTypeModified()

    startup = False

    scriptDialog.ShowDialog( len( args ) > 0 )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "DJVSettings.ini" )

def ToggleOtherLoadGroupBoxes(name):
    if name != "GroupBoxL1":
        scriptDialog.SetCollapsed("GroupBoxL1", True)
    if name != "GroupBoxL2":
        scriptDialog.SetCollapsed("GroupBoxL2", True)
    if name != "GroupBoxL3":
        scriptDialog.SetCollapsed("GroupBoxL3", True)
    if name != "GroupBoxL4":
        scriptDialog.SetCollapsed("GroupBoxL4", True)
    if name != "GroupBoxL5":
        scriptDialog.SetCollapsed("GroupBoxL5", True)
    if name != "GroupBoxL6":
        scriptDialog.SetCollapsed("GroupBoxL6", True)

def GroupBoxL1Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBoxL1")

def GroupBoxL2Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBoxL2")
        
def GroupBoxL3Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBoxL3")
        
def GroupBoxL4Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBoxL4")
        
def GroupBoxL5Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBoxL5")
        
def GroupBoxL6Toggled(toggled):
    if toggled:
        ToggleOtherLoadGroupBoxes("GroupBoxL6")

def ToggleOtherSaveGroupBoxes(name):
    if name != "GroupBoxS1":
        scriptDialog.SetCollapsed("GroupBoxS1", True)
    if name != "GroupBoxS2":
        scriptDialog.SetCollapsed("GroupBoxS2", True)
    if name != "GroupBoxS3":
        scriptDialog.SetCollapsed("GroupBoxS3", True)
    if name != "GroupBoxS4":
        scriptDialog.SetCollapsed("GroupBoxS4", True)
    if name != "GroupBoxS5":
        scriptDialog.SetCollapsed("GroupBoxS5", True)
    if name != "GroupBoxS6":
        scriptDialog.SetCollapsed("GroupBoxS6", True)
    if name != "GroupBoxS7":
        scriptDialog.SetCollapsed("GroupBoxS7", True)
    if name != "GroupBoxS8":
        scriptDialog.SetCollapsed("GroupBoxS8", True)
    if name != "GroupBoxS9":
        scriptDialog.SetCollapsed("GroupBoxS9", True)
    if name != "GroupBoxS10":
        scriptDialog.SetCollapsed("GroupBoxS10", True)
    if name != "GroupBoxS11":
        scriptDialog.SetCollapsed("GroupBoxS11", True)

def GroupBoxS1Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS1")

def GroupBoxS2Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS2")

def GroupBoxS3Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS3")

def GroupBoxS4Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS4")

def GroupBoxS5Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS5")

def GroupBoxS6Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS6")

def GroupBoxS7Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS7")

def GroupBoxS8Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS8")

def GroupBoxS9Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS9")

def GroupBoxS10Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS10")
        
def GroupBoxS11Toggled(toggled):
    if toggled:
        ToggleOtherSaveGroupBoxes("GroupBoxS11")

def CloseDialog():
    global scriptDialog
    global settings
    #scriptDialog.SaveSettings( GetSettingsFilename(), settings )
    scriptDialog.CloseDialog()
   
def CloseButtonPressed(*args):
    CloseDialog()

def ResetButtonPressed(*args):
    global scriptDialog

    result = scriptDialog.ShowMessageBox("Are you sure you want to reset ALL DJV Settings?","Warning : DJV Settings",("Yes","No"))

    if(result=="Yes"):
        scriptDialog.SetValue( "AutoGenerateTagsBox","False" )
        scriptDialog.SetValue( "CineonLoadBlackBox","95" )
        scriptDialog.SetValue( "CineonLoadColorProfileBox","auto" )
        scriptDialog.SetValue( "CineonLoadConvertBox","none" )
        scriptDialog.SetValue( "CineonLoadGammaBox",1.7 )
        scriptDialog.SetValue( "CineonLoadSoftClipBox","0" )
        scriptDialog.SetValue( "CineonLoadWhiteBox","685" )
        scriptDialog.SetValue( "CineonSaveBlackBox","95" )
        scriptDialog.SetValue( "CineonSaveColorProfileBox","film print" )
        scriptDialog.SetValue( "CineonSaveGammaBox","1.7" )
        scriptDialog.SetValue( "CineonSaveWhiteBox","685" )
        scriptDialog.SetValue( "ColorProfileBox","gamma" )
        scriptDialog.SetValue( "DepartmentBox","" )
        scriptDialog.SetValue( "DPXBlackBox","95" )
        scriptDialog.SetValue( "DPXColorProfileBox","auto" )
        scriptDialog.SetValue( "DPXConvertBox","none" )
        scriptDialog.SetValue( "DPXGammaBox","1.7" )
        scriptDialog.SetValue( "DPXSaveBlackBox","95" )
        scriptDialog.SetValue( "DPXSaveColorProfileBox","film print" )
        scriptDialog.SetValue( "DPXSaveFileEndianBox","msb" )
        scriptDialog.SetValue( "DPXSaveFileTypeBox","u10" )
        scriptDialog.SetValue( "DPXSaveFileVersionBox","2.0" )
        scriptDialog.SetValue( "DPXSaveGammaBox","1.7" )
        scriptDialog.SetValue( "DPXSaveWhiteBox","685" )
        scriptDialog.SetValue( "DPXSoftClipBox","0" )
        scriptDialog.SetValue( "DPXWhiteBox","685" )
        scriptDialog.SetValue( "EXRChannelsBox","group known" )
        scriptDialog.SetValue( "EXRCompressionTypeBox","none" )
        scriptDialog.SetValue( "EXRCompressionLevelBox", "45" )
        scriptDialog.SetValue( "EXRDefogBox","0" )
        scriptDialog.SetValue( "EXRGammaBox","2.2" )
        scriptDialog.SetValue( "EXRKneeHighBox","5" )
        scriptDialog.SetValue( "EXRKneeLowBox","0" )
        scriptDialog.SetValue( "EXRValueBox","0" )
        scriptDialog.SetValue( "FrameRateBox","default" )
        scriptDialog.SetValue( "GroupBox","none" )
        scriptDialog.SetValue( "IFFCompressionTypeBox","rle" )
        scriptDialog.SetValue( "ImageChannels","default" )
        scriptDialog.SetValue( "ImageReSizeHBox","0" )
        scriptDialog.SetValue( "ImageReSizeWBox","0" )
        scriptDialog.SetValue( "ImageScalePercentage","0" )
        scriptDialog.SetValue( "ImageScaleXBox","0" )
        scriptDialog.SetValue( "ImageScaleYBox","0" )
        scriptDialog.SetValue( "ImageTagNameBox","" )
        scriptDialog.SetValue( "ImageTagValueBox","" )
        scriptDialog.SetValue( "InputEndFrameBox","0" )
        scriptDialog.SetValue( "InputImageTimeoutBox","0" )
        scriptDialog.SetValue( "InputLayerBox","" )
        scriptDialog.SetValue( "InputStartFrameBox","0" )
        scriptDialog.SetValue( "IsBlacklistBox","False" )
        scriptDialog.SetValue( "JPEGQualityBox","100" )
        scriptDialog.SetValue( "LimitGroupBox","" )
        scriptDialog.SetValue( "LUTFileLoadFormatBox","auto" )
        scriptDialog.SetValue( "LUTFileLoadTypeBox","auto" )
        scriptDialog.SetValue( "LUTFileSaveFormatBox","auto" )
        scriptDialog.SetValue( "MachineListBox","" )
        scriptDialog.SetValue( "MaintainAspectRatioBox","False" )
        scriptDialog.SetValue( "MirrorImage","none" )
        scriptDialog.SetValue( "OffscreenBufferBox","fbo" )
        scriptDialog.SetValue( "OnJobCompleteBox","Nothing" )
        scriptDialog.SetValue( "OutputFrameRateBox","default" )
        scriptDialog.SetValue( "PixelTypeBox","default" )
        scriptDialog.SetValue( "PoolBox","none" )
        scriptDialog.SetValue( "PPMFileDataBox","binary" )
        scriptDialog.SetValue( "PPMFileTypeBox","auto" )
        scriptDialog.SetValue( "PriorityBox","50" )
        scriptDialog.SetValue( "ProxyScaleBox","none" )
        scriptDialog.SetValue( "QTcodec","mjpeg-a" )
        scriptDialog.SetValue( "QTquality","normal" )
        scriptDialog.SetValue( "QTStartFrameBox","0" )
        scriptDialog.SetValue( "QTLibQuicktimeCodecBox", "mjpa" )
        scriptDialog.SetValue( "RendererBox","opengl 2.0" )
        scriptDialog.SetValue( "RenderFilterMagBox","nearest" )
        scriptDialog.SetValue( "RenderFilterMinBox","linear" )
        scriptDialog.SetValue( "SecondaryPoolBox","" )
        scriptDialog.SetValue( "SGICompressionTypeBox","none" )
        scriptDialog.SetValue( "SlateFrameBox","0" )
        scriptDialog.SetValue( "SlateInputBox","" )
        scriptDialog.SetValue( "SubmitSuspendedBox","False" )
        scriptDialog.SetValue( "TGACompressionTypeBox","none" )
        #scriptDialog.SetValue( "ThreadCountBox","4" )
        scriptDialog.SetValue( "TIFFCompressionTypeBox","none" )
        scriptDialog.SetValue( "TimeUnitsBox","frames" )
        scriptDialog.SetValue( "ImageCropXBox", "0" )
        scriptDialog.SetValue( "ImageCropYBox", "0" )
        scriptDialog.SetValue( "ImageCropWBox", "0" )
        scriptDialog.SetValue( "ImageCropHBox", "0" )
        scriptDialog.SetValue( "CropPercentageBox", "False" )
        scriptDialog.SetValue( "FileSequenceBox", "False" )

def SaveSettingsButtonPressed(*args):
    global scriptDialog

    SettingsFile = scriptDialog.ShowSaveFileBrowser("DJV_Settings.ini","ini Files (*.ini)" )
    if SettingsFile != None:
        writer = File.CreateText( SettingsFile )
        ## DJV Options
        writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )
        writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
        ## Job Options
        writer.WriteLine( "TimeUnitsBox=%s" % scriptDialog.GetValue( "TimeUnitsBox" ) )
        writer.WriteLine( "FrameRate=%s" % scriptDialog.GetValue( "FrameRateBox" ) )
        ## Input Options
        writer.WriteLine( "InputLayerBox=%s" % scriptDialog.GetValue( "InputLayerBox" ) )
        writer.WriteLine( "ProxyScaleBox=%s" % scriptDialog.GetValue( "ProxyScaleBox" ) )
        writer.WriteLine( "InputStartFrameBox=%s" % scriptDialog.GetValue( "InputStartFrameBox" ) )
        writer.WriteLine( "InputEndFrameBox=%s" % scriptDialog.GetValue( "InputEndFrameBox" ) )
        writer.WriteLine( "SlateInputBox=%s" % scriptDialog.GetValue( "SlateInputBox" ) )		
        writer.WriteLine( "SlateFrameBox=%s" % scriptDialog.GetValue( "SlateFrameBox" ) )
        writer.WriteLine( "InputImageTimeoutBox=%s" % scriptDialog.GetValue( "InputImageTimeoutBox" ) )
        ## Output Options
        writer.WriteLine( "PixelTypeBox=%s" % scriptDialog.GetValue( "PixelTypeBox" ) )	
        writer.WriteLine( "OutputFrameRateBox=%s" % scriptDialog.GetValue( "OutputFrameRateBox" ) )
        # Custom Image Tag
        writer.WriteLine( "ImageTagNameBox=%s" % scriptDialog.GetValue( "ImageTagNameBox" ) )
        writer.WriteLine( "ImageTagValueBox=%s" % scriptDialog.GetValue( "ImageTagValueBox" ) )
        writer.WriteLine( "AutoGenerateTagsBox=%s" % scriptDialog.GetValue( "AutoGenerateTagsBox" ) )
        ## LOAD
        # OpenGL Options
        writer.WriteLine( "RendererBox=%s" % scriptDialog.GetValue( "RendererBox" ) )
        writer.WriteLine( "RenderFilterMinBox=%s" % scriptDialog.GetValue( "RenderFilterMinBox" ) )
        writer.WriteLine( "RenderFilterMagBox=%s" % scriptDialog.GetValue( "RenderFilterMagBox" ) )
        writer.WriteLine( "OffscreenBufferBox=%s" % scriptDialog.GetValue( "OffscreenBufferBox" ) )
        # OpenEXR Options
        #writer.WriteLine( "ThreadCountBox=%s" % scriptDialog.GetValue( "ThreadCountBox" ) )
        writer.WriteLine( "ColorProfileBox=%s" % scriptDialog.GetValue( "ColorProfileBox" ) )
        writer.WriteLine( "EXRGammaBox=%s" % scriptDialog.GetValue( "EXRGammaBox" ) )
        # Exposure
        writer.WriteLine( "EXRValueBox=%s" % scriptDialog.GetValue( "EXRValueBox" ) )
        writer.WriteLine( "EXRDefogBox=%s" % scriptDialog.GetValue( "EXRDefogBox" ) )
        writer.WriteLine( "EXRKneeLowBox=%s" % scriptDialog.GetValue( "EXRKneeLowBox" ) )
        writer.WriteLine( "EXRKneeHighBox=%s" % scriptDialog.GetValue( "EXRKneeHighBox" ) )	
        writer.WriteLine( "EXRChannelsBox=%s" % scriptDialog.GetValue( "EXRChannelsBox" ) )
        # Cineon Options
        writer.WriteLine( "CineonLoadColorProfileBox=%s" % scriptDialog.GetValue( "CineonLoadColorProfileBox" ) )
        # Film Print
        writer.WriteLine( "CineonLoadBlackBox=%s" % scriptDialog.GetValue( "CineonLoadBlackBox" ) )
        writer.WriteLine( "CineonLoadWhiteBox=%s" % scriptDialog.GetValue( "CineonLoadWhiteBox" ) )
        writer.WriteLine( "CineonLoadGammaBox=%s" % scriptDialog.GetValue( "CineonLoadGammaBox" ) )
        writer.WriteLine( "CineonLoadSoftClipBox=%s" % scriptDialog.GetValue( "CineonLoadSoftClipBox" ) )
        writer.WriteLine( "CineonLoadConvertBox=%s" % scriptDialog.GetValue( "CineonLoadConvertBox" ) )
        # DPX Options
        writer.WriteLine( "DPXColorProfileBox=%s" % scriptDialog.GetValue( "DPXColorProfileBox" ) )	
        # Film Print
        writer.WriteLine( "DPXBlackBox=%s" % scriptDialog.GetValue( "DPXBlackBox" ) )
        writer.WriteLine( "DPXWhiteBox=%s" % scriptDialog.GetValue( "DPXWhiteBox" ) )
        writer.WriteLine( "DPXGammaBox=%s" % scriptDialog.GetValue( "DPXGammaBox" ) )
        writer.WriteLine( "DPXSoftClipBox=%s" % scriptDialog.GetValue( "DPXSoftClipBox" ) )
        writer.WriteLine( "DPXConvertBox=%s" % scriptDialog.GetValue( "DPXConvertBox" ) )
        # LUT Options
        writer.WriteLine( "LUTFileLoadFormatBox=%s" % scriptDialog.GetValue( "LUTFileLoadFormatBox" ) )
        writer.WriteLine( "LUTFileLoadTypeBox=%s" % scriptDialog.GetValue( "LUTFileLoadTypeBox" ) )
        # QuickTime Options
        writer.WriteLine( "QTStartFrameBox=%s" % scriptDialog.GetValue( "QTStartFrameBox" ) )
        ## SAVE
        # OpenEXR Options
        writer.WriteLine( "EXRCompressionTypeBox=%s" % scriptDialog.GetValue( "EXRCompressionTypeBox" ) )
        writer.WriteLine( "EXRCompressionLevelBox=%s" % scriptDialog.GetValue( "EXRCompressionLevelBox" ) )
        # Cineon Options
        writer.WriteLine( "CineonSaveColorProfileBox=%s" % scriptDialog.GetValue( "CineonSaveColorProfileBox" ) )
        # Film Print
        writer.WriteLine( "CineonSaveBlackBox=%s" % scriptDialog.GetValue( "CineonSaveBlackBox" ) )
        writer.WriteLine( "CineonSaveWhiteBox=%s" % scriptDialog.GetValue( "CineonSaveWhiteBox" ) )
        writer.WriteLine( "CineonSaveGammaBox=%s" % scriptDialog.GetValue( "CineonSaveGammaBox" ) )
        # DPX Options
        writer.WriteLine( "DPXSaveColorProfileBox=%s" % scriptDialog.GetValue( "DPXSaveColorProfileBox" ) )	
        # Film Print
        writer.WriteLine( "DPXSaveBlackBox=%s" % scriptDialog.GetValue( "DPXSaveBlackBox" ) )
        writer.WriteLine( "DPXSaveWhiteBox=%s" % scriptDialog.GetValue( "DPXSaveWhiteBox" ) )
        writer.WriteLine( "DPXSaveGammaBox=%s" % scriptDialog.GetValue( "DPXSaveGammaBox" ) )
        writer.WriteLine( "DPXSaveFileVersionBox=%s" % scriptDialog.GetValue( "DPXSaveFileVersionBox" ) )
        writer.WriteLine( "DPXSaveFileTypeBox=%s" % scriptDialog.GetValue( "DPXSaveFileTypeBox" ) )	
        writer.WriteLine( "DPXSaveFileEndianBox=%s" % scriptDialog.GetValue( "DPXSaveFileEndianBox" ) )
        # IFF Options
        writer.WriteLine( "IFFCompressionTypeBox=%s" % scriptDialog.GetValue( "IFFCompressionTypeBox" ) )	
        # LUT Options
        writer.WriteLine( "LUTFileSaveFormatBox=%s" % scriptDialog.GetValue( "LUTFileSaveFormatBox" ) )	
        # PPM Options
        writer.WriteLine( "PPMFileTypeBox=%s" % scriptDialog.GetValue( "PPMFileTypeBox" ) )		
        writer.WriteLine( "PPMFileDataBox=%s" % scriptDialog.GetValue( "PPMFileDataBox" ) )
        # SGI Options
        writer.WriteLine( "SGICompressionTypeBox=%s" % scriptDialog.GetValue( "SGICompressionTypeBox" ) )	
        # Targa Options
        writer.WriteLine( "TGACompressionTypeBox=%s" % scriptDialog.GetValue( "TGACompressionTypeBox" ) )	
        # JPEG OPtions
        writer.WriteLine( "JPEGQualityBox=%s" % scriptDialog.GetValue( "JPEGQualityBox" ) )	
        # QuickTime Options
        writer.WriteLine( "QTcodec=%s" % scriptDialog.GetValue( "QTcodec" ) )
        writer.WriteLine( "QTquality=%s" % scriptDialog.GetValue( "QTquality" ) )
        writer.WriteLine( "QTLibQuicktimeCodecBox=%s" % scriptDialog.GetValue( "QTLibQuicktimeCodecBox" ) )
        # TIFF Options
        writer.WriteLine( "TIFFCompressionTypeBox=%s" % scriptDialog.GetValue( "TIFFCompressionTypeBox" ) )
        ## Image Options
        # Mirror Options
        writer.WriteLine( "MirrorImage=%s" % scriptDialog.GetValue( "MirrorImage" ) )
        # Scale Options
        writer.WriteLine( "ImageScalePercentage=%s" % scriptDialog.GetValue( "ImageScalePercentage" ) )
        writer.WriteLine( "ImageScaleXBox=%s" % scriptDialog.GetValue( "ImageScaleXBox" ) )
        writer.WriteLine( "ImageScaleYBox=%s" % scriptDialog.GetValue( "ImageScaleYBox" ) )
        # ReSize Options
        writer.WriteLine( "ImageReSizeWBox=%s" % scriptDialog.GetValue( "ImageReSizeWBox" ) )
        writer.WriteLine( "ImageReSizeHBox=%s" % scriptDialog.GetValue( "ImageReSizeHBox" ) )
        writer.WriteLine( "MaintainAspectRatioBox=%s" % scriptDialog.GetValue( "MaintainAspectRatioBox" ) )
        # Crop Options
        writer.WriteLine( "ImageCropXBox=%s" % scriptDialog.GetValue( "ImageCropXBox" ) )
        writer.WriteLine( "ImageCropYBox=%s" % scriptDialog.GetValue( "ImageCropYBox" ) )
        writer.WriteLine( "ImageCropWBox=%s" % scriptDialog.GetValue( "ImageCropWBox" ) )
        writer.WriteLine( "ImageCropHBox=%s" % scriptDialog.GetValue( "ImageCropHBox" ) )
        writer.WriteLine( "CropPercentageBox=%s" % scriptDialog.GetValue( "CropPercentageBox" ) )
        # Image Channels
        writer.WriteLine( "ImageChannels=%s" % scriptDialog.GetValue( "ImageChannels" ) )
        # File Sequencing
        writer.WriteLine( "FileSequenceBox=%s" % scriptDialog.GetValue( "FileSequenceBox" ) )

        writer.Close()
        scriptDialog.ShowMessageBox( "Custom DJV Settings have been SAVED.", "Success : DJV Settings" )

def LoadSettingsButtonPressed(*args):
    global scriptDialog

    INIsettings = ("CategoryBox","CommentBox","DepartmentBox","PoolBox","GroupBox","PriorityBox","LimitGroupBox","OnJobCompleteBox","MachineListBox","SubmitSuspendedBox","IsBlacklistBox","BuildBox",
    "VersionBox","TimeUnitsBox","FrameRateBox","InputLayerBox","ProxyScaleBox","InputStartFrameBox","InputEndFrameBox","SlateInputBox", "SlateFrameBox", "InputImageTimeoutBox",
    "PixelTypeBox", "OutputFrameRateBox","ImageTagNameBox","ImageTagValueBox", "AutoGenerateTagsBox","RendererBox", "RenderFilterMinBox", "RenderFilterMagBox",
    "OffscreenBufferBox","ColorProfileBox","EXRGammaBox","EXRValueBox", "EXRDefogBox", "EXRKneeLowBox","EXRKneeHighBox","EXRChannelsBox",
    "CineonLoadColorProfileBox","CineonLoadBlackBox","CineonLoadWhiteBox","CineonLoadGammaBox","CineonLoadSoftClipBox","CineonLoadConvertBox","DPXColorProfileBox",
    "DPXBlackBox","DPXWhiteBox","DPXGammaBox","DPXSoftClipBox","DPXConvertBox","LUTFileLoadFormatBox","LUTFileLoadTypeBox","QTStartFrameBox","EXRCompressionTypeBox","EXRCompressionLevelBox",
    "CineonSaveColorProfileBox","CineonSaveBlackBox","CineonSaveWhiteBox","CineonSaveGammaBox","DPXSaveColorProfileBox","DPXSaveBlackBox","DPXSaveWhiteBox",
    "DPXSaveGammaBox","DPXSaveFileVersionBox","DPXSaveFileTypeBox","DPXSaveFileEndianBox","IFFCompressionTypeBox","LUTFileSaveFormatBox","PPMFileTypeBox",
    "PPMFileDataBox","SGICompressionTypeBox","TGACompressionTypeBox","JPEGQualityBox", "QTcodec","QTquality","QTLibQuicktimeCodecBox","TIFFCompressionTypeBox", "MirrorImage","ImageScalePercentage",
    "ImageScaleXBox","ImageScaleYBox","ImageReSizeWBox","ImageReSizeHBox","MaintainAspectRatioBox","ImageCropXLabel","ImageCropXBox","ImageCropYLabel","ImageCropYBox",
    "ImageCropWLabel","ImageCropWBox","ImageCropHLabel","ImageCropHBox","CropPercentageBox","ImageChannels","FileSequenceBox")

    selectedFile = scriptDialog.ShowOpenFileBrowser("DJV_Settings.ini","ini Files (*.ini)")
    if selectedFile != None:

        scriptDialog.LoadSettings( selectedFile, INIsettings )

        scriptDialog.ShowMessageBox( "Custom DJV Settings have been LOADED.", "Success : DJV Settings" )

def VersionModified(*args):
    global scriptDialog

    version = scriptDialog.GetValue( "VersionBox" )

    scriptDialog.SetEnabled( "ImageCropXLabel", int( version) >= 101 )
    scriptDialog.SetEnabled( "ImageCropXBox", int( version) >= 101 )
    scriptDialog.SetEnabled( "ImageCropYLabel", int( version) >= 101 )
    scriptDialog.SetEnabled( "ImageCropYBox", int( version) >= 101 )
    scriptDialog.SetEnabled( "ImageCropWLabel", int( version) >= 101 )
    scriptDialog.SetEnabled( "ImageCropWBox", int( version) >= 101 )
    scriptDialog.SetEnabled( "ImageCropHLabel", int( version) >= 101 )
    scriptDialog.SetEnabled( "ImageCropHBox", int( version) >= 101 )
    scriptDialog.SetEnabled( "CropPercentageBox", int( version) >= 101 )
    scriptDialog.SetEnabled( "FileSequenceBox", int( version) >= 101 )
    scriptDialog.SetEnabled( "EXRFileCompressionLevelLabel", int( version) >= 101 )
    scriptDialog.SetEnabled( "EXRCompressionLevelBox", int( version) >= 101 )
    scriptDialog.SetEnabled( "QTLibQTCodecLabel", int( version) >= 101 )
    scriptDialog.SetEnabled( "QTLibQuicktimeCodecBox", int( version) >= 101 )

def InputImagesModified(*args):
    global startup
    global outputDirectory
    global outputFilename
    global DJVJob
    global DJVJobName
    global DJVJobFrames

    success = False

    try:
        filename = scriptDialog.GetValue( "InputBox" )
        output = scriptDialog.GetValue( "OutputBox" )
        if filename != "":
            initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
            paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )

            startFrame = 0
            endFrame = 0
            outputFilename = ""

            if initFrame >= 0 and paddingSize > 0:
                filename = FrameUtils.GetLowerFrameFilename( filename, initFrame, paddingSize )

                if DJVJob:
                    FrameRange = DJVJobFrames.split( "-" )
                    startFrame = int( FrameRange[0] )
                    endFrame = int( FrameRange[-1] )
                    outputFilename = output.replace( "\\", "/" )
                    scriptDialog.SetValue( "NameBox", ( DJVJobName + " [DJV QT] " + Path.GetFileName( outputFilename ) + " [" + "%s - %s" % ( startFrame, endFrame ) + "]" ) )
                else:
                    startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
                    endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
                    outputFilename = filename.replace( "\\", "/" )
                    scriptDialog.SetValue( "NameBox", ( Path.GetFileName( outputFilename ) + " [" + "%s - %s" % (startFrame, endFrame) + "]" ) )

            filename = filename.replace( "\\", "/" )

            scriptDialog.SetValue( "InputBox", filename )
            scriptDialog.SetValue( "OutputBox", outputFilename )
            scriptDialog.SetValue( "StartFrameBox", startFrame )
            scriptDialog.SetValue( "EndFrameBox", endFrame )
            outputDirectory = Path.GetDirectoryName( outputFilename )

            success = True

    except Exception as e:
        if not startup:
            scriptDialog.ShowMessageBox( e.Message, "Error Parsing Input Images" )
        
        if not success:
            scriptDialog.SetValue( "InputBox", "" )
            scriptDialog.SetValue( "OutputBox", "" )
            scriptDialog.SetValue( "StartFrameBox", 0 )
            scriptDialog.SetValue( "EndFrameBox", 0 )
            scriptDialog.SetValue( "NameBox", "" )

def FrameRangeModified(*args):
    global scriptDialog
    global DJVJob
    global DJVJobName

    filename = scriptDialog.GetValue( "InputBox" )
    output = scriptDialog.GetValue( "OutputBox" )
    startFrame = scriptDialog.GetValue( "StartFrameBox" )
    endFrame = scriptDialog.GetValue( "EndFrameBox" )
    
    if filename != "":
        if DJVJob:
            scriptDialog.SetValue( "NameBox", ( DJVJobName + " [DJV QT] " + Path.GetFileName( output ) + " [" + "%s - %s" % ( startFrame, endFrame ) + "]" ) )
        else:
            scriptDialog.SetValue( "NameBox", ( Path.GetFileName( output ) + " [" + "%s - %s" % (startFrame, endFrame) + "]" ) )

def OutputImagesModified(*args):
    global scriptDialog
    global DJVJob
    global DJVJobName

    filename = scriptDialog.GetValue( "InputBox" )
    output = scriptDialog.GetValue( "OutputBox" )
    startFrame = scriptDialog.GetValue( "StartFrameBox" )
    endFrame = scriptDialog.GetValue( "EndFrameBox" )
    
    if filename != "":
        if DJVJob:
            scriptDialog.SetValue( "NameBox", ( DJVJobName + " [DJV QT] " + Path.GetFileName( output ) + " [" + "%s - %s" % ( startFrame, endFrame ) + "]" ) )
        else:
            scriptDialog.SetValue( "NameBox", ( Path.GetFileName( output ) + " [" + "%s - %s" % (startFrame, endFrame) + "]" ) )

        scriptDialog.SetValue( "OutputBox", output.replace( "\\", "/" ) )

    # Set Deadline Job Script argument "DJVJob" = False so any further configuration by the user is then a normal DJV Job and not necessarily a DJV QuickTime push out
    DJVJob = False

def EXRCompressionTypeModified(*args):
    global scriptDialog

    EXRCompressionTypeOption = scriptDialog.GetValue( "EXRCompressionTypeBox" )
    version = scriptDialog.GetValue( "VersionBox" )

    if int(version) < 101:
        if EXRCompressionTypeOption == "dwaa" or EXRCompressionTypeOption == "dwab":
            scriptDialog.ShowMessageBox("Dreamworks Animation DWAA or DWAB EXR compression is only available in DJV v1.0.1 or later","Error")
            scriptDialog.SetEnabled( "EXRFileCompressionLevelLabel", False )
            scriptDialog.SetEnabled( "EXRCompressionLevelBox", False )

    if int(version) >= 101:
        scriptDialog.SetEnabled( "EXRFileCompressionLevelLabel", (EXRCompressionTypeOption == "dwaa" or EXRCompressionTypeOption == "dwab") )
        scriptDialog.SetEnabled( "EXRCompressionLevelBox", (EXRCompressionTypeOption == "dwaa" or EXRCompressionTypeOption == "dwab") )

def SlateInputFileModified(*args):
    global scriptDialog

    SlateInputFile = scriptDialog.GetValue( "SlateInputBox" )
    if SlateInputFile != "":
        scriptDialog.SetValue( "SlateInputBox", SlateInputFile.replace( "\\", "/" ) )

def GetSupportedFormats():
    supportedFormats = (".cin", ".dpx", ".iff", ".z", ".ifl", ".lut", ".1dl", ".pic", ".ppm", ".pnm", ".pgm",
        ".pbm", ".rla", ".rpf", ".sgi", ".rgba", ".rgb", ".bw", ".tga", ".jpeg", ".jpg", ".jfif", ".exr",
        ".png", ".qt", ".mov", ".avi", ".mp4", ".tiff", ".tif", ".vlut")
    return supportedFormats

def IsInputFormatSupported( inputFile ):
    extension = Path.GetExtension( inputFile ).lower()
    supportedFormats = GetSupportedFormats()
    for format in supportedFormats:
        if extension == format.lower():
            return True
    return False

def IsOutputFormatSupported( outputFile ):
    extension = Path.GetExtension( outputFile ).lower()
    supportedFormats = GetSupportedFormats()
    for format in supportedFormats:
        if extension == format.lower():
            return True
    return False
    
def IsInputMovieFormat( inputFile ):
    extension = Path.GetExtension( inputFile ).lower()
    movieFormats = ( ".qt",".mov",".avi",".mp4" )
    for format in movieFormats:
        if extension == format.lower():
            return True
    return False

def IsOutputMovieFormat( outputFile ):
    extension = Path.GetExtension( outputFile ).lower()
    movieFormats = ( ".qt",".mov",".avi",".mp4" )
    for format in movieFormats:
        if extension == format.lower():
            return True
    return False

def SubmitButtonPressed(*args):
    global scriptDialog
    global outputDirectory
    global DJVJob
    global integration_dialog
    
    # Check input file.
    inputFile = scriptDialog.GetValue( "InputBox" ).strip()

    # Check if input file has been defined.
    if(len(inputFile)==0):
        scriptDialog.ShowMessageBox("No input file specified","Error")
        return

    # Check if input files exist.	
    if( not File.Exists( inputFile ) and not DJVJob ):
        scriptDialog.ShowMessageBox("The input file %s does not exist." % inputFile, "Error" )
        return

    # Check that local file footage storage is OK for submission to network farm?
    if( PathUtils.IsPathLocal( inputFile ) ):
        result = scriptDialog.ShowMessageBox( "The input file " + inputFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return

    # Check inputFile file format is supported by DJV
    if( not IsInputFormatSupported( inputFile ) ):
        result = scriptDialog.ShowMessageBox( "The input file " + inputFile + " is not a supported format. If this format is supported by DJV, please email Deadline Support so we can update the supported format list.\n\nDo you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return

    # Check output file.
    outputFile = scriptDialog.GetValue( "OutputBox" ).strip()

    # Check outputFile has been specified
    if(len(outputFile)==0):
        scriptDialog.ShowMessageBox("No output file specified","Error")
        return

    # Check that outputFile path directory exists on the system OK?
    if not DJVJob:
        if( not Directory.Exists( Path.GetDirectoryName( outputFile ) ) ):
            scriptDialog.ShowMessageBox( "Path for the output file " + outputFile + " does not exist.", "Error" )
            return

    # Check that outputFile is NOT local. Should be on the network to work correctly on the farm
    elif( PathUtils.IsPathLocal( outputFile ) ):
        result = scriptDialog.ShowMessageBox( "The output file " + outputFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return

    # Check outputFile file format is supported by DJV
    if( not IsOutputFormatSupported( outputFile ) ):
        result = scriptDialog.ShowMessageBox( "The output file " + outputFile + " is not a supported format. If this format is supported by DJV, please email Deadline Support so we can update the supported format list.\n\nDo you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return
            
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( outputFile ):
        return

    # Check DJV is forcing 32bit build if outputFile is a QuickTime Movie File Format and DJV is v1.0 or earlier
    version = scriptDialog.GetValue( "VersionBox" )
    if int(version) >= 110:
        if( IsOutputMovieFormat( outputFile ) and scriptDialog.GetValue( "BuildBox" ) != "32bit" ):
            scriptDialog.ShowMessageBox("djv_convert.exe x32bit build must be used when outputting to a QuickTime File Format if using an older DJV version than v1.1.", "Error" )
            return

    # Check EXR Save Compression Level Option
    extension = Path.GetExtension( outputFile ).lower()
    if extension == ".exr":
        EXRCompressionTypeOption = scriptDialog.GetValue( "EXRCompressionTypeBox" )
        version = scriptDialog.GetValue( "VersionBox" )
        if int(version) < 101:
            if EXRCompressionTypeOption == "dwaa" or EXRCompressionTypeOption == "dwab":
                scriptDialog.ShowMessageBox("Dreamworks Animation DWAA or DWAB EXR compression is only available in DJV v1.0.1 or later\n\nSee [SAVE] - [OpenEXR Options] for more details.","Error")
                return

    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "djv_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=DJV" )
    writer.WriteLine( "Name=%s" % jobName )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )

    # Force Machine Limit size = 1 if INPUT or OUTPUT File is a MOVIE based file as only 1 machine can read / write from / to this file type concurrently
    if IsInputMovieFormat( inputFile ) or IsOutputMovieFormat( outputFile ):
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

    writer.WriteLine( "Frames=%s-%s" % (scriptDialog.GetValue( "StartFrameBox" ), scriptDialog.GetValue( "EndFrameBox")) )

    # Force Chunk Size = 100000 if INPUT or OUTPUT File is a MOVIE based file as only 1 machine can read / write from / to this file type concurrently
    if IsInputMovieFormat( inputFile ) or IsOutputMovieFormat( outputFile ):
        writer.WriteLine( "ChunkSize=100000" )
    else:
        startFrame = scriptDialog.GetValue( "StartFrameBox" )
        endFrame = scriptDialog.GetValue( "EndFrameBox" )
        TaskCount = abs( int(startFrame) - int(endFrame) ) + 1
        if TaskCount < 10:
            writer.WriteLine( "ChunkSize=1" )
        elif TaskCount >= 10 and TaskCount <= 100:
            writer.WriteLine( "ChunkSize=2" )
        elif TaskCount >= 101 and TaskCount <= 500:
            writer.WriteLine( "ChunkSize=5" )
        elif TaskCount >= 501 and TaskCount <= 1000:
            writer.WriteLine( "ChunkSize=10" )
        else:
            writer.WriteLine( "ChunkSize=20" )

    writer.WriteLine( "OutputDirectory0=%s" % outputDirectory )
    writer.WriteLine( "OutputFilename0=%s" % outputFile )
    
    #Shotgun/Draft
    extraKVPIndex = 0
    groupBatch = False
    
    if integration_dialog.IntegrationProcessingRequested():
        extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
        groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()
        
    if groupBatch:
        writer.WriteLine( "BatchName=%s\n" % (jobName ) ) 
    writer.Close()

    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "djv_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

    ## DJV Options
    writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )
    versionIndex = 0
    for currVersion in scriptDialog.GetItems( "VersionBox" ):
        writer.WriteLine( "Version%s=%s" % (versionIndex,currVersion) )
        versionIndex = versionIndex + 1

    writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
    writer.WriteLine( "Build0=None" )
    writer.WriteLine( "Build1=32bit" )
    writer.WriteLine( "Build2=64bit" )

    writer.WriteLine( "InputFile=%s" % inputFile )
    writer.WriteLine( "OutputFile=%s" % outputFile )

    ## Job Options
    writer.WriteLine( "TimeUnitsBox=%s" % scriptDialog.GetValue( "TimeUnitsBox" ) )
    writer.WriteLine( "TimeUnitsBox0=timecode" )
    writer.WriteLine( "TimeUnitsBox1=frames" )

    writer.WriteLine( "FrameRate=%s" % scriptDialog.GetValue( "FrameRateBox" ) )
    writer.WriteLine( "FrameRate0=default" )
    writer.WriteLine( "FrameRate1=1" )
    writer.WriteLine( "FrameRate2=3" )
    writer.WriteLine( "FrameRate3=6" )
    writer.WriteLine( "FrameRate4=12" )
    writer.WriteLine( "FrameRate5=15" )
    writer.WriteLine( "FrameRate6=16" )
    writer.WriteLine( "FrameRate7=18" )
    writer.WriteLine( "FrameRate8=23.98" )
    writer.WriteLine( "FrameRate9=24" )
    writer.WriteLine( "FrameRate10=25" )
    writer.WriteLine( "FrameRate11=29.97" )
    writer.WriteLine( "FrameRate12=30" )
    writer.WriteLine( "FrameRate13=50" )
    writer.WriteLine( "FrameRate14=59.94" )
    writer.WriteLine( "FrameRate15=60" )
    writer.WriteLine( "FrameRate16=120" )
    
    ## Input Options
    writer.WriteLine( "InputLayerBox=%s" % scriptDialog.GetValue( "InputLayerBox" ) )
    writer.WriteLine( "ProxyScaleBox=%s" % scriptDialog.GetValue( "ProxyScaleBox" ) )
    writer.WriteLine( "ProxyScaleBox0=none" )
    writer.WriteLine( "ProxyScaleBox1=1/2" )
    writer.WriteLine( "ProxyScaleBox2=1/4" )
    writer.WriteLine( "ProxyScaleBox3=1/8" )
    writer.WriteLine( "InputStartFrameBox=%s" % scriptDialog.GetValue( "InputStartFrameBox" ) )
    writer.WriteLine( "InputEndFrameBox=%s" % scriptDialog.GetValue( "InputEndFrameBox" ) )
    writer.WriteLine( "SlateInputBox=%s" % scriptDialog.GetValue( "SlateInputBox" ) )		
    writer.WriteLine( "SlateFrameBox=%s" % scriptDialog.GetValue( "SlateFrameBox" ) )
    writer.WriteLine( "InputImageTimeoutBox=%s" % scriptDialog.GetValue( "InputImageTimeoutBox" ) )

    ## Output Options
    writer.WriteLine( "PixelTypeBox=%s" % scriptDialog.GetValue( "PixelTypeBox" ) )
    writer.WriteLine( "PixelTypeBox0=default" )
    writer.WriteLine( "PixelTypeBox1=l u8" )
    writer.WriteLine( "PixelTypeBox2=l u16" )
    writer.WriteLine( "PixelTypeBox3=l f16" )
    writer.WriteLine( "PixelTypeBox4=l f32" )
    writer.WriteLine( "PixelTypeBox5=la u8" )
    writer.WriteLine( "PixelTypeBox6=la u16" )
    writer.WriteLine( "PixelTypeBox7=la f16" )
    writer.WriteLine( "PixelTypeBox8=la f32" )
    writer.WriteLine( "PixelTypeBox9=rgb u8" )
    writer.WriteLine( "PixelTypeBox10=rgb u10" )
    writer.WriteLine( "PixelTypeBox11=rgb u16" )
    writer.WriteLine( "PixelTypeBox12=rgb f16" )
    writer.WriteLine( "PixelTypeBox13=rgb f32" )
    writer.WriteLine( "PixelTypeBox14=rgba u8" )
    writer.WriteLine( "PixelTypeBox15=rgba u16" )
    writer.WriteLine( "PixelTypeBox16=rgba f16" )
    writer.WriteLine( "PixelTypeBox17=rgba f32" )

    writer.WriteLine( "OutputFrameRateBox=%s" % scriptDialog.GetValue( "OutputFrameRateBox" ) )
    writer.WriteLine( "OutputFrameRateBox0=default" )
    writer.WriteLine( "OutputFrameRateBox1=1" )
    writer.WriteLine( "OutputFrameRateBox2=3" )
    writer.WriteLine( "OutputFrameRateBox3=6" )
    writer.WriteLine( "OutputFrameRateBox4=12" )
    writer.WriteLine( "OutputFrameRateBox5=15" )
    writer.WriteLine( "OutputFrameRateBox6=16" )
    writer.WriteLine( "OutputFrameRateBox7=18" )
    writer.WriteLine( "OutputFrameRateBox8=23.98" )
    writer.WriteLine( "OutputFrameRateBox9=24" )
    writer.WriteLine( "OutputFrameRateBox10=25" )
    writer.WriteLine( "OutputFrameRateBox11=29.97" )
    writer.WriteLine( "OutputFrameRateBox12=30" )
    writer.WriteLine( "OutputFrameRateBox13=50" )
    writer.WriteLine( "OutputFrameRateBox14=59.94" )
    writer.WriteLine( "OutputFrameRateBox15=60" )
    writer.WriteLine( "OutputFrameRateBox16=120" )

    # Custom Image Tag
    writer.WriteLine( "ImageTagNameBox=%s" % scriptDialog.GetValue( "ImageTagNameBox" ) )
    writer.WriteLine( "ImageTagValueBox=%s" % scriptDialog.GetValue( "ImageTagValueBox" ) )
    writer.WriteLine( "AutoGenerateTagsBox=%s" % scriptDialog.GetValue( "AutoGenerateTagsBox" ) )

    ## LOAD
    # OpenGL Options
    writer.WriteLine( "RendererBox=%s" % scriptDialog.GetValue( "RendererBox" ) )
    writer.WriteLine( "RendererBox0=opengl 2.0" )
    writer.WriteLine( "RendererBox1=opengl 1.2" )
    
    writer.WriteLine( "RenderFilterMinBox=%s" % scriptDialog.GetValue( "RenderFilterMinBox" ) )
    writer.WriteLine( "RenderFilterMinBox0=nearest" )
    writer.WriteLine( "RenderFilterMinBox1=linear" )
    writer.WriteLine( "RenderFilterMinBox2=box" )
    writer.WriteLine( "RenderFilterMinBox3=triangle" )
    writer.WriteLine( "RenderFilterMinBox4=bell" )
    writer.WriteLine( "RenderFilterMinBox5=b-spline" )
    writer.WriteLine( "RenderFilterMinBox6=lanczos3" )
    writer.WriteLine( "RenderFilterMinBox7=cubic" )
    writer.WriteLine( "RenderFilterMinBox8=mitchell" )
    
    writer.WriteLine( "RenderFilterMagBox=%s" % scriptDialog.GetValue( "RenderFilterMagBox" ) )
    writer.WriteLine( "RenderFilterMagBox0=nearest" )
    writer.WriteLine( "RenderFilterMagBox1=linear" )
    writer.WriteLine( "RenderFilterMagBox2=box" )
    writer.WriteLine( "RenderFilterMagBox3=triangle" )
    writer.WriteLine( "RenderFilterMagBox4=bell" )
    writer.WriteLine( "RenderFilterMagBox5=b-spline" )
    writer.WriteLine( "RenderFilterMagBox6=lanczos3" )
    writer.WriteLine( "RenderFilterMagBox7=cubic" )
    writer.WriteLine( "RenderFilterMagBox8=mitchell" )
    
    writer.WriteLine( "OffscreenBufferBox=%s" % scriptDialog.GetValue( "OffscreenBufferBox" ) )
    writer.WriteLine( "OffscreenBufferBox0=pbuffer" )
    writer.WriteLine( "OffscreenBufferBox1=fbo" )
    
    # OpenEXR Options
    #writer.WriteLine( "ThreadCountBox=%s" % scriptDialog.GetValue( "ThreadCountBox" ) )
    writer.WriteLine( "ColorProfileBox=%s" % scriptDialog.GetValue( "ColorProfileBox" ) )
    writer.WriteLine( "ColorProfileBox0=none" )
    writer.WriteLine( "ColorProfileBox1=gamma" )
    writer.WriteLine( "ColorProfileBox2=exposure" )

    writer.WriteLine( "EXRGammaBox=%s" % scriptDialog.GetValue( "EXRGammaBox" ) )

    # Exposure
    writer.WriteLine( "EXRValueBox=%s" % scriptDialog.GetValue( "EXRValueBox" ) )
    writer.WriteLine( "EXRDefogBox=%s" % scriptDialog.GetValue( "EXRDefogBox" ) )
    writer.WriteLine( "EXRKneeLowBox=%s" % scriptDialog.GetValue( "EXRKneeLowBox" ) )
    writer.WriteLine( "EXRKneeHighBox=%s" % scriptDialog.GetValue( "EXRKneeHighBox" ) )	
    writer.WriteLine( "EXRChannelsBox=%s" % scriptDialog.GetValue( "EXRChannelsBox" ) )
    writer.WriteLine( "EXRChannelsBox0=group none" )
    writer.WriteLine( "EXRChannelsBox1=group known" )
    writer.WriteLine( "EXRChannelsBox2=group all" )
    
    # Cineon Options
    writer.WriteLine( "CineonLoadColorProfileBox=%s" % scriptDialog.GetValue( "CineonLoadColorProfileBox" ) )
    writer.WriteLine( "CineonLoadColorProfileBox0=auto" )
    writer.WriteLine( "CineonLoadColorProfileBox1=none" )
    writer.WriteLine( "CineonLoadColorProfileBox2=film print" )
    # Film Print
    writer.WriteLine( "CineonLoadBlackBox=%s" % scriptDialog.GetValue( "CineonLoadBlackBox" ) )
    writer.WriteLine( "CineonLoadWhiteBox=%s" % scriptDialog.GetValue( "CineonLoadWhiteBox" ) )
    writer.WriteLine( "CineonLoadGammaBox=%s" % scriptDialog.GetValue( "CineonLoadGammaBox" ) )
    writer.WriteLine( "CineonLoadSoftClipBox=%s" % scriptDialog.GetValue( "CineonLoadSoftClipBox" ) )
    writer.WriteLine( "CineonLoadConvertBox=%s" % scriptDialog.GetValue( "CineonLoadConvertBox" ) )
    writer.WriteLine( "CineonLoadConvertBox0=none" )
    writer.WriteLine( "CineonLoadConvertBox1=u8" )
    writer.WriteLine( "CineonLoadConvertBox2=u16" )

    # DPX Options
    writer.WriteLine( "DPXColorProfileBox=%s" % scriptDialog.GetValue( "DPXColorProfileBox" ) )
    writer.WriteLine( "DPXColorProfileBox0=auto" )
    writer.WriteLine( "DPXColorProfileBox1=none" )
    writer.WriteLine( "DPXColorProfileBox2=film print" )
    # Film Print
    writer.WriteLine( "DPXBlackBox=%s" % scriptDialog.GetValue( "DPXBlackBox" ) )
    writer.WriteLine( "DPXWhiteBox=%s" % scriptDialog.GetValue( "DPXWhiteBox" ) )
    writer.WriteLine( "DPXGammaBox=%s" % scriptDialog.GetValue( "DPXGammaBox" ) )
    writer.WriteLine( "DPXSoftClipBox=%s" % scriptDialog.GetValue( "DPXSoftClipBox" ) )
    writer.WriteLine( "DPXConvertBox=%s" % scriptDialog.GetValue( "DPXConvertBox" ) )
    writer.WriteLine( "DPXConvertBox0=none" )
    writer.WriteLine( "DPXConvertBox1=u8" )
    writer.WriteLine( "DPXConvertBox2=u16" )
    
    # LUT Options
    writer.WriteLine( "LUTFileLoadFormatBox=%s" % scriptDialog.GetValue( "LUTFileLoadFormatBox" ) )
    writer.WriteLine( "LUTFileLoadFormatBox0=auto" )
    writer.WriteLine( "LUTFileLoadFormatBox1=inferno" )
    writer.WriteLine( "LUTFileLoadFormatBox2=kodak" )
    writer.WriteLine( "LUTFileLoadTypeBox=%s" % scriptDialog.GetValue( "LUTFileLoadTypeBox" ) )
    writer.WriteLine( "LUTFileLoadTypeBox0=auto" )
    writer.WriteLine( "LUTFileLoadTypeBox1=u8" )
    writer.WriteLine( "LUTFileLoadTypeBox2=u10" )
    writer.WriteLine( "LUTFileLoadTypeBox3=u16" )
    
    # QuickTime Options
    writer.WriteLine( "QTStartFrameBox=%s" % scriptDialog.GetValue( "QTStartFrameBox" ) )

    ## SAVE
    # OpenEXR Options
    writer.WriteLine( "EXRCompressionTypeBox=%s" % scriptDialog.GetValue( "EXRCompressionTypeBox" ) )
    writer.WriteLine( "EXRCompressionTypeBox0=none" )
    writer.WriteLine( "EXRCompressionTypeBox1=rle" )
    writer.WriteLine( "EXRCompressionTypeBox2=zips" )
    writer.WriteLine( "EXRCompressionTypeBox3=zip" )
    writer.WriteLine( "EXRCompressionTypeBox4=piz" )
    writer.WriteLine( "EXRCompressionTypeBox5=pxr24" )
    writer.WriteLine( "EXRCompressionTypeBox6=b44" )
    writer.WriteLine( "EXRCompressionTypeBox7=b44a" )
    writer.WriteLine( "EXRCompressionTypeBox8=dwaa" )
    writer.WriteLine( "EXRCompressionTypeBox9=dwab" )
    writer.WriteLine( "EXRCompressionLevelBox=%s" % scriptDialog.GetValue( "EXRCompressionLevelBox" ) )

    # Cineon Options
    writer.WriteLine( "CineonSaveColorProfileBox=%s" % scriptDialog.GetValue( "CineonSaveColorProfileBox" ) )
    writer.WriteLine( "CineonSaveColorProfileBox0=film print" )
    writer.WriteLine( "CineonSaveColorProfileBox1=auto" )
    writer.WriteLine( "CineonSaveColorProfileBox2=none" )

    # Film Print
    writer.WriteLine( "CineonSaveBlackBox=%s" % scriptDialog.GetValue( "CineonSaveBlackBox" ) )
    writer.WriteLine( "CineonSaveWhiteBox=%s" % scriptDialog.GetValue( "CineonSaveWhiteBox" ) )
    writer.WriteLine( "CineonSaveGammaBox=%s" % scriptDialog.GetValue( "CineonSaveGammaBox" ) )

    # DPX Options
    writer.WriteLine( "DPXSaveColorProfileBox=%s" % scriptDialog.GetValue( "DPXSaveColorProfileBox" ) )
    writer.WriteLine( "DPXSaveColorProfileBox0=film print" )
    writer.WriteLine( "DPXSaveColorProfileBox1=auto" )
    writer.WriteLine( "DPXSaveColorProfileBox2=none" )

    # Film Print
    writer.WriteLine( "DPXSaveBlackBox=%s" % scriptDialog.GetValue( "DPXSaveBlackBox" ) )
    writer.WriteLine( "DPXSaveWhiteBox=%s" % scriptDialog.GetValue( "DPXSaveWhiteBox" ) )
    writer.WriteLine( "DPXSaveGammaBox=%s" % scriptDialog.GetValue( "DPXSaveGammaBox" ) )
    writer.WriteLine( "DPXSaveFileVersionBox=%s" % scriptDialog.GetValue( "DPXSaveFileVersionBox" ) )
    writer.WriteLine( "DPXSaveFileVersionBox0=1.0" )
    writer.WriteLine( "DPXSaveFileVersionBox1=2.0" )
    writer.WriteLine( "DPXSaveFileTypeBox=%s" % scriptDialog.GetValue( "DPXSaveFileTypeBox" ) )
    writer.WriteLine( "DPXSaveFileTypeBox0=auto" )
    writer.WriteLine( "DPXSaveFileTypeBox1=u10" )
    writer.WriteLine( "DPXSaveFileEndianBox=%s" % scriptDialog.GetValue( "DPXSaveFileEndianBox" ) )
    writer.WriteLine( "DPXSaveFileEndianBox0=auto" )
    writer.WriteLine( "DPXSaveFileEndianBox1=msb" )
    writer.WriteLine( "DPXSaveFileEndianBox2=lsb" )

    # IFF Options
    writer.WriteLine( "IFFCompressionTypeBox=%s" % scriptDialog.GetValue( "IFFCompressionTypeBox" ) )	
    writer.WriteLine( "IFFCompressionTypeBox0=none" )
    writer.WriteLine( "IFFCompressionTypeBox1=rle" )
    # LUT Options
    writer.WriteLine( "LUTFileSaveFormatBox=%s" % scriptDialog.GetValue( "LUTFileSaveFormatBox" ) )	
    writer.WriteLine( "LUTFileSaveFormatBox0=auto" )
    writer.WriteLine( "LUTFileSaveFormatBox1=inferno" )
    writer.WriteLine( "LUTFileSaveFormatBox2=kodak" )

    # PPM Options
    writer.WriteLine( "PPMFileTypeBox=%s" % scriptDialog.GetValue( "PPMFileTypeBox" ) )
    writer.WriteLine( "PPMFileTypeBox0=auto" )
    writer.WriteLine( "PPMFileTypeBox1=u1" )
    writer.WriteLine( "PPMFileDataBox=%s" % scriptDialog.GetValue( "PPMFileDataBox" ) )
    writer.WriteLine( "PPMFileDataBox0=ascii" )
    writer.WriteLine( "PPMFileDataBox1=binary" )

    # SGI Options
    writer.WriteLine( "SGICompressionTypeBox=%s" % scriptDialog.GetValue( "SGICompressionTypeBox" ) )	
    writer.WriteLine( "SGICompressionTypeBox0=none" )
    writer.WriteLine( "SGICompressionTypeBox1=rle" )

    # Targa Options
    writer.WriteLine( "TGACompressionTypeBox=%s" % scriptDialog.GetValue( "TGACompressionTypeBox" ) )	
    writer.WriteLine( "TGACompressionTypeBox0=none" )
    writer.WriteLine( "TGACompressionTypeBox1=rle" )

    # JPEG Options
    writer.WriteLine( "JPEGQualityBox=%s" % scriptDialog.GetValue( "JPEGQualityBox" ) )	
    
    # QuickTime Options
    writer.WriteLine( "QTcodec=%s" % scriptDialog.GetValue( "QTcodec" ) )
    writer.WriteLine( "QTcodec0=raw" )
    writer.WriteLine( "QTcodec1=jpeg" )
    writer.WriteLine( "QTcodec2=mjpeg-a" )
    writer.WriteLine( "QTcodec3=mjpeg-b" )
    writer.WriteLine( "QTcodec4=h263" )
    writer.WriteLine( "QTcodec5=h264" )
    writer.WriteLine( "QTcodec6=dvd-ntsc" )
    writer.WriteLine( "QTcodec7=dvd-pal" )

    # Lib Quicktime Codec Options (Linux Only)
    writer.WriteLine( "QTLibQuicktimeCodecBox=%s" % scriptDialog.GetValue( "QTLibQuicktimeCodecBox" ) )
    writer.WriteLine( "QTLibQuicktimeCodecBox0=rtjpeg" )
    writer.WriteLine( "QTLibQuicktimeCodecBox1=raw" )
    writer.WriteLine( "QTLibQuicktimeCodecBox2=rawalpha" )
    writer.WriteLine( "QTLibQuicktimeCodecBox3=v308" )
    writer.WriteLine( "QTLibQuicktimeCodecBox4=v408" )
    writer.WriteLine( "QTLibQuicktimeCodecBox5=v410" )
    writer.WriteLine( "QTLibQuicktimeCodecBox6=yuv2" )
    writer.WriteLine( "QTLibQuicktimeCodecBox7=yuv4" )
    writer.WriteLine( "QTLibQuicktimeCodecBox8=yv12" )
    writer.WriteLine( "QTLibQuicktimeCodecBox9=2vuy" )
    writer.WriteLine( "QTLibQuicktimeCodecBox10=v210" )
    writer.WriteLine( "QTLibQuicktimeCodecBox11=yuvs" )
    writer.WriteLine( "QTLibQuicktimeCodecBox12=jpeg" )
    writer.WriteLine( "QTLibQuicktimeCodecBox13=mjpa" )
    writer.WriteLine( "QTLibQuicktimeCodecBox14=png" )
    writer.WriteLine( "QTLibQuicktimeCodecBox15=pngalpha" )
    writer.WriteLine( "QTLibQuicktimeCodecBox16=ffmpeg_mpg4" )
    writer.WriteLine( "QTLibQuicktimeCodecBox17=ffmpeg_msmpeg4v3" )
    writer.WriteLine( "QTLibQuicktimeCodecBox18=ffmpeg_msmpeg4v3_wmp" )
    writer.WriteLine( "QTLibQuicktimeCodecBox19=ffmpeg_h263" )
    writer.WriteLine( "QTLibQuicktimeCodecBox20=ffmpeg_h263p" )
    writer.WriteLine( "QTLibQuicktimeCodecBox21=ffmpeg_mjpg" )
    writer.WriteLine( "QTLibQuicktimeCodecBox22=ffmpeg_rle" )
    writer.WriteLine( "QTLibQuicktimeCodecBox23=ffmpeg_dv" )
    writer.WriteLine( "QTLibQuicktimeCodecBox24=ffmpeg_dvcpro" )
    writer.WriteLine( "QTLibQuicktimeCodecBox25=ffmpeg_dv50" )
    writer.WriteLine( "QTLibQuicktimeCodecBox26=ffmpeg_ffvhuff" )
    writer.WriteLine( "QTLibQuicktimeCodecBox27=ffmpeg_ffv1" )
    writer.WriteLine( "QTLibQuicktimeCodecBox28=ffmpeg_dnxhd" )
    writer.WriteLine( "QTLibQuicktimeCodecBox29=ffmpeg_imx" )

    writer.WriteLine( "QTquality=%s" % scriptDialog.GetValue( "QTquality" ) )	
    writer.WriteLine( "QTquality0=lossless" )
    writer.WriteLine( "QTquality1=min" )
    writer.WriteLine( "QTquality2=max" )
    writer.WriteLine( "QTquality3=low" )
    writer.WriteLine( "QTquality4=normal" )
    writer.WriteLine( "QTquality5=high" )

    # TIFF Options
    writer.WriteLine( "TIFFCompressionTypeBox=%s" % scriptDialog.GetValue( "TIFFCompressionTypeBox" ) )
    writer.WriteLine( "TIFFCompressionTypeBox0=none" )
    writer.WriteLine( "TIFFCompressionTypeBox1=rle" )
    writer.WriteLine( "TIFFCompressionTypeBox2=lzw" )

    ## Image Options
    # Mirror Options
    writer.WriteLine( "MirrorImage=%s" % scriptDialog.GetValue( "MirrorImage" ) )
    writer.WriteLine( "MirrorImage0=none" )
    writer.WriteLine( "MirrorImage1=mirror_h" )
    writer.WriteLine( "MirrorImage2=mirror_v" )
    # Scale Options
    writer.WriteLine( "ImageScalePercentage=%s" % scriptDialog.GetValue( "ImageScalePercentage" ) )
    writer.WriteLine( "ImageScalePercentage0=0" )
    writer.WriteLine( "ImageScalePercentage1=10" )
    writer.WriteLine( "ImageScalePercentage2=20" )
    writer.WriteLine( "ImageScalePercentage3=30" )
    writer.WriteLine( "ImageScalePercentage4=40" )
    writer.WriteLine( "ImageScalePercentage5=50" )
    writer.WriteLine( "ImageScalePercentage6=60" )
    writer.WriteLine( "ImageScalePercentage7=70" )
    writer.WriteLine( "ImageScalePercentage8=80" )
    writer.WriteLine( "ImageScalePercentage9=90" )
    writer.WriteLine( "ImageScalePercentage10=100" )
    writer.WriteLine( "ImageScalePercentage11=200" )
    writer.WriteLine( "ImageScalePercentage12=300" )
    writer.WriteLine( "ImageScalePercentage13=400" )
    writer.WriteLine( "ImageScalePercentage14=500" )
    
    writer.WriteLine( "ImageScaleXBox=%s" % scriptDialog.GetValue( "ImageScaleXBox" ) )
    writer.WriteLine( "ImageScaleYBox=%s" % scriptDialog.GetValue( "ImageScaleYBox" ) )
    # ReSize Options
    writer.WriteLine( "ImageReSizeWBox=%s" % scriptDialog.GetValue( "ImageReSizeWBox" ) )
    writer.WriteLine( "ImageReSizeHBox=%s" % scriptDialog.GetValue( "ImageReSizeHBox" ) )
    writer.WriteLine( "MaintainAspectRatioBox=%s" % scriptDialog.GetValue( "MaintainAspectRatioBox" ) )

    # Crop Options (Version >= 101)
    writer.WriteLine( "ImageCropXBox=%s" % scriptDialog.GetValue( "ImageCropXBox" ) )
    writer.WriteLine( "ImageCropYBox=%s" % scriptDialog.GetValue( "ImageCropYBox" ) )
    writer.WriteLine( "ImageCropWBox=%s" % scriptDialog.GetValue( "ImageCropWBox" ) )
    writer.WriteLine( "ImageCropHBox=%s" % scriptDialog.GetValue( "ImageCropHBox" ) )
    writer.WriteLine( "CropPercentageBox=%s" % scriptDialog.GetValue( "CropPercentageBox" ) )

    # Image Channels
    writer.WriteLine( "ImageChannels=%s" % scriptDialog.GetValue( "ImageChannels" ) )
    writer.WriteLine( "ImageChannels0=default" )
    writer.WriteLine( "ImageChannels1=red" )
    writer.WriteLine( "ImageChannels2=green" )
    writer.WriteLine( "ImageChannels3=blue" )
    writer.WriteLine( "ImageChannels4=alpha" )

    # File Sequencing (Version >= 101)
    writer.WriteLine( "FileSequenceBox=%s" % scriptDialog.GetValue( "FileSequenceBox" ) )

    writer.Close()

    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
    
    CloseDialog()
