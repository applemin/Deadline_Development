from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

import re
import os
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
    scriptDialog.SetTitle( "Submit Houdini Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Houdini' ) )
    
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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Houdini Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Houdini File", 1, 0, "The scene file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Houdini Files (*.hip *.hipnc *.hiplc)", 1, 1, colSpan=3 )

    outputBox = scriptDialog.AddSelectionControlToGrid("OutputLabel","CheckBoxControl",False,"Override Output", 2, 0, "Enable this option to override the output path in the scene file. Include $F in the filename if doing tile rendering for multiple frames.", False)
    outputBox.ValueModified.connect(OutputChanged)
    scriptDialog.AddSelectionControlToGrid("OutputBox","FileSaverControl","", "Bitmap (*.bmp);;JPG (*.jpg);;PNG (*.png);;Targa (*.tga);;TIFF (*.tif);;All Files (*)", 2, 1, colSpan=3)

    scriptDialog.AddControlToGrid("RendererLabel","LabelControl","Render Node", 3, 0, "You must manually enter a renderer (output driver) to use. Note that the full node path must be specified, so if your output driver is 'mantra1', it's likely that the full node path would be '/out/mantra1'. ", False)
    scriptDialog.AddControlToGrid("RendererBox","TextControl","", 3, 1)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 4, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 4, 1 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 4, 2, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 4, 3 )

    scriptDialog.AddControlToGrid("VersionLabel","LabelControl","Version", 5, 0, "The version of Houdini to render with.", False)
    scriptDialog.AddComboControlToGrid("VersionBox","ComboControl","17.5",("9.0","10.0","11.0","12.0","13.0","14.0","15.0","15.5","16.0","16.5", "17.0", "17.5"), 5, 1)
    scriptDialog.AddControlToGrid("BuildLabel","LabelControl","Build to Force", 5, 2, "You can force 32 or 64 bit rendering with this option.", False)
    scriptDialog.AddComboControlToGrid("BuildBox","ComboControl","None",("None","32bit","64bit"), 5, 3)

    scriptDialog.AddSelectionControlToGrid("IgnoreInputsBox","CheckBoxControl",False,"Ignore Inputs", 6, 0, "If enabled, only the specified ROP will be rendered (does not render any of its dependencies).")
    scriptDialog.AddSelectionControlToGrid("SubmitSceneBox","CheckBoxControl",False,"Submit Houdini Scene",6, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering.")
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.AddTabPage("Mantra")
    scriptDialog.AddGrid()

    ifdBox = scriptDialog.AddSelectionControlToGrid("IFDLabel","CheckBoxControl",False,"Override Export IFD", 0, 0, "Enable this option to export IFD files from the Houdini scene file. Specify the path to the output IFD files here.", False)
    ifdBox.ValueModified.connect(IfdChanged)
    scriptDialog.AddSelectionControlToGrid("IFDBox","FileSaverControl","", "IFD (*.ifd);;All Files (*)",0, 1, colSpan=2)

    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "", 1, 0, colSpan=3 )

    mantraBox = scriptDialog.AddSelectionControlToGrid("MantraBox","CheckBoxControl",False,"Submit Dependent Mantra Standalone Job", 2, 0, "Enable this option to submit a dependent Mantra standalone job that will render the resulting IFD files.", colSpan=3)
    mantraBox.ValueModified.connect(MantraChanged)

    scriptDialog.AddControlToGrid( "MantraPoolLabel", "LabelControl", "Pool", 3, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "MantraPoolBox", "PoolComboControl", "none", 3, 1 )
    
    scriptDialog.AddControlToGrid( "MantraSecondaryPoolLabel", "LabelControl", "Secondary Pool", 4, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "MantraSecondaryPoolBox", "SecondaryPoolComboControl", "", 4, 1 )

    scriptDialog.AddControlToGrid( "MantraGroupLabel", "LabelControl", "Group", 5, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "MantraGroupBox", "GroupComboControl", "none", 5, 1 )

    scriptDialog.AddControlToGrid( "MantraPriorityLabel", "LabelControl", "Priority", 6, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "MantraPriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 6, 1 )

    scriptDialog.AddControlToGrid( "MantraTaskTimeoutLabel", "LabelControl", "Task Timeout", 7, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MantraTaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "MantraAutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 7, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job." )

    scriptDialog.AddControlToGrid( "MantraConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 8, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "MantraConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 8, 1 )
    scriptDialog.AddSelectionControlToGrid( "MantraLimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 8, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MantraMachineLimitLabel", "LabelControl", "Machine Limit", 9, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MantraMachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 9, 1 )
    scriptDialog.AddSelectionControlToGrid( "MantraIsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 9, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MantraMachineListLabel", "LabelControl", "Machine List", 10, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MantraMachineListBox", "MachineListControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "MantraLimitGroupLabel", "LabelControl", "Limits", 11, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "MantraLimitGroupBox", "LimitGroupControl", "", 11, 1, colSpan=2 )

    scriptDialog.AddControlToGrid("ThreadsLabel","LabelControl","Mantra Threads", 12, 0, "The number of threads to use for the Mantra stanadlone job.", False)
    scriptDialog.AddRangeControlToGrid("ThreadsBox","RangeControl",0,0,256,0,1, 12, 1)
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
    
    scriptDialog.AddSelectionControlToGrid( "ErrorOnMissingCheck", "CheckBoxControl", True, "Error on Missing Tile", 5, 0, "If enabled, the assembly job will fail if any tiles are missing.", False, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "ErrorOnMissingBackgroundCheck", "CheckBoxControl", False, "Error on Missing Background", 5, 2, "If enabled, the assembly will fail if the background is missing.", False, 1, 2 )
    
    scriptDialog.AddControlToGrid("AssembleOverLabel","LabelControl","Assemble Over", 6, 0, "What the tiles should be assembled over.", False)
    assembleBox = scriptDialog.AddComboControlToGrid("AssembleOverBox","ComboControl","Blank Image",("Blank Image","Previous Output","Selected Image"), 6, 1)
    assembleBox.ValueModified.connect(AssembleOverChanged)
    
    scriptDialog.AddControlToGrid("BackgroundLabel","LabelControl","Background Image File", 7, 0, "The Background image to assemble over.", False)
    scriptDialog.AddSelectionControlToGrid("BackgroundBox","FileSaverControl","", "Bitmap (*.bmp);;JPG (*.jpg);;PNG (*.png);;Targa (*.tga);;TIFF (*.tif);;All Files (*)", 7, 1, colSpan=3)
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "HoudiniMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","OutputBox", "IFDLabel", "IFDBox","FramesBox","ChunkSizeBox","RendererBox","IgnoreInputsBox","SubmitSceneBox","BuildBox","VersionBox", "MantraPoolBox", "MantraSecondaryPoolBox", "MantraGroupBox", "MantraPriorityBox", "MantraTaskTimeoutBox", "MantraAutoTimeoutBox","MantraConcurrentTasksBox", "MantraLimitConcurrentTasksBox", "MantraMachineLimitBox", "MantraIsBlacklistBox", "MantraMachineListBox", "MantraLimitGroupBox","ThreadsBox")	
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    OutputChanged()
    IfdChanged()
        
    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "HoudiniSettings.ini" )

def OutputChanged(*args):
    global scriptDialog
    
    overrideOutput = scriptDialog.GetValue( "OutputLabel" )
    scriptDialog.SetEnabled( "OutputBox", overrideOutput )
    scriptDialog.SetEnabled( "EnableTilesCheck", overrideOutput )
    
    TilesChanged()
    
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
    
def IfdChanged(*args):
    global scriptDialog
    
    overrideIfd = scriptDialog.GetValue( "IFDLabel" )
    mantraJob = scriptDialog.GetValue( "MantraBox" )
    scriptDialog.SetEnabled( "IFDBox", overrideIfd )
    scriptDialog.SetEnabled( "MantraBox", overrideIfd )
    scriptDialog.SetEnabled( "ThreadsLabel", overrideIfd and mantraJob )
    scriptDialog.SetEnabled( "ThreadsBox", overrideIfd and mantraJob )

def MantraChanged(*args):
    global scriptDialog
    
    overrideIfd = scriptDialog.GetValue( "IFDLabel" )
    mantraJob = scriptDialog.GetValue( "MantraBox" )
    scriptDialog.SetEnabled( "ThreadsLabel", overrideIfd and mantraJob )
    scriptDialog.SetEnabled( "ThreadsBox", overrideIfd and mantraJob )

def RightReplace( fullString, oldString, newString, occurences ):
    return newString.join( fullString.rsplit( oldString, occurences ) )

def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog
    
    paddedNumberRegex = Regex( "\\$F([0-9]+)" )
    errors = ""
    warnings = ""
    
    # Check if houdini files exist.
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        errors += "Houdini file %s does not exist.\n\n" % sceneFile
    elif (PathUtils.IsPathLocal(sceneFile) and not scriptDialog.GetValue("SubmitSceneBox")):
        warnings += "Houdini file %s is local.\n\n" % sceneFile
    
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        errors += "Frame range %s is not valid.\n\n" % frames
    
    # Check the output file
    regionRendering = False
    singleRegionJob = False
    regionJobCount = 1
    tilesInX = 1
    tilesInY = 1
    outputFile = ""
    paddedOutputFile = ""
    if scriptDialog.GetValue("OutputLabel"):
        outputFile = scriptDialog.GetValue("OutputBox").strip()
        if outputFile == "":
            errors += "Please specify an output file.\n\n"
        elif(not Directory.Exists(Path.GetDirectoryName(outputFile))):
            errors += "The directory of the output file does not exist:\n%s\n\n" % Path.GetDirectoryName(outputFile)
        
        if paddedNumberRegex.IsMatch( outputFile ):
            paddingSize = int(paddedNumberRegex.Match( outputFile ).Groups[1].Value)
            padding = "#";
            while len(padding) < paddingSize:
                padding = padding + "#"
            paddedOutputFile = paddedNumberRegex.Replace( outputFile, padding )
        else:
            paddedOutputFile = outputFile.replace( "$F", "#" )
    
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( paddedOutputFile ):
        return
    
    # Check the ifd file
    ifdFile = ""
    paddedIfdFile = ""
    if scriptDialog.GetValue("IFDLabel"):
        ifdFile = scriptDialog.GetValue("IFDBox").strip()
        if ifdFile == "":
            errors += "Please specify an IFD file.\n\n"
        elif(not Directory.Exists(Path.GetDirectoryName(ifdFile))):
            errors += "The directory of the ifd file does not exist:\n%s\n\n" % Path.GetDirectoryName( ifdFile )
        
        startFrame = FrameUtils.Parse( frames )[0]
        if paddedNumberRegex.IsMatch( ifdFile ):
            paddingSize = int(paddedNumberRegex.Match( ifdFile ).Groups[1].Value)
            padding = StringUtils.ToZeroPaddedString( startFrame, paddingSize, False )
            paddedIfdFile = paddedNumberRegex.Replace( ifdFile, padding )
        else:
            paddedIfdFile = ifdFile.replace( "$F", str(startFrame) )
    
    if scriptDialog.GetValue("OutputLabel"):
        if scriptDialog.GetValue("EnableTilesCheck"):
            regionRendering = True
            tilesInX = scriptDialog.GetValue("XTilesBox")
            tilesInY = scriptDialog.GetValue("YTilesBox")
            regionJobCount = tilesInX * tilesInY
            
            if scriptDialog.GetValue("SingleFrameEnabledCheck"):
                regionJobCount = 1
                singleRegionJob = True
                taskLimit = RepositoryUtils.GetJobTaskLimit()
                if tilesInX * tilesInY > taskLimit:
                    scriptDialog.ShowMessageBox("Unable to submit job with " + (str(tilesInX * tilesInY)) + " tasks.  Task Count exceeded Job Task Limit of "+str(taskLimit),"Error")
                    return
                
            if ifdFile != "" and scriptDialog.GetValue( "MantraBox" ):
                regionJobCount = 1
    
    # A renderer must be specified
    renderer = scriptDialog.GetValue("RendererBox")
    dependentMantraJob = scriptDialog.GetValue( "MantraBox" )

    if(len(renderer)==0):
        errors += "No Render Node specified (for example, /out/mantra1).\n\n"


    if len( errors ) > 0:
        errors = "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % errors
        scriptDialog.ShowMessageBox( errors, "Error" )
        return

    if len( warnings ) > 0:
        warnings = "Warnings:\n\n%s\n\nAre you sure you want to continue?\n" % warnings
        result = scriptDialog.ShowMessageBox( warnings, "Warning", ("Yes","No") )
        if result == "No":
            return
    
    jobIds = []
    jobCount = 0
    jobResult = ""
    
    for jobNum in range( 0, regionJobCount ):
        jobName = scriptDialog.GetValue( "NameBox" )
        
        modifiedName = jobName
        if regionRendering and not singleRegionJob and not( ifdFile != "" and dependentMantraJob ):
            modifiedName = modifiedName + " - Region " + str(jobNum)
        
        batchName = jobName
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "houdini_job_info%d.job" % jobNum )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Houdini" )
        writer.WriteLine( "Name=%s" % modifiedName )
        
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
            if not( ifdFile != "" and scriptDialog.GetValue( "MantraBox" ) ):
                writer.WriteLine( "TileJob=True" )
                writer.WriteLine( "TileJobTilesInX=%s" % tilesInX )
                writer.WriteLine( "TileJobTilesInY=%s" % tilesInY )
                writer.WriteLine( "TileJobFrame=%s" % scriptDialog.GetValue( "SingleJobFrameBox" ) )
            else:
                writer.WriteLine( "Frames=%s" % scriptDialog.GetValue( "SingleJobFrameBox" ) ) 
        else:
            writer.WriteLine( "Frames=%s" % frames )
        
        if singleRegionJob:
            if ifdFile != "" and scriptDialog.GetValue( "MantraBox" ):
                writer.WriteLine( "ChunkSize=1" )
        else:
            writer.WriteLine( "ChunkSize=%s" %  scriptDialog.GetValue( "ChunkSizeBox" ) )
        
        doIntegration = False
        doDraft = False
        
        if singleRegionJob and not( ifdFile != "" and scriptDialog.GetValue( "MantraBox" ) ):
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

        elif ifdFile != "":
            writer.WriteLine( "OutputDirectory0=%s" % Path.GetDirectoryName(ifdFile) )
            if not scriptDialog.GetValue( "MantraBox" ):
                doIntegration = True
        elif paddedOutputFile != "":
            writer.WriteLine( "OutputFilename0=%s" % paddedOutputFile )
            doDraft = True
            doIntegration = True
        
        extraKVPIndex = 0
        groupBatch = False
        
        if not ( dependentMantraJob or ( regionRendering and scriptDialog.GetValue( "SubmitDependentCheck" ) ) ):
            if integration_dialog.IntegrationProcessingRequested():
                extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
                groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

        if ifdFile != "" and dependentMantraJob:
            groupBatch = True
            
        if regionRendering:
            groupBatch = True
            
        if groupBatch:
            writer.WriteLine( "BatchName=%s" % ( jobName ) ) 
        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "houdini_plugin_info%d.job" % jobNum )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
        if(not scriptDialog.GetValue("SubmitSceneBox")):
            writer.WriteLine("SceneFile=" + sceneFile.replace("\\","/"))
        writer.WriteLine("Output=" + outputFile.replace("\\","/"))
        writer.WriteLine("IFD=" + ifdFile.replace("\\","/"))
        writer.WriteLine("OutputDriver=" + renderer)
        writer.WriteLine("IgnoreInputs=%s" % scriptDialog.GetValue("IgnoreInputsBox"))
        writer.WriteLine("Version=" + scriptDialog.GetValue("VersionBox"))
        writer.WriteLine("Build=" + scriptDialog.GetValue("BuildBox"))
        
        if regionRendering and not( ifdFile != "" and dependentMantraJob ):
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
        
        arguments = []
        arguments.append( jobInfoFilename )
        arguments.append( pluginInfoFilename )
        if scriptDialog.GetValue( "SubmitSceneBox" ):
            arguments.append( sceneFile )
            
        jobResult = results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        jobId = "";
        resultArray = jobResult.split("\n")
        for line in resultArray:
            if line.startswith("JobID="):
                jobId = line.replace("JobID=","")
                jobId = jobId.strip()
                break
        
        jobIds.append(jobId)
        jobCount += 1
        
    if ifdFile != "" and dependentMantraJob:    
        mantraJobCount = 1
        if regionRendering and not singleRegionJob:
            mantraJobCount = tilesInX*tilesInY
        
        mantraJobDependencies = ",".join(jobIds)
        jobIds = []
        
        for mantraJobNum in range( 0, mantraJobCount ):
            mantraJobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "mantra_job_info.job" )
            mantraPluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "mantra_plugin_info.job" )
            
            mantraJobName = jobName + " - Mantra Job"
            if regionRendering and not singleRegionJob:
                mantraJobName = mantraJobName + " - Region " + str(mantraJobNum)
            
            # Create mantra job and plugin info file if necessary
            writer = StreamWriter( mantraJobInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "Plugin=Mantra" )
            writer.WriteLine( "Name=%s" % mantraJobName )
            writer.WriteLine( "BatchName=%s" % batchName )
            writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
            writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
            writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "MantraPoolBox" ) )
            writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "MantraSecondaryPoolBox" ) )
            writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "MantraGroupBox" ) )
            writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "MantraPriorityBox" ) )
            writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "MantraTaskTimeoutBox" ) )
            writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "MantraAutoTimeoutBox" ) )
            writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "MantraConcurrentTasksBox" ) )
            writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "MantraLimitConcurrentTasksBox" ) )
            writer.WriteLine( "JobDependencies=%s" % mantraJobDependencies )
            
            writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MantraMachineLimitBox" ) )
            if( bool(scriptDialog.GetValue( "MantraIsBlacklistBox" )) ):
                writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MantraMachineListBox" ) )
            else:
                writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MantraMachineListBox" ) )
            
            writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "MantraLimitGroupBox" ) )
            writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
            
            if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
                writer.WriteLine( "InitialStatus=Suspended" )
            
            if singleRegionJob:
                writer.WriteLine( "TileJob=True" )
                writer.WriteLine( "TileJobTilesInX=%s" % tilesInX )
                writer.WriteLine( "TileJobTilesInY=%s" % tilesInY )
                writer.WriteLine( "TileJobFrame=%s" % scriptDialog.GetValue( "SingleJobFrameBox" )  )
            else:
                writer.WriteLine( "Frames=%s" % frames )
                writer.WriteLine( "ChunkSize=1")
                writer.WriteLine( "IsFrameDependent=true" )
            
            if paddedOutputFile != "":
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
                        
                else:
                    writer.WriteLine( "OutputFilename0=%s" % paddedOutputFile )
                
                if not ( regionRendering and scriptDialog.GetValue( "SubmitDependentCheck" ) ):
                    if integration_dialog.IntegrationProcessingRequested():
                        extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            
            writer.Close()
            
            # Create plugin info file.
            writer = StreamWriter( mantraPluginInfoFilename, False, Encoding.Unicode )
            writer.WriteLine("SceneFile=" + paddedIfdFile)
            writer.WriteLine("Version=" + scriptDialog.GetValue("VersionBox"))
            writer.WriteLine("Threads=" + str(scriptDialog.GetValue("ThreadsBox")))
            writer.WriteLine("OutputFile=" + outputFile)
            writer.WriteLine("CommandLineOptions=")
            
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
                    writer.WriteLine( "CurrentTile=%s" % mantraJobNum )
                    
                    curY = 0
                    curX = 0
                    jobNumberFound = False
                    tempJobNum = 0
                    for y in range(0, tilesInY):
                        for x in range(0, tilesInX):
                            if tempJobNum == mantraJobNum:
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
            
            arguments = []
            arguments.append( mantraJobInfoFilename )
            arguments.append( mantraPluginInfoFilename )
                
            jobResult = ClientUtils.ExecuteCommandAndGetOutput( arguments )
            jobId = "";
            resultArray = jobResult.split("\n")
            for line in resultArray:
                if line.startswith("JobID="):
                    jobId = line.replace("JobID=","")
                    jobId = jobId.strip()
                    break
            
            jobIds.append(jobId)
            jobCount += 1
            
    if regionRendering and scriptDialog.GetValue("SubmitDependentCheck"):
        
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
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "MantraPoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "MantraSecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "MantraGroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "MantraPriorityBox" ) )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "MantraTaskTimeoutBox" ) )
        writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "MantraAutoTimeoutBox" ) )
        writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "MantraConcurrentTasksBox" ) )
        writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "MantraLimitConcurrentTasksBox" ) )
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
        #writer.WriteLine( "Frames=0-%i" % (len(frameList)-1) )
       
        writer.WriteLine( "ChunkSize=1" )
        
        if ifdFile != "":
            if paddedOutputFile != "":
                writer.WriteLine( "OutputFilename0=%s" % paddedOutputFile )
            else:
                writer.WriteLine( "OutputDirectory0=%s" % Path.GetDirectoryName( ifdFile ) )
        elif paddedOutputFile != "":
            writer.WriteLine( "OutputFilename0=%s" % paddedOutputFile )
        
        writer.WriteLine( "BatchName=%s" % ( batchName ) ) 

        extraKVPIndex = 0
        groupBatch = False
        if integration_dialog.IntegrationProcessingRequested():
            extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

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
                writer.WriteLine( "BackgroundSource=" +outputName +"\n" )
            elif backgroundType == "Selected Image":
                writer.WriteLine( "BackgroundSource=" +scriptDialog.GetValue( "BackgroundBox" ) +"\n" )
            
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
        scriptDialog.ShowMessageBox( jobResult, "Submission Results" )
    else:
        scriptDialog.ShowMessageBox( ("All %d jobs submitted" % jobCount), "Submission Results" )
    