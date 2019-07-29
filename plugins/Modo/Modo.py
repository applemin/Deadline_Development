from System.Diagnostics import *
from System.IO import *
from System.Text.RegularExpressions import *

from Deadline.Plugins import *
from Deadline.Scripting import *

from FranticX.Processes import *

import itertools
import os
import sys
import re

import traceback
import struct
import chunk
import cStringIO
import fnmatch
import locale

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return ModoPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the modo plugin.
######################################################################
class ModoPlugin (DeadlinePlugin):
    Executable = ""
    JobFilename = ""
    AckFilename = ""
    ResFilename = ""
    ProgramName = ""
    ThreadID = ""
    Process = None
    ModoDBRJob = False
    
    LayeredFormats = ["LayeredPSD", "PNGs", "PNGs16", "openexrlayers", "openexrlayers32"]
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob
    
    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback
        
        if self.Process:
            self.Process.Cleanup()
            del self.Process
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings. Because this is an advanced plugin,
        # we do not need to set the process specific settings here.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Advanced

        self.massagePaths = self.GetBooleanConfigEntryWithDefault( "MassagePaths", True )
        self.resolveAliases = self.GetBooleanConfigEntryWithDefault( "ResolvePathAliases", True )
        self.pathAliases = self.GetPathAliases()

        
    ## Called by Deadline when the job is first loaded.
    def StartJob( self ):
        self.ModoDBRJob = self.GetBooleanPluginInfoEntryWithDefault( "ModoDBRJob", False )

        # Modo's network rendering only needs to start in slave mode
        if not self.ModoDBRJob:
            # Get the scene file.
            sceneFilename = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
            sceneFilename = self.CleanupPath( sceneFilename )
            if not File.Exists( sceneFilename ):
                self.FailRender( "Scene file \"" + sceneFilename + "\" could not be found" )
            
            # Check if we should be doing path mapping on the contents of the modo scene file. Note that this only handles
            # videoStill paths. Output paths are handled after the scene is loaded.
            if self.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
                tempSceneDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
                tempSceneFilename = Path.Combine( tempSceneDirectory, Path.GetFileName( sceneFilename ) )
                
                map_paths( self, sceneFilename, tempSceneFilename )
                sceneFilename = tempSceneFilename
            
            # Get the thread ID, which is used for creating the job and ack filenames.
            self.ThreadID = str( self.GetThreadNumber() )
            
            # Create the job and ack filenames.
            self.JobFilename = Path.Combine( self.GetJobsDataDirectory(), "job" + self.ThreadID + ".txt" )
            self.AckFilename = Path.Combine( self.GetJobsDataDirectory(), "ack" + self.ThreadID + ".txt" )
            
            # Delete any existing job or ack filenames.
            File.Delete( self.JobFilename )
            File.Delete( self.AckFilename )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "VRayRender", False ):
                threads = self.GetThreadCount()
                self.LogInfo( "Setting VRAY_NUM_THREADS environment variable to %s" % threads )
                self.SetProcessEnvironmentVariable( "VRAY_NUM_THREADS", str( threads ) )
        
            
            # Start the modo monitored process.
            self.ProgramName = "modo" + self.ThreadID
            self.LogInfo( "Starting monitored process: " + self.ProgramName )
            self.Process = modoProcess( self, self.JobFilename, self.AckFilename )
            self.StartMonitoredManagedProcess( self.ProgramName, self.Process )
            
            # Wait until modo is ready.
            self.LogInfo( "Waiting until modo is ready" )
            self.WaitForAck()
            
            # Logging to console is only supported in 4xx and later.
            version = self.GetModoVersion()
            if version >= 4:
                self.SendCommand( "log.toConsole true", True )
                
            # Version 6xx and later allow for more verbose logging.
            if version >= 6:
                self.SendCommand( "log.toConsoleRolling true", True )
            
            # Get the LxResource config file path so that we can check what error codes mean.
            resourcePath = self.SendQuery( "query platformservice path.path ? resource" )
            if Directory.Exists( resourcePath ):
                self.ResFilename = Path.Combine( resourcePath, "msglxresult.cfg" )
                self.Process.SetResFilename( self.ResFilename )
                self.LogInfo( "LxResult config filename: " + self.ResFilename )
            else:
                self.LogWarning( "Could not detect path for LxResult config filename" )
            
            # Load the scene file.
            self.SendCommand( "!scene.open {%s} normal" % sceneFilename, True )
    
            # Perform path mapping on the output paths before rendering.
            pathToMap = self.SendPathMapping( "START" )
            while pathToMap != "FINISHED":
                pathToMap = RepositoryUtils.CheckPathMapping( pathToMap ).replace( "\\", "/" )
                pathToMap = self.SendPathMapping( pathToMap )
    
    def RenderTasks( self ):
        version = self.GetModoVersion()
        fromMonitor = not self.GetBooleanPluginInfoEntryWithDefault( "SubmittedFromModo", False )

        self.SetStatusMessage( "Starting render task" )

        if self.ModoDBRJob and version >= 7:
            self.Process = modoProcess( self, "", "" )
            self.RunManagedProcess( self.Process )
        else:
            # Get the render threads value (0 means automatic).
            threads = self.GetThreadCount()
            if threads > 0:
                self.LogInfo( "Using " + str(threads) + " render threads" )
                self.SendCommand( "pref.value render.autoThreads false", True )
                self.SendCommand( "pref.value render.numThreads " + str(threads), True )
            else:
                self.LogInfo( "Using automatic render threads" )
                self.SendCommand( "pref.value render.autoThreads true", True )
                            
            # See if we should automatically set the geometry cache.
            if self.GetBooleanConfigEntryWithDefault( "GeoCacheEnabled", False ):
                self.LogInfo( "Auto geometry cache detection enabled" )
                
                # This value is already in MB.
                geoCacheBuffer = self.GetLongConfigEntryWithDefault( "GeoCacheBuffer", 512 )
                self.LogInfo( "Geometry cache buffer is " + str(geoCacheBuffer) + " MB" )
                
                # Convert this value to MB.
                availableMemory = (SystemUtils.GetAvailableRam() / 1024) / 1024
                self.LogInfo( "Available system memory is " + str(availableMemory) + " MB" )
                
                # Now calculate the limit we should pass to modo.
                memoryLimit = availableMemory - geoCacheBuffer
                self.LogInfo( "Setting geometry cache to " + str(memoryLimit) + " MB" )
                
                # Send command to set the geometry cache size.
                geoCacheBytes = (memoryLimit * 1024) * 1024
                self.SendCommand( "pref.value render.cacheSize " + str(geoCacheBytes), True )
            
            bakeItems = self.GetBooleanPluginInfoEntryWithDefault( "BakeItems", False )
            if bakeItems:
                self.RenderBakeItems()
                return
            
            # Send command to select the render item.
            self.SendCommand( "select.itemType polyRender", True )
            
            startFrame = self.GetStartFrame()
            endFrame = self.GetEndFrame()
            outputFile = ""
            outputFormat = ""
            outputArgument = "{*}"
            
            # Check if we're doing a region render.
            if self.IsTileJob():
                regionFrame = self.GetStartFrame()
                startFrame = regionFrame
                endFrame = regionFrame
                
                regionIndex = self.GetCurrentTaskId()
                left = self.GetFloatPluginInfoEntry( "RegionLeft%s" % regionIndex )
                right = self.GetFloatPluginInfoEntry( "RegionRight%s" % regionIndex )
                top = self.GetFloatPluginInfoEntry( "RegionTop%s" % regionIndex )
                bottom = self.GetFloatPluginInfoEntry( "RegionBottom%s" % regionIndex )

                self.SendCommand( "item.channel polyRender$region [true]", True )
                self.SendCommand( "item.channel polyRender$regX0 [%s]" % left, True )
                self.SendCommand( "item.channel polyRender$regX1 [%s]" % right, True )
                self.SendCommand( "item.channel polyRender$regY0 [%s]" % top, True )
                self.SendCommand( "item.channel polyRender$regY1 [%s]" % bottom, True )

                if fromMonitor:
                    
                    # Tile jobs from the Monitor will have the region file name and format defined, and they need to be applied globally via the output argument.
                    outputFile = self.GetPluginInfoEntry( "RegionFilename%s" % regionIndex )
                    outputFile = self.CleanupPath( outputFile )
                    outputFormat = self.GetPluginInfoEntry( "RegionFormat" )
                    outputArgument = "{%s} %s" % ( outputFile, outputFormat )
                    
                else:
                    
                    # Tile jobs from modo can have the output path overridden, in which case OutputFormat is defined.
                    outputFormat = self.GetPluginInfoEntryWithDefault( "OutputFormat", "" )
                    if outputFormat in self.LayeredFormats:
                        
                        # For layered formats, we just need to set the one name globally via the render argument.
                        outputFile = self.GetPluginInfoEntryWithDefault( "Output0RegionFilename%s" % regionIndex, "" )
                        if len(outputFile) > 0:
                            outputFile = self.CleanupPath( outputFile )
                            outputArgument = "{%s} %s" % ( outputFile, outputFormat )
                            
                    else:
                        
                        # It's either a non-layered format, or the format isn't being overwritten. In both cases, update the output directly in each output item.
                        currOutput = 0
                        renderOutput = ""
                        while True:
                            outputFile = self.GetPluginInfoEntryWithDefault( "Output%sRegionFilename%s" % ( currOutput, regionIndex ), "" )
                            if outputFile == "":
                                break
                            
                            outputFile = self.CleanupPath( outputFile )
                            outputFormat = self.GetPluginInfoEntryWithDefault( "OutputFormat%s" % currOutput, "" )
                            
                            renderOutput = self.GetPluginInfoEntry( "RenderOutputID%s" % currOutput )
                            self.SendCommand( "select.item {%s}" % renderOutput, True )
                            self.SendCommand( "item.channel renderOutput$filename {%s}" % outputFile, True )
                            self.SendCommand( "item.channel renderOutput$format {%s}" % outputFormat, True )
                            currOutput += 1
                            
            else:
                # For non tiled jobs, check if we have an output override.
                outputFile = self.GetPluginInfoEntryWithDefault( "OutputFilename", "" )
                if len( outputFile ) > 0:
                    outputFile = self.CleanupPath( outputFile )
                    outputFormat = self.GetPluginInfoEntryWithDefault( "OutputFormat", "" )
                    
                    # If we have an output override, then we set the global override for layered formats, or if it was submitted from the Monitor.
                    if fromMonitor or outputFormat in self.LayeredFormats:
                        outputArgument = "{%s} %s" % ( outputFile, outputFormat )
                    else:
                        
                        # If submitted from modo, then set the output directly in each output item.
                        currOutput = 0
                        while True:
                            renderOutput = self.GetPluginInfoEntryWithDefault( "RenderOutputID%s" % currOutput, "" )
                            if renderOutput == "":
                                break
                            
                            self.SendCommand( "select.item {%s}" % renderOutput, True )
                            self.SendCommand( "item.channel renderOutput$filename {%s}" % outputFile, True )
                            self.SendCommand( "item.channel renderOutput$format {%s}" % outputFormat, True )
                            currOutput += 1
            
            # Select the render item again, since it could have become unselected when changing output above.
            self.SendCommand( "select.itemType polyRender", True )
            
            # Set the pattern if necessary.
            if version >= 6:
                outputPattern = self.GetPluginInfoEntryWithDefault( "OutputPattern", "No Pattern" )
                if outputPattern != "No Pattern" and outputPattern != "":
                    self.SendCommand( "item.channel outPat \"%s\"" % outputPattern, True )
                elif outputPattern == "":
                    self.SendCommand( "item.channel outPat \"%s\"" % unicode("<FFFF>"), True )
            
            # Set the animation settings.
            self.SendCommand( "item.channel first %s" % startFrame, True )
            self.SendCommand( "item.channel last %s" % endFrame, True )
            
            # If this is version 6xx or later, see if a passes group was specified.
            passGroup = ""
            if version >= 6:
                passGroup = self.GetPluginInfoEntryWithDefault( "PassGroup", "" )
            
            self.SetStatusMessage( "Rendering" )
            
            # Send the render command.
            
            if self.GetBooleanPluginInfoEntryWithDefault( "VRayRender", False ):
                
                command = "!vray.render.animation"
                if passGroup != "":
                    command += ( " group:\"%s\"" % passGroup )
                
                if outputFile != "":
                    command += ( " filename:\"%s\"" % outputFile )
                
                if outputFormat != "":
                    command += ( " format:\"%s\"" % outputFormat )
                
                self.SendCommand( command, True )
                
            else:
                if passGroup != "":
                    self.SendCommand( "!render.animation %s group:{%s}" % (outputArgument, passGroup), True )
                else:
                    self.SendCommand( "!render.animation %s" % outputArgument, True )
            
            # Remove the region if we just did a region render.
            if self.IsTileJob():
                self.SendCommand( "item.channel polyRender$region [false]", True )
            
            self.SetStatusMessage( "Rendering finished" )
            self.SetProgress( 100.0 )
            
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
    
    def GetThreadCount( self ):
        threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if self.OverrideCpuAffinity() and self.GetBooleanConfigEntryWithDefault( "LimitThreadsToCPUAffinity", False ):
            affinity = len( self.CpuAffinity() )
            if threads == 0:
                threads = affinity
            else:
                threads = min( affinity, threads )
                
        return threads
    
    def RenderBakeItems( self ):
        self.SetStatusMessage( "Baking" )
                
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        
        for frame in range( startFrame, endFrame + 1 ):
            self.SetProgress( float( frame - startFrame) / float( endFrame - startFrame + 1 ) * 100 )
            self.SendCommand( "bakeItem.bake bakeItem %s" % frame, True )
        
        self.SendCommand( "clip.saveall", True )
        self.SetStatusMessage( "Finished Baking" )
        self.SetProgress( 100.0 )
        
        self.FlushMonitoredManagedProcessStdout( self.ProgramName )
    
    def EndJob( self ):
        if not self.ModoDBRJob:
            self.LogInfo( "Ending modo Job" )

            # Only try to stop the process if we've actually started it.
            if self.Process != None:
                self.FlushMonitoredManagedProcessStdoutNoHandling( self.ProgramName )
                
                # Send SHUTDOWN command
                self.LogInfo( "Shutting down modo" )
                self.SendCommand( "QUIT", False )
                self.WaitForMonitoredManagedProcessToExit( self.ProgramName, 2000 )
                self.ShutdownMonitoredManagedProcess( self.ProgramName )
        
    def SendCommand( self, command, waitForAck ):
        self.CreateCommandFile( self.JobFilename, "EXECUTE\n" + command )
        if waitForAck:
            return self.WaitForAck()
    
    def SendQuery( self, command ):
        self.CreateCommandFile( self.JobFilename, "QUERY\n" + command )
        return self.WaitForAck()
    
    def SendPathMapping( self, command ):
        self.CreateCommandFile( self.JobFilename, "PATHMAPPING\n" + command )
        return self.WaitForAck()
    
    def WaitForAck( self ):
        while True:
            self.VerifyMonitoredManagedProcess( self.ProgramName )
            self.FlushMonitoredManagedProcessStdout( self.ProgramName )
            
            blockingDialogMessage = self.CheckForMonitoredManagedProcessPopups( self.ProgramName )
            if( blockingDialogMessage != "" ):
                self.FailRender( blockingDialogMessage )
                
            if self.IsCanceled():
                self.FailRender( "Received cancel task command from Deadline." )
            
            response = self.WaitForCommandFile( self.AckFilename, True, 100 )
            if response != "":
                return response
                
    def CleanupPath( self, path ):
        path = RepositoryUtils.CheckPathMapping( path )
        if SystemUtils.IsRunningOnWindows():
            path = path.replace( "/", "\\" )
            if path.startswith( "\\" ) and not path.startswith( "\\\\" ):
                path = "\\" + path
        else:
            path = path.replace( "\\", "/" )
            if path.startswith("//"):
                # chop off first '/' for linux/osx
                path = path[1:]
        return path
    
    def GetModoVersion( self ):
        fullVersion = self.GetPluginInfoEntryWithDefault( "Version", "3xx" )
        xLocation = fullVersion.find('x')
        if xLocation < 0:
            xLocation = None
        version = int( fullVersion[ :xLocation ] )
        return version

    def GetPathAliases( self ):
        """
        Retrieves a dictionary containing all PathAliases from the submission machines and the Paths they represent.
        :return: The dicionary of Path Aliases.
        """

        aliases = {}
        # We don't know how many Path aliases existed at submission time so loop until we hit an exception.
        for index in itertools.count():
            try:
                alias = self.GetPluginInfoEntry( "PathAlias%s" % index )
                aliasPath = self.GetPluginInfoEntry( "PathAliasPath%s" % index )
            except RenderPluginException as e:
                break
            aliases[ alias ] = aliasPath

        return aliases

######################################################################
## This is the class for running modo process.
######################################################################
class modoProcess (ManagedProcess):
    deadlinePlugin = None
    
    JobFilename = ""
    AckFilename = ""
    ResFilename = ""
    
    def __init__( self, deadlinePlugin, jobFilename, ackFilename ):
        self.deadlinePlugin = deadlinePlugin
        
        self.JobFilename = jobFilename
        self.AckFilename = ackFilename
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.negProgress = False
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess( self ):
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.PopupHandling = True
        self.StdoutHandling = True
        
        self.AddPopupIgnorer(".*Render history settings.*")
        
        self.AddStdoutHandlerCallback( "Unknown command: .*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( "Path mapping error: .*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( r"!render\.animation.*failed with" ).HandleCallback += self.HandleRenderFailed
        self.AddStdoutHandlerCallback( ".*failed with (-?[0-9]+)" ).HandleCallback += self.HandleCommandError

        self.AddStdoutHandlerCallback( r'.*V-Ray \(aborted\).*' ).HandleCallback += self.HandleError

        self.AddStdoutHandlerCallback( r"\)\s+Frame\s+([0-9]+)" ).HandleCallback += self.HandleProgress
        self.AddStdoutHandlerCallback( r"sceneProgress:\s?(-?[0-9]+\.[0-9]+)" ).HandleCallback += self.HandleRollingProgress
        self.AddStdoutHandlerCallback( r"V-Ray Render.*(\d+) / (\d+).*Rendering image.* (\d+\.\d+) % complete" ).HandleCallback += self.HandleVRayProgress

    def RenderExecutable( self ):
        build = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        version = str( self.deadlinePlugin.GetModoVersion() )
        
        executable = ""
        executableList = self.deadlinePlugin.GetConfigEntry( "RenderExecutable" + version )
        
        if(SystemUtils.IsRunningOnWindows()):
            if( build == "32bit" ):
                self.deadlinePlugin.LogInfo( "Enforcing 32 bit build of modo" )
                executable = FileUtils.SearchFileListFor32Bit( executableList )
                if( executable == "" ):
                    self.deadlinePlugin.LogWarning( "32 bit modo " + version + " render executable was not found in the semicolon separated list \"" + executableList + "\". Checking for any executable that exists instead." )
            
            elif( build == "64bit" ):
                self.deadlinePlugin.LogInfo( "Enforcing 64 bit build of modo" )
                executable = FileUtils.SearchFileListFor64Bit( executableList )
                if( executable == "" ):
                    self.deadlinePlugin.LogWarning( "64 bit modo " + version + " render executable was not found in the semicolon separated list \"" + executableList + "\". Checking for any executable that exists instead." )
            
        if( executable == "" ):
            self.deadlinePlugin.LogInfo( "Not enforcing a build of modo" )
            executable = FileUtils.SearchFileList( executableList )
            if executable == "":
                self.deadlinePlugin.FailRender( "modo " + version + " render executable was not found in the semicolon separated list \"" + executableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return executable
        
    def RenderArgument( self ):
        version = self.deadlinePlugin.GetModoVersion()
        modoDBRJob = self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "ModoDBRJob", False )
        arguments = ""
        
        if modoDBRJob and version >= 7:
            arguments = "-slave"
        else:
            # In modo 4xx and earlier, there wasn't a modo_cl app for mac, so we have to pass the console argument.
            if SystemUtils.IsRunningOnMac() and version <= 4:
                arguments = "-console "

            if version >= 9:
                arguments += "-dboff:crashreport "
            
            arguments += "-cmd:\"@\\\"" + Path.Combine( self.deadlinePlugin.GetPluginDirectory(), "render.pl" ) + "\\\""
            arguments += " \\\"" + self.JobFilename + "\\\" \\\"" + self.AckFilename + "\\\"\""
        
        return arguments
    
    def HandleError( self ):
        self.deadlinePlugin.FailRender( self.GetRegexMatch( 0 ) )

    def HandleRenderFailed( self ):
        self.deadlinePlugin.FailRender( "Modo render failed to save output. Please make sure all defined output paths are accessible." )
    
    def HandleCommandError( self ):
        if len(self.ResFilename) == 0 or not File.Exists( self.ResFilename ):
            self.deadlinePlugin.FailRender( self.GetRegexMatch( 0 ) + ". Check the meaning of this error code in the modo error codes message table, resource:msglxresult.cfg" )
        else:
            vrayMatch = False
            if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "VRayRender", False ):
                vrayRegex = Regex( '.*!vray.render.*' )
                vrayMatch = vrayRegex.Match( self.GetRegexMatch(0) ).Success
            
            if vrayMatch:
                self.deadlinePlugin.FailRender( "Missing function vray.render. Please make sure V-Ray is installed." )
            else:
                errorCode = self.GetRegexMatch( 1 )
                errorRegex = Regex( 'key="' + errorCode + '"[^>]*>([^<]*)<', RegexOptions.IgnoreCase )
                
                contents = File.ReadAllText( self.ResFilename )
                match = errorRegex.Match( contents )
                if match.Success:
                    self.deadlinePlugin.FailRender( self.GetRegexMatch( 0 ) + ": " + match.Groups[1].Value )
                else:
                    self.deadlinePlugin.FailRender( self.GetRegexMatch( 0 ) + ". Check the meaning of this error code in the modo error codes message table, resource:msglxresult.cfg" )
    
    def HandleProgress( self ):
        startFrame = self.deadlinePlugin.GetStartFrame()
        endFrame = self.deadlinePlugin.GetEndFrame()
        finishedFrame = int(self.GetRegexMatch(1))
        
        if( endFrame - startFrame + 1 != 0 ):
            self.deadlinePlugin.SetProgress( float((finishedFrame - startFrame + 1) * 100.0) / float(endFrame - startFrame + 1) )
    
    def HandleRollingProgress( self ):
        progress = float(self.GetRegexMatch(1))

        if progress < 0 or self.negProgress:
            self.negProgress = True
            progress+= 100

        self.deadlinePlugin.SetProgress(progress)
        #self.SuppressThisLine()

    def HandleVRayProgress( self ):
        frame = float( self.GetRegexMatch(1) )
        totalFrames = float( self.GetRegexMatch(2) )
        frameProgress = float( self.GetRegexMatch(3) )
        self.deadlinePlugin.SetStatusMessage( "Rendering Frame %s of %s: %s%%" % ( int(frame), int(totalFrames), frameProgress ) )

        progress = ( frame - 1 ) / totalFrames * 100 + frameProgress / totalFrames
        self.deadlinePlugin.SetProgress( progress )

    def SetResFilename( self, resFilename ):
        self.ResFilename = resFilename


