import re
import os
import stat

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text.RegularExpressions import *

from FranticX.Processes import *
from FranticX import Environment2

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return CmdPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Cmd plugin.
######################################################################
class CmdPlugin( DeadlinePlugin ):
    MyCmdController = None
    VRaySpawner = None
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob
        self.MonitoredManagedProcessExitCallback += self.MonitoredManagedProcessExit

        self.VrayDBRJob = False
        self.VrayRtDBRJob = False
        self.MentalRayDBRJob = False
        self.Prefix = ""
    
    def Cleanup( self ):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback
        del self.MonitoredManagedProcessExitCallback

        if self.MyCmdController:
            self.MyCmdController.Cleanup()
            del self.MyCmdController

        if self.VRaySpawner:
            self.VRaySpawner.Cleanup()
            del self.VRaySpawner

    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.LogInfo( "3dsCmd Plugin Initializing..." )
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Advanced
        self.HideDosWindow = True

        self.LogInfo( "Slave Running as Service: %s" % self.IsRunningAsService() )

    ## Called by Deadline when the job is first loaded.
    def StartJob( self ):
        self.LogInfo( "Start Job called - starting up 3dsCmd plugin" )

        self.MyCmdController = CmdController( self )
        
        # If this is a DBR job, we can't load 3dsmaxcmd until we know which task we are (which isn't until the RenderTasks phase).
        self.VrayDBRJob = self.GetBooleanPluginInfoEntryWithDefault( "VRayDBRJob", False )
        self.VrayRtDBRJob = self.GetBooleanPluginInfoEntryWithDefault( "VRayRtDBRJob", False )
        self.MentalRayDBRJob = self.GetBooleanPluginInfoEntryWithDefault( "MentalRayDBRJob", False )
        
        if self.VrayDBRJob or self.VrayRtDBRJob or self.MentalRayDBRJob:
            if self.VrayDBRJob:
                self.Prefix = "V-Ray DBR: "
            elif self.VrayRtDBRJob:
                self.Prefix = "V-Ray RT DBR: "
            else:
                self.Prefix = "Mental Ray Satellite: "
            
            self.LogInfo( self.Prefix + "Delaying load of 3dsmaxcmd until RenderTasks phase" )
        else:
            # Initialize the Cmd controller.
            self.MyCmdController.Initialize()

    ## Called by Deadline when the job is unloaded.
    def EndJob( self ):
        self.LogInfo( "End Job called - shutting down 3dsCmd plugin" )

        # Nothing to do during EndJob phase for DBR jobs.
        if self.VrayDBRJob or self.VrayRtDBRJob or self.MentalRayDBRJob:
            return

        if self.MyCmdController:
            # End the 3dsmaxcmd job.
            self.MyCmdController.EndCmdJob()

    ## Called by Deadline when a task is to be rendered.
    def RenderTasks( self ):
        self.LogInfo( "Render Tasks called" )

        # For V-RayDBRJob jobs, task 0 can't render until all the other tasks have been picked up unless Dynamic Start is enabled.
        if self.VrayDBRJob or self.VrayRtDBRJob or self.MentalRayDBRJob:

            if self.GetCurrentTaskId() == "0":

                currentJob = self.GetJob()
                RepositoryUtils.SetMachineLimitListedSlaves( currentJob.JobId, [] )

                slaveName = self.GetCurrentTask().TaskSlaveName
                self.LogInfo( "Releasing DBR job as MASTER has now been elected: %s" % slaveName )

                # Initialize the Max controller.
                self.MyCmdController.Initialize()
                
                self.LogInfo( self.Prefix + "Configuring Distributed Render Job..." )

                # Load settings.
                if self.VrayDBRJob:
                    self.MyCmdController.GetVrayDBRSettings()
                    self.LogInfo( self.Prefix + "Dynamic Start: %s" % self.MyCmdController.VrayDBRDynamicStart )
                    self.LogInfo( self.Prefix + "Plugin Config Settings to be applied to local file: vray_dr.cfg" )
                    self.LogInfo( self.Prefix + "Port Range: %s" % self.MyCmdController.VrayDBRPortRange )
                    self.LogInfo( self.Prefix + "Use Local Machine: %s" % self.MyCmdController.VrayDBRUseLocalMachine )
                    self.LogInfo( self.Prefix + "Transfer Missing Assets: %s" % self.MyCmdController.VrayDBRTransferMissingAssets )
                    self.LogInfo( self.Prefix + "Use Cached Assets: %s" % self.MyCmdController.VrayDBRUseCachedAssets )
                    self.LogInfo( self.Prefix + "Cache Limit Type: %s" % self.MyCmdController.VrayDBRCacheLimitType )
                    self.LogInfo( self.Prefix + "Cache Limit: %s" % self.MyCmdController.VrayDBRCacheLimit )
                elif self.VrayRtDBRJob:
                    self.MyCmdController.GetVrayRtDBRSettings()
                    self.LogInfo( self.Prefix + "Dynamic Start: %s" % self.MyCmdController.VrayRtDBRDynamicStart )
                    self.LogInfo( self.Prefix + "Plugin Config Settings to be applied to local file: vrayrt_dr.cfg" )
                    self.LogInfo( self.Prefix + "Port Range: %s" % self.MyCmdController.VrayRtDBRPortRange )
                    self.LogInfo( self.Prefix + "Auto-Start Local Slave: %s" % self.MyCmdController.VrayRtDBRAutoStartLocalSlave )
                else:
                    self.MyCmdController.GetMentalRaySettings()
                    self.LogInfo( self.Prefix + "Satellite Port Number: %s" % self.MyCmdController.MentalRaySatPortNumber )

                # If job uses V-Ray Dynamic Start and V-Ray Use Local Host is Enabled than start immediately.
                if (self.VrayDBRJob and self.MyCmdController.VrayDBRDynamicStart and self.MyCmdController.VrayDBRUseLocalMachine) or \
                (self.VrayRtDBRJob and self.MyCmdController.VrayRtDBRDynamicStart and self.MyCmdController.VrayRtDBRAutoStartLocalSlave):
                    # Start job immediately before all tasks have been dequeued.
                    self.LogInfo( self.Prefix + "Starting distributed render immediately" )
                
                # If job uses V-Ray Dynamic Start and V-Ray Use Local Host is Disabled than wait for at least one job task to start.
                elif (self.VrayDBRJob and self.MyCmdController.VrayDBRDynamicStart and not self.MyCmdController.VrayDBRUseLocalMachine) or \
                (self.VrayRtDBRJob and self.MyCmdController.VrayRtDBRDynamicStart and not self.MyCmdController.VrayRtDBRAutoStartLocalSlave):
                    # Wait until at least one job task start
                    self.LogInfo( self.Prefix + "Waiting for at least one job task other than master node to start rendering before starting distributed render" )
                    while True:
                        if self.IsCanceled():
                            self.FailRender( "Task canceled" )
                        
                        updatedJob = RepositoryUtils.GetJob( currentJob.JobId, True )
                        # Wait until there are more rendering tasks then just a master node.
                        if updatedJob.JobRenderingTasks > 1:
                            break
                        
                        # Sleep a bit so that we're not constantly polling the job.
                        SystemUtils.Sleep( 5000 )

                    self.LogInfo( self.Prefix + "At least one job task other than master node is rendering, setting up distributed config file" )

                # If job does not use V-Ray Dynamic Start then wait for all job tasks to dequeue.
                else:
                    # Wait until the job has no queued tasks left.
                    self.LogInfo( self.Prefix + "Waiting for all job tasks to be dequeued before starting distributed render" )
                    while True:
                        if self.IsCanceled():
                            self.FailRender( "Task canceled" )
                        
                        # When checking for queued tasks, take into account a potential queued post job task.
                        updatedJob = RepositoryUtils.GetJob( currentJob.JobId, True )
                        if updatedJob.JobQueuedTasks == 0 or (updatedJob.JobPostJobScript != "" and updatedJob.JobQueuedTasks <= 1):
                            break
                        
                        # Sleep a bit so that we're not constantly polling the job.
                        SystemUtils.Sleep( 5000 )

                    self.LogInfo( self.Prefix + "All tasks dequeued, setting up distributed config file" )

                # Get any global DBR settings.
                self.MyCmdController.GetDBRSettings()
                self.LogInfo( self.Prefix + "Use IP Address instead of Hostname: %s" % self.MyCmdController.DBRUseIPAddresses )

                # Get the list of machines currently rendering the job.
                self.MyCmdController.DBRMachines = self.MyCmdController.GetDBRMachines()

                if len(self.MyCmdController.DBRMachines) > 0:
                    self.LogInfo( self.Prefix + "Commencing distributed render with the following machines:" )
                    for machine in self.MyCmdController.DBRMachines:
                        self.LogInfo( self.Prefix + "  " + machine )
                else:
                    self.LogInfo( self.Prefix + "0 machines available currently to DBR, local machine will be used unless configured in plugin settings to be ignored" )
                
                # Now get the config file.
                self.MyCmdController.DBRConfigFile = self.MyCmdController.GetDBRConfigFile()
                backupConfigFile = Path.Combine( self.GetJobsDataDirectory(), Path.GetFileName( self.MyCmdController.DBRConfigFile ) )
                
                if( File.Exists( self.MyCmdController.DBRConfigFile ) ):

                    # Check file permissions on config file.
                    fileAtt = os.stat( self.MyCmdController.DBRConfigFile )[0]
                    if (not fileAtt & stat.S_IWRITE):
                        # File is read-only, so make it writeable
                        try:
                            self.LogInfo( self.Prefix + "Config File is read-only. Attempting to set the file to be writeable" )
                            os.chmod( self.MyCmdController.DBRConfigFile, stat.S_IWRITE )
                        except:
                            self.FailRender( "FAILED to make the config file writeable. Check Permissions!" )

                    self.LogInfo( self.Prefix + "Backing up original config file to: " + backupConfigFile )
                    File.Copy( self.MyCmdController.DBRConfigFile, backupConfigFile, True )
                    self.LogInfo( self.Prefix + "Deleting original config file: " + self.MyCmdController.DBRConfigFile )
                    File.Delete( self.MyCmdController.DBRConfigFile )
                else:
                    self.LogInfo( self.Prefix + "Skipping backup and deletion of original config file as it does not exist" )

                # Construct the V-Ray/V-RayRT/Mental Ray DR cfg file based on plugin config settings.
                if self.VrayDBRJob:
                    self.MyCmdController.UpdateVrayDBRConfigFile( self.MyCmdController.DBRMachines, self.MyCmdController.DBRConfigFile )
                elif self.VrayRtDBRJob:
                    self.MyCmdController.UpdateVrayRtDBRConfigFile( self.MyCmdController.DBRMachines, self.MyCmdController.DBRConfigFile )
                else:
                    self.MyCmdController.UpdateMentalRayConfigFile( self.MyCmdController.DBRMachines, self.MyCmdController.DBRConfigFile )
                
                self.LogInfo( self.Prefix + "Config file created: " + self.MyCmdController.DBRConfigFile )
                
                if self.VrayDBRJob or self.VrayRtDBRJob:
                    # Sleeping a bit for now to give V-Ray Spawner time to initialize on other machines.
                    self.LogInfo( self.Prefix + "Waiting 10 seconds to give V-Ray Spawner time to initialize on other machines" )
                    SystemUtils.Sleep( 10000 )
                
                self.LogInfo( self.Prefix + "Ready to go, moving on to distributed render" )

                # Render the tasks.
                self.MyCmdController.RenderTasks()
                
                if( File.Exists( backupConfigFile ) ):
                    self.LogInfo( self.Prefix + "Restoring backup config file: %s to original location: %s" % ( backupConfigFile, self.MyCmdController.DBRConfigFile )  )
                    File.Copy( backupConfigFile, self.MyCmdController.DBRConfigFile, True )
                else:
                    self.LogWarning( self.Prefix + "Skipping restore of backup config file as it does not exist" )
                
                # Need to mark all other rendering tasks as complete for this job (except for pre/post job script tasks).
                self.LogInfo( self.Prefix + "Marking other incomplete tasks as complete" )

                tasks = RepositoryUtils.GetJobTasks( currentJob, True )
                for task in tasks.Tasks:
                    if task.TaskId != "0" and (task.TaskStatus == "Rendering" or task.TaskStatus == "Queued"):
                        RepositoryUtils.CompleteTasks( currentJob, [task,], task.TaskSlaveName )
                
                # End the 3dsmaxcmd job.
                self.MyCmdController.EndCmdJob()

            else:
                # Non task 0 jobs just start the DBR process if necessary and wait for the render to finish.
                if self.VrayDBRJob or self.VrayRtDBRJob:
                    # For V-Ray, launch the V-Ray Spawner process and wait until we're marked as complete by the master (task 0).
                    self.LogInfo( self.Prefix + "Launching V-Ray Spawner process and waiting for V-Ray DBR render to complete" )
                    self.VRaySpawner = VRaySpawnerProcess( self, self.VrayRtDBRJob )
                    self.RunManagedProcess( self.VRaySpawner )
                else:
                    # For mental ray DBR, there is nothing to do because the DBR service should already be running.
                    # Just chill until we're marked as complete by the master (task 0).
                    self.LogInfo( self.Prefix + "Waiting for Mental Ray Satellite render to complete" )
                    while True:
                        if self.IsCanceled():
                            self.FailRender( "Task canceled" )
                        SystemUtils.Sleep( 5000 )
        else:
            # Render the tasks.
            self.MyCmdController.RenderTasks()

    def MonitoredManagedProcessExit( self, name ):
        self.FailRender( "Monitored managed process \"" + name + "\" has exited or been terminated.\n" )

