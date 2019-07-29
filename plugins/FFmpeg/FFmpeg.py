from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return FFmpegPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class FFmpegPlugin(DeadlinePlugin):
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
    
    def InitializeProcess(self):
        self.SingleFramesOnly=False
        self.StdoutHandling=True
        
        self.AddStdoutHandlerCallback(".*Error.*").HandleCallback += self.HandleStdoutError
    
    def RenderExecutable(self):
        FFmpegExeList = self.GetConfigEntry("FFmpeg_RenderExecutable")
        FFmpegExe = FileUtils.SearchFileList( FFmpegExeList )
        
        if( FFmpegExe == "" ):
            self.FailRender( "No file found in the semicolon separated list \"" + FFmpegExeList+ "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return FFmpegExe
        
    def RenderArgument(self):
        outputFile = self.GetPluginInfoEntryWithDefault( "OutputFile", "" )
        outputFile = RepositoryUtils.CheckPathMapping( outputFile )
        outputFile = self.ProcessPath( outputFile )
        
        outputArgs = self.GetPluginInfoEntryWithDefault( "OutputArgs", "" )
        additionalArgs = self.GetPluginInfoEntryWithDefault( "AdditionalArgs", "" )
        useSameArgs = self.GetBooleanPluginInfoEntryWithDefault( "UseSameInputArgs", False )
        
        videoPreset = self.GetPluginInfoEntryWithDefault( "VideoPreset", "" )
        videoPreset = RepositoryUtils.CheckPathMapping( videoPreset )
        videoPreset = self.ProcessPath( videoPreset )
        
        audioPreset = self.GetPluginInfoEntryWithDefault( "AudioPreset", "" )
        audioPreset = RepositoryUtils.CheckPathMapping( audioPreset )
        audioPreset = self.ProcessPath( audioPreset )
        
        subtitlePreset = self.GetPluginInfoEntryWithDefault( "SubtitlePreset", "" )
        subtitlePreset = RepositoryUtils.CheckPathMapping( subtitlePreset )
        subtitlePreset = self.ProcessPath( subtitlePreset )
        
        if useSameArgs:
            inputArgs0 = self.GetPluginInfoEntryWithDefault( "InputArgs0", "" )
            
        if( outputFile == "" ):
            self.FailRender( "No output file was specified." )
        
        renderArgument = ""
        
        if useSameArgs:
            self.LogInfo( "UseSameInputArgs = True" )
        else:
            self.LogInfo( "UseSameInputArgs = False" )
        
        for i in range(0,9):
            inputFile = self.GetPluginInfoEntryWithDefault( "InputFile%d" % i, "" )
            inputArgs = self.GetPluginInfoEntryWithDefault( "InputArgs%d" % i, "" )
            replacePadding = self.GetBooleanPluginInfoEntryWithDefault( "ReplacePadding%d" % i, True )
            
            if inputFile != "":
                inputFile = RepositoryUtils.CheckPathMapping( inputFile )
                inputFile = self.ProcessPath( inputFile )
                
                # img-%03d
                if replacePadding:
                    currPadding = FrameUtils.GetFrameStringFromFilename( inputFile )
                    paddingSize = len( currPadding )
                    
                    if '-' in currPadding:
                        front = "-%"
                        paddingSize = paddingSize - 1
                    else:
                        front = "%"
                    
                    if paddingSize > 0:
                        padding = front + StringUtils.ToZeroPaddedString( paddingSize, 2, False ) + "d"
                        inputFile = FrameUtils.SubstituteFrameNumber( inputFile, padding )
                
                if (useSameArgs and inputArgs0 != ""):
                    renderArgument += "%s " % inputArgs0
                elif (not useSameArgs and inputArgs != ""):
                    renderArgument += "%s " % inputArgs
                
                renderArgument += "-i \"%s\" " % inputFile
        
        if outputArgs != "":
            renderArgument += "%s " % outputArgs
        
        renderArgument += "-y \"%s\"" % outputFile
        
        if additionalArgs != "":
            renderArgument += " %s" % additionalArgs
            
        if videoPreset != "":
            renderArgument += " -vpre \"%s\"" % videoPreset
        
        if audioPreset != "":
            renderArgument += " -apre \"%s\"" % audioPreset
        
        if subtitlePreset != "":
            renderArgument += " -spre \"%s\"" % subtitlePreset
                
        return renderArgument
        
    def ProcessPath( self, filepath ):
        if SystemUtils.IsRunningOnWindows():
            filepath = filepath.replace("/","\\")
            if filepath.startswith( "\\" ) and not filepath.startswith( "\\\\" ):
                filepath = "\\" + filepath
        else:
            filepath = filepath.replace("\\","/")
        return filepath
        
    def PreRenderTasks(self):
        self.LogInfo( "FFmpeg job starting..." ) 
        
    def PostRenderTasks(self):
        self.LogInfo( "FFmpeg job finished." )
        
    def HandleStdoutError(self):
        self.FailRender( self.GetRegexMatch(0) )
