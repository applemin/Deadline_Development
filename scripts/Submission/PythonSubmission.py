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
settings = None
jobOptions_dialog = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global jobOptions_dialog

    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Python Script To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Python' ) )
    
    jobOptions_dialog = JobOptionsUI.JobOptionsDialog( parentAppName = "PythonMonitor" )
    
    scriptDialog.AddScriptControl( "JobOptionsDialog", jobOptions_dialog, "" )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Python Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "JobTypeLabel", "LabelControl", "Job Type", 1, 0, "Choose a normal or maintenance job.", False )
    jobTypeBox = scriptDialog.AddComboControlToGrid( "JobTypeBox", "ComboControl", "Normal", ("Normal","Maintenance"), 1, 1 )
    jobTypeBox.ValueModified.connect(jobTypeChanged)
    singleFramesBox = scriptDialog.AddSelectionControlToGrid( "SingleFramesOnlyBox", "CheckBoxControl", False, "Single Frames Only", 1, 2, "If enabled, the Python plugin will only render one frame at a time even if a single task contains a chunk of frames." )
    singleFramesBox.ValueModified.connect(singleFramesChanged)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 2, 0, "The list of frames for the normal job.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 2, 1 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 2, 2, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 2, 3 )

    scriptDialog.AddControlToGrid( "StartFrameLabel", "LabelControl", "Start Frame", 3, 0, "The first frame for the maintenance job.", False )
    scriptDialog.AddRangeControlToGrid( "StartFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 1 )
    scriptDialog.AddControlToGrid( "EndFrameLabel", "LabelControl", "End Frame", 3, 2, "The last frame for the maintenance job.", False )
    scriptDialog.AddRangeControlToGrid( "EndFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Python Script File", 4, 0, "The script file to be executed.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Python Files (*.py);;All Files (*)", 4, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "ArgsLabel", "LabelControl", "Arguments", 5, 0, "The arguments to pass to the script. If no arguments are required, leave this blank.", False )
    scriptDialog.AddControlToGrid( "ArgsBox", "TextControl", "", 5, 1, colSpan=3 )

    scriptDialog.AddControlToGrid("SpacerLabel","LabelControl", "Argument Tags", 6, 0, "Use these buttons to add tags to the arguments.", False )
    startFButton = scriptDialog.AddControlToGrid("StartFButton","ButtonControl", "Start Frame Tag", 6, 1, 'Adds a Start Frame tag to the arguments.' )
    endFButton = scriptDialog.AddControlToGrid("EndFButton","ButtonControl", "End Frame Tag", 6, 2, 'Adds an End Frame tag to the arguments.' )
    quoteButton = scriptDialog.AddControlToGrid("QuoteButton","ButtonControl", "Quote Tag", 6, 3, 'Adds a Quote tag to the arguments.' )
    startFButton.ValueModified.connect(startFPressed)
    endFButton.ValueModified.connect(endFPressed)
    quoteButton.ValueModified.connect(quotePressed)

    scriptDialog.AddControlToGrid("FramePaddingLabel","LabelControl", "Frame Tag Padding", 7, 0, "Controls the amount of frame padding for the Start Frame and End Frame tags.", False )
    scriptDialog.AddRangeControlToGrid( "FramePaddingBox", "RangeControl", 0, 0, 10, 0, 1, 7, 1 )
    
    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 8, 0, "The version of Python to use.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "2.7", ("2.3","2.4","2.5","2.6","2.7","3.0","3.1","3.2","3.3","3.4","3.5","3.6","3.7"), 8, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", True, "Submit Script File", 8, 2, "If this option is enabled, the script file will be submitted with the job, and then copied locally to the Slave machine during execution." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    closeButton.ValueModified.connect(jobOptions_dialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ( "SceneBox","ArgsBox","VersionBox","SubmitSceneBox","FramesBox","ChunkSizeBox","SingleFramesOnlyBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    jobTypeChanged( None )

    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "PythonSettings.ini" )

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

def SubmitButtonPressed( *args ):
    global scriptDialog
    global jobOptions_dialog

    warnings = []
    errors = []
    
    # Check if python file exist.
    sceneFile = scriptDialog.GetValue( "SceneBox" )

    if sceneFile == "":
        errors.append( "Please specify a Python file." )
    elif( not File.Exists( sceneFile ) ):
        errors.append( "The Python file %s does not exist." % sceneFile )
    elif (not scriptDialog.GetValue("SubmitSceneBox") and PathUtils.IsPathLocal(sceneFile)):
        warnings.append( "The Python file %s is local. Are you sure you want to continue?" % sceneFile )

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
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "python_job_info.job" )
    try:
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    except Exception as e:
        scriptDialog.ShowMessageBox("error: " + str(e) , "")
    
    writer.WriteLine( "Plugin=Python" )

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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "python_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    if(not scriptDialog.GetValue( "SubmitSceneBox" ) ):
        writer.WriteLine( "ScriptFile=" + sceneFile )
        
    writer.WriteLine( "Arguments=%s" % scriptDialog.GetValue( "ArgsBox" ) )
    writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )
    writer.WriteLine( "SingleFramesOnly=%s" % scriptDialog.GetValue( "SingleFramesOnlyBox" ) )
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
