import os

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
errors = ""
warnings = ""

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit VDenoise Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'VDenoise' ) )

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

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )
    
    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.AddTabPage("VDenoise Options")
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "VDenoise Options", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input Image(s)", 1, 0, "Specify the input .vrimg or .exr file; can contain wildcards, f.e. \"c:\\path\\to\\files\\sequence_????.exr\" to denoise a sequence of frames.", False )
    scriptDialog.AddSelectionControlToGrid( "InputBox", "FileBrowserControl", "", "OpenEXR (*.exr);;V-Ray Image (*.vrimg);;All Files (*)", 1, 1, colSpan=3 )
    
    useFramesCheck = scriptDialog.AddSelectionControlToGrid( "UseFramesCheck", "CheckBoxControl", False, "Render Frame Range ", 2, 0, "If enabled, will only render the frames specified in the frame list field.", colSpan=2 )
    useFramesCheck.ValueModified.connect( UseFrameListModified )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 2, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 3, 3 )

    scriptDialog.AddControlToGrid( "ModeLabel", "LabelControl", "Render Mode", 4, 0, "Select one of three defined presets for radius/threshold/noise level multiplier, or select user defined settings.", False )
    scriptDialog.AddComboControlToGrid( "ModeBox", "ComboControl", "Default", ( "Strong", "Default", "Mild" ), 4, 1 )
    
    scriptDialog.AddControlToGrid( "BoostLabel", "LabelControl", "Boost Preset", 4, 2, "Boost the effect of the selected preset.", False )
    scriptDialog.AddRangeControlToGrid( "BoostBox", "RangeControl", 0, 0, 2, 0, 1, 4, 3 )
    
    scriptDialog.AddSelectionControlToGrid( "SkipExistingCheck", "CheckBoxControl", False, "Skip Existing Images ", 5, 0, "Skip an input image if the corresponding output image already exists.", colSpan=2 )
    scriptDialog.AddSelectionControlToGrid( "ElementsCheck", "CheckBoxControl", False, "Denoise Render Elements", 5, 2, "If False, the colors in the final image are denoised in one pass;\nwhen True, the render elements are denoised separately and\nthen composited together.\n(default is False - single pass RGB denoising only)", colSpan=2 )
    
    scriptDialog.AddSelectionControlToGrid( "GPUCheck", "CheckBoxControl", False, "Use GPU", 6, 0, "If checked then, attempt to use the best OpenCL, fall back to CPU if unsuccessful.", colSpan=2 )
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Advanced Options", 7, 0, colSpan=4 )
    
    overrideThresholdCheck = scriptDialog.AddSelectionControlToGrid( "OverrideThresholdCheck", "CheckBoxControl", False, "Override Threshold", 8, 0, "Override the threshold for denoising.  This is required if your input image does not contain a noise level render element.", colSpan=2 )
    overrideThresholdCheck.ValueModified.connect( OverrideThresholdModified )
    
    scriptDialog.AddControlToGrid( "ThresholdLabel", "LabelControl", "Threshold", 8, 2, "Specifies threshold for denoising when noise levels render element is missing. Typically equal to the noise threshold for AA in V-Ray. (default is 0.001 and the denoiser relies on the noise level render element)", False )
    scriptDialog.AddRangeControlToGrid( "ThresholdBox", "RangeControl", 0.001, 0, 10, 6, 0.001, 8, 3 )
    
    overrideStrengthCheck = scriptDialog.AddSelectionControlToGrid( "OverrideStrengthCheck", "CheckBoxControl", False, "Override Strength", 9, 0, "Override the Denoiser Strength.", colSpan=2 )
    overrideStrengthCheck.ValueModified.connect( OverrideStrengthModified )
    
    scriptDialog.AddControlToGrid( "StrengthLabel", "LabelControl", "Denoiser Strength", 9, 2, "The main denoiser control. Larger values remove noise more aggressively but may blur the image too much.", False )
    scriptDialog.AddRangeControlToGrid( "StrengthBox", "RangeControl", 1, 0, 1000000, 2, 0.1, 9, 3 )
    
    overrideRadiusCheck = scriptDialog.AddSelectionControlToGrid( "OverrideRadiusCheck", "CheckBoxControl", False, "Override Radius", 10, 0, "Override the Pixel Radius.", colSpan=2 )
    overrideRadiusCheck.ValueModified.connect( OverrideRadiusModified )
    
    scriptDialog.AddControlToGrid( "RadiusLabel", "LabelControl", "Pixel Radius", 10, 2, "Specifies pixel radius for denoising. Larger values slow down the denoiser, but may produce smoother results.", False )
    scriptDialog.AddRangeControlToGrid( "RadiusBox", "RangeControl", 10, 0, 1000000, 1, 1, 10, 3 )
    
    scriptDialog.AddSelectionControlToGrid( "AutoRadiusCheck", "CheckBoxControl", False, "Automatically adjust Radius", 11, 0, "Automatically adjust the denoising radius based on the noise level render element. Setting this to 1 may slow down the denoiser quite a bit for more noisy images.", colSpan=2 )
     
    scriptDialog.AddControlToGrid( "BlendLabel", "LabelControl", "Frame Blend", 11, 2, "Use N adjacent frames when denoising animations. This reduces flickering between adjacent animation frames.", False )
    scriptDialog.AddRangeControlToGrid( "BlendBox", "RangeControl", 1, 0, 1000000, 0, 1, 11, 3 )
    
    scriptDialog.AddControlToGrid( "StripsLabel", "LabelControl", "Number of Strips", 12,0, "Force image split in N strips. (default is -1 - use split count heuristic)", False )
    scriptDialog.AddRangeControlToGrid( "StripsBox", "RangeControl", -1, -1, 1000000, 0, 1, 12, 1 )
       
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.EndTabControl()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 23, 0 )

    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 23, 3, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 23, 4, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","ThreadsBox","SubmitSceneBox","InputBox","ModeBox","BoostBox","SkipExistingCheck","ElementsCheck","GPUCheck","OverrideThresholdCheck","ThresholdBox","OverrideStrengthCheck","StrengthBox","OverrideRadiusCheck","RadiusBox", "AutoRadiusCheck","BlendBox","StripsBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    OverrideThresholdModified( None )
    OverrideStrengthModified( None )
    OverrideRadiusModified( None )
    UseFrameListModified( None )
    
    scriptDialog.ShowDialog( False )
        
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "VDenoiseSettings.ini" )   

