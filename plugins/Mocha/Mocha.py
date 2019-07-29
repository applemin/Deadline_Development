from __future__ import print_function
import re
import os
import datetime

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Plugins import *
from Deadline.Scripting import *

from FranticX.Processes import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return MochaPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Mocha plugin.
######################################################################

class MochaPlugin (DeadlinePlugin):

    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.renderExecutable
        self.RenderArgumentCallback += self.renderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks        

    def InitializeProcess( self ):
        self.StdoutHandling=True
        
        # Verbosity levels 0 and 1
        self.AddStdoutHandlerCallback("\[CRITICAL\]\s+\S+\s+\S+\s(.*)").HandleCallback += self.HandleExpectedStdoutError
        self.AddStdoutHandlerCallback("\[ERROR\]\s+\S+\s+\S+\s(.*)").HandleCallback += self.HandleExpectedStdoutError

        # Unexpected Mocha errors
        self.AddStdoutHandlerCallback("Unable to find any images in clip.*").HandleCallback += self.HandleUnexpectedStdoutError
        self.AddStdoutHandlerCallback("Failed to save image.*").HandleCallback += self.HandleUnexpectedStdoutError
    
    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
        
        if self.Process:
            self.Process.Cleanup()
            del self.Process    

    def HandleExpectedStdoutError( self ):
        self.FailRender( self.GetRegexMatch(1) )

    def HandleUnexpectedStdoutError( self ):
        self.FailRender( self.GetRegexMatch(0) )

    def renderExecutable( self ):
        mochaPythonExecutableList = self.GetConfigEntry( "Mocha_Python_Executable_" + self.GetPluginInfoEntryWithDefault( "Version", "5" ).strip() )
        mochaPythonExecutable = FileUtils.SearchFileList( mochaPythonExecutableList )
        if mochaPythonExecutable == "":
            self.FailRender( "Mocha Python executable was not found in the semicolon separated list \"" + mochaPythonExecutableList + "\". The path to the Python executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return mochaPythonExecutable
   
    def getViews( self ):
        formattedViewsList = ""

        viewsStr = self.GetPluginInfoEntryWithDefault( "Views", "" ).strip()
        if len( viewsStr ) == 0:
            return ""
        else:
            views = viewsStr.split(',')
            for view in views:
                formattedViewsList += " \"" + view.strip() + "\""

        return formattedViewsList

    def pathMapSceneFile( self, sceneFile ):
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        if SystemUtils.IsRunningOnWindows():
            sceneFile = sceneFile.replace( "/", "\\" )
            if sceneFile.startswith( "\\" ) and not sceneFile.startswith( "\\\\" ):
                sceneFile = "\\" + sceneFile
        else:
            sceneFile = sceneFile.replace( "\\", "/" )

        if self.GetBooleanConfigEntryWithDefault( "EnablePathMapping", "" ):
            tempSceneDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
            tempSceneFileName = Path.Combine( tempSceneDirectory, Path.GetFileName( sceneFile ) )
            tempSceneFileName = tempSceneFileName.replace( "\\", "/" )
                        
            RepositoryUtils.CheckPathMappingInFileAndReplaceSeparator( sceneFile, tempSceneFileName, "\\", "/" )
            sceneFile = tempSceneFileName

        return sceneFile

    def pathMapOutputDirectory( self, outputDirectory ):
        outputDirectory = RepositoryUtils.CheckPathMapping( outputDirectory )
        if SystemUtils.IsRunningOnWindows():
            outputDirectory = outputDirectory.replace( "/", "\\" )
            if outputDirectory.startswith( "\\" ) and not outputDirectory.startswith( "\\\\" ):
                outputDirectory = "\\" + outputDirectory
        else:
            outputDirectory = outputDirectory.replace( "\\", "/" )

        return outputDirectory

    def extractIndividualLayers( self, layersInfo ):
        layers = []

        for layer in layersInfo.split( "," ):
            layer = layer.strip()
            print("layers is", layer)
            if len( layer ) > 0:
                layers.append( layer )

        print(layers)
        return layers

    def extractLayerGroupInfo( self, line ):
        group = None
 
        colonIndex = line.find( ":" ) 
        if colonIndex != -1:
            # grouped layers
            group = line[ :colonIndex ].strip()
            line = line[ colonIndex+1: ].strip()

        layers = self.extractIndividualLayers( line )

        return group, layers

    def getLayerGroupInfo ( self ): 
        ungroupedLayers = []
        groupedLayers = {}
        
        userInput = self.GetPluginInfoEntryWithDefault( "LayerGroupInfo", "" )

        lines = re.split("\n|\r", userInput)
        for line in lines:
            line = line.strip()
            if ( len( line ) > 0 ):
                group, layers = self.extractLayerGroupInfo( line )
                if group == None:
                    ungroupedLayers.extend( layers )
                else:
                    if group not in groupedLayers:
                        groupedLayers[ group ] = layers
                    else:
                        if len( groupedLayers[ group ] ) == 0 or len( layers ) == 0: # empty group means that all its leyers need to be rendered
                            groupedLayers[ group ] = []
                        else:
                            groupedLayers[ group ].extend( layers )

        return ungroupedLayers, groupedLayers       

    def formLayerGroupString( self ):
        # When constructing a parameter string for mocharender.py, follow these rules:
        # - first, specify any ungrouped layers, separating them by a space
        # - then you can specify groups layers of which you want to render. Before the group name, add "-g" to the string
        # - if you want to render all layers within a group, the group name is enough 
        # - if you want to render only certain leyers within the group, specify their names after the group name, separating all by a space
        # - you can specify multiple groups - just remember to add "-g" to the string in front of any new group name

        formattedString = ""

        ungroupedLayers, groupedLayers = self.getLayerGroupInfo()

        if len( ungroupedLayers ) > 0:
            formattedString = " " + " ".join( "\"" + layer + "\"" for layer in ungroupedLayers )

        for group, layers in groupedLayers.items():
            formattedString += " -g " + "\"" + group + "\"" 
            if len( layers ) > 0:
                formattedString += " " + " ".join( "\"" + layer + "\"" for layer in layers ) 

        return formattedString

    def renderArgument( self ):
        renderArguments = "" 

        jobType = self.GetPluginInfoEntryWithDefault( "JobType", "Render" )   
        jobSubType = self.GetPluginInfoEntryWithDefault( "JobSubType", "remove" )   
        views = self.getViews()    

        mochaScriptExecutableList = self.GetConfigEntryWithDefault( "Mocha_" + jobType + "_Executable_" + self.GetPluginInfoEntryWithDefault( "Version", "5" ).strip(), "" )
        mochaScriptExecutable = FileUtils.SearchFileList( mochaScriptExecutableList )
        if mochaScriptExecutable == "":
            self.FailRender( "Mocha " + jobType + " executable was not found in the semicolon separated list \"" + mochaScriptExecutableList + "\". The path to the " + jobType + " executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        renderArguments += "\""+mochaScriptExecutable+"\""
  
        sceneFile = self.GetPluginInfoEntryWithDefault( "Scene", self.GetDataFilename() ) #todo test
        sceneFile = self.pathMapSceneFile( sceneFile ) 
        renderArguments += " -p \"" + sceneFile + "\""       

        outputDirectory = self.GetPluginInfoEntryWithDefault( "Output", "" )
        outputDirectory = self.pathMapOutputDirectory( outputDirectory )
        renderArguments += " -D \"" + outputDirectory + "\""  

        renderArguments += " -w " + str( self.GetIntegerPluginInfoEntryWithDefault( "FrameIndexWidth", 0 ) )

        offset = self.GetIntegerPluginInfoEntryWithDefault( "ProjFrameOffset", 0 )
        renderArguments += " -I " + str( self.GetStartFrame() - offset )
        renderArguments += " -O " + str( self.GetEndFrame() - offset )
       
        if jobType == "Render":
            self.LogInfo( "Handling a render job" )
            renderArguments += " -R " + jobSubType
            renderArguments += " -E " + self.GetPluginInfoEntryWithDefault( "FileExtension", "png" ) 
            renderArguments += " -P \"" + self.GetPluginInfoEntryWithDefault( "OutputPrefix", "" ) + "\"" 
            renderArguments += " -S \"" + self.GetPluginInfoEntryWithDefault( "OutputSuffix", "" ) + "\"" 
            renderArguments += self.formLayerGroupString() # accounts for groups and layers
            renderArguments += " -V " + str( self.GetIntegerPluginInfoEntryWithDefault( "ClipViewIndex", 0 ) )   
        
        elif jobType == "Export" and jobSubType != "rendered-shapes":
            self.LogInfo( "Handling an export job" ) 
            renderArguments += " -e " + jobSubType           
            renderArguments += " -n \"" + self.GetPluginInfoEntryWithDefault( "ExporterName", "" ) + "\""
            renderArguments += " -f \"" + os.path.join( outputDirectory, self.GetPluginInfoEntryWithDefault( "FileName", "" ) ) + "\""
            if views != "":
                renderArguments += " -V " + views
            renderArguments += " -C " + self.GetPluginInfoEntryWithDefault( "Colorize", "grayscale" ).lower()          
            if self.GetBooleanPluginInfoEntryWithDefault( "Invert", False ):
                renderArguments += " -i "
            if self.GetBooleanPluginInfoEntryWithDefault( "RemoveLensDistortion", False ):
                renderArguments += " -R "
            if self.GetBooleanPluginInfoEntryWithDefault( "Stabilize", False ):
                renderArguments += " -s "
        
        elif jobType == "Export" and jobSubType == "rendered-shapes":
            # "Rendered Shapes" is a hybrid between rendering and exporting
            renderArguments += " -E " + self.GetPluginInfoEntryWithDefault( "FileExtension", "png" )
            renderArguments += " -P \"" + self.GetPluginInfoEntryWithDefault( "OutputPrefix", "" ) + "\""
            renderArguments += " -S \"" + self.GetPluginInfoEntryWithDefault( "OutputSuffix", "" ) + "\""
            renderArguments += self.formLayerGroupString() # accounts for groups and layers
            if views != "":
                renderArguments += " -V " + views
            renderArguments += " -C " + self.GetPluginInfoEntryWithDefault( "Colorize", "grayscale" ).lower()          
            if self.GetBooleanPluginInfoEntryWithDefault( "Invert", False ):
                renderArguments += " -i "
            if self.GetBooleanPluginInfoEntryWithDefault( "RemoveLensDistortion", False ):
                renderArguments += " -R "
            if self.GetBooleanPluginInfoEntryWithDefault( "Stabilize", False ):
                renderArguments += " -s "

        renderArguments += " -" + self.GetConfigEntryWithDefault( "Verbosity", "v4" )

        return renderArguments

    def PreRenderTasks( self ):
        self.LogInfo( "Starting handling Mocha job..." ) 

    def PostRenderTasks( self ):
        self.LogInfo( "Handling job finished." )