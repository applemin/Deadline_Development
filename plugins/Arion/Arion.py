
from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return ArionPlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class ArionPlugin(DeadlinePlugin):
    Framecount=0
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

    def InitializeProcess(self):
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Simple
        
        self.StdoutHandling = True
        self.PopupHandling = True    
        self.UseProcessTree = True
        #~ self.HideDosWindow = False
        #~ self.CreateNewConsole = True
        
    def RenderExecutable(self):
        exeList = self.GetConfigEntry("Arion_RenderExecutable")
        exe = FileUtils.SearchFileList( exeList )
        if( exe == "" ):
            self.FailRender( "Arion render executable was not found in the semicolon separated list \"" + exeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return exe
        
    def RenderArgument(self):
        renderArguments = ""

        sceneFile = self.GetPluginInfoEntry( "SceneFile" )
        sceneFile = PathUtils.ToPlatformIndependentPath( RepositoryUtils.CheckPathMapping( sceneFile ) )
        renderArguments += "-rcs:\"" + sceneFile + "\""
        
        ldroutputFile = self.GetPluginInfoEntryWithDefault( "LdrOutputFile", "" ).strip()
        if ldroutputFile != "":
            ldroutputFile = PathUtils.ToPlatformIndependentPath( RepositoryUtils.CheckPathMapping( ldroutputFile ) )
            renderArguments += " -ldr:\"" + ldroutputFile + "\""
        
        hdroutputFile = self.GetPluginInfoEntryWithDefault( "HdrOutputFile", "" ).strip()
        if hdroutputFile != "":
            hdroutputFile = PathUtils.ToPlatformIndependentPath( RepositoryUtils.CheckPathMapping( hdroutputFile ) )
            renderArguments += " -hdr:\"" + hdroutputFile + "\""
            
        threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if( threads > 0 ):
            renderArguments += " -cpu:" + str(threads)
            
        minutes = self.GetIntegerPluginInfoEntryWithDefault( "Minutes", 0 )
        if( minutes > 0 ) :
            renderArguments += " -minutes:" + str(minutes)
            
        passes = self.GetIntegerPluginInfoEntryWithDefault( "Passes", 0 )
        if( passes > 0 ) :
            renderArguments += " -passes:" + str(passes)
        
        channelArguments = ""
        if self.GetBooleanPluginInfoEntryWithDefault( "Main", False ):
            channelArguments += "main "
        if self.GetBooleanPluginInfoEntryWithDefault( "Alpha", False ):        
            channelArguments += "alpha "
        if self.GetBooleanPluginInfoEntryWithDefault( "Ambient", False ):
            channelArguments += "ambient "
        if self.GetBooleanPluginInfoEntryWithDefault( "Ao", False ):
            channelArguments += "ao "
        if self.GetBooleanPluginInfoEntryWithDefault( "Coverage", False ):
            channelArguments += "coverage "
        if self.GetBooleanPluginInfoEntryWithDefault( "Depth", False ):
            channelArguments += "depth "
        
        if self.GetBooleanPluginInfoEntryWithDefault( "Diffuse", False ):
            channelArguments += "diffuse "
        if self.GetBooleanPluginInfoEntryWithDefault( "Direct", False ):
            channelArguments += "direct "
        if self.GetBooleanPluginInfoEntryWithDefault( "Fresnel", False ):
            channelArguments += "fresnel "
        if self.GetBooleanPluginInfoEntryWithDefault( "Glossy", False ):
            channelArguments += "glossy "
        if self.GetBooleanPluginInfoEntryWithDefault( "Indirect", False ):
            channelArguments += "indirect "
        if self.GetBooleanPluginInfoEntryWithDefault( "Lights", False ):
            channelArguments += "lights "
            
        if self.GetBooleanPluginInfoEntryWithDefault( "LightMixer1", False ):
            channelArguments += "lm1 "
        if self.GetBooleanPluginInfoEntryWithDefault( "LightMixer2", False ):
            channelArguments += "lm2 "
        if self.GetBooleanPluginInfoEntryWithDefault( "LightMixer3", False ):
            channelArguments += "lm3 "
        if self.GetBooleanPluginInfoEntryWithDefault( "LightMixer4", False ):
            channelArguments += "lm4 "
        if self.GetBooleanPluginInfoEntryWithDefault( "LightMixer5", False ):
            channelArguments += "lm5 "
        if self.GetBooleanPluginInfoEntryWithDefault( "LightMixer6", False ):
            channelArguments += "lm6 "
            
        if self.GetBooleanPluginInfoEntryWithDefault( "LightMixer7", False ):
            channelArguments += "lm7 "
        if self.GetBooleanPluginInfoEntryWithDefault( "LightMixer8", False ):
            channelArguments += "lm8 "
        if self.GetBooleanPluginInfoEntryWithDefault( "MtlId", False ):
            channelArguments += "mtlid "
        if self.GetBooleanPluginInfoEntryWithDefault( "Normals", False ):
            channelArguments += "normals "
        if self.GetBooleanPluginInfoEntryWithDefault( "ObjId", False ):
            channelArguments += "objid "
        if self.GetBooleanPluginInfoEntryWithDefault( "Reflection", False ):
            channelArguments += "reflection "
            
        if self.GetBooleanPluginInfoEntryWithDefault( "Refraction", False ):
            channelArguments += "refraction "
        if self.GetBooleanPluginInfoEntryWithDefault( "Roughness", False ):
            channelArguments += "roughness "
        if self.GetBooleanPluginInfoEntryWithDefault( "Shadows", False ):
            channelArguments += "shadows "
        if self.GetBooleanPluginInfoEntryWithDefault( "Specular", False ):
            channelArguments += "specular "
        if self.GetBooleanPluginInfoEntryWithDefault( "SSS", False ):
            channelArguments += "sss "
        if self.GetBooleanPluginInfoEntryWithDefault( "Sun", False ):
            channelArguments += "sun "
        
        channelArguments = channelArguments.strip()
        if len(channelArguments) > 0:
            renderArguments += " -aov:\"" + channelArguments + "\""
        
        additionalArgs = self.GetPluginInfoEntryWithDefault( "AdditionalArgs", "" ).strip()
        if additionalArgs != "":
            renderArguments += " " + additionalArgs
        
        return renderArguments
        
    def CheckExitCode( self, exitCode ):
        if exitCode != 0 and exitCode != -1:
            self.FailRender( "Arion returned an error code: " + str(exitCode) + ". Check the render log for details." )
