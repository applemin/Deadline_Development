import clr
import sys

from System.Diagnostics import *
from System.IO import *

from Deadline.Scripting import *
from Deadline.Jobs import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

def __main__():    

    folders = []
    scriptDialog = DeadlineScriptDialog()
    dialogString = ""

    Jobs = MonitorUtils.GetSelectedJobs()
    
    for job in Jobs:
        if job.GetJobInfoKeyValue( "Plugin" ) != "Nuke":
            scriptDialog.ShowMessageBox( "%s is not a Nuke job. This script only works for Nuke jobs." % job.GetJobInfoKeyValue( "Name" ), "Error" )
            return
        elif job.JobStatus == "Active" or job.JobStatus == "Pending":
            scriptDialog.ShowMessageBox( "Do NOT attempt to DELETE \".tmp\" files when a job is [%s]\n\n" + "Only Suspended/Completed/Failed jobs should be processed." % job.JobStatus, "Error" )
            return

    for job in Jobs:
        i = 0
        outputDir = job.GetJobInfoKeyValue( "OutputDirectory%i" % i )

        while outputDir != "":
            if( folders.count( outputDir ) == 0 ):
                folders.append( outputDir )
                dialogString += outputDir + "\n"
            i += 1
            outputDir = job.GetJobInfoKeyValue( "OutputDirectory%i" % i )

    if len( folders ) == 0:
        scriptDialog.ShowMessageBox( "Cannot locate the Output Folder(s) for the selected job(s)!", "No Output Folders Specified" )
        return
    
    result = scriptDialog.ShowMessageBox( "This will find and DELETE files ending in \".tmp\" in the following folder(s):\n\n%s\nContinue?" % dialogString, "Delete .tmp Files?", ("Yes","No") )
    if result == "No":
        return

    dialogString = ""
    errorIOString = ""
    errorPermissionsString = ""
    tmpFiles = 0
    tmpIOFiles = 0
    tmpPermissionsFiles = 0

    for folder in folders:
        files = Directory.GetFiles( folder )
        for file in files:
            if Path.GetExtension( file ) == ".tmp":
                try:
                    File.Delete(file)
                    dialogString =  dialogString + file + "\n"
                    tmpFiles += 1
                except  IOException as e: # IOException = The specified file is in use.
                    errorIOString = errorIOString + file + e + "\n"
                    tmpIOFiles += 1
                except UnauthorizedAccessException as e: # UnauthorizedAccessException = The caller does not have the required permission.
                    errorPermissionsString = errorPermissionsString + file + e + "\n"
                    tmpPermissionsFiles += 1

    if tmpFiles > 0:
        if tmpIOFiles == 0 and tmpPermissionsFiles == 0:
            if tmpFiles < 50:
                scriptDialog.ShowMessageBox( "The following %d \".tmp\" files were deleted:\n\n%s" % (tmpFiles, dialogString), "Deleted Files" )
            else :
                scriptDialog.ShowMessageBox( "%d \".tmp\" files were found and deleted!" % tmpFiles, "Deleted Files" )
                
        elif tmpIOFiles > 0 and tmpPermissionsFiles == 0:
            if tmpFiles < 25 and tmpIOFiles < 25:
                scriptDialog.ShowMessageBox( "The following %d \".tmp\" files were deleted:\n\n%s\n\nThe following %d files FAILED due to being LOCKED to another IO process:\n\n%s" % (tmpFiles, dialogString, tmpIOFiles, errorIOString), "Deleted Files Completed with IO Error(s)" )
            else:
                scriptDialog.ShowMessageBox( "%d \".tmp\" files were found and deleted! BUT %d FAILED due to the file being LOCKED to another IO process!" % (tmpFiles, tmpIOFiles), "Deleted Files Completed with IO Error(s)" )

        elif tmpIOFiles == 0 and tmpPermissionsFiles > 0:
            if tmpFiles < 25 and tmpPermissionsFiles < 25:
                scriptDialog.ShowMessageBox( "The following %d \".tmp\" files were deleted:\n\n%s\n\nThe following %d files FAILED due to Incorrect Permissions:\n\n%s" % (tmpFiles, dialogString, tmpPermissionsFiles, errorPermissionsString), "Deleted Files Completed with Permissions Error(s)" )
            else:
                scriptDialog.ShowMessageBox( "%d \".tmp\" files were found and deleted! BUT %d FAILED due to Incorrect Permissions!" % (tmpFiles, tmpPermissionsFiles), "Deleted Files Completed with Permissions Error(s)" )
                
        elif tmpIOFiles > 0 and tmpPermissionsFiles > 0:
            scriptDialog.ShowMessageBox( "%d \".tmp\" files were found and deleted! BUT %d FAILED due to the file being LOCKED to another IO process and %d FAILED due to Incorrect Permissions!" % (tmpFiles, tmpIOFiles, tmpPermissionsFiles), "Deleted Files Completed with IO & Permissions Error(s)" )
    else:
        scriptDialog.ShowMessageBox( "No \".tmp\" files were deleted!", "No files deleted" )
