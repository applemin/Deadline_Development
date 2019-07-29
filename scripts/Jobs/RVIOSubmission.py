import clr
import sys

from System.IO import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
rvioScriptDialog = None
scriptPath = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global rvioScriptDialog
    global scriptPath
    
    rvioScriptDialog = DeadlineScriptDialog()
    rvioScriptDialog.SetIcon( Path.Combine( RepositoryUtils.GetRootDirectory("plugins/RVIO"), "RVIO.ico" ) )
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    if len(selectedJobs) > 1:
        rvioScriptDialog.ShowMessageBox( "Only one job can be selected at a time.", "Multiple Jobs Selected" )
        return
    
    scriptPath = Path.Combine( RepositoryUtils.GetRootDirectory("scripts/Submission"), "RVIOSubmission.py" )
    scriptPath = PathUtils.ToPlatformIndependentPath( scriptPath )
    
    job = selectedJobs[0]
    outputFilenameCount = len(job.JobOutputFileNames)

    if outputFilenameCount == 0:
        rvioScriptDialog.ShowMessageBox( "Job does not contain any output filename(s).", "Missing Output" )
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
            
            shotgunSettingsPath = Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "RVIOSettingsShotgun.ini" )
            File.WriteAllLines( shotgunSettingsPath, tuple(lines) )
    
    if outputFilenameCount > 1:        
        rvioScriptDialog.AllowResizingDialog( False )
        rvioScriptDialog.SetTitle( "Submit RVIO Quicktime Job To Deadline" )
        
        rvioScriptDialog.AddGrid()
        rvioScriptDialog.AddControlToGrid( "Label", "LabelControl", "Please select the output images to create a QuickTime MOV using RVIO", 0, 0 )
        for i in range( 0, outputFilenameCount ):
            outputFilename = Path.Combine(  job.JobOutputDirectories[i], job.JobOutputFileNames[i])
            outputFilename = FrameUtils.ReplacePaddingWithFrameNumber( outputFilename, job.JobFramesList[0] )
            outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
            outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
            rvioScriptDialog.AddSelectionControlToGrid( str(i), "CheckBoxControl", (i==0), Path.GetFileName( outputFilename ), i+1, 0 )
        
        rvioScriptDialog.EndGrid()
        rvioScriptDialog.AddGrid()
        rvioScriptDialog.AddHorizontalSpacerToGrid( "DummyLabel1", 0, 0 )
        submitButton = rvioScriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
        submitButton.ValueModified.connect(SubmitButtonPressed)
        closeButton = rvioScriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
        closeButton.ValueModified.connect(CloseButtonPressed)
        rvioScriptDialog.EndGrid()
        
        rvioScriptDialog.ShowDialog( True )
    else:
        outputFilename = Path.Combine(  job.JobOutputDirectories[0], job.JobOutputFileNames[0])
        outputFilename = FrameUtils.ReplacePaddingWithFrameNumber( outputFilename, job.JobFramesList[0] )
        outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
        outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
        
        arguments = [outputFilename,]
        if versionId != "":
            arguments.append( "EnableShotgun" )
        
        ClientUtils.ExecuteScript( scriptPath, arguments )

def CloseRvioDialog():
    global rvioScriptDialog
    rvioScriptDialog.CloseDialog()

def CloseButtonPressed(*args):
    CloseRvioDialog()
    
def SubmitButtonPressed(*args):
    global rvioScriptDialog
    global scriptPath
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    job = selectedJobs[0]
    
    versionId = job.GetJobExtraInfoKeyValue( "VersionId" )
    
    outputFilenameCount = len(job.JobOutputFileNames)
    for i in range( 0, outputFilenameCount ):
        if bool(rvioScriptDialog.GetValue( str(i) ) ):
            outputFilename = Path.Combine(  job.JobOutputDirectories[i], job.JobOutputFileNames[i])
            outputFilename = FrameUtils.ReplacePaddingWithFrameNumber( outputFilename, job.JobFramesList[0] )
            outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
            outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
            
            arguments = [outputFilename,]
            if versionId != "":
                arguments.append( "EnableShotgun" )
            
            ClientUtils.ExecuteScript( scriptPath, arguments )
    
    CloseRvioDialog()
