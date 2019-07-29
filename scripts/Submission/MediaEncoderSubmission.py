import clr

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *
from Deadline.Plugins import *

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
ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = False

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog

    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Setup Adobe Media Encoder With Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'MediaEncoder' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
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
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
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
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Media Encoder Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "DirFileChooserLabel", "LabelControl", "Selection Method", 1, 0, "Choose the selection method by file or by directory.", False )
    DirFileChooserRC1 = scriptDialog.AddRadioControlToGrid( "DirChooser", "RadioControl", False, "Select by Directory", "SelectMethodRadioCtrl", 1, 1, "Choose a root directory to scan for all supported files." )
    DirFileChooserRC1.ValueModified.connect(DirFileChooserChanged)
    DirFileChooserRC2 = scriptDialog.AddRadioControlToGrid( "FileChooser", "RadioControl", True, "Select by File", "SelectMethodRadioCtrl", 1, 2, "Choose by individual file selection." )
    DirFileChooserRC2.ValueModified.connect(DirFileChooserChanged)

    scriptDialog.AddControlToGrid( "FileExtLabel", "LabelControl", "File Extension(s)", 2, 0, "A comma separated list of file extension(s) to search for supported file formats for batch submission, ie: aepx,mov,mp4. Image file sequences are NOT supported.", False )
    scriptDialog.AddControlToGrid( "FileExtBox", "TextControl", "mov,mp4,aep,aepx,prproj", 2, 1 )
    scriptDialog.SetEnabled( "FileExtLabel", False )
    scriptDialog.SetEnabled( "FileExtBox", False )

    scriptDialog.AddSelectionControlToGrid( "SubDirectoriesBox", "CheckBoxControl", True, "Process Sub-Directories", 2, 2, "Optionally choose to scan sub-directories as well for supported files." )
    scriptDialog.SetEnabled( "SubDirectoriesBox", False )

    scriptDialog.AddControlToGrid( "AmeInputDirectoryLabel", "LabelControl", "Input Directory", 3, 0, "Choose a root directory to scan for all supported video files.", False )
    scriptDialog.AddSelectionControlToGrid( "AmeInputDirectoryBox", "FolderBrowserControl", "", "", 3, 1, colSpan=2 )
    scriptDialog.SetEnabled( "AmeInputDirectoryLabel", False )
    scriptDialog.SetEnabled( "AmeInputDirectoryBox", False )

    scriptDialog.AddControlToGrid( "AmeOutputDirectoryLabel", "LabelControl", "Output Directory", 4, 0, "Choose a root directory to output the generated media file(s).", False )
    scriptDialog.AddSelectionControlToGrid( "AmeOutputDirectoryBox", "FolderBrowserControl", "", "", 4, 1, colSpan=2 )
    scriptDialog.SetEnabled( "AmeOutputDirectoryLabel", False )
    scriptDialog.SetEnabled( "AmeOutputDirectoryBox", False )

    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input File", 5, 0, "The path to the media file to be encoded. This can be any video file format supported by AME.", False )
    scriptDialog.AddSelectionControlToGrid( "InputBox", "FileBrowserControl", "", "All Files (*)", 5, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output File", 6, 0, "The name of the media file to be generated.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "", "All Files (*)", 6, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "PresetLabel", "LabelControl", "Preset File", 7, 0, "The preset file to use. This file determines what to do with the input, and can be exported from Media Encoder presets.", False )
    scriptDialog.AddSelectionControlToGrid( "PresetBox", "FileBrowserControl", "", "AME Preset File (*.epr)", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 8, 0 , "The version of Media Encoder to encode with.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "CC2017", ("CC2014","CC2015","CC2017","CC2018"), 8, 1 )

    scriptDialog.AddSelectionControlToGrid( "OverwriteCheckBox", "CheckBoxControl", True, "Overwrite Output If Present", 9, 1, "If enabled, AME will overwrite any file located at the output location with the new output." )
    scriptDialog.AddSelectionControlToGrid( "SubmitEPRCheckBox", "CheckBoxControl", False, "Submit Preset File With Job", 9, 2, "If enabled, the preset file will be uploaded to the Deadline Repository along with the Job (useful if your .epr file is local)." )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "MediaEncoderMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 2, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 3, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ( "CategoryBox","DepartmentBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","LimitGroupBox","OnJobCompleteBox","MachineListBox","SubmitSuspendedBox","IsBlacklistBox","VersionBox","FileExtBox","AmeInputDirectoryBox","AmeOutputDirectoryBox","InputBox","OutputBox","PresetBox","OverwriteCheckBox","SubmitEPRCheckBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    if len( args ) > 0:
        scriptDialog.SetValue( "InputBox", args[0] )

    scriptDialog.ShowDialog( False )    

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "MediaEncoderSettings.ini" )

