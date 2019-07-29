from __future__ import print_function

import imp
import io
import os
import socket
import subprocess
import time
import traceback

from Deadline.Scripting import ClientUtils, FrameUtils, PathUtils, RepositoryUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

from System.IO import StreamWriter
from System.Text import Encoding

# For Integration UI
imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
renderers = ["Brazil r/s 2.0 for Rhino", "Flamingo Raytrace", "Flamingo Photometric", "Maxwell for Rhino", "Penguin Render", "Rhino Render", "TreeFrog Render", "V-Ray for Rhino"]
assembleOverOptions = ["Blank Image", "Previous Output", "Selected Image"]
ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = True
appSubmission = False

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global appSubmission
    global scriptDialog
    global settings
    global renderers
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Rhino Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Rhino' ) )
    scriptDialog.rhinoDimensions = []
    scriptDialog.allViews = None

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
    scriptDialog.AddSelectionControlToGrid( "CloseOnSubmissionBox", "CheckBoxControl", False, "Close on Submission", 4, 2, "If enabled, the submitter will be closed after the job is submitted." )

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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Rhino Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Rhino File", 1, 0, "The scene file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Rhino 3D Models (*.3dm);;Rhino Work Session (*.rws);;All Files (*)", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "OutputLabel","LabelControl","Output File", 2, 0, "The filename of the image(s) to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid("OutputBox","FileSaverControl","","Windows Bitmap (*.bmp);;Targa (*.tga);;JPEG (*.jpg *.jpeg);;PCX (*.pcx);;PNG (*.png);;TIFF (*.tif *.tiff);;All files (*)", 2, 1, colSpan=3)

    scriptDialog.AddControlToGrid( "RendererLabel", "LabelControl", "Renderer", 3, 0, "The Rhino renderer to use.", False )
    rendererBox = scriptDialog.AddComboControlToGrid( "RendererBox", "ComboControl", "Rhino Render", renderers, 3, 1 )
    rendererBox.ValueModified.connect( RendererBoxChanged )

    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Rhino Scene File", 3, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering." )

    scriptDialog.AddControlToGrid( "ViewLabel", "LabelControl", "View", 4, 0, "Select the view to render. If it doesn't exist, the current view in the scene will be rendered.", False )
    if len(args) > 8:
        scriptDialog.AddComboControlToGrid( "ViewBox", "ComboControl", "", "", 4, 1 )
    else:
        scriptDialog.AddControlToGrid( "ViewBox", "TextControl", "", 4, 1 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 5, 0, "The Rhino Version to use.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "6", ("4", "5", "6"), 5, 1 )
    versionBox.ValueModified.connect( versionBoxChanged )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
        
    scriptDialog.AddTabPage("Animation / Tile Rendering")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator10", "SeparatorControl", "Bongo Animation Rendering", 0, 0, colSpan=4 )
    
    bongoBox = scriptDialog.AddSelectionControlToGrid( "BongoBox", "CheckBoxControl", False, "Render Bongo Animation", 1, 0, "If your Rhino file uses the Bongo animation plugin, you can enable a Bongo animation job.", colSpan=2 )
    bongoBox.ValueModified.connect(BongoBoxChanged)
    
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 2, 0, "The list of frames to render (if rendering a Bongo animation).", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 2, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 0, "This is the number of frames that will be rendered at a time for each job task (if rendering a Bongo animation).", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 3, 1 )
    
    scriptDialog.AddControlToGrid( "BongoVersionLabel", "LabelControl", "Bongo Version", 4, 0, "The Bongo Version to use.", False )
    scriptDialog.AddComboControlToGrid( "BongoVersionBox", "ComboControl", "2", ("1", "2"), 4, 1 )
    
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator9", "SeparatorControl", "Tile Rendering", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "RegionWarningLabel", "LabelControl", "Tile Rendering is only available when submitting from within Rhino and\nis not supported in Rhino 6 or when using V-Ray as the rendering engine.", 1, 0, "To enable Tile Rendering, you must run the submitter from within Rhino.", colSpan=4 )
    
    regionRenderingBox = scriptDialog.AddSelectionControlToGrid( "EnableRegionRenderingBox", "CheckBoxControl", False, "Enable Tile Rendering", 2, 0, "If this option is enabled, then the image will be divided into multiple tasks and assembled afterwards.", colSpan=2 )
    regionRenderingBox.ValueModified.connect(RegionRenderingBoxChanged)
    scriptDialog.SetEnabled( "EnableRegionRenderingBox", False )
    
    useJigsawBox = scriptDialog.AddSelectionControlToGrid( "UseJigsawBox", "CheckBoxControl", False, "Use Jigsaw", 3, 0, "If this option is enabled, the regions will be created using Jigsaw. Otherwise they will be created using tiles." )
    useJigsawBox.ValueModified.connect(UseJigsawChanged)
    jigsawButton = scriptDialog.AddControlToGrid( "JigsawButton", "ButtonControl", "Open Jigsaw", 3, 1 )
    jigsawButton.ValueModified.connect(JigsawButtonPressed)
    
    scriptDialog.AddControlToGrid( "TilesXLabel", "LabelControl", "Tiles in X", 4, 0, "The number of tiles to divide the region into.", False )
    xControl = scriptDialog.AddRangeControlToGrid( "TilesXControl", "RangeControl", 1, 1, 16, 0, 1, 4, 1 )
    
    scriptDialog.AddControlToGrid( "TilesYLabel", "LabelControl", "Tiles in Y", 5, 0, "The number of tiles to divide the region into.", False )
    yControl = scriptDialog.AddRangeControlToGrid( "TilesYControl", "RangeControl", 1, 1, 16, 0, 1, 5, 1 )
    
    submitDependentBox = scriptDialog.AddSelectionControlToGrid( "SubmitDependentAssemblyBox", "CheckBoxControl", True, "Submit Dependent Assembly Job", 6, 0, "If this option is enabled then an assembly job will be submitted.", colSpan=2 )
    submitDependentBox.ValueModified.connect(SubmitDependentBoxChanged)
    
    scriptDialog.AddControlToGrid( "AssembleOverLabel", "LabelControl", "Assemble Over", 7, 0, "The initial image you wish to assemble over.", False )
    assembleOverBox = scriptDialog.AddComboControlToGrid( "AssembleOverBox", "ComboControl", "Blank Image", assembleOverOptions, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "MissingBackgroundBox", "CheckBoxControl", False, "Error on Missing Background", 7, 2, "If this option is enabled, the render will fail if the background image specified does not exist." )
    
    scriptDialog.AddControlToGrid( "AssembleOverFileLabel", "LabelControl", "Image File", 8, 0, "The background image file to be used for assembly over.", False )
    assembleOverBox.ValueModified.connect(SubmitDependentBoxChanged)
    scriptDialog.AddSelectionControlToGrid( "AssembleOverFileBox", "FileBrowserControl", "", "All Files (*)", 8, 1, colSpan=3 )
    
    scriptDialog.AddSelectionControlToGrid( "CleanupTilesBox", "CheckBoxControl", False, "Cleanup Tiles After Assembly", 9, 1, "If this option is enabled, the tiles will be deleted after the assembly job is completed." )
    scriptDialog.AddSelectionControlToGrid( "ErrorOnMissingBox", "CheckBoxControl", True, "Error on Missing Tiles", 9, 2, "If this option is enabled, the assembly job will fail if it cannot find any of the tiles." )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "RhinoMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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

    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","BongoBox","BongoVersionBox","SubmitSceneBox","VersionBox","CloseOnSubmissionBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    if len( args ) > 0:
        appSubmission = True
        
        scriptDialog.SetValue( "SceneBox", args[0] )
        scriptDialog.SetValue( "NameBox", os.path.basename( args[0] ) )
        
        # Check if the renderer was specified.
        if len( args ) > 1:
            renderer = args[1]
            
            # If the renderer is not in the current renderers list, add it.
            if renderer not in renderers:
                renderers.append( renderer )
                scriptDialog.SetItems( "RendererBox", renderers )

            # Now set the renderer.
            scriptDialog.SetValue( "RendererBox", renderer )

        def toFloatList( arg ):
            """
            Casts a float represented by a string into a list of floats
            :param arg: a string representing floats. ie. "805.00,465.00"
            :return: a list of floats
            """
            return [ float( val ) for val in arg.split( ',' ) ]

        def toIntList( arg ):
            """
            Casts a float represented by a string into a list of integers
            :param arg: a string representing floats. ie. "805.00,465.00"
            :return: a list of integers
            """
            return [ int( val ) for val in toFloatList( arg ) ]

        # Support for Region Rendering
        if len( args ) > 5:
            scriptDialog.SetEnabled( "EnableRegionRenderingBox", True )

            scriptDialog.rhinoLowerLeftCorner = toFloatList( args[2] )
            scriptDialog.rhinoUpperLeftCorner = toFloatList( args[3] )
            scriptDialog.rhinoLowerRightCorner = toFloatList( args[4] )
            scriptDialog.rhinoDimensions = toIntList( args[5] )

            xControl.Maximum = scriptDialog.rhinoDimensions[0]/15
            yControl.Maximum = scriptDialog.rhinoDimensions[1]/15
            scriptDialog.rhinoJigsawImage = None

        # Support for jigsaw images
        if len( args ) > 7:
            scriptDialog.rhinoJigsawImage = args[6]
            scriptDialog.rhinoJigsawImageDimensions = toIntList( args[7] )

        # Support for populating views
        if len( args ) > 8 :
            scriptDialog.allViews = args[8].split(';')
            scriptDialog.SetItems( "ViewBox", scriptDialog.allViews )

        # Support for passing in Rhino major version, was added in Rhino 6 so if we don't
        # see a version and it's an in-app submission, assume it's Rhino 5
        scriptDialog.SetValue( "VersionBox", "5" )
        if len( args ) > 9:
            scriptDialog.SetValue( "VersionBox", getRhinoMajorVersion( args[9] ) )

    BongoBoxChanged( None )
    RegionRenderingBoxChanged( None )
    
    scriptDialog.ShowDialog( appSubmission )
    
