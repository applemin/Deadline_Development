from System.IO import *
from System import *

from Deadline.Scripting import *
from Deadline.Plugins import *

def GetDeadlinePlugin():
    return CompositePlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class CompositePlugin (DeadlinePlugin):
    
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
    
    def InitializeProcess( self ):
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        self.PopupHandling = True
        
        self.AddStdoutHandlerCallback( ".*Progress: ([0-9]+) of ([0-9]+)" ).HandleCallback += self.HandleStdoutProgress
        
        self.AddPopupHandler( "Composite - Warning", "OK" )
            
    def RenderExecutable( self ):
        version = self.GetIntegerPluginInfoEntryWithDefault( "Version", 2010 )
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        compositeExe = ""
        compositeExeList = self.GetConfigEntry( "Composite" + str(version) + "RenderExecutable" )
       
        if(SystemUtils.IsRunningOnWindows()):
            if build == "32bit":
                compositeExe = FileUtils.SearchFileListFor32Bit( compositeExeList )
                if( compositeExe == "" ):
                    self.LogWarning( "32 bit Composite %d render executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % (version, compositeExeList))
            elif build == "64bit":
                compositeExe = FileUtils.SearchFileListFor64Bit( compositeExeList )
                if( compositeExe == "" ):
                    self.LogWarning( "64 bit Composite %d render executable could not be found in the semicolon separated list \"%s\". Checking for any executable that exists instead." % (version, compositeExeList))
            
        if( compositeExe == "" ):
            compositeExe = FileUtils.SearchFileList( compositeExeList )
            if( compositeExe == "" ):
                self.FailRender( "Composite %d render executable could not be found in the semicolon separated list \"%s\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." % (version, compositeExeList) )
        
        return compositeExe
        
    def RenderArgument( self ):
        auxiliaryFilenames = self.GetAuxiliaryFilenames()
        
        # Common arguments
        projectFile = self.GetDataFilename()
        arguments = " -p \"" + projectFile + "\""
        arguments += " -c \"" + auxiliaryFilenames[1] + "\""		
        arguments += " -v \"" + self.GetPluginInfoEntry( "CompositionVersion" ) + "\""
        arguments += " -s " + str(self.GetStartFrame())
        arguments += " -e " + str((self.GetEndFrame() + 1))
        
        # If a users ini file was given use that
        if len(auxiliaryFilenames) > 2:
            userfile = auxiliaryFilenames[2]
            arguments += " -userfilepath \"" + userfile + "\""
        
        return arguments

    def HandleStdoutProgress( self ):
        self.SetProgress( 100 * float(self.GetRegexMatch(1)) / float(self.GetRegexMatch(2)) )
