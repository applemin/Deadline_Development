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
presetSettings = None
startup = True
updatingOutputFile = False
ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = True

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global presetSettings
    global startup
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Quicktime Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Quicktime' ) )
    
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
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Quicktime Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input Images", 1, 0, "The frames you would like to generate the Quicktime from. If a sequence of frames exist in the same folder, Deadline will automatically collect the range of the frames and will set the Frame Range accordingly. ", False )
    inputBox = scriptDialog.AddSelectionControlToGrid( "InputBox", "FileBrowserControl", "", "All Files (*)", 1, 1, colSpan=3 )
    inputBox.ValueModified.connect(InputImagesModified)

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Movie File", 2, 0, "The name of the Quicktime to be generated. ", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "", "All Files (*)", 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "StartFrameLabel", "LabelControl", "Start Frame", 3, 0, "The first frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "StartFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 1 )
    scriptDialog.AddControlToGrid( "EndFrameLabel", "LabelControl", "End Frame", 3, 2, "The last frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "EndFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 3 )

    scriptDialog.AddControlToGrid( "CodecLabel", "LabelControl", "Codec", 4, 0, "The codec format to use for the Quicktime. ", False )
    codecBox = scriptDialog.AddComboControlToGrid( "CodecBox", "ComboControl", "QuickTime Movie", ("3G","AVI","DV Stream","FLC","MPEG-4","QuickTime Movie"), 4, 1 )
    codecBox.ValueModified.connect(CodecChanged)
    scriptDialog.AddControlToGrid( "FrameRateLabel", "LabelControl", "Frame Rate", 4, 2, "The frame rate of the Quicktime. ", False )
    scriptDialog.AddRangeControlToGrid( "FrameRateBox", "RangeControl", 24.00, 0.01, 100.00, 2, 1.00, 4, 3 )

    scriptDialog.AddControlToGrid( "AudioLabel", "LabelControl", "Audio File (Optional)", 5, 0, "Specify an audio file to be added to the Quicktime movie. Leave blank to disable this feature. ", False )
    scriptDialog.AddSelectionControlToGrid( "AudioBox", "FileBrowserControl", "", "All Files (*)", 5, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "SettingsLabel", "LabelControl", "Settings File (Optional)", 6, 0, "The Quicktime settings file to use. If not specified here, you will be prompted to specify your settings after pressing the Submit button.", False )
    scriptDialog.AddSelectionControlToGrid( "SettingsBox", "FileBrowserControl", "", "All Files (*)", 6, 1, colSpan=3 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "QuicktimeMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    settingsButton = scriptDialog.AddControlToGrid( "SettingsButton", "ButtonControl", "Create Settings", 0, 0, "Create a new Quicktime settings file. ", False )
    settingsButton.ValueModified.connect(SettingsButtonPressed)
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 1 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 2, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 3, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ( "CategoryBox","DepartmentBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","LimitGroupBox","OnJobCompleteBox","MachineListBox","SubmitSuspendedBox","IsBlacklistBox","InputBox","FrameRateBox","AudioBox","CodecBox","SettingsBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    if len( args ) > 0:
        scriptDialog.SetValue( "InputBox", args[0] )
    
    InputImagesModified()
    CodecChanged()
    
    startup = False
    
    scriptDialog.ShowDialog( len( args ) > 0 )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "QuicktimeSettings.ini" )

def GetExtension():
    global scriptDialog
    
    codec = scriptDialog.GetValue( "CodecBox" )
    if codec == "3G":
        return ".3gp"
    elif codec == "AVI":
        return ".avi"
    elif codec == "DV Stream":
        return ".dv"
    elif codec == "FLC":
        return ".flc"
    elif codec == "MPEG-4":
        return ".mp4"
    elif codec == "QuickTime Movie":
        return ".mov"
    else:
        return ""

def InputImagesModified(*args):
    global startup
    global updatingOutputFile
    
    if not updatingOutputFile:
        success = False
        
        try:
            filename = scriptDialog.GetValue( "InputBox" )
            if filename != "":
                initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
                paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
                
                startFrame = 0
                endFrame = 0
                outputFilename = ""
                
                #if initFrame >= 0 and paddingSize > 0:
                if paddingSize > 0:
                    filename = FrameUtils.GetLowerFrameFilename( filename, initFrame, paddingSize )
                    
                    updatingOutputFile = True
                    scriptDialog.SetValue( "InputBox", filename )
                    updatingOutputFile = False
                    
                    startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
                    endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
                    outputFilename = Path.ChangeExtension( filename , GetExtension() )
                else:
                    outputFilename = Path.ChangeExtension( filename, GetExtension() )
                
                scriptDialog.SetValue( "StartFrameBox", startFrame )
                scriptDialog.SetValue( "EndFrameBox", endFrame )
                
                scriptDialog.SetValue( "OutputBox", outputFilename )
                scriptDialog.SetValue( "NameBox", Path.GetFileNameWithoutExtension( outputFilename ) )
                
                success = True
            
        except Exception as e:
            if not startup:
                scriptDialog.ShowMessageBox( e.Message, "Error Parsing Input Images" )
        
        if not success:
            scriptDialog.SetValue( "InputBox", "" )
            scriptDialog.SetValue( "StartFrameBox", 0 )
            scriptDialog.SetValue( "EndFrameBox", 0 )
            scriptDialog.SetValue( "OutputBox", "" )
            scriptDialog.SetValue( "NameBox", "Untitled" )

def CodecChanged(*args):
    global scriptDialog
    
    outputFilename = scriptDialog.GetValue( "OutputBox" )
    outputFilename = Path.ChangeExtension( outputFilename, GetExtension() )
    scriptDialog.SetValue( "OutputBox", outputFilename )

def SettingsButtonPressed(*args):
    global scriptDialog
    
    codec = scriptDialog.GetValue( "CodecBox" )
    settingsFile = Path.Combine( ClientUtils.GetDeadlineTempPath(), "temp_quicktime_export_settings.xml" )
    
    qtGenerator = Path.Combine( ClientUtils.GetBinDirectory(), "deadlinequicktimegenerator" )
    process = ProcessUtils.SpawnProcess( qtGenerator, "-ExportSettings \"" + settingsFile + "\" \"" + codec + "\"", ClientUtils.GetBinDirectory() )
    
    ProcessUtils.WaitForExit( process, -1 )
    exitCode = process.ExitCode
    if exitCode != 0 and exitCode != 128:
        #scriptDialog.ShowMessageBox( "Export settings could not be generated. Either the process was canceled, the selected codec isn't supported, the version of QuickTime installed on this machine isn't supported, or an error occurred.", "Error Generating Export Settings" )
        return
    
    newSettingsFile = scriptDialog.ShowSaveFileBrowser( "quicktime_export_settings.xml", "All Files (*)" )
    if newSettingsFile != None:
        File.Copy( settingsFile, newSettingsFile, True )
        scriptDialog.SetValue( "SettingsBox", newSettingsFile )

def GetSupportedFormats():
    formats = ( ".3gp",
                ".3g2",
                ".aiff",
                ".aif",
                ".au",
                ".snd",
                ".avi",
                ".bmp",
                ".dv",
                ".swf",
                ".gif",
                ".jpg",
                ".pnt",
                ".mid",
                ".mp3",
                ".mpu",
                ".mpeg",
                ".mpg",
                ".mp4",
                ".m4a",
                ".pct",
                ".psd",
                ".png",
                ".qtz",
                ".qtif",
                ".qif",
                ".qti",
                ".sgi",
                ".smi",
                ".tga",
                ".tiff",
                ".tif",
                ".wav",
                ".wmv")
    return formats

def IsFormatSupported( inputFile ):
    extension = Path.GetExtension( inputFile ).lower()
    supportedFormats = GetSupportedFormats()
    for format in supportedFormats:
        if extension == format.lower():
            return True
    return False

def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog

    # Check if input files exist.
    inputFile = scriptDialog.GetValue( "InputBox" ).strip()
    
    if(len(inputFile)==0):
        scriptDialog.ShowMessageBox("No input file specified","Error")
        return
        
    if( PathUtils.IsPathLocal( inputFile ) ):
        result = scriptDialog.ShowMessageBox( "The input file " + inputFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    if( not IsFormatSupported( inputFile ) ):
        scriptPath = RepositoryUtils.GetRepositoryFilePath( "scripts/Submission/QuicktimeSubmission.py", True )
        result = scriptDialog.ShowMessageBox( "The input file " + inputFile + " is not a supported format. If this format is supported by Quicktime, you can add its file extension to " + scriptPath + " to prevent this warning from appearing.\n\nDo you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    # Ensure the output file has the correct extension before the job is submitted.
    CodecChanged()
    
    # Check output file.
    outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
    if(len(outputFile)==0):
        scriptDialog.ShowMessageBox("No output file specified","Error")
        return
    if( not Directory.Exists( Path.GetDirectoryName( outputFile ) ) ):
        scriptDialog.ShowMessageBox( "Path for the output file " + outputFile + " does not exist.", "Error" )
        return
    elif( PathUtils.IsPathLocal( outputFile ) ):
        result = scriptDialog.ShowMessageBox( "The output file " + outputFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return

    # Check if Integration options are valid.
    if not integration_dialog.CheckIntegrationSanity( outputFile ):
        return
    
    codec = scriptDialog.GetValue( "CodecBox" )
    plugin = "Quicktime"
        
    # Check audio file.
    audioFile = scriptDialog.GetValue( "AudioBox" ).strip()
    if( len( audioFile ) > 0 ):
        if( not File.Exists( audioFile ) ):
            scriptDialog.ShowMessageBox( "The audio file " + audioFile + " does not exist.", "Error" )
            return
        elif( PathUtils.IsPathLocal( audioFile ) ):
            result = scriptDialog.ShowMessageBox( "The audio file " + audioFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
            if( result == "No" ):
                return
    
    # Check settings file.
    settingsFile = scriptDialog.GetValue( "SettingsBox" ).strip()
    if( len( settingsFile ) > 0 ):
        if( not File.Exists( settingsFile ) ):
            scriptDialog.ShowMessageBox( "The settings file " + settingsFile + " does not exist.", "Error" )
            return
    else:
        # Create new export settings if necessary.
        settingsFile = Path.Combine( ClientUtils.GetDeadlineTempPath(), "quicktime_export_settings.xml" )
        
        qtGenerator = Path.Combine( ClientUtils.GetBinDirectory(), "deadlinequicktimegenerator" )
        process = ProcessUtils.SpawnProcess( qtGenerator, "-ExportSettings \"" + settingsFile + "\" \"" + codec + "\""  )
        
        ProcessUtils.WaitForExit( process, -1 )
        exitCode = process.ExitCode
        if exitCode != 0 and exitCode != 128:
            scriptDialog.ShowMessageBox( "Export settings could not be generated. Either the process was canceled, the selected codec isn't supported, the version of QuickTime installed on this machine isn't supported, or an error occurred.", "Error Generating Export Settings" )
            return
        
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "quicktime_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=%s" % plugin )
    writer.WriteLine( "Name=%s" % jobName )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "MachineLimit=1" )
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
    
    writer.WriteLine( "Frames=%s-%s" % (scriptDialog.GetValue( "StartFrameBox" ), scriptDialog.GetValue( "EndFrameBox")) )
    writer.WriteLine( "ChunkSize=100000" )
    writer.WriteLine( "OutputFilename0=%s" % outputFile )
    
    # Integration
    extraKVPIndex = 0
    groupBatch = False

    if integration_dialog.IntegrationProcessingRequested():
        extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
        groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

    if groupBatch:
        writer.WriteLine( "BatchName=%s\n" % ( jobName ) ) 
    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "quicktime_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    writer.WriteLine( "InputImages=%s" % inputFile )
    writer.WriteLine( "OutputFile=%s" % outputFile )
    writer.WriteLine( "FrameRate=%s" % scriptDialog.GetValue( "FrameRateBox" ) )
    
    # Apple specific options
    writer.WriteLine( "Codec=%s" % codec )
    writer.WriteLine( "AudioFile=%s" % audioFile )
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    arguments.Add( settingsFile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
