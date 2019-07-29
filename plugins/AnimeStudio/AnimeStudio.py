from System import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return AnimeStudioPlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class AnimeStudioPlugin(DeadlinePlugin):
    frameCount=0
    finishedFrameCount=0
    
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
    
    def InitializeProcess(self):
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        
        #Std out handlers
        self.AddStdoutHandlerCallback(r"Frame [0-9]+ \(([0-9]+)/([0-9]+)\).*").HandleCallback += self.HandleProgress
        self.AddStdoutHandlerCallback(r"Unrecognized argument:.*").HandleCallback += self.HandleError
    
    def RenderExecutable(self):
        versionStr = self.GetPluginInfoEntryWithDefault( "Version", "9.5" )
        
        executableList = self.GetConfigEntry( "Anime_RenderExecutable" + versionStr.replace( ".", "_" ) )	
        executable = FileUtils.SearchFileList( executableList )
        if executable == "":
            self.FailRender( "Anime Studio/Moho " + versionStr + " render executable was not found in the semicolon separated list \"" + executableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return executable
        
    def RenderArgument(self):
        version = self.GetFloatPluginInfoEntryWithDefault( "Version", 9.5 )
        sceneSubmitted = False
        
        # Set the scene file option
        sceneFile = self.GetPluginInfoEntryWithDefault( "SceneFile", "" ).strip()
        if len(sceneFile) == 0:
            sceneFile = self.GetDataFilename() 
            sceneSubmitted = True
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        sceneFile = PathUtils.ToPlatformIndependentPath( sceneFile )
        arguments = " -r \"" + sceneFile + "\""
        
        # Verbose
        arguments += " -v"
        
        # Supported formats: QT, JPEG, TGA, BMP, PNG, PSD, and SWF
        format = self.GetPluginInfoEntryWithDefault( "OutputFormat", "JPEG" )
        
        # In version 9.5 and later, the format must be in lower case. Otherwise it needs to be upper case.
        if version < 9.5:
            format = format.upper()
        else:
            format = format.lower()
        
        if format.find( " " ) != -1:
            format = "\"" + format + "\""
        arguments += " -f " + format
        
        # If no output specified, it is automatically saved to the same location as the scene file.
        outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip()
        if len(outputFile) > 0:
            outputFile = RepositoryUtils.CheckPathMapping( outputFile )
            outputFile = PathUtils.ToPlatformIndependentPath( outputFile )
            arguments += " -o \"" + outputFile + "\""
        else:
            # Need to fail if the scene was submitted, because the output would get rendered to the local folder and then get lost.
            if sceneSubmitted:
                self.FailRender( "The scene file was submitted with the job, but no output file was specified. This would result in the rendered images being lost." )
        
        # Specify the frame range.
        arguments += " -start " + str(self.GetStartFrame()) + " -end " + str(self.GetEndFrame())
        
        # Layer Comp Name argument only available in 10 and later.
        if version >= 10:
            layerCompName = self.GetPluginInfoEntryWithDefault( "LayerComp", "" )
            if layerCompName != "":
                if layerCompName.find( " " ) != -1:
                    layerCompName = "\"" + layerCompName + "\""
                arguments += " -layercomp " + layerCompName
                
                # Additional layer comp options introduced in 11.2
                if version >= 11:
                    if self.GetBooleanPluginInfoEntryWithDefault( "AddLayerCompSuffix", False ):
                        arguments += " -addlayercompsuffix yes"
                    if self.GetBooleanPluginInfoEntryWithDefault( "CreateFolderForLayerComps", False ):
                        arguments += " -createfolderforlayercomps yes"
        
        # Format Suffice argument only available in 9.5 and later.
        if version >= 9.5 and self.GetBooleanPluginInfoEntryWithDefault( "AddFormatSuffix", False ):
            arguments += " -addformatsuffix"
        
        # Now specify the remaining flags.
        arguments += " -aa " + self.GetYesOrNo( self.GetBooleanPluginInfoEntryWithDefault( "Antialised", True ) )
        arguments += " -shapefx " + self.GetYesOrNo( self.GetBooleanPluginInfoEntryWithDefault( "ShapeEffects", True ) )
        arguments += " -layerfx " + self.GetYesOrNo( self.GetBooleanPluginInfoEntryWithDefault( "LayerEffects", True ) )
        arguments += " -halfsize " + self.GetYesOrNo( self.GetBooleanPluginInfoEntryWithDefault( "HalfSize", False ) )
        arguments += " -halffps " + self.GetYesOrNo( self.GetBooleanPluginInfoEntryWithDefault( "HalfFrameRate", False ) )
        arguments += " -fewparticles " + self.GetYesOrNo( self.GetBooleanPluginInfoEntryWithDefault( "ReducedParticles", False ) )
        arguments += " -extrasmooth " + self.GetYesOrNo( self.GetBooleanPluginInfoEntryWithDefault( "ExtraSmooth", False ) )
        arguments += " -ntscsafe " + self.GetYesOrNo( self.GetBooleanPluginInfoEntryWithDefault( "NtscSafeColors", False ) )
        arguments += " -premultiply " + self.GetYesOrNo( not self.GetBooleanPluginInfoEntryWithDefault( "NoPremultiplyAlpha", False ) )
        #arguments += " -multithread " + self.GetYesOrNo( self.GetBooleanPluginInfoEntryWithDefault( "MultiThreaded", True ) )
        
        # This flag is only supported with SWF renders.
        if format == "SWF":
            arguments += " -variablewidths " + self.GetYesOrNo( self.GetBooleanPluginInfoEntryWithDefault( "VariableLineWidths", False ) )
        
        # These options are only supported with QTrenders, and only work in 10 and later.
        if version >= 10 and format == "QT":
            arguments += " -videocodec " + self.GetPluginInfoEntryWithDefault( "VideoCodec", "" )
            arguments += " -quality " + self.GetPluginInfoEntryWithDefault( "Quality", "3" )
            arguments += " -depth " + self.GetPluginInfoEntryWithDefault( "Depth", "24" )
        
        return arguments
    
    def GetYesOrNo( self, flag ):
        if flag:
            return "yes"
        else:
            return "no"
    
    def HandleProgress(self):
        self.SetStatusMessage( self.GetRegexMatch(0) )
        
        currFrame = float(self.GetRegexMatch(1))
        totalFrames = float(self.GetRegexMatch(2))
        progress = (currFrame * 100) / totalFrames
        if progress > 100:
            progress = 100
        self.SetProgress( (currFrame * 100) / totalFrames ) 

    def HandleError(self):
        self.FailRender( self.GetRegexMatch(0))