def DirFileChooserChanged( *args ):
    global scriptDialog
    dirSelect = scriptDialog.GetValue( "DirChooser" )
    fileSelect = scriptDialog.GetValue( "FileChooser" )

    scriptDialog.SetEnabled( "SubDirectoriesBox", dirSelect )
    scriptDialog.SetEnabled( "AmeInputDirectoryLabel", dirSelect )
    scriptDialog.SetEnabled( "AmeInputDirectoryBox", dirSelect )
    scriptDialog.SetEnabled( "AmeOutputDirectoryLabel", dirSelect )
    scriptDialog.SetEnabled( "AmeOutputDirectoryBox", dirSelect )
    scriptDialog.SetEnabled( "FileExtLabel", dirSelect )
    scriptDialog.SetEnabled( "FileExtBox", dirSelect )
    
    scriptDialog.SetEnabled( "InputLabel", fileSelect )
    scriptDialog.SetEnabled( "InputBox", fileSelect )
    scriptDialog.SetEnabled( "OutputLabel", fileSelect )
    scriptDialog.SetEnabled( "OutputBox", fileSelect )

def GetVersionNumber():
    global scriptDialog
    
    versionStr = scriptDialog.GetValue( "VersionBox" )
    
    if versionStr == "CC2014":
        return 13.0
    elif versionStr == "CC2015":
        return 13.5
    elif versionStr == "CC2017":
        return 14.0
    elif versionStr == "CC2018":
        return 15.0
    else:
        return float(versionStr)

def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog

    inputFiles = []
    warnings = []
    errors = []

    fileSelect = scriptDialog.GetValue( "FileChooser" )
    dirSelect = scriptDialog.GetValue( "DirChooser" )

    if fileSelect:
        inputFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "InputBox" ), False )
    elif dirSelect:
        extensions = ( scriptDialog.GetValue( "FileExtBox" ) )
        
        if extensions == "":
            scriptDialog.ShowMessageBox( "No file extension was specified!", "Error" )
            return
        else:
            extensions = tuple( extensions.rstrip( "," ).split( "," ) )

        rootDir = scriptDialog.GetValue( "AmeInputDirectoryBox" )

        if scriptDialog.GetValue( "SubDirectoriesBox" ):
            for root, dirnames, filenames in os.walk(rootDir):
                for filename in filenames:
                    if filename.endswith(extensions):
                        inputFiles.append(os.path.join(root, filename))
        else:
            for filename in os.listdir(rootDir):
                if filename.endswith(extensions):
                    inputFiles.append(os.path.join(rootDir, filename))

    if len( inputFiles ) == 0:
        errors.append( "No input file(s) specified!" )

    for inputFile in inputFiles:
        if PathUtils.IsPathLocal( inputFile ):
            warnings.append( "The provided input (" + inputFile + ") is on a local drive, are you sure you want to continue?" )

    # Check output file/dir.
    if fileSelect:
        output = scriptDialog.GetValue( "OutputBox" ).strip()
    else:
        output = scriptDialog.GetValue( "AmeOutputDirectoryBox" ).strip()

    if len( output ) == 0:
        errors.append( "No output specified!" )
    elif not Directory.Exists( Path.GetDirectoryName( output ) ):
        errors.append( "Path for the output " + output + " does not exist." )
    elif PathUtils.IsPathLocal( output ):
        warnings.append( "The output " + output + " is local, are you sure you want to continue?" )

    # Check preset file.
    presetFile = scriptDialog.GetValue( "PresetBox" ).strip()
    submitPresetFile = scriptDialog.GetValue( "SubmitEPRCheckBox" )
    
    if len( presetFile ) == 0:
        errors.append( "No preset file specified!" )
    elif( not File.Exists( presetFile ) ):
        errors.append( "The preset file " + presetFile + " does not exist." )
    elif( not presetFile.lower().endswith( ".epr" ) ):
        errors.append( "This preset file does not have the extension .epr to be an AME preset file." )
    elif not submitPresetFile and PathUtils.IsPathLocal( presetFile ):
        warnings.append( "The preset file " + presetFile + " is local and it is not being submitted with the job, are you sure you want to continue?" )

    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity():
        return

    if len( errors ) > 0:
        scriptDialog.ShowMessageBox( "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % ( "\n".join( errors ) ), "Errors" )
        return

    if len( warnings ) > 0:
        result = scriptDialog.ShowMessageBox( "Warnings:\n\n%s\n\nDo you still want to continue?" % ( "\n".join( warnings ) ), "Warnings", ( "Yes","No" ) )
        if result == "No":
            return

    successes = 0
    failures = 0

    for inputFile in inputFiles:
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "mediaencoder_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=MediaEncoder" )

        jobName = scriptDialog.GetValue( "NameBox" ) + " [%s]" % os.path.basename( inputFile )
        writer.WriteLine( "Name=%s" % jobName )
        
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
        
        if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        writer.WriteLine( "Frames=0" )
        writer.WriteLine( "ChunkSize=10000" )

        if fileSelect and os.path.isfile( output ):
            writer.WriteLine( "OutputFilename0=%s" % output )
        else:
            writer.WriteLine( "OutputDirectory0=%s" % output )
        
        # Integration
        extraKVPIndex = 0
        groupBatch = False

        if integration_dialog.IntegrationProcessingRequested():
            extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

        if groupBatch:
            writer.WriteLine( "BatchName=%s" % ( scriptDialog.GetValue( "NameBox" ) ) ) 
        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "mediaencoder_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
        version = GetVersionNumber()
        writer.WriteLine( "Version=%s" % str(version) )

        writer.WriteLine( "InputPath=%s" % inputFile )
        
        if fileSelect:
            writer.WriteLine( "OutputPath=%s" % output )
        else:
            outputPath = os.path.join( output, os.path.splitext( os.path.basename ( inputFile ) )[0] )
            writer.WriteLine( "OutputPath=%s" % outputPath )

        writer.WriteLine( "OverwriteOutput=%s" % scriptDialog.GetValue( "OverwriteCheckBox" ) )

        submittingEPR = bool( scriptDialog.GetValue( "SubmitEPRCheckBox" ) )

        if not submittingEPR:
            writer.WriteLine( "PresetFile=%s" % presetFile )
        writer.Close()
        
        # Setup the command line arguments.
        arguments = StringCollection()
        
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )

        if submittingEPR:
            arguments.Add( presetFile )

        # Now submit the job.
        if( len( inputFiles ) == 1 ):
            results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
            scriptDialog.ShowMessageBox( results, "Submission Results" )
        else:
            exitCode = ClientUtils.ExecuteCommand( arguments )
            if( exitCode == 0 ):
                successes = successes + 1
            else:
                failures = failures + 1
        
    if( len( inputFiles ) > 1 ):
        scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % ( successes, failures ), "Submission Results" )
