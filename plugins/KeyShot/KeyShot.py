import clr
import os
import shutil
import time
import sys
import subprocess
import json

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
    
    def RenderArgument( self ):

        ######################################################################
        ## get plugin and job entries
        ######################################################################

        sceneFilename           =self.GetPluginInfoEntry("SceneFile")
        sceneFilename           =sceneFilename.replace("\\", "/")
        outputFilename          =self.GetPluginInfoEntry("OutputFile")
        outputFilename          =outputFilename.replace("\\", "/")
        camera                  =self.GetPluginInfoEntryWithDefault( "CameraName", "" )
        width                   =self.GetIntegerPluginInfoEntryWithDefault( "RenderWidth", 1280 )
        height                  =self.GetIntegerPluginInfoEntryWithDefault( "RenderHeight", 720 )
        renderLayers            =self.GetBooleanPluginInfoEntryWithDefault( "IncludeRenderLayers", False )
        includeAlpha            =self.GetBooleanPluginInfoEntryWithDefault( "IncludeAlpha", False )
        overrideRenderPasses    =self.GetBooleanPluginInfoEntryWithDefault( "OverrideRenderPasses", False )
        qualityType             =self.GetPluginInfoEntryWithDefault( "QualityType", "Maximum Time" ).strip()
        startFrame              =self.GetStartFrame()
        endFrame                =self.GetEndFrame()
        maximumTime             =self.GetFloatPluginInfoEntryWithDefault( "MaxTime", 30 )
        maximumSamples          =self.GetIntegerPluginInfoEntryWithDefault( "ProgressiveMaxSamples", 16 )
        advancedMaxSamples      =self.GetIntegerPluginInfoEntryWithDefault( "AdvancedMaxSamples", 16 )
        rayBounces              =self.GetIntegerPluginInfoEntryWithDefault( "RayBounces", 16 )
        antiAliasing            =self.GetIntegerPluginInfoEntryWithDefault( "AntiAliasing", 16 )
        shadows                 =self.GetFloatPluginInfoEntryWithDefault( "Shadows", 1.0 )

        #renderScriptDirectory  =self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )

        # TODO: the temp scene file needs new implementation
        position = len(sceneFilename)-4
        temp_sceneFilename = sceneFilename[:position] + "_{}".format(camera) + "_{}".format(startFrame) + sceneFilename[position:]
        temp_sceneBaseFilename = os.path.basename(temp_sceneFilename)


        ######################################################################
        ## Constructing ENV file
        ######################################################################

        renderScript = os.path.join( self.GetPluginDirectory(), "KeyShot_Deadline.py" )

        INFO_FILE_LINE_DESC = {
            "ENV_SCENE_FILE_NAME":              sceneFilename,
            "ENV_TEMP_SCENE_BASE_FILE_NAME":    temp_sceneBaseFilename,
            "ENV_CAMERA":                       camera,
            "ENV_START_FRAME":                  startFrame,
            "ENV_END_FRAME":                    endFrame,
            "ENV_WIDTH":                        width,
            "ENV_HEIGHT":                       height,
            "ENV_OUTPUT_FILE_NAME":             outputFilename,
            "ENV_RENDER_LAYERS":                renderLayers,
            "ENV_INCLUDE_ALPHA":                includeAlpha,
            "ENV_OVERRIDE_RENDER_PASSES":       overrideRenderPasses,
            "ENV_MAXIMUM_TIME":                 maximumTime,
            "ENV_PROGRESSIVE_MAX_SAMPLES":      maximumSamples,
            "ENV_ADVANCED_MAX_SAMPLES":         advancedMaxSamples,
            "ENV_RAY_BOUNCES":                  rayBounces,
            "ENV_ANTI_ALIASING":                antiAliasing,
            "ENV_SHADOWS":                      shadows,
            "ENV_QUALITY_TYPE":                 qualityType}

        self.LogInfo("Contents of DEADLINE_KEYSHOT_INFO file:")

        with open(self.infoFilePath, 'w') as JsonData:
            json.dump(INFO_FILE_LINE_DESC, JsonData, indent=4)

        for key, value in INFO_FILE_LINE_DESC.items():
            self.LogInfo("\t%s=%s" % (key, value))

        # with open( self.infoFilePath, 'w' ) as fileHandle:
        #     for key, value in INFO_FILE_LINE_DESC.items():
        #         fileHandle.write( value + '\n' )
        #         self.LogInfo("\t%s=%s" % (line_desc, line))

        arguments = []
        arguments.append( "-script \"%s\"" % renderScript)
        
        return " ".join( arguments )

    def PreRenderTasks(self):

        self.infoFilePath = os.path.join( self.GetJobsDataDirectory(), "deadline_KeyShot_info.json" )
        self.SetEnvironmentVariable( "DEADLINE_KEYSHOT_INFO", self.infoFilePath )
        self.LogInfo( 'Setting DEADLINE_KEYSHOT_INFO environment variable to "%s"' % self.infoFilePath )

        self.LogInfo( "Starting KeyShot Job" )