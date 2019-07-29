import io
import os
import re
import subprocess
import threading

from Deadline.Plugins import DeadlinePlugin
from Deadline.Scripting import FileUtils, FrameUtils, PathUtils, RepositoryUtils, StringUtils, SystemUtils
from System.IO import Path

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return VrayPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.cleanup()

######################################################################
## This is the main DeadlinePlugin class for the VrayPlugin plugin.
######################################################################
class VrayPlugin (DeadlinePlugin):
    progress = 0
    currFrame = 0
    tempSceneFilename = ""
    
    def __init__( self ):
        self.InitializeProcessCallback += self.initializeProcess
        self.RenderExecutableCallback += self.renderExecutable
        self.RenderArgumentCallback += self.renderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
        self.IsSingleFramesOnlyCallback += self.isSingleFramesOnly
        self.CheckExitCodeCallback += self.CheckExitCode
        
        self.vrayVersion = 3.6
        self.failedLoadingDLL = False
    
    def cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
        del self.IsSingleFramesOnlyCallback
        del self.CheckExitCodeCallback
    
    def initializeProcess( self ):
        self.StdoutHandling = True

        self.AddStdoutHandlerCallback( ".*error: Error loading plugin library.*vray_BRDFSimbiont.dll.*LoadLibrary failed.*" ).HandleCallback += self.handleStdoutFailedLoadingDLL
        self.AddStdoutHandlerCallback( ".*error:.*" ).HandleCallback += self.handleStdoutError

        self.AddStdoutHandlerCallback( r"Rendering image.*:[ ]+([0-9]+(?:\.[0-9]+)?)%" ).HandleCallback += self.handleStdoutProgress
        self.AddStdoutHandlerCallback( "Rendering image.*: done" ).HandleCallback += self.handleStdoutComplete
        self.AddStdoutHandlerCallback( "Starting frame ([0-9]*)" ).HandleCallback += self.handleStdoutStartFrame

        self.AddStdoutHandlerCallback( ".*Closing log.*" ).HandleCallback += self.handleStdoutClosing
        self.AddStdoutHandlerCallback( ".*Frame took.*" ).HandleCallback += self.handleStdoutClosing
        
    def renderExecutable( self ):
        vrayExeList = self.GetConfigEntry( "VRay_RenderExecutable" )
        vrayExe = FileUtils.SearchFileList( vrayExeList )
        if vrayExe == "":
            self.FailRender( "V-Ray render executable was not found in the semicolon separated list \"" + vrayExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        self.vrayVersion = self.getVrayVersion( vrayExe )
        
        return vrayExe
        
    def renderArgument( self ):
    
        renderEngines = {"V-Ray" : "0", "V-Ray RT" : "1", u"V-Ray RT(OpenCL)" : "3", u"V-Ray RT(CUDA)" : "5"}
        sRGBOptions = ["On", "Off"]

        displayWindow = self.GetBooleanPluginInfoEntryWithDefault( "DisplayVFB", False )
        autoclose = self.GetBooleanPluginInfoEntryWithDefault( "AutocloseVFB", True )
        displaySRGB = self.GetPluginInfoEntryWithDefault( "DisplaySRGB", "On" )

        # Get the frame information.
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        singleRegionJob = self.IsTileJob()
        singleRegionFrame = str(self.GetStartFrame())
        singleRegionIndex = self.GetCurrentTaskId()
        separateFilesPerFrame = self.GetBooleanPluginInfoEntryWithDefault( "SeparateFilesPerFrame", False )
        regionRendering = self.GetBooleanPluginInfoEntryWithDefault( "RegionRendering", False )
        rtEngine = self.GetPluginInfoEntryWithDefault( "VRayEngine", "V-Ray" )
        rtTimeout = self.GetFloatPluginInfoEntryWithDefault( "RTTimeout", 0.00 )
        rtNoise = self.GetFloatPluginInfoEntryWithDefault( "RTNoise", 0.001 )
        rtSampleLevel = self.GetIntegerPluginInfoEntryWithDefault( "RTSamples", 0 )

        # Can't allow it to be interactive or display the image because that would hang the slave
        renderarguments = " -scenefile=\"" + self.tempSceneFilename + "\" -interactive=0"

        if not displayWindow:
            renderarguments += " -display=0" # Default value is 1
        else:
            if autoclose:
                renderarguments += " -autoclose=1"# Default value is 0

            renderarguments += " -displaySRGB=%s" % ( sRGBOptions.index( displaySRGB ) + 1 )
            
        renderarguments += " -rtEngine=%s" % renderEngines[ rtEngine.strip() ]

        if not rtEngine == "V-Ray":
            renderarguments += " -rtTimeOut=%s -rtNoise=%s -rtSampleLevel=%s" % ( rtTimeout, rtNoise, rtSampleLevel )

        renderarguments += " -frames=" + str( startFrame )
        if endFrame > startFrame:
            renderarguments += "-" + str( endFrame )
        
        # Set the output path.
        outputFile = self.GetPluginInfoEntryWithDefault( "OutputFilename", "" ).strip()
        if outputFile != "":
            outputFile = RepositoryUtils.CheckPathMapping( outputFile )
            outputFile = PathUtils.ToPlatformIndependentPath( outputFile )

            if regionRendering:
                outputPath = Path.GetDirectoryName( outputFile )
                outputFileName = Path.GetFileNameWithoutExtension( outputFile )
                outputExtension = Path.GetExtension( outputFile )
                
                if singleRegionJob:
                    outputFile = os.path.join(outputPath, ( "_tile%s_" % singleRegionIndex ) + outputFileName +  outputExtension )

                else:
                    currTile = self.GetIntegerPluginInfoEntryWithDefault( "CurrentTile", 1 )
                    outputFile = os.path.join(outputPath, ( "_tile%d_" % currTile ) + outputFileName +  outputExtension )
                
            renderarguments += " -imgFile=\"" + outputFile + "\""
        
        # Now set the rest of the options.
        renderarguments += " -numThreads=" + str( self.GetThreadCount() )
        
        width = self.GetIntegerPluginInfoEntryWithDefault( "Width", 0 )
        if width > 0:
            renderarguments += " -imgWidth=" + str( width )
        
        height = self.GetIntegerPluginInfoEntryWithDefault( "Height", 0 )
        if height > 0:
            renderarguments += " -imgHeight=" + str( height )

        if regionRendering:
            regionNumString = ""
            if singleRegionJob:
                regionNumString = str( singleRegionIndex )
                
            #Coordinates In Pixels will always be true when using the common tilerendering code.
            if self.GetBooleanPluginInfoEntryWithDefault( "CoordinatesInPixels", False ):
                #With the coordinates already being in pixels we do not need to modify the coordinates.
                xStart = self.GetIntegerPluginInfoEntryWithDefault("RegionXStart"+regionNumString,0)
                xEnd = self.GetIntegerPluginInfoEntryWithDefault("RegionXEnd"+regionNumString,0)
                yStart = self.GetIntegerPluginInfoEntryWithDefault("RegionYStart"+regionNumString,0)
                yEnd = self.GetIntegerPluginInfoEntryWithDefault("RegionYEnd"+regionNumString,0)

            else:
                self.LogWarning( "Using deprecated coordinate system.  Please submit new jobs to use the new coordinates system." )
                xStart = round( self.GetFloatPluginInfoEntryWithDefault( "RegionXStart" + regionNumString, 0 ) * width )
                xEnd = round( self.GetFloatPluginInfoEntryWithDefault( "RegionXEnd" + regionNumString, 0 ) * width )
                yStart = round( self.GetFloatPluginInfoEntryWithDefault( "RegionYStart" + regionNumString, 0 ) * height )
                yEnd = round( self.GetFloatPluginInfoEntryWithDefault( "RegionYEnd" + regionNumString, 0 ) * height )

            renderarguments += " -region=%d;%d;%d;%d" % ( xStart,yStart,xEnd, yEnd )
    
        disableProgressColor = self.GetBooleanConfigEntryWithDefault( "DisableProgressColor", False)
        if disableProgressColor:
            renderarguments += " -DisableProgressColor=0"
        
        renderarguments += " " + self.GetPluginInfoEntryWithDefault( "CommandLineOptions", "" )
        
        yetiSearchPaths = []
        searchPathIndex = 0
        while True:
            searchPath = self.GetPluginInfoEntryWithDefault( "YetiSearchPath" + str(searchPathIndex), "" ).replace( "\\", "/" )
            if not searchPath:
                break
            
            yetiSearchPaths.append( RepositoryUtils.CheckPathMapping( searchPath ) )
        
            searchPathIndex += 1
        
        if len(yetiSearchPaths) >0:
            oldSearchPath = os.environ.get( "PG_IMAGE_PATH" )
            if oldSearchPath:
                yetiSearchPaths.append(oldSearchPath)
            
            yetiSepChar = ":"
            if SystemUtils.IsRunningOnWindows():
                yetiSepChar = ";"
            
            self.SetProcessEnvironmentVariable( "PG_IMAGE_PATH", yetiSepChar.join( yetiSearchPaths )  )
        
        return renderarguments
    
    def GetThreadCount( self ):
        threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if self.OverrideCpuAffinity() and self.GetBooleanConfigEntryWithDefault( "LimitThreadsToCPUAffinity", False ):
            affinity = len( self.CpuAffinity() )
            if threads == 0:
                threads = affinity
            else:
                threads = min( affinity, threads )
                
        return threads    
    
    def PreRenderTasks( self ):       
        self.LogInfo( "Starting V-Ray Task" )
        
        # Get the scene file to render.
        sceneFilename = self.GetPluginInfoEntry( "InputFilename" )
        sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename )
        sceneFilename = PathUtils.ToPlatformIndependentPath( sceneFilename )
        
        # If we're rendering separate files per frame, need to get the vrscene file for the current frame.
        separateFilesPerFrame = self.GetBooleanPluginInfoEntryWithDefault( "SeparateFilesPerFrame", False )
        if separateFilesPerFrame:
            currPadding = FrameUtils.GetFrameStringFromFilename( sceneFilename )
            paddingSize = len( currPadding )
            newPadding = StringUtils.ToZeroPaddedString( self.GetStartFrame(), paddingSize, False )
            sceneFilename = sceneFilename.replace( currPadding, newPadding )
        
        # Check if we should be doing path mapping.
        slaveInfo = RepositoryUtils.GetSlaveInfo( self.GetSlaveName(), True )
        if self.GetBooleanConfigEntryWithDefault( "EnableVrscenePathMapping", True ) or slaveInfo.IsAWSPortalInstance:
            self.LogInfo( "Performing path mapping on vrscene file" )
            
            tempSceneDirectory = self.CreateTempDirectory( "thread" + str( self.GetThreadNumber() ) )
            tempSceneFileName = Path.GetFileName( sceneFilename )
            self.tempSceneFilename = os.path.join( tempSceneDirectory, tempSceneFileName )
                            
            mappedFiles = set()
            filesToMap = [ ( sceneFilename, os.path.dirname(sceneFilename) ) ] 
            while filesToMap:
                curFile, originalSceneDirectory = filesToMap.pop()
                #Include directives normally contain relative paths but just to be safe we must run pathmapping again.
                curFile = RepositoryUtils.CheckPathMapping( curFile )
                
                if not os.path.isabs( curFile ):
                    curFile = os.path.join( originalSceneDirectory, curFile )
                    
                if not os.path.exists( curFile ):
                    self.LogInfo( "The include file %s does not exist." % curFile )
                    continue
                
                if os.path.basename( curFile ) in mappedFiles:
                    self.LogInfo( "The include file %s has already been mapped." % curFile )
                    continue

                self.LogInfo( "Starting to map %s" %curFile )
                    
                mappedFiles.add( os.path.basename( curFile ) )
                tempFileName = os.path.join( tempSceneDirectory, os.path.basename( curFile ) )
                
                foundFiles = self.map_vrscene_includes_cancelable( curFile, tempFileName )
                newOriginDirectory = os.path.dirname( curFile )
                for foundFile in foundFiles:
                    filesToMap.append( ( foundFile, newOriginDirectory) )
                
                map_files_and_replace_slashes( tempFileName, tempFileName )
                if self.IsCanceled():
                    self.FailRender( "Received cancel task command from Deadline." )

        else:
            self.tempSceneFilename = sceneFilename
                
        self.tempSceneFilename = PathUtils.ToPlatformIndependentPath( self.tempSceneFilename )
    
    def PostRenderTasks( self ):       
        slaveInfo = RepositoryUtils.GetSlaveInfo( self.GetSlaveName(), True )
        # Clean up the temp file if we did path mapping on the vrscene file.
        if self.GetBooleanConfigEntryWithDefault( "EnableVrscenePathMapping", True ) or slaveInfo.IsAWSPortalInstance:
            tempDir = os.path.dirname(self.tempSceneFilename)
            for fileName in os.listdir(tempDir):
                os.remove(os.path.join(tempDir, fileName))
        
        self.LogInfo( "Finished V-Ray Task" )
    
    def isSingleFramesOnly( self ):
        # If we are rendering one file per frame, then we can only render one frame at a time.
        separateFilesPerFrame = self.GetBooleanPluginInfoEntryWithDefault( "SeparateFilesPerFrame", False )
        return separateFilesPerFrame

    ######################################################################
    ## Standard Out Handlers
    ######################################################################
    def handleStdoutFailedLoadingDLL( self ):
        self.failedLoadingDLL = True
        self.LogWarning( "V-Ray failed to load the following DLL. If this is a critical error, please contact Deadline support." )
        self.LogWarning( self.GetRegexMatch( 0 ) )

    def handleStdoutError( self ):
        self.FailRender( self.GetRegexMatch( 0 ) )
        self.updateProgress()
        
    def handleStdoutProgress(self):
        self.progress = float( self.GetRegexMatch( 1 ) )
        self.updateProgress()
        
    def handleStdoutComplete( self ):
        self.progress = 100
        self.updateProgress()
        
    def handleStdoutStartFrame( self ):
        self.currFrame = float( self.GetRegexMatch( 1 ) )
        self.SetStatusMessage( "Rendering Frame - " + self.GetRegexMatch( 1 ) )
        
    def handleStdoutClosing( self ):
        self.SetStatusMessage( "Job Complete" )
        
    ######################################################################
    ## Helper Functions
    ######################################################################
    def updateProgress( self ):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        
        if startFrame == endFrame:
            self.SetProgress( self.progress )
        else:
            overallProgress = ( ( 1.0 / ( endFrame - startFrame + 1 ) ) ) * self.progress
            currentFrameProgress = ( ( ( ( self.currFrame - startFrame ) * 1.0 ) / ( ( ( endFrame - startFrame + 1 ) * 1.0 ) ) ) * 100 )
            self.SetProgress( overallProgress + currentFrameProgress )
            
    def getVrayVersion( self, executable ):
        ver = 3.6
        
        arguments = [executable, "-version"]
        
        # Hide the window
        startupinfo = None
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        output, errors = proc.communicate()
        
        versionRegex = re.compile(r"V-Ray core version is (\d+.\d+).\d+", re.IGNORECASE)
        match = versionRegex.search( output )
        if match:
            ver = float( match.group(1) )
        
        return ver

    def CheckExitCode( self, exitCode ):
        # If V-Ray failed to load a known benign DLL, it will have an exit code other than 0. (ie. 3)
        if exitCode == 3:
            if self.failedLoadingDLL:
                return

        if exitCode != 0:
            self.FailRender( "V-Ray returned non-zero error code: %s. Check the render log." % exitCode )
    
    def map_vrscene_includes_cancelable( self, filename, outputfilename ):
        vrsceneThread = map_vrscene_includes_threaded( filename, outputfilename )
        while not vrsceneThread.is_complete():
            SystemUtils.Sleep( 1000 )
            if self.IsCanceled():
                vrsceneThread.cancel()
            self.LogInfo( "Mapping %s Include Directives: %02d%%" % (filename, vrsceneThread.get_progress() *100 ) )
            
        return vrsceneThread.get_results()
    
