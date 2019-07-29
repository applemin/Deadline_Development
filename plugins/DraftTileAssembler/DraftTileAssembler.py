from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

import filecmp
import os
import re

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return DraftTileAssemblerPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
######################################################################
## This is the main DeadlinePlugin class for the Tile Assembler plugin.
######################################################################
class DraftTileAssemblerPlugin (DeadlinePlugin):
    
    isFolderAssembly = False
    currentFile = 1
    maxFiles = 1
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        
        self.StartupDirectoryCallback += self.StartupDirectory
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
        
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.StartupDirectoryCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
        
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        self.SingleFramesOnly = True
        self.StdoutHandling = True
        self.HideDosWindow = True

        self.PluginType = PluginType.Simple
        draftLocalPath = Path.Combine( self.GetSlaveDirectory(), "Draft" )
        
        self.AddStdoutHandlerCallback( "Draft Tile Assembler Failed! see log for more details." ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "Assembling Progress: [0-9]+%" ).HandleCallback += self.HandleStdoutProgress
        self.AddStdoutHandlerCallback( "Assembling image [0-9]+ of [0-9]+" ).HandleCallback += self.HandleStdoutFolderFile
        self.AddStdoutHandlerCallback( "Assembling Folder" ).HandleCallback += self.HandleStdoutIsFolder
                
        self.DraftAutoUpdate( draftLocalPath )
        
        if SystemUtils.IsRunningOnWindows():
            draftLibrary = Path.Combine( draftLocalPath, "Draft.pyd" )
        else:
            draftLibrary = Path.Combine( draftLocalPath, "Draft.so" )
        
        if not os.path.isfile( draftLibrary ):
            self.FailRender( "Could not find local Draft installation." )
        else:
            self.LogInfo( "Found Draft python module at: '%s'" % draftLibrary )
        
        self.DraftDirectory = draftLocalPath
        
        #preserve existing env vars by appending/prepending
        newPythonPath = self.DraftDirectory
        if Environment.GetEnvironmentVariable( "PYTHONPATH" ) != None:
            newPythonPath = newPythonPath + Path.PathSeparator + Environment.GetEnvironmentVariable( "PYTHONPATH" )
            
        newMagickPath =  self.DraftDirectory
        if Environment.GetEnvironmentVariable( "MAGICK_CONFIGURE_PATH" ) != None:
            #give locally set MAGICK path priority over the Draft one
            newMagickPath =  Environment.GetEnvironmentVariable( "MAGICK_CONFIGURE_PATH" ) + Path.PathSeparator + newMagickPath
            
        self.SetEnvironmentVariable( 'PYTHONPATH', newPythonPath )
        self.SetEnvironmentVariable( 'MAGICK_CONFIGURE_PATH', newMagickPath )
        
        if SystemUtils.IsRunningOnLinux():
            newLDPath = Path.Combine(ClientUtils.GetBinDirectory(),"python","lib")+Path.PathSeparator+self.DraftDirectory
            if Environment.GetEnvironmentVariable( "LD_LIBRARY_PATH" ) != None:
                newLDPath = newLDPath + Path.PathSeparator + Environment.GetEnvironmentVariable( "LD_LIBRARY_PATH" )
                
            self.SetEnvironmentVariable( 'LD_LIBRARY_PATH', newLDPath )
        elif SystemUtils.IsRunningOnMac():
            newDYLDPath = self.DraftDirectory
            if Environment.GetEnvironmentVariable( "DYLD_LIBRARY_PATH" ) != None:
                newDYLDPath = newDYLDPath + Path.PathSeparator + Environment.GetEnvironmentVariable( "DYLD_LIBRARY_PATH" )
    
            self.SetEnvironmentVariable( 'DYLD_LIBRARY_PATH', newDYLDPath )
            
    
    def DraftAutoUpdate( self, localPath ):
        updateNeeded = True

        draftPathComponents = "draft"
        if SystemUtils.IsRunningOnMac():
            draftPathComponents = os.path.join( draftPathComponents, "Mac" )
        else:
            if SystemUtils.IsRunningOnLinux():
                draftPathComponents = os.path.join( draftPathComponents, "Linux" )
            else:
                draftPathComponents = os.path.join( draftPathComponents, "Windows" )
            
            if SystemUtils.Is64Bit():
                draftPathComponents = os.path.join( draftPathComponents, "64bit" )
            else:
                draftPathComponents = os.path.join( draftPathComponents, "32bit" )
                    
        localFile = os.path.join( localPath, "Version" )
        repoFile = RepositoryUtils.GetRepositoryFilePath( os.path.join( draftPathComponents, "Version" ), False ) 
        
        if not os.path.exists( repoFile ):
            self.FailRender( "ERROR: Draft was not found in the Deadline Repository!" )
        
        if ( os.path.exists( localPath ) and os.path.isfile( localFile ) and os.path.isfile( repoFile ) ):
            if filecmp.cmp(localFile, repoFile):
                updateNeeded = False
        elif not os.path.exists( localPath ):
            self.LogInfo( "Creating local Draft directory..." )
            os.makedirs( localPath )
                
        if ( updateNeeded ):
            repoPath = RepositoryUtils.GetRepositoryPath( draftPathComponents, False ) 
            self.LogInfo( "Draft upgrade detected, copying updated files..." )
            for filePath in Directory.GetFiles( repoPath ):
                fileName = Path.GetFileName( filePath )
                self.LogInfo( "Copying '%s'..." % fileName )
                File.Copy( filePath, Path.Combine(localPath, fileName), True )
            self.LogInfo( "Draft update completed!" )
        
    def RenderExecutable( self ):
        #build up the path parts based on system type & bitness
        if SystemUtils.IsRunningOnWindows():
            pythonExe = "dpython.exe"
        elif SystemUtils.IsRunningOnMac():
            pythonExe = "dpython"
        else:
            pythonExe = "dpython"
        
        pythonPath = Path.Combine( ClientUtils.GetBinDirectory(), pythonExe )
        
        self.LogInfo( "Looking for bundled python at: '%s'" % pythonPath )
        
        if not FileUtils.FileExists( pythonPath ):
            self.FailRender( "Could not find bundled Python executable." )
        
        self.PythonExe = pythonPath
        return self.PythonExe
        
    def StartupDirectory(self):
        return self.DraftDirectory
    
    def PreRenderTasks(self):
        self.LogInfo( "Draft Tile Assembler job starting..." )
        sceneFilename = ""
        if not self.GetBooleanPluginInfoEntryWithDefault( "MultipleConfigFiles", False ):
            sceneFilename = self.GetDataFilename()
        else:
            configFilenames = self.GetAuxiliaryFilenames()
            sceneFilename = configFilenames[int(self.GetCurrentTaskId())]
        
        tempSceneDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
        tempSceneFileName = Path.GetFileName( sceneFilename )
        self.TempSceneFilename = Path.Combine( tempSceneDirectory, tempSceneFileName )
        
        if SystemUtils.IsRunningOnWindows():        
            RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator(sceneFilename, self.TempSceneFilename, "/", "\\")
        else:
            RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator(sceneFilename, self.TempSceneFilename, "\\", "/")
            os.chmod( self.TempSceneFilename, os.stat( self.TempSceneFilename ).st_mode )
        
    def PostRenderTasks(self):
        #check if we're running a post render script (ie, shotgun upload)
        postRenderScript = self.GetPluginInfoEntryWithDefault("postRenderScript", None)
        if ( postRenderScript ) :
            ProcessUtils.SpawnProcess( self.PythonExe, postRenderScript )
        
        self.LogInfo( "Draft Tile Assembler Job Completed" )
        
    def HandleStdoutError(self):
        self.FailRender( self.GetRegexMatch(0) )
    
    def HandleStdoutProgress(self):
        output = self.GetRegexMatch(0)
        percentage = re.search('(\d+)%$', output).group(0)
        percentage = int(percentage[:-1])*1.0
        
        if self.isFolderAssembly:
            output = "File "+str(self.currentFile)+" of "+str(self.maxFiles)+ ": "+output
            percentage = percentage/self.maxFiles
            additonalPercentage = ((self.currentFile-1.0)/self.maxFiles)*100
            
            percentage = percentage+additonalPercentage
            percentage = int(percentage+0.5)*1.0
        
        self.SetProgress( percentage )
        self.SetStatusMessage( output )
    
    def HandleStdoutFolderFile(self):
        output = self.GetRegexMatch(0)
        match = re.search('(\d+) of (\d+)', output)
        self.currentFile = float(match.group(1))
        self.maxFiles = float(match.group(2))
    
    def HandleStdoutIsFolder(self):
        self.isFolderAssembly = True
    
    def RenderArgument( self ):
        scriptFile = Path.Combine( self.GetPluginDirectory(), "Assembler.py" )
        configFile = self.TempSceneFilename
        tempFolder = self.CreateTempDirectory("AssembledImage")

        errorOnMissing = self.GetBooleanPluginInfoEntryWithDefault("ErrorOnMissing", True)
        cleanupTiles = self.GetBooleanPluginInfoEntryWithDefault("CleanupTiles", False)
        errorOnMissingBackground = self.GetBooleanPluginInfoEntryWithDefault("ErrorOnMissingBackground", True)

        return '"' + scriptFile + '" "' + configFile + '" ' + str(errorOnMissing) + " " + str(cleanupTiles) + " " + str(errorOnMissingBackground) + ' "' + tempFolder + '"'