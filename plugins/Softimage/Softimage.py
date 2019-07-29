import re

from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return SoftimagePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class SoftimagePlugin (DeadlinePlugin):
    Framecount = 0
    
    LocalRendering = False
    NetworkFilePath = ""
    LocalFilePath = ""
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
        self.CheckExitCodeCallback += self.CheckExitCode
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
        del self.CheckExitCodeCallback
    
    #alled by deadline to initialize the process
    def InitializeProcess(self):
        
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple
        
        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.Normal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        
        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( ".*ERROR :.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback("(Rendering frame: [0-9]+) \\(([0-9]+) % done\\)").HandleCallback += self.HandleStdoutFrameDone
        self.AddStdoutHandlerCallback("(Rendering frame: [0-9]+) \\(([0-9]+\\.[0-9]+) % done\\)").HandleCallback += self.HandleStdoutFrameDone
        self.AddStdoutHandlerCallback("'INFO : Rendering done!").HandleCallback += self.HandleStdoutInfoDone
        self.AddStdoutHandlerCallback("'INFO : Couldn't find the pass name .*").HandleCallback += self.HandleStdoutInfoError
        self.AddStdoutHandlerCallback(".*progr:\\s+([0-9]{1,3}.[0-9]+)%\\s+rendered\\son.*").HandleCallback += self.HandleStdoutProgress1
        self.AddStdoutHandlerCallback(".*progr:\\s+rendering\\sfinished.*").HandleCallback += self.HandleStdoutProgress2
        self.AddStdoutHandlerCallback(".*Render completed \\(100% done\\).*").HandleCallback += self.HandleStdoutComplete
        self.AddStdoutHandlerCallback(".*INFO : 4000 - Comp.*").HandleCallback += self.HandleStdoutFxTreeProgress
        self.AddStdoutHandlerCallback(".*INFO : 4000 - Done.*").HandleCallback += self.HandleStdoutFxTreeDone
        
        self.AddStdoutHandlerCallback(".*\\[arnold\\].* +([0-9]+)% done.*").HandleCallback += self.HandleStdoutProgress1
        self.AddStdoutHandlerCallback(".*\\[arnold\\].* render done.*").HandleCallback += self.HandleStdoutProgress2
        
    def PreRenderTasks(self):
        self.Framecount = 0
        
        workgroup = self.GetPluginInfoEntryWithDefault( "Workgroup", "" ).strip()
        workgroup = RepositoryUtils.CheckPathMapping( workgroup )
        
        if len( workgroup ) > 0:
            self.LogInfo( "Switching workgroup before rendering to " + workgroup )
            
            executable = self.RenderExecutable()
            arguments = " -processing -w \"" + workgroup + "\""
            startupDir = Path.GetDirectoryName( executable )
            
            self.RunProcess( executable, arguments, startupDir, -1 )
    
    def RenderExecutable(self):
        softimageExe = ""
        
        version = self.GetPluginInfoEntry( "Version" )
        periodIndex = version.find( "." )
        if periodIndex > 0:
            version = version[0:periodIndex]
        
        self.LogInfo( "Rendering with Softimage version " + version )
        
        softimageExeList = self.GetConfigEntry( "RenderExecutable" + version )
        if SystemUtils.IsRunningOnWindows():
            softimageExeList = softimageExeList.lower()
        
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
       
        if SystemUtils.IsRunningOnWindows():
            if build == "32bit":
                tempSoftimageExeList = self.ReplaceSoftimageBatchPath( softimageExeList )
                self.LogInfo( "Enforcing 32 bit build of Softimage" )
                softimageExe = FileUtils.SearchFileListFor32Bit( tempSoftimageExeList )
                if( softimageExe == "" ):
                    self.LogWarning("32 bit Softimage " + version + " render executable was not found in the semicolon separated list \"" + softimageExeList + "\". Checking for any executable that exists instead.")
                softimageExe = self.RevertSoftimageBatchPath( softimageExe )
                
            elif build == "64bit":
                tempSoftimageExeList = self.ReplaceSoftimageBatchPath( softimageExeList )
                self.LogInfo( "Enforcing 64 bit build of Softimage" )
                softimageExe = FileUtils.SearchFileListFor64Bit( tempSoftimageExeList )
                if( softimageExe == "" ):
                    self.LogWarning( "64 bit Softimage " + version + " render executable was not found in the semicolon separated list \"" + softimageExeList + "\". Checking for any executable that exists instead.")
                softimageExe = self.RevertSoftimageBatchPath( softimageExe )
            
        if( softimageExe == "" ):
            self.LogInfo( "Not enforcing a build of Softimage" )
            softimageExe = FileUtils.SearchFileList( softimageExeList )
            if( softimageExe == "" ):
                self.FailRender("Softimage " + version + " render executable was not found in the semicolon separated list \"" + softimageExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor.")
        
        return softimageExe
    
    def RenderArgument(self):
        if (self.GetBooleanPluginInfoEntryWithDefault("ScriptJob", False)):
            return self.ScriptJobRenderArguments()
        else:
            return self.RegularJobRenderArguments()
    
    def ScriptJobRenderArguments(self):
        arguments=""
        
        arguments+="-script \"" + self.GetDataFilename() + "\""
        arguments+=StringUtils.BlankIfEitherIsBlank(" -lang ", self.GetPluginInfoEntryWithDefault("ScriptLang","").strip())
        arguments+=StringUtils.BlankIfEitherIsBlank(" -main ", self.GetPluginInfoEntryWithDefault("ScriptMain","").strip())
        arguments+=StringUtils.BlankIfEitherIsBlank(" -args ", self.GetPluginInfoEntryWithDefault("ScriptArgs","").strip())
    
        return arguments
    
    def RegularJobRenderArguments(self):
        renderarguments = ""
        
         # The processing flag can be used when rendering with non-mentalray renders to skip Softimage's batch license check.
        if self.GetBooleanPluginInfoEntryWithDefault( "SkipBatchLicense", False ):
            renderarguments += " -processing"
        
        version = self.GetPluginInfoEntry("Version") 
        periodIndex = version.find(".")
        if( periodIndex > 0 ):
            version = version[0:periodIndex]
                
        #Softimage Seems to resolve windows UNC paths,ie. Windows to Linux but not vice versa
        sceneFile = self.GetPluginInfoEntryWithDefault("SceneFile",self.GetDataFilename())
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        if(SystemUtils.IsRunningOnWindows()):
            sceneFile=sceneFile.replace("/","\\")
            if(sceneFile.startswith("\\") and not sceneFile.startswith("\\\\")):
                sceneFile = "\\" + sceneFile
        
        isFxTreeRender = self.GetBooleanPluginInfoEntryWithDefault( "FxTreeRender", False )
        
        if(isFxTreeRender):
            self.LogInfo( "Rendering an FxTree job" )
            
            scriptarguments = ""
            scriptarguments += " -sceneFilename \"" + sceneFile + "\""
            scriptarguments += " -fxTreeOutputNode \"" + self.GetPluginInfoEntry( "FxTreeOutputNode" ) + "\""
            scriptarguments += " -startFrame " + str(self.GetStartFrame()) + " -endFrame " + str(self.GetEndFrame()) + " -stepFrame 1" 
            scriptarguments += " -frameOffset " + self.GetPluginInfoEntryWithDefault( "FxTreeFrameOffset", "0" )
            
            outputFile = self.GetPluginInfoEntryWithDefault( "FxTreeOutputFile", "" )
            outputFile = RepositoryUtils.CheckPathMapping( outputFile )
            scriptarguments += " -outputFilename \"" + outputFile + "\""
            
            renderarguments += " -script \"" +Path.Combine(self.GetPluginDirectory(),"RenderFxOp.vbs") + "\""
            renderarguments += " -main RenderFxOpMain -args " + scriptarguments
        else:
            renderPass = self.GetPluginInfoEntryWithDefault( "Pass", "" )
            
            regionRendering = self.GetBooleanPluginInfoEntryWithDefault( "RegionRendering", False )
            singleRegionJob = self.IsTileJob()
            singleRegionFrame = str(self.GetStartFrame())
            singleRegionIndex = self.GetCurrentTaskId()
            
            fileprefix = ""
            if singleRegionJob:
                fileprefix = self.GetPluginInfoEntryWithDefault( "RegionPrefix" + singleRegionIndex, "" ).strip()
            else:
                fileprefix = self.GetPluginInfoEntryWithDefault( "TilePrefix", "" ).strip()
            fileprefix = fileprefix.replace("TILE","tile")

            gpus = ""
            gpusPerTask = self.GetIntegerPluginInfoEntryWithDefault( "RedshiftGPUsPerTask", -1 )
            
            # gpusPerTask will be 0 or greater if RedShift is the chosen renderer.
            if gpusPerTask != -1:
                gpusSelectDevices = self.GetPluginInfoEntryWithDefault( "RedshiftGPUsSelectDevices", "" )
                
                if gpusPerTask == 0 and gpusSelectDevices != "":
                    gpuList = gpusSelectDevices.split(",")
                    gpus = ",".join(gpuList)
                    self.LogInfo( "Specific GPUs specified, so the following GPUs will be used by RedShift: " + gpus )

                elif gpusPerTask > 0:
                    gpuList = []
                    for i in range((self.GetThreadNumber() * gpusPerTask), (self.GetThreadNumber() * gpusPerTask) + gpusPerTask):
                        gpuList.append(str(i))
                    
                    gpus = ",".join(gpuList)
                    self.LogInfo( "GPUs per task is greater than 0, so the following GPUs will be used by RedShift: " + gpus )
                    
                elif self.OverrideGpuAffinity():
                    gpuList = []
                    for gpuId in self.GpuAffinity():
                        gpuList.append( str( gpuId ) )
                    
                    gpus = ",".join(gpuList)
                    self.LogInfo( "This Slave is overriding its GPU affinity, so the following GPUs will be used by RedShift: " + gpus )

            scriptarguments = ""
            scriptarguments += " -script \"" + Path.Combine(self.GetPluginDirectory(),"AdditionalRenderOptions.vbs") +"\""
            scriptarguments += " -main SetAdditionalRenderOptions -args"
            scriptarguments += " -passName \"" + renderPass + "\""
            scriptarguments += " -width \"" + self.GetPluginInfoEntryWithDefault( "Width", "" ) + "\""
            scriptarguments += " -height \"" + self.GetPluginInfoEntryWithDefault( "Height", "" ) + "\""
            scriptarguments += " -sampleMin \"" + self.GetPluginInfoEntryWithDefault( "SampleMin", "" ) + "\""
            scriptarguments += " -sampleMax \"" + self.GetPluginInfoEntryWithDefault( "SampleMax", "" ) + "\""
            scriptarguments += " -sampleFilter \"" + self.GetPluginInfoEntryWithDefault( "Filter", "" ) + "\""
            scriptarguments += " -sampleJitter \"" + self.GetPluginInfoEntryWithDefault( "SampleJitter", "" ) + "\""
            scriptarguments += " -outputPrefix \"" + fileprefix + "\""
            
            if regionRendering:
                if singleRegionJob:
                    scriptarguments += " -xMin \"" + self.GetPluginInfoEntryWithDefault( "RegionLeft" + singleRegionIndex, "0" ) + "\""
                    scriptarguments += " -yMin \"" + self.GetPluginInfoEntryWithDefault( "RegionTop" + singleRegionIndex, "0" ) + "\""
                    scriptarguments += " -xMax \"" + self.GetPluginInfoEntryWithDefault( "RegionRight" + singleRegionIndex, "0" ) + "\""
                    scriptarguments += " -yMax \"" + self.GetPluginInfoEntryWithDefault( "RegionBottom" + singleRegionIndex, "0" ) + "\""
                else:
                    scriptarguments += " -xMin \"" + self.GetPluginInfoEntryWithDefault( "RegionLeft", "0" ) + "\""
                    scriptarguments += " -yMin \"" + self.GetPluginInfoEntryWithDefault( "RegionTop", "0" ) + "\""
                    scriptarguments += " -xMax \"" + self.GetPluginInfoEntryWithDefault( "RegionRight", "0" ) + "\""
                    scriptarguments += " -yMax \"" + self.GetPluginInfoEntryWithDefault( "RegionBottom", "0" ) + "\""
            else:
                scriptarguments += " -xMin \"\""
                scriptarguments += " -yMin \"\""
                scriptarguments += " -xMax \"\""
                scriptarguments += " -yMax \"\""
            
            scriptarguments += " -gpus \"" + gpus + "\""
            
            threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
            if threads > 0:
                renderarguments += "-thread " + str(threads)
            
            renderarguments += " -render \"" + sceneFile + "\""
            
            if regionRendering and singleRegionJob:
                renderarguments += " -frames " + singleRegionFrame + "," + singleRegionFrame + ",1"
            else:
                renderarguments += " -frames " + str(self.GetStartFrame()) + "," + str(self.GetEndFrame()) + ",1"
            
            renderarguments += StringUtils.BlankIfEitherIsBlank( StringUtils.BlankIfEitherIsBlank( " -pass \"", renderPass ), "\"" )
            
            filepath = self.GetPluginInfoEntryWithDefault( "FilePath", "" ).strip()
            filepath = RepositoryUtils.CheckPathMapping( filepath )
            if( len( filepath ) > 0 ):
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
            
            renderarguments += StringUtils.BlankIfEitherIsBlank( StringUtils.BlankIfEitherIsBlank( " -output_dir \"", filepath ), "\"" )
            renderarguments += StringUtils.BlankIfEitherIsBlank( " -skip ", self.GetPluginInfoEntryWithDefault( "SkipFrames", "" ) )
            renderarguments += StringUtils.BlankIfEitherIsBlank( " -mb ", self.GetPluginInfoEntryWithDefault( "MotionBlur", "" ) )
            renderarguments += " -verbose on"
            
            if(self.GetPluginInfoEntryWithDefault("Pass","") != ""):
                renderarguments += scriptarguments
        
        return renderarguments
    
    def CheckExitCode(self, returnCode):
        # If the error code is not 0, check if we should ignore it.
        if( returnCode != 0 ):
            returnCodesToIgnore = self.GetConfigEntry( "ReturnCodesToIgnore" )
            ignoreCode = False
            
            # Loop through the semicolon separated list of error codes to ignore.
            returnCodeList = StringUtils.FromSemicolonSeparatedString( returnCodesToIgnore )
            for code in returnCodeList:
                if code == str(returnCode):
                    ignoreCode = True
                    break
                
            # If the error code was not found in the ignore list, fail the render.
            if not ignoreCode:
                self.FailRender( "Renderer returned non-zero error code, " + str(returnCode) + ". If this error code is not fatal to your render, you can add it to the list of error codes to ignore in the Softimage Plugin Configuration.")
            else:
                self.LogInfo( "Renderer returned non-zero error code, " + str(returnCode) + ", which will be ignored because it is part of the list of error codes to ignore in the Softimage Plugin Configuration." )
            
    
    def PostRenderTasks(self):
        if( self.LocalRendering ):
            self.LogInfo( "Moving output files and folders from " + self.LocalFilePath + " to " + self.NetworkFilePath )
            self.VerifyAndMoveDirectory( self.LocalFilePath, self.NetworkFilePath, False, -1 )
    
    def ProcessOutputPath( self, outputPath ):
        if SystemUtils.IsRunningOnLinux():
            outputPath = outputPath.replace( "\\","/" )
        else:
            outputPath = outputPath.replace( "/", "\\" )
        
        lastChar = outputPath[ len( outputPath ) - 1 : len( outputPath ) ]
        if( lastChar == "\\" or lastChar == "/" ):
            outputPath = outputPath[ 0 : len( outputPath ) - 1 ]
        
        return outputPath
    
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
    
    def HandleStdoutError(self):
        if self.GetBooleanConfigEntryWithDefault( "StrictErrorChecking", True ):
            error = self.GetRegexMatch(0)
            
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
            elif error.find( "This command can't be used in batch mode" ) >= 0:
                ignore = True
            
            if not ignore:
                self.FailRender( error )
            else:
                self.LogInfo( "Ignoring error" )
        else:
            self.LogInfo( "Ignoring error because Strict Error Checking is disabled in the plugin configuration." )
    
    def HandleStdoutFrameDone(self):
        self.SetProgress(self.GetRegexMatch(2))
        self.SetStatusMessage(self.GetRegexMatch(1))
        
    def HandleStdoutInfoDone(self):
        self.SetProgress(100)
        self.SetStuatsMessage("Finished Rendering " + str((self.GetStartFrame()+self.GetEndFrame()+1)) + " frames")
        
    def HandleStdoutInfoError(self):
        self.FailRender(self.GetRegexMatch(0))
        
    def HandleStdoutProgress1(self):
        start=self.GetStartFrame()
        end=self.GetEndFrame()
        
        if((end-start)!=-1):
            progress = ((float(self.GetRegexMatch(1))/100 + self.Framecount)*100)/(end-start+1)
            self.SetProgress(progress)
            self.SetStatusMessage( "Rendering %s%%" % progress )
            #self.SuppressThisLine()
            
    def HandleStdoutProgress2(self):
        self.Framecount+=1
        start=self.GetStartFrame()
        end=self.GetEndFrame()
        
        if(end-start!=-1):
            self.SetProgress((float(self.Framecount) /(end-start+1))*100)
            self.SetStatusMessage("Rendering Frame " + str(self.GetStartFrame() + self.Framecount))
        
    def HandleStdoutComplete(self):
        self.SetProgress(100)
        self.SetStatusMessage("Finished rendering " + str((self.GetEndFrame() - self.GetStartFrame() + 1)) + " frames")
    
    def HandleStdoutFxTreeProgress(self):
        self.Framecount+=1
    
        self.SetProgress((float(self.Framecount)*100)/(self.GetEndFrame()-self.GetStartFrame()+1))
        self.SetStatusMessage("Rendering Frame " + str(self.Framecount) + " (FxTree Render")
        
    def HandleStdoutFxTreeDone(self):
        self.SetProgress(100)
        self.SetStatusMessage("Finished rendering " + str((self.GetEndFrame() - self.GetStartFrame() + 1)) + " frames (FxTree Render)")
