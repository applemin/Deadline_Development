from __future__ import with_statement # with_statement is needed for python 2.5 compatability

import json
import os
import traceback

import win32com.client
from win32com.client import constants

import SoftimageToDeadlineFunctions
import SoftimageToDeadlineLogic

#Get handles to the xsi application
Application = win32com.client.Dispatch( 'XSI.Application' )
XSIUtils = win32com.client.Dispatch( 'XSI.Utils' )
XSIUIToolkit = win32com.client.Dispatch( 'XSI.UIToolkit' )

##-------------------------------------------------------------------------------------
## SoftimageToDeadline.py
## Thinkbox Software Inc, 2016
##
## This main script submits a Softimage scene to Deadline to be rendered.
##-------------------------------------------------------------------------------------

#Main Function Called by the proxy script
def Main():
    SubmitToDeadline()
    
def SubmitToDeadline():
    #check the version
    if SoftimageToDeadlineFunctions.GetIntVersion() < 8:
        Application.LogMessage("Only Softimage versions 2010 and later are supported by Deadline")
        XSIUIToolkit.MsgBox("Only Softimage versions 2010 and later are supported by Deadline")
        return
        
    #save the scene first
    if SoftimageToDeadlineFunctions.IsSaveRequired():
        Application.LogMessage( "A save is required, saving scene..." )
        try:
            Application.ExecuteCommand("SaveScene",None)
        except:
            # Exception thrown when canceled, so just return
            return
    
    progressBar = SoftimageToDeadlineFunctions.CreateProgressBar( "Launching Submission Script", 6, False )
    progressBar.Increment()
    progressBar.StatusText = "Loading scene data..."
    
    #Get the active scene and scene filename
    scene = Application.ActiveProject.ActiveScene
    
    #check how many we are going to need
    passCount = 0
    for currPass in scene.Passes:
        passCount += 1

    passesListBoxItems = [0] * (passCount * 2)
        
    listCount = 0
    for currPass in scene.Passes:        
        passesListBoxItems[listCount] = currPass.Name
        passesListBoxItems[listCount+1] = currPass.Name
        listCount += 2
    
    passesListBoxItems.sort()
    
    #Figure out what passes should be check by default (if any)
    initPassesListValue = ";".join([currPass.name for currPass in scene.Passes if currPass.Selected])
    
    progressBar.Increment()
    progressBar.StatusText = "Getting maximum priority..."
    
    
    maximumPriorityArray = SoftimageToDeadlineFunctions.GetDeadlineArray(["-getmaximumpriority",])
    if(len(maximumPriorityArray) >1 and maximumPriorityArray[1] == "Error"):
        Application.LogMessage("There was an error getting the maximum priority from Deadline: " + maximumPriorityArray[0])
        return
    
    try:
        maximumPriority = int(maximumPriorityArray[0])
    except:
        maximumPriority = 100
    
    
    progressBar.Increment()
    progressBar.StatusText = "Loading groups..."
    
        
    groupComboItems = SoftimageToDeadlineFunctions.GetDeadlineArray(["-groups",])
    if(len(groupComboItems) >1 and groupComboItems[1] == "Error"):
        Application.LogMessage("There was an error getting the groups from Deadline: " + groupComboItems[0])
        return
    
    
    progressBar.Increment()
    progressBar.StatusText = "Loading pools..."
    
    
    poolsComboItems = SoftimageToDeadlineFunctions.GetDeadlineArray(["-pools",])
    if(len(poolsComboItems)>1 and poolsComboItems[1] == "Error"):
        Application.LogMessage("There was an error getting the pools from Deadline: " + poolComboItems[0])
        return
    
    secondaryPoolsComboItems = []
    secondaryPoolsComboItems.append("")
    secondaryPoolsComboItems.append("")
    for currPool in poolsComboItems:
        secondaryPoolsComboItems.append(currPool)
    
    progressBar.Increment()
    progressBar.StatusText = "Loading initial settings..."
    
    
    Application.LogMessage(str(groupComboItems))
    fxTrees = Application.ActiveSceneRoot.Properties.Filter("FxTree")
    
    index=0
    size=0
    for tree in fxTrees:
        for op in tree.FXOperators:
            if(op.Type == "FileOutputOp"):
                size+=1
    
    fxTreeOutputNodeCollection = [0]*size
    for tree in fxTrees:
        for op in tree.FXOperators:
            if(op.Type == "FileOutputOp"):
                fxTreeOutputNodeCollection[index]=(tree.Name + "." + op.Name)
                index+=1
    
    fxTreeComboItems=["",""]
    if(len(fxTreeOutputNodeCollection) > 0):
        size = len(fxTreeOutputNodeCollection)*2
        fxTreeComboItems =[0]*size
        index=0
        for fxTreeOutputNode in fxTreeOutputNodeCollection:
            fxTreeComboItems[index] = fxTreeOutputNode
            fxTreeComboItems[index+1] = fxTreeOutputNode
            index+=2
    
    #Check if any passes use redshift as the renderer.
    isRedshift = False
    for currPass in scene.Passes:
        if SoftimageToDeadlineFunctions.IsRedshift(currPass):
            isRedshift = True
            break
    
    buildValue = "None"
    if(XSIUtils.Is64BitOS()):
        buildValue = "64bit"
    else:
        buildValue = "32bit"


    # (key, value) => (variable, (UI name, default value, type, save))
    settingsDict = {
        "defaultJobName" : ["JobNameTextBox", Application.ActiveProject.ActiveScene, 'str', False],
        "defaultComment" : ["CommentTextBox", "", 'str', True],
        "defaultDepartment" : ["DepartmentTextBox", "", 'str', True],
        "defaultPool" : ["PoolComboBox", SoftimageToDeadlineFunctions.GetDefaultItem(poolsComboItems,"none"), 'str', True],
        "defaultSecondaryPool" : ["SecondaryPoolComboBox", SoftimageToDeadlineFunctions.GetDefaultItem(secondaryPoolsComboItems,""), 'str', True],
        "defaultGroup" : ["GroupComboBox", SoftimageToDeadlineFunctions.GetDefaultItem(groupComboItems,"none"), 'str', True],
        "defaultPriority" : ["PriorityNumeric", 50, 'int', True],
        "defaultConcurrentTasks" : ["ConcurrentTasksNumeric", 1, 'int', True],
        "defaultMachineLimit" : ["MachineLimitNumeric", 0, 'int', True],
        "defaultSlaveTimeout" : ["SlaveTimeoutNumeric", 0, 'int', True],
        "defaultAutoTimeout" : ["AutoTimeout", 0, 'bool', True],
        "defaultLimitGroups" : ["LimitGroupsTextBox", "", 'str', True],
        "defaultDependencies" : ["DependenciesTextBox", "", 'str', True],
        "defaultMachineList" : ["MachineListTextBox", "", 'str', True],
        "defaultIsBlacklist" : ["IsBlacklist", False, 'bool', True],
        "defaultSuspended" : ["SubmitSuspended", False, 'bool', True],
        "defaultOnComplete" : ["OnCompleteComboBox", "Nothing", 'str', False],
        "defaultChunkSize" : ["ChunkSizeNumeric", 1, 'int', True],
        "defaultWorkgroup" : ["WorkgroupFolder", SoftimageToDeadlineFunctions.GetWorkgroupPath(), 'str', False],
        "defaultBuild" : ["BuildComboBox", buildValue, 'str', True],
        "defaultThreads" : ["ThreadsNumeric", 0, 'int', True],
        "defaultSubmitScene" : ["SubmitXsiSceneCheckBox", False, 'bool', True],
        "defaultBatch" : ["BatchBox", True, 'bool', True],
        "defaultLocalRendering" : ["LocalRenderingBox", False, 'bool', True],
        "defaultSkipBatchLicense" : ["SkipBatchLicenseBox", False, 'bool', True],
        "defaultRedshiftGPUsPerTask" : ["RedshiftGPUsPerTaskNumeric", 0, 'int', False],
        "defaultRedshiftGPUsSelectDevices" : ["RedshiftGPUsSelectDevicesBox", "", 'str', False],
        "defaultOverridePasses" : ["OverridePasses", False, 'bool', True],
        "defaultRenderAll" : ["RenderAllPasses", False, 'bool', True],
        "defaultPassesList" : ["PassesListToRender", initPassesListValue, 'str', True],
        "defaultRegion" : ["RegionRenderingCheckBox", False, 'bool', True],
        "defaultRegionX" : ["RegionXNumeric", 2, 'int', True],
        "defaultRegionY" : ["RegionYNumeric", 2, 'int', True],
        "defaultRegionError" : ["RegionErrorOnMissingCheckBox", True, 'bool', True],
        "defaultRegionLeft" : ["RegionLeft", 0, 'int', True],
        "defaultRegionTop" : ["RegionTop", 0, 'int', True],
        "defaultRegionRight" : ["RegionRight", 0, 'int', True],
        "defaultRegionBottom" : ["RegionBottom", 0, 'int', True],
        "defaultRegionSingleJob" : ["RegionSingleJobCheckBox", 0, 'bool', True],
        "defaultRegionAssemblyJob" : ["RegionAssemblyJobCheckBox", 1, 'bool', True],
        "defaultRegionCleanupJob" : ["RegionCleanupJobCheckBox", 0, 'bool', True],
        "defaultFXTree" : ["FxTreeCheckBox", False, 'bool', True],
        "defaultFXValue" : ["FxTreeComboBox", "", 'str', True],
        "defaultFXOffset" : ["FxTreeFrameOffsetNumeric", 0, 'int', True]
    }

        
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")

    # Persist submission settings within current scene
    if opSet:

        for key in settingsDict:
            # if this setting is to be updated
            shouldUpdate = settingsDict[key][3]
            if shouldUpdate:
                value = SoftimageToDeadlineFunctions.GetOpSetValue( opSet, settingsDict[key][0], settingsDict[key][1] )
                settingType = settingsDict[key][2]

                if settingType == 'int':
                    value = int(value)
                elif settingType == 'bool':
                    value = bool(value)

                settingsDict[key][1] = value

        opSet = None
        Application.ExecuteCommand("DeleteObj",[str(Application.ActiveSceneRoot) + ".SubmitSoftimageToDeadline"])
    
    # For the very first submission, attempt to load in stickySettings from last scene
    else:
        try:
            settingsPath = SoftimageToDeadlineFunctions.GetDeadlineLine(["-GetCurrentUserHomeDirectory"], False)
            with open(os.path.join(settingsPath, "settings", "softimageSticky.json"), 'r') as stickySettingsFile:
                stickySettings = json.load(stickySettingsFile)

                for key in stickySettings:   
                    settingsDict[key][1] = stickySettings[key]   

        # If file does not yet exist, catch the exception (or some other exception that may occur)           
        except Exception as e:
            Application.LogMessage( str(e) )

    if settingsDict['defaultPriority'][1] > maximumPriority:
       settingsDict['defaultPriority'][1] = (maximumPriority / 2)
    
    opSet = Application.ActiveSceneRoot.AddProperty("CustomProperty",False,"SubmitSoftimageToDeadline")
    
    opSet.AddParameter3("JobNameTextBox", constants.siString, settingsDict['defaultJobName'][1], False, False)
    opSet.AddParameter3("CommentTextBox", constants.siString, settingsDict['defaultComment'][1], False, False)
    opSet.AddParameter3("DepartmentTextBox", constants.siString, settingsDict['defaultDepartment'][1], False, False)
    
    #Render info parameters
    opSet.AddParameter3("PoolComboBox",constants.siString, SoftimageToDeadlineFunctions.GetDefaultItem(poolsComboItems, settingsDict['defaultPool'][1]), False, False)
    opSet.AddParameter3("SecondaryPoolComboBox",constants.siString, SoftimageToDeadlineFunctions.GetDefaultItem(secondaryPoolsComboItems, settingsDict['defaultSecondaryPool'][1]), False, False)
    opSet.AddParameter3("GroupComboBox",constants.siString,SoftimageToDeadlineFunctions.GetDefaultItem(groupComboItems, settingsDict['defaultGroup'][1]), False, False)
    opSet.AddParameter3("PriorityNumeric", constants.siInt2, settingsDict['defaultPriority'][1], 0, maximumPriority, False, False)
    opSet.AddParameter3("ConcurrentTasksNumeric", constants.siInt2, settingsDict['defaultConcurrentTasks'][1], 1, 16, False, False)
    opSet.AddParameter3("MachineLimitNumeric", constants.siInt2, settingsDict['defaultMachineLimit'][1], 0, 1000, False, False)
    opSet.AddParameter3("SlaveTimeoutNumeric", constants.siInt2, settingsDict['defaultSlaveTimeout'][1], 0, 5000, False, False)
    opSet.AddParameter3("AutoTimeout", constants.siBool, settingsDict['defaultAutoTimeout'][1], False, False, False)
    opSet.AddParameter3("LimitGroupsTextBox", constants.siString, settingsDict['defaultLimitGroups'][1], False, False)
    opSet.AddParameter3("DependenciesTextBox", constants.siString, settingsDict['defaultDependencies'][1], False, False)
    opSet.AddParameter3("MachineListTextBox", constants.siString, settingsDict['defaultMachineList'][1], False, False)
    opSet.AddParameter3("IsBlacklist", constants.siBool, settingsDict['defaultIsBlacklist'][1], False, False, False)
    opSet.AddParameter3("SubmitSuspended",constants.siBool, settingsDict['defaultSuspended'][1], False, False, False)
    opSet.AddParameter3("OnCompleteComboBox", constants.siString, settingsDict['defaultOnComplete'][1], False, False)
    
    #XSI Info Params
    frameStr = SoftimageToDeadlineFunctions.GetFrameRange(scene.ActivePass)
    if not SoftimageToDeadlineFunctions.GetCreateMovie(scene.ActivePass):
        frameStr = frameStr + str(SoftimageToDeadlineFunctions.GetFrameStep(scene.ActivePass))
        
    singleFrame = SoftimageToDeadlineFunctions.GetCurrentFrame()
    
    opSet.AddParameter3("Frames",constants.siString,frameStr, False, False)
    opSet.AddParameter3("ChunkSizeNumeric", constants.siInt2, settingsDict['defaultChunkSize'][1], 1, 1000, False, False)
    opSet.AddParameter3("WorkgroupFolder", constants.siString, settingsDict['defaultWorkgroup'][1], False, False)
        
    opSet.AddParameter3("BuildComboBox", constants.siString, settingsDict['defaultBuild'][1], False, False)
    opSet.AddParameter3("ThreadsNumeric", constants.siInt2, settingsDict['defaultThreads'][1], 0, 256, False, False)
    opSet.AddParameter3("SubmitXsiSceneCheckBox", constants.siBool, settingsDict['defaultSubmitScene'][1], False, False, False)
    opSet.AddParameter3("BatchBox",constants.siBool, settingsDict['defaultBatch'][1], False, False, False)
    opSet.AddParameter3("LocalRenderingBox",constants.siBool, settingsDict['defaultLocalRendering'][1], False, False, False)
    opSet.AddParameter3("SkipBatchLicenseBox",constants.siBool, settingsDict['defaultSkipBatchLicense'][1], False, False, False)
    opSet.AddParameter3("RedshiftGPUsPerTaskNumeric", constants.siInt2, settingsDict['defaultRedshiftGPUsPerTask'][1], 0, 16, False, False)
    opSet.AddParameter3("RedshiftGPUsSelectDevicesBox", constants.siString, settingsDict['defaultRedshiftGPUsSelectDevices'][1], False, False)
        
    #XSI PASSES
    opSet.AddParameter3("OverridePasses",constants.siBool, settingsDict['defaultOverridePasses'][1], False, False, False)
    opSet.AddParameter3("RenderAllPasses",constants.siBool, settingsDict['defaultRenderAll'][1], False, False, False)
    opSet.AddParameter3("PassesListToRender", constants.siString, "", False, False)
    opSet.Parameters("PassesListToRender").Value = settingsDict['defaultPassesList'][1]
    
    #Region Rendering Parameters
    opSet.AddParameter3("RegionRenderingCheckBox",constants.siBool, settingsDict['defaultRegion'][1], False, False, False)
    opSet.AddParameter3("RegionXNumeric", constants.siInt4, settingsDict['defaultRegionX'][1], 1, 20, False, False)
    opSet.AddParameter3("RegionYNumeric", constants.siInt4, settingsDict['defaultRegionY'][1], 1, 20, False, False)
    opSet.AddParameter3("RegionSingleJobCheckBox", constants.siBool, settingsDict['defaultRegionSingleJob'][1], False, False, False)
    opSet.AddParameter3("RegionSingleFrameBox", constants.siInt4, singleFrame, -100000, 100000, False, False)
    opSet.AddParameter3("RegionAssemblyJobCheckBox", constants.siBool, settingsDict['defaultRegionAssemblyJob'][1], False, False, False)
    opSet.AddParameter3("RegionCleanupJobCheckBox", constants.siBool, settingsDict['defaultRegionCleanupJob'][1], False, False, False)
    opSet.AddParameter3("RegionErrorOnMissingCheckBox",constants.siBool, settingsDict['defaultRegionError'][1], False, False, False)
    
    opSet.AddParameter3("RegionLeft", constants.siInt4, settingsDict['defaultRegionLeft'][1], 0, 1000000, False, False)
    opSet.AddParameter3("RegionTop", constants.siInt4, settingsDict['defaultRegionTop'][1], 0, 1000000, False, False)
    opSet.AddParameter3("RegionRight", constants.siInt4, settingsDict['defaultRegionRight'][1], 0, 1000000, False, False)
    opSet.AddParameter3("RegionBottom", constants.siInt4, settingsDict['defaultRegionBottom'][1], 0, 1000000, False, False)
    
    opSet.AddParameter3("RegionSingleLeft", constants.siString, "", False, False)
    opSet.AddParameter3("RegionSingleTop", constants.siString, "", False, False)
    opSet.AddParameter3("RegionSingleRight", constants.siString, "", False, False)
    opSet.AddParameter3("RegionSingleBottom", constants.siString, "", False, False)
    opSet.AddParameter3("RegionSinglePrefix", constants.siString, "", False, False)
    opSet.AddParameter3("RegionSingleTiles", constants.siInt4, settingsDict['defaultRegionLeft'][1], 0, 1000000, False, False)
    
    opSet.AddParameter3("FxTreeCheckBox", constants.siBool, settingsDict['defaultFXTree'][1], False, False, False)
    opSet.AddParameter3("FxTreeComboBox", constants.siString, settingsDict['defaultFXValue'][1], False, False)
    opSet.AddParameter3("FxTreeFrameOffsetNumeric", constants.siInt4, settingsDict['defaultFXOffset'][1], -10, 10, False, False)

    opSet.AddParameter3("integrationSettingsPath",constants.siString, None, False, False)
    opSet.AddParameter3("extraKVPIndex",constants.siString, None, False, False)
    opSet.AddParameter3("batchMode",constants.siString, None, False, False)
    
    #script filename
    scriptFilename = SoftimageToDeadlineFunctions.GetRepositoryPath("submission/Softimage/Main")
    opSet.AddParameter3("ScriptFilename", constants.siString, scriptFilename, False, False)    
    
    #Run the sanity check script if it exists, this can be used to change some initial values
    sanityCheckFile = os.path.join( scriptFilename, "CustomSanityChecks.py" )
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
    oPPGLayout.AddTab("Submission Options")
    
    #Job Info
    oPPGLayout.AddGroup("Job Description", True)
    oPPGLayout.AddRow()
    oPPGLayout.AddItem("JobNameTextBox","Job Name", constants.siControlString)
    oPPGLayout.AddButton("SetJobNameButton", "< Scene")
    oPPGLayout.EndRow()
    oPPGLayout.AddItem("CommentTextBox","Comment", constants.siControlString)
    oPPGLayout.AddItem("DepartmentTextBox","Department",constants.siControlString)
    oPPGLayout.EndGroup()
    
    #Render Info
    oPPGLayout.AddGroup("Job Scheduling", True)
    oPPGLayout.AddEnumControl("PoolComboBox", poolsComboItems, "Pool", constants.siControlCombo)
    oPPGLayout.AddEnumControl("SecondaryPoolComboBox", secondaryPoolsComboItems, "Secondary Pool", constants.siControlCombo)
    oPPGLayout.AddEnumControl("GroupComboBox",groupComboItems,"Group",constants.siControlCombo)
    oPPGLayout.AddItem("PriorityNumeric", "Priority", constants.siControlNumber)
    oPPGLayout.AddItem("ConcurrentTasksNumeric", "Concurrent Tasks", constants.siControlNumber)
    oPPGLayout.AddItem("MachineLimitNumeric", "Machine Limit", constants.siControlNumber)
    oPPGLayout.AddItem("SlaveTimeoutNumeric", "Task Timeout", constants.siControlNumber)
    oPPGLayout.AddItem("AutoTimeout", "Enable Auto Timeout", constants.siControlBoolean)
    oPPGLayout.AddRow()
    limitsButton = oPPGLayout.AddButton("LimitGroupsButton", "Limits")
    limitsButton.SetAttribute( constants.siUICX, 140 )
    limitsTextBox = oPPGLayout.AddItem("LimitGroupsTextBox", " ", constants.siControlString)
    limitsTextBox.SetAttribute( constants.siUINoLabel, True )
    oPPGLayout.EndRow()
    oPPGLayout.AddRow()
    dependenciesButton = oPPGLayout.AddButton("DependenciesButton", "Dependencies")
    dependenciesButton.SetAttribute( constants.siUICX, 140 )
    dependenciesTextBox = oPPGLayout.AddItem ("DependenciesTextBox", " ", constants.siControlString)
    dependenciesTextBox.SetAttribute( constants.siUINoLabel, True )
    oPPGLayout.EndRow()
    oPPGLayout.AddRow()
    machineListButton = oPPGLayout.AddButton("MachineListButton", "Machine List")
    machineListButton.SetAttribute( constants.siUICX, 140 )
    machineListTextBox = oPPGLayout.AddItem ("MachineListTextBox", " ", constants.siControlString)
    machineListTextBox.SetAttribute( constants.siUINoLabel, True )
    oPPGLayout.EndRow()
    oPPGLayout.AddItem ("IsBlacklist", "Machine List is a Blacklist", constants.siControlBoolean)
    oPPGLayout.AddEnumControl("OnCompleteComboBox",( "Nothing", "Nothing", "Archive", "Archive", "Delete", "Delete" ),"On Complete",constants.siControlCombo)
    oPPGLayout.AddItem ("SubmitSuspended", "Submit Job As Suspended", constants.siControlBoolean)
    oPPGLayout.EndGroup()
    
    #XSI INFO
    oPPGLayout.AddGroup("Softimage Options", True)
    oPPGLayout.AddItem("Frames", "Frame List", constants.siControlString)
    oPPGLayout.AddItem("OverridePasses", "Ignore Per Pass Frame List (Use Frame List)", constants.siControlBoolean)
    oPPGLayout.AddItem("ChunkSizeNumeric", "Group Size", constants.siControlNumber)
    oPPGLayout.AddItem("WorkgroupFolder", "Workgroup", constants.siControlFolder)
    oPPGLayout.AddRow()
    oPPGLayout.AddEnumControl("BuildComboBox", ( "None", "None", "32bit", "32bit", "64bit", "64bit" ), "Force Build", constants.siControlCombo)
    oPPGLayout.AddItem("SubmitXsiSceneCheckBox", "Submit Softimage Scene File", constants.siControlBoolean)
    oPPGLayout.EndRow()
    oPPGLayout.AddRow()
    oPPGLayout.AddItem("ThreadsNumeric", "Threads", constants.siControlNumber)
    oPPGLayout.AddItem("BatchBox","Use Softimate Batch Plugin", constants.siControlBoolean)
    oPPGLayout.EndRow()
    oPPGLayout.AddItem("LocalRenderingBox","Enable Local Rendering", constants.siControlBoolean)
    oPPGLayout.AddItem("SkipBatchLicenseBox","Skip Batch Licensing Check (non-MentalRay renders only)", constants.siControlBoolean)
    #Only show this option if at least one of the passes has Redshift as the current renderer.
    if isRedshift:
        oPPGLayout.AddItem("RedshiftGPUsPerTaskNumeric", "GPUs Per Task (Redshift only)", constants.siControlNumber)
        oPPGLayout.AddItem("RedshiftGPUsSelectDevicesBox", "Select GPU Devices (Redshift only)", constants.siControlString)
    oPPGLayout.EndGroup()

    #Buttons (Job Options Tab)
    oPPGLayout.AddRow()
    oPPGLayout.AddButton("IntegrationButton", "Pipeline Tools")
    oPPGLayout.AddButton("SubmitButton", "Submit To Deadline")
    oPPGLayout.AddButton("CloseButton", "Close Dialog")
    oPPGLayout.AddButton("ResetButton", "Close Dialog And Reset Options")
    oPPGLayout.EndRow()

    oPPGLayout.AddTab("Passes To Render")
    
    #XSI Passes
    oPPGLayout.AddGroup("Passes To Render (current pass is used if none are selected)", True)
    oPPGLayout.AddItem("RenderAllPasses", "Render All " + str(passCount) + " Passes", constants.siControlBoolean)

    passesList = oPPGLayout.AddItem("PassesListToRender", "Select Passes", constants.siControlListBox)
    passesList.SetAttribute( constants.siUICY, 424 )
    passesList.SetAttribute( constants.siUIMultiSelectionListBox, True )
    passesList.UIItems = passesListBoxItems
    
    oPPGLayout.EndGroup()
    
    #Buttons (Passes Tab)
    oPPGLayout.AddRow()
    oPPGLayout.AddButton("IntegrationButton", "Pipeline Tools")
    oPPGLayout.AddButton("SubmitButton", "Submit To Deadline")
    oPPGLayout.AddButton("CloseButton", "Close Dialog")
    oPPGLayout.AddButton("ResetButton", "Close Dialog And Reset Options")
    oPPGLayout.EndRow()

    oPPGLayout.AddTab("Tile Rendering")
    # Region Rendering
    oPPGLayout.AddGroup("Tile Rendering", True)
    oPPGLayout.AddItem("RegionRenderingCheckBox", "Enable Tile Rendering", constants.siControlBoolean)
    oPPGLayout.AddItem("RegionXNumeric", "Tiles in X", constants.siControlNumber)
    oPPGLayout.AddItem("RegionYNumeric", "Tiles in Y", constants.siControlNumber)
    oPPGLayout.EndGroup()
    
    oPPGLayout.AddGroup("Single Job Tile Rendering", True)
    oPPGLayout.AddItem("RegionSingleJobCheckBox", "Submit All Tiles As A Single Job", constants.siControlBoolean)
    oPPGLayout.AddItem("RegionSingleFrameBox", "Single Job Frame", constants.siControlNumber)
    oPPGLayout.AddItem("RegionAssemblyJobCheckBox", "Submit Dependent Assembly Job", constants.siControlBoolean)
    oPPGLayout.AddItem("RegionCleanupJobCheckBox", "Cleanup Tile Files After Assembly Job Completes", constants.siControlBoolean)
    oPPGLayout.AddItem("RegionErrorOnMissingCheckBox", "Error On Missing Tiles", constants.siControlBoolean)
    oPPGLayout.EndGroup()
    
    #Buttons (Tile Rendering Tab)
    oPPGLayout.AddRow()
    oPPGLayout.AddButton("IntegrationButton", "Pipeline Tools")
    oPPGLayout.AddButton("SubmitButton", "Submit To Deadline")
    oPPGLayout.AddButton("CloseButton", "Close Dialog")
    oPPGLayout.AddButton("ResetButton", "Close Dialog And Reset Options")
    oPPGLayout.EndRow()

    oPPGLayout.AddTab("FxTree Rendering")

    #FxTree Rendering
    oPPGLayout.AddGroup("FxTree Rendering", True)
    oPPGLayout.AddItem("FxTreeCheckBox", "Submit An FxTree Render Job (ignores Passes and Tile Rendering options)", constants.siControlBoolean)
    oPPGLayout.AddEnumControl("FxTreeComboBox", fxTreeComboItems, "FxTree Output", constants.siControlCombo)
    oPPGLayout.AddItem("FxTreeFrameOffsetNumeric", "Frame Offset", constants.siControlNumber)
    oPPGLayout.EndGroup()

    #Buttons (FxTree Tab)
    oPPGLayout.AddRow()
    oPPGLayout.AddButton("IntegrationButton", "Pipeline Tools")
    oPPGLayout.AddButton("SubmitButton", "Submit To Deadline")
    oPPGLayout.AddButton("CloseButton", "Close Dialog")
    oPPGLayout.AddButton("ResetButton", "Close Dialog And Reset Options")
    oPPGLayout.EndRow()
    
    #Use get script file name to get the full path then just change the script
    script = os.path.join( scriptFilename, "SoftimageToDeadlineLogic.py" )
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

    #oPPGLayout.Language = "Python"
    oPPGLayout.Language = "pythonscript"
    oView = Application.Desktop.ActiveLayout.CreateView( "Property Panel", "DeadlineProperties" )
    
    oView.BeginEdit()
    oView.Move(10, 10)
    if isRedshift:
        oView.Resize(580, 735)
    else:
        oView.Resize(580, 695)
    oView.SetAttributeValue("targetcontent", opSet.FullName)
    oView.EndEdit()
    
    #Read in the button logic from another script
    
#######################################################################################################
## Uncomment the following line when debugging this script from within Softimage's script editor.
#######################################################################################################
#SubmitToDeadline()
