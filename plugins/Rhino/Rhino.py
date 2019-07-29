import clr
import os
import tempfile
import time
import subprocess

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return RhinoPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Rhino plugin.
######################################################################
class RhinoPlugin (DeadlinePlugin):
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
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple
        
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.StdoutHandling = True
        self.PopupHandling = True
        self.HandleQtPopups = True
        self.PopupMaxChildWindows = 25
        self.SetEnvironmentVariable( "QT_USE_NATIVE_WINDOWS","1" )
        
        self.AddPopupIgnorer( r"Preparing Plug-ins for First Use" )
        self.AddPopupIgnorer( r"V-Ray -- Render Progress" )
        self.AddPopupIgnorer( r"Render history settings" )
        self.AddPopupIgnorer( r"Python Debugger Window" )
        self.AddPopupIgnorer( r"V-Ray progress window" )
        self.AddPopupIgnorer( r"V-Ray option editor" )
        self.AddPopupIgnorer( r"V-Ray Frame Buffer" )
        
        self.AddPopupHandler( r"Bongo", "OK" )
        self.AddPopupHandler( r"Startup Template", "Cancel;Open;OK" )
        self.AddPopupHandler( r"Rhinoceros 4.0", "No;OK" )
        self.AddPopupHandler( r"Rhinoceros 5.0", "No;OK" )
        self.AddPopupHandler( r"Rhino Plug-in Error", "OK" )
        
        self.AddPopupHandler( r"ASGvis Product License", "I have a floating license server and would like to use that;Next" )
        self.AddPopupHandler( r"License server settings for: V-Ray for Rhinoceros", "OK" )
        self.AddPopupHandler( r"Flamingo Evaluation Version", "Close" )
        self.AddPopupHandler( r"V-Ray license", "OK" )
        self.AddPopupHandler( r"Message", "OK" )
        self.AddPopupHandler( r"File Is Read-only", "OK" )
        self.AddPopupHandler( r"Read-Only File", "Open Read-only" )
        self.AddPopupHandler( r"Rhino", "[X]" )
        self.AddPopupHandler( r"Done installing plug-ins, press close to continue", "Close" )
        
        self.HandleWindows10Popups = True
        
        self.AddPopupHandler( "Maxwell - MX.*", "Overwrite the existing file(s)." )
        self.AddPopupHandler( "Maxwell not licensed", "No" )
        self.AddPopupIgnorer( "Maxwell" )
    
    def PreRenderTasks( self ):
        outputDir = os.path.dirname( self.GetPluginInfoEntry( "OutputFile" ) )

        # Ensure the slave can write to the output directory to wasteful rendering.
        # We force outputDir to exist before submitting, so no need to check directory existence.
        try:
            with tempfile.NamedTemporaryFile( dir=outputDir, delete=True ):
                self.LogInfo( 'Slave can successfully write to output directory "%s"' % outputDir )
        except:
            self.FailRender( 'Failed to create file in the output directory "%s". Ensure the directory exists, check permissions, and try again.' % outputDir )

        sceneFilename = self.GetPluginInfoEntryWithDefault( "SceneFile", "" )
        if sceneFilename != "":
            sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename )
            if not File.Exists( sceneFilename ):
                self.FailRender( "The Rhino scene file cannot be found. It wasn't submitted with the job, so it needs to be in a location that is accessible to all Slaves. The scene file path is \"" + sceneFilename + "\"." )
    
    def PostRenderTasks( self ):
        rhinoSceneFilename = self.GetPluginInfoEntry( "OutputFile" )
        filenameWithoutExt, extension = os.path.splitext( rhinoSceneFilename )
        rhinoSceneBaseFilename = os.path.basename( filenameWithoutExt )

        maxwellID =  self.getMaxwellProcessID( rhinoSceneBaseFilename )
        if maxwellID is not None:
            while self.isMaxwellRunning( maxwellID ):
                time.sleep( self.GetIntegerConfigEntryWithDefault( "SleepTime", 5 ) )
                if self.IsCanceled():
                    self.FailRender()

    def RenderExecutable( self ):
        version = self.GetPluginInfoEntryWithDefault( "Version", "4" ).strip() #default to empty string (this should match pre-versioning config entries)
        
        rhinoExeList = self.GetConfigEntry( "Rhino_RenderExecutable%s" % version )
        rhinoExe = FileUtils.SearchFileList( rhinoExeList )
        if( rhinoExe == "" ):
            self.FailRender( "Rhino render executable was not found in the semicolon separated list \"" + rhinoExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return rhinoExe
    
    def RenderArgument( self ):
        sceneFilename = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() )
        sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename )
        
        outputFilename = self.GetPluginInfoEntry( "OutputFile" )
        outputFilename = RepositoryUtils.CheckPathMapping( outputFilename )

        view = self.GetPluginInfoEntryWithDefault( "View", "" )
        if "current -" in view.lower():
            view = ""
        
        # Rhino 5 doesn't seem to like forward slashes very much
        if ( SystemUtils.IsRunningOnWindows() ):
            sceneFilename = sceneFilename.replace( "/", "\\" )
            outputFilename = outputFilename.replace( "/", "\\" )
        
        renderer = self.GetPluginInfoEntryWithDefault( "Renderer", "Rhino Render" )
        renderBongo = self.GetBooleanPluginInfoEntryWithDefault( "RenderBongo", False )
        
        arguments = "/nosplash /runscript=\""
        arguments += "_SetCurrentRenderPlugin \"\"%s\"\" " % renderer
               
        if not self.IsTileJob():
            if renderer == "Maxwell for Rhino":
                outputFilename = outputFilename.replace( "\\", "\\\\" )

                extension = Path.GetExtension( outputFilename )
                scriptBuilder = StringBuilder()
                scriptBuilder.AppendLine( "import rhinoscriptsyntax as rs" )
                scriptBuilder.AppendLine( "import traceback" )
                scriptBuilder.AppendLine( "try:" )
                scriptBuilder.AppendLine( "    rs.Command( \"Maxwell_OutputSettings ImagePath \\\"%s\\\" Enter\" )" % outputFilename )
                scriptBuilder.AppendLine( "    rs.Command( \"Maxwell_OutputSettings ImageType %s Enter\" )" % extension ) # This changes the extension in ImagePath, but may not update the display value for ImageType
                scriptBuilder.AppendLine( "    rs.Command( \"Maxwell_OutputSettings CommandLine -nowait Enter\" )" )

                # We can't end up with 'rs.Command( "" )' as Rhino will fail to close then
                if self.SetViewToRender( view ) != "":
                    scriptBuilder.AppendLine( "    rs.Command( \"{}\" )".format( self.SetViewToRender( view ) ) )
                
                scriptBuilder.AppendLine( "    rs.Command( \"_Render\" )" )
                scriptBuilder.AppendLine( "except:" )
                scriptBuilder.AppendLine( "    print traceback.format_exc()" )
                scriptBuilder.AppendLine( "rs.Exit()" )

                globalScriptFilename = Path.GetTempFileName().replace( ".tmp", ".py" )

                File.WriteAllText( globalScriptFilename, scriptBuilder.ToString() )

                arguments += "-_RunPythonScript %s " % globalScriptFilename

            else:
                # If using vray, use this setup script to ensure that batch rendering is enabled.
                if renderer == "V-Ray for Rhino":
                    script = []
                    script.append( "Option Explicit" )
                    script.append( "Dim vfr_object" )
                    script.append( "On Error Resume Next" )
                    script.append( "Set vfr_object = Rhino.GetPluginObject(\"" + renderer + "\")" )
                    script.append( "If Err.Number = 0 Then" )
                    script.append( "    vfr_object.SetBatchRenderOn True" )
                    script.append( "End If" )
                    
                    scriptDirectory = self.CreateTempDirectory( "Setup" )
                    scriptFile = Path.Combine( scriptDirectory, "setup.rvb" )
                    File.WriteAllLines( scriptFile, tuple(script) )
                    
                    arguments += "-_LoadScript \"\"" + scriptFile + "\"\" "
                
                if renderBongo:
                    bongoVersion = self.GetIntegerPluginInfoEntryWithDefault( "BongoVersion", 2 )
                    
                    for frame in range( self.GetStartFrame(), self.GetEndFrame() + 1 ):
                        directory = Path.GetDirectoryName( outputFilename )
                        filePrefix = Path.GetFileNameWithoutExtension( outputFilename )
                        extension = Path.GetExtension( outputFilename )
                        frameOutputFilename = Path.Combine( directory, filePrefix + StringUtils.ToZeroPaddedString( frame, 4, False ) + extension )
                    
                        arguments += "Bongo "
                        if bongoVersion >= 2:
                            arguments += "BongoSetCurrentTick " + str(frame) + " "
                        else:
                            arguments += "BongoSetSliderPosition " + str(frame) + " "
                        
                        arguments += self.SetViewToRender( view )
                        arguments += "_Render "
                        arguments += "-_SaveRenderWindowAs \"\"" + frameOutputFilename + "\"\" "
                        arguments += "-_CloseRenderWindow "
                else:
                    arguments += self.SetViewToRender( view )
                    arguments += "_Render Enter "
                    arguments += "-_SaveRenderWindowAs \"\"" + outputFilename + "\"\" "
                    arguments += "-_CloseRenderWindow "
        else:
            #arguments += "-_ViewportProperties S # # enter"
            curTask = self.GetCurrentTaskId()
            startX = self.GetPluginInfoEntry( "RegionStart"+str(curTask)+"X" )
            startY = self.GetPluginInfoEntry( "RegionStart"+str(curTask)+"Y" )
            startZ = self.GetPluginInfoEntry( "RegionStart"+str(curTask)+"Z" )
            endX = self.GetPluginInfoEntry( "RegionEnd"+str(curTask)+"X" )
            endY = self.GetPluginInfoEntry( "RegionEnd"+str(curTask)+"Y" )
            endZ = self.GetPluginInfoEntry( "RegionEnd"+str(curTask)+"Z" )
            
            dimensionsX = self.GetPluginInfoEntry( "RenderDimensionX" )
            dimensionsY = self.GetPluginInfoEntry( "RenderDimensionY" )
            
            baseName = os.path.basename(outputFilename)
            dirName = os.path.dirname(outputFilename)
            regionOutputFileName = dirName+os.sep+"_region_"+str(curTask)+"_" + baseName
            
            arguments += "-_ViewportProperties S "+str(dimensionsX)+" "+str(dimensionsY)+" Enter "
            if renderer == "Maxwell for Rhino":
                extension = Path.GetExtension( regionOutputFileName )
                arguments += "Maxwell_OutputSettings ImagePath \"\"" + regionOutputFileName + "\"\" ImageType " + extension + " CommandLine \"\"-nowait\"\" Enter "
                arguments += "Maxwell_RenderRegion RenderScene "+startX+","+startY+","+startZ+" "+endX+","+endY+","+endZ+" "
            else:
                arguments += "-_RenderInWindow "+startX+","+startY+","+startZ+" "+endX+","+endY+","+endZ+" "
                arguments += "-_SaveRenderWindowAs \"\""+ regionOutputFileName + "\"\" "
                arguments += "-_CloseRenderWindow "
        
        if not renderer == "Maxwell for Rhino":
            arguments += "-_Exit "

            # It seems that Rhino 6 can run into a situation where it no longer uses a pop-up asking to save when exiting after render
            # So we add this no option to not save.
            if self.GetIntegerPluginInfoEntryWithDefault( "Version", 5 ) >= 6:
                arguments += "No "

        arguments += "\" \"" + sceneFilename + "\""
        
        return arguments

    def SetViewToRender( self, view ):
        arguments = ""
        if view != "":
            if self.IsStandardView( view ):
                arguments += "_-SetView _World _" + view + " "
            else:
                arguments += "_-NamedView _Restore " + view + " _Enter "

        return arguments

    def IsStandardView( self, view ):
        isStandardView = False
        standardView = ["Back", "Bottom", "Front", "Left", "Perspective", "Right", "Top"]

        if view in standardView:
            isStandardView = True

        return isStandardView

    def isMaxwellRunning( self, id ):
        isRunning = False

        try:
            Process.GetProcessById( id ) # Errors out if the process doesn't exist
            isRunning = True
        except:
            pass

        return isRunning

    def getMaxwellProcessID( self, rhinoSceneBaseFilename ):
        #WMIC is built into Windows. Its output is comma-separated HOST_NAME,COMMAND_LINE_ARGS,PROCESS_ID and can be parsed.
        #From there we find which command line has our scene name, and return its associated process id.
        #Its output looks like this:
        #
        #Node,CommandLine,ProcessId\r\n
        #MOBILE-030,maxwell -mxs:c:\path\to\MyScene1.mxs,12200\r\n
        #MOBILE-030,maxwell -mxs:c:\path\to\MyScene2.mxs,8464\r\n
        #
        #So, calling getMaxwellProcessID( "MyScene1" ) in the above example will return "12200"

        command = "wmic process where \"name='maxwell.exe'\" get ProcessID, CommandLine /format:CSV"
        
        # Hide the window
        startupinfo = None
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = subprocess.Popen( command, stdout=subprocess.PIPE, startupinfo=startupinfo )
        csvMaxwellProcessInfoOutput = proc.stdout.read()
        csvMaxwellProcessInfoArray = csvMaxwellProcessInfoOutput.replace( "\r", "" ).split( "\n" )
        for csvMaxwellProcessInfo in csvMaxwellProcessInfoArray:
            maxwellProcessInfo = csvMaxwellProcessInfo.split( "," )
            if len( maxwellProcessInfo ) == 3:
                if maxwellProcessInfo[1].find( rhinoSceneBaseFilename ) != -1:
                    return maxwellProcessInfo[2]
        return None