import clr

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
    return NaiadPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Naiad plugin.
######################################################################
class NaiadPlugin (DeadlinePlugin):
    JobMode = ""
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.IsSingleFramesOnlyCallback += self.IsSingleFramesOnly
        self.PreRenderTasksCallback += self.PreRenderTasks
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.IsSingleFramesOnlyCallback
        del self.PreRenderTasksCallback
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple
        
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( "NAIAD ERROR.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( "Solving frame ([0-9]+)" ).HandleCallback += self.HandleSimProgress
        
    def IsSingleFramesOnly( self ):
        self.JobMode = self.GetPluginInfoEntry( "JobMode" ) 
        return (self.JobMode == "Emp2Prt")
    
    def PreRenderTasks( self ):
        if self.JobMode != "Simulation" and self.JobMode != "Emp2Prt":
            self.FailRender( "Unrecognized job mode: " + self.JobMode )
        else:
            self.LogInfo( "Job mode: " + self.JobMode )
    
    def RenderExecutable( self ):
        exeList = self.GetConfigEntry( self.JobMode + "_Executable" )
        exe = FileUtils.SearchFileList( exeList )
        if( exe == "" ):
            self.FailRender( self.JobMode + " executable was not found in the semicolon separated list \"" + exeList + "\". The path to the " + self.JobMode + " executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return exe
        
    def RenderArgument( self ):
        arguments = ""
        
        if self.JobMode == "Simulation":
            sceneFileName = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
            sceneFileName = RepositoryUtils.CheckPathMapping( sceneFileName ).replace( "\\", "/" )
            self.LogInfo( "Naiad file: " + sceneFileName )
            arguments = "\"" + sceneFileName + "\""
            
            startFrame = str(self.GetStartFrame())
            endFrame = str(self.GetEndFrame())
            self.LogInfo( "Start frame: " + startFrame )
            self.LogInfo( "End frame: " + endFrame )
            arguments += " --frames " + startFrame + " " + endFrame
            
            threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
            if threads > 0:
                self.LogInfo( "Threads: " + str(threads) )
                arguments += " --threads " + str(threads)
            else:
                self.LogInfo( "Threads: 0 (uses default)" )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "Verbose", False ):
                self.LogInfo( "Verbose: enabled" )
                arguments += " --verbose"
            else:
                self.LogInfo( "Verbose: disabled" )
            
        elif self.JobMode == "Emp2Prt":
            empBodyName = self.GetPluginInfoEntry( "EmpBodyName" )
            self.LogInfo( "EMP body: " + empBodyName )
            
            empFileName = self.GetPluginInfoEntry( "EmpFileName" )
            empFileName = RepositoryUtils.CheckPathMapping( empFileName ).replace( "\\", "/" )
            padding = StringUtils.ToZeroPaddedString( self.GetStartFrame(), 4 )
            empFileName = empFileName.replace( "#", padding )
            
            vars = Environment.GetEnvironmentVariables()
            for var in vars.Keys:
                varCode = "`$" + var + "`"
                if empFileName.find( varCode ) >= 0:
                    varValue = vars[ var ]
                    self.LogInfo( "Replacing " + varCode + " in path with " + varValue )
                    empFileName = empFileName.replace( varCode, varValue )
            
            self.LogInfo( "EMP file: " + empFileName )
            
            outFileName = Path.ChangeExtension( empFileName, ".prt" )
            self.LogInfo( "Output file: " + outFileName )
            
            arguments = "\"" + empFileName + "\" \"" + empBodyName + "\" \"" + outFileName + "\""

        return arguments
    
    def HandleError( self ):
        self.FailRender( self.GetRegexMatch( 0 ) )
    
    def HandleSimProgress( self ):
        self.SetStatusMessage( self.GetRegexMatch( 0 ) )
        
        startFrame = float(self.GetStartFrame())
        endFrame = float(self.GetEndFrame())
        currentFrame = float(self.GetRegexMatch( 1 ))
        if (endFrame - startFrame + 1) != 0:
            self.SetProgress( ((currentFrame - startFrame) * 100.0) / (endFrame - startFrame + 1) )
