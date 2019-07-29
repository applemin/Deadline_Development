#Python.NET
from __future__ import print_function

import os
import re
import sys
import traceback

from System.IO import *

from Deadline.Scripting import *
from Deadline.Jobs import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

global scriptDialog
global shotgunPath

def __main__( *args ):
    global shotgunPath
    global scriptDialog

    shotgunPath = RepositoryUtils.GetEventPluginDirectory("Shotgun")
    
    #get a scriptDialog just so we can show any error messages
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetIcon( os.path.join( shotgunPath, "Shotgun.ico" ) )
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    if len(selectedJobs) > 1:
        scriptDialog.ShowMessageBox( "Only one job can be selected at a time.", "Multiple Jobs Selected" )
        return
    
    # Make a call to ShotgunUI.py to get info for the new version
    args = ("-executescript", os.path.join( shotgunPath, "ShotgunUI.py" ), "DeadlineMonitor" )
    output = ClientUtils.ExecuteCommandAndGetOutput( args )
    outputLines = output.splitlines()
    
    shotgunKVPs = {}
    for line in outputLines:
        line = line.strip()
        
        tokens = line.split( '=', 1 )
        
        if len( tokens ) > 1:
            key = tokens[0]
            value = tokens[1]
            
            shotgunKVPs[key] = value
            
    if len( shotgunKVPs ) == 0:
        pass
    else:	
        #we have stuff, do things!
        job = selectedJobs[0]
        
        versionId = CreateShotgunVersion( job, shotgunKVPs )
        
        if versionId == None:
            return
        
        try:
            #update the job to reflect shotgun stuff
            job.SetJobExtraInfoKeyValue( 'VersionId', str(versionId) )
            
            #fill out the Extra Info fields, and delete the KVPs so we don't add these again later
            job.ExtraInfo0 = shotgunKVPs['TaskName']
            del shotgunKVPs['TaskName']
                
            job.ExtraInfo1 = shotgunKVPs['ProjectName']
            del shotgunKVPs['ProjectName']
                
            job.ExtraInfo2 = shotgunKVPs['EntityName']
            del shotgunKVPs['EntityName']
                
            job.ExtraInfo3 = shotgunKVPs['VersionName']
            del shotgunKVPs['VersionName']
                
            job.ExtraInfo4 = shotgunKVPs['Description']
            del shotgunKVPs['Description']
                
            job.ExtraInfo5 = shotgunKVPs['UserName']
            del shotgunKVPs['UserName']
                
            #create the rest of the KVP values
            for key in shotgunKVPs:
                if key != "DraftTemplate":
                    job.SetJobExtraInfoKeyValue( key, shotgunKVPs[key] )
        except:
            scriptDialog.ShowMessageBox( "The Shotgun Version was successfully created, but an error occurred while updating the Deadline Job's Properties.", "Results - Error" )
            ClientUtils.LogText( traceback.format_exc() )
            return
            
        try:
            #save the job
            RepositoryUtils.SaveJob( job )
        except:
            scriptDialog.ShowMessageBox( "The Shotgun Version was successfully created, but an error occurred while saving the updated Job to the Repository.", "Results - Error" )
            ClientUtils.LogText( traceback.format_exc() )
            return
        
        scriptDialog.ShowMessageBox( "Successfully created new Version in Shotgun with ID %s:\n  %s" % (versionId, job.ExtraInfo3 ), "Results - Success" )
    
    
