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
workspace = None

ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = True

########################################################################
## A class for gathering information about the selected workspace.
########################################################################
class Workspace( object ):
    
    Filename = ""
    
    RenderInfoInputPathname = ""
    RenderInfoOutputPathname = ""
    
    Operators = None
    OperatorIds = None
    OperatorStartFrames = None
    OperatorEndFrames = None
    OperatorFrameRanges = None
    OperatorFilenames = None
    OperatorIsFilenameMovies = None
    OperatorFrameSizes = None
    OperatorCustomWidths = None
    OperatorCustomHeights = None
    OperatorLockAspects = None
    OperatorBitDepths = None
    OperatorQualities = None
    
    def __init__( self, workspaceFilename ):
        self.Filename = workspaceFilename
        
        self.OutputOperators = []
        self.OperatorIds = {}
        self.OperatorStartFrames = {}
        self.OperatorEndFrames = {}
        self.OperatorFrameRanges = {}
        self.OperatorFilenames = {}
        self.OperatorIsFilenameMovies = {}
        self.OperatorFrameSizes = {}
        self.OperatorCustomWidths = {}
        self.OperatorCustomHeights = {}
        self.OperatorLockAspects = {}
        self.OperatorBitDepths = {}
        self.OperatorQualities = {}
        
        operatorRe = Regex( r" *SetOperatorName (\"[^\"]*\"|[^\"]*)" )
        operatorIdRe = Regex( r" *SetCurrentOperator ([0-9]+)" )
        outputInfoRe = Regex( r" *OutputInfo\.Info (\"[^\"]*\"|[^\"]*) (\"[^\"]*\"|[^\"]*) on" )
        frameRangeRe = Regex( r" *OutputInfo\.Range ([0-9]+) ([0-9]+) ([0-9]+)" )
        filenameRe = Regex( r" *OutputInfo\.VideoFileName \"([^\"]*)\"" )
        frameSizeRe = Regex( r" *OutputInfo\.FrameSize ([0-9]+) ([0-9]+) ([0-9]+) ([a-zA-Z]*) ([0-9]+)" )
        qualityRe = Regex( r" *OutputInfo\.Quality ([0-9]+)" )
        inputPathnameRe = Regex( r" *RenderInfo\.InputPathname \"([^\"]*)\"" )
        outputPathnameRe = Regex( r" *RenderInfo\.OutputPathname \"([^\"]*)\"" )
        
        currentOperator = ""
        currentOperatorId = ""
        currentOutputOperator = ""
        
        reader = File.OpenText( workspaceFilename )
        line = reader.ReadLine()
        while line != None:
            
            if len( line ) > 0:
                
                if inputPathnameRe.IsMatch( line ):
                    inputPathname = inputPathnameRe.Match( line ).Groups[ 1 ].Value
                    self.RenderInfoInputPathname = inputPathname
                        
                if outputPathnameRe.IsMatch( line ):
                    outputPathname = outputPathnameRe.Match( line ).Groups[ 1 ].Value
                    self.RenderInfoOutputPathname = outputPathname
                
                if operatorIdRe.IsMatch( line ):
                    currentOperatorId = operatorIdRe.Match( line ).Groups[ 1 ].Value
                
                if operatorRe.IsMatch( line ):
                    currentOperator = operatorRe.Match( line ).Groups[ 1 ].Value.replace( "\"", "" )
                    currentOutputOperator = ""
                
                if len(currentOperator) > 0 and outputInfoRe.IsMatch( line ):
                    currentOutputOperator = currentOperator + "/" + outputInfoRe.Match( line ).Groups[ 1 ].Value.replace( "\"", "" )
                    self.OutputOperators.append( currentOutputOperator )
                    self.OperatorIds[ currentOutputOperator ] = currentOperatorId
                
                if len(currentOutputOperator) > 0:
                    
                    if frameRangeRe.IsMatch( line ):
                        startFrame = frameRangeRe.Match( line ).Groups[ 1 ].Value
                        endFrame = frameRangeRe.Match( line ).Groups[ 2 ].Value
                        byFrame = frameRangeRe.Match( line ).Groups[ 3 ].Value
                        
                        frameRange = startFrame + "-" + endFrame
                        if byFrame != "1":
                            frameRange += "x" + byFrame
                        
                        self.OperatorStartFrames[ currentOutputOperator ] = startFrame
                        self.OperatorEndFrames[ currentOutputOperator ] = endFrame
                        self.OperatorFrameRanges[ currentOutputOperator ] = frameRange
                    
                    elif filenameRe.IsMatch( line ):
                        filename = filenameRe.Match( line ).Groups[ 1 ].Value
                        self.OperatorFilenames[ currentOutputOperator ] = filename
                        
                        ext = Path.GetExtension( filename ).lower()
                        isMovie = (ext == ".vdr" or ext == ".wav" or ext == ".dvs" or ext == ".omf" or ext == ".omf" or ext == ".omfi" or ext == ".stm" or ext == ".tar" or ext == ".vpr" or ext == ".gif" or ext == ".img" or ext == ".flc" or ext == ".flm" or ext == ".mp3" or ext == ".mov" or ext == ".rm" or ext == ".avi" or ext == ".wmv")
                        self.OperatorIsFilenameMovies[ currentOutputOperator ] = isMovie
                        
                    elif frameSizeRe.IsMatch( line ):
                        frameSize = frameSizeRe.Match( line ).Groups[ 1 ].Value
                        if frameSize == "0":
                            frameSize = "normal"
                        elif frameSize == "1":
                            frameSize = "half"
                        elif frameSize == "2":
                            frameSize = "third"
                        elif frameSize == "3":
                            frameSize = "quarter"
                        elif frameSize == "4":
                            frameSize = "eighth"
                        elif frameSize == "5":
                            frameSize = "custom"
                        
                        customWidth = frameSizeRe.Match( line ).Groups[ 2 ].Value
                        customHeight = frameSizeRe.Match( line ).Groups[ 3 ].Value
                        
                        lockAspect = frameSizeRe.Match( line ).Groups[ 4 ].Value
                        if lockAspect == "on":
                            lockAspect = "true"
                        else:
                            lockAspect = "false"
                        
                        bitDepth = frameSizeRe.Match( line ).Groups[ 5 ].Value
                        if bitDepth == "32":
                            bitDepth = "float"
                        
                        self.OperatorFrameSizes[ currentOutputOperator ] = frameSize
                        self.OperatorCustomWidths[ currentOutputOperator ] = customWidth
                        self.OperatorCustomHeights[ currentOutputOperator ] = customHeight
                        self.OperatorLockAspects[ currentOutputOperator ] = lockAspect
                        self.OperatorBitDepths[ currentOutputOperator ] = bitDepth
                    
                    elif qualityRe.IsMatch( line ):
                        quality = qualityRe.Match( line ).Groups[ 1 ].Value
                        
                        # There is no 'preview' command line option, so just
                        # render 'medium' if 'preview' is selected for now.
                        if quality == "1":
                            quality = "best"
                        elif quality == "0" or quality == "2":
                            quality = "medium"
                        elif quality == "3":
                            quality = "draft"
                        
                        self.OperatorQualities[ currentOutputOperator ] = quality
            
            line = reader.ReadLine()
        
        reader.Close()
    
    def GetRenderInfoInputPathname( self ):
        return self.RenderInfoInputPathname
        
    def GetRenderInfoOutputPathname( self ):
        return self.RenderInfoOutputPathname
        
    def GetOutputOperators( self ):
        return tuple(self.OutputOperators)
    
    def GetId( self, operator ):
        return self.OperatorIds[ operator ]
    
    def GetStartFrame( self, operator ):
        return self.OperatorStartFrames[ operator ]
    
    def GetEndFrame( self, operator ):
        return self.OperatorEndFrames[ operator ]
    
    def GetFrameRange( self, operator ):
        return self.OperatorFrameRanges[ operator ]
    
    def GetOutputFilename( self, operator ):
        return self.OperatorFilenames[ operator ]
    
    def IsOutputMovie( self, operator ):
        return self.OperatorIsFilenameMovies[ operator ]
    
    def GetFrameSize( self, operator ):
        return self.OperatorFrameSizes[ operator ]
    
    def GetCustomWidth( self, operator ):
        return self.OperatorCustomWidths[ operator ]
    
    def GetCustomHeight( self, operator ):
        return self.OperatorCustomHeights[ operator ]
    
    def GetLockAspect( self, operator ):
        return self.OperatorLockAspects[ operator ]
    
    def GetBitDepth( self, operator ):
        return self.OperatorBitDepths[ operator ]
    
    def GetQuality( self, operator ):
        return self.OperatorQualities[ operator ]


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
    scriptDialog.SetTitle( "Submit Combustion Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Combustion' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2)

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

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "The whitelisted or blacklisted list of machines.", False )
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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Combustion Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Workspace File", 1, 0, "The workspace file to render.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Workspace Files (*.cws)", 1, 1, colSpan=2 )
    sceneBox.ValueModified.connect(WorkspaceFileChanged)

    scriptDialog.AddControlToGrid( "OutputOperatorLabel", "LabelControl", "Output Operator", 2, 0, "Select the output operator in the workspace file to render. The render will fail if the operator cannot be found.", False )
    scriptDialog.AddComboControlToGrid( "OutputOperatorBox", "ComboControl", "", (), 2, 1 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 3, 0, "The version of Combustion to render with.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "2008", ("4","2008"), 3, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Workspace File", 3, 2, "If this option is enabled, the workspace file will be submitted with the job, and then copied locally to the slave machine during rendering." )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 4, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "SkipExistingBox", "CheckBoxControl", False, "Skip Existing Frames", 4, 2, "Skip over existing frames during rendering." )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 5, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "SingleCpuBox", "CheckBoxControl", False, "Use A Single CPU to Render", 5, 2, "Limit rendering to one CPU." )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "CombustionMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid("HSpacer1", 0, 0 )

    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)

    scriptDialog.EndGrid()

    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","UseDefaultsBox","SkipExistingBox","InputBox", "OutputBox", "SingleCpuBox", "SubmitSceneBox","VersionBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    WorkspaceFileChanged( None )
        
    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "CombustionSettings.ini" )
  
