from __future__ import print_function
from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import traceback
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
startup = True
ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = True

submissionSceneRoot = None
sceneAccessible = None

renderPassList = { 
                "rgb" : "tgRgb",
                "alpha" : "tgAlpha",
                
                "atmosphere_rgb" : "tgAtmoRgb",
                "atmosphere_alpha" : "tgAtmoAlpha",
                "atmosphere_direct" : "tgAtmoDirect",
                "atmosphere_indirect" : "tgAtmoIndirect",
                
                "cloud_rgb" : "tgCloudRgb",
                "cloud_alpha" : "tgCloudAlpha",
                "cloud_depth" : "tgCloudDepth",
                "cloud_position" : "tgCloudPos",
                "cloud_2d_motion" : "tgCloud2dMotion",
                "cloud_direct" : "tgCloudDirect",
                "cloud_indirect" : "tgCloudIndirect",
                
                "surface_direct" : "tgSurfDirect",
                "surface_indirect" : "tgSurfIndirect",
                "surface_direct_diffuse" : "tgSurfDirectDiff",
                "surface_indirect_diffuse" : "tgSurfIndirectDiff",
                "surface_direct_specular" : "tgSurfDirectSpec",
                "surface_indirect_specular" : "tgSurfIndirectSpec",
                "surface_emission" : "tgSurfEmit",
                "surface_depth" : "tgSurfDepth",
                "surface_position" : "tgSurfPos",
                "surface_2d_motion" : "tgSurf2dMotion",
                "surface_normal" : "tgSurfNormal",
                "surface_diffuse_colour" : "tgSurfDiffCol",
                "surface_rgb" : "tgSurfRgb",
                "surface_alpha" : "tgSurfAlpha" }

paddingRe = re.compile( "%([0-9]+)d", re.IGNORECASE )
                            
########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global startup
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Terragen Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Terragen' ) )
    
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
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job." )

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

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Terragen Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "ProjectLabel", "LabelControl", "Project File", 1, 0, "The Terragen project file to render.", False )
    projectBox = scriptDialog.AddSelectionControlToGrid( "ProjectBox", "FileBrowserControl", "", "Project Files (*.tgd)", 1, 1, colSpan=2 )
    projectBox.ValueModified.connect(ProjectModified)

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 2, 0, "The version of Terragen to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "4",("2","3","4"), 2, 1 )

    scriptDialog.AddControlToGrid( "RenderNodeLabel", "LabelControl", "Render Node (Optional)", 3, 0, "Optionally specify the render node to render. Leave blank to use the default in the project.", False )
    scriptDialog.AddComboControlToGrid( "RenderNodeBox", "ComboControl", "", ("",), 3, 1  )
    submitAllNodesBox = scriptDialog.AddSelectionControlToGrid( "SubmitAllNodesBox", "CheckBoxControl", False, "Submit All Render Nodes as Separate Jobs", 3, 2, "If this option is enabled, all render nodes in the project file will be submitted as separate jobs.")
    submitAllNodesBox.ValueModified.connect(SubmitAllNodesModified)
    
    scriptDialog.AddControlToGrid( "OutputLabel","LabelControl","Output (Optional)", 4, 0, "Optionally override the output path in the project file. If rendering a sequence of frames, remember to include the %04d format in the output file name so that padding is added to each frame.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox","FileSaverControl","", "BMP (*.bmp);;EXR (*.exr);;RGB (*.rgb);;SGI (*.sgi);;TIF (*.tif);;TIFF (*.tiff)", 4, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "ExtraOutputLabel","LabelControl","Extra Output (Optional)", 5, 0, "Optionally override the extra output path in the project file. If rendering a sequence of frames, remember to include the IMAGETYPE.%04d format in the output file name so that padding is added to each frame.", False )
    scriptDialog.AddSelectionControlToGrid( "ExtraOutputBox","FileSaverControl","", "BMP (*.bmp);;EXR (*.exr);;RGB (*.rgb);;SGI (*.sgi);;TIF (*.tif);;TIFF (*.tiff)", 5, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 6, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "1", 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LocalRenderingBox", "CheckBoxControl", False, "Enable Local Rendering", 6, 2, "If enabled, Deadline will render the frames locally before copying them over to the final network location. Note that this requires that an Output file be specified above.")

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 7, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Project File With Job", 7, 2, "If this option is enabled, the project file will be submitted with the job, and then copied locally to the slave machine during rendering.")
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
    integration_dialog.AddIntegrationTabs( scriptDialog, "TerragenMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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
    
    settings = ( "DepartmentBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","ProjectBox","OutputBox","ExtraOutputBox","FramesBox","ChunkSizeBox","SubmitSceneBox","LocalRenderingBox", "SubmitAllNodesBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    TilesChanged( None )
    SubmitAllNodesModified( None )
    
    startup = False
    
    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "TerragenSettings.ini" )

def ProjectModified( *args ):
    global startup
    
    unattachRenderScene()
    
    success = False
    
    filename = scriptDialog.GetValue( "ProjectBox" )
    if filename != "" and File.Exists( filename ):
        startFrame = ""
        endFrame = ""
        
        inRenderNode = False
        renderNodes = [""]
        renderNodeName = ""
        
        sceneRoot = getRenderScene()
        
        if sceneRoot is not None:
        
            startFrame = sceneRoot.get("start_frame")
            endFrame = sceneRoot.get( "end_frame" )
            
            terragenRenderNodes = sceneRoot.findall("render")
                        
            for node in terragenRenderNodes:
                renderNodes.append( node.get("name"))
            
            if startFrame != "" and endFrame != "":
                scriptDialog.SetValue( "FramesBox", startFrame + "-" + endFrame )
            else:
                scriptDialog.SetValue( "FramesBox", "" )
            
            scriptDialog.SetValue( "NameBox", Path.GetFileNameWithoutExtension( filename ) )
            scriptDialog.SetItems( "RenderNodeBox", tuple(renderNodes) )
            scriptDialog.SetValue( "RenderNodeBox", "" )
            success = True
        
    if not success:
        scriptDialog.SetValue( "FramesBox", "" )
        scriptDialog.SetValue( "NameBox", "Untitled" )
        scriptDialog.SetItems( "RenderNodeBox", ("",) )
        scriptDialog.SetValue( "RenderNodeBox", "" )

def SubmitAllNodesModified(*args):
    global scriptDialog
    enable = not scriptDialog.GetValue( "SubmitAllNodesBox" )
    
    scriptDialog.SetEnabled( "RenderNodeLabel", enable )
    scriptDialog.SetEnabled( "RenderNodeBox", enable )
        
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

def SingleFrameChanged(*args):
    global scriptDialog
    enableSingleFrameRegion = ( scriptDialog.GetValue( "SingleFrameEnabledCheck" ) and scriptDialog.GetEnabled( "SingleFrameEnabledCheck" ) )
    
    scriptDialog.SetEnabled( "SingleJobFrameLabel", enableSingleFrameRegion )
    scriptDialog.SetEnabled( "SingleJobFrameBox", enableSingleFrameRegion )

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

def unattachRenderScene():
    global submissionSceneRoot
    global sceneAccessible
    
    submissionSceneRoot = None
    sceneAccessible = None
    
def getRenderScene():
    global submissionSceneRoot
    global sceneAccessible
    global scriptDialog
    
    if sceneAccessible:
        return submissionSceneRoot
        
    elif sceneAccessible is None:
        try:
            submissionSceneRoot = ET.parse( scriptDialog.GetValue( "ProjectBox" ).strip() ).getroot()
            sceneAccessible = True
            return submissionSceneRoot
        except:
            pass
    
    sceneAccessible = False
    return None
    
def findMasterNodeName():
    sceneRoot = getRenderScene()
    if sceneRoot is None:
        return None
    
    terragenRenderNodes = sceneRoot.findall("render")
    for findNode in terragenRenderNodes:
        if findNode.get( "master" ) == "1":
            return findNode.get( "name" )
    
    return ""
    
    
def findRenderNode( nodeName ):
    sceneRoot = getRenderScene()
    if sceneRoot is None or nodeName == "":
        return None
    
    terragenRenderNodes = sceneRoot.findall("render")
        
    for findNode in terragenRenderNodes:
        if findNode.get( "name" ) == nodeName:
            return findNode
  
    return None

def findLayerNode( nodeName ):
    sceneRoot = getRenderScene()
    if sceneRoot is None or nodeName == "":
        return None
        
    sceneRoot = getRenderScene()
    terragenLayerNodes = sceneRoot.findall("render_layer")
    for findLayer in terragenLayerNodes:
        if findLayer.get( "name" ) == nodeName:
            return findLayer
            
    return None

def getSeparatePassDir( node ):
    
    if node is None:
        return False
    
    return (node.get( "create_subfolders" ) == "1")
    
def getRenderPasses( node, overrideExtraFile = False ):
    global renderPassList
    renderPasses = []
    
    if node is not None:
        if node.get( "extra_output_images" )  == "1" or overrideExtraFile:
            layerNode = findLayerNode( node.get( "render_layer" ) )
            
            if layerNode is not None:
                for key in renderPassList.keys():
                    if layerNode.get( key ) == "1":
                        renderPasses.append( renderPassList[ key ] )
            else:
                renderPasses = [ "tgAlpha" ]
            
    return renderPasses
    
def getNodeOutputFileName( node, sceneFile ):
    if node is None:
        return ""
    
    fileName = node.get( "output_image_filename" )
    if not os.path.isabs( fileName ):
        fileName = os.path.join( os.path.dirname( sceneFile ), fileName )
    fileName = os.path.normpath(fileName)
    
    return fileName

def getNodeExtraOutputFileName( node, sceneFile ):
    if node is None:
        return ""
    
    fileName = ""
    
    if node.get( "extra_output_images" ) == "1":
        fileName = node.get( "extra_output_image_filename" )
        if not os.path.isabs( fileName ):
            fileName = os.path.join( os.path.dirname( sceneFile ), fileName )
        fileName = os.path.normpath(fileName)
    
    return fileName

def replacePrintFPadding( fileName, frameNum = None ):
    global paddingRe
    
    if fileName == "":
        return fileName
    
    searchResults = paddingRe.search( fileName )
    
    if searchResults == None:
        return fileName
    
    paddingLength = int( searchResults.group(1) )
    
    padding = ""
    if frameNum is None:
        while len( padding ) < paddingLength:
            padding += "#"
    else:
        padding = str(frameNum)
        while len( padding ) < paddingLength:
            padding = "0" + padding
    
    fileName = paddingRe.sub( padding, fileName )
    return fileName

def WriteCommonJobFileProperites( writer, jobName, dependencies ):
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

    writer.WriteLine( "JobDependencies=%s" % dependencies )
        
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    
    version = scriptDialog.GetValue( "VersionBox" )
    submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
    
    unattachRenderScene()
    sceneRoot = getRenderScene()
    terragenRenderNodes = None
    terragenLayerNodes = None
    
    projectFile = scriptDialog.GetValue( "ProjectBox" ).strip()
    outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
    extraOutputFile = scriptDialog.GetValue( "ExtraOutputBox" ).strip()
    frames = scriptDialog.GetValue( "FramesBox" ) 
    
    regionRendering = scriptDialog.GetValue( "EnableTilesCheck" )
    singleFrameJob = scriptDialog.GetValue( "SingleFrameEnabledCheck" )
    singleFrameJobFrame = scriptDialog.GetValue( "SingleJobFrameBox" )
    submitDependent = scriptDialog.GetValue( "SubmitDependentCheck" )
    tilesInX = scriptDialog.GetValue("XTilesBox")
    tilesInY = scriptDialog.GetValue("YTilesBox")
    regionJobCount = tilesInX * tilesInY
    
    errors = []
    warnings = []
    
    # Check project file.
    if not File.Exists( projectFile ):
        errors.append( "Project file %s does not exist" % projectFile )
    elif PathUtils.IsPathLocal( projectFile ) and not submitScene:
        warnings.append( "Project file " + projectFile + " is local." )
        
    # Check output file if necessary.
    if outputFile != "":
        if not Directory.Exists( Path.GetDirectoryName( outputFile ) ):
            errors.append( "The directory of the output file does not exist:\n" + Path.GetDirectoryName( outputFile ) )
        elif PathUtils.IsPathLocal( outputFile ):
            warnings.append( "Output file " + outputFile + " is local." )

    # Check if Integration options are valid.
    if not integration_dialog.CheckIntegrationSanity( outputFile ):
        return
    
    # Check extra output file if necessary
    if extraOutputFile != "":
        if not Directory.Exists( Path.GetDirectoryName( extraOutputFile ) ):
            errors.append( "The directory of the extra output file does not exist:\n" + Path.GetDirectoryName( extraOutputFile ) )
        elif PathUtils.IsPathLocal( extraOutputFile ):
            warnings.append( "Extra output file " + extraOutputFile + " is local." )
        
    if regionRendering and sceneRoot is None:
        if outputFile == "":
            errors.append( "The specfied scene file cannot be read and no output file was set so Region rendering cannot be completed." )
        if not extraOutputFile == "":
            warnings.append( "The specified scene file cannot be read, so Extra output files will not be assembled." )
    
    # Check frames if necessary.
    if not FrameUtils.FrameRangeValid( frames ) and not singleFrameJob:
        errors.append( "Frame range %s is not valid" % frames )
    
    if regionRendering and singleFrameJob:
        taskLimit = RepositoryUtils.GetJobTaskLimit()
        if regionJobCount > taskLimit:
            errors.append( "Unable to submit job with " + str(regionJobCount) + " tasks.  Task Count exceeded Job Task Limit of "+str(taskLimit) )
    
    if len( errors ) > 0:
        errors = "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % "\n".join(errors)
        scriptDialog.ShowMessageBox( errors, "Error" )
        return

    if len( warnings ) > 0:
        warnings = "Warnings:\n\n%s\n\nAre you sure you want to continue?\n" % "\n".join(warnings)
        result = scriptDialog.ShowMessageBox( warnings, "Warning", ("Yes","No") )
        if result == "No":
            return
    
    renderNodes = [ scriptDialog.GetValue( "RenderNodeBox" ) ]
    if scriptDialog.GetValue( "SubmitAllNodesBox" ):
        renderNodes = scriptDialog.GetItems( "RenderNodeBox" )[1:]
    
    if renderNodes[ 0 ] == "" and sceneRoot is not None:
        renderNodes[0] = findMasterNodeName()
    
    jobName = scriptDialog.GetValue( "NameBox" )
    
    jobCount = 1
    if regionRendering and not singleFrameJob:
        jobCount = regionJobCount
        
    totalJobCount = 0
    totalSuccesses = 0
    totalFails = 0
    jobResult = ""
    for node in renderNodes:
        
        jobIds = []
        
        curRenderNode = findRenderNode( node )
            
        currentOutputName = outputFile
        if currentOutputName == "":
            currentOutputName = getNodeOutputFileName( curRenderNode, projectFile )
        currentExtraOutputName = extraOutputFile
        if currentExtraOutputName == "":
            currentExtraOutputName = getNodeExtraOutputFileName( curRenderNode, projectFile )
            
        renderPasses = getRenderPasses( curRenderNode, ( not currentExtraOutputName == "" ) ) 
        separatePassDirs = getSeparatePassDir( curRenderNode )
        
        for jobNum in xrange( jobCount ):
            
            tempJobName = jobName
            if not node == "":
                tempJobName += " - " + node
                
            if regionRendering:
                if singleFrameJob:
                    tempJobName += " - Region Rendering"
                else:
                    tempJobName += " - Region " + str( jobNum )
                
            # Create job info file.
            jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "terragen_job_info.job" )
            writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "Plugin=Terragen" )
            
            WriteCommonJobFileProperites( writer, tempJobName, scriptDialog.GetValue( "DependencyBox" ) )

            if singleFrameJob:
                writer.WriteLine( "TileJob=True" )
                writer.WriteLine( "TileJobTilesInX=%s" % tilesInX )
                writer.WriteLine( "TileJobTilesInY=%s" % tilesInY )
                writer.WriteLine( "TileJobFrame=%s" % singleFrameJobFrame )
            else:
                writer.WriteLine( "Frames=%s" % frames )
                writer.WriteLine( "ChunkSize=%s" %  scriptDialog.GetValue( "ChunkSizeBox" ) )
            
            outputCount = 0
            if not currentOutputName == "":
                paddedFile = replacePrintFPadding( currentOutputName )
                
                if regionRendering and singleFrameJob:
                    regionCount = 0
                    extLessPath, ext = os.path.splitext( paddedFile )
                    for frame in xrange( regionJobCount ):
                        writer.WriteLine( "OutputFilename" + str(outputCount) + "Tile" + str( regionCount ) + "=" + extLessPath + "_tile" +str( regionCount ) + ext )
                        regionCount += 1
                else:
                    if regionRendering:
                        extLessPath, ext = os.path.splitext( paddedFile )
                        writer.WriteLine( "OutputFilename" + str(outputCount) + "=" + extLessPath + "_tile" +str( jobNum ) + ext )
                    else:
                        writer.WriteLine( "OutputFilename" + str(outputCount) + "=" + paddedFile )
                   
                outputCount += 1
            
            if not currentExtraOutputName == "":
                if len( renderPasses ) == 0:
                    writer.WriteLine( "OutputDirectory" + count + "=" + os.path.dirname( currentExtraOutputName ) )
                    outputCount += 1
                else:
                    for renderPass in renderPasses:
                        passFilename = replacePrintFPadding( currentExtraOutputName ).replace( "IMAGETYPE", renderPass )
                        if separatePassDirs:
                            passFilename = os.path.join( os.path.dirname(passFilename), renderPass, os.path.basename(passFilename) )

                        if regionRendering and singleFrameJob:
                            regionCount = 0
                            extLessPath, ext = os.path.splitext( passFilename )
                            for frame in xrange( regionJobCount ):
                                writer.WriteLine( "OutputFilename" + str(outputCount) + "Tile" + str( regionCount ) + "=" + extLessPath + "_tile" +str( regionCount ) + ext )
                                regionCount += 1
                        else:
                            if regionRendering:
                                extLessPath, ext = os.path.splitext( passFilename )
                                writer.WriteLine( "OutputFilename" + str(outputCount) + "=" + extLessPath + "_tile" +str( jobNum ) + ext )
                            else:
                                writer.WriteLine( "OutputFilename" + str(outputCount) + "=" + passFilename )
                        outputCount += 1
            
            # Integration
            extraKVPIndex = 0
            groupBatch = ( regionRendering and submitDependent ) or ( len( renderNodes ) > 1 )

            if integration_dialog.IntegrationProcessingRequested() and not regionRendering:
                extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
                groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

            if groupBatch:
                writer.WriteLine( "BatchName=%s\n" % ( jobName ) )
                
            writer.Close()
            
            # Create plugin info file.
            pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "terragen_plugin_info.job" )
            writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
            if not submitScene:
                writer.WriteLine( "ProjectFile=%s" % projectFile )
            writer.WriteLine( "RenderNode=%s" % node )
            
            if regionRendering:
                writer.WriteLine( "OutputFile=%s" % currentOutputName )
                writer.WriteLine( "ExtraOutputFile=%s" % currentExtraOutputName )
            else:
                writer.WriteLine( "OutputFile=%s" % outputFile )
                writer.WriteLine( "ExtraOutputFile=%s" % extraOutputFile )
                
            writer.WriteLine( "LocalRendering=%s" % scriptDialog.GetValue( "LocalRenderingBox" ) )
            writer.WriteLine( "Version=%s" % version )
            
            if regionRendering:
                writer.WriteLine( "RegionRendering=True" )
                
                if singleFrameJob:
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
                    
                    curY = int( jobNum / tilesInX )
                    curX =  jobNum % tilesInX
                    
                    xstart = float( curX ) / tilesInX
                    xend = ( curX + 1.0 ) / tilesInX
                    ystart = float( curY ) / tilesInY
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
            if submitScene:
                arguments.Add( projectFile )
            
            jobResult = ClientUtils.ExecuteCommandAndGetOutput( arguments )
            jobId = "";
            resultArray = jobResult.split("\n")
            for line in resultArray:
                if line.startswith("JobID="):
                    jobId = line.replace("JobID=","")
                    jobId = jobId.strip()
                    totalSuccesses += 1
                    break
            else:
                totalFails += 1
            
            jobIds.append(jobId)
            totalJobCount += 1
            if not ( regionRendering and ( submitDependent or not singleFrameJob ) ) and len( renderNodes ) == 1:
                scriptDialog.ShowMessageBox( jobResult, "Submission Results" )
            else:
                print("---------------------------------------------")
                print(jobResult)
        
        if regionRendering and submitDependent and ( currentOutputName != "" or currentExtraOutputName != "" ):
            tempRenderPassess = renderPasses
            if currentOutputName != "":
                tempRenderPassess.insert(0, "")
            
            if singleFrameJob:
                tempJobName = jobName
                if not node == "":
                    tempJobName += " - " + node
                
                tempJobName = "%s - Assembly"%(jobName)
                    
                # Create submission info file
                jigsawJobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "jigsaw_submit_info.job" )
                jigsawPluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "jigsaw_plugin_info.job" )        
                
                writer = StreamWriter( jigsawJobInfoFilename, False, Encoding.Unicode )
                writer.WriteLine( "Plugin=DraftTileAssembler" )
                WriteCommonJobFileProperites( writer, tempJobName, ( ",".join(jobIds) ) )
                
                writer.WriteLine( "Frames=0-%s" % ( len(tempRenderPassess) -1 ) )
                writer.WriteLine( "ChunkSize=1" )
                
                frameNum = None
                if singleFrameJob:
                    frameNum = singleFrameJobFrame
                    
                outputCount = 0
                if not currentOutputName == "":
                    paddedFile = replacePrintFPadding( currentOutputName, frameNum = frameNum )
                    
                    writer.WriteLine( "OutputFilename" + str(outputCount) + "=" + paddedFile )
                    outputCount += 1
                
                if not currentExtraOutputName == "":
                    for renderPass in renderPasses:
                        passFilename = replacePrintFPadding( currentExtraOutputName, frameNum = frameNum ).replace( "IMAGETYPE", renderPass )
                        if separatePassDirs:
                            passFilename = os.path.join( os.path.dirname(passFilename), renderPass, os.path.basename(passFilename) )

                        writer.WriteLine( "OutputFilename" + str(outputCount) + "=" + passFilename )
                        outputCount += 1
                
                writer.WriteLine( "BatchName=%s" % ( jobName ) ) 

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
                
                for renderPass in tempRenderPassess: 
                    passName = currentExtraOutputName
                    if renderPass == "":
                        passName = currentOutputName
                        
                    passFilename = replacePrintFPadding( passName, frameNum = frameNum ).replace( "IMAGETYPE", renderPass )
                    if separatePassDirs:
                        passFilename = os.path.join( os.path.dirname(passFilename), renderPass, os.path.basename(passFilename) )
                    
                    outputName = passFilename
                    extLessPath, ext = os.path.splitext( passFilename )
                    tileName = extLessPath + "_tile?" + ext
                    
                    date = time.strftime("%Y_%m_%d_%H_%M_%S")
                    
                    outputFileNameOnly = os.path.basename(outputName)
                    configFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), os.path.splitext(outputFileNameOnly)[0]+"_"+renderPass+"_config_"+date+".txt" )
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
                resultArray = jobResult.split("\n")
                for line in resultArray:
                    if line.startswith("JobID="):
                        totalSuccesses += 1
                        break
                else:
                    totalFails += 1
                totalJobCount += 1
                
                print("---------------------------------------------")
                print(jobResult)
                
            else:
                for renderPass in tempRenderPassess:
                    tempJobName = jobName
                    if not node == "":
                        tempJobName += " - " + node
                    
                    if renderPass == "":
                        tempJobName += " - Main Output"
                    else:
                        tempJobName += " - " + renderPass
                    
                    tempJobName += " - Assembly"
                        
                    # Create submission info file
                    jigsawJobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "jigsaw_submit_info.job" )
                    jigsawPluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "jigsaw_plugin_info.job" )        
                    
                    writer = StreamWriter( jigsawJobInfoFilename, False, Encoding.Unicode )
                    writer.WriteLine( "Plugin=DraftTileAssembler" )
                    
                    WriteCommonJobFileProperites( writer, tempJobName, ( ",".join(jobIds) ) )
                                        
                    writer.WriteLine( "Frames=%s" % frames )
                   
                    writer.WriteLine( "ChunkSize=1" )
                    
                    if renderPass == "":
                        paddedFile = replacePrintFPadding( currentOutputName )
                        writer.WriteLine( "OutputFilename0=" + paddedFile )
                    else:
                        passFilename = replacePrintFPadding( currentExtraOutputName ).replace( "IMAGETYPE", renderPass )
                        if separatePassDirs:
                            passFilename = os.path.join( os.path.dirname(passFilename), renderPass, os.path.basename(passFilename) )

                        writer.WriteLine( "OutputFilename0=" + passFilename )
                    
                    writer.WriteLine( "BatchName=%s" % ( jobName ) ) 

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
                    
                    for frameNum in FrameUtils.Parse( frames ): 
                        passName = currentExtraOutputName
                        if renderPass == "":
                            passName = currentOutputName
                            
                        passFilename = replacePrintFPadding( passName, frameNum = frameNum ).replace( "IMAGETYPE", renderPass )
                        if separatePassDirs:
                            passFilename = os.path.join( os.path.dirname(passFilename), renderPass, os.path.basename(passFilename) )
                        
                        outputName = passFilename
                        extLessPath, ext = os.path.splitext( passFilename )
                        tileName = extLessPath + "_tile?"+ ext
                        
                        date = time.strftime("%Y_%m_%d_%H_%M_%S")
                        
                        outputFileNameOnly = os.path.basename(outputName)
                        configFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), os.path.splitext(outputFileNameOnly)[0]+"_"+renderPass+"_config_"+date+".txt" )
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
                    resultArray = jobResult.split("\n")
                    for line in resultArray:
                        if line.startswith("JobID="):
                            totalSuccesses += 1
                            break
                    else:
                        totalFails += 1
                        
                    totalJobCount += 1
                    print("----------")
                    print(jobResult)
                            
    if totalJobCount == 1:
        scriptDialog.ShowMessageBox( jobResult, "Submission Results" )
    else:
        scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d\n\nCheck the console for additional information." % (totalSuccesses, totalFails), "Submission Results" )
        