######################################################################
## This code generously provided by the Foundry to perform
## path mapping on the paths in the modo scene file.
######################################################################

class SubChunk(chunk.Chunk):
    """LXO subchunks have a smaller (2 byte) chunk size value than regular chunks
    (4 byte) which isn't actually supported by Python's built in Chunk module so
    we'll just subclass that & redefine the chunksize attribute.

    """
    def __init__(self, data, align=True, bigendian=True, inclheader=False):
        self.closed = False
        self.align = align      # whether to align to word (2-byte) boundaries
        if bigendian:
            strflag = '>'
        else:
            strflag = '<'
        self.file = data
        self.chunkname = data.read(4)
        if len(self.chunkname) < 4:
            raise EOFError
        try:
            self.chunksize = struct.unpack(strflag+'H', data.read(2))[0]
        except struct.error:
            raise EOFError
        if inclheader:
            self.chunksize = self.chunksize - 8 # subtract header
        self.size_read = 0
        try:
            self.offset = self.file.tell()
        except (AttributeError, IOError):
            self.seekable = False
        else:
            self.seekable = True

def get_unpacked_string(data):
    """ pops an unpacked string from the data stream stripped of any null padding.

    """
    string = ""
    while 1:
        char = data.read(1)
        if char == "\0":
            if (len(string) % 2 == 0):
                char = data.read(1)
            return string
        string += char