def map_files_and_replace_slashes( inputFile, outputFile ):
    if SystemUtils.IsRunningOnWindows():
        RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator( inputFile, outputFile, "/", "\\" )
    else:
        RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator( inputFile, outputFile, "\\", "/" )
        os.chmod( outputFile, os.stat( inputFile ).st_mode )
        
class map_vrscene_includes_threaded:
    def __init__( self, filename, outputfilename ):
        self._threading_controller = _ThreadingController()
        self._thread = threading.Thread(target = _map_vrscene_includes_internal, args = ( filename, outputfilename, self._threading_controller,))
        self._thread.start()
    #Client can call this during operation to cancel and complete the operation.
    #Will wait until thread execution has ended.
    def cancel( self ):
        self._threading_controller.set_canceled()
        self._thread.join()
    #Returns true if the operation is complete (ie results are in or it's been canceled)
    def is_complete( self ):
        return self._threading_controller.is_complete()
    #Gets the progress of the operation. Range is 0.0 to 1.0
    def get_progress( self ):
        return self._threading_controller.get_progress()
    #Stops execution until the operation is complete.
    def wait_for_complete( self ):
        self._thread.join()
    #Will return the results if the results are ready.
    #Will return None if the operation was canceled.
    #Will raise an exception if the results are still processing.
    #Will raise an exception if there was a problem with the operation (eg file not found, etc.)
    def get_results( self ):
        if not self._threading_controller.is_complete():
            raise Exception( "get_vrscene_properties_threaded: Do not call get_results() until is_complete() return True." )
        if self._threading_controller.exception:
            raise self._threading_controller.exception #Raise the exception that occured in the thread
        if self._threading_controller.is_canceled():
            return None
        return self._threading_controller.results
        
