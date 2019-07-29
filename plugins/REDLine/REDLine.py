import os

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return REDLinePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the REDLine plugin.
######################################################################
class REDLinePlugin( DeadlinePlugin ):
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
    
    def Cleanup( self ):
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
        self.AddStdoutHandlerCallback( " : ([0-9]+)" ).HandleCallback += self.HandleMovieProgress
        self.AddStdoutHandlerCallback( ".*Export Job frame complete.* ([0-9]*\.?[0-9]+)" ).HandleCallback += self.HandleFrameProgress
        self.AddStdoutHandlerCallback( "ExportJobR3DTrim finished with error" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( "Internal Error" ).HandleCallback += self.HandleError
    
    def RenderExecutable( self ):
        executable = ""
        executableList = self.GetConfigEntry( "Redline_RenderExecutable" )
        executable = FileUtils.SearchFileList( executableList )
        if executable == "":
            self.FailRender( "REDLine render executable was not found in the semicolon separated list \"" + executableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return executable

    def HandleFilePath( self, filePath ):
        filePath = RepositoryUtils.CheckPathMapping( filePath ).replace( "\\", "/" )
        
        if SystemUtils.IsRunningOnWindows() and filePath.startswith( "/" ) and not filePath.startswith( "//" ):
            filePath = "/" + filePath

        return filePath
    
    def RenderArgument( self ):
        arguments = "--verbose"

        #### File Settings & 3D Settings ####
        viewType = self.GetPluginInfoEntryWithDefault( "ViewType", "SingleView" )
        
        if viewType == "SingleView":
            sceneFile = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
            sceneFile = self.HandleFilePath( sceneFile )

            if not os.path.isfile( sceneFile ):
                self.FailRender( "Could not find scene file: %s" % sceneFile )

            # --i <filename> - input file (required)
            arguments += ' --i "%s"' % sceneFile
        
        elif viewType == "StereoView":
            leftEyeFile = self.GetPluginInfoEntryWithDefault( "LeftEyeFile", "" )
            rightEyeFile = self.GetPluginInfoEntryWithDefault( "RightEyeFile", "" )
            
            leftEyeFile = self.HandleFilePath( leftEyeFile )
            rightEyeFile = self.HandleFilePath( rightEyeFile )

            if not os.path.isfile( leftEyeFile ):
                self.FailRender( "Could not find left eye file: %s" % leftEyeFile )
            if not os.path.isfile( rightEyeFile ):
                self.FailRender( "Could not find right eye file: %s" % rightEyeFile )

            # --i3d <leftEyeFilename> <rightEyeFilename> - Left eye and right eye input files (required instead of --i for 3D export)
            arguments += ' --i3d "%s" "%s"' % (leftEyeFile, rightEyeFile )

            # --3dmode <int> - 3d Export Mode: [default = PixelInterleave]
            mode3D = self.GetPluginInfoEntryWithDefault( "3DMode", "PixelInterleave" )
            if mode3D == "PixelInterleave":
                arguments += " --3dmode 1"
            elif mode3D == "Side By Side":
                arguments += " --3dmode 2"
            elif mode3D == "Right Top, Left Bottom":
                arguments += " --3dmode 3"
            elif mode3D == "Left Top, Right Bottom":
                arguments += " --3dmode 4"
            elif mode3D == "Row Interleave":
                arguments += " --3dmode 5"

            # --3doffset <int> - 
            arguments += " --3doffset " + self.GetPluginInfoEntryWithDefault( "3DOffset", "0" )

        # --o <filename> - output basename
        arguments += ' --o "%s"' % self.GetPluginInfoEntry( "OutputBaseName" )

        # --pad <int> - filename padding [default = 6]
        arguments += " --pad " + self.GetPluginInfoEntryWithDefault( "OutputPadding", "6" )
        
        outputFolder = self.GetPluginInfoEntry( "OutputFolder" )
        outputFolder = self.HandleFilePath( outputFolder )

        # Create outputFolder if it doesn't already exist
        if not os.path.isdir( outputFolder ):
            os.makedirs( outputFolder )

        # --outDir <path> - output directory path
        arguments += ' --outDir "%s"' % outputFolder

        audioFile = self.GetPluginInfoEntryWithDefault( "AudioFile", "" ).strip()
        if audioFile != "":
            audioFile = self.HandleFilePath( audioFile )
            
            if not os.path.isfile( audioFile ):
                self.FailRender( "Missing audio file: %s" % audioFile )

            # --audio [ <filename> ] - input audio file
            arguments += " --audio " + audioFile

        if self.GetBooleanPluginInfoEntryWithDefault( "MakeSubfolder", False ):
            # --makeSubDir - Make a subdirectory for each output
            arguments += " --makeSubDir"
        
        exportPreset = self.GetPluginInfoEntryWithDefault( "ExportPreset", "" )
        if exportPreset != "":
            presetFile = self.GetPluginInfoEntryWithDefault( "PresetFile", "" )
            if presetFile != "":
                presetFile = self.HandleFilePath( presetFile )

                if not os.path.isfile( presetFile ):
                    self.FailRender( "Missing preset file: %s" % presetFile )

                # --exportPreset <name> - Load settings from an export preset: [default = none]
                arguments += ' --exportPreset "%s"' % exportPreset
                
                # --presetFile <filename> - The file to load export presets from: [default = /Users/$USER/Library/Application Support/Red/RedCineX/Presets/UserExportPresets.xml]
                arguments += ' --presetFile "%s"' % presetFile
            else:
                self.FailRender( "Missing export preset file: UserExportPresets.xml" )
        
        #### Misc Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideAdvLutRender", False ):
            advLutRender = self.GetPluginInfoEntryWithDefault( "AdvLutRender", "Assimilate 16bit LUT" )
            if advLutRender == "Assimilate 16bit LUT":
                arguments += " --advLutRender 1"
            elif advLutRender == "Shake 12bit LUT":
                arguments += " --advLutRender 2"
            elif advLutRender == "CSP 1D (0.0-1.0)":
                arguments += " --advLutRender 3"

        if self.GetBooleanPluginInfoEntryWithDefault( "NoRender", False ):
            arguments += " --noRender"

        if self.GetBooleanPluginInfoEntryWithDefault( "NoAudio", False ):
            arguments += " --noAudio"

        #### Format Settings ####
        outputFormat = self.GetPluginInfoEntryWithDefault( "OutputFormat", "DPX" ).strip()
        if outputFormat == "DPX":
            arguments += " --format 0"
        elif outputFormat == "Tiff":
            arguments += " --format 1"
        elif outputFormat == "OpenEXR":
            arguments += " --format 2"
        elif outputFormat == "SGI":
            arguments += " --format 4"
        elif outputFormat == "QT Wrappers":
            arguments += " --format 10"
        elif outputFormat == "QT Transcode":
            arguments += " --format 11"
        elif outputFormat == "R3D Trim":
            arguments += " --format 102"
        elif outputFormat == "REDray":
            arguments += " --format 104"
        elif outputFormat == "Apple ProRes":
            arguments += " --format 201"
        elif outputFormat == "Avid DNX":
            arguments += " --format 204"
        
        resolution = self.GetPluginInfoEntryWithDefault( "Resolution", "Full" ).strip()
        if resolution == "Full":
            arguments += " --res 1"
        elif resolution == "Half High":
            arguments += " --res 2"
        elif resolution == "Half Standard":
            arguments += " --res 3"
        elif resolution == "Quarter":
            arguments += " --res 4"
        elif resolution == "Eighth":
            arguments += " --res 8"
        
        colorSciVersion = self.GetPluginInfoEntryWithDefault( "ColorSciVersion", "Current Version" ).strip()
        if colorSciVersion == "Current Version":
            arguments += " --colorSciVersion 0"
        elif colorSciVersion == "Version 1":
            arguments += " --colorSciVersion 1"
        elif colorSciVersion == "Version 2":
            arguments += " --colorSciVersion 2"
        
        #### Frame Settings ####
        if not self.GetBooleanPluginInfoEntryWithDefault( "RenderAllFrames", False ):
            arguments += " --start " + str(self.GetStartFrame()) + " --end " + str(self.GetEndFrame())
            
        renumber = self.GetPluginInfoEntryWithDefault( "Renumber", "" ).strip()
        if renumber != "":
            arguments += " --renum " + renumber
        
        #### Crop and Scale Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "Crop", False ):
            cropWidth = self.GetPluginInfoEntryWithDefault( "CropWidth", "" ).strip()
            if cropWidth != "":
                arguments += " --cropW " + cropWidth
            cropHeight = self.GetPluginInfoEntryWithDefault( "CropHeight", "" ).strip()
            if cropHeight != "":
                arguments += " --cropH " + cropHeight
            cropOriginX = self.GetPluginInfoEntryWithDefault( "CropOriginX", "" ).strip()
            if cropOriginX != "":
                arguments += " --cropX " + cropOriginX
            cropOriginY = self.GetPluginInfoEntryWithDefault( "CropOriginY", "" ).strip()
            if cropOriginY != "":
                arguments += " --cropY " + cropOriginY
        
        if self.GetBooleanPluginInfoEntryWithDefault( "Scale", False ):
            scaleWidth = self.GetPluginInfoEntryWithDefault( "ScaleWidth", "" ).strip()
            if scaleWidth != "":
                arguments += " --resizeX " + scaleWidth
            scaleHeight = self.GetPluginInfoEntryWithDefault( "ScaleHeight", "" ).strip()
            if scaleHeight != "":
                arguments += " --resizeY " + scaleHeight
            
            scaleFit = self.GetPluginInfoEntryWithDefault( "ScaleFit", "Fit Width" ).strip()
            if scaleFit == "Fit Width":
                arguments += " --fit 1"
            elif scaleFit == "Fit Height":
                arguments += " --fit 2"
            elif scaleFit == "Stretch":
                arguments += " --fit 3"
            elif scaleFit == "Fit Width 2x":
                arguments += " --fit 4"
            elif scaleFit == "Fit Width .9x":
                arguments += " --fit 5"
            elif scaleFit == "Fit Height .9x":
                arguments += " --fit 6"
            elif scaleFit == "Fit Width 1.46x":
                arguments += " --fit 7"
            elif scaleFit == "Fit Width 1.09x":
                arguments += " --fit 8"
            elif scaleFit == "Fit Width 0.5x":
                arguments += " --fit 9"
            elif scaleFit == "Fit Height 0.5x":
                arguments += " --fit 10"
            elif scaleFit == "Fit Width 1.3x":
                arguments += " --fit 11"
            elif scaleFit == "Fit Height 1.3x":
                arguments += " --fit 12"
            elif scaleFit == "Fit Width 1.25x":
                arguments += " --fit 13"
            
            scaleFilter = self.GetPluginInfoEntryWithDefault( "ScaleFilter", "CatmulRom (sharper)" ).strip()
            if scaleFilter == "Bilinear (fastest)":
                arguments += " --filter 0"
            elif scaleFilter == "Bell (smoother)":
                arguments += " --filter 1"
            elif scaleFilter == "Lanczos (sharper)":
                arguments += " --filter 2"
            elif scaleFilter == "Quadratic (smoother)":
                arguments += " --filter 3"
            elif scaleFilter == "Cubic-bspline (smoother)":
                arguments += " --filter 4"
            elif scaleFilter == "CatmulRom (sharper)":
                arguments += " --filter 5"
            elif scaleFilter == "Mitchell (smoother)":
                arguments += " --filter 6"
            elif scaleFilter == "Gauss (smoother)":
                arguments += " --filter 7"
            elif scaleFilter == "WideGauss (smoothest)":
                arguments += " --filter 8"
            elif scaleFilter == "Sinc (sharpest)":
                arguments += " --filter 9"
            elif scaleFilter == "Keys (sharper)":
                arguments += " --filter 10"
            elif scaleFilter == "Rocket (sharper)":
                arguments += " --filter 11"

        # --forceFlipHorizontal <int> - 0 = Disables any horizontal flip setting in metadata, 1 = Forces the image to be flipped horizontally.
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideForceFlipHorizontal", False ):
            forceFlipHorizontal = self.GetBooleanPluginInfoEntryWithDefault( "ForceFlipHorizontal", False )
            if forceFlipHorizontal:
                arguments += " --forceFlipHorizontal 1"
            else:
                arguments += " --forceFlipHorizontal 0"

        # --forceFlipVertical <int> - 0 = Disables any vertical flip setting in metadata, 1 = Forces the image to be flipped vertically.
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideForceFlipVertical", False ):
            forceFlipVertical = self.GetBooleanPluginInfoEntryWithDefault( "ForceFlipVertical", False )
            if forceFlipVertical:
                arguments += " --forceFlipVertical 1"
            else:
                arguments += " --forceFlipVertical 0"

        # --rotate <float> - Rotates the image only 0.0, -90.0 and 90.0 degrees are currently accepted.
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideRotate", False ):
            arguments += " --rotate " + self.GetPluginInfoEntryWithDefault( "Rotate", "0.0" )

        # --preventNegativePixels <int> - Prevents the scaler from generating negative pixel values. 0=off 1=on [default = 1].
        if self.GetBooleanPluginInfoEntryWithDefault( "OverridePreventNegativePixels", False ):
            preventNegativePixels = self.GetPluginInfoEntryWithDefault( "PreventNegativePixels", "On" )
            if preventNegativePixels == "On":
                arguments += " --preventNegativePixels 1"
            else:
                arguments += " --preventNegativePixels 0"

        #### Metadata Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "UseMeta", False ):
            arguments += " --useMeta"

            # --metaIgnoreFrameGuide - Use in conjunction with useMeta. Ignores frame guides.
            if self.GetBooleanPluginInfoEntryWithDefault( "MetaIgnoreFrameGuide", False ):
                arguments += " --metaIgnoreFrameGuide"

        rsxFile = self.GetPluginInfoEntryWithDefault( "RSXFile", "" ).strip()
        if rsxFile != "":
            rsxFile = self.HandleFilePath( rsxFile )
            
            if not os.path.isfile( rsxFile ):
                self.FailRender( "Missing RSX file: %s" % rsxFile )

            arguments += ' --loadRSX "%s"' % rsxFile
            
            useRSX = self.GetPluginInfoEntryWithDefault( "UseRSX", "Color & In/Out" ).strip()
            if useRSX == "Color & In/Out":
                arguments += " --useRSX 1"
            elif useRSX == "Color Only":
                arguments += " --useRSX 2"
                
        rmdFile = self.GetPluginInfoEntryWithDefault( "RMDFile", "" ).strip()
        if rmdFile != "":
            rmdFile = self.HandleFilePath( rmdFile )

            if not os.path.isfile( rmdFile ):
                self.FailRender( "Missing RMD file: %s" % rmdFile )

            arguments += ' --loadRMD "%s"' % rmdFile
            
            useRMD = self.GetPluginInfoEntryWithDefault( "UseRMD", "Color & In/Out" ).strip()
            if useRMD == "Color & In/Out":
                arguments += " --useRMD 1"
            elif useRMD == "Color Only":
                arguments += " --useRMD 2"

        # --printMeta <int> - Print out metadata settings, 0=header, 1=normal, 2=csv, 3=header+csv, 4=3D rig, 5=per-frame lens+acc+gyro
        if self.GetBooleanPluginInfoEntryWithDefault( "OverridePrintMeta", False ):
            printMeta = self.GetPluginInfoEntryWithDefault( "PrintMeta", "normal" )
            if printMeta == "header":
                arguments += " --printMeta 0"
            elif printMeta == "normal":
                arguments += " --printMeta 1"
            elif printMeta == "csv":
                arguments += " --printMeta 2"
            elif printMeta == "header+csv":
                arguments += " --printMeta 3"
            elif printMeta == "3D rig":
                arguments += " --printMeta 4"
            elif printMeta == "per-frame lens+acc+gyro":
                arguments += " --printMeta 5"

        # --ALE <filename> - Saves an ale file with given filename.
        aleFile = self.GetPluginInfoEntryWithDefault( "ALEFile", "" )
        if aleFile != "":
            aleFile = self.HandleFilePath( aleFile )
            
            if not os.path.isdir( os.path.dirname( aleFile) ):
                os.makedirs( os.path.dirname( aleFile ) )

            arguments += ' --ALE "%s"' % aleFile

        # --reelID <int> - 0=full name, 1=FCP 8 Character
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideReelID", False ):
            reelID = self.GetPluginInfoEntryWithDefault( "ReelID", "full name" )
            if reelID == "full name":
                arguments += " --reelID 0"
            else:
                arguments += " --reelID 1"

        # --clipFrameRate <int> - Change Clip Framerate: 1=23.976fps, 2=24fps, 3=25fps, 4=29.97fps, 5=30fps,
        # 6=47.952fps,7=48fps, 8=50fps, 9=59.94fps, 10=60fps, 11=71.928fps, 12=72fps
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideClipFrameRate", False ):
            clipFrameRate = self.GetPluginInfoEntry( "ClipFrameRate" ) # no default
            if clipFrameRate == "23.976fps":
                arguments += " --clipFrameRate 1"
            elif clipFrameRate == "24fps":
                arguments += " --clipFrameRate 2"
            elif clipFrameRate == "25fps":
                arguments += " --clipFrameRate 3"
            elif clipFrameRate == "29.97fps":
                arguments += " --clipFrameRate 4"
            elif clipFrameRate == "30fps":
                arguments += " --clipFrameRate 5"
            elif clipFrameRate == "47.952fps":
                arguments += " --clipFrameRate 6"
            elif clipFrameRate == "48fps":
                arguments += " --clipFrameRate 7"
            elif clipFrameRate == "50fps":
                arguments += " --clipFrameRate 8"
            elif clipFrameRate == "59.94fps":
                arguments += " --clipFrameRate 9"
            elif clipFrameRate == "60fps":
                arguments += " --clipFrameRate 10"
            elif clipFrameRate == "71.928fps":
                arguments += " --clipFrameRate 11"
            elif clipFrameRate == "72fps":
                arguments += " --clipFrameRate 12"

        #### Quicktime Transcode Settings ####
        if outputFormat == "QT Transcode":
            qtCodec = self.GetPluginInfoEntryWithDefault( "QTCodec", "Apple ProRes 422 (HQ)" )
            if qtCodec == "Apple ProRes 422 (HQ)":
                arguments += " --QTcodec 0"
            elif qtCodec == "Apple ProRes 422":
                arguments += " --QTcodec 1"
            elif qtCodec == "H.264":
                arguments += " --QTcodec 2"
            elif qtCodec == "MJPEG A":
                arguments += " --QTcodec 3"
            elif qtCodec == "MJPEG B":
                arguments += " --QTcodec 4"
            elif qtCodec == "JPEG":
                arguments += " --QTcodec 10"
            elif qtCodec == "Component":
                arguments += " --QTcodec 5"
            elif qtCodec == "H.263":
                arguments += " --QTcodec 6"
            elif qtCodec == "None":
                arguments += " --QTcodec 7"
            elif qtCodec == "Pixlet":
                arguments += " --QTcodec 8"
            elif qtCodec == "DVCPRO720":
                arguments += " --QTcodec 9"
            elif qtCodec == "Animation/RLE":
                arguments += " --QTcodec 11"
            elif qtCodec == "Uncompressed 8-bit 4:2:2":
                arguments += " --QTcodec 12"
            elif qtCodec == "Uncompressed 10-bit 4:2:2":
                arguments += " --QTcodec 13"
            elif qtCodec == "AVID DNxHD":
                arguments += " --QTcodec 14"
            elif qtCodec == "BlackMagic RGB 10bit":
                arguments += " --QTcodec 15"
            elif qtCodec == "AJA Kona 10bit Log RGB":
                arguments += " --QTcodec 17"
            elif qtCodec == "AJA Kona 10bit RGB":
                arguments += " --QTcodec 18"
            elif qtCodec == "AVID 1080P DNxHD 36 8-bit (23.98, 24, 25)":
                arguments += " --QTcodec 20"
            elif qtCodec == "AVID 1080P DNxHD 115/120 8-bit (23.98, 24, 25)":
                arguments += " --QTcodec 21"
            elif qtCodec == "AVID 1080P DNxHD 175/185 8-bit (23.98, 24, 25)":
                arguments += " --QTcodec 22"
            elif qtCodec == "AVID 1080P DNxHD 175/185 10-bit (23.98, 24, 25)":
                arguments += " --QTcodec 23"
            elif qtCodec == "AVID 720P DNxHD 60/75 8-bit (23.98, 25, 29.97)":
                arguments += " --QTcodec 24"
            elif qtCodec == "AVID 720P DNxHD 90/110 8-bit (23.98, 29.97)":
                arguments += " --QTcodec 25"
            elif qtCodec == "AVID 720P DNxHD 90/110 10-bit (23.98, 29.97)":
                arguments += " --QTcodec 26"
            elif qtCodec == "AVID 720P DNxHD 120/145 8-bit (50, 59.94)":
                arguments += " --QTcodec 27"
            elif qtCodec == "AVID 720P DNxHD 185/220 8-bit (50, 59.94)":
                arguments += " --QTcodec 28"
            elif qtCodec == "AVID 720P DNxHD 185/220 10-bit (50, 59.94)":
                arguments += " --QTcodec 29"
            elif qtCodec == "Apple ProRes 4444":
                arguments += " --QTcodec 30"
            elif qtCodec == "Apple ProRes 422 LT":
                arguments += " --QTcodec 31"
            elif qtCodec == "Apple ProRes 422 Proxy":
                arguments += " --QTcodec 32"
            
            if not self.GetBooleanPluginInfoEntryWithDefault( "QTClobber", True ):
                arguments += " --noClobber"

            #### Text Burn-In Settings ####
            if self.GetBooleanPluginInfoEntryWithDefault( "Burn", False ):
                arguments += " --burnIn"
                
                burnFrames = self.GetPluginInfoEntryWithDefault( "BurnFrames", "All" )
                if burnFrames == "All":
                    arguments += " --burnFrames 0"
                elif burnFrames == "First":
                    arguments += " --burnFrames 1"
                elif burnFrames == "First & Last":
                    arguments += " --burnFrames 2"
                elif burnFrames == "Last":
                    arguments += " --burnFrames 3"
                elif burnFrames == "Count":
                    # --burnFramesCount <int> - Number of frames to burn in. [default = 1]
                    arguments += " --burnFramesCount " + self.GetPluginInfoEntryWithDefault( "BurnFramesCount", "1" )
                
                burnFont = self.GetPluginInfoEntryWithDefault( "BurnFont", "Letter Gothic" )
                if burnFont == "Letter Gothic":
                    arguments += " --burnFont 1"
                elif burnFont == "Monaco":
                    arguments += " --burnFont 2"
                elif burnFont == "Courier":
                    arguments += " --burnFont 3"
                elif burnFont == "Lucida Type":
                    arguments += " --burnFont 4"
                elif burnFont == "Andale Mono":
                    arguments += " --burnFont 5"
                elif burnFont == "OCRA":
                    arguments += " --burnFont 6"
                elif burnFont == "Orator Std":
                    arguments += " --burnFont 7"
                
                arguments += " --burnSz " + self.GetPluginInfoEntryWithDefault( "BurnSize", "20" )
                arguments += " --burnBase " + self.GetPluginInfoEntryWithDefault( "BurnBase", "20" )
                
                burnLowerLeft = self.GetPluginInfoEntryWithDefault( "BurnLowerLeft", "Reel/Filename" )
                if burnLowerLeft == "Reel/Filename":
                    arguments += " --burnLL 1"
                elif burnLowerLeft == "Frames":
                    arguments += " --burnLL 2"
                elif burnLowerLeft == "Frames In Edit":
                    arguments += " --burnLL 3"
                elif burnLowerLeft == "Frames In Source":
                    arguments += " --burnLL 4"
                elif burnLowerLeft == "Edge Code":
                    arguments += " --burnLL 5"
                elif burnLowerLeft == "EXT/TOD Time Code":
                    arguments += " --burnLL 6"
                
                burnLowerRight = self.GetPluginInfoEntryWithDefault( "BurnLowerRight", "Reel/Filename" )
                if burnLowerRight == "Reel/Filename":
                    arguments += " --burnLR 1"
                elif burnLowerRight == "Frames":
                    arguments += " --burnLR 2"
                elif burnLowerRight == "Frames In Edit":
                    arguments += " --burnLR 3"
                elif burnLowerRight == "Frames In Source":
                    arguments += " --burnLR 4"
                elif burnLowerRight == "Edge Code":
                    arguments += " --burnLR 5"
                elif burnLowerRight == "EXT/TOD Time Code":
                    arguments += " --burnLR 6"
                
                burnUpperLeft = self.GetPluginInfoEntryWithDefault( "BurnUpperLeft", "Reel/Filename" )
                if burnUpperLeft == "Reel/Filename":
                    arguments += " --burnUL 1"
                elif burnUpperLeft == "Frames":
                    arguments += " --burnUL 2"
                elif burnUpperLeft == "Frames In Edit":
                    arguments += " --burnUL 3"
                elif burnUpperLeft == "Frames In Source":
                    arguments += " --burnUL 4"
                elif burnUpperLeft == "Edge Code":
                    arguments += " --burnUL 5"
                elif burnUpperLeft == "EXT/TOD Time Code":
                    arguments += " --burnUL 6"
                
                burnUpperRight = self.GetPluginInfoEntryWithDefault( "BurnUpperRight", "Reel/Filename" )
                if burnUpperRight == "Reel/Filename":
                    arguments += " --burnUR 1"
                elif burnUpperRight == "Frames":
                    arguments += " --burnUR 2"
                elif burnUpperRight == "Frames In Edit":
                    arguments += " --burnUR 3"
                elif burnUpperRight == "Frames In Source":
                    arguments += " --burnUR 4"
                elif burnUpperRight == "Edge Code":
                    arguments += " --burnUR 5"
                elif burnUpperRight == "EXT/TOD Time Code":
                    arguments += " --burnUR 6"
                
                arguments += " --burnTxtR " + self.GetPluginInfoEntryWithDefault( "BurnTextR", "0" )
                arguments += " --burnTxtG " + self.GetPluginInfoEntryWithDefault( "BurnTextG", "0" )
                arguments += " --burnTxtB " + self.GetPluginInfoEntryWithDefault( "BurnTextB", "0" )
                arguments += " --burnTxtA " + self.GetPluginInfoEntryWithDefault( "BurnTextA", "1" )
                
                arguments += " --burnBgR " + self.GetPluginInfoEntryWithDefault( "BurnBackgroundR", "0" )
                arguments += " --burnBgG " + self.GetPluginInfoEntryWithDefault( "BurnBackgroundG", "0" )
                arguments += " --burnBgB " + self.GetPluginInfoEntryWithDefault( "BurnBackgroundB", "0" )
                arguments += " --burnBgA " + self.GetPluginInfoEntryWithDefault( "BurnBackgroundA", "1" )

        #### Watermark Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideWatermark", False ):
            # --watermark - Turn on watermarking.
            arguments += " --watermark"
            
            # --watermarkFont <int> - Letter Gothic=1, Andale Mono=5, OCRA=6, DejaVu Sans Mono=8, [default = 6]
            watermarkFont = self.GetPluginInfoEntryWithDefault( "WatermarkFont", "OCRA" )
            if watermarkFont == "Letter Gothic":
                arguments += " --watermarkFont 1"
            elif watermarkFont == "Andale Mono":
                arguments += " --watermarkFont 5"
            elif watermarkFont == "OCRA":
                arguments += " --watermarkFont 6"
            elif watermarkFont == "DejaVu Sans Mono":
                arguments += " --watermarkFont 8"

            # --watermarkText <string> - Watermark text
            arguments += " --watermarkText " + self.GetPluginInfoEntryWithDefault( "WatermarkText", "" )

            # --watermarkSz <float> - Height of text in percent of output height [default = 5]
            arguments += " --watermarkSz " + self.GetPluginInfoEntryWithDefault( "WatermarkSz", "5.0" )

            # --watermarkBase <float> - Watermark Y location in percent of height [default = 20]
            arguments += " --watermarkBase " + self.GetPluginInfoEntryWithDefault( "WatermarkBase", "20.0" )
        
            # --watermarkTxtR <float> - Text red channel (0-1.0) [default = 1.0]
            arguments += " --watermarkTxtR " + self.GetPluginInfoEntryWithDefault( "WatermarkTxtR", "1.0" )

            # --watermarkTxtG <float> - Text green channel (0-1.0) [default = 1.0]
            arguments += " --watermarkTxtG " + self.GetPluginInfoEntryWithDefault( "WatermarkTxtG", "1.0" )

            # --watermarkTxtB <float> - Text blue channel (0-1.0) [default = 1.0]
            arguments += " --watermarkTxtB " + self.GetPluginInfoEntryWithDefault( "WatermarkTxtB", "1.0" )

            # --watermarkTxtA <float> - Text alpha channel (0-1.0) [default = 0.8]
            arguments += " --watermarkTxtA " + self.GetPluginInfoEntryWithDefault( "WatermarkTxtA", "0.8" )

        #### Color/Gamma Space Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideColorSpace", False ):
                colorSpace = self.GetPluginInfoEntryWithDefault( "ColorSpace", "REDspace" )
                if colorSpace == "REDspace":
                    arguments += " --colorSpace 11"
                elif colorSpace == "Camera RGB":
                    arguments += " --colorSpace 12"
                elif colorSpace == "REC709":
                    arguments += " --colorSpace 13"
                elif colorSpace == "REDcolor":
                    arguments += " --colorSpace 14"
                elif colorSpace == "sRGB":
                    arguments += " --colorSpace 15"
                elif colorSpace == "Adobe1998":
                    arguments += " --colorSpace 5"
                elif colorSpace == "REDcolor2":
                    arguments += " --colorSpace 18"
                elif colorSpace == "REDcolor3":
                    arguments += " --colorSpace 19"
                elif colorSpace == "DRAGONcolor":
                    arguments += " --colorSpace 20"
                elif colorSpace == "XYZ":
                    arguments += " --colorSpace 21"
                elif colorSpace == "REDcolor4":
                    arguments += " --colorSpace 22"
                elif colorSpace == "DRAGONcolor2":
                    arguments += " --colorSpace 23"
                elif colorSpace == "rec2020":
                    arguments += " --colorSpace 24"
                elif colorSpace == "REDWideGamutRGB":
                    arguments += " --colorSpace 25"

        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideGammaCurve", False ):
            gammaCurve = self.GetPluginInfoEntryWithDefault( "GammaCurve", "REDspace" )
            if gammaCurve == "Linear Light":
                arguments += " --gammaCurve -1"
            elif gammaCurve == "REC709":
                arguments += " --gammaCurve 1"
            elif gammaCurve == "sRGB":
                arguments += " --gammaCurve 2"
            elif gammaCurve == "REDlog":
                arguments += " --gammaCurve 3"
            elif gammaCurve == "PDlog 985":
                arguments += " --gammaCurve 4"
            elif gammaCurve == "PDlog 685":
                arguments += " --gammaCurve 5"
            elif gammaCurve == "PDLogCustom":
                arguments += " --gammaCurve 6"
            elif gammaCurve == "REDspace":
                arguments += " --gammaCurve 14"
            elif gammaCurve == "REDgamma":
                arguments += " --gammaCurve 15"
            elif gammaCurve == "REDLogFilm":
                arguments += " --gammaCurve 27"
            elif gammaCurve == "REDgamma2":
                arguments += " --gammaCurve 28"
            elif gammaCurve == "REDgamma3":
                arguments += " --gammaCurve 29"
            elif gammaCurve == "REDgamma4":
                arguments += " --gammaCurve 30"
            elif gammaCurve == "HDR-2084":
                arguments += " --gammaCurve 31"
            elif gammaCurve == "BT1886":
                arguments += " --gammaCurve 32"
            elif gammaCurve == "Log3G12":
                arguments += " --gammaCurve 33"
            elif gammaCurve == "Log3G10":
                arguments += " --gammaCurve 34"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideDetail", False ):
            detail = self.GetPluginInfoEntryWithDefault( "Detail", "High" )
            if detail == "Leading Lady":
                arguments += " --detail 1"
            elif detail == "Medium":
                arguments += " --detail 4"
            elif detail == "High":
                arguments += " --detail 8"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideOLPFCompensation", False ):
            olpfCompensation = self.GetPluginInfoEntryWithDefault( "OLPFCompensation", "Off" )
            if olpfCompensation == "Low":
                arguments += " --OLPF 1"
            elif olpfCompensation == "Medium":
                arguments += " --OLPF 50"
            elif olpfCompensation == "High":
                arguments += " --OLPF 100"

        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideNoiseReduction", False ):
            noiseReduction = self.GetPluginInfoEntryWithDefault( "NoiseReduction", "Mild" )
            if noiseReduction == "Off":
                arguments += " --NR 0"
            elif noiseReduction == "Very Mild":
                arguments += " --NR 1000"
            elif noiseReduction == "Milder":
                arguments += " --NR 500"
            elif noiseReduction == "Mild":
                arguments += " --NR 250"
            elif noiseReduction == "Medium":
                arguments += " --NR 100"
            elif noiseReduction == "Strong":
                arguments += " --NR 50"
            elif noiseReduction == "Max":
                arguments += " --NR 10"

        # --SMPTEColorRange <int> - Restricts colors to the SMPTE range. 0=off 1=on [default = 0].
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideSMPTEColorRange", False ):
            smpteColorRange = self.GetPluginInfoEntryWithDefault( "SMPTEColorRange", "Off" )
            if smpteColorRange == "On":
                arguments += " --SMPTEColorRange 1"
            else:
                arguments += " --SMPTEColorRange 0"
        
        #### Color Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideISO", False ):
            arguments += " --iso " + self.GetPluginInfoEntryWithDefault( "ISO", "320" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideFlut", False ):
            arguments += " --flut " + self.GetPluginInfoEntryWithDefault( "Flut", "0.0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideShadow", False ):
            arguments += " --shadow " + self.GetPluginInfoEntryWithDefault( "Shadow", "0.0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideKelvin", False ):
            arguments += " --kelvin " + self.GetPluginInfoEntryWithDefault( "Kelvin", "5600" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideTint", False ):
            arguments += " --tint " + self.GetPluginInfoEntryWithDefault( "Tint", "0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideExposure", False ):
            arguments += " --exposure " + self.GetPluginInfoEntryWithDefault( "Exposure", "0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideSaturation", False ):
            arguments += " --saturation " + self.GetPluginInfoEntryWithDefault( "Saturation", "1" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideContrast", False ):
            arguments += " --contrast " + self.GetPluginInfoEntryWithDefault( "Contrast", "0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideBrightness", False ):
            arguments += " --brightness " + self.GetPluginInfoEntryWithDefault( "Brightness", "0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideRed", False ):
            arguments += " --redGain " + self.GetPluginInfoEntryWithDefault( "Red", "1" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideGreen", False ):
            arguments += " --greenGain " + self.GetPluginInfoEntryWithDefault( "Green", "1" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideBlue", False ):
            arguments += " --blueGain " + self.GetPluginInfoEntryWithDefault( "Blue", "1" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideDRX", False ):
            arguments += " --drx " + self.GetPluginInfoEntryWithDefault( "DRX", "0.5" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideDEB", False ):
            debValue = self.GetPluginInfoEntryWithDefault( "DEB", "Off" )
            if debValue == "Off":
                arguments += " --deb 0"
            else:
                arguments += " --deb 1"
        
        #### Lift Gamma Gain Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideRedLift", False ):
            arguments += " --lggRedLift " + self.GetPluginInfoEntryWithDefault( "RedLift", "0.0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideGreenLift", False ):
            arguments += " --lggGreenLift " + self.GetPluginInfoEntryWithDefault( "GreenLift", "0.0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideBlueLift", False ):
            arguments += " --lggBlueLift " + self.GetPluginInfoEntryWithDefault( "BlueLift", "0.0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideRedGamma", False ):
            arguments += " --lggRedGamma " + self.GetPluginInfoEntryWithDefault( "RedGamma", "1.0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideGreenGamma", False ):
            arguments += " --lggGreenGamma " + self.GetPluginInfoEntryWithDefault( "GreenGamma", "1.0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideBlueGamma", False ):
            arguments += " --lggBlueGamma " + self.GetPluginInfoEntryWithDefault( "BlueGamma", "1.0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideRedGain", False ):
            arguments += " --lggRedGain " + self.GetPluginInfoEntryWithDefault( "RedGain", "1.0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideGreenGain", False ):
            arguments += " --lggGreenGain " + self.GetPluginInfoEntryWithDefault( "GreenGain", "1.0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideBlueGain", False ):
            arguments += " --lggBlueGain " + self.GetPluginInfoEntryWithDefault( "BlueGain", "1.0" )

        #### Print Density Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverridePdBlack", False ):
            arguments += " --pdBlack " + self.GetPluginInfoEntryWithDefault( "PdBlack", "95" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverridePdWhite", False ):
            arguments += " --pdWhite " + self.GetPluginInfoEntryWithDefault( "PdWhite", "685" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverridePdGamma", False ):
            arguments += " --pdGamma " + self.GetPluginInfoEntryWithDefault( "PdGamma", "0.6" )

        #### Curve Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideBlack", False ):
            arguments += " --black " + self.GetPluginInfoEntryWithDefault( "Black", "0" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideWhite", False ):
            arguments += " --white " + self.GetPluginInfoEntryWithDefault( "White", "100" )

        #### New Curve Point Values ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideLumaCurve", False ):
            arguments += " --lumaCurve " + self.GetPluginInfoEntryWithDefault( "LumaCurve", "0:0:25:25:50:50:75:75:100:100" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideRedCurve", False ):
            arguments += " --redCurve " + self.GetPluginInfoEntryWithDefault( "RedCurve", "0:0:25:25:50:50:75:75:100:100" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideGreenCurve", False ):
            arguments += " --greenCurve " + self.GetPluginInfoEntryWithDefault( "GreenCurve", "0:0:25:25:50:50:75:75:100:100" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideBlueCurve", False ):
            arguments += " --blueCurve " + self.GetPluginInfoEntryWithDefault( "BlueCurve", "0:0:25:25:50:50:75:75:100:100" )
        
        #### HDR Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideHdrMode", False ):
            hdrMode = self.GetPluginInfoEntryWithDefault( "HdrMode", "A Frame" )
            if hdrMode == "A Frame":
                arguments += " --hdrMode 1"
            elif hdrMode == "X Frame":
                arguments += " --hdrMode 2"
            elif hdrMode == "Simple Blend":
                arguments += " --hdrMode 3"
            elif hdrMode == "Magic Motion":
                arguments += " --hdrMode 4"

            if hdrMode == "Simple Blend" or hdrMode == "Magic Motion":
                arguments += " --hdrBias " + self.GetPluginInfoEntryWithDefault( "HdrBias", "0.0" )

        #### DPX Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideDpxByteOrder", False ):
            dpxByteOrder = self.GetPluginInfoEntryWithDefault( "DpxByteOrder", "LSB" )
            if dpxByteOrder == "LSB":
                arguments += " --byteOrder 0"
            else:
                arguments += " --byteOrder 1"

        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideDpxBitDepth", False ):
            arguments += " --bitDepth " + self.GetPluginInfoEntryWithDefault( "DpxBitDepth", "10" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideDpxMaxWriters", False ):
            arguments += " --maxWriters " + self.GetPluginInfoEntryWithDefault( "DpxMaxWriters", "10" )

        #### OpenEXR Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideExrCompression", False ):
            exrCompression = self.GetPluginInfoEntryWithDefault( "ExrCompression", "NONE" )
            if exrCompression == "NONE":
                arguments += " --exrCompression 0"
            elif exrCompression == "RLE":
                arguments += " --exrCompression 1"
            elif exrCompression == "ZIPS":
                arguments += " --exrCompression 2"
            elif exrCompression == "ZIP":
                arguments += " --exrCompression 3"
            elif exrCompression == "PIZ":
                arguments += " --exrCompression 4"
            elif exrCompression == "PXR24":
                arguments += " --exrCompression 5"
            elif exrCompression == "B44":
                arguments += " --exrCompression 6"
            elif exrCompression == "B44A":
                arguments += " --exrCompression 7"
            elif exrCompression == "DWAA":
                arguments += " --exrCompression 8"
            elif exrCompression == "DWAB":
                arguments += " --exrCompression 9"

            if exrCompression == "DWAA":
                arguments += " --exrDWACompression " + self.GetPluginInfoEntryWithDefault( "ExrDWACompression", "45" )

        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideExrMultiView", False ):
            exrMultiView = self.GetPluginInfoEntryWithDefault( "ExrMultiView", "Single Channel" )
            if exrMultiView == "Single Channel":
                arguments += " --exrMultiView 0"
            else:
                arguments += " --exrMultiView 1"

        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideExrWriters", False ):
            arguments += " --exrMaxWriters " + self.GetPluginInfoEntryWithDefault( "ExrWriters", "10" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideExrACES", False ):
            exrAces = self.GetPluginInfoEntryWithDefault( "ExrACES", "Off" )
            if exrAces == "Off":
                arguments += " --exrACES 0"
            else:
                arguments += " --exrACES 1"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideExrSoftClamp", False ):
            exrSoftClamp = self.GetPluginInfoEntryWithDefault( "ExrSoftClamp", "Off" )
            if exrSoftClamp == "Off":
                arguments += " --exrSoftClamp 0"
            else:
                arguments += " --exrSoftClamp 1"

        #### R3D Trim Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "TrimRmdSidecar", False ):
            arguments += " --trimRMDSidecar"
        if self.GetBooleanPluginInfoEntryWithDefault( "TrimQtWrappers", False ):
            arguments += " --trimQTWrappers"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideTrimFcpXml", False ):
            trimFcpXml = self.GetPluginInfoEntryWithDefault( "TrimFcpXml", "No FCP XML" )
            if trimFcpXml == "No FCP XML":
                arguments += " --trimFCPXml 0"
            elif trimFcpXml == "Full":
                arguments += " --trimFCPXml 1"
            elif trimFcpXml == "Half":
                arguments += " --trimFCPXml 2"
            elif trimFcpXml == "Quarter":
                arguments += " --trimFCPXml 3"
            elif trimFcpXml == "Eighth":
                arguments += " --trimFCPXml 4"

        if self.GetBooleanPluginInfoEntryWithDefault( "TrimAudio", False ):
            arguments += " --trimAudio"

        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideTrimChangeFrameRate", False ):
            trimChangeFrameRate = self.GetPluginInfoEntryWithDefault( "TrimChangeFrameRate", "24fps" )
            if trimChangeFrameRate == "23.976fps":
                arguments += " --trimChangeFrameRate 1"
            elif trimChangeFrameRate == "24fps":
                arguments += " --trimChangeFrameRate 2"
            elif trimChangeFrameRate == "25fps":
                arguments += " --trimChangeFrameRate 3"
            elif trimChangeFrameRate == "29.97fps":
                arguments += " --trimChangeFrameRate 4"
            elif trimChangeFrameRate == "30fps":
                arguments += " --trimChangeFrameRate 5"
            elif trimChangeFrameRate == "47.952fps":
                arguments += " --trimChangeFrameRate 6"
            elif trimChangeFrameRate == "48fps":
                arguments += " --trimChangeFrameRate 7"
            elif trimChangeFrameRate == "50fps":
                arguments += " --trimChangeFrameRate 8"
            elif trimChangeFrameRate == "59.94fps":
                arguments += " --trimChangeFrameRate 9"
            elif trimChangeFrameRate == "60fps":
                arguments += " --trimChangeFrameRate 10"
            elif trimChangeFrameRate == "71.928fps":
                arguments += " --trimChangeFrameRate 11"
            elif trimChangeFrameRate == "72fps":
                arguments += " --trimChangeFrameRate 12"

        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideTrimChangeOLPF", False ):
            arguments += " --trimChangeOLPF " + self.GetPluginInfoEntryWithDefault( "TrimChangeOLPF", "1" )

        #### Avid DNX Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideDnxCodec", False ):
            dnxCodec = self.GetPluginInfoEntryWithDefault( "DnxCodec", "Avid DNxHR HQ" )
            if dnxCodec == "Avid DNxHR 444":
                arguments += " --dnxCodec 0"
            elif dnxCodec == "Avid DNxHR HQX":
                arguments += " --dnxCodec 1"
            elif dnxCodec == "Avid DNxHR HQ":
                arguments += " --dnxCodec 2"
            elif dnxCodec == "Avid DNxHR SQ":
                arguments += " --dnxCodec 3"
            elif dnxCodec == "Avid DNxHR LB":
                arguments += " --dnxCodec 4"

        # Avid Media Framerate
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideDnxFrameRate", False ):
            dnxFrameRate = self.GetPluginInfoEntryWithDefault( "DnxFrameRate", "23.98" )
            if dnxFrameRate == "23.976":
                arguments += " --dnxFrameRate 0"
            elif dnxFrameRate == "24":
                arguments += " --dnxFrameRate 1"
            elif dnxFrameRate == "25":
                arguments += " --dnxFrameRate 2"
            elif dnxFrameRate == "29.97":
                arguments += " --dnxFrameRate 3"
            elif dnxFrameRate == "30":
                arguments += " --dnxFrameRate 4"
            elif dnxFrameRate == "50":
                arguments += " --dnxFrameRate 5"
            elif dnxFrameRate == "59.94":
                arguments += " --dnxFrameRate 6"
            elif dnxFrameRate == "60":
                arguments += " --dnxFrameRate 7"

        #### REDray Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideRrContentTitle", False ):
            arguments += " --rrContentTitle " + self.GetPluginInfoEntryWithDefault( "RrContentTitle", "" )
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideRrPosterFrame", False ):
            arguments += " --rrPosterFrame " + self.GetPluginInfoEntryWithDefault( "RrPosterFrame", "" )

        #### Rocket Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "NoRocket", False ):
            arguments += " --noRocket"
        if self.GetBooleanPluginInfoEntryWithDefault( "SingleRocket", False ):
            arguments += " --singleRocket"
        if self.GetBooleanPluginInfoEntryWithDefault( "ForceRocket", False ):
            arguments += " --forceRocket"
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideUseRocket", False ):
            rocketIndices = self.GetPluginInfoEntryWithDefault( "UseRocket", "" )
            if rocketIndices != "":
                deviceList = rocketIndices.split(",") # split by comma character
                rocketDevices = " ".join(deviceList)
                arguments += " --useRocket " + rocketDevices # generate a space separated string of Rocket indices.
            else:
                self.FailRender("No rocket indices provided!")

        #### Graph Processing/OpenCL/CUDA Settings ####
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideGpuPlatform", False ):
            gpuPlatform = self.GetPluginInfoEntryWithDefault( "GpuPlatform", "No GPU" ) # default=1 (OpenCL) in --help, but switching to "No GPU" for headless CPU based renderfarm, typical with Deadline.
            if gpuPlatform == "No GPU":
                arguments = " --gpuPlatform 0"
            elif gpuPlatform == "OpenCL":
                arguments = " --gpuPlatform 1"
            elif gpuPlatform == "CUDA":
                arguments = " --gpuPlatform 2"

            self.LogInfo( "GPU Platform: %s" % gpuPlatform )

            if gpuPlatform == "OpenCL" or gpuPlatform == "CUDA":

                # Calculate the gpus to use.
                gpusSelectDevices = self.GetPluginInfoEntryWithDefault( "GPUsSelectDevices", "" )
                gpus = ""
                gpuList = []

                if gpusSelectDevices != "":
                    self.LogInfo( "Specific GPUs specified, so the following GPUs will be used by REDLine: " + gpusSelectDevices )
                    gpuList = gpusSelectDevices.split(",") # split by comma character
                    gpus = " ".join(gpuList) # generate a space separated string
                
                elif self.OverrideGpuAffinity():
                    for gpuId in self.GpuAffinity():
                        gpuList.append( str( gpuId ) )
                    
                    gpus = " ".join(gpuList) # generate a space separated string
                    self.LogInfo( "This Slave is overriding its GPU affinity, so the following GPUs will be used by REDLine: " + gpus )
                
                if gpus != "":
                    if gpuPlatform == "OpenCL":
                        arguments += " --openclDeviceIndexes " + gpus # GPU affinity - OpenCL
                    else:
                        arguments += " --cudaDeviceIndexes " + gpus # GPU affinity - CUDA
                else:
                    self.LogWarning( "No GPUs specified. Skipping GPU." )

        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideDecodeThreads", False ):
            arguments += " --decodeThreads " + self.GetPluginInfoEntryWithDefault( "DecodeThreads", "7" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideNumGraphs", False ):
            arguments += " --numGraphs " + self.GetPluginInfoEntry( "NumGraphs" ) # no default
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideNumOclStreams", False ):
            arguments += " --numOclStreams " + self.GetPluginInfoEntry( "NumOclStreams" ) # no default

        #### Advanced Dragon Debayer (A.D.D.) ####
        if self.GetBooleanPluginInfoEntryWithDefault( "EnableADD", False ):
            arguments += " --enableADD"

            if self.GetBooleanPluginInfoEntryWithDefault( "OverrideADDUsmAmount", False ):
                arguments += " --ADDUsmAmount " + self.GetPluginInfoEntryWithDefault( "ADDUsmAmount", "200" )

            if self.GetBooleanPluginInfoEntryWithDefault( "OverrideADDUsmRadius", False ):
                arguments += " --ADDUsmRadius " + self.GetPluginInfoEntryWithDefault( "ADDUsmRadius", "0.6" )

            if self.GetBooleanPluginInfoEntryWithDefault( "OverrideADDUsmThreshold", False ):
                arguments += " --ADDUsmThreshold " + self.GetPluginInfoEntryWithDefault( "ADDUsmThreshold", "1.0" )

            if self.GetBooleanPluginInfoEntryWithDefault( "ADDUsmDisable", False ):
                arguments += " --ADDUsmDisable"
        
        #### 3D LUT Settings ####
        lutFile = self.GetPluginInfoEntryWithDefault( "LutFile", "" ).strip()
        
        if lutFile != "":
            lutFile = self.HandleFilePath( lutFile )
            arguments += " --lut " + lutFile

            if self.GetBooleanPluginInfoEntryWithDefault( "OverrideLutEdgeLength", False ):
                arguments += " --lutEdgeLength " + self.GetPluginInfoEntryWithDefault( "LutEdgeLength", "" )
        
        return arguments
    
    def HandleMovieProgress( self ):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        currFrame = int(self.GetRegexMatch(1))
        
        numerator = currFrame - startFrame + 1
        denominator = endFrame - startFrame + 1
        if denominator != 0:
            self.SetProgress( (float(numerator) / float(denominator)) * 100.0 )

    def HandleFrameProgress( self ):
        progress = float(self.GetRegexMatch(1)) * 100.0
        self.SetProgress( progress )

    def HandleError( self ):
        self.FailRender( self.GetRegexMatch(0) )