def get_packed_string(string):
    """ builds a null terminated string padded to an even number of characters
    (bytes) if necessary - strings stored in IFF files have to be null terminated
    and padded to an even boundary.

    """
    string += "\0"
    if len(string) % 2 == 1:
        string += "\0"
    return string, len(string)

def read_item_chunk(lxchunk):
    """ Returns an ITEM chunk's name, type, uniqueID and, if it's a "VideoStill"
    chunk, the start position (offset) of it's subchunks - image paths are stored
    in a string channel subchunk (CHNS) belonging to Item chunks of type "VideoStill"

    """
    offset = 0
    data = cStringIO.StringIO(lxchunk.read())
    itemtype = get_unpacked_string(data)
    itemname = get_unpacked_string(data)
    uniqueID = struct.unpack(">L", data.read(4))[0]
    offset =  data.tell()
    return (itemtype, itemname, uniqueID, offset)

def read_subs_chunk( lxchunk ):
    data = cStringIO.StringIO(lxchunk.read())
    sourceFile = get_unpacked_string(data)
    remainder = data.read()
    
    return (sourceFile, remainder)

def read_chns_subchunk(subchunk):
    """Unpacks a string channel subchunk returning the chanel's name and the
    string value stripped of any padding.

    """
    data = cStringIO.StringIO(subchunk.read())
    name =  get_unpacked_string(data)
    value =  get_unpacked_string(data)
    return (name, value)

