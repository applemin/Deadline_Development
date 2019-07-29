import re
import sys
import os
import mimetypes
import traceback
import glob

from System import Array
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.Diagnostics import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

import imp
imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

########################################################################
## Globals
########################################################################
scriptDialog = None
integration_dialog = None
settings = None

shotgunSettings = {}
versionID = None
deadlineJobID = None


startup = True
updatingInputFile = False

#get the path to the Shotgun events folder, and import the ShotgunUtils module
shotgunPath = RepositoryUtils.GetEventPluginDirectory("Shotgun")
sys.path.append( shotgunPath )
import ShotgunUtils

def CreateDraftScriptDialog():
    global scriptDialog
    global ProjectManagementOptions
    global integration_dialog

    global settings
    global shotgunPath
    global startup
    global versionID
    global deadlineJobID
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Draft Script To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'DraftPlugin' ) )

    scriptDialog.AddTabControl( "Tabs", 0, 0 )
    
    scriptDialog.AddTabPage( "Job Options" )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "JobOptionsSeparator", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

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
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1, expand=False )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 5, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 6, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 6, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 7, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 8, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 9, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 9, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 9, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "DraftOptionsSeparator", "SeparatorControl", "Draft Options", 0, 0, colSpan=6 )

    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input File", 2, 0, "The input file(s) on which to apply the Draft script.", False )
    inputBox = scriptDialog.AddSelectionControlToGrid( "InputBox", "MultiFileBrowserControl", "", "All Files (*)", 2, 1, colSpan=5 )
    inputBox.ValueModified.connect( InputImagesModified )

    scriptDialog.AddControlToGrid( "OutputDirectoryLabel", "LabelControl", "Output Folder Name", 3, 0, "The output folder in which the Draft script should put output files.  Can be absolute, or relative to input folder.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputDirectoryBox", "FolderBrowserControl", "Draft", "", 3, 1, colSpan=5 )

    scriptDialog.AddControlToGrid( "OutputFileLabel", "LabelControl", "Output File Name", 4, 0, "The name that the script should use for the output file(s).", False )
    outputFileBox = scriptDialog.AddControlToGrid( "OutputFileBox", "TextControl", "", 4, 1, colSpan=5 )
    outputFileBox.ValueModified.connect( OutputFileBoxModified )

    scriptDialog.AddControlToGrid( "FrameListLabel", "LabelControl", "Frame List", 5, 0, "The list of Frames that should be processed by the script.", False )
    scriptDialog.AddControlToGrid( "FrameListBox", "TextControl", "", 5, 1, colSpan=5 )

    distributedJob = scriptDialog.AddSelectionControlToGrid( "DraftDistributedJobBox", "CheckBoxControl", False, "Distributed Job", 6, 0, "Specify if the job will be distributed. If enabled, custom scripts must work with taskStartFrame and taskEndFrame.", expand=False )
    distributedJob.ValueModified.connect( AdjustDistributedJobEnabled )

    scriptDialog.AddControlToGrid( "DraftNumberOfFramesLabel", "LabelControl", "Frames Per Task", 6, 1, "The number of frames, or chunk size, to be assigned to each task.", False )
    scriptDialog.AddRangeControlToGrid( "DraftNumberOfFramesBox", "RangeControl", 200, 0, 9999, 0, 1, 6, 2, expand=False )

    scriptDialog.AddControlToGrid( "DraftMachineLimitLabel", "LabelControl", "Machine Limit", 6, 3, "The maximum number of machines that can process a distributed job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "DraftMachineLimitBox", "RangeControl", 5, 0, 9999, 0, 1, 6, 4, expand=False )

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    firstFrameFile = GetFirstFrameFile()
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "DraftMonitor", addDraftTab = True, projectManagements = ["Shotgun","FTrack"], fromDraftSubmitterFlag = True, firstFrameFile = firstFrameFile )
    integration_dialog.Draft_dialog.draftQuickRadio.ValueModified.connect(InputImagesModified)
    integration_dialog.Draft_dialog.draftCustomRadio.ValueModified.connect(InputImagesModified)
    integration_dialog.Draft_dialog.draftFormatBox.ValueModified.connect(InputImagesModified)
    
    scriptDialog.EndTabControl()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer2", 0, 0 )

    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    
    scriptDialog.EndGrid()
    
    #Load sticky settings
    settings = ("DepartmentBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","IsBlacklistBox","MachineListBox","LimitGroupBox","DraftTemplateBox","InputBox","OutputDirectoryBox","OutputFileBox","FrameListBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
        
    return scriptDialog

#This functions fills in default values based on the selected job
def LoadDefaults():
    global versionID
    global integration_dialog
    
    job = MonitorUtils.GetSelectedJobs()[0]
    settingsDict = {}
    #check for shotgun
    if job.GetJobExtraInfoKeyValue( 'VersionId' ) != "" and job.ExtraInfo5 != "":
        versionID = job.GetJobExtraInfoKeyValue( 'VersionId' )
        settingsDict["EntityName"] = job.ExtraInfo2
        settingsDict["VersionName"] = job.ExtraInfo3
        settingsDict["UserName"] = job.ExtraInfo5        
    else: 
        versionID = None
        settingsDict["UserName"] = job.UserName
        settingsDict["EntityName"] = job.Name
    integration_dialog.PopulateCustomDraftFields( "Shotgun", settingsDict )
    
    inputFile = ""
    outputDir = ""
    outputFile = ""
    if len(job.OutputDirectories) > 0:
        inputFile = job.OutputDirectories[0]
        inputFile = RepositoryUtils.CheckPathMapping( inputFile, False )
        inputFile = PathUtils.ToPlatformIndependentPath( inputFile )
        
        outputDir = os.path.join( inputFile, "Draft" )
        
        if len(job.OutputFileNames) > 0:
            inputFile = os.path.join( inputFile, job.OutputFileNames[0] )
            inputFile = re.sub( "\?", "#", inputFile )
            
            (tempFileName, oldExt) = os.path.splitext( job.OutputFileNames[0] )
            tempFileName = re.sub( "[\?#]", "", tempFileName ).rstrip( "_.- " )
            outputFile = tempFileName + ".mov"
    
    scriptDialog.SetValue( 'InputBox', inputFile )
    scriptDialog.SetValue( 'OutputDirectoryBox', outputDir )
    scriptDialog.SetValue( 'OutputFileBox', outputFile )
    
    scriptDialog.SetValue( 'DependencyBox', job.JobId )
    frameList = FrameUtils.ToFrameString( job.Frames )
    scriptDialog.SetValue( 'FrameListBox', frameList )
    scriptDialog.SetValue( 'NameBox', job.Name + " [DRAFT]" )

def GetFirstFrameFile():
    firstFrameFile = ""

    if len( MonitorUtils.GetSelectedJobs() ) > 0:
        job = MonitorUtils.GetSelectedJobs()[0]
        inputFile = ""

        if len(job.OutputDirectories) > 0:
            inputFile = job.OutputDirectories[0]
            inputFile = RepositoryUtils.CheckPathMapping( inputFile, False )
            inputFile = PathUtils.ToPlatformIndependentPath( inputFile )
                        
            if len(job.OutputFileNames) > 0:
                inputFile = os.path.join( inputFile, job.OutputFileNames[0] )
                inputFile = re.sub( "\?", "#", inputFile )
        
        firstFrameFile = FrameUtils.ReplacePaddingWithFrameNumber( inputFile, job.Frames[0] )

    return firstFrameFile

def AdjustDistributedJobEnabled( *args ):
    global scriptDialog

    distributedJobEnabled = scriptDialog.GetValue( "DraftDistributedJobBox" )
    scriptDialog.SetEnabled( "DraftNumberOfFramesLabel", distributedJobEnabled )
    scriptDialog.SetEnabled( "DraftNumberOfFramesBox", distributedJobEnabled )
    scriptDialog.SetEnabled( "DraftMachineLimitLabel", distributedJobEnabled )
    scriptDialog.SetEnabled( "DraftMachineLimitBox", distributedJobEnabled )

def InputImagesModified( *args ):
    global scriptDialog
    global integration_dialog
    global startup

    try:
        fileNames = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "InputBox" ) )

        if ( len( fileNames ) == 1 ):
            #only one file, behave as before
            scriptDialog.SetEnabled( "OutputFileLabel", True )
            scriptDialog.SetEnabled( "OutputFileBox", True )
            scriptDialog.SetEnabled( "FrameListBox", True )
            scriptDialog.SetEnabled( "FrameListLabel", True )
            
            #Get the frame range and padding from the file
            fileName = fileNames[0].strip()
            (paddedName, frameString) = ParseFrameStringFromFile( fileName )
            scriptDialog.SetValue( "InputBox",  paddedName )
            scriptDialog.SetValue( "FrameListBox", frameString )

            outputFileName = integration_dialog.Draft_dialog.GetValidDraftOutputFilename( paddedName )
            scriptDialog.SetValue( "OutputFileBox", outputFileName )
                      
        elif ( len( fileNames ) > 1 ):
            #several files were specified; clear out frames/output file name
            scriptDialog.SetEnabled( "OutputFileLabel", False )
            scriptDialog.SetEnabled( "OutputFileBox", False )
            scriptDialog.SetValue( "OutputFileBox", "" )
            scriptDialog.SetEnabled( "FrameListBox", False )
            scriptDialog.SetEnabled( "FrameListLabel", False )
            scriptDialog.SetValue( "FrameListBox", "" )
    except:
        pass
            
def ParseFrameStringFromFile( inFile ):
    if inFile != None and inFile != "":
        inFile.strip()
        (mimeType, _) = mimetypes.guess_type( inFile )
        
        if mimeType != None and mimeType.startswith( 'video' ):
            #file seems to be a video, don't bother looking for padding
            return ( inFile, "" )
        else:
            #Assume it's an image sequence
            (dirName, fileName) = os.path.split( inFile )

            #Nuke can use python formatting for padding
            try:
                #try doing pythony formatting to the string
                fileName = fileName % 1
            except:
                pass
            
            #Look for a string of digits
            regexObj = re.compile( r"[\d#\?]+" )
            matchObj = regexObj.search( fileName )
            
            matches = []
            while not matchObj == None:
                #insert at beginning of list to reverse matches
                matches.insert( 0, matchObj )
                matchObj = regexObj.search( fileName, matchObj.end() )
            
            while len(matches) > 0:
                #pop the first match from the list
                matchObj = matches.pop( 0 )
                start = matchObj.start()
                end = matchObj.end()
                
                #translate the match to a file filter, and get a list of files matching that filter
                fileFilter = fileName[:start] + ("[0-9]" * (end - start)) + fileName[end:]
                fileFilter = os.path.join( dirName, fileFilter )
                seqMatches = glob.glob( fileFilter )
                
                #check our match count (if == 1, then this isn't a sequence number)
                if len(seqMatches) > 1:
                    #I don't think this is guaranteed to already be sorted, so sort it now
                    seqMatches.sort()
                    
                    paddedFile = fileName[:start] + ("#" * (end - start)) + fileName[end:]
                    offset = len( seqMatches[0] ) - len( paddedFile )
                    start += offset
                    end += offset
                    
                    return (os.path.join( dirName, paddedFile ), str(int(seqMatches[0][start:end])) + "-" + str(int(seqMatches[-1][start:end])))
                
                
    return ( inFile, "" ) # no sequence found

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "DraftSettings.ini" )

def OutputFileBoxModified():
    global integration_dialog
    global scriptDialog

    integration_dialog.Draft_dialog.UpdateOutputPaddingSize( scriptDialog.GetValue( "OutputFileBox" ) )

def SubmitDraftJob( inputFile, outputfile, frameString, draftScript, oneOfMany, isDistributed=False, dependencies=None, quickType="" ):
    global scriptDialog
    global shotgunSettings
    global versionID
    global integration_dialog
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "draft_job_info.job" )
    
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    try:
        writer.WriteLine( "Plugin=DraftPlugin" )
        if oneOfMany:
            writer.WriteLine( "Name=%s [%s]" % (scriptDialog.GetValue( "NameBox" ), os.path.basename( inputFile )) )
        else:
            writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
            
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )

        if dependencies:
            writer.WriteLine( "JobDependencies=%s" % dependencies )
        else:
            writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )

        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        #Assume it's a quicktime and set a huge chunk size
        writer.WriteLine( "Frames=" + frameString )

        if isDistributed:
            writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "DraftNumberOfFramesBox" ) )
            writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "DraftMachineLimitBox" ) )
        else:
            #Assume it's a quicktime and set a huge chunk size
            writer.WriteLine( "ChunkSize=1000000" )
            writer.WriteLine( "MachineLimit=1" )

        writer.WriteLine( "OutputFilename0=%s\n" % outputfile )
        
        if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            
        if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
            writer.WriteLine( "InitialStatus=Suspended" )

        if integration_dialog.UploadDraftMovieRequested():
            integration_dialog.WriteProjectManagementInfo( writer, 0 )

    finally:
        writer.Close()
        
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "draft_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

    isQuickDraft = integration_dialog.Draft_dialog.GetValue( "DraftQuickRadio" )
    try:
        if not isQuickDraft:
            writer.WriteLine( "scriptFile=%s" % draftScript )

        if quickType == "concatenateMovie":
            args = ['quickType="concatenateMovies" ']
        else:
            # Get argument from DraftUI
            args = integration_dialog.Draft_dialog.GetDraftScriptArguments()
        
        args.append( 'isDistributed="%s" ' % isDistributed )
        
        frames = FrameUtils.Parse( frameString )
        args.append( 'frameList=%s ' % frameString )
        
        if frames != None and len(frames) > 0:
            args.append( 'startFrame=%s ' % str(frames[0]) )
            args.append( 'endFrame=%s ' % str(frames[-1]) )
        
        args.append( 'outFolder="%s" ' % os.path.dirname( outputfile ) )
        args.append( 'outFile="%s" ' % outputfile )
        args.append( 'inFile="%s" ' % inputFile )
        
        if deadlineJobID != None:
            args.append( 'deadlineJobID="%s"' % deadlineJobID )
        
        #write out the params to the plugin info file
        i = 0
        for scriptArg in args:
            writer.WriteLine( "ScriptArg%d=%s" % ( i, scriptArg ) )
            i += 1
    finally:
        writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    if isQuickDraft:
        arguments.Add( draftScript )

    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )

    if not oneOfMany and quickType != "concatenateMovie" :
        scriptDialog.ShowMessageBox( results, "Submission Results" )

    resultArray = results.split()
    jobId = ""
    for line in resultArray:
        if line.startswith("JobID="):
            jobId = line.replace("JobID=","")
        if line.startswith("Result="):
            result = line.replace("Result=","")   
    return ( result == "Success", jobId )
        
