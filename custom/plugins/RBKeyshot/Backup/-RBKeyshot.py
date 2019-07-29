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
    return RB_KeyshotPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()


######################################################################
## This is the main DeadlinePlugin class for the KeyShot plugin.
######################################################################

class RB_KeyshotPlugin( DeadlinePlugin ):

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
        self.PluginType = PluginType.Simple

    def RenderExecutable( self ):
        return ""

    def RenderArgument( self ):
        return ""


    def RenderExecutable( self ):
        version = self.GetPluginInfoEntryWithDefault("version","7")  # default to empty string (this should match pre-versioning config entries)

        keyshotExeList = self.GetConfigEntry("RenderExecutable%s" % version)
        keyshotExe = FileUtils.SearchFileList(keyshotExeList)
        if (keyshotExe == ""):
            self.FailRender(
                "KeyShot " + version + " render executable was not found in the semicolon separated list \"" + keyshotExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor.")

        return keyshotExe

    def RenderArgument( self ):

        sceneFilename = self.GetPluginInfoEntryWithDefault("SceneFile", self.GetDataFilename())
        sceneFilename = sceneFilename.replace("\\", "/")

        outputFilename = self.GetPluginInfoEntry("OutputFile")
        outputFilename = RepositoryUtils.CheckPathMapping(outputFilename)
        outputFilename = outputFilename.replace("\\", "/")

        width = self.GetIntegerPluginInfoEntryWithDefault("render_width", 1920)
        height = self.GetIntegerPluginInfoEntryWithDefault("render_height", 1080)
        camera = self.GetPluginInfoEntryWithDefault("camera", "")

        renderLayers = self.GetBooleanPluginInfoEntryWithDefault("output_render_layers", False)
        includeAlpha = self.GetBooleanPluginInfoEntryWithDefault("output_alpha_channel", False)


        render_mode = self.GetPluginInfoEntryWithDefault("render_mode","")

        render_mode_dict = {"0": "custom_control", "1": "maximum_time", "2": "maximum_samples"}
        qualityType = render_mode_dict[str(render_mode)]


        #overrideRenderPasses = self.GetBooleanPluginInfoEntryWithDefault("OverrideRenderPasses", False)
        #qualityType = self.GetPluginInfoEntryWithDefault("QualityType", "Maximum Time").strip()

        renderScriptDirectory = self.CreateTempDirectory("thread" + str(self.GetThreadNumber()))

        renderScript = Path.Combine(renderScriptDirectory, "KeyShot_RenderScript.py")
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        # startFrame = self.GetPluginInfoEntryWithDefault("start_frame", 1)
        # endFrame = self.GetPluginInfoEntryWithDefault("end_frame", 1)
        writer = StreamWriter(renderScript)

        file_dir = os.path.dirname(sceneFilename)
        file_name_ext = os.path.basename(sceneFilename)
        file_name, file_ext = os.path.splitext(file_name_ext)

        set_sceneFilename = file_name + "_" + camera + "_" + str(startFrame) + "_" + file_ext
        temp_sceneFilename = os.path.join(file_dir, set_sceneFilename)

        # if abs(startFrame-endFrame) == 0:
        #     temp_sceneFilename += self.GetPluginInfoEntryWithDefault("camera", "")

        writer.WriteLine()
        writer.WriteLine("import os")
        writer.WriteLine("lux.openFile( \"%s\")" % sceneFilename)
        if camera != "":
            writer.WriteLine("lux.setCamera(\"%s\")" % camera)
        writer.WriteLine("lux.setAnimationFrame( %d )" % startFrame)
        writer.WriteLine("lux.saveFile( \"%s\")" % temp_sceneFilename)
        writer.WriteLine("lux.openFile( \"%s\")" % temp_sceneFilename)
        writer.WriteLine("path = \"%s\"" % outputFilename)
        writer.WriteLine("width = %s" % width)
        writer.WriteLine("height = %s" % height)

        writer.WriteLine("opts = lux.getRenderOptions()")
        writer.WriteLine("opts.setAddToQueue(False)")

        writer.WriteLine("opts.setOutputRenderLayers(%s)" % renderLayers)
        writer.WriteLine("opts.setOutputAlphaChannel(%s)" % includeAlpha)

        #overrideRenderPasses = self.GetBooleanPluginInfoEntryWithDefault("OverrideRenderPasses", False)
        #if overrideRenderPasses:
        renderPassOptions = [
            ("output_diffuse_pass", "setOutputDiffusePass"),
            ("output_reflection_pass", "setOutputReflectionPass"),
            ("output_clown_pass", "setOutputClownPass"),
            ("output_direct_lighting_pass", "setOutputDirectLightingPass"),
            ("output_refraction_pass", "setOutputRefractionPass"),
            ("output_depth_pass", "setOutputDepthPass"),
            ("output_indirect_lighting_pass", "setOutputIndirectLightingPass"),
            ("output_indirect_lighting_pass", "setOutputShadowPass"),
            ("output_normals_pass", "setOutputNormalsPass"),
            ("output_caustics_pass", "setOutputCausticsPass"),
            ("output_shadow_pass", "setOutputShadowPass"),
            ("output_ambient_occlusion_pass", "setOutputAmbientOcclusionPass")
        ]

        for pluginEntry, renderOption in renderPassOptions:
            writer.WriteLine("try:")
            writer.WriteLine(
                "    opts.%s(%s)" % (renderOption, self.GetBooleanPluginInfoEntryWithDefault(pluginEntry, False)))
            writer.WriteLine("except AttributeError:")
            writer.WriteLine('   print( "Failed to set render pass: %s" )' % pluginEntry)

        if qualityType == "maximum_time":
            writer.WriteLine("opts.setMaxTimeRendering(%s)" % self.GetFloatPluginInfoEntryWithDefault("progressive_max_time", 30))
        elif qualityType == "maximum_samples":
            writer.WriteLine(
                "opts.setMaxSamplesRendering(%s)" % self.GetIntegerPluginInfoEntryWithDefault("progressive_max_samples",
                                                                                              16))
        else:
            advancedRenderingOptions = [
                ("advanced_samples", "setAdvancedRendering", int, "16"),
                ("engine_global_illumination", "setGlobalIllumination", float, "1"),
                ("engine_ray_bounces", "setRayBounces", int, "6"),
                ("engine_pixel_blur", "setPixelBlur", float, "1.5"),
                ("engine_anti_aliasing", "setAntiAliasing", int, "1"),
                ("engine_dof_quality", "setDofQuality", int, "3" ),
                ("engine_shadow_quality", "setShadowQuality", float, "1"),
                ("engine_caustics_quality", "setCausticsQuality", float, "1"),
                ("engine_sharp_shadows", "setSharpShadows", bool, "False"),
                ("engine_sharper_texture_filtering", "setSharperTextureFiltering", bool, "False"),
                ("engine_global_illumination_cache", "setGlobalIlluminationCache", bool, "False")
            ]

            for pluginEntry, renderOption, type, default in advancedRenderingOptions:
                writer.WriteLine("try:")
                writer.WriteLine("    opts.%s( %s )" % (
                renderOption, type(self.GetPluginInfoEntryWithDefault(pluginEntry, default))))
                writer.WriteLine("except AttributeError:")
                writer.WriteLine('   print( "Failed to set render option: %s" )' % pluginEntry)

        writer.WriteLine("for frame in range( %d, %d ):" % (startFrame, endFrame + 1))
        writer.WriteLine("    renderPath = path")
        writer.WriteLine("    renderPath =  renderPath.replace( \"%d\", str(frame) )")
        writer.WriteLine("    lux.setAnimationFrame( frame )")
        writer.WriteLine("    lux.renderImage(path = renderPath, width = width, height = height, opts = opts)")
        writer.WriteLine("    print(\"Rendered Image: \"+renderPath)")
        writer.WriteLine("os.remove( \"%s\")" % temp_sceneFilename)

        # This only works for a script run from the command line. If run in the scripting console in Keyshot it instead just reloads python
        writer.WriteLine("exit()")

        arguments = " -script \"%s\"" % renderScript

        writer.Close()

        return arguments

