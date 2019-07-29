from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Main Guerilla Submission Dialog
########################################################################
class GuerillaDialog( DeadlineScriptDialog ):
    appSubmission = False
    
    def __init__( self, args ):
        super( GuerillaDialog, self ).__init__()
        
        self.SetTitle( "Submit Guerilla Job To Deadline" )
        self.SetIcon( RepositoryUtils.GetRepositoryFilePath("plugins/Guerilla/Guerilla.ico", True) )
        
        self.AddGrid()
        self.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )
        
        self.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
        self.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

        self.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
        self.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

        self.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
        self.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

        self.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
        self.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

        self.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
        self.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

        self.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
        self.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

        self.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
        self.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

        self.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
        self.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
        self.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

        self.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
        self.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
        self.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

        self.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "", False )
        self.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
        self.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "" )

        self.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
        self.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

        self.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
        self.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

        self.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering. ", False )
        self.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

        self.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
        self.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
        self.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render. " )
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid( "Separator3", "SeparatorControl", "Guerilla Options", 0, 0, colSpan=3 )

        self.AddControlToGrid( "SceneLabel", "LabelControl", "LUA Files", 1, 0, "The LUA files to be rendered (can be ASCII or binary formatted). These files should be network accessible.", False )
        sceneBox = self.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "LUA Files (*.lua);;All files (*)", 1, 1, colSpan=2 )
        
        self.AddControlToGrid( "CommandLineLabel", "LabelControl", "Additional Arguments", 2, 0, "Specify additional command line arguments you would like to pass to the LUA files.", False )
        self.AddControlToGrid( "CommandLineBox", "TextControl", "", 2, 1, colSpan=2 )

        self.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render.", False )
        self.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1, colSpan=2 )
        
        self.EndGrid()
        
        self.AddGrid()
        self.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
        submitButton = self.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
        submitButton.ValueModified.connect( self.submitButtonPressed )
        closeButton = self.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
        closeButton.ValueModified.connect( self.closeEvent )
        self.EndGrid()

        settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ThreadsBox","CommandLineBox", "WorkingDirBox")
        self.LoadSettings( self.getSettingsFilename(), settings )
        self.EnabledStickySaving( settings, self.getSettingsFilename() )
        
        if len( args ) > 0:
            self.appSubmission = True
            jobName = args[0]
            frames = args[1]
            jobDir = args[2]
            
            self.SetValue( "NameBox", jobName )
            self.SetValue( "SceneLabel", "Jobs Directory" )
            self.SetToolTip( "SceneLabel", "The directory that contains the LUA script files that will be rendered." )
            self.SetValue( "SceneBox", jobDir )
            self.SetValue( "CommandLineBox", "" )
            self.SetValue( "FramesBox", frames )
            
            self.SetEnabled( "NameLabel", False )
            self.SetEnabled( "NameBox", False )
            self.SetEnabled( "SceneLabel", False )
            self.SetEnabled( "SceneBox", False )
            self.SetEnabled( "CommandLineLabel", False )
            self.SetEnabled( "CommandLineBox", False )
            self.SetEnabled( "FramesLabel", False )
            self.SetEnabled( "FramesBox", False )
        else:
            sceneBox.ValueModified.connect( self.sceneChanged )
            self.sceneChanged()
            
    def getSettingsFilename( self ):
        return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "GuerillaSettings.ini" )
        
    def sceneChanged( self ):
        filename = self.GetValue( "SceneBox" )
        frameString = ""
        
        try:
            initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
            paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
            
            startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
            endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
            if startFrame == endFrame:
                frameString = str(startFrame)
            else:
                frameString = str(startFrame) + ":" + str(endFrame)
        except:
            frameString = ""
        
        self.SetValue( "FramesBox", frameString )
        
    def submitButtonPressed( self ):
        if not self.appSubmission:
            # Check lua files.
            sceneFile = self.GetValue( "SceneBox" )
            if not File.Exists( sceneFile ):
                self.ShowMessageBox( "LUA file '%s' does not exist." % sceneFile, "Error" )
                return
            elif PathUtils.IsPathLocal( sceneFile ):
                result = self.ShowMessageBox( "The LUA file '%s' is local, are you sure you want to continue?" % sceneFile, "Warning", ("Yes","No") )
                if result == "No":
                    return
            
            # Check if a valid frame range has been specified.
            frames = self.GetValue( "FramesBox" )
            if( not FrameUtils.FrameRangeValid( frames ) ):
                self.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
                return
            
            # Create job info file.
            jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "guerilla_job_info.job" )
            writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "Plugin=Guerilla" )
            writer.WriteLine( "Name=%s" % self.GetValue( "NameBox" ) )
            writer.WriteLine( "Comment=%s" % self.GetValue( "CommentBox" ) )
            writer.WriteLine( "Department=%s" % self.GetValue( "DepartmentBox" ) )
            writer.WriteLine( "Pool=%s" % self.GetValue( "PoolBox" ) )
            writer.WriteLine( "SecondaryPool=%s" % self.GetValue( "SecondaryPoolBox" ) )
            writer.WriteLine( "Group=%s" % self.GetValue( "GroupBox" ) )
            writer.WriteLine( "Priority=%s" % self.GetValue( "PriorityBox" ) )
            writer.WriteLine( "TaskTimeoutMinutes=%s" % self.GetValue( "TaskTimeoutBox" ) )
            writer.WriteLine( "EnableAutoTimeout=%s" % self.GetValue( "AutoTimeoutBox" ) )
            writer.WriteLine( "ConcurrentTasks=%s" % self.GetValue( "ConcurrentTasksBox" ) )
            writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % self.GetValue( "LimitConcurrentTasksBox" ) )
            
            writer.WriteLine( "MachineLimit=%s" % self.GetValue( "MachineLimitBox" ) )
            if( bool(self.GetValue( "IsBlacklistBox" )) ):
                writer.WriteLine( "Blacklist=%s" % self.GetValue( "MachineListBox" ) )
            else:
                writer.WriteLine( "Whitelist=%s" % self.GetValue( "MachineListBox" ) )
            
            writer.WriteLine( "LimitGroups=%s" % self.GetValue( "LimitGroupBox" ) )
            writer.WriteLine( "JobDependencies=%s" % self.GetValue( "DependencyBox" ) )
            writer.WriteLine( "OnJobComplete=%s" % self.GetValue( "OnJobCompleteBox" ) )
            
            if( bool(self.GetValue( "SubmitSuspendedBox" )) ):
                writer.WriteLine( "InitialStatus=Suspended" )
            
            writer.WriteLine( "Frames=%s" % frames )
            writer.WriteLine( "ChunkSize=1" )
            writer.Close()
            
            # Create plugin info file.
            pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "guerilla_plugin_info.job" )
            writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
            writer.WriteLine( "ScriptFile=%s" % sceneFile )
            writer.WriteLine( "ScriptArgs=%s" % self.GetValue( "CommandLineBox" ).strip() ) 
            writer.Close()
            
            # Setup the command line arguments.
            arguments = StringCollection()
            arguments.Add( jobInfoFilename )
            arguments.Add( pluginInfoFilename )
            
            # Now submit the job.
            results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
            self.ShowMessageBox( results, "Submission Results" )
            
        else:
            submitJob = True
            
            # Check job directory.
            jobDirectory = self.GetValue( "SceneBox" )
            if not Directory.Exists( jobDirectory ):
                self.ShowMessageBox( "Guerilla jobs directory '%s' does not exist." % jobDirectory, "Error" )
                submitJob = False
            elif PathUtils.IsPathLocal( jobDirectory ):
                result = self.ShowMessageBox( "Guerilla jobs directory '%s' is local, are you sure you want to continue?" % jobDirectory, "Warning", ("Yes","No") )
                if result == "No":
                    submitJob = False
            
            if submitJob:
                ClientUtils.LogText( "SUBMISSION OPTIONS" )
                
                ClientUtils.LogText( "Name=%s" % self.GetValue( "NameBox" ) )
                ClientUtils.LogText( "Comment=%s" % self.GetValue( "CommentBox" ) )
                ClientUtils.LogText( "Department=%s" % self.GetValue( "DepartmentBox" ) )
                ClientUtils.LogText( "Pool=%s" % self.GetValue( "PoolBox" ) )
                ClientUtils.LogText( "SecondaryPool=%s" % self.GetValue( "SecondaryPoolBox" ) )
                ClientUtils.LogText( "Group=%s" % self.GetValue( "GroupBox" ) )
                ClientUtils.LogText( "Priority=%s" % self.GetValue( "PriorityBox" ) )
                ClientUtils.LogText( "TaskTimeoutMinutes=%s" % self.GetValue( "TaskTimeoutBox" ) )
                ClientUtils.LogText( "EnableAutoTimeout=%s" % self.GetValue( "AutoTimeoutBox" ) )
                ClientUtils.LogText( "ConcurrentTasks=%s" % self.GetValue( "ConcurrentTasksBox" ) )
                ClientUtils.LogText( "LimitConcurrentTasksToNumberOfCpus=%s" % self.GetValue( "LimitConcurrentTasksBox" ) )
                ClientUtils.LogText( "MachineLimit=%s" % self.GetValue( "MachineLimitBox" ) )
                
                if( bool(self.GetValue( "IsBlacklistBox" )) ):
                    ClientUtils.LogText( "Blacklist=%s" % self.GetValue( "MachineListBox" ) )
                else:
                    ClientUtils.LogText( "Whitelist=%s" % self.GetValue( "MachineListBox" ) )
                    
                ClientUtils.LogText( "LimitGroups=%s" % self.GetValue( "LimitGroupBox" ) )
                ClientUtils.LogText( "JobDependencies=%s" % self.GetValue( "DependencyBox" ) )
                ClientUtils.LogText( "OnJobComplete=%s" % self.GetValue( "OnJobCompleteBox" ) )
                
                if( bool(self.GetValue( "SubmitSuspendedBox" )) ):
                    ClientUtils.LogText( "InitialStatus=Suspended" )
            
                self.closeEvent( None )

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    scriptDialog = GuerillaDialog( args )
    scriptDialog.ShowDialog( True )
    