from __future__ import print_function
import sys
import os
import subprocess
import traceback
import re
import hou
import time
import threading
import time
import socket
import uuid
import tempfile
import platform

try:
    import ConfigParser
except:
    print( "Could not load ConfigParser module, sticky settings will not be loaded/saved" )

dialog = None
closing = False


maxPriority = 0
homeDir = ""
deadlineSettings = ""
deadlineTemp = ""

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

def CallDeadlineCommand( arguments, background=True, readStdout=True ):
    deadlineCommand = GetDeadlineCommand()

    startupinfo = None
    creationflags = 0
    if os.name == 'nt':
        if background:
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
    
    stdoutPipe = None
    if readStdout:
        stdoutPipe=subprocess.PIPE
        
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=stdoutPipe, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags)
    proc.stdin.close()
    proc.stderr.close()

    output = ""
    if readStdout:
        output = proc.stdout.read()
    return output

def InitializeDialog():
    global dialog, maxPriority
    
    # Get maximum priority
    try:
        output = CallDeadlineCommand( ["-getmaximumpriority",] )
        maxPriority = int(output)
    except:
        maxPriority = 100

    # Get pools
    output = CallDeadlineCommand( ["-pools",] )
    pools = output.splitlines()
    secondaryPools = pools 

    # Get groups
    output = CallDeadlineCommand( ["-groups",] )
    groups = output.splitlines()

    # Make the file name the name of the job
    scene = hou.hipFile.name() 
    index1 = scene.rfind( "\\" )
    index2 = scene.rfind( "/" )
    
    name = ""
    if index1 > index2:
        name = scene[index1+1:len(scene)]
    else:
        name = scene[index2+1:len(scene)]
    
    renderers = []
    ropList = []
    node = hou.node( "/" )
    allNodes = node.allSubChildren()
    
    for rop in allNodes:
        if isinstance(rop, hou.RopNode):
            if rop.type().description() == "Mantra":
                renderers.append(rop)
                ropList.append( rop.path() )
        
    #SET INITIAL GUI VALUES
    dialog.setValue( "joboptions.val", 1 )
    dialog.setValue( "jobname.val", name )
    dialog.setValue( "comment.val", "" )
    dialog.setValue( "department.val", "" )

    dialog.setMenuItems( "pool.val", pools )
    dialog.setMenuItems( "secondarypool.val", secondaryPools )
    dialog.setMenuItems( "group.val", groups )
    dialog.setValue( "priority.val", maxPriority/2 )
    dialog.setValue( "tasktimeout.val", 0 )
    dialog.setValue( "autotimeout.val", 0 )
    dialog.setValue( "concurrent.val", 1 )
    dialog.setValue( "slavelimit.val", 1 )
    dialog.setValue( "machinelimit.val", 0 )
    dialog.setValue( "machinelist.val", "" )
    dialog.setValue( "isblacklist.val", 0 )
    dialog.setValue( "limits.val", "" )
    dialog.setValue( "dependencies.val", "" )
    dialog.setMenuItems( "onjobcomplete.val", ["Nothing", "Archive", "Delete"] )
    dialog.setMenuItems( "rendernode.val", ropList )
    dialog.setValue( "servercount.val", 1 )
    
    dialog.enableValue( "reserveservers.val", True )
    dialog.enableValue( "updateservers.val", False )
    dialog.enableValue( "startrender.val", False )
    dialog.enableValue( "releaseservers.val", False )
    
    #dialog.enableValue( "renderjobid.val", False)
    #dialog.enableValue( "renderjobstatus.val", False)
    #dialog.enableValue( "activeservers.val", False)
    
    return True
    
def Callbacks():
    dialog.addCallback( "getmachinelist.val", GetMachineListFromDeadline )
    dialog.addCallback( "getlimits.val", GetLimitGroupsFromDeadline )
    dialog.addCallback( "getdependencies.val", GetDependenciesFromDeadline )

    dialog.addCallback( "priority.val", JobPriorityCallback )
    dialog.addCallback( "tasktimeout.val", TaskTimeoutCallback )
    dialog.addCallback( "concurrent.val", ConcurrentTasksCallback )
    dialog.addCallback( "machinelimit.val", MachineLimitCallback )

    dialog.addCallback( "reserveservers.val", ReserveServersCallback )
    dialog.addCallback( "updateservers.val", UpdateServersCallback )
    dialog.addCallback( "startrender.val", StartRenderCallback )
    dialog.addCallback( "releaseservers.val", ReleaseServersCallback )
    dialog.addCallback( "servercount.val", ServerCountDialogCallback )
    dialog.addCallback( "dlg.val", DialogClosedCallback )
              
def GetMachineListFromDeadline():
    global dialog

    output = CallDeadlineCommand( ["-selectmachinelist", dialog.value("machinelist.val")], False )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        dialog.setValue( "machinelist.val", output )

def GetLimitGroupsFromDeadline():
    global dialog

    output = CallDeadlineCommand( ["-selectlimitgroups", dialog.value("limits.val")], False )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        dialog.setValue( "limits.val", output )

def GetDependenciesFromDeadline():
    global dialog

    output = CallDeadlineCommand( ["-selectdependencies", dialog.value("dependencies.val")], False )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        dialog.setValue( "dependencies.val", output )

def JobPriorityCallback():
    global dialog, maxPriority
    
    priority = dialog.value( "priority.val" )
    if priority > maxPriority:
        dialog.setValue( "priority.val", maxPriority )
    elif priority < 0:
        dialog.setValue( "priority.val", 0 )

def TaskTimeoutCallback():
    global dialog

    taskTimeout = dialog.value( "tasktimeout.val" )
    if taskTimeout > 1000000:
        dialog.setValue( "tasktimeout.val", 1000000 )
    elif taskTimeout < 0:
        dialog.setValue( "tasktimeout.val", 0 )

def ConcurrentTasksCallback():
    global dialog

    concurrentTasks = dialog.value( "concurrent.val" )
    if concurrentTasks > 16:
        dialog.setValue( "concurrent.val", 16 )
    elif concurrentTasks < 1:
        dialog.setValue( "concurrent.val", 1 )

def ServerCountDialogCallback():
    global dialog
    
    serverCount = dialog.value( "servercount.val" )
    if serverCount < 1:
        dialog.setValue( "servercount.val", 1 )
    
        
def MachineLimitCallback():
    global dialog

    machineLimit = dialog.value( "machinelimit.val" )
    if machineLimit > 1000000:
        dialog.setValue( "machinelimit.val", 1000000 )
    elif machineLimit < 0:
        dialog.setValue( "machinelimit.val", 0 )
   
def ReserveServersCallback():
    global dialog, homeDir, jigsawThread
    
    jobResult = ""
        
    # if no secondary pool is selected, get rid of the space
    if dialog.value( "secondarypool.val" ) == " ":
        dialog.setValue( "secondarypool.val", "" )
    
    jobName = dialog.value( "jobname.val" )
        
    # Create submission info file
    jobInfoFile = os.path.join(homeDir, "temp", "hserver_submit_info.job")
    fileHandle = open( jobInfoFile, "w" )
    fileHandle.write( "Plugin=HServer\n" )
    fileHandle.write( "Name=%s - HServer Reservation\n" % jobName )
    fileHandle.write( "Comment=%s\n" % dialog.value( "comment.val" ) )
    fileHandle.write( "Department=%s\n" % dialog.value( "department.val" ) )
    fileHandle.write( "Pool=%s\n" % dialog.value( "pool.val" ) )
    fileHandle.write( "SecondaryPool=%s\n" % dialog.value( "secondarypool.val" ) )
    fileHandle.write( "Group=%s\n" % dialog.value( "group.val" ) )
    fileHandle.write( "Priority=%s\n" % dialog.value ( "priority.val" ) )
    fileHandle.write( "TaskTimeoutMinutes=%s\n" % dialog.value( "tasktimeout.val" ) )
    fileHandle.write( "EnableAutoTimeout=%s\n" % dialog.value( "autotimeout.val" ) )
    fileHandle.write( "ConcurrentTasks=%s\n" % dialog.value( "concurrent.val" ) )
    fileHandle.write( "MachineLimit=%s\n" % dialog.value( "machinelimit.val" ) )
    fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % dialog.value( "slavelimit.val" ) )
    fileHandle.write( "LimitGroups=%s\n" % dialog.value( "limits.val" ) )
    fileHandle.write( "JobDependencies=%s\n" % dialog.value( "dependencies.val" ) )
    fileHandle.write( "OnJobComplete=%s\n" % dialog.value( "onjobcomplete.val" ) )

    if dialog.value( "isblacklist.val" ):
        fileHandle.write( "Blacklist=%s\n" % dialog.value( "machinelist.val" ) )
    else:
        fileHandle.write( "Whitelist=%s\n" % dialog.value( "machinelist.val" ) )
                    
    fileHandle.write( "ChunkSize=1\n" )
    fileHandle.write( "Frames=0-%s\n" % ( dialog.value( "servercount.val" ) - 1 ) )
    fileHandle.write( "ForceReloadPlugin=True\n" )
    fileHandle.close()
    
    # Create plugin info file
    pluginInfoFile = os.path.join( homeDir, "temp", "hserver_plugin_info.job" )
    fileHandle = open( pluginInfoFile, "w" )
    fileHandle.close()
    
    arguments = []
    arguments.append( jobInfoFile )
    arguments.append( pluginInfoFile )
        
    jobResult = CallDeadlineCommand( arguments )
    
    dialog.setValue( "status.val", "100%: Job submitted" )
    print("Job submitted\n")
    hou.ui.displayMessage( jobResult, title="Submit HServer To Deadline" )
    
    jobId = "";
    resultArray = jobResult.split("\n")
    for line in resultArray:
        if line.startswith("JobID="):
            jobId = line.replace("JobID=","")
            jobId = jobId.strip()
            break
    
    dialog.setValue( "renderjobid.val", jobId )
    dialog.enableValue( "reserveservers.val", False )
    dialog.enableValue( "updateservers.val", True )
    dialog.enableValue( "startrender.val", False )
    dialog.enableValue( "releaseservers.val", True )
    

def UpdateServersCallback():

    useIpAddress = dialog.value( "useipaddress.val" )
    jobId = dialog.value( "renderjobid.val" )
    servers = CallDeadlineCommand( ["GetMachinesRenderingJob", jobId, "true" if useIpAddress else "false", "true" ])
    servers = servers.splitlines()
    dialog.setValue( "activeservers.val", ",".join( servers ) )
    
    jobState = ""
    jobInfo = CallDeadlineCommand( ["GetJob", jobId, "false"] )
    for line in jobInfo.splitlines():
        if line.startswith( "Status=" ):
            jobState = line[7:]
            break
    
    dialog.enableValue( "startrender.val", False )
    if jobState == "Active":
        if len( servers ) > 0:
            jobState = "Rendering"
            dialog.enableValue( "startrender.val", True )
        else:
            jobState = "Queued"        
    elif jobState == "":
        jobState = "Deleted"
    dialog.setValue( "renderjobstatus.val", jobState )
    

def ReleaseServersCallback():

    jobId = dialog.value( "renderjobid.val" )
    if len(jobId) > 0 :  
        CallDeadlineCommand( ["CompleteJob", jobId] ) 
    
    dialog.setValue( "renderjobid.val", "" )
    dialog.setValue( "activeservers.val", "" )
    dialog.setValue( "renderjobstatus.val", "" )

    dialog.enableValue( "reserveservers.val", True )
    dialog.enableValue( "updateservers.val", False )
    dialog.enableValue( "startrender.val", False )
    dialog.enableValue( "releaseservers.val", False )
    
def getDependentNodes(job):
    dependentJobs = []
    node = hou.node(job)
    try:
        for inputNode in node.inputs():
            if inputNode.type().description() == "Mantra" and not inputNode.isBypassed():
                dependentJobs.append(inputNode.path())
            dependentJobs.extend(InputRenderJobs(inputNode.path(),availableJobs))
    except:
        pass
    return dependentJobs
    
    
def StartRenderCallback():
    oldValues = {}
    
    rop = dialog.value( "rendernode.val")
    
    if rop == "No Valid ROPs":
        hou.ui.displayMessage( "No valid ROPS selected.", title="Submit HServer To Deadline" )
        return
        
    node = hou.node(rop)
    commandParm = node.parm("soho_pipecmd")
    renderCommand = commandParm.eval()
    
    oldValues[rop] = renderCommand
    
    for depPath in getDependentNodes(rop):
        depNode = hou.node(depPath)
        depCommandParm = depNode.parm("soho_pipecmd")
        depCommand = depCommandParm.eval()
        
        oldValues[depNode.path()] = depCommand
        depCommandParts = depCommand.split()
        try:
            serverIndex = depCommandParts.index("-H")
            depCommandParts[serverIndex+1] = dialog.value("activeservers.val")
        except ValueError:
            depCommandParts.append("-H")
            depCommandParts.append( dialog.value("activeservers.val") )        
        
        depCommandParm.set(" ".join(depCommandParts))
    
    commandParts = renderCommand.split()
    try:
        serverIndex = commandParts.index("-H")
        commandParts[serverIndex+1] = dialog.value("activeservers.val")
    except ValueError:
        commandParts.append("-H")
        commandParts.append( dialog.value("activeservers.val") )        
    
    commandParm.set(" ".join(commandParts))
    
    try:
        node.render()
    except:
        pass
    done = False
    while not done:
        try:
            done = True
            for ropName, oldCommand in oldValues.iteritems():
                node = hou.node(ropName)
                node.parm("soho_pipecmd").set(oldCommand)
        except KeyboardInterrupt:
            done = False
                
    
def DialogClosedCallback():
    dlgOpen = dialog.value( "dlg.val" )
    if not dlgOpen:
        jobId = dialog.value( "renderjobid.val" )
        if len(jobId) > 0 :  
            CallDeadlineCommand( ["CompleteJob", jobId] ) 
    
    
def SubmitHServerToDeadline( uiPath ): 
    global dialog, deadlineSettings, deadlineTemp, shotgunScript, homeDir, configFile, ftrackScript
    
    
    homeDir = CallDeadlineCommand( ["-GetCurrentUserHomeDirectory",] )
    homeDir = homeDir.replace( "\r", "" ).replace( "\n", "" )
    
    # Need to strip off the last eol char, it wasn't a \n
    deadlineTemp = os.path.join( homeDir, "temp" )
    deadlineSettings = os.path.join( homeDir, "settings" )
    
    print("Creating Submission Dialog...")
    dialog = hou.ui.createDialog( uiPath )
    
    if not InitializeDialog():
        return

    print("Initializing Callbacks...")
    Callbacks()

################################################################################
## DEBUGGING
################################################################################
#
# HOWTO: (1) Open Houdini's python shell: Alt + Shift + P   or   Windows --> Python Shell
#        (2) Copy and paste line (A) to import this file (MAKE SURE THE PATH IS CORRECT FOR YOU)
#        (3) Copy and paste line (B) to execute this file for testing
#        (4) If you change this file, copy and paste line (C) to reload this file, GOTO step (3)
#
# (A)
# root = "C:/DeadlineRepository6/";import os;os.chdir(root + "submission/Houdini/Main/");import SubmitHoudiniToDeadline
#
# (B)
# SubmitHoudiniToDeadline.SubmitToDeadline(root)
#
# (C)
# reload(SubmitHoudiniToDeadline)