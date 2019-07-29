import os
import tempfile
import traceback

from Deadline.Plugins import DeadlinePlugin, PluginType
from Deadline.Scripting import FileUtils, FrameUtils, PathUtils, ProcessUtils, RepositoryUtils, SystemUtils
from System import Environment
from System.Diagnostics import Process, ProcessPriorityClass


######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return AfterEffectsPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the After Effects plugin.
######################################################################
class AfterEffectsPlugin( DeadlinePlugin ):
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
        self.RenderCanceledCallback += self.RenderCanceled
        self.CheckExitCodeCallback += self.CheckExitCode

    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
        del self.RenderCanceledCallback
        del self.CheckExitCodeCallback
        
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple
        version = self.GetFloatPluginInfoEntry( "Version" )
        
        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        self.SetEnvironmentVariable( "KMP_DUPLICATE_LIB_OK", "TRUE" )
        
        # Initialize start and end frame
        self.FramesStartTime = 0
        self.FramesEndTime = 0

        self.Framecount = 0
        self.DelayedFailure = False
        self.FailureMessage = ""
        self.HandleProgress = True

        self.FailWithoutFinishedMessage = False
        self.FailOnExistingAEProcess = False
        self.RenderSuccess = False

        self.LocalRendering = False
        self.NetworkFilePath = ""
        self.LocalFilePath = ""

        self.MultiMachine = False
        self.MultiMachineStartFrame = -1
        self.MultiMachineEndFrame = -1

        self.TempSceneFilename = ""

        self.PrintCudaWarningOnce = False

        # The Optical Flares License popup uses a wxWindowClassNR control for the "OK" button, so we need to check for that class too.
        self.PopupButtonClasses = ( "Button", "wxWindowClassNR", "TButton" )
        
        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( "aerender version (.*)" ).HandleCallback += self.HandleRenderVersion

        self.AddStdoutHandlerCallback( ".*GL_VERS: 32Prog Error: 1280.*|.*Create Buffer Error: 1280.*" ).HandleCallback += self.HandleNonFatalError
        self.AddStdoutHandlerCallback( ".*error: internal verification failure, sorry.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "INFO:This project contains .*" ).HandleCallback += self.HandleStdoutInfo
        self.AddStdoutHandlerCallback( "This project contains a reference to a missing effect.*" ).HandleCallback += self.HandleStdoutInfo
        self.AddStdoutHandlerCallback( ".*Unable to obtain a license.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "unexpected failure during application startup" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "Invalid Serial Number" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( ".*Error:.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "aerender ERROR.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( ".*AEsend failed to send apple event.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( ".*There is an error in background rendering so switching to foreground rendering.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "INFO:(The following layer dependencies are missing)" ).HandleCallback += self.HandleMissingLayerDependencies
        self.AddStdoutHandlerCallback( "a layer has missing dependencies.*" ).HandleCallback += self.HandleMissingLayerDependencies
        self.AddStdoutHandlerCallback( ".*Finished composition.*" ).HandleCallback += self.HandleRenderSuccess #English
        self.AddStdoutHandlerCallback( ".*fin de la composition.*" ).HandleCallback += self.HandleRenderSuccess #French
        self.AddStdoutHandlerCallback( ".*Komposition.*beendet.*" ).HandleCallback += self.HandleRenderSuccess #German
        self.AddStdoutHandlerCallback( ".*After Effects successfully launched.*" ).HandleCallback += self.HandleRenderSuccess #To handle cases where 'Finished composition' never appears.
        self.AddStdoutHandlerCallback( "WARNING:(After Effects [Ww]arn[ui]ng: .*)" ).HandleCallback += self.HandleStdoutWarning #English/#German
        self.AddStdoutHandlerCallback( ".*NVAPI error.*" ).HandleCallback += self.HandleCudaError
        
        #This code is left undeleted because the new progress update is untested in versions prior to 13, so the code remains to ensure old versions don't change behaviour unexpectedly.
        if version >= 13:
            # These stdout handlers watch for timecode-based progress.
            self.AddStdoutHandlerCallback( "PROGRESS:\s+ Start: (\d+[:;]\d+[:;]\d+[:;]\d+).*" ).HandleCallback += self.HandleProgressTimecodeStart
            self.AddStdoutHandlerCallback( "PROGRESS:\s+ End: (\d+[:;]\d+[:;]\d+[:;]\d+).*" ).HandleCallback += self.HandleProgressTimecodeEnd
            self.AddStdoutHandlerCallback( "PROGRESS:.*(\d+[:;]\d+[:;]\d+[:;]\d+).*" ).HandleCallback += self.HandleStdoutTimecodeProgress
            
            # These stdout handlers watch for frame-based progress.
            self.AddStdoutHandlerCallback( "PROGRESS:\s+ Start: (\d+)[^:;]*" ).HandleCallback += self.HandleProgressFrameStart
            self.AddStdoutHandlerCallback( "PROGRESS:\s+ End: (\d+)[^:;]*" ).HandleCallback += self.HandleProgressFrameEnd
            self.AddStdoutHandlerCallback( "PROGRESS:\s+ (\d+)[^:;]*" ).HandleCallback += self.HandleStdoutFrameProgress
        else:
            self.AddStdoutHandlerCallback( "PROGRESS:\\s+([0-9]+[:;]*[0-9]*[:;]*[0-9]*[:;]*[0-9]*).*" ).HandleCallback += self.HandleStdoutProgressLegacy

        # Trapcode licensing issues.
        self.AddStdoutHandlerCallback( ".*is using the same serial number.*" ).HandleCallback += self.HandleStdoutError
        
        # Format issue handling
        if version < 15:
            # Certain old versions of After Effects would output this message when they encountered
            # a bug that caused them to forget what format they were supposed to output
            # to and just output single frame AVI files.
            # Around version 15, it started outputting this message for other--non-error--reasons.
            # We don't know exactly which version this happened since we can't install versions older than 15 anymore.
            # We at least know that in version 15 and later we don't want to fail the render if we see this message.
            self.AddStdoutHandlerCallback( ".*Adding specified comp to Render Queue.*" ).HandleCallback += self.HandleStdoutFormat

        # Set the popup ignorers.
        self.AddPopupIgnorer( "Motion Sketch" )
        self.AddPopupIgnorer( "The Smoother" )
        self.AddPopupIgnorer( "Time Controls" )
        self.AddPopupIgnorer( "Brush Tips" )
        self.AddPopupIgnorer( "The Wiggler" )
        self.AddPopupIgnorer( "Tracker Controls" )
        
        # Generic After Effects I have died pop-up dialog.
        # This generic pop-up dialog occurs for many reasons including the machine running out of RAM.
        # Adobe advise purge caches, increase RAM / memory allocation, decrease multi-machine / multi-processing.
        self.AddPopupHandler( ".*After Effects.*", "OK;Yes" )
        
        # Handle Adobe CS4 Color Finesse LE - Serial Number Dialog Registration Window.
        self.AddPopupHandler( ".*On-line Registration.*", "No" )
        
        # Handle Optical Flares License popup (the "OK" button is actually called "panel").
        self.AddPopupHandler( ".*Optical Flares License.*", "panel" )
        
        # "Tablet Version Mismatch", Message "Please reinstall the tablet software.
        self.AddPopupHandler( "Tablet Version Mismatch", "OK" )

        # Handle QuickTime popup dialog.
        # "QuickTime does not support the current Display Setting.  Please change it and restart this application."
        self.AddPopupHandler( "Unsupported Display", "OK" )
        self.AddPopupHandler( "Nicht.*", "OK" )

        # Handle Debug Event pop-up dialog. Typically occurs after a generic "After Effects" title pop-up dilaog which is handled separately.
        self.AddPopupHandler( "After Effects Debug Event", "Continue" )

        # Handle generic old After Effects app crash.
        self.AddPopupHandler( ".*AfterFX.exe.*", "OK" )
        self.AddPopupHandler( ".*Application Error.*", "OK" )
        self.AddPopupHandler( ".*Microsoft Visual.*", "OK" )

        self.FailWithoutFinishedMessage = self.GetBooleanConfigEntryWithDefault( "FailWithoutFinishedMessage", False )
        self.LogInfo( "Fail Without Finished Message set to: %s" % self.FailWithoutFinishedMessage  )
  
        # Read in the Fail On Existing AE Process setting, which can be overridden in the plugin info file.
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideFailOnExistingAEProcess", False ):
            self.FailOnExistingAEProcess = self.GetBooleanPluginInfoEntryWithDefault( "FailOnExistingAEProcess", True )
            self.LogInfo( "Fail on Existing After Effects process: %s (from plugin info override)" % self.FailOnExistingAEProcess )
        else:
            self.FailOnExistingAEProcess = self.GetBooleanConfigEntryWithDefault( "FailOnExistingAEProcess", False )
            self.LogInfo( "Fail on Existing After Effects process: %s" % self.FailOnExistingAEProcess )

        if self.FailOnExistingAEProcess:
            self.LogInfo( "Scanning for Existing After Effects GUI process which can sometimes cause 3rd party AE plugins to malfunction during network rendering" )
            processName = "After Effects"
            if ProcessUtils.IsProcessRunning( processName ):
                self.LogWarning( "Found Existing %s process" % processName )
                process = Process.GetProcessesByName( processName )[ 0 ]
                self.FailRender( "FailOnExistingAEProcess is enabled, and a process %s with pid %d exists - shut down this copy of After Effects to enable network rendering on this machine" % (processName, process.Id) )
            else:
                self.LogInfo( "No instances of After Effects currently running were found" )

    ## Called by Deadline to get the render executable.
    def RenderExecutable( self ):
        version = self.GetFloatPluginInfoEntry( "Version" )
        if version < 12:
            aeExeList = self.GetConfigEntry( "RenderExecutable" + str(version).replace( ".", "_" ) )
        elif 13.5 <= version < 14:
            aeExeList = self.GetConfigEntry( "RenderExecutable13_5")
        else:
            # For now, we are only supporting the major version of CC
            aeExeList = self.GetConfigEntry( "RenderExecutable" + str(float(int(version ))).replace( ".", "_" ) )
        
        aeExe = FileUtils.SearchFileList( aeExeList )
        if aeExe == "":
            self.FailRender( "After Effects " + str(version) + " render executable was not found in the semicolon separated list \"" + aeExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return aeExe

    ## Called by Deadline to get the render arguments.
    def RenderArgument( self ):
        version = int( self.GetFloatPluginInfoEntry( "Version" ) )
        self.MultiMachine = self.GetBooleanPluginInfoEntryWithDefault( "MultiMachineMode", False )
        if self.MultiMachine:
            self.MultiMachineStartFrame = self.GetIntegerPluginInfoEntryWithDefault( "MultiMachineStartFrame", -1 )
            self.MultiMachineEndFrame = self.GetIntegerPluginInfoEntryWithDefault( "MultiMachineEndFrame", -1 )
        
        renderarguments = "-project \"" + self.TempSceneFilename + "\""
        
        # See if we're rendering a specific comp. The -s, -e, and -output options are only valid in this case.
        comp = self.GetPluginInfoEntryWithDefault( "Comp", "" )
        if comp != "":
            self.HandleProgress = True
            
            renderarguments += " -comp \"" + comp + "\""
            
            if self.MultiMachine:
                self.LogInfo( "Multi Machine Mode enabled" )
            else:
                renderarguments += " -s " + str(self.GetStartFrame())
                renderarguments += " -e " + str(self.GetEndFrame())
            
            self.LocalRendering = False
            outputFile = self.GetPluginInfoEntryWithDefault( "Output", "" ).strip()
            outputFile = RepositoryUtils.CheckPathMapping( outputFile )
            outputFile = PathUtils.ToPlatformIndependentPath( outputFile )

            if outputFile != "":
                outputDir = os.path.dirname( outputFile )
                self.NetworkFilePath = outputDir

                if not self.MultiMachine:
                    self.LocalRendering = self.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False )

                    if self.LocalRendering:
                        outputDir = self.CreateTempDirectory( "AfterEffectsOutput" )
                        self.LocalFilePath = outputDir
                        
                        outputFile = os.path.join( outputDir, os.path.basename( outputFile ) )
                        
                        self.LogInfo( "Rendering to local drive, will copy files and folders to final location after render is complete" )
                    else:
                        self.LogInfo( "Rendering to network drive" )
                    
                if SystemUtils.IsRunningOnMac():
                    outputFile = outputFile.replace( "\\", "/" )
                else:
                    outputFile = outputFile.replace( "/", "\\" )
                
                self.ValidateFilepath( self.NetworkFilePath )

                renderarguments += " -output \"" + outputFile + "\""
        else:
            self.HandleProgress = False
        
        # Check if we should use the memory management flag.
        memoryManagementString = self.GetBooleanPluginInfoEntryWithDefault( "MemoryManagement" , False )
        if memoryManagementString:
            imageCache = self.GetIntegerPluginInfoEntryWithDefault( "ImageCachePercentage", 0 )
            maxMemory = self.GetIntegerPluginInfoEntryWithDefault( "MaxMemoryPercentage", 0 )
            if imageCache > 0 and maxMemory > 0:
                renderarguments = renderarguments + " -mem_usage " + str(imageCache) + " " + str(maxMemory)
        
        # Check if we should use the multi-process flag (AE 8 and later).
        multiProcessString = self.GetBooleanPluginInfoEntryWithDefault( "MultiProcess", False )
        if multiProcessString:
            renderarguments = renderarguments + " -mp"
        
        continueOnMissingFootage = self.GetBooleanPluginInfoEntryWithDefault( "ContinueOnMissingFootage", False )
        if version >= 9 and continueOnMissingFootage:
            self.LogInfo( "Continuing on missing footage" )
            renderarguments = renderarguments + " -continueOnMissingFootage"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "IgnoreMissingEffectReferencesErrors", False ):
            self.LogInfo( "Ignoring missing effect reference errors" )
        if self.GetBooleanPluginInfoEntryWithDefault( "IgnoreMissingLayerDependenciesErrors", False ):
            self.LogInfo( "Ignoring missing layer dependency errors" )
        if self.GetBooleanPluginInfoEntryWithDefault( "FailOnWarnings", False ):
            self.LogInfo( "Failing on warning messages" )

        # Ensure we always enforce StdOut/Err/render progress to be generated.
        if version >= 9:
            renderarguments += " -v ERRORS_AND_PROGRESS"
        
        renderarguments += " -close DO_NOT_SAVE_CHANGES"
        renderarguments += " -sound OFF"
        
        return renderarguments

    ## Function to validate a directory.
    def ValidateFilepath( self, directory ):
        self.LogInfo( "Validating the path: '%s'" % directory )

        if not os.path.exists( directory ):
            try:
                os.makedirs( directory )
                self.LogInfo( "Output directory has been created" )
            except:
                self.FailRender( "Failed to create path: '%s'" % directory )

        # Test to see if we have permission to create a file
        try:
            # TemporaryFile deletes the "file" when it closes, we only care that it can be created
            with tempfile.TemporaryFile( dir=directory ) as tempFile:
                pass
        except:
            self.FailRender( "Failed to create test file in directory: '%s'" % directory )

    ## Called by Deadline before the renderer starts.
    def PreRenderTasks( self ):
        self.FailureMessage = ""
        self.Framecount = 0
        self.PreviousFrameTime = ""

        # Reset Slave Status Message between Tasks.
        self.SetStatusMessage("")

        # Check if we should be doing path mapping.
        sceneFilename = RepositoryUtils.CheckPathMapping( self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() ) )
        
        if SystemUtils.IsRunningOnMac():
            sceneFilename = sceneFilename.replace( "\\", "/" )
        else:
            sceneFilename = sceneFilename.replace( "/", "\\" )
        
        # We can only do path mapping on .aepx files (they're xml files).
        if (os.path.splitext( sceneFilename )[1]).lower() == ".aepx" and self.GetBooleanConfigEntryWithDefault( "EnableAepxPathMapping", True ):
            self.LogInfo( "Performing path mapping on aepx project file" )
            
            tempSceneDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
            tempSceneFileName = os.path.basename( sceneFilename )
            self.TempSceneFilename = os.path.join( tempSceneDirectory, tempSceneFileName )
            
            if SystemUtils.IsRunningOnMac():
                RepositoryUtils.CheckPathMappingInFileAndReplace( sceneFilename, self.TempSceneFilename, ("\\","platform=\"Win\""), ("/","platform=\"MacPOSIX\"") )
                os.chmod( self.TempSceneFilename, os.stat( sceneFilename ).st_mode )
            else:
                RepositoryUtils.CheckPathMappingInFileAndReplace( sceneFilename, self.TempSceneFilename, ("/","platform=\"MacPOSIX\"","\\>"), ("\\","platform=\"Win\"","/>") )
                if SystemUtils.IsRunningOnLinux():
                    os.chmod( self.TempSceneFilename, os.stat( sceneFilename ).st_mode )
        else:
            self.TempSceneFilename = sceneFilename
                
        self.TempSceneFilename = PathUtils.ToPlatformIndependentPath( self.TempSceneFilename )

        # Get the path to the text file that forces After Effects to run the English version.
        if SystemUtils.IsRunningOnMac():
            myDocumentsPath = os.path.join( Environment.GetFolderPath( Environment.SpecialFolder.Personal ), "Documents/ae_force_english.txt" )
        else:
            myDocumentsPath = os.path.join( Environment.GetFolderPath( Environment.SpecialFolder.Personal ), "ae_force_english.txt" )
        
        # Check if we want to change After Effects to the English version. If we do, create the file.
        if self.GetBooleanConfigEntryWithDefault( "ForceRenderingEnglish", False ):
            try:
                self.LogInfo( "Attempting to create \"%s\" to force After Effects to run in English" % myDocumentsPath ) 
                open( myDocumentsPath, 'w' ).close()
            except:
                self.LogWarning( "Failed to create \"%s\" because %s" % ( myDocumentsPath, traceback.format_exc() ) ) 
        else:
            # If we don't want to force the English version, delete the file.
            if os.path.isfile( myDocumentsPath ):
                try:
                    self.LogInfo( "Attempting to delete \"%s\" to allow After Effects to run in the user's original language" % myDocumentsPath )
                    os.remove( myDocumentsPath )
                except:
                    self.LogWarning( "Failed to delete \"%s\" because %s" % ( myDocumentsPath, traceback.format_exc() ) ) 
               
        myRePath = self.getAERenderOnlyFileName()
        
        # Check if we want to start After Effects in render engine mode. If we do, create the file. And important delete it later.
        if self.GetBooleanConfigEntryWithDefault( "ForceRenderEngine", False ):
            try:
                self.LogInfo( "Attempting to create \"%s\" to force After Effects to run in Render Engine mode" % myRePath )
                open( myRePath, 'w' ).close()
            except:
                self.LogWarning( "Failed to create \"%s\" because %s" % ( myRePath, traceback.format_exc() ) ) 
        else:
            if self.GetBooleanConfigEntryWithDefault( "DeleteRenderEngineFile", False ):
                # If we don't want to force in Render Engine mode, delete the file.
                if os.path.isfile( myRePath ):
                    try:
                        self.LogInfo( "Attempting to delete \"%s\" to allow After Effects to run in the workstation environment" % myDocumentsPath )
                        os.remove( myRePath )
                    except:
                        self.LogWarning( "Failed to delete \"%s\" because %s" % ( myRePath, traceback.format_exc() ) ) 

    def CleanupRenderEngineFile( self, myRePath ):
        # Clean up Render Engine mode for the user to run it normal as a workstation. Delete the file.
        if self.GetBooleanConfigEntryWithDefault( "ForceRenderEngine", False ):
            self.LogInfo( "Checking for file \"%s\"" % myRePath )
            if os.path.isfile( myRePath ):
                try:
                    self.LogInfo( "Attempting to delete \"%s\" to allow After Effects to run in the workstation environment" % myRePath )
                    os.remove( myRePath )
                except:
                    self.LogWarning( "Failed to delete \"%s\" because %s" % ( myRePath, traceback.format_exc() ) )

    ## Called by Deadline after the renderer has exited.
    def PostRenderTasks( self ):
        failures = 0

        if self.FailWithoutFinishedMessage:
            if not self.RenderSuccess: # fail here if Succeed didn't get tripped.
                self.FailAERender( "The composition was not rendered completely. Found NO \"Finished Composition\" notice. To disable this failure if applicable, ensure 'Fail Without Finished Message' is set to False in AE plugin configuration." )
        
        myRePath = self.getAERenderOnlyFileName()
        self.CleanupRenderEngineFile( myRePath )
        
        # Clean up the temp file if we did path mapping on the aepx project file.
        if (os.path.splitext( self.TempSceneFilename )[1]).lower() == ".aepx" and self.GetBooleanConfigEntryWithDefault( "EnableAepxPathMapping", True ):
            os.remove( self.TempSceneFilename )

        if self.DelayedFailure:
            self.FailRender( "There was an error but the message could not properly be extracted\n" + self.FailureMessage )
        else:
            # Since the output option is only valid when rendering a specific comp, we will only check
            # the output size in this case.
            comp = self.GetPluginInfoEntryWithDefault( "Comp", "" )
            if comp and not self.MultiMachine:
                if self.LocalRendering:
                    self.LogInfo( "Moving output files and folders from " + self.LocalFilePath + " to " + self.NetworkFilePath )
                    self.VerifyAndMoveDirectory( self.LocalFilePath, self.NetworkFilePath, True, 0 )
                
                outputDirectories = self.GetJob().JobOutputDirectories
                outputFilenames = self.GetJob().JobOutputFileNames
                minSizeInKB = self.GetIntegerPluginInfoEntryWithDefault( "MinFileSize", 0 )
                deleteFilesUnderMinSize = self.GetBooleanPluginInfoEntryWithDefault( "DeleteFilesUnderMinSize", False )
                
                for outputDirectory, outputFilename in zip( outputDirectories, outputFilenames ):
                    outputFile = os.path.join( outputDirectory, outputFilename )
                    outputFile = RepositoryUtils.CheckPathMapping( outputFile )
                    outputFile = PathUtils.ToPlatformIndependentPath( outputFile )
                    
                    if outputFile and minSizeInKB > 0:
                        if outputFile.find( "#" ) >= 0:
                            frames = range( self.GetStartFrame(), self.GetEndFrame()+1 )
                            for frame in frames:
                                currFile = FrameUtils.ReplacePaddingWithFrameNumber( outputFile, frame )
                                failures += self.CheckFileSize( currFile, minSizeInKB, deleteFilesUnderMinSize )

                        else:
                            failures += self.CheckFileSize( outputFile, minSizeInKB, deleteFilesUnderMinSize )
                            
                        if failures != 0:
                            self.FailRender( "There were 1 or more errors with the output" )
                    else:
                        self.SetProgress(100)
                        self.SetStatusMessage( "Finished Rendering " + str(self.GetEndFrame() - self.GetStartFrame() + 1) + " frames" )
            else:
                self.LogInfo( "Skipping output file size check because a specific comp isn't being rendered or Multi-Machine rendering is enabled" )

    def CheckFileSize( self, fileToCheck, minFileSizeInKB, deleteFilesUnderMinSize ):
        failures = 0

        self.LogInfo( 'Checking file size of "%s"' % fileToCheck )
        if os.path.isfile( fileToCheck ):
            # bytes -> kilobytes (KB)
            fileSizeInKB = os.path.getsize( fileToCheck ) / 1024
            if fileSizeInKB < minFileSizeInKB:
                self.LogInfo( "    " + os.path.basename( fileToCheck ) + " has size " + str( fileSizeInKB ) + " KB and is less than " + str( minFileSizeInKB ) + " KB" )
                failures += 1
                if deleteFilesUnderMinSize:
                    os.remove( fileToCheck )
                    self.LogInfo( "    %s has been deleted" % os.path.basename( fileToCheck ) )
        else:
            self.LogInfo( "    %s does not exist" % os.path.basename( fileToCheck ) )
            failures += 1

        return failures
    
    def FailAERender( self, message ):
        myRePath = self.getAERenderOnlyFileName()
        self.CleanupRenderEngineFile( myRePath )
        self.FailRender( message )
    
    def RenderCanceled( self ):
        myRePath = self.getAERenderOnlyFileName()
        self.CleanupRenderEngineFile( myRePath )
    
    def HandleStdoutProgressLegacy( self ):
        currentFrameTime = self.GetRegexMatch(1)
        if self.HandleProgress and self.PreviousFrameTime != currentFrameTime:
            self.PreviousFrameTime = currentFrameTime
            
            #If the job is being submitted from the Monitor, no progress will be shown on the tasks/slave UI as the relevant information
            #is retrieved from After Effects. So the Monitor has no way of knowing the start and end frames.
            if self.MultiMachine:
                startFrame = self.MultiMachineStartFrame
                endFrame = self.MultiMachineEndFrame
                
                if startFrame == -1 and endFrame == -1:
                    return
            else:
                startFrame = self.GetStartFrame()
                endFrame = self.GetEndFrame()
            
            if ( endFrame - startFrame ) != -1:
                self.SetProgress((float(self.Framecount)/(endFrame-startFrame + 1)) *100)
                    
            if self.Framecount < (endFrame - startFrame + 1):
                self.SetStatusMessage( "Rendering frame " + str(startFrame + self.Framecount) )
            
            self.Framecount=self.Framecount+1

    def ParseTimeFromMatch( self ):
        string_date = self.GetRegexMatch(1)
        string_date = string_date.replace(';', ':')
        b = string_date.split(':')
        
        time  = int(b[3])
        time += int(b[2]) * 60
        time += int(b[1]) * 60 * 60
        time += int(b[0]) * 60 * 60 * 24
        
        return time
        
    def HandleStdoutTimecodeProgress( self ):
        currentTime = self.ParseTimeFromMatch()
        
        if self.FramesEndTime - self.FramesStartTime == 0:
            progress = 0
        else:
            progress = (currentTime - self.FramesStartTime) / ((self.FramesEndTime - self.FramesStartTime) / 100.0)
    
        self.SetProgress(progress)

    def HandleProgressTimecodeStart( self ):
        self.FramesStartTime = self.ParseTimeFromMatch()
    
    def HandleProgressTimecodeEnd( self ):
        self.FramesEndTime = self.ParseTimeFromMatch()
        
    def HandleStdoutFrameProgress( self ):
        currentTime = int(self.GetRegexMatch(1))
        
        if self.FramesEndTime - self.FramesStartTime == 0:
            progress = 0
        else:
            progress = (currentTime - self.FramesStartTime) / ((self.FramesEndTime - self.FramesStartTime) / 100.0)
        
        self.SetProgress(progress)

    def HandleProgressFrameStart( self ):
        self.FramesStartTime = int(self.GetRegexMatch(1) )
    
    def HandleProgressFrameEnd( self ):
        self.FramesEndTime = int(self.GetRegexMatch(1) )
        
    def HandleStdoutError( self ):
        if "auto-save" in unicode(self.GetRegexMatch(0)).lower(): # This was an autosaving issue, so it was not necessarily a critical error
            self.LogWarning( "After Effects auto-save was unsuccessful" )
        else:
            self.FailAERender( self.GetRegexMatch(0) )

    def HandleNonFatalError( self ):
        self.LogWarning( 'Ignoring the following error due to it being non fatal: %s' % self.GetRegexMatch(0) )
        
    def HandleStdoutFormat( self ):
        self.FailAERender( "After Effects tried to change output file formats. Cancelling task to avoid unusable output." )

    def HandleRenderVersion( self ):
        renderVersion = self.GetRegexMatch( 1 )
        SubmittedFromVersion = self.GetPluginInfoEntryWithDefault( "SubmittedFromVersion", "" )
        if SubmittedFromVersion:
            self.LogInfo( "Submitted from After Effects version: %s" % SubmittedFromVersion )
            if renderVersion != SubmittedFromVersion:
                self.LogWarning( "Slave's After Effects version is NOT the same as the After Effects version that was used to submit this job! Unexpected results may occur!" )


    def HandleStdoutInfo( self ):
        if not self.GetBooleanPluginInfoEntryWithDefault( "IgnoreMissingEffectReferencesErrors", False ):
            self.FailAERender( self.GetRegexMatch(0) )

    def HandleMissingLayerDependencies( self ):
        """
        This is a standard out handler that will fire when we see a missing layer dependencies error.
        If the plugin is set up to error on this message we add new output handlers to fail on the next line.

        This error message appears across multiple lines, so we must delay the failure so we can grab what is actually wrong.

        """
        if not self.GetBooleanPluginInfoEntryWithDefault( "IgnoreMissingLayerDependenciesErrors", False ):
            #only add the failLaterHandlers if they have not been added
            if not self.DelayedFailure:
                self.AddStdoutHandlerCallback( "PROGRESS:.*" ).HandleCallback += self.HandleFailLaterNoMessage
                self.AddStdoutHandlerCallback( ".*" ).HandleCallback += self.HandleFailLaterWithMessage

            self.DelayedFailure = True
            self.FailureMessage = "Error: " + self.GetRegexMatch( 0 )

    def HandleStdoutWarning( self ):
        warning = self.GetRegexMatch(1)
        if self.GetBooleanPluginInfoEntryWithDefault( "FailOnWarnings", False ):
            self.FailAERender( warning + " Failing render because this job has 'Fail On Warning Messages' enabled." )
        else:
            if warning.find( "The name of an output module for this render item is already in use." ) != -1:
                self.FailAERender( warning + " After Effects cannot render when the render queue contains more than one item with the same name." )

    def HandleFailLaterNoMessage( self ):
        """
        A standard out handler which fails the job on a multiline error message when we do not see the second line.
        """
        self.FailAERender( self.FailureMessage )

    def HandleFailLaterWithMessage( self ):
        """
        A standard out handler which fails the job on a multiline error message when we see the second line.
        """
        self.FailAERender( self.FailureMessage +"\n"+self.GetRegexMatch(0) )

    def HandleCudaError( self ):
        if not self.PrintCudaWarningOnce:
            self.PrintCudaWarningOnce = True
            self.LogWarning( "After Effects Project File Settings are configured to use Mercury/GPU rendering but Slave does not have any available GPU card.\n"
            "In the case of headless machines with no GPU capabilities, ensure you select to use 'Mercury Software Only' option in your Project Settings\n"
            "in After Effects before job submission to remove this warning message. GPU rendering while running as a service is NOT supported, so\n"
            "'Mercury Software Only' option should be used. However, this is dependent on whether the latest graphics drivers or 3rd party GPU accelerated AE plugins\n"
            "are being used as well. After Effects has now reverted to using the CPU for rendering. See Deadline docs for more info." )

    def HandleRenderSuccess( self ):
        self.RenderSuccess = True

        # Force shutdown of known processes which can sometimes 'hang' the aerender process.
        # processNames = ["AdobeIPCBroker","Adobe CEF Helper"]
        # for process in processNames:
        #     if ProcessUtils.KillProcesses( process ):
        #         self.LogInfo( "Shutdown process: %s" % process )

        # Force shutdown of aerender process & children.
        # processIDs = self.GetManagedProcessIDs()
        # for pid in processIDs:
        #     if ProcessUtils.KillParentAndChildProcesses( pid ):
        #         self.LogInfo( "Shutdown aerender process with PID: %s" % pid )

    def CheckExitCode( self, exitCode ):
        if self.FailWithoutFinishedMessage: # job marked to fail if no render success message found
            if not self.RenderSuccess: # no render success message found
                self.FailRender( "After Effects did not report successful render; exit code: %s. Check the render log." % exitCode )
        else:
            if exitCode != 0: # if exit code non-zero, then fail the job
                self.FailRender( "After Effects returned non-zero error code: %s. Check the render log." % exitCode )

    def getAERenderOnlyFileName( self ):
        # Get the path to the text file that forces After Effects to run in Render Engine mode.
        outputPath = os.path.join( Environment.GetFolderPath( Environment.SpecialFolder.Personal ), "ae_render_only_node.txt" )
        if SystemUtils.IsRunningOnMac():
            outputPath = os.path.join( Environment.GetFolderPath( Environment.SpecialFolder.Personal ), "Documents/ae_render_only_node.txt" )
            
        return outputPath