def GetSettingsFilename():
    return os.path.join( ClientUtils.GetUsersSettingsDirectory(), "RhinoSettings.ini" )

def getRhinoMajorVersion( versionStr ):
    """
    Determines Rhino's major version from it's version string. Rhino 4 does NOT use this, since we only started
    passing in the Rhino Version in the toolbar installed with Rhino 5 and later. Example version strings:
    Rhino 5: '20150830'
    Rhino 6: '6,8,18240,20051'
    :param versionStr: the version string passed by the client submitter script
    :return: The Rhino major version as a string
    """
    if "," in versionStr:
        return versionStr.strip().split( ',' )[ 0 ]
    else:
        return "5"

def recvData( theSocket ):
    totalData=[]
    data=''
    while True:
        data=theSocket.recv(8192)
        if not data:
            return
        if "\n" in data:
            totalData.append(data[:data.find("\n")])
            break
        totalData.append(data)
    return ''.join(totalData)

def BongoBoxChanged( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "BongoBox" )
    scriptDialog.SetEnabled( "FramesLabel", enabled )
    scriptDialog.SetEnabled( "FramesBox", enabled )
    scriptDialog.SetEnabled( "ChunkSizeLabel", enabled )
    scriptDialog.SetEnabled( "ChunkSizeBox", enabled )
    scriptDialog.SetEnabled( "BongoVersionLabel", enabled )
    scriptDialog.SetEnabled( "BongoVersionBox", enabled )

def RendererBoxChanged( *args ):
    """
    Fires when the chosen Renderer changes
    """
    enableRegionRendering()

def versionBoxChanged( *args ):
    """
    Fires when the chosen Version changes
    """
    enableRegionRendering()

def enableRegionRendering():
    """
    All the logic used to determine if we should enable the region rendering feature in Rhino
    """
    global appSubmission, scriptDialog

    isVRay = scriptDialog.GetValue( "RendererBox" ) == "V-Ray for Rhino"
    isRhinoVersionNotSupported = int( scriptDialog.GetValue( "VersionBox" ) ) >= 6
    if not appSubmission or isVRay or isRhinoVersionNotSupported:
        scriptDialog.SetEnabled( "EnableRegionRenderingBox", False )
        scriptDialog.SetValue( "EnableRegionRenderingBox", False )
    else:
        scriptDialog.SetEnabled( "EnableRegionRenderingBox", True )

def RegionRenderingBoxChanged( *args ):
    global scriptDialog

    enabled = scriptDialog.GetEnabled( "EnableRegionRenderingBox" ) and scriptDialog.GetValue( "EnableRegionRenderingBox" )
    scriptDialog.SetEnabled( "SubmitDependentAssemblyBox", enabled )
    try:
        if scriptDialog.rhinoJigsawImage is None:
            scriptDialog.SetEnabled( "UseJigsawBox", False )
        else:
            scriptDialog.SetEnabled( "UseJigsawBox", enabled )
    except:
        scriptDialog.SetEnabled( "UseJigsawBox", False )
    SubmitDependentBoxChanged(None)
    UseJigsawChanged(None)

def UseJigsawChanged( *args ):
    global scriptDialog

    jigsawEnabled = scriptDialog.GetValue( "EnableRegionRenderingBox" ) and scriptDialog.GetValue( "UseJigsawBox" )
    tilesEnabled = scriptDialog.GetValue( "EnableRegionRenderingBox" ) and not scriptDialog.GetValue( "UseJigsawBox" )
    scriptDialog.SetEnabled( "TilesXLabel", tilesEnabled )
    scriptDialog.SetEnabled( "TilesXControl", tilesEnabled )
    scriptDialog.SetEnabled( "TilesYLabel", tilesEnabled )
    scriptDialog.SetEnabled( "TilesYControl", tilesEnabled )
    scriptDialog.SetEnabled( "JigsawButton", jigsawEnabled )
    
def SubmitDependentBoxChanged( *args ):
    global scriptDialog

    enabled = scriptDialog.GetValue( "EnableRegionRenderingBox" ) and scriptDialog.GetValue( "SubmitDependentAssemblyBox" )
    scriptDialog.SetEnabled( "CleanupTilesBox", enabled )
    scriptDialog.SetEnabled( "ErrorOnMissingBox", enabled )
    scriptDialog.SetEnabled( "AssembleOverLabel", enabled )
    scriptDialog.SetEnabled( "AssembleOverBox", enabled )
    AssembleOverBoxChanged( None )
    
def AssembleOverBoxChanged( *args ):
    global scriptDialog

    enabled = scriptDialog.GetValue( "EnableRegionRenderingBox" ) and scriptDialog.GetValue( "SubmitDependentAssemblyBox" ) and not scriptDialog.GetValue("AssembleOverBox") == "Blank Image"
    scriptDialog.SetEnabled( "MissingBackgroundBox", enabled )
    enabled = scriptDialog.GetValue( "EnableRegionRenderingBox" ) and scriptDialog.GetValue( "SubmitDependentAssemblyBox" ) and scriptDialog.GetValue("AssembleOverBox") == "Selected Image"
    scriptDialog.SetEnabled( "AssembleOverFileLabel", enabled )
    scriptDialog.SetEnabled( "AssembleOverFileBox", enabled )

def JigsawButtonPressed( *args ):
    global scriptDialog

    try:
        scriptDialog.deadlineSocket.sendall("TEST\n")
        scriptDialog.ShowMessageBox( "Jigsaw window is already open", "Jigsaw Window" )
        return
    except:
        pass
    
    try:
        HostOut = 'localhost'                 # Symbolic name meaning all available interfaces
        PORTout = get_open_port()              # Arbitrary non-privileged port
        scriptDialog.deadlineSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        scriptPath = RepositoryUtils.GetRepositoryFilePath(os.path.join("submission", "Jigsaw", "Jigsaw.py"), True).rstrip()

        multiplier = float(scriptDialog.rhinoDimensions[0])/float(scriptDialog.rhinoJigsawImageDimensions[0])
        minWidth = int((15/multiplier)+0.5)

        # This is needed for the asynchronous behaviour of jigsaw
        deadlineCommand = os.path.join( os.environ.get('DEADLINE_PATH', ''), 'deadlinecommandbg' )
        subprocess.Popen([deadlineCommand,"-executescript",scriptPath,str(PORTout),scriptDialog.rhinoJigsawImage, "False",str(minWidth),str(minWidth)])#,str(PORTin)]
        count = 0
        while True:
            try:
                time.sleep(1)
                scriptDialog.deadlineSocket.connect((HostOut, PORTout))
                break
            except:
                count+=1
                if count>=10:
                    scriptDialog.ShowMessageBox("Failed to connect to Jigsaw window","Deadline Jigsaw")
                    #infodialog("Deadline Jigsaw","Failed to connect to Jigsaw window")
                    break
    except:
        scriptDialog.ShowMessageBox(traceback.format_exc(),"Error")
        
def get_open_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    port = s.getsockname()[1]
    s.close()
    return port

def WriteIntegrationSettings( writer, groupBatch ):
    # Integration
    extraKVPIndex = 0
        
    if integration_dialog.IntegrationProcessingRequested():
        extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
        groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

    return groupBatch

def getJobIDFromSubmissionResults( results ):
    """
    Obtain the jobID associated with the recently submitted job.
    :param results: a string containing the results of a job submission
    :return: a string containing the jobID
    """
    jobID = ""
    for line in results.splitlines():
        if line.startswith( "JobID=" ):
            jobID = line.replace( "JobID=", "" )
            break

    return jobID

def SubmitButtonPressed( *args ):
    global scriptDialog
    global renderers
    global integration_dialog
    
    try:
        errors = ""
        warnings = ""
        jigsawRegions = []
        if scriptDialog.GetValue( "EnableRegionRenderingBox" ) and scriptDialog.GetValue( "UseJigsawBox" ):
            try:
                scriptDialog.deadlineSocket.sendall("getrenderregions\n")
                regionString = recvData(scriptDialog.deadlineSocket)
                regionData = regionString.split("=")
                if regionData[0] == "renderregion" and len(regionData) >1:
                    regionData = regionData[1]
                    regionData = regionData.split(";")
                    for region in regionData:
                        coordinates = region.split(",")
                        if len(coordinates) == 4:
                            jigsawRegions.append(float(coordinates[0]))
                            jigsawRegions.append(float(coordinates[0])+float(coordinates[2]))
                            jigsawRegions.append(float(coordinates[1]))
                            jigsawRegions.append(float(coordinates[1])+float(coordinates[3]))
            except:
                scriptDialog.ShowMessageBox( "In order to submit a Jigsaw region job the Jigsaw window must be open.", "Deadline Jigsaw" )
                scriptDialog.deadlineSocket.close()
                return
        
        # Check Rhino file.
        sceneFile = scriptDialog.GetValue( "SceneBox" )
        submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
        if not os.path.isfile( sceneFile ):
            errors += "Rhino file %s does not exist.\n\n" % sceneFile
        elif not submitScene and PathUtils.IsPathLocal( sceneFile ):
            warnings += "The Rhino file %s is local and is not being submitted with the job.\n\n" % sceneFile
        
        # Check output file.
        outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
        if not outputFile:
            errors += "Please specify an output file.\n\n"
        elif outputFile.endswith( ("/", "\\") ):
            errors += "Output File path ends in a slash, please enter a valid filename.\n\n"
        elif not os.path.isdir( os.path.dirname( outputFile ) ):
            errors += "Directory for output file %s does not exist.\n\n" % outputFile
        elif PathUtils.IsPathLocal( outputFile ):
            warnings += "Output file %s is local.\n\n" % outputFile

        # Check if Integration options are valid.
        if not integration_dialog.CheckIntegrationSanity( outputFile ):
            return
        
        # Check if a valid frame range has been specified.
        bongo = scriptDialog.GetValue( "BongoBox" )
        frames = scriptDialog.GetValue( "FramesBox" )
        if not bongo:
            frames = "0"
        elif not FrameUtils.FrameRangeValid( frames ):
            errors += "Frame range %s is not valid.\n\n" % frames
        
        jobName = scriptDialog.GetValue( "NameBox" )
        groupBatch = False
        
        if scriptDialog.GetValue( "EnableRegionRenderingBox" ):
            xCount = int(scriptDialog.GetValue( "TilesXControl" ))
            yCount = int(scriptDialog.GetValue( "TilesYControl" ))
            tileCount = xCount * yCount
            if scriptDialog.GetValue( "UseJigsawBox" ):
                tileCount = len(jigsawRegions)/4
            
            taskLimit = RepositoryUtils.GetJobTaskLimit()
            if tileCount > taskLimit:
                errors += "Unable to submit job with %i tasks. Task Count exceeded Job Task Limit of %i.\n" % ( tileCount, taskLimit)

        if errors:
            scriptDialog.ShowMessageBox( errors, "Error" )
            return
        
        if warnings:
            warnings = "Warnings:\n\n%s\n\nAre you sure you want to continue?\n" % warnings
            result = scriptDialog.ShowMessageBox( warnings, "Warning", ("Yes","No") )
            if result == "No":
                return

        # Create job info file.
        jobInfoFilename = os.path.join( ClientUtils.GetDeadlineTempPath(), "rhino_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Rhino" )
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
        if scriptDialog.GetValue( "IsBlacklistBox" ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )

        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )

        if scriptDialog.GetValue( "SubmitSuspendedBox" ):
            writer.WriteLine( "InitialStatus=Suspended" )

        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )

        if scriptDialog.GetValue( "EnableRegionRenderingBox" ):
            baseName = os.path.basename(outputFile)
            dirName = os.path.dirname(outputFile)

            if not scriptDialog.GetValue( "UseJigsawBox" ):
                xCount = int(scriptDialog.GetValue( "TilesXControl" ))
                yCount = int(scriptDialog.GetValue( "TilesYControl" ))

                count = 0
                if len(scriptDialog.rhinoDimensions) > 1:
                    for x in range(xCount):
                        for y in range(yCount-1,-1,-1):
                            regionOutputFileName = dirName+os.sep+"_region_"+str(count)+"_" + baseName
                            writer.WriteLine( "OutputFilename0Tile%s=%s"%(count,regionOutputFileName) )
                            count+=1

            else:
                tileCount = len(jigsawRegions)/4
                for region in range(tileCount):
                    regionOutputFileName = dirName+os.sep+"_region_"+str(region)+"_" + baseName
                    writer.WriteLine( "OutputFilename0Tile%s=%s"%(region,regionOutputFileName) )
        else:
            if bongo:
                directory = os.path.dirname( outputFile )
                filename, extension = os.path.splitext( os.path.basename( outputFile ) )
                writer.WriteLine( "OutputFilename0=%s" % os.path.join( directory, filename + "####" + extension ) )
            else:
                writer.WriteLine( "OutputFilename0=%s" % outputFile )

        if scriptDialog.GetValue( "EnableRegionRenderingBox" ):
            writer.WriteLine( "TileJob=True" )

            if not scriptDialog.GetValue( "UseJigsawBox" ):
                writer.WriteLine("TileJobTileCount="+str(int(scriptDialog.GetValue( "TilesXControl" ))*int(scriptDialog.GetValue( "TilesYControl" ))))
            else:
                writer.WriteLine( "TileJobTileCount="+str(len(jigsawRegions)/4))

        dependentAssembly = scriptDialog.GetValue( "SubmitDependentAssemblyBox" )
        regionRendering = scriptDialog.GetValue( "EnableRegionRenderingBox" )

        if regionRendering and dependentAssembly:
            groupBatch = True

        if not( regionRendering and dependentAssembly ):
            groupBatch = WriteIntegrationSettings( writer, groupBatch )

        if groupBatch:
            writer.WriteLine( "BatchName=%s\n" % jobName )

        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = os.path.join( ClientUtils.GetDeadlineTempPath(), "rhino_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        if not submitScene:
            writer.WriteLine( "SceneFile=%s" % sceneFile )
        writer.WriteLine( "OutputFile=%s" % outputFile )
        writer.WriteLine( "Renderer=%s" % scriptDialog.GetValue( "RendererBox" ) )
        writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )

        if scriptDialog.allViews is not None:
            viewToRender = scriptDialog.GetValue( "ViewBox" )
            writer.WriteLine( "View=%s" % viewToRender )

            for index, view in enumerate( scriptDialog.allViews ):
                writer.WriteLine( "View%d=%s" % (index, view) )
        else:
            writer.WriteLine( "View=%s" % scriptDialog.GetValue( "ViewBox" ) )

        writer.WriteLine( "RenderBongo=%d" % bongo )
        
        if bongo:
            writer.WriteLine( "BongoVersion=%s" % scriptDialog.GetValue( "BongoVersionBox" ) )

        for index, renderer in enumerate(renderers):
            writer.WriteLine( "Renderer%d=%s" % (index,renderer) )
        
        if scriptDialog.GetValue( "EnableRegionRenderingBox" ):
            writer.WriteLine("RenderDimensionX="+str(scriptDialog.rhinoDimensions[0]))
            writer.WriteLine("RenderDimensionY="+str(scriptDialog.rhinoDimensions[1]))
            if not scriptDialog.GetValue( "UseJigsawBox" ):
                xCount = int(scriptDialog.GetValue( "TilesXControl" ))
                yCount = int(scriptDialog.GetValue( "TilesYControl" ))
                
                lowerLeft = scriptDialog.rhinoLowerLeftCorner
                
                perX = (
                    (scriptDialog.rhinoLowerRightCorner[0]-lowerLeft[0])/xCount,
                    (scriptDialog.rhinoLowerRightCorner[1]-lowerLeft[1])/xCount,
                    (scriptDialog.rhinoLowerRightCorner[2]-lowerLeft[2])/xCount,
                )
                perY = (
                    (scriptDialog.rhinoUpperLeftCorner[0]-lowerLeft[0])/yCount,
                    (scriptDialog.rhinoUpperLeftCorner[1]-lowerLeft[1])/yCount,
                    (scriptDialog.rhinoUpperLeftCorner[2]-lowerLeft[2])/yCount,
                )
                
                count = 0
                for x in range(xCount):
                    for y in range(yCount):
                        writer.WriteLine("RegionStart"+str(count)+"X="+str(lowerLeft[0]+(perX[0]*x)+(perY[0]*y)))
                        writer.WriteLine("RegionStart"+str(count)+"Y="+str(lowerLeft[1]+(perX[1]*x)+(perY[1]*y)))
                        writer.WriteLine("RegionStart"+str(count)+"Z="+str(lowerLeft[2]+(perX[2]*x)+(perY[2]*y)))
                        writer.WriteLine("RegionEnd"+str(count)+"X="+str(lowerLeft[0]+(perX[0]*(x+1))+(perY[0]*(y+1))))
                        writer.WriteLine("RegionEnd"+str(count)+"Y="+str(lowerLeft[1]+(perX[1]*(x+1))+(perY[1]*(y+1))))
                        writer.WriteLine("RegionEnd"+str(count)+"Z="+str(lowerLeft[2]+(perX[2]*(x+1))+(perY[2]*(y+1))))
                        count+=1
            else:
                lowerLeft = scriptDialog.rhinoLowerLeftCorner
                xLen = (
                    scriptDialog.rhinoLowerRightCorner[0]-lowerLeft[0],
                    scriptDialog.rhinoLowerRightCorner[1]-lowerLeft[1],
                    scriptDialog.rhinoLowerRightCorner[2]-lowerLeft[2],
                )
                
                yLen = (
                    scriptDialog.rhinoUpperLeftCorner[0]-lowerLeft[0],
                    scriptDialog.rhinoUpperLeftCorner[1]-lowerLeft[1],
                    scriptDialog.rhinoUpperLeftCorner[2]-lowerLeft[2],
                )
                
                for region in range(len(jigsawRegions)/4):
                    startXPercent = jigsawRegions[4*region]/float(scriptDialog.rhinoJigsawImageDimensions[0])
                    endXPercent = jigsawRegions[4*region+1]/float(scriptDialog.rhinoJigsawImageDimensions[0])
                    startyPercent = jigsawRegions[4*region+2]/float(scriptDialog.rhinoJigsawImageDimensions[1])
                    endYPercent = jigsawRegions[4*region+3]/float(scriptDialog.rhinoJigsawImageDimensions[1])
                    
                    writer.WriteLine("RegionStart"+str(region)+"X="+str(lowerLeft[0]+(xLen[0]*startXPercent)+(yLen[0]*startyPercent)))
                    writer.WriteLine("RegionStart"+str(region)+"Y="+str(lowerLeft[1]+(xLen[1]*startXPercent)+(yLen[1]*startyPercent)))
                    writer.WriteLine("RegionStart"+str(region)+"Z="+str(lowerLeft[2]+(xLen[2]*startXPercent)+(yLen[2]*startyPercent)))
                    writer.WriteLine("RegionEnd"+str(region)+"X="+str(lowerLeft[0]+(xLen[0]*endXPercent)+(yLen[0]*endYPercent)))
                    writer.WriteLine("RegionEnd"+str(region)+"Y="+str(lowerLeft[1]+(xLen[1]*endXPercent)+(yLen[1]*endYPercent)))
                    writer.WriteLine("RegionEnd"+str(region)+"Z="+str(lowerLeft[2]+(xLen[2]*endXPercent)+(yLen[2]*endYPercent)))
                
        writer.Close()
        
        # Setup the command line arguments.
        arguments = [ jobInfoFilename, pluginInfoFilename ]
        if submitScene:
            arguments.append( sceneFile )
        
        # Now submit the job.
        results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    except:
        scriptDialog.ShowMessageBox( traceback.format_exc(), "Submission Results" )
        return
    
    if not ( dependentAssembly and regionRendering ):
        scriptDialog.ShowMessageBox( results, "Submission Results" )
    else:
        try:
            jobId = getJobIDFromSubmissionResults( results )

            draftJobInfoFilename = os.path.join( ClientUtils.GetDeadlineTempPath(), "rhino_assembly_job_info.job" )
            writer = StreamWriter( draftJobInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "Plugin=DraftTileAssembler" )
            writer.WriteLine( "BatchName=%s\n" % jobName )
            writer.WriteLine( "Name=%s - Assembly Job" % jobName )
            writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
            writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
            writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
            writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
            writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
            writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
            writer.WriteLine( "OutputFilename0=%s" % outputFile )
            writer.WriteLine( "JobDependencies=%s" % jobId )
            writer.WriteLine( "Frames=0")
            writer.WriteLine( "ChunkSize=1" )
            writer.WriteLine( "MachineLimit=1" )
            if scriptDialog.GetValue( "IsBlacklistBox" ):
                writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            else:
                writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )

            WriteIntegrationSettings( writer, True )

            writer.Close()
            
            draftPluginInfoFilename = os.path.join( ClientUtils.GetDeadlineTempPath(), "rhino_draft_plugin_info.job" )
            writer = StreamWriter( draftPluginInfoFilename, False, Encoding.Unicode )
            if scriptDialog.GetValue("ErrorOnMissingBox"):
                writer.WriteLine( "ErrorOnMissing=True" )
            else:
                writer.WriteLine( "ErrorOnMissing=False" )
            if not scriptDialog.GetValue("AssembleOverBox") == "Blank Image":
                if scriptDialog.GetValue("MissingBackgroundBox"):
                    writer.WriteLine( "ErrorOnMissingBackground=True" )
                else:
                    writer.WriteLine( "ErrorOnMissingBackground=False" )
            if scriptDialog.GetValue("CleanupTilesBox"):
                writer.WriteLine( "CleanupTiles=True" )
            else:
                writer.WriteLine( "CleanupTiles=False" )
            writer.Close()
            
            dirname, basename = os.path.split(outputFile)
            
            date = time.strftime("%Y_%m_%d_%H_%M_%S")
            configFilename = os.path.join( dirname, "%s_config_%s.txt" % ( basename, date ) )
            writer = StreamWriter( configFilename, False )
            writer.WriteLine( "" )
            writer.WriteLine( "ImageFileName=" +outputFile )
            if len(scriptDialog.rhinoDimensions) > 1:
                writer.WriteLine( "ImageWidth=" +str(scriptDialog.rhinoDimensions[0]) )
                writer.WriteLine( "ImageHeight=" +str(scriptDialog.rhinoDimensions[1]) )
            
            if scriptDialog.GetValue( "RendererBox" ) == "Maxwell for Rhino":
                writer.WriteLine( "TilesCropped=False" )
            else:
                writer.WriteLine( "TilesCropped=True" )
            
            if scriptDialog.GetValue("AssembleOverBox") == "Previous Output":
                writer.WriteLine( "BackgroundSource=" +outputFile )
            elif scriptDialog.GetValue("AssembleOverBox") == "Selected Image":
                writer.WriteLine( "BackgroundSource=" +scriptDialog.GetValue("AssembleOverFileBox" ))
            
            if not scriptDialog.GetValue( "UseJigsawBox" ):
                xCount = int(scriptDialog.GetValue( "TilesXControl" ))
                yCount = int(scriptDialog.GetValue( "TilesYControl" ))
                
                tileCount = xCount * yCount
                writer.WriteLine( "TileCount=" +str(tileCount) )
                
                count = 0
                if len(scriptDialog.rhinoDimensions) > 1:
                    perX = scriptDialog.rhinoDimensions[0]/xCount
                    perY = scriptDialog.rhinoDimensions[1]/yCount
                    for x in range(xCount):
                        for y in range(yCount-1,-1,-1):
                            regionOutputFileName = os.path.join( dirname, "_region_%s_%s" % ( count, basename ) )
                            writer.WriteLine( "Tile%iFileName=%s"%(count,regionOutputFileName) )
                            writer.WriteLine( "Tile%iX=%s"%(count,perX*x) )
                            writer.WriteLine( "Tile%iY=%s"%(count,perY*y) )
                            writer.WriteLine( "Tile%iWidth=%s"%(count,int(perX)) )
                            writer.WriteLine( "Tile%iHeight=%s"%(count,int(perY)) )
                            count+=1
                
            else:
                writer.WriteLine( "TileCount=" +str(len(jigsawRegions)/4) )
                multiplier = float(scriptDialog.rhinoDimensions[0])/float(scriptDialog.rhinoJigsawImageDimensions[0])
                
                for region in range(len(jigsawRegions)/4):
                    regionOutputFileName = os.path.join( dirname, "_region_%s_%s" % ( region, basename ) )
                    
                    X = int(jigsawRegions[4*region]*multiplier+0.5)
                    Y = int(scriptDialog.rhinoDimensions[1]-jigsawRegions[4*region+3]*multiplier+0.5)
                    width = int( (jigsawRegions[region*4+1] - jigsawRegions[region*4] )*multiplier+0.5)
                    height = int( (jigsawRegions[region*4+3] - jigsawRegions[region*4+2] ) * multiplier + 0.5 )
                    writer.WriteLine( "Tile%iFileName=%s"%(region,regionOutputFileName) )
                    writer.WriteLine( "Tile%iX=%s"%(region,X) )
                    writer.WriteLine( "Tile%iY=%s"%(region,Y) )
                    
            writer.Close()
            arguments = [ draftJobInfoFilename, draftPluginInfoFilename, configFilename ]
            
            ClientUtils.ExecuteCommandAndGetOutput( arguments )
            scriptDialog.ShowMessageBox( "Done Submitting 2 Jobs.", "Submission Results" )
        except:
            scriptDialog.ShowMessageBox( traceback.format_exc(), "error Results" )
            return
    
    if scriptDialog.GetValue( "CloseOnSubmissionBox" ):
        scriptDialog.accept()
