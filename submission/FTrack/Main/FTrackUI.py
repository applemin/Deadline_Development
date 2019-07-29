import json
import io
import os
import sys
import threading
import time
import traceback
from collections import deque

from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from System.IO import *

########################################################################
## Globals
########################################################################
scriptDialog = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    parentAppName = ""

    if len( args ) > 0:
        parentAppName = args[0]

    scriptDialog = FTrackDialog( parentAppName )
    
    # Add control buttons
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer", 0, 0 )
    okButton = scriptDialog.AddControlToGrid( "OkButton", "ButtonControl", "OK", 0, 1, expand=False )
    okButton.clicked.connect( OKButtonClicked )
    cancelButton = scriptDialog.AddControlToGrid( "CancelButton", "ButtonControl", "Cancel", 0, 2, expand=False )
    cancelButton.clicked.connect( CancelButtonClicked )
    scriptDialog.EndGrid()

    scriptDialog.ShowDialog( True )

def OKButtonClicked():
    global scriptDialog

    if not scriptDialog.Validate(): 
        return

    settingsDict = scriptDialog.GetSettingsDictionary()
    
    for key in settingsDict.keys():
        ClientUtils.LogText( "%s=%s" % ( key, settingsDict[key] ) )

    scriptDialog.CloseConnection()
    super( FTrackDialog, scriptDialog ).accept()

def CancelButtonClicked():
    scriptDialog.CloseConnection()
    super( FTrackDialog, scriptDialog ).reject()

########################################################################
## Subclass of DeadlineScriptDialog for the UI
########################################################################
class FTrackDialog( DeadlineScriptDialog ):
    ftrackURL = None
    ftrackKey = None
    ftrackProxy = None
    ftrackConnection = None

    currentUser = None

    defaultProject = None
    defaultTask = None
    defaultAsset = None

    stickySettings = {}

    #These dictionaries map from string keys displayed in combo boxes to actual Ftrack objects
    curProjectDict = {}
    curTaskDict = {}
    curAssetDict = {}

    #These dictionaries cache tasks/assets from projects/tasks (respectively) not currently selected
    cachedTasks = {}
    cachedAssets = {}
    
    def __init__( self, parentAppName="", parent=None ):
        super( FTrackDialog, self ).__init__( parent )

        config = RepositoryUtils.GetEventPluginConfig( "FTrack" )
        self.ftrackURL = config.GetConfigEntryWithDefault( "FTrackURL", "" ).strip()
        self.ftrackKey = config.GetConfigEntryWithDefault( "FTrackAPIKey", "" ).strip()
        self.ftrackProxy = config.GetConfigEntryWithDefault( "FTrackProxy", "" ).strip()

        self.parentAppName = parentAppName #used to keep distinct StickySettings between applications
        self.logMessages = [""]
        self.dataValidated = False
        self.settingsDict = {}
        
        self.enableUI = True
        
        self.SetTitle( "FTrack Asset Picker" )


        dialogWidth = 480
        controlHeight = -1 #20

        self.AddControl( "Separator1", "SeparatorControl", "FTrack Fields", dialogWidth, controlHeight )

        self.AddGrid()
        curRow = 0

        self.AddControlToGrid( "LoginLabel", "LabelControl", "Login Name", curRow, 0, "Your FTrack login name.", expand=False )
        self.loginBox = self.AddControlToGrid( "LoginBox", "TextControl", "", curRow, 1, colSpan=2 )
        self.loginBox.ValueModified.connect( self.loginNameChanged )
        self.loginButton = self.AddControlToGrid( "LoginButton", "ButtonControl", "Connect", curRow, 3, expand=False )
        self.loginButton.ValueModified.connect( self.loginButtonPressed )
        self.loginButton.setDefault( True ) #Start off with the login button as default
        curRow += 1
        
        self.AddControlToGrid( "UserLabel", "LabelControl", "Connected User", curRow, 0, "The user that is currently connected.", expand=False )
        self.AddControlToGrid( "UserBox", "ReadOnlyTextControl", "", curRow, 1, colSpan=3 )
        curRow += 1

        self.AddControlToGrid( "ProjectLabel", "LabelControl", "Project", curRow, 0, "The project for the current task.", expand=False )
        self.projectBox = self.AddComboControlToGrid( "ProjectBox", "ComboControl", "", (), curRow, 1, colSpan=3 )
        self.projectBox.ValueModified.connect( self.selectedProjectChanged )
        curRow += 1

        self.AddControlToGrid( "TaskLabel", "LabelControl", "Task", curRow, 0, "Select a task that is assigned to the current user.", expand=False )
        self.taskBox = self.AddComboControlToGrid( "TaskBox", "ComboControl", "", (), curRow, 1, colSpan=3 )
        self.taskBox.ValueModified.connect( self.selectedTaskChanged )
        #self.AddControlToGrid( "NewTaskButton", "ButtonControl", "+", 20, controlHeight, "Click to add a new task for the current user." )
        curRow += 1
        
        self.AddControlToGrid( "AssetLabel", "LabelControl", "Asset", curRow, 0, "Select an Asset for which a new Version will be created.", expand=False )
        #assetBox = self.AddComboControlToGrid( "AssetBox", "ComboControl", "", (), dialogWidth - (labelWidth + padding + 25), controlHeight )
        self.assetBox = self.AddComboControlToGrid( "AssetBox", "ComboControl", "", (), curRow, 1, colSpan=2)
        self.assetBox.ValueModified.connect( self.selectedAssetChanged )
        self.newAssetBtn = self.AddControlToGrid( "NewAssetButton", "ButtonControl", "+", curRow, 3, expand=False )
        self.newAssetBtn.setMaximumWidth( 23 )
        self.newAssetBtn.ValueModified.connect( self.newAssetBtnPressed )
        curRow += 1

        #self.AddControlToGrid( "VersionLabel", "LabelControl", "Version Name", labelWidth, controlHeight, "The name to give the new Version." )
        #self.AddControlToGrid( "VersionBox", "TextControl", "", dialogWidth - (labelWidth + padding), controlHeight )

        self.AddControlToGrid( "DescriptionLabel", "LabelControl", "Version Description", curRow, 0, "A comment descrinbing the new Version.", expand=False )
        self.AddControlToGrid( "DescriptionBox", "TextControl", "", curRow, 1, colSpan=3 )
        curRow += 1

        self.AddControlToGrid( "LogLabel", "LabelControl", "FTrack Log:", curRow, 0, expand=False )
        curRow += 1

        self.logBox = self.AddComboControlToGrid( "LogBox", "ListControl", "", (""), curRow, 0, colSpan=4 )
        self.logBox.setSelectionMode( QAbstractItemView.ExtendedSelection )
        curRow += 1

        self.EndGrid()

        self.AddGrid()
        curRow = 0
        
        self.AddRangeControlToGrid( "ProgressBar", "ProgressBarControl", 0, 0, 100, 0, 0, curRow, 0, expand=False )
        self.statusLabel = self.AddControlToGrid( "StatusLabel", "LabelControl", "", curRow, 1 )
        self.statusLabel.setMinimumWidth( 100 )

        curRow += 1
        self.EndGrid()

        #New Asset menu
        self.newAssetMenu = QMenu()

        self.LoadStickySettings( self.getStickyFilename() )
        
        self.defaultProject = self.stickySettings.get( "ProjectDisplayName", None )
        self.defaultTask = self.stickySettings.get( "TaskDisplayName", None )
        self.defaultAsset = self.stickySettings.get( "AssetDisplayName", None )
                
        self.UpdateEnabledStatus()

        #Check logname environment var (should have priority over sticky settings)
        logName = os.environ.get( "LOGNAME", "" )
        ftServer = os.environ.get( "FTRACK_SERVER", "" ) #LOGNAME can also be set by the OS, so check FTRACK_SERVER too to make sure it's the FT Launcher's doing
        if ftServer and logName:
            self.SetValue( "LoginBox", logName )

    def reject( self ):
        parent = self.parent()
        if parent == None:
            QDialog.reject()
        else:
            # The parent dialog is 4 levels up, the levels in-between consist of widgets and tab controls which don't implement reject
            self.window().reject()

    ########################################################################
    ## Utility Functions
    ########################################################################    
    def getStickyFilename( self ):
        settingsDir = ClientUtils.GetUsersSettingsDirectory()

        return os.path.join( settingsDir, str(self.parentAppName) + "FTrackSticky.txt" )
    
    #Updates which controls are enabled based on the UI's current state
    def UpdateEnabledStatus( self ):
        #check which fields are empty -- this will help determine what should be enabled
        connected = (self.ftrackConnection != None and self.currentUser != None)
        projectEmpty = False if self.GetValue( "ProjectBox" ) else True
        taskEmpty = False if self.GetValue( "TaskBox" ) else True
        assetEmpty = False if self.GetValue( "AssetBox" ) else True

        #check if we're currently doing stuff
        finishedWorking = not connected or not self.ftrackConnection.isWorking()

        #login-related stuff
        loginName = self.GetValue( "LoginBox" )
        loginEmpty = False if loginName else True
        loginChanged = False

        if connected:
            loginChanged = (self.currentUser.getUsername() != loginName)

        self.SetEnabled( "LoginLabel", finishedWorking and self.enableUI )
        self.SetEnabled( "LoginBox", finishedWorking and self.enableUI )
        self.SetEnabled( "LoginButton", finishedWorking and not loginEmpty and self.enableUI )

        if connected and not loginChanged:
            self.SetValue( "LoginButton", "Refresh" )
        else:
            self.SetValue( "LoginButton", "Connect" )

        self.SetEnabled( "UserLabel", connected and finishedWorking and self.enableUI )
        self.SetEnabled( "UserBox", connected and finishedWorking and self.enableUI )

        self.SetEnabled( "ProjectLabel", connected and finishedWorking and self.enableUI )
        self.SetEnabled( "ProjectBox", connected and finishedWorking and self.enableUI )

        self.SetEnabled( "TaskLabel", connected and finishedWorking and not projectEmpty and self.enableUI )
        self.SetEnabled( "TaskBox", connected and finishedWorking and not projectEmpty and self.enableUI )
        #self.SetEnabled( "NewTaskButton", connected and finishedWorking and not projectEmpty )

        self.SetEnabled( "AssetLabel", connected and finishedWorking and not taskEmpty and self.enableUI )
        self.SetEnabled( "AssetBox", connected and finishedWorking and not taskEmpty and self.enableUI )
        self.SetEnabled( "NewAssetButton", connected and finishedWorking and not taskEmpty and self.enableUI )

        self.SetEnabled( "DescriptionLabel", connected and finishedWorking and not (projectEmpty or taskEmpty or assetEmpty) and self.enableUI )
        self.SetEnabled( "DescriptionBox", connected and finishedWorking and not (projectEmpty or taskEmpty or assetEmpty) and self.enableUI )

    def writeToLogBox( self, logMessage, suppressNewLine=False ):
        try:
            #Make sure it's a python string! (and not a filthy QString)
            logMessage = unicode( logMessage )
            lines = logMessage.splitlines()

            if not self.logMessages:
                self.logMessages = [""]
            
            for i in range( 0, len(lines) ):
                line = lines[ i ]
                self.logMessages[ -1 ] += line

                #check if we should add a new line or not
                if not suppressNewLine or i < (len( lines ) - 1):
                    self.logMessages.append( "" )

            self.SetItems( "LogBox", tuple( self.logMessages ) )
        except:
            #log box might not be initialized yet, just suppress the exception and write to trace
            ClientUtils.LogText( traceback.format_exc() )

    # FTrack ui updates using 'counter'
    uiUpdateStack = deque() # Use a deque since its pop/append are atomic
    def beginUIUpdate( self ):
        self.uiUpdateStack.append( True ) #doesn't need to be true, just append *something*

    def endUIUpdate( self ):
        self.uiUpdateStack.popleft()

    def isUpdatingUI( self ):
        return len( self.uiUpdateStack ) > 0

    ########################################################################
    ## UI Event Handlers
    ########################################################################
    def loginButtonPressed( self, *args ):
        userName = self.GetValue( "LoginBox" ).strip()

        if userName:
            if self.ftrackConnection == None:
                #if we haven't created a connection object yet do it now
                self.ftrackConnection = FTrackConnection( self.ftrackURL, self.ftrackKey, self.ftrackProxy, userName )
                self.ftrackConnection.userUpdated.connect( self.updateUser )
                self.ftrackConnection.projectsUpdated.connect( self.updateProjects )
                self.ftrackConnection.tasksUpdated.connect( self.updateTasks )
                self.ftrackConnection.assetTypesUpdated.connect( self.updateAssetTypes )
                self.ftrackConnection.assetsUpdated.connect( self.updateAssets )
                self.ftrackConnection.versionsUpdated.connect( self.updateVersions )

                self.ftrackConnection.progressUpdated.connect( self.updateProgress )
                self.ftrackConnection.errorOccurred.connect( self.displayError )
                self.ftrackConnection.logMessage.connect( self.writeToLogBox )
                self.ftrackConnection.workCompleted.connect( self.UpdateEnabledStatus )
            elif self.currentUser:
                #Refreshing or re-connecting, try to maintain current selection
                self.defaultProject = self.GetValue( "ProjectBox" )
                self.defaultTask = self.GetValue( "TaskBox" )
                self.defaultAsset = self.GetValue( "AssetBox" )

            self.currentUser = None
            self.curProjectDict = {}
            self.curTaskDict = {}
            self.curAssetDict = {}

            self.cachedTasks = {}
            self.cachedAssets = {}

            self.SetValue( "UserBox", "" )
            self.SetItems( "ProjectBox", () )
            self.SetItems( "TaskBox", () )
            self.SetItems( "AssetBox", () )

            self.ftrackConnection.connectAsUserAsync( userName )

            self.UpdateEnabledStatus()

    def loginNameChanged( self, *args ):
        self.UpdateEnabledStatus()

    def selectedProjectChanged( self, *args ):
        selectedProjectKey = self.GetValue( "ProjectBox" )

        if selectedProjectKey in self.curProjectDict:
            selectedProject = self.curProjectDict[selectedProjectKey]
            
            cachedTaskList = self.cachedTasks.get( selectedProjectKey, None )
            if cachedTaskList != None:
                #we have these tasks already, just re-use those
                self.updateTasks( cachedTaskList )
            else:
                #we don't have these yet, get them from ftrack
                self.ftrackConnection.getTasksForProjectAsync( selectedProject )
        else:
            self.SetItems( "TaskBox", tuple() )

        self.UpdateEnabledStatus()

    def selectedTaskChanged( self, *args ):
        selectedTaskKey = self.GetValue( "TaskBox" )

        if selectedTaskKey in self.curTaskDict:
            selectedTask = self.curTaskDict[selectedTaskKey]

            cachedAssetList = self.cachedAssets.get( selectedTaskKey, None )
            if cachedAssetList != None:
                #we already have the assets cached, just re-use those
                self.updateAssets( cachedAssetList )
            else:
                #we don't have these yet, get them from ftrack
                self.ftrackConnection.getAssetsForTask( selectedTask )
        else:
            self.SetItems( "AssetBox", tuple() )

        self.UpdateEnabledStatus()

    def newAssetBtnPressed( self, buttonControl ):
        self.newAssetMenu.exec_( buttonControl.mapToGlobal( QPoint( 0, 0 ) ) )

    def selectedAssetChanged( self, *args ):
        selectedAssetKey = self.GetValue( "AssetBox" )

        self.UpdateEnabledStatus()

    def Validate( self ):
    
        connected = (self.ftrackConnection != None and self.currentUser != None)
        projectEmpty = False if self.GetValue( "ProjectBox" ) else True
        taskEmpty = False if self.GetValue( "TaskBox" ) else True
        assetEmpty = False if self.GetValue( "AssetBox" ) else True

        #check if we're currently doing stuff
        finishedWorking = not connected or not self.ftrackConnection.isWorking()

        validationPassed = ( not connected or finishedWorking ) and not (projectEmpty or taskEmpty or assetEmpty)

        if not validationPassed:
            validationMessage = "You must complete this form in order to create a new FTrack Version for this job.\n\nPlease fill in any missing info before proceeding."
            self.ShowMessageBox( validationMessage, "FTrack Form Incomplete" )
            return False
        
        if connected:
            #print out the results of the selection
            projectKey = self.GetValue( "ProjectBox" )
            taskKey = self.GetValue( "TaskBox" )
            assetKey = self.GetValue( "AssetBox" )
            description = self.GetValue( "DescriptionBox" )

            #grab ftrack objects from the cached dictionaries
            project = self.curProjectDict.get( projectKey, None )
            task = self.curTaskDict.get( taskKey, None )
            asset = self.curAssetDict.get( assetKey, None )

            self.settingsDict["FT_ProjectName"] = project.getName()
            self.settingsDict["FT_TaskName"] = task.getName()
            self.settingsDict["FT_AssetName"] = asset.getName()

            self.settingsDict["FT_ProjectId"] = project.getId()
            self.settingsDict["FT_TaskId"] = task.getId()
            self.settingsDict["FT_AssetId"] = asset.getId()

            self.settingsDict["FT_Description"] = description
            self.settingsDict["FT_Username"] = self.currentUser.getUsername()
        else:
            self.settingsDict["FT_ProjectName"] = self.stickySettings["ProjectName"]
            self.settingsDict["FT_TaskName"] = self.stickySettings["TaskName"]
            self.settingsDict["FT_AssetName"] = self.stickySettings["AssetName"]

            self.settingsDict["FT_ProjectId"] = self.stickySettings["ProjectId"]
            self.settingsDict["FT_TaskId"] = self.stickySettings["TaskId"]
            self.settingsDict["FT_AssetId"] = self.stickySettings["AssetId"]

            self.settingsDict["FT_Description"] = self.stickySettings["Description"]
            self.settingsDict["FT_Username"] = self.stickySettings["Username"]
            
        #Save sticky settings
        self.writeToLogBox( "Saving sticky settings... ", True )
        self.SaveStickySettings( self.getStickyFilename() )
        self.writeToLogBox( "done!" )

        self.dataValidated = validationPassed
        
        return validationPassed
    
    def LoadStickySettings( self, fileName ):
        self.stickySettings = {}
        settingsFile = None
        
        try:
            self.writeToLogBox( "Retrieving sticky settings... ", True )
            with io.open( fileName, "r", encoding='utf-8' ) as settingsFile:
                self.stickySettings = json.loads( settingsFile.read() )
        except:
            pass
                
        if len( self.stickySettings ) > 0:
            
            try:
                self.SetValue( "LoginBox", self.stickySettings[ "Username" ] )
                self.SetValue( "UserBox", self.stickySettings[ "UserDisplayName" ] )
            except:
                pass
            
            try:
                project = self.stickySettings[ "ProjectDisplayName" ]
                self.SetItems( "ProjectBox", [ project ] )
                self.SetValue( "ProjectBox", project )
            except:
                pass
            
            try:
                task = self.stickySettings[ "TaskDisplayName" ]
                self.SetItems( "TaskBox", [ task ] )
                self.SetValue( "TaskBox", task )
            except:
                pass
             
            try:
                task = self.stickySettings[ "AssetDisplayName" ]
                self.SetItems( "AssetBox", [ task ] )
                self.SetValue( "AssetBox", task )
            except:
                pass
            
            try:
                self.SetValue( "DescriptionBox", self.stickySettings[ "Description" ] )
            except:
                pass

        self.writeToLogBox( "done!" )
    
    def SaveStickySettings( self, fileName ):
    
        connected = (self.ftrackConnection != None and self.currentUser != None)
        
        #print out the results of the selection
        projectKey = self.GetValue( "ProjectBox" )
        taskKey = self.GetValue( "TaskBox" )
        assetKey = self.GetValue( "AssetBox" )
        description = self.GetValue( "DescriptionBox" )

        #grab ftrack objects from the cached dictionaries
        project = self.curProjectDict.get( projectKey, None )
        task = self.curTaskDict.get( taskKey, None )
        asset = self.curAssetDict.get( assetKey, None )
        
        if connected:
            self.stickySettings = {}
            
            self.stickySettings["ProjectName"] = project.getName()
            self.stickySettings["ProjectDisplayName"] = projectKey
            self.stickySettings["TaskName"] = task.getName()
            self.stickySettings["TaskDisplayName"] = taskKey
            self.stickySettings["AssetName"] = asset.getName()
            self.stickySettings["AssetDisplayName"] = assetKey

            self.stickySettings["ProjectId"] = project.getId()
            self.stickySettings["TaskId"] = task.getId()
            self.stickySettings["AssetId"] = asset.getId()

            self.stickySettings["Description"] = description
            self.stickySettings["Username"] = self.currentUser.getUsername()
            self.stickySettings[ "UserDisplayName" ] = self.currentUser.getName()
            
            
        with io.open( fileName, "w", encoding='utf-8' ) as settingsFile:
            settingsFile.write( json.dumps( self.stickySettings ).decode( 'utf-8' ) )

    def GetSettingsDictionary( self ):
        if not self.dataValidated:
            self.ShowMessageBox( "FTrack data has not been validated.", "Warning" )
        return self.settingsDict

    def CloseConnection( self ):
        if self.ftrackConnection != None:
            self.ftrackConnection.disconnect()

        #invoke parent function to handle closing properly
        super( FTrackDialog, self ).accept()

    ########################################################################
    ## Async callbacks
    ########################################################################
    @pyqtSlot( object )
    def updateUser( self, ftrackUser ):
        #just ignore None value
        if ftrackUser != None:
            #either way, update the displayed name if it's not None
            self.currentUser = ftrackUser
            self.SetValue( "UserBox", ftrackUser.getName() )

            #get projects now!
            self.ftrackConnection.getProjectsForUserAsync( ftrackUser )

            #populate asset types too!
            self.ftrackConnection.getAssetTypesAsync()

        self.UpdateEnabledStatus()

    @pyqtSlot( list )
    def updateProjects( self, projectList ):
        #ignore None value
        if projectList != None:
            newProjDict = {}

            foundDefault = False
            for project in projectList:
                projName = project.getFullName()

                projectKey = projName
                if projName in newProjDict:
                    #In the event we have multiple projects with the same display name, append the ID to stay unique
                    projectKey = "%s [id: %s]" % (projName, project.getId())

                newProjDict[projectKey] = project

                if projectKey == self.defaultProject:
                    foundDefault = True

            comboEntries = sorted( newProjDict.keys() )
            comboEntries.insert( 0, "" ) 
            self.SetItems( "ProjectBox", tuple( comboEntries ) )
            self.curProjectDict = newProjDict

            #automatically select a project if we're defaulting or if there's only one
            default = ""
            if foundDefault:
                default = self.defaultProject
            elif len(comboEntries) == 2:
                default = comboEntries[1]

            if default:
                self.writeToLogBox( "Defaulting to project '%s'" % default ) #don't print this out if we're setting the blank item

            self.SetValue( "ProjectBox", default )
            self.defaultProject = None #reset default

        self.UpdateEnabledStatus()

    @pyqtSlot( list )
    def updateTasks( self, taskList ):
        #ignore None value
        if taskList != None:
            #update cache
            selectedProjKey = self.GetValue( "ProjectBox" )
            self.cachedTasks[ selectedProjKey ] = taskList

            newTaskDict = {}

            foundDefault = False
            for task in taskList:
                pathNames = []
                if 'path' in task.dict:
                    taskPath = task.dict['path'][1:] #strip off the first one, since that's the project
                    pathNames = [x['name'] for x in taskPath]
                else:
                    pathNames = [task.getName()]

                taskKey = " / ".join( pathNames )

                if taskKey in newTaskDict:
                    #already a task with this name, append the key to stay unique
                    taskKey += " [id: %s]" % task.getId()

                newTaskDict[taskKey] = task

                if taskKey == self.defaultTask:
                    foundDefault = True

            comboEntries = sorted( newTaskDict.keys() )
            comboEntries.insert( 0, "" )
            self.SetItems( "TaskBox", tuple( comboEntries ) )
            self.curTaskDict = newTaskDict

            #automatically select a task if we're defaulting or if there's only one (actual) entry
            default = ""
            if foundDefault:
                default = self.defaultTask
            elif len(comboEntries) == 2:
                default = comboEntries[1]

            if default:
                self.writeToLogBox( "Defaulting to task '%s'" % default ) #don't print this out if we're setting the blank item

            self.SetValue( "TaskBox", default )
            self.defaultTask = None #reset default

        self.UpdateEnabledStatus()

    @pyqtSlot( list )
    def updateAssetTypes( self, assetTypeList ):
        if assetTypeList != None:
            if len( assetTypeList ) > 0:
                self.newAssetMenu.clear()

                for assetType in assetTypeList:
                    caption = "New {0}...".format( assetType.getName() )
                    action = QAction( caption, self.newAssetMenu )
                    action.setData( assetType )
                    action.triggered.connect( self.CreateNewAsset )

                    self.newAssetMenu.addAction( action )

    @pyqtSlot( bool )
    def CreateNewAsset( self, checked ):
        action = self.sender()
        if action != None:
            assetType = action.data()

            if assetType != None:
                assetName, ok = QInputDialog.getText( self, "Asset Name", "Name of the {0} Asset to create:".format( assetType.getName() ) )

                if not ok:
                    return

                selectedTaskKey = self.GetValue( "TaskBox" )
                currentTask = self.curTaskDict[selectedTaskKey]

                self.ftrackConnection.createNewAssetAsync( currentTask, assetType.getShort(), assetName )

                self.UpdateEnabledStatus()
            else:
                self.writeToLogBox( "ERROR: Invalid menu item." )

    @pyqtSlot( list )
    def updateAssets( self, assetList ):
        if assetList != None:
            #update cache
            selectedTaskKey = self.GetValue( "TaskBox" )
            self.cachedAssets[ selectedTaskKey ] = assetList

            newAssetDict = {}

            foundDefault = False
            for asset in assetList:
                assetName = asset.getName()

                assetKey = assetName
                if assetKey in newAssetDict:
                    assetKey = "%s [id: %s]" % (assetName, asset.getId())

                newAssetDict[assetKey] = asset

                if assetKey == self.defaultAsset:
                    foundDefault = True

            comboEntries = sorted( newAssetDict.keys() )
            comboEntries.insert( 0, "" )
            self.SetItems( "AssetBox", tuple( comboEntries ) )
            self.curAssetDict = newAssetDict

            #automatically select an asset if we're defaulting or if there's only one (actual) entry
            default = ""
            if foundDefault:
                default = self.defaultAsset
            elif len(comboEntries) == 2:
                default = comboEntries[1]

            if default:
                self.writeToLogBox( "Defaulting to asset '%s'" % default )

            self.SetValue( "AssetBox", default )
            self.defaultAsset = None #reset default

    @pyqtSlot( list )
    def updateVersions( self, versionList ):
        #nothing to do here...
        self.UpdateEnabledStatus()

    @pyqtSlot( int, str )
    def updateProgress( self, progress, statusMessage ):
        self.SetValue( "ProgressBar", progress )
        self.SetValue( "StatusLabel", statusMessage )

    @pyqtSlot( str )
    def displayError( self, errorMessage ):
        dialog = QMessageBox( self )
        dialog.addButton( QMessageBox.Ok )
        dialog.setIcon( QMessageBox.Critical )

        dialog.setText( errorMessage )
        dialog.setWindowTitle( "Error" )

        dialog.exec_()

