from System.IO import StreamWriter
from System.Text import Encoding

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
jobOptionsDialog = None
frameList = None
framesPerTask = None
submittedFromMonitor = None
imageRender = False
outputFile = None
rndFileName = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global jobOptionsDialog
    global frameList
    global framesPerTask
    global submittedFromMonitor
    global imageRender
    global outputFile
    global rndFileName

    submittedFromMonitor = not bool( args )

    if not submittedFromMonitor:
        rndFileName = args[ 0 ]
        rndName = args[ 1 ]
        frameRange = args[ 2 ]
        # there's no way to detect an image render if submitted through the monitor, so initialize it here
        # videos will say Movie.dev and Mistika files will say Xfs.dev
        imageRender = args[ 3 ] == "Disk.dev"
        outputFile = args[ 4 ]

    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Mistika VR Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( "MistikaVR" ) )

    jobOptionsDialog = JobOptionsUI.JobOptionsDialog( parentAppName="MistikaVRMonitor" )

    scriptDialog.AddScriptControl( "JobOptionsDialog", jobOptionsDialog, "" )

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Mistika VR Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Mistika File", 1, 0, "The Mistika file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Mistika Render Files (*.rnd);;All Files (*)", 1, 1, colSpan=3 )

    imageBox = scriptDialog.AddSelectionControlToGrid( "ImageBox", "CheckBoxControl", False, "Image Render", 2, 1, "Check this box if the selected .rnd file corresponds to an image sequence render." )
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Mistika File With The Job", 2, 2, "If this option is enabled, the Mistika render file will be submitted with the job, and then copied locally to the Slave machine during rendering.", colSpan=2 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render.", False )
    framesBox = scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 2, "This is the number of frames that will be rendered at a time for each job task.", False )
    chunkSizeBox = scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 3, 3 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect( SubmitButtonPressed )

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect( scriptDialog.closeEvent )
    closeButton.ValueModified.connect( jobOptionsDialog.closeEvent )
    scriptDialog.EndGrid()

    settings = ( "FramesBox", "SubmitSceneBox", "ChunkSizeBox", "ImageBox", "SceneBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    frameList = scriptDialog.GetValue( "FramesBox" )
    framesPerTask = scriptDialog.GetValue( "ChunkSizeBox" )

    # if submitting through Mistika VR then populate some fields
    if not submittedFromMonitor:
        jobOptionsDialog.SetValue( "NameBox", rndName )
        scriptDialog.SetValue( "SceneBox", rndFileName )
        scriptDialog.SetEnabled( "ImageBox", False )

        if imageRender:
            scriptDialog.SetValue( "ImageBox", True )
            # do this so the integrated submitter will have the frame range specified in Mistika when it appears
            frameList = frameRange
        else:
            scriptDialog.SetValue( "ImageBox", False )

    ImageBoxChanged()

    # set the callbacks here so they don't get triggered when filling in the values initially
    imageBox.ValueModified.connect( ImageBoxChanged )
    framesBox.ValueModified.connect( FramesBoxChanged )
    chunkSizeBox.ValueModified.connect( ChunkSizeBoxChanged )

    scriptDialog.ShowDialog( True )

def GetSettingsFilename():
    return os.path.join( GetDeadlineSettingsPath(), "MistikaVRSettings.ini" )

def ImageBoxChanged():
    global scriptDialog
    global frameList
    global framesPerTask

    imageRenderChecked = scriptDialog.GetValue( "ImageBox" )

    scriptDialog.SetEnabled( "FramesLabel", imageRenderChecked )
    scriptDialog.SetEnabled( "FramesBox", imageRenderChecked )
    scriptDialog.SetEnabled( "ChunkSizeLabel", imageRenderChecked )
    scriptDialog.SetEnabled( "ChunkSizeBox", imageRenderChecked )

    if imageRenderChecked:
        scriptDialog.SetValue( "FramesBox", frameList )
        scriptDialog.SetValue( "ChunkSizeBox", framesPerTask )
    else:
        scriptDialog.SetValue( "FramesBox", "1" )
        scriptDialog.SetValue( "ChunkSizeBox", "1" )

def FramesBoxChanged():
    global frameList

    if scriptDialog.GetEnabled( "FramesBox" ):
        frameList = scriptDialog.GetValue( "FramesBox" )

def ChunkSizeBoxChanged():
    global framesPerTask

    if scriptDialog.GetEnabled( "ChunkSizeBox" ):
        framesPerTask = scriptDialog.GetValue( "ChunkSizeBox" )

def SubmitButtonPressed( *args ):
    global scriptDialog
    global jobOptionsDialog
    global submittedFromMonitor
    global imageRender
    global outputFile
    global rndFileName

    warnings = []
    errors = []

    # Check if Mistika VR render files exist.
    sceneFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "SceneBox" ), False )
    if len( sceneFiles ) == 0 :
        errors.append( "No Mistika VR render file specified." )

    submitScene = scriptDialog.GetValue( "SubmitSceneBox" )

    # Check if Mistika VR render file exists.
    for sceneFile in sceneFiles:
        if not os.path.isfile( sceneFile ):
            errors.append( "Mistika VR render file: %s does not exist." % sceneFile )
        elif not submitScene and PathUtils.IsPathLocal( sceneFile ):
            warnings.append( "The Mistika VR render file: " + sceneFile + " is local and is not being submitted with the job, are you sure you want to continue?" )

    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if not FrameUtils.FrameRangeValid( frames ):
        errors.append( "Frame range %s is not valid." % frames )

    if len( errors ) > 0:
        scriptDialog.ShowMessageBox( "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % ( "\n\n".join( errors ) ), "Errors" )
        return

    if len( warnings ) > 0:
        result = scriptDialog.ShowMessageBox( "Warnings:\n\n%s\n\nDo you still want to continue?" % ( "\n\n".join( warnings ) ), "Warnings", ( "Yes", "No" ) )
        if result == "No":
            return

    jobOptions = jobOptionsDialog.GetJobOptionsValues()

    successes = 0
    failures = 0

    # Submit each Mistika VR render file separately.
    for sceneFile in sceneFiles:
        originalJobName = jobOptions[ "Name" ]
        if len( sceneFiles ) > 1:
            newJobName = "%s [%s]" % ( originalJobName, os.path.basename( sceneFile ) )
            jobOptions[ "Name" ] = newJobName

        # Create job info file.
        jobInfoFilename = os.path.join( ClientUtils.GetDeadlineTempPath(), "mistikavr_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=MistikaVR" )

        for option, value in jobOptions.iteritems():
            writer.WriteLine( "%s=%s" % ( option, value ) )

        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )

        if not submittedFromMonitor and sceneFile == rndFileName:
            writer.WriteLine( "OutputFilename0=%s" % outputFile.replace( "%06d", "######" ) )

        writer.Close()

        if len( sceneFiles ) > 1:
            # reset the job name for the next job to be submitted
            jobOptions[ "Name" ] = originalJobName

        # Create plugin info file.
        pluginInfoFilename = os.path.join( ClientUtils.GetDeadlineTempPath(), "mistikavr_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

        if not submitScene:
            writer.WriteLine( "SceneFile=%s" % sceneFile )

        writer.WriteLine( "ImageRender=%s" % scriptDialog.GetValue( "ImageBox" ) )
        writer.Close()

        # Setup the command line arguments.
        arguments = [ jobInfoFilename, pluginInfoFilename ]

        if submitScene:
            arguments.append( sceneFile )

        if len( sceneFiles ) == 1:
            results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
            scriptDialog.ShowMessageBox( results, "Submission Results" )
        else:
            # Now submit the job.
            exitCode = ClientUtils.ExecuteCommand( arguments )
            if exitCode == 0:
                successes = successes + 1
            else:
                failures = failures + 1

    if len( sceneFiles ) > 1:
        scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )
