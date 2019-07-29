r"""
:        %epin% or %1 contains the file with full path and no extensions for input files
:
:        %epout% or %2 contains the file with full path and no extensions for output files
:
:        %epinext% or %3 contains the extension of the file selected from the EP-Launch
:          program.  Could be imf or idf -- having this parameter ensures that the
:          correct user selected file will be used in the run.
:
:        %epwthr% or %4 contains the file with full path and extension for the weather file
:         
:        %eptype% or %5 contains either "EP" or "NONE" to indicate if a weather file is used
:
:        %pausing% or %6 contains Y if pause should occur between major portions of
:          batch file
:
:        %maxcol% or %7 contains "250" if limited to 250 columns otherwise contains
:                 "nolimit" if unlimited (used when calling readVarsESO)
:
:        %convESO% or %8 contains Y if convertESOMTR program should be called
:
:        %procCSV% or %9 contains Y if csvProc program should be called
:
:        %cntActv% or %10 contains the count of other simulations active or about to be active
:
:        %multithrd% or %11 contains N if multithreading should be disabled

"C:\EnergyPlusV8-1-0\Epl-run.bat" "c:\EP\Exercise1A" "c:\EP\Exercise1A" idf "c:\EP\wd\USA_VA_Sterling-Washington.Dulles.Intl.AP.724030_TMY3.epw" EP Y nolimit N N 0 Y
"""
from System import *
from System.Diagnostics import *
from System.IO import *

import os
import zipfile

