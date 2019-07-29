import clr
import os

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
    return KeyShotPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the KeyShot plugin.
######################################################################
class KeyShotPlugin (DeadlinePlugin):

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
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple
         
    def RenderExecutable( self ):
        version = self.GetPluginInfoEntryWithDefault( "Version", "6" ).strip() #default to empty string (this should match pre-versioning config entries)
        
        keyshotExeList = self.GetConfigEntry( "RenderExecutable%s" % version )
        keyshotExe = FileUtils.SearchFileList( keyshotExeList )
        if( keyshotExe == "" ):
            self.FailRender( "KeyShot " + version + " render executable was not found in the semicolon separated list \"" + keyshotExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return keyshotExe
    
    def RenderArgument( self ):
        sceneFilename = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
        sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename )
        sceneFilename = sceneFilename.replace( "\\", "/" )
        
        outputFilename = self.GetPluginInfoEntry( "OutputFile" )
        outputFilename = RepositoryUtils.CheckPathMapping( outputFilename )
        outputFilename = outputFilename.replace( "\\", "/" )
        
        width = self.GetIntegerPluginInfoEntryWithDefault( "RenderWidth", 1920 )
        height = self.GetIntegerPluginInfoEntryWithDefault( "RenderHeight", 1080 )
        
        renderLayers = self.GetBooleanPluginInfoEntryWithDefault( "IncludeRenderLayers", False )
        includeAlpha = self.GetBooleanPluginInfoEntryWithDefault( "IncludeAlpha", False )
        
        overrideRenderPasses = self.GetBooleanPluginInfoEntryWithDefault( "OverrideRenderPasses", False )
        qualityType = self.GetPluginInfoEntryWithDefault( "QualityType", "Maximum Time" ).strip()

        renderScriptDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
        
        renderScript = Path.Combine(renderScriptDirectory,"KeyShot_RenderScript.py")
        
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        writer = StreamWriter( renderScript )
                
        writer.WriteLine()
        writer.WriteLine( "lux.openFile( \"%s\")" % sceneFilename )
        writer.WriteLine( "path = \"%s\"" % outputFilename )
        writer.WriteLine( "width = %s" % width )
        writer.WriteLine( "height = %s" % height )
        
        writer.WriteLine( "opts = lux.getRenderOptions()" )
        writer.WriteLine( "opts.setAddToQueue(False)" )

        writer.WriteLine( "opts.setOutputRenderLayers(%s)" % renderLayers )
        writer.WriteLine( "opts.setOutputAlphaChannel(%s)" % includeAlpha )
        
        overrideRenderPasses = self.GetBooleanPluginInfoEntryWithDefault( "OverrideRenderPasses", False )
        if overrideRenderPasses:           
            renderPassOptions = [
                ("IncludeDiffusePass", "setOutputDiffusePass"),
                ("IncludeReflectionPass", "setOutputReflectionPass"),
                ("IncludeClownPass", "setOutputClownPass"),
                ("IncludeLightingPass", "setOutputDirectLightingPass"),
                ("IncludeRefractionPass", "setOutputRefractionPass"),
                ("IncludeDepthPass", "setOutputDepthPass"),
                ("IncludeGIPass", "setOutputIndirectLightingPass"),
                ("IncludeShadowPass", "setOutputShadowPass"),
                ("IncludeGeometricNormalPass", "setOutputNormalsPass"),
                ("IncludeCausticsPass", "setOutputCausticsPass"),
                ("IncludeAOPass", "setOutputAmbientOcclusionPass")
            ]
            
            for pluginEntry, renderOption in renderPassOptions:
                writer.WriteLine( "try:" )
                writer.WriteLine( "    opts.%s(%s)" % (renderOption, self.GetBooleanPluginInfoEntryWithDefault(pluginEntry, False) ) )
                writer.WriteLine( "except AttributeError:" )
                writer.WriteLine( '   print( "Failed to set attribute: %s" )' % pluginEntry )
        
        if qualityType == "Maximum Time":
            writer.WriteLine( "opts.setMaxTimeRendering(%s)" % self.GetFloatPluginInfoEntryWithDefault( "MaxTime", 30 ) )
        elif qualityType == "Maximum Samples":
            writer.WriteLine( "opts.setMaxSamplesRendering(%s)" % self.GetIntegerPluginInfoEntryWithDefault( "ProgressiveMaxSamples", 16 ) )
        else:
            advancedRenderingOptions = [
                ( "AdvancedMaxSamples", "setAdvancedRendering", int, "16" ),
                ( "GlobalIllumination", "setGlobalIllumination", float, "1" ),
                ( "RayBounces", "setRayBounces", int, "6" ),
                ( "PixelBlur", "setPixelBlur", float, "1.5" ),
                ( "AntiAliasing", "setAntiAliasing", int, "1" ),
                ( "DepthOfField", "setDofQuality", int, "3" ),
                ( "Shadows", "setShadowQuality", float, "1" ),
                ( "Caustics", "setCausticsQuality", float, "1" ),
                ( "SharpShadows", "setSharpShadows", bool, "False" ),
                ( "SharperTextureFiltering", "setSharperTextureFiltering", bool, "False" ),
                ( "GICache", "setGlobalIlluminationCache", bool, "False" )
            ]
            
            for pluginEntry, renderOption, type, default in advancedRenderingOptions:
                writer.WriteLine( "try:" )
                writer.WriteLine( "    opts.%s( %s )" % (renderOption, type( self.GetPluginInfoEntryWithDefault( pluginEntry, default ) ) ) )
                writer.WriteLine( "except AttributeError:" )
                writer.WriteLine( '   print( "Failed to set attribute: %s" )' % pluginEntry )
        
        writer.WriteLine( "for frame in range( %d, %d ):" % ( startFrame, endFrame + 1 )  )
        writer.WriteLine( "    renderPath = path" )
        writer.WriteLine( "    renderPath =  renderPath.replace( \"%d\", str(frame) )" )
        writer.WriteLine( "    lux.setAnimationFrame( frame )" )
        writer.WriteLine( "    lux.renderImage(path = renderPath, width = width, height = height, opts = opts)" )
        writer.WriteLine( "    print(\"Rendered Image: \"+renderPath)" )
        
        #This only works for a script run from the command line. If run in the scripting console in Keyshot it instead just reloads python
        writer.WriteLine( "exit()" )
        writer.Close()
        
        arguments = []
        
        if self.GetBooleanConfigEntryWithDefault( "UseRenderNodeLicenses", False ):
            thisSlave = self.GetSlaveName().lower()
            proSlaveString = self.GetConfigEntryWithDefault( "ProSlaves", "" )
            proSlaves = [ proSlave.strip().lower() for proSlave in proSlaveString.split(",") ]
            
            if thisSlave in proSlaves:
                self.LogInfo( "This slave is in the pro license list - a KeyShot pro license will be used instead of a render node license" )
            else:
                arguments.append( "-keyshot_render_node" )
        
        
        arguments.append( "-script \"%s\"" % renderScript)
        
        return " ".join( arguments )