def _map_vrscene_includes_internal( filename, outputfilename, threadingController ):
    try:
        datablockArray = _replace_all_directives_and_copy( filename, outputfilename, threadingController  )
        threadingController.results = datablockArray

    except Exception as e:
        del threadingController.results[:]
        threadingController.exception = e

    threadingController.set_complete()
        
def replaceSlashesByOS( value ):
    if SystemUtils.IsRunningOnWindows():
        value = value.replace('/', '\\')
    else:
        value = value.replace( "\\", "/" )
        
    return value

def _remove_files_from_directive( directiveLine, additionalFilesToMap ):
    directiveLine = directiveLine.strip()
    
    directiveInfo = directiveLine.split(None, 1 )
    #Directive is of the form #include "PATH"
    if len(directiveInfo) == 2:
        includePath = directiveInfo[1]
        includePath = includePath.strip().strip("\"'")
        includePath = replaceSlashesByOS( includePath )
        includePath = RepositoryUtils.CheckPathMapping( includePath )
        additionalFilesToMap.append( includePath )
        
        directiveInfo[1] = u'"%s"' % os.path.basename( includePath )
        
    directiveLine = u" ".join(directiveInfo)
    
    return directiveLine + u"\r\n"  

def _process_identifier_and_return_end( bufferBytes, startIndex, outputFileHandle, filesToMap, linePrefix=u"" ):
    lineBreakFindIndex = bufferBytes.find( "\n", startIndex )

    if lineBreakFindIndex == -1:
        return -1

    identifier = linePrefix + bufferBytes[ startIndex : lineBreakFindIndex + 1 ]
    identifier = _remove_files_from_directive(identifier, filesToMap)
    outputFileHandle.write(identifier)

    return lineBreakFindIndex


def _replace_all_directives_and_copy(filename, output_filename, threading_controller):
    """
    Path map all of the #include directives in the vrscene file and copy it the temporary location for rendering.
    :param (str) filename: The name of the file to path map.
    :param (str) output_filename: The temporary location of the path mapped file for rendering.
    :param (_ThreadingController) threading_controller: The thread controller that the path mapping is running in.
    :return (List): A list of all the files in #include directives that need to be path mapped yet
    """
    files_to_map = []

    file_size = float(os.path.getsize(filename))
    identifier_string = "#include"
    
    buffer_size = 8192

    with io.open(filename, mode='r', encoding="utf-8") as file_handle:
        with io.open(output_filename, mode='w', encoding="utf-8") as output_file_handle:
            buffer_pos_in_file = 0
            buffer_bytes = file_handle.read(buffer_size)
            holdover_buffer_find_index = -1

            while buffer_bytes:
                # Get the next block of data
                next_buffer_bytes = file_handle.read(buffer_size)

                buffer_find_index = holdover_buffer_find_index
                mid_buffer_index = holdover_buffer_find_index + 1
                holdover_buffer_find_index = -1

                # Do a straight search of the buffer
                while True:
                    buffer_find_index = buffer_bytes.find(identifier_string, buffer_find_index + 1)

                    if buffer_find_index == -1:
                        break

                    output_file_handle.write(buffer_bytes[mid_buffer_index:buffer_find_index])

                    identifier_end = _process_identifier_and_return_end(buffer_bytes, buffer_find_index,
                                                                        output_file_handle, files_to_map)
                    if identifier_end > -1:
                        mid_buffer_index = identifier_end + 1
                    else:
                        identifier_end = _process_identifier_and_return_end(
                            bufferBytes=next_buffer_bytes,
                            startIndex=0,
                            outputFileHandle=output_file_handle,
                            filesToMap=files_to_map,
                            linePrefix=buffer_bytes[buffer_find_index:]
                        )

                        if identifier_end > -1:
                            holdover_buffer_find_index = identifier_end
                            mid_buffer_index = len(buffer_bytes)

                # Catch the find case where the identifier string falls halfway between two buffer reads.
                # For example one buffer ends with '#inc' and the next buffer starts with 'lude "...."'
                if next_buffer_bytes and buffer_bytes:
                    inbetween_start_index = len(buffer_bytes) - len(identifier_string) + 1
                    inbetween_bytes = \
                        buffer_bytes[inbetween_start_index:] + next_buffer_bytes[0:len(identifier_string) - 1]

                    inbetween_find_index = -1

                    while True:
                        inbetween_find_index = inbetween_bytes.find(identifier_string, inbetween_find_index + 1)

                        if inbetween_find_index == -1:
                            break

                        output_file_handle.write(
                            buffer_bytes[mid_buffer_index:inbetween_start_index + inbetween_find_index]
                        )

                        identifier_end = _process_identifier_and_return_end(
                            bufferBytes=next_buffer_bytes,
                            startIndex=0,
                            outputFileHandle=output_file_handle,
                            filesToMap=files_to_map,
                            linePrefix=buffer_bytes[inbetween_start_index + inbetween_find_index:]
                        )

                        if identifier_end > -1:
                            holdover_buffer_find_index = identifier_end
                            mid_buffer_index = len(buffer_bytes)

                try:
                    output_file_handle.write(buffer_bytes[mid_buffer_index:])
                except IndexError:
                    pass

                # Get ready for the next loop
                buffer_pos_in_file += len(buffer_bytes)
                buffer_bytes = next_buffer_bytes

                # Update progress and check for cancel
                threading_controller.set_progress(buffer_pos_in_file / file_size)
                if threading_controller.is_canceled():
                    return []

    return files_to_map


class _ThreadingController:
    def __init__( self ):
        #Output results. Only access these once "is_complete" is true.
        self.results = []
        self.exception = None

        self._threadLock = threading.Lock()
        self._isComplete = False
        self._isCanceled = False
        self._progress = 0.0

    def is_complete( self ):
        with self._threadLock:
            return self._isComplete
    def get_progress( self ):
        with self._threadLock:
            return self._progress
    def is_canceled( self ):
        with self._threadLock:
            return self._isCanceled

    def set_complete( self ):
        with self._threadLock:
            self._isComplete = True
    def set_progress( self, progress ):
        with self._threadLock:
            self._progress = progress
    def set_canceled( self ):
        with self._threadLock:
            self._isCanceled = True
            self._isComplete = True
            del self.results[:]
            self.exception = None
