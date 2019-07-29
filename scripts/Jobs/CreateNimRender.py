import os
import sys
import traceback
import re

from Deadline.Scripting import *
from Deadline.Jobs import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

global scriptDialog
global nimPath

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global nimPath
    global scriptDialog
    
    try:
        nimPath = RepositoryUtils.GetEventPluginDirectory("NIM")

        #get a scriptDialog just so we can show any error messages
        scriptDialog = DeadlineScriptDialog()
        scriptDialog.SetIcon( os.path.join( nimPath, "NIM.ico" ) )
        
        selectedJobs = MonitorUtils.GetSelectedJobs()
        if len(selectedJobs) > 1:
            scriptDialog.ShowMessageBox( "Only one job can be selected at a time.", "Multiple Jobs Selected" )
            return
        
        nimUIScript = os.path.join( nimPath, "NIM_UI.py" )
        args = ( "-executescript", nimUIScript, "DeadlineMonitor" )
        output = ClientUtils.ExecuteCommandAndGetOutput( args )
        outputLines = output.splitlines()

        nimKVPs = {}
        for line in outputLines:
            tokens = line.strip().split( '=', 1 )

            if len( tokens ) > 1:
                key = tokens[0]
                value = tokens[1]

                nimKVPs[key] = value

        if len( nimKVPs ) > 0:
            #we have stuff, do things!
            job = selectedJobs[0]
            
            job.ExtraInfo0 = nimKVPs.get( "nim_renderName", "" )
            job.ExtraInfo1 = nimKVPs.get( "nim_jobName", "" )
            job.ExtraInfo2 = nimKVPs.get( "nim_showName", "" )
            job.ExtraInfo3 = nimKVPs.get( "nim_shotName", "" )
            job.ExtraInfo4 = nimKVPs.get( "nim_description", "" )
            job.ExtraInfo5 = nimKVPs.get( "nim_user", "" )

            for key, value in nimKVPs.iteritems():
                job.SetJobExtraInfoKeyValue( key.strip(), value.strip() )

            ClientUtils.LogText( "Saving updated Job...")
            RepositoryUtils.SaveJob( job )
            ClientUtils.LogText( "Successfully saved updated Job.")
            
            # If the job is already complete, then create a new render now.
            if job.Status == JobStatus.Completed:
                try:
                    if nimPath not in sys.path:
                        sys.path.append( nimPath )
                    
                    from NIM import NimEventListener
                    nimEvent = NimEventListener()
                    nimEvent.SetCalledFromCreateVersionScript()
                    
                    ClientUtils.LogText( "Processing completed job" )
                    nimEvent.ProcessNimJob( job )
                except:
                    scriptDialog.ShowMessageBox( "An error occurred while attempting to create a new Render in NIM:\n\n" + str(traceback.format_exc()), "Results - Error" )
        else:
            ClientUtils.LogText( "No Task/Asset selected, NIM Render will not be created." )        
    except:
        ClientUtils.LogText( "An unexpected error occurred:" )
        ClientUtils.LogText( traceback.format_exc() )
