import sys
import os

from System.IO import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

vrimgScriptDialog = None
scriptPath = None
vrimgFilenames = []

def __main__():
    global vrimgScriptDialog
    global scriptPath
    global vrimgFilenames
    
    vrimgScriptDialog = DeadlineScriptDialog()
    vrimgScriptDialog.SetIcon( os.path.join( RepositoryUtils.GetRootDirectory("plugins/Vrimg2Exr"), "Vrimg2Exr.ico" ) )
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    if len(selectedJobs) > 1:
        vrimgScriptDialog.ShowMessageBox( "Only one job can be selected at a time.", "Multiple Jobs Selected" )
        return
    
    scriptPath = Path.Combine( RepositoryUtils.GetRootDirectory("scripts/Submission"), "Vrimg2ExrSubmission.py" )
    scriptPath = PathUtils.ToPlatformIndependentPath( scriptPath )
    
    job = selectedJobs[0]
    outputFilenameCount = len(job.JobOutputFileNames)

    if outputFilenameCount == 0:
        vrimgScriptDialog.ShowMessageBox( "Job does not contain any output filename(s).", "Missing Output" )
        return

    for i in range( 0, outputFilenameCount ):
        outputFilename = Path.Combine(  job.JobOutputDirectories[i], job.JobOutputFileNames[i])
        outputFilename = FrameUtils.ReplacePaddingWithFrameNumber( outputFilename, job.JobFramesList[0] )
        if outputFilename.lower().endswith( ".vrimg" ):
            vrimgFilenames.append( outputFilename )
    
    vrimgFilenameCount = len( vrimgFilenames )
    if vrimgFilenameCount > 1:
        dialogWidth = 600
        
        vrimgScriptDialog.AllowResizingDialog( False )
        #vrimgScriptDialog.SetSize( dialogWidth, (vrimgFilenameCount * 32) + 100 )
        vrimgScriptDialog.SetTitle( "Submit Vrimg2Exr Job To Deadline" )
        
        vrimgScriptDialog.AddGrid()
        vrimgScriptDialog.AddControlToGrid( "Label", "LabelControl", "Please select the vrming images to convert to exr.", 0, 0 )
        for i in range( 0, vrimgFilenameCount ):
            outputFilename = vrimgFilenames[ i ]
            outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
            outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
            vrimgScriptDialog.AddSelectionControlToGrid( str(i), "CheckBoxControl", (i==0), Path.GetFileName( outputFilename ), i+1, 0 )
        vrimgScriptDialog.EndGrid()
        
        vrimgScriptDialog.AddGrid()
        vrimgScriptDialog.AddHorizontalSpacerToGrid( "DummyLabel1", 0, 0 )
        submitButton = vrimgScriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
        submitButton.ValueModified.connect(SubmitButtonPressed)
        closeButton = vrimgScriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
        closeButton.ValueModified.connect(CloseButtonPressed)
        vrimgScriptDialog.EndGrid()
        
        vrimgScriptDialog.ShowDialog( True )
    elif vrimgFilenameCount == 1:
        outputFilename = vrimgFilenames[ 0 ]
        outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
        outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
        ClientUtils.ExecuteScript( scriptPath, outputFilename )
    else:
        ClientUtils.ExecuteScript( scriptPath, "" )

def CloseVrimgDialog():
    global vrimgScriptDialog
    vrimgScriptDialog.CloseDialog()

def CloseButtonPressed(*args):
    CloseVrimgDialog()
    
def SubmitButtonPressed(*args):
    global vrimgScriptDialog
    global scriptPath
    global vrimgFilenames
    
    vrimgFilenameCount = len( vrimgFilenames )
    for i in range( 0, vrimgFilenameCount ):
        if bool(vrimgScriptDialog.GetValue( str(i) ) ):
            outputFilename = vrimgFilenames[ i ]
            outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
            outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
            ClientUtils.ExecuteScript( scriptPath, outputFilename )
    
    CloseVrimgDialog()
