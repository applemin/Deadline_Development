import os

from System.IO import *

from Deadline.Scripting import *
from Deadline.Plugins import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return VDenoisePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the VDenoise plugin.
######################################################################
class VDenoisePlugin( DeadlinePlugin ):    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
    
    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess( self ):
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( "error.*|Error.*" ).HandleCallback += self.HandleStdoutError
        
    def RenderExecutable( self ):
        executableList = self.GetConfigEntry( "VDenoise_RenderExecutable" )
        executable = FileUtils.SearchFileList( executableList )
        if executable == "":
            self.FailRender( "VDenoise executable was not found in the semicolon separated list \"" + executableList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return executable

    def RenderArgument( self ):
        usingFrames = self.GetBooleanPluginInfoEntryWithDefault( "UsingFrames", False )

        renderArguments = "-display=0 "

        renderArguments += ( "-inputFile=\"%s\" " % self.GetPluginInfoEntryWithDefault( "InputPath", "" ) )

        renderArguments += ( "-mode=%s " % self.GetPluginInfoEntryWithDefault( "DenoiseMode", "Default" ) )
        renderArguments += ( "-boost=%s " % self.GetPluginInfoEntryWithDefault( "Boost", "0" ) )

        if usingFrames:
            startFrame = self.GetStartFrame()
            endFrame = self.GetEndFrame()
            renderArguments += ( "-frames=%s-%s " % ( startFrame, endFrame ) )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "SkipExisting", False ):
             renderArguments += ( "-skipExisting=1 " )
         
        if self.GetBooleanPluginInfoEntryWithDefault( "DenoiseElements", False ):
             renderArguments += ( "-elements=1 " )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "UseGPU", False ):
             renderArguments += ( "-useGpu=1 " )
            
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideThreshold", False ):
             renderArguments += ( "-threshold=%s " % self.GetPluginInfoEntryWithDefault( "Threshold", "0.001" ) )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideStrength", False ):
             renderArguments += ("-strength=%s " % self.GetPluginInfoEntryWithDefault( "Strength", "1" ) )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "OverrideRadius", False ):
             renderArguments += ( "-radius=%s " % self.GetPluginInfoEntryWithDefault( "PixelRadius", "10" ) )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "AdjustRadius", False ):
             renderArguments += ( "-autoRadius=1 " )
        
        renderArguments += ( "-frameBlend=%s " % self.GetPluginInfoEntryWithDefault( "FrameBlend", "1" ) )
        renderArguments += ( "-strips=%s " % self.GetPluginInfoEntryWithDefault( "RenderStrips", "-1" ) )
        
        return renderArguments

    ######################################################################
    ## Standard Out Handlers
    ######################################################################
    def HandleStdoutError( self ):
        self.FailRender( self.GetRegexMatch( 0 ) )
        