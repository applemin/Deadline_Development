from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

import argparse
import io
import json
import os
import re
import sys
import traceback

# For Integration UI
import imp
imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None

ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = False
OutputFiles = []

#a single regex that can be used to pull the render range out of a line from a fusion comp file as long as it is at the start of a line (default behavior)
renderRangeRE = re.compile(r"RenderRange\s*=\s*{(\s*(-?\d+),\s*(-?\d+),?\s*})?")

########################################################################
## Command-line argument parsing
########################################################################

class FusionSubmissionArgumentParser(argparse.ArgumentParser):
    # We overload the exit and error methods of the ArgumentParser because
    # they output to stderr which causes an IO error when run from Fusion.
    # Instead, we output to stdout.

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stdout)
        sys.exit(status)

    def error(self, message):
        
        from gettext import gettext
        self.print_usage(sys.stdout)
        args = {'prog': self.prog, 'message': message}
        self.exit(2, gettext('%(prog)s: error: %(message)s\n') % args)

def parse_args( args ):
    argParser = FusionSubmissionArgumentParser()
    argParser.add_argument( "sceneFile", nargs="*", default=[] )
    argParser.add_argument( "--name" )
    argParser.add_argument( "--frames" )
    argParser.add_argument( "--fusion-version", type=float )
    argParser.add_argument( "--settings", nargs="?" )
    argParser.add_argument( "--output", action='append', default=[] )

    return argParser.parse_args( args )

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    global OutputFiles

    parsedArgs = parse_args( args )

    DraftRequested = len(parsedArgs.output) > 0
    OutputFiles = parsedArgs.output

    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Fusion Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Fusion' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )
    
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
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job." )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "" )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render. " )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Fusion Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Fusion Comp", 1, 0, "The comp file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "MultiFileBrowserControl", "", "Fusion Files (*.comp)", 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 2, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 2, 1 )
    framesFromFileBox = scriptDialog.AddSelectionControlToGrid( "FramesFromFileBox", "CheckBoxControl", False, "Use Frame List In Comp", 2, 2, "Enable this option to pull the frame range from the comp file." )
    framesFromFileBox.ValueModified.connect(FramesFromFileBoxChanged)

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 3, 1 )
    scriptDialog.AddSelectionControlToGrid( "CheckOutputBox", "CheckBoxControl", False, "Check Output", 3, 2, "If checked, Deadline will check all savers to ensure they have saved their image file (not supported in command line mode)." )

    scriptDialog.AddControlToGrid( "ProxyLabel", "LabelControl", "Proxy", 4, 0, "The proxy level to use (not supported in command line mode).", False )
    scriptDialog.AddRangeControlToGrid( "ProxyBox", "RangeControl", 1, 1, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "HighQualityBox", "CheckBoxControl", False, "High Quality", 4, 2, "Whether or not to render with high quality (not supported in command line mode)." )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 5, 0, "The version of Fusion to render with.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "7", ["5","6","7","8", "9"], 5, 1 )
    commandLineModeBox = scriptDialog.AddSelectionControlToGrid( "CommandLineModeBox", "CheckBoxControl", False, "Command Line Mode", 5, 2, "Enable to render in command line mode using the FusionCmd plugin (this disables some features)." )
    commandLineModeBox.ValueModified.connect(CommandLineModeChanged)

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build", 6, 0, "", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 6, 1 )
    scriptDialog.AddSelectionControlToGrid("SubmitSceneBox", "CheckBoxControl", False, "Submit Comp File", 6, 2, "If this option is enabled, the flow/comp file will be submitted with the job, and then copied locally to the slave machine during rendering.")
    scriptDialog.EndGrid()
    
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "FusionMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "ProgressLabel", "LabelControl", "", 0, 0 )
    
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)

    scriptDialog.EndGrid()
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","FramesFromFileBox","ChunkSizeBox","VersionBox","ProxyBox", "HighQualityBox", "CheckOutputBox", "SubmitSceneBox", "BuildBox","CommandLineModeBox")
    
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    if parsedArgs.sceneFile:
        scriptDialog.SetValue( "SceneBox", ";".join( parsedArgs.sceneFile ) )

    if parsedArgs.frames:
        scriptDialog.SetValue( "FramesBox", parsedArgs.frames )
        scriptDialog.SetValue( "FramesFromFileBox", False )
    else:
        scriptDialog.SetValue( "FramesFromFileBox", True )

    if parsedArgs.name:
        jobName = parsedArgs.name
        if len( parsedArgs.sceneFile ) > 1:
            jobName += " - " + os.path.basename( parsedArgs.sceneFile[0] )
        scriptDialog.SetValue( "NameBox", jobName )
    elif len(parsedArgs.sceneFile) == 1:
        scriptDialog.SetValue( "NameBox", os.path.basename( parsedArgs.sceneFile[0] ) )

    if parsedArgs.fusion_version:
        scriptDialog.SetValue( "VersionBox", str( int( parsedArgs.fusion_version ) ) )

    if parsedArgs.settings:
        ReadSettingsFile( parsedArgs.settings )
    
    FramesFromFileBoxChanged( None )
    CommandLineModeChanged( None )

    appSubmission = len(args) > 0
    scriptDialog.ShowDialog( appSubmission )

