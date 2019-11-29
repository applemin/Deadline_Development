import clr
import os
import sys
import time
import json
import shutil
import datetime
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

class RB_KeyshotPlugin(DeadlinePlugin):

    d_render_mode = {"0": "custom_control",
                     "1": "maximum_time",
                     "2": "maximum_samples"}

    l_req_transfer = ["exr", "psd", "tif"]
    s_random = str(time.time()).split('.')[0]
    b_output_transfer = False
    d_transfer_data = {"src_path": str(),
                       "out_path": str()}
    s_job_name = str()

    def __init__(self):

        self.InitializeProcessCallback  += self.InitializeProcess
        self.RenderExecutableCallback   += self.RenderExecutable
        self.RenderArgumentCallback     += self.RenderArgument
        self.PreRenderTasksCallback     += self.PreRenderTasks
        self.PostRenderTasksCallback    += self.PostRenderTasks
        self.infoFilePath = str()

    def TempCleanup(self):
        s_temp_path = str(os.path.join(os.environ['HOMEPATH'], 'Desktop', 'Temp')).replace("\\", "/")
        self.LogInfo("Default Temp Folder Dir : " + s_temp_path)
        self.LogInfo("Running TempCleanup System")

        if not s_temp_path:
            self.LogWarning("temp directory not exists")
            return

        for dir in os.walk(s_temp_path):
            if dir[0] != s_temp_path:
                set_dir = dir[0]
                last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(set_dir))
                now_time = datetime.datetime.now()
                delta_time = now_time - last_modified

                if int(delta_time.days) >= 3:
                    try:
                        shutil.rmtree(set_dir, ignore_errors=True)
                    except OSError:
                        self.LogWarning("Directory : %s could not be deleted" % set_dir)
                    if not os.path.exists(set_dir):
                        self.LogInfo("[Deleted] Time Passed : %s >> Directory : %s " % (delta_time, set_dir))


    def RenderTempSetup(self):

        render_dir = str(os.path.join(os.environ['HOMEPATH'], 'Desktop', 'TempRender')).replace("\\", "/")
        if not os.path.exists(render_dir):
            try:
                os.mkdir(render_dir)
            except OSError:
                print ("Creation of the directory %s failed" % render_dir)
            else:
                print ("Successfully created the directory %s " % render_dir)

        return render_dir

    def Cleanup(self):

        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback

    def InitializeProcess(self):

        self.PluginType = PluginType.Simple
        self.StdoutHandling = True

    def RenderExecutable(self):
        version = self.GetPluginInfoEntryWithDefault("version","7")

        keyshotExeList = self.GetConfigEntry("RenderExecutable%s" % version)
        keyshotExe = FileUtils.SearchFileList(keyshotExeList)
        if (keyshotExe == ""):
            self.FailRender("KeyShot "
                            + version
                            + " render executable was not found in the semicolon separated list \""
                            + keyshotExeList)

        return keyshotExe

    def RenderArgument(self):

        currentJob = self.GetJob()
        self.s_job_name = str(currentJob.JobName)
        self.TempCleanup()
        s_temp_render_path = self.RenderTempSetup()

        ######################################################################
        ## get plugin and job entries
        ######################################################################
        s_task_id = self.GetCurrentTaskId()

        i_version                = self.GetIntegerPluginInfoEntry("version")

        i_start_frame            = self.GetLongPluginInfoEntry("start_frame")
        i_end_frame              = self.GetLongPluginInfoEntry("end_frame")

        s_render_region          = self.GetPluginInfoEntryWithDefault("region", None)
        s_camera_name            = self.GetPluginInfoEntryWithDefault("Camera0", str())
        s_model_set_name         = self.GetPluginInfoEntryWithDefault("active_model_set", str())

        s_scene_file_name        = self.GetPluginInfoEntryWithDefault("SceneFile", self.GetDataFilename())
        s_scene_file_name        = s_scene_file_name.replace("\\", "/")

        s_output_file_name       = self.GetPluginInfoEntry("OutputFile")
        i_output_id              = self.GetPluginInfoEntryWithDefault("output_id", "-1")
        s_output_file_name       = s_output_file_name.replace("\\", "/")
        s_temp_output            = os.path.join(s_temp_render_path, self.s_job_name)

        b_still_batch            = self.GetBooleanPluginInfoEntryWithDefault("still_batch", False)
        b_animation_batch        = self.GetBooleanPluginInfoEntryWithDefault("animation_batch", False)
        b_animation_still        = self.GetBooleanPluginInfoEntryWithDefault("animation_still", False)
        b_single_frame           = self.GetBooleanPluginInfoEntryWithDefault("single_frame", False)
        b_multi_task_rendering   = self.GetBooleanPluginInfoEntryWithDefault("multi_task_rendering", False)
        b_multi_camera_rendering = self.GetBooleanPluginInfoEntryWithDefault("MultiCameraRendering", False)
        b_region_rendering       = self.GetBooleanPluginInfoEntryWithDefault("RegionRendering", False)
        s_render_mode            = self.GetPluginInfoEntryWithDefault("render_mode", "1")

        f_maximum_time           = self.GetFloatPluginInfoEntryWithDefault("progressive_max_time", 30)

        i_width                  = self.GetIntegerPluginInfoEntryWithDefault("render_width", 1920)
        i_height                 = self.GetIntegerPluginInfoEntryWithDefault("render_height", 1080)
        i_max_samples            = self.GetIntegerPluginInfoEntryWithDefault("progressive_max_samples", 16)

        # get custom quality options
        setAdvancedRendering       = int  (self.GetPluginInfoEntryWithDefault("advanced_samples", "16"))
        setRayBounces              = int  (self.GetPluginInfoEntryWithDefault("engine_ray_bounces", "6"))
        setAntiAliasing            = int  (self.GetPluginInfoEntryWithDefault("engine_anti_aliasing", "1"))
        setDofQuality              = int  (self.GetPluginInfoEntryWithDefault("engine_dof_quality", "3"))
        setIndirectBounces         = int  (self.GetIntegerPluginInfoEntryWithDefault("engine_indirect_bounces", "1"))
        setSharpShadows            = bool (self.GetPluginInfoEntryWithDefault("engine_sharp_shadows", "False"))
        setSharperTextureFiltering = bool (self.GetPluginInfoEntryWithDefault("engine_sharper_texture_filtering", "False"))
        setGlobalIlluminationCache = bool (self.GetPluginInfoEntryWithDefault("engine_global_illumination_cache", "False"))
        setShadowQuality           = float(self.GetPluginInfoEntryWithDefault("engine_shadow_quality", "1.0"))
        setCausticsQuality         = float(self.GetPluginInfoEntryWithDefault("engine_caustics_quality", "1.0"))
        setPixelBlur               = float(self.GetPluginInfoEntryWithDefault("engine_pixel_blur", "1.5"))
        setGlobalIllumination      = float(self.GetPluginInfoEntryWithDefault("engine_global_illumination", "1.0"))

        # get render pass options
        setOutputRenderLayers           = self.GetBooleanPluginInfoEntryWithDefault("output_render_layers", False)
        setOutputAlphaChannel           = self.GetBooleanPluginInfoEntryWithDefault("output_alpha_channel", False)
        setOutputDiffusePass            = self.GetBooleanPluginInfoEntryWithDefault("output_diffuse_pass", False)
        setOutputReflectionPass         = self.GetBooleanPluginInfoEntryWithDefault("output_reflection_pass", False)
        setOutputClownPass              = self.GetBooleanPluginInfoEntryWithDefault("output_clown_pass", False)
        setOutputDirectLightingPass     = self.GetBooleanPluginInfoEntryWithDefault("output_direct_lighting_pass", False)
        setOutputRefractionPass         = self.GetBooleanPluginInfoEntryWithDefault("output_refraction_pass", False)
        setOutputDepthPass              = self.GetBooleanPluginInfoEntryWithDefault("output_depth_pass", False)
        setOutputIndirectLightingPass   = self.GetBooleanPluginInfoEntryWithDefault("output_indirect_lighting_pass", False)
        setOutputNormalsPass            = self.GetBooleanPluginInfoEntryWithDefault("output_normals_pass", False)
        setOutputCausticsPass           = self.GetBooleanPluginInfoEntryWithDefault("output_caustics_pass", False)
        setOutputShadowPass             = self.GetBooleanPluginInfoEntryWithDefault("output_shadow_pass", False)
        setOutputAmbientOcclusionPass   = self.GetBooleanPluginInfoEntryWithDefault("output_ambient_occlusion_pass", False)

        # extract data from keys
        l_region_data            = [int(s) for s in str(s_render_region).split('"') if s.isdigit()]
        s_quality_type           = self.d_render_mode[str(s_render_mode)]

        if b_multi_camera_rendering:

            s_camera_name       = self.GetPluginInfoEntryWithDefault("Camera" + str(s_task_id), str())
            s_output_directory  = os.path.dirname(s_output_file_name)
            s_file_name, s_ext  = os.path.splitext(os.path.basename(s_output_file_name))
            s_output_file_name  = os.path.join(s_output_directory,
                                               s_camera_name,
                                               str(s_file_name + "_" + str(s_camera_name) + s_ext))

            s_output_file_name  = s_output_file_name.replace("\\", "/")
            self.LogInfo("Multitask : %s | Output path : %s" % (b_multi_camera_rendering, s_output_file_name))


        if not b_single_frame:
            # TODO : this needs testing
            i_start_frame = self.GetStartFrame()
            i_end_frame   = self.GetEndFrame()


        if b_still_batch:
            self.b_output_transfer=True
            s_camera_name       = self.GetPluginInfoEntryWithDefault("camera_batch" + str(s_task_id), str())
            s_model_set_name    = self.GetPluginInfoEntryWithDefault("moldelset_batch" + str(s_task_id), str())
            s_output_directory  = os.path.dirname(s_output_file_name)
            s_file_name, s_ext  = os.path.splitext(os.path.basename(s_output_file_name))
            # s_output_file_name  = os.path.join(s_output_directory,
            #                                    s_camera_name + "_" + s_model_set_name,
            #                                    str(s_file_name + s_ext))
            s_output_file_name  = os.path.join(s_temp_render_path,
                                               s_camera_name + "_" + s_model_set_name,
                                               str(s_file_name + s_ext))

            self.d_transfer_data["src_path"] = os.path.dirname(s_output_file_name)
            self.d_transfer_data["out_path"] = os.path.dirname(s_output_directory)

        if b_animation_batch:
            s_camera_name       = self.GetPluginInfoEntryWithDefault("active_camera", str())
            s_model_set_name    = self.GetPluginInfoEntryWithDefault("active_model_set", str())


        s_scene_name, s_ext = os.path.splitext(os.path.basename(s_scene_file_name))
        s_temp_scene_file_name = s_scene_name + "_{}".format(self.s_random) + "_{}".format(str(i_start_frame)) + s_ext


        ######################################################################
        ## Constructing ENV file
        ######################################################################

        renderScript = os.path.join(self.GetPluginDirectory(), "KeyShot_Deadline.py")

        d_data_file = {
            "version":                          i_version,
            "output_id":                        i_output_id,
            "DAT_SCENE_FILE_NAME":              s_scene_file_name,
            "DAT_TEMP_SCENE_BASE_FILE_NAME":    s_temp_scene_file_name,
            "DAT_CAMERA":                       s_camera_name,
            "DAT_MODEL_SET":                    [s_model_set_name],
            "DAT_START_FRAME":                  i_start_frame,
            "DAT_END_FRAME":                    i_end_frame,
            "DAT_WIDTH":                        i_width,
            "DAT_HEIGHT":                       i_height,
            "DAT_OUTPUT_FILE_NAME":             s_output_file_name,
            "DAT_MAXIMUM_TIME":                 f_maximum_time,
            "DAT_PROGRESSIVE_MAX_SAMPLES":      i_max_samples,
            "DAT_QUALITY_TYPE":                 s_quality_type,  # TODO: check for "advanced mode"
            "DAT_MULTI_CAMERA_RENDERING":       b_multi_camera_rendering,
            "DAT_MULTI_TASK_RENDERING":         b_multi_task_rendering,
            "DAT_REGION_DATA":                  l_region_data,
            "setAdvancedRendering":             setAdvancedRendering,
            "setGlobalIllumination":            setGlobalIllumination,
            "setRayBounces":                    setRayBounces,
            "setPixelBlur":                     setPixelBlur,
            "setAntiAliasing":                  setAntiAliasing,
            "setDofQuality":                    setDofQuality,
            "setShadowQuality":                 setShadowQuality,
            "setCausticsQuality":               setCausticsQuality,
            "setSharpShadows":                  setSharpShadows,
            "setSharperTextureFiltering":       setSharperTextureFiltering,
            "setGlobalIlluminationCache":       setGlobalIlluminationCache,
            "setIndirectBounces":               setIndirectBounces,
            "setOutputRenderLayers":            setOutputRenderLayers,
            "setOutputAlphaChannel":            setOutputAlphaChannel,
            "setOutputDiffusePass":             setOutputDiffusePass,
            "setOutputReflectionPass":          setOutputReflectionPass,
            "setOutputClownPass":               setOutputClownPass,
            "setOutputDirectLightingPass":      setOutputDirectLightingPass,
            "setOutputRefractionPass":          setOutputRefractionPass,
            "setOutputDepthPass":               setOutputDepthPass,
            "setOutputIndirectLightingPass":    setOutputIndirectLightingPass,
            "setOutputNormalsPass":             setOutputNormalsPass,
            "setOutputCausticsPass":            setOutputCausticsPass,
            "setOutputShadowPass":              setOutputShadowPass,
            "setOutputAmbientOcclusionPass":    setOutputAmbientOcclusionPass}

        self.LogInfo("Contents of DEADLINE_KEYSHOT_INFO file:")
        self.LogInfo(self.infoFilePath)

        with open(self.infoFilePath, 'w') as JsonData:
            json.dump(d_data_file, JsonData, indent=4)

        for key, value in sorted(d_data_file.items()):
            self.LogInfo("\t%s=%s" % (key, value))

        arguments = " -script \"%s\"" % renderScript

        return arguments

    def PreRenderTasks(self):
        self.LogInfo("Running PreRenderTasks")
        self.infoFilePath = os.path.join( self.GetJobsDataDirectory(), "deadline_KeyShot_info.json")
        self.SetEnvironmentVariable("DEADLINE_KEYSHOT_INFO", self.infoFilePath)
        self.LogInfo('Setting DEADLINE_KEYSHOT_INFO environment variable to "%s"' % self.infoFilePath)

    def PostRenderTasks(self):
        self.LogInfo("Running PostRenderTasks")
        if self.b_output_transfer:
            self.OutputTransfer(self.d_transfer_data["src_path"], self.d_transfer_data["out_path"])

    def OutputTransfer(self, src_path, out_path):

        o_package = shutil.make_archive(src_path, 'zip', os.path.dirname(src_path), self.s_job_name)
        shutil.move(o_package, out_path)