def CreateShotgunVersion( job, shotgunKVPs ):
    global shotgunPath
    global scriptDialog

    try:
        sys.path.append( shotgunPath )
        import ShotgunUtils
        sgConfig = RepositoryUtils.GetEventPluginConfig( "Shotgun" )
    except:
        scriptDialog.ShowMessageBox( "An error occurred while trying to import ShotgunUtils. Check the Monitor console for details.", "Error" )
        ClientUtils.LogText( traceback.format_exc() )
        return None
    
    try:
        # Create the shotgun version
        userName = shotgunKVPs['UserName']
        taskId = int(shotgunKVPs['TaskId'])
        projectId = int(shotgunKVPs['ProjectId'])
        entityId = int(shotgunKVPs['EntityId'])
        entityType = shotgunKVPs['EntityType']
        version = re.sub( '(?i)\$\{jobid\}', job.JobId, shotgunKVPs['VersionName'] ) #swap out the placeholder for the job ID
        version = re.sub( '(?i)\$\{jobname\}', job.JobName, version ) #swap out the placeholder for the job Name
        description = re.sub( '(?i)\$\{jobid\}', job.JobId, shotgunKVPs['Description'] )
        
        frameCount = len(job.JobFramesList)
        frameList = FrameUtils.ToFrameString( job.JobFramesList )
        if len( frameList ) > len( job.FramesList ):
            frameList = job.FramesList
        
        outputPath = ""
        if len( job.JobOutputDirectories ) > 0:
            if len( job.JobOutputFileNames ) > 0:
                outputPath = os.path.join( job.JobOutputDirectories[0], job.JobOutputFileNames[0] )
            else:
                outputPath = job.JobOutputDirectories[0]
        
        # Use ShotgunUtils to replace padding in output path.
        framePaddingCharacter = sgConfig.GetConfigEntryWithDefault( "FramePaddingCharacter", "#" )
        outputPath = ShotgunUtils.ReplacePadding( outputPath, framePaddingCharacter)
        
        ClientUtils.LogText( "Output path: " + outputPath )
    except:
        scriptDialog.ShowMessageBox( "An error occurred while retrieving Shotgun info -- values are either missing or incorrectly formatted.\n\nNo Shotgun Version has been created.", "Results - Error" )
        ClientUtils.LogText( traceback.format_exc() )
        return None
    
    versionId = None
    try:
        # Use ShotgunUtils to create a new Version in Shotgun
        newVersion = ShotgunUtils.AddNewVersion( userName, taskId, projectId, entityId, entityType, version, description, frameList, frameCount, outputPath, shotgunPath, job.JobId )
        versionId = newVersion['id']
    except:
        scriptDialog.ShowMessageBox( "An error occurred while attempting to create a new Version to Shotgun:\n\n" + str(traceback.format_exc()), "Results - Error" )
        ClientUtils.LogText( traceback.format_exc() )
        return None
    
    if job.Status == JobStatus.Completed:
        # If the job is completed, try updating the version with render times
        try:
            avgTime = None
            totalTime = None
            
            # format is 00d 00h 00m 00s
            timePattern = ".*?=(?P<days>\d\d)d\s*(?P<hours>\d\d)h\s*(?P<minutes>\d\d)m\s*(?P<seconds>\d\d)s"
            
            tempStr = ClientUtils.ExecuteCommandAndGetOutput( ("GetJobTaskTotalTime", job.JobId) ).strip( "\r\n" )
            timeParts = re.match( timePattern, tempStr )			
            if ( timeParts != None ):
                #Converts the days, hours, mins into seconds:
                #((days * 24h + hours) * 60m + minutes) * 60s + seconds
                totalTime = ( ( int(timeParts.group('days')) * 24 + int(timeParts.group('hours')) ) * 60 + int(timeParts.group('minutes')) ) * 60 + int(timeParts.group('seconds'))
            
            tempStr = ClientUtils.ExecuteCommandAndGetOutput( ("GetJobTaskAverageTime", job.JobId) ).strip( "\r\n" )				
            timeParts = re.match( timePattern, tempStr)
            if ( timeParts != None ):
                avgTime = ( ( int(timeParts.group('days')) * 24 + int(timeParts.group('hours')) ) * 60 + int(timeParts.group('minutes')) ) * 60 + int(timeParts.group('seconds'))
                
            #Upload times to shotgun
            if ( avgTime != None or totalTime != None ):
                ShotgunUtils.UpdateRenderTimeForVersion( int(versionId), avgTime, totalTime, shotgunPath )
        except:
            #not a huge deal if this fails, the version was still created
            pass
        
        # Now try to get the thumbnail up there if applicable
        try:
            # Upload a thumbnail if necessary.
            thumbnailFrame = sgConfig.GetConfigEntryWithDefault( "ThumbnailFrame", "" )
            if thumbnailFrame != "" and thumbnailFrame != "None":
                frameList = job.JobFramesList
                
                # Figure out which frame to upload.
                frameNum = -1
                if len(frameList) > 1:
                    if thumbnailFrame == 'First Frame' :
                        frameNum = frameList[0]
                    elif thumbnailFrame == 'Last Frame' :
                        frameNum = frameList[-1]
                    elif thumbnailFrame == 'Middle Frame' :
                        frameNum = frameList[len(frameList)/2]
                    else :
                        print( "ERROR: Unknown thumbnail frame option: '" + thumbnailFrame + "'" )
                        return
                else:
                    frameNum = frameList[0]
                
                # Get the output path for the frame.
                outputPath = os.path.join(job.JobOutputDirectories[0], job.JobOutputFileNames[0]).replace("//","/")
                outputPath = RepositoryUtils.CheckPathMapping( outputPath, False )
                outputPath = PathUtils.ToPlatformIndependentPath( outputPath )
                
                # Pad the frame as required.
                paddingRegex = re.compile("[^\\?#]*([\\?#]+).*")
                m = re.match(paddingRegex,outputPath)
                if( m != None):
                    padding = m.group(1)
                    frame = StringUtils.ToZeroPaddedString(frameNum,len(padding),False)
                    outputPath = outputPath.replace( padding, frame )
                
                # Upload the thumbnail to Shotgun.
                ClientUtils.LogText("ShotgunThumbnailUpload: " + outputPath + " (" + str(versionId) + ")" )
                ShotgunUtils.UploadThumbnailToVersion( int(versionId), outputPath, shotgunPath )
        except:
            #Again, not a huge deal if this fails; the version creation was succesful
            pass
        
            
    return versionId
