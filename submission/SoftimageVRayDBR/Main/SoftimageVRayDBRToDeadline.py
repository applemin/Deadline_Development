import os
import traceback
import win32com.client
from win32com.client import constants

import SoftimageVRayDBRToDeadlineFunctions
import SoftimageVRayDBRToDeadlineLogic

##-------------------------------------------------------------------------------------
## SoftimageVRayDBRToDeadline.py
## Thinkbox Software Inc, 2014
##
## This main script submits a VRay DBR job to reserve Deadline Slaves for VRay DBR for Softimage.
##-------------------------------------------------------------------------------------

Application = win32com.client.Dispatch( 'XSI.Application' )
XSIUtils = win32com.client.Dispatch( 'XSI.Utils' )
XSIUIToolkit = win32com.client.Dispatch( 'XSI.UIToolkit' )

#Main Function Called by the proxy script
def Main():
    SubmitVRayDBRToDeadline()
    
def SubmitVRayDBRToDeadline():

    #check the version
    if SoftimageVRayDBRToDeadlineFunctions.GetIntVersion() < 8:
        Application.LogMessage("Only Softimage versions 2010 and later are supported by Deadline")
        XSIUIToolkit.MsgBox("Only Softimage versions 2010 and later are supported by Deadline")
        return

    progressBar = SoftimageVRayDBRToDeadlineFunctions.CreateProgressBar( "Launching Submission Script", 4, False )

    progressBar.Increment()
    progressBar.StatusText = "Getting maximum priority..."
    
    maximumPriorityArray = SoftimageVRayDBRToDeadlineFunctions.GetDeadlineArray(["-getmaximumpriority",])
    if(len(maximumPriorityArray) >1 and maximumPriorityArray[1] == "Error"):
        Application.LogMessage("There was an error getting the maximum priority from Deadline: " + maximumPriorityArray[0])
        return
    
    try:
        maximumPriority = int(maximumPriorityArray[0])
    except:
        maximumPriority = 100
    
    progressBar.Increment()
    progressBar.StatusText = "Loading pools..."
    
    poolsComboItems = SoftimageVRayDBRToDeadlineFunctions.GetDeadlineArray(["-pools",])
    if(len(poolsComboItems)>1 and poolsComboItems[1] == "Error"):
        Application.LogMessage("There was an error getting the pools from Deadline: " + poolComboItems[0])
        return
    
    progressBar.Increment()
    progressBar.StatusText = "Loading groups..."

    groupComboItems = SoftimageVRayDBRToDeadlineFunctions.GetDeadlineArray(["-groups",])
    if(len(groupComboItems) >1 and groupComboItems[1] == "Error"):
        Application.LogMessage("There was an error getting the groups from Deadline: " + groupComboItems[0])
        return
    
    secondaryPoolsComboItems = []
    secondaryPoolsComboItems.append("")
    secondaryPoolsComboItems.append("")
    for currPool in poolsComboItems:
        secondaryPoolsComboItems.append(currPool)
    
    progressBar.Increment()
    progressBar.StatusText = "Loading initial settings..."
    
    defaultJobName = ( "VRay DBR Job (Softimage %s)" % str(SoftimageVRayDBRToDeadlineFunctions.GetYearVersion()) )
    defaultComment = ""
    defaultDepartment = ""
    defaultPool = SoftimageVRayDBRToDeadlineFunctions.GetDefaultItem(poolsComboItems,"none")
    defaultSecondaryPool = SoftimageVRayDBRToDeadlineFunctions.GetDefaultItem(secondaryPoolsComboItems,"")
    defaultGroup = SoftimageVRayDBRToDeadlineFunctions.GetDefaultItem(groupComboItems,"none")
    defaultPriority = 50
    defaultTaskTimeout = 0
    defaultLimitGroups = ""
    defaultMachineList = ""
    defaultIsBlacklist = False
    defaultIsInterruptible = False
    defaultMaxServers = 10
    defaultUseIpAddress = False
    defaultPortNumber = 20207
    
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageVRayDBRToDeadline")
    if(opSet != None):
        defaultJobName = SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "JobNameTextBox", defaultJobName )
        defaultComment = SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "CommentTextBox", defaultComment )
        defaultDepartment = SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "DepartmentTextBox", defaultDepartment )
        defaultPool = SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "PoolComboBox", defaultPool )
        defaultSecondaryPool = SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "SecondaryPoolComboBox", defaultSecondaryPool )
        defaultGroup = SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "GroupComboBox", defaultGroup )
        defaultPriority = int(SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "PriorityNumeric", defaultPriority ))
        defaultLimitGroups = SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "LimitGroupsTextBox", defaultLimitGroups )
        defaultMachineList = SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "MachineListTextBox", defaultMachineList )
        defaultIsBlacklist = bool(SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "IsBlacklist", defaultIsBlacklist ))
        defaultIsInterruptible = bool(SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "IsInterruptible", defaultIsInterruptible ))
        defaultMaxServers = int(SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "MaxServers", defaultMaxServers ))
        defaultUseIpAddress = bool(SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "UseIpAddress", defaultUseIpAddress ))
        defaultPortNumber = int(SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "PortNumber", defaultPortNumber ))
        defaultTaskTimeout = int(SoftimageVRayDBRToDeadlineFunctions.GetOpSetValue( opSet, "TaskTimeout", defaultTaskTimeout ))

        opSet = None
        Application.ExecuteCommand("DeleteObj",[str(Application.ActiveSceneRoot) + ".SubmitSoftimageVRayDBRToDeadline"])
    
    if defaultPriority > maximumPriority:
       defaultPriority = (maximumPriority / 2)
    
    opSet = Application.ActiveSceneRoot.AddProperty("CustomProperty",False,"SubmitSoftimageVRayDBRToDeadline")
    
    opSet.AddParameter3("JobNameTextBox", constants.siString, defaultJobName)
    opSet.AddParameter3("CommentTextBox", constants.siString, defaultComment)
    opSet.AddParameter3("DepartmentTextBox", constants.siString, defaultDepartment)
    opSet.AddParameter3("PoolComboBox", constants.siString, SoftimageVRayDBRToDeadlineFunctions.GetDefaultItem(poolsComboItems,defaultPool))
    opSet.AddParameter3("SecondaryPoolComboBox", constants.siString, SoftimageVRayDBRToDeadlineFunctions.GetDefaultItem(secondaryPoolsComboItems,defaultSecondaryPool))
    opSet.AddParameter3("GroupComboBox", constants.siString, SoftimageVRayDBRToDeadlineFunctions.GetDefaultItem(groupComboItems,defaultGroup))
    opSet.AddParameter3("PriorityNumeric", constants.siInt2, defaultPriority, 0, maximumPriority, False)
    opSet.AddParameter3("TaskTimeoutNumeric", constants.siInt2, defaultTaskTimeout, 0, 10000, False)
    opSet.AddParameter3("LimitGroupsTextBox", constants.siString, defaultLimitGroups)
    opSet.AddParameter3("MachineListTextBox", constants.siString, defaultMachineList)
    opSet.AddParameter3("IsBlacklist", constants.siBool, defaultIsBlacklist, False, False, False)
    opSet.AddParameter3("IsInterruptible", constants.siBool, defaultIsInterruptible, False, False, False)
    opSet.AddParameter3("MaxServers", constants.siInt2, defaultMaxServers, 1, 100, False)
    opSet.AddParameter3("UseIpAddress", constants.siBool, defaultUseIpAddress, False, False, False)
    opSet.AddParameter3("PortNumber", constants.siUInt4, defaultPortNumber, 0, 99999, False)
    
    tempOP = opSet.AddParameter3("StandaloneJobId", constants.siString, "")
    tempOP.Enable( False )
    tempOP = opSet.AddParameter3("StandaloneJobStatus", constants.siString, "")
    tempOP.Enable( False )
    tempOP = opSet.AddParameter3("ActiveServers", constants.siString, "")
    tempOP.Enable( False )

    #Run the sanity check script if it exists, this can be used to change some initial values
    sanityCheckFile = ( SoftimageVRayDBRToDeadlineFunctions.GetScriptFilename() ).replace( "SoftimageVRayDBRToDeadline.py", "CustomSanityChecks.py" )
    if os.path.isfile( sanityCheckFile ):
        Application.LogMessage( "Running sanity check script: " + sanityCheckFile )
        try:
            import CustomSanityChecks
            sanityResult = CustomSanityChecks.RunSanityCheck( opSet )
            if not sanityResult:
                Application.LogMessage( "Sanity check returned false, exiting" )
                progressBar.Visible = False
                return
        except:
            Application.LogMessage( "Could not run CustomSanityChecks.py script: " + traceback.format_exc() )
    
    #Set up the layout of the dialog
    oPPGLayout = opSet.PPGLayout
##################

    oPPGLayout.Clear()
    
    #Job Info
    oPPGLayout.AddGroup("Job Description", True)
    oPPGLayout.AddRow()
    oItem = oPPGLayout.AddItem("JobNameTextBox","Job Name", constants.siControlString)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oPPGLayout.AddButton("SetJobNameButton", "< Scene")
    oPPGLayout.EndRow()
    oItem = oPPGLayout.AddItem("CommentTextBox","Comment", constants.siControlString)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oItem = oPPGLayout.AddItem("DepartmentTextBox","Department",constants.siControlString)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oPPGLayout.EndGroup()
    
    #Render Info
    oPPGLayout.AddGroup("Job Scheduling", True)
    oItem = oPPGLayout.AddEnumControl("PoolComboBox", poolsComboItems, "Pool", constants.siControlCombo)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oItem = oPPGLayout.AddEnumControl("SecondaryPoolComboBox", secondaryPoolsComboItems, "Secondary Pool", constants.siControlCombo)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oItem = oPPGLayout.AddEnumControl("GroupComboBox",groupComboItems,"Group",constants.siControlCombo)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oItem = oPPGLayout.AddItem("PriorityNumeric", "Priority", constants.siControlNumber)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oItem = oPPGLayout.AddItem("TaskTimeoutNumeric", "Task Timeout", constants.siControlNumber)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oPPGLayout.AddRow()
    limitsButton = oPPGLayout.AddButton("LimitGroupsButton", "Limits")
    limitsButton.SetAttribute( constants.siUICX, 90 )
    limitsTextBox = oPPGLayout.AddItem("LimitGroupsTextBox", " ", constants.siControlString)
    limitsTextBox.SetAttribute( constants.siUINoLabel, True )
    oPPGLayout.EndRow()
    oPPGLayout.AddRow()
    machineListButton = oPPGLayout.AddButton("MachineListButton", "Machine List")
    machineListButton.SetAttribute( constants.siUICX, 90 )
    machineListTextBox = oPPGLayout.AddItem ("MachineListTextBox", " ", constants.siControlString)
    machineListTextBox.SetAttribute( constants.siUINoLabel, True )
    oPPGLayout.EndRow()
    oPPGLayout.AddItem ("IsBlacklist", "Machine List is a Blacklist", constants.siControlBoolean)
    oPPGLayout.AddItem ("IsInterruptible", "Job Is Interruptible", constants.siControlBoolean)
    oPPGLayout.EndGroup()
    
    #XSI INFO
    oPPGLayout.AddGroup("VRay Standalone Options", True)
    oItem = oPPGLayout.AddItem("MaxServers", "Maximum Servers", constants.siControlNumber)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oItem = oPPGLayout.AddItem("PortNumber", "Port Number", constants.siControlNumber)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    
    oPPGLayout.AddItem ("UseIpAddress", "Use Server IP Address Instead of Host Name", constants.siControlBoolean)

    oPPGLayout.AddRow()
    oItem = oPPGLayout.AddItem ("StandaloneJobId", "Active Job ID", constants.siControlString)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oPPGLayout.EndRow()

    oPPGLayout.AddRow()
    oItem = oPPGLayout.AddItem ("StandaloneJobStatus", "Active Job Status", constants.siControlString)
    oItem.SetAttribute( constants.siUILabelMinPixels, 90 )
    oPPGLayout.EndRow()

    activeServersList = oPPGLayout.AddItem("ActiveServers", "Active Servers", constants.siControlListBox)
    activeServersList.SetAttribute( constants.siUILabelMinPixels, 90 )
    activeServersList.SetAttribute( constants.siUICY, 150 )
    activeServersList.SetAttribute( constants.siUIMultiSelectionListBox, False )
    activeServersListBoxItems = []
    activeServersList.UIItems = activeServersListBoxItems

    oPPGLayout.EndGroup()
     
    #Buttons (Job Options Tab)
    oPPGLayout.AddRow()    
    
    oItem = oPPGLayout.AddButton("ReserveServers", "Reserve Servers")
    oItem.SetAttribute( constants.siUICX, 120 )
    oItem = oPPGLayout.AddButton("RenderCurrentPass", "Render Current Pass")
    oItem.SetAttribute( constants.siUICX, 120 )
    oItem.SetAttribute( constants.siUIButtonDisable, True )
    oItem = oPPGLayout.AddButton("RenderAllPasses", "Render All Passes")
    oItem.SetAttribute( constants.siUICX, 120 )
    oItem.SetAttribute( constants.siUIButtonDisable, True )
    oItem = oPPGLayout.AddButton("ReleaseServers", "Release Servers")
    oItem.SetAttribute( constants.siUICX, 120 )
    oItem.SetAttribute( constants.siUIButtonDisable, True )
    oPPGLayout.EndRow()

    oPPGLayout.AddRow()
    oItem = oPPGLayout.AddButton("SceneOptions", "Scene Options")
    oItem.SetAttribute( constants.siUICX, 120 )
    oItem = oPPGLayout.AddButton("VRayDROptions", "VRay DR Options")
    oItem.SetAttribute( constants.siUICX, 120 )
    oItem = oPPGLayout.AddButton("CloseButton", "Close Dialog")
    oItem.SetAttribute( constants.siUICX, 120 )
    oItem = oPPGLayout.AddButton("ResetButton", "Close/Reset Dialog")
    oItem.SetAttribute( constants.siUICX, 120 )
    oPPGLayout.EndRow()
    
    #Use get script file name to get the full path then just change the script
    script = SoftimageVRayDBRToDeadlineFunctions.GetScriptFilename()
    script = script.replace("SoftimageVRayDBRToDeadline.py", "SoftimageVRayDBRToDeadlineLogic.py")
    Application.LogMessage("Script file: " + script)
    
    if(os.path.exists(script)):
        textStream = open(script,"r")
        logic = textStream.read()
        oPPGLayout.Logic = logic
        textStream.close()
    else:
        Application.LogMessage("Script Logic File Not Found")

    progressBar.Increment()
    progressBar.StatusText = "Finished"
    progressBar.Visible = False

    oPPGLayout.Language = "Python"
    oView = Application.Desktop.ActiveLayout.CreateView2( "Property Panel", "DeadlineVRayDBRProperties" )
    
    oView.BeginEdit()
    oView.Move(10, 10)
    oView.Resize(500, 670)
    oView.SetAttributeValue("targetcontent", opSet.FullName)
    oView.EndEdit()
    
#######################################################################################################
## Uncomment the following line when debugging this script from within Softimage's script editor.
#######################################################################################################
#SubmitVRayDBRToDeadline()
