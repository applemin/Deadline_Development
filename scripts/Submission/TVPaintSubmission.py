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
    
    dialogWidth = 600
    labelWidth = 150
    dialogHeight = 666
    controlWidth = 156
    
    tabWidth = dialogWidth-16
    tabHeight = 616
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit TVPaint Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'TVPaint' ) )
    
    scriptDialog.AddTabControl("Job Options Tabs", dialogWidth+8, tabHeight)
    
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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "TVPaint Options", 0, 0, colSpan=6 )
    
    scriptDialog.AddControlToGrid( "Job Mode", "LabelControl", "Job Mode", 1, 0, "The different TVPaint job modes supported by Deadline.", False )
    jobModeBox = scriptDialog.AddComboControlToGrid( "JobModeBox", "ComboControl", "Sequence/Animation", ( "Sequence/Animation","Single Image","Script Job","Export Layers", "Single Layer" ), 1, 1, colSpan=4)
    jobModeBox.ValueModified.connect(JobModeBoxChanged)
    
    scriptDialog.AddControlToGrid( "AlphaSaveModeLabel", "LabelControl", "Alpha Save Mode", 2, 0, "The different Alpha Save Mode's supported by TVPaint.", False )
    scriptDialog.AddComboControlToGrid( "AlphaSaveModeBox", "ComboControl", "NoPreMultiply", ("NoPreMultiply","PreMultiply","NoAlpha","AlphaOnly"), 2, 1, colSpan=4)
    
    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "TVPaint File", 3, 0, "The TVPaint scene file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "TVPaint Files (*.tvpp);;All Files (*)", 3, 1, colSpan=5 )
    
    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output File", 4, 0,  "The output path to render to.", False )
    outputBox = scriptDialog.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "", "QUICKTIME (*.mov);;AVI (*.avi);;BMP (*.bmp);;CINEON (*.cin);;DEEP (*.dip);;DPX (*.dpx);;FLI (*.fli);;GIF (*.gif);;ILBM (*.iff);;JPEG (*.jpg);;PCX (*.pcx);;PNG (*.png);;PSD (*.psd);;SGI (*.rgb);;SOFTIMAGE (*.pic);;SUN (*.ras);;TGA (*.tga);;TIFF (*.tiff);;VPB (*.vpb)", 4, 1, colSpan=5 )
    outputBox.ValueModified.connect(OutputBoxChanged)
    
    scriptDialog.AddControlToGrid( "ScriptLabel", "LabelControl", "Script File", 5, 0,  "The render script to use.", False )
    scriptDialog.AddSelectionControlToGrid( "ScriptBox", "FileBrowserControl", "", "George Scripts (*.grg);;All Files (*)", 5, 1, colSpan=5 )
    
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 6, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 6, 1, colSpan=5 )
    
    scriptDialog.AddControlToGrid( "LayerLabel", "LabelControl", "Layer", 7, 0, "The layer to export for a Single Layer job.", False )
    scriptDialog.AddControlToGrid( "LayerBox", "TextControl", "", 7, 1, colSpan=5 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 8, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 8, 1, colSpan=4)
   
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit TVPaint Scene File With Job", 8, 5, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering.", "" )
    
    scriptDialog.AddControlToGrid( "FrameNumberLabel", "LabelControl", "Frame Number", 9, 0, "This is the index number of the frame that will be rendered for the job task. ", False )
    scriptDialog.AddRangeControlToGrid( "FrameNumberBox", "RangeControl", 0, 0, 1000000, 0, 1, 9, 1, colSpan=4 )
    scriptDialog.AddSelectionControlToGrid( "UseCameraBox", "CheckBoxControl", False, "Use Scene Camera", 9, 5, "If this option is enabled, TVPaint only renders what's in the camera's frame.", "" )
            
    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 10, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 10, 1, colSpan=3 )
    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 10, 4, "The version of TVPaint to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "11", ("11",), 10, 5)
    scriptDialog.EndGrid()
    
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "TVPaintMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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

    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","FrameNumberBox","ChunkSizeBox","VersionBox","SubmitSceneBox","UseCameraBox","OutputBox","BuildBox","JobModeBox","AlphaSaveModeBox","SubmitScriptBox","ScriptBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    OutputBoxChanged( None )
    JobModeBoxChanged( None )
        
    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "TVPaintSettings.ini" )

