from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return VuePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Vue plugin.
######################################################################
class VuePlugin(DeadlinePlugin):
    
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
    
    def InitializeProcess(self):
        # Set the process specific settings.
        self.StdoutHandling = True
        self.PopupHandling = True
        
        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( "Error:.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "Unable to initialize application" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "Error writing file.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "Rendering... ([0-9]+\.[0-9]+)%" ).HandleCallback += self.HandleStdoutStillRendering
        self.AddStdoutHandlerCallback( "Rendering frame ([0-9]+)... ([0-9]+\.[0-9]+)%" ).HandleCallback += self.HandleStdoutAnimationRendering
        
        # Handle Vue 8 xStream "Welcome New User!" Dialog in GUI / Workstation mode
        self.AddPopupHandler( ".*Welcome To Vue 8 xStream!.*", "Don't show this dialog again;Close" )
        self.AddPopupHandler( ".*Welcome To Vue 8.5 xStream!.*", "Don't show this dialog again;Close" )
        
        # Handle Vue 8 xStream Dialog: Switching to OpenGL Engine when an incompatible graphics card is detected
        self.AddPopupHandler( ".*Vue 8 xStream.*", "OK" )
        self.AddPopupHandler( ".*Vue 8.5 xStream.*", "OK" )
        
    def RenderArgument(self):
        sceneFile = self.GetPluginInfoEntryWithDefault("SceneFile",self.GetDataFilename())
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        overrideOutput = self.GetBooleanPluginInfoEntry("OverrideOutputBox")
        outputPath = ""
        arguments = ""
        
        if overrideOutput:
            outputPath = self.GetPluginInfoEntryWithDefault( "OutputPath", "" ).strip()
            outputPath = RepositoryUtils.CheckPathMapping( outputPath )
            outputPath = PathUtils.ToPlatformIndependentPath( outputPath )
        
        if SystemUtils.IsRunningOnWindows():
            sceneFile = sceneFile.replace( "/", "\\" )
            if sceneFile.startswith( "\\" ) and not sceneFile.startswith( "\\\\" ):
                sceneFile = "\\" + sceneFile
        else:
            sceneFile = sceneFile.replace( "\\", "/" )
        
        arguments = " -file \"" + sceneFile + "\""
        if not outputPath == "":
            arguments = " -output \"{}\" -file \"{}\"".format(outputPath, sceneFile)
            
        # If not rendering an animation sequence, don't include the -frame option.
        if self.GetBooleanPluginInfoEntryWithDefault("Animation",True):
            arguments += " -range " + str(self.GetStartFrame()) + " " + str(self.GetEndFrame())
            
        return arguments
        
    def RenderExecutable(self):
        version = self.GetIntegerPluginInfoEntryWithDefault( "Version", 7 )
        
        vueExe = ""
        vueExeList = self.GetConfigEntry( "Vue" + str(version) + "_RenderExecutable" )
        
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        if(SystemUtils.IsRunningOnWindows()):
            if build == "32bit":
                vueExe = FileUtils.SearchFileListFor32Bit( vueExeList )
                if( vueExe == "" ):
                    self.LogWarning( "32 bit Vue " + str(version) + " render executable was not found in the semicolon separated list \"" + vueExeList + "\". Checking for any executable that exists instead." )
            elif build == "64bit":
                vueExe = FileUtils.SearchFileListFor64Bit( vueExeList )
                if( vueExe == "" ):
                    self.LogWarning( "64 bit Vue " + str(version) + " render executable was not found in the semicolon separated list \"" + vueExeList + "\". Checking for any executable that exists instead." )
            
        if( vueExe == "" ):
            vueExe = FileUtils.SearchFileList( vueExeList )
            if( vueExe == "" ):
                self.FailRender( "Vue " + str(version) + " render executable was not found in the semicolon separated list \"" + vueExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return vueExe
        
    def HandleStdoutError(self):
        self.FailRender(self.GetRegexMatch(0) + " - Check render log for more information." )

    def HandleStdoutStillRendering(self):
        frame_progress = self.GetRegexMatch( 1 )
        self.SetProgress( float(frame_progress) )
        self.SetStatusMessage( frame_progress )
        
    def HandleStdoutAnimationRendering(self):
        frame_progress = float(self.GetRegexMatch( 2 ))
        frame_number = int(self.GetRegexMatch( 1 ))
        
        task_progress = frame_progress
        if self.GetBooleanPluginInfoEntryWithDefault("Animation",True):
            start_frame = self.GetStartFrame()
            end_frame = self.GetEndFrame()
            num_frames = end_frame - start_frame + 1
            task_progress = (100 * (frame_number - start_frame) + frame_progress) / num_frames

        self.SetProgress( float(task_progress) )
        self.SetStatusMessage( str(task_progress) )
