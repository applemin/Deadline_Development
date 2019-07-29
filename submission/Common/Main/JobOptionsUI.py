from System.IO import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

class JobOptionsDialog( DeadlineScriptDialog ):
    settings = None
    
    def __init__( self, parentAppName="", parent=None ):
        super( JobOptionsDialog, self ).__init__( parent )

        self.parentAppName = parentAppName

        self.AddGrid()
        self.AddControlToGrid( "JobDescriptionSeparator", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

        self.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "<html><head/><body><p>The name of your job. This is optional, and if left blank, it will default to 'Untitled'.</p></body></html>", False )
        self.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

        self.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "<html><head/><body><p>A simple description of your job. This is optional and can be left blank.</p></body></html>", False )
        self.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

        self.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "<html><head/><body><p>The department you belong to. This is optional and can be left blank.</p></body></html>", False )
        self.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid( "JobOptionsSeparator", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

        self.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
        self.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

        self.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "<html><head/><body><p>The secondary pool lets you specify a pool to use if the primary pool does not have any available Slaves.</p></body></html>", False )
        self.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

        self.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
        self.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

        maxPriority = RepositoryUtils.GetMaximumPriority()
        self.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "<html><head/><body><p>A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.</p></body></html>", False )
        self.AddRangeControlToGrid( "PriorityBox", "RangeControl", maxPriority / 2, 0, maxPriority, 0, 1, 4, 1 )

        self.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "<html><head/><body><p>The number of minutes a Slave has to render a task for this job before it requeues it. Specify 0 for no limit.</p></body></html>", False )
        self.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
        self.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "<html><head/><body><p>If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job.</p></body></html>" )

        self.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "<html><head/><body><p>The number of tasks that can render concurrently on a single Slave. This is useful if the rendering application only uses one thread to render and your Slaves have multiple CPUs.</p></body></html>", False )
        self.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
        self.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "<html><head/><body><p>If you limit the tasks to a Slave's task limit, then by default, the Slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual Slaves by an administrator.</p></body></html>" )

        self.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "<html><head/><body><p>Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.</p></body></html>", False )
        self.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
        self.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "<html><head/><body><p>You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist.</p></body></html>" )

        self.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "The whitelisted or blacklisted list of machines.", False )
        self.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

        self.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
        self.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

        self.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "<html><head/><body><p>Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.</p></body></html>", False )
        self.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

        self.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
        self.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
        self.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "<html><head/><body><p>If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.</p></body></html>" )
        self.EndGrid()
        
        settings =  ( "NameBox", "DepartmentBox", "PoolBox", "SecondaryPoolBox", "GroupBox", "PriorityBox", "MachineLimitBox",
        "IsBlacklistBox", "MachineListBox", "LimitGroupBox", "CommentBox", "ConcurrentTasksBox", "LimitConcurrentTasksBox",
        "DependencyBox", "OnJobCompleteBox", "SubmitSuspendedBox" )

        self.LoadSettings( self.GetSettingsFilename(), settings )
        self.EnabledStickySaving( settings, self.GetSettingsFilename() )
        self.SaveSettings( self.GetSettingsFilename(), settings )
        
    def GetSettingsFilename( self ):
        return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), self.parentAppName + "JobOptions.ini" )

    def GetJobOptionsValues( self ):
        values = {}
        
        values["Name"] = self.GetValue( "NameBox" )
        values["Comment"] = self.GetValue( "CommentBox" )
        values["Department"] = self.GetValue( "DepartmentBox" )
        values["Pool"] = self.GetValue( "PoolBox" )
        values["SecondaryPool"] = self.GetValue( "SecondaryPoolBox" )
        values["Group"] = self.GetValue( "GroupBox" )
        values["Priority"] = self.GetValue( "PriorityBox" )
        values["TaskTimeoutMinutes"] = self.GetValue( "TaskTimeoutBox" )
        values["EnableAutoTimeout"] = self.GetValue( "AutoTimeoutBox" )
        values["ConcurrentTasks"] = self.GetValue( "ConcurrentTasksBox" )
        values["LimitConcurrentTasksToNumberOfCpus"] = self.GetValue( "LimitConcurrentTasksBox" )
        values["MachineLimit"] = self.GetValue( "MachineLimitBox" )
        
        if( bool(self.GetValue( "IsBlacklistBox" )) ):
            values["Blacklist"] = self.GetValue( "MachineListBox" )
        else:
            values["Whitelist"] = self.GetValue( "MachineListBox" )
        
        values["LimitGroups"] = self.GetValue( "LimitGroupBox" )
        values["JobDependencies"] = self.GetValue( "DependencyBox" )
        values["OnJobComplete"] = self.GetValue( "OnJobCompleteBox" )
        values["InitialStatus"] = "Active"
        
        if( bool( self.GetValue( "SubmitSuspendedBox" ) ) ):
            values["InitialStatus"] = "Suspended"
        
        return values