########################################################################
## FTrack connection layer used to do async work
########################################################################
class FTrackConnection( QObject ):
    URL = None
    APIKey = None
    Proxy = None
    User = None

    canConnect = False

    workerThread = None #Thread used to do actual work in the background
    progressThread = None #Thread for updating the progressbar, in order to look "busy"
    statusThread = None

    errorMessage = ""
    statusMessage = ""

    #Signals used for async calls
    logMessage = pyqtSignal( str, bool ) #Signals that a message should be logged
    progressUpdated = pyqtSignal( int, str ) #Signals that progress should be retrieved, with the current status
    errorOccurred = pyqtSignal( str ) #Signals that an error occurred
    workCompleted = pyqtSignal() #Signals that work has been completed

    userUpdated = pyqtSignal( object ) #Signals that a new user have been retrieved
    projectsUpdated = pyqtSignal( list ) #Signals that new Projects have been retrieved
    tasksUpdated = pyqtSignal( list ) #Signals that new Tasks have been retrieved
    versionsUpdated = pyqtSignal( list ) #Signals that new Tasks have been retrieved
    assetsUpdated = pyqtSignal( list ) #Singlas that new Assets have been retrieved
    assetTypesUpdated = pyqtSignal( list ) #Signals that Asset Types have been retrieved

    workQueue = deque() #a queue of functions to perform asynchronously represented by tuples: (func, (args, ))
    workTimer = None

    def __init__( self, ftrackURL, ftrackKey, ftrackProxy=None, userName=None ):
        super( FTrackConnection, self ).__init__()

        self.URL = ftrackURL
        self.APIKey = ftrackKey
        self.Proxy = ftrackProxy

        if ftrackURL:
            os.environ["FTRACK_SERVER"] = ftrackURL

        if ftrackKey:
            os.environ["FTRACK_APIKEY"] = ftrackKey

        if ftrackProxy:
            os.environ["FTRACK_PROXY"] = ftrackProxy

        if userName != None:
            os.environ["LOGNAME"] = userName
            self.User = userName

        #Add Ftrack event dir to search path
        ftrackPath = Path.Combine( RepositoryUtils.GetAPISyncFolder(), "API" )
        sys.path.append( ftrackPath )

        try:
            import ftrack

            self.canConnect = True
        except:
            #TODO show an appropriate error
            self.canConnect = False

        self.statusThread = threading.Thread( target = self.DoWork )
        self.statusThread.start()

    #Status thread that checks for work, and spins up a worker thread when necessary
    exit = False
    def DoWork( self ):
        try:
            idleCount = 0
            progress = 0
            while not self.exit:
                if len( self.workQueue ) > 0:
                    idleCount = 0

                    #process the first item in the queue
                    func, arguments = self.workQueue.popleft()

                    workerThread = threading.Thread( target = func, args = arguments )
                    workerThread.start()

                    #monitor thread while updating the UI with progress
                    progress = 0
                    while( workerThread.isAlive() and not self.errorMessage ):
                        progress = (progress + 2) % 101
                        dots = "." * (progress / 25)

                        self.progressUpdated.emit( progress, self.statusMessage + dots )
                        time.sleep( 0.05 )

                    #thread exited, or errored
                    if not self.errorMessage:
                        #no error, rejoice!
                        progress = 100
                        self.progressUpdated.emit( progress, "request complete" )
                    else:
                        #there was an error, display it
                        progress = 0
                        self.progressUpdated.emit( progress, "error :(" )

                        self.errorOccurred.emit( self.errorMessage )
                        self.errorMessage = ""

                    self.workCompleted.emit()
                else:
                    time.sleep( 0.1 )
                    idleCount += 1

                    #clear status message after ~2 secs
                    if idleCount == 20:
                        self.progressUpdated.emit( progress, "" )
        except:
            ClientUtils.LogText.WriteLine( traceback.format_exc() )

    #Checks to see if the connection is currently doing work in a worker thread
    def isWorking( self ):
        return (self.workQueue and len(self.workQueue) > 0) or (self.workerThread and self.workerThread.isAlive())

    #Disconnects and cleans up resources
    def disconnect( self ):
        self.workQueue.clear()
        self.errorMessage = ""
        self.statusMessage = ""
        self.exit = True

    def connectAsUserAsync( self, userName ):
        #re-start the status thread if it's no longer around
        if not self.statusThread or not self.statusThread.isAlive():
            self.statusThread = threading.Thread( target = self.DoWork )
            self.statusThread.start()

        #Add this to the queue of operations    
        self.workQueue.append( (self.connectAsUser, (userName, )) )

    #Connect to ftrack and return an ftrack user object
    def connectAsUser( self, userName ):
        newUser = None

        try:
            self.statusMessage = "connecting"

            import ftrack

            try:
                self.changeUser( userName ) #update user

                self.logMessage.emit( "Connecting to FTrack as '%s'... " % userName, True )
                newUser = ftrack.User( userName )

                if newUser != None:
                    self.logMessage.emit( "done!", False )
                else:
                    self.logMessage.emit( "failed.", False )
            except:
                self.errorMessage = "An error occurred while attempting to retrieve user from FTrack.\nSee FTrack log window for more details."
                raise

            if newUser == None:
                self.errorMessage = "Failed to connect to FTrack with the given login name.\nPlease double-check your login and try again."
            else:
                self.userUpdated.emit( newUser )
        except:
            #Make sure we set this to notify other threads that this failed
            if not self.errorMessage:
                self.errorMessage = "An error occurred while connecting to FTrack.\nSee FTrack log window for more details."
                    
            self.logMessage.emit( "UNEXPECTED ERROR:", False )
            self.logMessage.emit( str( sys.exc_info()[0] ), False )
            self.logMessage.emit( str( sys.exc_info()[1] ), False )
            self.logMessage.emit( "---END ERROR INFO---", False )

        return newUser

    def getTasksForUserAsync( self, user ):
        #Add to work queue
        self.workQueue.append( (self.getTasksForUser, (user, )) )

    #Returns a list of tasks for a given ftrack user
    def getTasksForUser( self, user ):
        tasks = []

        try:
            self.statusMessage = "fetching tasks"

            import ftrack

            #check if they provided a string (ie, an ID) instead of an ftrack object
            if isinstance( user, basestring ):
                user = ftrack.User( id=user )
            
            self.logMessage.emit( "Getting Task list for user '%s'... " % user.getUsername(), True )
            tasks = user.getTasks( includePath = True )
            self.logMessage.emit( "done!" % user.getUsername(), False )

            self.tasksUpdated.emit( tasks )
        except:
            #Make sure we set this to notify other threads that this failed
            if not self.errorMessage:
                self.errorMessage = "An error occurred while attempting to collect Tasks from FTrack.\nSee FTrack log window for more details."
            
            self.logMessage.emit( "UNEXPECTED ERROR:", False )
            self.logMessage.emit( str( sys.exc_info()[0] ), False )
            self.logMessage.emit( str( sys.exc_info()[1] ), False )
            self.logMessage.emit( "---END ERROR INFO---", False )

        return tasks


    def getProjectsForUserAsync( self, user ):
        #Add this to the work queue
        self.workQueue.append( (self.getProjectsForUser, (user, )) )

    def getProjectsForUser( self, user ):
        projects = []

        try:
            self.statusMessage = "fetching projects"

            import ftrack

            self.logMessage.emit( "Getting Project list for user '%s'... " % user.getUsername(), True )
            projects = ftrack.getProjects()
            self.logMessage.emit( "done!", False )

            self.projectsUpdated.emit( projects )
        except:
            #Make sure we set this to notify other threads that this failed
            if not self.errorMessage:
                self.errorMessage = "An error occurred while attempting to collect Project Names from FTrack.\nSee FTrack log window for more details."
            
            self.logMessage.emit( "UNEXPECTED ERROR:", False )
            self.logMessage.emit( str( sys.exc_info()[0] ), False )
            self.logMessage.emit( str( sys.exc_info()[1] ), False )
            self.logMessage.emit( "---END ERROR INFO---", False )

        return projects

    def getTasksForProjectAsync( self, project ):
        #Add this to the work queue
        self.workQueue.append( (self.getTasksForProject, (project, )) )

    def getTasksForProject( self, project ):
        tasks = []

        try:
            self.statusMessage = "fetching tasks"

            import ftrack

            #check if they provided an string (ie, an ID) instead of an ftrack object
            if isinstance( project, basestring ):
                project = ftrack.Project( id=project )

            self.logMessage.emit( "Getting Task list for project '%s'... " % project.getName(), True )
            tasks = project.getTasks( includeChildren=True, includePath=True, users=[self.User] )
            self.logMessage.emit( "done!", False )

            self.tasksUpdated.emit(tasks)
        except:
            #Make sure we set this to notify other threads that this failed
            if not self.errorMessage:
                self.errorMessage = "An error occurred while attempting to collect Task Names from FTrack.\nSee FTrack log window for more details."
            
            self.logMessage.emit( "UNEXPECTED ERROR:", False )
            self.logMessage.emit( str( sys.exc_info()[0] ), False )
            self.logMessage.emit( str( sys.exc_info()[1] ), False )
            self.logMessage.emit( "---END ERROR INFO---", False )

        return tasks

    def getAssetTypesAsync( self ):
        #Add this to the work queue
        self.workQueue.append( (self.getAssetTypes, ()) )

    def getAssetTypes( self ):
        assetTypes = []
        try:
            self.statusMessage = "fetching asset types"

            import ftrack

            self.logMessage.emit( "Getting Asset Type list... ", True )
            assetTypes = ftrack.getAssetTypes()
            self.logMessage.emit( "done!", False )

            self.assetTypesUpdated.emit( assetTypes )
        except:
            #Make sure we set this to notify other threads that this failed
            if not self.errorMessage:
                self.errorMessage = "An error occurred while attempting to collect Asset Types from FTrack.\nSee FTrack log window for more details."
            
            self.logMessage.emit( "UNEXPECTED ERROR:", False )
            self.logMessage.emit( str( sys.exc_info()[0] ), False )
            self.logMessage.emit( str( sys.exc_info()[1] ), False )
            self.logMessage.emit( "---END ERROR INFO---", False )

        return assetTypes


    def createNewAssetAsync( self, taskObj, assetType, name ):
        self.workQueue.append( ( self.createNewAsset, ( taskObj, assetType, name, ) ) )

    def createNewAsset( self, task, assetType, name ):
        try:
            self.statusMessage = "creating new asset"

            import ftrack

            self.logMessage.emit( "Creating new {0} Asset named '{1}'... ".format( assetType, name ), True )

            #The tasks we deal with aren't what you actually create the assets in. Need to get the parent
            taskParent = task.getParent()
            taskParent.createAsset( name, assetType )
            self.logMessage.emit( "done!", False )

            #Update the Assets, since they've changed now
            self.getAssetsForTask( task )
        except:
            #Make sure we set this to notify other threads that this failed
            if not self.errorMessage:
                self.errorMessage = "An error occurred while attempting to create new Asset in FTrack.\nSee FTrack log window for more details."
            
            self.logMessage.emit( "UNEXPECTED ERROR:", False )
            self.logMessage.emit( str( sys.exc_info()[0] ), False )
            self.logMessage.emit( str( sys.exc_info()[1] ), False )
            self.logMessage.emit( "---END ERROR INFO---", False )


    def getAssetsForTaskAsync( self, task ):
        #Add this to the work queue
        self.workQueue.append( (self.getAssetsForTask, (task, )) )

    def getAssetsForTask( self, task, getParentAssets=True ):
        assets = []

        try:
            self.statusMessage = "fetching assets"

            import ftrack

            #check if they provided an string (ie, an ID) instead of an ftrack object
            if isinstance( task, basestring ):
                task = ftrack.Task( id=task )

            self.logMessage.emit( "Getting Asset list for task '%s'... " % task.getName(), True )
            try:
                if getParentAssets:
                    task = task.getParent()
            except:
                #probably a root-level task. That's ok, just get the Assets from current one.
                pass

            assets = task.getAssets()
            self.logMessage.emit( "done!", False )

            self.assetsUpdated.emit( assets )
        except:
            #Make sure we set this to notify other threads that this failed
            if not self.errorMessage:
                self.errorMessage = "An error occurred while attempting to collect Assets from FTrack.\nSee FTrack log window for more details."
            
            self.logMessage.emit( "UNEXPECTED ERROR:", False )
            self.logMessage.emit( str( sys.exc_info()[0] ), False )
            self.logMessage.emit( str( sys.exc_info()[1] ), False )
            self.logMessage.emit( "---END ERROR INFO---", False )

        return assets


    def getVersionsForTaskAsync( self, task ):
        #Add this to the work queue
        self.workQueue.append( (self.getVersionsForTask, (task, )) )

    def getVersionsForTask( self, task ):
        versions = []

        try:
            self.statusMessage = "fetching versions"

            import ftrack

            #check if they provided an string (ie, an ID) instead of an ftrack object
            if isinstance( task, basestring ):
                task = ftrack.Task( id=task )

            self.logMessage.emit( "Getting Version list for task '%s'... " % task.getName(), True )
            versions = task.getAssetVersions()
            self.logMessage.emit( "done!", False )

            self.versionsUpdated.emit( versions )
        except:
            #Make sure we set this to notify other threads that this failed
            if not self.errorMessage:
                self.errorMessage = "An error occurred while attempting to collect Version Names from FTrack.\nSee FTrack log window for more details."
            
            self.logMessage.emit( "UNEXPECTED ERROR:", False )
            self.logMessage.emit( str( sys.exc_info()[0] ), False )
            self.logMessage.emit( str( sys.exc_info()[1] ), False )
            self.logMessage.emit( "---END ERROR INFO---", False )

        return versions

    def changeUser( self, userName ):
        if userName != None:
            os.environ["LOGNAME"] = userName
        else:
            os.environ["LOGNAME"] = ""

        self.User = os.environ["LOGNAME"]