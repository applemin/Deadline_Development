from System import *
from System.IO import *
from System.Text import *
from System.Diagnostics import *
from System.Collections.Specialized import *

import os
import traceback
import mimetypes

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings

    scriptDialog = DeadlineScriptDialog()

    scriptDialog.SetTitle( "Submit Episode Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Episode' ) )

    scriptDialog.AddTabControl( "Tabs", 0, 0 )

    scriptDialog.AddTabPage( "Job Options" )
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

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 6, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 6, 2, "" )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 7, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 8, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 9, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 9, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 9, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()

    scriptDialog.EndTabPage()

    scriptDialog.AddTabPage( "Episode Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "File Options", 0, 0, colSpan=20 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "DirFileChooserLabel", "LabelControl", "Selection Method", 1, 0, "Choose the selection method by file or by directory.", False )
    DirFileChooserRC1 = scriptDialog.AddRadioControlToGrid( "DirChooser", "RadioControl", False, "Select by Directory", "SelectMethodRadioCtrl", 1, 1, "Choose a root directory to scan for all supported files.", False )
    DirFileChooserRC1.ValueModified.connect(DirFileChooserChanged)
    DirFileChooserRC2 = scriptDialog.AddRadioControlToGrid( "FileChooser", "RadioControl", True, "Select by File", "SelectMethodRadioCtrl", 1, 2, "Choose by individual file selection.", False )
    DirFileChooserRC2.ValueModified.connect(DirFileChooserChanged)

    scriptDialog.AddControlToGrid( "DirectoryLabel", "LabelControl", "Input Source Directory", 2, 0, "Choose a root directory to scan for all supported files.", False )
    scriptDialog.AddSelectionControlToGrid( "DirectoryBox", "FolderBrowserControl", "", "", 2, 1, colSpan=19 )
    scriptDialog.SetEnabled( "DirectoryLabel", False )
    scriptDialog.SetEnabled( "DirectoryBox", False )

    scriptDialog.AddSelectionControlToGrid( "SubDirectoriesBox", "CheckBoxControl", True, "Process Sub-Directories", 3, 0, "Optionally choose to scan sub-directories as well for supported files.", False )
    scriptDialog.SetEnabled( "SubDirectoriesBox", False )

    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input Source File(s)", 4, 0, "The input file(s) to be encoded.", False )
    scriptDialog.AddSelectionControlToGrid( "InputFileBox", "MultiLineMultiFileBrowserControl", "", "All Files (*)", 4, 1, colSpan=19 )

    scriptDialog.AddControlToGrid( "EncoderInputLabel", "LabelControl", "Encoder (*.epitask) File", 5, 0, "The encoder file that will be used (required).", False )
    scriptDialog.AddSelectionControlToGrid( "EncoderInputFileBox", "FileBrowserControl", "", "Episode Encoder Files (*.epitask);;All Files (*)", 5, 1, colSpan=19 )

    scriptDialog.AddSelectionControlToGrid( "SubmitEncoderBox", "CheckBoxControl", False, "Submit Encoder File with Job", 6, 0, "If enabled, the Encoder file will be uploaded to the Deadline Repository along with the Job (useful if the file is local).", False )

    scriptDialog.AddControlToGrid( "OutputFolderLabel", "LabelControl", "Output Path (optional)", 7, 0, "The output path of the encoded output. If left blank, the job will output beside the Input Source File with the default naming convention.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputFolderBox", "FolderBrowserControl", "", "", 7, 1, colSpan=19 )

    scriptDialog.AddControlToGrid( "CustomOutputNameLabel", "LabelControl", "Custom Output Name (optional)", 8, 0, "Optionally, override the default output file naming convention.", False )
    scriptDialog.AddControlToGrid( "CustomOutputNameBox", "TextControl", "", 8, 1, colSpan=19 )

    enableSplit = scriptDialog.AddSelectionControlToGrid( "SplitBox", "CheckBoxControl", False, "Split and Stitch", 9, 0, "If enabled, the encoder(s) will split the encoding and stitch to the final output.", False )
    enableSplit.ValueModified.connect(EnableSplitChanged)

    scriptDialog.AddControlToGrid( "MinSplitTimeLabel", "LabelControl", "Minimum Split Duration (sec)", 10, 0, "Specify minimum duration in seconds for each split. The default value is 30.", False )
    scriptDialog.AddRangeControlToGrid( "MinSplitTimeBox", "RangeControl", 30, 9, 3600, 0, 1, 10, 1 )    
    scriptDialog.AddControlToGrid( "MaxSplitsLabel", "LabelControl", "Maximum Number of Video Splits", 10, 2, "Specify maximum number of splits created. The default value is 16.", False )
    scriptDialog.AddRangeControlToGrid( "MaxSplitsBox", "RangeControl", 16, 2, 32, 0, 1, 10, 3, colSpan=17 )
    
    scriptDialog.AddControlToGrid( "ArgsLabel", "LabelControl", "Additional CLI Arguments (optional)", 11, 0, "Any additional command line arguments to be submitted." )
    scriptDialog.AddControlToGrid( "ArgsBox", "TextControl", "", 11, 1, colSpan=19 )

    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Cluster Encoding", 12, 0, colSpan=20 )

    scriptDialog.AddControlToGrid( "ClusterTypeLabel", "LabelControl", "Cluster Submission", 13, 0, "Disabled: No cluster encoding will take place.\nSubmit To Independent Cluster: Submit the encoding job to an existing Episode cluster on the network outside of Deadline queue.", False )
    clusterTypeBox = scriptDialog.AddComboControlToGrid( "ClusterTypeBox", "ComboControl", "Disabled", ("Disabled","Submit To Independent Cluster"), 13, 1, colSpan=19 )
    clusterTypeBox.ValueModified.connect(ClusterTypeChanged)

    scriptDialog.AddControlToGrid( "ClusterNameLabel", "LabelControl", "Cluster Name (Bonjour required)", 14, 0, "The name of the cluster that you wish to use for encoding (requires Bonjour to work)." )
    clusterName = scriptDialog.AddControlToGrid( "ClusterNameBox", "TextControl", "", 14, 1, colSpan=19 )
    clusterName.ValueModified.connect(ClusterNameChanged)

    scriptDialog.AddControlToGrid( "HostNameLabel", "LabelControl", "Hostname / IP Address", 15, 0, "The hostname or ip address of the cluster's master node that you wish to submit to for encoding." )
    hostName = scriptDialog.AddControlToGrid( "HostNameBox", "TextControl", "", 15, 1, colSpan=19 )
    hostName.ValueModified.connect(ClusterHostChanged)

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SubDirectoriesBox","InputFileBox","EncoderInputFileBox","SubmitEncoderBox","OutputFolderBox","CustomOutputNameBox","SplitBox","ArgsBox","MinSplitTimeBox","MaxSplitsBox","ClusterTypeBox","ClusterNameBox","HostNameBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    DirFileChooserChanged()
    EnableSplitChanged()
    ClusterTypeChanged()

    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return os.path.join( ClientUtils.GetUsersSettingsDirectory(), "EpisodeSettings.ini" )

def DirFileChooserChanged( *args ):
    global scriptDialog
    
    dirSelect = scriptDialog.GetValue( "DirChooser" )
    fileSelect = scriptDialog.GetValue( "FileChooser" )

    scriptDialog.SetEnabled( "SubDirectoriesBox", dirSelect )
    scriptDialog.SetEnabled( "DirectoryLabel", dirSelect )
    scriptDialog.SetEnabled( "DirectoryBox", dirSelect )
    scriptDialog.SetEnabled( "InputLabel", fileSelect )
    scriptDialog.SetEnabled( "InputFileBox", fileSelect )

def EnableSplitChanged( *args ):
    global scriptDialog

    splitEnabled = scriptDialog.GetValue( "SplitBox" )

    scriptDialog.SetEnabled( "MinSplitTimeLabel", splitEnabled )
    scriptDialog.SetEnabled( "MinSplitTimeBox", splitEnabled )
    scriptDialog.SetEnabled( "MaxSplitsLabel", splitEnabled )
    scriptDialog.SetEnabled( "MaxSplitsBox", splitEnabled )

def ClusterTypeChanged( *args ):
    global scriptDialog
    
    clusterType = scriptDialog.GetValue( "ClusterTypeBox" )

    if clusterType == "Disabled":
        clusterState = False
        scriptDialog.SetEnabled( "ClusterNameLabel", clusterState )
        scriptDialog.SetEnabled( "ClusterNameBox", clusterState )
        scriptDialog.SetEnabled( "HostNameLabel", clusterState )
        scriptDialog.SetEnabled( "HostNameBox", clusterState )
    
    elif clusterType == "Submit To Independent Cluster":
        clusterState = True
        scriptDialog.SetEnabled( "ClusterNameLabel", clusterState )
        scriptDialog.SetEnabled( "ClusterNameBox", clusterState )
        scriptDialog.SetEnabled( "HostNameLabel", clusterState )
        scriptDialog.SetEnabled( "HostNameBox", clusterState )

    scriptDialog.SetEnabled( "SubmitEncoderBox", not clusterState )

    if clusterType == "Submit To Independent Cluster":
        ClusterNameChanged()
        ClusterHostChanged()

def ClusterNameChanged( *args ):
    global scriptDialog
    
    clusterName = scriptDialog.GetValue( "ClusterNameBox" )
    
    scriptDialog.SetEnabled( "HostNameLabel", (clusterName == "") )
    scriptDialog.SetEnabled( "HostNameBox", (clusterName == "") )

def ClusterHostChanged( *args ):
    global scriptDialog
    
    hostName = scriptDialog.GetValue( "HostNameBox" )
    
    scriptDialog.SetEnabled( "ClusterNameLabel", (hostName == "") )
    scriptDialog.SetEnabled( "ClusterNameBox", (hostName == "") )

def GetPluginConfig():
    pluginConfig = RepositoryUtils.GetPluginConfig( "Episode", None )
    return pluginConfig

def GetEpisodeExecutable():
    pluginConfig = GetPluginConfig()
    exeList = pluginConfig.GetConfigEntry( "Episode_InterpreterExecutable" )
    episodeExe = FileUtils.SearchFileList( exeList )
    if episodeExe != "":
        return episodeExe
    else:
        scriptDialog.ShowMessageBox( "Episode executable was not found in the semicolon separated list \"" + exeList + "\".\nThe path to the Episode executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return

def GetEpisodeLaunchArguments( command ):
    pluginConfig = GetPluginConfig()
    processList = pluginConfig.GetConfigEntryWithDefault( "EpisodeRequiredProcesses", "" ).split( ";" )
    arguments = "launch " + command + " "
    for processName in processList:
        if not ( ProcessUtils.IsProcessRunning( processName ) ):
            if processName == "EpisodeNode":
                arguments += "--node "
            elif processName == "EpisodeIOServer":
                arguments += "--ioserver "
            elif processName == "EpisodeAssistant":
                arguments += "--assistant "
            elif processName == "EpisodeClientProxy":
                arguments += "--clientproxy "
            elif processName == "EpisodeXMLRPCServer":
                arguments += "--xmlrpc "
            elif processName == "EpisodeJSONRPCServer":
                arguments += "--jsonrpc "
    return arguments

def EpisodeProcess( arguments ):
    episodeExe = GetEpisodeExecutable()
    startupDir = os.path.dirname( episodeExe )
    process = ProcessUtils.SpawnProcess( episodeExe, arguments, startupDir, ProcessWindowStyle.Hidden )
    ProcessUtils.WaitForExit( process, -1 )
    returnCode = process.ExitCode
    if returnCode != 0:
        ClientUtils.LogText( "Error: EpisodeProcess: Command: [%s]\n%s" % ( arguments, traceback.format_exc() ) )

def StartBackgroundProcesses():
    ClientUtils.LogText( "Starting Episode Background Processes..." )
    args = GetEpisodeLaunchArguments( "start" )
    EpisodeProcess( args )
    # Wait 5 seconds as Episode needs a moment to initialise/shutdown, otherwise it
    # raises this error "*** Error: Not connected to local IOServer, unable to share"
    ClientUtils.LogText( "Waiting 5 seconds to allow Episode processes to initialize..." )
    SystemUtils.Sleep( 5000 )

def StopBackgroundProcesses():
    ClientUtils.LogText( "Stopping Episode Background Processes..." )
    args = GetEpisodeLaunchArguments( "stop" )
    EpisodeProcess( args )

def SubmitButtonPressed( *args ):
    global scriptDialog

    # Pre-Flight submission checks
    errors = ""
    warnings = ""
    groupBatch = False

    jobName = scriptDialog.GetValue( "NameBox" )
    encoderFile = scriptDialog.GetValue( "EncoderInputFileBox" )
    outputPath = scriptDialog.GetValue( "OutputFolderBox" )
    submittingEncoder = scriptDialog.GetValue( "SubmitEncoderBox" )
    customOutputName = scriptDialog.GetValue( "CustomOutputNameBox" )
    splitEnabled = scriptDialog.GetValue( "SplitBox" )
    minSplitTime = scriptDialog.GetValue( "MinSplitTimeBox" )
    maxSplits = scriptDialog.GetValue( "MaxSplitsBox" )
    extraArgs = scriptDialog.GetValue( "ArgsBox" )
    clusterType = scriptDialog.GetValue( "ClusterTypeBox" )
    clusterName = scriptDialog.GetValue( "ClusterNameBox" )
    hostName = scriptDialog.GetValue( "HostNameBox" )

    fileSelect = scriptDialog.GetValue( "FileChooser" )
    
    if fileSelect:
        sourceFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "InputFileBox" ), False )
    else:
        rootDirectory = scriptDialog.GetValue( "DirectoryBox" )
        
        if scriptDialog.GetValue( "SubDirectoriesBox" ):
            searchOption = SearchOption.AllDirectories
        else:
            searchOption = SearchOption.TopDirectoryOnly
        
        try:
            sourceFiles = Directory.GetFiles( rootDirectory, "*.*", searchOption )
        except:
            scriptDialog.ShowMessageBox( "Do not select symbolic path shortcuts or UNC paths", "Error" )
            return

    files=[]

    for sourceFile in sourceFiles:

        (mimeType, _) = mimetypes.guess_type( sourceFile )

        if mimeType != None and mimeType.startswith( 'video' ):
            #file appears to be a video, so pass
            pass
        else:
            initFrame = FrameUtils.GetFrameNumberFromFilename( sourceFile )
            paddingSize = FrameUtils.GetPaddingSizeFromFilename( sourceFile )
            
            if initFrame >= 0 and paddingSize > 0:
                sourceFile = FrameUtils.GetLowerFrameFilename( sourceFile, initFrame, paddingSize )
        
        files.append( sourceFile )

    sourceFiles = list(set(files))

    # Check if files exist.
    if len( sourceFiles ) == 0 :
        errors += "No input source file has been found.\n"
    
    for sourceFile in sourceFiles:
        # Check if source/input file exists.
        if not os.path.exists( sourceFile ):
            errors += "The file [%s] does not exist.\n" % sourceFile
        elif PathUtils.IsPathLocal( sourceFile ):
            warnings += " The file [%s] is local.\n" % sourceFile
    
    # Check if encoder file exists.
    if encoderFile == "":
        errors += "No encoder file specified.\n"
    elif not os.path.exists( encoderFile ):
        errors += "The encoder file [%s] does not exist.\n" % encoderFile
    elif PathUtils.IsPathLocal( encoderFile ) and not submittingEncoder:
        warnings += "The encoder file [%s] is local.\n" % encoderFile

    if not outputPath == "":
        if not os.path.exists( outputPath ):
            errors += "The destination folder specified does not exist.\n"
        elif PathUtils.IsPathLocal( outputPath ):
            warnings += "The destination [%s] is local.\n" % outputPath

    if clusterType == "Submit To Independent Cluster" and clusterName == "" and hostName == "":
        errors += "The name of an existing [cluster] or [hostname/ip address] must be entered if submitting an independent Cluster job.\n"

    if len( errors ) > 0:
        scriptDialog.ShowMessageBox( "The following errors were encountered:\n\n%s\nPlease resolve these issues and submit again.\n" % errors, "Errors" )
        return

    if len( warnings ) > 0:
        result = scriptDialog.ShowMessageBox( "Warnings:\n\n%s\n\nDo you still want to continue?" % warnings, "Warnings", ( "Yes", "No" ) )
        if result == "No":
            return

    successes = 0
    failures = 0

    # Submit job directly to Episode cluster and return
    if clusterType == "Submit To Independent Cluster":

        episodeExe = GetEpisodeExecutable()

        pluginConfig = GetPluginConfig()
        startEpisodeProcesses = pluginConfig.GetBooleanConfigEntryWithDefault( "StartEpisodeProcesses", False )

        if startEpisodeProcesses:
            StartBackgroundProcesses()
        
        for index, sourceFile in enumerate( sourceFiles ):

            ClientUtils.LogText( "Submitting Episode Cluster Job: %s of %s" % ( index+1, len(sourceFiles) ) )

            arguments = "ws "

            (mimeType, _) = mimetypes.guess_type( sourceFile )

            if mimeType != None and mimeType.startswith( 'video' ):
                # file appears to be a video
                arguments += "-f \"%s\" -e \"%s\" " % ( sourceFile, encoderFile )
            else:
                # file appears to be an image sequence
                arguments += "-f file+iseq:\"%s\" -e \"%s\" " % ( sourceFile, encoderFile )

            # If no override output path declared, then explicity declare output path to match source file directory
            if outputPath == "":
                outputPath = os.path.dirname( sourceFile )

            arguments += "-d \"%s/\" " % outputPath

            if customOutputName != "":
                arguments += "--naming \"%s\" " % customOutputName

            if extraArgs != "":
                arguments += "%s " % extraArgs

            demoVersion = pluginConfig.GetBooleanConfigEntryWithDefault( "DemoVersion", False )

            if demoVersion:
                arguments += "--demo "

            if clusterName != "":
                arguments += "--cluster %s " % clusterName
            else:
                arguments += "--host %s " % hostName

            if splitEnabled:
                arguments += "--split --max-splits %s --min-split-time %s " % ( maxSplits, minSplitTime )

            arguments += "--id-out"
            
            startupDir = os.path.dirname( episodeExe )
            process = ProcessUtils.SpawnProcess( episodeExe, arguments, startupDir, ProcessWindowStyle.Hidden, True )
            ProcessUtils.WaitForExit( process, -1 )
            returnCode = process.ExitCode

            if returnCode == 0:
                output = process.StandardOutput.ReadToEnd()
                ClientUtils.LogText( "Episode Cluster Job successfully submitted: %s" % output )
                if( len( sourceFiles ) == 1 ):
                    scriptDialog.ShowMessageBox( "Episode Cluster Job Submitted Successfully.\n\n%s" % output, "Episode Cluster Job Submission Successful" )
                    return
                else:
                    successes = successes + 1
            else:
                error = process.StandardError.ReadToEnd()
                ClientUtils.LogText( "Episode Cluster Job failed to be submitted: %s" % error )
                if( len( sourceFiles ) == 1 ):
                    scriptDialog.ShowMessageBox( "%s" % error, "Error" )
                    return
                else:
                    failures = failures + 1

            # When using Bonjour to locate cluster, it needs a few seconds pause between broadcasts over the network to be successful.
            if clusterName != "" and sourceFiles[index] != sourceFiles[-1]:
                ClientUtils.LogText( "Waiting 5 seconds to allow Bonjour system to re-initialize..." )
                SystemUtils.Sleep( 5000 )

        if startEpisodeProcesses:
            StopBackgroundProcesses()

    # Submit normal Deadline job
    else:
        for sourceFile in sourceFiles:

            # Create job info file.
            jobInfoFilename = os.path.join( ClientUtils.GetDeadlineTempPath(), "episode_job_info.job" )    
            writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )

            writer.WriteLine( "Plugin=Episode" )
            
            if jobName == "" or jobName == "Untitled":
                jobName = Path.GetFileName( sourceFile )
            
            writer.WriteLine( "Name=%s" % jobName )

            writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
            writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
            writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
            writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
            writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
            writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
            writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
            writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
            
            if scriptDialog.GetValue( "IsBlacklistBox" ):
                writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            else:
                writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            
            writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
            writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
            writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
            
            writer.WriteLine( "ChunkSize=1000000" )
            writer.WriteLine( "MachineLimit=1" )
            
            if scriptDialog.GetValue( "SubmitSuspendedBox" ):
                writer.WriteLine( "InitialStatus=Suspended" )

            if outputPath == "":
                outputPath = os.path.dirname( sourceFile )
                writer.WriteLine( "OutputDirectory0=%s" % outputPath )
            else:
                writer.WriteLine( "OutputDirectory0=%s" % outputPath )

            writer.Close()

            # Create plugin info file.
            pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "episode_plugin_info.job" )
            writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "SourceFile=%s" % sourceFile )
            
            if not submittingEncoder:
                writer.WriteLine( "EncoderFile=%s" % encoderFile )

            writer.WriteLine( "OutputPath=%s" % outputPath )
            writer.WriteLine( "CustomOutputName=%s" % customOutputName )

            writer.WriteLine( "SplitEnabled=%s" % splitEnabled )
            writer.WriteLine( "MinSplitTime=%s" % minSplitTime )
            writer.WriteLine( "MaxSplits=%s" % maxSplits )
            
            writer.WriteLine( "ExtraArguments=%s" % extraArgs )

            writer.Close()

            arguments = StringCollection()

            if( len( sourceFiles ) == 1 ):
                arguments.Add( "-notify" )

            arguments.Add( jobInfoFilename )
            arguments.Add( pluginInfoFilename )

            if submittingEncoder:
                arguments.Add( encoderFile )
            
            # Now submit the job.
            exitCode = ClientUtils.ExecuteCommand( arguments )
            if( exitCode == 0 ):
                successes = successes + 1
            else:
                failures = failures + 1
        
    if( len( sourceFiles ) > 1 ):
        scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )
        return
