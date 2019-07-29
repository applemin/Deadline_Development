from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

import os
import stat
import re
import zipfile

from time import strftime as date

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return CSiBridgePlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class CSiBridgePlugin(DeadlinePlugin):
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
    
    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback

    def UpdateIniFile(self, iniFile="", createMissing=False):
        if iniFile != "":
            if File.Exists( iniFile ):

                fileAtt = os.stat( iniFile )[0]
                if (not fileAtt & stat.S_IWRITE):
                    # File is read-only, so make it writeable
                    try:
                        os.chmod( iniFile, stat.S_IWRITE )
                    except:
                        self.LogWarning( "FAILED to make the INI File writeable. Check Permissions!" )
                        return

                # Define RegEx to locate & replace KVPs. We can't use the normal FileUtils.SetIniFileSetting method due to abnormal behaviour by the application with the INI file
                showTipsRe = Regex( r" ShowTips=True" )
                showWelcomeRe = Regex( r" ShowWelcome=True" )
                checkForUpdatesRe = Regex( r" CheckForUpdates=True" )
                showStartPageRe = Regex( r" ShowStartPage=True" )

                # Store temp file in local job folder (automatic deletion by the Deadline client)
                tempIniFileName = Path.GetFileName( iniFile )
                tempIniFile = Path.Combine( self.GetJobsDataDirectory(), tempIniFileName )

                if File.Exists( tempIniFile ):
                    File.Delete( tempIniFile )

                # Read in all lines into an array
                lines = File.ReadAllLines( iniFile )

                writer = File.CreateText( tempIniFile )
                
                Counter = 0

                # Loop through each line in the array, make changes if necessary, and write to temp file.
                for line in lines:
                    if len( line ) > 0:
                        # Check the line for each regex to see if there is a match. If so, perform a Regex.Replace
                        if showTipsRe.IsMatch( line ):
                            line = showTipsRe.Replace( line, " ShowTips=False", 1 )
                            self.LogInfo( "INI File Updated: %s" % line )
                            Counter += 1
                        if showWelcomeRe.IsMatch( line ):
                            line = showWelcomeRe.Replace( line, " ShowWelcome=False", 1 )
                            self.LogInfo( "INI File Updated: %s" % line )
                            Counter += 1
                        if checkForUpdatesRe.IsMatch( line ):
                            line = checkForUpdatesRe.Replace( line, " CheckForUpdates=False", 1 )
                            self.LogInfo( "INI File Updated: %s" % line )
                            Counter += 1
                        if showStartPageRe.IsMatch( line ):
                            line = showStartPageRe.Replace( line, " ShowStartPage=False", 1 )
                            self.LogInfo( "INI File Updated: %s" % line )
                            Counter += 1
                    writer.WriteLine( line )
                writer.Close()

                if Counter > 0:
                    # Now that the file has been processed, copy it over to the local user's directory
                    self.LogInfo( "Fixed a total of %s issues in the INI File" % Counter )
                    self.LogInfo( "Copying tempIniFile=%s to user directory location=%s" % (tempIniFile, iniFile) )
                    File.Copy( tempIniFile, iniFile, True )
                else:
                    self.LogInfo( "%s issues found with the INI File" % Counter )
                    self.LogInfo( "No necessary changes were made to the INI File=%s" % iniFile )

                File.Delete( tempIniFile )

            else:
                # create the file from scratch if the application has never been started on a slave
                if str(version) == "15":
                    self.LogWarning( "CSi Bridge 15 INI file NOT created, please startup CSi Bridge application at least once on this machine, under the same user account: %s" % iniFile )

                if str(version) == "2014":
                    writer = File.CreateText( iniFile )
                    writer.WriteLine( "[License]" )
                    writer.WriteLine( ";  Optional - choose one of the following for ProgramLevel" )
                    writer.WriteLine( ";           ANY" )
                    writer.WriteLine( ";           ADVANCEDRATING" )
                    writer.WriteLine( ";           ADVANCED" )
                    writer.WriteLine( ";           PLUSRATING" )
                    writer.WriteLine( ";           PLUS" )
                    writer.WriteLine( ";           ADVANCEDRATINGC" )
                    writer.WriteLine( ";           ADVANCEDC" )
                    writer.WriteLine( ";           PLUSRATINGC" )
                    writer.WriteLine( ";           PLUSC" )
                    writer.WriteLine( ";           ADVANCED" )
                    writer.WriteLine( ";           PLUSI" )
                    writer.WriteLine( ";           ENTERPRISESB" )
                    writer.WriteLine( ";           PROFESSIONALSB" )
                    writer.WriteLine( " ProgramLevel=" )
                    writer.WriteLine( " ShowMessage=True" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[System]" )
                    writer.WriteLine( " InputFilePath1=" )
                    writer.WriteLine( " InputFilePath2=" )
                    writer.WriteLine( " InputFilePath3=" )
                    writer.WriteLine( " InputFilePath4=" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[Misc]" )
                    writer.WriteLine( " Sound=True" )
                    writer.WriteLine( " Language=English" )
                    writer.WriteLine( " AutoModelSaveTime=0" )
                    writer.WriteLine( " SaveTextFile=False" )
                    writer.WriteLine( " GraphicsMode=GDIPlus" )
                    writer.WriteLine( " Units=1" )
                    writer.WriteLine( " ShowWelcome=False" )
                    writer.WriteLine( " CheckForUpdates=False" )
                    writer.WriteLine( " KnownIssuesDate=" )
                    writer.WriteLine( " RibbonColor=Blue" )
                    writer.WriteLine( " ScreenLineThickness=1" )
                    writer.WriteLine( " ScreenColors=0,0,0,0,65535,65535,65535,65280,65280,255,65535,255,128,255,16711680,65280,65535,16777215,16776960,128,65280,65280,65280,65280,16776960,16711680,255,65280,16776960,8421504,65280,8421504,255,16777215,12632256,0,0.5,0.5,0.5,0.5" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[PlugIn]" )
                    writer.WriteLine( " NumberPlugIns=0" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[QuickAccessToolBarButtons]" )
                    writer.WriteLine( " Save=True" )
                    writer.WriteLine( " PrintGraphics=False" )
                    writer.WriteLine( " Undo=True" )
                    writer.WriteLine( " Redo=True" )
                    writer.WriteLine( " ModelLock=True" )
                    writer.WriteLine( " RubberbandZoom=False" )
                    writer.WriteLine( " RestoreFullView=False" )
                    writer.WriteLine( " SetDefault3DView=False" )
                    writer.WriteLine( " Rotate3DView=False" )
                    writer.WriteLine( " RefreshWindow=False" )
                    writer.WriteLine( " SetDisplayOptions=False" )
                    writer.WriteLine( " SelectPointer=False" )
                    writer.WriteLine( " SelectAll=False" )
                    writer.WriteLine( " GetPreviousSelection=False" )
                    writer.WriteLine( " ClearSelection=False" )
                    writer.WriteLine( " ShowUndeformedShape=False" )
                    writer.WriteLine( " ShowBridgeSuperstructureForcesStresses=False" )
                    writer.WriteLine( " ShowTables=False" )
                    writer.WriteLine( " InteractiveDatabaseEditing=False" )
                    writer.WriteLine( " RunAnalysis=False" )
                    writer.Close()

                    self.LogInfo( "CSi Bridge 2014 INI file created: %s" % iniFile )

                if str(version) == "2015":
                    writer = File.CreateText( iniFile )
                    writer.WriteLine( "[License]" )
                    writer.WriteLine( ";  Optional - choose one of the following for ProgramLevel" )
                    writer.WriteLine( ";           ANY" )
                    writer.WriteLine( ";           ADVANCEDRATING" )
                    writer.WriteLine( ";           ADVANCED" )
                    writer.WriteLine( ";           PLUSRATING" )
                    writer.WriteLine( ";           PLUS" )
                    writer.WriteLine( ";           ADVANCEDRATINGC" )
                    writer.WriteLine( ";           ADVANCEDC" )
                    writer.WriteLine( ";           PLUSRATINGC" )
                    writer.WriteLine( ";           PLUSC" )
                    writer.WriteLine( ";           ADVANCEDI" )
                    writer.WriteLine( ";           PLUSI" )
                    writer.WriteLine( ";           ENTERPRISESB" )
                    writer.WriteLine( ";           PROFESSIONALSB" )
                    writer.WriteLine( " ProgramLevel=" )
                    writer.WriteLine( " ShowMessage=True" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[System]" )
                    writer.WriteLine( " InputFilePath1=" )
                    writer.WriteLine( " InputFilePath2=" )
                    writer.WriteLine( " InputFilePath3=" )
                    writer.WriteLine( " InputFilePath4=" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[Misc]" )
                    writer.WriteLine( " Sound=True" )
                    writer.WriteLine( " Language=English" )
                    writer.WriteLine( " AutoModelSaveTime=0" )
                    writer.WriteLine( " SaveTextFile=False" )
                    writer.WriteLine( " GraphicsMode=GDIPlus" )
                    writer.WriteLine( " Units=3" )
                    writer.WriteLine( " ShowWelcome=False" )
                    writer.WriteLine( " CheckForUpdates=False" )
                    writer.WriteLine( " KnownIssuesDate=" )
                    writer.WriteLine( " RibbonColor=Blue" )
                    writer.WriteLine( " ScreenLineThickness=2" )
                    writer.WriteLine( " ScreenColors=DefaultWhiteBkGrndColors" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[PlugIn]" )
                    writer.WriteLine( " NumberPlugIns=0" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[QuickAccessToolBarButtons]" )
                    writer.WriteLine( " Save=True" )
                    writer.WriteLine( " PrintGraphics=False" )
                    writer.WriteLine( " Undo=True" )
                    writer.WriteLine( " Redo=True" )
                    writer.WriteLine( " ModelLock=True" )
                    writer.WriteLine( " RubberbandZoom=False" )
                    writer.WriteLine( " RestoreFullView=False" )
                    writer.WriteLine( " SetDefault3DView=False" )
                    writer.WriteLine( " Rotate3DView=False" )
                    writer.WriteLine( " RefreshWindow=False" )
                    writer.WriteLine( " SetDisplayOptions=False" )
                    writer.WriteLine( " SelectPointer=False" )
                    writer.WriteLine( " SelectAll=False" )
                    writer.WriteLine( " GetPreviousSelection=False" )
                    writer.WriteLine( " ClearSelection=False" )
                    writer.WriteLine( " ShowUndeformedShape=False" )
                    writer.WriteLine( " ShowBridgeSuperstructureForcesStresses=False" )
                    writer.WriteLine( " ShowTables=False" )
                    writer.WriteLine( " InteractiveDatabaseEditing=False" )
                    writer.WriteLine( " RunAnalysis=False" )
                    writer.WriteLine( " ShowingMenuInCSiBridge=True" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[ToolStrips]" )
                    writer.WriteLine( "Version = Ver 15.1" )
                    writer.WriteLine( "Dock = 1, X = 0, Y = 14, Tools = miNewModel; miOpen; ; miSave; miPrintGraphics; ; miUndo; miRedo; ; miRefreshWindow; ; miLockModel; ; miRunAnalysis; miAutoRunAnalysis; ; miRubberBandZoom; miRestoreFullView; miPreviousZoom; miZoomInOneStep; miZoomOutOneStep; ; miPan; ; tiSetDefault3DView; tiSetXY_View; tiSetXZ_View; tiSetYZ_View; miShowNamedView; tiRotate3DView; tiPerspective; ; tiUp; tiDown; ; tiObjectShrinkToggle; miSetElements; ; miAssigntoGroup; ddb" )
                    writer.WriteLine( "Dock = 1, X = 764, Y = 14, Tools = miShowUndeformedShape; miShowDeformedShape; miShowElementForces/Stresses; miShowNamedDisplay; ; ddb" )
                    writer.WriteLine( "Dock = 1, X = 901, Y = 14, Tools = miSteelFrameDesign; ; miConcreteFrameDesign; ; ddb" )
                    writer.WriteLine( "Dock = -1, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = 1, X = 1088, Y = 42, Tools = miRating_Requests; miStart_Rating; ; ddb" )
                    writer.WriteLine( "Dock = 3, X = 14, Y = 0, Tools = miSelectObject; miReshapeObject; ; ddb" )
                    writer.WriteLine( "Dock = -1, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = 3, X = 14, Y = 260, Tools = miAll; miGetPreviousSelection; miClearSelection; miIntersectingLine; ddb" )
                    writer.WriteLine( "Dock = 3, X = 14, Y = 79, Tools = miPointsandGridIntersections; miEndsandMidpoints; miIntersections; miPerpendicularProjections; miLinesandEdges; miFineGrid; ddb" )
                    writer.WriteLine( "Dock = -1, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = -1, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = -1, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = -1, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = 0, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = 0, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = 0, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = 0, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = 0, X = 0, Y = 0, Tools = " )
                    writer.WriteLine( "Dock = 0, X = 0, Y = 0, Tools = " )
                    writer.Close()

                    self.LogInfo( "CSi Bridge 2015 INI file created: %s" % iniFile )

    def InitializeProcess(self):
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        self.PopupHandling = True
        self.HandleWindows10Popups = True

        # Handle Pop-up dialogs due to data file being READ-ONLY
        #self.AddPopupHandler( "Bridge", "OK;No" )

        # Handle 'Design' Pop-up dialog
        # Design combinations do not exist for requested design and automatic default design combinations are turned off. Please add design combinations or turn default combinations ON.
        self.AddPopupHandler( "CSiBridge 2014$", "OK" )

        self.AddPopupIgnorer( "CSiBridge.*" )
        self.AddPopupIgnorer( "cSapBaseForm" )
        self.AddPopupIgnorer( "Analyzing.*" )
        self.AddPopupIgnorer( "Analyzing, Please Wait..." )
        self.AddPopupIgnorer( "AnalysisForm" )
        self.AddPopupIgnorer( "Analysis Complete.*" )

        # Handle Software Updates - 'Installed CSI Software and Utilities' Pop-up dialog
        self.AddPopupHandler( "Software Updates", "Close" )

        # Handle License Expiration warning dialog
        self.AddPopupHandler( "License Expiration", "Cancel" )

    def RenderExecutable(self):
        version = self.GetPluginInfoEntryWithDefault( "Version", "" )
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()

        executable = ""
        executableList = self.GetConfigEntry( "Bridge_Executable" + str(version) )

        if(SystemUtils.IsRunningOnWindows()):
            if( build == "32bit" ):
                self.LogInfo( "Enforcing 32 bit build of CSi Bridge" )
                executable = FileUtils.SearchFileListFor32Bit( executableList )
                if( executable == "" ):
                    self.LogWarning( "32 bit CSi Bridge " + str(version) + " executable was not found in the semicolon separated list \"" + executableList + "\". Checking for any executable that exists instead." )

            elif( build == "64bit" ):
                self.LogInfo( "Enforcing 64 bit build of CSi Bridge" )
                executable = FileUtils.SearchFileListFor64Bit( executableList )
                if( executable == "" ):
                    self.LogWarning( "64 bit CSi Bridge " + str(version) + " executable was not found in the semicolon separated list \"" + executableList + "\". Checking for any executable that exists instead." )

        if( executable == "" ):
            self.LogInfo( "Not enforcing a build of CSi Bridge" )
            executable = FileUtils.SearchFileList( executableList )
            if executable == "":
                self.FailRender( "CSi Bridge " + str(version) + " executable was not found in the semicolon separated list \"" + executableList + "\". The path to the executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        # Modify the ini file(s) to eliminate some popups we cannot handle at startup
        if str(version) != "":
            self.AppIniFile = Path.Combine( Path.GetDirectoryName( executable ), "CSiBridge " + str(version) + ".ini" )
            self.UserProfileDataPath = Path.Combine( PathUtils.GetLocalApplicationDataPath(), "Computers and Structures\\CSiBridge " + str(version) )
            self.UserIniFile = Path.Combine( self.UserProfileDataPath, "CSiBridge " + str(version) + ".ini" )

            self.LogInfo( "Scanning App Programs INI File: %s" % self.AppIniFile )
            self.UpdateIniFile( self.AppIniFile, False )

            self.LogInfo( "Scanning Local Users INI File: %s" % self.UserIniFile )
            self.UpdateIniFile( self.UserIniFile, True )

        return executable

    def RenderArgument(self):
        self.dataFile = self.GetPluginInfoEntryWithDefault( "DataFile", self.GetDataFilename() )
        self.dataFile = RepositoryUtils.CheckPathMapping( self.dataFile )

        if self.dataFile == "":
            self.FailRender( "**Data File is missing from Job Plugin Info Parameters for this TaskId or is NOT present in the Aux Files Directory for the job!**" )

        if SystemUtils.IsRunningOnWindows():
            self.dataFile = self.dataFile.replace( "/", "\\" )
            if self.dataFile.startswith( "\\" ) and not self.dataFile.startswith( "\\\\" ):
                self.dataFile = "\\" + self.dataFile
        else:
            self.dataFile = self.dataFile.replace( "\\", "/" )

        self.LogInfo( "  +Data File: %s" % self.dataFile )

        fileAtt = os.stat( self.dataFile )[0]
        if (not fileAtt & stat.S_IWRITE):
            # File is read-only, so make it writeable
            try:
                self.LogInfo( "  +Data File is read-only. Attempting to make file writeable..." )
                os.chmod( self.dataFile, stat.S_IWRITE )
            except:
                self.LogWarning( "FAILED to make the Data File writeable. Check Permissions!" )

        self.ThreadID = str( self.GetThreadNumber() )
        self.tempDir = Path.Combine( self.GetJobsDataDirectory(), self.ThreadID )

        try:
            Directory.CreateDirectory( self.tempDir )
            self.LogInfo( "  +Successfully created temp directory: %s" % self.tempDir )
        except:
            self.LogWarning( "FAILED to create temp directory for processing: %s" % self.tempDir )
            self.FailRender( "**FAILED to create temp directory for processing**" )

        self.tempFile = Path.Combine( self.tempDir, Path.GetFileName(self.dataFile) )
        self.LogInfo( "  +Temp File: %s" % self.tempFile )

        # Copy data file to slave's jobData [ThreadID] directory for faster I/O processing (if network path) or to support concurrent processing
        try:
            File.Copy( self.dataFile, self.tempFile, True )
            self.LogInfo( "  +Successfully copied dataFile to: %s" % self.tempFile )
        except IOException as e:
            self.LogWarning( "FAILED to copy data file locally: %s" % e.Message )
            self.FailRender( "**FAILED to copy data file locally for better performance**" )

        arguments = " \"" + self.tempFile + "\""
        
        self.ProcessType = self.GetPluginInfoEntryWithDefault( "ProcessMethod", "GUI Process" )
        if self.ProcessType == "GUI Process":
            self.ProcessMethod = " P1"
        elif self.ProcessType == "Separate Process":
            self.ProcessMethod = " P2"

        self.LogInfo( "  +Process Type: %s" % self.ProcessType )

        self.SolverType = self.GetPluginInfoEntryWithDefault( "SolverMethod", "Standard Solver" )
        if self.SolverType == "Standard Solver":
            self.SolverMethod = " S1"
        if self.SolverType == "Advanced Solver":
            self.SolverMethod = " S2"

        self.LogInfo( "  +Solver Type: %s" % self.SolverType )
        
        arguments += " /R" + str(self.ProcessMethod) + str(self.SolverMethod)

        self.DesignSteelFrame = self.GetBooleanPluginInfoEntryWithDefault( "DesignSteelFrame", False )
        self.DesignConcreteFrame = self.GetBooleanPluginInfoEntryWithDefault( "DesignConcreteFrame", False )
        self.DesignAluminiumFrame = self.GetBooleanPluginInfoEntryWithDefault( "DesignAluminiumFrame", False )
        self.DesignColdFormedFrame = self.GetBooleanPluginInfoEntryWithDefault( "DesignColdFormedFrame", False )

        self.LogInfo( "  +Design Steel Frame: %s" % self.DesignSteelFrame )
        self.LogInfo( "  +Design Concrete Frame: %s" % self.DesignConcreteFrame )
        self.LogInfo( "  +Design Aluminium Frame: %s" % self.DesignAluminiumFrame )
        self.LogInfo( "  +Design Cold Formed Frame: %s" % self.DesignColdFormedFrame )

        if( self.DesignSteelFrame or self.DesignConcreteFrame or self.DesignAluminiumFrame or self.DesignColdFormedFrame ):
            arguments += " /D "
            if( self.DesignSteelFrame ):
                arguments += "S"
            if( self.DesignConcreteFrame ):
                arguments += "C"
            if( self.DesignAluminiumFrame ):
                arguments += "A"
            if( self.DesignColdFormedFrame ):
                arguments += "O"

        self.CommandLineArgs = self.GetPluginInfoEntryWithDefault( "CommandLineArgs", "" )
        if self.CommandLineArgs != "":
            arguments += self.CommandLineArgs
            self.LogInfo( "  +Command Line Args: %s" % self.CommandLineArgs )

        arguments += " /C"

        self.DeletionType = self.GetPluginInfoEntryWithDefault( "DeletionOption", "keep everything" )
        if self.DeletionType == "keep everything":
            self.DeletionOption = ""
        if self.DeletionType == "delete all files (not *.mdb)":
            self.DeletionOption = " /K AO"
        if self.DeletionType == "delete analysis files only":
            self.DeletionOption = " /K A"
        if self.DeletionType == "delete log/out files only":
            self.DeletionOption = " /K O"

        self.LogInfo( "  +Deletion Type: %s" % self.DeletionType )

        arguments += self.DeletionOption

        return arguments
        
    def PreRenderTasks(self):
        self.LogInfo( "CSi Bridge job starting..." )

    def Zip(self, output_file, source_dir=None):
        zf = zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED)
        self.IncludeDataFile = self.GetBooleanPluginInfoEntryWithDefault( "IncludeDataFile", True )
        if source_dir:
            for dirname, subdirs, files in os.walk(source_dir):
                for name in files:

                    if self.IncludeDataFile:
                        zf.write(os.path.join(dirname, name), arcname=name)
                        self.LogInfo( "  +Adding To Zip File: %s" % name )

                    elif not name.upper().endswith((".BDB",".MDB",".XLS",".$BR",".B2K")):
                        zf.write(os.path.join(dirname, name), arcname=name)
                        self.LogInfo( "  +Adding To Zip File: %s" % name )
        zf.close()

    def PostRenderTasks(self):
        self.OutputDir = self.GetPluginInfoEntryWithDefault( "OverrideOutputDirectory", "" )
        if self.OutputDir == "":
            self.OutputDir = Path.GetDirectoryName(self.dataFile)

        self.OutputDir = RepositoryUtils.CheckPathMapping( self.OutputDir )
        if SystemUtils.IsRunningOnWindows():
            self.OutputDir = self.OutputDir.replace( "/", "\\" )
            if self.OutputDir.startswith( "\\" ) and not self.OutputDir.startswith( "\\\\" ):
                self.OutputDir = "\\" + self.OutputDir
        else:
            self.OutputDir = self.OutputDir.replace( "\\", "/" )

        self.timeStamp = Path.GetFileName( self.dataFile ) + "_" + date( "%Y-%m-%d %H-%M-%S" )
        self.OutputDir = Path.Combine( self.OutputDir, self.timeStamp )

        self.LogInfo( "  +Output Directory: %s" % self.OutputDir )

        try:
            Directory.CreateDirectory(self.OutputDir)
            self.LogInfo( "  +Successfully created output directory: %s" % self.OutputDir )
        except IOException as e:
            self.LogWarning( "FAILED to create output directory: %s" % e.Message)
            self.FailRender( "**FAILED to create output directory**" )

        # If enabled, compress output and write back a zip file to output directory
        if self.GetBooleanPluginInfoEntryWithDefault( "CompressOutput", False ):
            zipFileName = self.timeStamp + ".zip"
            zipFilePath = Path.Combine( self.OutputDir, zipFileName )
            try:
                self.Zip(zipFilePath, self.tempDir)
                self.LogInfo( "  +Successfully created zip file: %s" % zipFilePath )
            except Exception as e:
                self.LogWarning( "FAILED to create zip file in output directory: %s" % e.Message )
                self.FailRender( "**FAILED to create zip file in output directory**" )
        else:
            # Alternatively, just copy the files back to output directory, skipping the original data file
            self.LogInfo( "  +Synchronizing processed files back to output directory" )

            fileList = []
            self.IncludeDataFile = self.GetBooleanPluginInfoEntryWithDefault( "IncludeDataFile", True )

            for dirname, subdirs, files in os.walk(self.tempDir):
                for name in files:
                    tempFile = os.path.join(dirname, name)

                    if self.IncludeDataFile:
                        fileList.append(tempFile)
                        self.LogInfo( "  +File To Sync: %s" % name )

                    elif not name.upper().endswith((".BDB",".MDB",".XLS",".$BR",".B2K")):
                        fileList.append(tempFile)
                        self.LogInfo( "  +File To Sync: %s" % name )

            result = DirectoryUtils.SynchronizeFiles( fileList, self.OutputDir )

            if result:
                self.LogInfo("  +Files successfully synchronized to: %s" % self.OutputDir)
            else:
                self.LogWarning("One or more files failed to synchronize back to output directory: %s" % self.OutputDir)

        try:
            Directory.Delete( self.tempDir, True )
        except Exception as e:
            self.LogWarning( "FAILED to delete temp directory: %s" % e.Message)
            pass

        self.LogInfo( "CSi Bridge job finished." )