def JobModeBoxChanged( *args ):
    global scriptDialog
                                  
    if scriptDialog.GetValue( "JobModeBox" ) == "Sequence/Animation" or scriptDialog.GetValue( "JobModeBox" ) == "Script Job": 
        scriptDialog.SetEnabled( "ChunkSizeLabel", True)
        scriptDialog.SetEnabled( "ChunkSizeBox", True)
        scriptDialog.SetEnabled( "FramesLabel", True )
        scriptDialog.SetEnabled( "FramesBox", True)
        scriptDialog.SetEnabled( "FrameNumberLabel", False)
        scriptDialog.SetEnabled( "FrameNumberBox", False)
        scriptDialog.SetEnabled( "LayerLabel", False)
        scriptDialog.SetEnabled( "LayerBox", False)
        
    elif scriptDialog.GetValue( "JobModeBox" ) == "Export Layers":
        scriptDialog.SetEnabled( "ChunkSizeLabel", False)
        scriptDialog.SetEnabled( "ChunkSizeBox", False)
        scriptDialog.SetEnabled( "FramesLabel", False)
        scriptDialog.SetEnabled( "FramesBox", False)
        scriptDialog.SetEnabled( "FrameNumberLabel", False)
        scriptDialog.SetEnabled( "FrameNumberBox", False)
        scriptDialog.SetEnabled( "LayerLabel", False)
        scriptDialog.SetEnabled( "LayerBox", False)
        
    elif scriptDialog.GetValue( "JobModeBox" ) == "Single Image":
        scriptDialog.SetEnabled( "FrameNumberLabel", True)
        scriptDialog.SetEnabled( "FrameNumberBox", True)
        scriptDialog.SetEnabled( "ChunkSizeLabel", False)
        scriptDialog.SetEnabled( "ChunkSizeBox", False)
        scriptDialog.SetEnabled( "FramesLabel", False )
        scriptDialog.SetEnabled( "FramesBox", False)
        scriptDialog.SetEnabled( "LayerLabel", False)
        scriptDialog.SetEnabled( "LayerBox", False)
        
    elif scriptDialog.GetValue( "JobModeBox" ) == "Single Layer":
        scriptDialog.SetEnabled( "ChunkSizeLabel", False)
        scriptDialog.SetEnabled( "ChunkSizeBox", False)
        scriptDialog.SetEnabled( "FramesLabel", False)
        scriptDialog.SetEnabled( "FramesBox", False)
        scriptDialog.SetEnabled( "FrameNumberLabel", False)
        scriptDialog.SetEnabled( "FrameNumberBox", False)
        scriptDialog.SetEnabled( "LayerLabel", True)
        scriptDialog.SetEnabled( "LayerBox", True)
       
    scriptDialog.SetEnabled( "ScriptLabel", (scriptDialog.GetValue( "JobModeBox" ) == "Script Job"))
    scriptDialog.SetEnabled( "ScriptBox", (scriptDialog.GetValue( "JobModeBox" ) == "Script Job") )
    
def OutputBoxChanged( *args ):
    global scriptDialog
    
    outputFile = scriptDialog.GetValue( "OutputBox" )
    isMovie = IsMovie( outputFile )
    enableAlphaSaveMode = bool(GetOutputFormat( outputFile ) in "AVI QUICKTIME TGA TIFF SGI ILBM SUN")
    
    if scriptDialog.GetValue( "JobModeBox" ) == "Sequence/Animation":
        scriptDialog.SetEnabled( "ChunkSizeLabel", not isMovie )
        scriptDialog.SetEnabled( "ChunkSizeBox", not isMovie)
    
    scriptDialog.SetEnabled( "AlphaSaveModeLabel", enableAlphaSaveMode)
    scriptDialog.SetEnabled( "AlphaSaveModeBox", enableAlphaSaveMode)  
        
def IsMovie( outputFile ):
    return IsQt( outputFile ) or IsAVI( outputFile )

def IsQt( outputFile ):
    return outputFile.lower().endswith( ".mov" )

def IsAVI( outputFile ):
    return outputFile.lower().endswith( ".avi" )

def GetOutputFormat( outputFile ):
    global scriptDialog
    
    # Supported formats: 
    if outputFile.lower().endswith( ".mov" ):
        return "QUICKTIME"
    if outputFile.lower().endswith( ".avi" ):
        return "AVI"
    if outputFile.lower().endswith( ".bmp" ):
        return "BMP"
    if outputFile.lower().endswith( ".cin" ):
        return "CINEON"
    if outputFile.lower().endswith( ".dip" ):
        return "DEEP"
    if outputFile.lower().endswith( ".dpx" ):
        return "DPX"
    if outputFile.lower().endswith( ".fli" ):
        return "FLI"
    if outputFile.lower().endswith( ".gif" ):
        return "GIF"
    if outputFile.lower().endswith( ".iff" ):
        return "ILBM"
    if outputFile.lower().endswith( ".jpg" ):
        return "JPEG"
    if outputFile.lower().endswith( ".pcx" ):
        return "PCX"
    if outputFile.lower().endswith( ".png" ):
        return "PNG"
    if outputFile.lower().endswith( ".psd" ):
        return "PSD"
    if outputFile.lower().endswith( ".rgb" ):
        return "SGI"
    if outputFile.lower().endswith( ".pic" ):
        return "SOFTIMAGE"
    if outputFile.lower().endswith( ".ras" ):
        return "SUN"
    if outputFile.lower().endswith( ".tga" ):
        return "TGA"
    if outputFile.lower().endswith( ".tiff" ):
        return "TIFF"
    if outputFile.lower().endswith( ".vpb" ):
        return "VPB"
       
    return "UNKNOWN"

