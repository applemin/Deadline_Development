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
ReadVarsESOMaxCol = "unlimited"

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
        
    scriptDialog = DeadlineScriptDialog()

    scriptDialog.SetTitle( "Submit EnergyPlus Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'EnergyPlus' ) )
    
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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "EnergyPlus File Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "DataLabel", "LabelControl", "EnergyPlus IDF File(s)", 1, 0, "The EnergyPlus IDF file(s) to be processed.", False )
    scriptDialog.AddSelectionControlToGrid( "DataBox", "MultiFileBrowserControl", "", "EnergyPlus Files (*.idf)", 1, 1, colSpan=2 )
    
    scriptDialog.AddControlToGrid( "WeatherDirLabel", "LabelControl", "Weather EPW File(s)", 2, 0, "The Weather EPW File(s) to be referenced (Optional).", False )
    scriptDialog.AddSelectionControlToGrid( "WeatherDirBox", "MultiFileBrowserControl", "", "EnergyPlus Files (*.epw)", 2, 1, colSpan=2 )
    
    OverrideOutput = scriptDialog.AddSelectionControlToGrid( "OverrideOutput", "CheckBoxControl", False, "Override Output Directory", 3, 0, "If this option is enabled, an output directory can be used to re-direct all processed files to.", False )
    OverrideOutput.ValueModified.connect(OverrideOutputPressed)
    scriptDialog.AddSelectionControlToGrid( "OutputDirectoryBox", "FolderBrowserControl", "", "", 3, 1, colSpan=2 )
    scriptDialog.SetEnabled( "OutputDirectoryBox", False )

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 4, 0, "You can force 32 or 64 bit processing with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 4, 1 )
    scriptDialog.AddSelectionControlToGrid("SubmitDataBox","CheckBoxControl",False,"Submit File(s) With The Job", 4, 2, "If this option is enabled, the data file(s) will be submitted with the job, and then copied locally to the slave machine during processing.")
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Advanced Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "EP Post-Process Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "ReadVarsESOLabel", "LabelControl", "../ReadVarsESO.exe Max.Columns", 1, 0, "Limit the maximium number of columns used when calling readVarsESO.exe.", False )
    ReadVarsESOMaxCol = scriptDialog.AddComboControlToGrid( "ReadVarsESOMaxColBox", "ComboControl", "unlimited", ("unlimited","less than 250"), 1, 1 )
    ReadVarsESOMaxCol.ValueModified.connect(ReadVarsESOMaxColChanged)

    scriptDialog.AddSelectionControlToGrid( "ConvESOBox", "CheckBoxControl", False, "Execute ../convertESOMTR.exe", 2, 0, "Execute the convertESOMTR.exe application as a post-process.", colSpan=2 )

    scriptDialog.AddSelectionControlToGrid( "CSVprocBox", "CheckBoxControl", False, "Execute ../CSVproc.exe", 3, 0, "Execute the csvProc.exe application as a post-process.", colSpan=2 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "Processing Options", 0, 0, colSpan=3 )

    scriptDialog.AddSelectionControlToGrid( "MultithreadingBox", "CheckBoxControl", True, "Multithreading", 1, 0, "If enabled, EnergyPlus simulations will use multithreading. Ignored if Concurrent Tasks > 1." )

    scriptDialog.AddSelectionControlToGrid( "DebugBox", "CheckBoxControl", False, "Pause Mode (DEBUG only)", 2, 0, "Only for Debug purposes. Will PAUSE the program execution at key steps." )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator6", "SeparatorControl", "Other Options", 0, 0, colSpan=3 )    

    scriptDialog.AddSelectionControlToGrid( "IncludeDataFileBox", "CheckBoxControl", True, "Include Data File", 1, 0, "If enabled, the output zip file will contain the data file OR if outputting to a directory path, the data file will be included." )
    scriptDialog.AddSelectionControlToGrid( "CompressOutputBox", "CheckBoxControl", True, "Compress (ZIP) Output", 2, 0, "Automatically compress the EP output to a single zip file." )
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
    
    settings = ("DepartmentBox","CategoryBox","PoolBox", "SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","DataBox","ChunkSizeBox","OutputBox","BuildBox", "WeatherDirBox", "ReadVarsESOMaxColBox", "ConvESOBox", "CSVprocBox", "MultithreadingBox", "DebugBox", "IncludeDataFileBox", "CompressOutputBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )

    scriptDialog.Shown.connect( InitializeDialog )

    scriptDialog.ShowDialog( True )

def InitializeDialog( *args ):
    global scriptDialog

    OverrideOutputPressed()
    ReadVarsESOMaxColChanged()

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "EnergyPlusSettings.ini" )

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

def ReadVarsESOMaxColChanged(*args):
    global scriptDialog
    global ReadVarsESOMaxCol

    ReadVarsESOMaxCol = scriptDialog.GetValue( "ReadVarsESOMaxColBox" )

def SubmitButtonPressed(*args):
    global scriptDialog
    global ReadVarsESOMaxCol

    try:
        # Check if EnergyPlus files exist.
        dataFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "DataBox" ), False )

        if( len( dataFiles ) == 0 ):
            scriptDialog.ShowMessageBox( "No EnergyPlus IDF file specified!", "Error" )
            return

        for dataFile in dataFiles:
            if( not File.Exists( dataFile ) ):
                scriptDialog.ShowMessageBox( "The EnergyPlus IDF file [%s] does not exist!" % dataFile, "Error" )
                return
            if ( not scriptDialog.GetValue("SubmitDataBox") and PathUtils.IsPathLocal(dataFile)):
                scriptDialog.ShowMessageBox( "The EnergyPlus IDF file [%s] is local and 'Submit File(s) With The Job' is disabled.\n\nAll local data files must be submitted with the job." % dataFile, "Error" )
                return
            elif ( not scriptDialog.GetValue("SubmitDataBox") and ( not PathUtils.IsPathRooted(dataFile) ) ):
                scriptDialog.ShowMessageBox( "The EnergyPlus IDF file [%s] is not rooted and 'Submit File(s) With The Job' is disabled.\n\nAll local data files must be submitted with the job." % dataFile, "Error" )
                return

            # Check if submitting local data file, then Override OutputDirectory must be specified
            if( scriptDialog.GetValue("SubmitDataBox") and PathUtils.IsPathLocal(dataFile)):
                if ( not bool( scriptDialog.GetValue( "OverrideOutput" ) ) ):
                    scriptDialog.ShowMessageBox( "The EnergyPlus data file [%s] is local.\n\nAn Output Directory must be specified on the network!" % dataFile, "Error" )
                    return

        # Check if Weather EPW Files exist and if local, then must be submitted with job
        weatherFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "WeatherDirBox" ), False )

        for weatherFile in weatherFiles:
            if( not File.Exists( weatherFile ) ):
                scriptDialog.ShowMessageBox( "The EnergyPlus Weather EPW file [%s] does not exist!" % weatherFile, "Error" )
                return
            if ( not scriptDialog.GetValue("SubmitDataBox") and PathUtils.IsPathLocal(weatherFile) ):
                scriptDialog.ShowMessageBox( "The EnergyPlus Weather EPW file [%s] is local\nand 'Submit File(s) With The Job' is disabled.\n\nAll local weather files must be submitted with the job!" % weatherFile, "Error" )
                return
            elif ( not scriptDialog.GetValue("SubmitDataBox") and ( not PathUtils.IsPathRooted(weatherFile) ) ):
                scriptDialog.ShowMessageBox( "The EnergyPlus Weather EPW file [%s] is not rooted and 'Submit File(s) With The Job' is disabled.\n\nAll local weather files must be submitted with the job." % weatherFile, "Error" )
                return

        # Check override output directory
        if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
            OverrideOutputDirectory = scriptDialog.GetValue( "OutputDirectoryBox" )
            if OverrideOutputDirectory == "":
                scriptDialog.ShowMessageBox( "No Override Output Directory specified!", "Error" )
                return        
            else:
                if(not Directory.Exists(OverrideOutputDirectory)):
                    scriptDialog.ShowMessageBox( "The Output Directory: [%s] does not exist!" % OverrideOutputDirectory, "Error" )
                    return
                elif PathUtils.IsPathLocal(OverrideOutputDirectory):
                    scriptDialog.ShowMessageBox( "Override Output Directory is local and will not be available to other machines!", "Error" )
                    return

        ## Check that if Override Output Directory is enabled, that EnergyPlus Data File Directory != Override Output Directory!
        if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
            for dataFile in dataFiles:
                dataFileDirectory = Path.GetDirectoryName(dataFile)
                OverrideOutputDirectory = scriptDialog.GetValue( "OutputDirectoryBox" )
                if( dataFileDirectory == OverrideOutputDirectory ):
                    scriptDialog.ShowMessageBox( "Override output directory must NOT be the same as the data file directory!", "Error" )
                    return

        # Check Weather dependent aux files *.ddy & *.stat exist in the same directory as the *.epw file
        for weatherFile in weatherFiles:
            statFilename = Path.GetFileNameWithoutExtension( weatherFile) + ".stat"
            statFile = Path.Combine( Path.GetDirectoryName( weatherFile ), statFilename )

            ddyFilename = Path.GetFileNameWithoutExtension( weatherFile) + ".ddy"
            ddyFile = Path.Combine( Path.GetDirectoryName( weatherFile ), ddyFilename )

            if( not File.Exists( statFile ) ):
                result = scriptDialog.ShowMessageBox( "The EnergyPlus EPW Weather dependent *.stat file [%s] does not exist!\n\nClick Continue to ignore warning." % statFile, "Warning", ("Continue","Cancel") )
                if( result == "Cancel" ):
                    return
            if( not File.Exists( ddyFile ) ):
                scriptDialog.ShowMessageBox( "The EnergyPlus EPW Weather dependent *.ddy file [%s] does not exist!\n\nClick Continue to ignore warning." % ddyFile, "Warning", ("Continue","Cancel") )
                if( result == "Cancel" ):
                    return

        weatherFilesCount = len(weatherFiles)
        
        # Submit multiple jobs containing all IDF files per weather file (when multiple weather files supplied)
        if weatherFilesCount > 1:

            successes = 0
            failures = 0

            for weatherFile in weatherFiles:

                # Create job info file.
                jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "energyplus_job_info.job" )
                writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
                writer.WriteLine( "Plugin=EnergyPlus" )
                tempName = " [" + str(Path.GetFileName(weatherFile)) + "]"
                writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) + tempName )
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

                writer.WriteLine( "Frames=0-%s" % str( len( dataFiles ) - 1 ) )
                writer.WriteLine( "ChunkSize=1" )

                if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
                    writer.WriteLine( "OutputDirectory0=%s" % OverrideOutputDirectory )
                else:
                    for index, dataFile in enumerate( dataFiles ):
                        writer.WriteLine( "OutputDirectory%s=%s" % ( index, Path.GetDirectoryName(dataFile) ) )

                writer.Close()

                # Create plugin info file.
                pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "energyplus_plugin_info.job" )
                writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

                index = 0
                for dataFile in dataFiles:
                    dataFile = dataFile.replace( "\\", "/" )
                    tempString = "DataFile%" + "d=%s"
                    writer.WriteLine( tempString % ( index, dataFile ) )
                    weatherFile = weatherFile.replace( "\\", "/" )
                    tempString = "WeatherFile%" + "d=%s"
                    writer.WriteLine( tempString % ( index, weatherFile ) )
                    index += 1
            
                if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
                    OverrideOutputDirectory = scriptDialog.GetValue( "OutputDirectoryBox" )
                    writer.WriteLine( "OverrideOutputDirectory=%s" % OverrideOutputDirectory )
                else:
                    writer.WriteLine( "OverrideOutputDirectory=" )

                writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
                writer.WriteLine( "Build0=None" )
                writer.WriteLine( "Build1=32bit" )
                writer.WriteLine( "Build2=64bit" )

                writer.WriteLine( "ReadVarsESOMaxCol=%s" % ReadVarsESOMaxCol )
                writer.WriteLine( "ReadVarsESOMaxCol0=unlimited" )
                writer.WriteLine( "ReadVarsESOMaxCol1=less than 250" )

                writer.WriteLine( "ConvESO=%s" % scriptDialog.GetValue( "ConvESOBox" ) )
                writer.WriteLine( "CSVproc=%s" % scriptDialog.GetValue( "CSVprocBox" ) )

                # Handle Multi-threading if ConcurrentTasks > 1
                if( int( scriptDialog.GetValue( "ConcurrentTasksBox" ) ) > 1 ):
                    writer.WriteLine( "Multithreading=False" )
                else:   
                    writer.WriteLine( "Multithreading=%s" % scriptDialog.GetValue( "MultithreadingBox" ) )

                writer.WriteLine( "Debug=%s" % scriptDialog.GetValue( "DebugBox" ) )

                writer.WriteLine( "IncludeDataFile=%s" % scriptDialog.GetValue( "IncludeDataFileBox" ) )
                writer.WriteLine( "CompressOutput=%s" % scriptDialog.GetValue( "CompressOutputBox" ) )

                writer.Close()

                # Setup the command line arguments.
                arguments = StringCollection()
            
                arguments.Add( jobInfoFilename )
                arguments.Add( pluginInfoFilename )

                # Handle multiple IDF & EPW/STAT/DDY file that needs to be submitted with Deadline Job if LOCAL on the submitting user's machine
                if scriptDialog.GetValue( "SubmitDataBox" ):
                    for dataFile in dataFiles:
                        arguments.Add( dataFile )
                    
                    arguments.Add( weatherFile )

                    statFilename = Path.GetFileNameWithoutExtension( weatherFile) + ".stat"
                    statFile = Path.Combine( Path.GetDirectoryName( weatherFile ), statFilename )
                    if File.Exists(statFile):
                        arguments.Add( statFile )

                    ddyFilename = Path.GetFileNameWithoutExtension( weatherFile) + ".ddy"
                    ddyFile = Path.Combine( Path.GetDirectoryName( weatherFile ), ddyFilename )
                    if File.Exists(ddyFile):
                        arguments.Add( ddyFile )

                # Now submit the job.
                exitCode = ClientUtils.ExecuteCommand( arguments )
                if( exitCode == 0 ):
                    successes = successes + 1
                else:
                    failures = failures + 1
            
            scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )

        # Submit one job containing all IDF files (one per frame) against either NO weather file or just a single weather file (optional)
        else:

            # Create job info file.
            jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "energyplus_job_info.job" )
            writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "Plugin=EnergyPlus" )
            writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
            writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
            writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
            writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
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

            writer.WriteLine( "Frames=0-%s" % str( len( dataFiles ) - 1 ) )
            writer.WriteLine( "ChunkSize=1" )

            if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
                writer.WriteLine( "OutputDirectory0=%s" % OverrideOutputDirectory )
            else:
                for index, dataFile in enumerate( dataFiles ):
                    writer.WriteLine( "OutputDirectory%s=%s" % ( index, Path.GetDirectoryName(dataFile) ) )

            writer.Close()

            # Create plugin info file.
            pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "energyplus_plugin_info.job" )
            writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

            index = 0
            for dataFile in dataFiles:
                dataFile = dataFile.replace( "\\", "/" )
                tempString = "DataFile%" + "d=%s"
                writer.WriteLine( tempString % ( index, dataFile ) )

                if weatherFilesCount > 0:
                    # Return first entry in weatherFiles list
                    weatherFile = weatherFiles[0].replace( "\\", "/" )
                    tempString = "WeatherFile%" + "d=%s"
                    writer.WriteLine( tempString % ( index, weatherFile ) )

                index += 1

            if ( bool( scriptDialog.GetValue( "OverrideOutput" ) ) == True ):
                OverrideOutputDirectory = scriptDialog.GetValue( "OutputDirectoryBox" )
                writer.WriteLine( "OverrideOutputDirectory=%s" % OverrideOutputDirectory )
            else:
                writer.WriteLine( "OverrideOutputDirectory=" )

            writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
            writer.WriteLine( "Build0=None" )
            writer.WriteLine( "Build1=32bit" )
            writer.WriteLine( "Build2=64bit" )

            writer.WriteLine( "ReadVarsESOMaxCol=%s" % ReadVarsESOMaxCol )
            writer.WriteLine( "ReadVarsESOMaxCol0=unlimited" )
            writer.WriteLine( "ReadVarsESOMaxCol1=less than 250" )

            writer.WriteLine( "ConvESO=%s" % scriptDialog.GetValue( "ConvESOBox" ) )
            writer.WriteLine( "CSVproc=%s" % scriptDialog.GetValue( "CSVprocBox" ) )

            # Handle Multi-threading if ConcurrentTasks > 1
            if( int( scriptDialog.GetValue( "ConcurrentTasksBox" ) ) > 1 ):
                writer.WriteLine( "Multithreading=False" )
            else:   
                writer.WriteLine( "Multithreading=%s" % scriptDialog.GetValue( "MultithreadingBox" ) )

            writer.WriteLine( "Debug=%s" % scriptDialog.GetValue( "DebugBox" ) )

            writer.WriteLine( "IncludeDataFile=%s" % scriptDialog.GetValue( "IncludeDataFileBox" ) )
            writer.WriteLine( "CompressOutput=%s" % scriptDialog.GetValue( "CompressOutputBox" ) )

            writer.Close()

            # Setup the command line arguments.
            arguments = StringCollection()
        
            arguments.Add( jobInfoFilename )
            arguments.Add( pluginInfoFilename )

            # Handle multiple IDF & EPW/STAT/DDY file that needs to be submitted with Deadline Job if LOCAL on the submitting user's machine
            if scriptDialog.GetValue( "SubmitDataBox" ):
                for dataFile in dataFiles:
                    arguments.Add( dataFile )
                
                if weatherFilesCount > 0:
                    arguments.Add( weatherFile )

                    statFilename = Path.GetFileNameWithoutExtension( weatherFile) + ".stat"
                    statFile = Path.Combine( Path.GetDirectoryName( weatherFile ), statFilename )
                    if File.Exists(statFile):
                        arguments.Add( statFile )

                    ddyFilename = Path.GetFileNameWithoutExtension( weatherFile) + ".ddy"
                    ddyFile = Path.Combine( Path.GetDirectoryName( weatherFile ), ddyFilename )
                    if File.Exists(ddyFile):
                        arguments.Add( ddyFile )

            # Now submit the job.
            results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
            scriptDialog.ShowMessageBox( results, "Submission Results" )

    except:
        import traceback
        scriptDialog.ShowMessageBox(traceback.format_exc(), "")
