from __future__ import print_function
import os
import sys
import subprocess
import traceback

from PySide.QtGui import *
from PySide.QtCore import *

def addDeadlineMenu():
    application = QApplication.instance()
    widgets = application.allWidgets()
    mochaMenuBar = filter(lambda wgt: isinstance(wgt, QMenuBar), widgets)[0]
    deadlineMenu = mochaMenuBar.addMenu( "Deadline" )
    submitAction = QAction( "Submit To Deadline      ", deadlineMenu )
    submitAction.triggered.connect( submitToDeadline )
    deadlineMenu.addAction( submitAction )

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
    
def getRepositoryPath(subdir = None):
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
    if subdir != None and subdir != "":
        args.append(subdir)

    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    proc.stdin.close()
    proc.stderr.close()
    
    path = proc.stdout.read()
    path = path.replace("\n","").replace("\r","")
    return path

def submitToDeadline():
    path = getRepositoryPath("submission/Mocha/Main")
    if path != "":
        path = path.replace( "\\", "/" )
        
        # Add the path to the system path
        if path not in sys.path :
            print( "Appending \"" + path + "\" to system path to import SubmitMochaToDeadline module" )
            sys.path.append( path )
        else:
            print( "\"%s\" is already in the system path" % path )

        # Import the script and call the main() function
        try:
            import SubmitMochaToDeadline
            SubmitMochaToDeadline.submitToDeadline( )
        except:
            print( traceback.format_exc() )
            print ( "The SubmitMochaToDeadline.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository." )
    else:
        print ( "The SubmitMochaToDeadline.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository." )

def main():
    addDeadlineMenu()