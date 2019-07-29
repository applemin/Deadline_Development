from __future__ import print_function
import sys
import os
import subprocess
import traceback

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

def RunDeadlineCommand( arguments, hideWindow=True ):
    deadlineCommand = GetDeadlineCommand()
    
    startupinfo = None
    if hideWindow and os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    arguments.insert( 0, deadlineCommand)
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    proc.stdin.close()
    proc.stderr.close()
    
    result = proc.stdout.read()
    result = result.replace("\n","").replace("\r","")
    return result

# Get the root directory.
script = RunDeadlineCommand( ["-GetRepositoryFilePath","scripts/Submission/CompositeSubmission.py",] )
print("Running script \"" + script + "\"")
if os.path.isfile( script ):
    #Create an ini file in the users directory
    homeDir = RunDeadlineCommand( ["-GetCurrentUserHomeDirectory",] )
    iniFilePath = homeDir + "/temp/compositeapplicationsettings.ini"

    iniFile = open(iniFilePath,"w")
    args = sys.argv
    for i in range(0,len(args)):
        if(args[i] == "-d"):
            iniFile.write("Database=" + args[i+1] + "\n")
        elif(args[i] == "-u"):
            iniFile.write("Userfile=" + args[i+1] + "\n")
        elif(args[i] == "-c"):
            iniFile.write("Composition=" + args[i+1] + "\n")
        elif(args[i] == "-v"):
            iniFile.write("Version=" + args[i+1] + "\n")
        elif(args[i] == "-s"):
            iniFile.write("StartFrame=" + args[i+1] + "\n")
        elif(args[i] == "-e"):
            iniFile.write("EndFrame=" + args[i+1] + "\n")
        elif(args[i] == "-r"):
            iniFile.write("CompositeVersion=" + args[i+1] + "\n")
        elif(args[i] == "-b"):
            iniFile.write("Build=" + args[i+1] + "\n")
    iniFile.close()
    
    RunDeadlineCommand( ["-ExecuteScript", script], False )
else:
    raise RuntimeError( "The CompositeSubmission.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository." )
