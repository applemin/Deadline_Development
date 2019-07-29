import os
import hashlib

from System import *
from System.Collections.Specialized import *
from System.Diagnostics import *
from System.IO import *
from System.Text.RegularExpressions import *

from FranticX.Net import *
from FranticX.Processes import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return AutoCADPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
######################################################################
## This is the main DeadlinePlugin class for the AutoCAD plugin.
######################################################################
class AutoCADPlugin( DeadlinePlugin ):
    MyAutoCADController = None
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob
        
        
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.PluginType = PluginType.Advanced
        
    def Cleanup( self ):
        del self.InitializeProcessCallback
        
    ## Called by Deadline when the job is first loaded.
    def StartJob( self ):
        self.LogInfo( "Start Job called - starting up AutoCAD plugin" )
        
        self.MyAutoCADController = AutoCADController(self)
        
        # Initialize the AutoCAD controller.
        self.MyAutoCADController.Initialize()
        self.MyAutoCADController.slaveDirectory = self.GetSlaveDirectory()
        
        # Start AutoCAD.
        self.MyAutoCADController.StartAutoCAD()
        
    def RenderTasks( self ):
        self.LogInfo( "Render Tasks called" )
        self.MyAutoCADController.RenderTasks()
        
    def EndJob( self ):
        self.LogInfo( "End Job called - shutting down AutoCAD plugin" )
                
        if self.MyAutoCADController:
            # End the AutoCAD job (unloads the scene file, etc).
            self.MyAutoCADController.EndAutoCADJob()
        
class AutoCADController( object ):
    plugin = None
    ProgramName = "AutoCADProcess"
    
    AutoCADSocket = None
    AutoCADStartupFile = ""
    slaveDirectory = ""
    AutoCADFilename = ""
    AutoCADRenderExecutable = ""
    TempSceneFilename = ""
    
    ManagedAutoCADProcessRenderArgument = ""
    ManagedAutoCADProcessStartupDirectory = ""
    ManagedAutoCADProcessRenderExecutable = ""
    AuthentificationToken = ""
    
    LoadAutoCADTimeout = 45
    ProgressUpdateTimeout = 8000
    
    FunctionRegex = Regex( "FUNCTION: (.*)" )
    SuccessMessageRegex = Regex( "SUCCESS: (.*)" )
    SuccessNoMessageRegex = Regex( "SUCCESS" )
    CanceledRegex = Regex( "CANCELED" )
    ErrorRegex = Regex( "ERROR: (.*)" )
    
    StdoutRegex = Regex( "STDOUT: (.*)" )
    WarnRegex = Regex( "WARN: (.*)" )
    
    def __init__( self, plugin ):
        self.Plugin = plugin
        self.ProgramName = "AutoCADProcess"
    def Cleanup(self):
        pass
        
    ########################################################################
    ## Main functions (to be called from Deadline Entry Functions)
    ########################################################################
    # Reads in the plugin configuration settings and sets up everything in preparation to launch AutoCAD.
    # Also does some checking to ensure a AutoCAD job can be rendered on this machine.
    def Initialize( self ):
        # Read in the AutoCAD version.
        self.Version = self.Plugin.GetIntegerPluginInfoEntry( "Version" )
        if( self.Version < 2015 ):
            self.Plugin.FailRender( "Only Autodesk 2015 and later is supported" )
            
        # Figure out the render executable to use for rendering.
        renderExecutableKey = "RenderExecutable" + str(self.Version)
        
        lightningRepoPath = RepositoryUtils.GetRepositoryPath( "plugins/AutoCAD/LightningBundle", True )
        localPath = Path.Combine( "${AppData}", "Autodesk","ApplicationPlugins" )
        localPath = os.path.expandvars(localPath)
        self.LightningAutoUpdate(localPath,lightningRepoPath)
        
        renderExecutableList = self.Plugin.GetConfigEntry( renderExecutableKey ).strip()
        self.AutoCADRenderExecutable = FileUtils.SearchFileList( renderExecutableList )
        if( self.AutoCADRenderExecutable == "" ):
            self.Plugin.FailRender( "No AutoCAD" + self.Version + " render executable found in the semicolon separated list \"" + renderExecutableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
    
    
    def LightningAutoUpdate( self, localPath, repoPath ):
        updateNeeded = True
        if ( os.path.exists( localPath ) ):
            localHash = self.GetFileMD5Hash( os.path.join( localPath, "AutoCADLightning.bundle","Contents","AutoCADLightning.dll" ) )
            repoHash = self.GetFileMD5Hash( os.path.join( repoPath, "AutoCADLightning.bundle","Contents","AutoCADLightning.dll" ) )
            
            if ( localHash == repoHash ):
                updateNeeded = False
        else:
            os.makedirs( localPath )
        
        if ( updateNeeded ):
            self.directoryCopy(repoPath,localPath)
    
    def directoryCopy(self, source, dest):
        dirInfo = DirectoryInfo(source)
        dirs = dirInfo.GetDirectories()
    
        if not Directory.Exists(dest):
            Directory.CreateDirectory(dest)
            
        files = dirInfo.GetFiles()
        
        for file in files:
            temppath = Path.Combine(dest, file.Name);
            file.CopyTo(temppath, True);
        
        for subdir in dirs:
            temppath = Path.Combine(dest, subdir.Name)
            self.directoryCopy(subdir.FullName, temppath)    
    
    def GetFileMD5Hash( self, filename ):
        if ( os.path.isfile( filename ) ):
            fileHash = hashlib.md5()
            file = open( filename, 'r' )
            
            try:
                while True:
                    data = file.read( 1024 )
                    
                    if len(data)  == 0:
                        break
                        
                    fileHash.update( data )
                    
                return fileHash.hexdigest()
            finally:
                file.close()
                
        return None  
    
    def StartAutoCAD( self ):
        # Initialize the listening socket.
        self.AutoCADSocket = ListeningSocket()
        self.AutoCADSocket.StartListening( 0, True, True, 10 )
        if( not self.AutoCADSocket.IsListening ):
            self.Plugin.FailRender( "Failed to open a port for listening to the lightning AutoCAD daemon" )
        else:
            self.Plugin.LogInfo( "AutoCAD socket connection port: %d" % self.AutoCADSocket.Port )
        
        # Create the startup script which is executed by the callback in the AutoCAD startup scene file.
        self.CreateStartupScript( self.AutoCADSocket.Port )
        
        # Setup the command line parameters, and then start AutoCAD.

        sceneFilename = self.Plugin.GetPluginInfoEntryWithDefault( "SceneFile", self.Plugin.GetDataFilename() )
        sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename )
        
        tempSceneDirectory = self.Plugin.CreateTempDirectory( "thread" + str(self.Plugin.GetThreadNumber()) )

        if SystemUtils.IsRunningOnWindows():
            sceneFilename = sceneFilename.replace( "/", "\\" )
        else:
            sceneFilename = sceneFilename.replace( "\\", "/" )
            
        tempSceneFileName = Path.GetFileName( sceneFilename )
        self.TempSceneFilename = Path.Combine( tempSceneDirectory, tempSceneFileName )
            
        if SystemUtils.IsRunningOnWindows():
            self.TempSceneFilename = self.TempSceneFilename.replace( "/", "\\" )
            if sceneFilename.startswith( "\\" ) and not sceneFilename.startswith( "\\\\" ):
                sceneFilename = "\\" + sceneFilename
            if sceneFilename.startswith( "/" ) and not sceneFilename.startswith( "//" ):
                sceneFilename = "/" + sceneFilename
        else:
            self.TempSceneFilename = self.TempSceneFilename.replace( "\\", "/" )
        
        RepositoryUtils.CheckPathMappingInFileAndReplace( sceneFilename, self.TempSceneFilename,"" ,"")
        if SystemUtils.IsRunningOnLinux() or SystemUtils.IsRunningOnMac():
            os.chmod( self.TempSceneFilename, os.stat( sceneFilename ).st_mode )
        
        parameters = "\""+self.TempSceneFilename +"\" /b \""+self.AutoCADStartupFile+"\""
        
        self.Plugin.LogInfo("post Launch AutoCAD")
        
        self.Plugin.LogInfo("Parameters: "+parameters)
        self.LaunchAutoCAD( self.AutoCADRenderExecutable, parameters, Path.GetDirectoryName( self.AutoCADRenderExecutable ) )
        self.Plugin.LogInfo("post Launch AutoCAD")
        
        self.WaitForConnection( "AutoCAD startup" )
        self.Plugin.LogInfo("Connected to AutoCAD")
        self.AutoCADSocket.Send( "DeadlineStartup" )
    
    def RenderTasks(self):
        
        jobType = self.Plugin.GetPluginInfoEntryWithDefault("JobType","")
        
        if jobType == "Render":
            renderView = self.Plugin.GetPluginInfoEntryWithDefault("RenderView"+self.Plugin.GetCurrentTaskId(),"")
            #activeRenderPreset = self.Plugin.GetPluginInfoEntryWithDefault("RenderPreset","")
            renderHeight = self.Plugin.GetPluginInfoEntryWithDefault("RenderHeight","480")
            renderWidth = self.Plugin.GetPluginInfoEntryWithDefault("RenderWidth","640")
            outputFileName = self.Plugin.GetPluginInfoEntryWithDefault("OutputFileName","")
            
            renderProcedure = self.Plugin.GetPluginInfoEntryWithDefault("RenderProcedure","View")
            renderSelection = self.Plugin.GetPluginInfoEntryWithDefault("RenderSelection","")
            
            if renderView != "Current":
                self.AutoCADSocket.Send("ChangeView:"+renderView)
                name, ext = os.path.splitext(outputFileName)
                outputFileName = name+"_"+renderView+ext
            '''
            if activeRenderPreset == "DeadlineCustomPreset":
                setupPresetString = "BackFacesEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("BackFacesEnabled","False")
                setupPresetString += "|DiagnosticBackgroundEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("DiagnosticBackgroundEnabled","False")
                setupPresetString += "|DiagnosticBSPMode="+self.Plugin.GetPluginInfoEntryWithDefault("DiagnosticBSPMode","")
                setupPresetString += "|DiagnosticGridMode="+self.Plugin.GetPluginInfoEntryWithDefault("DiagnosticGridMode","False")
                setupPresetString += "|DiagnosticGridSize="+self.Plugin.GetPluginInfoEntryWithDefault("DiagnosticGridSize","False")
                setupPresetString += "|DiagnosticMode="+self.Plugin.GetPluginInfoEntryWithDefault("DiagnosticMode","False")
                setupPresetString += "|DiagnosticPhotonMode="+self.Plugin.GetPluginInfoEntryWithDefault("DiagnosticPhotonMode","False")
                setupPresetString += "|DisplayIndex="+self.Plugin.GetPluginInfoEntryWithDefault("DisplayIndex","False")
                setupPresetString += "|EnergyMultiplier="+self.Plugin.GetPluginInfoEntryWithDefault("EnergyMultiplier","False")
                setupPresetString += "|ExportMIEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("ExportMIEnabled","False")
                setupPresetString += "|FGRayCount="+self.Plugin.GetPluginInfoEntryWithDefault("FGRayCount","False")
                setupPresetString += "|FGSampleRadiusStateMin="+self.Plugin.GetPluginInfoEntryWithDefault("FGSampleRadiusStateMin","False")
                setupPresetString += "|FGSampleRadiusStateMax="+self.Plugin.GetPluginInfoEntryWithDefault("FGSampleRadiusStateMax","False")
                setupPresetString += "|FGSampleRadiusStatePixels="+self.Plugin.GetPluginInfoEntryWithDefault("FGSampleRadiusStatePixels","False")
                setupPresetString += "|FinalGatheringEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("FinalGatheringEnabled","False")
                setupPresetString += "|FinalGatheringMode="+self.Plugin.GetPluginInfoEntryWithDefault("FinalGatheringMode","False")
                setupPresetString += "|GIPhotonsPerLight="+self.Plugin.GetPluginInfoEntryWithDefault("GIPhotonsPerLight","False")
                setupPresetString += "|GISampleCount="+self.Plugin.GetPluginInfoEntryWithDefault("GISampleCount","False")
                setupPresetString += "|GISampleRadius="+self.Plugin.GetPluginInfoEntryWithDefault("GISampleRadius","False")
                setupPresetString += "|GISampleRadiusEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("GISampleRadiusEnabled","False")
                setupPresetString += "|GlobalIlluminationEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("GlobalIlluminationEnabled","False")
                setupPresetString += "|LightLuminanceScale="+self.Plugin.GetPluginInfoEntryWithDefault("LightLuminanceScale","False")
                setupPresetString += "|MaterialsEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("MaterialsEnabled","False")
                setupPresetString += "|MemoryLimit="+self.Plugin.GetPluginInfoEntryWithDefault("MemoryLimit","False")
                setupPresetString += "|PhotonTraceDepthReflection="+self.Plugin.GetPluginInfoEntryWithDefault("PhotonTraceDepthReflection","False")
                setupPresetString += "|PhotonTraceDepthRefraction="+self.Plugin.GetPluginInfoEntryWithDefault("PhotonTraceDepthRefraction","False")
                setupPresetString += "|PhotonTraceDepthSum="+self.Plugin.GetPluginInfoEntryWithDefault("PhotonTraceDepthSum","False")
                setupPresetString += "|PreviewImageFileName="+self.Plugin.GetPluginInfoEntryWithDefault("PreviewImageFileName","False")
                setupPresetString += "|RayTraceDepthReflection="+self.Plugin.GetPluginInfoEntryWithDefault("RayTraceDepthReflection","False")
                setupPresetString += "|RayTraceDepthRefraction="+self.Plugin.GetPluginInfoEntryWithDefault("RayTraceDepthRefraction","False")
                setupPresetString += "|RayTraceDepthSum="+self.Plugin.GetPluginInfoEntryWithDefault("RayTraceDepthSum","False")
                setupPresetString += "|RayTracingEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("RayTracingEnabled","False")
                setupPresetString += "|SamplingMin="+self.Plugin.GetPluginInfoEntryWithDefault("SamplingMin","False")
                setupPresetString += "|SamplingMax="+self.Plugin.GetPluginInfoEntryWithDefault("SamplingMax","False")
                setupPresetString += "|SamplingContrastColorRed="+self.Plugin.GetPluginInfoEntryWithDefault("SamplingContrastColorRed","False")
                setupPresetString += "|SamplingContrastColorGreen="+self.Plugin.GetPluginInfoEntryWithDefault("SamplingContrastColorGreen","False")
                setupPresetString += "|SamplingContrastColorBlue="+self.Plugin.GetPluginInfoEntryWithDefault("SamplingContrastColorBlue","False")
                setupPresetString += "|SamplingContrastColorAlpha="+self.Plugin.GetPluginInfoEntryWithDefault("SamplingContrastColorAlpha","False")
                setupPresetString += "|SamplingFilterType="+self.Plugin.GetPluginInfoEntryWithDefault("SamplingFilterType","False")
                setupPresetString += "|SamplingFilterWidth="+self.Plugin.GetPluginInfoEntryWithDefault("SamplingFilterWidth","False")
                setupPresetString += "|SamplingFilterHeight="+self.Plugin.GetPluginInfoEntryWithDefault("SamplingFilterHeight","False")
                setupPresetString += "|ShadowMapsEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("ShadowMapsEnabled","False")
                setupPresetString += "|ShadowMode="+self.Plugin.GetPluginInfoEntryWithDefault("ShadowMode","False")
                setupPresetString += "|ShadowSamplingMultiplier="+self.Plugin.GetPluginInfoEntryWithDefault("ShadowSamplingMultiplier","False")
                setupPresetString += "|ShadowsEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("ShadowsEnabled","False")
                setupPresetString += "|TextureSampling="+self.Plugin.GetPluginInfoEntryWithDefault("TextureSampling","False")
                setupPresetString += "|TileOrder="+self.Plugin.GetPluginInfoEntryWithDefault("TileOrder","False")
                setupPresetString += "|TileSize="+self.Plugin.GetPluginInfoEntryWithDefault("TileSize","False")
                
                self.AutoCADSocket.Send( "SetupPreset:"+setupPresetString )
                self.PollUntilComplete(False)
            
            
            if self.Plugin.GetBooleanPluginInfoEntryWithDefault("UseCustomSunSettings",False):
                setupSunString = "SunStatus="+self.Plugin.GetPluginInfoEntryWithDefault("SunStatus","0")
                setupSunString += "|SunIntensity="+self.Plugin.GetPluginInfoEntryWithDefault("SunIntensity","2")
                setupSunString += "|SunShadowsEnabled="+self.Plugin.GetPluginInfoEntryWithDefault("SunShadowsEnabled","False")
                setupSunString += "|SunSkyStatus="+self.Plugin.GetPluginInfoEntryWithDefault("SunSkyStatus","-1")
                setupSunString += "|SunSkyIntensity="+self.Plugin.GetPluginInfoEntryWithDefault("SunSkyIntensity","2")
                setupSunString += "|SunSkyHaze="+self.Plugin.GetPluginInfoEntryWithDefault("SunSkyHaze","2")
                setupSunString += "|SunHorizonHeight="+self.Plugin.GetPluginInfoEntryWithDefault("SunHorizonHeight","2")
                setupSunString += "|SunHorizonBlur="+self.Plugin.GetPluginInfoEntryWithDefault("SunHorizonBlur","2")
                setupSunString += "|SunGroundColorRed="+self.Plugin.GetPluginInfoEntryWithDefault("SunGroundColorRed","128")
                setupSunString += "|SunGroundColorBlue="+self.Plugin.GetPluginInfoEntryWithDefault("SunGroundColorBlue","128")
                setupSunString += "|SunGroundColorGreen="+self.Plugin.GetPluginInfoEntryWithDefault("SunGroundColorGreen","128")
                setupSunString += "|SunNightColorRed="+self.Plugin.GetPluginInfoEntryWithDefault("SunNightColorRed","128")
                setupSunString += "|SunNightColorBlue="+self.Plugin.GetPluginInfoEntryWithDefault("SunNightColorBlue","128")
                setupSunString += "|SunNightColorGreen="+self.Plugin.GetPluginInfoEntryWithDefault("SunNightColorGreen","128")
                setupSunString += "|SunAerialPerspective="+self.Plugin.GetPluginInfoEntryWithDefault("SunAerialPerspective","False")
                setupSunString += "|SunVisibilityDistance="+self.Plugin.GetPluginInfoEntryWithDefault("SunVisibilityDistance","1000")
                setupSunString += "|SunDiskScale="+self.Plugin.GetPluginInfoEntryWithDefault("SunDiskScale","4")
                setupSunString += "|SunDiskGlowIntensity="+self.Plugin.GetPluginInfoEntryWithDefault("SunDiskGlowIntensity","2")
                setupSunString += "|SunDiskIntensity="+self.Plugin.GetPluginInfoEntryWithDefault("SunDiskIntensity","2")
                setupSunString += "|SunDate="+self.Plugin.GetPluginInfoEntryWithDefault("SunDate","")
                setupSunString += "|SunTime="+self.Plugin.GetPluginInfoEntryWithDefault("SunTime","")
                setupSunString += "|SunDaylightSavings="+self.Plugin.GetPluginInfoEntryWithDefault("SunDaylightSavings","True")
                setupSunString += "|SunShadowType="+self.Plugin.GetPluginInfoEntryWithDefault("SunShadowType","Sampled")
                setupSunString += "|SunShadowSamples="+self.Plugin.GetPluginInfoEntryWithDefault("SunShadowSamples","16")
                setupSunString += "|SunShadowSoftness="+self.Plugin.GetPluginInfoEntryWithDefault("SunShadowSoftness","2")
                
                self.AutoCADSocket.Send( "SetupSun:"+setupPresetString )
                self.PollUntilComplete(False)
                
            if self.Plugin.GetBooleanPluginInfoEntryWithDefault("UseCustomFogSettings",False):
                setupFogString = "EnableFog=" + self.Plugin.GetPluginInfoEntryWithDefault("EnableFog","False")   
                setupFogString += "|FogColorRed=" + self.Plugin.GetPluginInfoEntryWithDefault("FogColorRed","128")
                setupFogString += "|FogColorGreen=" + self.Plugin.GetPluginInfoEntryWithDefault("FogColorGreen","128")
                setupFogString += "|FogColorBlue=" + self.Plugin.GetPluginInfoEntryWithDefault("FogColorBlue","128")
                setupFogString += "|FogBackground=" + self.Plugin.GetPluginInfoEntryWithDefault("FogBackground","False")
                setupFogString += "|FogNearDistance=" + self.Plugin.GetPluginInfoEntryWithDefault("FogNearDistance","0")
                setupFogString += "|FogFarDistance=" + self.Plugin.GetPluginInfoEntryWithDefault("FogFarDistance","10")
                setupFogString += "|FogNearPercentage=" + self.Plugin.GetPluginInfoEntryWithDefault("FogNearPercentage","0")
                setupFogString += "|FogFarPercentage=" + self.Plugin.GetPluginInfoEntryWithDefault("FogFarPercentage","10")
                self.AutoCADSocket.Send( "SetupFog:"+setupPresetString )
                self.PollUntilComplete(False)
                
            if self.Plugin.GetBooleanPluginInfoEntryWithDefault("UseCustomExposureSettings",False):
                setupExposureString = "ExposureBrightness="+self.Plugin.GetPluginInfoEntryWithDefault("ExposureBrightness","65")
                setupExposureString += "|ExposureContrast="+self.Plugin.GetPluginInfoEntryWithDefault("ExposureContrast","50")
                setupExposureString += "|ExposureMidTones="+self.Plugin.GetPluginInfoEntryWithDefault("ExposureMidTones","1.0")
                setupExposureString += "|ExposureDaylight="+self.Plugin.GetPluginInfoEntryWithDefault("ExposureDaylight","50")
                self.AutoCADSocket.Send( "SetupExposure:"+setupExposureString )
                self.PollUntilComplete(False)
            '''
            
            #self.AutoCADSocket.Send( "RenderToFile:renderpreset="+activeRenderPreset+"|width="+renderWidth+"|height="+renderHeight+"|filename="+outputFileName+"|renderprocedure="+renderProcedure+"|renderselection="+renderSelection)
            self.AutoCADSocket.Send( "RenderToFile:width="+renderWidth+"|height="+renderHeight+"|filename="+outputFileName+"|renderprocedure="+renderProcedure+"|renderselection="+renderSelection)
        elif jobType == "Plot":
        
            commandString = "PlotToFile:plotter="+self.Plugin.GetPluginInfoEntryWithDefault("Plotter","")
            commandString += "|plotarea="+self.Plugin.GetPluginInfoEntryWithDefault("PlotArea","Display")
            commandString += "|fitplotscale="+self.Plugin.GetPluginInfoEntryWithDefault("FitPlotScale","True")
            useDetailedConfig = self.Plugin.GetBooleanPluginInfoEntryWithDefault("UseDetailedPlotConfig",False)
            commandString += "|usedetailedplotconfig="+str(useDetailedConfig)
            if self.Plugin.GetBooleanPluginInfoEntryWithDefault("UsePaperSize",True):
                commandString += "|papersize="+self.Plugin.GetPluginInfoEntryWithDefault("PaperSize","")
            else:
                commandString += "|usepapersize=False"
                commandString += "|paperwidth="+self.Plugin.GetPluginInfoEntryWithDefault("PaperWidth","")
                commandString += "|paperheight="+self.Plugin.GetPluginInfoEntryWithDefault("PaperHeight","")
            commandString += "|plottedunitscale="+self.Plugin.GetPluginInfoEntryWithDefault("PlottedUnitScale","")
            commandString += "|drawingunitscale="+self.Plugin.GetPluginInfoEntryWithDefault("DrawingUnitScale","")
            commandString += "|plotstyletable="+self.Plugin.GetPluginInfoEntryWithDefault("PlotStyleTable","")
            commandString += "|uselineweights="+self.Plugin.GetPluginInfoEntryWithDefault("UseLineWeights","")
            commandString += "|scalelineweights="+self.Plugin.GetPluginInfoEntryWithDefault("ScaleLineWeights","")
            commandString += "|paperunits="+self.Plugin.GetPluginInfoEntryWithDefault("PaperUnits","")
            commandString+= "|filename="+self.Plugin.GetPluginInfoEntryWithDefault("PlotFilePrefix","")
            self.AutoCADSocket.Send( commandString )
            self.PollUntilComplete(False)
        elif jobType == "Export":
            exportFilename = self.Plugin.GetPluginInfoEntryWithDefault("ExportFilename","")
            
            commandString = "ExportFile:ExportFilename="+exportFilename
            extension = os.path.splitext(exportFilename)[1]
            if extension == ".dwf" or extension == ".dwfx" or extension == ".fbx" or extension == ".stl" or extension == ".dxx" or extension == ".iges" or extension == ".igs":
                commandString += "|Selection="+self.Plugin.GetPluginInfoEntryWithDefault("Selection","All")
            if extension == ".fbx":
                commandString += "|ExportAll="+self.Plugin.GetPluginInfoEntryWithDefault("ExportAll","True")
                commandString += "|ExportObjects="+self.Plugin.GetPluginInfoEntryWithDefault("ExportObjects","True")
                commandString += "|ExportLights="+self.Plugin.GetPluginInfoEntryWithDefault("ExportLights","True")
                commandString += "|ExportCameras="+self.Plugin.GetPluginInfoEntryWithDefault("ExportCameras","True")
                commandString += "|ExportMaterials="+self.Plugin.GetPluginInfoEntryWithDefault("ExportMaterials","True")
                commandString += "|HandleTextures="+self.Plugin.GetPluginInfoEntryWithDefault("HandleTextures","Embed")
            if extension == ".dwf" or extension == ".dwfx":
                commandString += "|ExportMaterials="+self.Plugin.GetPluginInfoEntryWithDefault("ExportMaterials","True")
            if extension == ".dgn":
                commandString += "|DGNVersion="+self.Plugin.GetPluginInfoEntryWithDefault("DGNVersion","V8")
                commandString += "|DGNConversionUnits="+self.Plugin.GetPluginInfoEntryWithDefault("DGNConversionUnits","Master")
                commandString += "|DGNMappingSetup="+self.Plugin.GetPluginInfoEntryWithDefault("DGNMappingSetup","Standard")
                commandString += "|DGNSeedFile="+self.Plugin.GetPluginInfoEntryWithDefault("DGNSeedFile","")
                
            self.AutoCADSocket.Send(commandString)
            self.PollUntilComplete(False)
            
        elif jobType == "Import":
            commandString = "ImportFile:ImportFileName="+self.Plugin.GetPluginInfoEntryWithDefault("ImportFileName"+self.Plugin.GetCurrentTaskId(),"")
            commandString += "|importLocationX="+self.Plugin.GetPluginInfoEntryWithDefault("importLocationX","0")
            commandString += "|importLocationY="+self.Plugin.GetPluginInfoEntryWithDefault("importLocationY","0")
            commandString += "|importLocationZ="+self.Plugin.GetPluginInfoEntryWithDefault("importLocationZ","0")
            commandString += "|importScale="+self.Plugin.GetPluginInfoEntryWithDefault("importScale","0")
            self.AutoCADSocket.Send( commandString )
            self.PollUntilComplete(False)
            
        self.AutoCADSocket.Send( "EndTask" )
        self.PollUntilComplete(False)
    
    # This tells AutoCAD to unload the current scene file.
    def EndAutoCADJob( self ):
        if( not self.Plugin.MonitoredManagedProcessIsRunning( self.ProgramName ) ):
            self.Plugin.LogWarning( "AutoCAD.exe was shut down before the proper shut down sequence" )
        else:
            response = ""
            
            # If an error occurs while sending EndJob, set the response so that we don't enter the while loop below.
            try:
                self.Plugin.LogInfo("Sending End Job")
                self.AutoCADSocket.Send( "EndJob" )
            except Exception as e:
                response = ( "ERROR: Error sending EndJob command: %s" % e.Message )
            
            countdown = 5000
            while( countdown > 0 and response == "" ):
                try:
                    countdown = countdown - 100
                    response = self.AutoCADSocket.Receive( 100 )
                    
                    # If this is a STDOUT message, print it out and reset 'response' so that we keep looping
                    match = self.StdoutRegex.Match( response )
                    if( match.Success ):
                        self.Plugin.LogInfo( match.Groups[ 1 ].Value )
                        response = ""
                    
                    # If this is a WARN message, print it out and reset 'response' so that we keep looping
                    match = self.WarnRegex.Match( response )
                    if( match.Success ):
                        self.Plugin.LogWarning( match.Groups[ 1 ].Value )
                        response = ""
                    
                except Exception as e:
                    if( not isinstance( e, SimpleSocketTimeoutException ) ):
                        response = ( "ERROR: Error when waiting for renderer to close: %s" % e.Message )
            
            if( response == "" ):
                self.Plugin.LogWarning( "Timed out waiting for the renderer to close." )
                
            if( response.startswith( "ERROR: " ) ):
                self.Plugin.LogWarning( response[7:] )
            
            if( not response.startswith( "SUCCESS" ) ):
                self.Plugin.LogWarning( "Did not receive a success message in response to EndJob: %s" % response )
        
        while self.Plugin.MonitoredManagedProcessIsRunning( self.ProgramName ):
            pass
        File.Delete( self.TempSceneFilename )
        
    def PollUntilComplete( self, timeoutEnabled, timeoutOverride=-1 ):
        #progressCountdown = self.ProgressUpdateTimeout * 1000
        progressCountdown = (self.ProgressUpdateTimeout if timeoutOverride < 0 else timeoutOverride) * 1000
        
        while( progressCountdown > 0 and self.AutoCADSocket.IsConnected and not self.Plugin.IsCanceled() ):
            try:
                # Verify that AutoCAD is still running.
                self.Plugin.VerifyMonitoredManagedProcess( self.ProgramName )
                self.Plugin.FlushMonitoredManagedProcessStdout( self.ProgramName )
                
                # Check for any popup dialogs.
                blockingDialogMessage = self.Plugin.CheckForMonitoredManagedProcessPopups( self.ProgramName )
                if( blockingDialogMessage != "" ):
                    self.Plugin.FailRender( blockingDialogMessage )
                
                # Only decrement the timeout value if timeouts are enabled
                if timeoutEnabled:
                    progressCountdown = progressCountdown - 500
                
                start = DateTime.Now.Ticks
                while( TimeSpan.FromTicks( DateTime.Now.Ticks - start ).Milliseconds < 500 ):
                    request = self.AutoCADSocket.Receive( 500 )
                    
                    # We received a request, so reset the progress update timeout.
                    progressCountdown = (self.ProgressUpdateTimeout if timeoutOverride < 0 else timeoutOverride) * 1000
                    
                    match = self.FunctionRegex.Match( request )
                    if( match.Success ):
                        # Call the lightning function handler method to see if we should reply or if the render is finished.
                        reply = ""
                        try:
                            reply = self.LightingFunctionHandler( match.Groups[ 1 ].Value )
                            if( reply != "" ):
                                self.AutoCADSocket.Send( reply )
                        except Exception as e:
                            self.Plugin.FailRender( e.Message )
                        continue
                    
                    match = self.SuccessMessageRegex.Match( request )
                    if( match.Success ): # Render finished successfully
                        return match.Groups[ 1 ].Value
                    
                    if( self.SuccessNoMessageRegex.IsMatch( request ) ): # Render finished successfully
                        return ""
                    
                    if( self.CanceledRegex.IsMatch( request ) ): # Render was canceled
                        self.Plugin.FailRender( "Render was canceled" )
                        continue
                    
                    match = self.ErrorRegex.Match( request )
                    if( match.Success ): # There was an error
                        self.Plugin.FailRender( "%s\n%s" % (match.Groups[ 1 ].Value, self.NetworkLogGet()) )
                        continue
                    
            except Exception as e:
                if( isinstance( e, SimpleSocketTimeoutException ) ):
                    if( progressCountdown <= 0 ):
                        if timeoutOverride < 0:
                            self.Plugin.FailRender( "Timed out waiting for the next progress update. The ProgressUpdateTimeout setting can be modified in the AutoCAD plugin configuration.\n%s" % self.NetworkLogGet() )
                        else:
                            self.Plugin.FailRender( "Timed out waiting for the next progress update.\n%s" % self.NetworkLogGet() )
                elif( isinstance( e, SimpleSocketException ) ):
                    self.Plugin.FailRender( "RenderTask: AutoCAD may have crashed (%s)" % e.Message )
                else:
                    self.Plugin.FailRender( "RenderTask: Unexpected exception (%s)" % e.Message )
        
        if( self.Plugin.IsCanceled() ):
            self.Plugin.FailRender( "Render was canceled" )
        
        if( not self.AutoCADSocket.IsConnected ):
            self.Plugin.FailRender( "Socket disconnected unexpectedly" )
        
        return "undefined"
        
    def LaunchAutoCAD( self, executable, arguments, startupDir ):
        self.ManagedAutoCADProcessRenderExecutable = executable
        self.ManagedAutoCADProcessRenderArgument = arguments
        self.ManagedAutoCADProcessStartupDirectory = startupDir
        
        self.AutoCADProcess = AutoCADProcess(self)
        self.Plugin.StartMonitoredManagedProcess( self.ProgramName, self.AutoCADProcess )
        self.Plugin.VerifyMonitoredManagedProcess( self.ProgramName )
        
    def CreateStartupScript( self, port ):
        self.AutoCADStartupFile = Path.Combine( PathUtils.GetSystemTempPath(), "AutoCAD_startup.scr" )
        self.AuthentificationToken = str( DateTime.Now.TimeOfDay.Ticks )
        writer = File.CreateText( self.AutoCADStartupFile )
        jobType = self.Plugin.GetPluginInfoEntryWithDefault("JobType","")
        #if (jobType == "Render"):
        #    writer.WriteLine("DEADLINERELOADFILE")
        writer.WriteLine("CONNECTTODEADLINESOCKET")
        writer.WriteLine(str(port))
        writer.WriteLine(self.AuthentificationToken)
        writer.Close()
    
    def WaitForConnection( self, errorMessageOperation ):
        countdown = self.LoadAutoCADTimeout * 1000
        receivedToken = ""
        
        while( countdown > 0 and not self.AutoCADSocket.IsConnected and not self.Plugin.IsCanceled() ):
            try:
                self.Plugin.VerifyMonitoredManagedProcess( self.ProgramName )
                self.Plugin.FlushMonitoredManagedProcessStdout( self.ProgramName )
                
                blockingDialogMessage = self.Plugin.CheckForMonitoredManagedProcessPopups( self.ProgramName )
                if( blockingDialogMessage != "" ):
                    self.Plugin.FailRender( blockingDialogMessage )
                    
                countdown = countdown - 500
                self.AutoCADSocket.WaitForConnection( 500, True )
                countdown = countdown - 3000
                receivedToken = self.AutoCADSocket.Receive( 3000 )
                
                if( receivedToken.startswith( "TOKEN:" ) ):
                    receivedToken = receivedToken[6:]
                else:
                    self.AutoCADSocket.Disconnect( False )
                self.Plugin.LogInfo("Received Token: "+receivedToken)
            except Exception as e:
                if( not isinstance( e, SimpleSocketTimeoutException ) ):
                    self.Plugin.FailRender( "%s: Error getting connection from AutoCAD: %s\n%s" % (errorMessageOperation, e.Message, self.NetworkLogGet()) )
            
            if( self.Plugin.IsCanceled() ):
                self.Plugin.FailRender( "%s: Initialization was canceled by Deadline" % errorMessageOperation )
        
        if( not self.AutoCADSocket.IsConnected ):
            if( countdown > 0 ):
                self.Plugin.FailRender( "%s: AutoCAD exited unexpectedly - check that AutoCAD starts up with no dialog messages\n%s" % (errorMessageOperation, self.NetworkLogGet()) )
            else:
                self.Plugin.FailRender( "%s: Timed out waiting for AutoCAD to start - consider increasing the LoadAutoCADTimeout in the AutoCAD plugin configuration\n%s" % (errorMessageOperation, self.NetworkLogGet()) )
    
######################################################################
## This is the class that starts up the AutoCAD process.
######################################################################
class AutoCADProcess( ManagedProcess ):
    AutoCADController = None
    
    def __init__( self, autoCADController ):
        self.AutoCADController = autoCADController
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.StartupDirectoryCallback += self.StartupDirectory
    
    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.StartupDirectoryCallback
    
    def InitializeProcess( self ):
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        self.PopupHandling = True
        self.HideDosWindow = False
        self.HandleQtPopups = True
        self.SetEnvironmentVariable("QT_USE_NATIVE_WINDOWS","1")
        
        self.AddPopupHandler( ".*License.*", "Close")
        self.AddPopupHandler( ".*Output file exists.*", "OK" )
        self.AddPopupHandler( ".*Drawing Recovery.*", "Close" )
        self.AddPopupHandler( ".*AutoCAD Error Report.*", "Close" )
        self.AddPopupHandler( ".*View 3D DWF.*", "No" )
        self.AddPopupHandler( ".*Import - Processing Background Job.*", "Close" )
        self.AddPopupHandler( ".*Export - Processing Background Job.*", "Close" )
        self.AddPopupHandler( "Export Data", "Save" )
        # self.AddPopupHandler( ".*AutoCAD Error Report.*", "Send Report" )
        # self.AddPopupHandler( ".*Drawing Recovery.*", "&Close;Close" )

    def RenderExecutable( self ):
        return self.AutoCADController.ManagedAutoCADProcessRenderExecutable
    
    def RenderArgument( self ):
        return self.AutoCADController.ManagedAutoCADProcessRenderArgument
    
    def StartupDirectory( self ):
        return self.AutoCADController.ManagedAutoCADProcessStartupDirectory