## ------------------------------------------------------------
## JobDJVSubmission.py
## Created April 12th 2011 by Mike Owen
## 
## DJV Job Submission based on Output Filename Image Sequence or Movie File Job in the Deadline Queue System
## Tested with Win7x64 OS and potentially 'compatiable' with any other Windows OS and also MAC OS X & Linux
## ------------------------------------------------------------
## NOTES:
## 
## ------------------------------------------------------------
import sys

from System.IO import *
from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
djvScriptDialog = None
scriptPath = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global djvScriptDialog
    global scriptPath
    
    djvScriptDialog = DeadlineScriptDialog()
    djvScriptDialog.SetIcon( Path.Combine( RepositoryUtils.GetRootDirectory("plugins/DJV"), "DJV.ico" ) )
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    if len(selectedJobs) > 1:
        djvScriptDialog.ShowMessageBox( "Only one job can be selected at a time.", "Multiple Jobs Selected" )
        return
    
    scriptPath = Path.Combine( RepositoryUtils.GetRootDirectory("scripts/Submission"), "DJVSubmission.py" )
    scriptPath = PathUtils.ToPlatformIndependentPath( scriptPath )
    
    job = selectedJobs[0]
    outputFilenameCount = len(job.JobOutputFileNames)

    if outputFilenameCount == 0:
        djvScriptDialog.ShowMessageBox( "Job does not contain any output filename(s).", "Missing Output" )
        return

    versionId = ""
    if outputFilenameCount > 0:        
        versionId = job.GetJobExtraInfoKeyValue( "VersionId" )
        if versionId != "":
            lines = []
            lines.append( "VersionId=%s" % versionId )
            
            if job.GetJobExtraInfoKeyValue( "EntityId" ) != "":
                lines.append( "EntityId=%s" % job.GetJobExtraInfoKeyValue( "EntityId" ) )
            if job.GetJobExtraInfoKeyValue( "EntityType" ) != "":
                lines.append( "EntityType=%s" % job.GetJobExtraInfoKeyValue( "EntityType" ) )
            if job.GetJobExtraInfoKeyValue( "ProjectId" ) != "":
                lines.append( "ProjectId=%s" % job.GetJobExtraInfoKeyValue( "ProjectId" ) )
            if job.GetJobExtraInfoKeyValue( "TaskId" ) != "":
                lines.append( "TaskId=%s" % job.GetJobExtraInfoKeyValue( "TaskId" ) )
                
            if job.JobExtraInfo0 != "":
                lines.append( "TaskName=%s" % job.JobExtraInfo0 )
            elif job.GetJobExtraInfoKeyValue( "TaskName" ) != "":
                lines.append( "TaskName=%s" % job.GetJobExtraInfoKeyValue( "TaskName" ) )
            
            if job.JobExtraInfo1 != "":
                lines.append( "ProjectName=%s" % job.JobExtraInfo1 )
            elif job.GetJobExtraInfoKeyValue( "ProjectName" ) != "":
                lines.append( "ProjectName=%s" % job.GetJobExtraInfoKeyValue( "ProjectName" ) )
            
            if job.JobExtraInfo2 != "":
                lines.append( "EntityName=%s" % job.JobExtraInfo2 )
            elif job.GetJobExtraInfoKeyValue( "EntityName" ) != "":
                lines.append( "EntityName=%s" % job.GetJobExtraInfoKeyValue( "EntityName" ) )
            
            if job.JobExtraInfo3 != "":
                lines.append( "VersionName=%s" % job.JobExtraInfo3 )
            elif job.GetJobExtraInfoKeyValue( "VersionName" ) != "":
                lines.append( "VersionName=%s" % job.GetJobExtraInfoKeyValue( "VersionName" ) )
            
            if job.JobExtraInfo4 != "":
                lines.append( "Description=%s" % job.JobExtraInfo4 )
            elif job.GetJobExtraInfoKeyValue( "Description" ) != "":
                lines.append( "Description=%s" % job.GetJobExtraInfoKeyValue( "Description" ) )
                
            if job.JobExtraInfo5 != "":
                lines.append( "UserName=%s" % job.JobExtraInfo5 )
            elif job.GetJobExtraInfoKeyValue( "UserName" ) != "":
                lines.append( "UserName=%s" % job.GetJobExtraInfoKeyValue( "UserName" ) )
            
            shotgunSettingsPath = Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "DJVSettingsShotgun.ini" )
            File.WriteAllLines( shotgunSettingsPath, tuple(lines) )
    
    if outputFilenameCount > 1:
        djvScriptDialog.AllowResizingDialog( False )
        djvScriptDialog.SetTitle( "Submit DJV QuickTime Job To Deadline" )
        
        djvScriptDialog.AddGrid()
        djvScriptDialog.AddControlToGrid( "Label", "LabelControl", "Please select the output images to create a QuickTime MOV using DJV", 0, 0 )
        for i in range( 0, outputFilenameCount ):
            outputFilename = Path.Combine(  job.JobOutputDirectories[i], job.JobOutputFileNames[i])
            outputFilename = FrameUtils.ReplacePaddingWithFrameNumber( outputFilename, job.JobFramesList[0] )
            outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
            outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
            djvScriptDialog.AddSelectionControlToGrid( str(i), "CheckBoxControl", (i==0), Path.GetFileName( outputFilename ), i+1, 0 )
        
        djvScriptDialog.EndGrid()
        djvScriptDialog.AddGrid()
        djvScriptDialog.AddHorizontalSpacerToGrid( "DummyLabel1", 0, 0 )
        submitButton = djvScriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
        submitButton.ValueModified.connect(SubmitButtonPressed)
        closeButton = djvScriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
        closeButton.ValueModified.connect(CloseButtonPressed)
        djvScriptDialog.EndGrid()
        
        djvScriptDialog.ShowDialog( True )
    else:
        JobName = job.JobName
        JobID = job.JobId
        FramesList = job.JobFrames
        
        # Unable to handle nth Frame based FramesList at the moment, until Deadline.Scripting API Function improved in a future release of Deadline (~v5.1?)
        FrameRange = FramesList.split( "-" )
        FrameRange = FramesList.split( "," )
        
        # Throw Error if the Frame List is not in the form "0-100"
        if len(FrameRange) >= 4:
            djvScriptDialog.ShowMessageBox( "DJV presently does not support handling nth Frame based render input sequences.", "Error!" )
            CloseDJVDialog()
            return

        startFrame = FrameRange[0] # get first item in list
        endFrame = FrameRange[-1] # get last item in list, no matter how long it is
        FramesList = startFrame + "-" + endFrame
        
        outputFilename = Path.Combine(  job.JobOutputDirectories[0], job.JobOutputFileNames[0])
        outputFilename = FrameUtils.ReplacePaddingWithFrameNumber( outputFilename, job.JobFramesList[0] )
        outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
        outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
        
        InputImages = outputFilename.replace( "\\", "/" )
        OutputMovie = ""
        
        if outputFilename and len(outputFilename) > 0:
            imgDirectory = Path.GetDirectoryName( outputFilename )
            if imgDirectory != None:
                imgFilename = Path.GetFileNameWithoutExtension( outputFilename )

                # Job Script hard-wired to QuickTime MOV until above Deadline.Scripting API Function improved to handle nth frame based render output sequences. Deadline (~v5.1?)
                OutputMovie = ( imgDirectory.replace( "\\", "/" ) + "/" + imgFilename + ".mov" )
        
        arguments = [ InputImages, OutputMovie, JobID, JobName, FramesList ]
        if versionId != "":
            arguments.append( "EnableShotgun" )
        
        ClientUtils.ExecuteScript( scriptPath, arguments )

def CloseDJVDialog():
    global djvScriptDialog
    djvScriptDialog.CloseDialog()

def CloseButtonPressed(*args):
    CloseDJVDialog()

def SubmitButtonPressed(*args):
    global djvScriptDialog
    global scriptPath
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    job = selectedJobs[0]
    JobName = job.JobName
    JobID = job.JobId
    FramesList = job.JobFrames
    
    # Unable to handle nth Frame based FramesList at the moment, until Deadline.Scripting API Function improved in a future release of Deadline (~v5.1?)
    FrameRange = FramesList.split( "-" )
    FrameRange = FramesList.split( "," )
    
    # Throw Error if the Frame List is not in the form "0-100"
    if len(FrameRange) >= 4:
        djvScriptDialog.ShowMessageBox( "DJV presently does not support handling nth Frame based render input sequences.", "Error!" )
        CloseDJVDialog()
        return

    startFrame = FrameRange[0] # get first item in list
    endFrame = FrameRange[-1] # get last item in list, no matter how long it is
    FramesList = startFrame + "-" + endFrame
    
    versionId = job.GetJobExtraInfoKeyValue( "VersionId" )

    outputFilenameCount = len(job.JobOutputFileNames)
    for i in range( 0, outputFilenameCount ):
        if bool(djvScriptDialog.GetValue( str(i) ) ):
            outputFilename = Path.Combine(  job.JobOutputDirectories[i], job.JobOutputFileNames[i])
            outputFilename = FrameUtils.ReplacePaddingWithFrameNumber( outputFilename, job.JobFramesList[0] )
            outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
            outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
            
            InputImages = outputFilename.replace( "\\", "/" )
            OutputMovie = ""
            
            imgDirectory = Path.GetDirectoryName( outputFilename )
            if imgDirectory != None:
                imgFilename = Path.GetFileNameWithoutExtension( outputFilename )

                # Job Script hard-wired to QuickTime MOV until above Deadline.Scripting API Function improved to handle nth frame based render output sequences. Deadline (~v5.1?)
                OutputMovie = ( imgDirectory.replace( "\\", "/" ) + "/" + imgFilename + ".mov" )
            
            arguments = [ InputImages, OutputMovie, JobID, JobName, FramesList ]
            if versionId != "":
                arguments.append( "EnableShotgun" )
            
            ClientUtils.ExecuteScript( scriptPath, arguments )
    
    CloseDJVDialog()
