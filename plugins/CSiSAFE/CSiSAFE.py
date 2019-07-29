"""
"C:\\ProgramFiles\\SAFE\\SAFE.exe" /s "C:\\SAFEFiles\\tempScript.txt"
"""
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
    return CSiSAFEPlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class CSiSAFEPlugin(DeadlinePlugin):
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
                    self.LogInfo( "Copying tempIniFile=%s to directory location=%s" % (tempIniFile, iniFile) )
                    File.Copy( tempIniFile, iniFile, True )
                else:
                    self.LogInfo( "%s issues found with the INI File" % Counter )
                    self.LogInfo( "No necessary changes were made to the INI File=%s" % iniFile )

                File.Delete( tempIniFile )

            else:
                if createMissing:
                    # create the file from scratch if the application has never been started on a slave
                    writer = File.CreateText( iniFile )
                    writer.WriteLine( "[License]" )
                    writer.WriteLine( "; leave ProgramLevel blank or choose one of the following" )
                    writer.WriteLine( ";    ANY" )
                    writer.WriteLine( ";    STANDARD" )
                    writer.WriteLine( ";    PT" )
                    writer.WriteLine( ";    STANDARDC" )
                    writer.WriteLine( ";    PTC" )
                    writer.WriteLine( ";    STANDARDI" )
                    writer.WriteLine( ";    PTI" )
                    writer.WriteLine( ";    ENTERPRISE SEF" )
                    writer.WriteLine( ";    PROFESSIONAL SEF" )
                    writer.WriteLine( ";    ENTERPRISE EF" )
                    writer.WriteLine( ";    PROFESSIONAL EF" )
                    writer.WriteLine( " ProgramLevel=" )
                    writer.WriteLine( " ShowMessage=True" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[System]" )
                    writer.WriteLine( " PgmWidth=800" )
                    writer.WriteLine( " PgmHeight=600" )
                    writer.WriteLine( " PgmTop=0" )
                    writer.WriteLine( " PgmLeft=0" )
                    writer.WriteLine( " PgmWindowState=0" )
                    writer.WriteLine( " InputFilePath1=" )
                    writer.WriteLine( " InputFilePath2=" )
                    writer.WriteLine( " InputFilePath3=" )
                    writer.WriteLine( " InputFilePath4=" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[Misc]" )
                    writer.WriteLine( " ShowTips=False" )
                    writer.WriteLine( " Sound=True" )
                    writer.WriteLine( " Units=1" )
                    writer.WriteLine( " ShowWelcome=False" )
                    writer.WriteLine( " AutoModelSaveTime=0" )
                    writer.WriteLine( " Language=English" )
                    writer.WriteLine( "" )
                    writer.WriteLine( "[Printing]" )
                    writer.WriteLine( " NoEject=False" )
                    writer.WriteLine( " ColorPrinter=True" )
                    writer.WriteLine( " Default=True" )
                    writer.WriteLine( " Lines=56" )
                    writer.Close()

                    self.LogInfo( "CSi SAFE INI file created: %s" % iniFile )

    def InitializeProcess(self):
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        self.PopupHandling = True
        self.HandleWindows10Popups = True

        # Handle Pop-up dialogs due to data file being READ-ONLY
        #self.AddPopupHandler( "SAFE", "OK;No" )

        # Handle 'Design' Pop-up dialog
        # Design combinations do not exist for requested design and automatic default design combinations are turned off. Please add design combinations or turn default combinations ON.
        self.AddPopupIgnorer( "SAFE 12.*" )
        self.AddPopupIgnorer( "^SAFE$" )
        self.AddPopupIgnorer( "SAFE 12 EVALUATION VERSION - NOT FOR COMMERCIAL USE" )
        self.AddPopupIgnorer( "SAFE 2014 EVALUATION VERSION - NOT FOR COMMERCIAL USE" )
        self.AddPopupHandler( "^$", "[X]" )
        self.AddPopupHandler( "Tip of the Day", "[X]" )

        self.AddPopupIgnorer( "cSapBaseForm" )
        self.AddPopupIgnorer( "Analyzing.*" )
        self.AddPopupIgnorer( "Analyzing, Please Wait..." )
        self.AddPopupIgnorer( "AnalysisForm" )
        self.AddPopupIgnorer( "Analysis Complete.*" )
        
        self.AddPopupHandler( "SAFE 12$", "OK" )
        self.AddPopupHandler( "SAFE 2014$", "OK" )

        # Handle Software Updates - 'Installed CSI Software and Utilities' Pop-up dialog
        self.AddPopupHandler( "Software Updates", "Close" )

        # Handle License Expiration warning dialog
        self.AddPopupHandler( "License Expiration", "Cancel" )

    def RenderExecutable(self):
        version = self.GetPluginInfoEntryWithDefault( "Version", "" )
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        executable = ""
        executableList = self.GetConfigEntry( "SAFE_Executable" + str(version) )
        
        if(SystemUtils.IsRunningOnWindows()):
            if( build == "32bit" ):
                self.LogInfo( "Enforcing 32 bit build of CSi SAFE" )
                executable = FileUtils.SearchFileListFor32Bit( executableList )
                if( executable == "" ):
                    self.LogWarning( "32 bit CSi SAFE " + str(version) + " executable was not found in the semicolon separated list \"" + executableList + "\". Checking for any executable that exists instead." )
            
            elif( build == "64bit" ):
                self.LogInfo( "Enforcing 64 bit build of CSi SAFE" )
                executable = FileUtils.SearchFileListFor64Bit( executableList )
                if( executable == "" ):
                    self.LogWarning( "64 bit CSi SAFE " + str(version) + " executable was not found in the semicolon separated list \"" + executableList + "\". Checking for any executable that exists instead." )
            
        if( executable == "" ):
            self.LogInfo( "Not enforcing a build of CSi SAFE" )
            executable = FileUtils.SearchFileList( executableList )
            if executable == "":
                self.FailRender( "CSi SAFE " + str(version) + " executable was not found in the semicolon separated list \"" + executableList + "\". The path to the executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        # Modify the ini file(s) to eliminate some popups we cannot handle at startup
        if str(version) != "":
            if str(version) == "12":
                self.AppIniFile = Path.Combine( Path.GetDirectoryName( executable ), "SAFEv12.ini" )
                self.UserProfileDataPath = Path.Combine( PathUtils.GetLocalApplicationDataPath(), "Computers and Structures" )
                self.UserIniFile = Path.Combine( self.UserProfileDataPath, "SAFEv12.ini" )
            else:
                self.AppIniFile = Path.Combine( Path.GetDirectoryName( executable ), "SAFEv" + str(version) + ".ini" )
                self.UserProfileDataPath = Path.Combine( PathUtils.GetLocalApplicationDataPath(), "Computers and Structures\\SAFE " + str(version) )
                self.UserIniFile = Path.Combine( self.UserProfileDataPath, "SAFEv" + str(version) + ".ini" )

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

        ScriptCommands = []
        ScriptCommands.append( "FileOpen Filename=\"" + self.tempFile + "\"" ) #FileOpen Filename="C:\SAFEFiles\MyFile.FDB"

        self.SolverType = self.GetPluginInfoEntryWithDefault( "SolverMethod", "Standard Solver" )
        if self.SolverType == "Standard Solver":
            self.SolverMethod = "Standard"
        if self.SolverType == "Advanced Solver":
            self.SolverMethod = "Advanced"
        if self.SolverType == "Multithreaded Solver":
            self.SolverMethod = "Multithreaded"
        
        self.LogInfo( "  +Solver Type: %s" % self.SolverType )

        self.ProcessType = self.GetPluginInfoEntryWithDefault( "ProcessMethod", "GUI Process" )
        if self.ProcessType == "GUI Process":
            self.ProcessMethod = "GUI"
        elif self.ProcessType == "Separate Process":
            self.ProcessMethod = "Separate"
        
        self.LogInfo( "  +Process Type: %s" % self.ProcessType )

        self.Always32bit = self.GetPluginInfoEntryWithDefault( "Always32bit", "No" )
        if self.Always32bit == "Yes":
            self.Always32Bit = "Yes"
        else:
            self.Always32Bit = "No"
        
        self.LogInfo( "  +Always 32bit: %s" % self.Always32bit )

        self.RunMethod = self.GetPluginInfoEntryWithDefault( "RunMethod", "Disabled" )
        if self.RunMethod == "Run Analysis":
            self.RunType = "RunAnalysis SolverOpt=%s ProcessOpt=%s Always32Bit=%s" % ( self.SolverType, self.ProcessType, self.Always32bit )
        if self.RunMethod == "Run Analysis & Design":
            self.RunType = "RunDesign SolverOpt=%s ProcessOpt=%s Always32Bit=%s" % ( self.SolverType, self.ProcessType, self.Always32bit )
        if self.RunMethod == "Run Analysis, Design & Detailing":
            self.RunType = "RunDetailing SolverOpt=%s ProcessOpt=%s Always32Bit=%s" % ( self.SolverType, self.ProcessType, self.Always32bit )
        
        self.LogInfo( "  +Run Method: %s" % self.RunMethod )

        if self.RunMethod != "Disabled":
            ScriptCommands.append( self.RunType )

        self.CreateReport = self.GetBooleanPluginInfoEntryWithDefault( "CreateReport", False )
        if self.CreateReport:
            reportFileName = Path.GetFileNameWithoutExtension( self.tempFile) + ".rtf"
            reportFilePath = Path.Combine( Path.GetDirectoryName( self.tempFile ), reportFileName )
            reportFile = "FileCreateReport Filename=\"%s\" Open=No" % reportFilePath
            ScriptCommands.append( reportFile )
        
        self.LogInfo( "  +Create Report: %s" % self.CreateReport )

        self.FileExportOption = self.GetPluginInfoEntryWithDefault( "FileExportOption", "Disabled" )
        if self.FileExportOption == "Microsoft Access (.mdb)":
            self.FileExportExtension = ".mdb"
        if self.FileExportOption == "Microsoft Excel (.xls)":
            self.FileExportExtension = ".xls"
        if self.FileExportOption == "Text file (.txt)":
            self.FileExportExtension = ".txt"
        
        self.LogInfo( "  +File Export Option: %s" % self.FileExportOption )

        self.DBNamedSet = self.GetPluginInfoEntryWithDefault( "DBNamedSet", "" )
        self.DBGroupSet = self.GetPluginInfoEntryWithDefault( "DBGroupSet", "" )

        if self.FileExportOption != "Disabled":
            exportFileName = Path.GetFileNameWithoutExtension( self.tempFile ) + self.FileExportExtension
            exportFilePath = Path.Combine( Path.GetDirectoryName( self.tempFile ), exportFileName )

            if self.DBNamedSet == "":
                self.FailRender( "**FAILED - DB Named Set must not be empty when creating a File Export**" )

            self.LogInfo( "  +DB Named Set: %s" % self.DBNamedSet )

            exportFile = "FileExport Filename=\"%s\" NamedSet=%s" % ( exportFilePath, self.DBNamedSet )
            
            if self.DBGroupSet != "":
                exportFile = exportFile + " Group=%s" % self.DBGroupSet

            self.LogInfo( "  +DB Group Set: %s" % self.DBGroupSet )

            ScriptCommands.append( exportFile )

        self.DeletionType = self.GetPluginInfoEntryWithDefault( "DeletionOption", "keep everything" )
        if self.DeletionType == "delete analysis & output files":
            self.DeletionOption = "FileDelete"
        if self.DeletionType == "delete analysis files only":
            self.DeletionOption = "FileDelete Analysis=Yes Output=No"
        if self.DeletionType == "delete output files only":
            self.DeletionOption = "FileDelete Analysis=No Output=Yes"

        self.LogInfo( "  +Deletion Option: %s" % self.DeletionType )

        if self.DeletionType != "keep everything":
            ScriptCommands.append( self.DeletionOption )

        ScriptCommands.append( "FileExit" )

        # Create tempScript
        self.tempScript = Path.Combine( self.tempDir, "tempScript.txt" )

        if File.Exists( self.tempScript ):
            File.Delete( self.tempScript)

        writer = File.CreateText( self.tempScript )
        for command in ScriptCommands:
            writer.WriteLine( "%s\n" % command )
            self.LogInfo( "  >ScriptCommand: %s" % command )
        writer.Close()

        arguments = "/s"
        arguments += " \"" + self.tempScript + "\""

        return arguments
        
    def PreRenderTasks(self):
        self.LogInfo( "CSi SAFE job starting..." )
        
    def Zip(self, output_file, source_dir=None):
        zf = zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED)
        self.IncludeDataFile = self.GetBooleanPluginInfoEntryWithDefault( "IncludeDataFile", True )
        if source_dir:
            for dirname, subdirs, files in os.walk(source_dir):
                for name in files:

                    if name != "tempScript.txt" and self.IncludeDataFile:
                        zf.write(os.path.join(dirname, name), arcname=name)
                        self.LogInfo( "  +Adding To Zip File: %s" % name )

                    elif name != "tempScript.txt" and not name.upper().endswith((".FDB",".$2K",".F2K")):
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

                    if name != "tempScript.txt" and self.IncludeDataFile:
                        fileList.append(tempFile)
                        self.LogInfo( "  +File To Sync: %s" % name )

                    elif name != "tempScript.txt" and not name.upper().endswith((".FDB",".$2K",".F2K")):
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

        self.LogInfo( "CSi SAFE job finished." )