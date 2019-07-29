import math

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
    scriptDialog.SetTitle( "Submit Maxwell Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Maxwell' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
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

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 5, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 5, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 6, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 6, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 7, 0, "The whitelisted or blacklisted list of machines." )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 8, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 9, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 9, 1 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 10, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 10, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 10, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Maxwell Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Maxwell File", 1, 0, "The Maxwell files to be rendered. Can be a single file, or a sequence of files.", False )

    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Maxwell Files (*.mxs);;All files (*)", 1, 1, colSpan=3 )
    sceneBox.ValueModified.connect(SceneBoxChanged)

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 2, 0, "The version of Maxwell to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "2",("2","3","4"), 2, 1 )
    versionBox.ValueModified.connect(VersionBoxChanged)
    scriptDialog.AddControlToGrid("VerbosityLabel","LabelControl","Verbosity", 2, 2, "Set the amount of information that Maxwell should output while rendering.", False)
    scriptDialog.AddComboControlToGrid("VerbosityBox","ComboControl","All",("None","Errors","Warnings","Info","All"), 2, 3)

    singleFileBox = scriptDialog.AddSelectionControlToGrid( "SingleFileBox", "CheckBoxControl", False, "Single Frame Job", 3, 1, "This should be checked if you're submitting a single Maxwell file only." )
    singleFileBox.ValueModified.connect(SingleFileBoxChanged)
    scriptDialog.AddControlToGrid("BuildLabel","LabelControl","Build To Force", 3, 2, "Force 32 bit or 64 bit rendering.", False )
    scriptDialog.AddComboControlToGrid("BuildBox","ComboControl","None",("None","32bit","64bit"), 3, 3)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 4, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 5, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddControlToGrid( "ThreadsLabel", "LabelControl", "Threads", 5, 2, "The number of threads to use for rendering.", False )
    scriptDialog.AddRangeControlToGrid( "ThreadsBox", "RangeControl", 0, 0, 256, 0, 1, 5, 3 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage( "Additional Options" )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator9", "SeparatorControl", "Cooperative Rendering", 0, 0, colSpan=3 )

    coopBox = scriptDialog.AddSelectionControlToGrid( "CoopBox", "CheckBoxControl", False, "Cooperative Rendering", 1, 0, "If enabled, multiple jobs will be submitted to Deadline, each with a different seed. You can then use Maxwell to combine the resulting output after the rendering has completed.", False )
    coopBox.ValueModified.connect(CoopBoxChanged)
    separateCoopJobsBox = scriptDialog.AddSelectionControlToGrid( "SeparateCoopJobsBox", "CheckBoxControl", False, "Split Co-op Renders Into Separate Jobs", 1, 1, "If enabled, co-op renders will be split up into separate jobs. This is required if rendering an animation instead of a single Maxwell file.", False )
    separateCoopJobsBox.ValueModified.connect(SeparateCoopJobsChanged)
    scriptDialog.AddHorizontalSpacerToGrid("AOHSpacer1", 1, 2 )

    scriptDialog.AddControlToGrid( "AutoComputeSamplingEmptyLabel", "LabelControl", "",2, 0, "", False )
    scriptDialog.AddSelectionControlToGrid( "AutoComputeSamplingBox", "CheckBoxControl", False, "Adjust Sampling Overrides For Cooperative Rendering", 2, 1, "Enable to adjust the Sampling Level overrides below for each individual render so that the merged results have the Sampling Levels specified." )

    scriptDialog.AddControlToGrid( "CoopJobsLabel", "LabelControl", "Number Of Co-op Renders", 3, 0, "The number of co-op renders to submit to Deadline.", False )
    scriptDialog.AddRangeControlToGrid( "CoopJobsBox", "RangeControl", 2, 2, 1000000, 0, 1, 3, 1, expand=False )
    
    autoMergeBox = scriptDialog.AddSelectionControlToGrid( "AutoMergeBox", "CheckBoxControl", False, "Auto-Merge Files", 4, 0, "Enable if you want Deadline to use Maxwell to merge the results from the co-op jobs.", False )
    autoMergeBox.ValueModified.connect(AutoMergeChanged)
    scriptDialog.AddSelectionControlToGrid( "FailOnMissingFilesBox", "CheckBoxControl", True, "Fail On Missing Intermediate Files", 4, 1, "Enable to have the merge job fail if there are co-op results that are missing.", False )

    scriptDialog.AddSelectionControlToGrid( "DeleteFilesBox", "CheckBoxControl", False, "Delete Intermediate Files", 5, 1, "Enable to have Deadline automatically delete the individual co-op results after merging the final result.", False )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator10", "SeparatorControl", "Output Options", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "MxiLabel","LabelControl","Output MXI File (optional)", 1, 0, "Optionally configure the output path for the MXI file which can be used to resume the render later. Note that this is required for co-op rendering though.", False )
    scriptDialog.AddSelectionControlToGrid("MxiBox","FileSaverControl","","MXI (*.mxi);;All files (*)", 1, 1 )

    scriptDialog.AddControlToGrid( "OutputLabel","LabelControl","Output Image File (optional)", 2, 0, "Optionally configure the output path for the image file.", False )
    scriptDialog.AddSelectionControlToGrid("OutputBox","FileSaverControl","","PNG (*.png);;Targa (*.tga);;JPG (*.jpg);;TIFF (*.tif);;JPG2000 (*.jp2);;HDR (*.hdr);;EXR (*.exr);;PSD (*.psd);;BMP (*.bmp);;PPM (*.ppm);;PBM (*.pbm);;PGM (*.pgm);;All files (*)", 2, 1 )
    
    scriptDialog.AddControlToGrid( "CameraLabel","LabelControl","Render Camera (optional)", 3, 0, "Optionally choose which camera to render.", False )
    scriptDialog.AddControlToGrid( "CameraBox", "TextControl", "", 3, 1 )
    
    scriptDialog.AddSelectionControlToGrid( "LocalRenderingBox", "CheckBoxControl", False, "Enable Local Rendering", 4, 0, "If enabled, the mxi file and/or the image file will be rendered to a local file and copied to the network after rendering is complete. Note that this requires you to specify an mxi and/or an image path in the submitter.", colSpan=2)
    scriptDialog.AddSelectionControlToGrid( "ResumeBox", "CheckBoxControl", False, "Resume From MXI File If It Exists (requires Maxwell 2.5.1 or later)", 5, 0, "Requires Maxwell 2.5.1. If enabled, Maxwell will use the specified MXI file to resume the render if it exists. If you suspend the job in Deadline, it will pick up from where it left off when it resumes.", colSpan=2 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "Overrides", 0, 0, colSpan=3 )

    overrideTimeCheck = scriptDialog.AddSelectionControlToGrid( "OverrideTime", "CheckBoxControl", False, "Override Time", 1, 0, "Enable to override the Time setting in the Maxwell file.", False )
    overrideTimeCheck.ValueModified.connect(OverrideTimeChanged)
    scriptDialog.AddRangeControlToGrid( "OverrideTimeBox", "RangeControl", 10, 1, 9999999, 2, 1, 1, 1, "The Time override value (minutes)." )

    overrideSamplingCheck = scriptDialog.AddSelectionControlToGrid( "OverrideSampling", "CheckBoxControl", False, "Override Sampling Level", 2, 0, "Enable to override the Sampling setting in the Maxwell file.", False )
    overrideSamplingCheck.ValueModified.connect(OverrideSamplingChanged)
    scriptDialog.AddRangeControlToGrid( "OverrideSamplingBox", "RangeControl", 10, 0, 50, 2, 1, 2, 1 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator11", "SeparatorControl", "Extra Sampling (requires Maxwell 3.1 or later)", 0, 0, colSpan=4 )
    
    overrideExtraSamplingCheck = scriptDialog.AddSelectionControlToGrid( "OverrideExtraSampling", "CheckBoxControl", False, "Override Extra Sampling", 1, 0, "If the extra sampling settings should be overridden.", False, colSpan=2 )
    overrideExtraSamplingCheck.ValueModified.connect(OverrideExtraSamplingChanged)
    extraSamplingEnabledCheck = scriptDialog.AddSelectionControlToGrid( "ExtraSamplingEnabled", "CheckBoxControl", False, "Enabled", 1, 2, "If extra sampling is enabled.", False, colSpan=2 )
    extraSamplingEnabledCheck.ValueModified.connect(OverrideExtraSamplingChanged)
    
    scriptDialog.AddControlToGrid( "ExtraSamplingLevelLabel", "LabelControl", "Sampling Level", 2, 0, "The extra sampling level.", False )
    scriptDialog.AddRangeControlToGrid( "ExtraSamplingLevelBox", "RangeControl", 10, 0, 50, 2, 1, 2, 1 )
    scriptDialog.AddSelectionControlToGrid( "ExtraSamplingInvertMask", "CheckBoxControl", False, "Invert Mask", 2, 2, "If the extra sampling alpha mask must be inverted.", False, colSpan=2 )
    
    scriptDialog.AddControlToGrid( "ExtraSamplingMaskLabel", "LabelControl", "Mask", 3, 0, "The extra sampling mask.", False )
    maskBox = scriptDialog.AddComboControlToGrid("ExtraSamplingMaskBox","ComboControl","Alpha",("Custom Alpha","Alpha","Bitmap"), 3, 1)
    maskBox.ValueModified.connect(OverrideExtraSamplingChanged)
    scriptDialog.AddControlToGrid( "ExtraSamplingCustomAlphaLabel", "LabelControl", "Custom Alpha", 3, 2, "The custom alpha name that will be used for the extra sampling mask (if Mask is set to Custom Alpha).", False )
    scriptDialog.AddControlToGrid( "ExtraSamplingCustomAlphaBox", "TextControl", "", 3, 3 )
    
    scriptDialog.AddControlToGrid( "ExtraSamplingBitmapLabel", "LabelControl", "Bitmap File", 4, 0, "The bitmap file that will be used for the extra sampling mask (if Mask is set to Bitmap).", False )
    scriptDialog.AddSelectionControlToGrid( "ExtraSamplingBitmapBox", "FileBrowserControl", "", "All files (*)", 4, 1, colSpan=3 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Command Line Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "CommandLineLabel", "LabelControl", "Additional Arguments", 1, 0, "Additional command line arguments to pass to the renderer.", False )
    scriptDialog.AddControlToGrid( "CommandLineBox", "TextControl", "", 1, 1, colSpan=2 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "MaxwellMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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

    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","ThreadsBox","CoopJobsBox","BuildBox","AutoMergeBox","DeleteFilesBox", "VersionBox", "VerbosityBox","OverrideTime","OverrideTimeBox","OverrideSampling","OverrideSamplingBox","MxiBox","ResumeBox","OutputBox","SingleFileBox","AutoComputeSamplingBox", "LocalRenderingBox", "SeparateCoopJobsBox", "FailOnMissingFilesBox", "OverrideExtraSampling", "ExtraSamplingEnabled", "ExtraSamplingLevelBox", "ExtraSamplingInvertMask", "ExtraSamplingMaskBox", "ExtraSamplingCustomAlphaBox", "ExtraSamplingBitmapBox")
    
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    VersionBoxChanged(None)
    SceneBoxChanged(None)
    SingleFileBoxChanged(None)
    CoopBoxChanged(None)
    AutoMergeChanged(None)
    SeparateCoopJobsChanged(None)
    OverrideTimeChanged(None)
    OverrideSamplingChanged(None)
    OverrideExtraSamplingChanged(None)
    
    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "MaxwellSettings.ini" )
    
def OverrideTimeChanged(*args):
    global scriptDialog
    enabled = scriptDialog.GetValue( "OverrideTime" )
    scriptDialog.SetEnabled( "OverrideTimeBox", enabled )
    
def OverrideSamplingChanged(*args):
    global scriptDialog
    enabled = scriptDialog.GetValue( "OverrideSampling" )
    scriptDialog.SetEnabled( "OverrideSamplingBox", enabled )
    
def OverrideExtraSamplingChanged(*args):
    global scriptDialog
    
    version = int(scriptDialog.GetValue( "VersionBox" ))
    overriden = scriptDialog.GetValue( "OverrideExtraSampling" ) and version >= 3
    enabled = scriptDialog.GetValue( "ExtraSamplingEnabled" )
    customAlphaMask = (scriptDialog.GetValue( "ExtraSamplingMaskBox" ) == "Custom Alpha")
    bitmapMask = (scriptDialog.GetValue( "ExtraSamplingMaskBox" ) == "Bitmap")
    
    scriptDialog.SetEnabled( "ExtraSamplingEnabled", overriden )
    scriptDialog.SetEnabled( "ExtraSamplingLevelLabel", overriden and enabled )
    scriptDialog.SetEnabled( "ExtraSamplingLevelBox", overriden and enabled )
    scriptDialog.SetEnabled( "ExtraSamplingInvertMask", overriden and enabled )
    scriptDialog.SetEnabled( "ExtraSamplingMaskLabel", overriden and enabled )
    scriptDialog.SetEnabled( "ExtraSamplingMaskBox", overriden and enabled )
    scriptDialog.SetEnabled( "ExtraSamplingCustomAlphaLabel", overriden and enabled and customAlphaMask )
    scriptDialog.SetEnabled( "ExtraSamplingCustomAlphaBox", overriden and enabled and customAlphaMask )
    scriptDialog.SetEnabled( "ExtraSamplingBitmapLabel", overriden and enabled and bitmapMask )
    scriptDialog.SetEnabled( "ExtraSamplingBitmapBox", overriden and enabled and bitmapMask )
    
def VersionBoxChanged(*args):
    global scriptDialog
    version = int(scriptDialog.GetValue( "VersionBox" ))
    
    scriptDialog.SetEnabled( "ResumeBox", version >= 2 )
    scriptDialog.SetEnabled( "VerbosityBox", version >= 2 )
    scriptDialog.SetEnabled( "VerbosityLabel", version >= 2 )
    
    scriptDialog.SetEnabled( "Separator11", version >= 3 )
    scriptDialog.SetEnabled( "OverrideExtraSampling", version >= 3 )
    
    OverrideExtraSamplingChanged(None)

def SceneBoxChanged(*args):
    filename = scriptDialog.GetValue("SceneBox")

    try:
        if(File.Exists(filename)):
            paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
            if paddingSize > 0:
                frameString = "1"
                startFrame = 0
                endFrame = 0
                initFrame = FrameUtils.GetFrameNumberFromFilename( filename )

                startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
                endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
                if( startFrame != endFrame ):
                    frameString = str(startFrame) + "-" + str(endFrame)
                    scriptDialog.SetValue("FramesBox",frameString)
                    scriptDialog.SetValue("SingleFileBox",False)
                else:
                    scriptDialog.SetValue("SingleFileBox",True)
            else:
                scriptDialog.SetValue("SingleFileBox",True)
    except:
        pass

def SingleFileBoxChanged(*args):
    global scriptDialog
    singleFileChecked = scriptDialog.GetValue( "SingleFileBox" )
    
    enabled = not singleFileChecked
    scriptDialog.SetEnabled( "FramesLabel", enabled )
    scriptDialog.SetEnabled( "FramesBox", enabled )
    scriptDialog.SetEnabled( "ChunkSizeLabel", enabled )
    scriptDialog.SetEnabled( "ChunkSizeBox", enabled )
    
    coopEnabled = scriptDialog.GetValue( "CoopBox" )
    scriptDialog.SetEnabled( "SeparateCoopJobsBox", singleFileChecked and coopEnabled )
    if not singleFileChecked:
        scriptDialog.SetValue( "SeparateCoopJobsBox", True )

def CoopBoxChanged(*args):
    global scriptDialog
    enabled = scriptDialog.GetValue( "CoopBox" )
    scriptDialog.SetEnabled( "CoopJobsLabel", enabled )
    scriptDialog.SetEnabled( "CoopJobsBox", enabled )
    scriptDialog.SetEnabled( "AutoMergeBox", enabled )
    scriptDialog.SetEnabled( "DeleteFilesBox", enabled and scriptDialog.GetValue( "AutoMergeBox" ) )
    scriptDialog.SetEnabled( "FailOnMissingFilesBox", enabled and scriptDialog.GetValue( "AutoMergeBox" ) )
    scriptDialog.SetEnabled( "AutoComputeSamplingBox", enabled )
    if enabled:
        scriptDialog.SetValue( "MxiLabel", "Output MXI File (required)" )
    else:
        scriptDialog.SetValue( "MxiLabel", "Output MXI File (optional)" )
        
    singleFileChecked = scriptDialog.GetValue( "SingleFileBox" )
    scriptDialog.SetEnabled( "SeparateCoopJobsBox", singleFileChecked and enabled )

def AutoMergeChanged(*args):
    global scriptDialog
    enabled = scriptDialog.GetValue( "CoopBox" ) and scriptDialog.GetValue( "AutoMergeBox" )
    scriptDialog.SetEnabled( "DeleteFilesBox", enabled )
    scriptDialog.SetEnabled( "FailOnMissingFilesBox", enabled )

def SeparateCoopJobsChanged(*args):
    pass
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    
    version = int(scriptDialog.GetValue( "VersionBox" ))
    singleFile = scriptDialog.GetValue( "SingleFileBox" )
    
    coopRendering = scriptDialog.GetValue( "CoopBox" )
    separateCoopJobs = scriptDialog.GetValue( "SeparateCoopJobsBox" )

    if not singleFile:
        separateCoopJobs = True
    
    coopJobs = 1
    if coopRendering:
        coopJobs = int(scriptDialog.GetValue( "CoopJobsBox" ))
    
    # Determine the Sampling Level if doing a co-op render.
    overrideSampling = scriptDialog.GetValue( "OverrideSampling" )
    overrideSamplingValue = scriptDialog.GetValue( "OverrideSamplingBox" )
    autoComputeSampling = scriptDialog.GetValue( "AutoComputeSamplingBox" )
    #~ if coopRendering and autoComputeSampling:
        #~ # This algorithm comes from Next Limit.
        #~ #   - LOCAL is the Sampling Level we need to pass for each co-op job
        #~ #   - SL_MERGED is the desired Sampling Level after merging
        #~ #   - NODES is the number of co-op jobs
        #~ # double LOCAL = ( log( ( (exp( SL_MERGED * log (1.5) ) - 1.0 ) / (double)nNodes ) + 1.0 )) / log(1.5); 
        #~ overrideSamplingValue = round(( math.log( ( (math.exp( overrideSamplingValue * math.log(1.5) ) - 1.0 ) / float(coopJobs) ) + 1.0 )) / math.log(1.5), 2)
        
    warnings = ""
    errors = ""
    
    # Check maxwell file.
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        errors += (" - Maxwell file %s does not exist.\n" % sceneFile)
    elif( PathUtils.IsPathLocal( sceneFile ) ):
        warnings += (" - The maxwell file " + sceneFile + " is local.\n")
    
    # Check mxi file.
    mxiFile = (scriptDialog.GetValue( "MxiBox" )).strip()
    if( len( mxiFile ) > 0 ):
        if( not Directory.Exists( Path.GetDirectoryName( mxiFile ) ) ):
            errors += (" - Directory for MXI file %s does not exist.\n" % mxiFile)
        elif( PathUtils.IsPathLocal( mxiFile ) ):
            warnings += (" - MXI file " + mxiFile + " is local.\n")
    elif( coopRendering ):
        errors += " - Cooperative Rendering requires that you specify an MXI file.\n"
    
    # Check output file.
    outputFile = (scriptDialog.GetValue( "OutputBox" )).strip()
    if( len( outputFile ) > 0 ):
        if( not Directory.Exists( Path.GetDirectoryName( outputFile ) ) ):
            errors += (" - Directory for output file %s does not exist.\n" % outputFile)
        elif( PathUtils.IsPathLocal( outputFile ) ):
            warnings += (" - Output file " + outputFile + " is local.\n")

    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( outputFile ):
        return
    
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( singleFile ):
        frames = "0"
    elif( not FrameUtils.FrameRangeValid( frames ) ):
        errors += (" - Frame range '%s' is not valid.\n" % frames)
    
    if len( errors ) > 0:
        scriptDialog.ShowMessageBox( "The following errors were found:\n\n" + errors + "\nPlease fix these before submitting the job.", "Error" )
        return
    if len( warnings ) > 0:
        result = scriptDialog.ShowMessageBox( "The following potential problems were found:\n\n" + warnings + "\nAre you sure you want to submit the job?", "Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    successes = 0
    failures = 0
    jobIds = []
    
    resultsDisplayed = False
    
    batchName = scriptDialog.GetValue( "NameBox" )

    for i in range(int(coopJobs)):
        jobName = scriptDialog.GetValue( "NameBox" )
        if coopRendering:
            if separateCoopJobs:
                jobName += " - Cooperative Job " + str(i+1) + " of " + str(coopJobs)
            else:
                jobName += " - Single Cooperative Job"
        
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "maxwell_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Maxwell" )
        writer.WriteLine( "Name=%s" % jobName )
        
        if coopRendering:
            if separateCoopJobs or scriptDialog.GetValue( "AutoMergeBox" ):
                writer.WriteLine( "BatchName=%s" % batchName )

        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
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
        
        if separateCoopJobs:
            writer.WriteLine( "Frames=%s" % frames )
            writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        else:
            writer.WriteLine( "Frames=1-%s" % coopJobs)
            writer.WriteLine( "ChunkSize=1" )
        
        if( len( outputFile ) > 0 ):
            if( singleFile ):
                if separateCoopJobs:
                    writer.WriteLine( "OutputFilename0=%s" % outputFile )
                else:
                    directory = Path.GetDirectoryName( outputFile )
                    writer.WriteLine( "OutputDirectory0=%s" % directory )
                    writer.WriteLine( "OutputFilename0=%s" % outputFile )
            else:
                directory = Path.GetDirectoryName( outputFile )
                filename = Path.GetFileNameWithoutExtension( outputFile )
                extension = Path.GetExtension( outputFile )
                writer.WriteLine( "OutputFilename0=%s" % Path.Combine( directory, filename + "####" + extension ) )
        
        elif( len( mxiFile ) > 0 ):
            directory = Path.GetDirectoryName( mxiFile )
            writer.WriteLine( "OutputDirectory0=%s" % directory )
        
        if not coopRendering:
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
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "maxwell_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Version=%s" % str(version) )
        writer.WriteLine( "SingleFile=%d" % singleFile )
        writer.WriteLine( "MaxwellFile=%s" % sceneFile )
        writer.WriteLine( "OutputFile=%s" % outputFile )
        writer.WriteLine( "MxiFile=%s" % mxiFile )
        writer.WriteLine( "LocalRendering=%s" % scriptDialog.GetValue( "LocalRenderingBox" ) )
        
        writer.WriteLine( "Camera=%s" % scriptDialog.GetValue( "CameraBox" ) )
        
        if( scriptDialog.GetValue( "ResumeBox" ) ):
            writer.WriteLine( "ResumeFromMxiFile=True" )
        else:
            writer.WriteLine( "ResumeFromMxiFile=False" )
        
        writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
        writer.WriteLine( "RenderThreads=%s" % scriptDialog.GetValue( "ThreadsBox" ) )
        writer.WriteLine( "CommandLineOptions=%s" % scriptDialog.GetValue( "CommandLineBox" ).strip() )
        
        writer.WriteLine( "OverrideTime=%s" % scriptDialog.GetValue( "OverrideTime" ) )
        writer.WriteLine( "OverrideTimeValue=%s" % scriptDialog.GetValue( "OverrideTimeBox" ) )
        writer.WriteLine( "OverrideSampling=%s" % overrideSampling )
        writer.WriteLine( "OverrideSamplingValue=%s" % overrideSamplingValue )
        
        if version >= 3:
            writer.WriteLine( "OverrideExtraSampling=%s" % scriptDialog.GetValue( "OverrideExtraSampling" ) )
            writer.WriteLine( "ExtraSamplingEnabled=%s" % scriptDialog.GetValue( "ExtraSamplingEnabled" ) )
            writer.WriteLine( "ExtraSamplingLevel=%s" % scriptDialog.GetValue( "ExtraSamplingLevelBox" ) )
            writer.WriteLine( "ExtraSamplingMask=%s" % scriptDialog.GetValue( "ExtraSamplingMaskBox" ) )
            writer.WriteLine( "ExtraSamplingCustomAlphaName=%s" % scriptDialog.GetValue( "ExtraSamplingCustomAlphaBox" ) )
            writer.WriteLine( "ExtraSamplingBitmapFile=%s" % scriptDialog.GetValue( "ExtraSamplingBitmapBox" ) )
            writer.WriteLine( "ExtraSamplingInvertMask=%s" % scriptDialog.GetValue( "ExtraSamplingInvertMask" ) )
        
        if version >= 2:
            writer.WriteLine( "Verbosity=%s" % scriptDialog.GetValue( "VerbosityBox" ) )
        
        if coopRendering:
            writer.WriteLine( "CoopRendering=True" )
            writer.WriteLine( "CoopJobs=%d" % coopJobs )
            writer.WriteLine( "AutoComputeSampling=%s" % autoComputeSampling )
            if separateCoopJobs:
                writer.WriteLine( "CoopSeed=%d" % (i+1) )
            else:
                writer.WriteLine( "SingleCoopJob=True" )
        
        writer.WriteLine( "MergeJob=False" )
        
        writer.Close()
        
        # Setup the command line arguments.
        arguments = StringCollection()
        if not coopRendering:
            resultsDisplayed = True
        else:
            if not scriptDialog.GetValue( "AutoMergeBox" ) and not separateCoopJobs:
                resultsDisplayed = True
        
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        
        # Now submit the job.
        submissionResults = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        submissionResultLines = submissionResults.splitlines()
        
        # Only show the results if necessary.
        if resultsDisplayed:
            scriptDialog.ShowMessageBox( submissionResults, "Submission Results" )
        
        # Try to find a job ID in the render job's submission results
        jobIdFound = False
        
        jobIdString = "JobID="
        for line in submissionResultLines:
            jobIdIndex = line.find( jobIdString )
            if jobIdIndex != -1:
                jobIdIndex += len(jobIdString)
                jobId = line[jobIdIndex:]
                jobIds.append( jobId )
                jobIdFound = True
                break
                
        if jobIdFound:
            successes = successes + 1
        else:
            failures = failures + 1
            
        # We only loop once if the separate jobs are combined into one.
        if not separateCoopJobs:
            break
        
    if coopRendering and scriptDialog.GetValue( "AutoMergeBox" ):
        jobDependencies = ""
        for jobId in jobIds:
            jobDependencies = jobDependencies + jobId + ","
        jobDependencies = jobDependencies.strip( "," )
        
        jobName = scriptDialog.GetValue( "NameBox" ) + " - Merge Job"
        
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "maxwell_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Maxwell" )
        writer.WriteLine( "Name=%s" % jobName )
        writer.WriteLine( "BatchName=%s" % batchName )
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "ConcurrentTasksBox" ) )
        writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
        
        writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
        if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % jobDependencies )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        
        if( len( outputFile ) > 0 ):
            if( singleFile ):
                writer.WriteLine( "OutputFilename0=%s" % outputFile )
            else:
                directory = Path.GetDirectoryName( outputFile )
                filename = Path.GetFileNameWithoutExtension( outputFile )
                extension = Path.GetExtension( outputFile )
                writer.WriteLine( "OutputFilename0=%s" % Path.Combine( directory, filename + "####" + extension ) )
        
        elif( len( mxiFile ) > 0 ):
            directory = Path.GetDirectoryName( mxiFile )
            writer.WriteLine( "OutputDirectory0=%s" % directory )
        
        # Integration
        extraKVPIndex = 0
        groupBatch = False
        
        if integration_dialog.IntegrationProcessingRequested():
            extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "maxwell_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Version=%s" % str(version) )
        writer.WriteLine( "SingleFile=%d" % singleFile )
        writer.WriteLine( "MaxwellFile=%s" % sceneFile )
        writer.WriteLine( "OutputFile=%s" % outputFile )
        writer.WriteLine( "MxiFile=%s" % mxiFile )
        
        if( scriptDialog.GetValue( "ResumeBox" ) ):
            writer.WriteLine( "ResumeFromMxiFile=True" )
        else:
            writer.WriteLine( "ResumeFromMxiFile=False" )
        
        writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )        
        writer.WriteLine( "CoopRendering=True" )
        writer.WriteLine( "CoopJobs=%d" % coopJobs )
        writer.WriteLine( "DeleteFiles=%s" % scriptDialog.GetValue( "DeleteFilesBox" ) )
        writer.WriteLine( "FailOnMissingFiles=%s" % scriptDialog.GetValue( "FailOnMissingFilesBox" ) )
        writer.WriteLine( "MergeJob=True" )
        
        writer.Close()
        
        # Setup the command line arguments.
        arguments = StringCollection()
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        
        # Now submit the job.
        exitCode = ClientUtils.ExecuteCommand( arguments )
        if( exitCode == 0 ):
            successes = successes + 1
        else:
            failures = failures + 1
        
    if not resultsDisplayed:
        scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )
