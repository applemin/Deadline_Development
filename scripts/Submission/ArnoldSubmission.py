from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

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

ProjectManagementOptions = [ "Shotgun", "FTrack" ]
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
    scriptDialog.SetTitle( "Submit Arnold Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( "Arnold" ) )
    
    scriptDialog.AddTabControl( "Tabs", 0, 0 )
    
    scriptDialog.AddTabPage( "Job Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1)

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
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.", False )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Arnold Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Arnold File", 1, 0, "The Arnold file(s) to be rendered. If you are submitting a sequence of .ass files, select one of the numbered frames in the sequence, and the frame range will automatically be detected.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Arnold Files (*.ass);;All Files (*)", 1, 1, colSpan=2 )
    sceneBox.ValueModified.connect( SceneBoxChanged )

    scriptDialog.AddControlToGrid( "OutputLabel","LabelControl","Output File (optional)",2, 0, "The output file. If left blank, Arnold will save the output to the location defined in the .ass file.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox","FileSaverControl","", "EXR (*.exr);;JPG (*.jpg);;PNG (*.png);;TIFF (*.tif);;All Files (*)", 2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render. If you are submitting a sequence of .ass files, the frames you choose to render should correspond to the numbers in the .ass files.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoFramesBox", "CheckBoxControl", False, "Calculate Frames From Arnold File", 3, 2, "If enabled, the frame list will be calculated based on the selected input file." )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 4, 0, "The version of Arnold to render with.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "Release", ("Beta","Release"), 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "LocalRendering", "CheckBoxControl", False, "Enable Local Rendering", 4, 2, "If enabled, the frames will be rendered locally, and then copied to their final network location. This requires the output path to be specified." )

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 5, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 5, 1 )
    disableFrameInterpretation = scriptDialog.AddSelectionControlToGrid( "DisableFrameInterpretation", "CheckBoxControl", False, "Disable Frame Interpretation", 5, 2, "If enabled, Deadline won't try to interpret if there's frame padding in the input file, allowing version numbers in the input file." )
    disableFrameInterpretation.ValueModified.connect( DisableFrameInterpretationChanged )

    scriptDialog.AddControlToGrid( "ThreadsLabel","LabelControl","Threads", 6, 0, "The number of threads to use for rendering.", False )
    scriptDialog.AddRangeControlToGrid( "ThreadsBox","RangeControl",0,0,256,0,1, 6, 1 )

    scriptDialog.AddControlToGrid( "VerboseLabel","LabelControl","Verbosity", 7, 0, "The verbosity level for the render output.", False )
    scriptDialog.AddRangeControlToGrid( "VerboseBox","RangeControl",4,0,6,0,1, 7, 1 )

    scriptDialog.AddControlToGrid( "CommandLineLabel","LabelControl","Command Line Args", 8, 0, "Specify additional command line arguments you would like to pass to the Arnold renderer. ", False )
    scriptDialog.AddControlToGrid( "CommandLineBox","TextControl","", 8, 1, colSpan=2 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage( "Advanced Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Additional Plugin Folders (Optional)", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "PluginLabel1","LabelControl","Plugin Folder 1", 1, 0, "Specify up to three additional plugin folders that Arnold should use when rendering.", False )
    scriptDialog.AddSelectionControlToGrid( "PluginBox1","FolderBrowserControl","","", 1, 1 )

    scriptDialog.AddControlToGrid( "PluginLabel2","LabelControl","Plugin Folder 2", 2, 0, "Specify up to three additional plugin folders that Arnold should use when rendering.", False )
    scriptDialog.AddSelectionControlToGrid( "PluginBox2","FolderBrowserControl","","", 2, 1 )

    scriptDialog.AddControlToGrid( "PluginLabel3","LabelControl","Plugin Folder 3", 3, 0, "Specify up to three additional plugin folders that Arnold should use when rendering.", False )
    scriptDialog.AddSelectionControlToGrid( "PluginBox3","FolderBrowserControl","","",3, 1 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "ArnoldMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect( SubmitButtonPressed )
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect( integration_dialog.CloseProjectManagementConnections )
    closeButton.ValueModified.connect( scriptDialog.closeEvent )
    scriptDialog.EndGrid()
    
    #Application Box must be listed before version box or else the application changed event will change the version
    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","OutputBox","LocalRendering","ThreadsBox","VersionBox","BuildBox","DisableFrameInterpretation","VerboseBox","CommandLineBox","PluginBox1","PluginBox2","PluginBox3","AutoFramesBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    SceneBoxChanged( None )
    DisableFrameInterpretationChanged( None )
    scriptDialog.ShowDialog( False )
    
def SceneBoxChanged(*args):
    global scriptDialog
    
    # Only update the frames box if this option is enabled.
    if not scriptDialog.GetValue( "AutoFramesBox" ):
        return
    
    filename = scriptDialog.GetValue( "SceneBox" )
    frameString = ""
    
    try:
        startFrame = 0
        endFrame = 0
        initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
        paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
        
        # Check for valid frame number.
        #~ if initFrame >= 0:
            #~ startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
            #~ endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
            
            #~ if startFrame >= 0 and endFrame >=0:
                #~ if startFrame == endFrame:
                    #~ frameString = str(startFrame)
                #~ else:
                    #~ frameString = str(startFrame) + "-" + str(endFrame)

        startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
        endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
        if startFrame == endFrame:
            frameString = str(startFrame)
        else:
            frameString = str( startFrame ) + "-" + str( endFrame )
        
    except:
        frameString = ""
        
    scriptDialog.SetValue( "FramesBox", frameString )
    
def DisableFrameInterpretationChanged( *args ):
    global scriptDialog
    
    disableFrameInterpretation = scriptDialog.GetValue( "DisableFrameInterpretation" )
    if disableFrameInterpretation:
        scriptDialog.SetValue( "FramesBox", "1" )
    
    scriptDialog.SetEnabled( "FramesLabel", not disableFrameInterpretation )
    scriptDialog.SetEnabled( "FramesBox", not disableFrameInterpretation )
    scriptDialog.SetEnabled( "AutoFramesBox", not disableFrameInterpretation )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "ArnoldSettings.ini" )

def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog
    
    # Check if Arnold files exist.
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "Arnold file %s does not exist" % sceneFile, "Error" )
        return
    elif (PathUtils.IsPathLocal(sceneFile)):
        result = scriptDialog.ShowMessageBox( "The Arnold file " + sceneFile + " is local, are you sure you want to continue?","Warning", ( "Yes", "No" ) )
        if(result=="No"):
            return
                
    # Check the output folder
    outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
    if len(outputFile) > 0:
        if(not Directory.Exists(Path.GetDirectoryName(outputFile))):
            scriptDialog.ShowMessageBox( "The directory of the output file does not exist:\n" + Path.GetDirectoryName(outputFile), "Error" )
            return
        elif (PathUtils.IsPathLocal(outputFile)):
            result = scriptDialog.ShowMessageBox( "The output file " + outputFile + " is local, are you sure you want to continue?","Warning", ( "Yes", "No" ) )
            if(result=="No"):
                return
            
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return
    
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( ):
        return
        
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "arnold_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Arnold" )
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
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" ) ) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    
    writer.WriteLine( "Frames=%s" % frames )
    writer.WriteLine( "ChunkSize=1" )
    
    if len( outputFile ) > 0:
        tempOutputFile = outputFile
        
        currPadding = FrameUtils.GetFrameStringFromFilename( sceneFile )
        paddingSize = len( currPadding )
        if paddingSize > 0:
            outputPath = Path.GetDirectoryName( outputFile )
            outputFileName = Path.GetFileNameWithoutExtension( outputFile )
            outputExtension = Path.GetExtension( outputFile )
            
            newPadding = "#"
            while len(newPadding) < paddingSize:
                newPadding = newPadding + "#"
            
            tempOutputFile = Path.Combine( outputPath, outputFileName + newPadding + outputExtension )
        
        writer.WriteLine( "OutputFilename0=%s" % tempOutputFile )
    
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "arnold_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "InputFile=%s" % sceneFile )
    writer.WriteLine( "OutputFile=%s" % outputFile )
    writer.WriteLine( "LocalRendering=%s" % scriptDialog.GetValue( "LocalRendering" ) )
    writer.WriteLine( "DisableFrameInterpretation=%s" % scriptDialog.GetValue( "DisableFrameInterpretation" ) )
    writer.WriteLine( "PluginFolder1=%s" % scriptDialog.GetValue( "PluginBox1" ) )
    writer.WriteLine( "PluginFolder2=%s" % scriptDialog.GetValue( "PluginBox2" ) )
    writer.WriteLine( "PluginFolder3=%s" % scriptDialog.GetValue( "PluginBox3" ) )
    writer.WriteLine( "Threads=%s" % scriptDialog.GetValue( "ThreadsBox" ) )
    writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )
    writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
    writer.WriteLine( "CommandLineOptions=%s" % scriptDialog.GetValue( "CommandLineBox" ) )
    writer.WriteLine( "Verbose=%s" % scriptDialog.GetValue( "VerboseBox" ) )
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
