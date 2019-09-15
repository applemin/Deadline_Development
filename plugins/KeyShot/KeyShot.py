import clr
import os
import shutil
import time
import sys
import subprocess

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

        self.StdoutHandling = True
        self.PopupHandling = True
        self.HandleQtPopups = True
        self.PopupMaxChildWindows = 25
        self.HandleWindows10Popups=True

        self.AddPopupHandler("FPS", "Are you sure you want to continue?", "Yes")


        #self.AddPopupHandler( r"KeyShot 7", "Close program" )
        #self.AddPopupHandler("KeyShot 7", "OK")
        #self.AddExitCodeToIgnore(-1)

    def RenderExecutable( self ):
        version = self.GetPluginInfoEntryWithDefault( "Version", "6" ).strip() #default to empty string (this should match pre-versioning config entries)
        
        keyshotExeList = self.GetConfigEntry( "RenderExecutable%s" % version )
        keyshotExe = FileUtils.SearchFileList( keyshotExeList )
        if( keyshotExe == "" ):
            self.FailRender( "KeyShot " + version + " render executable was not found in the semicolon separated list \"" + keyshotExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return keyshotExe
    
    def RenderArgument(self):


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

        multi_camera_rendering = self.GetBooleanPluginInfoEntryWithDefault("MultiCameraRendering", False)
        task_id = self.GetCurrentTaskId()

        if multi_camera_rendering:
            self.LogInfo("Multi Camera Rendering Activated.")
            camera = str(self.GetPluginInfoEntry("Camera" + str(task_id)))
            mpath = os.path.dirname(outputFilename)
            fname = os.path.basename(outputFilename)
            path, ext = os.path.splitext(fname)

            outputFilename = os.path.join(mpath, camera, str(path + "_" + str(camera) + ext)).replace("\\", "/")
        else:
            camera = self.GetPluginInfoEntryWithDefault("CameraName", "")

        writer = StreamWriter( renderScript )

        position = len(sceneFilename)-4

        temp_sceneFilename = sceneFilename[:position] + "_{}".format(camera) + "_{}".format(startFrame) + sceneFilename[position:]
        temp_sceneBaseFilename = os.path.basename(temp_sceneFilename)
                
        writer.WriteLine()
        writer.WriteLine()
        writer.WriteLine("import os")
        writer.WriteLine("import time")
        writer.WriteLine("import shutil")

        writer.WriteLine("HOME_PATH = os.path.join(os.environ['HOMEPATH'], 'Desktop', 'Temp')")
        writer.WriteLine("SCENE_FILE_PATH ='{}'".format(sceneFilename))
        writer.WriteLine("NEW_SCENE_FILE_NAME = os.path.basename(SCENE_FILE_PATH)")
        writer.WriteLine("NEW_TEMP_SCENE_FILE_NAME ='{}'".format(temp_sceneBaseFilename))

        writer.WriteLine("def valid_temp_folder():")
        writer.WriteLine("    if os.path.exists(HOME_PATH):")
        writer.WriteLine("        print('Temp folder has already been created.')")
        writer.WriteLine("        return True")
        writer.WriteLine("    else:")
        writer.WriteLine("        try:")
        writer.WriteLine("            os.makedirs(HOME_PATH)")
        writer.WriteLine("            print('Temp folder created successfully.')")
        writer.WriteLine("            return True")
        writer.WriteLine("        except:")
        writer.WriteLine("            print('Temp folder could not be created.')")
        writer.WriteLine("            return False")

        writer.WriteLine("def dir_update_check(NETWORK_FILE_DIR, DESTINATION_PATH):")
        writer.WriteLine("    NETWORK_FILE_DIR_LIST = os.listdir(NETWORK_FILE_DIR)")
        writer.WriteLine("    DESTINATION_PATH_LIST = os.listdir(DESTINATION_PATH)")

        writer.WriteLine("    if len(NETWORK_FILE_DIR_LIST) == len(DESTINATION_PATH_LIST) or len(NETWORK_FILE_DIR_LIST) < len(DESTINATION_PATH_LIST):")
        writer.WriteLine("        print('No directory update required.')")
        writer.WriteLine("        return True")
        writer.WriteLine("    else:")
        writer.WriteLine("        print('Directory update required.')")
        writer.WriteLine("        return False")

        writer.WriteLine("def file_transfer(SCENE_FILE_PATH):")
        writer.WriteLine("    NETWORK_FILE_DIR = os.path.dirname(SCENE_FILE_PATH)")
        writer.WriteLine("    NETWORK_DIR_NAME = os.path.basename(NETWORK_FILE_DIR)")
        writer.WriteLine("    DESTINATION_PATH = os.path.join(os.environ['HOMEPATH'], 'Desktop', 'Temp', NETWORK_DIR_NAME)")
        writer.WriteLine("    NEW_SCENE_PATH = os.path.join(DESTINATION_PATH, NEW_SCENE_FILE_NAME)")
        writer.WriteLine("    NEW_SCENE_TEMP_PATH = os.path.join(DESTINATION_PATH, NEW_TEMP_SCENE_FILE_NAME)")

        writer.WriteLine("    if os.path.exists(DESTINATION_PATH) and dir_update_check(NETWORK_FILE_DIR, DESTINATION_PATH):")
        writer.WriteLine("        print('Render folder has already been transferred , returning immediately .')")
        writer.WriteLine("        return NEW_SCENE_PATH, NEW_SCENE_TEMP_PATH")
        writer.WriteLine("    elif os.path.exists(DESTINATION_PATH) and not dir_update_check(NETWORK_FILE_DIR, DESTINATION_PATH):")
        writer.WriteLine("        shutil.rmtree(DESTINATION_PATH)")
        writer.WriteLine("        print('Render folder has been removed.')")

        writer.WriteLine("    if valid_temp_folder():")
        writer.WriteLine("        try:")
        writer.WriteLine("            shutil.copytree(NETWORK_FILE_DIR, DESTINATION_PATH)")
        writer.WriteLine("            print('Render folder transferred successfully.')")
        writer.WriteLine("        except:")
        writer.WriteLine("            print('Render folder could not be transferred.')")
        writer.WriteLine("    else:")
        writer.WriteLine("        print('File transfer failed')")

        writer.WriteLine("    return NEW_SCENE_PATH, NEW_SCENE_TEMP_PATH")

        writer.WriteLine("def main(scene_file_path, get_new_file_path):")
        writer.WriteLine("    lux.openFile(scene_file_path)")

        if camera != "":
            writer.WriteLine("    lux.setCamera(\"%s\")" % camera )

        writer.WriteLine("    lux.setAnimationFrame( %d )" % startFrame )
        writer.WriteLine("    width = %s" % width )
        writer.WriteLine("    height = %s" % height )
        if not multi_camera_rendering:
            writer.WriteLine("    lux.saveFile(get_new_file_path)")
            writer.WriteLine("    lux.openFile(get_new_file_path)")
        writer.WriteLine("    path = \"%s\"" % outputFilename )
        
        writer.WriteLine( "    opts = lux.getRenderOptions()" )
        writer.WriteLine( "    opts.setAddToQueue(False)" )

        writer.WriteLine( "    opts.setOutputRenderLayers(%s)" % renderLayers )
        writer.WriteLine( "    opts.setOutputAlphaChannel(%s)" % includeAlpha )
        
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
                writer.WriteLine( "    try:" )
                writer.WriteLine( "        opts.%s(%s)" % (renderOption, self.GetBooleanPluginInfoEntryWithDefault(pluginEntry, False) ) )
                writer.WriteLine( "    except AttributeError:" )
                writer.WriteLine( "        print( 'Failed to set attribute: %s' )" % pluginEntry )
        
        if qualityType == "Maximum Time":
            writer.WriteLine( "    opts.setMaxTimeRendering(%s)" % self.GetFloatPluginInfoEntryWithDefault( "MaxTime", 30 ) )
        elif qualityType == "Maximum Samples":
            writer.WriteLine( "    opts.setMaxSamplesRendering(%s)" % self.GetIntegerPluginInfoEntryWithDefault( "ProgressiveMaxSamples", 16 ) )
        else:
            advancedRenderingOptions = [
                ( "AdvancedMaxSamples", "setAdvancedRendering", int, "16" ),
                ( "RayBounces", "setRayBounces", int, "6" ),
                ( "AntiAliasing", "setAntiAliasing", int, "1" ),
                ( "Shadows", "setShadowQuality", float, "1" ),
            ]
            
            for pluginEntry, renderOption, type, default in advancedRenderingOptions:
                writer.WriteLine( "    try:" )
                writer.WriteLine( "        opts.%s( %s )" % (renderOption, type( self.GetPluginInfoEntryWithDefault( pluginEntry, default ) ) ) )
                writer.WriteLine( "    except AttributeError:" )
                writer.WriteLine( "           print( 'Failed to set attribute: %s' )" % pluginEntry )
        
        writer.WriteLine( "    for frame in range( %d, %d ):" % ( startFrame, endFrame + 1 )  )
        writer.WriteLine( "        renderPath = path" )
        writer.WriteLine( "        renderPath =  renderPath.replace( \"%d\", str(frame) )" )
        writer.WriteLine( "        lux.setAnimationFrame( frame )" )
        writer.WriteLine( "        lux.renderImage(path = renderPath, width = width, height = height, opts = opts)" )
        writer.WriteLine( "        print(\"Rendered Image: \"+renderPath)" )

        if not multi_camera_rendering:
            writer.WriteLine("    os.remove(get_new_file_path)")
        
        #This only works for a script run from the command line. If run in the scripting console in Keyshot it instead just reloads python
        writer.WriteLine("    print ('Job Completed')")
        writer.WriteLine("    exit()" )

        writer.WriteLine("GET_NEW_FILE_PATH, GET_NEW_TEMP_FILE_PATH = file_transfer(SCENE_FILE_PATH)")
        writer.WriteLine("print('GET_NEW_FILE_PATH ={}'.format(GET_NEW_FILE_PATH))")
        writer.WriteLine("print('GET_NEW_TEMP_FILE_PATH ={}'.format(GET_NEW_TEMP_FILE_PATH))")

        writer.WriteLine("if GET_NEW_FILE_PATH:")
        writer.WriteLine("    print('Starting new workflow...')")
        writer.WriteLine("    main(GET_NEW_FILE_PATH, GET_NEW_TEMP_FILE_PATH)")
        writer.WriteLine("else:")
        writer.WriteLine("    print('Switching to old workflow...')")
        writer.WriteLine("    main(SCENE_FILE_PATH)")
        
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
