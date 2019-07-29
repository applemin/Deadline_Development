from __future__ import print_function

import argparse
import getpass
import hashlib
import imp
import os
import random
import string
import sys

from Deadline.Scripting import ClientUtils, RepositoryUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog
from PyQt5.QtCore  import pyqtSlot
from System.IO import StreamWriter

#Loads and initializes the IntegrationUI module, used for creating the integration dialog.
imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

# Loads and initializes the PipelineToolsSettingsWriter module, used for writing pipeline tool settings to a file in the deadline settings folder.
imp.load_source( 'PipelineToolsSettingsWriter', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/PipelineToolsSettingsWriter.py", True ) )
import PipelineToolsSettingsWriter

########################################################################
# Globals
######################################################################## 
main_dialog = None
integration_dialog = None
appName = ""
extraKVPIndex = 0
settingsWriterObj = None
pipelineToolsVersionNumber = 0
pipelineToolSettingsPath = ""

########################################################################
# Main function called by the Integrated Submitter
########################################################################
def __main__( *args ):
    global main_dialog
    global integration_dialog
    global appName
    global extraKVPIndex
    global pipelineToolSettingsPath
    global settingsWriterObj
    global pipelineToolsVersionNumber

    # Parse command line arguments
    arguments = ParseArgs( args )
    pipelineToolsVersionNumber = arguments.version
    # Check to see if user is using Pipeline tools version 2.
    if pipelineToolsVersionNumber == 2:
        # Set variable indicating whether or not to use Draft.
        addDraftTab = arguments.draft
        # Initialize list of project management tools.
        projectManagements = arguments.project_management
        # Initialize remaining global variables.
        appName = arguments.app
        scenePath = arguments.path.replace("\\", "/")
        # Parse file name out of path.
        sceneName = os.path.basename(scenePath)
        sceneName = os.path.splitext(sceneName)[0]
        user = getpass.getuser()

        # Generates a unique key that is used as part of the filename of the specific scenes' pipeline tool settings.
        sceneKey = hashlib.sha256( scenePath.encode('utf-8') ).hexdigest()[:10]

        # Initialize global variable path to where pipeline tool settings are stored.
        pipelineToolSettingsPath = PipelineToolsSettingsWriter.SettingsWriter.GetPathToPipelineToolSettings( appName, user, sceneName, sceneKey )

    else:
        # old way of parsing command line arguments for backwards compatibility.
        projectManagements = []
        addDraftTab = False
        for arg in args:
            if arg == "Shotgun":
                projectManagements.append("Shotgun")
            elif arg == "FTrack":
                projectManagements.append("FTrack")
            elif arg == "NIM":
                projectManagements.append("NIM")
            elif arg == "Draft":
                addDraftTab = True
            elif arg.isdigit():
                extraKVPIndex = int(arg)
            else:
                appName = arg

    # Create main dialog.
    main_dialog = DeadlineScriptDialog()
    # Add project management and Draft dialog.
    main_dialog.AddTabControl( "Tabs", 0, 0 )
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( main_dialog, appName, addDraftTab, projectManagements )
    main_dialog.EndTabControl()

    # Add control buttons.
    main_dialog.AddGrid()
    main_dialog.AddHorizontalSpacerToGrid( "HSpacer", 0, 0 )
    okButton = main_dialog.AddControlToGrid( "OkButton", "ButtonControl", "OK", 0, 1, expand=False )
    okButton.clicked.connect( main_dialog.accept )
    cancelButton = main_dialog.AddControlToGrid( "CancelButton", "ButtonControl", "Cancel", 0, 2, expand=False )
    cancelButton.clicked.connect( main_dialog.reject )
    main_dialog.EndGrid()

    main_dialog.accepted.connect( accepted )
    main_dialog.rejected.connect( rejected )
    
    # Determine window's title.
    windowTitle = "Pipeline Tools"
    if appName:
        windowTitle = appName + " " + windowTitle
    main_dialog.setWindowTitle( windowTitle )
    # Check to see if we are using "New Pipeline Tools", if so initialize settingsWriterObj.
    if pipelineToolsVersionNumber == 2:
        # Initialize settings writer object used for writing settings to settings store and obtaining status message.
        settingsWriterObj = PipelineToolsSettingsWriter.SettingsWriter(integration_dialog, pipelineToolSettingsPath)

    # Show main dialog
    main_dialog.ShowDialog( True )

@pyqtSlot()
def accepted():
    """
    Executes whenever the accepted signal fires. Writes out the pipeline tools settings based on the version of pipeline tools, then closes.
    """
    global integration_dialog
    global appName
    global extraKVPIndex
    global settingsWriterObj
    global pipelineToolsVersionNumber

    if integration_dialog.IntegrationProcessingRequested():
        # Check if Integration options are valid.
        if not integration_dialog.CheckIntegrationSanity():
            return

        if pipelineToolsVersionNumber == 2:
            # Write to the pipeline tool settings file and get the status message of which tools are currently enabled.
            settingsWriterObj.WritePipelineToolSettings()
            SetPipelineToolStatus()
        else:
            # Determine a unique integration settings filename .
            randomKey = ''.join( random.choice( string.digits ) for i in range( 10 ) )
            integrationSettingsPath = os.path.join( ClientUtils.GetDeadlineTempPath(), appName + "IntegrationSettings_" + randomKey + ".txt" )

            # Write the integration settings file.
            writer = StreamWriter( integrationSettingsPath, False )
            extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            writer.Close()

            # Build output for Integrated Submitter.
            ClientUtils.LogText("integrationSettingsPath=%s" % integrationSettingsPath)
            ClientUtils.LogText("extraKVPIndex=%s" % extraKVPIndex)
            ClientUtils.LogText("batchMode=%s" % integration_dialog.IntegrationGroupBatchRequested())

    # Make sure all the project management connections are closed properly.
    integration_dialog.CloseProjectManagementConnections()

@pyqtSlot()
def rejected():
    """
    Fires off any time the dialog closes when it's not being accepted. ie. Alt-F4, ESC, Clicking 'X', right-click close,Hitting the cancel button, etc.
    """
    global pipelineToolsVersionNumber

    if pipelineToolsVersionNumber == 2:
        # Set pipeline tool status message.
        SetPipelineToolStatus()

    # Make sure all the project management connections are closed properly.
    integration_dialog.CloseProjectManagementConnections()

def SetPipelineToolStatus():
    global pipelineToolSettingsPath
    global settingsWriterObj
    # Set pipeline tool status message.
    statusList = settingsWriterObj.GetPipelineToolStatus( pipelineToolSettingsPath )
    if not statusList:
        statusString = "No Pipeline Tools Set"
    else:
        statusString = ', '.join(statusList)
    ClientUtils.LogText(statusString)

# Method for creating parser to parse command lind arguments.
def ParseArgs( args ):
    parser = argparse.ArgumentParser(description="Process command line arguments for IntegrationUIStandAlone call.")
    parser.add_argument("-v", "--version", default=1, type=int,
                        help='Flag used to specify which version of Pipeline Tools to use.')
    parser.add_argument("app", type=str, help='Name of the application.')
    parser.add_argument("-d", "--draft", action='store_true', default=False, help='Flag used to indicate that Draft is being used.')
    parser.add_argument("project_management", nargs="+", type=str, help='List of project management tools being used.')
    parser.add_argument("--path", type=unicode, default=None, action='store', help='Path to the current scene file.')

    args = parser.parse_args(args)

    # If the path was not specified or is an empty string and using version 2, exit with an error
    if args.version == 2 and not args.path:
        parser.error('Missing the "--path" argument, please include the path argument along with the path to the '
                     'current scene file. Example: --path C:\\Path\\To\\Scene')

    return args
