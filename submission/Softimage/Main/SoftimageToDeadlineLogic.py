from __future__ import with_statement  # with_statement is needed for python 2.5 compatability

import json
import os
import re

import win32com.client
from win32com.client import constants

import SoftimageToDeadlineFunctions

##-------------------------------------------------------------------------------------
## SoftimageToDeadlineLogic.py
## Thinkbox Software Inc, 2016
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
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")
    if(opSet != None):    
        PPG.JobNameTextBox.Value = Application.ActiveProject.ActiveScene

def LimitGroupsButton_OnClicked():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")
    if(opSet != None):    
        progressBar = SoftimageToDeadlineFunctions.CreateProgressBar( "Running deadlinecommand", 2, False )
        progressBar.Increment()
        progressBar.StatusText = "Collecting limits..."
    
        limitGroups = SoftimageToDeadlineFunctions.GetDeadlineLine(["-selectlimitgroups", PPG.LimitGroupsTextBox.Value], True)
        
        progressBar.Increment()
        progressBar.StatusText = "Finished"
        progressBar.Visible = False
        
        if(limitGroups != "Error getting line" and limitGroups != "Action was cancelled by user" ):
            PPG.LimitGroupsTextBox.Value = limitGroups

def DependenciesButton_OnClicked():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")
    if(opSet != None):
        progressBar = SoftimageToDeadlineFunctions.CreateProgressBar( "Running deadlinecommand", 2, False )
        progressBar.Increment()
        progressBar.StatusText = "Collecting dependencies..."
        
        dependencies = SoftimageToDeadlineFunctions.GetDeadlineLine(["-selectdependencies", PPG.DependenciesTextBox.Value], True)
        
        progressBar.Increment()
        progressBar.StatusText = "Finished"
        progressBar.Visible = False
        
        if(dependencies != "Error getting line" and dependencies != "Action was cancelled by user"):
            PPG.DependenciesTextBox.Value = dependencies

def MachineListButton_OnClicked():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")
    if(opSet != None):
        progressBar = SoftimageToDeadlineFunctions.CreateProgressBar( "Running deadlinecommand", 2, False )
        progressBar.Increment()
        progressBar.StatusText = "Collecting machine list..."
        
        machineList = SoftimageToDeadlineFunctions.GetDeadlineLine(["-selectmachinelist", PPG.MachineListTextBox.Value], True)
        
        progressBar.Increment()
        progressBar.StatusText = "Finished"
        progressBar.Visible = False
        
        if(machineList != "Error getting line" and machineList != "Action was cancelled by user"):
            PPG.MachineListTextBox.Value = machineList

def ResetButton_OnClicked():
    result = XSIUIToolkit.MsgBox("This will close the submission dialog and remove the saved options from the scene root\nDo you wish to continue?",constants.siMsgYesNo | constants.siMsgQuestion, "Warning")
    
    if(result == constants.siMsgYes):
        opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")
        if(opSet != None):
            Application.ExecuteCommand("DeleteObj",[opSet])
        PPG.Close()

def RedshiftGPUsPerTaskNumeric_OnChanged():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")
    if(opSet != None):
        PPG.RedshiftGPUsSelectDevicesBox.Enable( PPG.RedshiftGPUsPerTaskNumeric.Value == 0 )

def RedshiftGPUsSelectDevicesBox_OnChanged():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")
    if(opSet != None):
        PPG.RedshiftGPUsPerTaskNumeric.Enable( PPG.RedshiftGPUsSelectDevicesBox.Value == "" )

def CloseButton_OnClicked():
    Application.LogMessage("Closing")
    PPG.Close()