def repack_subchunk(stream, chunkID, size, data):
    """repacks a subchunk and adds it back into to the data stream."""
    stream.write(struct.pack(">4s",  chunkID))
    stream.write(struct.pack(">H",  size))
    stream.write(data.read())

def build_chns_subchunk(newstring):
    """Generates a new filename string channel (CHNS) subchunk with the new
    image file path.

    """
    data = cStringIO.StringIO()
    data.write(struct.pack('>4s', "CHNS"))
    fname, fnamesize = get_packed_string("filename")
    newstring, newstringsize = get_packed_string(newstring)
    data.write(struct.pack('>H', fnamesize + newstringsize))
    data.write(struct.pack('>%ds' % fnamesize, fname))
    data.write(struct.pack('>%ds' % newstringsize, newstring.encode( locale.getpreferredencoding() )))
    
    return data

def do_chunks(deadlinePlugin, data, inFile):
    """ Process the root chunks of the IFF file. We're looking for 'ITEM' chunks
    of type 'videoStill'. When we find one we'll process the subchunks
    looking for a string channel (CHNS) subchunk of type 'filename'. Once
    we've got one of those we can get and replace the file path of the image.

    """

    # output stream to hold the file's chunks as they're processed.
    output = cStringIO.StringIO()

    while 1:
        try:
            # get next chunk
            lxchunk = chunk.Chunk(data)
        except EOFError:
            break

        ctype = lxchunk.chunkname
        size = lxchunk.chunksize
        if ctype == 'ITEM':
            # Got an 'ITEM' chunk, we're looking for "VideoStill" item chunks so
            # we need to read it's type and, if it's a chunk we're looking for,
            # the start position (offset) of it's subchunks.
            itemtype, itemname, uniqueID, offset = read_item_chunk(lxchunk)
            # Got a videoStill item, process the subchunks looking for the
            # 'CHNS' subchunk with type 'filename'
            deadlinePlugin.LogInfo( '    Found '+itemtype )
            lxchunk.seek(offset)
            # process the chunk's subchunks to find the 'filename' string
            # channel subchunk and update it.
            subchunks = process_itemsubchunks(deadlinePlugin, lxchunk, inFile, itemtype)
            # rebuild the 'VideoStill' item chunk because it's size has changed.
            itemtype, itemtypesize = get_packed_string(itemtype)
            itemname, itemnamesize = get_packed_string(itemname)
            # seek to end of subchunk data stream to get it's size.
            subchunks.seek(0, 2)
            # chunk type ID ('ITEM')
            output.write(struct.pack(">4s",  ctype))
            # chunk size
            subchunk_size = subchunks.tell() + itemtypesize + itemnamesize + 4
            output.write(struct.pack(">L",  subchunk_size))
            # item type string
            output.write(struct.pack(">%ds" % itemtypesize, itemtype))
            # item name
            output.write(struct.pack(">%ds" % itemnamesize, itemname))
            # item ID
            output.write(struct.pack(">L",  uniqueID))
            # subchunk data
            chunk_data = subchunks.getvalue()
            if subchunk_size % 2:
                chunk_data += "\0"
            output.write(chunk_data)
            continue
        elif ctype == 'SUBS':

            file, remainder = read_subs_chunk(lxchunk)
            remainderLength = len(remainder)
            deadlinePlugin.LogInfo( '    Found SUBS' )

            newPath = process_file( deadlinePlugin, file )

            newPath, newPathSize = get_packed_string( str(newPath) )
            output.write(struct.pack(">4s",  ctype))
            output.write(struct.pack(">L",  (newPathSize+remainderLength)))
            output.write(struct.pack(">%ds" % (newPathSize+remainderLength), str(newPath)+str(remainder)))
            continue

        # write the chunk to the output stream
        output.write(struct.pack(">4s",  ctype))
        output.write(struct.pack(">L",  size))

        # Check if we need to add a pad byte
        chunk_data = lxchunk.read()
        if size % 2:
            chunk_data += "\0"
        output.write(chunk_data)

    return output

