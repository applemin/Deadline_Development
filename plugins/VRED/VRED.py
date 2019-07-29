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
    return VREDPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the VRED plugin.
######################################################################
class VREDPlugin( DeadlinePlugin ):

    qualityDict = {"Analytic Low":"VR_QUALITY_ANALYTIC_LOW", "Analytic High":"VR_QUALITY_ANALYTIC_HIGH", "Realistic Low":"VR_QUALITY_REALISTIC_LOW", "Realistic High":"VR_QUALITY_REALISTIC_HIGH", "Raytracing":"VR_QUALITY_RAYTRACING", "NPR":"VR_QUALITY_NPR" }

    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
    
    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple
        
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.StdoutHandling = True
        self.PopupHandling = True
        self.PopupMaxChildWindows = 25
    
        self.HandleQtPopups = True
        self.SetEnvironmentVariable("QT_USE_NATIVE_WINDOWS","1")

        # Set the stdout handlers.
        self.AddStdoutHandlerCallback(".*No valid license found.*").HandleCallback += self.HandleFatalError
        self.AddStdoutHandlerCallback(".*SyntaxError: invalid syntax.*").HandleCallback += self.HandleFatalError
        
        self.AddPopupHandler(".*Renderpasses activated.*", "qt_msgbox_buttonbox ")
        self.AddPopupIgnorer(".*Processing Sequence.*")
        self.AddPopupIgnorer(".*VREDPro.*")
        self.AddPopupIgnorer(".*Cluster.*")
        self.AddPopupIgnorer(".*Autodesk VRED Professional.*")
        self.AddPopupIgnorer(".*Autodesk VRED Server Node.*")
        self.AddPopupIgnorer(".*VREDServerNode*")
        self.AddPopupIgnorer(".*Pipe Configuration Wizard*")
        
    def PreRenderTasks( self ):
        self.LogInfo( "Slave Running as Service: %s" % self.IsRunningAsService() )

        if self.IsRunningAsService():
            self.LogWarning( "VRED can sometimes crash when running as a service. If VRED appears crashed, try running the Slave as a normal application instead of as a service to see if that fixes the problem." )

    def RenderExecutable( self ):
        version = self.GetPluginInfoEntryWithDefault( "Version", "9.0" ).strip() #default to empty string (this should match pre-versioning config entries)
        
        vredExeList = self.GetConfigEntry( "RenderExecutable%s" %  version.replace( ".", "_" ) )
        vredExe = FileUtils.SearchFileList( vredExeList )
        if( vredExe == "" ):
            self.FailRender( "VRED \"" + str(version) + "\" render executable was not found in the semicolon separated list \"" + vredExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return vredExe
    
    def RenderArgument( self ):
        version = self.GetFloatPluginInfoEntryWithDefault( "Version", 9.0 )
        
        self.LogInfo( "VRED Version: %s" % version )

        sceneFilename = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() ).strip().replace( "\\", "/" )
        sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename ).replace( "\\", "/" )
        if SystemUtils.IsRunningOnWindows() and sceneFilename.startswith( "/" ) and not sceneFilename.startswith( "//" ):
            sceneFilename = "/" + sceneFilename

        if not File.Exists( sceneFilename ):
            self.FailRender( "The VRED project file cannot be found. If it wasn't submitted with the job, then it needs to be in a location that is accessible to all Slaves. The VRED project file path is \"" + sceneFilename + "\"" )

        outputFilename = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip().replace( "\\", "/" )
        outputFilename = RepositoryUtils.CheckPathMapping( outputFilename ).replace( "\\", "/" )
        if SystemUtils.IsRunningOnWindows() and outputFilename.startswith( "/" ) and not outputFilename.startswith( "//" ):
            outputFilename = "/" + outputFilename
        
        renderScriptDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
        
        renderScript = Path.Combine(renderScriptDirectory,"VRED_RenderScript.py").strip().replace( "\\", "/" )
        renderScriptDirectory = renderScriptDirectory.replace("\\","\\\\")
        
        arguments = "\"" + sceneFilename + "\" "

        if version > 8 or ( version == 8 and SystemUtils.IsRunningOnLinux() ):
            arguments += "\"" + renderScript + "\" "
        else:
            arguments += "-postpython \"import sys;sys.path.append(\\\""+renderScriptDirectory+"\\\");from VRED_RenderScript import *;DeadlineRender()\" "
        
        arguments += "-nogui"

        writer = StreamWriter( renderScript )
        # Insert a blank line at top of py script to handle unicoding statements which are typically line: 1
        writer.WriteLine( "" )
        writer.WriteLine( "from vrSequencer import *" )
        writer.WriteLine( "from vrRenderQueue import *" )
        writer.WriteLine( "from vrController import *" )
        writer.WriteLine( "from vrMovieExport import *")
        writer.WriteLine( "from vrOSGWidget import *")
        if version > 9:
            writer.WriteLine( "from vrCamera import *")
        else:
            writer.WriteLine( "from vrCameraEditor import *")
        writer.WriteLine( "from vrRenderSettings import *")
        writer.WriteLine( "import traceback" )
        writer.WriteLine( "def DeadlineRender():" )
        writer.WriteLine( "    try:" ) 
        
        jobType = self.GetPluginInfoEntryWithDefault( "JobType", "Animation" )
        if jobType == "Render Queue":
            writer.WriteLine( "        print('Starting to render all jobs in the render queue')" )
            writer.WriteLine( "        runAllRenderJobs()" )
        elif jobType == "Sequencer":
            sequenceName = self.GetPluginInfoEntryWithDefault( "SequenceName", "" )
            if version == 7 or sequenceName == "":
                writer.WriteLine( "        print('Starting to run all Sequences')" )
                writer.WriteLine( "        runAllSequences()" )
            else:
                writer.WriteLine( "        print('Starting to run the following sequence: %s')" %sequenceName )
                writer.WriteLine( "        runSequence('%s')" % sequenceName )
        elif jobType == "Render":            
            view = self.GetPluginInfoEntryWithDefault( "View", "" )
            if not view == "":
                writer.WriteLine("        viewList = getViewpoints()" )
                writer.WriteLine("        if \""+view+"\" in viewList:")
                writer.WriteLine("            for innerView in viewList:")
                writer.WriteLine("                if not innerView == \""+view+"\":")
                writer.WriteLine("                    removeViewPoint(innerView)")
                writer.WriteLine("            jumpViewPoint(\""+view+"\")")
                writer.WriteLine("            selectViewPoint(\""+view+"\")")
                writer.WriteLine("            selectCamera(\"Perspective\")")
                writer.WriteLine("        else:")
                writer.WriteLine("            selectCamera(\""+view+"\")")
                
            renderQuality = self.GetPluginInfoEntryWithDefault("RenderQuality","Realistic High")
            writer.WriteLine("        setRenderQuality("+self.qualityDict[renderQuality]+")")
            
            width = self.GetIntegerPluginInfoEntryWithDefault("RenderWidth", 1920)
            height = self.GetIntegerPluginInfoEntryWithDefault("RenderHeight",1080)
            dpi = self.GetIntegerPluginInfoEntryWithDefault("DPI", 72)
            writer.WriteLine( "        setRenderPixelResolution(%s, %s, %s)" % ( width, height, dpi ) )
            
            isAnimation = self.GetBooleanPluginInfoEntryWithDefault( "RenderAnimation", False )
            
            isRegionRendering = self.GetBooleanPluginInfoEntryWithDefault( "RegionRendering", False )
            singleFrameRegionIndex = self.GetCurrentTaskId()
            
            if version > 8: 
                if isAnimation:
                    startFrame = self.GetStartFrame()
                    endFrame = self.GetEndFrame()
                    
                    animationClip = self.GetPluginInfoEntryWithDefault( "AnimationClip", "" )
                    animationType = self.GetIntegerPluginInfoEntryWithDefault( "AnimationType", 0 )
                    writer.WriteLine( "        setRenderAnimation(True)" )
                    writer.WriteLine( "        setRenderStartFrame(%s)" % startFrame )
                    writer.WriteLine( "        setRenderFrameStep(1)" )
                    writer.WriteLine( "        setRenderStopFrame(%s)" % endFrame )
                    writer.WriteLine( "        setRenderAnimationFormat(0)" )#0=images 1=video
                    writer.WriteLine( "        setRenderAnimationType(%s)" % animationType )#0=clip 1=timeline
                    writer.WriteLine( "        setRenderAnimationClip(\"%s\")" % animationClip )
                else:
                    writer.WriteLine( "        setRenderAnimation(False)" )
                
                alpha = self.GetBooleanPluginInfoEntryWithDefault("IncludeAlphaChannel",False)
                writer.WriteLine( "        setRenderAlpha(%s)" % alpha )
                
                overrideMetaData = self.GetBooleanPluginInfoEntryWithDefault("OverrideMetaData",False)
                if overrideMetaData:
                    metaDataOptions = [
                    ( "EmbedRenderSettings", 120 ),
                    ( "EmbedCameraSettings", 1 ),
                    ( "EmbedNodeVisibilities", 2 ),
                    ( "EmbedSwitchNodeStates", 4 ),
                    ( "EmbedSwitchMaterialStates", 128 )
                    ]
                    metaData = 0
                    
                    for metaDataOption, val in metaDataOptions:
                        if self.GetBooleanPluginInfoEntryWithDefault(metaDataOption,False):
                            metaData += val
                
                overrideRenderPasses = self.GetBooleanPluginInfoEntryWithDefault( "OverrideRenderPass", False )
                if overrideRenderPasses:
                    exportRenderPasses = self.GetBooleanPluginInfoEntryWithDefault("ExportRenderPass",False)
                    writer.WriteLine( "        setUseRenderPasses(%s)" % exportRenderPasses )
                    
                    rpOptions = [
                        ("BeautyPass","beauty"),
                        ("DiffuseIBLPass","diffuse_ibl"),
                        ("DiffuseLightPass","diffuse_light"),
                        ("DiffuseIndirectPass","diffuse_indirect"),
                        ("IncandescencePass","incandescence"),
                        ("GlossyIBLPass","glossy_ibl"),
                        ("GlossyLightPass","glossy_light"),
                        ("GlossyIndirectPass","glossy_indirect"),
                        ("TranslucentPass","translucency"),
                        ("TransparencyColorPass","transparency_color"),
                        ("OcclusionPass","occlusion"),
                        ("MaskPass","mask"),
                        ("MaterialIDPass","materialID"),
                        ("DepthPass","depth"),
                        ("NormalPass","normal"),
                        ("PositionPass","position"),
                        ("ViewVectorPass","view"),
                        ("DiffuseColorPass","diffuse_color"),
                        ("GlossyColorPass","glossy_color"),
                        ("SpecularColorPass","specular_color"),
                        ("TranslucencyColorPass","translucency_color"),
                        ("IBLDiffusePass","diffuse_ibl_illumination"),
                        ("LightsDiffusePass","diffuse_light_illumination"),
                        ("IndirectDiffusePass","diffuse_indirect_illumination"),
                        ("IBLGlossyPass","glossy_ibl_illumination"),
                        ("LightsGlossyPass","glossy_light_illumination"),
                        ("IndirectGlossyPass","glossy_indirect_illumination"),
                        ("IBLTranslucencyPass","translucency_ibl_illumination"),
                        ("LightTranslucencyPass","translucency_light_illumination"),
                        ("IndirectTranslucencyPass","translucency_indirect_illumination"),
                        ("IndirectSpecularPass","specular_indirect_illumination")
                    ]
                    rpArray = []
                    
                    for dlParam, rpassParam in rpOptions:
                        if self.GetBooleanPluginInfoEntryWithDefault( dlParam, False ):
                            rpArray.append(rpassParam)
                    writer.WriteLine( "        setRenderPasses(%s)"%str(rpArray) )                    
                
                bgRed = self.GetFloatPluginInfoEntryWithDefault("BackgroundRed",0.0)
                bgGreen = self.GetFloatPluginInfoEntryWithDefault("BackgroundGreen",0.0)
                bgBlue = self.GetFloatPluginInfoEntryWithDefault("BackgroundBlue",0.0)
                self.LogInfo("Unable to Update Background Color")
                #writer.WriteLine( "        setRenderBackgroundColor( %s, %s, %s )" % ( bgRed, bgGreen, bgBlue ) )
                
                alphaPreMult = self.GetBooleanPluginInfoEntryWithDefault("PremultiplyAlpha",False)
                writer.WriteLine( "        setRenderPremultiply(%s)" % alphaPreMult )
                
                tonemapHdr = self.GetBooleanPluginInfoEntryWithDefault("TonemapHDR",False)
                writer.WriteLine( "        setRenderTonemapHDR(%s)" % tonemapHdr )
                
                if isRegionRendering:
                    left = 0
                    right = 0
                    top = 0
                    bottom = 0
                    if isAnimation:
                        left = self.GetPluginInfoEntryWithDefault( "RegionLeft", "0" ).strip()
                        right = self.GetPluginInfoEntryWithDefault( "RegionRight", "0" ).strip()
                        bottom = self.GetPluginInfoEntryWithDefault( "RegionBottom", "0" ).strip()
                        top = self.GetPluginInfoEntryWithDefault( "RegionTop", "0" ).strip()
                        
                        regionID = self.GetPluginInfoEntryWithDefault( "RegionID", "0" ).strip()
                        file, ext = os.path.splitext( outputFilename )
                        outputFilename = file + "_region_" + regionID + "_" + ext
                        
                    else:
                        left = self.GetPluginInfoEntryWithDefault( "RegionLeft" + singleFrameRegionIndex, "0" )
                        right = self.GetPluginInfoEntryWithDefault( "RegionRight" + singleFrameRegionIndex, "0" )
                        bottom = self.GetPluginInfoEntryWithDefault( "RegionBottom" + singleFrameRegionIndex, "0" )
                        top = self.GetPluginInfoEntryWithDefault( "RegionTop" + singleFrameRegionIndex, "0" )
                        
                        file, ext = os.path.splitext( outputFilename )
                        outputFilename = file + "_region_" + singleFrameRegionIndex + "_" + ext
                        
                    writer.WriteLine( "        setUseRenderRegion( True )" )
                    writer.WriteLine( "        setRenderRegionStartX( " + left + " )" )
                    writer.WriteLine( "        setRenderRegionEndX( " + right + " )" )
                    writer.WriteLine( "        setRenderRegionStartY( " + bottom + " )" )
                    writer.WriteLine( "        setRenderRegionEndY( " + top + " )" )
                
                writer.WriteLine( "        setRenderFilename(\"" + outputFilename.replace( "\\", "\\\\" ) + "\")" )
                writer.WriteLine( "        print('Starting Render')" )
                writer.WriteLine( "        startRenderToFile(True)" )
            else:
            
                animation = self.GetPluginInfoEntryWithDefault( "AnimationClip", "" )
                width = self.GetIntegerPluginInfoEntryWithDefault("RenderWidth", 1920)
                height = self.GetIntegerPluginInfoEntryWithDefault("RenderHeight",1080)
                ssf = self.GetIntegerPluginInfoEntryWithDefault("SuperSamplingFactor",32)
                
                alpha = self.GetBooleanPluginInfoEntryWithDefault("IncludeAlphaChannel",False)
                embed = self.GetBooleanPluginInfoEntryWithDefault("EmbedMetaData",False)
                renderPasses = self.GetBooleanPluginInfoEntryWithDefault("ExportRenderPass",False)
                
                if alpha:
                    if outputFilename.endswith(".bmp") or outputFilename.endswith(".jpg") or outputFilename.endswith(".jpeg"):
                        alpha = False
                
                if embed:
                    if outputFilename.endswith(".png") or outputFilename.endswith(".jpg") or outputFilename.endswith(".tif"):
                        embedRenderSettings = str(self.GetBooleanPluginInfoEntryWithDefault("EmbedRenderSettings",False))
                        embedCameraSettings = str(self.GetBooleanPluginInfoEntryWithDefault("EmbedCameraSettings",False))
                        embedNodeVisibilities = str(self.GetBooleanPluginInfoEntryWithDefault("EmbedNodeVisibilities",False))
                        embedSwitchNodeStates = str(self.GetBooleanPluginInfoEntryWithDefault("EmbedSwitchNodeStates",False))
                        embedSwitchMaterialStates = str(self.GetBooleanPluginInfoEntryWithDefault("EmbedSwitchMaterialStates",False))
                        
                        writer.WriteLine( "        setSnapshotEmbedMetaData("+embedRenderSettings+", "+embedCameraSettings+", "+embedNodeVisibilities+", "+embedSwitchNodeStates+", "+embedSwitchMaterialStates+")" )
                        
                if renderPasses:
                    beauty = str(self.GetBooleanPluginInfoEntryWithDefault("BeautyPass",False))
                    diffuseIBL = str(self.GetBooleanPluginInfoEntryWithDefault("DiffuseIBLPass",False))
                    diffuseLight = str(self.GetBooleanPluginInfoEntryWithDefault("DiffuseLightPass",False))
                    glossyIBL = str(self.GetBooleanPluginInfoEntryWithDefault("GlossyIBLPass",False))
                    glossyLight = str(self.GetBooleanPluginInfoEntryWithDefault("GlossyLightPass",False))
                    specularReflection = str(self.GetBooleanPluginInfoEntryWithDefault("SpecularReflectionPass",False))
                    translucent = str(self.GetBooleanPluginInfoEntryWithDefault("TranslucentPass",False))
                    incandescence = str(self.GetBooleanPluginInfoEntryWithDefault("CombinedIncandescencePass",False))
                    diffuseIndirect = str(self.GetBooleanPluginInfoEntryWithDefault("DiffuseIndirectPass",False))
                    glossyIndirect = str(self.GetBooleanPluginInfoEntryWithDefault("GlossyIndirectPass",False))
                    transparencyColor = str(self.GetBooleanPluginInfoEntryWithDefault("TransparencyColorPass",False))
                    backgroundColor = str(self.GetBooleanPluginInfoEntryWithDefault("CombinedBackgroundColorPass",False))
                    
                    writer.WriteLine("        setCombinedChannelsRenderPasses("+beauty+", "+diffuseIBL+", "+diffuseLight+", "+glossyIBL+", "+glossyLight+", "+specularReflection+", "+translucent+", "+incandescence+", "+diffuseIndirect+", "+glossyIndirect+", "+transparencyColor+", "+backgroundColor+")")
                    
                    occlusion = str(self.GetBooleanPluginInfoEntryWithDefault("OcclusionPass",False))
                    normal = str(self.GetBooleanPluginInfoEntryWithDefault("NormalPass",False))
                    depth = str(self.GetBooleanPluginInfoEntryWithDefault("DepthPass",False))
                    materialID = str(self.GetBooleanPluginInfoEntryWithDefault("MaterialIDPass",False))
                    mask = str(self.GetBooleanPluginInfoEntryWithDefault("MaskPass",False))
                    position = str(self.GetBooleanPluginInfoEntryWithDefault("PositionPass",False))
                    viewVector = str(self.GetBooleanPluginInfoEntryWithDefault("ViewVectorPass",False))
                    
                    writer.WriteLine("        setAuxiliaryChannelsRenderPasses("+occlusion+", "+normal+", "+depth+", "+materialID+", "+mask+", "+position+", "+viewVector+")")
                    
                    diffuseColor = str(self.GetBooleanPluginInfoEntryWithDefault("DiffuseColorPass",False))
                    glossyColor = str(self.GetBooleanPluginInfoEntryWithDefault("GlossyColorPass",False))
                    specularColor = str(self.GetBooleanPluginInfoEntryWithDefault("SpecularColorPass",False))
                    translucencyColor = str(self.GetBooleanPluginInfoEntryWithDefault("TranslucencyColorPass",False))
                    
                    writer.WriteLine("        setMaterialChannelsRenderPasses("+diffuseColor+", "+glossyColor+", "+specularColor+", "+translucencyColor+", "+transparencyColor+")")
                    
                    IBLDiffuse = str(self.GetBooleanPluginInfoEntryWithDefault("IBLDiffusePass",False))
                    IBLGlossy = str(self.GetBooleanPluginInfoEntryWithDefault("IBLGlossyPass",False))
                    IBLTranslucency = str(self.GetBooleanPluginInfoEntryWithDefault("IBLTranslucencyPass",False))
                    lightsDiffuse = str(self.GetBooleanPluginInfoEntryWithDefault("LightsDiffusePass",False))
                    lightsGlossy = str(self.GetBooleanPluginInfoEntryWithDefault("LightsGlossyPass",False))
                    lightTranslucency = str(self.GetBooleanPluginInfoEntryWithDefault("LightTranslucencyPass",False))
                    indirectDiffuse = str(self.GetBooleanPluginInfoEntryWithDefault("IndirectDiffusePass",False))
                    indirectGlossy = str(self.GetBooleanPluginInfoEntryWithDefault("IndirectGlossyPass",False))
                    indirectSpecular = str(self.GetBooleanPluginInfoEntryWithDefault("IndirectSpecularPass",False))
                    indirectTranslucency = str(self.GetBooleanPluginInfoEntryWithDefault("IndirectTranslucencyPass",False))
                    
                    writer.WriteLine("        setIlluminationChannelsRenderPasses("+IBLDiffuse+", "+IBLGlossy+", "+IBLTranslucency+", "+lightsDiffuse+", "+lightsGlossy+", "+lightTranslucency+", "+indirectDiffuse+", "+indirectGlossy+", "+indirectSpecular+", "+indirectTranslucency+")")
                    
                bgRed = self.GetFloatPluginInfoEntryWithDefault("BackgroundRed",0.0)
                bgGreen = self.GetFloatPluginInfoEntryWithDefault("BackgroundGreen",0.0)
                bgBlue = self.GetFloatPluginInfoEntryWithDefault("BackgroundBlue",0.0)
                
                alphaPreMult = self.GetBooleanPluginInfoEntryWithDefault("PremultiplyAlpha",False)
                tonemapHdr = self.GetBooleanPluginInfoEntryWithDefault("TonemapHDR",False)
                
                if isRegionRendering:
                    left = 0
                    right = 0
                    top = 0
                    bottom = 0
                    if isAnimation:
                        left = self.Plugin.GetPluginInfoEntryWithDefault( "RegionLeft", "0" ).strip()
                        right = self.Plugin.GetPluginInfoEntryWithDefault( "RegionRight", "0" ).strip()
                        bottom = self.Plugin.GetPluginInfoEntryWithDefault( "RegionBottom", "0" ).strip()
                        top = self.Plugin.GetPluginInfoEntryWithDefault( "RegionTop", "0" ).strip()
                        
                        regionID = self.GetPluginInfoEntryWithDefault( "RegionID", "0" ).strip()
                        file, ext = os.path.splitext( outputFilename )
                        outputFilename = file + "_region_" + regionID + "_" + ext
                        
                    else:
                        left = self.Plugin.GetPluginInfoEntryWithDefault( "RegionLeft" + singleFrameRegionIndex, "0" )
                        right = self.Plugin.GetPluginInfoEntryWithDefault( "RegionRight" + singleFrameRegionIndex, "0" )
                        bottom = self.Plugin.GetPluginInfoEntryWithDefault( "RegionBottom" + singleFrameRegionIndex, "0" )
                        top = self.Plugin.GetPluginInfoEntryWithDefault( "RegionTop" + singleFrameRegionIndex, "0" )
                        
                        file, ext = os.path.splitext( outputFilename )
                        outputFilename = file + "_region_" + singleFrameRegionIndex + "_" + ext
                    
                    left = float( left ) / width
                    right = float( right ) / width
                    bottom = float( bottom ) / height 
                    top = float( top ) / height
                    
                    renderBottom = 1 - top
                    renderTop = 1 - bottom
                    
                    writer.WriteLine("        setRaytracingRenderRegion( " + left + ", "+right+", "+renderBottom+","+renderTop+" )")
                
                if isAnimation:
                    startFrame = str(self.GetStartFrame())
                    endFrame = str(self.GetEndFrame())
                    
                    writer.WriteLine("        renderAnimation(\""+animation+"\", \""+outputFilename.replace( "\\", "\\\\" )+"\", "+str(width)+", "+str(height)+", 25, "+startFrame+", "+endFrame+", "+str(ssf)+", "+str(alpha)+", "+str(bgRed)+", "+str(bgGreen)+", "+str(bgBlue) +", True, "+str(alphaPreMult)+", "+str(tonemapHdr)+")")
                else:
                    dpi = self.GetIntegerPluginInfoEntryWithDefault("DPI", 72)

                    writer.WriteLine("        createSnapshot(\""+outputFilename.replace( "\\", "\\\\" )+"\", "+str(width)+", "+str(height)+", "+str(ssf)+", "+str(alpha)+", "+str(bgRed)+", "+str(bgGreen)+", "+str(bgBlue)+ ", " + str(dpi) + ", True, False, "+str(alphaPreMult)+", "+str(tonemapHdr)+")")            
                
        writer.WriteLine( "    except:" )
        writer.WriteLine( "        print(traceback.format_exc())" )
        writer.WriteLine( "        crashVred(1)" ) #Crash quietly/no popups
        writer.WriteLine( "    finally:" )
        writer.WriteLine( "        terminateVred()" )
        
        if version > 8 or ( version == 8 and SystemUtils.IsRunningOnLinux() ):
            writer.WriteLine( "DeadlineRender()" )
        
        writer.Close()
        
        return arguments

    def HandleFatalError( self ):
        self.FailRender( self.GetRegexMatch(0) )
