from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

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
appSubmission=False

ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = False

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Composite Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Composite' ) )

    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2)

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
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Composite Options", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid("ProjectLabel","LabelControl","Project File", 1, 0, "Path to the project file. ", False)
    scriptDialog.AddSelectionControlToGrid("ProjectBox","FileBrowserControl","","Projects (*.txproject)", 1, 1, colSpan=3)

    scriptDialog.AddControlToGrid("CompositionLabel","LabelControl","Composition",2, 0, "Path to the composition file.", False)
    scriptDialog.AddSelectionControlToGrid("CompositionBox","FileBrowserControl","","Compositions (*.txcomposition)",2, 1, colSpan=3)

    scriptDialog.AddControlToGrid("VersionLabel","LabelControl","Composition Version", 3, 0, "The version of the current composition selected. ", False)
    scriptDialog.AddControlToGrid("VersionBox","TextControl","", 3, 1, colSpan=3)

    scriptDialog.AddControlToGrid("UsersFileLabel","LabelControl","User File", 4, 0, "The path to the user.ini file for this composition. ", False)
    scriptDialog.AddSelectionControlToGrid("UsersFileBox","FileBrowserControl","","User Files (*.txuser *.ini);;All Files (*)", 4, 1, colSpan=3)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 5, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 5, 1)
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 5, 2, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 5, 3 )

    scriptDialog.AddControlToGrid( "CompositeVersionLabel", "LabelControl", "Version", 6, 0, "The version of Composite to render with.", False )
    scriptDialog.AddComboControlToGrid( "CompositeVersionBox", "ComboControl", "2012", ( "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017" ), 6, 1 )
    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build to Force", 6, 2, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ( "None", "32bit", "64bit" ), 6, 3 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "CompositeMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )

    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)

    scriptDialog.EndGrid()
    
    #Application Box must be listed before version box or else the application changed event will change the version
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","FramesBox","ChunkSizeBox","ProjectBox","CompositionBox","VersionBox","UsersFileBox","CompositeVersionBox","BuildBox")	
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    
    appSubmission = LoadContext()
    if appSubmission:
        # Keep the submission window above all other windows when submitting from another app.
        scriptDialog.MakeTopMost()
    else:
        scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
        
    scriptDialog.ShowDialog( appSubmission )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "CompositeSettings.ini" )
    
def LoadContext():
    global scriptDialog
    global appSubmission
    
    tempDir = ClientUtils.GetDeadlineTempPath()
    iniFilePath = tempDir + "/compositeapplicationsettings.ini"
    
    if(File.Exists(iniFilePath)):
        appSubmission=True
        iniFile = open(iniFilePath,"r")
        
        currline = iniFile.readline().strip().replace("\n","")
        
        startframe = None
        endframe = None
        
        while(currline != ""):
            index =currline.find("=")
            if(currline.startswith("Database=")):
                scriptDialog.SetValue("ProjectBox",currline[index+1:len(currline)])
            elif(currline.startswith("Composition=")):
                composition = currline[index+1:len(currline)]
                scriptDialog.SetValue("CompositionBox",composition)
                scriptDialog.SetValue("NameBox",Path.GetFileNameWithoutExtension(composition))
            elif(currline.startswith("Version=")):
                scriptDialog.SetValue("VersionBox",currline[index+1:len(currline)])
            elif(currline.startswith("StartFrame=")):
                startframe = currline[index+1:len(currline)]
            elif(currline.startswith("EndFrame=")):
                endframe = currline[index+1:len(currline)]
            elif(currline.startswith("Userfile=")):
                scriptDialog.SetValue("UsersFileBox",currline[index+1:len(currline)])
            elif(currline.startswith("CompositeVersion=")):
                scriptDialog.SetValue("CompositeVersionBox",currline[index+1:len(currline)])
            elif(currline.startswith("Build=")):
                scriptDialog.SetValue("BuildBox",currline[index+1:len(currline)])
                    
            currline = iniFile.readline().strip().replace("\n","")
            
        if(endframe != None and startframe != None):
            startFrameNumber = int(startframe)
            endFrameNumber = int(endframe)
            if endFrameNumber > startFrameNumber:
                endFrameNumber = endFrameNumber - 1
            
            scriptDialog.SetValue("FramesBox",str(startFrameNumber) + "-" + str(endFrameNumber))
            
        iniFile.close()
        File.Delete(iniFilePath)
        
        return True
    else:
        return False
  
def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog
    
    version = scriptDialog.GetValue("CompositeVersionBox")
    
    # Check the project file
    projectFile = scriptDialog.GetValue( "ProjectBox" )
    if not File.Exists( projectFile ):
        scriptDialog.ShowMessageBox( "Project file " + projectFile + " does not exist.", "Error" )
        return
    elif version == "2008" and PathUtils.IsPathLocal( projectFile ):
        result = scriptDialog.ShowMessageBox( "Project file " + projectFile + " is local. Are you sure you want to continue?","Warning",("Yes","No"))
        if result != "Yes":
            return
    
    # Check the comp file if we are using version 2009
    compFile = scriptDialog.GetValue( "CompositionBox" )
    if version != "2008" and not File.Exists( compFile ):
        scriptDialog.ShowMessageBox( "Composition file " + compFile + " does not exist.", "Error" )
        return
    
    # Check the users ini file
    usersfile = scriptDialog.GetValue("UsersFileBox")
    if len(usersfile) > 0:
        if not File.Exists( usersfile ):
            scriptDialog.ShowMessageBox( "Users file " + usersfile + " does not exist.", "Error" )
            return

    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return
        
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( ):
        return
    
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "composite_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Composite" )
    writer.WriteLine( "Name=%s" % jobName )
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "composite_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    if version == "2008":
        writer.WriteLine( "ProjectFile=" + projectFile )
        writer.WriteLine( "Composition=" + compFile )
    writer.WriteLine( "CompositionVersion=" + scriptDialog.GetValue( "VersionBox" ) )
    writer.WriteLine( "Version=" + version )
    writer.WriteLine( "Build=" + scriptDialog.GetValue( "BuildBox" ) )
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    if version != "2008":
        arguments.Add( projectFile )
        arguments.Add( compFile )
    
    if len(usersfile) > 0:
        arguments.Add( usersfile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