def str2bool( input ):
  return input.lower() in ("yes", "true", "t", "1")

def ReadSettingsFile(settingsFilename):
    try:
        renderSettingOptions = {
            "DEADLINE_AutoTimeout":[str2bool, "AutoTimeoutBox"],
            "DEADLINE_CheckOutput":[str2bool, "CheckOutputBox"],
            "DEADLINE_DefaultChunkSize":[int, "ChunkSizeBox"],
            "DEADLINE_DefaultCommandLineMode":[str2bool, "CommandLineModeBox"],
            "DEADLINE_DefaultDepartment":[str, "DepartmentBox"],
            "DEADLINE_DefaultGroup":[str, "GroupBox"],
            "DEADLINE_DefaultMachineLimit":[int, "MachineLimitBox"],
            "DEADLINE_DefaultPool":[str, "PoolBox"],
            "DEADLINE_DefaultPriority":[int, "PriorityBox"],
            "DEADLINE_DefaultSecondaryPool":[str, "SecondaryPoolBox"],
            "DEADLINE_DefaultSlaveTimeout":[int, "TaskTimeoutBox"],
            "DEADLINE_FrameRange":[str, "FramesBox"],
            "DEADLINE_LimitGroups":[str, "LimitGroupBox"],
            "DEADLINE_SubmitComp":[str2bool, "SubmitSceneBox"]
        }

        with open(settingsFilename, "r") as optionsFile:
            renderSettings = json.load(optionsFile)

        for key, val in renderSettings["DeadlineSettings"].items():
            typeFunc, boxName = renderSettingOptions[key]
            try:

                scriptDialog.SetValue(boxName, typeFunc(val))
            except KeyError:
                scriptDialog.ShowMessageBox(traceback.format_exc(), "Error")
    except:
        scriptDialog.ShowMessageBox(traceback.format_exc(), "Error")

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "FusionSettings.ini" )

def FramesFromFileBoxChanged(*args):
    global scriptDialog
    scriptDialog.SetEnabled( "FramesBox", not scriptDialog.GetValue( "FramesFromFileBox" ) )

def CommandLineModeChanged(*args):
    global scriptDialog
    commandLineMode = scriptDialog.GetValue( "CommandLineModeBox" )
    
    scriptDialog.SetEnabled( "CheckOutputBox", not commandLineMode )
    scriptDialog.SetEnabled( "ProxyLabel", not commandLineMode )
    scriptDialog.SetEnabled( "ProxyBox", not commandLineMode )
    scriptDialog.SetEnabled( "HighQualityBox", not commandLineMode )
    
    scriptDialog.SetEnabled( "ConcurrentTasksLabel", commandLineMode )
    scriptDialog.SetEnabled( "ConcurrentTasksBox", commandLineMode )
    scriptDialog.SetEnabled( "LimitConcurrentTasksBox", commandLineMode )
    
