from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

import re
import time

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
ProjectManagementOptions = ["Shotgun","FTrack","NIM"]
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
    scriptDialog.SetTitle( "Submit Mantra Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Mantra' ) )
    
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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Mantra Options", 0, 0, colSpan=4 )
    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "IFD File", 1, 0, "Specify the Mantra IFD file(s) to render.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "IFD Files (*.ifd);;All Files (*)", 1, 1, colSpan=3 )
    sceneBox.ValueModified.connect(SceneFileChanged)

    scriptDialog.AddControlToGrid("OutputLabel","LabelControl","Output File (Optional)", 2, 0, "Enable this option to override the output path in the IFD file(s).", False )
    scriptDialog.AddSelectionControlToGrid("OutputBox","FileSaverControl","", "BMP (*.bmp);;EXR (*.exr);;JPG (*.jpg);;PIC (*.pic);;PNG (*.png);;SGI (*.sgi);;TGA (*.tga);;TIF (*.tif);;All Files (*)", 2, 1, colSpan=3)
    
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render. If you are submitting a sequence of .ifd files, the frames you choose to render should correspond to the numbers in the .ifd files.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoFramesBox", "CheckBoxControl", False, "Calculate Frames From IFD File", 3, 2, "If enabled, the frame list will be calculated based on the selected input file.", colSpan=2 )

    scriptDialog.AddControlToGrid("VersionLabel","LabelControl","Version", 4, 0, "The version of Mantra to render with.", False)
    versionBox=scriptDialog.AddComboControlToGrid("VersionBox","ComboControl","17.5",("7.0","8.0","9.0","10.0","11.0","12.0","13.0","14.0","15.0","15.5","16.0","16.5","17.0","17.5"), 4, 1)
    versionBox.ValueModified.connect(VersionChanged)
    scriptDialog.AddControlToGrid("ThreadsLabel","LabelControl","Threads", 4, 2, "The number of threads to use for rendering. ", False)
    scriptDialog.AddRangeControlToGrid("ThreadsBox","RangeControl",0,0,256,0,1, 4, 3)

    scriptDialog.AddControlToGrid("CommandLabel","LabelControl","Additional Arguments", 5, 0, "Additional command line arguments to pass to the renderer. ", False)
    scriptDialog.AddControlToGrid("CommandBox","TextControl","", 5, 1, colSpan=3)
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Tile Rendering")
    scriptDialog.AddGrid()
    
    scriptDialog.AddControlToGrid( "Separator9", "SeparatorControl", "Tile Rendering", 0, 0, colSpan=4 )
    enableTilesBox = scriptDialog.AddSelectionControlToGrid("EnableTilesCheck","CheckBoxControl",False,"Enable Tile Rendering", 1, 0, "Enable to tile render the output.", False)
    enableTilesBox.ValueModified.connect(TilesChanged)
    
    scriptDialog.AddControlToGrid( "XTilesLabel", "LabelControl", "Tiles in X", 2, 0, "The number of tiles in the X direction.", False )
    scriptDialog.AddRangeControlToGrid( "XTilesBox", "RangeControl", 2, 1, 100, 0, 1, 2, 1 )
    scriptDialog.AddControlToGrid( "YTilesLabel", "LabelControl", "Tiles in Y", 2, 2, "The number of tiles in the Y direction.", False )
    scriptDialog.AddRangeControlToGrid( "YTilesBox", "RangeControl", 2, 1, 100, 0, 1, 2, 3 )
    
    singleFrameEnabledBox = scriptDialog.AddSelectionControlToGrid("SingleFrameEnabledCheck","CheckBoxControl",False,"Single Frame Tile Job Enabled", 3, 0, "Enable to submit all tiles in a single job.", False,1,2)
    singleFrameEnabledBox.ValueModified.connect(SingleFrameChanged)
    scriptDialog.AddControlToGrid( "SingleJobFrameLabel", "LabelControl", "Single Job Frame", 3, 2, "Which Frame to Render if Single Frame is enabled.", False )
    scriptDialog.AddRangeControlToGrid( "SingleJobFrameBox", "RangeControl", 1, 1, 100000, 0, 1, 3, 3 )
    
    SubmitDependentBox = scriptDialog.AddSelectionControlToGrid( "SubmitDependentCheck", "CheckBoxControl", True, "Submit Dependent Assembly Job", 4, 0, "If enabled, a dependent assembly job will be submitted.", False, 1, 2 )
    SubmitDependentBox.ValueModified.connect(SubmitDependentChanged)
    scriptDialog.AddSelectionControlToGrid( "CleanupTilesCheck", "CheckBoxControl", True, "Cleanup Tiles After Assembly", 4, 2, "If enabled, all tiles will be cleaned up by the assembly job.", False, 1, 2 )
    
    scriptDialog.AddSelectionControlToGrid( "ErrorOnMissingCheck", "CheckBoxControl", True, "Error on Missing Tiles", 5, 0, "If enabled, the assembly job will fail if any tiles are missing.", False, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "ErrorOnMissingBackgroundCheck", "CheckBoxControl", False, "Error on Missing Background", 5, 2, "If enabled, the assembly will fail if the background is missing.", False, 1, 2 )
    
    scriptDialog.AddControlToGrid("AssembleOverLabel","LabelControl","Assemble Over", 6, 0, "What the tiles should be assembled over.", False)
    assembleBox = scriptDialog.AddComboControlToGrid("AssembleOverBox","ComboControl","Blank Image",("Blank Image","Previous Output","Selected Image"), 6, 1)
    assembleBox.ValueModified.connect(AssembleOverChanged)
    
    scriptDialog.AddControlToGrid("BackgroundLabel","LabelControl","Background Image File", 7, 0, "The Background image to assemble over.", False)
    scriptDialog.AddSelectionControlToGrid("BackgroundBox","FileSaverControl","", "Bitmap (*.bmp);;JPG (*.jpg);;PNG (*.png);;Targa (*.tga);;TIFF (*.tif);;All Files (*)", 7, 1, colSpan=3)
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "MantraMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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
    
    # Application Box must be listed before version box or else the application changed event will change the version
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","OutputBox","VersionBox","ThreadsBox","CommandBox","AutoFramesBox")	
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    SceneFileChanged()
    VersionChanged()
    TilesChanged()
    
    scriptDialog.ShowDialog( False )
    
def VersionChanged(*args):
    global scriptDialog
    
    if( float( scriptDialog.GetValue( "VersionBox" ) ) < 9 ):
        scriptDialog.SetEnabled( "ThreadsBox", False )
    else:
        scriptDialog.SetEnabled( "ThreadsBox", True )

def SceneFileChanged(*args):
    global scriptDialog
    
    # Only update the frames box if this option is enabled.
    if not scriptDialog.GetValue( "AutoFramesBox" ):
        return
    
    filename = scriptDialog.GetValue("SceneBox")
    frameString = "1-1"
    multiFrame = True

    try:
        if(File.Exists(filename)):
            startFrame = 0
            endFrame = 0
            initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
            paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
        
            #~ if( initFrame >= 0 ):
                #~ #valid frame numbers
                #~ multiFrame = False
        
                #~ startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
                #~ endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
        
                #~ if( startFrame >= 0 and endFrame >= 0 ):
                    #~ if( startFrame == endFrame ):
                        #~ frameString = str(startFrame)
                    #~ else:
                        #~ frameString = str(startFrame) + "-" + str(endFrame)

            startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
            endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
            if( startFrame == endFrame ):
                frameString = str(startFrame)
            else:
                frameString = str(startFrame) + "-" + str(endFrame)
            
            scriptDialog.SetValue("FramesBox",frameString)
        else:
            scriptDialog.SetValue("FramesBox","")
    except:
        scriptDialog.SetValue("FramesBox","")
    
def TilesChanged(*args):
    global scriptDialog
    enableRegionRendering = ( scriptDialog.GetValue( "EnableTilesCheck" ) and scriptDialog.GetEnabled( "EnableTilesCheck" ) )
    
    scriptDialog.SetEnabled( "XTilesLabel", enableRegionRendering )
    scriptDialog.SetEnabled( "XTilesBox", enableRegionRendering )
    scriptDialog.SetEnabled( "YTilesLabel", enableRegionRendering )
    scriptDialog.SetEnabled( "YTilesBox", enableRegionRendering )
    scriptDialog.SetEnabled( "SingleFrameEnabledCheck", enableRegionRendering )
    scriptDialog.SetEnabled( "SubmitDependentCheck", enableRegionRendering )
    
    SingleFrameChanged()
    SubmitDependentChanged()

def SubmitDependentChanged(*args):
    global scriptDialog
    submitDependentEnabled = ( scriptDialog.GetValue( "SubmitDependentCheck" ) and scriptDialog.GetEnabled( "SubmitDependentCheck" ) )
    
    scriptDialog.SetEnabled( "CleanupTilesCheck", submitDependentEnabled )
    scriptDialog.SetEnabled( "ErrorOnMissingCheck", submitDependentEnabled )
    scriptDialog.SetEnabled( "ErrorOnMissingBackgroundCheck", submitDependentEnabled )
    scriptDialog.SetEnabled( "AssembleOverLabel", submitDependentEnabled )
    scriptDialog.SetEnabled( "AssembleOverBox", submitDependentEnabled )
    
    AssembleOverChanged()
    
def AssembleOverChanged(*args):
    global scriptDialog
    AssembleOverEnabled = ( (scriptDialog.GetValue( "AssembleOverBox" ) == "Selected Image") and scriptDialog.GetEnabled( "AssembleOverBox" ) )
    
    scriptDialog.SetEnabled( "BackgroundLabel", AssembleOverEnabled )
    scriptDialog.SetEnabled( "BackgroundBox", AssembleOverEnabled )
    
def SingleFrameChanged(*args):
    global scriptDialog
    enableSingleFrameRegion = ( scriptDialog.GetValue( "SingleFrameEnabledCheck" ) and scriptDialog.GetEnabled( "SingleFrameEnabledCheck" ) )
    
    scriptDialog.SetEnabled( "SingleJobFrameLabel", enableSingleFrameRegion )
    scriptDialog.SetEnabled( "SingleJobFrameBox", enableSingleFrameRegion )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "MantraSettings.ini" )

def RightReplace( fullString, oldString, newString, occurences ):
    return newString.join( fullString.rsplit( oldString, occurences ) )

def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog
    
    errors = ""
    warnings = ""

    paddedNumberRegex = Regex( "\\$F([0-9]+)" )
    
    # Check if mantra files exist.
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        errors += "\nIFD file %s does not exist.\n"
    elif (PathUtils.IsPathLocal(sceneFile)):
        warnings += "\nIFD file %s is local.\n" % sceneFile
    
    regionRendering = False
    singleRegionJob = False
    regionJobCount = 1
    tilesInX = 1
    tilesInY = 1
    submitDependent = False
    #Check Output, if one is given
    output = scriptDialog.GetValue("OutputBox")
    paddedOutputFile = ""
    outputFolder = None
    if(len(output) != 0):
        outputFolder = Path.GetDirectoryName(output)
        try:
            if(not Directory.Exists(outputFolder)):
                errors += "\nDirectory " + outputFolder + " does not exist.\n"
        except:
            errors += "\nDirectory " + outputFolder + " is not valid.\n"
        
        if(PathUtils.IsPathLocal(outputFolder)):
            warnings += "\nOutput folder %s is local.\n" % outputFolder
        
        if paddedNumberRegex.IsMatch( output ):
            paddingSize = int(paddedNumberRegex.Match( output ).Groups[1].Value)
            padding = "#";
            while len(padding) < paddingSize:
                padding = padding + "#"
            paddedOutputFile = paddedNumberRegex.Replace( output, padding )
        else:
            paddedOutputFile = output.replace( "$F", "#" )
        
    if scriptDialog.GetValue( "EnableTilesCheck" ):
        regionRendering = True
        
        if(len(output) != 0):
            errors += "\nUnable to submit a Tile job without an output path defined."
        
        
        tilesInX = scriptDialog.GetValue("XTilesBox")
        tilesInY = scriptDialog.GetValue("YTilesBox")
        regionJobCount = tilesInX * tilesInY
        submitDependent = scriptDialog.GetValue( "SubmitDependentCheck" )
        if scriptDialog.GetValue( "SingleFrameEnabledCheck" ):
            singleRegionJob = True
            regionJobCount = 1
            
            taskLimit = RepositoryUtils.GetJobTaskLimit()
            if tilesInX * tilesInY > taskLimit:
                errors += "\nUnable to submit job with " + (str(tilesInX * tilesInY)) + " tasks.  Task Count exceeded Job Task Limit of "+str(taskLimit) + ".\n"
    
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( paddedOutputFile ):
        return

    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        errors += "\nFrame range %s is not valid.\n" % frames
    
    if len( errors ) > 0:
        errors = "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % errors
        scriptDialog.ShowMessageBox( errors, "Error" )
        return

    if len( warnings ) > 0:
        warnings = "Warnings:\n\n%s\n\nAre you sure you want to continue?\n" % warnings
        result = scriptDialog.ShowMessageBox( warnings, "Warning", ("Yes","No") )
        if result == "No":
            return

    jobName = scriptDialog.GetValue( "NameBox" )
    batchName = jobName
    
    jobIds = []
    jobCount = 0
    for jobNum in range( 0, regionJobCount ):
        # Create job info file.
        
        renderJobName = jobName
        if regionRendering:
            if singleRegionJob:
                renderJobName = renderJobName + " - Single Region"
            else:
                renderJobName = renderJobName + " - Region "+str(jobNum)
                
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "mantra_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Mantra" )
        writer.WriteLine( "Name=%s" % renderJobName )
        
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
        
        if singleRegionJob:
            tileName = paddedOutputFile
            paddingRegex = re.compile( "(#+)", re.IGNORECASE )
            matches = paddingRegex.findall( os.path.basename( tileName ) )
            if matches != None and len( matches ) > 0:
                paddingString = matches[ len( matches ) - 1 ]
                paddingSize = len( paddingString )
                padding = str(scriptDialog.GetValue( "SingleJobFrameBox" ))
                while len(padding) < paddingSize:
                    padding = "0" + padding
                
                padding = "_tile?_" + padding
                tileName = RightReplace( tileName, paddingString, padding, 1 )
            else:
                splitFilename = os.path.splitext(tileName)
                tileName = splitFilename[0]+"_tile?_"+splitFilename[1]
            
            for currTile in range(0, tilesInX*tilesInY):
                regionOutputFileName = tileName.replace( "?", str(currTile) )
                writer.WriteLine( "OutputFilename0Tile%s=%s"%(currTile,regionOutputFileName) )
                
        elif paddedOutputFile != "":
            writer.WriteLine( "OutputFilename0=%s" % paddedOutputFile )
                
        elif(outputFolder != None):
            writer.WriteLine("OutputDirectory0=" + outputFolder)
            
        if singleRegionJob:
            writer.WriteLine( "TileJob=True" )
            writer.WriteLine( "TileJobTilesInX=%s" % tilesInX )
            writer.WriteLine( "TileJobTilesInY=%s" % tilesInY )
            writer.WriteLine( "TileJobFrame=%s" % scriptDialog.GetValue( "SingleJobFrameBox" )  )
        else:
            writer.WriteLine( "Frames=%s" % frames )
            writer.WriteLine( "ChunkSize=1")
        
        groupBatch = False
        extraKVPIndex = 0
        
        if integration_dialog.IntegrationProcessingRequested() and not submitDependent:
            extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

        if submitDependent:
            groupBatch = True
            
        if groupBatch:
            writer.WriteLine( "BatchName=%s\n" % ( batchName ) )
        
        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "mantra_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
        writer.WriteLine("SceneFile=" + sceneFile)
        writer.WriteLine("Version=" + scriptDialog.GetValue("VersionBox"))
        writer.WriteLine("Threads=" + str(scriptDialog.GetValue("ThreadsBox")))
        writer.WriteLine("OutputFile=" + output)
        writer.WriteLine("CommandLineOptions=" + scriptDialog.GetValue("CommandBox"))
        
        if regionRendering:
            writer.WriteLine( "RegionRendering=True" )
            if singleRegionJob:
                curRegion = 0
                for y in range(0, tilesInY):
                    for x in range(0, tilesInX):
                        
                        xstart = x * 1.0 / tilesInX
                        xend = ( x + 1.0 ) / tilesInX
                        ystart = y * 1.0 / tilesInY
                        yend = ( y + 1.0 ) / tilesInY
                        
                        writer.WriteLine( "RegionLeft%s=%s" % (curRegion, xstart) )
                        writer.WriteLine( "RegionRight%s=%s" % (curRegion, xend) )
                        writer.WriteLine( "RegionBottom%s=%s" % (curRegion, ystart) )
                        writer.WriteLine( "RegionTop%s=%s" % (curRegion,yend) )
                        curRegion += 1
            else:
                writer.WriteLine( "CurrentTile=%s" % jobNum )
                
                curY = 0
                curX = 0
                jobNumberFound = False
                tempJobNum = 0
                for y in range(0, tilesInY):
                    for x in range(0, tilesInX):
                        if tempJobNum == jobNum:
                            curY = y
                            curX = x
                            jobNumberFound = True
                            break
                        tempJobNum = tempJobNum + 1
                    if jobNumberFound:
                        break
                
                xstart = curX * 1.0 / tilesInX
                xend = ( curX + 1.0 ) / tilesInX
                ystart = curY * 1.0 / tilesInY
                yend = ( curY + 1.0 ) / tilesInY
            
                writer.WriteLine( "RegionLeft=%s" % xstart )
                writer.WriteLine( "RegionRight=%s" % xend )
                writer.WriteLine( "RegionBottom=%s" % ystart )
                writer.WriteLine( "RegionTop=%s" % yend )
        
        writer.Close()
    
        # Setup the command line arguments.
        arguments = StringCollection()
        
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        
        # Now submit the job.
        results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        jobId = "";
        resultArray = results.split("\n")
        for line in resultArray:
            if line.startswith("JobID="):
                jobId = line.replace("JobID=","")
                jobId = jobId.strip()
                break
        
        jobIds.append(jobId)
        jobCount += 1
    
    if regionRendering and submitDependent:
        jobName = scriptDialog.GetValue( "NameBox" )
        jobName = "%s - Assembly"%(jobName)
        
        # Create submission info file
        jigsawJobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "jigsaw_submit_info.job" )
        jigsawPluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "jigsaw_plugin_info.job" )        
        
        writer = StreamWriter( jigsawJobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=DraftTileAssembler" )
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
            
        writer.WriteLine( "JobDependencies=%s" % ",".join(jobIds) )
        
        if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        if singleRegionJob:
            writer.WriteLine( "Frames=%s" % scriptDialog.GetValue( "SingleJobFrameBox" ) )
        else:
            writer.WriteLine( "Frames=%s" % frames )
       
        writer.WriteLine( "ChunkSize=1" )
        
        if paddedOutputFile != "":
            writer.WriteLine( "OutputFilename0=%s" % paddedOutputFile )
        
        writer.WriteLine( "BatchName=%s" % ( batchName ) ) 

        if integration_dialog.IntegrationProcessingRequested() and not submitDependent:
            extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()
            if singleRegionJob:
                writer.WriteLine( "ExtraInfoKeyValue%d=FrameRangeOverride=%d\n" % ( extraKVPIndex, scriptDialog.GetValue( "SingleJobFrameBox" ) ) )
            
        if submitDependent:
            groupBatch = True

        writer.Close()
        
        # Create plugin info file
        writer = StreamWriter( jigsawPluginInfoFilename, False, Encoding.Unicode )
        
        writer.WriteLine( "ErrorOnMissing=%s\n" % (scriptDialog.GetValue( "ErrorOnMissingCheck" )) )
        writer.WriteLine( "ErrorOnMissingBackground=%s\n" % (scriptDialog.GetValue( "ErrorOnMissingBackgroundCheck" )) )
        writer.WriteLine( "CleanupTiles=%s\n" % (scriptDialog.GetValue( "CleanupTilesCheck" )) )
        writer.WriteLine( "MultipleConfigFiles=%s\n" % True )
        
        writer.Close()
        
        configFiles = []
        
        frameList = []
        if singleRegionJob:
            frameList = [scriptDialog.GetValue( "SingleJobFrameBox" )]
        else:
            frameList = FrameUtils.Parse( frames )
        
        for frame in frameList:
            imageFileName = paddedOutputFile.replace("\\","/")
            
            tileName = imageFileName
            outputName = imageFileName
            paddingRegex = re.compile( "(#+)", re.IGNORECASE )
            matches = paddingRegex.findall( os.path.basename( imageFileName ) )
            if matches != None and len( matches ) > 0:
                paddingString = matches[ len( matches ) - 1 ]
                paddingSize = len( paddingString )
                padding = str(frame)
                while len(padding) < paddingSize:
                    padding = "0" + padding
                
                outputName = RightReplace( imageFileName, paddingString, padding, 1 )
                padding = "_tile?_" + padding
                tileName = RightReplace( imageFileName, paddingString, padding, 1 )
            else:
                outputName = imageFileName
                splitFilename = os.path.splitext(imageFileName)
                tileName = splitFilename[0]+"_tile?_"+splitFilename[1]
            
            date = time.strftime("%Y_%m_%d_%H_%M_%S")
            configFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), outputName+"_"+str(frame)+"_config_"+date+".txt" )
            writer = StreamWriter( configFilename, False, Encoding.Unicode )
            writer.WriteLine( "" )
            writer.WriteLine( "ImageFileName=" +outputName )
            backgroundType = scriptDialog.GetValue( "AssembleOverBox" )
            if backgroundType == "Previous Output":
                fileHandle.write( "BackgroundSource=" +outputName +"\n" )
            elif backgroundType == "Selected Image":
                fileHandle.write( "BackgroundSource=" +scriptDialog.GetValue( "BackgroundBox" ) +"\n" )
            
            writer.WriteLine( "TilesCropped=False" )
            writer.WriteLine( "TileCount=" +str( tilesInX * tilesInY ) )
            writer.WriteLine( "DistanceAsPixels=False" )
            
            currTile = 0
            for y in range(0, tilesInY):
                for x in range(0, tilesInX):
                    width = 1.0/tilesInX
                    height = 1.0/tilesInY
                    xRegion = x*width
                    yRegion = y*height
                    
                    regionOutputFileName = tileName.replace( "?", str(currTile) )
                    
                    writer.WriteLine( "Tile%iFileName=%s"%(currTile,regionOutputFileName) )
                    writer.WriteLine( "Tile%iX=%s"%(currTile,xRegion) )
                    writer.WriteLine( "Tile%iY=%s"%(currTile,yRegion) )
                    writer.WriteLine( "Tile%iWidth=%s"%(currTile,width) )
                    writer.WriteLine( "Tile%iHeight=%s"%(currTile,height) )
                    currTile += 1
            
            writer.Close()
            configFiles.append(configFilename)
        
        arguments = []
        arguments.append( jigsawJobInfoFilename )
        arguments.append( jigsawPluginInfoFilename )
        arguments.extend( configFiles )
        jobResult = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        jobCount += 1
        
    if jobCount == 1:
        scriptDialog.ShowMessageBox( results, "Submission Results" )
    else:
        scriptDialog.ShowMessageBox( ("All %d jobs submitted" % jobCount), "Submission Results" )