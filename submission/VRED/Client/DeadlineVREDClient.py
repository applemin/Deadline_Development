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

def GetRepositoryPath(subdir = None):
    deadlineCommand = GetDeadlineCommand()
    
    startupinfo = None
    if os.name == 'nt' and hasattr( subprocess, 'STARTF_USESHOWWINDOW' ): #not all python versions have this
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    args = [deadlineCommand, "-GetRepositoryPath "]   
    if subdir != None and subdir != "":
        args.append(subdir)

    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    proc.stdin.close()
    proc.stderr.close()
    
    path = proc.stdout.read()
    path = path.replace("\n","").replace("\r","")
    return path

def InstallDeadline( window = None ):
    try:
        # Get the repository path
        path = GetRepositoryPath("submission/VRED/Main")
        if path != "":
            path = path.replace( "\\", "/" )
            
            # Add the path to the system path
            if path not in sys.path :
                print( "Appending \"" + path + "\" to system path to import SubmitVREDToDeadline module" )
                sys.path.append( path )
            else:
                print( "\"%s\" is already in the system path" % path )
        
            # Import the script and call the main() function
            try:
                import SubmitVREDToDeadline
                SubmitVREDToDeadline.addDeadlineMenu( window )
            except:
                try:
                    import SubmitVREDToDeadline
                    SubmitVREDToDeadline.addDeadlinePythonQtMenu( window )
                except:
                    print( traceback.format_exc() )
                    print( "An error occured when attempting to add Deadline menu. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository." )
        else:
            print( "The SubmitVREDToDeadline.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository." )

    except Exception as e:
        print( "An error occured when attempting to add Deadline menu. " + str(e) )
