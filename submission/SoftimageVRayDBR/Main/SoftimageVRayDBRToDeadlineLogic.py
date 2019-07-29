import win32com.client
from win32com.client import constants

import SoftimageVRayDBRToDeadlineFunctions

##-------------------------------------------------------------------------------------
## SoftimageVRayDBRToDeadlineLogic.py
## Thinkbox Software Inc, 2014
##
## Logic used by the main script.
##-------------------------------------------------------------------------------------

Application = win32com.client.Dispatch( 'XSI.Application' )
XSIUtils = win32com.client.Dispatch( 'XSI.Utils' )
XSIUIToolkit = win32com.client.Dispatch( 'XSI.UIToolkit' )

##-------------------------------------------------------------------------------------
## Button Logic Callbacks
##-------------------------------------------------------------------------------------
def SetJobNameButton_OnClicked():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
    if(opSet != None):
        suffix = "VRay DBR Job (Softimage %s)" % str(SoftimageVRayDBRToDeadlineFunctions.GetYearVersion())
        SceneName = Application.ActiveProject.ActiveScene.Name
        if SceneName == "Scene":
            PPG.JobNameTextBox.Value = "Untitled" + " - " + suffix
        else:
            PPG.JobNameTextBox.Value = SceneName + " - " + suffix

def LimitGroupsButton_OnClicked():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
    if(opSet != None):    
        progressBar = SoftimageVRayDBRToDeadlineFunctions.CreateProgressBar( "Running deadlinecommand", 2, False )
        progressBar.Increment()
        progressBar.StatusText = "Collecting limits..."
    
        limitGroups = SoftimageVRayDBRToDeadlineFunctions.GetDeadlineLine(["-selectlimitgroups", PPG.LimitGroupsTextBox.Value], True)
        
        progressBar.Increment()
        progressBar.StatusText = "Finished"
        progressBar.Visible = False
        
        if(limitGroups != "Error getting line" and limitGroups != "Action was cancelled by user" ):
            PPG.LimitGroupsTextBox.Value = limitGroups

def MachineListButton_OnClicked():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
    if(opSet != None):
        progressBar = SoftimageVRayDBRToDeadlineFunctions.CreateProgressBar( "Running deadlinecommand", 2, False )
        progressBar.Increment()
        progressBar.StatusText = "Collecting machine list..."
        
        machineList = SoftimageVRayDBRToDeadlineFunctions.GetDeadlineLine(["-selectmachinelist", PPG.MachineListTextBox.Value], True)
        
        progressBar.Increment()
        progressBar.StatusText = "Finished"
        progressBar.Visible = False
        
        if(machineList != "Error getting line" and machineList != "Action was cancelled by user"):
            PPG.MachineListTextBox.Value = machineList

def SceneOptions_OnClicked():
    Application.InspectObj("Passes.RenderOptions", "", "", 1, "")

def VRayDROptions_OnClicked():
    currPass = Application.GetCurrentPass()
    if(SoftimageVRayDBRToDeadlineFunctions.IsVRay( currPass )):
        if Application.ActiveSceneRoot.Properties("VrayDistributedRendering") != None:
            Application.InspectObj( "VrayDistributedRendering" )
        else:
            Application.LogMessage( "VRay renderer must be INITIALIZED as the renderer for this pass!", constants.siWarning )
    else:
        Application.LogMessage( "VRay renderer must be set as CURRENT renderer for this pass!", constants.siWarning )

def CloseButton_OnClicked():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
    jobId = SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "StandaloneJobId", "" )
    if jobId != "":
        message = "This will complete the VRay Spawner job and close the submission dialog.\n\nDo you wish to continue?"
        result = XSIUIToolkit.MsgBox(message, constants.siMsgYesNo | constants.siMsgQuestion, "Warning")
        if(result != constants.siMsgYes):
            return
    
    updateTimer = Application.EventInfos( "SubmitSoftimageVRayDBRToDeadline_TIMER" )
    updateTimer.Mute = True
    
    SoftimageVRayDBRToDeadlineFunctions.MarkJobAsComplete()
    PPG.Close()

def ResetButton_OnClicked():
    message = "This will close the submission dialog and remove the saved options from the scene root.\n\nDo you wish to continue?"
    
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
    jobId = SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "StandaloneJobId", "" )
    if jobId != "":
        message = "This will complete the VRay Spawner job, close the submission dialog, and remove the saved options from the scene root.\n\nDo you wish to continue?"
    
    result = XSIUIToolkit.MsgBox(message, constants.siMsgYesNo | constants.siMsgQuestion, "Warning")
    if(result == constants.siMsgYes):
        updateTimer = Application.EventInfos( "SubmitSoftimageVRayDBRToDeadline_TIMER" )
        updateTimer.Mute = True
        
        SoftimageVRayDBRToDeadlineFunctions.MarkJobAsComplete()
        
        opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
        if(opSet != None):
            Application.ExecuteCommand("DeleteObj",[opSet])
        
        PPG.Close()

def ReserveServers_OnClicked():
    Application.LogMessage("Reserving Servers...")
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
    if(opSet != None):

        # Check VRay is the renderer for the current pass
        currPass = Application.GetCurrentPass()
        if(not SoftimageVRayDBRToDeadlineFunctions.IsVRay( currPass )):
            XSIUIToolkit.MsgBox("VRay is not the current renderer!\n\nPlease make it the current renderer before reserving servers.",constants.siMsgOkOnly | constants.siMsgExclamation, "Warning")
            return
            
        # Check "VRay DR Options" dialog has been initialized at least once by opening the dialog in Softimage
        if Application.ActiveSceneRoot.Properties("VrayDistributedRendering") == None:
            XSIUIToolkit.MsgBox("VRay must be INITIALIZED as the renderer for this pass!\n\nOpen 'VRay DR Options' to initialize.",constants.siMsgOkOnly | constants.siMsgExclamation, "Warning")
            return
            
        # Check VRay DR is enabled for the current pass
        if (not Application.GetValue("VrayDistributedRendering.use_dr")):
            XSIUIToolkit.MsgBox("VRay distributed rendering must be enabled before reserving servers.\n\nOpen 'VRay DR Options' and enable 'Use Distributed Rendering'",constants.siMsgOkOnly | constants.siMsgExclamation, "Warning")
            return

        results = SoftimageVRayDBRToDeadlineFunctions.SubmitDBRJob(opSet)
        
        jobId = ""
        for line in results.splitlines():
            if line.startswith( "JobID=" ):
                jobId = line[6:]
                break
        
        if jobId != "":
            Application.LogMessage( "DBR job submitted: " + jobId )

            SoftimageVRayDBRToDeadlineFunctions.SetOpSetValue( opSet, "StandaloneJobId", jobId )
            SoftimageVRayDBRToDeadlineFunctions.SetOpSetValue( opSet, "StandaloneJobStatus", "" )
            
            SoftimageVRayDBRToDeadlineFunctions.SetOpSetEnabled( opSet, "MaxServers", False )
            SoftimageVRayDBRToDeadlineFunctions.SetOpSetEnabled( opSet, "PortNumber", False )
            SoftimageVRayDBRToDeadlineFunctions.SetOpSetEnabled( opSet, "StandaloneJobStatus", True )
            SoftimageVRayDBRToDeadlineFunctions.SetOpSetEnabled( opSet, "ActiveServers", True )
            
            oPPGLayout = opSet.PPGLayout
            oPPGLayout.Item("ActiveServers").UIItems = []
            oPPGLayout.Item("ReserveServers").SetAttribute( constants.siUIButtonDisable, True )
            oPPGLayout.Item("RenderCurrentPass").SetAttribute( constants.siUIButtonDisable, False )
            oPPGLayout.Item("RenderAllPasses").SetAttribute( constants.siUIButtonDisable, False )
            oPPGLayout.Item("ReleaseServers").SetAttribute( constants.siUIButtonDisable, False )
            
            PPG.Refresh()
            
            updateTimer = Application.EventInfos( "SubmitSoftimageVRayDBRToDeadline_TIMER" )
            updateTimer.Mute = False

def RenderCurrentPass_OnClicked():
    Application.LogMessage("Rendering Current Pass...")
    
    scene = Application.ActiveProject.ActiveScene
    currentFrame = SoftimageVRayDBRToDeadlineFunctions.GetCurrentFrame()
    passName = "Passes." + scene.ActivePass.Name
    
    Application.LogMessage("Pass: " + passName)
    Application.LogMessage( "Frame: " + str(currentFrame))
    
    Application.RenderPasses(passName, currentFrame, currentFrame, 1)
    
def RenderAllPasses_OnClicked():
    Application.LogMessage("Rendering All Passes...")
    
    scene = Application.ActiveProject.ActiveScene
    currentFrame = SoftimageVRayDBRToDeadlineFunctions.GetCurrentFrame()
    
    passNames = []
    for currPass in scene.Passes:
        passNames.append( "Passes." + currPass.Name )
    
    Application.RenderPasses(",".join(passNames), currentFrame, currentFrame, 1)

def ReleaseServers_OnClicked():
    message = "This will complete the VRay Spawner job. Do you wish to continue?"
    result = XSIUIToolkit.MsgBox(message, constants.siMsgYesNo | constants.siMsgQuestion, "Warning")
    if(result == constants.siMsgYes):
        Application.LogMessage("Releasing Servers...")
        
        updateTimer = Application.EventInfos( "SubmitSoftimageVRayDBRToDeadline_TIMER" )
        updateTimer.Mute = True
        
        SoftimageVRayDBRToDeadlineFunctions.MarkJobAsComplete()
        SoftimageVRayDBRToDeadlineFunctions.ResetSpawnerControls()
        
        PPG.Refresh()

def StandaloneJobStatus_OnChanged():
    # Just do a refresh so that the active server list gets updated in the UI.
    PPG.Refresh()