def process_file(deadlinePlugin, file):
    newPath = file
    modified = False
    aliasResolved = False
    if not os.path.isabs(file):
        scene_dir = deadlinePlugin.GetPluginInfoEntryWithDefault( "SceneFile", "" )
        if not scene_dir == "":
            scene_dir = os.path.dirname( replaceSlashesByOS( scene_dir ) )
        else:
            scene_dir = deadlinePlugin.GetPluginInfoEntryWithDefault( "SceneDirectory", "" )
        
        possible_path = replaceSlashesByOS( scene_dir )
        
        if ':' not in file:
            deadlinePlugin.LogWarning('Relative path '+ file + ' detected')
            # Check for asset files
            newPath, modified = find_existing_path( deadlinePlugin, file, possible_path, False )
        else:
            value_splited = file.split(':')
            host, path_to_file = value_splited[0], ''.join(value_splited[1:])
            not_network_dir = not os.path.isfile('//'+host+'/'+path_to_file)
            not_mounted_dir = not os.path.isfile('/'+host+'/'+path_to_file)
            if not_mounted_dir and not_network_dir:
                deadlinePlugin.LogWarning(file + ' could not be found')

    if deadlinePlugin.resolveAliases:
        newPath, aliasResolved = resolve_path_aliases( deadlinePlugin, newPath )

    if deadlinePlugin.massagePaths:
        newPath = massage_path( deadlinePlugin, newPath )
    
    if RepositoryUtils.PathMappingRequired( newPath ):
        newPath = str(RepositoryUtils.CheckPathMapping( newPath ))
        newPath = replaceSlashesByOS( newPath )
        
        deadlinePlugin.LogInfo( "    Updated to: %s" % newPath )
    elif modified or aliasResolved:
        deadlinePlugin.LogInfo( "    Updated to: %s" % newPath )
    else:
        deadlinePlugin.LogInfo( "    Not Updating Path: %s" % newPath )
        
    return newPath
    