def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog
    global renderRangeRE
    
    # Check if max files exist.
    sceneFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "SceneBox" ), False )
    
    if( len( sceneFiles ) == 0 ):
        scriptDialog.ShowMessageBox( "No fusion comp specified", "Error" )
        return
    
    for sceneFile in sceneFiles:
        if( not File.Exists( sceneFile ) ):
            scriptDialog.ShowMessageBox("Fusion comp file %s does not exist" % sceneFile, "Error" )
            return
        elif(not bool(scriptDialog.GetValue("SubmitSceneBox")) and PathUtils.IsPathLocal(sceneFile)):
            result = scriptDialog.ShowMessageBox("The scene file " + sceneFile + " is local, are you sure you want to continue","Warning", ("Yes","No") )
            
            if(result=="No"):
                return
    
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( ):
        return
    
    # Grab frame range from comp files (Fusion 5 and later only)
    if(bool(scriptDialog.GetValue("FramesFromFileBox"))):
        frames_from_file = []
        for sceneFile in sceneFiles:
            with io.open( sceneFile, mode='r', encoding="utf-8" ) as fileHandle:
                try:
                    for line in fileHandle:
                        #This regex returns a match if the line contains the start of a render range block "RenderRange = {" with any amount of whitespace.
                        #If the array contains a render range formatted how we expect (2 comma separated numbers that might have a comma a the end) it will then return thos values in matches 2 and 3
                        reMatch = renderRangeRE.search( line )
                        if reMatch:
                            if not reMatch.group(2):
                                scriptDialog.ShowMessageBox( "Unable to get RenderRange from comp file %s." % sceneFile, "Error" )
                                return
                            else:
                                frames_from_file.append( "%s-%s" % ( reMatch.group(2), reMatch.group(3) ) )
                                break
                    else:
                        scriptDialog.ShowMessageBox( "Comp file does not contain RenderRange %s." % sceneFile, "Error" )
                        return
                except:
                    scriptDialog.ShowMessageBox( "Unable to read comp file %s." % sceneFile, "Error" )
                    return
    else:
        # Check if a valid frame range has been specified.
        frames = scriptDialog.GetValue( "FramesBox" )
        if( not FrameUtils.FrameRangeValid( frames ) ):
            scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
            return
    
    successes = 0
    failures = 0
    
    plugin = "Fusion"
    version = scriptDialog.GetValue( "VersionBox" )
    
    commandLineMode = scriptDialog.GetValue( "CommandLineModeBox" )
    if commandLineMode:
        plugin = "FusionCmd"
    
    # Submit each scene file separately.
    sceneIndex = 0
    sceneCount = len(sceneFiles)
    for sceneFile in sceneFiles:
        
        jobName = scriptDialog.GetValue( "NameBox" )
        if sceneCount > 1:
            jobName = jobName + " [" + Path.GetFileName( sceneFile ) + "]"
        
        # Show progress.
        scriptDialog.SetValue( "ProgressLabel", "Submitting job " + str(sceneIndex+1) + " of " + str(sceneCount) + " ..." )
        # Force the label control to redraw itself.
        scriptDialog.SetEnabled( "ProgressLabel", False )
        scriptDialog.SetEnabled( "ProgressLabel", True )
    
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "fusion_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=%s" % plugin )
        writer.WriteLine( "Name=%s" % jobName )
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
        writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )

        for i, outputFile in enumerate(OutputFiles):
            writer.WriteLine( "OutputFilename%d=%s" % (i, outputFile) )
        
        if commandLineMode:
            writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "ConcurrentTasksBox" ) )
            writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
        
        writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
        if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        if(bool(scriptDialog.GetValue("FramesFromFileBox"))):
            writer.WriteLine( "Frames=%s" % frames_from_file[sceneIndex] )
        else:
            writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        
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
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "fusion_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
        if(not bool(scriptDialog.GetValue("SubmitSceneBox"))):
            writer.WriteLine("FlowFile=%s" % sceneFile)
        
        writer.WriteLine( "Version=%s" % version )
        if version != "4":
            writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
        
        if not commandLineMode:
            writer.WriteLine( "Proxy=%s" % scriptDialog.GetValue( "ProxyBox" ) )
            writer.WriteLine( "HighQuality=%s" % scriptDialog.GetValue( "HighQualityBox" ) )
            writer.WriteLine( "CheckOutput=%s" % scriptDialog.GetValue( "CheckOutputBox" ) )
        
        writer.Close()
        
        # Setup the command line arguments.
        arguments = StringCollection()
        
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        if scriptDialog.GetValue( "SubmitSceneBox" ):
            arguments.Add( sceneFile )
        
        
        if( len( sceneFiles ) == 1 ):
            results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
            scriptDialog.ShowMessageBox( results, "Submission Results" )
        else:
            # Now submit the job.
            exitCode = ClientUtils.ExecuteCommand( arguments )
            if( exitCode == 0 ):
                successes = successes + 1
            else:
                failures = failures + 1
        
        sceneIndex = sceneIndex + 1
    
    scriptDialog.SetValue( "ProgressLabel", "" )
    
    if( len( sceneFiles ) > 1 ):
        scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )
