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
    global settings
    global scriptDialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Corona Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Corona' ) )
    
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
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.", False )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Corona Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Corona Version", 1, 0, "The version of Corona Standalone to use.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "2", ["1.4","1.5","1.6","1.7","2"], 1, 1 )
    versionBox.ValueModified.connect( VersionChanged )
    
    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Corona Scene", 2, 0, "The Corona scene file to be rendered. If submitting a multiple frame job, the frame number must be in the scene file name right before the file extension.", False )
    sceneBox=scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Corona Scene Files (*.scn)", 2, 1, colSpan=2 )
    
    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output File Directory", 3, 0, "The directory for the output to be saved to.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox","FolderBrowserControl","", "", 3, 1, colSpan=2 )
    
    scriptDialog.AddControlToGrid( "OutputFileNameLabel", "LabelControl", "Output File Name", 4,0, "The name prefix for the output file(s). If left blank the name prefix will be \"output\". No file extension should be included, as Corona automatically generates the appropriate extension.", False )
    scriptDialog.AddControlToGrid( "OutputFileNameBox", "TextControl", "", 4, 1, colSpan=2 )

    scriptDialog.AddSelectionControlToGrid( "OutputAlphaBox", "CheckBoxControl", False, "Save Alpha", 5, 1, "If enabled, saves the output image with alpha channel. Only some image formats support alpha channel.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputRawBox", "CheckBoxControl", False, "Save RAW", 5, 2, "If enabled, no tone mapping will be applied to the saved image (which is useful when saving high dynamic range images).", False )
    
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 6, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 6, 1 )
    checkBox = scriptDialog.AddSelectionControlToGrid( "SingleFrameBox", "CheckBoxControl", True, "Single Frame Job", 6, 2, "If enabled, the job will consist of a single frame. Otherwise, the scene file must have a frame number included in the name." )
    scriptDialog.SetEnabled( "FramesLabel", False )
    scriptDialog.SetEnabled( "FramesBox", False )
    checkBox.ValueModified.connect( SingleFrameChanged )
    
    scriptDialog.AddControlToGrid( "ConfigurationLabel", "LabelControl", "Configuration File(s)", 7, 0, "Configuration file(s) for the Corona Renderer.", False )
    scriptDialog.AddSelectionControlToGrid( "ConfigurationBox", "MultiFileBrowserControl", "", "Corona Configuration Files (*.conf)", 7, 1, colSpan=2 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage( "Advanced Options" )
    scriptDialog.AddGrid()
    
    overridePasses = scriptDialog.AddSelectionControlToGrid( "OverridePassesControl", "CheckBoxControl", False, "Override Maximum # of Passes", 0, 0, "You can override the configuration file setting for the maximum number of passes here if this is enabled.", False )
    scriptDialog.AddRangeControlToGrid( "MaxPassesBox", "RangeControl", 0, 0, 9999, 0, 1, 0, 1 )
    scriptDialog.SetEnabled( "MaxPassesBox", False )
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacerPasses", 0, 2 )
    overridePasses.ValueModified.connect( OverridePassesChanged )
    
    overrideTime = scriptDialog.AddSelectionControlToGrid( "OverrideRenderTimeControl", "CheckBoxControl", False, "Override Maximum Render Time", 1, 0, "You can override the configuration file setting for the maximum render time here if this is enabled.", False )
    scriptDialog.AddRangeControlToGrid( "RenderHourTimeBox", "RangeControl", 0, 0, 23, 0, 1, 1, 1 )
    scriptDialog.SetEnabled( "RenderHourTimeBox", False )
    scriptDialog.AddRangeControlToGrid( "RenderMinuteTimeBox", "RangeControl", 0, 0, 59, 0, 1, 1, 2 )
    scriptDialog.SetEnabled( "RenderMinuteTimeBox", False )
    scriptDialog.AddRangeControlToGrid( "RenderSecTimeBox", "RangeControl", 0, 0, 59, 0, 1, 1, 3 )
    scriptDialog.SetEnabled( "RenderSecTimeBox", False )
    overrideTime.ValueModified.connect( OverrideTimeChanged )
    
    overrideThread = scriptDialog.AddSelectionControlToGrid( "OverrideThreadControl", "CheckBoxControl", False, "Override Threads", 2, 0, "You can override the configuration file setting for the number of threads here if this is enabled.", False )
    scriptDialog.AddRangeControlToGrid( "ThreadBox", "RangeControl", 0, 0, 256, 0, 1, 2, 1)
    scriptDialog.SetEnabled( "ThreadBox", False )
    overrideThread.ValueModified.connect( OverrideThreadChanged )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect( SubmitButtonPressed )
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect( scriptDialog.closeEvent )
    scriptDialog.EndGrid()
    
    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","VersionBox","SceneBox","FramesBox","OutputBox","OutputAlphaBox","OutputRawBox","ConfigurationBox","OutputFileNameBox","SingleFrameBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    SingleFrameChanged( None )
    VersionChanged( None )
    
    scriptDialog.ShowDialog( False )

def GetCoronaVersions():
    """
    Returns a tuple containing two alternative representations of the Corona version selected by the user in the
    submission dialog.

    The first element in the tuple is a string representation of the dotted version number of Corona to use
    (e.g. "1.4").

    The second element in the tuple is itself a tuple of ints representing the components of the version number. This
    representation is useful since it respects lexicographic ordering when comparing two such tuples. For example,
    if the user specified version "1.0" would correspond to (1, 0)

    :return: A tuple containing two representations of the Corona version selected in the submission dialog
    """
    global scriptDialog

    strVersion = scriptDialog.GetValue("VersionBox")
    version = tuple(int(part) for part in strVersion.split("."))

    return strVersion, version

def VersionChanged( *args ):
    global scriptDialog

    _, version = GetCoronaVersions()
    scriptDialog.SetEnabled( "OutputAlphaBox", version >= (1, 5) )
    scriptDialog.SetEnabled( "OutputRawBox", version >= (1, 5) )

def OverridePassesChanged( *args ):
    global scriptDialog
    
    overridePasses = scriptDialog.GetValue("OverridePassesControl")
    scriptDialog.SetEnabled("MaxPassesBox", overridePasses)
    
def OverrideTimeChanged( *args ):
    global scriptDialog
    
    overrideTime = scriptDialog.GetValue("OverrideRenderTimeControl")
    scriptDialog.SetEnabled("RenderHourTimeBox", overrideTime)
    scriptDialog.SetEnabled("RenderMinuteTimeBox", overrideTime)
    scriptDialog.SetEnabled("RenderSecTimeBox", overrideTime)
    
def OverrideThreadChanged( *args ):
    global scriptDialog
    
    overrideThreads = scriptDialog.GetValue("OverrideThreadControl")
    scriptDialog.SetEnabled("ThreadBox", overrideThreads)
    
def SingleFrameChanged( *args ):
    global scriptDialog
    
    singleFrame = scriptDialog.GetValue("SingleFrameBox")
    scriptDialog.SetEnabled("FramesLabel", not singleFrame)
    scriptDialog.SetEnabled("FramesBox", not singleFrame)
   
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "CoronaSettings.ini" )
   
def SubmitButtonPressed( *args ):
    global scriptDialog
    
    sceneFile = scriptDialog.GetValue("SceneBox")
    
    #Check if the scene file exists
    if len(sceneFile) <= 0:
        scriptDialog.ShowMessageBox( "Must provide a Corona scene file.", "Error" )
        return
    
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "Corona Scene file %s does not exist" % sceneFile, "Error" )
        return
    elif (PathUtils.IsPathLocal(sceneFile)):
        result = scriptDialog.ShowMessageBox("The Corona Scene file " + sceneFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if(result=="No"):
            return
            
    # Check if Corona Config files exist
    configFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "ConfigurationBox" ), False )
    cFiles = ""
    for configFile in configFiles:
        if( not File.Exists( configFile ) ):
            scriptDialog.ShowMessageBox( "Corona configuration file %s does not exist" % configFile, "Error" )
            return
        #if the submit scene box is checked check if they are local, if they are warn the user
        elif( PathUtils.IsPathLocal( configFile ) ):
            result = scriptDialog.ShowMessageBox( "The Corona configuration file " + configFile + " is local, are you sure you want to continue?", "Warning", ("Yes","No") )
            if( result == "No" ):
                return
        cFiles = cFiles + configFile.replace("\\","/") + ","
    cFiles = cFiles[:-1]
            
    # Check the output folder
    outputFile = scriptDialog.GetValue("OutputBox").strip()
    
    if len(outputFile) <= 0:
        scriptDialog.ShowMessageBox( "Must provide an output directory.", "Error" )
        return
    
    if len(outputFile) > 0:
        if(not Directory.Exists(Path.GetDirectoryName(outputFile))):
            scriptDialog.ShowMessageBox( "The directory of the output file does not exist:\n" + Path.GetDirectoryName(outputFile), "Error" )
            return
        elif (PathUtils.IsPathLocal(outputFile)):
            result = scriptDialog.ShowMessageBox("The output file " + outputFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
            if(result=="No"):
                return
                
    outputName = scriptDialog.GetValue("OutputFileNameBox").strip()
    
    if outputName == None or outputName == "":
        outputName = "output.exr"
    
    outputPath = outputFile.replace("\\","/")
    if outputPath[len(outputPath)-1] != "/":
        outputName = "/"+outputName
        
    outputPath = outputPath + outputName
                
    # Check if a valid frame range has been specified if not single frame job
    singleFrame = scriptDialog.GetValue("SingleFrameBox")

    frames = scriptDialog.GetValue( "FramesBox" )
    if not singleFrame:
        if( not FrameUtils.FrameRangeValid( frames ) ):
            scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
            return
        
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "corona_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Corona" )
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
    if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )

    if outputPath != "":
        directory = Path.GetDirectoryName( outputPath )
        writer.WriteLine( "OutputDirectory0=%s" % directory )

    writer.WriteLine( "Frames=%s" % frames )
    writer.WriteLine( "ChunkSize=1" )
    
    writer.Close()
    
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "corona_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

    strVersion, version = GetCoronaVersions()
    
    writer.WriteLine( "Version=%s" % strVersion )
    writer.WriteLine( "SceneFile=" + sceneFile.replace("\\","/") )
    writer.WriteLine( "OutputFile=" + outputPath )

    if version >= (1, 5):
        writer.WriteLine( "OutputAlpha=%s" % scriptDialog.GetValue( "OutputAlphaBox" ) )
        writer.WriteLine( "OutputRaw=%s" % scriptDialog.GetValue( "OutputRawBox" ) )

    writer.WriteLine( "ConfigFiles="+ cFiles )
    writer.WriteLine( "SingleFrame=%s" % scriptDialog.GetValue("SingleFrameBox") )
    
    overridePasses = scriptDialog.GetValue( "OverridePassesControl" )
    if overridePasses:
        writer.WriteLine( "OverridePasses=True" )
        writer.WriteLine( "MaxPasses=%s" % scriptDialog.GetValue("MaxPassesBox") )
        
    overrideTime = scriptDialog.GetValue( "OverrideRenderTimeControl" )
    if overrideTime:
        writer.WriteLine( "OverrideRenderTime=True" )
        writer.WriteLine( "RenderHourTime=%s" % scriptDialog.GetValue( "RenderHourTimeBox" ) )
        writer.WriteLine( "RenderMinuteTime=%s" % scriptDialog.GetValue( "RenderMinuteTimeBox" ) )
        writer.WriteLine( "RenderSecTime=%s" % scriptDialog.GetValue( "RenderSecTimeBox" ) )        
        
    overrideThreads = scriptDialog.GetValue( "OverrideThreadControl" )
    if overrideThreads:
        writer.WriteLine( "OverrideThreads=True" )
        writer.WriteLine( "Threads=%s" % scriptDialog.GetValue( "ThreadBox") )
    
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