def OverrideThresholdModified( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "OverrideThresholdCheck" )
    
    scriptDialog.SetEnabled( "ThresholdLabel", enabled )
    scriptDialog.SetEnabled( "ThresholdBox", enabled )
    
def OverrideStrengthModified( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "OverrideStrengthCheck" )
    
    scriptDialog.SetEnabled( "StrengthLabel", enabled )
    scriptDialog.SetEnabled( "StrengthBox", enabled )
    
def OverrideRadiusModified( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "OverrideRadiusCheck" )
    
    scriptDialog.SetEnabled( "RadiusLabel", enabled )
    scriptDialog.SetEnabled( "RadiusBox", enabled )    

def UseFrameListModified( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "UseFramesCheck" )

    scriptDialog.SetEnabled( "FramesBox", enabled )
    scriptDialog.SetEnabled( "FramesLabel", enabled )
    scriptDialog.SetEnabled( "ChunkSizeBox", enabled )
    scriptDialog.SetEnabled( "ChunkSizeLabel", enabled )

def SubmitButtonPressed( *args ):
    global scriptDialog
    global errors
    global warnings

    warnings = ""
    errors = ""
    inputPath = scriptDialog.GetValue( "InputBox" )
    if inputPath == "":
        errors += "No input path selected.\n"
    elif PathUtils.IsPathLocal( inputPath ):
        warnings += "The selected input path " + inputPath + " is local.\n"
    
    if bool( scriptDialog.GetValue( "UseFramesCheck" ) ):
        frames = scriptDialog.GetValue( "FramesBox" )
        if( not FrameUtils.FrameRangeValid( frames ) ):
            errors += "Frame range %s is not valid.\n\n" % frames

    if len( errors ) > 0:
        errors = "The following errors were encountered:\n%s\nPlease resolve these issues and submit again.\n" % errors
        scriptDialog.ShowMessageBox( errors, "Errors" )
        return
    else:
        if len( warnings ) > 0:
            result = scriptDialog.ShowMessageBox( "Warnings:\n%s\nDo you still want to continue?" % warnings, "Warnings", ( "Yes","No" ) )
            if result == "No":
                return

        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "vdenoise_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=VDenoise" )
        writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
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
        if( bool(scriptDialog.GetValue( "IsBlacklistBox" ) ) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        if( bool( scriptDialog.GetValue( "SubmitSuspendedBox" ) ) ):
            writer.WriteLine( "InitialStatus=Suspended" )

        if bool( scriptDialog.GetValue( "UseFramesCheck" ) ):
            frames = scriptDialog.GetValue( "FramesBox" )
            chunkSize = scriptDialog.GetValue( "ChunkSizeBox" )
        else:
            frames = 1
            chunkSize = 1

        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % chunkSize )
            
        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "vdenoise_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
        writer.WriteLine( "InputPath=%s" % inputPath )        
        writer.WriteLine( "DenoiseMode=%s" % scriptDialog.GetValue("ModeBox" ) )
        writer.WriteLine( "Boost=%s" % scriptDialog.GetValue("BoostBox" ) )
        writer.WriteLine( "SkipExisting=%s" % scriptDialog.GetValue("SkipExistingCheck" ) )
        writer.WriteLine( "DenoiseElements=%s" % scriptDialog.GetValue("ElementsCheck" ) )
        writer.WriteLine( "UseGPU=%s" % scriptDialog.GetValue("GPUCheck" ) )
        writer.WriteLine( "OverrideThreshold=%s" % scriptDialog.GetValue("OverrideThresholdCheck" ) )
        writer.WriteLine( "Threshold=%s" % scriptDialog.GetValue("ThresholdBox" ) )
        writer.WriteLine( "OverrideStrength=%s" % scriptDialog.GetValue("OverrideStrengthCheck" ) )
        writer.WriteLine( "Strength=%s" % scriptDialog.GetValue("StrengthBox" ) )
        writer.WriteLine( "OverrideRadius=%s" % scriptDialog.GetValue("OverrideRadiusCheck" ) )
        writer.WriteLine( "PixelRadius=%s" % scriptDialog.GetValue("RadiusBox" ) )
        writer.WriteLine( "AdjustRadius=%s" % scriptDialog.GetValue("AutoRadiusCheck" ) )
        writer.WriteLine( "FrameBlend=%s" % scriptDialog.GetValue("BlendBox" ) )
        writer.WriteLine( "RenderStrips=%s" % scriptDialog.GetValue("StripsBox" ) )
        writer.WriteLine( "UsingFrames=%s" % scriptDialog.GetValue( "UseFramesCheck" ) )
        
        writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )