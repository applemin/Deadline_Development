from __future__ import print_function
import os
import sys
import re
import traceback
import subprocess
import time

from threading import Thread, Timer

import xml.etree.cElementTree as ET

import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils

try:
    import ConfigParser
except:
    print( "Could not load ConfigParser module, sticky settings will not be loaded/saved" )

submitWindowName = "DeadlineVRayDBRSubmitWindow"
mainFormLayoutName = "DeadlineVRayDBRMainForm"
jobNameControl = "DeadlineVRayDBRJobName"
commentControl = "DeadlineVRayDBRComment"
departmentControl = "DeadlineVRayDBRDepartment"
poolControl = "DeadlineVRayDBRPool"
secondaryPoolControl = "DeadlineVRayDBRSecondaryPool"
groupControl = "DeadlineVRayDBRGroup"
priorityControl = "DeadlineVRayDBRPriority"
limitControl = "DeadlineVRayDBRLimit"
machineListControl = "DeadlineVRayDBRMachineList"
isBlacklistControl = "DeadlineVRayDBRIsBlacklist"
isInterruptibleControl = "DeadlineVRayDBRIsInterruptible"
maxServersControl = "DeadlineVRayDBRMaxServers"
portNumberControl = "DeadlineVrayDBRPortNumber"
useIpAddressControl = "DeadlineVRayDBRUseIpAddress"
activeServersLabel = "DeadlineVRayDBRActiveServersLabel"
activeServersControl = "DeadlineVRayDBRActiveServers"
spawnerJobIdControl = "DeadlineVRayDBRSpawnerJobId"
spawnerJobStatusControl = "DeadlineVRayDBRSpawnerJobStatus"
reserveServersButton = "DeadlineVRayDBRReserveServers"
startRenderButton = "DeadlineVRayDBRStartRender"
releaseServersButton = "DeadlineVRayDBRReleaseServers"
taskTimeoutControl = "DeadlineVRayDBRTaskTimeout"

revertDeadlineVRayDistributedEnabled = False

# The main submission function.
def Setup( scriptDirectory ):
    newShelfName = "Deadline"
    newButtonName = "DeadlineVRayDBRButton"
    shelfFileName = os.path.join(cmds.internalVar(userShelfDir=True), "shelf_" + newShelfName + ".mel")

    addNewShelf = True
    if os.path.isfile( shelfFileName ):
        addNewShelf = False
    else:
        # Check for existing shelves in optionVars.
        shelfCount = cmds.optionVar(q="numShelves")
        for i in range(1, shelfCount+1):
            varName = "shelfName" + str(i)
            shelfName = cmds.optionVar(q=varName)
            if newShelfName == shelfName:
                addNewShelf = False
                break
                
        if addNewShelf:
            # This is hacky it works for now
            mel.eval("addNewShelfTab "+newShelfName+";")

    addButton = True
    buttonArray = cmds.shelfLayout(newShelfName, q=True, childArray=True)
    # buttonArray seems to be a bool when running Maya in batch mode - this just avoids a warning message
    # buttonArray seems to be "None" when the "Deadline" menu is present, but has no items.
    if buttonArray != None and not type(buttonArray) is bool:
        for button in buttonArray:
            buttonAnnotation = cmds.shelfButton(button, q=True, annotation=True)
            if buttonAnnotation == "Setup VRay DBR With Deadline":
                imagePath = os.path.join(scriptDirectory, "SubmitVRay.png")
                cmds.shelfButton(button, edit=True, image1=imagePath)
                addButton = False
                break
    
    if addButton:
        #imagePath = "commandButton.xpm"
        imagePath = os.path.join(scriptDirectory, "SubmitVRay.png")
        cmds.shelfButton(newButtonName, parent=newShelfName, annotation="Setup VRay DBR With Deadline", image1=imagePath, command="import SubmitMayaVRayDBRToDeadline\nSubmitMayaVRayDBRToDeadline.SubmitToDeadline()")

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
        
def CallDeadlineCommand( arguments, hideWindow=True ):
    environment = None
    
    deadlineCommand = GetDeadlineCommand()
            
    if os.name == 'nt':
        # Need to set the PATH, cuz windows 8 seems to load DLLs from the PATH earlier that cwd....
        environment = {}
        for key in os.environ.keys():
            environment[key] = str(os.environ[key])
        environment['PATH'] = str(os.path.dirname( deadlineCommand ) + ";" + os.environ['PATH'])
    
    startupinfo = None
    creationflags = 0
    if os.name == 'nt':
        if hideWindow:
            # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
            if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            # still show top-level windows, but don't show a console window
            CREATE_NO_WINDOW = 0x08000000   #MSDN process creation flag
            creationflags = CREATE_NO_WINDOW
    
    arguments.insert( 0, deadlineCommand)
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, env=environment, creationflags=creationflags)
    proc.stdin.close()
    proc.stderr.close()
    
    output = proc.stdout.read()
    
    return output
    
