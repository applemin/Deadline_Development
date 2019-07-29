from __future__ import print_function
from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *

from random import randint

import filecmp
import os
import sys

def GetDeadlinePlugin():
    return DraftPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class DraftPlugin ( DeadlinePlugin ):
    Version = "2.6.7"
    PythonExe = ""
    DraftDirectory = ""
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        
        self.StartupDirectoryCallback += self.StartupDirectory
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
        
    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.StartupDirectoryCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback

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
    
    
    def InitializeProcess( self ):
        self.PluginType = PluginType.Simple
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        
        self.AddStdoutHandlerCallback( ".*Progress: ([0-9]+).*" ).HandleCallback += self.HandleStdoutProgress
        self.AddStdoutHandlerCallback( ".*Could not find a license for module 'Draft'.*" ).HandleCallback += self.HandleStdoutLicenseError
        
        draftLocalPath = Path.Combine( self.GetSlaveDirectory(), "Draft" )
                
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
        newPythonPath = self.DraftDirectory + os.pathsep + os.pathsep.join( sys.path )
            
        newMagickPath =  self.DraftDirectory
        if Environment.GetEnvironmentVariable( "MAGICK_CONFIGURE_PATH" ) != None:
            #give locally set MAGICK path priority over the Draft one
            newMagickPath =  Environment.GetEnvironmentVariable( "MAGICK_CONFIGURE_PATH" ) + Path.PathSeparator + newMagickPath
            
        self.SetProcessEnvironmentVariable( 'PYTHONPATH', newPythonPath )
        self.SetProcessEnvironmentVariable( 'MAGICK_CONFIGURE_PATH', newMagickPath )
        
        if SystemUtils.IsRunningOnLinux():
            newLDPath = Path.Combine(ClientUtils.GetBinDirectory(),"python","lib")+Path.PathSeparator+self.DraftDirectory
            if Environment.GetEnvironmentVariable( "LD_LIBRARY_PATH" ) != None:
                newLDPath = newLDPath + Path.PathSeparator + Environment.GetEnvironmentVariable( "LD_LIBRARY_PATH" )
                
            self.SetProcessEnvironmentVariable( 'LD_LIBRARY_PATH', newLDPath )
        elif SystemUtils.IsRunningOnMac():
            newDYLDPath = self.DraftDirectory
            if Environment.GetEnvironmentVariable( "DYLD_LIBRARY_PATH" ) != None:
                newDYLDPath = newDYLDPath + Path.PathSeparator + Environment.GetEnvironmentVariable( "DYLD_LIBRARY_PATH" )
    
            self.SetProcessEnvironmentVariable( 'DYLD_LIBRARY_PATH', newDYLDPath )

        #create 'draft' output directory if it does not already exist
        outputFolders = self.GetJob().OutputDirectories
        for folder in outputFolders:
            folder = RepositoryUtils.CheckPathMapping( folder, True )
            folder = PathUtils.ToPlatformIndependentPath( folder )
            if not os.path.isdir( folder ):
                try:
                    self.LogInfo( 'Creating the output directory "%s"' % folder )
                    os.makedirs( folder )
                except:
                    self.FailRender( 'Failed to create output directory "%s". The path may be invalid or permissions may not be sufficient.' % folder )

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
        
        
    def RenderArgument( self ):
        scriptFile = self.GetPluginInfoEntryWithDefault( "scriptFile", self.GetDataFilename() )
        
        argsList = []
        
        #Get any arguments specified as ScriptArg# in the plugin info file
        i = 0
        while True:
            argument = self.GetPluginInfoEntryWithDefault( "ScriptArg" + str( i ), None )

            if ( argument == None ):
                break
            
            #split out the value from the key (if applicable), to process it (for path mapping)
            separator = '='
            tokens = argument.split( separator, 1 )
            value = tokens[-1].strip()
            
            #temporarily strip quotes if there are any
            wasQuoted = False
            if value.startswith( '"' ) and value.endswith( '"' ) and len(value) > 1:
                wasQuoted = True
                value = value[1:-1]

            try:
                if tokens[0] == "annotationsString":
                    if value.strip() != "None" and value.strip() != "":
                        #We are looping here to guarantee that are creating a unique file, this should never have to loop but it is here as a safety measure
                        while True:
                            randomNumber = randint( 1000000000, 9000000000 )
                            outputPath = Path.Combine( ClientUtils.GetDeadlineTempPath(), "draft_annotations_info_%d.txt" % randomNumber )

                            if not os.path.exists( outputPath ):
                                break

                        outputFile = open( outputPath, 'w' )
                        outputFile.write( value )
                        outputFile.close()
                        tokens[0] = 'annotationsFilePath'
                        value = outputPath
                    else:
                        tokens[0] = 'annotationsFilePath'
                        value = '"None"'
            except Exception as e:
                print(e)
            
            #do some path fixing, in case our value is a path
            value = RepositoryUtils.CheckPathMapping( value, True )
            value = PathUtils.ToPlatformIndependentPath( value )
            
            #A single \ followed by a quote is an escaped quote; don't want that!
            if wasQuoted and value.endswith( '\\' ) and not value.endswith( "\\\\" ):
                value += "\\"

            #put quotes back if we had some
            if wasQuoted:
                value = '"%s"' % value
            
            tokens[-1] = value
            
            #append the re-joined kvp to the arguments
            argsList.append( separator.join( tokens ) )
            i += 1
        
        #Add the repo root as an argument, should already be in a format that the Slave understands
        argsList.append( '%s="%s"' % ( "deadlineRepository", RepositoryUtils.GetRootDirectory() ) )
        
        #Add the current task's start/end frame to the arguments
        argsList.append( '%s=%s' % ( "taskStartFrame", self.GetStartFrame() ) )
        argsList.append( '%s=%s' % ( "taskEndFrame", self.GetEndFrame() ) )
        
        separator = ' '
        arguments = separator.join( argsList )
        
        #check the path of the script itself
        scriptFile = RepositoryUtils.CheckPathMapping( scriptFile, True )
        scriptFile = PathUtils.ToPlatformIndependentPath( scriptFile )
        
        #Get legacy arguments, if any are there
        legacyArgs = self.GetPluginInfoEntryWithDefault( "arguments", "" )
        
        return ( '-u "%s" %s %s' % (scriptFile, arguments, legacyArgs) )
    
    
    def StartupDirectory( self ):
        return self.DraftDirectory
    
    def PreRenderTasks( self ):
        self.LogInfo( "Draft job starting..." )
        
    def PostRenderTasks( self ):
        #check if we're running a post render script (ie, shotgun upload)
        postRenderScript = self.GetPluginInfoEntryWithDefault( "postRenderScript", None )
        if ( postRenderScript ):
            self.LogInfo( "Running post-render script..." )

            scriptDir = os.path.dirname( postRenderScript )
            exitCode = self.RunProcess( self.PythonExe, postRenderScript, scriptDir, -1 )

            if exitCode == 0:
                self.LogInfo( "Success!" )
            else:
                self.LogInfo( "WARNING -- An error occurred while running post-render script. See output above for details." )
        
        self.LogInfo( "Draft job complete!" )
        
    def HandleStdoutError( self ):
        self.FailRender( self.GetRegexMatch( 0 ) )

    def HandleStdoutLicenseError( self ):
        self.FailRender( "Draft was unable to obtain a license. Please review the license server logs for more info." )
    
    def HandleStdoutProgress( self ):
        percentage = float( self.GetRegexMatch( 1 ) )
        self.SetProgress( percentage ) 
