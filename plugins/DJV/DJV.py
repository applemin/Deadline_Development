## ------------------------------------------------------------
## DJV.py
## Created March 06, 2011
## Updated June 18, 2015
## 
## DJV Plugin to Deadline Queue System
## Command Line Utility to convert image sequences and create QuickTime Movies from image sequences including RPF & OpenEXR File Formats
## Tested with Windows 7 and potentially 'compatible' with any other Windows OS
## ------------------------------------------------------------
## NOTES:
## DJV presently does NOT support negative frame ranges in the python submission code in Deadline
## ------------------------------------------------------------
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return DJVPlugin()

######################################################################
## This is the main DeadlinePlugin class for the DJV plugin.
######################################################################
class DJVPlugin (DeadlinePlugin):

    VersionString = "082"
    Version = 82
    IsInputMovie = False
    IsOutputMovie = False

    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.CheckExitCodeCallback += self.CheckExitCode
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.CheckExitCodeCallback

    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple
    
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True

        # [ERROR] OpenEXR - ERROR MESSAGE FORMAT
        self.AddStdoutHandlerCallback("\[ERROR\].*").HandleCallback += self.HandleRenderTasksError
        # [100%] Estimated
        self.AddStdoutHandlerCallback("\[([\s0-9]+)%\]").HandleCallback += self.HandleRenderTasksProgress

    def RenderExecutable( self ):
        self.VersionString = self.GetPluginInfoEntryWithDefault( "Version", "082")
        self.Version = int( self.VersionString )

        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()

        djvExeList = self.GetConfigEntry( "djvExecutable" + self.VersionString )
        djvExe = ""
        if(SystemUtils.IsRunningOnWindows()):
            if build == "32bit":
                djvExe = FileUtils.SearchFileListFor32Bit( djvExeList )
                if( djvExe == "" ):
                    self.LogWarning( "32 bit djv_convert executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % djvExeList )
            elif build == "64bit":
                djvExe = FileUtils.SearchFileListFor64Bit( djvExeList )
                if( djvExe == "" ):
                    self.LogWarning( "64 bit djv_convert executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % djvExeList )
            
        if( djvExe == "" ):
            djvExe = FileUtils.SearchFileList( djvExeList )
            if( djvExe == "" ):
                self.FailRender( "djv_convert executable could not be found in the semicolon separated list \"%s\". The path to the djv_convert executable can be configured from the Plugin Configuration in the Deadline Monitor." % djvExeList )

        djvExe = RepositoryUtils.CheckPathMapping( djvExe )
        if SystemUtils.IsRunningOnWindows():
            djvExe = djvExe.replace( "/", "\\" )
            if djvExe.startswith( "\\" ) and not djvExe.startswith( "\\\\" ):
                djvExe = "\\" + djvExe
        else:
            djvExe = djvExe.replace( "\\", "/" )

        return djvExe
    
    def IsInputMovieFormat( self, InputFile ):
        extension = Path.GetExtension( InputFile ).lower()
        movieFormats = ( ".qt",".mov",".avi",".mp4" )
        for format in movieFormats:
            if extension == format.lower():
                self.IsInputMovie = True
                return True
        self.IsInputMovie = False
        return False

    def IsOutputMovieFormat( self, OutputFile ):
        extension = Path.GetExtension( OutputFile ).lower()
        movieFormats = ( ".qt",".mov",".avi",".mp4" )
        for format in movieFormats:
            if extension == format.lower():
                self.IsOutputMovie = True
                return True
        self.IsOutputMovie = False
        return False

    def IsTagsSupported( self, OutputFile ):
        extension = Path.GetExtension( OutputFile ).lower()
        tagSupportedFormats = ( ".cin",".dpx",".exr" )
        for format in tagSupportedFormats:
            if extension == format.lower():
                return True
        return False

    def RenderArgument( self ):
    
        # Read in settings from plugin info file.
        InputFile = self.GetPluginInfoEntry( "InputFile" ).strip()
        InputFile = RepositoryUtils.CheckPathMapping( InputFile )
        if SystemUtils.IsRunningOnWindows():
            InputFile = InputFile.replace( "/", "\\" )
            if InputFile.startswith( "\\" ) and not InputFile.startswith( "\\\\" ):
                InputFile = "\\" + InputFile
        else:
            InputFile = InputFile.replace( "\\", "/" )

        OutputFile = self.GetPluginInfoEntry( "OutputFile" ).strip()
        OutputFile = RepositoryUtils.CheckPathMapping( OutputFile )
        if SystemUtils.IsRunningOnWindows():
            OutputFile = OutputFile.replace( "/", "\\" )
            if OutputFile.startswith( "\\" ) and not OutputFile.startswith( "\\\\" ):
                OutputFile = "\\" + OutputFile
        else:
            OutputFile = OutputFile.replace( "\\", "/" )
        
        InputFileDirectory = Path.GetDirectoryName( InputFile )
        self.LogInfo( "Input File Directory: %s" % InputFileDirectory )
        InputExtension = Path.GetExtension( InputFile ).lower()
        self.LogInfo( "Input File Extension: %s" % InputExtension)

        if( not self.IsInputMovieFormat( InputFile ) ):
            # Need to process the "InputFile" to be in the correct format = "C:\Test_EXR_Seq_0000-0000.exr"
            paddingLength = FrameUtils.GetPaddingSizeFromFilename( InputFile )
            StartFrameInput = FrameUtils.SubstituteFrameNumber(InputFile,StringUtils.ToZeroPaddedString(self.GetStartFrame(),paddingLength,False))
            InputFilename = Path.GetFileNameWithoutExtension( StartFrameInput )
            EndFrame = StringUtils.ToZeroPaddedString( self.GetEndFrame(),paddingLength, False )
            InputFile = Path.Combine( InputFileDirectory, InputFilename )
            InputFile = InputFile + "-" + EndFrame + InputExtension

        self.LogInfo( "InputFile: %s" % InputFile )

        OutputExtension = Path.GetExtension( OutputFile ).lower()
        self.LogInfo( "Output Extension: %s" % OutputExtension )

        if( not self.IsOutputMovieFormat( OutputFile ) ):
            # Need to process the "OutputFile" to be in the correct format for an IMAGE sequence, such as "C:\Test_EXR_Seq_0000.jpg"
            OutputFile = FrameUtils.SubstituteFrameNumber(OutputFile,StringUtils.ToZeroPaddedString(self.GetStartFrame(),paddingLength,False))

        self.LogInfo( "Output File: %s" % OutputFile ) 

        # djv_convert (input) (output) [option]...
        renderArguments = ""
        renderArguments = " \"" + InputFile + "\"" + " \"" + OutputFile + "\""

        ## General Image Options
        timeUnits = self.GetPluginInfoEntryWithDefault( "TimeUnitsBox", "frames" )
        renderArguments += " -time_units " + timeUnits
        frameRate = self.GetPluginInfoEntryWithDefault( "FrameRate", "24" )
        if frameRate != "default":
            if self.Version < 101:
                renderArguments += " -speed_default " + frameRate
            else:
                renderArguments += " -default_speed " + frameRate

        ## Input Options
        Layer = self.GetPluginInfoEntryWithDefault( "InputLayerBox", "" )
        if Layer != "":
            renderArguments += " -layer " + Layer
        ProxyScale = self.GetPluginInfoEntryWithDefault( "ProxyScaleBox", "none" )
        if ProxyScale != "none":
            renderArguments += " -proxy " + ProxyScale
        InputStartFrame = self.GetPluginInfoEntryWithDefault( "InputStartFrameBox", "0" )
        InputEndFrame = self.GetPluginInfoEntryWithDefault( "InputEndFrameBox", "0" )
        if InputStartFrame != "0" or InputEndFrame != "0":
            renderArguments += " -time " + InputStartFrame + " " + InputEndFrame
        SlateInput = self.GetPluginInfoEntryWithDefault( "SlateInputBox", "" )

        # Check Path Mapping for different OS
        SlateInput = RepositoryUtils.CheckPathMapping( SlateInput )
        SlateFrame = self.GetPluginInfoEntryWithDefault( "SlateFrameBox", "0" )
        if SlateInput != "" and SlateFrame != "0":
            renderArguments += " -slate " + "\"" + SlateInput + "\"" + " " + SlateFrame
        InputImageTimeout = self.GetPluginInfoEntryWithDefault( "InputImageTimeoutBox", "0" )
        if InputImageTimeout != "0":
            renderArguments += " -timeout " + InputImageTimeout

        ## Output Options
        PixelType = self.GetPluginInfoEntryWithDefault( "PixelTypeBox", "default" )
        if PixelType != "default":
            if self.Version < 101:
                renderArguments += " -pixel " + PixelType
            else:
                renderArguments += " -pixel " + "\"" + PixelType + "\""

        OutputFrameRate = self.GetPluginInfoEntryWithDefault( "OutputFrameRateBox", "default" )
        if OutputFrameRate != "default":
            renderArguments += " -speed " + OutputFrameRate

        # Custom Image Tag (if not movie and image format supports <TIMECODE> tags)

        # [-tag] is currently broken in DJV

        # if (not self.IsOutputMovie) and self.IsTagsSupported(OutputFile):
        #     ImageTagName = self.GetPluginInfoEntryWithDefault( "ImageTagNameBox", "" )
        #     ImageTagValue = self.GetPluginInfoEntryWithDefault( "ImageTagValueBox", "" )
        #     if ImageTagName != "":
        #         renderArguments += " -tag " + ImageTagName + " " + ImageTagValue

            # [-tag_auto] is currently broken in DJV

            # AutoGenerateTags = self.GetPluginInfoEntryWithDefault( "AutoGenerateTagsBox", "true" )
            # renderArguments += " -tag_auto " + AutoGenerateTags

        # OpenGL Options
        if self.Version < 101:
            OpenGL = self.GetPluginInfoEntryWithDefault( "RendererBox", "opengl 2.0" )
            if OpenGL != "opengl 2.0":
                renderArguments += " -render " + OpenGL

        RenderFilterMin = self.GetPluginInfoEntryWithDefault( "RenderFilterMinBox", "linear" )
        RenderFilterMag = self.GetPluginInfoEntryWithDefault( "RenderFilterMagBox", "nearest" )

        if self.Version >= 101 and RenderFilterMin == "Lanczos3" and RenderFilterMag == "Mitchell":
            renderArguments += " -render_filter_high"
        elif RenderFilterMin != "linear" or RenderFilterMag != "nearest":
            renderArguments += " -render_filter " + RenderFilterMin + " " + RenderFilterMag

        if self.Version < 101:
            RenderOffscreen = self.GetPluginInfoEntryWithDefault( "OffscreenBufferBox", "fbo" )
            if RenderOffscreen != "fbo":
                renderArguments += " -render_offscreen " + RenderOffscreen

        # OpenEXR LOADING Options
        if InputExtension == ".exr":
            exrColorProfile = self.GetPluginInfoEntryWithDefault( "ColorProfileBox", "gamma" )
            exrEXRGamma = self.GetPluginInfoEntryWithDefault( "EXRGammaBox", "2.2" )
            exrEXRValue = self.GetPluginInfoEntryWithDefault( "EXRValueBox", "0" )
            exrEXRDefog = self.GetPluginInfoEntryWithDefault( "EXRDefogBox", "0" )
            exrEXRKneeLow = self.GetPluginInfoEntryWithDefault( "EXRKneeLowBox", "0" )
            exrEXRKneeHigh = self.GetPluginInfoEntryWithDefault( "EXRKneeHighBox", "5" )
            exrEXRChannels = self.GetPluginInfoEntryWithDefault( "EXRChannelsBox", "group known" )
            
            if self.Version < 101:
                renderArguments += " -load openexr color profile " + exrColorProfile
                if exrColorProfile == "gamma":
                    renderArguments += " -load openexr gamma " + exrEXRGamma
                elif exrColorProfile == "exposure":
                    renderArguments += " -load openexr exposure " + exrEXRValue + " " + exrEXRDefog + " " + exrEXRKneeLow + " " + exrEXRKneeHigh
                renderArguments += " -load openexr channels " + "\"" + exrEXRChannels + "\""
            else:
                renderArguments += " -exr_input_color_profile " + exrColorProfile
                if exrColorProfile == "gamma":
                    renderArguments += " -exr_input_gamma " + exrEXRGamma
                elif exrColorProfile == "exposure":
                    renderArguments += " -exr_input_exposure " + exrEXRValue + " " + exrEXRDefog + " " + exrEXRKneeLow + " " + exrEXRKneeHigh
                
                if exrEXRChannels == "group known":
                    channelOption = "Known"
                elif exrEXRChannels == "group none":
                    channelOption = "None"
                elif exrEXRChannels == "group all":
                    channelOption = "All"
                else:
                    channelOption = "Known"

                renderArguments += " -exr_channels " + channelOption

        # OpenEXR SAVING Options
        if OutputExtension == ".exr":
            EXRCompressionType = self.GetPluginInfoEntryWithDefault( "EXRCompressionTypeBox", "none" )
            EXRCompressionLevel = self.GetPluginInfoEntryWithDefault( "EXRCompressionLevelBox", "45" )
            if self.Version < 101:
                if EXRCompressionType == "dwaa" or EXRCompressionType == "dwab":
                    self.FailRender( "EXR: Dreamworks Animation DWAA or DWAB EXR Compression only supported in DJV v1.0.1 or later" )
                renderArguments += " -save openexr compression " + EXRCompressionType
            else:
                renderArguments += " -exr_compression " + EXRCompressionType
                if EXRCompressionType == "dwaa" or EXRCompressionType == "dwab":
                    renderArguments += " -exr_dwa_compression_level " + EXRCompressionLevel

        # Cineon LOADING Options
        if InputExtension == ".cin":
            CineonLoadColorProfile = self.GetPluginInfoEntryWithDefault( "CineonLoadColorProfileBox", "auto" )
            CineonLoadBlack = self.GetPluginInfoEntryWithDefault( "CineonLoadBlackBox", "95" )
            CineonLoadWhite = self.GetPluginInfoEntryWithDefault( "CineonLoadWhiteBox", "685" )
            CineonLoadGamma = self.GetPluginInfoEntryWithDefault( "CineonLoadGammaBox", "1.7" )
            CineonLoadSoftClip = self.GetPluginInfoEntryWithDefault( "CineonLoadSoftClipBox", "0" )
            CineonLoadConvert = self.GetPluginInfoEntryWithDefault( "CineonLoadConvertBox", "none" )

            if self.Version < 101:
                renderArguments += " -load cineon color profile " + "\"" + CineonLoadColorProfile + "\""
                if CineonLoadColorProfile == "film print":	
                    renderArguments += " -load cineon film print " + CineonLoadBlack + " " + CineonLoadWhite + " " + CineonLoadGamma + " " + CineonLoadSoftClip
                if CineonLoadConvert != "none":
                    renderArguments += " -load cineon convert " + CineonLoadConvert
            else:
                renderArguments += " -cineon_input_color_profile " + "\"" + CineonLoadColorProfile + "\""
                if CineonLoadColorProfile == "film print":
                    renderArguments += " -cineon_input_film_print " + CineonLoadBlack + " " + CineonLoadWhite + " " + CineonLoadGamma + " " + CineonLoadSoftClip
                if CineonLoadConvert != "none":
                    renderArguments += " -cineon_convert " + CineonLoadConvert

        # Cineon SAVING Options
        if OutputExtension == ".cin":
            CineonSaveColorProfile = self.GetPluginInfoEntryWithDefault( "CineonSaveColorProfileBox", "film print" )
            CineonSaveBlack = self.GetPluginInfoEntryWithDefault( "CineonSaveBlackBox", "95" )
            CineonSaveWhite = self.GetPluginInfoEntryWithDefault( "CineonSaveWhiteBox", "685" )
            CineonSaveGamma = self.GetPluginInfoEntryWithDefault( "CineonSaveGammaBox", "1.7" )
            
            if self.Version < 101:            
                renderArguments += " -save cineon color profile " + "\"" + CineonSaveColorProfile + "\""
                if CineonSaveColorProfile == "film print":
                    renderArguments += " -save cineon film print " + CineonSaveBlack + " " + CineonSaveWhite + " " + CineonSaveGamma
            else:
                renderArguments += " -cineon_output_color_profile " + "\"" + CineonSaveColorProfile + "\""
                if CineonSaveColorProfile == "film print":
                    renderArguments += " -cineon_output_film_print " + CineonSaveBlack + " " + CineonSaveWhite + " " + CineonSaveGamma

        # DPX LOADING Options
        if InputExtension == ".dpx":
            DPXColorProfile = self.GetPluginInfoEntryWithDefault( "DPXColorProfileBox", "auto" )
            DPXBlack = self.GetPluginInfoEntryWithDefault( "DPXBlackBox", "95" )
            DPXWhite = self.GetPluginInfoEntryWithDefault( "DPXWhiteBox", "685" )
            DPXGamma = self.GetPluginInfoEntryWithDefault( "DPXGammaBox", "1.7" )
            DPXSoftClip = self.GetPluginInfoEntryWithDefault( "DPXSoftClipBox", "0" )
            DPXConvert = self.GetPluginInfoEntryWithDefault( "DPXConvertBox", "none" )

            if self.Version < 101:
                renderArguments += " -load dpx color profile " + "\"" + DPXColorProfile + "\""
                if DPXColorProfile == "film print":
                    renderArguments += " -load dpx film print " + DPXBlack + " " + DPXWhite + " " + DPXGamma + " " + DPXSoftClip
                if DPXConvert != "none":
                    renderArguments += " -load dpx convert " + DPXConvert
            else:
                renderArguments += " -dpx_input_color_profile " + "\"" + DPXColorProfile + "\""
                if DPXColorProfile == "film print":
                    renderArguments += " -dpx_input_film_print " + DPXBlack + " " + DPXWhite + " " + DPXGamma + " " + DPXSoftClip
                if DPXConvert != "none":
                    renderArguments += " -dpx_convert " + DPXConvert

        # DPX SAVING Options
        if OutputExtension == ".dpx":
            DPXSaveColorProfile = self.GetPluginInfoEntryWithDefault( "DPXSaveColorProfileBox", "film print" )
            DPXSaveBlack = self.GetPluginInfoEntryWithDefault( "DPXSaveBlackBox", "95" )
            DPXSaveWhite = self.GetPluginInfoEntryWithDefault( "DPXSaveWhiteBox", "685" )
            DPXSaveGamma = self.GetPluginInfoEntryWithDefault( "DPXSaveGammaBox", "1.7" )
            DPXSaveFileVersion = self.GetPluginInfoEntryWithDefault( "DPXSaveFileVersionBox", "2.0" )
            DPXSaveFileType = self.GetPluginInfoEntryWithDefault( "DPXSaveFileTypeBox", "u10" )
            DPXSaveFileEndian = self.GetPluginInfoEntryWithDefault( "DPXSaveFileEndianBox", "msb" )

            if self.Version < 101:
                renderArguments += " -save dpx color profile " + "\"" + DPXSaveColorProfile + "\""
                if DPXSaveColorProfile == "film print":
                    renderArguments += " -save dpx film print " + DPXSaveBlack + " " + DPXSaveWhite + " " + DPXSaveGamma
                renderArguments += " -save dpx file version " + DPXSaveFileVersion
                renderArguments += " -save dpx file type " + DPXSaveFileType
                renderArguments += " -save dpx file endian " + DPXSaveFileEndian
            else:
                renderArguments += " -dpx_output_color_profile " + "\"" + DPXSaveColorProfile + "\""
                if DPXSaveColorProfile == "film print":
                    renderArguments += " -dpx_output_film_print " + DPXSaveBlack + " " + DPXSaveWhite + " " + DPXSaveGamma
                renderArguments += " -dpx_version " + DPXSaveFileVersion
                renderArguments += " -dpx_type " + DPXSaveFileType
                renderArguments += " -dpx_endian " + DPXSaveFileEndian

        # LUT or 1DL LOADING Options
        if InputExtension == ".lut" or InputExtension == ".1dl":
            LUTFileLoadFormat = self.GetPluginInfoEntryWithDefault( "LUTFileLoadFormatBox", "auto" )
            LUTFileLoadType = self.GetPluginInfoEntryWithDefault( "LUTFileLoadTypeBox", "auto" )

            if self.Version < 101:
                renderArguments += " -load lut file format " + LUTFileLoadFormat
                renderArguments += " -load lut file type " + LUTFileLoadType
            else:
                renderArguments += " -lut_type " + LUTFileLoadType

        # LUT or 1DL SAVING Options
        if OutputExtension == ".lut" or OutputExtension == ".1dl":
            LUTFileSaveFormat = self.GetPluginInfoEntryWithDefault( "LUTFileSaveFormatBox", "auto" )
            renderArguments += " -save lut file format " + LUTFileSaveFormat

        # QuickTime LOADING Options
        if InputExtension == ".qt" or InputExtension == ".mov":
            if self.Version < 101:
                QTStartFrame = self.GetPluginInfoEntryWithDefault( "QTStartFrameBox", "0" )
                renderArguments += " -load quicktime start frame " + QTStartFrame

        # QuickTime SAVING Options
        # NOTE: djv uses QuickTime on Windows, but libQuicktime on Linux which has different options
        # It only supports the codec option there, but has an undocumented library of codecs, dunno
        # if there is a way to easily read it.
        if (OutputExtension == ".mov" or OutputExtension == ".qt"):
            QTcodec = self.GetPluginInfoEntryWithDefault( "QTcodec", "mjpeg-a" )
            QTquality = self.GetPluginInfoEntryWithDefault( "QTquality", "normal" )

            if not SystemUtils.IsRunningOnLinux():
                if self.Version < 101:
                    renderArguments += " -save quicktime codec " + QTcodec
                    renderArguments += " -save quicktime quality " + QTquality
                else:
                    renderArguments += " -quicktime_codec " + QTcodec
                    renderArguments += " -quicktime_quality " + QTquality
            else:
                # DJV v1.0.1 adds "libquicktime" codec documentation, so we can now add support for it!
                if self.Version >= 101:
                    QTLibQuicktimeCodec = self.GetPluginInfoEntryWithDefault( "QTLibQuicktimeCodecBox", "mjpa" )
                    renderArguments += " -libquicktime_codec " + QTLibQuicktimeCodec
                    renderArguments += " -quicktime_quality " + QTquality

        # IFF or Z SAVING Options
        if OutputExtension == ".iff" or OutputExtension == ".z":
            IFFCompressionType = self.GetPluginInfoEntryWithDefault( "IFFCompressionTypeBox", "rle" )
            if self.version < 101:
                renderArguments += " -save iff compression " + IFFCompressionType
            else:
                renderArguments += " -iff_compression " + IFFCompressionType

        # PPM SAVING Options
        if OutputExtension == ".ppm" or OutputExtension == ".pnm" or OutputExtension == ".pgm" or OutputExtension == ".pbm":
            PPMFileType = self.GetPluginInfoEntryWithDefault( "PPMFileTypeBox", "auto" )
            PPMFileData = self.GetPluginInfoEntryWithDefault( "PPMFileDataBox", "binary" )
            if self.Version < 101:
                renderArguments += " -save ppm file type " + PPMFileType
                renderArguments += " -save ppm file data " + PPMFileData
            else:
                renderArguments += " -ppm_type " + PPMFileType
                renderArguments += " -ppm_data " + PPMFileData

        # SGI SAVING Options
        if OutputExtension == ".sgi" or OutputExtension == ".rgba" or OutputExtension == ".rgb" or OutputExtension == ".bw":
            SGICompressionType = self.GetPluginInfoEntryWithDefault( "SGICompressionTypeBox", "none" )
            if self.Version < 101:
                renderArguments += " -save sgi compression " + SGICompressionType
            else:
                renderArguments += " -sgi_compression " + SGICompressionType

        # Targa SAVING Options
        if OutputExtension == ".tga":
            TGACompressionType = self.GetPluginInfoEntryWithDefault( "TGACompressionTypeBox", "none" )
            if self.Version < 101:
                renderArguments += " -save targa compression " + TGACompressionType
            else:
                renderArguments += " -targa_compression " + TGACompressionType

        # JPEG SAVING Options
        if OutputExtension == ".jpg" or OutputExtension == ".jpeg" or OutputExtension == ".jfif":
            JPEGQuality = self.GetPluginInfoEntryWithDefault( "JPEGQualityBox", "90" )
            if self.Version < 101:
                renderArguments += " -save jpeg quality " + JPEGQuality
            else:
                renderArguments += " -jpeg_quality " + JPEGQuality

        # TIFF SAVING Options
        if OutputExtension == ".tif" or OutputExtension == ".tiff":
            TIFFCompressionType = self.GetPluginInfoEntryWithDefault( "TIFFCompressionTypeBox", "none" )
            if self.Version < 101:
                renderArguments += " -save tiff compression " + TIFFCompressionType
            else:
                renderArguments += " -tiff_compression " + TIFFCompressionType

        ## Conversion Options
        # Mirror Options
        MirrorImage = self.GetPluginInfoEntryWithDefault( "MirrorImage", "none" )
        if MirrorImage == "mirror_h":
            renderArguments += " -mirror_h"
        elif MirrorImage == "mirror_v":
            renderArguments += " -mirror_v"

        # Scale Options
        ImageScalePercentage = self.GetPluginInfoEntryWithDefault( "ImageScalePercentage", "0" )
        if ImageScalePercentage != "0":
            renderArguments += " -scale " + ImageScalePercentage
        ImageScaleX = self.GetPluginInfoEntryWithDefault( "ImageScaleXBox", "0" )
        ImageScaleY = self.GetPluginInfoEntryWithDefault( "ImageScaleYBox", "0" )
        if ImageScalePercentage == "0":
            if ImageScaleX != "0" and ImageScaleY != "0":
                renderArguments += " -scale_xy " + ImageScaleX + " " + ImageScaleY

        # ReSize Options
        ImageReSizeW = self.GetPluginInfoEntryWithDefault( "ImageReSizeWBox", "0" )
        ImageReSizeH = self.GetPluginInfoEntryWithDefault( "ImageReSizeHBox", "0" )
        MaintainAspectRatio = self.GetPluginInfoEntryWithDefault( "MaintainAspectRatioBox", "False" )
        if MaintainAspectRatio == "True":
            if ImageReSizeW != "0" and ImageReSizeH != "0":
                renderArguments += " -width " + ImageReSizeW + " -height " + ImageReSizeH
        elif MaintainAspectRatio == "False":
            if ImageReSizeW != "0" and ImageReSizeH != "0":
                renderArguments += " -resize " + ImageReSizeW + " " + ImageReSizeH

        # Crop Options (Version >= 101)
        ImageCropX = self.GetPluginInfoEntryWithDefault( "ImageCropXBox", "0" )
        ImageCropY = self.GetPluginInfoEntryWithDefault( "ImageCropYBox", "0" )
        ImageCropW = self.GetPluginInfoEntryWithDefault( "ImageCropWBox", "0" )
        ImageCropH = self.GetPluginInfoEntryWithDefault( "ImageCropHBox", "0" )
        CropPercentage = self.GetPluginInfoEntryWithDefault( "CropPercentageBox", "False" )

        if ImageCropX != "0" or ImageCropY != "0" or ImageCropW != "0" or ImageCropH != "0":
            if CropPercentage == "True":
                renderArguments += " -crop_percent " + ImageCropX + " " + ImageCropY + " " + ImageCropW + " " + ImageCropH
            else:
                renderArguments += " -crop " + ImageCropX + " " + ImageCropY + " " + ImageCropW + " " + ImageCropH

        # Image Channels
        ImageChannels = self.GetPluginInfoEntryWithDefault( "ImageChannels", "default" )
        if ImageChannels != "default":
            renderArguments += " -channel " + ImageChannels

        # File Sequencing (Version >= 101)
        FileSequence = self.GetPluginInfoEntryWithDefault( "FileSequenceBox", "False" )
        if FileSequence == "True":
            renderArguments += " -seq True"

        renderArguments = RepositoryUtils.CheckPathMapping( renderArguments )
        if SystemUtils.IsRunningOnWindows():
            renderArguments = renderArguments.replace( "/", "\\" )
        else:
            renderArguments = renderArguments.replace( "\\", "/" )

        return renderArguments
    
    def CheckExitCode( self, exitCode ):
        if exitCode != 0:
            self.FailRender( "djv_convert.exe returned a non-zero error code of %d" % exitCode )

    def HandleRenderTasksError( self ):
        self.FailRender( self.GetRegexMatch(0) )
    
    def HandleRenderTasksProgress( self ):
        self.SetProgress( float(self.GetRegexMatch(1)) )
