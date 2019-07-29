import os
import sys
import subprocess
import traceback

import c4d
from c4d import gui

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

    deadlineCommand = os.path.join( deadlineBin, "deadlinecommand" )
    
    return deadlineCommand

def GetRepositoryPath( subdir=None ):
    deadlineCommand = GetDeadlineCommand()
    
    startupinfo = None
    if os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    args = [deadlineCommand, "-GetRepositoryPath "]
    if subdir:
        args.append( subdir )

    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    path, errors = proc.communicate()
    path = path.strip()
    
    return path

def main():
    # Get the repository path
    path = GetRepositoryPath( "submission/Cinema4D/Main" ).strip()
    if path.startswith( "Error:" ):
        print( path )
    elif path != "":
        path = path.replace( "\\", "/" )

        # Add the path to the system path
        if path not in sys.path:
            print( "Appending \"" + path + "\" to system path to import SubmitC4DToDeadline module" )
            sys.path.append( path )
        else:
            print( "\"%s\" is already in the system path" % path )
        
        # Import the script and call the main() function
        try:
            import SubmitC4DToDeadline
            SubmitC4DToDeadline.main( path )
        except:
            print( traceback.format_exc() )
            print( "The SubmitC4DToDeadline.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository." )
    else:
        print( "Could not find Repository root. Make sure the Deadline client applications are installed on this machine, and that the Monitor can connect to the Repository." )
        
if __name__=='__main__':
    main()
