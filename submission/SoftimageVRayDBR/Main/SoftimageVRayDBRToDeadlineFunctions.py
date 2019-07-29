from __future__ import print_function
import win32com.client
import os
import subprocess
import datetime

from win32com.client import constants
from win32com.shell import shell, shellcon

##-------------------------------------------------------------------------------------
## SoftimageVRayDBRToDeadlineFunctions.py
## Thinkbox Software Inc, 2014
##
## This script contains all the additional functions used by both
## the SoftimageVRayDBRToDeadline.py and SoftimageVRayDBRToDeadlineLogic.py scripts.
##-------------------------------------------------------------------------------------

Application = win32com.client.Dispatch( 'XSI.Application' )
XSIUIToolkit = win32com.client.Dispatch( 'XSI.UIToolkit' )

##-------------------------------------------------------------------------------------
## HELPER FUNCTIONS
##-------------------------------------------------------------------------------------

def GetDeadlineLine(arguments, forceShowWindow = False):
    deadlineLine = "Error getting line"
    
    deadlineArray=GetDeadlineArray(arguments, forceShowWindow)
    
    if(len(deadlineArray)<2 or deadlineArray[1] != "Error"):
        if(len(deadlineArray)>0):
            deadlineLine = deadlineArray[0]
        else:
            deadlineLine=""
            
    return deadlineLine
        
#Reads in a list of items from the specified file and returns them in an array.
def GetArray(text):

    text=text.splitlines()
    
    size=0
    for line in text:
        if(line!=""):
            size+=1
            
    tempDeadlineArray = [0]*(size)
    index=0
    for line in text:
        if(line!=""):
            tempDeadlineArray[index] = line
            index+=1
    
    size*=2
    deadlineArray=[0]*(size)
    index=0
    for item in tempDeadlineArray:
        deadlineArray[index] = item
        deadlineArray[index+1] = item
        index+=2


    return deadlineArray

#Returns an array of available items returned from DeadlineCommand.exe using the
#specified argument.
def GetDeadlineArray(arguments, forceShowWindow = False):
    deadlineArray = [0]*2
    try:
        deadlineCommand = GetDeadlineCommand()
        arguments.insert(0, deadlineCommand)
        
        startupinfo = None
        creationflags = 0
        if os.name == 'nt':
            if forceShowWindow:
                # still show top-level windows, but don't show a console window
                CREATE_NO_WINDOW = 0x08000000   #MSDN process creation flag
                creationflags = CREATE_NO_WINDOW
            else:
                # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
                if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
                elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
        proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags)
        proc.stdin.close()
        proc.stderr.close()
        
        text = proc.stdout.read()
        
        if(text != "Bad submission arguments"):
            deadlineArray =  GetArray(text)
        else:
            deadlineArray[0]="Bad submission arguments"
            deadlineArray[1]="Error"
    except:
        Application.LogMessage("An Exception was generated attempting to run deadline command with args " + argument)
        deadlineArray[0]="Error getting array"
        deadlineArray[1]="Error"
        
    return deadlineArray

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
    
#Returns desired item if it exists in the array, otherwise it returns the first item.
def GetDefaultItem(deadlineArray,desiredItem):
    default = deadlineArray[0]
    
    for item in deadlineArray:
        if(item==desiredItem):
            default=desiredItem
            
    return default

##-------------------------------------------------------------------------------------
## PROPERTY FUNCTIONS
##-------------------------------------------------------------------------------------

#Gets the version from the application and parses it for major/minor.
def GetVersion():
    fullVersionString = Application.Version()
    firstPeriod = fullVersionString.find(".")
    secondPeriod = fullVersionString.find(".",firstPeriod+1)
    return fullVersionString[0:secondPeriod]

# Gets the major version from the application as a number instead of a string.
def GetIntVersion():
    fullVersionString = Application.Version()
    firstPeriod = fullVersionString.find(".")
    return int(fullVersionString[0:firstPeriod])

# Get 'year' version as Autodesk now name the product by year instead of by major version
def GetYearVersion():
    majorVer = GetIntVersion()
    now = datetime.datetime.now()
    yearVer = str(now.year)[:2]
    yearVer = yearVer + str(majorVer+2)
    return yearVer

def IsSaveRequired():
    # Check the project
    dirtyCount = Application.ExecuteCommand("GetValue",["Project.dirtycount"])
    if dirtyCount > 0:
        return True
    
    # Check root model - all sub-models will notify up
    dirtyCount = Application.ExecuteCommand("GetValue",[str(Application.ActiveSceneRoot) + ".dirty_count"])
    if dirtyCount > 0:
        return True
    
    return False

def GetOpSetValue( opSet, name, defaultValue ):
    if opSet.Parameters(name) != None:
        return opSet.Parameters(name).Value
    return defaultValue

def SetOpSetValue( opSet, name, value ):
    opSet.Parameters(name).Value = value

def SetOpSetEnabled( opSet, name, enabled ):
    opSet.Parameters(name).Enable(enabled)

def SetOpSetAttribute( opSet, name, attribute, value ):
    opSet.Parameters(name).SetAttribute(attribute, value)

def IsVRay( currPass ):
    renderer = ""
    renderer = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".Renderer"])
    if(renderer == ""):
        renderer = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.Renderer"])

    if(renderer.lower() == "vray"):
        result=True
    else:
        result=False
        
    return result

def CreateProgressBar( caption, maximum, cancelEnabled ):
    progressBar = XSIUIToolkit.ProgressBar
    progressBar.Maximum = maximum
    progressBar.Caption = caption
    progressBar.CancelEnabled = cancelEnabled
    progressBar.Visible = True
    return progressBar

##-------------------------------------------------------------------------------------
## SUBMISSION FILE CREATION FUNCTIONS
##-------------------------------------------------------------------------------------

#Creates the submission info file.
def CreateSubmissionInfoFile(opSet, submitInfoFilename):
    Application.LogMessage("Creating Submission Info")

    #Create the submit info file
    submitInfoFile = open(submitInfoFilename,"w")
    submitInfoFile.write("Plugin=VraySpawner")
    submitInfoFile.write("\nName=" + opSet.Parameters( "JobNameTextBox" ).Value)
    submitInfoFile.write("\nFrames=0-" + str(opSet.Parameters( "MaxServers" ).Value-1))
    submitInfoFile.write("\nChunkSize=1")
    submitInfoFile.write("\nComment=" + opSet.Parameters( "CommentTextBox" ).Value)
    submitInfoFile.write("\nDepartment=" + opSet.Parameters( "DepartmentTextBox" ).Value)
    submitInfoFile.write("\nPool=" + opSet.Parameters( "PoolComboBox" ).Value)
    submitInfoFile.write("\nSecondaryPool=" + opSet.Parameters( "SecondaryPoolComboBox" ).Value)
    submitInfoFile.write("\nGroup=" + opSet.Parameters( "GroupComboBox" ).Value)
    submitInfoFile.write("\nPriority=" + str(opSet.Parameters( "PriorityNumeric" ).Value))
    submitInfoFile.write("\nLimitGroups=" + opSet.Parameters( "LimitGroupsTextBox" ).Value)
    submitInfoFile.write("\nTaskTimeoutMinutes=" + str(opSet.Parameters( "TaskTimeoutNumeric" ).Value))
    submitInfoFile.write("\nOnTaskTimeout=Complete")
    
    if opSet.Parameters("IsBlacklist").Value:
        submitInfoFile.write("\nBlacklist=" + opSet.Parameters( "MachineListTextBox" ).Value)
    else:
        submitInfoFile.write("\nWhitelist=" + opSet.Parameters( "MachineListTextBox" ).Value)
    
    if opSet.Parameters("IsInterruptible").Value:
        submitInfoFile.write("\nInterruptible=True")

    submitInfoFile.close()

#Creates the plugin info file.
def CreatePluginInfoFile(opSet, jobInfoFilename):
    Application.LogMessage("Creating Plugin Info")
   
    #Create the job info file
    jobInfoFile = open(jobInfoFilename, "w")

    jobInfoFile.write("Version=Softimage" + str(GetYearVersion()))
    jobInfoFile.write("\nPortNumber=" + str(opSet.Parameters( "PortNumber" ).Value))
 
    jobInfoFile.close()

def SubmitDBRJob(opSet):
    Application.LogMessage("SubmitSoftimageVRayDBRToDeadline")
    
    temp = GetTempFolder()
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        submitInfoFilename = temp + "\\softimage_vraydbr_submit_info.job"
        jobInfoFilename = temp + "\\softimage_vraydbr_job_info.job"
    else:
        submitInfoFilename = temp + "/softimage_vraydbr_submit_info.job"
        jobInfoFilename = temp + "/softimage_vraydbr_job_info.job"

    #Set up the command line
    startupinfo = None
    if os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    deadlineCommand = GetDeadlineCommand()
    commandLine = "\"" + deadlineCommand + "\" \"" + submitInfoFilename + "\" \"" + jobInfoFilename + "\""

    progressBar = CreateProgressBar( "Job Submission", 2, False )
                    
    CreateSubmissionInfoFile(opSet,submitInfoFilename)
    CreatePluginInfoFile(opSet,jobInfoFilename)

    progressBar.Increment()

    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(commandLine, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    proc.stdin.close()
    proc.stderr.close()

    output = proc.stdout.read()

    progressBar.Increment()
    progressBar.Visible = False
        
    return output
    
def GetRepositoryPath(folder=None):
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
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    if folder == None:
        proc = subprocess.Popen([deadlineCommand, '-getrepositorypath'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    else:
        proc = subprocess.Popen([deadlineCommand, '-getrepositorypath', folder], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    proc.stdin.close()
    proc.stderr.close()
    
    path = proc.stdout.read()
    path = path.replace("\n","").replace("\r","")
    return path

# Get The Script Filename
def GetScriptFilename():
    return  GetRepositoryPath("submission/SoftimageVRayDBR/Main/") + "SoftimageVRayDBRToDeadline.py"

#need to get this to work
def GetTempFolder():
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        return os.getenv("Temp")
    else:
        return "/tmp"

#Gets the current frame.
def GetCurrentFrame():
    return (Application.ExecuteCommand("GetValue",["PlayControl.Current"]))

def MarkJobAsComplete():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
    if(opSet != None):
        jobId = GetOpSetValue( opSet, "StandaloneJobId", "" )
        if jobId != "":
            Application.LogMessage( "Marking job complete: " + jobId )
            GetDeadlineLine( ["CompleteJob", jobId] )

def ResetSpawnerControls():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
    if(opSet != None):
        SetOpSetValue( opSet, "StandaloneJobId", "" )
        
        SetOpSetEnabled( opSet, "MaxServers", True )
        SetOpSetEnabled( opSet, "PortNumber", True )
        SetOpSetEnabled( opSet, "StandaloneJobStatus", False )
        SetOpSetEnabled( opSet, "ActiveServers", False )
        
        oPPGLayout = opSet.PPGLayout
        oPPGLayout.Item("ActiveServers").UIItems = []
        oPPGLayout.Item("ReserveServers").SetAttribute( constants.siUIButtonDisable, False )
        oPPGLayout.Item("RenderCurrentPass").SetAttribute( constants.siUIButtonDisable, True )
        oPPGLayout.Item("RenderAllPasses").SetAttribute( constants.siUIButtonDisable, True )
        oPPGLayout.Item("ReleaseServers").SetAttribute( constants.siUIButtonDisable, True )
        
        # Set the state last, because there is an event defined in the Logic code that refreshes the UI when this value is changed.
        # This appears to be necessary in order to update the active server list.
        SetOpSetValue( opSet, "StandaloneJobStatus", "" )

def UpdateServers():
    updateTimer = Application.EventInfos( "SubmitSoftimageVRayDBRToDeadline_TIMER" )
    updateTimer.Mute = True
    
    oView = Application.Desktop.ActiveLayout.FindView( "DeadlineVRayDBRProperties" )
    if not oView:
        # The UI has been closed, so just mark the job as complete.
        MarkJobAsComplete()
        return
    
    try:
        opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
        if(opSet != None):
            jobId = GetOpSetValue( opSet, "StandaloneJobId", "" )
            if jobId != "":
                portNumber = GetOpSetValue( opSet, "PortNumber", False )
                useIpAddress = GetOpSetValue( opSet, "UseIpAddress", False )
                
                # Get the machines rendering the job.
                servers = GetDeadlineArray( ["GetMachinesRenderingJob", jobId, "true" if useIpAddress else "false"] )
                
                # Get the job state.
                jobState = ""
                jobInfo = GetDeadlineArray( ["GetJob", jobId, "false"] )
                for line in jobInfo:
                    if line.startswith( "Status=" ):
                        jobState = line[7:]
                        break
                
                if jobState == "Active":
                    jobState = "Rendering" if len(servers) > 0 else "Queued"
                elif jobState == "":
                    jobState = "Deleted"
                
                # Update the server list.
                opSet.PPGLayout.Item("ActiveServers").UIItems = servers
                
                # Set the state last, because there is an event defined in the Logic code that refreshes the UI when this value is changed.
                # This appears to be necessary in order to update the active server list.
                SetOpSetValue( opSet, "StandaloneJobStatus", jobState )
                
                # Update the vray config file.
                serverFileName = os.path.join( shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0), "dr_server_list.txt" )
                
                serverPortList = []
                for i in range(0, len(servers), 2):
                    serverPortList.append( servers[i] + ":" + str(portNumber) )
                
                try:
                    fileHandle = open( serverFileName, "w" )
                    fileHandle.write( "\n".join(serverPortList) + "\n" )
                    fileHandle.close()
                except:
                    print( traceback.format_exc() )
                
                # If the job state has changed, warn the user.
                if jobState != "Rendering" and jobState != "Queued":
                    message = "The spawner job is no longer active, it is now " + jobState + "."
                    XSIUIToolkit.MsgBox(message, constants.siMsgOkOnly | constants.siMsgExclamation, "Warning")
                    ResetSpawnerControls()
    
    finally:
        updateTimer.Mute = False