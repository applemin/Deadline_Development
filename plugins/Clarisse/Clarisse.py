import os
import platform
import subprocess

# Pipes is removed in python3, and its functionality is moved to shlex
try:
    from pipes import quote
except ImportError:
    from shlex import quote

from Deadline.Plugins import DeadlinePlugin
from Deadline.Scripting import FileUtils, RepositoryUtils, SystemUtils

def GetDeadlinePlugin():
    return ClarissePlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class ClarissePlugin(DeadlinePlugin):
    
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
        self.SingleFramesOnly=False
        self.StdoutHandling=True

        self.finishedImages = 0.0
        self.imageSet = set()
        images = self.GetPluginInfoEntryWithDefault( "Image", "" )
        if images:
            for image in images.split( " " ):
                self.imageSet.add( image.split( "." )[0] )

        #Stdout handlers
        self.AddStdoutHandlerCallback( "Progress for '.*' : ([0-9]+)%" ).HandleCallback += self.HandleStdoutProgress
        self.AddStdoutHandlerCallback( "Progress 100%" ).HandleCallback += self.HandleFinishedImage
        self.AddStdoutHandlerCallback( "00:00:00[\s]+[0-9]+/[0-9]+MB[\s]+project://(.*)" ).HandleCallback += self.HandleImagesToRender

        self.AddStdoutHandlerCallback( "ERROR: .*" ).HandleCallback += self.HandleStdoutError
    
    def RenderExecutable(self):
        version = self.GetPluginInfoEntryWithDefault( "Version", "3" )
        renderer = self.GetPluginInfoEntryWithDefault( "RenderUsing", "CRender" )
        
        executableString = "_RenderExecutable_"+version
        if renderer == "CRender":
            executableString = "Clarisse"+executableString
        else:
            executableString = "CNode"+executableString
        
        executableList = self.GetConfigEntry( executableString )
        executable = FileUtils.SearchFileList( executableList )
        if executable == "":
            self.FailRender( renderer+" render executable was not found in the semicolon separated list \"" + executableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return executable
        
    def RenderArgument(self):
        """
        Build up the render arguments we pass to the render executable
        :return: a string of render arguments
        """
        # The input file is the render archive that was exported from Clarisse.
        sceneFile = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
        sceneFile = self.MapAndCleanPath( sceneFile )

        arguments = [ sceneFile ]
        
        renderImage = self.GetPluginInfoEntryWithDefault( "Image", "" )
        if renderImage:
            arguments.extend( ( "-image", renderImage ) )

        # In Clarisse 3, a max log_width was added, with a default of 80. We want no maximum log width as it
        # interferes with our stdout handlers. Clarisse won't error out on not finding a command-line arg.
        if self.GetIntegerPluginInfoEntryWithDefault( "Version", 3 ) >= 3:
            arguments.extend( ( "-log_width", "0" ) )
        
        # Print out additional stats after the render.
        arguments.append( "-stats" )
        
        # Check if verbose logging is enabled.
        if self.GetBooleanPluginInfoEntryWithDefault( "Verbose", False ):
            arguments.append( "-verbose" )
        
        # Set the frames to be rendered.
        arguments.extend( ( "-frame", str(self.GetStartFrame()), str(self.GetEndFrame()) ) )
        
        # Set the threads if necessary.
        threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if threads > 0:
            self.LogInfo( "Overriding render threads: " + str(threads) )
            arguments.extend( ( "-threads", str(threads) ) )
        
        # Check if there is a global config file we should be using.
        configFile = self.GetConfigEntryWithDefault( "ConfigFile", "" ).strip()
        if configFile:
            configFile = self.MapAndCleanPath( configFile )
            self.LogInfo( "Using global config file: %s" % configFile )
            arguments.extend( ( '-config_file', configFile ) )
        
        # Check if there are any module paths we should be including.
        modulePaths = self.GetConfigEntryWithDefault( "ModulePaths", "" ).strip()
        if modulePaths:
            modulePathArray = modulePaths.split( ';' )
            if modulePathArray:
                mappedModulePaths = [ self.MapAndCleanPath( modulePath ) for modulePath in modulePathArray ]
                self.LogInfo( "Adding additional module paths: %s" % ", ".join( mappedModulePaths ) )
                arguments.append( "-module_path" )
                arguments.extend( mappedModulePaths )
        
        # Check if there are any search paths we should be including.
        searchPaths = self.GetConfigEntryWithDefault( "SearchPaths", "" ).strip()
        if searchPaths:
            searchPathArray = searchPaths.split( ';' )
            if searchPathArray:
                mappedSearchPaths = [ self.MapAndCleanPath( searchPath ) for searchPath in searchPathArray ]
                self.LogInfo( "Adding additional search paths: %s" % ", ".join( mappedSearchPaths ) )
                arguments.append( "-search_path" )
                arguments.extend( mappedSearchPaths )

        return self.quoteCommandlineArgs( arguments )

    @staticmethod
    def quoteCommandlineArgs( commandline ):
        """
        A helper function used to quote commandline arguments as needed on a case-by-case basis (args with spaces, escape characters, etc.)
        :param commandline: The list of commandline arguments
        :return: a string composed of the commandline arguments, quoted properly
        """
        if platform.system() == 'Windows':
            return subprocess.list2cmdline( commandline )
        else:
            return " ".join( quote(arg) for arg in commandline )
        
    def MapAndCleanPath(self, path):
        path = RepositoryUtils.CheckPathMapping( path )
        if SystemUtils.IsRunningOnWindows():
            path = path.replace( "/", "\\" )
            if path.startswith( "\\" ) and not path.startswith( "\\\\" ):
                path = "\\" + path
        
        extension = os.path.splitext( path )[ 1 ]
        if extension == ".project":
            tempSceneDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
            tempSceneFileName = os.path.basename( path )
            tempSceneFilename = os.path.join( tempSceneDirectory, tempSceneFileName )
            RepositoryUtils.CheckPathMappingInFileAndReplace( path, tempSceneFilename,"" ,"")
            path = tempSceneFilename
            
        return path.replace( "\\", "/" )
    
    def HandleStdoutProgress( self ):
        self.SetStatusMessage( self.GetRegexMatch(0) )
        if len( self.imageSet ) > 0:
            totalImages = float( len( self.imageSet ) )
            frameProgress = float( self.GetRegexMatch(1) )
            progress = self.finishedImages / totalImages * 100.0 + frameProgress / totalImages
            self.SetProgress( min( progress, 100.0 ) )
        else:
            self.SetProgress( float( self.GetRegexMatch(1) ) )

    def HandleFinishedImage( self ):
        self.finishedImages += 1
        progress = 100.0
        if len( self.imageSet ) > 0:
            progress = self.finishedImages / float( len( self.imageSet ) ) * 100.0

        self.SetProgress( min( progress, 100.0 ) )

    def HandleImagesToRender( self ):
        image = self.GetRegexMatch(1)
        self.imageSet.add( image.split(".")[0] )

    def HandleStdoutError( self ):
        self.FailRender( self.GetRegexMatch(0) )
