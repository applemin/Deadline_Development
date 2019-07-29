import math

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
    return MaxwellPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Maxwell plugin.
######################################################################
class MaxwellPlugin (DeadlinePlugin):
    Version = 0
    VersionString = ""
    
    MergeJob = False
    MxiSeedFiles = []
    
    RenderingTime = 0.0
    SamplingLevel = 0.0
    
    LocalRendering = False
    LocalTempDirectory = ""
    LocalMxiDirectory = ""
    LocalOutputDirectory = ""
    NetworkMxiDirectory = ""
    NetworkOutputDirectory = ""
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
        self.RenderCanceledCallback += self.RenderCanceled
        self.IsSingleFramesOnlyCallback += self.IsSingleFramesOnly
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
        del self.RenderCanceledCallback
        del self.IsSingleFramesOnlyCallback
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple
        
        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        
        self.HideDosWindow = False
        self.CreateNewConsole = True
        
        # This is needed because the Maxwell render will wait for someone to hit 'Enter' after an error
        # before it exits, which essentially halts the render.
        self.PressEnterDuringRender = True
        
        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( r".*Error:.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( r".*Please check the file exists and its permissions.*" ).HandleCallback += self.HandleError
        
        self.AddStdoutHandlerCallback( r"[Dd]esired rendering time : ([0-9]+\.?[0-9]*)" ).HandleCallback += self.HandleRenderingTime
        self.AddStdoutHandlerCallback( r"[Dd]esired sampling level : ([0-9]+\.?[0-9]*)" ).HandleCallback += self.HandleSamplingLevel
        self.AddStdoutHandlerCallback( r"Extra Sampling: New \(estimated\) global target SL: ([0-9]+\.?[0-9]*)" ).HandleCallback += self.HandleSamplingLevel
        self.AddStdoutHandlerCallback( r"Extra Sampling: New global target SL: ([0-9]+\.?[0-9]*)" ).HandleCallback += self.HandleSamplingLevel
        self.AddStdoutHandlerCallback( r"Time: ([0-9]+)s.*SL of ([0-9]+\.?[0-9]*)" ).HandleCallback += self.HandleProgressSeconds
        self.AddStdoutHandlerCallback( r"Time: ([0-9]+)m([0-9]+)s.*SL of ([0-9]+\.?[0-9]*)" ).HandleCallback += self.HandleProgressMinutes
        self.AddStdoutHandlerCallback( r"Time: ([0-9]+)h([0-9]+)m([0-9]+)s.*SL of ([0-9]+\.?[0-9]*)" ).HandleCallback += self.HandleProgressHours
        self.AddStdoutHandlerCallback( r"Time: ([0-9]+)d([0-9]+)h([0-9]+)m([0-9]+)s.*SL of ([0-9]+\.?[0-9]*)" ).HandleCallback += self.HandleProgressDays
    
    def PreRenderTasks( self ):
        # Reset these values, which are used for determining progress.
        self.RenderingTime = 0.0
        self.SamplingLevel = 0.0
        self.MxiSeedFiles = []
        
        # Get the version we're rendering with.
        self.Version = self.GetIntegerPluginInfoEntryWithDefault( "Version", 2 )
        self.VersionString = str(self.Version)

        renderExecName = self.RenderExecutable()
        maxwellPath = Path.GetDirectoryName( renderExecName ) # Get the directory of the executable for Maxwell that is being used
        maxwellName = "MAXWELL" + self.VersionString + "_ROOT"

        # Set the environment variable to the proper value based on Maxwell Version
        self.LogInfo( "Setting "+ maxwellName +" to " + maxwellPath )
        self.SetEnvironmentVariable( maxwellName, maxwellPath ) # Maxwell version path set to directory of executable being used
        
        # Determine if this is a merge job or not.
        self.MergeJob = self.GetBooleanPluginInfoEntryWithDefault( "MergeJob", False )
        
        # Set up local rendering if necessary.
        self.LocalTempDirectory = ""
        self.LocalMxiDirectory = ""
        self.LocalOutputDirectory = ""
        
        self.NetworkMxiDirectory = ""
        self.NetworkOutputDirectory = ""
        
        self.LocalRendering = self.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False )
        if self.LocalRendering:
            self.LocalTempDirectory = self.CreateTempDirectory( "maxwellOutput" )
            self.LocalMxiDirectory = Path.Combine( self.LocalTempDirectory, "MXI" )
            self.LocalOutputDirectory = Path.Combine( self.LocalTempDirectory, "Output" )
            
            # Create the temporary local directories.
            Directory.CreateDirectory( self.LocalMxiDirectory )
            Directory.CreateDirectory( self.LocalOutputDirectory )
            
            # If trying to resume, we need to check if there is a network MXI file we should resume from.
            if self.GetBooleanPluginInfoEntryWithDefault( "ResumeFromMxiFile", False ):
                mxiFile = self.GetPluginInfoEntryWithDefault( "MxiFile", "" ).strip()
                mxiFile = RepositoryUtils.CheckPathMapping( mxiFile )
                mxiFile = self.FixPathSeparators( mxiFile )
                
                # If there is an MXI file to resume from, copy it locally so that we can resume from it.
                if len( mxiFile ) > 0:
                    # If we are doing a co-op render, we need to look for the specific seed file.
                    if self.GetBooleanPluginInfoEntryWithDefault( "CoopRendering", False ):
                        seed = "1"
                        
                        # If it's a single co-op job, get the seed from the task file.
                        if self.GetBooleanPluginInfoEntryWithDefault( "SingleCoopJob", False ):
                            seed = str(self.GetStartFrame())
                        else:
                            seed = self.GetPluginInfoEntry( "CoopSeed" )
                            
                        padding = StringUtils.ToZeroPaddedString( int(seed), 4, False )
                        directory = Path.GetDirectoryName( mxiFile )
                        filename = Path.GetFileNameWithoutExtension( mxiFile )
                        extension = Path.GetExtension( mxiFile )
                        
                        mxiPadding = ""
                        if not self.GetBooleanPluginInfoEntry( "SingleFile" ):
                            startFrame = self.GetStartFrame()
                            mxiPadding = "."+StringUtils.ToZeroPaddedString( int(startFrame), 4, False )
                        
                        mxiFile = Path.Combine( directory, filename + "_s" + padding + mxiPadding + extension )
                    
                    if File.Exists( mxiFile ):
                        self.LogInfo( "Copying MXI file " + mxiFile + " locally to try and resume" )
                        localMxiFile = Path.Combine( self.LocalMxiDirectory, Path.GetFileName( mxiFile ) )
                        File.Copy( mxiFile, localMxiFile, True )
                

    def IsSingleFramesOnly( self ):
        # Only work on one msx file at a time.
        return True
    
    ## Called by Deadline to get the render executable.
    def RenderExecutable( self ):
        exeType = "Render"
        if self.MergeJob:
            exeType = "Merge"
        
        executable = ""
        exeList = self.GetConfigEntry( "Maxwell" + self.VersionString + "_" + exeType + "Executable" )
        
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        if(SystemUtils.IsRunningOnWindows()):
            if build == "32bit":
                executable = FileUtils.SearchFileListFor32Bit( exeList )
                if( executable == "" ):
                    self.LogWarning( "32 bit Maxwell " + self.VersionString + " " + exeType + " executable was not found in the semicolon separated list \"" + exeList + "\". Checking for any executable that exists instead." )
            elif build == "64bit":
                executable = FileUtils.SearchFileListFor64Bit( exeList )
                if( executable == "" ):
                    self.LogWarning( "64 bit Maxwell " + self.VersionString + " " + exeType + " executable was not found in the semicolon separated list \"" + exeList + "\". Checking for any executable that exists instead." )
            
        if( executable == "" ):
            executable = FileUtils.SearchFileList( exeList )
            if( executable == "" ):
                self.FailRender( "Maxwell " + self.VersionString + " " + exeType + " executable was not found in the semicolon separated list \"" + exeList + "\". The path to the " + exeType + " executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return executable
    
    ## Called by Deadline to get the render arguments.
    def RenderArgument( self ):
        arguments = ""
        if not self.MergeJob:
            coopRendering = self.GetBooleanPluginInfoEntryWithDefault( "CoopRendering", False )
            coopJobs = self.GetIntegerPluginInfoEntryWithDefault( "CoopJobs", 0 )
            
            sceneFile = self.GetPluginInfoEntry( "MaxwellFile" )
            sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
            sceneFile = self.FixPathSeparators( sceneFile )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "SeparateFiles", False ):
                startFrame = self.GetStartFrame()
                directory = Path.GetDirectoryName( sceneFile )
                filename = Path.GetFileNameWithoutExtension( sceneFile )
                extension = Path.GetExtension( sceneFile )
                paddingSize = self.GetIntegerPluginInfoEntryWithDefault( "AnimationPadding", 4 )
                padding = "."+StringUtils.ToZeroPaddedString( int(startFrame), paddingSize, False )
                sceneFile = Path.Combine( directory, filename + padding + extension )
            
            arguments = " -mxs:\"" + sceneFile + "\" -nowait"
            
            # Hide the console (version 2 and later).
            arguments += " -hide"
            
            # If rendering a single file only, don't include the animation options.
            mxiPadding = ""
            if self.GetBooleanPluginInfoEntry( "SingleFile" ):
                self.LogInfo( "This is a single Maxwell file job, not including animation option." )
            elif not self.GetBooleanPluginInfoEntryWithDefault( "SeparateFiles", False ):
                startFrame = self.GetStartFrame()
                mxiPadding = "."+StringUtils.ToZeroPaddedString( int(startFrame), 4, False )
                
                arguments += " -animation:" + str(startFrame) + "-" + str(startFrame)
            
            # Set the threads (0 uses all threads).
            arguments += " -threads:" + self.GetPluginInfoEntryWithDefault( "RenderThreads", "0" )
            
            # Check overrides.
            if self.GetBooleanPluginInfoEntryWithDefault( "OverrideTime", False ):
                arguments += " -time:" + self.GetPluginInfoEntry( "OverrideTimeValue" )
                
            if self.GetBooleanPluginInfoEntryWithDefault( "OverrideSampling", False ):
                samplingValue = self.GetFloatPluginInfoEntry( "OverrideSamplingValue" )
                
                # If this is a co-op render, check if we need to adjust the sampling level accordingly.
                if coopRendering and self.GetBooleanPluginInfoEntryWithDefault( "AutoComputeSampling", False ):
                    samplingValue = ( math.log( ( (math.exp( samplingValue * math.log(1.5) ) - 1.0 ) / float(coopJobs) ) + 1.0 )) / math.log(1.5)
                
                samplingValue = round(samplingValue, 2)
                arguments += " -sampling:" + str(samplingValue)
            
            # Check if extra sampling settings are being overridden.
            if self.GetBooleanPluginInfoEntryWithDefault( "OverrideExtraSampling", False ):
                if self.GetBooleanPluginInfoEntry( "ExtraSamplingEnabled" ):
                    arguments += " -extrasamplingenabled:yes"
                    
                    extraSamplingValue = self.GetFloatPluginInfoEntry("ExtraSamplingLevel")
                    
                    # If this is a co-op render, check if we need to adjust the sampling level accordingly.
                    if coopRendering and self.GetBooleanPluginInfoEntryWithDefault( "AutoComputeSampling", False ):
                        extraSamplingValue = ( math.log( ( (math.exp( extraSamplingValue * math.log(1.5) ) - 1.0 ) / float(coopJobs) ) + 1.0 )) / math.log(1.5)
                    
                    extraSamplingValue = round(extraSamplingValue, 2)
                    
                    arguments += " -extrasamplingsl:" + str(extraSamplingValue)
                    
                    extraSamplingMask = self.GetPluginInfoEntry( "ExtraSamplingMask" )
                    if extraSamplingMask == "Custom Alpha":
                        arguments += " -extrasamplingmask:0"
                        
                        customAlphaName = self.GetPluginInfoEntry("ExtraSamplingCustomAlphaName")
                        arguments += " -extrasamplingcustomalpha:" + customAlphaName
                        
                    elif extraSamplingMask == "Alpha":
                        arguments += " -extrasamplingmask:1"
                        
                    elif extraSamplingMask == "Bitmap":
                        arguments += " -extrasamplingmask:2"
                        
                        bitmapFile = self.GetPluginInfoEntry("ExtraSamplingBitmapFile").strip()
                        bitmapFile = RepositoryUtils.CheckPathMapping( bitmapFile )
                        bitmapFile = self.FixPathSeparators( bitmapFile )
                        arguments += " -extrasamplinguserbitmap:" + bitmapFile
                        
                    if self.GetBooleanPluginInfoEntry( "ExtraSamplingInvertMask" ):
                        arguments += " -extrasamplinginvert:yes"
                    else:
                        arguments += " -extrasamplinginvert:no"                    
                else:
                    arguments += " -extrasamplingenabled:no"
            
            # Use interactive license if necessary
            slaveFound = False
            thisSlave = self.GetSlaveName().lower()
            interactiveSlaves = self.GetConfigEntryWithDefault( "InteractiveSlaves", "" ).split( ',' )
            for slave in interactiveSlaves:
                if slave.lower().strip() == thisSlave:
                    self.LogInfo( "This slave is in the interactive license list - an interactive license will be used instead of a render license" )
                    slaveFound = True
                    break
            
            if not slaveFound:
                arguments += " -node"
                
            # Set verbosity (version 2 and later).
            verbosityValue = "4"
            
            verbosity = self.GetPluginInfoEntryWithDefault( "Verbosity", "All" )
            if verbosity == "None":
                verbosityValue = "0"
            elif verbosity == "Errors":
                verbosityValue = "1"
            elif verbosity == "Warnings":
                verbosityValue = "2"
            elif verbosity == "Info":
                verbosityValue = "3"
            elif verbosity == "All":
                verbosityValue = "4"
            
            arguments += " -verbose:" + verbosityValue
            
            # Check if this is part of a co-op render.
            outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip()
            outputFile = RepositoryUtils.CheckPathMapping( outputFile )
            outputFile = self.FixPathSeparators( outputFile )
            
            mxiFile = self.GetPluginInfoEntryWithDefault( "MxiFile", "" ).strip()
            mxiFile = RepositoryUtils.CheckPathMapping( mxiFile )
            mxiFile = self.FixPathSeparators( mxiFile )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "AppendFrame", False ):
                padding = StringUtils.ToZeroPaddedString( int(self.GetStartFrame()), 4, False )
                if len(outputFile) >0: 
                    directory = Path.GetDirectoryName( outputFile )
                    filename = Path.GetFileNameWithoutExtension( outputFile )
                    extension = Path.GetExtension( outputFile )
                    outputFile = Path.Combine( directory, filename +"."+ padding + extension ) 
                
                if len(mxiFile) >0:
                    directory = Path.GetDirectoryName( mxiFile )
                    filename = Path.GetFileNameWithoutExtension( mxiFile )
                    extension = Path.GetExtension( mxiFile )
                    mxiFile = Path.Combine( directory, filename +"."+ padding + extension ) 
            
            if coopRendering:
                seed = "1"
                
                # If it's a single co-op job, get the seed from the task file.
                if self.GetBooleanPluginInfoEntryWithDefault( "SingleCoopJob", False ):
                    seed = str(self.GetStartFrame())
                else:
                    seed = self.GetPluginInfoEntry( "CoopSeed" )
                    
                padding = StringUtils.ToZeroPaddedString( int(seed), 4, False )
                
                if len( outputFile ) > 0:
                    directory = Path.GetDirectoryName( outputFile )
                    filename = Path.GetFileNameWithoutExtension( outputFile )
                    extension = Path.GetExtension( outputFile )
                    outputFile = Path.Combine( directory, filename + "_s" + padding + mxiPadding + extension )
                
                directory = Path.GetDirectoryName( mxiFile )
                filename = Path.GetFileNameWithoutExtension( mxiFile )
                extension = Path.GetExtension( mxiFile )
                mxiFile = Path.Combine( directory, filename + "_s" + padding + mxiPadding + extension )
                
                arguments += " -idcpu:" + seed
                self.LogInfo( "This is part of a cooperative render, rendering with seed " + seed )
                
            else:
                if len( mxiFile ) > 0:
                    directory = Path.GetDirectoryName( mxiFile )
                    filename = Path.GetFileNameWithoutExtension( mxiFile )
                    extension = Path.GetExtension( mxiFile )
                    mxiFile = Path.Combine( directory, filename + mxiPadding + extension )
            
            # Set the output file.
            if len( outputFile ) > 0:
                if self.LocalRendering:
                    localOutputFile = Path.Combine( self.LocalOutputDirectory, Path.GetFileName( outputFile ) )
                    self.NetworkOutputDirectory = Path.GetDirectoryName( outputFile )
                    
                    self.LogInfo( "Saving local output for this job to " + localOutputFile )
                    self.LogInfo( "When finished, local output will be copied to " + outputFile )
                    
                    arguments += " -output:\"" + localOutputFile + "\""
                    arguments += " -copyimage:\"" + outputFile + "\""
                    
                else:
                    self.LogInfo( "Saving output for this job to " + outputFile )
                    arguments += " -output:\"" + outputFile + "\""
            
            # Set the mxi file.
            if len( mxiFile ) > 0:
                tryToResume = self.GetBooleanPluginInfoEntryWithDefault( "ResumeFromMxiFile", False )
                
                if self.LocalRendering:
                    localMxiFile = Path.Combine( self.LocalMxiDirectory, Path.GetFileName( mxiFile ) )
                    self.NetworkMxiDirectory = Path.GetDirectoryName( mxiFile )
                    
                    self.LogInfo( "Saving local MXI for this job to " + localMxiFile )
                    self.LogInfo( "When finished, local MXI will be copied to " + mxiFile )
                    
                    arguments += " -mxi:\"" + localMxiFile + "\""
                    arguments += " -copymxi:\"" + mxiFile + "\""
                
                    # This isn't supported with local rendering, since the local mxi file will never exist.
                    #if tryToResume:
                    #	self.LogWarning( "Cannot try to resume from existing MXI file when Local Rendering is enabled" )
                else:
                    self.LogInfo( "Saving MXI for this job to " + mxiFile )
                    arguments += " -mxi:\"" + mxiFile + "\""
                
                # See if we should try to resume from the mxi file. Note that the -trytoresume
                # feature was introduced in 2.5.1, so they need to be at least running that version.
                if tryToResume:
                    arguments += " -trytoresume"
            
            if self.LocalRendering and (len( outputFile ) > 0 or len( mxiFile ) > 0):
                arguments += " -removeaftercopy:yes"
            
            if not self.GetPluginInfoEntryWithDefault( "Camera", "" ) == "":
                arguments += " -camera:" + self.GetPluginInfoEntryWithDefault( "Camera", "" )
            
            # Finally, append the user-specified command line options.
            arguments += " " + self.GetPluginInfoEntryWithDefault( "CommandLineOptions", "" )
        else:
            mxiFile = self.GetPluginInfoEntryWithDefault( "MxiFile", "" ).strip()
            mxiFile = RepositoryUtils.CheckPathMapping( mxiFile )
            mxiFile = self.FixPathSeparators( mxiFile )
            
            outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip()
            outputFile = RepositoryUtils.CheckPathMapping( outputFile )
            outputFile = self.FixPathSeparators( outputFile )
            
            coopJobs = self.GetIntegerPluginInfoEntryWithDefault( "CoopJobs", 0 )
            
            self.MxiSeedFiles = []
            if self.GetBooleanPluginInfoEntry( "SingleFile" ):
                for seed in range( 1, coopJobs + 1 ):
                    padding = StringUtils.ToZeroPaddedString( seed, 4, False )
                    directory = Path.GetDirectoryName( mxiFile )
                    filename = Path.GetFileNameWithoutExtension( mxiFile )
                    extension = Path.GetExtension( mxiFile )
                    
                    seedFile = Path.Combine( directory, filename + "_s" + padding + extension )
                    if File.Exists( seedFile ):
                        self.MxiSeedFiles.append( seedFile )
                        arguments += " -source:\"" + seedFile + "\""
                    else:
                        if self.GetBooleanPluginInfoEntryWithDefault( "FailOnMissingFiles", True ):
                            self.FailRender( "Cannot perform merge because seed file \"" + seedFile + "\" is missing" )
                        else:
                            self.LogWarning( "Seed file \"" + seedFile + "\" is missing" )
                    
                if len(self.MxiSeedFiles) == 0:
                    self.FailRender( "Cannot perform merge because all seed files are missing" )
                    
                arguments += " -target:\"" + mxiFile + "\""
                
                if len( outputFile ) > 0:
                    arguments += " -image:\"" + outputFile + "\""
                    arguments += " -extractchannels:\"" + outputFile + "\""
            else:
                startFrame = self.GetStartFrame()
                
                filenamePadding = "."+StringUtils.ToZeroPaddedString( int(startFrame), 4, False )
                
                
                for seed in range( 1, coopJobs + 1 ):
                    padding = StringUtils.ToZeroPaddedString( seed, 4, False )
                    directory = Path.GetDirectoryName( mxiFile )
                    filename = Path.GetFileNameWithoutExtension( mxiFile )
                    extension = Path.GetExtension( mxiFile )
                    
                    seedFile = Path.Combine( directory, filename + "_s" + padding + filenamePadding + extension )
                    if File.Exists( seedFile ):
                        self.MxiSeedFiles.append( seedFile )
                        arguments += " -source:\"" + seedFile + "\""
                    else:
                        if self.GetBooleanPluginInfoEntryWithDefault( "FailOnMissingFiles", True ):
                            self.FailRender( "Cannot perform merge because seed file \"" + seedFile + "\" is missing" )
                        else:
                            self.LogWarning( "Seed file \"" + seedFile + "\" is missing" )
                    
                if len(self.MxiSeedFiles) == 0:
                    self.FailRender( "Cannot perform merge because all seed files are missing" )
                    
                directory = Path.GetDirectoryName( mxiFile )
                filename = Path.GetFileNameWithoutExtension( mxiFile )
                extension = Path.GetExtension( mxiFile )
                
                currMxiFile = Path.Combine( directory, filename + filenamePadding + extension )
                arguments += " -target:\"" + currMxiFile + "\""
                
                if len( outputFile ) > 0:
                    directory = Path.GetDirectoryName( outputFile )
                    filename = Path.GetFileNameWithoutExtension( outputFile )
                    extension = Path.GetExtension( outputFile )
                    
                    currOutputFile = Path.Combine( directory, filename + filenamePadding + extension )
                    arguments += " -image:\"" + currOutputFile + "\""
                    arguments += " -extractchannels:\"" + currOutputFile + "\""
                    
        return arguments
    
    def PostRenderTasks( self ):
        if self.MergeJob and self.GetBooleanPluginInfoEntryWithDefault( "DeleteFiles", False ):
            outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip()
            outputFile = RepositoryUtils.CheckPathMapping( outputFile )
            outputFile = self.FixPathSeparators( outputFile )
            
            coopJobs = self.GetIntegerPluginInfoEntryWithDefault( "CoopJobs", 0 )
            if self.GetBooleanPluginInfoEntry( "SingleFile" ):
                self.LogInfo( "Deleting intermediate files" )
                for seedFile in self.MxiSeedFiles:
                    self.DeleteSeedOutputFile( seedFile )
                
                if len( outputFile ) > 0:
                    for seed in range( 1, coopJobs + 1 ):
                        padding = StringUtils.ToZeroPaddedString( seed, 4, False )
                        directory = Path.GetDirectoryName( outputFile )
                        filename = Path.GetFileNameWithoutExtension( outputFile )
                        extension = Path.GetExtension( outputFile )
                        
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_material_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_object_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_alpha_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_fresnel_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_normals_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_position_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_roughness_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_zbuffer_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_motion_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_shadow_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_normal_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_uv_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_deep_" + padding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_alpha_custom_" + padding + extension ) )
            else:
                startFrame = self.GetStartFrame()
                
                filenamePadding = "."+StringUtils.ToZeroPaddedString( int(startFrame), 4, False )
                self.LogInfo( "Deleting intermediate files for frame " + str(startFrame) )
                
                for seedFile in self.MxiSeedFiles:
                    self.DeleteSeedOutputFile( seedFile )
                
                if len( outputFile ) > 0:
                    for seed in range( 1, coopJobs + 1 ):
                        padding = StringUtils.ToZeroPaddedString( seed, 4, False )
                        directory = Path.GetDirectoryName( outputFile )
                        filename = Path.GetFileNameWithoutExtension( outputFile )
                        extension = Path.GetExtension( outputFile )
                        
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_material_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_object_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_alpha_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_fresnel_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_normals_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_position_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_roughness_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_zbuffer_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_motion_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_shadow_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_normal_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_uv_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_deep_" + padding + filenamePadding + extension ) )
                        self.DeleteSeedOutputFile( Path.Combine( directory, filename + "_s_alpha_custom_" + padding + filenamePadding + extension ) )

    def DeleteSeedOutputFile( self, seedOutputFile ):
        if File.Exists( seedOutputFile ):
            self.LogInfo( "  Deleting " + seedOutputFile )
            try:
                File.Delete( seedOutputFile )
            except Exception as e:
                self.LogWarning( "  FAILED to delete file: %s" % e.Message )

    def RenderCanceled( self ):
        if self.LocalRendering:
            if self.NetworkMxiDirectory != "":
                self.LogInfo( "Render canceled, moving local mxi to " + self.NetworkMxiDirectory )
                self.VerifyAndMoveDirectory( self.LocalMxiDirectory, self.NetworkMxiDirectory, False, -1 )
                
            if self.NetworkOutputDirectory != "":
                self.LogInfo( "Render canceled, moving local output to " + self.NetworkOutputDirectory )
                self.VerifyAndMoveDirectory( self.LocalOutputDirectory, self.NetworkOutputDirectory, False, -1 )
    
    def HandleError( self ):
        self.FailRender( self.GetRegexMatch( 0 ) )
    
    def HandleRenderingTime( self ):
        self.RenderingTime = float(self.GetRegexMatch( 1 )) * 60.0 # convert to seconds
    
    def HandleSamplingLevel( self ):
        self.SamplingLevel = float(self.GetRegexMatch( 1 ))
    
    def HandleProgressSeconds( self ):
        currentRenderingTime = float(self.GetRegexMatch( 1 ))
        currentSamplingLevel = float(self.GetRegexMatch( 2 ))
        self.CalculateProgress( currentRenderingTime, currentSamplingLevel )
        
    def HandleProgressMinutes( self ):
        currentRenderingTime = (float(self.GetRegexMatch( 1 )) * 60.0) + float(self.GetRegexMatch( 2 ))
        currentSamplingLevel = float(self.GetRegexMatch( 3 ))
        self.CalculateProgress( currentRenderingTime, currentSamplingLevel )
    
    def HandleProgressHours( self ):
        currentRenderingTime = (float(self.GetRegexMatch( 1 )) * 3600.0) + (float(self.GetRegexMatch( 2 )) * 60.0) + float(self.GetRegexMatch( 3 ))
        currentSamplingLevel = float(self.GetRegexMatch( 4 ))
        self.CalculateProgress( currentRenderingTime, currentSamplingLevel )
        
    def HandleProgressDays( self ):
        currentRenderingTime = (float(self.GetRegexMatch( 1 )) * 86400.0) + (float(self.GetRegexMatch( 2 )) * 3600.0) + (float(self.GetRegexMatch( 3 )) * 60.0) + float(self.GetRegexMatch( 4 ))
        currentSamplingLevel = float(self.GetRegexMatch( 5 ))
        self.CalculateProgress( currentRenderingTime, currentSamplingLevel )
    
    def CalculateProgress( self, currentRenderingTime, currentSamplingLevel ):
        renderingTimeProgress = 0.0
        if self.RenderingTime > 0:
            renderingTimeProgress = ((currentRenderingTime*100.0) / self.RenderingTime)
        
        samplingLevelProgress = 0.0
        if self.SamplingLevel > 0:
            samplingLevelProgress = ((currentSamplingLevel*100.0) / self.SamplingLevel)
        
        if renderingTimeProgress > samplingLevelProgress:
            self.SetProgress( float(round( renderingTimeProgress, 1 )))
        else:
            self.SetProgress( float(round( samplingLevelProgress, 1 )))
        
        # round to 1 to stop progress hovering at 0.01% as a "task render status" string message
        self.SetStatusMessage( "Rendering time progress: " + str(round( renderingTimeProgress, 1 )) + "%  Sampling level progress: " + str(round( samplingLevelProgress, 1 )) + "%" )
    
    def FixPathSeparators( self, path ):
        if SystemUtils.IsRunningOnWindows():
            path = path.replace( "/", "\\" )
            if path.startswith( "\\" ) and not path.startswith( "\\\\" ):
                path = "\\" + path
        else:
            path = path.replace( "\\", "/" )
        
        return path