from time import strftime as date

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return EnergyPlusPlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class EnergyPlusPlugin(DeadlinePlugin):

    EPexecutable = ""

    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.StartupDirectoryCallback += self.StartupDirectory
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks

    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.StartupDirectoryCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback

    def InitializeProcess(self):
        self.SingleFramesOnly = False
        self.StdoutHandling = True
        self.UseProcessTree = True

    def RenderExecutable(self):
        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()

        EPexecutableList = self.GetConfigEntry( "EnergyPlus_Executable" )
        
        if(SystemUtils.IsRunningOnWindows()):
            if( build == "32bit" ):
                self.LogInfo( "Enforcing 32 bit build of EnergyPlus" )
                self.EPexecutable = FileUtils.SearchFileListFor32Bit( EPexecutableList )
                if( self.EPexecutable == "" ):
                    self.LogWarning( "32 bit EnergyPlus EPexecutable was not found in the semicolon separated list \"" + EPexecutableList + "\". Checking for any executable that exists instead." )
            
            elif( build == "64bit" ):
                self.LogInfo( "Enforcing 64 bit build of EnergyPlus" )
                self.EPexecutable = FileUtils.SearchFileListFor64Bit( EPexecutableList )
                if( self.EPexecutable == "" ):
                    self.LogWarning( "64 bit EnergyPlus EPexecutable was not found in the semicolon separated list \"" + EPexecutableList + "\". Checking for any executable that exists instead." )
            
        if( self.EPexecutable == "" ):
            self.LogInfo( "Not enforcing a build of EnergyPlus" )
            self.EPexecutable = FileUtils.SearchFileList( EPexecutableList )
            if self.EPexecutable == "":
                self.FailRender( "EnergyPlus EPexecutable was not found in the semicolon separated list \"" + EPexecutableList + "\". The path to the EPexecutable can be configured from the Plugin Configuration in the Deadline Monitor." )

        self.EplRunBatFile = Path.Combine( Path.GetDirectoryName( self.EPexecutable), "Epl-run.bat" )

        return self.EplRunBatFile

    def RenderArgument(self):
        currFile = "DataFile" + str( self.GetStartFrame() )
        self.dataFile = self.GetPluginInfoEntryWithDefault( currFile, "" )

        if self.dataFile == "":
            self.FailRender( "**IDF File entry is missing from job Plugin Info Parameters for this TaskId!**" )
        
        auxFiles = self.GetAuxiliaryFilenames()

        # return location of idf data file
        if len(auxFiles) > 0:
            for index, auxFile in enumerate( auxFiles ):
                if auxFile == Path.GetFileName( self.dataFile ):
                    self.dataFile = Path.Combine( self.GetJobsDataDirectory(), auxFiles[index] )
        else:
            self.dataFile = RepositoryUtils.CheckPathMapping( self.dataFile )

        if SystemUtils.IsRunningOnWindows():
            self.dataFile = self.dataFile.replace( "/", "\\" )
            if self.dataFile.startswith( "\\" ) and not self.dataFile.startswith( "\\\\" ):
                self.dataFile = "\\" + self.dataFile
        else:
            self.dataFile = self.dataFile.replace( "\\", "/" )

        self.LogInfo( "  +Data File: %s" % self.dataFile )

        self.ThreadID = str( self.GetThreadNumber() )
        self.tempDir = Path.Combine( self.GetJobsDataDirectory(), self.ThreadID )
        
        try:
            Directory.CreateDirectory( self.tempDir )
            self.LogInfo( "  +Successfully created local temp directory: %s" % self.tempDir )
        except:
            self.LogWarning( "FAILED to create local temp directory for processing: %s" % self.tempDir )
            self.FailRender( "**FAILED to create local temp directory for processing**" )
        
        self.tempDataFile = Path.Combine( self.tempDir, Path.GetFileName(self.dataFile) )
        self.LogInfo( "  +Temp File: %s" % self.tempDataFile )

        # Copy idf data file to slave's jobsData [ThreadID] directory for faster I/O processing (if network path) or to support concurrent processing
        try:
            File.Copy( self.dataFile, self.tempDataFile, True )
            self.LogInfo( "  +Successfully copied Data File to: %s" % self.tempDir )
        except Exception as e:
            self.LogWarning( "FAILED to copy data file locally: %s" % e.Message )
            self.FailRender( "**FAILED to copy data file locally for better performance**" )

        inputDir = Path.Combine( Path.GetDirectoryName( self.tempDataFile ), Path.GetFileNameWithoutExtension( self.tempDataFile ) )
        outputDir = Path.Combine( Path.GetDirectoryName( self.tempDataFile ), Path.GetFileNameWithoutExtension( self.tempDataFile ) )

        arguments = " \"" + inputDir + "\"" + " \"" + outputDir + "\""
        self.FileExtension = Path.GetExtension( self.tempDataFile )
        self.FileExtension = self.FileExtension.replace( ".", "" ).lower()
        arguments += " " + self.FileExtension
        
        currWeatherFile = "WeatherFile" + str( self.GetStartFrame() )
        self.weatherFile = self.GetPluginInfoEntryWithDefault( currWeatherFile, "" )

        if self.weatherFile != "":

            # return location of weather file if applicable
            if len(auxFiles) > 0:
                for index, auxFile in enumerate( auxFiles ):
                    if auxFile == Path.GetFileName( self.weatherFile ):
                        self.weatherFile = Path.Combine( self.GetJobsDataDirectory(), auxFiles[index] )
            else:
                self.weatherFile = self.weatherFile
                self.weatherFile = RepositoryUtils.CheckPathMapping( self.weatherFile )

            if SystemUtils.IsRunningOnWindows():
                self.weatherFile = self.weatherFile.replace( "/", "\\" )
                if self.weatherFile.startswith( "\\" ) and not self.weatherFile.startswith( "\\\\" ):
                    self.weatherFile = "\\" + self.weatherFile
            else:
                self.weatherFile = self.weatherFile.replace( "\\", "/" )
            
            self.tempWeatherFile = Path.Combine( self.tempDir, Path.GetFileName(self.weatherFile) )
            self.LogInfo( "  +Weather EPW File: %s" % self.tempWeatherFile )

            if( not File.Exists(self.weatherFile) ):
                self.FailRender("**Weather File does not exist!**")

            # Copy weather file to slave's jobsData [ThreadID] directory for faster I/O processing (if network path) or to support concurrent processing
            if( not PathUtils.IsPathLocal( self.weatherFile) ):
                try:
                    tmplist = []
                    tmplist.append( self.weatherFile )

                    statFilename = Path.GetFileNameWithoutExtension( self.weatherFile) + ".stat"
                    statFile = Path.Combine( Path.GetDirectoryName( self.weatherFile ), statFilename )
                    if File.Exists(statFile):
                        tmplist.append( statFile )
                    else:
                        self.LogInfo("  -No *.stat file exists in the same directory as weather file. Skipping...")

                    ddyFilename = Path.GetFileNameWithoutExtension( self.weatherFile) + ".ddy"
                    ddyFile = Path.Combine( Path.GetDirectoryName( self.weatherFile ), ddyFilename )
                    if File.Exists(ddyFile):
                        tmplist.append( ddyFile )
                    else:
                        self.LogInfo("  -No *.ddy file exists in the same directory as weather file. Skipping...")                        
                    
                    DirectoryUtils.SynchronizeFiles( tmplist, self.tempDir )
                    self.LogInfo( "  +Successfully copied weather (EPW/STAT/DDY) files to: %s" % self.tempDir )

                except Exception as e:
                    self.LogWarning( "FAILED to copy weather files locally: %s" % e.Message )
                    self.FailRender( "**FAILED to copy weather files locally for better performance**" )

                arguments += " \"" + self.tempWeatherFile + "\"" + " EP"

            # if self.weatherFile submitted with job, then reference it in the arguments directly from jobsData directory
            else:
                self.tempWeatherFile = Path.Combine( self.GetJobsDataDirectory(), Path.GetFileName( self.weatherFile ) )
                arguments += " \"" + self.tempWeatherFile + "\"" + " EP"
        else:
            # if no weather files defined then process with no weather files directly referenced.
            arguments += " \"" + "\"" + " NONE"

        self.Debug = self.GetBooleanPluginInfoEntryWithDefault( "Debug", False )
        if self.Debug:
            arguments += " Y"
        else:
            arguments += " N"
        
        self.ReadVarsESOMaxColOption = self.GetPluginInfoEntryWithDefault( "ReadVarsESOMaxCol", "unlimited" )
        if self.ReadVarsESOMaxColOption == "unlimited":
            self.ReadVarsESOMaxCol = "nolimit"
        if self.ReadVarsESOMaxColOption == "less than 250":
            self.ReadVarsESOMaxCol = "250"

        arguments += " " + self.ReadVarsESOMaxCol

        self.ConvESO = self.GetBooleanPluginInfoEntryWithDefault( "ConvESO", False )
        if self.ConvESO:
            arguments += " Y"
        else:
            arguments += " N"

        self.CSVproc = self.GetBooleanPluginInfoEntryWithDefault( "CSVproc", False )
        if self.CSVproc:
            arguments += " Y"
        else:
            arguments += " N"

        self.CountActiveSims = "0"
        arguments += " " + self.CountActiveSims

        self.Multithreading = self.GetBooleanPluginInfoEntryWithDefault( "Multithreading", False )
        job = self.GetJob()
        if( job.JobConcurrentTasks > 1):
            arguments += " N"
        else:
            arguments += " Y"

        return arguments

    def StartupDirectory(self):
        self.ThreadID = str( self.GetThreadNumber() )
        self.tempDir = Path.Combine( self.GetJobsDataDirectory(), self.ThreadID )
        return self.tempDir

    def PreRenderTasks(self):
        self.LogInfo( "EnergyPlus job starting..." ) 

    def Zip(self, output_file, source_dir=None):
        zf = zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED)
        self.IncludeDataFile = self.GetBooleanPluginInfoEntryWithDefault( "IncludeDataFile", True )
        if source_dir:
            for dirname, subdirs, files in os.walk(source_dir):
                for name in files:

                    if self.IncludeDataFile:
                        zf.write(os.path.join(dirname, name), arcname=name)
                        self.LogInfo( "  +Adding To Zip File: %s" % name )

                    elif not name.lower().endswith((".idf", ".epw", ".ddy", ".stat")):
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
        except Exception as e:
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
            # Alternatively, just copy the files back to output directory
            self.LogInfo( "  +Synchronizing processed files back to output directory" )

            fileList = []
            self.IncludeDataFile = self.GetBooleanPluginInfoEntryWithDefault( "IncludeDataFile", True )

            for dirname, subdirs, files in os.walk(self.tempDir):
                for name in files:
                    tempFile = os.path.join(dirname, name)

                    if self.IncludeDataFile:
                        fileList.append(tempFile)
                        self.LogInfo( "  +File To Sync: %s" % name )

                    elif not name.lower().endswith((".idf", ".epw", ".ddy", ".stat")):
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

        self.LogInfo( "EnergyPlus job finished." )
