from __future__ import print_function

import argparse
import getpass
import hashlib
import imp
import io
import os
import re

from Deadline.Scripting import ClientUtils, RepositoryUtils
# Load and initialize the PipelineToolsSettingsWriter module, used for retrieving the pipeline tool status message.
imp.load_source( 'PipelineToolsSettingsWriter', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/PipelineToolsSettingsWriter.py", True ) )
import PipelineToolsSettingsWriter
"""This module is used for concatenating pipeline tool settings to a .job file.
 
Functions:
    ConcatenateJob: Concatenates a dictionary to a .job file.
    ParseArgs: Parses the command line arguments.
    isGroupBatch: Determines whether or not to write the 'BatchName' entry to the .job file."""


def __main__( *args ):
    global globalSceneName
    global settingsPath
    global appName

    # Parse command line arguments and store the input.
    arguments = ParseArgs( args )
    appName = arguments.app

    scenePath = arguments.scene_path.replace( "\\", "/" )
    globalSceneName = os.path.basename( scenePath )
    globalSceneName = os.path.splitext( globalSceneName )[0]
    user = getpass.getuser()

    sceneKey = hashlib.sha256( scenePath.encode( 'utf-8' ) ).hexdigest()[:10]

    settingsPath = PipelineToolsSettingsWriter.SettingsWriter.GetPathToPipelineToolSettings( appName, user, globalSceneName, sceneKey )

    # If "--status" flag was set, get status string and log text to the client.
    if arguments.status:
        statusList = PipelineToolsSettingsWriter.SettingsWriter.GetPipelineToolStatus( settingsPath )
        if not statusList:
            statusString = "No Pipeline Tools Set"
        else:
            statusString = ', '.join( statusList )
        ClientUtils.LogText( statusString )
    # If "--write" flag was set, concatenate settings dictionary containing settings to the .job file.
    if arguments.write:
        settings = PipelineToolsSettingsWriter.SettingsWriter.GetSettingsDict( settingsPath )
        ConcatenateJob( settings, arguments.job_path, arguments.batch_name )
        ClientUtils.LogText( "Job Written Successfully" )

def ConcatenateJob( settings, jobPath, batchName ):
    """Concatenates a settings dictionary to the .job file in the format "ExtraInfoKeyValue#=Key=Value."
        Arguments:
        settings (dict): Dictionary containing the pipeline tools settings.
        jobPath (str): Path to the .job file. """
    # Read existing .job file and save contents to a dictionary, allowing us to rewrite the .job file with utf-8-sig encoding, ensuring unicode characters will be handled.
    if os.path.isfile( jobPath ):
        with io.open( jobPath, "r", encoding="utf-8-sig" ) as readJob:
            # Read in all entries to jobDict, splitting at the first occurence of '='.
            jobDict = dict( line.strip().split( '=', 1 ) for line in readJob if line.strip() )

        # Iterate through all key-value pairs in jobDict, adding any 'ExtraInfoKeyValue#' entries to extraInfoKVPDict.
        extraInfoKVPDict = dict( jobDict[key].split( '=', 1 ) for key in jobDict if re.match( r'ExtraInfoKeyValue\d+', key ) )
        # Iterate through jobDict, removing all 'ExtraInfoKeyValue#' entries.
        jobDict = {key: jobDict[key] for key in jobDict if not re.match( r'^ExtraInfoKeyValue\d+', key )}

        # Creates a dictionary from all 'ExtraInfo#' entries in settings.
        settingsExtraInfo = {key: settings[key] for key in settings if re.match( r'^ExtraInfo\d+', key )}

        # Creates a dictionary from all 'ExtraInfoKeyValue#' entries in settings
        settingsExtraInfoKVP = {key: settings[key] for key in settings if not re.match( r'^ExtraInfo\d+', key )}
        # Overwrite any "ExtraInfoKeyValue#" entries from the .job that have the same key as entries from settingsExtraInfoKVP
        extraInfoKVPDict.update( settingsExtraInfoKVP )

        # Add ExtraInfoKeyValue entries to jobDict in the correct format.
        for index, key in enumerate(extraInfoKVPDict):
            jobDict[u"ExtraInfoKeyValue%d" % index] = unicode(key) + u"=" + unicode(extraInfoKVPDict[key])

        # Update jobDict with all "ExtraInfo#" entries from settings
        jobDict.update( settingsExtraInfo )

        # Check if job needs to be group batched, if so, set BatchName KVP.
        if batchName and isGroupBatch( extraInfoKVPDict ):
            jobDict["BatchName"] = batchName

        # Write jobDict to the .job file in the correct format.
        with io.open( jobPath, "w", encoding="utf-8-sig" ) as writeJob:
            for key, value in jobDict.iteritems():
                writeJob.write( unicode( key ) + u"=" + unicode( value )+ "\n" )

def ParseArgs( args ):
    """Method for creating a Parser that parses command line arguments."""
    parser = argparse.ArgumentParser(description="Concatenate a dictionary to a .job file")
    parser.add_argument("app", help='Name of the application being used.')
    parser.add_argument("--write", action='store_true',
                        help='Flag indicating that we are concatenating a dictionary to the .job file.')
    parser.add_argument("--status", action='store_true',
                        help='Flag indicating that we want to return the status of which pipeline tools are enabled.')
    parser.add_argument("-jp", "--job-path", action="store", type=unicode, help='Path to .job file.')
    parser.add_argument("-sp", "--scene-path", action="store", type=unicode, required=True, help='Path to the current scene file.')
    parser.add_argument("-bn", "--batch-name", action="store", type=unicode, help='The potential batch name if multiple jobs are created and grouped together.')
    parsedArgs = parser.parse_args( args )
    if parsedArgs.write and not parsedArgs.job_path:
        parser.error('Error: Missing the "--job-path" argument, please include the job path argument along with the path to the .job file. Example: --job-path C:/Path/To/Jobfile')
    return parsedArgs

def isGroupBatch( settingsDict ):
    """Method for determining if the job creates multiple jobs, in which case we want to group them together in the deadline monitor."""
    return any(key in settingsDict for key in ["DraftExtension", "DraftUsername", "Draft_CreateSGMovie", "Draft_CreateSGFilmstrip", "Draft_CreateFTMovie", "Draft_CreateNimMovie"])

