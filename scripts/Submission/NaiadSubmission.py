from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text.RegularExpressions import *

from Deadline.Scripting import *

import re

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
empToPrtJobBox = None
settings = None
projectPath = ""

ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = False


########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global empToPrtJobBox
    global settings
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Naiad Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Naiad' ) )
    
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
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

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

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering. ", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render. " )
    scriptDialog.EndGrid()

    #Naiad Options
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Naiad Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Naiad File", 1, 0, "The Naiad file to simulate.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Naiad Files (*.ni);;All Files (*)", 1, 1, colSpan=2 )
    sceneBox.ValueModified.connect(SceneBoxChanged)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 2, 0, "The list of frames to simulate.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 2, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Naiad File With Job", 2, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering." )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 3, 1 )
    
    scriptDialog.EndGrid()
    
    #Naiad Simulation Options
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "Naiad Simulation Job", 0, 0, colSpan=2 )

    simJobBox = scriptDialog.AddSelectionControlToGrid( "SimJobBox", "CheckBoxControl", True, "Submit Simulation Job", 1, 0, "Enable to submit a Simulation job to Deadline.", False )
    simJobBox.ValueModified.connect(SimJobBoxChanged)
    scriptDialog.AddSelectionControlToGrid("SingleMachineBox","CheckBoxControl",False,"Run Simulation On A Single Machine", 1, 1, "If enabled, the simluation job will be submitted as a single task consisting of all frames so that a single machine runs the entire simulation.")
    scriptDialog.EndGrid()
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "ThreadsLabel", "LabelControl", "Threads", 0, 0, "The number of render threads to use. Specify 0 to let Naiad determine the number of threads to use.", False )
    scriptDialog.AddRangeControlToGrid( "ThreadsBox", "RangeControl", 0, 0, 1024, 0, 1, 0, 1 )
    scriptDialog.AddSelectionControlToGrid( "VerboseBox", "CheckBoxControl", False, "Enable Verbose Logging", 0, 2, "Enables verbose logging during the simulation." )
    scriptDialog.EndGrid()

    #Naiad Prt Conversion Options
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "EMP to PRT Conversion Job", 0, 0, colSpan=2 )

    empToPrtJobBox = scriptDialog.AddSelectionControlToGrid( "EmpToPrtBox", "CheckBoxControl", False, "Submit EMP to PRT Conversion Job", 1, 0, "Enable to submit a PRT Conversion job to Deadline.", colSpan=2 )
    empToPrtJobBox.ValueModified.connect(EmpToPrtJobBoxChanged)

    scriptDialog.AddControlToGrid( "EMPBodyLabel", "LabelControl", "EMP Body Name", 2, 0, "The EMP body name.", False )
    initBodyNames = ()
    scriptDialog.AddComboControlToGrid("EMPBodyBox","ComboControl","", initBodyNames , 2, 1)

    scriptDialog.AddControlToGrid( "EMPFileLabel", "LabelControl", "EMP Body File Name", 3, 0, "The path to the EMP files to be converted.", False )
    initBodyFileNames = ()
    scriptDialog.AddComboControlToGrid("EMPBodyFilenameBox","ComboControl","", initBodyFileNames ,3, 1)
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "NaiadMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ("NameBox","DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","SubmitSceneBox", "SimJobBox", "EmpToPrtBox", "ThreadsBox", "VerboseBox", "SingleMachineBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    if len(args) > 0:
        if args[0] != "":
            scriptDialog.SetValue( "SceneBox", args[0] )
    
    SceneBoxChanged(None)
    SimJobBoxChanged(None)
    EmpToPrtJobBoxChanged(None)
        
    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "NaiadSettings.ini" )

def SimJobBoxChanged( *args ):
    global scriptDialog
    global empToPrtJobBox
    
    simEnabled = scriptDialog.GetValue( "SimJobBox" )
    scriptDialog.SetEnabled( "ThreadsLabel", simEnabled )
    scriptDialog.SetEnabled( "ThreadsBox", simEnabled )
    scriptDialog.SetEnabled( "VerboseBox", simEnabled )
    
    if simEnabled:
        empToPrtJobBox.Text = "Submit an EMP to PRT Conversion Job (uses EMP files from Simulation job)"
    else:
        empToPrtJobBox.Text = "Submit an EMP to PRT Conversion Job (EMP files must already exist)"
    
    empToPrtEnabled = scriptDialog.GetValue( "EmpToPrtBox" )
    scriptDialog.SetEnabled( "SubmitButton", simEnabled or empToPrtEnabled )
    
