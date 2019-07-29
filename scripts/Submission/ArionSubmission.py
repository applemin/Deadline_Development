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
    scriptDialog.SetTitle( "Submit Arion Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Arion' ) )

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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Arion Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Arion File", 1, 0, "The Arion file to render.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Arion Files (*.rcs);;All Files (*)", 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LdrOutputLabel", "LabelControl", "LDR Output File", 2, 0, "Override the LDR output path. This is optional, and can be left blank.", False )
    scriptDialog.AddSelectionControlToGrid( "LdrOutputBox", "FileSaverControl", "", "All Files (*)", 2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "HdrOutputLabel", "LabelControl", "HDR Output File", 3, 0, "Override the HDR output path. This is optional, and can be left blank.", False )
    scriptDialog.AddSelectionControlToGrid( "HdrOutputBox", "FileSaverControl", "", "All Files (*)", 3, 1, colSpan=2 )

    passesCheckBox = scriptDialog.AddSelectionControlToGrid("EnablePassesBox","CheckBoxControl",False,"Set Passes",4, 0, "Enable to set the number of passes to use for rendering.", False )
    passesCheckBox.ValueModified.connect(passesCheckBoxChanged)
    scriptDialog.AddRangeControlToGrid( "PassesBox", "RangeControl",1,1,999999,0,1, 4, 1, expand=False )
    scriptDialog.SetEnabled("PassesBox", False)
    scriptDialog.AddHorizontalSpacerToGrid("HSpacer1", 4, 2)

    minutesCheckBox = scriptDialog.AddSelectionControlToGrid("EnableMinutesBox","CheckBoxControl",False,"Set Minutes",5, 0, "Enable to set the number of minutes to use for rendering.", False )
    minutesCheckBox.ValueModified.connect(minutesCheckBoxChanged)
    scriptDialog.AddRangeControlToGrid( "MinutesBox", "RangeControl",1,1,999999,0,1, 5, 1, expand=False )
    scriptDialog.SetEnabled("MinutesBox", False)
    
    scriptDialog.AddControlToGrid( "ThreadsLabel", "LabelControl", "Threads", 6, 0, "The number of render threads to use. Specify 0 to have Arion figure out the optimal number.", False )
    scriptDialog.AddRangeControlToGrid( "ThreadsBox", "RangeControl",0,0,256,0,1, 6, 1, expand=False )

    scriptDialog.AddControlToGrid( "CmdLabel", "LabelControl", "Command Line Args", 7, 0, "Specify additional command line arguments to use for rendering.", False )
    scriptDialog.AddControlToGrid( "CmdBox", "TextControl", "", 7, 1, colSpan=2 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Channels")
    scriptDialog.AddGrid()
    scriptDialog.AddSelectionControlToGrid("MainBox","CheckBoxControl",False,"Main", 0, 0, "Enable to render the Main channel." )
    scriptDialog.AddSelectionControlToGrid("AlphaBox","CheckBoxControl",False,"Alpha", 0, 1, "Enable to render the Alpha channel.")
    scriptDialog.AddSelectionControlToGrid("AmbientBox","CheckBoxControl",False,"Ambient", 0, 2, "Enable to render the Ambient channel.")
    scriptDialog.AddSelectionControlToGrid("AOBox","CheckBoxControl",False,"Amb Ocl", 0, 3, "Enable to render the Ambient Oclussion channel.")
    scriptDialog.AddSelectionControlToGrid("CoverageBox","CheckBoxControl",False,"Coverage", 0, 4, "Enable to render the Coverage channel." )

    scriptDialog.AddSelectionControlToGrid("DepthBox","CheckBoxControl",False,"Depth", 1, 0, "Enable to render the Depth channel.")
    scriptDialog.AddSelectionControlToGrid("DiffuseBox","CheckBoxControl",False,"Diffuse", 1, 1, "Enable to render the Diffuse channel.")
    scriptDialog.AddSelectionControlToGrid("DirectBox","CheckBoxControl",False,"Direct", 1, 2, "Enable to render the Direct channel.")
    scriptDialog.AddSelectionControlToGrid("FresnelBox","CheckBoxControl",False,"Fresnel", 1, 3, "Enable to render the Fresnel channel.")
    scriptDialog.AddSelectionControlToGrid("GlossyBox","CheckBoxControl",False,"Glossy", 1, 4, "Enable to render the Glossy channel.")

    scriptDialog.AddSelectionControlToGrid("IndirectBox","CheckBoxControl",False,"Indirect", 2, 0, "Enable to render the Indirect channel.")
    scriptDialog.AddSelectionControlToGrid("LightsBox","CheckBoxControl",False,"Lights", 2, 1, "Enable to render the Lights channel.")
    scriptDialog.AddSelectionControlToGrid("LightMixer1Box","CheckBoxControl",False,"Light Mixer 1", 2, 2, "Enable to render the Light Mixer 1 channel.")
    scriptDialog.AddSelectionControlToGrid("LightMixer2Box","CheckBoxControl",False,"Light Mixer 2", 2, 3, "Enable to render the Light Mixer 2 channel.")
    scriptDialog.AddSelectionControlToGrid("LightMixer3Box","CheckBoxControl",False,"Light Mixer 3", 2, 4, "Enable to render the Light Mixer 3 channel.")

    scriptDialog.AddSelectionControlToGrid("LightMixer4Box","CheckBoxControl",False,"Light Mixer 4", 3, 0, "Enable to render the Light Mixer 4 channel.")
    scriptDialog.AddSelectionControlToGrid("LightMixer5Box","CheckBoxControl",False,"Light Mixer 5", 3, 1, "Enable to render the Light Mixer 5 channel.")
    scriptDialog.AddSelectionControlToGrid("LightMixer6Box","CheckBoxControl",False,"Light Mixer 6", 3, 2, "Enable to render the Light Mixer 6 channel.")
    scriptDialog.AddSelectionControlToGrid("LightMixer7Box","CheckBoxControl",False,"Light Mixer 7", 3, 3, "Enable to render the Light Mixer 7 channel.")
    scriptDialog.AddSelectionControlToGrid("LightMixer8Box","CheckBoxControl",False,"Light Mixer 8", 3, 4, "Enable to render the Light Mixer 8 channel.")

    scriptDialog.AddSelectionControlToGrid("MtlIdBox","CheckBoxControl",False,"MtlId", 4, 0, "Enable to render the Material ID channel.")
    scriptDialog.AddSelectionControlToGrid("NormalsBox","CheckBoxControl",False,"Normals", 4, 1, "Enable to render the Normals channel.")
    scriptDialog.AddSelectionControlToGrid("ObjIdBox","CheckBoxControl",False,"ObjId", 4, 2, "Enable to render the Object ID channel.")
    scriptDialog.AddSelectionControlToGrid("ReflectionBox","CheckBoxControl",False,"Reflection", 4, 3, "Enable to render the Reflection channel.")
    scriptDialog.AddSelectionControlToGrid("RefractionBox","CheckBoxControl",False,"Refraction", 4, 4, "Enable to render the Refraction channel.")

    scriptDialog.AddSelectionControlToGrid("RoughnessBox","CheckBoxControl",False,"Roughness", 5, 0, "Enable to render the Roughness channel.")
    scriptDialog.AddSelectionControlToGrid("ShadowsBox","CheckBoxControl",False,"Shadow", 5, 1, "Enable to render the Shadow channel.")
    scriptDialog.AddSelectionControlToGrid("SpecularBox","CheckBoxControl",False,"Specular", 5, 2, "Enable to render the Specular channel.")
    scriptDialog.AddSelectionControlToGrid("SSSBox","CheckBoxControl",False,"SSS", 5, 3, "Enable to render the SSS channel.")
    scriptDialog.AddSelectionControlToGrid("SunBox","CheckBoxControl",False,"Sun", 5, 4, "Enable to render the Sun channel.")
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "ArionMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer2", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","LdrOutputBox","HdrOutputBox","EnablePassesBox","PassesBox","EnableMinutesBox","MinutesBox","ThreadsBox","MainBox","AlphaBox","AmbientBox","AOBox","CoverageBox","DepthBox","DiffuseBox","DirectBox","FresnelBox","GlossyBox","IndirectBox","LightsBox","LightMixer1Box","LightMixer2Box","LightMixer3Box","LightMixer4Box","LightMixer5Box","LightMixer6Box","LightMixer7Box","LightMixer8Box","MtlIdBox","NormalsBox","ObjIdBox","ReflectionBox","RefractionBox","RoughnessBox","ShadowsBox","SpecularBox","SSSBox","SunBox","CmdBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    scriptDialog.ShowDialog( False )

def passesCheckBoxChanged(**args):
    enabled = bool(scriptDialog.GetValue("EnablePassesBox"))    
    scriptDialog.SetEnabled("PassesBox", enabled)

def minutesCheckBoxChanged(**args):
    enabled = bool(scriptDialog.GetValue("EnableMinutesBox"))    
    scriptDialog.SetEnabled("MinutesBox", enabled)

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "ArionSettings.ini" )
       
def SubmitButtonPressed(*args):
    global scriptDialog
    
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "The Arion file %s does not exist" % sceneFile, "Error" )
        return
    elif PathUtils.IsPathLocal(sceneFile):
        result = scriptDialog.ShowMessageBox( "The Arion file %s is local. Are you sure you want to continue?" % sceneFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    ldrOutputfile = scriptDialog.GetValue( "LdrOutputBox" )
    if ldrOutputfile != "":
        if(not Directory.Exists(Path.GetDirectoryName(ldrOutputfile))):
            scriptDialog.ShowMessageBox( "The directory of the LDR output file %s does not exist." % Path.GetDirectoryName(ldrOutputfile), "Error" )
            return
        elif( PathUtils.IsPathLocal(ldrOutputfile) ):
            result = scriptDialog.ShowMessageBox( "The LDR output file %s is local. Are you sure you want to continue?" % ldrOutputfile, "Warning", ("Yes","No") )
            if(result=="No"):
                return
                
    hdrOutputfile = scriptDialog.GetValue( "HdrOutputBox" )
    if hdrOutputfile != "":
        if(not Directory.Exists(Path.GetDirectoryName(hdrOutputfile))):
            scriptDialog.ShowMessageBox( "The directory of the HDR output file %s does not exist." % Path.GetDirectoryName(hdrOutputfile), "Error" )
            return
        elif( PathUtils.IsPathLocal(hdrOutputfile) ):
            result = scriptDialog.ShowMessageBox( "The HDR output file %s is local. Are you sure you want to continue?" % hdrOutputfile, "Warning", ("Yes","No") )
            if(result=="No"):
                return
    
    # Do a single pass if neither are enabled otherwise Arion will render forever which isn't ideal.
    minutesEnabled = bool(scriptDialog.GetValue("EnableMinutesBox"))
    passesEnabled =  bool(scriptDialog.GetValue("EnablePassesBox"))
    if (not minutesEnabled) and (not passesEnabled):
        result = scriptDialog.ShowMessageBox( "The number of minutes or passes till completion have not been specified. This job will render indefinitely. Are you sure you want to submit this job?","Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( ):
        return
    
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "arion2_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Arion" )
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
    writer.WriteLine( "Frames=0" )
                        
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
        
    outputCount = 0
    if ldrOutputfile != "":
        writer.WriteLine( "OutputFilename%d=%s" % ( outputCount, ldrOutputfile ) )
        outputCount += 1
        
    if hdrOutputfile != "":
        writer.WriteLine( "OutputFilename%d=%s" % ( outputCount, hdrOutputfile ) )
        outputCount += 1
    
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "arion_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    writer.WriteLine("SceneFile=" + sceneFile)
    
    if ldrOutputfile != "":
        writer.WriteLine( "LdrOutputFile=%s" % ldrOutputfile )
    if hdrOutputfile != "":
        writer.WriteLine( "HdrOutputFile=%s" % hdrOutputfile )
        
    writer.WriteLine( "Threads=%s" % scriptDialog.GetValue( "ThreadsBox" ) )
    
    if minutesEnabled:
        writer.WriteLine( "Minutes=%s" % scriptDialog.GetValue( "MinutesBox" ) )
    else:
        writer.WriteLine( "Minutes=0" )
        
    if passesEnabled:
        writer.WriteLine( "Passes=%s" % scriptDialog.GetValue( "PassesBox" ) )
    else:
        writer.WriteLine(" Passes=0" )
    
    #Channels
    writer.WriteLine( "Main=%s" % scriptDialog.GetValue( "MainBox" ) )
    writer.WriteLine( "Alpha=%s" % scriptDialog.GetValue( "AlphaBox" ) )
    writer.WriteLine( "Ambient=%s" % scriptDialog.GetValue( "AmbientBox" ) )
    writer.WriteLine( "Ao=%s" % scriptDialog.GetValue( "AOBox" ) )
    writer.WriteLine( "Coverage=%s" % scriptDialog.GetValue( "CoverageBox" ) )
    writer.WriteLine( "Depth=%s" % scriptDialog.GetValue( "DepthBox" ) )
    
    writer.WriteLine( "Diffuse=%s" % scriptDialog.GetValue( "DiffuseBox" ) )
    writer.WriteLine( "Direct=%s" % scriptDialog.GetValue( "DirectBox" ) )
    writer.WriteLine( "Fresnel=%s" % scriptDialog.GetValue( "FresnelBox" ) )
    writer.WriteLine( "Glossy=%s" % scriptDialog.GetValue( "GlossyBox" ) )
    writer.WriteLine( "Indirect=%s" % scriptDialog.GetValue( "IndirectBox" ) )
    writer.WriteLine( "Lights=%s" % scriptDialog.GetValue( "LightsBox" ) )
    
    writer.WriteLine( "LightMixer1=%s" % scriptDialog.GetValue( "LightMixer1Box" ) )
    writer.WriteLine( "LightMixer2=%s" % scriptDialog.GetValue( "LightMixer2Box" ) )
    writer.WriteLine( "LightMixer3=%s" % scriptDialog.GetValue( "LightMixer3Box" ) )
    writer.WriteLine( "LightMixer4=%s" % scriptDialog.GetValue( "LightMixer4Box" ) )
    writer.WriteLine( "LightMixer5=%s" % scriptDialog.GetValue( "LightMixer5Box" ) )
    writer.WriteLine( "LightMixer6=%s" % scriptDialog.GetValue( "LightMixer6Box" ) )
    
    writer.WriteLine( "LightMixer7=%s" % scriptDialog.GetValue( "LightMixer7Box" ) )
    writer.WriteLine( "LightMixer8=%s" % scriptDialog.GetValue( "LightMixer8Box" ) )
    writer.WriteLine( "MtlId=%s" % scriptDialog.GetValue( "MtlIdBox" ) )
    writer.WriteLine( "Normals=%s" % scriptDialog.GetValue( "NormalsBox" ) )
    writer.WriteLine( "ObjId=%s" % scriptDialog.GetValue( "ObjIdBox" ) )
    writer.WriteLine( "Reflection=%s" % scriptDialog.GetValue( "ReflectionBox" ) )
    
    writer.WriteLine( "Refraction=%s" % scriptDialog.GetValue( "RefractionBox" ) )
    writer.WriteLine( "Roughness=%s" % scriptDialog.GetValue( "RoughnessBox" ) )
    writer.WriteLine( "Shadows=%s" % scriptDialog.GetValue( "ShadowsBox" ) )
    writer.WriteLine( "Specular=%s" % scriptDialog.GetValue( "SpecularBox" ) )
    writer.WriteLine( "SSS=%s" % scriptDialog.GetValue( "SSSBox" ) )
    writer.WriteLine( "Sun=%s" % scriptDialog.GetValue( "SunBox" ) )
    
    # Additional Arguments
    writer.WriteLine( "AdditionalArgs=%s" % scriptDialog.GetValue("CmdBox") )

    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
