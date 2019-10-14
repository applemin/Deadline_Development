import clr
import os
import shutil
import time
import sys
import subprocess
import json
import datetime

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *
from Deadline.Plugins import *
from Deadline.Scripting import *
from FranticX.Processes import *

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
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.infoFilePath = ""

    def TempCleanup(self):
        s_temp_path = str(os.path.join(os.environ['HOMEPATH'], 'Desktop', 'Temp')).replace("\\", "/")
        self.LogInfo("Default Temp Folder Dir : " + s_temp_path)
        self.LogInfo("Running TempCleanup System")

        for dir in os.walk(s_temp_path):
            if dir[0] != s_temp_path:
                set_dir = dir[0]
                last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(set_dir))
                now_time = datetime.datetime.now()
                delta_time = now_time - last_modified

                if int(delta_time.days) >= 3:
                    try:
                        shutil.rmtree(set_dir, ignore_errors=True)
                    except:
                        pass
                    if not os.path.exists(set_dir):
                        self.LogInfo("[Deleted] Time Passed : %s >> Directory : %s " % (delta_time, set_dir))

    def Cleanup(self):

        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess( self ):

        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple

        self.StdoutHandling = True
        self.PopupHandling = True
        self.HandleQtPopups = True
        self.PopupMaxChildWindows = 25
        self.HandleWindows10Popups=True


    def RenderExecutable( self ):

        version = self.GetPluginInfoEntryWithDefault( "Version", "6" ).strip() #default to empty string (this should match pre-versioning config entries)
        
        keyshotExeList = self.GetConfigEntry( "RenderExecutable%s" % version )
        keyshotExe = FileUtils.SearchFileList( keyshotExeList )
        if( keyshotExe == "" ):
            self.FailRender( "KeyShot " + version + " render executable was not found in the semicolon separated list \"" + keyshotExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return keyshotExe
    
    def RenderArgument(self):

        self.TempCleanup()

        ######################################################################
        ## get plugin and job entries
        ######################################################################

        task_id                 = self.GetCurrentTaskId()
        sceneFilename           = self.GetPluginInfoEntry("SceneFile")
        sceneFilename           = sceneFilename.replace("\\", "/")
        outputFilename          = self.GetPluginInfoEntry("OutputFile")
        outputFilename          = outputFilename.replace("\\", "/")
        width                   = self.GetIntegerPluginInfoEntryWithDefault("RenderWidth", 1280)
        height                  = self.GetIntegerPluginInfoEntryWithDefault("RenderHeight", 720)
        renderLayers            = self.GetBooleanPluginInfoEntryWithDefault("IncludeRenderLayers", False)
        includeAlpha            = self.GetBooleanPluginInfoEntryWithDefault("IncludeAlpha", False)
        overrideRenderPasses    = self.GetBooleanPluginInfoEntryWithDefault("OverrideRenderPasses", False)
        qualityType             = self.GetPluginInfoEntryWithDefault("QualityType", "Maximum Time").strip()
        startFrame              = self.GetStartFrame()
        endFrame                = self.GetEndFrame()
        maximumTime             = self.GetFloatPluginInfoEntryWithDefault("MaxTime", 30 )
        maximumSamples          = self.GetIntegerPluginInfoEntryWithDefault("ProgressiveMaxSamples", 16)
        advancedMaxSamples      = self.GetIntegerPluginInfoEntryWithDefault("AdvancedMaxSamples", 16)
        rayBounces              = self.GetIntegerPluginInfoEntryWithDefault("RayBounces", 16)
        antiAliasing            = self.GetIntegerPluginInfoEntryWithDefault("AntiAliasing", 16)
        shadows                 = self.GetFloatPluginInfoEntryWithDefault("Shadows", 1.0)
        multiTaskRendering      = self.GetBooleanPluginInfoEntryWithDefault("MultiCameraRendering", False)

        if multiTaskRendering:
            camera              = self.GetPluginInfoEntryWithDefault("Camera" + str(task_id), str())
            outputDirectory     = os.path.dirname(outputFilename)
            sFileName, sExt     = os.path.splitext(os.path.basename(outputFilename))
            outputFilename      = os.path.join(outputDirectory, camera, str(sFileName + "_" + str(camera) + sExt))
        else:
            sOldKey = self.GetPluginInfoEntryWithDefault("CameraName", str())
            sNewKey = self.GetPluginInfoEntryWithDefault("Camera0", str())
            camera              = sOldKey or sNewKey or str()


        s_sceneFilename, s_ext = os.path.splitext(os.path.basename(sceneFilename))
        s_temp_sceneFilename = s_sceneFilename + "_{}".format(camera) + "_{}".format(startFrame) + s_ext


        ######################################################################
        ## Constructing ENV file
        ######################################################################

        renderScript = os.path.join( self.GetPluginDirectory(), "KeyShot_Deadline.py" )

        INFO_FILE_LINE_DESC = {
            "DAT_SCENE_FILE_NAME":              sceneFilename,
            "DAT_TEMP_SCENE_BASE_FILE_NAME":    s_temp_sceneFilename,
            "DAT_CAMERA":                       camera,
            "DAT_START_FRAME":                  startFrame,
            "DAT_END_FRAME":                    endFrame,
            "DAT_WIDTH":                        width,
            "DAT_HEIGHT":                       height,
            "DAT_OUTPUT_FILE_NAME":             outputFilename,
            "DAT_RENDER_LAYERS":                renderLayers,
            "DAT_INCLUDE_ALPHA":                includeAlpha,
            "DAT_OVERRIDE_RENDER_PASSES":       overrideRenderPasses,
            "DAT_MAXIMUM_TIME":                 maximumTime,
            "DAT_PROGRESSIVE_MAX_SAMPLES":      maximumSamples,
            "DAT_ADVANCED_MAX_SAMPLES":         advancedMaxSamples,
            "DAT_RAY_BOUNCES":                  rayBounces,
            "DAT_ANTI_ALIASING":                antiAliasing,
            "DAT_SHADOWS":                      shadows,
            "DAT_QUALITY_TYPE":                 qualityType,
            "DAT_MULTI_TASK_RENDERING":         multiTaskRendering}

        self.LogInfo("Contents of DEADLINE_KEYSHOT_INFO file:")
        self.LogInfo(self.infoFilePath)

        with open(self.infoFilePath, 'w') as JsonData:
            json.dump(INFO_FILE_LINE_DESC, JsonData, indent=4)

        for key, value in INFO_FILE_LINE_DESC.items():
            self.LogInfo("\t%s=%s" % (key, value))

        arguments = []
        arguments.append("-script \"%s\"" % renderScript)
        
        return " ".join(arguments)

    def PreRenderTasks(self):

        self.infoFilePath = os.path.join( self.GetJobsDataDirectory(), "deadline_KeyShot_info.json" )
        self.SetEnvironmentVariable( "DEADLINE_KEYSHOT_INFO", self.infoFilePath )
        self.LogInfo('Setting DEADLINE_KEYSHOT_INFO environment variable to "%s"' % self.infoFilePath )