def OpenRenderGlobals(*args):
    mel.eval( "unifiedRenderGlobalsWindow" )
    
def GetMachineListFromDeadline(*args):
    output = CallDeadlineCommand( ["-selectmachinelist", cmds.textFieldButtonGrp( machineListControl, q=True, text=True)], False )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        cmds.textFieldButtonGrp( machineListControl, e=True, text=output )

def GetLimitGroupsFromDeadline(*args):
    output = CallDeadlineCommand( ["-selectlimitgroups", cmds.textFieldButtonGrp( limitControl, q=True, text=True)], False )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        cmds.textFieldButtonGrp( limitControl, e=True, text=output )

def AddStringAttribute( attrName ):
    attrExists = cmds.attributeQuery( attrName, node='defaultRenderGlobals', exists=True )
    if not attrExists:
        mel.eval( 'addAttr -shortName "' + attrName + '" -longName "' + attrName + '" -dt "string" defaultRenderGlobals;' )

def AddLongAttribute( attrName ):
    attrExists = cmds.attributeQuery( attrName, node='defaultRenderGlobals', exists=True )
    if not attrExists:
        mel.eval( 'addAttr -shortName "' + attrName + '" -longName "' + attrName + '" -at long defaultRenderGlobals;' )


def SavePersistentDeadlineOptions(*args):
    AddStringAttribute( "deadlineVrayDBRJobName" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRJobName", cmds.textFieldButtonGrp( jobNameControl, q=True, text=True ), type="string" )
    
    AddStringAttribute( "deadlineVrayDBRJobComment" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRJobComment", cmds.textFieldGrp( commentControl, q=True, text=True ), type="string" )
    
    AddStringAttribute( "deadlineVrayDBRDepartment" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRDepartment", cmds.textFieldGrp( departmentControl, q=True, text=True ), type="string" )
    
    AddStringAttribute( "deadlineVrayDBRPool" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRPool", cmds.optionMenuGrp( poolControl, q=True, v=True ), type="string" )
    
    AddStringAttribute( "deadlineVrayDBRSecondaryPool" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRSecondaryPool", cmds.optionMenuGrp( secondaryPoolControl, q=True, v=True ), type="string" )
    
    AddStringAttribute( "deadlineVrayDBRGroup" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRGroup", cmds.optionMenuGrp( groupControl, q=True, v=True ), type="string" )
    
    AddLongAttribute( "deadlineVrayDBRJobPriority" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRJobPriority", cmds.intSliderGrp( priorityControl, q=True, v=True ) )

    AddStringAttribute( "deadlineVrayDBRLimitGroups" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRLimitGroups", cmds.textFieldButtonGrp( limitControl, q=True, text=True ), type="string" )
    
    AddStringAttribute( "deadlineVrayDBRMachineList" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRMachineList", cmds.textFieldButtonGrp( machineListControl, q=True, text=True ), type="string" )

    AddLongAttribute( "deadlineVrayDBRIsBlacklist" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRIsBlacklist", cmds.checkBox( isBlacklistControl, q=True, v=True ) )
    
    AddLongAttribute( "deadlineVrayDBRIsInterruptible" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRIsInterruptible", cmds.checkBox( isInterruptibleControl, q=True, v=True ) )
    
    AddLongAttribute( "deadlineVrayDBRMaxServers" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRMaxServers", cmds.intSliderGrp( maxServersControl, q=True, v=True ) )
    
    AddLongAttribute( "deadlineVrayDBRPortNumber" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRPortNumber", cmds.intSliderGrp( portNumberControl, q=True, v=True ) )
    
    AddLongAttribute( "deadlineVrayDBRUseIpAddress" )
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRUseIpAddress", cmds.checkBox( useIpAddressControl, q=True, v=True ) )

def SetJobName(*args):
    jobName = ""
    
    sceneName = cmds.file( q=True, sceneName=True )
    if sceneName != "":
        jobName = os.path.splitext( os.path.basename( sceneName ) )[0] + "  -  "
    
    version = cmds.about( version=True )
    version = int(float(version.split()[0]))
        
    jobName = jobName + "VRay Spawner Job (Maya " + str(version) + ")"
    
    cmds.textFieldButtonGrp( jobNameControl, e=True, text=jobName )
    
    SavePersistentDeadlineOptions()

def SetJobIdAttribute( jobId ):
    AddStringAttribute("deadlineVrayDBRJobId")
    cmds.setAttr( "defaultRenderGlobals.deadlineVrayDBRJobId", jobId, type="string" )

def GetJobIdAttribute():
    if mel.eval("attributeExists deadlineVrayDBRJobId defaultRenderGlobals"):
        return cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRJobId" ) 
    return ""

def SubmitToDeadline():
    # Load initial settings from attributes if they exist.
    jobName = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRJobName" ) if mel.eval("attributeExists deadlineVrayDBRJobName defaultRenderGlobals") else ""
    comment = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRJobComment" ) if mel.eval("attributeExists deadlineVrayDBRJobComment defaultRenderGlobals") else ""
    department = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRDepartment" ) if mel.eval("attributeExists deadlineVrayDBRDepartment defaultRenderGlobals") else ""
    pool = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRPool" ) if mel.eval("attributeExists deadlineVrayDBRPool defaultRenderGlobals") else "none"
    secondaryPool = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRSecondaryPool" ) if mel.eval("attributeExists deadlineVrayDBRSecondaryPool defaultRenderGlobals") else ""
    group = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRGroup" ) if mel.eval("attributeExists deadlineVrayDBRGroup defaultRenderGlobals") else "none"
    priority = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRJobPriority" ) if mel.eval("attributeExists deadlineVrayDBRJobPriority defaultRenderGlobals") else 50
    limits = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRLimitGroups" ) if mel.eval("attributeExists deadlineVrayDBRLimitGroups defaultRenderGlobals") else ""
    machineList = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRMachineList" ) if mel.eval("attributeExists deadlineVrayDBRMachineList defaultRenderGlobals") else ""
    isBlacklist = (cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRIsBlacklist" )==1) if mel.eval("attributeExists deadlineVrayDBRIsBlacklist defaultRenderGlobals") else False
    isInterruptible = (cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRIsInterruptible" )==1) if mel.eval("attributeExists deadlineVrayDBRIsInterruptible defaultRenderGlobals") else False
    maxServers = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRMaxServers" ) if mel.eval("attributeExists deadlineVrayDBRMaxServers defaultRenderGlobals") else 10
    portNumber = cmds.getAttr("defaultRenderGlobals.deadlineVrayDBRPortNumber") if mel.eval("attributeExists deadlineVrayDBRPortNumber defaultRenderGlobals") else 20207
    useIpAddress = (cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRUseIpAddress" )==1) if mel.eval("attributeExists deadlineVrayDBRUseIpAddress defaultRenderGlobals") else False
    taskTimeout = cmds.getAttr( "defaultRenderGlobals.deadlineVrayDBRTaskTimeout" ) if mel.eval("attributeExists deadlineVrayDBRTaskTimeout defaultRenderGlobals") else 0
    
    # Get the maximum priority.
    try:
        maximumPriority = int(CallDeadlineCommand( ["-getmaximumpriority",] ))
    except:
        maximumPriority = 100
    
    # Get the pools.
    pools = CallDeadlineCommand( ["-pools",] ).splitlines()
    
    secondaryPools = []
    secondaryPools.append("")
    for currPool in pools:
        secondaryPools.append(currPool)
    
    # Get the groups.
    groups = CallDeadlineCommand( ["-groups",] ).splitlines()
  
    # Create a new submission dialog window (delete the old one if it already exists).
    if cmds.window( submitWindowName, exists=True ):
        cmds.deleteUI( submitWindowName, window=True )
    cmds.window( submitWindowName )
    
    # Reset the preferences if necessary.
    if cmds.windowPref( submitWindowName, exists=True ):
        cmds.windowPref( submitWindowName, remove=True )
        
    windowWidth = 460
    windowHeight = 500
    
    labelWidth = 110
    controlWidth = 320
    selectionControlWidth = 300
    selectionButtonWidth = 20
    buttonWidth = 95
    
    # Create the main submit window.
    cmds.window( submitWindowName, e=True, resizeToFitChildren=True, sizeable=True, title="Setup VRay DBR With Deadline", widthHeight=[windowWidth+8,windowHeight] )
    cmds.formLayout( mainFormLayoutName, width=(windowWidth+16), nd=100 )
    
    # MAIN COLUMN LAYOUT
    mainColumnLayout = cmds.columnLayout( adj=True, columnAttach=["both", 4] )
    
    # JOB DESCRIPTION
    cmds.frameLayout( label="Job Description", labelVisible=True, borderVisible=False, collapsable=True )
    cmds.columnLayout( adj=True, columnAttach=["both", 4], rowSpacing=4 )
    
    cmds.textFieldButtonGrp( jobNameControl, label="Job Name", buttonLabel="<", cl3=["left", "left", "left"], cw3=[labelWidth, selectionControlWidth, selectionButtonWidth], text=jobName, changeCommand=SavePersistentDeadlineOptions, buttonCommand=SetJobName, annotation="The name of the job (press '<' button to use the scene file name)" )
    cmds.textFieldGrp( commentControl, label="Comment", cl2=["left", "left"], cw2=[labelWidth, controlWidth], text=comment, changeCommand=SavePersistentDeadlineOptions, annotation="A brief comment about the job" )
    cmds.textFieldGrp( departmentControl, label="Department", cl2=["left", "left"], cw2=[labelWidth, controlWidth], text=comment, changeCommand=SavePersistentDeadlineOptions, annotation="The department the job (or the job's user) belongs to" )
    
    cmds.setParent( ".." ) # columnLayout
    cmds.setParent( ".." ) # frameLayout
    
    # JOB SCHEDULING
    cmds.frameLayout( label="Job Scheduling", labelVisible=True, borderVisible=False, collapsable=True )
    cmds.columnLayout( adj=True, columnAttach=["both", 4], rowSpacing=4 )
    
    cmds.optionMenuGrp( poolControl, label="Pool", cl2=["left", "left"], cw2=[labelWidth, 160], changeCommand=SavePersistentDeadlineOptions, annotation="The pool the job belongs to" )
    poolCount = 0
    for p in pools:
        cmds.menuItem( label=p )
        if p == pool:
            cmds.optionMenuGrp( poolControl, e=True, select=(poolCount+1) )
        poolCount = poolCount + 1
    
    cmds.optionMenuGrp( secondaryPoolControl, label="Secondary Pool", cl2=["left", "left"], cw2=[labelWidth, 160], changeCommand=SavePersistentDeadlineOptions, annotation="The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves" )
    poolCount = 0
    for p in secondaryPools:
        cmds.menuItem( label=p )
        if p == secondaryPool:
            cmds.optionMenuGrp( secondaryPoolControl, e=True, select=(poolCount+1) )
        poolCount = poolCount + 1
        
    cmds.optionMenuGrp( groupControl, label="Group", cl2=["left", "left"], cw2=[labelWidth, 160], changeCommand=SavePersistentDeadlineOptions, annotation="The group the job belongs to" )
    groupCount = 0
    for g in groups:
        cmds.menuItem( label=g )
        if g == group:
            cmds.optionMenuGrp( groupControl, e=True, select=(groupCount+1) )
        groupCount = groupCount + 1
        
    cmds.intSliderGrp( priorityControl, label="Priority", cal=[1, "left"], cw=[1, labelWidth], field=True, minValue=0, maxValue=maximumPriority, v=priority, changeCommand=SavePersistentDeadlineOptions, annotation="The job's priority (0 is the lowest, 100 is the highest)" )
    cmds.textFieldButtonGrp( limitControl, label="Limits", buttonLabel="...", cl3=["left", "left", "left"], cw3=[labelWidth, selectionControlWidth, selectionButtonWidth], text=limits, changeCommand=SavePersistentDeadlineOptions, buttonCommand=GetLimitGroupsFromDeadline, annotation="The limits that this job requires." )
    cmds.textFieldButtonGrp( machineListControl, label="Machine List", buttonLabel="...", cl3=["left", "left", "left"], cw3=[labelWidth, selectionControlWidth, selectionButtonWidth], text=machineList, changeCommand=SavePersistentDeadlineOptions, buttonCommand=GetMachineListFromDeadline, annotation="The whitelist or blacklist for the job" )
    
    cmds.intSliderGrp( taskTimeoutControl, label="Task Timeout", cal=[1, "left"], cw=[1, labelWidth], field=True, minValue=0, maxValue=10000, v=taskTimeout, changeCommand=SavePersistentDeadlineOptions, annotation="The tasks Timeout" )
        
    cmds.rowLayout( numberOfColumns=2, cw2=[labelWidth, 158], ct2=["left", "left"] )
    cmds.text( label="", align="left" )
    cmds.checkBox( isBlacklistControl, label="Machine List Is A Blacklist", v=isBlacklist, changeCommand=SavePersistentDeadlineOptions, annotation="If checked, the machine list will be a blacklist. Otherwise, it is a whitelist" )
    cmds.setParent( ".." ) # rowLayout
    
    cmds.rowLayout( numberOfColumns=2, cw2=[labelWidth, 158], ct2=["left", "left"] )
    cmds.text( label="", align="left" )
    cmds.checkBox( isInterruptibleControl, label="Job Is Interruptible", v=isInterruptible, changeCommand=SavePersistentDeadlineOptions, annotation="If enabled, this job can be interrupted by a higher priority job during rendering. Note that if a slave moves to a higher priority job, it will not be able to join this render again." )
    cmds.setParent( ".." ) # rowLayout
    
    cmds.setParent( ".." ) # columnLayout
    cmds.setParent( ".." ) # frameLayout
    
    # VRAY SPAWNER
    cmds.frameLayout( label="VRay Spawner Options", labelVisible=True, borderVisible=False, collapsable=True )
    cmds.columnLayout( adj=True, columnAttach=["both", 4], rowSpacing=4 )
    
    cmds.intSliderGrp( maxServersControl, label="Maximum Servers", cal=[1, "left"], cw=[1, labelWidth], field=True, minValue=1, maxValue=100, v=maxServers, changeCommand=SavePersistentDeadlineOptions, annotation="The maximum number of VRay Servers to reserve for distributed rendering" )
    cmds.intSliderGrp( portNumberControl, label="Port Number", cal=[1, "left"], cw=[1, labelWidth], field=True, minValue=1024, maxValue=65535,  v=portNumber, changeCommand=SavePersistentDeadlineOptions, annotation="The port number that VRay will use for distributed rendering. " )
    
    cmds.rowLayout( numberOfColumns=2, cw2=[labelWidth, 158], ct2=["left", "left"] )
    cmds.text( label="", align="left" )
    cmds.checkBox( useIpAddressControl, label="Use Server IP Address Instead of Host Name", v=useIpAddress, changeCommand=SavePersistentDeadlineOptions, annotation="If checked, the Active Servers list will show the server IP addresses instead of host names" )
    cmds.setParent( ".." ) # rowLayout
    
    cmds.textFieldGrp( spawnerJobIdControl, label="Spawner Job ID", enable=False, cl2=["left", "left"], cw2=[labelWidth, controlWidth], editable=False, text="", annotation="The spawner job's ID" )
    cmds.textFieldGrp( spawnerJobStatusControl, label="Spawner Job Status", enable=False, cl2=["left", "left"], cw2=[labelWidth, controlWidth], editable=False, text="", annotation="The spawner job's status" )
    
    cmds.rowLayout( numberOfColumns=2, cw2=[labelWidth, controlWidth], ct2=["left", "left"] )
    cmds.text( activeServersLabel, label="Active Servers", enable=False, align="left", annotation="The current active servers" )
    cmds.scrollField( activeServersControl, editable=False, height=100, width=controlWidth, enable=False, text="" )
    cmds.setParent( ".." ) # rowLayout
    
    cmds.setParent( ".." ) # columnLayout
    cmds.setParent( ".." ) # frameLayout
    
    # END MAIN COLUMN LAYOUT
    cmds.setParent( ".." ) # mainColumnLayout
    
    # BUTTONS
    buttonColumnLayout = cmds.columnLayout( adj=True, columnAttach=["both", 4], rowSpacing=4 )
    cmds.rowLayout( numberOfColumns=4, cw4=[105, 105, 105, 105] )
    
    cmds.button( label="Render Globals", width=buttonWidth, height=26, c=OpenRenderGlobals, annotation="Opens the Maya Render Globals Dialog" )
    cmds.button( reserveServersButton, label="Reserve Servers", width=buttonWidth, height=26, c=SubmitJob, annotation="Submits the VRay Spawner job to reserve servers" )
    cmds.button( startRenderButton, label="Start Render", width=buttonWidth, height=26, enable=False, c=StartRender, annotation="Starts the distributed render" )
    cmds.button( releaseServersButton, label="Release Servers", width=buttonWidth, height=26, enable=False, c=CompleteJob, annotation="Deletes the VRAy Spawner job to release the servers" )
    
    cmds.setParent( ".." ) # rowLayout
    cmds.setParent( ".." ) # columnLayout
    
    # SETUP LAYOUT
    cmds.formLayout( mainFormLayoutName, e=True, af=[buttonColumnLayout, "bottom", 5] )
    cmds.formLayout( mainFormLayoutName, e=True, af=[buttonColumnLayout, "left", 5] )
    cmds.formLayout( mainFormLayoutName, e=True, ac=[mainColumnLayout, "bottom", 5, buttonColumnLayout] )
    cmds.formLayout( mainFormLayoutName, e=True, af=[mainColumnLayout, "top", 5] )
    cmds.formLayout( mainFormLayoutName, e=True, af=[mainColumnLayout, "left", 5] )
    
    # Set the job name if it hasn't been set yet.
    if cmds.textFieldButtonGrp( jobNameControl, q=True, text=True ) == "":
        SetJobName()
        
    # Set up a script job to delete the spawner job when the UI is closed (if a job is running)
    cmds.scriptJob( uiDeleted=[submitWindowName, CompleteJobThread] )
    cmds.scriptJob( event=["quitApplication", CompleteJobThread] )
    
    # Show the window
    cmds.showWindow( submitWindowName )
    
    
def SubmitJob(*args):
    global revertDeadlineVRayDistributedEnabled
    currRenderer = mel.eval("currentRenderer").lower()
    if currRenderer != "vray":
        msg = "VRay is not the current renderer. Please make it the current renderer before reserving servers."
        cmds.confirmDialog( parent=submitWindowName, title="Error", message=msg, button="Close", icon="critical" )
        return
        
    if cmds.getAttr( "vraySettings.sys_distributed_rendering_on" ) == 0:
        msg = "VRay distributed rendering must be enabled before reserving servers. Would you like to enable it now?"
        if cmds.confirmDialog( parent=submitWindowName, title="Warning",  message=msg, button=["Yes", "No"], defaultButton="Yes", cancelButton="No", dismissString="No", icon="question" ) == "Yes":
            revertDeadlineVRayDistributedEnabled = True
            cmds.setAttr( "vraySettings.sys_distributed_rendering_on", 1 )
        else:
            return
    
    version = cmds.about( version=True )
    version = int(float(version.split()[0]))
    
    # Get the current user Deadline home directory, which we'll use to store temp files.
    deadlineHome = CallDeadlineCommand( ["-GetCurrentUserHomeDirectory",] ).replace( "\n", "" ).replace( "\r", "" )
    deadlineTemp = deadlineHome + "/temp"
    
    # Create the job info file
    jobInfoFile = os.path.join(deadlineTemp, "vray_spawner_job_info.job")
    fileHandle = open( jobInfoFile, "w" )
    fileHandle.write( "Plugin=VraySpawner\n" )
    fileHandle.write( "Frames=0-%s\n" % (cmds.intSliderGrp( maxServersControl, q=True, v=True )-1) )
    fileHandle.write( "ChunkSize=1\n" )
    fileHandle.write( "Name=%s\n" % cmds.textFieldButtonGrp( jobNameControl, q=True, text=True ) )
    fileHandle.write( "Comment=%s\n" % cmds.textFieldGrp( commentControl, q=True, text=True ) )
    fileHandle.write( "Department=%s\n" % cmds.textFieldGrp( departmentControl, q=True, text=True ) )
    fileHandle.write( "Priority=%s\n" % cmds.intSliderGrp( priorityControl, q=True, v=True ) )
    fileHandle.write( "Pool=%s\n" % cmds.optionMenuGrp( poolControl, q=True, value=True ) )
    fileHandle.write( "SecondaryPool=%s\n" % cmds.optionMenuGrp( secondaryPoolControl, q=True, value=True ) )
    fileHandle.write( "Group=%s\n" % cmds.optionMenuGrp( groupControl, q=True, value=True ) )
    fileHandle.write( "LimitGroups=%s\n" % cmds.textFieldButtonGrp( limitControl, q=True, text=True ) )
    fileHandle.write( "Interruptible=%s\n" % cmds.checkBox( isInterruptibleControl, q=True, v=True ) )
    fileHandle.write( "TaskTimeoutMinutes=%s\n" % cmds.intSliderGrp( taskTimeoutControl, q=True, v=True ) )
    fileHandle.write( "OnTaskTimeout=Complete\n" )

    if cmds.checkBox( isBlacklistControl, q=True, v=True ):
        fileHandle.write( "Blacklist=%s\n" % cmds.textFieldButtonGrp( machineListControl, q=True, text=True ) )
    else:
        fileHandle.write( "Whitelist=%s\n" % cmds.textFieldButtonGrp( machineListControl, q=True, text=True ) )
    
    fileHandle.close()
    
    # Create the plugin info file
    pluginInfoFile = os.path.join(deadlineTemp, "vray_spawner_plugin_info.job")
    fileHandle = open( pluginInfoFile, "w" )
    fileHandle.write( "Version=Maya%s\n" % version )
    fileHandle.write( "PortNumber=%s\n" % (cmds.intSliderGrp( portNumberControl, q=True, v=True)) )
    fileHandle.close()
    
    # Submit the job to Deadline
    args = []
    args.append( jobInfoFile )
    args.append( pluginInfoFile )
    
    results = CallDeadlineCommand( args )
    print( results )
    jobId = ""
    for line in results.splitlines():
        if line.startswith( "JobID=" ):
            jobId = line[6:]
            break
    
    if jobId != "":
        print( "Spawner job submitted: " + jobId )
        
        # Store the job Id as an attribute so that the Id can be retrieved if the window is closed.
        SetJobIdAttribute( jobId )
        
        cmds.intSliderGrp( maxServersControl, e=True, enable=False )
        cmds.intSliderGrp( portNumberControl, e=True, enable=False )
        cmds.textFieldGrp( spawnerJobIdControl, e=True, text=jobId, enable=True )
        cmds.textFieldGrp( spawnerJobStatusControl, e=True, text="", enable=True )        
        cmds.text( activeServersLabel, e=True, enable=True )
        cmds.scrollField( activeServersControl, e=True, clear=True, enable=True )
        cmds.button( reserveServersButton, e=True, enable=False )
        cmds.button( startRenderButton, e=True, enable=True )
        cmds.button( releaseServersButton, e=True, enable=True )
        
        jobId = cmds.textFieldGrp( spawnerJobIdControl, q=True, text=True )
        
        Thread(target=UpdateThread).start()
    
def StartRender(*args):
    currRenderer = mel.eval("currentRenderer").lower()
    if currRenderer != "vray":
        msg = "VRay is not the current renderer. Please make it the current renderer before starting the render."
        cmds.confirmDialog( parent=submitWindowName, title="Error", message=msg, button="Close", icon="critical" )
        return
        
    if cmds.getAttr( "vraySettings.sys_distributed_rendering_on" ) == 0:
        msg = "VRay distributed rendering must be enabled before starting the render. Would you like to enable it now?"
        if cmds.confirmDialog( parent=submitWindowName, title="Warning",  message=msg, button=["Yes", "No"], defaultButton="Yes", cancelButton="No", dismissString="No", icon="question" ) == "Yes":
            cmds.setAttr( "vraySettings.sys_distributed_rendering_on", 1 )
        else:
            return
    
    cmds.RenderIntoNewWindow()

def CompleteJob(*args):
    global revertDeadlineVRayDistributedEnabled
    msg = "This will complete the VRay Spawner job. Do you wish to continue?"
    if cmds.confirmDialog( parent=submitWindowName, title="Warning",  message=msg, button=["Yes", "No"], defaultButton="Yes", cancelButton="No", dismissString="No", icon="question" ) == "No":
        return
    
    jobId = cmds.textFieldGrp( spawnerJobIdControl, q=True, text=True )
    if jobId != "":
        print( "Completing spawner job: " + jobId )
        SetJobIdAttribute( "" )
        CallDeadlineCommand( ["CompleteJob", jobId] )
    
    if revertDeadlineVRayDistributedEnabled:            
        cmds.setAttr( "vraySettings.sys_distributed_rendering_on", 0 )
        
    ResetSpawnerControls()
    
def ResetSpawnerControls():
    cmds.intSliderGrp( maxServersControl, e=True, enable=True )
    cmds.intSliderGrp( portNumberControl, e=True, enable=True )
    cmds.textFieldGrp( spawnerJobIdControl, e=True, text="", enable=False )
    cmds.textFieldGrp( spawnerJobStatusControl, e=True, text="", enable=False )
    cmds.text( activeServersLabel, e=True, enable=False )
    cmds.scrollField( activeServersControl, e=True, clear=True, enable=False )
    cmds.button( reserveServersButton, e=True, enable=True )
    cmds.button( startRenderButton, e=True, enable=False )
    cmds.button( releaseServersButton, e=True, enable=False )
    
def CompleteJobThread():
    global revertDeadlineVRayDistributedEnabled
    # We need to get the job attribute here. We can't get it from the UI at this point because it's been deleted.
    jobId = GetJobIdAttribute()
    if jobId != "":
        print( "Deadline VRay Setup window closed, completing spawner job: " + jobId )
        SetJobIdAttribute( "" )
        if revertDeadlineVRayDistributedEnabled:            
            cmds.setAttr( "vraySettings.sys_distributed_rendering_on", 0 )
        CallDeadlineCommand( ["CompleteJob", jobId] )
    
def UpdateThread():
    userAppPath = utils.executeInMainThreadWithResult(GetUserAppPath)
    serverListPath = os.path.join( userAppPath, "server_list.tmp" )
    serverStatusPath = os.path.join( userAppPath, "server_status.tmp" )
    serverPortPath = os.path.join( userAppPath, "server_ports.tmp" )
    
    serverSettingsPath = os.path.join( userAppPath, "vray_dr_list.xml" )
    
    usesSingleFile = utils.executeInMainThreadWithResult(VrayUsesSingleSettingsFile)
    
    jobId = utils.executeInMainThreadWithResult(GetSpawnerJobId)
    portNumber = utils.executeInMainThreadWithResult(GetSpawnerPortNumber)
    
    while jobId != "":
        # Update the server list.
        useIpAddress = utils.executeInMainThreadWithResult(GetUseIpAddress)
        servers = CallDeadlineCommand( ["GetMachinesRenderingJob", jobId, "true" if useIpAddress else "false"] )
        servers = servers.splitlines()
        utils.executeInMainThreadWithResult(UpdateServers, servers)
        
        # Update the job's state.
        jobState = ""
        jobInfo = CallDeadlineCommand( ["GetJob", jobId, "false"] )
        for line in jobInfo.splitlines():
            if line.startswith( "Status=" ):
                jobState = line[7:]
                break
        
        if jobState == "Active":
            jobState = "Rendering" if len(servers) > 0 else "Queued"
        elif jobState == "":
            jobState = "Deleted"
                
        utils.executeInMainThreadWithResult(UpdateState, jobState)
        
        if not usesSingleFile:
            # Update the vray config file.
            serverText = "\n".join(servers) + "\n"
            
            enabledList = []
            portNumberList = []
            
            for i in range(0, len(servers)):
                enabledList.append( "Enable" )
                portNumberList.append(portNumber)
            enabledText = "\n".join(enabledList)  + "\n"
            portNumberText = "\n".join(portNumberList) + "\n"
            
            try:
                with open( serverListPath, "w" ) as fileHandle:
                    fileHandle.write( serverText )
                
                with open( serverPortPath, "w" ) as fileHandle:
                    fileHandle.write( portNumberText )
                
                with open( serverStatusPath, "w" ) as fileHandle:
                    fileHandle.write( enabledText )
                    
            except:
                print( traceback.format_exc() )
        
        else:
            tree = ET.parse( serverSettingsPath )
            root = tree.getroot()
            
            for server in root.findall("server"):
                root.remove(server)
            
            for serverName in servers:
                curServer = ET.SubElement( root, "server" )
                hostElement = ET.SubElement( curServer, "host" )
                hostElement.text = serverName
                portElement = ET.SubElement( curServer, "port" )
                portElement.text =portNumber
                aliasElement = ET.SubElement( curServer, "alias" )
                enabledElement = ET.SubElement( curServer, "enabled" )
                enabledElement.text = "1"
                
            tree.write( serverSettingsPath, encoding="UTF-8", xml_declaration=True )
                        
        if jobState != "Rendering" and jobState != "Queued":
            utils.executeInMainThreadWithResult(NotifyJobStateChanged, jobState)
        else:
            time.sleep(5.0)
        
        jobId = utils.executeInMainThreadWithResult(GetSpawnerJobId)

def VrayUsesSingleSettingsFile():
    vrayVersion = cmds.pluginInfo("vrayformaya", q=True, v=True)
    splitVrayVersion = vrayVersion.split(".")
    if int( splitVrayVersion[0] ) > 3 or ( int( splitVrayVersion[0] ) == 3 and int( splitVrayVersion[1] ) >= 60 ):
        return True
        
    return False
        
def GetSpawnerJobId():
    if cmds.textFieldGrp( spawnerJobIdControl, q=True, exists=True ):
        return cmds.textFieldGrp( spawnerJobIdControl, q=True, text=True )
    return ""
    
def GetSpawnerPortNumber():
    if cmds.intSliderGrp( portNumberControl, q=True, exists=True ):
        return str(cmds.intSliderGrp( portNumberControl, q=True, v=True ))
    return "20207"
    
def GetUseIpAddress():
    if cmds.checkBox( useIpAddressControl, q=True, exists=True ):
        return cmds.checkBox( useIpAddressControl, q=True, v=True )
    return False
    
def UpdateServers(servers):
    cmds.scrollField( activeServersControl, e=True, text="\n".join(servers) )

def UpdateState(state):
    cmds.textFieldGrp( spawnerJobStatusControl, e=True, text=state, enable=True )

def NotifyJobStateChanged(jobState):
    msg = "The spawner job is no longer active, it is now " + jobState + "."
    cmds.confirmDialog( parent=submitWindowName, title="Job Status Changed", message=msg, button="OK", icon="warning" )
    SetJobIdAttribute( "" )
    ResetSpawnerControls()

def GetUserAppPath():
    return cmds.internalVar( userAppDir=True )
