from System.IO import *

from Deadline.Scripting import *
from Deadline.Plugins import *

def GetDeadlinePlugin():
    return VrayPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class VrayPlugin(DeadlinePlugin):
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PostRenderTasksCallback += self.PostRenderTasks
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PostRenderTasksCallback
    
    def InitializeProcess(self):
        self.SingleFramesOnly = True
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( "Error opening file.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( "Cannot open image file.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( ": ([0-9]+\.[0-9]*)% done" ).HandleCallback += self.HandleProgress
        self.AddStdoutHandlerCallback( ": ([0-9]+)% done" ).HandleCallback += self.HandleProgress
        
    def RenderExecutable(self):
        exeList = self.GetConfigEntry( "Vrimg2Exr_RenderExecutable" )
        exe = FileUtils.SearchFileList( exeList )
        if( exe == "" ):
            self.FailRender( "Vrimg2Exr render executable was not found in the semicolon separated list \"" + exeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return exe
        
    def RenderArgument(self):
        arguments = ""
        
        filename = self.GetPluginInfoEntry( "InputFile" )
        filename = RepositoryUtils.CheckPathMapping( filename )
        
        currPadding = FrameUtils.GetFrameStringFromFilename( filename )
        paddingSize = len(currPadding)
        if paddingSize > 0:
            newPadding = StringUtils.ToZeroPaddedString( self.GetStartFrame(), paddingSize, False )
            filename = FrameUtils.SubstituteFrameNumber( filename, newPadding )
        
        # Windows handles both slashes as long as we don't mix and match the first two
        if SystemUtils.IsRunningOnWindows():
            # Check if it is a unc path
            if(filename.startswith("\\")):
                if(filename[0:2] != "\\\\"):
                    filename = "\\" + filename
            elif(filename.startswith("/")):
                if(filename[0:2] != "//"):
                    filename = "/" + filename
        else:
            filename = filename.replace("\\","/")
            if(filename[0:2] == "//"):
                filename = filename[1:-1]
        
        arguments = arguments + " \"" + filename + "\""
        
        outFilename = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip()
        if outFilename != "":
            outFilename = RepositoryUtils.CheckPathMapping( outFilename )
            if paddingSize > 0:
                outPath = Path.GetDirectoryName( outFilename )
                outPrefix = Path.GetFileNameWithoutExtension( outFilename )
                outFilename = Path.Combine( outPath, outPrefix + newPadding + ".exr" )
            
            if SystemUtils.IsRunningOnWindows():
                # Check if it is a unc path
                if(outFilename.startswith("\\")):
                    if(outFilename[0:2] != "\\\\"):
                        outFilename = "\\" + outFilename
                elif(outFilename.startswith("/")):
                    if(outFilename[0:2] != "//"):
                        outFilename = "/" + outFilename
            else:
                outFilename = outFilename.replace("\\","/")
                if(outFilename[0:2] == "//"):
                    outFilename = outFilename[1:-1]
            
            arguments = arguments + " \"" + outFilename + "\""
            
        if self.GetBooleanPluginInfoEntryWithDefault( "Half", False ):
            arguments = arguments + " -half"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "sRGB", False ):
            arguments = arguments + " -sRGB"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "DataWindow", False ):
            arguments = arguments + " -dataWindow"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "SeparateFiles", False ):
            arguments = arguments + " -separateFiles"
            
        if self.GetBooleanPluginInfoEntryWithDefault( "MultiPart", False ):
            arguments = arguments + " -multiPart"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "LongChanNames", False ):
            arguments = arguments + " -longChanNames"
        
        if self.GetBooleanPluginInfoEntryWithDefault( "SetGamma", False ):
            arguments = arguments + " -gamma " + self.GetPluginInfoEntry( "Gamma" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "SetChannel", False ):
            channel = self.GetPluginInfoEntryWithDefault( "Channel", "" ).strip()
            if channel == "":
                self.LogWarning( "Not setting channel because specified channel is blank" )
            else:
                arguments = arguments + " -channel \"" + self.GetPluginInfoEntry( "Channel" ) + "\""
        
        if self.GetBooleanPluginInfoEntryWithDefault( "SetCompression", False ):
            arguments = arguments + " -compression " + self.GetPluginInfoEntry( "Compression" )
        
        if self.GetBooleanPluginInfoEntryWithDefault( "SetBufferSize", False ):
            arguments = arguments + " -bufsize " + self.GetPluginInfoEntry( "BufferSize" )
            
        threads = self.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if threads > 0:
            arguments = arguments + " -threads " + str(threads)
        
        return arguments
    
    def HandleError( self ):
        self.FailRender( self.GetRegexMatch(0) )
    
    def HandleProgress( self ):
        self.SetProgress( float(self.GetRegexMatch(1)) )
    
    def PostRenderTasks(self):
        if self.GetBooleanPluginInfoEntryWithDefault( "DeleteInputFiles", False ):
            filename = self.GetPluginInfoEntry( "InputFile" )
            filename = RepositoryUtils.CheckPathMapping( filename )
            
            currPadding = FrameUtils.GetFrameStringFromFilename( filename )
            paddingSize = len(currPadding)
            if paddingSize > 0:
                newPadding = StringUtils.ToZeroPaddedString( self.GetStartFrame(), paddingSize, False )
                filename = FrameUtils.SubstituteFrameNumber( filename, newPadding )
            
            # Windows handles both slashes as long as we don't mix and match the first two
            if SystemUtils.IsRunningOnWindows():
                # Check if it is a unc path
                if(filename.startswith("\\")):
                    if(filename[0:2] != "\\\\"):
                        filename = "\\" + filename
                elif(filename.startswith("/")):
                    if(filename[0:2] != "//"):
                        filename = "/" + filename
            else:
                filename = filename.replace("\\","/")
                if(filename[0:2] == "//"):
                    filename = filename[1:-1]
            
            self.LogInfo( "Deleting input vrimg file \"" + filename + "\"" )
            File.Delete( filename )
