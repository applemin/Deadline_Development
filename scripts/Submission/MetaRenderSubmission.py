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

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global scriptDialog
    global settings
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit MetaRender Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'MetaRender' ) )
    
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
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1)
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 4, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 5, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 5, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 6, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 6, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 7, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 8, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 8, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 8, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job." )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 9, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 9, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 9, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "MetaRender Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input File", 1, 0, "The input file. It could be a movie file or part of an image sequence.", False )
    scriptDialog.AddSelectionControlToGrid( "InputBox", "FileBrowserControl", "", "All Files (*)", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output File", 2, 0, "The file or image sequence name that MetaRender will write to.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "", "All Files (*)", 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "EncodingLabel", "LabelControl", "Encoding Profile", 3, 0, "The path to the encoding profile saved with the Profile Editor.", False )
    scriptDialog.AddSelectionControlToGrid( "EncodingBox", "FileBrowserControl", "", "Encoding Profiles (*.iepf);;All Files (*)", 3, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "BurnLabel", "LabelControl", "Burn File (optional)", 4, 0, "Superimpose the specified burn-in template over the output frames.", False )
    scriptDialog.AddSelectionControlToGrid( "BurnBox", "FileBrowserControl", "", "Burn-in Templates (*.burnin);;All Files (*)", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ModeLabel", "LabelControl", "Rendering Mode", 5, 0, "Use the CPU or GPU for rendering.", False )
    modeBox = scriptDialog.AddComboControlToGrid( "ModeBox", "ComboControl", "CPU", ("CPU","GPU"), 5, 1 )
    modeBox.ValueModified.connect(ModeChanged)
    scriptDialog.AddSelectionControlToGrid( "AlphaBox", "CheckBoxControl", False, "Strip Alpha Channel", 5, 2, "Strips the alpha channel from the input sequence during conversion." )

    scriptDialog.AddControlToGrid( "ThreadsLabel", "LabelControl", "Threads", 6, 0, "The number of render threads to use (CPU mode only).", False )
    scriptDialog.AddRangeControlToGrid( "ThreadsBox", "RangeControl", 1, 1, 256, 0, 1, 6, 1 )
    draftBox = scriptDialog.AddSelectionControlToGrid( "DraftBox", "CheckBoxControl", False, "Draft Mode", 6, 2, "Speed up rendering for non-critical color work (GPU mode only).")
    draftBox.ValueModified.connect(DraftChanged)
    scriptDialog.AddSelectionControlToGrid( "CPUMasksBox", "CheckBoxControl", False, "Render CPU Masks", 6, 3, "Uses high quality mask rendering instead of low quality GPU-based masks (GPU mode with Draft enabled only)." )

    flexBox = scriptDialog.AddSelectionControlToGrid( "FlexBox", "CheckBoxControl", False, "Write Flex File", 7, 1, "Writes a flex file for the entire timeline." )
    flexBox.ValueModified.connect(FlexChanged)
    scriptDialog.AddSelectionControlToGrid( "TakesBox", "CheckBoxControl", False, "Render Takes Into Subfolders", 7, 2, "If the Flex File option is enabled, render takes into subfolders.", colSpan=2 )

    scriptDialog.AddControlToGrid( "CoreCommandLineLabel", "LabelControl", "Core Command Args", 8, 0, "Specify additional Core Command Line arguments (the basic command line options for all IRIDAS applications).", False )
    scriptDialog.AddControlToGrid( "CoreCommandLineBox", "TextControl", "", 8, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "CommandLineLabel", "LabelControl", "MetaRender Args", 9, 0, "Specify additional MetaRender-specific command line arguments.", False )
    scriptDialog.AddControlToGrid( "CommandLineBox", "TextControl", "", 9, 1, colSpan=3 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","IsBlacklistBox","MachineListBox","LimitGroupBox","InputBox","OutputBox","EncodingBox","BurnBox","ModeBox","AlphaBox","ThreadsBox","CPUMasksBox","FlexBox","TakesBox","CoreCommandLineBox","CommandLineBox","DraftBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    DraftChanged(None)
    ModeChanged(None)
    FlexChanged(None)
    
    scriptDialog.ShowDialog( True )

def DraftChanged(*args):
    global scriptDialog
    
    mode = scriptDialog.GetValue( "ModeBox" )
    scriptDialog.SetEnabled( "CPUMasksBox", mode == "GPU" and scriptDialog.GetValue( "DraftBox" ) )

def ModeChanged(*args):
    global scriptDialog
    
    mode = scriptDialog.GetValue( "ModeBox" )
    scriptDialog.SetEnabled( "ThreadsLabel", mode == "CPU" )
    scriptDialog.SetEnabled( "ThreadsBox", mode == "CPU" )
    scriptDialog.SetEnabled( "DraftBox", mode == "GPU" )
    scriptDialog.SetEnabled( "CPUMasksBox", mode == "GPU" and scriptDialog.GetValue( "DraftBox" ) )
    #scriptDialog.SetEnabled( "CPUMasksBox", mode == "Draft" )

def FlexChanged(*args):
    global scriptDialog
    
    flex = scriptDialog.GetValue( "FlexBox" )
    scriptDialog.SetEnabled( "TakesBox", flex )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "MetaRenderSettings.ini" )
    
def SubmitButtonPressed(*args):
    global scriptDialog
    
    # Check the input file.
    inputFile = scriptDialog.GetValue( "InputBox" ).strip()
    
    if inputFile == "":
        scriptDialog.ShowMessageBox( "Missing Input File!", "Error" )
        return

    if not File.Exists( inputFile ):
        scriptDialog.ShowMessageBox( "The input file " + inputFile + " does not exist", "Error" )
        return
    elif PathUtils.IsPathLocal( inputFile ):
        result = scriptDialog.ShowMessageBox( "The input file " + inputFile + " is local, are you sure you want to continue", "Warning", ("Yes","No") )
        if result == "No":
            return
    
    # Need to replace padding with #'s for MetaRender.
    paddingSize = FrameUtils.GetPaddingSizeFromFilename( inputFile )
    if paddingSize > 0:
        padding = "#"
        while len(padding) < paddingSize:
            padding += "#"
        inputFile = FrameUtils.SubstituteFrameNumber( inputFile, padding )
    
    # Check the output file.
    outputFile = scriptDialog.GetValue( "OutputBox" ).strip()

    if outputFile == "":
        scriptDialog.ShowMessageBox( "Missing Output File!", "Error" )
        return

    if not Directory.Exists( Path.GetDirectoryName( outputFile ) ):
        scriptDialog.ShowMessageBox( "The directory for output file " + outputFile + " does not exist", "Error" )
        return
    elif PathUtils.IsPathLocal( outputFile ):
        result = scriptDialog.ShowMessageBox( "The output file " + outputFile + " is local, are you sure you want to continue", "Warning", ("Yes","No") )
        if result == "No":
            return
    
    # Check the encoding profile.
    encodingFile = scriptDialog.GetValue( "EncodingBox" ).strip()
    if not File.Exists( encodingFile ):
        scriptDialog.ShowMessageBox( "The encoding file " + encodingFile + " does not exist", "Error" )
        return
    
    # Check the burn file if necessary.
    burnFile = scriptDialog.GetValue( "BurnBox" ).strip()
    if burnFile != "":
        if not File.Exists( burnFile ):
            scriptDialog.ShowMessageBox( "The burn file " + burnFile + " does not exist", "Error" )
            return
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "metarender_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=MetaRender" )
    writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
    writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
    writer.WriteLine( "MachineLimit=1" )
    
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
    
    if outputFile != "":
        directory = Path.GetDirectoryName( outputFile )
        writer.WriteLine( "OutputDirectory0=%s" % directory )

        tempOutputFile = outputFile
        currPadding = FrameUtils.GetFrameStringFromFilename( outputFile )
        paddingSize = len( currPadding )
        
        if paddingSize > 0:
            newPadding = "#"
            while len(newPadding) < paddingSize:
                newPadding += "#"

            outputPath = Path.GetDirectoryName( outputFile )
            outputFile = FrameUtils.SubstituteFrameNumber( outputFile, newPadding )
            tempOutputFile = Path.Combine( outputPath, outputFile )
        
        writer.WriteLine( "OutputFilename0=%s" % tempOutputFile )

    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "metarender_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "InputFile=%s" % inputFile )
    writer.WriteLine( "OutputFile=%s" % outputFile )
    writer.WriteLine( "RenderingMode=%s" % scriptDialog.GetValue( "ModeBox" ) )
    writer.WriteLine( "StripAlpha=%s" % scriptDialog.GetValue( "AlphaBox" ) )
    writer.WriteLine( "Threads=%s" % scriptDialog.GetValue( "ThreadsBox" ) )
    writer.WriteLine( "DraftMode=%s" % scriptDialog.GetValue( "DraftBox" ) )
    writer.WriteLine( "CPUMasks=%s" % scriptDialog.GetValue( "CPUMasksBox" ) )
    writer.WriteLine( "Flex=%s" % scriptDialog.GetValue( "FlexBox" ) )
    writer.WriteLine( "Takes=%s" % scriptDialog.GetValue( "TakesBox" ) )
    writer.WriteLine( "CoreCommandLine=%s" % scriptDialog.GetValue( "CoreCommandLineBox" ) )
    writer.WriteLine( "CommandLine=%s" % scriptDialog.GetValue( "CommandLineBox" ) )
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    arguments.Add( encodingFile )
    
    if burnFile != "":
        arguments.Add( burnFile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
