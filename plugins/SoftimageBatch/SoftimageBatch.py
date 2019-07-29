import time
import re

from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

from FranticX.Processes import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return SoftimageBatchPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class SoftimageBatchPlugin (DeadlinePlugin):
    ProgramName = ""
    ProgramProcess = None
    ThreadID = ""
    CommandFilename = ""
    AckFilename = ""
    
    LocalRendering = False
    LocalFilePath = ""
    NetworkFilePath = ""
    
    Framecount = 0
    NumPasses = 1
    PassesComplete = 0
    
    OriginalFilenames = {}
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob
    
    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback
        
        if self.ProgramProcess:
            self.ProgramProcess.Cleanup()
            del self.ProgramProcess
    
    def InitializeProcess( self ):
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Advanced
        self.ProgramName = "SoftimageProcess"
        
    def StartJob(self):
        self.LogInfo( "Start Job" )
        
        self.ThreadID = str( self.GetThreadNumber() )
        self.ProgramName = "SoftimageProcess" + self.ThreadID
        self.CommandFilename = Path.Combine( self.GetJobsDataDirectory(), "command" + self.ThreadID )
        self.AckFilename = Path.Combine( self.GetJobsDataDirectory(), "ack" + self.ThreadID )
        
        self.DeleteTempFiles()
        
        self.ProgramProcess = SoftimageProcess( self, self.CommandFilename, self.AckFilename )
        
        workgroup = self.GetPluginInfoEntryWithDefault( "Workgroup", "" ).strip()
        workgroup = RepositoryUtils.CheckPathMapping( workgroup )
        if len( workgroup ) > 0:
            self.LogInfo( "Switching workgroup before rendering to " + workgroup )
            
            executable = self.ProgramProcess.RenderExecutable()
            arguments = " -processing -w \"" + workgroup + "\""
            startupDir = Path.GetDirectoryName( executable )
            
            self.RunProcess( executable, arguments, startupDir, -1 )
        
        self.StartMonitoredManagedProcess( self.ProgramName, self.ProgramProcess )
        
        self.WaitForStartup()
        
        sceneFile = self.GetPluginInfoEntryWithDefault("SceneFile",self.GetDataFilename())
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        sceneFile = self.ConvertPath( sceneFile )
        self.SendCommand( "ExecuteCommand=OpenScene(" + sceneFile + ")", True )
        
        regionRendering = self.GetBooleanPluginInfoEntryWithDefault( "RegionRendering", False )
        singleRegionJob = self.IsTileJob()
        
        isFxTreeRender = self.GetBooleanPluginInfoEntryWithDefault( "FxTreeRender", False )
        if not isFxTreeRender:
            blank = ""
            
            self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.mentalray.VerbosityLevel,60," + blank + ")", False )
            
            width = self.GetPluginInfoEntryWithDefault( "Width", "" )
            if width != "":
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.ImageWidth," + width + "," + blank + ")", False )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.RenderOptions.ImageWidth," + width + "," + blank + ")", False )
                
            height = self.GetPluginInfoEntryWithDefault( "Height", "" )
            if height != "":
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.ImageHeight," + height + "," + blank + ")", False )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.RenderOptions.ImageHeight," + height + "," + blank + ")", False )
            
            sampleMax = self.GetPluginInfoEntryWithDefault( "SampleMax", "" )
            if sampleMax != "":
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.mentalray.SamplesMax," + sampleMax + "," + blank + ")", False )
            
            filter = self.GetPluginInfoEntryWithDefault( "Filter", "" )
            if filter != "":
                filter = self.GetFilterFromName( filter )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.mentalray.SamplesFilterType," + filter + "," + blank + ")", False )
            
            jitter = self.GetPluginInfoEntryWithDefault( "SampleJitter", "" )
            if jitter != "":
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.mentalray.SamplesJitter," + jitter + "," + blank + ")", False )
            
            motionBlur = self.GetPluginInfoEntryWithDefault( "MotionBlur", "" )
            if motionBlur != "":
                if self.GetBoolean( motionBlur ):
                    self.SendCommand( "ExecuteCommand=SetValue(Passes.*.MotionBlur,1," + blank + ")", False )
                else:
                    self.SendCommand( "ExecuteCommand=SetValue(Passes.*.MotionBlur,0," + blank + ")", False )
            
            skipFrames = self.GetPluginInfoEntryWithDefault( "SkipFrames", "" )
            if skipFrames != "":
                if self.GetBoolean( skipFrames ):
                    self.SendCommand( "ExecuteCommand=SetValue(Passes.*.FrameSkipRendered,1," + blank + ")", False )
                else:
                    self.SendCommand( "ExecuteCommand=SetValue(Passes.*.FrameSkipRendered,0," + blank + ")", False )
            
            # Only set this in StartJob if region rendering is spread across multiple jobs
            if regionRendering and not singleRegionJob:
                xMin = self.GetPluginInfoEntryWithDefault( "RegionLeft", "0" ) 
                yMin = self.GetPluginInfoEntryWithDefault( "RegionTop", "0" )
                xMax = self.GetPluginInfoEntryWithDefault( "RegionRight", "0" ) 
                yMax = self.GetPluginInfoEntryWithDefault( "RegionBottom", "0" )
                
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.CropWindowEnabled,bool(True)," + blank + ")", False )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.CropWindowOffsetX," + xMin + "," + blank + ")", False )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.CropWindowHeight," + yMin + "," + blank + ")", False )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.CropWindowWidth," + xMax + "," + blank + ")", False )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.CropWindowOffsetY," + yMax + "," + blank + ")", False )
            
            # Only set this if this is not a single tile rendering job
            if not singleRegionJob:
                tilePrefix = self.GetPluginInfoEntryWithDefault( "TilePrefix", "" )
                if tilePrefix != "":
                    renderPass = self.GetPluginInfoEntryWithDefault( "Pass", "" )
                    if renderPass != "":
                        frameBufferIndex = 0
                        while True:
                            frameBuffer = self.GetPluginInfoEntryWithDefault( "FrameBuffer" + str(frameBufferIndex), "" )
                            if frameBuffer == "":
                                break
                            
                            frameBufferPath = self.SendCommand( "ExecuteCommand=GetValue(Passes." + renderPass + "." + frameBuffer + ".Filename)", False )
                            frameBufferFilename = Path.GetFileName( frameBufferPath )
                            frameBufferPath = Path.GetDirectoryName( frameBufferPath )
                            self.SendCommand( "ExecuteCommand=SetValue(Passes." + renderPass + "." + frameBuffer + ".Filename," + Path.Combine( frameBufferPath, tilePrefix + frameBufferFilename ) + "," + blank + ")", False )
                            
                            frameBufferIndex = frameBufferIndex + 1
                    else:
                        mainFilename = self.SendCommand( "ExecuteCommand=GetValue(Passes.List.*.Main.Filename)", False )
                        self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.Main.Filename," + tilePrefix + mainFilename + "," + blank + ")", False )
                
            filepath = self.GetPluginInfoEntryWithDefault( "FilePath", "" ).strip()
            filepath = RepositoryUtils.CheckPathMapping( filepath )
            if( len( filepath ) > 0 ):
                filepath = self.ConvertPath( filepath )
                filepath = self.ProcessOutputPath( filepath )
                
                self.LocalRendering = self.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False )
                if self.LocalRendering:
                    self.NetworkFilePath = filepath
                    
                    filepath = self.CreateTempDirectory( "softimageOutput" )
                    filepath = self.ProcessOutputPath( filepath )
                    
                    self.LocalFilePath = filepath
                    
                    self.LogInfo( "Rendering to local drive, will copy files and folders to final location after render is complete" )
                else:
                    self.LogInfo( "Rendering to network drive" )
                
                self.SendCommand( "ExecuteCommand=SetValue(Passes.RenderOptions.OutputDir," + filepath +")", False )

            gpus = ""
            gpusPerTask = self.GetIntegerPluginInfoEntryWithDefault( "RedshiftGPUsPerTask", -1 )
            
            # gpusPerTask will be 0 or greater if RedShift is the chosen renderer.
            if gpusPerTask != -1:
                gpusSelectDevices = self.GetPluginInfoEntryWithDefault( "RedshiftGPUsSelectDevices", "" )
                
                if gpusPerTask == 0 and gpusSelectDevices != "":
                    gpuList = gpusSelectDevices.split(",")
                    gpus = ";".join(gpuList)
                    self.LogInfo( "Specific GPUs specified, so the following GPUs will be used by RedShift: " + gpus )
                    self.SendCommand( "ExecuteCommand=Redshift_SelectCudaDevices(array(" + gpus +"))", False )

                elif gpusPerTask > 0:
                    gpuList = []
                    for i in range((self.GetThreadNumber() * gpusPerTask), (self.GetThreadNumber() * gpusPerTask) + gpusPerTask):
                        gpuList.append(str(i))
                    
                    gpus = ";".join(gpuList)
                    self.LogInfo( "GPUs per task is greater than 0, so the following GPUs will be used by RedShift: " + gpus )
                    self.SendCommand( "ExecuteCommand=Redshift_SelectCudaDevices(array(" + gpus +"))", False )
                    
                elif self.OverrideGpuAffinity():
                    gpuList = []
                    for gpuId in self.GpuAffinity():
                        gpuList.append( str( gpuId ) )
                    
                    gpus = ";".join(gpuList)
                    self.LogInfo( "This Slave is overriding its GPU affinity, so the following GPUs will be used by RedShift: " + gpus )
                    self.SendCommand( "ExecuteCommand=Redshift_SelectCudaDevices(array(" + gpus +"))", False )
        
        self.FlushMonitoredManagedProcessStdout( self.ProgramName )
        
    def RenderTasks(self):
        self.LogInfo( "Render Tasks" )
        
        self.FlushMonitoredManagedProcessStdout( self.ProgramName )
        
        self.FrameCount = 0
        self.NumPasses = 1
        self.PassesComplete = 0
        
        startFrame = str(self.GetStartFrame())
        endFrame = str(self.GetEndFrame())
        blank = ""
        
        isFxTreeRender = self.GetBooleanPluginInfoEntryWithDefault( "FxTreeRender", False )
        if isFxTreeRender:
            outputNode = self.GetPluginInfoEntry( "FxTreeOutputNode" )
            outputFile = self.GetPluginInfoEntryWithDefault( "FxTreeOutputFile", "" )
            outputFile = RepositoryUtils.CheckPathMapping( outputFile )
            frameOffset = self.GetPluginInfoEntry( "FxTreeFrameOffset" )
            
            if outputFile != "":
                outputFile = self.ConvertPath( outputFile )
                outputFile = self.ProcessOutputPath( outputFile )
                self.SendCommand( "ExecuteCommand=SetValue(" + outputNode + ".FileName," + outputFile + "," + blank + ")", False )
            
            self.SendCommand( "ExecuteCommand=SetValue(" + outputNode + ".StartFrame," + startFrame +"," + blank +")", False )
            self.SendCommand( "ExecuteCommand=SetValue(" + outputNode + ".EndFrame," + endFrame +"," + blank +")", False )
            self.SendCommand( "ExecuteCommand=SetValue(" + outputNode + ".FrameOffset," + frameOffset + "," + blank + ")", False )
            self.SendCommand( "ExecuteCommand=SetValue(" + outputNode + ".Step,1," + blank + ")", False )
            
            self.SendCommand( "ExecuteCommand=RenderFxOp(" + outputNode + ")", False )
        else:
            renderPass = self.GetPluginInfoEntryWithDefault( "Pass", "" )
            
            regionRendering = self.GetBooleanPluginInfoEntryWithDefault( "RegionRendering", False )
            singleRegionJob = self.IsTileJob()
            singleRegionFrame = str(self.GetStartFrame())
            singleRegionIndex = self.GetCurrentTaskId()
            
            if regionRendering and singleRegionJob:
                xMin = self.GetPluginInfoEntryWithDefault( "RegionLeft" + singleRegionIndex, "0" )
                yMin = self.GetPluginInfoEntryWithDefault( "RegionTop" + singleRegionIndex, "0" )
                xMax = self.GetPluginInfoEntryWithDefault( "RegionRight" + singleRegionIndex, "0" )
                yMax = self.GetPluginInfoEntryWithDefault( "RegionBottom" + singleRegionIndex, "0" )
                
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.CropWindowEnabled,bool(True)," + blank + ")", False )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.CropWindowOffsetX," + xMin + "," + blank + ")", False )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.CropWindowHeight," + yMin + "," + blank + ")", False )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.CropWindowWidth," + xMax + "," + blank + ")", False )
                self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.CropWindowOffsetY," + yMax + "," + blank + ")", False )
                
                tilePrefix = self.GetPluginInfoEntryWithDefault( "RegionPrefix" + singleRegionIndex, "" ).strip()
                if tilePrefix != "":
                    if renderPass != "":
                        frameBufferIndex = 0
                        while True:
                            frameBuffer = self.GetPluginInfoEntryWithDefault( "FrameBuffer" + str(frameBufferIndex), "" )
                            if frameBuffer == "":
                                break
                            
                            if frameBuffer in self.OriginalFilenames:
                                frameBufferPath = self.OriginalFilenames[frameBuffer]
                            else:
                                frameBufferPath = self.SendCommand( "ExecuteCommand=GetValue(Passes." + renderPass + "." + frameBuffer + ".Filename)", False )
                                self.OriginalFilenames[frameBuffer] = frameBufferPath
                            
                            frameBufferFilename = Path.GetFileName( frameBufferPath )
                            frameBufferPath = Path.GetDirectoryName( frameBufferPath )
                            self.SendCommand( "ExecuteCommand=SetValue(Passes." + renderPass + "." + frameBuffer + ".Filename," + Path.Combine( frameBufferPath, tilePrefix + frameBufferFilename ) + "," + blank + ")", False )
                            
                            frameBufferIndex = frameBufferIndex + 1
                    else:
                        if "Main" in self.OriginalFilenames:
                            mainFilename = self.OriginalFilenames["Main"]
                        else:
                            mainFilename = self.SendCommand( "ExecuteCommand=GetValue(Passes.List.*.Main.Filename)", False )
                            self.OriginalFilenames["Main"] = mainFilename
                        
                        self.SendCommand( "ExecuteCommand=SetValue(Passes.List.*.Main.Filename," + tilePrefix + mainFilename + "," + blank + ")", False )
            
            if renderPass == "":
                response = self.SendCommand( "ExecuteCommand=GetValue(Passes.List)", False )
                passes = response.split(",")
                self.NumPasses = len(passes)
                
                for currPass in passes:
                    if regionRendering and singleRegionJob:
                        self.SendCommand( "ExecuteCommand=RenderPasses(" + currPass + ",int(" + singleRegionFrame + "),int(" + singleRegionFrame +"))", True )
                    else:
                        self.SendCommand( "ExecuteCommand=RenderPasses(" + currPass + ",int(" + startFrame + "),int(" + endFrame +"))", True )
            else:
                passes = renderPass.split(",")
                self.NumPasses = len(passes)
                
                for currPass in passes:
                    if not currPass.startswith( "Passes." ):
                        currPass = "Passes." + currPass
                    
                    if regionRendering and singleRegionJob:
                        self.SendCommand( "ExecuteCommand=RenderPasses(" + currPass + ",int(" + singleRegionFrame + "),int(" + singleRegionFrame +"))", True )
                    else:
                        self.SendCommand( "ExecuteCommand=RenderPasses(" + currPass + ",int(" + startFrame + "),int(" + endFrame +"))", True )
                
            self.PostRender()
        
        self.FlushMonitoredManagedProcessStdout( self.ProgramName )
    
    def EndJob(self):
        self.LogInfo( "Ending Softimage Job" )
        self.FlushMonitoredManagedProcessStdoutNoHandling(self.ProgramName)
        self.ShutdownMonitoredManagedProcess(self.ProgramName)
        
        self.DeleteTempFiles()
    
    def WaitForStartup( self ):
        timeout = self.GetIntegerConfigEntry( "ConnectionTimeout" )
        self.LogInfo( "Waiting for Softimage connection: "  + str(timeout) + " seconds remaining" )
        while timeout > 0:
            if self.IsCanceled():
                self.FailRender( "Received cancel task command from Deadline." )
            
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            response = self.WaitForCommandFile( self.AckFilename, True, 1000 )
            if response != "":
                self.LogInfo( "Received response: " + response )
                break
            
            timeout = timeout - 1
            if timeout % 10 == 0:
                self.LogInfo( "Waiting for Softimage connection: "  + str(timeout) + " seconds remaining..." )
            
        if timeout <= 0:
            self.FailRender( "Timed out while waiting for Softimage to start up and establish a connection. Perhaps consider increasing the Connection Timeout setting in the SoftimageBatch Plugin Configuration in the Deadline Monitor." )
    
    def SendCommand( self, command, checkProgress ):
        #self.LogInfo( "Sending command: " + command )
        self.CreateCommandFile( self.CommandFilename, command )
        
        progressTimeout = self.GetIntegerConfigEntryWithDefault( "ProgressUpdateTimeout", 0 ) * 1000
        if progressTimeout <= 0:
            checkProgress = False
        
        timeout = progressTimeout
        
        while True:
            if self.IsCanceled():
                self.FailRender( "Received cancel task command from Deadline." )
            
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            if checkProgress:
                if self.ProgramProcess.CheckGotProgress():
                    timeout = progressTimeout
                    self.ProgramProcess.ResetGotProgress()
                else:
                    timeout = timeout - 100
                    if timeout <= 0:
                        self.FailRender( "Timed out waiting for the next progress update - consider increasing the ProgressUpdateTimeout in the plugin configuration." )
            
            response = self.WaitForCommandFile( self.AckFilename, True, 100 )
            if response != "":
                #self.LogInfo( "Received response: " + response )
                return response

    def GetFilterFromName( self, filter ):
        filter = filter.lower()
        if filter =="box":
            return "0"
        elif filter == "triangle":
            return "1"
        elif filter == "gauss":
            return "2"
        elif filter == "mitchell":
            return "3"
        elif filter == "lanczos":
            return "4"
        else:
            self.FailRender( filter + " is not a known filter" )
            return ""
    
    def GetBoolean( self, value ):
        value = value.lower()
        return (value == "true" or value == "1")
    
    def ConvertPath( self, path ):
        path = path.replace( "\\", "/" )
        if SystemUtils.IsRunningOnWindows():
            if path.startswith( "/" ) and not path.startswith( "//" ):
                path = "/" + path
        else:
            if path.startswith( "//" ):
                path = path[1:len(path)]
        return path
    
    def ProcessOutputPath( self, outputPath ):
        if( SystemUtils.IsRunningOnLinux() ):
            outputPath = outputPath.replace( "\\","/" )
        else:
            outputPath = outputPath.replace( "/", "\\" )
        
        lastChar = outputPath[ len( outputPath ) - 1 : len( outputPath ) ]
        if( lastChar == "\\" or lastChar == "/" ):
            outputPath = outputPath[ 0 : len( outputPath ) - 1 ]
        
        return outputPath
        
    def PostRender( self ):
        if( self.LocalRendering ):
            self.LogInfo( "Moving output files and folders from " + self.LocalFilePath + " to " + self.NetworkFilePath )
            self.VerifyAndMoveDirectory( self.LocalFilePath, self.NetworkFilePath, False, -1 )
    
    def DeleteTempFiles( self ):
        if File.Exists( self.CommandFilename ):
            File.Delete( self.CommandFilename )
        if File.Exists( self.AckFilename ):
            File.Delete( self.AckFilename )