def IntegrationButton_OnClicked():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")
    scriptPath = SoftimageToDeadlineFunctions.GetRepositoryFilePath("submission/Integration/Main/IntegrationUIStandAlone.py", True)
    scriptPath = scriptPath.strip()
    
    argArray = ["-ExecuteScript", scriptPath, "SoftImage", "Draft", "Shotgun", "FTrack", "0"]

    results = SoftimageToDeadlineFunctions.CallDeadlineCommand( argArray, False )
    outputLines = results.splitlines()

    for line in outputLines:
        line = line.strip()
        if not line.startswith( "(" ):
            tokens = line.split( "=", 1 )

            if len( tokens ) > 1:
                key = tokens[0]
                value = tokens[1]

                opSet.Parameters( key ).Value = value

def SubmitButton_OnClicked():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")
    if(opSet != None):
        scene = Application.ActiveProject.ActiveScene

        #Check if any passes use redshift as the renderer.
        isRedshift = False
        for currPass in scene.Passes:
            if SoftimageToDeadlineFunctions.IsRedshift(currPass):
                isRedshift = True
                break

        if isRedshift:
            if PPG.RedshiftGPUsPerTaskNumeric.Value == 0 and PPG.RedshiftGPUsSelectDevicesBox != "":
                regex = re.compile( "^(\d{1,2}(,\d{1,2})*)?$" )
                validSyntax = regex.match( PPG.RedshiftGPUsSelectDevicesBox.Value )    
                if not validSyntax:
                    XSIUIToolkit.MsgBox("Redshift 'Select GPU Devices' syntax is invalid!\n\nTrailing 'commas' if present, should be removed.\n\nValid Examples: 0 or 2 or 0,1,2 or 0,3,4 etc")
                    return

        errorMessages = ""
        warningMessages = ""
        
        if(opSet.Parameters("FxTreeCheckBox").Value):
            currPass = scene.ActivePass
            fxTreeOutputNode = opSet.Parameters("FxTreeComboBox").Value
            
            if(fxTreeOutputNode == ""):
                errorMessages = errorMessages + "\n- " + "No FxTree render node is selected"
                
            outputFilename = SoftimageToDeadlineFunctions.GetFxOutputFilename(fxTreeOutputNode)
            Application.LogMessage("output file: " + outputFilename)
            
            if(not SoftimageToDeadlineFunctions.IsExtensionValid(outputFilename)):
                warningMessages = warningMessages + "\n- " + fxTreeOutputNode + ": The Output Image Filename does not include a valid extension at the end.\nIn order to view individual rendered images from the Deadline Monitor, the extension\nmust be included at the end when specifying the Output Image Filename."
                    
            if(not SoftimageToDeadlineFunctions.IsPathAbsolute(outputFilename)):
                errorMessages = errorMessages + "\n- " + fxTreeOutputNode + ": The image output path is not absolute"

            if(SoftimageToDeadlineFunctions.IsPathLocal(outputFilename)):
                warningMessages = warningMessages + "\n- " + fxTreeOutputNode + ": The image output path is local."
                    
            sceneFile = scene.Filename.Value
            if((not opSet.Parameters("SubmitXsiSceneCheckBox").Value) and SoftimageToDeadlineFunctions.IsPathLocal(sceneFile)):
                warningMessages = warningMessages + "\n- " + "Softimage Scene file " + sceneFile + " is on a local drive and is not being submitted."
            
            if errorMessages != "":
                XSIUIToolkit.MsgBox(errorMessages)
                return
            
            if warningMessages != "":
                result = XSIUIToolkit.MsgBox(warningMessages + "\n\nDo you wish to continue?")
                if(result == constants.siMsgNo):
                    return
                
            results = SoftimageToDeadlineFunctions.SubmitDeadlineJob(opSet,scene, currPass)
            XSIUIToolkit.MsgBox(results)
        
        else:
            passesListValue = opSet.Parameters("PassesListToRender").Value
            selectedPasses = passesListValue.split(";")
            allPasses = opSet.Parameters("RenderAllPasses").Value
            
            #Check output path for all passes being submitted
            for currPass in scene.Passes:
                #If all pass for submission or current pass for submission or this pass is selected then
                if(allPasses or (passesListValue == "") or (currPass.Name in selectedPasses)):
                    #If submitting current pass only then only check the current pass
                    if(passesListValue == "" and not allPasses):
                        currPass = scene.ActivePass
                        
                    #Check if the output extension is valid
                    outputFilename = SoftimageToDeadlineFunctions.GetOutputFilename(currPass)
                    if(not SoftimageToDeadlineFunctions.IsExtensionValid(outputFilename)):
                        warningMessages = warningMessages + "\n- " + currPass.Name + ": The Output Image Filename does not include a valid extension at the end.\nIn order to view individual rendered images from the Deadline Monitor, the extension\nmust be included at the end when specifying the Output Image Filename."
                            
                    #Check if the path is absolute
                    if(not SoftimageToDeadlineFunctions.IsPathAbsolute(outputFilename)):
                        errorMessages = errorMessages + "\n- " + currPass.Name + ": The image output path is not absolute."
                    
                    #Check if the path is local
                    if(SoftimageToDeadlineFunctions.IsPathLocal(outputFilename)):
                        warningMessages = warningMessages + "\n- " + currPass.Name + ": The image output path is local."
                    
                    #If creating a movie check the movie output path
                    isMovie = SoftimageToDeadlineFunctions.GetCreateMovie(currPass)
                    if(isMovie):
                        movieFilename = GetMovieFilename(currPass)
                        
                        #Check if the path is absolute
                        if(not SoftimageToDeadlineFunctions.IsPathAbsolute(movieFilename)):
                            errorMessages = errorMessages + "\n- " + currPass.Name + ": The movie output path is not absolute."
                            
                        #Check if the path is local
                        if(SoftimageToDeadlineFunctions.IsPathLocal(movieFilename)):
                            warningMessages = warningMessages + "\n- " + currPass.Name + ": The movie output path is local."
                    
                    #If submitting the current pass only the check only the current pass
                    if(passesListValue == "" and not allPasses):
                        break
            
            sceneFile = scene.Filename.Value
            if((not opSet.Parameters("SubmitXsiSceneCheckBox").Value) and SoftimageToDeadlineFunctions.IsPathLocal(sceneFile)):
                warningMessages = warningMessages + "\n- " + "Softimage Scene file " + sceneFile + " is on a local drive and is not being submitted."
            
            if errorMessages != "":
                XSIUIToolkit.MsgBox("The following errors were encountered:" + errorMessages + "\n\nPlease resolve these issues and submit again.\n\n")
                return
            
            if warningMessages != "":
                result = XSIUIToolkit.MsgBox("Warnings:" + warningMessages + "\n\nDo you wish to continue?\n\n",constants.siMsgYesNo | constants.siMsgQuestion, "Warning")
                if(result == constants.siMsgNo):
                    return
            
            submittedJobs = 0
            result = ""
            
            for currPass in scene.Passes:
                #If all pass for submission or current pass for submission or this pass is selected then
                if(allPasses or (passesListValue == "") or (currPass.Name in selectedPasses)):
                    
                    #If submitting current pass only, check the current pass
                    if(passesListValue == "" and not allPasses):
                        currPass = scene.ActivePass
                        
                    result = SoftimageToDeadlineFunctions.SubmitDeadlineJob(opSet,scene,currPass)
                    Application.LogMessage( result )
                    
                    submittedJobs = submittedJobs+1
                    
                    if(passesListValue == "" and not allPasses):
                        break
            
            if submittedJobs == 1:
                XSIUIToolkit.MsgBox(result)
            else:
                XSIUIToolkit.MsgBox("Finished submitting " + str(submittedJobs) + " jobs. See the History Log in the Script Editor for complete submission results." )
    


    initPassesListValue = ";".join([currPass.name for currPass in scene.Passes if currPass.Selected])

    jsonMap = {
        "defaultComment" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "CommentTextBox", "" ),
        "defaultDepartment" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "DepartmentTextBox", "" ),
        "defaultPool" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "PoolComboBox", "none" ),
        "defaultSecondaryPool" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "SecondaryPoolComboBox", "" ),
        "defaultGroup" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "GroupComboBox", "none" ),
        "defaultPriority" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "PriorityNumeric", 50 ),
        "defaultConcurrentTasks" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "ConcurrentTasksNumeric", 1 ),
        "defaultMachineLimit" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "MachineLimitNumeric", 0 ),
        "defaultSlaveTimeout" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "SlaveTimeoutNumeric", 0 ),
        "defaultAutoTimeout" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "AutoTimeout", 0 ),
        "defaultLimitGroups" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "LimitGroupsTextBox", "" ),
        "defaultDependencies" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "DependenciesTextBox", "" ),
        "defaultMachineList" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "MachineListTextBox", "" ),
        "defaultIsBlacklist" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "IsBlacklist", False ),
        "defaultSuspended" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "SubmitSuspended", False ),
        "defaultChunkSize" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "ChunkSizeNumeric", 1 ),
        "defaultBuild" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "BuildComboBox", "64bit" if XSIUtils.Is64BitOS() else "32bit" ),
        "defaultThreads" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "ThreadsNumeric", 0 ),
        "defaultSubmitScene" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "SubmitXsiSceneCheckBox", False ),
        "defaultBatch" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "BatchBox", True ),
        "defaultLocalRendering" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "LocalRenderingBox", False ),
        "defaultSkipBatchLicense" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "SkipBatchLicenseBox", False ),
        "defaultOverridePasses" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "OverridePasses", False ),
        "defaultRenderAll" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RenderAllPasses", False ),
        "defaultRegion" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionRenderingCheckBox", False ),
        "defaultRegionX" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionXNumeric", 2 ),
        "defaultRegionY" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionYNumeric", 2 ),
        "defaultRegionLeft" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionLeft", 0 ),
        "defaultRegionTop" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionTop", 0 ),
        "defaultRegionRight" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionRight", 0 ),
        "defaultRegionBottom" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionBottom", 0 ),
        "defaultRegionSingleJob" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionSingleJobCheckBox", 0 ),
        "defaultRegionAssemblyJob" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionAssemblyJobCheckBox", 1 ),
        "defaultRegionCleanupJob" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionCleanupJobCheckBox", 0 ),
        "defaultRegionError" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "RegionErrorOnMissingCheckBox", True ),
        "defaultFXTree" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "FxTreeCheckBox", False ),
        "defaultFXValue" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "FxTreeComboBox", "" ),
        "defaultFXOffset" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "FxTreeFrameOffsetNumeric", 0 ),
        "defaultOnComplete" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "OnCompleteComboBox", "Nothing" ),
        "defaultPassesList" : SoftimageToDeadlineFunctions.GetOpSetValue( opSet, "PassesListToRender", initPassesListValue )
    }

    settingsPath = SoftimageToDeadlineFunctions.GetDeadlineLine(["-GetCurrentUserHomeDirectory"], False)
    with open(os.path.join(settingsPath, "settings", "softimageSticky.json"), 'w') as stickySettingsFile:
        json.dump(jsonMap, stickySettingsFile)

def SubmitButton_OnClicked_Old():
    opSet = Application.ActiveSceneRoot.Properties("SubmitSoftimageToDeadline")
    if(opSet != None):
        scene = Application.ActiveProject.ActiveScene
        
        errorMessages = ""
        warningMessages = ""
        
        if(opSet.Parameters("FxTreeCheckBox").Value):
            currPass = scene.ActivePass
            fxTreeOutputNode = opSet.Parameters("FxTreeComboBox").Value
            
            if(fxTreeOutputNode == ""):
                errorMessages = errorMessages + "\n- " + "No FxTree render node is selected"
                
            outputFilename = SoftimageToDeadlineFunctions.GetFxOutputFilename(fxTreeOutputNode)
            Application.LogMessage("output file: " + outputFilename)
            
            if(not SoftimageToDeadlineFunctions.IsExtensionValid(outputFilename)):
                warningMessages = warningMessages + "\n- " + fxTreeOutputNode + ": The Output Image Filename does not include a valid extension at the end.\nIn order to view individual rendered images from the Deadline Monitor, the extension\nmust be included at the end when specifying the Output Image Filename."
                    
            if(not SoftimageToDeadlineFunctions.IsPathAbsolute(outputFilename)):
                errorMessages = errorMessages + "\n- " + fxTreeOutputNode + ": The image output path is not absolute"

            if(SoftimageToDeadlineFunctions.IsPathLocal(outputFilename)):
                warningMessages = warningMessages + "\n- " + fxTreeOutputNode + ": The image output path is local."
                    
            sceneFile = scene.Filename.Value
            if((not opSet.Parameters("SubmitXsiSceneCheckBox").Value) and SoftimageToDeadlineFunctions.IsPathLocal(sceneFile)):
                warningMessages = warningMessages + "\n- " + "Softimage Scene file " + sceneFile + " is on a local drive and is not being submitted."
            
            if errorMessages != "":
                XSIUIToolkit.MsgBox(errorMessages)
                return
            
            if warningMessages != "":
                result = XSIUIToolkit.MsgBox(warningMessages + "\n\nDo you wish to continue?")
                if(result == constants.siMsgNo):
                    return
                
            results = SoftimageToDeadlineFunctions.SubmitDeadlineJob(opSet,scene, currPass)
            XSIUIToolkit.MsgBox(results)
        
        else:
            passesValue = opSet.Parameters("PassesToRender").Value
            passesValue2 = opSet.Parameters("PassesToRender2").Value
            passesValue3 = opSet.Parameters("PassesToRender3").Value
            passesValue4 = opSet.Parameters("PassesToRender4").Value
            passesValue5 = opSet.Parameters("PassesToRender5").Value
            
            allPasses = opSet.Parameters("RenderAllPasses").Value
            
            Application.LogMessage("passesValue = " + str(passesValue))
            Application.LogMessage("passesValue2 = " + str(passesValue2))
            Application.LogMessage("passesValue3 = " + str(passesValue3))
            Application.LogMessage("passesValue4 = " + str(passesValue4))
            Application.LogMessage("passesValue5 = " + str(passesValue5))
            
            #maxPasses = 31
            maxPasses = 15
            currPassesValue = passesValue
            
            #Check output path for all passes being submitted
            passCount = 0
            for currPass in scene.Passes:
                passCount += 1
                if passCount == (maxPasses + 1):
                    currPassesValue = passesValue2
                elif passCount == ((maxPasses*2) + 1):
                    currPassesValue = passesValue3
                elif passCount == ((maxPasses*3) + 1):
                    currPassesValue = passesValue4
                elif passCount == ((maxPasses*4) + 1):
                    currPassesValue = passesValue5
                
                #If all pass for submission or current pass for submission or this pass is selected then
                if(allPasses or (passesValue+passesValue2+passesValue3+passesValue4+passesValue5) == 0 or (currPassesValue % 2) ==1):
                    Application.LogMessage("Curr pass Value " + str(currPassesValue))
                    #if submitting current pass only then only check the current pass
                    if((passesValue+passesValue2+passesValue3+passesValue4+passesValue5) == 0 and not allPasses):
                        currPass = scene.ActivePass
                        
                    #Check if the output extension is valid
                    outputFilename = SoftimageToDeadlineFunctions.GetOutputFilename(currPass)
                    if(not SoftimageToDeadlineFunctions.IsExtensionValid(outputFilename)):
                        warningMessages = warningMessages + "\n- " + currPass.Name + ": The Output Image Filename does not include a valid extension at the end.\nIn order to view individual rendered images from the Deadline Monitor, the extension\nmust be included at the end when specifying the Output Image Filename."
                            
                    #Check if the path is absolute
                    if(not SoftimageToDeadlineFunctions.IsPathAbsolute(outputFilename)):
                        errorMessages = errorMessages + "\n- " + currPass.Name + ": The image output path is not absolute"
                    
                    #Check if the path is local
                    if(SoftimageToDeadlineFunctions.IsPathLocal(outputFilename)):
                        warningMessages = warningMessages + "\n- " + currPass.Name + ": The image output path is local."
                    
                    #If creating a movie check the movie output path
                    isMovie = SoftimageToDeadlineFunctions.GetCreateMovie(currPass)
                    if(isMovie):
                        movieFilename = GetMovieFilename(currPass)
                        
                        #Check if the path is absolute
                        if(not SoftimageToDeadlineFunctions.IsPathAbsolute(movieFilename)):
                            errorMessages = errorMessages + "\n- " + currPass.Name + ": he movie output path is not absolute"
                            
                        #Check if the path is local
                        if(SoftimageToDeadlineFunctions.IsPathLocal(movieFilename)):
                            warningMessages = warningMessages + "\n- " + currPass.Name + ": The movie output path is local"
                    
                    #If submitting the current pass only the check only the current pass
                    if((passesValue+passesValue2+passesValue3+passesValue4+passesValue5) == 0 and not allPasses):
                        break
                        
                    currPassesValue=currPassesValue-1
                
                if(currPassesValue > 0):
                    currPassesValue = currPassesValue/2
            
            sceneFile = scene.Filename.Value
            if((not opSet.Parameters("SubmitXsiSceneCheckBox").Value) and SoftimageToDeadlineFunctions.IsPathLocal(sceneFile)):
                warningMessages = warningMessages + "\n- " + "Softimage Scene file " + sceneFile + " is on a local drive and is not being submitted."
            
            if errorMessages != "":
                XSIUIToolkit.MsgBox("The following errors were encountered:" + errorMessages + "\n\nPlease resolve these issues and submit again.\n\n")
                return
            
            if warningMessages != "":
                result = XSIUIToolkit.MsgBox("Warnings:" + warningMessages + "\n\nDo you wish to continue?\n\n",constants.siMsgYesNo | constants.siMsgQuestion, "Warning")
                if(result == constants.siMsgNo):
                    return
            
            submittedJobs = 0
            result = ""
            
            currPassesValue = passesValue
            
            passCount = 0
            for currPass in scene.Passes:
                passCount += 1
                if passCount == (maxPasses + 1):
                    currPassesValue = passesValue2
                elif passCount == ((maxPasses*2) + 1):
                    currPassesValue = passesValue3
                elif passCount == ((maxPasses*3) + 1):
                    currPassesValue = passesValue4
                elif passCount == ((maxPasses*4) + 1):
                    currPassesValue = passesValue5
                
                if(allPasses or (passesValue+passesValue2+passesValue3+passesValue4+passesValue5) == 0 or (currPassesValue % 2) ==1):
                    Application.LogMessage("Curr pass Value " + str(currPassesValue))
                    
                    #If submitting current pass only, check the current pass
                    if((passesValue+passesValue2+passesValue3+passesValue4+passesValue5) == 0 and not allPasses):
                        currPass = scene.ActivePass
                        
                    result = SoftimageToDeadlineFunctions.SubmitDeadlineJob(opSet,scene,currPass)
                    Application.LogMessage( result )
                    
                    submittedJobs = submittedJobs+1
                    
                    if((passesValue+passesValue2+passesValue3+passesValue4+passesValue5) == 0 and not allPasses):
                        break
                        
                    currPassesValue=currPassesValue-1
                        
                if(currPassesValue>0):
                    currPassesValue/=2
            
            if submittedJobs == 1:
                XSIUIToolkit.MsgBox(result)
            else:
                XSIUIToolkit.MsgBox("Finished submitting " + str(submittedJobs) + " jobs. See the History Log in the Script Editor for complete submission results." )