def find_existing_path( deadlinePlugin, file, sceneDir, isOutputDir ):
    compareVal = remove_padding( deadlinePlugin, file )
    
    results = file
    projectDir = deadlinePlugin.GetPluginInfoEntryWithDefault( "ProjectDirectory", "" )
    projectDir = RepositoryUtils.CheckPathMapping( projectDir )
    newPath = ""
    
    checkPaths = []
   
    checkPaths.append( (projectDir, ( isOutputDir and not projectDir == "") ) ) #First the project directory use it if this is an output path and the project is defined
    checkPaths.append( ( sceneDir, isOutputDir) ) # check the Scene directory, use this if it is an output directory
    checkPaths.append( ( os.path.join(sceneDir, 'imported_images'), False )  ) # Check the imported_images directory next
    checkPaths.append( ( os.path.dirname(sceneDir), False )  ) # Check one folder up from the scene directory, used for proxy files
    
    for path, override in checkPaths:
        newPath = RepositoryUtils.CheckPathMapping(os.path.join(path, compareVal))
        if override or os.path.isfile(newPath):
            deadlinePlugin.LogWarning('Replace relative path with new path '+ newPath)
            results = RepositoryUtils.CheckPathMapping( os.path.join( path, file) )
            break
    else:
        deadlinePlugin.LogWarning('Unable to find file  ' + RepositoryUtils.CheckPathMapping( os.path.join(sceneDir, file) ) )
        deadlinePlugin.LogWarning('Not able to fix relative path ' + file)
        
    return results, ( results != file )

def process_itemsubchunks(deadlinePlugin, data, inFile, itemtype):
    """This is the real meat of the script. We've found an Item chunk of type
    VideoStill, now we need to process it's subchunks looking for a string
    channel (CHNS) called 'filename'. Once we've found that we can replace it
    with a new one containing our updated file path and stuff it back into the
    stream.

    """
    # stream to hold the "Item" chunk's subchunks.
    stream = cStringIO.StringIO()
    
    fileNames = [
        'file',
        'filename',
        'pattern',
        'irrlname',
        'irrsname',
        'filepath',
        'filepattern',
        'scene',
        'vray_file',
        'vray_filename',
        'vray_filepath',
        'vray_prepass_filename',
        'vray_ptex_file',
        'vray_irr_file',
        'vray_lc_file',
        'vray_phomap_file',
        'vray_caus_file',
        'vray_lens_file',
        'vray_stereo_shademap_file',
        'vray_cache_cache_path'
        ]

    while 1:
        try:
            # get next subchunk
            itemchunk = SubChunk(data)
        except EOFError:
            break

        scID = itemchunk.chunkname
        if scID == "CHNS":
            # found a string channel subchunk, parse it to get the channel name
            name, value = read_chns_subchunk(itemchunk)
            if not value == "":
                if name.lower() in fileNames:

                    # Got a 'filename' channel, rebuild it with the new image file
                    # path and write it to the subchunk stream
                    deadlinePlugin.LogInfo( "    With file name: %s" % value )
                    repack = True
                    if not os.path.isabs(value):
                        scene_dir = deadlinePlugin.GetPluginInfoEntryWithDefault( "SceneFile", "" )
                        if not scene_dir == "":
                            scene_dir = os.path.dirname(replaceSlashesByOS( scene_dir ) )
                        else:
                            scene_dir = deadlinePlugin.GetPluginInfoEntryWithDefault( "SceneDirectory", "" )
                        
                        possible_path = replaceSlashesByOS( scene_dir )
                         
                        if ':' not in value:
                            deadlinePlugin.LogWarning('Relative path '+ value + ' detected')
                            value, found =  find_existing_path( deadlinePlugin, value, possible_path, (itemtype == "renderOutput" ) )
                            repack = not found
                        else:
                            value_splited = value.split(':')
                            host, path_to_file = value_splited[0], ''.join(value_splited[1:])
                            not_network_dir = not os.path.isfile('//'+host+'/'+path_to_file)
                            not_mounted_dir = not os.path.isfile('/'+host+'/'+path_to_file)
                            if not_mounted_dir and not_network_dir:
                                deadlinePlugin.LogWarning(value + ' could not be found')

                    aliasResolved = False
                    if deadlinePlugin.resolveAliases:
                        value, aliasResolved = resolve_path_aliases( deadlinePlugin, value )

                    if deadlinePlugin.massagePaths:
                        value = massage_path( deadlinePlugin, value)

                    # this next if/else clause is where the new file path for the image
                    # is added set. The original script was intended to update/replace
                    # the root path alias to/from 'asset:' to another alias. You'll
                    # need to change the whole clause for your own uses but in a
                    # network rendering environment it's advisable to use a path alias
                    # as the 'root' location with images stored relative to that.
                    #if not value.startswith(prefix):
                    #    fpath = os.path.dirname(value)
                    #    idx = fpath.rfind('/Images/')
                    #    value = prefix + value[idx+1:]
                    #    stream.write(build_chns_subchunk(value).getvalue())
                    #    deadlinePlugin.LogInfo( "    Updated to: %s" % value )
                    if RepositoryUtils.PathMappingRequired( value ):
                        value = replaceSlashesByOS( RepositoryUtils.CheckPathMapping( value ) )
                                                
                        stream.write(build_chns_subchunk(value).getvalue())
                        deadlinePlugin.LogInfo( "    Updated to: %s" % value )
                    elif aliasResolved:
                        stream.write( build_chns_subchunk( value ).getvalue() )
                        deadlinePlugin.LogInfo( "    Updated to: %s" % value )
                    elif repack:
                        itemchunk.seek(0)
                        repack_subchunk(stream, scID, itemchunk.chunksize, itemchunk)
                        deadlinePlugin.LogInfo( "    Repacking. No update required." )
                    else:
                        stream.write(build_chns_subchunk(value).getvalue())
                        deadlinePlugin.LogInfo( "    Updated to: %s" % value )
                else:
                    # otherwise we've got a 'CHNS' subchunk we're not interested
                    # in so reset the file pointer to the start of the chunk and
                    # repack it into the stream.
                    itemchunk.seek(0)
                    repack_subchunk(stream, scID, itemchunk.chunksize, itemchunk)
            else:
                    # If the Value is empty then we don't want to do any work to it so just repack it.
                    itemchunk.seek(0)
                    repack_subchunk(stream, scID, itemchunk.chunksize, itemchunk)     
        else:
            # all other subchunk types are just repacked back into the subchunk
            # stream unaltered.
            repack_subchunk(stream, scID, itemchunk.chunksize, itemchunk)

    return stream

