import clr
import sys

from System.Diagnostics import *
from System.IO import *
from System.Text.RegularExpressions import *

from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog
from Deadline.Jobs import *

def __main__():	
	global settings
	
	folders = []
	scriptDialog = DeadlineScriptDialog()
	dialogString = ""
	altRe = Regex( r"\.?_alt_[0-9]+" )
	
	for job in MonitorUtils.GetSelectedJobs():		
		for outputDir in job.JobOutputDirectories:
			if outputDir != "":
				if(folders.count(outputDir) == 0):
					folders.append( outputDir )
					dialogString += outputDir + "\n"
	
	# see if we can grab any output folder for this job
	if( len(folders) == 0 ):
		scriptDialog.ShowMessageBox( "Cannot locate the Output Folder(s) for the selected job(s)!", "No Output Folders Specified" )
		return
	
	result = scriptDialog.ShowMessageBox( "This will find and rename files ending in \"_alt_#\" in the following folder(s):\n\n%s\nContinue?" % dialogString, "Rename Alt Files?", ("Yes","No") )
	if( result == "No" ):
		return
	
	dialogString = ""
	altFiles = 0
	overwriteAll = 0
	skipAll = 0
		
	for folder in folders:
		
		files = Directory.GetFiles( folder )
		
		for file in files:
			newFileName = altRe.Replace( file, "" )
			
			if newFileName != file:
				
				if File.Exists (newFileName):
					
					if not overwriteAll and not skipAll:
						result = scriptDialog.ShowMessageBox( "A file named \"%s\" already exists! Renaming the alt file will overwrite it." % newFileName, "Warning", ("Overwrite","Skip","Overwrite All","Skip All") )
						if( result == "Skip" ):
							continue
						elif result == "Skip All":
							skipAll = 1
							continue
						elif result == "Overwrite All":
							overwriteAll = 1
					elif skipAll:
						continue
				
					File.Delete (newFileName)
					
				
				dialogString =  dialogString + file + "\n"
				altFiles += 1
				
				File.Move(file, newFileName)
			
	if altFiles > 0:
		
		if(altFiles < 50) :
			scriptDialog.ShowMessageBox( "The following %d files were renamed:\n\n%s" % (altFiles, dialogString), "Renamed Files" )
		else :
			scriptDialog.ShowMessageBox( "%d alt files were found and renamed!" % altFiles, "Renamed Files" )
	else:
		scriptDialog.ShowMessageBox( "No files were renamed!", "No files renamed" )

def CloseDialog():
	global scriptDialog	
	scriptDialog.CloseDialog()
	
def CloseButtonPressed(*args):
	CloseDialog()
	
def SubmitButtonPressed(*args):
	
	altRe = Regex( r"\.?_alt_[0-9]+" )
	
	files = Directory.GetFiles( scriptDialog.GetValue( "DirectoryBox" ) )
	
	dialogString = ""
	altFiles = 0
	overwriteAll = 0
	skipAll = 0
	
	for file in files:
		newFileName = altRe.Replace( file, "" )
		
		if newFileName != file:
			
			if File.Exists (newFileName):
				
				if not overwriteAll and not skipAll:
					result = scriptDialog.ShowMessageBox( "A file named \"%s\" already exists! Renaming the alt file will overwrite it." % file, "Warning", ("Overwrite","Skip","Overwrite All","Skip All") )
					if( result == "Skip" ):
						continue
					elif result == "Skip All":
						skipAll = 1
						continue
					elif result == "Overwrite All":
						overwriteAll = 1
				elif skipAll:
					continue
			
				File.Delete (newFileName)
				
			
			dialogString =  dialogString + file + "\n"
			altFiles += 1
			
			File.Move(file, newFileName)
			
	if altFiles > 0:
		scriptDialog.ShowMessageBox( "The following %d files were renamed:\n\n%s" % (altFiles, dialogString), "Renamed Files" )
	else:
		scriptDialog.ShowMessageBox( "No files were renamed!", "No files renamed" )
	
