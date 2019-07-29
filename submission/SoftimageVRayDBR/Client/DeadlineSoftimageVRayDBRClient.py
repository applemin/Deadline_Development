import os.path
import os
import sys
import subprocess
import traceback

from win32com.client import constants
##-------------------------------------------------------------------------------------
## SubmitSoftimageVRayDBRToDeadline.py
## Thinkbox Software Inc, 2014
##
## This proxy script submits a VRay DBR job to reserve Deadline Slaves for VRay DBR for Softimage.
##-------------------------------------------------------------------------------------

##-------------------------------------------------------------------------------------
## CALL BACKS
##-------------------------------------------------------------------------------------
def XSILoadPlugin(in_reg):
    
    #Set up some basic information for the whole plug-in
    in_reg.Name = "Setup VRay DBR With Deadline Python Style"
    in_reg.Author = "Mike Owen (Thinkbox Software Inc)"
    in_reg.Email = "support@thinkboxsoftware.com"
    in_reg.URL = "http://www.thinkboxsoftware.com/deadline/"
    in_reg.Major = 1
    in_reg.Minor = 0
    
    # Register the SubmitToDeadline command
    in_reg.RegisterCommand("SubmitSoftimageVRayDBRToDeadline_PY", "SubmitSoftimageVRayDBRToDeadline")
    
    # Register the update timer, but mute it for now.
    in_reg.RegisterTimerEvent("SubmitSoftimageVRayDBRToDeadline_TIMER", 5000)
    updateTimer = Application.EventInfos( "SubmitSoftimageVRayDBRToDeadline_TIMER" )
    updateTimer.Mute = True
    
    # Register a Menu as another plug-in item to appear in the render menu
    in_reg.RegisterMenu(constants.siMenuTbRenderRenderID , "SSVDTDPYMenu", False, False)
    
    #set up the custom path
    path = GetRepositoryPath("submission/SoftimageVRayDBR/Main")
    if path != "":
        if path not in sys.path :
            sys.path.append( path)
            Application.LogMessage( "Appending \"" + path + "\" to system path to import SoftimageVRayDBRToDeadline module", 8 )
        else:
            Application.LogMessage( "\"%s\" is already in the system path" % path, 8 )
    else:
        Application.LogMessage( "The SoftimageVRayDBRToDeadline.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository.", 2 )
    
    # Finish with success notification
    return True

def SubmitSoftimageVRayDBRToDeadline_PY_Init(in_context):
    oCmd = in_context.Source
    oCmd.ReturnValue = False
    return True

def SubmitSoftimageVRayDBRToDeadline_PY_Execute(in_context):
    Main(in_context)

def SSVDTDPYMenu_Init(in_context):
    oMnu = in_context.Source
    menuitem = oMnu.AddCallbackItem( "Setup VRay DBR With Deadline", "Main" )
    return True


##-------------------------------------------------------------------------------------
## FUNCTIONS
##-------------------------------------------------------------------------------------

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

# Get The Repository Root using DeadlineCommand
def GetRepositoryPath(folder=None, filePath=False):
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
    
    func = '-getrepositorypath'
    if filePath:
        func = '-getrepositoryfilepath'
    
    if folder == None:
        proc = subprocess.Popen([deadlineCommand, func ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    else:
        proc = subprocess.Popen([deadlineCommand, func, folder], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    proc.stdin.close()
    proc.stderr.close()
    
    path = proc.stdout.read()
    path = path.replace("\n","").replace("\r","")
    return path

# Get The Script Filename
def GetScriptFilename():
    return GetRepositoryPath("submission/SoftimageVRayDBR/Main/SoftimageVRayDBRToDeadline.py", True)

##-------------------------------------------------------------------------------------
## MAIN FUNCTION
##-------------------------------------------------------------------------------------

def Main(in_context):
    try:
        import SoftimageVRayDBRToDeadline
        SoftimageVRayDBRToDeadline.Main()
    except:
        Application.LogMessage( traceback.format_exc() )
        Application.LogMessage( "The SoftimageVRayDBRToDeadline.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository.", 2 )

def SubmitSoftimageVRayDBRToDeadline_TIMER_OnEvent( in_context ):
    try:
        import SoftimageVRayDBRToDeadlineFunctions
        SoftimageVRayDBRToDeadlineFunctions.UpdateServers()
    except:
        Application.LogMessage( traceback.format_exc() )