########################################################################
## Main Cmd Controller Class.
########################################################################
class CmdController( object ):
    Plugin = None
    CmdProcess = None
    
    def __init__( self, plugin ):
        self.Plugin = plugin
        self.ProgramName = "CmdProcess"

        self.ManagedCmdProcessRenderExecutable = ""
        self.ManagedCmdProcessRenderArgument = ""
        self.ManagedCmdProcessStartupDirectory = ""

        self.CmdExecutable = ""
        self.Version = -1
        self.MaxFilename = ""
        self.IsMaxIO = False
        self.UseSecureMode = False
        self.TempFolder = ""

        self.StripStitching = False
        self.LocalRendering = False
        self.NetworkFilePath = ""
        self.LocalFilePath = ""

        self.DBRUseIPAddresses = False
        self.DBRMachines = []
        self.DBRConfigFile = ""
        
        self.VrayDBRDynamicStart = False
        self.VrayDBRPortRange = "20204"
        self.VrayDBRUseLocalMachine = True
        self.VrayDBRTransferMissingAssets = False
        self.VrayDBRUseCachedAssets = False
        self.VrayDBRCacheLimitType = "None"
        self.VrayDBRCacheLimit = "100.000000"

        self.VrayRtDBRDynamicStart = False
        self.VrayRtDBRPortRange = "20206"
        self.VrayRtDBRAutoStartLocalSlave = True

        self.MentalRaySatPortNumber = ""

        self.MaxDescriptionDict = {
            "11.0.0.57": "3ds Max 2009 base install",
            "11.0.0.103": "3ds Max 2009 + hotfix3_2008.05.01",
            "11.1.0.208": "3ds Max 2009 + servicepack_sp1",
            "11.5.0.306": "3ds Max 2009 + hotfix4_2008.06.10_incl.previous_sp1",
            "11.5.2.315": "3ds Max 2009 + hotfix_2009.01.19_incl.previous_sp1",
            "11.5.2.318": "3ds Max 2009 + hotfix_2009.03.16_incl.previous_sp1",
            "11.5.2.324": "3ds Max 2009 + hotfix_2009.08.18",
            "11.5.3.330": "3ds Max 2009 + hotfix_2010.06.07/subs_creativity_extension",
            "12.0.0.106": "3ds Max 2010 base install",
            "12.0.1.201": "3ds Max 2010 + hotfix_2009.04.01",
            "12.0.3.203": "3ds Max 2010 + hotfix_2009.05.19",
            "12.1.0.310": "3ds Max 2010 + servicepack_sp1",
            "12.1.7.209": "3ds Max 2010 + hotfix_2009.09.22",
            "12.1.8.213": "3ds Max 2010 + hotfix_2010.02.17",
            "12.1.9.216": "3ds Max 2010 + hotfix_2010.06.08",
            "12.2.0.312": "3ds Max 2010 + servicepack_sp2/subs_connection_extension",
            "13.0.0.94": "3ds Max 2011 base install/hotfix_infocenter",
            "13.0.1.203": "3ds Max 2011 + hotfix_2010.06.07",
            "13.0.2.205": "3ds Max 2011 + hotfix_2010.07.21",
            "13.1.0.114": "3ds Max 2011 + service_pack_sp1/adv_pack_extension",
            "13.1.4.209": "3ds Max 2011 + hotfix4_2010.12.03",
            "13.6.0.118": "3ds Max 2011 + servicepack_sp2",
            "13.7.0.119": "3ds Max 2011 + servicepack_sp3",
            "14.0.0.121": "3ds Max 2012 base install - DOES NOT WORK WITH DEADLINE",
            "14.1.0.328": "3ds Max 2012 + servicepack_sp1/hotfix1",
            "14.1.2.210": "3ds Max 2012 + servicepack_sp1/hotfix2",
            "14.2.0.375": "3ds Max 2012 + servicepack_sp2",
            "14.6.0.388": "3ds Max 2012 + productupdate_pu6 - DOES NOT WORK WITH DEADLINE",
            "14.7.427.0": "3ds Max 2012 + productupdate_pu7",
            "14.8.437.0": "3ds Max 2012 + productupdate_pu8",
            "14.9.467.0": "3ds Max 2012 + productupdate_pu9",
            "14.10.483.0": "3ds Max 2012 + productupdate_pu10",
            "14.12.508.0": "3ds Max 2012 + productupdate_pu12/advantage_pack_extension",
            "15.0.0.347": "3ds Max 2013 base install - DOES NOT WORK WITH DEADLINE",
            "15.1.348.0": "3ds Max 2013 + productupdate_pu1 - DOES NOT WORK WITH DEADLINE",
            "15.2.54.0": "3ds Max 2013 + productupdate_pu2",
            "15.3.72.0": "3ds Max 2013 + productupdate_pu3",
            "15.4.99.0": "3ds Max 2013 + productupdate_pu4",
            "15.4.99.0": "3ds Max 2013 + subs_adv_pack_extension",
            "15.5.121.0": "3ds Max 2013 + productupdate_pu5",
            "15.6.164.0": "3ds Max 2013 + productupdate_pu6",
            "16.0.420.0": "3ds Max 2014 base install - ADSK GAMMA BUG (INSTALL SP5)",
            "16.1.178.0": "3ds Max 2014 + servicepack_sp1",
            "16.2.475.0": "3ds Max 2014 + servicepack_sp2",
            "16.3.207.0": "3ds Max 2014 + servicepack_sp3_BETA",
            "16.3.253.0": "3ds Max 2014 + servicepack_sp3/subs_py_stereo_cam_extension",
            "16.4.265.0": "3ds Max 2014 + servicepack_sp4 PR36 T265  - DOES NOT WORK WITH DEADLINE",
            "16.4.267.0": "3ds Max 2014 + servicepack_sp4 PR36.1 T267",
            "16.4.269.0": "3ds Max 2014 + servicepack_sp4 PR36.2 T269 (CIP fixed)",
            "16.4.270.0": "3ds Max 2014 + servicepack_sp4 (removed by ADSK due to bug - MAXX-16406)",
            "16.5.277.0": "3ds Max 2014 + servicepack_sp5",
            "16.6.556.0": "3ds Max 2014 + servicepack_sp6",
            "17.0.630.0": "3ds Max 2015 base install",
            "17.1.148.0": "3ds Max 2015 + servicepack_sp1 PR40.1 Elwood SP1 (Build E148)",
            "17.1.149.0": "3ds Max 2015 + servicepack_sp1",
            "17.2.259.0": "3ds Max 2015 + servicepack_sp2/subs_extension_1",
            "17.3.343.0": "3ds Max 2015 + servicepack_sp3/subs_extension_2 PR47 (Build E326.1)",
            "17.3.360.0": "3ds Max 2015 + servicepack_sp3/subs_extension_2 PR47 (Build E360)",
            "17.3.374.0": "3ds Max 2015 + servicepack_sp3/subs_extension_2",
            "17.4.476.0": "3ds Max 2015 + servicepack_sp4",
            "18.0.873.0": "3ds Max 2016 base install",
            "18.3.490.0": "3ds Max 2016 + servicepack_sp1/subs_extension_1",
            "18.6.667.0": "3ds Max 2016 + servicepack_sp2",
            "18.7.696.0": "3ds Max 2016 + servicepack_sp3",
            "18.8.739.0": "3ds Max 2016 + servicepack_sp4",
            "18.9.762.0": "3ds Max 2016 + servicepack_sp5",
            "19.0.1072.0": "3ds Max 2017 base install",
            "19.1.129.0": "3ds Max 2017 + servicepack_sp1",
            "19.2.472.0": "3ds Max 2017 + servicepack_sp2",
            "19.3.533.0": "3ds Max 2017 + servicepack_sp3",
            "19.5.917.0": "3ds Max 2017 + security fix",
            "19.50.781.0": "3ds Max 2017 + update 1",
            "19.51.835.0": "3ds Max 2017.1.1 Security Fix (Dec 9, 2016)",
            "19.52.915.0": "3ds Max 2017 + update 2",
            "20.0.0.966": "3ds Max 2018 base install",
            "20.1.0.228": "3ds Max IO 2018 PR4 (Build I228)",
            "20.1.0.1452": "3ds Max 2018 + update 1",
            "20.2.0.2345": "3ds Max 2018 + update 2",
            "20.3.0.3149": "3ds Max 2018 + update 3",
            "20.4.0.4224": "3ds Max 2018 + update 4",
            "20.4.0.4254": "3ds Max 2018 + update 4",
            "21.0.0.845": "3ds Max 2019 base install",
            "21.1.0.1314": "3ds Max 2019 + update 1",
            "21.1.1.1320": "3ds Max 2019.1.1",
            "21.2.0.2219": "3ds Max 2019 + update 2",
            "21.3.0.3250": "3ds Max 2019 + update 3",
            "22.0.0.757": "3ds Max 2020 base install",
            "22.1.0.1249": "3ds Max 2020 + update 1"
            }
    
    def Cleanup( self ):
        if self.CmdProcess:
            self.CmdProcess.Cleanup()
            del self.CmdProcess

    ########################################################################
    ## Main functions
    ########################################################################
    # Reads in the plugin configuration settings and sets up everything in preparation to launch 3dsmaxcmd.
    # Also does some checking to ensure a 3dsCmd job can be rendered on this machine.
    def Initialize( self ):
        self.TempFolder = self.Plugin.CreateTempDirectory( str(self.Plugin.GetThreadNumber()) )
        self.Plugin.SetProcessEnvironmentVariable( "NW_ROOT_PATH", self.TempFolder )

        # # PATH environment variable checking for Backburner
        # SysEnvVarPath = Environment.GetEnvironmentVariable( "PATH" )
        # self.Plugin.LogInfo( "Sys Env Var PATH: %s" % SysEnvVarPath )
        # self.Plugin.LogInfo( "Sys Env Var PATH length: %s" % len(SysEnvVarPath) )

        # # Check for malformed PATH sys env variable, such as PATH=;; from a bad 3rd party installer that tries to be clever with the existing PATH length
        # if SysEnvVarPath == "" or len(SysEnvVarPath) < 10:
        #     self.Plugin.LogWarning( "PATH is too short. Possibly malformed sys env var PATH or corrupt. Check your PATH environment variable!" )

        # # Check PATH isn't longer than 2048 characters.
        # if len(SysEnvVarPath) > 2048:
        #     self.Plugin.LogWarning( "If your PATH environment variable is more than 2048 characters it (and WINDIR) stop being visible in many contexts." )
        #     self.Plugin.LogWarning( "Bad Installers will try to add their application path to the end of PATH and if the Backburner application path is" )
        #     self.Plugin.LogWarning( "already at the end of PATH, it can sometimes delete the Backburner path from PATH!" )

        # SysEnvVarPaths = SysEnvVarPath.split( ";" )
        # BBRegEx = re.compile( r".*Backburner.*", re.IGNORECASE )
        # BBPaths = []
        # for SysEnvVarPath in SysEnvVarPaths:
        #     if BBRegEx.search( SysEnvVarPath ):
        #         BBPaths.append( SysEnvVarPath )

        # if len(BBPaths) >= 1: # print Backburner directory path(s) listing in PATH sys env variable
        #     tempStr = ", ".join(BBPaths)
        #     self.Plugin.LogInfo( "Backburner Path(s) Found in PATH: '%s'" % tempStr )

        # if len(BBPaths) > 1: # Generate Warning if more than 1 Backburner Path is discovered on the machine
        #     self.Plugin.LogWarning( "More than 1 Backburner Path can exist in PATH. However, ensure the latest version of Backburner is always the first entry in your PATH system environment variable" )

        # # Check .NET FileVersion of Backburner Server as identified in sys env var PATH
        # BBServerExeVersion = None
        # BBServerExecutable = PathUtils.GetApplicationPath( "server.exe" )
        # if BBServerExecutable == "" or not File.Exists( BBServerExecutable ):
        #     self.Plugin.LogWarning( "Autodesk Backburner server.exe could not be found on this machine, it is required to run Deadline-3dsCmd plugin" )
        #     self.Plugin.LogWarning( "Please install or upgrade Backburner on this machine and try again." )
        # else:
        #     BBServerExeVersion = FileVersionInfo.GetVersionInfo( BBServerExecutable )
        #     self.Plugin.LogInfo( "Backburner server.exe version: %s" % BBServerExeVersion.FileVersion )

        # Read in the 3dsmax version.
        self.Version = self.Plugin.GetIntegerPluginInfoEntryWithDefault( "Version", 2010 )

        # # Compare Backburner version to 3dsMax version if available and log warning if BB version < 3dsMax version
        # if BBServerExeVersion != None:
        #     bbVersion = (BBServerExeVersion.FileVersion).split(".")
        #     if (len(bbVersion) > 0):
        #         if (int(bbVersion[0]) < self.Version):
        #             self.Plugin.LogWarning( "Backburner version is too OLD to support this version of 3dsMax. 3dsMax will FAIL to start! Please upgrade Backburner and ensure machine is restarted." )

        renderExecutableKey = "CmdRenderExecutable" + str(self.Version)

        isMaxDesign = self.Plugin.GetBooleanPluginInfoEntryWithDefault( "IsMaxDesign", False )
        
        if isMaxDesign:
            self.Plugin.LogInfo( "Rendering with 3ds Max Cmd Design Version: %d" % self.Version )
        else:
            self.Plugin.LogInfo( "Rendering with 3ds Max Cmd Version: %d" % self.Version )

        forceBuild = self.Plugin.GetPluginInfoEntryWithDefault( "Build", "None" )
        if( self.Version > 2013 ):
            forceBuild = "None"
            self.Plugin.LogInfo( "Not enforcing a build of 3ds Max because version 2014 and later is 64 bit only" )
        else:
            self.Plugin.LogInfo( "Build of 3ds Max to force: %s" % forceBuild )

        maxEdition = ""
        if isMaxDesign:
            renderExecutableKey = renderExecutableKey + "Design"
            maxEdition = " Design"

        renderExecutableList = self.Plugin.GetConfigEntry( renderExecutableKey ).strip()
        self.CmdExecutable = ""
        if(SystemUtils.IsRunningOnWindows()):
            if( forceBuild == "32bit" ):
                self.CmdExecutable = FileUtils.SearchFileListFor32Bit( renderExecutableList )
                if( self.CmdExecutable == "" ):
                    self.Plugin.LogWarning( "No 32 bit 3dsmax" + maxEdition + " " + str(self.Version) + " render executable found in the semicolon separated list \"" + renderExecutableList + "\". Checking for any executable that exists instead." )
            elif( forceBuild == "64bit" ):
                self.CmdExecutable = FileUtils.SearchFileListFor64Bit( renderExecutableList )
                if( self.CmdExecutable == "" ):
                    self.Plugin.LogWarning( "No 64 bit 3dsmax" + maxEdition + " " + str(self.Version) + " render executable found in the semicolon separated list \"" + renderExecutableList + "\". Checking for any executable that exists instead." )
        
        if( self.CmdExecutable == "" ):
            self.CmdExecutable = FileUtils.SearchFileList( renderExecutableList )
            if( self.CmdExecutable == "" ):
                self.Plugin.FailRender( "No 3dsmax" + maxEdition + " " + str(self.Version) + " render executable found in the semicolon separated list \"" + renderExecutableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        # Identify if 3dsmaxcmdio executable is being used
        exeName = os.path.splitext( os.path.basename( self.CmdExecutable ) )[0]
        if exeName.endswith( "io" ):
            self.IsMaxIO = True

        # Try to find .NET FileVersion of 3dsmaxcmd.exe (can be unreliable)
        cmdExecutable = FileVersionInfo.GetVersionInfo( self.CmdExecutable )
        cmdExeVersion = cmdExecutable.FileVersion
        self.Plugin.LogInfo( "Slave 3ds Max Cmd Version: %s" % cmdExeVersion )

        # If known version of 3dsmaxcmd, then print out English description of 3dsmaxcmd.exe version (can be unreliable)
        if cmdExeVersion in self.MaxDescriptionDict:
            self.Plugin.LogInfo( "Slave 3ds Max Cmd Description: %s" % self.MaxDescriptionDict[cmdExeVersion] )

        # Figure out .NET FileVersion of 3dsmax.exe as 3dsmaxcmd.exe is unreliable in earlier versions of 3dsmax (~Max2012 or earlier)
        cmdExePath = Path.GetDirectoryName( self.CmdExecutable )
        maxExeName = "3dsmaxio.exe" if self.IsMaxIO else "3dsmax.exe"
        maxExe = Path.Combine( cmdExePath, maxExeName )
        maxExecutable = FileVersionInfo.GetVersionInfo( maxExe )
        maxExeVersion = maxExecutable.FileVersion
        self.Plugin.LogInfo( "Slave 3ds Max Version: %s" % maxExeVersion )

        # If known version of 3dsMax, then print out English description of 3dsmax.exe/3dsmaxio.exe version
        if maxExeVersion in self.MaxDescriptionDict:
            self.Plugin.LogInfo( "Slave 3ds Max Description: %s" % self.MaxDescriptionDict[maxExeVersion] )

        # If PluginInfoFile key=value pair "SubmittedFromVersion' available in job settings, then if version known in look-up dict, then print out English description of 3dsmax.exe version that job was submitted with.
        SubmittedFromVersion = self.Plugin.GetPluginInfoEntryWithDefault( "SubmittedFromVersion", "" )
        if SubmittedFromVersion != "":
            self.Plugin.LogInfo( "Submitted from 3ds Max Version: %s" % SubmittedFromVersion )
            if SubmittedFromVersion in self.MaxDescriptionDict:
                self.Plugin.LogInfo( "Submitted from 3ds Max Description: %s" % self.MaxDescriptionDict[SubmittedFromVersion] )    
            if maxExeVersion != SubmittedFromVersion:
                self.Plugin.LogWarning( "Slave's 3ds Max version is NOT the same as the 3ds Max version that was used to submit this job! Unexpected results may occur!" )

        # Read in Secure setting for 3ds Max IO.
        self.UseSecureMode = self.Plugin.GetBooleanConfigEntryWithDefault( "UseSecureMode", False )
        self.Plugin.LogInfo( "Secure mode enabled: %s" % self.UseSecureMode )

        # If we're overriding CPU Affinity, ensure it works for V-Ray by setting their environment variable
        if self.Plugin.OverrideCpuAffinity():
            self.Plugin.LogInfo( "Setting VRAY_USE_THREAD_AFFINITY to 0 to ensure CPU Affinity works." )
            self.Plugin.SetEnvironmentVariable( "VRAY_USE_THREAD_AFFINITY", "0" )

        # Check if we are overriding GPU affinity
        selectedGPUs = self.GetGpuOverrides()
        if len(selectedGPUs) > 0:
            gpus = ",".join(str(gpu) for gpu in selectedGPUs)
            self.Plugin.LogInfo( "This Slave is overriding its GPU affinity, so the following GPUs will be used by RedShift/V-Ray RT: %s" % gpus )
            self.Plugin.SetProcessEnvironmentVariable( "REDSHIFT_GPUDEVICES", gpus ) # Redshift
            vrayGpus = "index" + ";index".join( [ str( gpu ) for gpu in selectedGPUs ] ) # "index0;index1"
            self.Plugin.SetProcessEnvironmentVariable( "VRAY_OPENCL_PLATFORMS_x64", vrayGpus ) # V-Ray RT

        # Create output paths if they don't exist
        self.Plugin.LogInfo( "Creating output directories if necessary..." )
        self.CreateOutputFolders()

    def RenderTasks( self ):
        # Render frame(s) of job using CmdController class
        self.RenderFrame()

        # If we are local rendering, then try and move local renders to network file path location.
        if self.LocalRendering:
            self.Plugin.LogInfo( "Moving output files and folders from " + self.LocalFilePath + " to " + self.NetworkFilePath )
            self.Plugin.VerifyAndMoveDirectory( self.LocalFilePath, self.NetworkFilePath, False, -1 )
        
        # If we are performing a strip render, try to assemble the images.
        stripRendering = self.Plugin.GetBooleanPluginInfoEntryWithDefault( "StripRendering", False )
        if stripRendering:
            self.StripStitching = True
            executable = self.CmdExecutable
            arguments = self.GetArguments()
            self.Plugin.RunProcess( executable, arguments, Path.GetDirectoryName( executable ), -1 )

    def EndCmdJob( self ):
        if self.Plugin.MonitoredManagedProcessIsRunning( self.ProgramName ):
            self.Plugin.LogWarning( "Waiting for 3ds Max Cmd to shut down" )
            self.Plugin.ShutdownMonitoredManagedProcess( self.ProgramName )
            self.Plugin.LogInfo( "3ds Max Cmd has shut down" )

    ##################################################################
    ## Helper functions
    ##################################################################
    def GetArguments( self ):
        arguments = ""

        # If this is a V-Ray DBR job, and we're not the master, we're just launching the V-Ray Spawner, so no arguments needed.
        if (self.Plugin.VrayDBRJob or self.Plugin.VrayRtDBRJob) and self.Plugin.GetCurrentTaskId() != "0":
            return arguments
        
        contOnErrPart = ""
        continueOnError = self.Plugin.GetBooleanPluginInfoEntryWithDefault( "ContinueOnError", False )
        if(continueOnError) :
            contOnErrPart = " -continueOnError"
        
        stripPart = ""
        stripRendering = self.Plugin.GetBooleanPluginInfoEntryWithDefault( "StripRendering", False ) 
        if( stripRendering ):
            strips = self.Plugin.GetPluginInfoEntryWithDefault( "StripCount", "1" ).strip()
            overlap = self.Plugin.GetPluginInfoEntryWithDefault( "StripOverlap", "0" ).strip()
            if( self.StripStitching ):
                stripPart = " -stitch:" + strips + "," + overlap
            else:
                strip = self.Plugin.GetPluginInfoEntryWithDefault( "StripNumber", "1" ).strip()
                stripPart = " -strip:" + strips + "," + overlap + "," + strip
        
        # Don't apply gamma correction during the stitching phase.
        gammaCorrectionPart = ""
        if not self.StripStitching:
            if self.Plugin.GetBooleanPluginInfoEntryWithDefault( "GammaCorrection", False ):
                gammaCorrectionPart = " -gammaCorrection:true"
                gammaCorrectionPart += " -gammaValueIn:" + self.Plugin.GetPluginInfoEntryWithDefault("GammaInput", "1.0")
                gammaCorrectionPart += " -gammaValueOut:" + self.Plugin.GetPluginInfoEntryWithDefault("GammaOutput", "1.0")

        outputFile = self.Plugin.GetPluginInfoEntryWithDefault( "RenderOutput", "" ).strip()
        if( outputFile != "" ):
            # Create the output directory if it doesn't exist.
            outputDir = Path.GetDirectoryName( outputFile )
            if not Directory.Exists( outputDir ):
                Directory.CreateDirectory( outputDir )
            
            # Don't check for local rendering if we're just stitching the strips together.
            if( not self.StripStitching ):
                self.LocalRendering = self.Plugin.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False )
                if self.LocalRendering:
                    self.NetworkFilePath = outputDir
                    outputDir = self.Plugin.CreateTempDirectory( "3dsOutput" )
                    self.LocalFilePath = outputDir
                    outputFile = Path.Combine( outputDir, Path.GetFileName( outputFile ) )
                    
                    self.Plugin.LogInfo( "Rendering to local drive, will copy files and folders to final location after render is complete" )
                else:
                    self.Plugin.LogInfo( "Rendering to network drive" )
            
            outputFile = "\"" + outputFile + "\""
        
        pathConfigFile = self.Plugin.GetPluginInfoEntryWithDefault( "PathConfigFile", "" ).strip()
        if( pathConfigFile != "" ):
            pathConfigFile = Path.Combine( self.Plugin.GetJobsDataDirectory(), pathConfigFile )
            pathConfigFile = "\"" + pathConfigFile + "\""

        renderPresetFile = self.Plugin.GetPluginInfoEntryWithDefault( "RenderPresetFile", "" ).strip()
        if( renderPresetFile != "" ):
            renderPresetFile = Path.Combine( self.Plugin.GetJobsDataDirectory(), renderPresetFile )
            renderPresetFile = "\"" + renderPresetFile + "\""

        preRenderScript = self.Plugin.GetPluginInfoEntryWithDefault( "PreRenderScript", "" ).strip()
        if( preRenderScript != "" ):
            preRenderScript = Path.Combine( self.Plugin.GetJobsDataDirectory(), preRenderScript )
            preRenderScript = "\"" + preRenderScript + "\""

        postRenderScript = self.Plugin.GetPluginInfoEntryWithDefault( "PostRenderScript", "" ).strip()
        if( postRenderScript != "" ):
            postRenderScript = Path.Combine( self.Plugin.GetJobsDataDirectory(), postRenderScript )
            postRenderScript = "\"" + postRenderScript + "\""
        
        startFrame = self.Plugin.GetStartFrame()
        endFrame = self.Plugin.GetEndFrame()
        if self.Plugin.VrayDBRJob or self.Plugin.VrayRtDBRJob or self.Plugin.MentalRayDBRJob:
            dbrJobFrame = self.Plugin.GetIntegerPluginInfoEntryWithDefault( "DBRJobFrame", 0 )
            self.Plugin.LogInfo( self.Plugin.Prefix + "Rendering frame " + str(dbrJobFrame) )
            startFrame = dbrJobFrame
            endFrame = dbrJobFrame

        # Get the 3dsmax scene file to render.
        self.MaxFilename = self.Plugin.GetPluginInfoEntryWithDefault( "SceneFile", self.Plugin.GetDataFilename() )
        if( self.MaxFilename == None ):
            self.Plugin.FailRender( "No scene file was included with the job" )
            
        self.MaxFilename = RepositoryUtils.CheckPathMapping( self.MaxFilename ).replace( "/", "\\" )
        self.Plugin.LogInfo( "Scene file to render: \"%s\"" % self.MaxFilename )

        arguments += "\"" + self.MaxFilename + "\""
        arguments += " -v:" + str(self.Plugin.GetIntegerConfigEntryWithDefault("VerbosityLevel", 5))
        arguments += " -start:" + str(startFrame)
        arguments += " -end:" + str(endFrame)

        if self.IsMaxIO:
            if self.UseSecureMode:
                arguments += " -secure on"
            else:
                arguments += " -secure off"

        arguments += StringUtils.BlankIfEitherIsBlank( StringUtils.BlankIfEitherIsBlank(" -cam:\"", self.Plugin.GetPluginInfoEntryWithDefault("Camera","").strip()), "\"")
        arguments += StringUtils.BlankIfEitherIsBlank(" -w:", self.Plugin.GetPluginInfoEntryWithDefault("ImageWidth",""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -h:", self.Plugin.GetPluginInfoEntryWithDefault("ImageHeight",""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -pixelAspect:", self.Plugin.GetPluginInfoEntryWithDefault("PixelAspect",""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -atmospherics:", self.Plugin.GetPluginInfoEntryWithDefault("Atmospherics", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -renderHidden:", self.Plugin.GetPluginInfoEntryWithDefault("HiddenGeometry", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -effects:", self.Plugin.GetPluginInfoEntryWithDefault("Effects", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -useAreaLights:", self.Plugin.GetPluginInfoEntryWithDefault("AreaLights", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -displacements:", self.Plugin.GetPluginInfoEntryWithDefault("Displacements", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -force2Sided:", self.Plugin.GetPluginInfoEntryWithDefault("TwoSided", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -videoColorCheck:", self.Plugin.GetPluginInfoEntryWithDefault("VideoColorCheck", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -superBlack:", self.Plugin.GetPluginInfoEntryWithDefault("SuperBlack", ""))
        
        renderToFields = self.Plugin.GetPluginInfoEntryWithDefault("RenderToFields", "")
        arguments += StringUtils.BlankIfEitherIsBlank(" -renderFields:", renderToFields)
        if bool(renderToFields):
            arguments += StringUtils.BlankIfEitherIsBlank(" -fieldOrder:", self.Plugin.GetPluginInfoEntryWithDefault("FieldOrder", "Odd"))

        imageSequenceFile = self.Plugin.GetPluginInfoEntryWithDefault( "ImageSequenceFile", "none" )
        imgSeqFileCreation = 0
        if imageSequenceFile == ".imsq":
            imgSeqFileCreation = 1
        if imgSeqFileCreation == ".ifl":
            imgSeqFileCreation = 2

        if imgSeqFileCreation != 0:
            arguments += ( " -imageSequenceFile:%s" % imgSeqFileCreation )

        if self.Plugin.GetBooleanPluginInfoEntryWithDefault( "StillFrame", False ):
            arguments += " -stillFrame"

        sceneState = self.Plugin.GetPluginInfoEntryWithDefault( "SceneState", "" )
        if sceneState != "":
            arguments += ( " -sceneState:%s" % sceneState )

        batchRender = self.Plugin.GetBooleanPluginInfoEntryWithDefault( "BatchRender", False )
        if batchRender:
            arguments += " -batchRender"

        batchRenderName = self.Plugin.GetPluginInfoEntryWithDefault( "BatchRenderName", "" )
        if not batchRender and batchRenderName != "":
            arguments += ( " -batchRender:%s" % batchRenderName )

        arguments += StringUtils.BlankIfEitherIsBlank(" -skipRenderedFrames:", self.Plugin.GetPluginInfoEntryWithDefault("SkipRenderedFrames", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -outputName:", outputFile.replace( "/", "\\" ))
        arguments += StringUtils.BlankIfEitherIsBlank(" -pathFile:", pathConfigFile.replace( "/", "\\" ))
        arguments += StringUtils.BlankIfEitherIsBlank(" -preset:", renderPresetFile.replace( "/", "\\" ))
        arguments += StringUtils.BlankIfEitherIsBlank(" -preRenderScript:", preRenderScript.replace( "/", "\\" ))
        arguments += StringUtils.BlankIfEitherIsBlank(" -postRenderScript:", postRenderScript.replace( "/", "\\" ))
        arguments += StringUtils.BlankIfEitherIsBlank(" -renderElements:", self.Plugin.GetPluginInfoEntryWithDefault("RenderElements", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -useAdvLight:", self.Plugin.GetPluginInfoEntryWithDefault("UseAdvLighting", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -computeAdvLight:", self.Plugin.GetPluginInfoEntryWithDefault("ComputeAdvLighting", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -ditherPaletted:", self.Plugin.GetPluginInfoEntryWithDefault("DitherPaletted", ""))
        arguments += StringUtils.BlankIfEitherIsBlank(" -ditherTrueColor:", self.Plugin.GetPluginInfoEntryWithDefault("DitherTrueColor", ""))
        arguments += str( gammaCorrectionPart )
        arguments += str( contOnErrPart )
        arguments += str( stripPart )
        arguments += " -rfw:" + self.Plugin.GetPluginInfoEntryWithDefault("ShowVFB","1")
        arguments += " -videopostJob:" + self.Plugin.GetPluginInfoEntryWithDefault("VideoPost","0")

        # Bitmap Options
        bmpType = self.Plugin.GetPluginInfoEntryWithDefault( "BMP_TYPE", "" )
        if bmpType == "paletted":
            arguments += " -BMP_TYPE:2"
        elif bmpType == "true 24-bit":
            arguments += " -BMP_TYPE:8"

        arguments += StringUtils.BlankIfEitherIsBlank( " -JPEG_QUALITY:", self.Plugin.GetPluginInfoEntryWithDefault("JPEG_QUALITY", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -JPEG_SMOOTHING:", self.Plugin.GetPluginInfoEntryWithDefault("JPEG_SMOOTHING", ""))    

        arguments += StringUtils.BlankIfEitherIsBlank( " -TARGA_COLORDEPTH:", self.Plugin.GetPluginInfoEntryWithDefault("TARGA_COLORDEPTH", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -TARGA_COMPRESSED:", self.Plugin.GetPluginInfoEntryWithDefault("TARGA_COMPRESSED", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -TARGA_ALPHASPLIT:", self.Plugin.GetPluginInfoEntryWithDefault("TARGA_ALPHASPLIT", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -TARGA_PREMULTALPHA:", self.Plugin.GetPluginInfoEntryWithDefault("TARGA_PREMULTALPHA", ""))

        tifType = self.Plugin.GetPluginInfoEntryWithDefault( "TIF_TYPE", "" )
        if tifType == "mono":
            arguments += " -TIF_TYPE:0"
        elif tifType == "color":
            arguments += " -TIF_TYPE:1"
        elif tifType == "logl":
            arguments += " -TIF_TYPE:2"
        elif tifType == "logluv":
            arguments += " -TIF_TYPE:3"
        elif tifType == "16-bit color":
            arguments += " -TIF_TYPE:4"

        arguments += StringUtils.BlankIfEitherIsBlank( " -TIF_ALPHA:", self.Plugin.GetPluginInfoEntryWithDefault("TIF_ALPHA", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -TIF_COMPRESSION:", self.Plugin.GetPluginInfoEntryWithDefault("TIF_COMPRESSION", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -TIF_DPI:", self.Plugin.GetPluginInfoEntryWithDefault("TIF_DPI", ""))
        
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_COLORDEPTH:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_COLORDEPTH", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_ALPHA:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_ALPHA", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_PREMULTALPHA:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_PREMULTALPHA", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_DESCRIPTION:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_DESCRIPTION", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_AUTHOR:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_AUTHOR", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_ZDEPTHCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_ZDEPTHCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_MTLIDCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_MTLIDCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_OBJECTIDCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_OBJECTIDCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_UVCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_UVCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_NORMALCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_NORMALCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_NONCLAMPEDCOLORCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_NONCLAMPEDCOLORCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RLA_COVERAGECHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RLA_COVERAGECHANNEL", ""))

        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_COLORDEPTH:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_COLORDEPTH", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_ALPHA:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_ALPHA", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_PREMULTALPHA:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_PREMULTALPHA", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_DESCRIPTION:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_DESCRIPTION", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_AUTHOR:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_AUTHOR", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_ZDEPTHCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_ZDEPTHCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_MTLIDCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_MTLIDCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_OBJECTIDCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_OBJECTIDCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_UVCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_UVCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_NORMALCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_NORMALCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_NONCLAMPEDCOLORCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_NONCLAMPEDCOLORCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_COVERAGECHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_COVERAGECHANNEL", ""))

        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_NODERENDERIDCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_NODERENDERIDCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_COLORCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_COLORCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_TRANSPCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_TRANSPCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_VELOCCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_VELOCCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_WEIGHTCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_WEIGHTCHANNEL", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -RPF_MASKCHANNEL:", self.Plugin.GetPluginInfoEntryWithDefault("RPF_MASKCHANNEL", ""))

        arguments += StringUtils.BlankIfEitherIsBlank( " -EXR_USEEXPONENT:", self.Plugin.GetPluginInfoEntryWithDefault("EXR_USEEXPONENT", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -EXR_EXPONENT:", self.Plugin.GetPluginInfoEntryWithDefault("EXR_EXPONENT", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -EXR_PREMULTALPHA:", self.Plugin.GetPluginInfoEntryWithDefault("EXR_PREMULTALPHA", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -EXR_ALPHA:", self.Plugin.GetPluginInfoEntryWithDefault("EXR_ALPHA", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -EXR_RED:", self.Plugin.GetPluginInfoEntryWithDefault("EXR_RED", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -EXR_GREEN:", self.Plugin.GetPluginInfoEntryWithDefault("EXR_GREEN", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -EXR_BLUE:", self.Plugin.GetPluginInfoEntryWithDefault("EXR_BLUE", ""))
        
        exrBitDepth = self.Plugin.GetPluginInfoEntryWithDefault( "EXR_BITDEPTH", "" )
        if exrBitDepth == "8-bit integers":
            arguments += " -EXR_BITDEPTH:0"
        elif exrBitDepth == "half float":
            arguments += " -EXR_BITDEPTH:1"
        elif exrBitDepth == "float":
            arguments += " -EXR_BITDEPTH:2"
        
        arguments += StringUtils.BlankIfEitherIsBlank( " -EXR_USEFRAMENUMDIGITS:", self.Plugin.GetPluginInfoEntryWithDefault("EXR_USEFRAMENUMDIGITS", ""))
        arguments += StringUtils.BlankIfEitherIsBlank( " -EXR_FRAMENUMDIGITS:", self.Plugin.GetPluginInfoEntryWithDefault("EXR_FRAMENUMDIGITS", ""))

        exrCompressionType = self.Plugin.GetPluginInfoEntryWithDefault( "EXR_COMPRESSIONTYPE", "")
        if exrCompressionType == "no compression":
            arguments += " -EXR_COMPRESSIONTYPE:0"
        elif exrCompressionType == "RLE":
            arguments += " -EXR_COMPRESSIONTYPE:1"        
        elif exrCompressionType == "ZIP (1 scanline)":
            arguments += " -EXR_COMPRESSIONTYPE:2"
        elif exrCompressionType == "ZIP (16 scanlines)":
            arguments += " -EXR_COMPRESSIONTYPE:3"
        elif exrCompressionType == "PIZ":
            arguments += " -EXR_COMPRESSIONTYPE:4"

        arguments += StringUtils.BlankIfEitherIsBlank( " -EXR_USEREALPIX:", self.Plugin.GetPluginInfoEntryWithDefault("EXR_USEREALPIX", ""))

        return arguments

    def GetDBRSettings( self ):
        # DBR Settings
        self.DBRUseIPAddresses = self.Plugin.GetBooleanConfigEntryWithDefault( "DBRUseIPAddresses", False )

    def GetVrayDBRSettings( self ):
        self.VrayDBRDynamicStart = self.Plugin.GetBooleanConfigEntryWithDefault( "VRayDBRDynamicStart", False )
        self.VrayDBRPortRange = self.Plugin.GetConfigEntryWithDefault( "VRayDBRPortRange", "20204" )
        self.VrayDBRUseLocalMachine = self.Plugin.GetBooleanConfigEntryWithDefault( "VRayDBRUseLocalMachine", True )
        self.VrayDBRTransferMissingAssets = self.Plugin.GetBooleanConfigEntryWithDefault( "VRayDBRTransferMissingAssets", False )
        self.VrayDBRUseCachedAssets = self.Plugin.GetBooleanConfigEntryWithDefault( "VRayDBRUseCachedAssets", False )
        self.VrayDBRCacheLimitType = self.Plugin.GetConfigEntryWithDefault( "VRayDBRCacheLimitType", "None" )
        self.VrayDBRCacheLimit = self.Plugin.GetConfigEntryWithDefault( "VRayDBRCacheLimit", "100.000000" )

    def GetVrayRtDBRSettings( self ):
        self.VrayRtDBRDynamicStart = self.Plugin.GetBooleanConfigEntryWithDefault( "VRayRTDBRDynamicStart", False )
        self.VrayRtDBRPortRange = self.Plugin.GetConfigEntryWithDefault( "VRayRTDBRPortRange", "20206" )
        self.VrayRtDBRAutoStartLocalSlave = self.Plugin.GetBooleanConfigEntryWithDefault( "VRayRTDBRUseLocalMachine", True )

    def GetMentalRaySettings( self ):
        # Mental Ray Settings
        self.MentalRaySatPortNumber = self.Plugin.GetConfigEntryWithDefault( "MentalRaySatPortNumber%i" % self.Version, "" )

    def GetDBRMachines( self ):
        currentJob = self.Plugin.GetJob()
        machines = list(RepositoryUtils.GetMachinesRenderingJob( currentJob.JobId, self.DBRUseIPAddresses, False ))
        machines = [x.lower() for x in machines] # Ensure all machine names are lowercase

        localFQDN = (Environment2.FullyQualifiedDomainName).lower()
        localMachineName = (Environment2.MachineName).lower()
        localCleanMachineName = (Environment2.CleanMachineName).lower()

        slaveName = self.Plugin.GetSlaveName()
        slaveInfo = RepositoryUtils.GetSlaveInfo( slaveName, True )
        localIPAddress = SlaveUtils.GetMachineIPAddresses([slaveInfo])[0]

        while localFQDN in machines: machines.remove(localFQDN)
        while localMachineName in machines: machines.remove(localMachineName)
        while localCleanMachineName in machines: machines.remove(localCleanMachineName)
        while localIPAddress in machines: machines.remove(localIPAddress)

        return machines

    def GetLanguageCodeAndDirectory( self, executable, version ):
        languageCodeStr = ""
        languageSubDir = ""
        
        maxInstallDirectory = Path.GetDirectoryName( executable )

        maxIntVersion = version - 1998
        maxVersionStr = str(maxIntVersion)
        maxVersionStr += ".0"
        
        if version < 2013:
            languageCode = ""
            
            englishCode = "409"
            frenchCode = "40C"
            germanCode = "407"
            japaneseCode = "411"
            simplifiedChineseCode = "804"
            koreanCode = "412"
            
            maxKeyName = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Autodesk\\3DSMAX\\" + maxVersionStr + "\\MAX-1:"
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxKeyName, englishCode, languageCode )
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxKeyName, frenchCode, languageCode )
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxKeyName, germanCode, languageCode )
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxKeyName, japaneseCode, languageCode )
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxKeyName, simplifiedChineseCode, languageCode )
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxKeyName, koreanCode, languageCode )
            
            maxWowKeyName = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Autodesk\\3dsMax\\" + maxVersionStr + "\\MAX-1:"
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxWowKeyName, englishCode, languageCode )
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxWowKeyName, frenchCode, languageCode )
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxWowKeyName, germanCode, languageCode )
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxWowKeyName, japaneseCode, languageCode )
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxWowKeyName, simplifiedChineseCode, languageCode )
            languageCode = self.AutoCheckRegistryForLanguage( maxInstallDirectory, maxWowKeyName, koreanCode, languageCode )
            
            if languageCode != "":
                self.Plugin.LogInfo( "Found language code: " + languageCode )
                if languageCode == englishCode:
                    languageCodeStr = "enu"
                elif languageCode == frenchCode:
                    languageCodeStr = "fra"
                elif languageCode == germanCode:
                    languageCodeStr = "deu"
                elif languageCode == japaneseCode:
                    languageCodeStr = "jpn"
                elif languageCode == simplifiedChineseCode:
                    languageCodeStr = "chs"
                elif languageCode == koreanCode:
                    languageCodeStr = "kor"
                else:
                    self.Plugin.FailRender( "Unsupported language code: " + languageCode + ". Please email this error report to support@thinkboxsoftware.com so we can add support for this language code." )
            else:
                self.Plugin.LogInfo( "Language code could not be found. Defaulting to 409 (English)" )
                languageCodeStr = "enu"
            
            self.Plugin.LogInfo( "Language code string: " + languageCodeStr )
        else:
            languageCodeStr = "ENU"
            languageSubDir = "en-US"
            
            maxKeyName = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Autodesk\\3DSMAX\\" + maxVersionStr
            languageCodeStr = SystemUtils.GetRegistryKeyValue( maxKeyName, "DefaultLanguage", "" )
            if( languageCodeStr == "" ):
                maxKeyName = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Autodesk\\3DSMAX\\" + maxVersionStr
                languageCodeStr = SystemUtils.GetRegistryKeyValue( maxKeyName, "DefaultLanguage", "" )
                if( languageCodeStr == "" ):
                    self.Plugin.LogInfo( "Language code could not be found in registry. Defaulting to ENU (English)" )
                    languageCodeStr = "ENU"
            
            maxKeyName = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Autodesk\\3DSMAX\\" + maxVersionStr + "\\LanguagesInstalled\\" + languageCodeStr
            languageSubDir = SystemUtils.GetRegistryKeyValue( maxKeyName, "LangSubDir", "" )
            if( languageSubDir == "" ):
                maxKeyName = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Autodesk\\3DSMAX\\" + maxVersionStr + "\\LanguagesInstalled\\" + languageCodeStr
                languageSubDir = SystemUtils.GetRegistryKeyValue( maxKeyName, "LangSubDir", "" )
                if( languageSubDir == "" ):
                    self.Plugin.LogInfo( "Language sub directory could not be found in registry. Defaulting to en-US (English)" )
                    languageSubDir = "en-US"
            
            self.Plugin.LogInfo( "Language code string: " + languageCodeStr )
            self.Plugin.LogInfo( "Language sub directory: " + languageSubDir )
            
        return [languageCodeStr, languageSubDir]

    def CreateOutputFolders( self ):
        outputFolders = self.Plugin.GetJob().OutputDirectories
        for folder in outputFolders:
            folder = RepositoryUtils.CheckPathMapping( folder ).replace( "/", "\\" )
            if not os.path.isdir( folder ):
                try:
                    self.Plugin.LogInfo( 'Creating the output directory "%s"...' % folder )
                    os.makedirs( folder )
                except:
                    self.Plugin.FailRender( 'Failed to create output directory "%s". The path may be invalid or permissions may not be sufficient.' % folder )
        
    def AutoCheckRegistryForLanguage( self, installDirectory, keyName, languageCode, autoDetectedLanguageCode ):
        if( autoDetectedLanguageCode == "" ):
            tempInstallDir = SystemUtils.GetRegistryKeyValue( keyName + languageCode, "Installdir", "" )
            if( tempInstallDir != "" ):
                tempInstallDir = tempInstallDir.lower().replace( "/", "\\" ).rstrip( "\\" )
                if( tempInstallDir == installDirectory.lower().replace( "/", "\\" ).rstrip( "\\" ) ):
                    autoDetectedLanguageCode = languageCode
        return autoDetectedLanguageCode

    def GetDBRConfigFile( self ):
        if self.Plugin.VrayDBRJob or self.Plugin.VrayRtDBRJob:
            # Figure out where the vray_dr.cfg file is located.
            languageInfo = self.GetLanguageCodeAndDirectory( self.CmdExecutable, self.Version )
            
            installIni = PathUtils.ChangeFilename( self.CmdExecutable, "InstallSettings.ini" )
            useUserProfiles = FileUtils.GetIniFileSetting( installIni, "Least User Privilege", "useUserProfiles", "1" )
            if useUserProfiles == "1":
                is64Bit = FileUtils.Is64BitDllOrExe( self.CmdExecutable )
                isDesign = (self.CmdExecutable.lower().find("design") != -1)
                
                if is64Bit:
                    if isDesign:
                        maxDataPath = Path.Combine( PathUtils.GetLocalApplicationDataPath(), "Autodesk\\3dsMaxDesign\\" + str(self.Version) + " - 64bit\\" + languageInfo[0] )
                    else:
                        maxDirName = "3dsMaxIO" if self.IsMaxIO else "3dsMax"
                        maxDataPath = Path.Combine( PathUtils.GetLocalApplicationDataPath(), "Autodesk\\" + maxDirName + "\\" + str(self.Version) + " - 64bit\\" + languageInfo[0] )
                else:
                    if isDesign:
                        maxDataPath = Path.Combine( PathUtils.GetLocalApplicationDataPath(), "Autodesk\\3dsMaxDesign\\" + str(self.Version) + " - 32bit\\" + languageInfo[0] )
                    else:
                        maxDataPath = Path.Combine( PathUtils.GetLocalApplicationDataPath(), "Autodesk\\3dsmax\\" + str(self.Version) + " - 32bit\\" + languageInfo[0] )
                
                self.Plugin.LogInfo( "3dsmax user profile path: %s" % maxDataPath )
                plugCfgDirectory = Path.Combine( maxDataPath, languageInfo[1] + "\\plugcfg" )
                self.Plugin.LogInfo( "3dsmax plugcfg directory: %s" % plugCfgDirectory )
                
                if self.Plugin.VrayDBRJob:
                    return Path.Combine( plugCfgDirectory, "vray_dr.cfg" )
                else:
                    return Path.Combine( plugCfgDirectory, "vrayrt_dr.cfg" )
            else:
                if self.Version < 2013:
                    maxIni = PathUtils.ChangeFilename( self.CmdExecutable, "3dsmax.ini" )
                else:
                    maxIni = PathUtils.ChangeFilename( self.CmdExecutable, languageInfo[1] + "\\3dsmax.ini" )

                maxDataPath = Path.GetDirectoryName( self.CmdExecutable )
                plugCfgDirectory = Path.Combine( maxDataPath, Path.GetDirectoryName( maxIni ) + "\\plugcfg" )
                self.Plugin.LogInfo( "3dsmax plugcfg directory: %s" % plugCfgDirectory )
                
                if self.Plugin.VrayDBRJob:
                    return Path.Combine( plugCfgDirectory, "vray_dr.cfg" )
                else:
                    return Path.Combine( plugCfgDirectory, "vrayrt_dr.cfg" )
        else:
            # Figure out where the max.rayhosts file is located.
            configDirectory = Path.GetDirectoryName( self.CmdExecutable )

            # The config directory for the max.rayhosts file is different for different versions of max.
            if self.Version <= 2010:
                configDirectory = Path.Combine( configDirectory, "mentalray" )
            elif self.Version >= 2011:
                mainDir = configDirectory
                configDirectory = Path.Combine( self.TempFolder, "mentalRayHosts" )
                if self.Version <= 2014:
                    self.Plugin.SetProcessEnvironmentVariable( "MAX2011_MI_ROOT", configDirectory )
                else:
                    self.Plugin.SetProcessEnvironmentVariable( "MAX%i_MI_ROOT" % self.Version, configDirectory )
                
                rayFile = Path.Combine(configDirectory, "rayrc")
                if( not Directory.Exists( configDirectory ) ):
                    Directory.CreateDirectory( configDirectory )

                if self.Version >= 2011 and self.Version <=2012:
                    mainDir = Path.Combine( mainDir, "mentalimages" )
                else:
                    mainDir = Path.Combine( mainDir, "NVIDIA" )
                mainRayFile = Path.Combine(mainDir, "rayrc")
                File.Copy(mainRayFile,rayFile,True)
                fileLines = File.ReadAllLines(rayFile)
                newLines = []
                for line in fileLines:
                    line = line.replace("\".","\""+mainDir+"\\.")
                    line = line.replace(";.",";"+mainDir+"\\.")
                    newLines.append(line)
                File.WriteAllLines(rayFile,newLines)

            configFile = Path.Combine( configDirectory, "max.rayhosts" )

            return configFile
        
    def UpdateVrayDBRConfigFile( self, machines, configFile ):
        writer = File.CreateText( configFile )

        for machine in machines:
            if machine != "":
                writer.WriteLine( "%s 1 %s\n" % ( machine, self.VrayDBRPortRange ) )

        writer.WriteLine( "restart_slaves 0\n" ) #no point restarting slave after end of render as the job will be completed and V-Ray Spawner will be shutdown.
        writer.WriteLine( "list_in_scene 0\n" ) #we should never respect the V-Ray Spawners as declared/saved in the max scene file.
        writer.WriteLine( "max_servers 0\n" ) #we should always try to use ALL V-Ray Spawners that are configured in the cfg file.
        
        if self.VrayDBRUseLocalMachine:
            writer.WriteLine( "use_local_machine 1\n" )
        else:
            writer.WriteLine( "use_local_machine 0\n" )
        
        if self.VrayDBRTransferMissingAssets:
            writer.WriteLine( "transfer_missing_assets 1\n" )
        else:
            writer.WriteLine( "transfer_missing_assets 0\n" )

        if self.VrayDBRUseCachedAssets:
            writer.WriteLine( "use_cached_assets 1\n" )
        else:
            writer.WriteLine( "use_cached_assets 0\n" )
        
        if self.VrayDBRCacheLimitType == "None":
            writer.WriteLine( "cache_limit_type 0\n" )
        if self.VrayDBRCacheLimitType == "Age (hours)":
            writer.WriteLine( "cache_limit_type 1\n" )
        if self.VrayDBRCacheLimitType == "Size (GB)":
            writer.WriteLine( "cache_limit_type 2\n" )

        writer.WriteLine( "cache_limit %s\n" % self.VrayDBRCacheLimit )
        writer.Close()

    def UpdateVrayRtDBRConfigFile( self, machines, configFile ):
        writer = File.CreateText( configFile )

        for machine in machines:
            if machine != "":
                writer.WriteLine( "%s 1 %s\n" % ( machine, self.VrayRtDBRPortRange ) )

        if self.VrayRtDBRAutoStartLocalSlave:
            writer.WriteLine( "autostart_local_slave 1\n" )
        else:
            writer.WriteLine( "autostart_local_slave 0\n" )

        writer.Close()

    def UpdateMentalRayConfigFile( self, machines, configFile ):
        # Mental Ray - write out machine names, one entry per line into configFile, incl. port number if defined. If not, use default.
        writer = File.CreateText( configFile )

        for machine in machines:
            if machine != "":
                if self.MentalRaySatPortNumber != "":
                    writer.WriteLine( "%s:%s\n" % ( machine, self.MentalRaySatPortNumber ) )
                else:
                    writer.WriteLine( "%s\n" % machine )

        writer.Close()

    def GetGpuOverrides( self ):
        resultGPUs = []
        
        # If the number of gpus per task is set, then need to calculate the gpus to use.
        gpusPerTask = self.Plugin.GetIntegerPluginInfoEntryWithDefault( "GPUsPerTask", 0 )
        gpusSelectDevices = self.Plugin.GetPluginInfoEntryWithDefault( "GPUsSelectDevices", "" )

        if self.Plugin.OverrideGpuAffinity():
            overrideGPUs = self.Plugin.GpuAffinity()
            if gpusPerTask == 0 and gpusSelectDevices != "":
                gpus = gpusSelectDevices.split( "," )
                notFoundGPUs = []
                for gpu in gpus:
                    if int( gpu ) in overrideGPUs:
                        resultGPUs.append( gpu )
                    else:
                        notFoundGPUs.append( gpu )
                
                if len( notFoundGPUs ) > 0:
                    self.Plugin.LogWarning( "The Slave is overriding its GPU affinity and the following GPUs do not match the Slaves affinity so they will not be used: " + ",".join( notFoundGPUs ) )
                if len( resultGPUs ) == 0:
                    self.Plugin.FailRender( "The Slave does not have affinity for any of the GPUs specified in the job." )
            elif gpusPerTask > 0:
                if gpusPerTask > len( overrideGPUs ):
                    self.Plugin.LogWarning( "The Slave is overriding its GPU affinity and the Slave only has affinity for " + str( len( overrideGPUs ) ) + " Slaves of the " + str( gpusPerTask ) + " requested." )
                    resultGPUs =  overrideGPUs
                else:
                    resultGPUs = list( overrideGPUs )[:gpusPerTask]
            else:
                resultGPUs = overrideGPUs
        elif gpusPerTask == 0 and gpusSelectDevices != "":
            resultGPUs = gpusSelectDevices.split( "," )

        elif gpusPerTask > 0:
            gpuList = []
            for i in range( ( self.Plugin.GetThreadNumber() * gpusPerTask ), ( self.Plugin.GetThreadNumber() * gpusPerTask ) + gpusPerTask ):
                gpuList.append( str( i ) )
            resultGPUs = gpuList
        
        resultGPUs = list( resultGPUs )
        
        return resultGPUs

    def LaunchCmd( self, executable, arguments, startupDir ):
        self.ManagedCmdProcessRenderExecutable = executable
        self.ManagedCmdProcessRenderArgument = arguments
        self.ManagedCmdProcessStartupDirectory = startupDir

        self.CmdProcess = CmdProcess( self )

        # Newer versions of 3dsCmd use UTF-16-LE for stdout/stderr encoding.
        if self.Version >= 2016:
            self.CmdProcess.StdOutEncoding = "utf-16"

        self.Plugin.StartMonitoredManagedProcess( self.ProgramName, self.CmdProcess )
        self.Plugin.VerifyMonitoredManagedProcess( self.ProgramName )

    def RenderFrame( self ):
        # Wait for the render to complete.
        self.PollUntilComplete()

    def PollUntilComplete( self ):
        elapsedTime = DateTime.Now

        arguments = self.GetArguments()
        self.LaunchCmd( self.CmdExecutable, arguments, Path.GetDirectoryName( self.CmdExecutable ) )

        while not self.Plugin.IsCanceled() and self.Plugin.MonitoredManagedProcessIsRunning( self.ProgramName ) :
            try:
                # Verify that 3dsmaxcmd is still running.
                self.Plugin.VerifyMonitoredManagedProcess( self.ProgramName )
                self.Plugin.FlushMonitoredManagedProcessStdout( self.ProgramName )
                
                # Check for any popup dialogs.
                blockingDialogMessage = self.Plugin.CheckForMonitoredManagedProcessPopups( self.ProgramName )
                if( blockingDialogMessage != "" ):
                    self.Plugin.FailRender( blockingDialogMessage )

                start = DateTime.Now.Ticks
                while( TimeSpan.FromTicks( DateTime.Now.Ticks - start ).Milliseconds < 500 ):
                    
                    # if V-Ray or V-Ray RT DBR off-load job only.
                    if self.Plugin.VrayDBRJob or self.Plugin.VrayRtDBRJob:
                        
                        # Only for master TaskId:0 machine, update the local V-Ray *.cfg file.
                        if int(self.Plugin.GetCurrentTaskId()) == 0:

                            # Update DBR off-load cfg file if another 30 seconds has elapsed.
                            if DateTime.Now.Subtract( elapsedTime ).TotalSeconds >= 30:

                                # reset the time interval.
                                elapsedTime = DateTime.Now

                                machines = self.GetDBRMachines()

                                # Update only if list of DBR machines has changed.
                                if self.DBRMachines != machines:

                                    if len(machines) > 0:
                                        self.Plugin.LogInfo( self.Plugin.Prefix + "Updating cfg file for distributed render with the following machines:" )
                                        for machine in machines:
                                            self.Plugin.LogInfo( self.Plugin.Prefix + "  " + machine )
                                    else:
                                        self.Plugin.LogInfo( self.Plugin.Prefix + "0 machines available currently to DBR, local machine will be used unless configured in plugin settings to be ignored" )

                                    # Update the V-Ray cfg file on the master machine.
                                    if self.Plugin.VrayDBRJob:
                                        self.UpdateVrayDBRConfigFile( machines, self.DBRConfigFile )
                                    else:
                                        self.UpdateVrayRtDBRConfigFile( machines, self.DBRConfigFile )

                                    self.DBRMachines = machines

            except Exception as e:
                self.Plugin.FailRender( "RenderTask: Unexpected exception (%s)" % e.Message )
        
        if( self.Plugin.IsCanceled() ):
            self.Plugin.FailRender( "Render was canceled" )

######################################################################
## This is the class that starts up the 3dsCmd process.
######################################################################
class CmdProcess( ManagedProcess ):
    CmdController = None

    def __init__( self, cmdController ):
        self.CmdController = cmdController

        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.StartupDirectoryCallback += self.StartupDirectory
        self.CheckExitCodeCallback += self.CheckExitCode

        self.Framecount = 0
    
    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.StartupDirectoryCallback
        del self.CheckExitCodeCallback
    
    def InitializeProcess( self ):
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        self.HideDosWindow = True
        self.HandleQtPopups = True
        self.SetEnvironmentVariable( "QT_USE_NATIVE_WINDOWS","1" )
        self.HandleWindows10Popups = True

        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( "'ERROR :.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( ".*Error.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "Frame [0-9]+ assigned" ).HandleCallback += self.HandleStdoutProgress
        
        # Set the popup ignorers.
        self.AddPopupIgnorer( ".*Render history settings.*" )
        self.AddPopupIgnorer( ".*Render history note.*" )
        self.AddPopupIgnorer( ".*Rendering In Progress.*" )
        self.AddPopupIgnorer( ".*Rendering.*" )

        # Ignore 3dsMax MAXScript Debugger Popup (ENU, FRA, DEU, JPN, CHS, KOR, PTB)
        self.AddPopupIgnorer( "MAXScript .*" ) #ENU #JPN #CHS #KOR
        self.AddPopupIgnorer( ".* MAXScript" ) #FRA #PTB
        self.AddPopupIgnorer( "MAXScript-Debugger" ) #DEU

        # Handle Corona VFB Saving Options
        self.AddPopupIgnorer( ".*Save Image.*" )
        self.AddPopupIgnorer( ".*Confirmation.*" )
        self.AddPopupIgnorer( ".*Save as.*" )
        self.AddPopupIgnorer( ".*Select file.*" )
        self.AddPopupIgnorer( ".*File Exists.*" )
        self.AddPopupIgnorer( ".*Curve Editor.*" )

        # Handle Corona Error Message dialog
        self.AddPopupIgnorer( "Corona Error Message(s)" )

        # For Maxwell
        self.AddPopupIgnorer( ".*Maxwell Translation Window.*" )
        self.AddPopupIgnorer( ".*Import Multilight.*" )

        # Set the popup handlers.
        self.AddPopupHandler( ".*Microsoft Visual C\\+\\+ Runtime Library.*", "OK" )
        self.AddPopupHandler( ".*V-Ray warning.*", "OK" )
        
        # Handle Maxwell Plug-in Update Notification dialog
        self.AddPopupHandler( ".*Maxwell Plug-in Update Notification.*", "Don't notify me about this version automatically;Close" )
        
        # Handle RealFlow Plug-in Update Notification dialog
        self.AddPopupHandler( ".*RealFlow Plug-in Update Notification.*", "Don't notify me about this version automatically;Close" )

        # Handle Program Compatibility Assistant dialog
        self.AddPopupHandler( "Program Compatibility Assistant", "Close" )

        # Ignore 3dsMax State Sets dialog (visible when HandleWindows10Popups=True)
        self.AddPopupIgnorer( "State Sets" )

        # Handle PNG Plugin - [PNG Library Internal Error]
        self.AddPopupHandler( "PNG Plugin", "OK" )

        # Ignore Redshift Render View
        self.AddPopupIgnorer( "3dsmax" )
        self.AddPopupIgnorer( "Save Image As" )
        self.AddPopupIgnorer( "Save Multilayer EXR As" )
        self.AddPopupIgnorer( "Select snapshots folder" )

    def RenderExecutable( self ):
        return self.CmdController.ManagedCmdProcessRenderExecutable

    def RenderArgument( self ):
        return self.CmdController.ManagedCmdProcessRenderArgument

    def StartupDirectory( self ):
        return self.CmdController.ManagedCmdProcessStartupDirectory

    def HandleStdoutError( self ):
        self.CmdController.Plugin.FailRender( self.GetRegexMatch( 0 ) )
        
    def HandleStdoutProgress( self ):
        startFrame = self.CmdController.Plugin.GetStartFrame()
        endFrame = self.CmdController.Plugin.GetEndFrame()
        
        self.Framecount = self.Framecount + 1
        if( ( endFrame - startFrame) != -1 ):
            self.CmdController.Plugin.SetProgress( ( float(self.Framecount) / ( endFrame - startFrame + 1 ) ) * 100 )
                
        if( self.Framecount < ( endFrame - startFrame + 1 ) ):
            self.CmdController.Plugin.SetStatusMessage( "Rendering frame " + str( startFrame + self.Framecount ) )

    def CheckExitCode( self, exitCode ):
        if exitCode != 0:
            self.CmdController.Plugin.FailRender( "Process exit code: %s" % exitCode )

######################################################################
## This is the class that starts up the V-Ray Spawner process.
######################################################################
class VRaySpawnerProcess( ManagedProcess ):
    Plugin = None
    IsRT = False
    
    def __init__( self, plugin, isRT ):
        self.Plugin = plugin
        self.IsRt = isRT
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderArgumentCallback += self.RenderArgument
        self.RenderExecutableCallback += self.RenderExecutable
    
    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderArgumentCallback
        del self.RenderExecutableCallback
    
    def InitializeProcess( self ):
        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        self.HideDosWindow = True
        self.HandleQtPopups = True
        self.SetEnvironmentVariable( "QT_USE_NATIVE_WINDOWS","1" )

        # Ignore 3dsMax MAXScript Debugger Popup (ENU, FRA, DEU, JPN, CHS, KOR, PTB)
        self.AddPopupIgnorer( "MAXScript .*" ) #ENU #JPN #CHS #KOR
        self.AddPopupIgnorer( ".* MAXScript" ) #FRA #PTB
        self.AddPopupIgnorer( "MAXScript-Debugger" ) #DEU

        # Handle Corona VFB Saving Options
        self.AddPopupIgnorer( ".*Save Image.*" )
        self.AddPopupIgnorer( ".*Confirmation.*" )
        self.AddPopupIgnorer( ".*Save as.*" )
        self.AddPopupIgnorer( ".*Select file.*" )
        self.AddPopupIgnorer( ".*File Exists.*" )
        self.AddPopupIgnorer( ".*Curve Editor.*" )

        # Handle Corona Error Message dialog
        self.AddPopupIgnorer( "Corona Error Message(s)" )

        # For Maxwell
        self.AddPopupIgnorer( ".*Maxwell Translation Window.*" )
        self.AddPopupIgnorer( ".*Import Multilight.*" )

        # If we're overriding CPU Affinity, ensure it works for V-Ray by setting their environment variable
        if self.Plugin.OverrideCpuAffinity():
            self.Plugin.LogInfo( "Setting VRAY_USE_THREAD_AFFINITY to 0 to ensure CPU Affinity works." )
            self.SetEnvironmentVariable( "VRAY_USE_THREAD_AFFINITY", "0" )

        # Only V-Ray RT uses the GPU
        if self.IsRt:
            # Check if we are overriding GPU affinity
            selectedGPUs = self.Plugin.MyCmdController.GetGpuOverrides()
            if len(selectedGPUs) > 0:
                vrayGpus = "index" + ";index".join( [ str( gpu ) for gpu in selectedGPUs ] ) # "index0;index1"
                self.Plugin.LogInfo( "This Slave is overriding its GPU affinity, so the following GPUs will be used by V-Ray RT: %s" % vrayGpus )
                self.SetEnvironmentVariable( "VRAY_OPENCL_PLATFORMS_x64", vrayGpus ) # V-Ray RT

    def RenderExecutable( self ):
        version = self.Plugin.GetIntegerPluginInfoEntry( "Version" )
        if( version < 2010 ):
            self.Plugin.FailRender( self.Plugin.Prefix + "Only 3dsmax 2010 and later is supported" )

        isMaxDesign = self.Plugin.GetBooleanPluginInfoEntryWithDefault( "IsMaxDesign", False )
        forceBuild = self.Plugin.GetPluginInfoEntryWithDefault( "MaxVersionToForce", "none" ).lower()
        if( version > 2013 ):
            forceBuild = "none"
        
        # Figure out the render executable to use for rendering.
        vraySpawnerExecutable = ""
        if self.IsRt:
            if( forceBuild == "64bit" ):
                exeList = r"C:\Program Files\Chaos Group\V-Ray\RT for 3ds Max " + str(version) + r" for x64\bin\vrayrtspawner.exe"
                vraySpawnerExecutable = FileUtils.SearchFileList( exeList )
            elif( forceBuild == "32bit" ):
                exeList = r"C:\Program Files\Chaos Group\V-Ray\RT for 3ds Max " + str(version) + r" for x86\bin\vrayrtspawner.exe;C:\Program Files (x86)\Chaos Group\V-Ray\RT for 3ds Max " + str(version) + r" for x86\bin\vrayrtspawner.exe"
                vraySpawnerExecutable = FileUtils.SearchFileList( exeList )
            else:
                exeList = r"C:\Program Files\Chaos Group\V-Ray\RT for 3ds Max " + str(version) + r" for x64\bin\vrayrtspawner.exe;C:\Program Files\Chaos Group\V-Ray\RT for 3ds Max " + str(version) + r" for x86\bin\vrayrtspawner.exe;C:\Program Files (x86)\Chaos Group\V-Ray\RT for 3ds Max " + str(version) + r" for x86\bin\vrayrtspawner.exe"
                vraySpawnerExecutable = FileUtils.SearchFileList( exeList )
                
            if( vraySpawnerExecutable == "" ):
                self.Plugin.FailRender( self.Plugin.Prefix + "Could not find V-Ray Spawner executable in the following locations: " + exeList )
        else:
            renderExecutableKey = "CmdRenderExecutable" + str(version)
            maxEdition = ""
            if isMaxDesign:
                renderExecutableKey = renderExecutableKey + "Design"
                maxEdition = " Design"
            
            renderExecutableList = self.Plugin.GetConfigEntry( renderExecutableKey ).strip()
            maxRenderExecutable = ""
            if(SystemUtils.IsRunningOnWindows()):
                if( forceBuild == "32bit" ):
                    maxRenderExecutable = FileUtils.SearchFileListFor32Bit( renderExecutableList )
                    if( maxRenderExecutable == "" ):
                        self.Plugin.LogWarning( self.Plugin.Prefix + "No 32 bit 3dsmax" + maxEdition + " " + str(version) + " render executable found in the semicolon separated list \"" + renderExecutableList + "\". Checking for any executable that exists instead." )
                elif( forceBuild == "64bit" ):
                    maxRenderExecutable = FileUtils.SearchFileListFor64Bit( renderExecutableList )
                    if( maxRenderExecutable == "" ):
                        self.Plugin.LogWarning( self.Plugin.Prefix + "No 64 bit 3dsmax" + maxEdition + " " + str(version) + " render executable found in the semicolon separated list \"" + renderExecutableList + "\". Checking for any executable that exists instead." )
            
            if( maxRenderExecutable == "" ):
                maxRenderExecutable = FileUtils.SearchFileList( renderExecutableList )
                if( maxRenderExecutable == "" ):
                    self.Plugin.FailRender( self.Plugin.Prefix + "No 3dsmax" + maxEdition + " " + str(version) + " render executable found in the semicolon separated list \"" + renderExecutableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
                    
            self.Plugin.LogInfo( self.Plugin.Prefix + "3ds Max executable: %s" % maxRenderExecutable )
            vraySpawnerExecutable = PathUtils.ChangeFilename( maxRenderExecutable, "vrayspawner" + str(version) + ".exe" )
            if not File.Exists( vraySpawnerExecutable ):
                self.Plugin.FailRender( self.Plugin.Prefix + "V-Ray Spawner executable does not exist: " + vraySpawnerExecutable )

        self.Plugin.LogInfo( self.Plugin.Prefix + "Spawner executable: %s" % vraySpawnerExecutable )

        vraySpawnerExecutableVersion = FileVersionInfo.GetVersionInfo( vraySpawnerExecutable )
        self.Plugin.LogInfo( self.Plugin.Prefix + "Spawner executable version: %s" % vraySpawnerExecutableVersion.FileVersion )
        
        # Handle pre-existing v-ray spawner instance running on machine.
        spawnerExistingProcess = self.Plugin.GetConfigEntryWithDefault( "VRaySpawnerExistingProcess", "Fail On Existing Process" )
        self.Plugin.LogInfo( self.Plugin.Prefix + "Existing V-Ray Spawner Process: %s" % spawnerExistingProcess )

        processName = Path.GetFileNameWithoutExtension( vraySpawnerExecutable )
        if( ProcessUtils.IsProcessRunning( processName ) ):
            processes = Process.GetProcessesByName( processName )
            
            if len( processes ) > 0:
                self.Plugin.LogWarning( self.Plugin.Prefix + "Found existing '%s' process" % processName )
                process = processes[ 0 ]

                if( spawnerExistingProcess == "Fail On Existing Process" ):
                    if process != None:
                        self.Plugin.FailRender( self.Plugin.Prefix + "Fail On Existing Process is enabled, and a process '%s' with pid '%d' exists - shut down this copy of V-Ray Spawner. Ensure V-Ray Spawner is NOT already running! (GUI or Service Mode)" % (processName, process.Id) )

                if( spawnerExistingProcess == "Kill On Existing Process" ):
                    if( ProcessUtils.KillProcesses( processName ) ):
                        if process != None:
                            self.Plugin.LogInfo( self.Plugin.Prefix + "Successfully killed V-Ray Spawner process: '%s' with pid: '%d'" % (processName, process.Id) )

                        SystemUtils.Sleep( 5000 )

                        if( ProcessUtils.IsProcessRunning( processName ) ):
                            self.Plugin.LogWarning( self.Plugin.Prefix + "V-Ray Spawner is still running: '%s' process, perhaps due to it being automatically restarted after the previous kill command. Ensure V-Ray Spawner is NOT already running! (GUI or Service Mode)" % processName )
                            process = Process.GetProcessesByName( processName )[ 0 ]
                            if process != None:
                                self.Plugin.FailRender( self.Plugin.Prefix + "Kill On Existing Process is enabled, and a process '%s' with pid '%d' still exists after executing a kill command. Ensure V-Ray Spawner is NOT already running! (GUI or Service Mode)" % (processName, process.Id) )
        
        return vraySpawnerExecutable

    def RenderArgument( self ):
        return ""