def EmpToPrtJobBoxChanged( *args ):
    global scriptDialog
    
    empToPrtEnabled = scriptDialog.GetValue( "EmpToPrtBox" )
    scriptDialog.SetEnabled( "EMPBodyLabel", empToPrtEnabled )
    scriptDialog.SetEnabled( "EMPBodyBox", empToPrtEnabled )
    scriptDialog.SetEnabled( "EMPFileLabel", empToPrtEnabled )
    scriptDialog.SetEnabled( "EMPBodyFilenameBox", empToPrtEnabled )
    
    scriptDialog.SetEnabled( "ConcurrentTasksLabel", empToPrtEnabled )
    scriptDialog.SetEnabled( "ConcurrentTasksBox", empToPrtEnabled )
    scriptDialog.SetEnabled( "LimitConcurrentTasksBox", empToPrtEnabled )
        
    simEnabled = scriptDialog.GetValue( "SimJobBox" )
    scriptDialog.SetEnabled( "SubmitButton", simEnabled or empToPrtEnabled )

def SceneBoxChanged( *args ):
    global scriptDialog
    global projectPath
    
    empBodyNamesList = []
    empBodyFileNamesList = []
    
    firstFrame = ""
    lastFrame = ""
    
    sceneName = scriptDialog.GetValue( "SceneBox" )
    if File.Exists( sceneName ):
        f = open(sceneName, 'r')
        niFile = f.read()
        f.close()
        
        firstFrameRe = re.search('SetParam \"Global.First Frame\" \"([^\"]+)\"',niFile)
        if (firstFrameRe != None):
            firstFrame = firstFrameRe.group(1)
        
        lastFrameRe = re.search('SetParam \"Global.Last Frame\" \"([^\"]+)\"',niFile)
        if (lastFrameRe != None):
            lastFrame = lastFrameRe.group(1)
        
        globalPathRe = re.search('SetParam \"Global.Project Path\" \"([^\"]+)\"',niFile)
        if (globalPathRe != None):
            projectPath = globalPathRe.group(1)            
        
        allBodies = re.findall('Create BODY_OP Particle-Liquid \"([^\"]+)\"',niFile)
        for bodyName in allBodies:
            empBodyName = re.search(bodyName + '.Body Name\" \"([^\"]+)\"',niFile)
            if (empBodyName != None):
                empBodyNamesList.append(empBodyName.group(1))    
        #    empBodyName = re.search(bodyName + '.EMP Cache\" \"([^\"]+)\"',niFile)
        #    if (empBodyName != None):
        #        empBodyNamesList.append(empBodyName.group(1))
        
        allBodies = re.findall('Create BODY_OP Particle \"([^\"]+)\"',niFile)
        for bodyName in allBodies:
            empBodyName = re.search(bodyName + '.Body Name\" \"([^\"]+)\"',niFile)
            if (empBodyName != None):
                empBodyNamesList.append(empBodyName.group(1))    

        allBodies = re.findall('Create BODY_OP Emp-Terminal \"([^\"]+)\"',niFile)
        for bodyName in allBodies:
            empBodyName = re.search(bodyName + '.EMP Cache\" \"([^\"]+)\"',niFile)
            if (empBodyName != None):
                empBodyFileNamesList.append(empBodyName.group(1))
        
        allBodies = re.findall('Create BODY_OP Emp-Write \"([^\"]+)\"',niFile)
        for bodyName in allBodies:
            empBodyName = re.search(bodyName + '.EMP Cache\" \"([^\"]+)\"',niFile)
            if (empBodyName != None):
                empBodyFileNamesList.append(empBodyName.group(1))
    
    if len(empBodyNamesList) == 0:
        empBodyNamesList.append( "" )
    scriptDialog.SetItems("EMPBodyBox", tuple(empBodyNamesList))
    scriptDialog.SetValue("EMPBodyBox", empBodyNamesList[0])

    if len(empBodyFileNamesList) == 0:
        empBodyFileNamesList.append( "" )
    scriptDialog.SetItems("EMPBodyFilenameBox", tuple(empBodyFileNamesList))
    scriptDialog.SetValue("EMPBodyFilenameBox", empBodyFileNamesList[0])
    
    if firstFrame != "" and lastFrame != "":
        if firstFrame == lastFrame:
            scriptDialog.SetValue("FramesBox", firstFrame)
        else:
            scriptDialog.SetValue("FramesBox", firstFrame + "-" + lastFrame)

    fileNamePrefix = Path.GetFileNameWithoutExtension( sceneName )
    if len(fileNamePrefix) > 0:
        scriptDialog.SetValue("NameBox", fileNamePrefix)
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    global projectPath
    global integration_dialog
    
    submitSimJob = scriptDialog.GetValue( "SimJobBox" )
    submitEmpToPrtJob = scriptDialog.GetValue( "EmpToPrtBox" )
    
    if not submitSimJob and scriptDialog.GetValue( "ShotgunSubmitBox" ):
        scriptDialog.ShowMessageBox( "A Shotgun version can only be created if submitting a Simulation job.", "Error" )
        return
    
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
    
    empBody = scriptDialog.GetValue( "EMPBodyBox" )
    empBodyFilename = scriptDialog.GetValue( "EMPBodyFilenameBox" )
    
    # Only check the scene file if we're doing a simulation
    if submitSimJob:
        if not File.Exists( sceneFile ):
            scriptDialog.ShowMessageBox( "Naiad file %s does not exist" % sceneFile, "Error" )
            return
        if submitScene and PathUtils.IsPathLocal( sceneFile ):
            result = scriptDialog.ShowMessageBox( "The Naiad file " + sceneFile + " is local and is not being submitted with the job, are you sure you want to continue", "Warning", ("Yes","No") )
            if( result == "No" ):
                return
    
    # Only check the emp info if doing a emp to prt conversion
    if submitEmpToPrtJob:
        if empBody == "":
            scriptDialog.ShowMessageBox( "No EMP Body Name has been selected" , "Error" )
            return
        if empBodyFilename == "":
            scriptDialog.ShowMessageBox( "No EMP Body File Name has been selected" , "Error" )
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
    singleMachineSim = scriptDialog.GetValue( "SingleMachineBox" )

    # Build up the arguments
    arguments = StringCollection()
    arguments.Add( "-multi" )
    arguments.Add( "-dependent" )
    
    batchJob = False
    if submitSimJob and submitEmpToPrtJob:
        batchJob = True
    
    if submitSimJob:
        
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "naiad_sim_job_info.job" )
        writer = File.CreateText( jobInfoFilename )
        writer.WriteLine( "Plugin=Naiad" )
        writer.WriteLine( "Name=%s" % (jobName + " (Simulation Job)") )
        if batchJob:
            writer.WriteLine( "BatchName=%s" % (jobName) )
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
        writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        writer.WriteLine( "Frames=%s" % frames )
        
        if singleMachineSim:
            writer.WriteLine( "ChunkSize=1000000" )
            writer.WriteLine( "MachineLimit=1" )
        else:
            writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
            writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
            writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "ConcurrentTasksBox" ) )
            writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
            
        if scriptDialog.GetValue( "IsBlacklistBox" ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            
        if scriptDialog.GetValue( "SubmitSuspendedBox" ):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        # Integration
        extraKVPIndex = 0
        groupBatch = False
        
        if integration_dialog.IntegrationProcessingRequested():
            extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()
        
        if groupBatch:
            writer.WriteLine( "BatchName=%s\n" % (jobName ) ) 
        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "naiad_sim_plugin_info.job" )
        writer = File.CreateText( pluginInfoFilename )
        if not submitScene:
            writer.WriteLine( "SceneFile=%s" % sceneFile )
        writer.WriteLine( "JobMode=Simulation" )
        writer.WriteLine( "Threads=%s" % scriptDialog.GetValue( "ThreadsBox" ) )
        writer.WriteLine( "Verbose=%s" % scriptDialog.GetValue( "VerboseBox" ) )
        writer.Close()
        
        arguments.Add( "-job" )
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        if submitScene:
            arguments.Add( sceneFile )
    
    if submitEmpToPrtJob:
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "naiad_prt_job_info.job" )
        writer = File.CreateText( jobInfoFilename )
        writer.WriteLine( "Plugin=Naiad" )
        writer.WriteLine( "Name=%s" % (jobName + " (Emp2Prt Job)") )
        if batchJob:
            writer.WriteLine( "BatchName=%s" % (jobName) )
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
        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        if not singleMachineSim:
            writer.WriteLine( "IsFrameDependent=True" )
        
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
        
        if scriptDialog.GetValue( "IsBlacklistBox" ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            
        if scriptDialog.GetValue( "SubmitSuspendedBox" ):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "naiad_prt_plugin_info.job" )
        writer = File.CreateText( pluginInfoFilename )
        if not submitScene:
            writer.WriteLine( "SceneFile=%s" % sceneFile )
        writer.WriteLine( "JobMode=Emp2Prt" )
        writer.WriteLine( "EmpBodyName=%s" % empBody )
        if not Path.IsPathRooted( empBodyFilename ):
            empBodyFilename = Path.Combine( projectPath, scriptDialog.GetValue( "EMPBodyFilenameBox" ) )
        writer.WriteLine( "EmpFileName=%s" % empBodyFilename )       
        writer.Close()
        
        arguments.Add( "-job" )
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        if submitScene:
            arguments.Add( sceneFile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
