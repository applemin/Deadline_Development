from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *
import time

def GetDeadlinePlugin():
    return UnrealSwarmPlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class UnrealSwarmPlugin (DeadlinePlugin):
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.PostRenderTasksCallback += self.PostRenderTasks
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
       
    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.PostRenderTasksCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess(self):
        self.SingleFramesOnly = True
        self.UseProcessTree = True
        
    def PostRenderTasks( self ):
        while True:
            time.sleep( self.GetIntegerConfigEntryWithDefault("SleepTime",5) )
            if self.IsCanceled():
                self.FailRender()
            if( ProcessUtils.IsProcessRunning( "SwarmAgent" ) ):
                if process == None:
                    break
            else:
                break
    
    def RenderExecutable(self):
        version = self.GetPluginInfoEntryWithDefault( "Version", "4" ).strip() #default to empty string (this should match pre-versioning config entries)
        
        swarmExeList = self.GetConfigEntryWithDefault( "SwarmExecutable%s" % version, "" )
        swarmExe = FileUtils.SearchFileList( swarmExeList )
        if( swarmExe == "" ):
            self.FailRender( "Unreal Swarm executable was not found in the semicolon separated list \"" + swarmExeList + "\". The path to the swarm executable can be configured from the Plugin Configuration in the Deadline Monitor." )
            
        return swarmExe
    
    def RenderArgument( self ):
        localDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
        localFilename = Path.Combine( localDirectory, "SwarmAgent.Options.xml" )
        
        allowedAgents = self.GetPluginInfoEntryWithDefault( "AllowedRemoteAgentNames", "RENDER*" )
        self.LogInfo("allowedAgents="+allowedAgents )
        allowedAgentGroup = self.GetPluginInfoEntryWithDefault( "AllowedRemoteAgentGroup", "DefaultDeployed" )
        agentGroupName = self.GetPluginInfoEntryWithDefault( "AgentGroupName", "Default" )
        remotingHost = self.GetPluginInfoEntryWithDefault( "CoordinatorRemotingHost", "RENDER-01" )
        with open(localFilename, 'w') as file:            
            file.write( "<?xml version=\"1.0\"?>" )
            file.write( "<SettableOptions xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">" )
           
           #I have no idea what the serializable colors are however if it is missing then CoordinatorRemotingHost is the only option that will actually take effect.
            file.write( "<SerialisableColours>\n" )
            file.write( "    <SerialisableColour LocalColour=\"-1\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-1\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-1\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-1\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-5658199\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-5658199\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-5658199\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-2894893\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-1\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-7667712\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-7667712\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-2987746\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-2987746\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16777077\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16777077\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16777077\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16777077\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16777077\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16777077\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-7278960\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16744448\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16711681\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-8388480\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16744448\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16777216\" />\n" )
            file.write( "    <SerialisableColour LocalColour=\"-16777216\" />\n" )
            file.write( "</SerialisableColours>\n" )
            
            file.write( "<AllowedRemoteAgentNames>"+ allowedAgents + "</AllowedRemoteAgentNames>\n" )
            file.write( "<AllowedRemoteAgentGroup>"+allowedAgentGroup+"</AllowedRemoteAgentGroup>\n" )
            file.write( "<AgentGroupName>" + agentGroupName + "</AgentGroupName>\n" )
            file.write( "<CoordinatorRemotingHost>"+remotingHost+"</CoordinatorRemotingHost>\n" )
            file.write( "<BringToFront>false</BringToFront>\n" )
            file.write( "<OptionsVersion>15</OptionsVersion>\n" )
            file.write( "</SettableOptions>" )
            
        argument = "-OptionsFolder=\""+localDirectory+"\""
        self.LogInfo(argument)
        return argument