import os
import re

from System.IO import *
from System.Text import *

from Deadline.Scripting import *
from Deadline.Plugins import *

from FranticX.Processes import *

#######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
#######################################################################
def GetDeadlinePlugin():
    return CommandScriptPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

#######################################################################
## This is the main DeadlinePlugin class for the CommandScript plugin.
#######################################################################
class CommandScriptPlugin( DeadlinePlugin ):
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderTasksCallback += self.RenderTasks
        self.ShProcess = None
        
    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderTasksCallback

        if self.ShProcess:
            self.ShProcess.Cleanup()
            del self.ShProcess
    
    def InitializeProcess( self ):
        self.SingleFramesOnly = self.GetBooleanPluginInfoEntryWithDefault( "SingleFramesOnly", True )
        self.LogInfo( "Single Frames Only: %s" % self.SingleFramesOnly )
        
        self.PluginType = PluginType.Advanced
        self.StdoutHandling = True

        self.AddStdoutHandlerCallback( ".*Progress: (\d+)%.*" ).HandleCallback += self.HandleProgress

    def RenderTasks( self ):
        cmdFilePath = self.GetDataFilename()
        
        lines = File.ReadAllLines( cmdFilePath, Encoding.Default )
        if len( lines ) <= self.GetStartFrame():
            self.FailRender("Command file, " + cmdFilePath + ", did not have enough lines to get to frame " + str(self.GetStartFrame()))

        line = lines[self.GetStartFrame()].strip()

        # Replace curly quotation marks if present
        line = line.replace(u'\u201c', '"').replace(u'\u201d', '"')

        shellExecute = self.GetBooleanPluginInfoEntryWithDefault( "ShellExecute", False )
        self.LogInfo( "Execute in Shell: %s" % shellExecute )

        startupDir = self.GetPluginInfoEntryWithDefault( "StartupDirectory", "" )
        if startupDir != "":
            self.LogInfo( "Startup Directory: %s" % startupDir )

        if not shellExecute:
            self.LogInfo("Checking line: %s" % line)

            commandSplitRegex = re.compile('("[^"]*")(.*)')
            commandMatch = commandSplitRegex.match(line)
            
            arguments = ""
            if (commandMatch != None):
                executable = RepositoryUtils.CheckPathMapping(commandMatch.group(1).replace( "\"", "" ))
                arguments = RepositoryUtils.CheckPathMapping(commandMatch.group(2))
            else:
                spaceIndex = line.find( " " )
                if spaceIndex > 0 and spaceIndex < (len(line) - 1):
                    executable = RepositoryUtils.CheckPathMapping(line[:spaceIndex].replace( "\"", "" ))
                    arguments = RepositoryUtils.CheckPathMapping(line[spaceIndex+1:])
                else:
                    executable = RepositoryUtils.CheckPathMapping(line.replace( "\"", "" ))
            
            self.LogInfo( "Executable found: %s" % executable )
            self.LogInfo( "Arguments found: %s" % arguments )
            
            # Execute process when separate EXE and ARGS are provided in the commandsfile.txt
            self.LogInfo( "Invoking: Run Process" )
            exitCode = self.RunProcess( executable, arguments, startupDir, -1 )
        else:
            arguments = line
            
            if arguments == "":
                self.FailRender( "Command is missing!" )

            arguments = RepositoryUtils.CheckPathMapping( arguments, True )
            
            self.LogInfo( "Command: %s" % arguments )

            # Execute using Managed Process in Deadline, ensures child processes are terminated correctly
            self.LogInfo( "Invoking: Managed Shell Process" )
            self.ShProcess = ShellManagedProcess( self, arguments, startupDir )
            self.RunManagedProcess( self.ShProcess )
            exitCode = self.ShProcess.ExitCode

        self.LogInfo( "Command returned: %s" % exitCode )

        if exitCode != 0:
            self.FailRender( "Command returned non-zero exit code '{}'".format( exitCode ) )

    def HandleProgress( self ):
        progress = float( self.GetRegexMatch(1) )
        self.SetProgress( progress )

#################################################################################
## This is the shell managed process for running SHELL commands.
#################################################################################
class ShellManagedProcess( ManagedProcess ):
    '''
    This class provides a Deadline Managed Process using a pre-selected shell executable and provided command/arguments
    '''
    deadlinePlugin = None
    
    def __init__( self, deadlinePlugin, argument, directory ):
        self.deadlinePlugin = deadlinePlugin
        self.Argument = argument
        self.Directory = directory
        self.ExitCode = -1
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.StartupDirectoryCallback += self.StartupDirectory
        self.CheckExitCodeCallback += self.CheckExitCode

    def Cleanup( self ):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.StartupDirectoryCallback
        del self.CheckExitCodeCallback
    
    def InitializeProcess( self ):
        self.PopupHandling = True
        self.StdoutHandling = True
        self.HideDosWindow = True
        # Ensure child processes are killed and the parent process is terminated on exit
        self.UseProcessTree = True
        self.TerminateOnExit = True

        self.ShellString = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "Shell", "default" )
    
    def RenderExecutable( self ):
        shellExecutable = ""
        if self.ShellString == "default":
            # Grab the default shell executable from the User's environment.
            shellExecutable = os.environ.get( "SHELL", "/bin/sh" )
        else:
            # Search the list of potential paths for the shell executable.
            shellExeList = self.deadlinePlugin.GetConfigEntry( "ShellExecutable_" + self.ShellString )
            shellExecutable = FileUtils.SearchFileList( shellExeList )
        
        if( shellExecutable == "" ):
            self.deadlinePlugin.FailRender( self.ShellString + " shell executable was not found in the semicolon separated list \"" + shellExeList + "\". The path to the shell executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return shellExecutable

    def RenderArgument( self ):
        if self.ShellString == "cmd":
            return '/c "{}"'.format( self.Argument )
        else:
            escapedQuotes = self.Argument.replace( "'", "'\\''" )
            return "-c '{}'".format( escapedQuotes )
    
    def StartupDirectory( self ):
        return self.Directory

    def CheckExitCode( self, exitCode ):
        self.ExitCode = exitCode
