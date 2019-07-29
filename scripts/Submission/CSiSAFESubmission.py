from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
RunOption = "Run Analysis"
ProcessMethod = "GUI Process"
SolverMethod = "Standard Solver"
FileExportOption = "Disabled"
DeletionOption = "keep everything"

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    
    scriptDialog = DeadlineScriptDialog()

    scriptDialog.SetTitle( "Submit CSi SAFE Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'CSiSAFE' ) )

    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'No Job Name'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "No Job Name", 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1, colSpan=2 )
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

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to process a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the process times of previous processed files for the job. " )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can process concurrently on a single slave. This is useful if the processing application only uses one thread to process and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "You can force the job to process on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish processing.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start processing right away. Just resume it from the Monitor when you want it to process." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "CSi SAFE File Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "CSi SAFE Data File(s)", 1, 0, "The CSi SAFE Data File to be processed.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "MultiFileBrowserControl", "", "CSi SAFE Files (*.FDB);;Microsoft Access Files (*.MDB);;Microsoft Excel Files (*.XLS);;CSi SAFE Text Files (*.$2K *.F2K)", 1, 1, colSpan=2 )
    
    OverrideOutput = scriptDialog.AddSelectionControlToGrid( "OverrideOutput", "CheckBoxControl", False, "Override Output Directory", 2, 0, "If this option is enabled, an output directory can be used to re-direct all processed files to.", False )
    OverrideOutput.ValueModified.connect(OverrideOutputPressed)
    scriptDialog.AddSelectionControlToGrid( "OutputDirectoryBox", "FolderBrowserControl", "", "", 2, 1, colSpan=2 )
    scriptDialog.SetEnabled( "OutputDirectoryBox", False )

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 3, 0, "You can force 32 or 64 bit processing with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 3, 1 )
    scriptDialog.AddSelectionControlToGrid("SubmitSceneBox","CheckBoxControl",False,"Submit Data File With Job", 3, 2, "If this option is enabled, the SAFE file will be submitted with the job, and then copied locally to the slave machine during processing.")
    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 4, 0, "The version of CSi SAFE to process with.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "2014", ("12", "2014"), 4, 1 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.AddTabPage("Advanced Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Analysis/Design/Detailing Option", 0, 0, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "RunTypeLabel", "LabelControl", "Run Method", 1, 0, "Choose a run combination option.", False )
    RunType = scriptDialog.AddComboControlToGrid( "RunType", "ComboControl", "Run Analysis", ( "Disabled", "Run Analysis", "Run Analysis & Design", "Run Analysis, Design & Detailing" ), 1, 1 )
    RunType.ValueModified.connect(RunTypeChanged)
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "Process/Solver Options", 0, 0, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "ProcessLabel", "LabelControl", "Process Selection", 1, 0, "Choose to execute inside of the existing SAFE application process or as a separate process.", False )
    ProcessType = scriptDialog.AddComboControlToGrid( "ProcessType", "ComboControl", "GUI Process", ( "GUI Process", "Separate Process" ), 1, 1 )
    ProcessType.ValueModified.connect(ProcessTypeChanged)

    scriptDialog.AddControlToGrid( "SolverLabel", "LabelControl", "Solver Selection", 2, 0, "Select the Solver to perform the analysis on the data file.", False )
    SolverType = scriptDialog.AddComboControlToGrid( "SolverType", "ComboControl", "Standard Solver", ( "Standard Solver", "Advanced Solver", "Multithreaded Solver" ), 2, 1 )
    SolverType.ValueModified.connect(SolverTypeChanged)

    scriptDialog.AddSelectionControlToGrid( "Always32bitBox", "CheckBoxControl", False, "Force 32bit Process", 3, 0, "Force analysis to be calculated in 32 bit even when the computer is 64 bit.", colSpan=2 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator6", "SeparatorControl", "Report Option", 0, 0, colSpan=3 )

    scriptDialog.AddSelectionControlToGrid( "CreateReportBox", "CheckBoxControl", False, "Create Report", 1, 0, "Create a report based on the current report settings in the model file." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator7", "SeparatorControl", "Export Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "FileExportLabel", "LabelControl", "File Export", 1, 0, "File export a Microsoft Access, Microsoft Excel, or text file.", False )
    FileExportType = scriptDialog.AddComboControlToGrid( "FileExportType", "ComboControl", "Disabled", ( "Disabled", "Microsoft Access (.mdb)", "Microsoft Excel (.xls)", "Text file (.txt)" ), 1, 1 )
    FileExportType.ValueModified.connect(FileExportTypeChanged)

    scriptDialog.AddControlToGrid( "DBNamedSetLabel", "LabelControl", "DB Named Set (required)", 2, 0, "The name of the database tables named set that defines the tables to be exported. This parameter is required.", False )
    scriptDialog.AddControlToGrid( "DBNamedSet", "TextControl", "", 2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DBGroupedSetLabel", "LabelControl", "DB Group Set (optional)", 3, 0, "The specified group sets the selection for the exported tables. This parameter is optional. If it is not specified, the group ALL is assumed.", False )
    scriptDialog.AddControlToGrid( "DBGroupSet", "TextControl", "", 3, 1, colSpan=2 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator8", "SeparatorControl", "Deletion Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "DeletionLabel", "LabelControl", "Temp File Deletion", 1, 0, "Choose a deletion option to cleanup the analysis/output files if required.", False )
    DeletionType = scriptDialog.AddComboControlToGrid( "DeletionType", "ComboControl", "keep everything", ( "keep everything", "delete analysis & output files", "delete analysis files only", "delete output files only" ), 1, 1 )
    DeletionType.ValueModified.connect(DeletionTypeChanged)
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator9", "SeparatorControl", "Additional Options", 0, 0, colSpan=3 )

    scriptDialog.AddSelectionControlToGrid( "IncludeDataFileBox", "CheckBoxControl", True, "Include Data File", 1, 0, "If enabled, the output zip file will contain the data file OR if outputting to a directory path, the data file will be included." )
    scriptDialog.AddSelectionControlToGrid( "CompressOutputBox", "CheckBoxControl", True, "Compress (ZIP) Output", 2, 0, "Automatically compress the output to a single zip file." )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
   
    scriptDialog.EndTabControl()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )

    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(CloseButtonPressed)

    scriptDialog.EndGrid()
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","ChunkSizeBox","OutputBox","BuildBox","SubmitSceneBox","RunType","ProcessType","SolverType","Always32bitBox","CreateReportBox","FileExportType","DBNamedSet","DBGroupSet","DeletionType","IncludeDataFileBox","CompressOutputBox","VersionBox")

    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    
    scriptDialog.Shown.connect( InitializeDialog )

    scriptDialog.ShowDialog( True )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "CSiSAFESettings.ini" )   