def SubmitButtonPressed(*args):
    global scriptDialog
    global versionID
    global deadlineJobID
    global integration_dialog

    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity():
        return

    draftScript = integration_dialog.Draft_dialog.GetDraftScript()
    if draftScript == "":
        return

    #Check for input
    inFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "InputBox" ) )
    if len( inFiles ) > 0:
        for i in range( 0, len( inFiles ) ):
            if PathUtils.IsPathLocal( inFiles[i] ):
                result = scriptDialog.ShowMessageBox( "One or more of the selected input files are local. Are you sure you want to continue?", "Warning", ("Yes","No") )
                
                if result == "No":
                    return
                else:
                    break
    else:
        result = scriptDialog.ShowMessageBox( "No input was selected; please select at least one input file.", "Error" )
    
    #Check if the output is rooted or relative
    outputDirectory = scriptDialog.GetValue( "OutputDirectoryBox" ).strip()
    
    #Check if output directory exists
    if PathUtils.IsPathRooted( outputDirectory ) and not Directory.Exists( outputDirectory ):
        result = scriptDialog.ShowMessageBox( "The output directory '%s' does not exist.\n\nDo you wish to create this directory now?" % outputDirectory, "Warning", ("Yes","No") )
        if result == "Yes":
            Directory.CreateDirectory( outputDirectory )
    
    sequences = {} #use a dict to only track unique sequences
    for i in range( 0, len( inFiles ) ):
        #some apps use '?' instead of '#' to mark frame padding
        inFile = re.sub( "\?", "#", inFiles[i] )
        
        paddedFile, frameString = ParseFrameStringFromFile( inFile )
        sequences[paddedFile] = frameString
        
    successful = 0
    failed = 0
    promptforDirCreation = True
    createOutputDirs = False
    for inFile in sequences:
        outputDirectory = scriptDialog.GetValue( "OutputDirectoryBox" ).strip()
        
        if not PathUtils.IsPathRooted( outputDirectory ):
            inputDir = os.path.dirname( inFile )
            outputDirectory = os.path.join( inputDir, outputDirectory )
            
            if not Directory.Exists( outputDirectory ):
                #Ask user whether or not output directories should be created
                if promptforDirCreation:
                    result = scriptDialog.ShowMessageBox( "One or more of the output directories do not exist.\n\nDo you wish to create missing directories now?", "Warning", ("Yes","No") )
                    promptforDirCreation = False
                    
                    if result == "Yes":
                        createOutputDirs = True
                        
                #Create missing directory
                if createOutputDirs:
                    Directory.CreateDirectory( outputDirectory )
        
        if scriptDialog.GetValue( "OutputFileBox" ) != "":
            basename = scriptDialog.GetValue( "OutputFileBox" )
        else:
            # Create the pattern for the output files from the directory path joined with the file name pattern.
            basename = os.path.basename( inFile )

        if integration_dialog.Draft_dialog.GetValue( "DraftQuickRadio" ):
            basename = integration_dialog.Draft_dialog.GetValidDraftOutputFilename( basename )

        outFile = os.path.join( outputDirectory, basename )
        frameString = scriptDialog.GetValue( "FrameListBox" ).strip()

        if frameString == "":
            frameString = sequences[inFile]
            
        totalNumFrames = len( FrameUtils.Parse( frameString ) )
        chunkSize = scriptDialog.GetValue( "DraftNumberOfFramesBox" )
        isMovieFormat = integration_dialog.Draft_dialog.IsMovieFromFormat( integration_dialog.Draft_dialog.GetValue( "DraftFormatBox" ) )
        quickType = "createMovie" if isMovieFormat else "createImages"
        isDistributed = scriptDialog.GetValue( "DraftDistributedJobBox" ) and totalNumFrames > chunkSize
        
        if quickType == "createMovie" and isDistributed:
            tempFile = os.path.join( outputDirectory, os.path.splitext( basename )[0] + "_movie_chunk_." + integration_dialog.Draft_dialog.GetQuickDraftExtension() )
            success, jobId = SubmitDraftJob( inFile, tempFile, frameString, draftScript, len( sequences ) > 1, isDistributed, quickType=quickType )
            success, jobId = SubmitDraftJob( inFile, outFile, frameString, draftScript, len( sequences ) > 1, isDistributed=False, dependencies=jobId, quickType="concatenateMovie" )
        else:
            success, jobId = SubmitDraftJob( inFile, outFile, frameString, draftScript, len( sequences ) > 1, isDistributed, quickType = quickType )

        if success:
            successful += 1
        else:
            failed += 1

    if successful + failed > 1:
        scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successful, failed), "Submission Results" )