def WorkspaceFileChanged(*args):
    global scriptDialog
    global workspace
    
    scriptDialog.SetItems( "OutputOperatorBox", () )
    scriptDialog.SetValue( "FramesBox", "" )
    
    workspaceFilename = scriptDialog.GetValue( "SceneBox" )
    if File.Exists( workspaceFilename ):
        workspace = Workspace( workspaceFilename )
        outputOperators = workspace.GetOutputOperators()
        if len( outputOperators ) > 0:
            scriptDialog.SetItems( "OutputOperatorBox", outputOperators )
            scriptDialog.SetValue( "OutputOperatorBox", outputOperators[0] )
            scriptDialog.SetValue( "FramesBox", workspace.GetFrameRange( outputOperators[0] ) )
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    global workspace
    global integration_dialog
    
    # Check combustion file.
    sceneFile = scriptDialog.GetValue( "SceneBox" ).strip()
    if( len( sceneFile ) == 0 ):
        scriptDialog.ShowMessageBox( "No Combustion workspace file specified.", "Error" )
        return
    elif( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "Combustion workspace file %s does not exist." % sceneFile, "Error" )
        return
    # If the submit scene box is checked check if they are local, if they are warn the user.
    elif( not bool( scriptDialog.GetValue("SubmitSceneBox") ) and PathUtils.IsPathLocal( sceneFile ) ):
        result = scriptDialog.ShowMessageBox( "The Combustion workspace file " + sceneFile + " is local, are you sure you want to continue?", "Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    # Check that an output operator has been selected.
    if len( scriptDialog.GetItems( "OutputOperatorBox" ) ) == 0:
        scriptDialog.ShowMessageBox( "No enabled output operators could be found in the Combustion workspace file specified.", "Error" )
        return
    outputOperator = scriptDialog.GetValue( "OutputOperatorBox" )
    if outputOperator == "":
        scriptDialog.ShowMessageBox( "Please select an output operator.", "Error" )
        return
    
    # Check that the output operator doesn't have more than 1 '/' in it, because Combustion's command line renderer doesn't like this.
    if outputOperator.count( "/" ) > 1:
        scriptDialog.ShowMessageBox( "Combustion's command line renderer only accepts output operators with a single '/'. Please rename this operator and submit again.", "Error" )
        return
    
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid." % frames, "Error" )
        return
    
    # Check if the selected output operator's output directory does exist and display a WARNING if it is local.
    outputFilename = workspace.GetOutputFilename( outputOperator )
    
    if outputFilename == "":
        scriptDialog.ShowMessageBox( "The output path for the selected output operator [" + outputOperator + "] is undefined in the workspace file.", "Error" )
        return
    else:
        # Scan all output operators to see if any are missing an output path. This can cause errors when rendering
        # even if output is missing for an unselected operator.
        outputWarning = ""
        outputOperators = workspace.GetOutputOperators()
        for currOperator in outputOperators:
            currFilename = workspace.GetOutputFilename( currOperator )
            if currFilename == "":
                outputWarning += "\n" + currOperator
        
        if outputWarning != "":
            outputWarning = "The following output operators have undefined output paths in the workspace file:\n" + outputWarning + "\n\nThis can cause the render to fail. Do you wish to continue?"
            result = scriptDialog.ShowMessageBox( outputWarning, "Warning", ("Yes","No") )
            if( result == "No" ):
                return
        
        outputDirectory = Path.GetDirectoryName( outputFilename )
        if( not Directory.Exists( outputDirectory ) ):
            scriptDialog.ShowMessageBox( "The path for the selected output operator [" + outputOperator + "] does NOT exist:\n\n%s" % outputFilename, "Error" )
            return
        elif( PathUtils.IsPathLocal( outputDirectory ) ):
            result = scriptDialog.ShowMessageBox( "The path for the selected output operator [" + outputOperator + "] is local:\n\n%s\n\nAre you sure you want to continue?" % outputDirectory, "Warning", ("Yes","No") )
            if( result == "No" ):
                return
    
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( outputFilename ):
        return
    
    inputFilepath = workspace.GetRenderInfoInputPathname()
    if( not Directory.Exists( inputFilepath ) and ( inputFilepath != "" ) ):
        scriptDialog.ShowMessageBox( "The Render Queue (Global Settings) Input Folder path does NOT exist on the network:\n\n" + inputFilepath, "Error" )
        return

    outputFilepath = workspace.GetRenderInfoOutputPathname()
    if( not Directory.Exists( outputFilepath ) and ( outputFilepath != "" ) ):
        scriptDialog.ShowMessageBox( "The Render Queue (Global Settings) Output Folder path does NOT exist on the network:\n\n" + outputFilepath, "Error" )
        return
    
    # Check if the output is a movie format.
    isMovie = workspace.IsOutputMovie( outputOperator )
    
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "combustion_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Combustion" )
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
    
    if not isMovie:
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
    else:
        writer.WriteLine( "ChunkSize=100000" )
        writer.WriteLine( "MachineLimit=1" )
    
    if outputFilename != "":
        fileNameOnly = Path.GetFileNameWithoutExtension( outputFilename )
        if fileNameOnly.find( "[#" ) >= 0 and fileNameOnly.find( "#]" ) >= 0:
            fileNameOnly = fileNameOnly.replace( "[#", "#" ).replace( "#]", "#" )
        else:
            fileNameOnly = fileNameOnly +  "####"
        
        writer.WriteLine( "OutputDirectory0=%s" % Path.GetDirectoryName( outputFilename ) )
        writer.WriteLine( "OutputFilename0=%s" % (fileNameOnly + Path.GetExtension( outputFilename )) )
    
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "combustion_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    if not scriptDialog.GetValue( "SubmitSceneBox" ):
        writer.WriteLine( "SceneFile=%s" % sceneFile )
    
    writer.WriteLine( "OutputOperator=%s" % outputOperator )
    
    version = scriptDialog.GetValue( "VersionBox" )
    writer.WriteLine( "Version=%s" % version )
    
    # We're no longer including the output file here because of some issues on OSX.
    #if outputFilename != "":
    #	writer.WriteLine( "OutputFile=%s" % outputFilename )
    
    writer.WriteLine( "FrameSize=%s" % workspace.GetFrameSize( outputOperator ) )
    writer.WriteLine( "CustomWidth=%s" % workspace.GetCustomWidth( outputOperator ) )
    writer.WriteLine( "CustomHeight=%s" % workspace.GetCustomHeight( outputOperator ) )
    writer.WriteLine( "LockAspect=%s" % workspace.GetLockAspect( outputOperator ) )
    writer.WriteLine( "BitDepth=%s" % workspace.GetBitDepth( outputOperator ) )
    writer.WriteLine( "Quality=%s" % workspace.GetQuality( outputOperator ) )
    writer.WriteLine( "SkipExistingFrames=%s" % scriptDialog.GetValue( "SkipExistingBox" ) )
    writer.WriteLine( "UseSingleCpu=%s" % scriptDialog.GetValue( "SingleCpuBox" ) )
        
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( sceneFile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
