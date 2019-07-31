import clr
import os
import shutil
import time
import sys
import subprocess

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

    MultiCameraRendering = None
    outputFilename = None
    RandomNumber = str(time.time()).split('.')[0]
    continueProgress = True
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PostRenderTasks
    def Cleanup( self ):

        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallbac

    def InitializeProcess( self ):
        self.PluginType = PluginType.Simple
        self.StdoutHandling = True


        #self.AddStdoutHandlerCallback(r"[A-Z]\w*\s([0-9]+)%*").HandleCallback += self.HandleStdoutProgress
        #self.AddStdoutHandlerCallback(r"'Job Started").HandleCallback += self.PreRenderTasks

    def RenderExecutable( self ):
        version = self.GetPluginInfoEntryWithDefault("version","7")  # default to empty string (this should match pre-versioning config entries)

        keyshotExeList = self.GetConfigEntry("RenderExecutable%s" % version)
        keyshotExe = FileUtils.SearchFileList(keyshotExeList)
        if (keyshotExe == ""):
            self.FailRender(
                "KeyShot " + version + " render executable was not found in the semicolon separated list \"" + keyshotExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor.")

        return keyshotExe



    def RenderArgument( self ):
        AnimationStill = self.GetBooleanPluginInfoEntryWithDefault("animation_still", False)
        SingleFrame = self.GetBooleanPluginInfoEntryWithDefault("single_frame", False)
        camera = self.GetPluginInfoEntry("Camera0")
        self.MultiCameraRendering = self.GetBooleanPluginInfoEntryWithDefault("MultiCameraRendering", False)
        regionRendering = self.GetBooleanPluginInfoEntryWithDefault("RegionRendering", False)
        #singleRegionJob = self.IsTileJob()  # Return bool
        singleRegionIndex = self.GetCurrentTaskId()  # Return str
        curTile = 0

        if regionRendering:
            currTile = singleRegionIndex
            reg_Left = int(self.GetFloatPluginInfoEntryWithDefault("RegionLeft" + str(singleRegionIndex), 0))
            reg_Width = int(self.GetFloatPluginInfoEntryWithDefault("RegionWidth" + str(singleRegionIndex), 0))
            reg_Top = int(self.GetFloatPluginInfoEntryWithDefault("RegionTop", 0))
            reg_Height = int(self.GetFloatPluginInfoEntryWithDefault("RegionHeight", 0))
            region_set = reg_Left, reg_Top, reg_Width, reg_Height

        sceneFilename = self.GetPluginInfoEntryWithDefault("SceneFile", self.GetDataFilename())
        sceneFilename = sceneFilename.replace("\\", "/")
        self.outputFilename = self.GetPluginInfoEntry("OutputFile")
        self.outputFilename = RepositoryUtils.CheckPathMapping(self.outputFilename)
        self.outputFilename = self.outputFilename.replace("\\", "/")

        if self.MultiCameraRendering:
            camera = str(self.GetPluginInfoEntry("Camera" + str(singleRegionIndex)))
            #path, ext = os.path.splitext(self.outputFilename)
            # print path
            # path = os.path.join(os.path.dirname(self.outputFilename), camera)
            # print path
            # self.outputFilename = os.path.join(path, "_", str(camera), ext)
            # print self.outputFilename
            mpath = os.path.dirname(self.outputFilename)
            fname = os.path.basename(self.outputFilename)
            path, ext = os.path.splitext(fname)

            self.outputFilename = os.path.join(mpath, camera, str(path + "_" + str(camera) + ext)).replace("\\", "/")
            print self.outputFilename

        jobName = self.GetJobInfoEntry("Name")

        if regionRendering:
            if self.outputFilename != "":
                path, ext = os.path.splitext(self.outputFilename)
                self.outputFilename = path + "_tile_" + str(currTile) + ext

        if regionRendering and not os.path.exists(os.path.join(os.path.dirname(sceneFilename), jobName + ".txt")):
            print("Region rendering is enabled but proper tile config file is not yet created.")
            tile_config_file = os.path.join(os.path.dirname(sceneFilename),"Tile_Config.txt")
            if os.path.exists(tile_config_file):
                print("Base tile config file found.")
                new_config_file = os.path.join(os.path.dirname(sceneFilename),"{}.txt".format(jobName))
                shutil.copyfile(tile_config_file, new_config_file)

                file = open(new_config_file, "a+")
                file.write("ImageFolder={}\n".format(os.path.dirname(self.outputFilename)))
                file.close()

        width = self.GetIntegerPluginInfoEntryWithDefault("render_width", 1920)
        height = self.GetIntegerPluginInfoEntryWithDefault("render_height", 1080)
        renderLayers = self.GetBooleanPluginInfoEntryWithDefault("output_render_layers", False)
        includeAlpha = self.GetBooleanPluginInfoEntryWithDefault("output_alpha_channel", False)
        render_mode = self.GetPluginInfoEntryWithDefault("render_mode","")
        render_mode_dict = {"0": "custom_control", "1": "maximum_time", "2": "maximum_samples"}
        qualityType = render_mode_dict[str(render_mode)]
        renderScriptDirectory = self.CreateTempDirectory("thread" + str(self.GetThreadNumber()))
        renderScript = Path.Combine(renderScriptDirectory, "KeyShot_RenderScript.py")
        startFrame = self.GetLongPluginInfoEntry("start_frame")
        endFrame = self.GetLongPluginInfoEntry("end_frame")

        if not SingleFrame:
            startFrame = self.GetStartFrame()
            endFrame = self.GetEndFrame()


        writer = StreamWriter(renderScript)

        if not regionRendering:
            file_dir = os.path.dirname(sceneFilename)
            file_name_ext = os.path.basename(sceneFilename)
            file_name, file_ext = os.path.splitext(file_name_ext)

            set_sceneFilename = file_name + "_" + self.RandomNumber + "_" + camera + "_" + str(startFrame) + "_" + file_ext
            temp_sceneFilename = os.path.join(file_dir, set_sceneFilename)



        writer.WriteLine()
        writer.WriteLine("print ('Job Started')")
        writer.WriteLine("import os")
        writer.WriteLine("import time")
        writer.WriteLine("import subprocess")
        writer.WriteLine("lux.openFile( \"%s\")" % sceneFilename)
        writer.WriteLine("lux.setCamera(\"%s\")" % camera)
        writer.WriteLine("lux.setAnimationFrame( %d )" % startFrame)

        if not regionRendering and not self.MultiCameraRendering and not SingleFrame:
            writer.WriteLine("lux.saveFile( \"%s\")" % temp_sceneFilename)
            writer.WriteLine("lux.openFile( \"%s\")" % temp_sceneFilename)
        writer.WriteLine("path = \"%s\"" % self.outputFilename)
        writer.WriteLine("width = %s" % width)
        writer.WriteLine("height = %s" % height)

        writer.WriteLine("opts = lux.getRenderOptions()")
        writer.WriteLine("opts.setAddToQueue(False)")
        if regionRendering:
            writer.WriteLine("opts.setRegion({})".format(region_set))
        writer.WriteLine("opts.setOutputRenderLayers(%s)" % renderLayers)
        writer.WriteLine("opts.setOutputAlphaChannel(%s)" % includeAlpha)

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

        writer.WriteLine("folder, filename = os.path.split(path)")
        if SingleFrame:

            #writer.WriteLine("opts.setBackgroundRendering(True)")
            # writer.WriteLine("for frame in range( %d, %d ):" % (startFrame, endFrame + 1))
            # writer.WriteLine("    renderPath = folder")
            # writer.WriteLine("    fileName = filename")
            # writer.WriteLine("    renderPath =  renderPath.replace( \"%d\", str(frame) )")
            # writer.WriteLine("    lux.setAnimationFrame( frame )")
            # writer.WriteLine("    lux.renderAnimation(folder = renderPath, frameFiles = fileName, width = width, height = height, opts = opts)")
            # writer.WriteLine("    print(\"Rendered Image: \"+renderPath)")
            writer.WriteLine("for frame in range( %d, %d ):" % (startFrame, endFrame + 1))
            writer.WriteLine("    renderPath = path")
            writer.WriteLine("    renderPath =  renderPath.replace( \"%d\", str(frame) )")
            writer.WriteLine("    lux.setAnimationFrame( frame )")
            writer.WriteLine("    lux.renderImage(path = renderPath, width = width, height = height, opts = opts)")
            writer.WriteLine("    print(\"Rendered Image: \"+renderPath)")


        if SingleFrame:
            writer.WriteLine("")
            writer.WriteLine("renderStat = False")
            writer.WriteLine("loopStat = True")
            writer.WriteLine("while(loopStat):")
            writer.WriteLine("  out=subprocess.Popen([r'C:/Users/mrb/AppData/Local/Programs/Python/Python37-32/python.exe',r'A:/ConsolePool/KeyshotProgress.py'],shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)")
            writer.WriteLine("  stdout,stderr = out.communicate()")
            writer.WriteLine("  if stdout:")
            writer.WriteLine("      renderStat = True")
            writer.WriteLine("      print(stdout.decode('utf-8'))")
            writer.WriteLine("  else:")
            writer.WriteLine("      if renderStat:")
            writer.WriteLine("          print ('Job Completed')")
            writer.WriteLine("          loopStat = False")
            #writer.WriteLine("          time.sleep(15)")
            #writer.WriteLine("          exit()")
            writer.WriteLine("  time.sleep(1)")
        
        if not regionRendering and not self.MultiCameraRendering and not SingleFrame:
            writer.WriteLine("os.remove( \"%s\")" % temp_sceneFilename)


        writer.WriteLine("exit()")

        arguments = " -script \"%s\"" % renderScript
        writer.Close()

        return arguments

    def PostRenderTasks(self):
        self.LogInfo( "Start Logging Progress Now..." )


        # if SingleFrame:
        #     writer.WriteLine("")
        #     writer.WriteLine("renderStat = False")
        #     writer.WriteLine("loopStat = True")
        #     writer.WriteLine("while(loopStat):")
        #     writer.WriteLine("  out=subprocess.Popen([r'C:/Users/mrb/AppData/Local/Programs/Python/Python37-32/python.exe',r'A:/ConsolePool/KeyshotProgress.py'],shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)")
        #     writer.WriteLine("  stdout,stderr = out.communicate()")
        #     writer.WriteLine("  if stdout:")
        #     writer.WriteLine("      renderStat = True")
        #     writer.WriteLine("      print(stdout.decode('utf-8'))")
        #     writer.WriteLine("  else:")
        #     writer.WriteLine("      if renderStat:")
        #     writer.WriteLine("          print ('Job Completed')")
        #     writer.WriteLine("          loopStat = False")
        #     #writer.WriteLine("          time.sleep(15)")
        #     #writer.WriteLine("          exit()")
        #     writer.WriteLine("  time.sleep(1)")

    def HandleStdoutProgress(self):

        # Set the progress to be the value of just the number
        self.SetProgress(float(self.GetRegexMatch(1)))
        # Set the status message to be the full line of output.
        self.SetStatusMessage(self.GetRegexMatch(0))