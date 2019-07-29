from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

# Job Options UI
import imp
import os
imp.load_source( "JobOptionsUI", os.path.join( RepositoryUtils.GetRepositoryPath( "submission/Common/Main", True ), "JobOptionsUI.py" ) )
import JobOptionsUI

########################################################################
## Globals
########################################################################
scriptDialog = None
outputBox = None
sceneBox = None
defaultLocation = None
settings = None
jobOptions_dialog = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global defaultLocation
    global outputBox
    global sceneBox
    global jobOptions_dialog
    
    defaultLocation = ""
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Command Line Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'CommandLine' ) )

    jobOptions_dialog = JobOptionsUI.JobOptionsDialog( parentAppName = "CommandLineMonitor" )
    
    scriptDialog.AddScriptControl( "JobOptionsDialog", jobOptions_dialog, "" )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Command Line Options", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "JobTypeLabel", "LabelControl", "Job Type", 1, 0, "Choose a normal or maintenance job.", False )
    jobTypeBox = scriptDialog.AddComboControlToGrid( "JobTypeBox", "ComboControl", "Normal", ("Normal","Maintenance"), 1, 1 )
    jobTypeBox.ValueModified.connect(jobTypeChanged)
    singleFramesBox = scriptDialog.AddSelectionControlToGrid( "SingleFramesOnlyBox", "CheckBoxControl", False, "Single Frames Only", 1, 2, "If enabled, the CommandLine plugin will only render one frame at a time even if a single task contains a chunk of frames." )
    singleFramesBox.ValueModified.connect(singleFramesChanged)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 2, 0, "The list of frames for the normal job.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 2, 1 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 2, 2, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 2, 3 )

    scriptDialog.AddControlToGrid( "StartFrameLabel", "LabelControl", "Start Frame", 3, 0, "The first frame for the maintenance job.", False )
    scriptDialog.AddRangeControlToGrid( "StartFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 1 )
    scriptDialog.AddControlToGrid( "EndFrameLabel", "LabelControl", "End Frame", 3, 2, "The last frame for the maintenance job.", False )
    scriptDialog.AddRangeControlToGrid( "EndFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 3 )

    scriptDialog.AddControlToGrid( "ExecutableLabel", "LabelControl", "Executable", 4, 0, "The Executable to use for rendering.", False )
    scriptDialog.AddSelectionControlToGrid( "ExecBox", "FileBrowserControl", "", "All Files (*)", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ArgsLabel", "LabelControl", "Arguments (optional)", 5, 0, "The command line arguments to be submitted." )
    scriptDialog.AddControlToGrid( "ArgsBox", "TextControl", "", 5, 1, colSpan=3 )

    scriptDialog.AddControlToGrid("SpacerLabel","LabelControl", "Argument Tags", 6, 0, "Use these buttons to add tags to the arguments.", False )
    startFButton = scriptDialog.AddControlToGrid("StartFButton","ButtonControl", "Start Frame Tag", 6, 1, 'Adds a Start Frame tag to the arguments.' )
    endFButton = scriptDialog.AddControlToGrid("EndFButton","ButtonControl", "End Frame Tag", 6, 2, 'Adds an End Frame tag to the arguments.' )
    quoteButton = scriptDialog.AddControlToGrid("QuoteButton","ButtonControl", "Quote Tag", 6, 3, 'Adds a Quote tag to the arguments.' )

    scriptDialog.AddControlToGrid("FramePaddingLabel","LabelControl", "Frame Tag Padding", 7, 0, "Controls the amount of frame padding for the Start Frame and End Frame tags.", False )
    scriptDialog.AddRangeControlToGrid( "FramePaddingBox", "RangeControl", 0, 0, 10, 0, 1, 7, 1 )
    shellExecute = scriptDialog.AddSelectionControlToGrid( "ShellExecuteBox", "CheckBoxControl", False, "Execute In Shell", 7, 2, "If enabled, the specified argument(s) will be executed through the current shell." )
    shellExecute.ValueModified.connect( ShellExecuteButtonPressed )
    scriptDialog.AddComboControlToGrid( "ShellToUseBox", "ComboControl", "default", ["default","bash","csh","ksh","sh","tcsh","zsh","cmd"], 7, 3 )

    scriptDialog.AddControlToGrid( "StartupLabel", "LabelControl", "Start Up Folder (optional)", 8, 0, "The directory that the command line will start up in.", False )
    scriptDialog.AddSelectionControlToGrid( "StartupBox", "FolderBrowserControl", "","", 8, 1, colSpan=3, browserLocation=defaultLocation)
    startFButton.ValueModified.connect(startFPressed)
    endFButton.ValueModified.connect(endFPressed)
    quoteButton.ValueModified.connect(quotePressed)
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0)
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    closeButton.ValueModified.connect(jobOptions_dialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ( "FramesBox","ChunkSizeBox","ExecBox","ArgsBox","StartupBox","ShellExecuteBox","ShellToUseBox","SingleFramesOnlyBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    jobTypeChanged( None )
    ShellExecuteButtonPressed( None )

    scriptDialog.ShowDialog( True )  

def jobTypeChanged( *args ):
    global scriptDialog
    
    normalJob = (scriptDialog.GetValue( "JobTypeBox" ) == "Normal")
    
    scriptDialog.SetEnabled( "FramesLabel", normalJob )
    scriptDialog.SetEnabled( "FramesBox", normalJob )
    scriptDialog.SetEnabled( "ChunkSizeLabel", normalJob )
    scriptDialog.SetEnabled( "ChunkSizeBox", normalJob )
    
    scriptDialog.SetEnabled( "StartFrameLabel", not normalJob )
    scriptDialog.SetEnabled( "StartFrameBox", not normalJob )
    scriptDialog.SetEnabled( "EndFrameLabel", not normalJob )
    scriptDialog.SetEnabled( "EndFrameBox", not normalJob )
    singleFramesChanged()

def singleFramesChanged( *args ):
    global scriptDialog

    singleFrames = scriptDialog.GetValue( "SingleFramesOnlyBox" )

    scriptDialog.SetEnabled( "EndFButton", not singleFrames )

def startFPressed( *args ):
    global scriptDialog
    
    currentText = scriptDialog.GetValue( "ArgsBox" )
    
    frameTag = "<STARTFRAME"
    
    padding = scriptDialog.GetValue( "FramePaddingBox" )
    if padding > 0:
        frameTag += "%" + str(padding)
        
    frameTag += ">"
    
    currentText += frameTag
    scriptDialog.SetValue( "ArgsBox", currentText ) 
    
def endFPressed( *args ):
    global scriptDialog
    
    currentText = scriptDialog.GetValue( "ArgsBox" )
    
    frameTag = "<ENDFRAME"
    
    padding = scriptDialog.GetValue( "FramePaddingBox" )
    if padding > 0:
        frameTag += "%" + str(padding)
        
    frameTag += ">"
    
    currentText += frameTag
    scriptDialog.SetValue( "ArgsBox", currentText )
    
def quotePressed( *args ):
    global scriptDialog
    
    currentText = scriptDialog.GetValue( "ArgsBox" ) 
    currentText += "<QUOTE>"
    scriptDialog.SetValue( "ArgsBox", currentText ) 

def ShellExecuteButtonPressed( *args ):
    global scriptDialog
    state = scriptDialog.GetValue( "ShellExecuteBox" )
    scriptDialog.SetEnabled( "ShellToUseBox", state )
    scriptDialog.SetEnabled( "ExecBox", not state )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "CommandLineSettings.ini" )
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    global jobOptions_dialog

    warnings = []
    errors = []
    
    # Check if the executable exists.
    execFile = scriptDialog.GetValue( "ExecBox" )
    shellExecute = scriptDialog.GetValue( "ShellExecuteBox" )

    if not shellExecute:
        if execFile == "":
            errors.append( "Please specify an Executable file." )  
        elif( not File.Exists( execFile ) ):
            warnings.append( "The Executable %s file does not exist at the given location. Are you sure you want to continue?" % execFile )
    
    # Check if a valid frame range has been specified.
    frames = ""
    if scriptDialog.GetValue( "JobTypeBox" ) == "Normal":
        frames = scriptDialog.GetValue( "FramesBox" )
        if( not FrameUtils.FrameRangeValid( frames ) ):
            errors.append( "Frame range %s is not valid." % frames )

    if len( errors ) > 0:
        scriptDialog.ShowMessageBox( "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % ( "\n\n".join( errors ) ), "Errors" )
        return

    if len( warnings ) > 0:
        result = scriptDialog.ShowMessageBox( "Warnings:\n\n%s\n\nDo you still want to continue?" % ( "\n\n".join( warnings ) ), "Warnings", ( "Yes","No" ) )
        if result == "No":
            return

    jobOptions = jobOptions_dialog.GetJobOptionsValues()

    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "commandline_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=CommandLine" )

    for option, value in jobOptions.iteritems():
        writer.WriteLine( "%s=%s" % ( option, value ) )

    if scriptDialog.GetValue( "JobTypeBox" ) == "Normal":
        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
    else:
        writer.WriteLine( "MaintenanceJob=true" )
        writer.WriteLine( "MaintenanceJobStartFrame=%s" % scriptDialog.GetValue( "StartFrameBox" ) )
        writer.WriteLine( "MaintenanceJobEndFrame=%s" % scriptDialog.GetValue( "EndFrameBox" ) )
        
    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "commandline_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

    writer.WriteLine( "SingleFramesOnly=%s" % scriptDialog.GetValue( "SingleFramesOnlyBox" ) )
    writer.WriteLine( "Executable=%s" % scriptDialog.GetValue( "ExecBox" ) )
    writer.WriteLine( "Arguments=%s" % scriptDialog.GetValue( "ArgsBox" ) )
    writer.WriteLine( "StartupDirectory=%s" % scriptDialog.GetValue( "StartupBox" ) )
    writer.WriteLine( "ShellExecute=%s" % scriptDialog.GetValue( "ShellExecuteBox" ) )
    writer.WriteLine( "Shell=%s" % scriptDialog.GetValue( "ShellToUseBox" ) )
    
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
