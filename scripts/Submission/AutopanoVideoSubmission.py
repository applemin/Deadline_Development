import os

from System import *
from System.IO import *
from System.Text import *
from System.Diagnostics import *
from System.Collections.Specialized import *

from Deadline.Scripting import *
from Deadline.Plugins import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog

    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Autopano Video To Deadline" )
    scriptDialog.SetIcon( RepositoryUtils.GetRepositoryFilePath( "plugins/AutopanoVideo/AutopanoVideo.ico", True ) )

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1, colSpan=2 )

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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Autopano Video Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "DirFileChooserLabel", "LabelControl", "Selection Method", 1, 0, "Choose the selection method by file or by directory.", False )
    DirFileChooserRC1 = scriptDialog.AddRadioControlToGrid( "DirChooser", "RadioControl", False, "Select by Directory", "SelectMethodRadioCtrl", 1, 1, "Choose a root directory to scan for all kava files.", False )
    DirFileChooserRC1.ValueModified.connect(DirFileChooserChanged)
    DirFileChooserRC2 = scriptDialog.AddRadioControlToGrid( "FileChooser", "RadioControl", True, "Select by File", "SelectMethodRadioCtrl", 1, 2, "Choose by individual kava file selection.", False )
    DirFileChooserRC2.ValueModified.connect(DirFileChooserChanged)

    scriptDialog.AddControlToGrid( "DirectoryLabel", "LabelControl", "Autopano File Directory", 2, 0, "Choose a root directory to scan for all kava files.", False )
    scriptDialog.AddSelectionControlToGrid( "DirectoryBox", "FolderBrowserControl", "", "", 2, 1, colSpan=3 )
    scriptDialog.SetEnabled( "DirectoryLabel", False )
    scriptDialog.SetEnabled( "DirectoryBox", False )

    scriptDialog.AddSelectionControlToGrid( "SubDirectoriesBox", "CheckBoxControl", True, "Process Sub-Directories", 3, 0, "Optionally choose to scan sub-directories as well for kava files.", False )
    scriptDialog.SetEnabled( "SubDirectoriesBox", False )

    scriptDialog.AddControlToGrid( "KavaLabel", "LabelControl", "Autopano File(s)", 4, 0, "The file path to the kava file(s) to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "KavaFileBox", "MultiLineMultiFileBrowserControl", "", "Autopano Video Files (*.kava)", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 5, 0, "The version of Autopano Video being used for this render job.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "3", ("2","3"), 5, 1 )
    
    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 6, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 6, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 1 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 2, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 3, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ( "CategoryBox","DepartmentBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","LimitGroupBox","OnJobCompleteBox","MachineListBox","SubmitSuspendedBox","IsBlacklistBox","DirChooser","FileChooser","DirectoryBox","SubDirectoriesBox","KavaFileBox","VersionBox","BuildBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    DirFileChooserChanged()

    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "AutopanoVideoSettings.ini" )

def DirFileChooserChanged( *args ):
    global scriptDialog
    
    dirSelect = scriptDialog.GetValue( "DirChooser" )
    fileSelect = scriptDialog.GetValue( "FileChooser" )

    scriptDialog.SetEnabled( "SubDirectoriesBox", dirSelect )
    scriptDialog.SetEnabled( "DirectoryLabel", dirSelect )
    scriptDialog.SetEnabled( "DirectoryBox", dirSelect )
    scriptDialog.SetEnabled( "KavaLabel", fileSelect )
    scriptDialog.SetEnabled( "KavaFileBox", fileSelect )

def SubmitButtonPressed( *args ):
    global scriptDialog

    try:
        fileSelect = scriptDialog.GetValue( "FileChooser" )
        
        if fileSelect:
            kavaFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "KavaFileBox" ), False )
        else:
            rootDirectory = scriptDialog.GetValue( "DirectoryBox" )
            
            if scriptDialog.GetValue( "SubDirectoriesBox" ):
                searchOption = SearchOption.AllDirectories
            else:
                searchOption = SearchOption.TopDirectoryOnly
            
            try:
                kavaFiles = Directory.GetFiles( rootDirectory, "*.kava", searchOption )
            except:
                scriptDialog.ShowMessageBox( "Do not select symbolic path shortcuts or UNC paths", "Error" )
                return

        warnings = []
        errors = []

        if( len( kavaFiles ) == 0 ):
            errors.append( "No Autopano Video file(s) specified" )

        for kavaFile in kavaFiles:

            if not File.Exists(kavaFile):
                errors.append( "Autopano Video file %s does not exist" % kavaFile )
                
            if( PathUtils.IsPathLocal( kavaFile ) ):
                warnings.append( "The Autopano Video file " + kavaFile + " is local, are you sure you want to continue?" )
            
            if( not kavaFile.endswith( ".kava" ) ):
                errors.append( "The Autopano Video file " + kavaFile + " is not a supported format. Please resubmit a valid Autopano Video file." )

        if len( errors ) > 0:
            scriptDialog.ShowMessageBox( "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % ( "\n".join( errors ) ), "Errors" )
            return

        if len( warnings ) > 0:
            result = scriptDialog.ShowMessageBox( "Warnings:\n\n%s\n\nDo you still want to continue?" % ( "\n".join( warnings ) ), "Warnings", ( "Yes","No" ) )
            if result == "No":
                return

        successes = 0
        failures = 0

        for kavaFile in kavaFiles:
            # Create job info file.
            jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "autopanovideo_job_info.job" )
            writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "Plugin=AutopanoVideo" )

            jobName = scriptDialog.GetValue( "NameBox" ) + " [%s]" % os.path.basename(kavaFile)

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
            writer.Close()

            # Create plugin info file.
            pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "autopanovideo_plugin_info.job" )
            writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

            writer.WriteLine( "KavaFile=%s" % kavaFile )
            writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )
            writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
            writer.Close()

            # Setup the command line arguments.
            arguments = StringCollection()

            arguments.Add( jobInfoFilename )
            arguments.Add( pluginInfoFilename )

            # Now submit the job.
            if( len( kavaFiles ) == 1 ):
                results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
                scriptDialog.ShowMessageBox( results, "Submission Results" )
            else:
                exitCode = ClientUtils.ExecuteCommand( arguments )
                if( exitCode == 0 ):
                    successes = successes + 1
                else:
                    failures = failures + 1
            
        if( len( kavaFiles ) > 1 ):
            scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % ( successes, failures ), "Submission Results" )
    except:
        import traceback
        scriptDialog.ShowMessageBox( traceback.format_exc(), "" )
