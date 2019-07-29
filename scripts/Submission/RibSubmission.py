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
    scriptDialog.SetTitle( "Submit RIB Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'RIB' ) )
    
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

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "" )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering. ", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render. " )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Rib Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "RIB Files", 1, 0, "The RIB files to be rendered (can be ASCII or binary formatted). These files should be network accessible. ", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "RIB Files (*.rib);;All files (*)", 1, 1, colSpan=2 )
    sceneBox.ValueModified.connect(SceneFileChanged)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 2, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 2, 1 )
    scriptDialog.AddHorizontalSpacerToGrid("RHSpacer1", 2, 2 )

    scriptDialog.AddControlToGrid( "RendererLabel", "LabelControl", "Renderer", 3, 0, "The renderer that will be used to render the RIB files. ", False )
    scriptDialog.AddComboControlToGrid( "RendererBox", "ComboControl", "3delight", ("3delight","Air","Aqsis","BMRT","Entropy","Pixie","RenderDotC","RenderMan","RenderPipe"), 3, 1 )

    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Command Line Options", 4, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "CommandLineLabel", "LabelControl", "Additional Arguments", 5, 0, "Specify additional command line arguments you would like to pass to the RIB renderer. See the documentation for your particular RIB renderer for additional arguments. ", False )
    scriptDialog.AddControlToGrid( "CommandLineBox", "TextControl", "", 5, 1, colSpan=2 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "RibMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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

    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","RendererBox","CommandLineBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    SceneFileChanged( None )
    
    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "RibSettings.ini" )

def ParseRibFile( filename ):
    results = [""] * 2
    frameString = "0"
    #overrideOutput = False
    
    try:
        startFrame = 0
        endFrame = 0
        initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
        paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
    
        #~ if initFrame >= 0:
            #~ # Valid frame number
            #~ startFrame = FrameUtils.GetLowerFrameRange(filename,initFrame,paddingSize)
            #~ endFrame = FrameUtils.GetUpperFrameRange(filename,initFrame,paddingSize)
            #~ if startFrame >= 0 and endFrame >= 0:
                #~ if startFrame == endFrame:
                    #~ frameString = str(startFrame)
                #~ else:
                    #~ frameString = str(startFrame) + "-" + str(endFrame)
        
        if paddingSize > 0:
            # Valid frame number
            startFrame = FrameUtils.GetLowerFrameRange(filename,initFrame,paddingSize)
            endFrame = FrameUtils.GetUpperFrameRange(filename,initFrame,paddingSize)
            if startFrame == endFrame:
                frameString = str(startFrame)
            else:
                frameString = str(startFrame) + "-" + str(endFrame)
        
        #~ if File.Exists( filename ):
            #~ displayRegex = Regex( " *Display \".*\"" )
            #~ for line in File.ReadAllLines( filename ):
                #~ match = displayRegex.Match( line )
                #~ if( match.Success ):
                    #~ overrideOutput = True
                    #~ break
        
        results[0] = frameString
        #results[1] = overrideOutput
    except:
        results = None
    
    return results

def SceneFileChanged( *args ):
    global scriptDialog
    
    results = ParseRibFile( scriptDialog.GetValue( "SceneBox" ) )
    if results != None:
        scriptDialog.SetValue( "FramesBox", results[ 0 ] )
        #scriptDialog.SetEnabled( "OutputBox", results[ 1 ] )
    else:
        scriptDialog.SetValue( "FramesBox", "" )
        #scriptDialog.SetEnabled( "OutputBox", False )
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    
    renderer = scriptDialog.GetValue( "RendererBox" )
    if( renderer == "3delight" ):
        renderer = "ThreeDelight"
    
    # Check if maya files.
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "Rib file %s does not exist" % sceneFile, "Error" )
        return
    elif( PathUtils.IsPathLocal( sceneFile ) ):
        result = scriptDialog.ShowMessageBox( "The rib file " + sceneFile + " is local, are you sure you want to continue", "Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    # Parse the rib file for output paths
    outputPaths = []
    displayRegex = Regex( "Display \"([^\"]*)\"" )
    for line in File.ReadAllLines( sceneFile ):
        match = displayRegex.Match( line )
        if( match.Success ):
            outputPath = match.Groups[ 1 ].Value
            
            # Additional display paths are prefixed with a '+', so let's strip it if it's there
            outputPath = outputPath.lstrip( "+" )
            
            # Only rooted paths can be supported
            if PathUtils.IsPathRooted( outputPath ):
                outputFolder = Path.GetDirectoryName( outputPath )
                outputFile = Path.GetFileName( outputPath )
                
                # If the file is padded, we need to replace the number string with #'s
                padding = FrameUtils.GetFrameStringFromFilename(outputFile)
                if len(padding) > 0:
                    newPadding = "#"
                    while len(newPadding) < len(padding):
                        newPadding += "#"
                    outputFile = FrameUtils.SubstituteFrameNumber( outputFile, newPadding )
                    outputPath = Path.Combine( outputFolder, outputFile )
                
                # If we hit a duplicate path, assume that we have all the paths we need. This way, if a single
                # rib contains an animation, we don't walk through the entire file.
                if not outputPath in outputPaths:
                    outputPaths.append( outputPath )
                else:
                    break
    
    
    outputFile = ""
    if len(outputPaths):
        outputFile = outputPaths[0]
    # Check if Integration options are valid.
    if not integration_dialog.CheckIntegrationSanity( outputFile ):
        return
    
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return
    
    # Check command line options.
    commandLine = scriptDialog.GetValue( "CommandLineBox" ).strip()
    if( renderer == "RenderPipe" and len( commandLine ) == 0 ):
        scriptDialog.ShowMessageBox( "To render with RenderPipe, you must specify the RenderDrive you want to render on in the command line arguments.\nAny additional command line arguments you wish to use must be specified before the RenderDrive. For example, if you\nwant to render on a RenderDrive with IP address 192.0.1.200, and you wanted to override the image resolution, you\nwould specify the following in the additional command line options:\n\n-x 640 -y 480 192.0.1.200", "Error" )
        return
    
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "rib_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=RIB" )
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
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    
    writer.WriteLine( "Frames=%s" % frames )
    writer.WriteLine( "ChunkSize=1" )
    
    outputIndex = 0
    for outputPath in outputPaths:
        writer.WriteLine( "OutputFilename%s=%s" % (outputIndex,outputPath) )
        outputIndex += 1
    
    #if( len( outputFile ) > 0 ):
    #	writer.WriteLine( "OutputFilename0=%s" % outputFile )
    
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "rib_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Renderer=%s" % renderer )
    writer.WriteLine( "RibFile=%s" % sceneFile )
    #writer.WriteLine( "OutputFile=%s" % outputFile )
    writer.WriteLine( "CommandLineOptions=%s" % commandLine )	
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
