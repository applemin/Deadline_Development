from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return RVIOPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Shake plugin.
######################################################################
class RVIOPlugin (DeadlinePlugin):
    
    def __init__( self ):
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
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        
        # Set the process specific settings.
        self.StdoutHandling = True
        self.PopupHandling = True
        
        # Add stdout handlers.
        self.AddStdoutHandlerCallback( "\\(([0-9]+.[0-9]*)% done\\)" ).HandleCallback += self.HandleProgress
    
    def RenderExecutable( self ):
        renderExeList = self.GetConfigEntry( "RVIO_RenderExecutable" )
        renderExe = ""
        
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        if SystemUtils.IsRunningOnWindows():
            if build == "32bit":
                self.LogInfo( "Enforcing 32 bit build of RVIO" )
                renderExe = FileUtils.SearchFileListFor32Bit( renderExeList )
                if renderExe == "":
                    self.LogWarning( "32 bit RVIO render executable was not found in the semicolon separated list \"" + renderExeList + "\". Checking for any executable that exists instead." )
            elif build == "64bit":
                self.LogInfo( "Enforcing 64 bit build of RVIO" )
                renderExe = FileUtils.SearchFileListFor64Bit( renderExeList )
                if renderExe == "":
                    self.LogWarning( "64 bit RVIO render executable was not found in the semicolon separated list \"" + renderExeList + "\". Checking for any executable that exists instead." )
            
        if renderExe == "":
            self.LogInfo( "Not enforcing a build of RVIO" )
            renderExe = FileUtils.SearchFileList( renderExeList )
            if renderExe == "":
                self.FailRender( "RVIO render executable was not found in the semicolon separated list \"" + renderExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return renderExe
    
    def GetSequencePath( self, filename, startFrame, endFrame ):
        if startFrame < endFrame:
            currPadding = FrameUtils.GetFrameStringFromFilename( filename )
            paddingSize = len( currPadding )
            if paddingSize > 0:
                #sequencePart = str(startFrame) + "-" + str(endFrame) + "#"
                
                # Use the @ symbol so that we can support padding of different sizes.
                padding = "@"
                while len(padding) < paddingSize:
                    padding = padding + "@"
                sequencePart = str(startFrame) + "-" + str(endFrame) + padding
                
                filename = FrameUtils.SubstituteFrameNumber( filename, sequencePart )
        
        return filename
    
    def RenderArgument( self ):
        arguments = ""
        
        layerCount = self.GetIntegerPluginInfoEntry( "LayerCount" )
        if layerCount <= 0:
            self.FailRender( "No intput layers specified" )
        
        for index in range( 0, layerCount ):
            name = self.GetPluginInfoEntry( "Layer" + str(index) + "Name" )
            self.LogInfo( "Processing layer: " + name )
            
            # Layers are surrounded with square brackets.
            arguments += " ["
            
            # Get the first input file.
            source1File = self.GetPluginInfoEntry( "Layer" + str(index) + "Input1" )
            source1StartFrame = self.GetIntegerPluginInfoEntry( "Layer" + str(index) + "Input1StartFrame" )
            source1EndFrame = self.GetIntegerPluginInfoEntry( "Layer" + str(index) + "Input1EndFrame" )
            
            source1File = self.GetSequencePath( source1File, source1StartFrame, source1EndFrame )
            source1File = RepositoryUtils.CheckPathMapping( source1File ).replace( "\\", "/" )
            if SystemUtils.IsRunningOnWindows() and source1File.startswith( "/" ) and not source1File.startswith( "//" ):
                source1File = "/" + source1File
            
            arguments += " \"" + source1File + "\""
            
            # Check if there is a second input file.
            source2File = self.GetPluginInfoEntryWithDefault( "Layer" + str(index) + "Input2", "" )
            if source2File != "":
                source2StartFrame = self.GetIntegerPluginInfoEntry( "Layer" + str(index) + "Input2StartFrame" )
                source2EndFrame = self.GetIntegerPluginInfoEntry( "Layer" + str(index) + "Input2EndFrame" )
                
                source2File = self.GetSequencePath( source2File, source2StartFrame, source2EndFrame )
                source2File = RepositoryUtils.CheckPathMapping( source2File ).replace( "\\", "/" )
                if SystemUtils.IsRunningOnWindows() and source2File.startswith( "/" ) and not source2File.startswith( "//" ):
                    source2File = "/" + source2File
                
                arguments += " \"" + source2File + "\""
            
            # Check if there are any audio files.
            audioFiles = self.GetPluginInfoEntryWithDefault( "Layer" + str(index) + "AudioFiles", "" )
            if audioFiles != "":
                for audioFile in audioFiles.split( "," ):
                    #arguments += " \"" + RepositoryUtils.CheckPathMapping( audioFile ).replace( "\\", "/" ) + "\""
                    audioFile = RepositoryUtils.CheckPathMapping( audioFile ).replace( "\\", "/" )
                    if SystemUtils.IsRunningOnWindows() and audioFile.startswith( "/" ) and not audioFile.startswith( "//" ):
                        audioFile = "/" + audioFile
                    arguments += " \"" + audioFile + "\""
                    
            # Check if there are any per-layer overrides.
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverridePixelAspectRatio", False ):
                arguments += " -pa " + self.GetPluginInfoEntry( "Layer" + str(index) + "PixelAspectRatio" )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverrideRangeOffset", False ):
                arguments += " -ro " + self.GetPluginInfoEntry( "Layer" + str(index) + "RangeOffset" )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverrideFPS", False ):
                arguments += " -fps " + self.GetPluginInfoEntry( "Layer" + str(index) + "FPS" )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverrideAudioOffset", False ):
                arguments += " -ao " + self.GetPluginInfoEntry( "Layer" + str(index) + "AudioOffset" )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverrideStereoOffset", False ):
                arguments += " -so " + self.GetPluginInfoEntry( "Layer" + str(index) + "StereoOffset" )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverrideVolume", False ):
                arguments += " -volume " + self.GetPluginInfoEntry( "Layer" + str(index) + "Volume" )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverrideFileLut", False ):
                arguments += " -flut \"" + self.GetPluginInfoEntry( "Layer" + str(index) + "FileLut" ) + "\""
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverrideLookLut", False ):
                arguments += " -llut \"" + self.GetPluginInfoEntry( "Layer" + str(index) + "LookLut" ) + "\""
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverridePreCacheLut", False ):
                arguments += " -pclut \"" + self.GetPluginInfoEntry( "Layer" + str(index) + "PreCacheLut" ) + "\""
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverrideChannels", False ):
                arguments += " -cmap \"" + self.GetPluginInfoEntry( "Layer" + str(index) + "Channels" ) + "\""
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverrideCrop", False ):
                arguments += " -crop " + self.GetPluginInfoEntry( "Layer" + str(index) + "CropX0" ) + " " + self.GetPluginInfoEntry( "Layer" + str(index) + "CropY0" ) + " " + self.GetPluginInfoEntry( "Layer" + str(index) + "CropX1" ) + " " + self.GetPluginInfoEntry( "Layer" + str(index) + "CropY1" )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "OverrideUnCrop", False ):
                arguments += " -crop " + self.GetPluginInfoEntry( "Layer" + str(index) + "UnCropW" ) + " " + self.GetPluginInfoEntry( "Layer" + str(index) + "UnCropH" ) + " " + self.GetPluginInfoEntry( "Layer" + str(index) + "UnCropX" ) + " " + self.GetPluginInfoEntry( "Layer" + str(index) + "UnCropY" )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Layer" + str(index) + "DisableAudio", False ):
                arguments += " -noMovieAudio"
            
            # Add the closing bracket.
            arguments += " ]"
        
        # Enable verbosity, and write stderr to stdout.
        arguments += " -v -err-to-out"
        
        # Check if there are any additional overrides.
        if self.GetBooleanPluginInfoEntryWithDefault( "InputConvertLog", False ):
            arguments += " -inlog"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "InputConvertSRGB", False ):
            arguments += " -insrgb"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "InputConvert709", False ):
            arguments += " -in709"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "InputPremultiply", False ):
            arguments += " -inpremult"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "InputUnpremultiply", False ):
            arguments += " -inunpremult"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "InputFlip", False ):
            arguments += " -flip"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "InputFlop", False ):
            arguments += " -flop"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "BestQuality", False ):
            arguments += " -q"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "NoPrerender", False ):
            arguments += " -noprerender"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "InputOverrideGamma", False ):
            arguments += " -ingamma " + self.GetPluginInfoEntry( "InputGamma" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "InputOverrideExposure", False ):
            arguments += " -exposure " + self.GetPluginInfoEntry( "InputExposure" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "InputOverrideScale", False ):
            arguments += " -scale " + self.GetPluginInfoEntry( "InputScale" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "InputOverrideResize", False ):
            arguments += " -resize " + self.GetPluginInfoEntry( "InputResizeWidth" )
            
            resizeHeight = self.GetPluginInfoEntry( "InputResizeHeight" )
            if resizeHeight != "0":
                arguments += " " + resizeHeight
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideResample", False ):
            arguments += " -resampleMethod \"" + self.GetPluginInfoEntry( "Resample" ) + "\""
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideThreads", False ):
            arguments += " -rthreads " + self.GetPluginInfoEntry( "Threads" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideLeaderFrames", False ):
            arguments += " -leaderframes " + self.GetPluginInfoEntry( "LeaderFrames" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideInputChannels", False ):
            arguments += " -inchannelmap " + self.GetPluginInfoEntry( "InputChannels" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideFlags", False ):
            arguments += " -flags " + self.GetPluginInfoEntry( "Flags" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideInitScript", False ):
            arguments += " -init " + self.GetPluginInfoEntry( "InitScript" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideLeaderScript", False ):
            arguments += " -leader " + self.GetPluginInfoEntry( "LeaderScript" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideOverlayScript", False ):
            arguments += " -overlay " + self.GetPluginInfoEntry( "OverlayScript" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputConvertLog", False ):
            arguments += " -outlog"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputConvertSRGB", False ):
            arguments += " -outsrgb"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputConvert709", False ):
            arguments += " -out709"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputPremultiply", False ):
            arguments += " -outpremult"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputUnpremultiply", False ):
            arguments += " -outunpremult"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputStereo", False ):
            arguments += " -outstereo"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputTimeFromRV", False ):
            arguments += " -tio"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideFPS", False ):
            arguments += " -outfps " + self.GetPluginInfoEntry( "OutputFPS" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideResolution", False ):
            arguments += " -outres " + self.GetPluginInfoEntry( "OutputResolutionWidth" ) + " " + self.GetPluginInfoEntry( "OutputResolutionHeight" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideGamma", False ):
            arguments += " -outgamma " + self.GetPluginInfoEntry( "OutputGamma" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideFormat", False ):
            arguments += " -outformat " + self.GetPluginInfoEntry( "OutputFormatBits" ) + " \"" + self.GetPluginInfoEntry( "OutputFormat" ) + "\""
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideCodecQuality", False ):
            arguments += " -quality " + self.GetPluginInfoEntry( "OutputCodecQuality" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideCodec", False ):
            arguments += " -codec \"" + self.GetPluginInfoEntry( "OutputCodec" ) + "\""
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideKeyInterval", False ):
            arguments += " -outkeyinterval " + self.GetPluginInfoEntry( "OutputKeyInterval" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideDataRate", False ):
            arguments += " -outdatarate " + self.GetPluginInfoEntry( "OutputDataRate" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideDLut", False ):
            arguments += " -dlut \"" + self.GetPluginInfoEntry( "OutputDLut" ) + "\""
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideChannels", False ):
            arguments += " -outchannelmap " + self.GetPluginInfoEntry( "OutputChannels" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideTimeRange", False ):
            arguments += " -t \"" + self.GetPluginInfoEntry( "OutputTimeRange" ) + "\""
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideComment", False ):
            arguments += " -comment \"" + self.GetPluginInfoEntry( "OutputComment" ) + "\""
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OutputOverrideCopyright", False ):
            arguments += " -copyright \"" + self.GetPluginInfoEntry( "OutputCopyright" ) + "\""
        
        if self.GetBooleanPluginInfoEntryWithDefault( "AudioOverrideCodec", False ):
            arguments += " -audiocodec " + self.GetPluginInfoEntry( "AudioCodec" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "AudioOverrideRate", False ):
            arguments += " -audiorate " + self.GetPluginInfoEntry( "AudioRate" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "AudioOverrideFormat", False ):
            arguments += " -audioformat " + self.GetPluginInfoEntry( "AudioFormatBits" ) + " \"" + self.GetPluginInfoEntry( "AudioFormat" ) + "\""
        
        if self.GetBooleanPluginInfoEntryWithDefault( "AudioOverrideQuality", False ):
            arguments += " -audioquality " + self.GetPluginInfoEntry( "AudioQuality" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "AudioOverrideChannels", False ):
            arguments += " -audiochannels " + self.GetPluginInfoEntry( "AudioChannels" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "ExrNoOneChannel", False ):
            arguments += " -exrNoOneChannel"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "ExrInherit", False ):
            arguments += " -exrInherit"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "ExrOverrideCPUs", False ):
            arguments += " -exrcpus " + self.GetPluginInfoEntry( "ExrCPUs" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "CinOverrideFormat", False ):
            arguments += " -cinpixel \"" + self.GetPluginInfoEntry( "CinFormat" ) + "\""
        
        # Add any additional command line args if necessary.
        commandLine = self.GetPluginInfoEntryWithDefault( "CommandLine", "" )
        if commandLine != "":
            arguments += " " + commandLine
        
        # Get the output file.
        outputFile = self.GetPluginInfoEntry( "OutputFile" )
        outputFile = RepositoryUtils.CheckPathMapping( outputFile ).replace( "\\", "/" )
        if SystemUtils.IsRunningOnWindows() and outputFile.startswith( "/" ) and not outputFile.startswith( "//" ):
            outputFile = "/" + outputFile
        
        arguments += " -o \"" + outputFile + "\""
        
        return arguments
    
    def HandleProgress( self ):
        progress = float(self.GetRegexMatch(1))
        self.SetProgress( progress )
        self.SetStatusMessage( self.GetRegexMatch(0) )
