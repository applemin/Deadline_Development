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
    return MentalRayPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class MentalRayPlugin(DeadlinePlugin):
    Framecount=0
    outputPath=""
    
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
    
    def InitializeProcess(self):
        self.SingleFramesOnly=False
        self.StdoutHandling=True
        
        self.AddStdoutHandlerCallback("'ERROR :.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback("\s*\S+\s+\S+\s+progr:\s+([\\d\\.]+)%.*").HandleCallback += self.HandleStdoutProgress
        self.AddStdoutHandlerCallback("\S+\s+\S+\s+error\s+([0-9]+)(.*)").HandleCallback += self.HandleStdoutParseError
        #self.AddStdoutHandlerCallback("\s*[e,E]+rror[:]*(.*)").HandleCallback += self.HandleStdoutError2
        self.AddStdoutHandlerCallback(".*Can't connect to any SPM license server.*").HandleCallback += self.HandleStdoutSPMError
        
    def PreRenderTasks(self):
        self.LogInfo("Starting Mental Ray Render")
        
    def RenderExecutable(self):
        mrExe = ""
        
        mrExeList = self.GetConfigEntry( "MentalRay_RenderExecutable" )
        if SystemUtils.IsRunningOnWindows():
            mrExeList = mrExeList.lower()
        
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        if(SystemUtils.IsRunningOnWindows()):
            if build == "32bit":
                self.LogInfo( "Enforcing 32 bit build of Mental Ray" )
                for mrExePath in mrExeList.split( ";" ):
                    tempMrExePath = self.ReplaceRayPath( mrExePath )
                    currMrExe = FileUtils.SearchFileListFor32Bit( tempMrExePath )
                    if( currMrExe != "" ):
                        if( tempMrExePath != mrExePath ):
                            currMrExe = self.RevertRayPath( currMrExe )
                        mrExe = currMrExe
                        break
                
                if( mrExe == "" ):
                    self.LogWarning( "32 bit Mental Ray render executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % mrExeList )

            elif build == "64bit":
                self.LogInfo( "Enforcing 64 bit build of Mental Ray" )
                for mrExePath in mrExeList.split( ";" ):
                    tempMrExePath = self.ReplaceRayPath( mrExePath )
                    currMrExe = FileUtils.SearchFileListFor64Bit( tempMrExePath )
                    if( currMrExe != "" ):
                        if( tempMrExePath != mrExePath ):
                            currMrExe = self.RevertRayPath( currMrExe )
                        mrExe = currMrExe
                        break
                
                if( mrExe == "" ):
                    self.LogWarning( "64 bit Mental Ray render executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % mrExeList )
                
        if( mrExe == "" ):
            mrExe = FileUtils.SearchFileList( mrExeList )
            if( mrExe == "" ):
                self.FailRender( "Mental Ray render executable could not be found in the semicolon separated list \"%s\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." % mrExeList )
        
        return mrExe
    
    def ReplaceRayPath( self, path ):
        if SystemUtils.IsRunningOnWindows():
            path = path.replace( "ray.bat", "ray.exe" )
        return path
    
    def RevertRayPath( self, path ):
        if SystemUtils.IsRunningOnWindows():
            path = path.replace( "ray.exe", "ray.bat" )
        return path
    
    def RenderArgument(self):
        global outputPath
        #Determine if we are saving directly to final location, or saving locally first.
        if( self.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False ) ):
            self.LogInfo( "Rendering to local drive, will copy files and folders to \"" + self.GetPluginInfoEntry( "OutputPath" ) + "\" after render is complete" )
            outputPath = self.CreateTempDirectory("MentalRay")
        else:
            self.LogInfo( "Rendering to network drive..." )
            outputPath = self.GetPluginInfoEntry( "OutputPath" )
            outputPath = RepositoryUtils.CheckPathMapping( outputPath )
            if outputPath.startswith( "\\" ) and not outputPath.startswith( "\\\\" ):
                outputPath = "\\" + outputPath
            if outputPath.startswith( "/" ) and not outputPath.startswith( "//" ):
                outputPath = "/" + outputPath
        
        #If the output path ends with a slash mental ray will hang so make sure we strip those off
        outputPath = outputPath.rstrip("/\\")
        # Verbose level of 5 is used to get the progress of the render.
        arguments = " -verbose " + self.GetPluginInfoEntryWithDefault( "Verbose", "5" ) 
        arguments += " -file_dir \"" + outputPath + "\" " + self.GetPluginInfoEntryWithDefault( "CommandLineOptions", "" )
        
        # If threads specified is 0, then just use the default number of threads.
        threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if( threads > 0 ):
            arguments = arguments + " -threads " + str(threads)
        
        # Determine if there are separate mi files per frame.
        separateFilesPerFrame = self.GetBooleanPluginInfoEntryWithDefault( "SeparateFilesPerFrame", False )
        if(not separateFilesPerFrame):
            # Figure out the frame offset, because regardless of the range in the mi file, the
            # mental ray command line renderer expects frames between 1 and N inclusive, where
            # N represents the number of frames in the mi file.
            startFrameOffset = self.GetIntegerPluginInfoEntryWithDefault( "StartFrameOffset", 1 )
            startFrame = self.GetStartFrame() - startFrameOffset + 1
            endFrame = self.GetEndFrame() - startFrameOffset + 1
            
            filename = self.GetPluginInfoEntry("InputFile")
            filename = RepositoryUtils.CheckPathMapping( filename )
            
            #windows handles both slashes as long as we don't mix and match the first two
            if(SystemUtils.IsRunningOnWindows()):
                #Check if it is a unc path
                if(filename.startswith("\\")):
                    if(filename[0:2] != "\\\\"):
                        filename = "\\" + filename
                elif(filename.startswith("/")):
                    if(filename[0:2] != "//"):
                        filename = "/" + filename
            else:
                filename = filename.replace("\\","/")
                if(filename[0:2] == "//"):
                    filename = filename[1:-1]
            
            arguments = arguments + " -render " + str(startFrame) + " " + str(endFrame) + " \"" + filename + "\""
        else:
            filename = self.GetPluginInfoEntry("InputFile")
            filename = RepositoryUtils.CheckPathMapping( filename )
            
            currPadding = FrameUtils.GetFrameStringFromFilename(filename)
            paddingSize = len(currPadding)
            newPadding = StringUtils.ToZeroPaddedString(self.GetStartFrame(),paddingSize,False)
            filename = FrameUtils.SubstituteFrameNumber( filename, newPadding )
            
            #windows handles both slashes as long as we don't mix and match the first two
            if(SystemUtils.IsRunningOnWindows()):
                #Check if it is a unc path
                if(filename.startswith("\\")):
                    if(filename[0:2] != "\\\\"):
                        filename = "\\" + filename
                elif(filename.startswith("/")):
                    if(filename[0:2] != "//"):
                        filename = "/" + filename
            else:
                filename = filename.replace("\\","/")
                if(filename[0:2] == "//"):
                    filename = filename[1:-1]
                
            arguments = arguments + " \"" + filename + "\""
        
        return arguments;
        
    def PostRenderTasks(self):
        global outputPath
        
        if( self.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False ) ):
            if(SystemUtils.IsRunningOnWindows()):
                networkOutputPath = self.GetPluginInfoEntry( "OutputPath" )
                networkOutputPath = RepositoryUtils.CheckPathMapping( networkOutputPath ).replace("/","\\")
                if(networkOutputPath.startswith("\\") and networkOutputPath[0:2] != "\\\\"):
                    networkOutputPath = "\\"  + networkOutputPath
            else:
                networkOutputPath = self.GetPluginInfoEntry( "OutputPath" )
                networkOutputPath = RepositoryUtils.CheckPathMapping( networkOutputPath ).replace("\\\\","/")
                networkOutputPath = networkOutputPath.replace("\\","/")
            
            self.LogInfo( "Moving output files and folders from " + outputPath + " to " + networkOutputPath )  
            self.VerifyAndMoveDirectory( outputPath, networkOutputPath, False, -1 )
        
        self.LogInfo( "Mental Ray task finished." )
        
    def HandleStdoutError(self):
        self.FailRender(self.GetRegexMatch(0))
        
    def HandleStdoutProgress(self):
        self.SetProgress( float(self.GetRegexMatch(1)) )
        #self.SuppressThisLine()
            
    def HandleStdoutParseError(self):
        # Check the mental ray error code to see if we should ignore this error.
        errorCode = int(self.GetRegexMatch(1))
        errorCodesToIgnore = StringUtils.FromSemicolonSeparatedString(self.GetConfigEntry( "ErrorCodesToIgnore" ))
        ignoreCode = False
        
        # Loop through the semicolon separated list of error codes to ignore.
        self.LogInfo( "An error occurred, checking error codes to ignore" )
        for currCode in errorCodesToIgnore:
            try:
                # Check if the current code matches the actual error code, and break if it does.
                if( int(currCode) == errorCode ):
                    ignoreCode = True
                    break
            except:
                self.LogWarning( "Error code to ignore, '" + currCode + "', is not a valid number, and will be skipped" )

        # If the error code was not found in the ignore list, fail the render.
        if( not ignoreCode ):
            self.FailRender( "Renderer reported an error with error code " + str(errorCode) + self.GetRegexMatch(2) + "\nIf this error code is not fatal to your render, you can add it to the list of error codes to ignore in the Mental Ray Plugin Configuration." )
        else:
            self.LogInfo( "Renderer reported an error with error code " + str(errorCode) + self.GetRegexMatch(2) + "\nThis will be ignored because it is part of the list of error codes to ignore in the Mental Ray Plugin Configuration." )
            
    #def HandleStdoutError2(self):
    #	self.FailRender(self.GetRegexMatch(1))

    def HandleStdoutSPMError(self):
        self.FailRender("Mental ray could not find any spm server, make sure the the spm server is running and set up correctly.")
        
    # Mental Ray 3.10 now returns 1 on success, so just ignore exit codes 0 and 1.
    def CheckExitCode( self, exitCode ):
        if exitCode != 0 and (exitCode != 1 or StringUtils.ParseBooleanWithDefault(self.GetConfigEntry("ExitCode1", False))):
            if exitCode == 1:
                self.LogInfo( "Renderer returned exit code 1, but Treat Exit Code 1 as Error is disabled in the Mental Ray Plugin Configuration." )
            else:
                self.FailRender( "Renderer returned exit code %d, which indicates there was an error. Check the render log for more info." % exitCode )
