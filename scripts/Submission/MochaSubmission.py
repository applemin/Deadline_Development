from __future__ import print_function
import re
import sys

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

exporters = { "Shapes": [], "Tracking": [], "Camera solve": [] }
renderTypes = [ "Remove", "Insert", "Stabilize" ]
exportTypes = [ "Shapes", "Tracking", "Camera solve", "Rendered Shapes" ]
fileExtensions = [ "png", "cin", "dpx", "jpg", "jpeg", "bw", "iris", "rgb", "rgba", "sgi", "targa", "tga", "tif", "tiff", "tim", "exr", "sxr" ]
colorizeTypes = [ "Grayscale", "Matte Color", "Layer" ]
layerGroupTooltip = "When specifying which layers to render, follow these rules:\n - if you want to render all layers inside a group, put the group name followed by a colon (e.g. myGroup:)\n - if you want to render only some layers inside a group, put the group name followed by a colon and then list group's individual layer names separating them by a comma (e.g. myGroup: layer1, layer2)\n - if you want to render ungrouped layers, list their names separating them by a comma (layer1, layer2) \n - you can render multiple groups as well as ungrouped layers but you must specify one group per line and have ungrouped layers on a separate line"
projRenderOffset = 0

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog

    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Mocha Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Mocha' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "JobDescriptionSeparator", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )
    
    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "JobOptionsSeparator", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

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
    scriptDialog.AddControlToGrid( "MochaOptionsSeparator", "SeparatorControl", "Mocha Options", 0, 0, colSpan=4 )

    # Mocha specific options    
    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 12, 0, "The version of Mocha Pro to render/export with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "5", ("5",), 12, 1 )    
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Mocha Project File With Job", 12, 2, "If this option is enabled, the project file will be submitted with the job, and then copied locally to the slave machine during rendering.", colSpan=2 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Mocha Project File", 13, 0, "The Mocha project to be rendered/exported.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Mocha Files (*.mocha);;All Files (*)", 13, 1, "", True, 1, 3 )

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Directory", 14, 0, "The directory where the render/export output will be written to.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox", "FolderBrowserControl", "", "", 14, 1, "", True, 1, 3 )

    scriptDialog.AddControlToGrid( "FrameIndexWidthLabel", "LabelControl", "Frame Index Width", 15, 0, "The number of digits allocated for the index portion of the file name. If the number is not large enough to accomodate all output frame indices, it will be ignored and the minimum required number of digits will be used instead.", False )
    scriptDialog.AddRangeControlToGrid( "FrameIndexWidthBox", "RangeControl", 0, 0, 10, 0, 1, 15, 1 )
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame Range", 15, 2, "Frame range to render/export.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 15, 3, "" )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 16, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 16, 1 )
    scriptDialog.AddControlToGrid( "FrameOffsetLabel", "LabelControl", "Frame Offset", 16, 2, "If the project frame range does not start with 0, please specify the offset.", False )
    scriptDialog.AddRangeControlToGrid( "FrameOffsetBox", "RangeControl", 0, 0, 1000000, 0, 1, 16, 3 )

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()  

    scriptDialog.AddTabPage("Advanced")
    scriptDialog.AddGrid()

    readExportersLists()

    scriptDialog.AddControlToGrid( "JobTypeLabel", "LabelControl", "Job Type", 0, 0, "The type of Mocha job.", False )
    jobTypeBox = scriptDialog.AddComboControlToGrid( "JobTypeBox", "ComboControl", "Render", ("Render","Export"), 0, 1 )
    jobTypeBox.ValueModified.connect(jobTypeChanged)

    scriptDialog.AddControlToGrid( "JobSubTypeLabel", "LabelControl", "Job Sub Type", 0, 2, "The sub type of Mocha job.", False )
    jobSubTypeBox = scriptDialog.AddComboControlToGrid( "JobSubTypeBox", "ComboControl", "", [], 0, 3 ) 
    jobSubTypeBox.ValueModified.connect(jobSubTypeChanged)

    # settings applicable when rendering
    scriptDialog.AddControlToGrid( "RenderOptionsSeparator", "SeparatorControl", "Render Options", 1, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "FileExtensionLabel", "LabelControl", "File Extension", 2, 0, "The output file extension." )
    versionBox = scriptDialog.AddComboControlToGrid( "FileExtensionBox", "ComboControl", "png", fileExtensions, 2, 1 )

    scriptDialog.AddControlToGrid( "ClipViewIndexLabel", "LabelControl", "Clip View Index", 2, 2, "By default, this is zero (0), but if you are working with a multi-view clip, you can set the index here. In stereo mode, Left and Right views are 0 and 1 respectively.", False )
    scriptDialog.AddComboControlToGrid( "ClipViewIndexBox", "ComboControl", "0", ("0","1"), 2, 3 )

    scriptDialog.AddControlToGrid( "OutputPrefixLabel", "LabelControl", "Output Prefix", 3, 0, "The output prefix goes before the frame number in the file name. Not required." )
    scriptDialog.AddControlToGrid( "OutputPrefixBox", "TextControl", "", 3, 1 )

    scriptDialog.AddControlToGrid( "OutputSuffixLabel", "LabelControl", "Output Suffix", 3, 2, "The output suffix goes after the frame number in the file name. Not required." )
    scriptDialog.AddControlToGrid( "OutputSuffixBox", "TextControl", "", 3, 3)

    scriptDialog.AddControlToGrid( "LayerGroupLabel", "LabelControl", "Layers", 4, 0, "The layers to render." )
    scriptDialog.AddControlToGrid( "LayerGroupBox", "MultiLineTextControl", "", 4, 1, layerGroupTooltip, colSpan=3 )

    # settings applicable when exporting
    scriptDialog.AddControlToGrid( "ExportOptionsSeparator", "SeparatorControl", "Export Options", 5, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "ExporterNameLabel", "LabelControl", "Exporter Name", 6, 0, "The name of the exporter. The exporters list can be accessed in <repository>/plugins/Mocha/Exporters.txt.", )
    versionBox = scriptDialog.AddComboControlToGrid( "ExporterNameBox", "ComboControl", "", [], 6, 1, "", True, 1, 3)
    updateExportersList()

    scriptDialog.AddControlToGrid( "FileNameLabel", "LabelControl", "File Name", 7, 0, "The exporter output file name. Please include the file extension applicable for the selected exporter." )
    scriptDialog.AddControlToGrid( "FileNameBox", "TextControl", "", 7, 1, "", True, 1, 3  )

    scriptDialog.AddControlToGrid( "ViewsLabel", "LabelControl", "View Names", 8, 0, "List of names or abbreviations of views to export (use comma as the delimiter). When in stereo mode, Left(L) will be used by default." )
    scriptDialog.AddControlToGrid( "ViewsBox", "TextControl", "", 8, 1, "", True, 1, 3  )  

    scriptDialog.AddControlToGrid( "FrameTimeLabel", "LabelControl", "Frame Time", 9, 0, "The frame time argument is used when working with tracking data exporters." )
    scriptDialog.AddRangeControlToGrid( "FrameTimeBox", "RangeControl", 0.000, 0.000, 10000, 3, 0.001, 9, 1 )

    scriptDialog.AddControlToGrid( "ColorizeLabel", "LabelControl", "Colorize", 9, 2, "Used to export the colored version of the mattes." )
    jobTypeBox = scriptDialog.AddComboControlToGrid( "ColorizeBox", "ComboControl", "Grayscale", colorizeTypes, 9, 3 )

    scriptDialog.AddSelectionControlToGrid( "InvertBox", "CheckBoxControl", True, "Invert", 10, 1, "Mimes Invert the checkbox in Mocha's Export Tracking Data dialog." )

    scriptDialog.AddSelectionControlToGrid( "StabilizeBox", "CheckBoxControl", True, "Stabilize", 10, 2, "Mimes the Stabilize checkbox of the Export Tracking Data dialog." )

    scriptDialog.AddSelectionControlToGrid( "RemoveLensDistortionBox", "CheckBoxControl", True, "Remove Lens Distortion", 10, 3, "Mimes the Remove Lens Distortion checkbox of the Export Tracking Data dialog." ) 

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()    
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "MochaMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(submitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
   
    updateJobSubTypeList()
    adjustOptionsSelection()

    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","VersionBox","SceneBox","SubmitSceneBox","OutputBox","FrameIndexWidthBox","FrameOffsetBox","FramesBox","ChunkSizeBox","JobTypeBox","JobSubTypeBox","FileExtensionBox","OutputPrefixBox","OutputSuffixBox","LayerGroupBox","ClipViewIndexBox","ExporterNameBox","FileNameBox","ViewsBox","FrameTimeBox","ColorizeBox","InvertBox","StabilizeBox","RemoveLensDistortionBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "MochaSettings.ini" )

def jobTypeChanged():  
    updateJobSubTypeList()  
    adjustOptionsSelection()

def updateJobSubTypeList():
    if scriptDialog.GetValue( "JobTypeBox" ) == "Render":
        scriptDialog.SetItems( "JobSubTypeBox", renderTypes )
    else:
        scriptDialog.SetItems( "JobSubTypeBox", exportTypes )

def adjustOptionsSelection():
    if scriptDialog.GetValue("JobTypeBox") == "Render":
        enableRenderJobOptions ( True )
        enableExportJobOptions ( False )
    else:
        enableRenderJobOptions ( False )
        enableExportJobOptions ( True )

def enableRenderJobOptions( enable ):
    scriptDialog.SetEnabled ( "RenderOptionsSeparator", enable )
    scriptDialog.SetEnabled ( "FileExtensionLabel", enable )
    scriptDialog.SetEnabled ( "FileExtensionBox", enable )
    scriptDialog.SetEnabled ( "OutputPrefixLabel", enable )
    scriptDialog.SetEnabled ( "OutputPrefixBox", enable )
    scriptDialog.SetEnabled ( "OutputSuffixLabel", enable )
    scriptDialog.SetEnabled ( "OutputSuffixBox", enable )
    scriptDialog.SetEnabled ( "LayerGroupLabel", enable )
    scriptDialog.SetEnabled ( "LayerGroupBox", enable )
    scriptDialog.SetEnabled ( "ClipViewIndexLabel", enable )
    scriptDialog.SetEnabled ( "ClipViewIndexBox", enable )

def enableExportJobOptions( enable ):
    scriptDialog.SetEnabled ( "ExportOptionsSeparator", enable )
    scriptDialog.SetEnabled ( "ViewsLabel", enable )
    scriptDialog.SetEnabled ( "ViewsBox", enable )
    scriptDialog.SetEnabled ( "ExporterNameLabel", enable )
    scriptDialog.SetEnabled ( "ExporterNameBox", enable )
    scriptDialog.SetEnabled ( "FileNameLabel", enable )
    scriptDialog.SetEnabled ( "FileNameBox", enable )
    scriptDialog.SetEnabled ( "FrameTimeLabel", enable )
    scriptDialog.SetEnabled ( "FrameTimeBox", enable )
    scriptDialog.SetEnabled ( "ColorizeBox", enable )
    scriptDialog.SetEnabled ( "ColorizeLabel", enable ) 
    scriptDialog.SetEnabled ( "InvertBox", enable )
    scriptDialog.SetEnabled ( "RemoveLensDistortionBox", enable )
    scriptDialog.SetEnabled ( "StabilizeBox", enable )

# this is to accomodate Rendered Shapes export hybrid options
def jobSubTypeChanged():
    updateExportersList()
    if scriptDialog.GetValue( "JobTypeBox" ) == "Export" and scriptDialog.GetValue( "JobSubTypeBox" ) == "Rendered Shapes":
        updateExportOptions ( True )
    elif scriptDialog.GetValue( "JobTypeBox" ) == "Export" and scriptDialog.GetValue( "JobSubTypeBox" ) != "Rendered Shapes":
        updateExportOptions ( False )

    updateExportersList()

def updateExportOptions( enable ):
    # enable is True if subtype == "Rendered Shapes"; False otherwise
    scriptDialog.SetEnabled ( "RenderOptionsSeparator", enable )

    scriptDialog.SetEnabled ( "FileExtensionLabel", enable )
    scriptDialog.SetEnabled ( "FileExtensionBox", enable )
    scriptDialog.SetEnabled ( "OutputPrefixLabel", enable )
    scriptDialog.SetEnabled ( "OutputPrefixBox", enable )
    scriptDialog.SetEnabled ( "OutputSuffixLabel", enable )
    scriptDialog.SetEnabled ( "OutputSuffixBox", enable )
    scriptDialog.SetEnabled ( "LayerGroupLabel", enable )
    scriptDialog.SetEnabled ( "LayerGroupBox", enable )

    scriptDialog.SetEnabled ( "ExporterNameLabel", not enable )
    scriptDialog.SetEnabled ( "ExporterNameBox", not enable )
    scriptDialog.SetEnabled ( "FileNameLabel", not enable ) 
    scriptDialog.SetEnabled ( "FileNameBox", not enable )

def updateExportersList():
    if scriptDialog.GetValue( "JobSubTypeBox" ) == "Shapes":
        scriptDialog.SetItems( "ExporterNameBox", exporters[ "Shapes" ] )
    if scriptDialog.GetValue( "JobSubTypeBox" ) == "Tracking":
        scriptDialog.SetItems( "ExporterNameBox", exporters[ "Tracking" ] )
    if scriptDialog.GetValue( "JobSubTypeBox" ) == "Camera solve":
        scriptDialog.SetItems( "ExporterNameBox", exporters[ "Camera solve" ] )
    if scriptDialog.GetValue( "JobSubTypeBox" ) == "Rendered Shapes":
        scriptDialog.SetItems( "ExporterNameBox", [] )

def readExportersLists():
    exportersListFileName = RepositoryUtils.GetRepositoryFilePath( "plugins/Mocha/Exporters.txt", True )
    
    if os.path.isfile( exportersListFileName ):
        exportersListFile = open ( exportersListFileName, 'r' ) 

        line = exportersListFile.readline()
        while line != None and line != "":
            if ( not line.isspace() ):
                exporterType = ""
                exporterType = line[ : line.find(" data exporters") ]
                if ( len( exporterType ) > 0 ):
                    temp = []
                    line = exportersListFile.readline()
                    while ( line != None and line != "" and not line.isspace() and line.find(" data exporters") == -1 ):
                        temp.append ( line.strip() )
                        line = exportersListFile.readline()
                    exporters[exporterType] = temp
                else:
                    print ("Unexpected format of the exporters list.")
                    return
            else:
                line = exportersListFile.readline()
    else:
        print ("The exporters list file was not found in the Mocha plugin folder.")

def getJobSubType():
    return scriptDialog.GetValue( "JobSubTypeBox" ).lower().replace(" ", "-")

def getColorizeType():
    return scriptDialog.GetValue( "ColorizeBox" ).lower().replace(" ", "-")

def getOutputFilename():
    outputFilename = ""

    largestFrameRequested = FrameUtils.Parse( scriptDialog.GetValue( "FramesBox" ) )[-1]
    frameWidth = max ( int( scriptDialog.GetValue( "FrameIndexWidthBox" ) ), len( str( largestFrameRequested ) ) )

    path = scriptDialog.GetValue( "OutputBox" ).strip()
    prefix = scriptDialog.GetValue( "OutputPrefixBox" ).strip()
    suffix = scriptDialog.GetValue( "OutputSuffixBox" ).strip()
    padding = "#" * frameWidth
    fileExtension = scriptDialog.GetValue( "FileExtensionBox" ).strip()

    outputFilename = path + "/" + prefix + padding + suffix + "." + fileExtension

    return outputFilename

def packLayerGroupInfo():
    layerGroupString = scriptDialog.GetValue( "LayerGroupBox" )
    layerGroupString = layerGroupString.replace("\n", ";").replace("\r", ";")

    return layerGroupString