#################################################################
##This class is to starup up xsibatch.bat with the script argument
###################################################################
class SoftimageProcess(ManagedProcess):
    deadlinePlugin = None
    
    CurrentPass = ""
    StartupScript = ""
    CommandFilename = ""
    AckFilename = ""
    GotProgress = False
    
    def __init__( self, deadlinePlugin, commandFilename, ackFilename ):
        self.deadlinePlugin = deadlinePlugin
        
        self.CommandFilename = commandFilename
        self.AckFilename = ackFilename
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess( self ):
        self.ProcessPriority = ProcessPriorityClass.Normal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( ".*ERROR :.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "(Rendering frame: [0-9]+) \\(([0-9]+) % done\\)" ).HandleCallback += self.HandleStdoutFrameDone
        self.AddStdoutHandlerCallback( "(Rendering frame: [0-9]+) \\(([0-9]+\\.[0-9]+) % done\\)" ).HandleCallback += self.HandleStdoutFrameDone
        self.AddStdoutHandlerCallback( "'INFO : Rendering done!" ).HandleCallback += self.HandleStdoutInfoDone
        self.AddStdoutHandlerCallback( "'INFO : Couldn't find the pass name .*" ).HandleCallback += self.HandleStdoutInfoError
        self.AddStdoutHandlerCallback( ".*progr:\\s+([0-9]{1,3}.[0-9]+)%\\s+rendered\\son.*" ).HandleCallback += self.HandleStdoutProgress1
        self.AddStdoutHandlerCallback( ".*progr:\\s+rendering\\sfinished.*" ).HandleCallback += self.HandleStdoutProgress2
        self.AddStdoutHandlerCallback( ".*Render completed \\(100% done\\).*" ).HandleCallback += self.HandleStdoutComplete
        self.AddStdoutHandlerCallback( ".*INFO : 4000 - Comp.*" ).HandleCallback += self.HandleStdoutFxTreeProgress
        self.AddStdoutHandlerCallback( ".*INFO : 4000 - Done.*" ).HandleCallback += self.HandleStdoutFxTreeDone
        self.AddStdoutHandlerCallback( ".*INFO : Rendering pass (.*)" ).HandleCallback += self.HandleStdoutNewPass
        self.AddStdoutHandlerCallback( ".*ERROR - Could not open script file.*" ).HandleCallback += self.HandleStdoutScriptError
        
        self.AddStdoutHandlerCallback(".*\\[arnold\\].* +([0-9]+)% done.*" ).HandleCallback += self.HandleStdoutProgress1
        self.AddStdoutHandlerCallback(".*\\[arnold\\].* render done.*" ).HandleCallback += self.HandleStdoutProgress2
        
    def RenderExecutable( self ):
        softimageExe = ""
        
        version = self.deadlinePlugin.GetPluginInfoEntry( "Version" )
        periodIndex = version.find( "." )
        if periodIndex > 0:
            version = version[0:periodIndex]
        
        self.deadlinePlugin.LogInfo( "Rendering with Softimage version " + version )
        
        softimageExeList = self.deadlinePlugin.GetConfigEntry( "RenderExecutable" + version )
        if SystemUtils.IsRunningOnWindows():
            softimageExeList = softimageExeList.lower()
        
        build = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        if SystemUtils.IsRunningOnWindows():
            if build == "32bit":
                tempSoftimageExeList = self.ReplaceSoftimageBatchPath( softimageExeList )
                self.deadlinePlugin.LogInfo( "Enforcing 32 bit build of Softimage" )
                softimageExe = FileUtils.SearchFileListFor32Bit( tempSoftimageExeList )
                if( softimageExe == "" ):
                    self.deadlinePlugin.LogWarning("32 bit Softimage " + version + " render executable was not found in the semicolon separated list \"" + softimageExeList + "\". Checking for any executable that exists instead.")
                softimageExe = self.RevertSoftimageBatchPath( softimageExe )
                
            elif build == "64bit":
                tempSoftimageExeList = self.ReplaceSoftimageBatchPath( softimageExeList )
                self.deadlinePlugin.LogInfo( "Enforcing 64 bit build of Softimage" )
                softimageExe = FileUtils.SearchFileListFor64Bit( tempSoftimageExeList )
                if( softimageExe == "" ):
                    self.deadlinePlugin.LogWarning( "64 bit Softimage " + version + " render executable was not found in the semicolon separated list \"" + softimageExeList + "\". Checking for any executable that exists instead.")
                softimageExe = self.RevertSoftimageBatchPath( softimageExe )
                
        if( softimageExe == "" ):
            self.deadlinePlugin.LogInfo( "Not enforcing a build of Softimage" )
            softimageExe = FileUtils.SearchFileList( softimageExeList )
            if( softimageExe == "" ):
                self.deadlinePlugin.FailRender("Softimage " + version + " render executable was not found in the semicolon separated list \"" + softimageExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor.")
        
        return softimageExe
    
    def RenderArgument( self ):
        self.StartupScript = Path.Combine( self.deadlinePlugin.GetPluginDirectory(), "SoftimageBatchStartup.vbs" )
        
        scriptArguments = "-args"
        scriptArguments += " -commandFilename \"" + self.CommandFilename + "\""
        scriptArguments += " -ackFilename \"" + self.AckFilename + "\""
        
        renderarguments = ""
        
        # The processing flag can be used when rendering with non-mentalray renders to skip Softimage's batch license check.
        if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "SkipBatchLicense", False ):
            renderarguments += " -processing"
        
        threads = self.deadlinePlugin.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if threads > 0:
            renderarguments += " -thread " + str(threads)
        
        renderarguments += " -script \"" + self.StartupScript + "\" -main RenderMain " + scriptArguments
        
        return renderarguments
    
    def ReplaceSoftimageBatchPath( self, path ):
        if SystemUtils.IsRunningOnWindows():
            path = path.replace( "xsibatch.bat", "xsibatch.exe" ).replace( "xsi.bat", "xsi.exe" )
        else:
            path = path.replace( "xsibatch", "XSIBATCH.bin" ).replace( "xsi", "XSI.bin" )
        return path
    
    def RevertSoftimageBatchPath( self, path ):
        if SystemUtils.IsRunningOnWindows():
            path = path.replace( "xsibatch.exe", "xsibatch.bat" ).replace( "xsi.exe", "xsi.bat" )
        else:
            path = path.replace( "XSIBATCH.bin", "xsibatch" ).replace( "XSI.bin", "xsi" )
        return path
    
    def CheckGotProgress( self ):
        return self.GotProgress
    
    def ResetGotProgress( self ):
        self.GotProgress = False
    
    ############################################################
    ##STDOUT HANDLERS
    ############################################################
    def HandleStdoutError( self ):
        if self.deadlinePlugin.GetBooleanConfigEntryWithDefault( "StrictErrorChecking", True ):
            error = self.GetRegexMatch(0)
            
            if error.find( "ERROR : 21000-REND-RenderPasses - Unspecified failure" ) >= 0:
                # Don't fail on this error. Otherwise, Softimage won't have a chance to print out the true error message.
                self.deadlinePlugin.LogWarning( "An error occurred in the batch script while rendering." )
            elif error.find( " ERROR : 21000 - Unspecified failure " ) >= 0:
                # Don't fail on this error. Otherwise, Softimage won't have a chance to print out the true error message.
                self.deadlinePlugin.LogWarning( "An error occurred in the batch script." )
            else:
                ignore = False
                if error.find( "ERROR : 2262" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : 2360" ) >= 0: # This plug-in is not compatible with the current platform and will be ignored
                    ignore = True
                elif error.find( "ERROR : 2356 - This plug-in is not installed" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : 2424 - XSI failed to load a .NET plug-in" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : 2000 - Unable to create object" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : Please select an object first" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : Invalid procedure call or argument" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : 2087 - The object" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : 21000-SELE-AddToSelection - Unspecified failure" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : 2000 - Argument 0 (Target) is invalid" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : 2004 - Invalid pointer - [line 2]" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : Invalid device id" ) >= 0:
                    ignore = True
                elif error.find( "ERROR : 2000 - The cachefile" ) >= 0:
                    ignore = True
                
                if not ignore:
                    self.deadlinePlugin.FailRender( error )
                else:
                    self.deadlinePlugin.LogInfo( "Ignoring error" )
        else:
            self.deadlinePlugin.LogInfo( "Ignoring error because Strict Error Checking is disabled in the plugin configuration." )
    
    def HandleStdoutFrameDone( self ):
        self.GotProgress = True
        self.deadlinePlugin.SetProgress( self.GetRegexMatch( 2 ) )
        self.deadlinePlugin.SetStatusMessage( self.GetRegexMatch( 1 ) )
        
    def HandleStdoutInfoDone( self ):
        self.GotProgress = True
        self.deadlinePlugin.SetProgress( 100 )
        self.deadlinePlugin.SetStatusMessage( "Finished Rendering " + str((self.deadlinePlugin.GetStartFrame() + self.deadlinePlugin.GetEndFrame() + 1) * self.deadlinePlugin.PassesComplete) + " frames" )
        
    def HandleStdoutInfoError( self ):
        self.FailRender( self.GetRegexMatch( 0 ) )
        
    def HandleStdoutProgress1( self ):
        self.GotProgress = True
        start = self.deadlinePlugin.GetStartFrame()
        end = self.deadlinePlugin.GetEndFrame()
        
        if (end - start) != -1:
            progress = ((((float(self.GetRegexMatch(1))/100 + self.deadlinePlugin.Framecount)*100)/(end-start+1))/self.deadlinePlugin.NumPasses) + (100/self.deadlinePlugin.NumPasses*self.deadlinePlugin.PassesComplete)
            self.deadlinePlugin.SetProgress( progress )
            self.deadlinePlugin.SetStatusMessage( "Rendering %s%%" % progress )
            #self.SuppressThisLine()
    
    def HandleStdoutProgress2( self ):
        self.GotProgress = True
        self.deadlinePlugin.Framecount += 1
        start = self.deadlinePlugin.GetStartFrame()
        end = self.deadlinePlugin.GetEndFrame()
        
        if (end - start) != -1:
            self.deadlinePlugin.SetProgress( (((float(self.deadlinePlugin.Framecount) /(end-start+1))*100)/self.deadlinePlugin.NumPasses) + (100/self.deadlinePlugin.NumPasses*self.deadlinePlugin.PassesComplete) )
            if self.CurrentPass == "":
                self.deadlinePlugin.SetStatusMessage( "Rendering Frame " + str(self.deadlinePlugin.GetStartFrame() + self.deadlinePlugin.Framecount) )
            else:
                self.deadlinePlugin.SetStatusMessage( "Rendering Frame " + str(self.deadlinePlugin.GetStartFrame() + self.deadlinePlugin.Framecount) + " of " + self.CurrentPass )
        
    def HandleStdoutComplete( self ):
        self.GotProgress = True
        self.deadlinePlugin.PassesComplete += 1
        
        self.deadlinePlugin.SetProgress( 100 / self.deadlinePlugin.NumPasses * self.deadlinePlugin.PassesComplete )
        self.deadlinePlugin.SetStatusMessage( "Finished Rendering " + str((self.deadlinePlugin.GetEndFrame() - self.deadlinePlugin.GetStartFrame() + 1) * self.deadlinePlugin.PassesComplete) + " frames" )
        
    def HandleStdoutFxTreeProgress( self ):
        self.deadlinePlugin.Framecount += 1
        self.GotProgress = True
        self.deadlinePlugin.SetProgress( (float(self.deadlinePlugin.Framecount)*100)/(self.deadlinePlugin.GetEndFrame()-self.deadlinePlugin.GetStartFrame()+1) )
        self.deadlinePlugin.SetStatusMessage( "Rendering Frame " + str(self.deadlinePlugin.Framecount) + " (FxTree Render)" )
        
    def HandleStdoutFxTreeDone( self ):
        self.deadlinePlugin.SetProgress( 100 )
        self.GotProgress = True
        self.deadlinePlugin.SetStatusMessage( "Finished rendering " + str((self.deadlinePlugin.GetEndFrame() - self.deadlinePlugin.GetStartFrame() + 1)) + " frames (FxTree Render)" )
        
    def HandleStdoutNewPass( self ):
        self.GotProgress = True
        self.deadlinePlugin.Framecount = 0
        self.CurrentPass = self.GetRegexMatch( 1 )
        
    def HandleStdoutScriptError( self ):
        self.deadlinePlugin.FailRender( self.GetRegexMatch( 0 ) + "\nScript File:" + self.StartupScript )