def InitializeDialog( *args ):
    global scriptDialog
    
    OverrideOutputPressed()
    RunTypeChanged()
    ProcessTypeChanged()
    SolverTypeChanged()
    FileExportTypeChanged()
    DeletionTypeChanged()

def CloseDialog():
    global scriptDialog
    global settings
    
    scriptDialog.SaveSettings(GetSettingsFilename(),settings)
    scriptDialog.CloseDialog()
    
def CloseButtonPressed(*args):
    CloseDialog()

def OverrideOutputPressed(*args):
	global scriptDialog

	if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
		scriptDialog.SetEnabled( "OutputDirectoryBox", True )
	else:
		scriptDialog.SetEnabled( "OutputDirectoryBox", False )

def RunTypeChanged(*args):
    global scriptDialog
    global RunMethod

    RunMethod = scriptDialog.GetValue( "RunType" )

def ProcessTypeChanged(*args):
	global scriptDialog
	global ProcessMethod

	ProcessMethod = scriptDialog.GetValue( "ProcessType" )

def SolverTypeChanged(*args):
    global scriptDialog
    global SolverMethod

    SolverMethod = scriptDialog.GetValue( "SolverType" )

def FileExportTypeChanged(*args):
    global scriptDialog
    global FileExportOption

    FileExportOption = scriptDialog.GetValue( "FileExportType" )

    if FileExportOption == "Disabled":
        scriptDialog.SetEnabled( "DBNamedSetLabel", False )
        scriptDialog.SetEnabled( "DBNamedSet", False )
        scriptDialog.SetEnabled( "DBGroupedSetLabel", False )
        scriptDialog.SetEnabled( "DBGroupSet", False )
    else:
        scriptDialog.SetEnabled( "DBNamedSetLabel", True )
        scriptDialog.SetEnabled( "DBNamedSet", True )
        scriptDialog.SetEnabled( "DBGroupedSetLabel", True )
        scriptDialog.SetEnabled( "DBGroupSet", True )

def DeletionTypeChanged(*args):
    global scriptDialog
    global DeletionOption

    DeletionOption = scriptDialog.GetValue( "DeletionType" )

def SubmitButtonPressed(*args):
    global scriptDialog
    global RunMethod
    global ProcessMethod
    global SolverMethod
    global DeletionOption
    global FileExportOption

    try:
        # Check if SAFE file(s) exist.
        dataFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "SceneBox" ), False )

        if( len( dataFiles ) == 0 ):
            scriptDialog.ShowMessageBox( "No CSi SAFE data file specified", "Error" )
            return

        for dataFile in dataFiles:
            if( not File.Exists( dataFile ) ):
                scriptDialog.ShowMessageBox( "The CSi SAFE data file '%s' does not exist" % dataFile, "Error" )
                return
            elif (not scriptDialog.GetValue("SubmitSceneBox") and PathUtils.IsPathLocal(dataFile)):
                scriptDialog.ShowMessageBox( "The CSi SAFE data file is local and 'Submit Data File with Job' is disabled.\n\nAll local data files must be submitted with the job.", "Error" )
                return
            # Check if submitting local data file, then Override OutputDirectory must be specified
            if( scriptDialog.GetValue("SubmitSceneBox") and PathUtils.IsPathLocal(dataFile)):
                if ( not bool( scriptDialog.GetValue( "OverrideOutput" ) ) ):
                    scriptDialog.ShowMessageBox( "The CSi SAFE data file '%s' is local.\n\nAn Output Directory must be specified on the network." % dataFile, "Error" )
                    return

        # Check override output directory
        if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
            OverrideOutputDirectory = scriptDialog.GetValue( "OutputDirectoryBox" )
            if OverrideOutputDirectory == "":
                scriptDialog.ShowMessageBox( "No Override Output Directory specified", "Error" )
                return        
            else:
                if(not Directory.Exists(OverrideOutputDirectory)):
                    scriptDialog.ShowMessageBox( "The Output Directory: '%s' does not exist." % OverrideOutputDirectory, "Error" )
                    return
                elif PathUtils.IsPathLocal(OverrideOutputDirectory):
                    scriptDialog.ShowMessageBox( "Override Output Directory is local and will not be available to other machines!", "Error" )
                    return

        # Check that if Override Output Directory is enabled, that SAFE Data File Directory != Override Output Directory!
        if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
            for dataFile in dataFiles:
                dataFileDirectory = Path.GetDirectoryName(dataFile)
                OverrideOutputDirectory = scriptDialog.GetValue( "OutputDirectoryBox" )
                if( dataFileDirectory == OverrideOutputDirectory ):
                    scriptDialog.ShowMessageBox( "Override output directory must NOT be the same as the data file directory!", "Error" )
                    return

        # Check if File Export Ooption enabled, then DB Named Set != ""
        if FileExportOption != "Disabled" and scriptDialog.GetValue( "DBNamedSet" ) == "":
            scriptDialog.ShowMessageBox( "File Export is enabled, but DB Named Set has not been declared!", "Error" )
            return

        successes = 0
        failures = 0

        for dataFile in dataFiles:         
            # Create job info file.
            jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "csisafe_job_info.job" )
            writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "Plugin=CSiSAFE" )
            writer.WriteLine( "Name=[%s] %s" % ( Path.GetFileName(dataFile), scriptDialog.GetValue( "NameBox" ) ) )
            writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
            writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
            writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
            writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
            writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
            writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
            writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
            writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
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

            writer.WriteLine( "Frames=0" )
            writer.WriteLine( "ChunkSize=1" )
    
            if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
                writer.WriteLine( "OutputDirectory0=%s" % OverrideOutputDirectory )
            else:
                writer.WriteLine( "OutputDirectory0=%s" % Path.GetDirectoryName(dataFile) )

            writer.Close()

            # Create plugin info file.
            pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "csisafe_plugin_info.job" )
            writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

            if( not scriptDialog.GetValue("SubmitSceneBox") ):
                writer.WriteLine( "DataFile=%s" % dataFile )

            if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
                OverrideOutputDirectory = scriptDialog.GetValue( "OutputDirectoryBox" )
                writer.WriteLine( "OverrideOutputDirectory=%s" % OverrideOutputDirectory )
            else:
                writer.WriteLine( "OverrideOutputDirectory=" )

            writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )
            writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
            writer.WriteLine( "Build0=None" )
            writer.WriteLine( "Build1=32bit" )
            writer.WriteLine( "Build2=64bit" )

            writer.WriteLine( "RunMethod=%s" % RunOption )
            writer.WriteLine( "RunMethod0=Disabled" )
            writer.WriteLine( "RunMethod1=Run Analysis" )
            writer.WriteLine( "RunMethod2=Run Analysis & Design" )
            writer.WriteLine( "RunMethod3=Run Analysis, Design & Detailing" )

            writer.WriteLine( "ProcessMethod=%s" % ProcessMethod )
            writer.WriteLine( "ProcessMethod0=GUI Process" )
            writer.WriteLine( "ProcessMethod1=Separate Process" )

            writer.WriteLine( "SolverMethod=%s" % SolverMethod )
            writer.WriteLine( "SolverMethod0=Standard Solver" )
            writer.WriteLine( "SolverMethod1=Advanced Solver" )
            writer.WriteLine( "SolverMethod2=Multithreaded Solver" )

            writer.WriteLine( "Always32bit=%s" % scriptDialog.GetValue( "Always32bitBox" ) )

            writer.WriteLine( "CreateReport=%s" % scriptDialog.GetValue( "CreateReportBox" ) )

            writer.WriteLine( "FileExportOption=%s" % FileExportOption )
            writer.WriteLine( "FileExportOption0=Disabled" )
            writer.WriteLine( "FileExportOption1=Microsoft Access (.mdb)" )
            writer.WriteLine( "FileExportOption2=Microsoft Excel (.xls)" )
            writer.WriteLine( "FileExportOption3=Text file (.txt)" )

            writer.WriteLine( "DBNamedSet=%s" % scriptDialog.GetValue( "DBNamedSet" ) )
            writer.WriteLine( "DBGroupSet=%s" % scriptDialog.GetValue( "DBGroupSet" ) )

            writer.WriteLine( "DeletionOption=%s" % DeletionOption )
            writer.WriteLine( "DeletionOption0=keep everything" )
            writer.WriteLine( "DeletionOption1=delete analysis & output files" )
            writer.WriteLine( "DeletionOption2=delete analysis files only" )
            writer.WriteLine( "DeletionOption3=delete output files only" )

            writer.WriteLine( "IncludeDataFile=%s" % scriptDialog.GetValue( "IncludeDataFileBox" ) )
            writer.WriteLine( "CompressOutput=%s" % scriptDialog.GetValue( "CompressOutputBox" ) )

            writer.Close()
    
            # Setup the command line arguments.
            arguments = StringCollection()
    
            arguments.Add( jobInfoFilename )
            arguments.Add( pluginInfoFilename )
            if scriptDialog.GetValue( "SubmitSceneBox" ):
                arguments.Add( dataFile )
    
            if( len( dataFiles ) == 1 ):
                results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
                scriptDialog.ShowMessageBox( results, "Submission Results" )
            else:
                # Now submit the job.
                exitCode = ClientUtils.ExecuteCommand( arguments )
                if( exitCode == 0 ):
                    successes = successes + 1
                else:
                    failures = failures + 1

        if( len( dataFiles ) > 1 ):
            scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )
    except:
        import traceback
        scriptDialog.ShowMessageBox(traceback.format_exc(), "")
