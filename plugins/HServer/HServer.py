from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *
import time

def GetDeadlinePlugin():
    return HServerPlugin()
    
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()
    
class HServerPlugin (DeadlinePlugin):
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderTasksCallback += self.RenderTasks
        
    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.RenderTasksCallback
    
    def InitializeProcess( self ):
        self.PluginType = PluginType.Advanced
        
    def RenderTasks( self ):
        while True:
            time.sleep( 5 )
            if self.IsCanceled():
                self.FailRender()