def replaceSlashesByOS( value ):
    if SystemUtils.IsRunningOnWindows():
        value = value.replace('/', '\\')
    else:
        value = value.replace( "\\", "/" )
        
    return value
    
def remove_padding( deadlinePlugin, path ):
    paddingRegex = re.compile( ".*(<F+>|\[#+\]).*" )
    match = re.match( paddingRegex, path )
    if( match != None ):
        job = deadlinePlugin.GetJob()
        frameNum = job.FirstFrame

        padding = match.group(1)
        
        frame = StringUtils.ToZeroPaddedString( frameNum, len( padding ) - 2, False )
        path = path.replace( padding, frame )
    
    return path

# If path massaging is enabled, we can manipulate what the raw path looks like before feeding it into
# RepositoryUtils.CheckPathMapping(). This allows path mapping to work with normal path formatting, and
# doesn't require users to define path mapping entries that handle modo's unique path formatting.
# 
# Here are examples of what the raw path can look like in modo and what it will look like after massaging:
#   - Windows drive letter:  R:share/   ->   R:/share/
#   - Windows UNC path:  server:share/   ->   //server/share/
#   - OSX Volumes path:  Volumes:share/   ->   /Volumes/share/
def massage_path( deadlinePlugin, path ):
    deadlinePlugin.LogInfo( "        Raw path: " + path )
    
    path = replaceSlashesByOS( path )
    
    # Special case to handle OSX's Volumes path.
    osxRegex = Regex( "^Volumes:", RegexOptions.IgnoreCase )
    if osxRegex.IsMatch( path ):
        path = osxRegex.Replace( path, "/Volumes/" )
    else:
        # Look for a UNC server or drive letter.
        winRegex = Regex( r"^([^\\]+):[\/\\]?" )
        winMatch = winRegex.Match( path )
        if winMatch.Success:
            # If server name is only one letter in length, assume it's a drive letter, which needs to be handled differently.
            serverName = winMatch.Groups[1].Value
            if len(serverName) > 1:
                path = winRegex.Replace( path, "\\\\" + serverName + "\\" )
            else:
                path = winRegex.Replace( path, serverName + ":\\" )
    
    deadlinePlugin.LogInfo( "        Massaged path: " + path )

    return path

def resolve_path_aliases( deadlinePlugin, path ):
    """
    Replaces any path aliases found in a path with the full path as it was defined on the submitting machine.
    :param deadlinePlugin: Deadline Plugin to Pull the path Aliases from
    :param path: The path that we want to resolve aliases for
    :return: The path that may have been modified and a boolean which states if we have successfully resolved a path alias.
    """
    resolved = False
    # if any path aliases were defined on the submitting machine then we want to start by checking if the path starts
    if deadlinePlugin.pathAliases:
        aliasMatch = re.search( r"^(%s):" % "|".join( deadlinePlugin.pathAliases.iterkeys() ), path )
        #Group 0 = The full match ( Alias: )
        #Group 1 = Just the path Alias
        if aliasMatch:
            fromPath = aliasMatch.group( 0 )
            toPath = deadlinePlugin.pathAliases[ aliasMatch.group( 1 ) ]
            #Aliases can but are not guaranteed to end with a separator and we need to ensure that they end with a slash.
            if not toPath.endswith( os.sep ):
                toPath += os.sep

            path = path.replace( fromPath, toPath )
            resolved = True

    return path, resolved

def map_paths( deadlinePlugin, inFile, outFile ):
    with open(inFile, 'rb') as curr_scene:
        try:
            formID, datasize, formtype = struct.unpack(">4s1L4s",  curr_scene.read(12))
        except:
            deadlinePlugin.FailRender( "Can't perform path mapping on '%s' because it is not a valid modo file" % inFile )

        if formtype != "LXOB":
            deadlinePlugin.FailRender( "Can't perform path mapping on '%s' because it is not a valid modo scene file" % inFile )

        deadlinePlugin.LogInfo( "Performing path mapping on '%s'" % inFile )

        # process the file's chunks
        data = do_chunks(deadlinePlugin, curr_scene, inFile)

        # changing file paths changes the size of the subchunks holding them
        # which, in turn, changes the size of the chunks the subchunks belong
        # to, which changes the overall size of the IFF file. We need to
        # update the size field at the head of the file to reflect that.
        data.seek(0, 2)
        fsize = data.tell() + 4

        with open(outFile, 'wb') as fout:
            fout.write(struct.pack(">4s1L4s",  formID, fsize, formtype))
            fout.write(data.getvalue())

