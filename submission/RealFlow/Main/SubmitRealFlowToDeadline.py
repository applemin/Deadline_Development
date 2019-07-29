import os
import sys
import re
import traceback
import subprocess

def GetDeadlineCommand():
    deadlineBin = ""
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        #if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass
        
    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if deadlineBin == "" and  os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f:
            deadlineBin = f.read().strip()

    deadlineCommand = os.path.join(deadlineBin, "deadlinecommand")
    
    return deadlineCommand

def CallDeadlineCommand( arguments ):
    deadlineCommand = GetDeadlineCommand()
    
    startupinfo = None
    #~ if os.name == 'nt':
        #~ startupinfo = subprocess.STARTUPINFO()
        #~ startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    arguments.insert( 0, deadlineCommand)
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    proc.stdin.close()
    proc.stderr.close()
    
    output = proc.stdout.read()
    
    return output

def SubmitToDeadline( scene ):
    scriptPath = CallDeadlineCommand( ["-GetRepositoryFilePath", "scripts/Submission/RealFlowSubmission.py"] ).replace('\r', '').replace('\n', '')
    if not os.path.isfile( scriptPath ):
        scene.message( "The RealFlowSubmission.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository." )
    else:
        # Get scene values
        scene.message( "Retrieving scene settings" )
        maxFrames = str( scene.getMaxFrames() )
        sceneFilename = str( scene.getFileName() )
        sceneRootPath = str( scene.getRootPath() )
        sceneCompletePath = sceneRootPath + "/" + sceneFilename
        
        version = "4"
        idocs = ""
        try:
            version = str( scene.getRealFlowVersion() )
            for idoc in scene.get_IDOCs():
                idocs = idocs + idoc.getName() + ","
            idocs = idocs.rstrip( "," )
        except:
            pass
        
        scene.message( "Version: %s" % version )
        
        # Save the scene before submitting
        scene.message( "Saving scene" )
        scene.save( sceneCompletePath )
        
        scene.message( "Script path: %s" % scriptPath )
        scene.message( "Scene path: %s" % sceneCompletePath )
        scene.message( "Frames: %s" % maxFrames )
        scene.message( "Version: %s" % version )
        scene.message( "IDocs: %s" % idocs )
        
        CallDeadlineCommand( ["-ExecuteScript", scriptPath, sceneCompletePath, maxFrames, version, idocs] )