def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    
    version = scriptDialog.GetValue( "VersionBox" )
    isScriptJob = bool(scriptDialog.GetValue( "JobModeBox" ) == "Script Job")
    scriptFile = scriptDialog.GetValue( "ScriptBox" ).strip()
    outputFile =""
    outputFormat =""
    frames =""
    
    # Check the TVPaint files.
    sceneFile = scriptDialog.GetValue( "SceneBox" ).strip()
    if( len( sceneFile ) == 0 ):
        scriptDialog.ShowMessageBox( "No TVPaint file specified", "Error" )
        return
        
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "TVPaint file %s does not exist" % sceneFile, "Error" )
        return
    # If the submit scene box is checked check if they are local, if they are warn the user
    elif( not bool( scriptDialog.GetValue("SubmitSceneBox") ) and PathUtils.IsPathLocal( sceneFile ) ):
        result = scriptDialog.ShowMessageBox( "The TVPaint file " + sceneFile + " is local.\n\nAre you sure you want to continue?", "Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    # Check output file
    outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
    if len(outputFile) == 0:
        scriptDialog.ShowMessageBox( "Please specify an output file.", "Error" )
        return
    if(not Directory.Exists(Path.GetDirectoryName(outputFile))):
            scriptDialog.ShowMessageBox( "The directory of the output file %s does not exist." % Path.GetDirectoryName(outputFile), "Error" )
            return
    elif( PathUtils.IsPathLocal(outputFile) ):
        result = scriptDialog.ShowMessageBox( "The output file %s is local. Are you sure you want to continue?" % outputFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    outputFormat = GetOutputFormat( outputFile )
    if outputFormat == "UNKNOWN":
        scriptDialog.ShowMessageBox( "The output format is not supported. Valid formats are: \n "
                                        +"mov, avi, bmp, cin, dip, dpx, fli, gif, iff, jpg, pcx, png, psd, rgb, pic, ras, tga, tiff, vpb", "Error" )
        return
    elif outputFormat == "QUICKTIME":
        result = scriptDialog.ShowMessageBox( "Please note that, the export format '.mov(Quicktime)' is only available for 32bits version of TVPaint Animation. A different file format may generated if a different version of TVPaint is used.\n\nAre you sure you want to continue?", "Warning", ("Yes","No") )
        if( result == "No" ):
            return

    # Check if Integration options are valid.
    if not integration_dialog.CheckIntegrationSanity( outputFile ):
        return
            
    # Check if a valid frame range has been specified(if its a Sequence).
    if scriptDialog.GetValue( "JobModeBox" ) == "Sequence/Animation" or scriptDialog.GetValue( "JobModeBox" ) == "Script Job":
        frames = scriptDialog.GetValue( "FramesBox" )
        if( not FrameUtils.FrameRangeValid( frames ) ):
            scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
            return
    else:
         frames = scriptDialog.GetValue( "FrameNumberBox" )
    
    # Check the TVPaint render script.
    if isScriptJob and len( scriptFile ) == 0:
        scriptDialog.ShowMessageBox( "'Script Job Mode' was selected but no custom render script was specified. Please specify custom script.", "Error" )
        return
    
    successes = 0
    failures = 0
    
    # Submit scene file
    jobName = scriptDialog.GetValue( "NameBox" )
        
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "tvpaint_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=TVPaint" )
    writer.WriteLine( "Name=%s" % jobName )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
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
    elif len(outputFile) > 0:
        writer.WriteLine( "OutputFilename0=%s" % outputFile )
        
    writer.WriteLine( "Frames=%s" % frames )
    
    if IsMovie( outputFile ):
        writer.WriteLine( "ChunkSize=100000" )
    else:
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
    
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "tvpaint_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
    if( not bool(scriptDialog.GetValue( "SubmitSceneBox" )) ):
        writer.WriteLine( "SceneFile=%s" % sceneFile )
        
        if isScriptJob:
            writer.WriteLine( "ScriptFile=%s" % scriptFile )
    
    if outputFormat in "AVI QUICKTIME TGA TIFF SGI ILBM SUN":
        writer.WriteLine( "AlphaSaveModeBox=%s" % scriptDialog.GetValue( "AlphaSaveModeBox" ) )
    
    writer.WriteLine( "JobModeBox=%s" % scriptDialog.GetValue( "JobModeBox" ) )
    writer.WriteLine( "OutputFile=%s" % outputFile )
    writer.WriteLine( "Version=%s" % version )
    writer.WriteLine( "OutputFormat=%s" % outputFormat )
    writer.WriteLine( "UseCameraBox=%s" % scriptDialog.GetValue( "UseCameraBox" ) )
    
    writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
    writer.WriteLine( "Build0=None" )
    writer.WriteLine( "Build1=32bit" )
    writer.WriteLine( "Build2=64bit" )
    
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( sceneFile )
        if isScriptJob:
            arguments.Add( scriptFile )
        
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )