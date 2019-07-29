"""
IntegrationUI.py
Integration UI for Monitor Submitters and Integration UI Standalone (used by the Integrated Submitters)
"""

from __future__ import print_function
import os
import sys
import json

from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

class IntegrationDialog( object ):
    ##################################################################################
    ## Functions called from Monitor Submitters and from the Integration UI Standalone
    ##################################################################################
    def __init__( self, parent=None ):
        self.main_dialog = None # Handles to the main dialog (in Monitor Submitter or in Integration UI Standalone)
        self.Draft_dialog = None # Controls the Draft UI
        self.projectManagement_dialogs = None # Dictionary of dialogs that controls project management UIs (one dialog for each supported project management)
        self.fromDraftSubmitter = False # Tracks if the IntegrationUI is added to the Draft Submitter
        self.projectManagementBox = None # Handles to the drop down that selects the project management
        self.parentAppName = ""
        self.stickySettings = ()
    
    """Adds Integration UI components to an existing DeadlineScriptDialog and creates all the global dialogs that will control those components.
    Arguments:
        scriptDialog (DeadlineScriptDialog): The DeadlineScriptDialog the tab(s) will be added to.
        parentAppName (str): The name of the application this function is called from.
        addDraftTab (bool): Determine if a Draft tab needs to be added.
        projectManagements (list): Determine the project managements to be added in the project management tab. If this list is empty, no project management tab will be added.
        fromDraftSubmitter (bool): Determine if the Integration UI will be added to Draft Monitor Submitter (Draft Submitter requires a slightly different UI).
        firstFrameFile (str): Path to the file which has the first rendered frame of this job."""
    def AddIntegrationTabs( self, scriptDialog, parentAppName, addDraftTab, projectManagements, fromDraftSubmitterFlag=False, failOnNoTabs=True, firstFrameFile="" ):
        self.fromDraftSubmitter = fromDraftSubmitterFlag
        self.firstFrameFile = firstFrameFile
        self.parentAppName = parentAppName

        usableProjectManagements = []
        for project in projectManagements:
            config = RepositoryUtils.GetEventPluginConfig( project )
            state = config.GetConfigEntry( "State" )
            if state == "Global Enabled":
                usableProjectManagements.append( project )

        draftEventPluginState = RepositoryUtils.GetEventPluginConfig( "DraftEventPlugin" ).GetConfigEntry( "State" )
        if draftEventPluginState == "Disabled":
            addDraftTab = False

        self.main_dialog = scriptDialog
        addProjectManagementTab = len( usableProjectManagements ) > 0
        
        if not addDraftTab and not addProjectManagementTab and failOnNoTabs:
            self.main_dialog.ShowMessageBox("Please ensure you have Draft or at least one project management event plugin enabled.", "Pipeline Tools Error")
            raise Exception( "ERROR: No Integration tab to add. Please select at least one project management or Draft." )

        dialogWidth = 480
        controlHeight = -1 #20

        if addDraftTab:
            self.Draft_dialog = self.CreateDraftDialog( parentAppName, addPMComponents=addProjectManagementTab, fromDraftSubmitter=self.fromDraftSubmitter, firstFrameFile=self.firstFrameFile )
            self.main_dialog.AddTabPage("Draft")
            self.main_dialog.AddScriptControl( "DraftDialog", self.Draft_dialog, "" )
            self.main_dialog.EndTabPage()

        if addProjectManagementTab:
            self.projectManagement_dialogs = self.CreateProjectManagementDialogs( parentAppName, usableProjectManagements )

            self.main_dialog.AddTabPage( "Project Management" )
            self.main_dialog.AddRow()
            self.main_dialog.AddControl( "Separator", "SeparatorControl", "Project Management Options", dialogWidth + 40, controlHeight )
            self.main_dialog.EndRow()
            self.main_dialog.AddGrid()
            self.main_dialog.AddControlToGrid( "IntegrationProjectManagementOptionsLabel", "LabelControl", "Project Management", 0, 0, "The Project Management that is currently selected.", False )
            self.projectManagementBox = self.main_dialog.AddComboControlToGrid( "ProjectManagementBox", "ComboControl", usableProjectManagements[0], usableProjectManagements, 0, 1, expand=False )
            self.projectManagementBox.ValueModified.connect( self.UpdateProjectManagementTab )
            # No new version is created when in select version mode
            if not self.fromDraftSubmitter:
                self.createVersionBox = self.main_dialog.AddSelectionControlToGrid( "CreateVersionBox", "CheckBoxControl", False, "Create New Version", 0, 2, "If enabled, Deadline will connect to Shotgun/FTrack/Nim and create a new version for this job.", expand=False )
                self.createVersionBox.ValueModified.connect( self.UpdateCreateVersion )
                self.main_dialog.AddHorizontalSpacerToGrid( "HSpacer", 0, 3 )
                self.main_dialog.AddControlToGrid( "IntegrationUploadOptionsLabel", "LabelControl", "Upload Movie", 1, 0, "", False )
                self.main_dialog.AddComboControlToGrid( "IntegrationUploadBox", "ComboControl", "None", [ "None", "Simple", "Draft" ], 1, 1, expand=False )
                self.uploadFilmStripBox = self.main_dialog.AddSelectionControlToGrid( "IntegrationUploadFilmStripBox", "CheckBoxControl", False, "Include Film Strip", 1, 2, "If this option is enabled, a draft job will be created to upload a filmstrip to Shotgun." )
            else:
                self.main_dialog.AddHorizontalSpacerToGrid( "HSpacer", 0, 2 )
                self.main_dialog.AddControlToGrid( "IntegrationUploadOptionsLabel", "LabelControl", "Upload Movie", 1, 0, "", False )
                self.main_dialog.AddComboControlToGrid( "IntegrationUploadBox", "ComboControl", "None", [ "None", "Draft" ], 1, 1, expand=False )
                
            self.main_dialog.EndGrid()

            for project in self.projectManagement_dialogs.keys():
                self.main_dialog.AddScriptControl( project + "Dialog", self.projectManagement_dialogs[project], "" )

            self.main_dialog.EndTabPage()

            self.stickySettings = ( "ProjectManagementBox", "IntegrationUploadBox", "IntegrationUploadFilmStripBox" )
            self.main_dialog.LoadSettings( self.GetSettingsFilename(), self.stickySettings )
            self.main_dialog.EnabledStickySaving( self.stickySettings, self.GetSettingsFilename() )

        self.UpdateProjectManagementTab()

    """Determine if Integration requires processing."""
    def IntegrationProcessingRequested( self ):
        return ( self, self.Draft_dialog and self.Draft_dialog.DraftJobRequested() ) or self.CreateNewVersionRequested() 

    """Determine if Integration requires a batch mode."""
    def IntegrationGroupBatchRequested( self ):
        if self.Draft_dialog and self.Draft_dialog.DraftJobRequested():
            return True
        if self.CreateNewVersionRequested() and self.UploadSimpleMovieRequested() or self.IncludeFilmStrip():
            return True
        return False
    
    def UpdateCreateVersion( self ):
        createVersionEnabled = self.main_dialog.GetValue( "CreateVersionBox" )
        projectManagement = self.main_dialog.GetValue( "ProjectManagementBox" )
        projectManagementSelected = projectManagement != "None"
        draftExists = self.Draft_dialog is not None
        
        self.main_dialog.SetEnabled( "IntegrationUploadOptionsLabel", projectManagementSelected and createVersionEnabled )
        self.main_dialog.SetEnabled( "IntegrationUploadBox", projectManagementSelected and createVersionEnabled )
        self.main_dialog.SetEnabled( "IntegrationUploadFilmStripBox", projectManagementSelected and createVersionEnabled and draftExists and self.main_dialog.GetValue("ProjectManagementBox") == "Shotgun" )
        
        self.projectManagement_dialogs[projectManagement].enableUI = createVersionEnabled
        self.projectManagement_dialogs[projectManagement].UpdateEnabledStatus()
    """Check the sanity of the entire Integration request.
    Arguments:
        outputFile (str):  Draft output file for Draft sanity. Optional. Default to "dummy".
    Returns: A bool indicating if the sanity check is passed or not."""
    def CheckIntegrationSanity( self, outputFile="dummy" ):
        uploadDraftMovie = self.UploadDraftMovieRequested()
        projectManagementSelected = self.projectManagement_dialogs and self.main_dialog.GetValue("ProjectManagementBox") != "None"
        createNewVersion = self.CreateNewVersionRequested()

        if uploadDraftMovie:
            if not self.Draft_dialog or not self.Draft_dialog.DraftJobRequested():
                self.main_dialog.ShowMessageBox( "A Draft movie can only be uploaded if you submit a dependent Draft job.", "Error" )
                return False
            if not projectManagementSelected:
                self.main_dialog.ShowMessageBox( "A Draft movie can only be uploaded if a project management is selected.", "Error" )
                return False
            if not self.fromDraftSubmitter and not createNewVersion:
                self.main_dialog.ShowMessageBox( "A Draft movie can only be uploaded to the selected project management if a new version is created.", "Error" )
                return False
            if not self.Draft_dialog.IsMovieFromFormat( self.Draft_dialog.GetValue( "DraftFormatBox" ) ) and not self.Draft_dialog.GetValue( "DraftCustomRadio" ):
                self.main_dialog.ShowMessageBox( "A Draft movie can only be uploaded if Quick Draft is creating a movie, or you're using Custom Draft.", "Error" )
                return False

        if projectManagementSelected and ( uploadDraftMovie or createNewVersion ):
            if not self.ValidateProjectManagement():
                return False

        if self.Draft_dialog and self.Draft_dialog.DraftJobRequested():
            if not self.Draft_dialog.CheckDraftSanity( outputFile ):
                return False

        self.main_dialog.SaveSettings( self.GetSettingsFilename(), self.stickySettings )

        return True

    """Writes integration info (for Draft and for projects management) to an existing StreamWriter using Deadline ExtraInfoKeyValue format. Assumes CheckIntegrationSanity has been called previously.
    Arguments:
        writer (StreamWriter): Handle to the existing StreamWriter.
        extraKVPIndex (int): The extra KVP Index just before writing the integration info.
    Returns: The extra KVP Index just after writing the integration info."""
    def WriteIntegrationInfo( self, writer, extraKVPIndex ):
        if self.projectManagement_dialogs and self.main_dialog.GetEnabled( "CreateVersionBox" ) and self.main_dialog.GetValue( "CreateVersionBox" ):
            extraKVPIndex = self.WriteProjectManagementInfo( writer, extraKVPIndex )

        if self.Draft_dialog and self.Draft_dialog.GetValue( "DraftSubmitBox" ):
            extraKVPIndex = self.WriteDraftInfo( writer, extraKVPIndex )
        
        return extraKVPIndex

    """Ensure all the project management connections are closed properly."""
    def CloseProjectManagementConnections( self ):
        if self.projectManagement_dialogs:
            for dialog in self.projectManagement_dialogs.values():
                dialog.CloseConnection()

    ##################################################################################
    ## Helper functions 
    ##################################################################################

    def GetSettingsFilename( self ):
        return os.path.join( ClientUtils.GetUsersSettingsDirectory(), self.parentAppName + "IntegrationSettings.ini" )

    """Creates a dialog to control the Draft UI."""
    def CreateDraftDialog( self, parentAppName, addPMComponents, fromDraftSubmitter, firstFrameFile ):
        draftUIPath = RepositoryUtils.GetRepositoryPath( "submission/Draft/Main", True )
        sys.path.append( draftUIPath )
        import DraftUI
    
        self.Draft_dialog = DraftUI.DraftDialog( parentAppName, addPMComponents, fromDraftSubmitter, firstFrameFile=firstFrameFile )
        self.Draft_dialog.AllowResizingDialog( False )
        if addPMComponents:
            self.Draft_dialog.draftPMButton.clicked.connect( self.PopulateCustomDraftFields )
        return self.Draft_dialog

    """Creates a dictionary of dialogs to control project managements UIs. Each dialog controls one project management UI."""
    def CreateProjectManagementDialogs( self, parentAppName, projectManagements ):
        pipelineToolsInfoFile = os.path.join( ClientUtils.GetDeadlineTempPath(), "pipeline_tools_info.json" )
        try:
            with open( pipelineToolsInfoFile, "r" ) as fileHandle:
                pipelineToolsInfo = json.loads( fileHandle.read() )
        except:
            pipelineToolsInfo = {
                "Shotgun": {},
                "NIM": {}
            }
        finally:
            try:
                os.remove( pipelineToolsInfoFile )
            except:
                pass

        self.projectManagement_dialogs = {}
        if "Shotgun" in projectManagements:
            shotgunUIPath = RepositoryUtils.GetEventPluginDirectory("Shotgun")
            sys.path.append( shotgunUIPath )
            import ShotgunUI
            
            self.projectManagement_dialogs["Shotgun"] = ShotgunUI.ShotgunDialog( parentAppName, self.fromDraftSubmitter, shotgunInfo=pipelineToolsInfo["Shotgun"] )
    
        if "FTrack" in projectManagements:
            ftrackUIPath = RepositoryUtils.GetRepositoryPath( "submission/FTrack/Main", True )
            sys.path.append( ftrackUIPath )
            import FTrackUI
            
            self.projectManagement_dialogs["FTrack"] = FTrackUI.FTrackDialog( parentAppName )
            
        if "NIM" in projectManagements:
            nimUIPath = RepositoryUtils.GetEventPluginDirectory("NIM")
            sys.path.append( nimUIPath )
            import NIM_UI
            
            self.projectManagement_dialogs["NIM"] = NIM_UI.NimDialog( parentAppName, nimInfo=pipelineToolsInfo["NIM"] )

        # Ensure each UI will keep the same disposition
        for project in self.projectManagement_dialogs.keys():
            self.projectManagement_dialogs[project].AllowResizingDialog( False )

        return self.projectManagement_dialogs

    """Ensure that the project management UI currently selected only is displayed, if any."""
    def UpdateProjectManagementTab( self ):
        projectManagementTab = self.projectManagement_dialogs != None
        DraftTab = self.Draft_dialog != None
        
        if projectManagementTab:
            for project in self.projectManagement_dialogs.keys():
                self.projectManagement_dialogs[project].hide()

            projectManagement = self.main_dialog.GetValue( "ProjectManagementBox" )
            projectManagementSelected = projectManagement != "None"

            if( projectManagementSelected ):
                self.projectManagement_dialogs[projectManagement].show()
            if not self.fromDraftSubmitter:
                self.main_dialog.SetEnabled( "CreateVersionBox", projectManagementSelected )
                createVersionEnabled = self.main_dialog.GetValue("CreateVersionBox")

                self.main_dialog.SetEnabled( "IntegrationUploadOptionsLabel", projectManagementSelected and createVersionEnabled )
                self.main_dialog.SetEnabled( "IntegrationUploadBox", projectManagementSelected and createVersionEnabled )
                self.main_dialog.SetEnabled( "IntegrationUploadFilmStripBox", projectManagementSelected and ( self.main_dialog.GetValue( "ProjectManagementBox" ) == "Shotgun" ) and createVersionEnabled )
                self.uploadFilmStripBox.setVisible( self.main_dialog.GetValue( "ProjectManagementBox" ) == "Shotgun" )
                if projectManagementSelected:
                    self.projectManagement_dialogs[projectManagement].enableUI = createVersionEnabled
                    self.projectManagement_dialogs[projectManagement].UpdateEnabledStatus()

    """Validate the project management currently selected."""
    def ValidateProjectManagement( self ):
        projectManagement = self.main_dialog.GetValue( "ProjectManagementBox" )
        if( projectManagement != "None" ):
            return self.projectManagement_dialogs[projectManagement].Validate()
        return True

    """Writes project management info to an existing StreamWriter using Deadline ExtraInfoKeyValue format. Assumes CheckIntegrationSanity has been called previously."""
    def WriteProjectManagementInfo( self, writer, extraKVPIndex ):
        uploadSimpleMovie = self.UploadSimpleMovieRequested()
        uploadFilmStrip = self.IncludeFilmStrip()

        projectManagement = self.main_dialog.GetValue("ProjectManagementBox")
        if( projectManagement != "None" ):
            settings = self.projectManagement_dialogs[projectManagement].GetSettingsDictionary()

        if projectManagement == "Shotgun":
            return self.WriteShotgunInfo( writer, settings, extraKVPIndex, uploadSimpleMovie, uploadFilmStrip )
        
        if projectManagement == "FTrack":
            return self.WriteFTrackInfo( writer, settings, extraKVPIndex, uploadSimpleMovie )

        if projectManagement == "NIM":
            return self.WriteNIMInfo( writer, settings, extraKVPIndex, uploadSimpleMovie )

        return extraKVPIndex

    """Writes Shotgun settings to an existing StreamWriter using Deadline ExtraInfoKeyValue format."""
    def WriteShotgunInfo( self, writer, settings, extraKVPIndex, uploadSimpleMovie, uploadFilmStrip ):
        writer.WriteLine( "ExtraInfo0=%s" % settings.get( 'TaskName', "" ) )
        writer.WriteLine( "ExtraInfo1=%s" % settings.get( 'ProjectName', "" ) )
        writer.WriteLine( "ExtraInfo2=%s" % settings.get( 'EntityName', "" ) )
        writer.WriteLine( "ExtraInfo3=%s" % settings.get( 'VersionName', "" ) )
        writer.WriteLine( "ExtraInfo4=%s" % settings.get( 'Description', "" ) )
        writer.WriteLine( "ExtraInfo5=%s" % settings.get( 'UserName', "" ) )

        extraKVPIndex = self.WriteExtraInfoKVPToFile( writer, settings, extraKVPIndex, fromShotgun=True )
      
        if uploadSimpleMovie:
            writer.WriteLine( "ExtraInfoKeyValue%s=Draft_CreateSGMovie=True" % ( extraKVPIndex ) )
            extraKVPIndex += 1
        if uploadFilmStrip:
            writer.WriteLine( "ExtraInfoKeyValue%s=Draft_CreateSGFilmstrip=True" % ( extraKVPIndex ) )
            extraKVPIndex += 1

        # Specific to Draft Submitter
        if self.UploadDraftMovieRequested() and self.fromDraftSubmitter:
            writer.WriteLine( "ExtraInfoKeyValue%s=Mode=UploadMovie" % ( extraKVPIndex ) )
            extraKVPIndex += 1

        return extraKVPIndex

    """Writes FTrack settings to an existing StreamWriter using Deadline ExtraInfoKeyValue format."""
    def WriteFTrackInfo( self, writer, settings, extraKVPIndex, uploadSimpleMovie ):
        writer.WriteLine( "ExtraInfo0=%s" % settings.get('FT_TaskName', "" ) )
        writer.WriteLine( "ExtraInfo1=%s" % settings.get('FT_ProjectName', "" ) )
        writer.WriteLine( "ExtraInfo2=%s" % settings.get( 'FT_AssetName', "" ) )
        writer.WriteLine( "ExtraInfo4=%s" % settings.get( 'FT_Description', "" ) )
        writer.WriteLine( "ExtraInfo5=%s" % settings.get('FT_Username', "" ) )
        
        extraKVPIndex = self.WriteExtraInfoKVPToFile( writer, settings, extraKVPIndex )

        if uploadSimpleMovie:
            writer.WriteLine( "ExtraInfoKeyValue%s=Draft_CreateFTMovie=True" % ( extraKVPIndex ) )
            extraKVPIndex += 1
        return extraKVPIndex

    """Writes NIM settings to an existing StreamWriter using Deadline ExtraInfoKeyValue format."""
    def WriteNIMInfo( self, writer, settings, extraKVPIndex, uploadSimpleMovie ):
        writer.WriteLine( "ExtraInfo0=%s" % settings.get( 'nim_renderName', "" ) )
        writer.WriteLine( "ExtraInfo1=%s" % settings.get( 'nim_jobName', "" ) )
        writer.WriteLine( "ExtraInfo2=%s" % settings.get( 'nim_showName', "" ) )
        writer.WriteLine( "ExtraInfo3=%s" % settings.get( 'nim_shotName', "" ) )
        writer.WriteLine( "ExtraInfo4=%s" % settings.get( 'nim_description', "" ) )
        writer.WriteLine( "ExtraInfo5=%s" % settings.get( 'nim_user', "" ) )
        
        extraKVPIndex = self.WriteExtraInfoKVPToFile( writer, settings, extraKVPIndex )

        if uploadSimpleMovie:
            writer.WriteLine( "ExtraInfoKeyValue%s=Draft_CreateNimMovie=True" % ( extraKVPIndex ) )
            extraKVPIndex += 1

        return extraKVPIndex

    """Writes Draft settings to an existing StreamWriter using Deadline ExtraInfoKeyValue format."""
    def WriteDraftInfo( self, writer, extraKVPIndex ):
        projectManagement = "None"
        createVersion = False
        uploadDraftMovie = False

        if self.projectManagement_dialogs:
            projectManagement = self.main_dialog.GetValue( "ProjectManagementBox" )
            createVersion = self.CreateNewVersionRequested()
            uploadDraftMovie = self.UploadDraftMovieRequested()
        settings = self.Draft_dialog.GetSettingsDictionary( projectManagement, createVersion, uploadDraftMovie )
        return self.WriteExtraInfoKVPToFile( writer, settings, extraKVPIndex )

    """Writes settings to an existing StreamWriter using Deadline ExtraInfoKeyValue format."""
    def WriteExtraInfoKVPToFile( self, writer, settings, extraKVPIndex, fromShotgun=False ):
        for key in settings:
            if not( fromShotgun and key == 'DraftTemplate' ):
                writer.WriteLine( "ExtraInfoKeyValue%d=%s=%s" % ( extraKVPIndex, key, settings[key] ) )
                extraKVPIndex += 1
        return extraKVPIndex

    """Determine if a new version needs to be created for the selected project management"""
    def CreateNewVersionRequested( self ):
        if self.projectManagement_dialogs and not self.fromDraftSubmitter:
            return self.main_dialog.GetEnabled( "CreateVersionBox" ) and self.main_dialog.GetValue( "CreateVersionBox" )
            
        return False

    def UploadSimpleMovieRequested( self ):
        if self.projectManagement_dialogs and not self.fromDraftSubmitter:
            return self.main_dialog.GetEnabled( "IntegrationUploadBox" ) and self.main_dialog.GetValue( "IntegrationUploadBox" ) == "Simple" and not self.fromDraftSubmitter
        return False
    
    """Determine if the Draft movie need to be uploaded to the selected project management"""
    def UploadDraftMovieRequested( self ):
        if self.projectManagement_dialogs:
            return self.main_dialog.GetEnabled( "IntegrationUploadBox" ) and self.main_dialog.GetValue( "IntegrationUploadBox" ) == "Draft"
        return False
    
    def IncludeFilmStrip( self ):
        if self.projectManagement_dialogs and not self.fromDraftSubmitter:
            return self.main_dialog.GetEnabled( "IntegrationUploadFilmStripBox" ) and self.main_dialog.GetValue( "IntegrationUploadFilmStripBox" ) and not self.fromDraftSubmitter
        return False

    """Populate Custom Draft fields with project management info."""
    def PopulateCustomDraftFields( self, projectManagement=None, settingsDict=None ):
        if not projectManagement or not settingsDict:
            try:
                projectManagement = self.main_dialog.GetValue( "ProjectManagementBox" )

                if projectManagement == "None":
                    self.main_dialog.ShowMessageBox( "No Project Management is currently selected", "Project Management Form Incomplete" )
                    return

                if not self.projectManagement_dialogs[projectManagement].Validate():
                    return

                settingsDict = self.projectManagement_dialogs[projectManagement].GetSettingsDictionary()
            except:
                pass

        if settingsDict:
            self.Draft_dialog.PopulateCustomDraftFields( projectManagement, settingsDict )