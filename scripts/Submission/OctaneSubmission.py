import re

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import traceback

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
DraftRequested = False
formatOptions = ["png8", "png16", "exr", "exrtonemapped"]
isOrbxFile = False

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
    scriptDialog.SetTitle( "Submit Octane Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Octane' ) )

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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Octane Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Octane Scene File", 1, 0, "The scene file to render.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Octane Scene Files (*.ocs);;Octane Package Files (*.orbx)", 1, 1, colSpan=3 )
    sceneBox.ValueModified.connect( SceneBoxChanged )

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Folder", 2, 0, "Override the output path in the scene.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox","FolderBrowserControl", "","All Files (*)", 2, 1, colSpan=3 )

    framePerFileBox = scriptDialog.AddSelectionControlToGrid( "FramePerFileBox", "CheckBoxControl", False, "Enable \"Single Frame per OCS File\" Mode", 3, 0, "Enable this mode if you have an animation with one frame per OCS file. Select just one file from the sequence.", colSpan=2 )
    framePerFileBox.ValueModified.connect( FramePerFileBoxChanged )

    scriptDialog.AddControlToGrid( "FilenameTemplateLabel", "LabelControl", "Filename Template", 4, 0, "Template parameters:\n\t%i render target index\n\t%n render target node name\n\t%e file extension\n\t%t timestamp\n\t%f frame number\n\t%F frame number prefixed with 0s\n\t%s sub frame number\n\t%p render pass name\nNote: Parameters ignored in \"Single Frame per OCS File\" mode." )
    scriptDialog.AddControlToGrid( "FilenameTemplateBox", "TextControl", "%F.%e", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 5, 0, "The Octane Standalone application version to use.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "4", ( "1", "2", "3", "4" ), 5, 1 )
    versionBox.ValueModified.connect( VersionBoxChanged )

    scriptDialog.AddControlToGrid( "FileFormatLabel", "LabelControl", "File Format", 5, 2, "What format the output file will be saved as.", False )
    scriptDialog.AddComboControlToGrid( "FileFormatBox", "ComboControl", "png8", formatOptions, 5, 3 )

    scriptDialog.AddControlToGrid( "TargetOCSLabel", "LabelControl", "Render Target (ocs)", 6, 0, "Select the target to render (ocs files only).", False )
    scriptDialog.AddComboControlToGrid( "TargetOCSBox", "ComboControl", "", [""], 6, 1 )
    scriptDialog.SetEnabled( "TargetOCSBox", False )
    scriptDialog.AddControlToGrid( "TargetORBXLabel", "LabelControl", "Render Target (orbx)", 6, 2, "The target to render (orbx files only). Leaving this field blank will render all targets.", False )
    scriptDialog.AddControlToGrid( "TargetORBXBox", "TextControl", "", 6, 3 )
    scriptDialog.SetEnabled( "TargetORBXBox", False )
    
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 7, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 7, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 8, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 8, 1, colSpan=2 )
    singleFileBox = scriptDialog.AddSelectionControlToGrid( "SingleFileBox", "CheckBoxControl", False, "Single Frame Job", 8, 3, "This should be checked if you're submitting a single Octane file only, as opposed to separate files per frame. " )
    singleFileBox.ValueModified.connect(SingleFileBoxChanged)
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.AddTabPage("Advanced Options")
    scriptDialog.AddGrid()
    overrideSamplingCheck = scriptDialog.AddSelectionControlToGrid( "OverrideSamplingBox", "CheckBoxControl", False, "Override Sampling", 9, 0, "Enable to override the Sampling setting in the scene file.", False )
    overrideSamplingCheck.ValueModified.connect(OverrideSamplingChanged)
    scriptDialog.AddRangeControlToGrid( "SampleBox", "RangeControl", 10, 0, 100000, 0, 1, 9, 1, colSpan=2 )
    scriptDialog.SetEnabled("SampleBox", False)
    
    scriptDialog.AddControlToGrid( "GPUsPerTaskLabel", "LabelControl", "GPUs Per Task", 10, 0, "The number of GPUs to use per task. If set to 0, the default number of GPUs will be used, unless 'Select GPU Devices' Id's have been defined.", False )
    GPUsPerTaskBox = scriptDialog.AddRangeControlToGrid( "GPUsPerTaskBox", "RangeControl", 0, 0, 1024, 0, 1, 10, 1, colSpan=2 )
    GPUsPerTaskBox.ValueModified.connect(GPUsPerTaskChanged)

    scriptDialog.AddControlToGrid( "GPUsSelectDevicesLabel", "LabelControl", "Select GPU Devices", 11, 0, "A comma separated list of the GPU devices to use specified by device Id. 'GPUs Per Task' will be ignored.", False )
    GPUsSelectDevicesBox = scriptDialog.AddControlToGrid( "GPUsSelectDevicesBox", "TextControl", "", 11, 1, colSpan=2 )
    GPUsSelectDevicesBox.ValueModified.connect(GPUsSelectDevicesChanged)

    scriptDialog.AddControlToGrid( "CmdLabel", "LabelControl", "Command Line Args", 12, 0, "Additional command line arguments to use for rendering.", False )
    scriptDialog.AddControlToGrid( "CmdBox", "TextControl", "", 12, 1, colSpan=3 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "OctaneMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )

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
    
    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","OutputBox","SampleBox","FramesBox","FilenameTemplateBox","FileFormatBox","CmdBox","SingleFileBox", "OverrideSamplingBox","TargetORBXBox","ChunkSizeBox","VersionBox","FramePerFileBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    scriptDialog.ShowDialog( False )

def GPUsPerTaskChanged( *args ):
    global scriptDialog

    perTaskEnabled = ( scriptDialog.GetValue( "GPUsPerTaskBox" ) == 0 )

    scriptDialog.SetEnabled( "GPUsSelectDevicesLabel", perTaskEnabled )
    scriptDialog.SetEnabled( "GPUsSelectDevicesBox", perTaskEnabled )

def GPUsSelectDevicesChanged( *args ):
    global scriptDialog

    selectDeviceEnabled = ( scriptDialog.GetValue( "GPUsSelectDevicesBox" ) == "" )

    scriptDialog.SetEnabled( "GPUsPerTaskLabel", selectDeviceEnabled )
    scriptDialog.SetEnabled( "GPUsPerTaskBox", selectDeviceEnabled )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "OctaneSettings.ini" )

def SceneBoxChanged( *args ):
    global scriptDialog
    filename = scriptDialog.GetValue("SceneBox")
    
    DetermineFrameRange( filename )
    DetermineRenderTargets( filename )

def DetermineFrameRange( filename ):
    global scriptDialog
    try:
        if(File.Exists(filename)):
            paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
            if paddingSize > 0:
                frameString = "1"
                startFrame = 0
                endFrame = 0
                initFrame = FrameUtils.GetFrameNumberFromFilename( filename )

                startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
                endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
                if( startFrame != endFrame ):
                    frameString = str(startFrame) + "-" + str(endFrame)
                    scriptDialog.SetValue("FramesBox",frameString)
                    scriptDialog.SetValue("SingleFileBox",False)
                else:
                    scriptDialog.SetValue("SingleFileBox",True)
            else:
                scriptDialog.SetValue("SingleFileBox",True)
    except:
        pass
        
def DetermineRenderTargets( filename ):
    global isOrbxFile
    targetList = []
    framePerFileMode = scriptDialog.GetValue( "FramePerFileBox" )

    if filename[-5:] == ".orbx":
        isOrbxFile = True
    else:
        isOrbxFile = False

        try:
            if File.Exists( filename ):
                ocsGraph = ET.parse( filename )
                ocsRoot = ocsGraph.getroot()
                
                if ocsRoot.tag == "OCS2":
                    renderTargets = ocsRoot.findall( "./graph/node" )
                    for node in renderTargets:
                        nodeType = node.attrib.get( "type", "" )
                        nodeName = node.attrib.get( "name", "" )
                        if nodeType == "56" and nodeName != "":
                            targetList.append( nodeName )
                    
                else:
                    renderTargets = ocsRoot.findall( "./Node/childgraph/NodeGraph/nodes/*" )
                    for node in renderTargets:
                        typename = node.find( "typename" ).text
                        if typename == "rendertarget":
                            renderTarget = node.find( "name" ).text
                            targetList.append( renderTarget )
        except:
            ClientUtils.LogText( "Error parsing Octane scene file: " + traceback.format_exc() )

    if isOrbxFile and not framePerFileMode:
        scriptDialog.SetItems( "TargetOCSBox", [""] )
        scriptDialog.SetEnabled( "TargetOCSBox", False )
        scriptDialog.SetEnabled( "TargetOCSLabel", False )
        scriptDialog.SetEnabled( "TargetORBXBox", True )
        scriptDialog.SetEnabled( "TargetORBXLabel", True )
    elif len( targetList ) > 0:
        scriptDialog.SetItems( "TargetOCSBox", targetList )
        scriptDialog.SetEnabled( "TargetOCSBox", True )
        scriptDialog.SetEnabled( "TargetOCSLabel", True )
        scriptDialog.SetItems( "TargetORBXBox", "" )
        scriptDialog.SetEnabled( "TargetORBXBox", False )
        scriptDialog.SetEnabled( "TargetORBXLabel", False )
    else:
        scriptDialog.SetItems( "TargetOCSBox", [""] )
        scriptDialog.SetEnabled( "TargetOCSBox", False )
        scriptDialog.SetEnabled( "TargetOCSLabel", False )
        scriptDialog.SetItems( "TargetORBXBox", "" )
        scriptDialog.SetEnabled( "TargetORBXBox", False )
        scriptDialog.SetEnabled( "TargetORBXLabel", False )

def OverrideSamplingChanged( *args ):
    global scriptDialog
    
    enabled = scriptDialog.GetValue("OverrideSamplingBox")
    scriptDialog.SetEnabled("SampleBox", enabled)

def SingleFileBoxChanged( *args ):
    global scriptDialog
    singleFileChecked = scriptDialog.GetValue( "SingleFileBox" )
    framePerFileMode = scriptDialog.GetValue( "FramePerFileBox" )
    
    enabled = not singleFileChecked
    scriptDialog.SetEnabled( "FramesLabel", enabled )
    scriptDialog.SetEnabled( "FramesBox", enabled )

    if framePerFileMode:
        scriptDialog.SetEnabled( "ChunkSizeLabel", False )
        scriptDialog.SetEnabled( "ChunkSizeBox", False )
    else:
        scriptDialog.SetEnabled( "ChunkSizeLabel", enabled )
        scriptDialog.SetEnabled( "ChunkSizeBox", enabled )

def FramePerFileBoxChanged( *args ):
    global scriptDialog
    framePerFileMode = scriptDialog.GetValue( "FramePerFileBox" )
    filename = scriptDialog.GetValue( "SceneBox" )
    enabled = not framePerFileMode
    singleFileChecked = scriptDialog.GetValue( "SingleFileBox" )
    
    DetermineRenderTargets(filename)

    if not singleFileChecked:
        scriptDialog.SetEnabled( "ChunkSizeLabel", enabled )
        scriptDialog.SetEnabled( "ChunkSizeBox", enabled )

def VersionBoxChanged( *args ):
    global scriptDialog
    version = scriptDialog.GetValue( "VersionBox" )

    if version == "1":
        scriptDialog.SetValue( "FramePerFileBox", True )
        scriptDialog.SetEnabled( "FramePerFileBox", False )
    else:
        scriptDialog.SetValue( "FramePerFileBox", False )
        scriptDialog.SetEnabled( "FramePerFileBox", True )
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog

    errors = ""
    
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "The Octane scene file %s does not exist" % sceneFile, "Error" )
        return
    elif (not scriptDialog.GetValue("SceneBox") and PathUtils.IsPathLocal(sceneFile)):
        result = scriptDialog.ShowMessageBox( "The Octane scene file %s is local. Are you sure you want to continue?" % sceneFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return

    outputFolder = scriptDialog.GetValue( "OutputBox" )
    if outputFolder == "":
        errors += "An output folder must be chosen."
    elif( not Directory.Exists( Path.GetDirectoryName( outputFolder ) ) ):
        scriptDialog.ShowMessageBox( "The directory of the output folder %s does not exist." % Path.GetDirectoryName( outputFolder ), "Error" )
        return
    elif( PathUtils.IsPathLocal( outputFolder ) ):
        result = scriptDialog.ShowMessageBox( "The output folder %s is local. Are you sure you want to continue?" % outputFolder, "Warning", ( "Yes","No" ) )
        if( result=="No" ):
            return

    framePerFile = scriptDialog.GetValue( "FramePerFileBox" )
    if framePerFile and sceneFile[-5:] == ".orbx":
        errors += "An orbx file cannot be selected in \"Single Frame per OCS File\" mode."

    filenameTemplate = scriptDialog.GetValue( "FilenameTemplateBox" )
    if ".%e" not in filenameTemplate:
        errors += ( "The filename template \"%s\" is invalid! It must contain \".%%e\"." % filenameTemplate )
    elif ( "%F" not in filenameTemplate ) and ( "%f" not in filenameTemplate ):
        result = scriptDialog.ShowMessageBox( "The filename template does not contain any padding (%F or %f). Are you sure you want to continue?", "Warning", ( "Yes", "No" ) )
        if( result == "No" ):
            return
          
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    singleFile = scriptDialog.GetValue("SingleFileBox")
    if( singleFile ):
        frames = "0"
    elif( not FrameUtils.FrameRangeValid( frames ) ):
        errors += (" - Frame range '%s' is not valid.\n" % frames)
    
    # If Octane and using 'select GPU device Ids' then check device Id syntax is valid
    if scriptDialog.GetValue( "GPUsPerTaskBox" ) == 0 and scriptDialog.GetValue( "GPUsSelectDevicesBox" ) != "" :
        regex = re.compile( "^(\d{1,2}(,\d{1,2})*)?$" )
        validSyntax = regex.match( scriptDialog.GetValue( "GPUsSelectDevicesBox" ) )
        if not validSyntax:
           errors += "'Select GPU Devices' syntax is invalid!\n\nTrailing 'commas' if present, should be removed.\n\nValid Examples: 0 or 2 or 0,1,2 or 0,3,4 etc\n"
           
        # Check if concurrent threads > 1
        if scriptDialog.GetValue( "ConcurrentTasksBox" ) > 1:
            errors += "If using 'Select GPU Devices', then 'Concurrent Tasks' must be set to 1\n"

    # Check if Integration options are valid.
    if not integration_dialog.CheckIntegrationSanity():
        return
    
    if len( errors ) > 0:
        scriptDialog.ShowMessageBox( "The following errors were found:\n\n" + errors + "\nPlease fix these before submitting the job.", "Error" )
        return

    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "octane_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Octane" )
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
    writer.WriteLine( "Frames=%s" % frames )

    if scriptDialog.GetEnabled( "ChunkSizeBox" ):
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )

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

    if outputFolder != "":
        writer.WriteLine( "OutputDirectory0=%s" % outputFolder )
    
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "octane_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    writer.WriteLine("SceneFile=%s" % sceneFile)
    writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )
    writer.WriteLine("SingleFile=%s" % singleFile)
    writer.WriteLine( "FramePerFileMode=%s" % framePerFile )
    
    if outputFolder != "":
        writer.WriteLine( "OutputFolder=%s" % outputFolder )

    writer.WriteLine( "FilenameTemplate=%s" % filenameTemplate )
    writer.WriteLine( "FileFormat=%s" % scriptDialog.GetValue( "FileFormatBox" ) )
    
    overrideSampling = scriptDialog.GetValue("OverrideSamplingBox")
    if overrideSampling:
        writer.WriteLine("OverrideSampling=%s" % scriptDialog.GetValue("SampleBox"))

    if isOrbxFile:
        writer.WriteLine( "RenderTargetORBX=%s" % scriptDialog.GetValue( "TargetORBXBox" ) )
    else:
        writer.WriteLine( "RenderTargetOCS=%s" % scriptDialog.GetValue( "TargetOCSBox" ) )
    
    # Enumerate the render targets
    pos = 0
    for target in scriptDialog.GetItems( "TargetOCSBox" ):
        writer.WriteLine("RenderTargetOCS%d=%s" % (pos,target))
        pos += 1
    
    writer.WriteLine( "GPUsPerTask=%s" % scriptDialog.GetValue( "GPUsPerTaskBox" ) )
    writer.WriteLine( "GPUsSelectDevices=%s" % scriptDialog.GetValue( "GPUsSelectDevicesBox" ) )
    
    writer.WriteLine( "AdditionalArgs=%s" % scriptDialog.GetValue("CmdBox" ) )

    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )