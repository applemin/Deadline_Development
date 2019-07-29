from __future__ import print_function

import os

from Deadline.Plugins import DeadlinePlugin
from Deadline.Scripting import FileUtils, RepositoryUtils

def GetDeadlinePlugin():
    return SketchUpPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class SketchUpPlugin( DeadlinePlugin ):
    INFO_FILE_LINE_DESC = (
        "ExportType",
        "OutputDirectory",
        "OutputFilename",
        "OutputExtension",
        "Width",
        "Height",
        "AntiAlias",
        "Compression",
        "Transparent",
        "UseVray",
        "FrameRate",
        "SceneName",
        "VrayVersion",
        "StartFrame",
        "EndFrame"
    )

    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks

        self.infoFilePath = ""

    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback

    def InitializeProcess( self ):
        self.StdoutHandling = True
        self.PopupHandling = True

        self.AddStdoutHandlerCallback( "Error: .*" ).HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback( "SU_PROGRESS ([0-9]+).*%" ).HandleCallback += self.HandleStdoutProgress

        self.AddPopupIgnorer( "Export Progress..." )
        self.AddPopupIgnorer( "Render history settings" ) # V-Ray

        self.AddPopupHandler( "SketchUp", "Do you wish to open this file as Read-Only?", "Yes" )
        self.AddPopupHandler( "SketchUp", "Save changes to", "No" )

        self.AddPopupHandler( "SketchUp", "No" ) # if VRay loads, it'll always ask to save, even though nothing changed
        self.AddPopupHandler( "SketchUp", "OK" )
        self.AddPopupHandler( "Welcome to SketchUp", "Start using SketchUp" )  # Doesn't seem to work. Geez...

    def RenderExecutable( self ):
        version = self.GetPluginInfoEntryWithDefault( "Version", "2017" )
        sketchUpExeList = self.GetConfigEntry( "SketchUp_" + version + "_Executable" )

        sketchUpExe = FileUtils.SearchFileList( sketchUpExeList )
        if not sketchUpExe:
            self.FailRender( "SketchUp " + version + " executable was not found in the semicolon separated list \"" + sketchUpExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return sketchUpExe

    def RenderArgument( self ):
        outputDirectory = self.GetPluginInfoEntryWithDefault( "ExportDirectory", "" )
        outputFilename = self.GetPluginInfoEntryWithDefault( "ExportName", "" )
        outputFormat = self.GetPluginInfoEntryWithDefault( "ExportFormat", "" )

        output = os.path.join( outputDirectory, outputFilename + outputFormat )
        output = RepositoryUtils.CheckPathMapping( output )

        scene = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
        scene = RepositoryUtils.CheckPathMapping( scene )

        # Windows handles both slashes as long as we don't mix and match the first two
        if os.name == 'nt':
            # Check if it is a unc path
            if scene.startswith( "\\" ):
                if scene[0:2] != "\\\\":
                    scene = "\\" + scene
            elif scene.startswith( "/" ):
                if scene[0:2] != "//":
                    scene = "/" + scene

            if output.startswith( "\\" ):
                if output[0:2] != "\\\\":
                    output = "\\" + output
            elif output.startswith( "/" ):
                if output[0:2] != "//":
                    output = "/" + output

        else:
            scene = scene.replace( "\\", "/" )
            if scene[0:2] == "//":
                scene = scene[1:len(scene)]

            output = output.replace( "\\", "/" )
            if output[0:2] == "//":
                output = output[1:len(output)]

        # We should fail out early here if the file can't be found
        if not os.path.isfile( scene ):
            self.FailRender( 'Could not find the following scene file: "%s"' % scene )

        # Check if directory exists, create if otherwise. SketchUp won't export anything if the directory doesn't exist
        directory = os.path.dirname( output )
        if not os.path.exists( directory ):
            self.LogWarning( 'The following output folder does not exist: "%s", trying to create it...' % directory )
            try:
                os.makedirs( directory )
            except Exception as e:
                self.FailRender( 'Failed to create the directory: "%s", please ensure the directory is created and accessible before trying again.\n%s' % ( directory, e ) )
        elif not os.path.isdir( directory ):
            self.FailRender( '"%s" exists but it is not a directory. Choose a different destination and ensure it exists and is accessible.' % directory )

        rubyScript = os.path.join( self.GetPluginDirectory(), "SketchUpDeadline.rb" )

        outputFilename, outputExtension = os.path.splitext( os.path.basename( output ) )
        infoFileContents = [
            self.GetPluginInfoEntryWithDefault( "ExportType", "" ),
            os.path.dirname( output ),
            outputFilename,
            outputExtension,
            self.GetPluginInfoEntryWithDefault( "Width", "0" ),
            self.GetPluginInfoEntryWithDefault( "Height", "0" ),
            self.GetPluginInfoEntryWithDefault( "AntiAlias", "False" ),
            self.GetPluginInfoEntryWithDefault( "Compression", "0" ),
            self.GetPluginInfoEntryWithDefault( "Transparent", "False" ),
            self.GetPluginInfoEntryWithDefault( "UseVray", "False" ) ,
            self.GetPluginInfoEntryWithDefault( "FrameRate", "0" ),
            self.GetPluginInfoEntryWithDefault( "SceneName", "" ),
            self.GetPluginInfoEntryWithDefault( "VrayVersion", "2" ),
            str( self.GetStartFrame() ),
            str( self.GetEndFrame() )
        ]

        self.LogInfo("Contents of DEADLINE_SKETCHUP_INFO file:")
        with open( self.infoFilePath, 'w' ) as fileHandle:
            for line_desc, line in zip(self.INFO_FILE_LINE_DESC, infoFileContents):
                fileHandle.write( line + '\n' )
                self.LogInfo("\t%s=%s" % (line_desc, line))

        # Construct the command line and return it
        arguments = ' -RubyStartup "' + rubyScript + '" "' + scene + '"'

        return arguments

    def PreRenderTasks(self):
        self.infoFilePath = os.path.join( self.GetJobsDataDirectory(), "deadline_sketchup_info.txt" )
        self.SetEnvironmentVariable( "DEADLINE_SKETCHUP_INFO", self.infoFilePath )
        self.LogInfo( 'Setting DEADLINE_SKETCHUP_INFO environment variable to "%s"' % self.infoFilePath )

        self.LogInfo( "Starting SketchUp Job" )
        self.SetProgress(0)

    def PostRenderTasks( self ):
        self.LogInfo( "Finished SketchUp Job" )
        self.SetProgress( 100 )

    def HandleStdoutError(self):
        self.FailRender( self.GetRegexMatch(0) )

    def HandleStdoutProgress(self):
        overallProgress = float( self.GetRegexMatch(1) )
        self.SetProgress( overallProgress )
        self.SetStatusMessage( "Progress: " + str( overallProgress ) + " %" )
