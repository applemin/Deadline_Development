import os

from System.IO import *

from Deadline.Scripting import *
from Deadline.Plugins import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return AltusPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Altus plugin.
######################################################################
class AltusPlugin( DeadlinePlugin ):    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument

        # The EXR compressions that Altus accepts. We communicate this choice to Altus via a 0-based index.
        self.EXR_COMPRESSIONS = ("No Compression", "RLE", "ZIPS", "ZIP", "PIZ", "PXR24", "B44", "B44A", "DWAA", "DWAB")

    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess( self ):
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( r"\[ FATAL \].*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "error.*|Error.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( ".*Unable to find a usable CPU device.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "([0-9]*\.[0-9]*)% Complete.*" ).HandleCallback += self.HandleStdoutProgress
        self.AddStdoutHandlerCallback( "\[(\s+)?([0-9]+.[0-9]+)%\].*" ).HandleCallback += self.HandleStdoutProgress2 # Altus 1.8 progress: "[ 66.67%]   Third stage..."
        self.AddStdoutHandlerCallback( "100% Complete.*" ).HandleCallback += self.HandleStdoutComplete
        self.AddStdoutHandlerCallback( "current frame number: ([0-9]*).*" ).HandleCallback += self.HandleStdoutStartFrame
        self.AddStdoutHandlerCallback( ".*Filtering frame:(\s+)?([0-9]+).*" ).HandleCallback += self.HandleStdoutStartFrame2
        self.AddStdoutHandlerCallback( "Total execution time :.*" ).HandleCallback += self.HandleStdoutClosing
        
        self.progress = 0
        self.currFrame = 0

        self.job = self.GetJob()
        self.version = self.GetFloatPluginInfoEntryWithDefault( "Version", 1.9 )
        self.executableType = self.GetPluginInfoEntryWithDefault( "ExecutableType", "Auto Select" )

        
    def RenderExecutable( self ):
        executableList = self.GetConfigEntry( "Altus_RenderExecutable_"+str( int( self.version ) ) )
        executable = FileUtils.SearchFileList( executableList )
        if executable == "":
            self.FailRender( "Altus executable was not found in the semicolon separated list \"" + executableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        exeName = os.path.splitext( os.path.basename( executable ) )[0]

        if self.version < 1.9:
            if self.executableType == "OpenCl":
                executable = self.rreplace( executable, exeName, "altus-opencl", 1 )
            elif self.executableType == "GPU":
                executable = self.rreplace( executable, exeName, "altus-cuda", 1 )
            elif self.executableType == "C++":
                executable = self.rreplace( executable, exeName, "altus-cpp", 1 )
            else:
                executable = self.rreplace( executable, exeName, "altus-cli", 1 )
        else: # As of 1.9 they're in the same executable...
            executable = self.rreplace( executable, exeName, "altus-cli", 1 )

        return executable

    def RenderArgument( self ):
        # Get the frame information.
        jobFrames = self.job.JobFramesList
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        
        config = self.GetPluginInfoEntryWithDefault( "Config", "" )
        outPath = self.GetPluginInfoEntryWithDefault( "OutputFile", "" )

        renderer = self.GetPluginInfoEntryWithDefault( "Renderer", "Other" )
        preserveLayers = self.GetPluginInfoEntryWithDefault( "PreserveLayers", "none" )
        outputQuality = self.GetPluginInfoEntryWithDefault( "OutputQuality", "" )
        aovQuality = self.GetPluginInfoEntryWithDefault( "AOVQuality", "none" )
        frameRadius = self.GetIntegerPluginInfoEntryWithDefault( "FrameRadius", 1 )
        filterRadius = self.GetIntegerPluginInfoEntryWithDefault( "FilterRadius", 10 )
        kc1 = self.GetFloatPluginInfoEntryWithDefault( "Kc_1", 0.45 )
        kc2 = self.GetFloatPluginInfoEntryWithDefault( "Kc_2", 0.45 )
        kc4 = self.GetFloatPluginInfoEntryWithDefault( "Kc_4", 0.45 )
        kf = self.GetFloatPluginInfoEntryWithDefault( "Kf", 0.6 )
        tile = self.GetBooleanPluginInfoEntryWithDefault( "Tile", False )
        tileSize = self.GetPluginInfoEntryWithDefault( "TileSize", "" )
        fireFly = self.GetBooleanPluginInfoEntryWithDefault( "FireFly", False )

        # Altus 1.9 changes
        if self.version < 1.9:
            forceContinue = self.GetBooleanPluginInfoEntryWithDefault( "ForceContinue", False )
        else:
            forceContinue = self.GetIntegerPluginInfoEntryWithDefault( "ForceContinueInt", 0 )

        ignoreAlpha = self.GetBooleanPluginInfoEntryWithDefault( "IgnoreAlpha", False )
        skipFrameRadius = self.GetBooleanPluginInfoEntryWithDefault( "SkipFrameRadius", False )

        singlePass = self.GetBooleanPluginInfoEntryWithDefault( "SinglePass", False )

        force16bitOutput = self.GetBooleanPluginInfoEntryWithDefault( "Force16bitOutput", False )
        exrCompression = self.GetPluginInfoEntryWithDefault( "EXRCompression", "" )
        
        # Plugin config option.
        verbose = self.GetBooleanConfigEntryWithDefault( "Verbose", True )
        verbosityLevel = self.GetIntegerConfigEntryWithDefault( "VerbosityLevel", 2 )
        
        rgbfiles = self.GetPluginInfoEntryWithDefault( "RgbFiles", "" )
        posfiles = self.GetPluginInfoEntryWithDefault( "PositionFiles", "" )
        nrmfiles = self.GetPluginInfoEntryWithDefault( "NormalsFiles", "" )
        visfiles = self.GetPluginInfoEntryWithDefault( "VisibilityFiles", "" )
        albfiles = self.GetPluginInfoEntryWithDefault( "AlbedoFiles", "" )
        caufiles = self.GetPluginInfoEntryWithDefault( "CausticFiles", "" )
        hairFiles = self.GetPluginInfoEntryWithDefault( "HairFiles", "" )
        extraFiles = self.GetPluginInfoEntryWithDefault( "ExtraFiles", "" )
        additionalFiles = self.GetPluginInfoEntryWithDefault( "AdditionalFiles", "" )

        arguments = []
        
        if len( jobFrames ) > 1:
            arguments.append( '--start-frame=%s' % startFrame )
            arguments.append( '--end-frame=%s' % endFrame )
            arguments.append( '--frame-radius=%s' % frameRadius )
        
        outPath = RepositoryUtils.CheckPathMapping( outPath ).replace( "\\", "/" )

        # Check if output directory exists, create if otherwise. Altus will fail to process task if the directory doesn't exist.
        directory = os.path.dirname( outPath )
        if not os.path.exists( directory ):
            self.LogWarning( 'The output folder does not exist: "%s", trying to create it...' % directory )
            try:
                os.makedirs( directory )
            except Exception as e:
                self.FailRender( 'Failed to create the directory: "%s", please ensure the directory is created and accessible before trying again.\n%s' % ( directory, e ) )
        elif not os.path.isdir( directory ):
            self.FailRender( '"%s" exists but it is not a directory. Choose a different destination and ensure it exists and is accessible.' % directory )

        arguments.append( '--out-path="%s"' % outPath )

        # If CUDA or OpenCL then use --gpu flag.
        if self.executableType in [ "OpenCl", "GPU" ] or self.version >= 1.9:
            arguments.append( '--gpu' ) # As of 1.9 this flag is the default

            # Check if we are overriding GPU affinity either via job settings or Slave centric GPU affinity.
            selectedGPUs = self.GetGpuOverrides()
            
            if len(selectedGPUs) > 0:
                if self.GetThreadNumber() > len(selectedGPUs):
                    self.FailRender( "Thread number is higher than selected GPU count! Altus currently only supports a single GPU ID." )

                if len(selectedGPUs) > 1: # Altus (at least from 1.8 to 1.9) only supports overriding a single gpu id.
                    selectedGPUs = [ selectedGPUs[self.GetThreadNumber()] ]
                    self.LogWarning( "Altus currently only supports a single GPU ID and multiple IDs have been declared! Switching to use GPU ID that matches current thread number." )

                gpus = ",".join(str(gpu) for gpu in selectedGPUs)
                self.LogInfo( "This Slave is overriding its GPU affinity, so the following GPU will be used: " + gpus )
                arguments.append( '--device-id=%s' % gpus )

        if self.version >= 2.0:
            arguments.append( '--verbose=%s' % verbosityLevel )
        else:
            arguments.append( '--verbose' if verbose else '--quiet' )

        # If using configFile, then return with configFilePath, ignoring all other settings below.
        if config:
            arguments.insert( 0, '--config="%s"' % config )
        
            return " ".join( arguments )

        arguments.append( '--radius=%s' % filterRadius )
        arguments.append( '--kc_1=%s' % kc1 )
        arguments.append( '--kc_2=%s' % kc2 )
        arguments.append( '--kc_4=%s' % kc4 )
        arguments.append( '--kf=%s' % kf )
        
        if renderer != "Other":
            arguments.append( '--renderer=%s' % renderer )
        
        if preserveLayers != "none":
            arguments.append( '--preserve-layers' ) # Altus 1.8 it is now just a boolean flag
        
        if outputQuality != "":
            arguments.append( '--quality=%s' % outputQuality )
        
        if aovQuality != "none":
            arguments.append( '--filter-aov=%s' % aovQuality )

        if tile:
            arguments.append( '--tile' )
            if tileSize != "":
                arguments.append( '--tile-size=%s' % tileSize )

        if fireFly:
            arguments.append( '--firefly' )

        if forceContinue:
            if self.version < 1.9:
                arguments.append( '--force-continue' )
            else:
                arguments.append( '--force-continue=%s' % forceContinue )

        if ignoreAlpha:
            arguments.append( '--ignore-alpha' )

        if skipFrameRadius:
            arguments.append( '--skip-frame-radius' )

        if singlePass:
            arguments.append( '--single-pass' )

        if force16bitOutput:
            arguments.append( '--out-16bit' )

        if exrCompression:
            arguments.append( '--compression=%s' % self.getEXRCompressionIndex( exrCompression ) )

        fileArgList = []
        
        self.prepFileArgs( fileArgList, rgbfiles, "rgb" )
        self.prepFileArgs( fileArgList, posfiles, "pos" )
        self.prepFileArgs( fileArgList, nrmfiles, "nrm" )
        self.prepFileArgs( fileArgList, visfiles, "vis" )
        self.prepFileArgs( fileArgList, albfiles, "alb" )
        self.prepFileArgs( fileArgList, caufiles, "cau" )
        self.prepFileArgs( fileArgList, hairFiles, "hair" )
        self.prepFileArgs( fileArgList, extraFiles, "extra" )
        self.prepFileArgs( fileArgList, additionalFiles, "additional" )
        
        for args in fileArgList:
            arguments.append( '--%s-%s="%s"' % args )
        
        return " ".join( arguments )

    def getEXRCompressionIndex( self, exrCompression ):
        """
        Converts the exr compression type into the index used by Altus on the command-line.
        :param exrCompression: A string indicating which exr compression to use
        :return: the index of the exr compression
        """
        return self.EXR_COMPRESSIONS.index( exrCompression )
    
    def rreplace( self, s, old, new, occurrence ):
        li = s.rsplit(old, occurrence)
        return new.join(li)
    
    def prepFileArgs( self, fileArgList, fileListStr, basicArg ):
        stereoEnabled = self.GetBooleanPluginInfoEntryWithDefault( "Stereo", False )
        if not fileListStr == "":
            fileList = filter( None, fileListStr.split( ';' ) )
            if stereoEnabled:
                if len(fileList) == 1:
                    mappedFile  = RepositoryUtils.CheckPathMapping( fileList[0] ).replace( "\\", "/" )
                    fileArgList.append( ( basicArg, "stereo", mappedFile ) )
            else:
                if len(fileList) == 2:
                    for idx, file in enumerate( fileList ):
                        mappedFile  = RepositoryUtils.CheckPathMapping( file ).replace( "\\", "/" )
                        fileArgList.append( ( basicArg, str(idx), mappedFile ) )

    # Currently this function is overkill as Altus only supports 1 x GPU device ID.
    # However, Altus in the future have noted they will support multiple GPU devices per instance of Altus,
    # so the generic function below is left intact and we limit the current GPU count <= 1 via the monitor submitter.
    def GetGpuOverrides( self ):
        resultGPUs = []
        
        # If the number of gpus per task is set, then need to calculate the gpus to use.
        gpusPerTask = self.GetIntegerPluginInfoEntryWithDefault( "GPUsPerTask", 0 )
        gpusSelectDevices = self.GetPluginInfoEntryWithDefault( "GPUsSelectDevices", "" )

        if self.OverrideGpuAffinity():
            overrideGPUs = self.GpuAffinity()
            if gpusPerTask == 0 and gpusSelectDevices != "":
                gpus = gpusSelectDevices.split( "," )
                notFoundGPUs = []
                for gpu in gpus:
                    if int( gpu ) in overrideGPUs:
                        resultGPUs.append( gpu )
                    else:
                        notFoundGPUs.append( gpu )
                
                if len( notFoundGPUs ) > 0:
                    self.LogWarning( "The Slave is overriding its GPU affinity and the following GPUs do not match the Slaves affinity so they will not be used: " + ",".join( notFoundGPUs ) )
                if len( resultGPUs ) == 0:
                    self.FailRender( "The Slave does not have affinity for any of the GPUs specified in the job." )
            elif gpusPerTask > 0:
                if gpusPerTask > len( overrideGPUs ):
                    self.LogWarning( "The Slave is overriding its GPU affinity and the Slave only has affinity for " + str( len( overrideGPUs ) ) + " Slaves of the " + str( gpusPerTask ) + " requested." )
                    resultGPUs =  overrideGPUs
                else:
                    resultGPUs = list( overrideGPUs )[:gpusPerTask]
            else:
                resultGPUs = overrideGPUs
        elif gpusPerTask == 0 and gpusSelectDevices != "":
            resultGPUs = gpusSelectDevices.split( "," )

        elif gpusPerTask > 0:
            gpuList = []
            for i in range( ( self.GetThreadNumber() * gpusPerTask ), ( self.GetThreadNumber() * gpusPerTask ) + gpusPerTask ):
                gpuList.append( str( i ) )
            resultGPUs = gpuList
        
        resultGPUs = list( resultGPUs )
        
        return resultGPUs

    ######################################################################
    ## Standard Out Handlers
    ######################################################################
    def HandleStdoutError( self ):
        self.FailRender( self.GetRegexMatch( 0 ) )
        
    def HandleStdoutProgress( self ):
        self.progress = float( self.GetRegexMatch( 1 ) )
        self.updateProgress()

    # Altus 1.8 onwards
    def HandleStdoutProgress2( self ):
        self.progress = float( self.GetRegexMatch( 2 ) )
        self.updateProgress()
        
    def HandleStdoutComplete( self ):
        self.progress = 100
        self.updateProgress()
        
    def HandleStdoutStartFrame( self ):
        self.currFrame = float( self.GetRegexMatch( 1 ) )
        self.SetStatusMessage( "Filtering Frame: %s" % self.GetRegexMatch( 1 ) )

    # Altus 1.8 onwards
    def HandleStdoutStartFrame2( self ):
        self.currFrame = float( self.GetRegexMatch( 2 ) )
        self.SetStatusMessage( "Filtering Frame: %s" % self.GetRegexMatch( 2 ) )
        
    def HandleStdoutClosing( self ):
        self.SetStatusMessage( "Job Complete" )
        
    ######################################################################
    ## Helper Functions
    ######################################################################
    def updateProgress( self ):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        
        if startFrame == endFrame: #single frame
            self.SetProgress( self.progress )
        else: #animation
            overallProgress = ( ( 1.0 / ( endFrame - startFrame + 1 ) ) ) * self.progress
            currentFrameProgress = ( ( ( ( self.currFrame - startFrame ) * 1.0 ) / ( ( ( endFrame - startFrame + 1 ) * 1.0 ) ) ) * 100 )
            self.SetProgress( overallProgress + currentFrameProgress )
