from __future__ import print_function

import io
import json
import os
# Module used to check the users event plugin configuration, i.e. Whether or not they have Draft and/or any project management event plugins enabled.
from Deadline.Scripting import RepositoryUtils, ClientUtils

"""Module used to read and write Pipeline Tool Settings.

Classes:
    SettingsWriter: Class that writes Pipeline Tool Settings to the deadline settings directory.
"""


class SettingsWriter(object):
    """Class that writes settings from PipelineToolsUI to the settings directory as a JSON object.
    Constructor Arguments:
        ui (IntegrationDialog): Instance of the integration dialog ui.
        settingsPath (str): Path to the file containing pipeline tool settings.
    """
    toolOptions = {
        "DraftEventPlugin": {
            "Name": "Draft",
            "RequiredOptions": ["DraftExtension", "DraftUsername"]
        },
        "Shotgun": {
            "Name": "Shotgun",
            "RequiredOptions": ["TaskName"]
        },
        "FTrack": {
            "Name": "FTrack",
            "RequiredOptions": ["FT_TaskName"]
        },
        "NIM": {
            "Name": "NIM",
            "RequiredOptions": ["nim_renderName"]
        },
    }
    # Dictionary containing info for each project management tool.
    projectManagementDict = {
        "Shotgun": {
            "ExtraInfo": {
                0: "TaskName",
                1: "ProjectName",
                2: "EntityName",
                3: "VersionName",
                4: "Description",
                5: "UserName"
            },
            "SimpleMovie": "Draft_CreateSGMovie",
            "FilmStrip": "Draft_CreateSGFilmstrip",
            "DraftMovie": "Mode"
        },
        "FTrack": {
            "ExtraInfo": {
                0: "FT_TaskName",
                1: "FT_ProjectName",
                2: "FT_AssetName",
                4: "FT_Description",
                5: "FT_Username"
            },
            "SimpleMovie": "Draft_CreateFTMovie"
        },
        "NIM": {
            "ExtraInfo": {
                0: "nim_renderName",
                1: "nim_jobName",
                2: "nim_showName",
                3: "nim_shotName",
                4: "nim_description",
                5: "nim_user"
            },
            "SimpleMovie": "Draft_CreateNimMovie"
        }
    }

    def __init__( self, ui, settingsPath ):
        self.ui = ui
        self.settingsPath = settingsPath
        # dictionary containing pipeline tool settings.
        self.settingsDict = {}

    def WritePipelineToolSettings( self ):
        """Writes Draft and/or Project management settings to a file in the settings directory."""
        if self.ui.projectManagement_dialogs and self.ui.main_dialog.GetEnabled( "CreateVersionBox" ) and self.ui.main_dialog.GetValue( "CreateVersionBox" ):
            self.GetProjectManagementInfo()

        if self.ui.Draft_dialog and self.ui.Draft_dialog.GetValue( "DraftSubmitBox" ):
            self.GetDraftSettings()

        self.WriteSettingsToFile()

    def GetDraftSettings( self ):
        """Updates instance variable 'settingsDict' to include the dictionary containing all Draft Settings."""
        projectManagement = "None"
        createVersion = False
        uploadDraftMovie = False

        if self.ui.projectManagement_dialogs:
            projectManagement = self.ui.main_dialog.GetValue( "ProjectManagementBox" )
            createVersion = self.ui.CreateNewVersionRequested()
            uploadDraftMovie = self.ui.UploadDraftMovieRequested()
        settings = self.ui.Draft_dialog.GetSettingsDictionary( projectManagement, createVersion, uploadDraftMovie )
        # Update dict instance variable with draft settings
        self.settingsDict.update( settings )

    def GetProjectManagementInfo( self ):
        """Updates instance variable 'settingsDict' to include the dictionary containing all Project Management Settings."""
        uploadSimpleMovie = self.ui.UploadSimpleMovieRequested()
        uploadFilmStrip = self.ui.IncludeFilmStrip()

        projectManagement = self.ui.main_dialog.GetValue( "ProjectManagementBox" )
        if projectManagement != "None":
            settingsFromDialog = self.ui.projectManagement_dialogs[projectManagement].GetSettingsDictionary()
            # Set project management settings
            self.settingsDict.update( settingsFromDialog )

        for projectManagementTool, projectManagementSettings in SettingsWriter.projectManagementDict.iteritems():
            if projectManagement == projectManagementTool:
                for ExtraInfoKey, ExtraInfoValue in projectManagementSettings["ExtraInfo"].iteritems():
                    self.settingsDict["ExtraInfo"+str(ExtraInfoKey)] = self.settingsDict.get(ExtraInfoValue, "")
                if uploadSimpleMovie and "SimpleMovie" in projectManagementSettings:
                    self.settingsDict[projectManagementSettings["SimpleMovie"]] = True
                if uploadFilmStrip and "FilmStrip" in projectManagementSettings:
                    self.settingsDict[projectManagementSettings["FilmStrip"]] = True
                if self.ui.UploadDraftMovieRequested() and self.ui.fromDraftSubmitter and "DraftMovie" in projectManagementSettings:
                    self.settingsDict[projectManagementSettings["DraftMovie"]] = "UploadMovie"

    def WriteSettingsToFile( self ):
        """Writes current dictionary of settings contained in the instance variable 'settingsDict' to a file specified by the settingsPath."""
        # Check if there is an existing pipeline tool settings directory, if not, create one.
        pipelineToolSettingsPath = os.path.dirname(self.settingsPath)
        if not os.path.exists(pipelineToolSettingsPath):
            os.makedirs(pipelineToolSettingsPath)
        with io.open( self.settingsPath, 'w', encoding='utf-8-sig' ) as filePointer:
            filePointer.write(  json.dumps( self.settingsDict ).decode('utf-8') )

    @staticmethod
    def GetSettingsDict( settingsPath ):
        """Method for getting the dictionary of pipeline tool settings for a scene.
            Arguments:
                settingsPath (str): Path to the file containing pipeline tool settings.
        """
        settingsDict = {}
        if os.path.isfile( settingsPath ):
            with io.open( settingsPath, 'r', encoding="utf-8-sig" ) as filePointer:
                settingsDict = json.load( filePointer )
        return settingsDict

    @classmethod
    def GetPipelineToolStatus( cls, settingsPath ):
        """ Method for getting the pipeline tools status, aka which tools are enabled, Ex. Draft, shotgun
            Arguments:
                settingsPath (str): Path to the file containing pipeline tool settings.
        """
        statusDict = SettingsWriter.GetSettingsDict( settingsPath )
        tools = []

        for tool, val in cls.toolOptions.iteritems():
            if RepositoryUtils.GetEventPluginConfig(tool).GetConfigEntryWithDefault("State", "") == "Global Enabled":
                if any( ( option in statusDict ) for option in val["RequiredOptions"] ):
                    tools.append(val["Name"] + " On")
                else:
                    tools.append(val["Name"] + " Off")

        return tools

    @staticmethod
    def GetPathToPipelineToolSettings( appName, user, sceneName, sceneKey ):
        """ Method for generating the path to a scene's pipeline tool settings.
                    Arguments:
                        appName (str): Name of the application being used (Ex. Maya, 3ds Max).
                        user (str): Name of the machines user (Ex. chris)
                        sceneName (str): Name of the current scene.
                        sceneKey (str): 10 character unique key
        """
        return os.path.join(ClientUtils.GetUsersSettingsDirectory(), "pipeline_tools",
                     appName + "_" + user + "_" + sceneName + "_" + sceneKey + ".JSON")