def sanityChecksPassed():
    sceneFile = scriptDialog.GetValue( "SceneBox" ).strip()
    if( len( sceneFile ) == 0 ):
        scriptDialog.ShowMessageBox( "No Mocha file specified.", "Error" )
        return False
    
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "Mocha file %s does not exist." % sceneFile, "Error" )
        return False

    outputDirectory = scriptDialog.GetValue( "OutputBox" ).strip()
    if( len( outputDirectory ) == 0 ):
        scriptDialog.ShowMessageBox( "No output directory specified.", "Error" )
        return False

    if( not Directory.Exists( outputDirectory ) ):
        scriptDialog.ShowMessageBox( "Output directory %s does not exist." % outputDirectory, "Error" )
        return False

    # If the submit scene box is checked, check if they are local. If they are, warn the user
    elif( not bool( scriptDialog.GetValue("SubmitSceneBox") ) and PathUtils.IsPathLocal( sceneFile ) ):
        result = scriptDialog.ShowMessageBox( "The Mocha file " + sceneFile + " is local.\n\nAre you sure you want to continue?", "Warning", ("Yes","No") )
        if( result == "No" ):
            return False

    frames = scriptDialog.GetValue( "FramesBox" )
    if ( len( frames.strip() ) == 0 or not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid." % frames, "Error" )
        return False

    if ( scriptDialog.GetValue( "JobTypeBox" ) == "Export" and scriptDialog.GetValue( "JobSubTypeBox" ) != "Rendered Shapes" ):
        if not len( scriptDialog.GetValue( "FileNameBox" ).strip() ) > 0:
            scriptDialog.ShowMessageBox( "File name must be specified.", "Error" )
            return False

    return True

def submitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    
    if not sanityChecksPassed():
        return

    outputFilename = getOutputFilename()

    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( outputFilename ):
        return
    
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "mocha_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Mocha" )
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
    
    writer.WriteLine( "Frames=%s" %  scriptDialog.GetValue( "FramesBox" ) )   
    writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )

    # Integration
    extraKVPIndex = 0
    groupBatch = False
    
    if integration_dialog.IntegrationProcessingRequested():
        extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
        groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()
                
    writer.WriteLine()
    writer.WriteLine( "OutputFilename0=%s" % outputFilename )

    if groupBatch:
        writer.WriteLine( "BatchName=%s" % ( jobName ) ) 

    writer.Close()
    
    # Create plugin info file
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "mocha_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    writer.WriteLine( "Version=%s" %  scriptDialog.GetValue( "VersionBox" ) )
    if not bool( scriptDialog.GetValue("SubmitSceneBox") ):
        writer.WriteLine( "Scene=%s" %  scriptDialog.GetValue( "SceneBox" ) )
    writer.WriteLine( "Output=%s" %  scriptDialog.GetValue( "OutputBox" ) )
    writer.WriteLine( "FrameIndexWidth=%s" % scriptDialog.GetValue( "FrameIndexWidthBox" ) )
    writer.WriteLine( "ProjFrameOffset=%s" % scriptDialog.GetValue( "FrameOffsetBox" ) )

    writer.WriteLine( "JobType=%s" %  scriptDialog.GetValue( "JobTypeBox" ) )
    writer.WriteLine( "JobSubType=%s" %  getJobSubType() )
    if scriptDialog.GetValue("JobTypeBox") == "Render":
        writer.WriteLine( "FileExtension=%s" % scriptDialog.GetValue( "FileExtensionBox" ) )
        writer.WriteLine( "OutputPrefix=%s" % scriptDialog.GetValue( "OutputPrefixBox" ) )
        writer.WriteLine( "OutputSuffix=%s" % scriptDialog.GetValue( "OutputSuffixBox" ) )
        writer.WriteLine( "LayerGroupInfo=%s" % packLayerGroupInfo() ) # adds info about groups and layers
        writer.WriteLine( "ClipViewIndex=%s" % scriptDialog.GetValue( "ClipViewIndexBox" ) )

    elif scriptDialog.GetValue("JobTypeBox") == "Export" and scriptDialog.GetValue("JobSubTypeBox") != "Rendered Shapes":
        writer.WriteLine( "ExporterName=%s" % scriptDialog.GetValue( "ExporterNameBox" ) )
        writer.WriteLine( "FileName=%s" % scriptDialog.GetValue( "FileNameBox" ) )
        writer.WriteLine( "Views=%s" %  scriptDialog.GetValue( "ViewsBox" ) )
        writer.WriteLine( "Colorize=%s" % getColorizeType() )       
        writer.WriteLine( "Invert=%s" % scriptDialog.GetValue( "InvertBox" ) )
        writer.WriteLine( "RemoveLensDistortion=%s" % scriptDialog.GetValue( "RemoveLensDistortionBox" ) )
        writer.WriteLine( "Stabilize=%s" % scriptDialog.GetValue( "StabilizeBox" ) )

    elif scriptDialog.GetValue("JobTypeBox") == "Export" and scriptDialog.GetValue("JobSubTypeBox") == "Rendered Shapes":
        # "Rendered Shapes" is a hybrid between rendering and exporting
        writer.WriteLine( "FileExtension=%s" % scriptDialog.GetValue( "FileExtensionBox" ) )
        writer.WriteLine( "OutputPrefix=%s" % scriptDialog.GetValue( "OutputPrefixBox" ) )
        writer.WriteLine( "OutputSuffix=%s" % scriptDialog.GetValue( "OutputSuffixBox" ) )
        writer.WriteLine( "LayerGroupInfo=%s" % packLayerGroupInfo() ) # adds info about groups and layers
        writer.WriteLine( "FileName=%s" % scriptDialog.GetValue( "FileNameBox" ) )
        writer.WriteLine( "Views=%s" %  scriptDialog.GetValue( "ViewsBox" ) )
        writer.WriteLine( "Colorize=%s" % getColorizeType() )       
        writer.WriteLine( "Invert=%s" % scriptDialog.GetValue( "InvertBox" ) )
        writer.WriteLine( "RemoveLensDistortion=%s" % scriptDialog.GetValue( "RemoveLensDistortionBox" ) )
        writer.WriteLine( "Stabilize=%s" % scriptDialog.GetValue( "StabilizeBox" ) )

    writer.Close()
    
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( sceneFile )
    
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )