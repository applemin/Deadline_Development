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
def __main__():
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Lightwave Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Lightwave' ) )
    
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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Lightwave Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Lightwave File", 1, 0, "The scene file to be rendered.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "MultiFileBrowserControl", "", "Lightwave Files (*.lws)", 1, 1, colSpan=2 )
    sceneBox.ValueModified.connect(SceneChanged)

    scriptDialog.AddControlToGrid("ContentLabel","LabelControl","Content Folder", 2, 0, "The Lightwave Content directory. Refer to your Lightwave documentation for more information. ", False)
    scriptDialog.AddSelectionControlToGrid("ContentBox","FolderBrowserControl","","", 2, 1, colSpan=2)

    scriptDialog.AddControlToGrid("ConfigLabel","LabelControl","Config Folder", 3, 0, "The Lightwave Config directory. Refer to your Lightwave documentation for more information. ", False)
    scriptDialog.AddSelectionControlToGrid("ConfigBox","FolderBrowserControl","","", 3, 1, colSpan=2)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 4, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 4, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 5, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Lightwave Scene File", 5, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering." )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 6, 0, "The version of Lightwave to render with.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "2019", ("8","9","10","11","2015","2018","2019"), 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "FPrimeBox", "CheckBoxControl", False, "Use FPrime Renderer", 6, 2, "Enable if you want to use the FPrime renderer instead of the normal Lightwave renderer. " )

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 7, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "ScreamerNetBox", "CheckBoxControl", True, "Use ScreamerNet Rendering", 7, 2, "ScreamerNet rendering keeps the Lightwave scene loaded in memory between frames, which reduces overhead time when rendering." )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "LightwaveMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","VersionBox","BuildBox","ContentBox","ConfigBox","FPrimeBox","ScreamerNetBox","SubmitSceneBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    SceneChanged(None)
    
    scriptDialog.ShowDialog(False)

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "LightwaveSettings.ini" )

def SceneChanged(*args):
    global scriptDialog
    
    sceneFilename = scriptDialog.GetValue( "SceneBox" )
    if File.Exists( sceneFilename ):
        startFrame = ""
        endFrame = ""
        
        sceneFileLines = File.ReadAllLines( sceneFilename )
        for line in sceneFileLines:
            if line.startswith( "FirstFrame " ):
                startFrame = line.replace( "FirstFrame ", "" )
            elif line.startswith( "LastFrame " ):
                endFrame = line.replace( "LastFrame ", "" )
            
            if startFrame != "" and endFrame != "":
                frameList = startFrame
                if startFrame != endFrame:
                    frameList = frameList + "-" + endFrame
                
                scriptDialog.SetValue( "FramesBox", frameList )

def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    
    # Check Lightwave files.
    sceneFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "SceneBox" ), False )
    if( len( sceneFiles ) == 0 ):
        scriptDialog.ShowMessageBox( "No Lightwave file specified", "Error" )
        return
    
    for sceneFile in sceneFiles:
        if( not File.Exists( sceneFile ) ):
            scriptDialog.ShowMessageBox( "The scene file %s does not exist" % sceneFile, "Error" )
            return
        elif( not scriptDialog.GetValue( "SubmitSceneBox" ) and PathUtils.IsPathLocal( sceneFile ) ):
            # If the submit scene box is checked check if they are local, if they are warn the user
            result = scriptDialog.ShowMessageBox( "The scene file " + sceneFile + " is local, are you sure you want to continue","Warning", ("Yes","No") )
            if( result == "No" ):
                return
    
    # Check content directory.
    contentFolder = ( scriptDialog.GetValue( "ContentBox" ) ).strip()
    if( not Directory.Exists( contentFolder ) ):
        scriptDialog.ShowMessageBox( "The content folder does not exist","Error" )
        return
    elif PathUtils.IsPathLocal( contentFolder ):
        result = scriptDialog.ShowMessageBox( "The content folder is local, are you sure you want to continue","Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    # Check config directory.
    configFolder = ( scriptDialog.GetValue( "ConfigBox" ) ).strip()
    if( not Directory.Exists( configFolder ) ):
        scriptDialog.ShowMessageBox( "The config folder does not exist","Error" )
        return
    elif PathUtils.IsPathLocal( configFolder ):
        result = scriptDialog.ShowMessageBox( "The config folder is local, are you sure you want to continue","Warning", ("Yes","No") )
        if( result == "No" ):
            return
            
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return

    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity():
        return
    
    successes = 0
    failures = 0
    
    # Submit each scene file separately.
    for sceneFile in sceneFiles:
        saveRGB = False
        pathRGB = ""
        saveAlpha = False
        pathAlpha = ""
        
        sceneFileLines = File.ReadAllLines( sceneFile )
        for line in sceneFileLines:
            if line.startswith( "SaveRGB 1" ):
                saveRGB = True
            if line.startswith( "SaveRGBImagesPrefix " ):
                pathRGB = line.replace( "SaveRGBImagesPrefix ", "" )
            if line.startswith( "SaveAlpha 1" ):
                saveAlpha = True
            if line.startswith( "SaveAlphaImagesPrefix " ):
                pathAlpha = line.replace( "SaveAlphaImagesPrefix ", "" )
        
        jobName = scriptDialog.GetValue( "NameBox" )
        if len(sceneFiles) > 1:
            jobName = jobName + " [" + Path.GetFileName( sceneFile ) + "]"
        
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "lightwave_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Lightwave" )
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
        if( scriptDialog.GetValue( "IsBlacklistBox" ) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        if( scriptDialog.GetValue( "SubmitSuspendedBox" ) ):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        
        count = 0
        if saveRGB and pathRGB != "":
            dirRGB = Path.GetDirectoryName( pathRGB )
            writer.WriteLine( "OutputDirectory%s=%s" % (count, dirRGB) )
            count = count + 1
        if saveAlpha and pathAlpha != "":
            dirAlpha = Path.GetDirectoryName( pathAlpha )
            writer.WriteLine( "OutputDirectory%s=%s" % (count, dirAlpha) )
            count = count + 1
        
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
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "lightwave_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
        if( not scriptDialog.GetValue("SubmitSceneBox") ):
            writer.WriteLine("SceneFile=%s" % sceneFile)
        
        writer.WriteLine("LW_Version=%s" % scriptDialog.GetValue("VersionBox"))
        writer.WriteLine("LW_Build=%s" % scriptDialog.GetValue("BuildBox"))
        writer.WriteLine("ContentDir=%s" % contentFolder)
        writer.WriteLine("ConfigDir=%s" % configFolder)
        writer.WriteLine("UseScreamerNet=%s" % scriptDialog.GetValue("ScreamerNetBox"))
        writer.WriteLine("UseFPrime=%s" % scriptDialog.GetValue("FPrimeBox"))
        writer.Close()
        
        # Setup the command line arguments.
        arguments = StringCollection()
        
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        if scriptDialog.GetValue( "SubmitSceneBox" ):
            arguments.Add( sceneFile )
        
        if( len( sceneFiles ) == 1 ):
            results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
            scriptDialog.ShowMessageBox( results, "Submission Results" )
        else:
            # Now submit the job.
            exitCode = ClientUtils.ExecuteCommand( arguments )
            if( exitCode == 0 ):
                successes = successes + 1
            else:
                failures = failures + 1
        
    if( len( sceneFiles ) > 1 ):
        scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )