import re

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text.RegularExpressions import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return RealFlowPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class RealFlowPlugin (DeadlinePlugin):
    UseNoGuiArgument = False
    StartPreviousFrame = False
    
    CurrentFrame = None
    
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

        # Initial values to support Task Render Status
        self.CurrentFrame = 0
        self.ElapsedTime = "00:00:00"
        self.RemainingTime = "00:00:00"
        self.AverageTime = "00:00:00"
        self.HybridoStatus = ""

        self.AddStdoutHandlerCallback( ".*RealFlow Error.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( ".*You have reached the maximum number of licenses.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( ".*A critial error has been found in the fluids engine.*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( ".*RealFlow Warning.*" ).HandleCallback += self.HandleStdoutWarning
        self.AddStdoutHandlerCallback( ".*Frame ([-]?[0-9]+) finished.*" ).HandleCallback += self.HandleProgress

        # New progress handling for RealFlow 2013
        self.AddStdoutHandlerCallback( ".*Frame ([-]?[0-9]+) started.*" ).HandleCallback += self.HandleFrameStart
        self.AddStdoutHandlerCallback( ".*Frame finished.*" ).HandleCallback += self.HandleFrameFinished

        # Task Render Status
        self.AddStdoutHandlerCallback( ".*Elapsed time: ([0-9]+:[0-9]+:[0-9]+)" ).HandleCallback += self.HandleRenderStatusProgress # 0: STDOUT: Elapsed time: 00:00:22
        self.AddStdoutHandlerCallback( ".*Remaining time \\(estimated\\): ([0-9]+:[0-9]+:[0-9]+)" ).HandleCallback += self.HandleRenderStatusProgress # 0: STDOUT: Remaining time (estimated): 00:01:18
        self.AddStdoutHandlerCallback( ".*Average time \\(frame\\): ([0-9]+:[0-9]+:[0-9]+)" ).HandleCallback += self.HandleRenderStatusProgress # 0: STDOUT: Average time (frame): 00:00:01
        self.AddStdoutHandlerCallback( ".*(\\[.* cells\\] \\[.* particles\\] \\[.* cell size\\])" ).HandleCallback += self.HandleRenderStatusProgress # Hybrido Status [134x35x132 619,080 cells] [1,630,893 particles] [0.150000 cell size]

    def RenderExecutable(self):
        version = self.GetPluginInfoEntryWithDefault( "Version", "4" ).strip()
        rfExeList = self.GetConfigEntry( "RF" + version + "_RenderExecutable" )
        rfExe = ""
        
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower().strip()
        
        if SystemUtils.IsRunningOnWindows():
            if( build == "32bit" ):
                self.LogInfo( "Enforcing 32 bit build of RealFlow" )
                rfExe = FileUtils.SearchFileListFor32Bit( rfExeList )
                if( rfExe == "" ):
                    self.LogWarning( "32 bit RealFlow " + version + " render executable was not found in the semicolon separated list \"" + rfExeList + "\". Checking for any executable that exists instead." )
            elif( build == "64bit" ):
                self.LogInfo( "Enforcing 64 bit build of RealFlow" )
                rfExe = FileUtils.SearchFileListFor64Bit( rfExeList )
                if( rfExe == "" ):
                    self.LogWarning( "64 bit RealFlow " + version + " render executable was not found in the semicolon separated list \"" + rfExeList + "\". Checking for any executable that exists instead." )
        
        if( rfExe == "" ):
            self.LogInfo( "Not enforcing a build of RealFlow" )
            rfExe = FileUtils.SearchFileList( rfExeList )
            if( rfExe == "" ):
                self.FailRender( "RealFlow " + version + " render executable was not found in the semicolon separated list \"" + rfExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        self.UseNoGuiArgument = False
        if Path.GetFileNameWithoutExtension( rfExe ).lower() != "realflownode":
            self.UseNoGuiArgument = True
        
        return rfExe
        
    def RenderArgument(self):
        version = int(self.GetPluginInfoEntryWithDefault( "Version", "4" ).strip())
        
        self.StartPreviousFrame = self.GetBooleanPluginInfoEntryWithDefault( "StartPreviousFrame", False )
        
        # Get the start frame and end frame for the simulation (required).
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if self.StartPreviousFrame and startFrame > 0:
            startFrame = startFrame - 1
        
        # Get the optional settings.
        idoc = self.GetPluginInfoEntryWithDefault( "IDOC", "" ).strip()
        threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        mesh = self.GetBooleanPluginInfoEntryWithDefault( "Mesh", False )
        useCache = self.GetBooleanPluginInfoEntryWithDefault( "UseCache", False )
        
        script = self.GetPluginInfoEntryWithDefault( "Script", "" ).strip()
        
        # Reset scene, graph and preview options only available in 2013 and later.
        resetScene = False
        preview = False
        graph = ""
        if version >= 2013:
            resetScene = self.GetBooleanPluginInfoEntryWithDefault( "ResetScene", False )
            preview = self.GetBooleanPluginInfoEntryWithDefault( "Preview", False )
            graph = self.GetPluginInfoEntryWithDefault( "Graph", "" ).strip()
        
        # Get the scene filename.
        scene = self.GetPluginInfoEntryWithDefault( "SceneFile" , self.GetDataFilename())
        scene = RepositoryUtils.CheckPathMapping( scene )
        
        # Windows handles both slashes as long as we don't mix and match the first two
        if SystemUtils.IsRunningOnWindows():
            # Check if it is a unc path
            if scene.startswith( "\\" ):
                if scene[0:2] != "\\\\":
                    scene = "\\" + scene
            elif scene.startswith( "/" ):
                if scene[0:2] != "//":
                    scene = "/" + scene
        else:
            scene = scene.replace("\\","/")
            if scene[0:2] == "//":
                scene = scene[1:-1]
        
        # Build the arguments as required and return them.
        arguments = ""
        if( self.UseNoGuiArgument ):
            arguments += " -nogui"
        
        arguments += " -range " + str(startFrame) + " " + str(endFrame)
        
        if( threads > 0 ):
            arguments += " -threads " + str(threads)
        
        if( mesh ):
            arguments +=" -mesh"
        
        if( useCache ):
            arguments += " -useCache"
        
        if( resetScene ):
            arguments += " -reset"
            
        if( preview ):
            arguments += " -maxwell"
        
        if( idoc != "" ):
            arguments += " -idoc \"" + idoc + "\""
        
        if( script != "" ):
            arguments += " -script \"" + script + "\""
            
        if( graph != "" ):
            arguments += " -graph \"" + graph + "\""
        
        arguments += " \"" + scene + "\""
        return arguments

    def HandleStdoutError(self):
        self.FailRender( self.GetRegexMatch(0) )

    def HandleStdoutWarning(self):
        if self.GetRegexMatch(0).find( "Invalid license" ) >=0:
            self.FailRender( self.GetRegexMatch(0) )

    def HandleProgress(self):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        finishedFrame = int(self.GetRegexMatch(1))
        self.CalculateProgress(startFrame, endFrame, finishedFrame)

    def HandleFrameStart(self):
        self.CurrentFrame = int(self.GetRegexMatch(1))

    def HandleFrameFinished(self):
        if self.CurrentFrame != None:
            startFrame = self.GetStartFrame()
            endFrame = self.GetEndFrame()
            self.CalculateProgress(startFrame, endFrame, self.CurrentFrame)

    def CalculateProgress(self, startFrame, endFrame, finishedFrame):
        if self.StartPreviousFrame and startFrame > 0:
            startFrame = startFrame - 1
        
        numerator = finishedFrame - startFrame
        denominator = endFrame - startFrame
        if denominator != 0:
            self.SetProgress( (float(numerator)/float(denominator)) * 100 )
            #self.LogInfo( "set progress to " + str((float(numerator)/float(denominator)) * 100))

    def HandleRenderStatusProgress(self):
        if re.match( r"Elapsed time:", self.GetRegexMatch( 0 ) ):
            self.ElapsedTime = self.GetRegexMatch( 1 )
        elif re.match( r"Remaining time \(estimated\):", self.GetRegexMatch( 0 ) ):
            self.RemainingTime = self.GetRegexMatch( 1 )
        elif re.match( r"Average time \(frame\):", self.GetRegexMatch( 0 ) ):
            self.AverageTime = self.GetRegexMatch( 1 )
        elif re.match( r"", self.GetRegexMatch( 0 ) ):
            self.HybridoStatus = self.GetRegexMatch( 1 )
        else:
            pass

        msg = "RF Sim: (" + str(self.CurrentFrame) + " to " + str(self.GetEndFrame()) + ") - Elap.Time: " + self.ElapsedTime + " - Rem.Time: " + self.RemainingTime + " - Av.Time: " + self.AverageTime + " " + self.HybridoStatus
        self.SetStatusMessage( msg )
