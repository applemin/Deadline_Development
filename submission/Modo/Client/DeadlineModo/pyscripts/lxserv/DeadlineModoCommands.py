import datetime
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from StringIO import StringIO

import DeadlineModoConfig

import lx
import lxifc
import lxu
import lxu.command

try:
    # Importing the TD SDK since it makes finding the files extremely easily.
    # 'modo' was added in Modo 901 so it's not available in all versions we support (7XX, 8XX)
    import modo
except ImportError:
    pass

if not 'deadlineSocket' in globals():
    globals()["deadlineSocket"]=None

global_config = None

deadlineEmptyPassName = " "

formats = {
    'Flexible Precision FLX' : '$FLEX',
    'Targa' : '$Targa',
    'Windows BMP' : 'BMP',
    'High Dynamic Range HDR' : 'HDR',
    'JPEG 2000' : 'JP2',
    'JPEG 2000 16-Bit' : 'JP216',
    'JPEG 2000 16-Bit Lossless' : 'JP216Lossless',
    'JPEG' : 'JPG',
    'PNG' : 'PNG',
    'PNG 16-bit' : 'PNG16',
    'PSD' : 'PSD',
    'SGI RGB' : 'SGI',
    'TIF' : 'TIF',
    '16-Bit TIF' : 'TIF16',
    '16-Bit Uncompr. TIF' : 'TIF16BIG',
    'OpenEXR 16-bit' : 'openexr',
    'OpenEXR 32-bit' : 'openexr_32',
    'OpenEXR Tiled 16-bit' : 'openexr_tiled',
    'OpenEXR Tiled 32-bit' : 'openexr_tiled32',
    'LayeredPSD' : 'LayeredPSD',
    'Layered OpenEXR 16-bit' : 'openexrlayers',
    'Layered OpenEXR 32-bit' : 'openexrlayers32' }

formatTranslator = {
    '$FLEX' : '.flx',
    '$Targa' : '.tga',
    'BMP' : '.BMP',
    'HDR' : '.hdr',
    'JP2' : '.jp2',
    'JP216' : '.jp2',
    'JP216Lossless' : '.jp2',
    'JPG' : '.jpg',
    'PNG' : '.png',
    'PNG16' : '.png',
    'PSD' : '.psd',
    'SGI' : '.SGI',
    'TIF' : '.tif',
    'TIF16' : '.tif',
    'TIF16BIG' : '.tif',
    'openexr' : '.exr',
    'openexr_32' : '.exr',
    'openexr_tiled16' : '.exr',
    'openexr_tiled32' : '.exr',
    'openexrlayers' : '.exr',
    'openexrlayers32' : '.exr',
    'LayeredPSD' : '.psd',
    'PNGs' : '.png',
    'PNGs16' : '.png' }

supportsAssembly = ['$Targa', 'BMP', 'JPG', 'PNG', 'PNG16', 'SGI', 'TIF', 'TIF16', 'TIF16BIG', 'openexr', 
                    'openexr_32', 'openexr_tiled', 'openexr_tiled32', 'openexrlayers', 'openexrlayers32']

assemblyUsesOpaqueOpacity = ['$Targa', 'BMP', 'JPG']

layeredFormats = ["LayeredPSD", "PNGs", "PNGs16" "openexrlayers", "openexrlayers32"]

def get_global_config():
    """
    Gets the global config parser creating it if necessary.  Only 1 parser is created since the config file is only updated when Modo exits
    :return: A Config parser for pulling machine level configuration settings.
    """
    global global_config

    if not global_config:
        configFilePath = lx.eval( 'query platformservice path.path ? configname' )
        global_config = DeadlineModoConfig.Config.fromFile( configFilePath )

    return global_config

# Null strings in modo return (unknown) instead of "", Use this anytime you worry about string values
def CheckEmptyString( userValue ):
    if not ( lx.eval( 'user.value deadlineUnknown ?' ) == lx.eval( 'user.value {%s} ?' % userValue ) or lx.eval( 'user.value {%s} ?' % userValue ) == None ):
        return lx.eval( 'user.value {%s} ?' % userValue )
    else:
        return ""

submissionInfo = ''
# Need to check on load, since the UI can be loaded without calling GetSubmissionInfo
if lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineSubmissionInfo' ) and CheckEmptyString( 'deadlineSubmissionInfo' ) != '':
    submissionInfo = json.loads( lx.eval( 'user.value deadlineSubmissionInfo ?' ) )

homeDir = ''
deadlineTemp = ''

def GetDeadlineCommand():
    deadlineBin = ""
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        #if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass
        
    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if deadlineBin == "" and  os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f:
            deadlineBin = f.read().strip()

    deadlineCommand = os.path.join( deadlineBin, "deadlinecommand" )
    
    return deadlineCommand

# Opens the 'Submit To Deadline' dialog
class DeadlineLaunchUI( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Execute( self, msg, flags ):
        global deadlineTemp, homeDir, submissionInfo
        # Ideally, we'd be check if it was already created, so that we only set pools/group/maxpriority on creation
        # However, I haven't found a good way of implementing that as you can also close this layout with the red 'X'

        # Populate dynamic lists / dynamic ranges
        lx.out( "Grabbing submitter info..." )
        try:
            output = json.loads( CallDeadlineCommand( [ "-prettyJSON", "-GetSubmissionInfo", "Pools", "Groups", "MaxPriority", "TaskLimit", "UserHomeDir", "RepoDir:submission/Modo/Main", "RepoDir:submission/Integration/Main", "RepoDirNoCustom:draft", "RepoDirNoCustom:submission/Jigsaw", ] ) )
        except:
            lx.out( "Unable to get submitter info from Deadline:\n\n" + traceback.format_exc() )
            raise

        if output[ "ok" ]:
            submissionInfo = output[ "result" ]
            lx.eval( 'user.value deadlineSubmissionInfo {%s}' % json.dumps( submissionInfo ) )
        else:
            lx.out( "DeadlineCommand returned a bad result and was unable to grab the submitter info.\n\n" + output[ "result" ] )
            raise Exception( output[ "result" ] )

        homeDir = submissionInfo[ "UserHomeDir" ].strip()
        deadlineTemp = os.path.join( homeDir, "temp" )

        # Attempt to fetch the pipeline tool status
        try:
            statusMessage = GetPipelineToolStatus(raise_on_returncode=True)
        except subprocess.CalledProcessError as e:
            # The subprocess returned a non-zero exit code, indicating some sort of error occurred. We don't want bugs
            # in the pipeline tools to block submission. Handle them gracefully and display an error message in the
            # pipeline status label.
            statusMessage = HandlePipelineToolException(e)

        lx.eval('user.value deadlinePipelineToolStatus "%s"' % statusMessage)

        try:
            SetMaxPriority()
            SetPools()
            SetGroups()

            # Values on create UI
            lx.eval( 'user.value deadlineOverrideOutput false' )
            lx.eval( 'user.value deadlineTileEnable false' )

            # Fill Job name
            jobName = str( lx.eval( 'query sceneservice scene.name ? current' ) )
            lx.eval( 'user.value deadlineJobName {%s}' % jobName )

            # Fill Frame List
            lx.eval( 'select.itemType polyRender' ) # selects render item ( only 1, ever )
            startFrame = lx.eval( 'item.channel first ?' )
            endFrame = lx.eval( 'item.channel last ?' )
            stepFrame = lx.eval( 'item.channel step ?' )

            frameRange = "%s-%s" % ( startFrame, endFrame )
            if stepFrame > 1:
                frameRange = frameRange + "x%s" % stepFrame
            lx.eval( 'user.value deadlineFrameList %s' % frameRange )

            if os.name == 'nt': # windows layout size
                lx.eval( 'layout.createOrClose cookie:DEADLINE layout:DeadlineModoLayout title:"Submit To Deadline" width:400 height:665 style:palette' )
            else: # mac size/linux size?
                lx.eval( 'layout.createOrClose cookie:DEADLINE layout:DeadlineModoLayout title:"Submit To Deadline" width:400 height:575 style:palette' )
        except:
            lx.out( traceback.format_exc() )

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass


##############################################################################################################################################################################
### Job Option Commands
##############################################################################################################################################################################

# Button that retrieves the Machine List from Deadline
class DeadlineGetMachineList( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Execute( self, msg, flags ):
        output = CallDeadlineCommand( ["-SelectMachineList", CheckEmptyString( 'deadlineMachineList' )], False ).strip("\r\n")
        if output != "Action was cancelled by user":
            lx.eval( 'user.value deadlineMachineList "%s"' % output )

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Button that retrieves the Limits from Deadline
class DeadlineGetLimits( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Execute( self, msg, flags ):
        output = CallDeadlineCommand( ["-SelectLimitGroups", CheckEmptyString( 'deadlineLimits' )], False ).strip("\r\n")
        if output != "Action was cancelled by user":
            lx.eval( 'user.value deadlineLimits "%s"' % output )

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Button that retrieves the Dependencies from Deadline
class DeadlineGetDependencies( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Execute( self, msg, flags ):
        output = CallDeadlineCommand( ["-SelectDependencies", CheckEmptyString( 'deadlineDependencies' )], False ).strip("\r\n")
        if output != "Action was cancelled by user":
            lx.eval( 'user.value deadlineDependencies "%s"' % output )

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

class DeadlinePipelineToolStatus( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )
        self.dyna_Add('template', lx.symbol.sTYPE_STRING)  # String attribute
        self.basic_SetFlags(0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_READONLY | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED)  # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Execute(self, msg, flags):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlinePipelineToolStatus {%s}' % self.dyna_String( 0, 'template' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddString( lx.eval( 'user.value deadlinePipelineToolStatus ?' ) )
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineOutputNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Button that opens the Unified Integration window
class DeadlineOpenIntegrationWindow( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Execute( self, msg, flags ):
        global submissionInfo
        pipelineToolUiPath = os.path.join( submissionInfo[ "RepoDirs" ][ "submission/Integration/Main" ].strip(), "IntegrationUIStandAlone.py" )
        scenePath = lx.eval('query sceneservice scene.file ? current')
        argArray = [
            # Run the pipeline tools UI
            "-ExecuteScript", pipelineToolUiPath,
            # with the following args...
            "-v", "2",              # use version 2 of pipeline tools
            "-d",                   # enable the Draft tab
            "modo",                 # indicate the calling application
            "Shotgun", "FTrack",    # project management tools to enable
            "--path", scenePath     # the path to the scene file (used as a key for persistent settings)
        ]

        try:
            statusMessage = CallDeadlineCommand( argArray, False, raise_on_returncode=True )
        except subprocess.CalledProcessError as e:
            # The subprocess returned a non-zero exit code, indicating some sort of error occurred. We don't want bugs
            # in the pipeline tools to block submission. Handle them gracefully and display an error message in the
            # pipeline status label.
            statusMessage = HandlePipelineToolException(e)

        lx.eval('user.value deadlinePipelineToolStatus "%s"' % statusMessage)
        notifier = DeadlineOutputNotifier()
        notifier.Notify(lx.symbol.fCMDNOTIFY_VALUE)

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Button that submits the Deadline job
class DeadlineSubmit( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Execute( self, msg, flags ):
        global assemblyUsesOpaqueOpacity, formatTranslator, submissionInfo
        
        try:
            # Run sanity check script if it exists.
            mainScriptDirectory = submissionInfo[ "RepoDirs" ][ "submission/Modo/Main" ].strip()
            sanityCheckFile = os.path.join( mainScriptDirectory, "CustomSanityChecks.py" )
            if os.path.isfile( sanityCheckFile ):
                if mainScriptDirectory not in sys.path:
                    lx.out( "Appending \"" + mainScriptDirectory + "\" to system path to import CustomSanityChecks module" )
                    sys.path.append( mainScriptDirectory )
                    
                lx.out( "Running sanity check script: " + sanityCheckFile )
                try:
                    import CustomSanityChecks
                    sanityResult = CustomSanityChecks.RunSanityCheck()
                    if not sanityResult:
                        lx.out( "Sanity check returned false, cancelling submission" )
                        return
                except:
                    lx.out( "Could not run CustomSanityChecks.py script" )
                    lx.out( traceback.format_exc() )
            
            sceneFile = lx.eval( 'query sceneservice scene.file ? current' )
            if sceneFile == None:
                errordialog( 'Save Scene', 'Scene must be saved once before it can be submitted to Deadline.' )
                return
            else:
                # save if they changed the scene
                sceneChanged = lx.eval( 'query sceneservice scene.changed ? current' )
                if sceneChanged:
                    if questiondialog( 'Save Scene', 'The scene file has been changed, would you like to save?' ):
                        lx.eval( 'scene.save' )
                        lx.eval( "config.save" )
                    else:
                        return

            try:
                hasBakeItems = ( lx.eval( 'bakeItem.count ?' ) > 0 )
            except:
                hasBakeItems = False

            submitBakeJob = ( lx.eval( 'deadline.bakeItems ?' ) > 0 ) and hasBakeItems
            submitBakeOnly = ( lx.eval( 'deadline.bakeOnly ?' ) > 0 ) and submitBakeJob
            
            submitEachPassGroup = lx.eval( 'user.value deadlineSubmitEachPassGroup ?' )
            tileRendering = lx.eval( 'deadline.tileEnable ?' )
            
            if not submitBakeOnly:
                camera = lx.eval( 'render.camera ?' )
                if camera is None:
                    errordialog( 'Camera cannot be accessed', 'No camera is accessible, please reselect the camera in the render settings.' )
                    return
            
            if not lx.eval( 'user.value deadlineSubmitModoScene ?' ) and IsPathLocal( sceneFile ):
                if not questiondialog( 'Local Scene File', 'The scene file "%s" is local and is not being submitted with the job, are you sure you want to continue?' % sceneFile ):
                    return
            
            if not submitBakeOnly:
                # Check if output is being overwritten.
                overrideOutput =  lx.eval( 'deadline.overrideOutput ?' )
                if overrideOutput:
                    outputFolder = CheckEmptyString( "deadlineOutputFolder" ).strip()
                    outputPrefix = CheckEmptyString( "deadlineOutputPrefix" ).strip()
                    if len(outputFolder) == 0 or len(outputPrefix) == 0:
                        errordialog( 'Override Output', 'When overriding the output, you must specify a folder name and prefix.' )
                        return
                
                # Check if the render outputs are local
                if overrideOutput:
                    outputFolder = CheckEmptyString( "deadlineOutputFolder" ).strip()
                    outputPrefix = CheckEmptyString( "deadlineOutputPrefix" ).strip()
                    outputFile = os.path.join( outputFolder, outputPrefix )
                    if IsPathLocal( outputFile ):
                        if not questiondialog( 'Local Output Files', 'The output folder in the Override Output Options is local, are you sure you want to continue?' ):
                            return
                else:
                    localOutputs = ""
                    
                    outputFilenames = GetOutputFilenames()
                    for outputFile in outputFilenames:
                        if IsPathLocal( outputFile ) and not outputFile == lx.eval( 'user.value deadlineUnknown ?' ):
                            localOutputs += ( "%s\n" % outputFile )
                    
                    if localOutputs != "":
                        if not questiondialog( 'Local Output Files', 'The following output files are local, are you sure you want to continue?\n%s' % localOutputs ):
                            return
                
                 # Check if the Jigsaw panel is open.
                tileUseJigsaw = lx.eval ( 'deadline.tileJigsaw ?' )
                if tileRendering and tileUseJigsaw:
                    try:
                        deadlineSocket.sendall("getrenderregions\n")
                        regionString = recvData(deadlineSocket)
                        
                        if not submitEachPassGroup:
                            regionData = regionString.split("=")
                            if regionData[0] == "renderregion" and len(regionData) >1:
                                regionData = regionData[1]
                                regionData = regionData.split(";")
                                taskLimit = int( submissionInfo.get( "TaskLimit", 5000 ) )
                                if len( regionData ) > taskLimit:
                                    errordialog( "Submission Results", "Unable to submit job with " + str( len( regionData ) ) + " tasks.  Task Count exceeded Job Task Limit of " + str( taskLimit ) )
                                    return
                    except:
                        lx.out(traceback.format_exc())
                        errordialog( "Jigsaw", "The Jigsaw Panel must be open when submitting a Jigsaw job." )
                        deadlineSocket.close()
                        return
                        
                if tileRendering and not tileUseJigsaw and not submitEachPassGroup:
                    tilesInX = lx.eval( 'deadline.tilesInX ?' )
                    tilesInY = lx.eval( 'deadline.tilesInY ?' )
                    tileCount = ( tilesInX * tilesInY )
                    taskLimit = int( submissionInfo.get( "TaskLimit", 5000 ) )
                    if tileCount > taskLimit:
                        errordialog( "Submission Results", "Unable to submit job with " + str( tileCount ) + " tasks.  Task Count exceeded Job Task Limit of " + str( taskLimit ) )
                        return
                
            bakeDependencies = ""
            if submitBakeJob:
                bakeDependencies = self.submit_bake_job()
                       
            if not submitBakeOnly:
                # If submitting each pass as a separate job, need to find all pass groups and submit them.
                if submitEachPassGroup:
                    jobsSubmitted = 0
                    
                    # loop through each item in the scene to see if it is a pass group
                    itemCount = lx.eval( 'query sceneservice item.N ?' )
                    for i in range( itemCount ):
                        
                        # check the item type to see if it is a group
                        itemType =  lx.eval( 'query sceneservice item.type ? %s' % i )
                        if itemType == "group":
                            
                            # it's a group, so get the item ID and name
                            itemID = lx.eval( 'query sceneservice item.id ? %s' % i )
                            itemName =  lx.eval( 'query sceneservice item.name ? %s' % i )
                            
                            # select the current item
                            lx.eval( 'select.item %s' % itemID )
                            
                            # if the current item is equal to the current group, then we know it's a pass group, and we should submit it
                            currentPassGroupID = lx.eval( 'query sceneservice pass.current ? %s' % itemID )
                            if itemID == currentPassGroupID:
                                lx.out( "Submitting job for pass group: %s" % itemName )
                                self.submit_job( False, itemName, dependencyOverride=bakeDependencies )
                                jobsSubmitted = jobsSubmitted + 1
                                
                    infodialog("Pass Group Jobs","Finished submitting %s pass groups as separate jobs. See the Event Log for more information." % jobsSubmitted)
                else:
                    # Just submit the current pass group.
                    self.submit_job( True, dependencyOverride=bakeDependencies )
                    
        except:
            lx.out( traceback.format_exc() )
    
    def submit_bake_job( self ):
        global deadlineTemp, homeDir, submissionInfo
        
        bakeItemCount = lx.eval( 'bakeItem.count ?' )
        sceneFile = lx.eval( 'query sceneservice scene.file ? current' )
        
        # Check basic job options for empty user values
        jobName = CheckEmptyString( "deadlineJobName" ) + " - Bake Job"
        comment = CheckEmptyString( "deadlineComment" )
        department = CheckEmptyString( "deadlineDepartment" )
        limits = CheckEmptyString( "deadlineLimits" )
        machineList = CheckEmptyString( "deadlineMachineList" )
        dependencies = CheckEmptyString( "deadlineDependencies" )

        jobInfoFile = os.path.join( deadlineTemp, "modo_job_info.job" )
        with open( jobInfoFile, "w" ) as fileHandle:
            fileHandle.write( "Plugin=Modo\n" )
            fileHandle.write( "Name=%s\n" % jobName )
            fileHandle.write( "Comment=%s\n" % comment )
            fileHandle.write( "Department=%s\n" % department )
            fileHandle.write( "Pool=%s\n" % lx.eval( 'user.value deadlinePool ?' )[6:] ) # strips off the internal padding name 'pools_'
            fileHandle.write( "SecondaryPool=%s\n" % lx.eval( 'user.value deadlineSecondaryPool ?' )[15:] ) # strips off the internal padding name 'secondaryPools_'
            fileHandle.write( "Group=%s\n" % lx.eval( 'user.value deadlineGroup ?' )[7:] ) # strips off the internal padding name 'groups_'
            fileHandle.write( "Priority=%s\n" % lx.eval( 'user.value deadlinePriority ?' ) )
            fileHandle.write( "TaskTimeoutMinutes=%s\n" % lx.eval( 'user.value deadlineTaskTimeout ?' ) )
            fileHandle.write( "EnableAutoTimeout=%s\n" % lx.eval( 'user.value deadlineAutoTaskTimeout ?' ) )
            fileHandle.write( "ConcurrentTasks=%s\n" % lx.eval( 'user.value deadlineConcurrentTasks ?' ) )
            fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % lx.eval( 'user.value deadlineLimitTasks ?' ) )
            fileHandle.write( "MachineLimit=%s\n" % lx.eval( 'user.value deadlineMachineLimit ?' ) )
            
            if lx.eval( 'user.value deadlineIsBlacklist ?' ):
                fileHandle.write( "Blacklist=%s\n" % machineList )
            else:
                fileHandle.write( "Whitelist=%s\n" % machineList )

            fileHandle.write( "LimitGroups=%s\n" % limits )
            fileHandle.write( "JobDependencies=%s\n" % dependencies )
            fileHandle.write( "OnJobComplete=%s\n" % lx.eval( 'user.value deadlineOnJobComplete ?' ) )

            if lx.eval( 'user.value deadlineSubmitAsSuspended ?' ):
                fileHandle.write( "InitialStatus=Suspended\n" )
            
            fileHandle.write( "Frames=0-%s\n" % ( bakeItemCount - 1) )
            fileHandle.write( "ChunkSize=1\n" )   
            
            writeAWSAssetFiles( fileHandle )
            
            groupBatch = False

            if groupBatch:
                fileHandle.write( "BatchName=%s\n" % jobName )
        
        version = lx.service.Platform().AppVersion() / 100

        # Create plugin file
        pluginInfoFile = os.path.join( deadlineTemp, "modo_plugin_info.job" )
        with open( pluginInfoFile, "w" ) as fileHandle:
            fileHandle.write( "Version=%sxx\n" % version )
            fileHandle.write( "SubmittedFromModo=True\n" )
            fileHandle.write( "ProjectDirectory=%s\n" % str( lx.eval( 'query platformservice path.path ? project' ) )    )

            if not lx.eval( 'user.value deadlineSubmitModoScene ?' ):
                fileHandle.write( "SceneFile=%s\n" % sceneFile )
            else:
                fileHandle.write( "SceneDirectory=%s\n" % os.path.dirname( sceneFile ) )
            
            fileHandle.write( "BakeItems=True\n" )

            write_aliases_to_submisison_file( fileHandle, get_path_aliases() )
            
        # Setup the command line arguments
        arguments = [ jobInfoFile, pluginInfoFile ]
        if lx.eval( 'user.value deadlineSubmitModoScene ?' ):
            arguments.append( sceneFile )

        submitResults = CallDeadlineCommand( arguments )
            
        successfulSubmission = ( submitResults.find( "Result=Success" ) != -1 )
        
        jobId = ""
        if successfulSubmission:
            jobId = GetJobIDFromSubmission( submitResults )
        
        if jobId:
            args = [ "AWSPortalPrecacheJob", jobId ]
            lx.out( CallDeadlineCommand( args ) )
        
        return jobId
    
    def submit_job( self, singleJob=True, passGroup="", dependencyOverride="" ):
        global assemblyUsesOpaqueOpacity, deadlineTemp, formatTranslator, homeDir, submissionInfo

        try:
            vray = lx.eval( 'user.value deadlineRenderWithVRay ?' )
            separator = ""
            if vray:
                separator = "."
        
            sceneFile = lx.eval( 'query sceneservice scene.file ? current' )
            
            tileRendering = lx.eval( 'deadline.tileEnable ?' )
            tileUseJigsaw = lx.eval ( 'deadline.tileJigsaw ?' )
            jigsawRegions = []
            tilesInX = lx.eval( 'deadline.tilesInX ?' )
            tilesInY = lx.eval( 'deadline.tilesInY ?' )
            tileCount = ( tilesInX * tilesInY )
            if singleJob and tileRendering and tileUseJigsaw:
                regionString = ""
                try:
                    deadlineSocket.sendall("getrenderregions\n")
                    
                    regionString = recvData(deadlineSocket)
                except:
                    lx.out(traceback.format_exc())
                    errordialog("Jigsaw","Please make sure the Jigsaw Panel is open.")
                    deadlineSocket.close()
                    return
                    
                regionData = regionString.split("=")
                if regionData[0] == "renderregion" and len(regionData) >1:
                    regionData = regionData[1]
                    regionData = regionData.split(";")
                    for region in regionData:
                        coordinates = region.split(",")
                        if len(coordinates) == 4:
                            jigsawRegions.append(float(coordinates[0]))
                            jigsawRegions.append(float(coordinates[0])+float(coordinates[2]))
                            jigsawRegions.append(float(coordinates[1]))
                            jigsawRegions.append(float(coordinates[1])+float(coordinates[3]))
                tileCount = len(jigsawRegions)/4
                tilesInX = tileCount
                tilesInY = 1

            tileDependent = lx.eval( 'deadline.tileSubmitAssembly ?' )
            tileFrame = lx.eval( 'deadline.tileFrameToRender ?' )
            
            # Get Pass Group name
            if passGroup == "":
                passGroupID = lx.eval( 'query sceneservice pass.current ?' )
                if passGroupID:
                    passGroup = lx.eval( 'query sceneservice pass.name ? %s' % passGroupID )   
            
            passes = GetPasses()
            outputFilenames = {}
            outputNames = {}
            fileFormats = {}
            
            if passGroup == "":
                passes = [deadlineEmptyPassName]
            
            for passName in passes:
                fileNames = GetOutputFilenames(passGroup, passName) 
                names = GetOutputNames(passGroup, passName)
                passFormats = GetFileFormats(passGroup, passName)
                
                outputFilenames[passName] = fileNames
                outputNames[passName] = names
                fileFormats[passName] = passFormats
            
            outputPassCount = 0
            
            for passName in passes:
                outputPassCount += len(outputFilenames[passName])
            
            if outputPassCount == 0:
                if passGroup == "":
                    errordialog( 'No Output Filenames', 'No output filenames found.')
                else:
                    errordialog( 'No Output Filenames', 'No output filenames found for the %s pass group.' % passGroup )
                return
            
            passNames = GetPasses()
            for passName in passNames:
                lx.eval('select.drop channel')
                lx.eval('select.item %s set' % passGroup)
                lx.eval('select.item %s set' % passName)
                lx.eval('layer.active active:off type:-1')

            # Check basic job options for empty user values
            jobName = CheckEmptyString( "deadlineJobName" )
            comment = CheckEmptyString( "deadlineComment" )
            department = CheckEmptyString( "deadlineDepartment" )
            limits = CheckEmptyString( "deadlineLimits" )
            machineList = CheckEmptyString( "deadlineMachineList" )
            dependencies = CheckEmptyString( "deadlineDependencies" )
            if dependencyOverride != "":
                dependencies = dependencyOverride
                
            frameList = CheckEmptyString( "deadlineFrameList" )

            jobInfoFile = os.path.join( deadlineTemp, "modo_job_info.job" )
            fileHandle = open( jobInfoFile, "w" )
            fileHandle.write( "Plugin=Modo\n" )
            fileHandle.write( "Name=%s\n" % jobName )
            fileHandle.write( "Comment=%s\n" % comment )
            fileHandle.write( "Department=%s\n" % department )
            fileHandle.write( "Pool=%s\n" % lx.eval( 'user.value deadlinePool ?' )[6:] ) # strips off the internal padding name 'pools_'
            fileHandle.write( "SecondaryPool=%s\n" % lx.eval( 'user.value deadlineSecondaryPool ?' )[15:] ) # strips off the internal padding name 'secondaryPools_'
            fileHandle.write( "Group=%s\n" % lx.eval( 'user.value deadlineGroup ?' )[7:] ) # strips off the internal padding name 'groups_'
            fileHandle.write( "Priority=%s\n" % lx.eval( 'user.value deadlinePriority ?' ) )
            fileHandle.write( "TaskTimeoutMinutes=%s\n" % lx.eval( 'user.value deadlineTaskTimeout ?' ) )
            fileHandle.write( "EnableAutoTimeout=%s\n" % lx.eval( 'user.value deadlineAutoTaskTimeout ?' ) )
            fileHandle.write( "ConcurrentTasks=%s\n" % lx.eval( 'user.value deadlineConcurrentTasks ?' ) )
            fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % lx.eval( 'user.value deadlineLimitTasks ?' ) )
            fileHandle.write( "MachineLimit=%s\n" % lx.eval( 'user.value deadlineMachineLimit ?' ) )

            fileHandle.write( "ForceReloadPlugin=%s\n" % ( vray & tileRendering ) )
            
            if lx.eval( 'user.value deadlineIsBlacklist ?' ):
                fileHandle.write( "Blacklist=%s\n" % machineList )
            else:
                fileHandle.write( "Whitelist=%s\n" % machineList )

            fileHandle.write( "LimitGroups=%s\n" % limits )
            fileHandle.write( "JobDependencies=%s\n" % dependencies )
            fileHandle.write( "OnJobComplete=%s\n" % lx.eval( 'user.value deadlineOnJobComplete ?' ) )

            if lx.eval( 'user.value deadlineSubmitAsSuspended ?' ):
                fileHandle.write( "InitialStatus=Suspended\n" )

            outputPattern = GetOutputPattern()
            
            stereo = GetStereo()

            frames = re.search( '.*\<(?P<frames>F+)\>.*', outputPattern ) # Gets the <F+> group, and labels it as group
            if frames:
                paddedFrames = frames.group( 'frames' ).replace( 'F', '#' )
                outputPattern = outputPattern.replace( "<" + frames.group( 'frames' ) + ">", paddedFrames ) # Replaces in the outputpattern
            
            if tileRendering:
                fileHandle.write( "TileJob=True\n" )
                fileHandle.write( "TileJobFrame=%s\n" % tileFrame )
                fileHandle.write( "TileJobTilesInX=%s\n" % tilesInX )
                fileHandle.write( "TileJobTilesInY=%s\n" % tilesInY )
                
                if not tileUseJigsaw:
                    currTile = 0
                    for y in range( 0, tilesInY ):
                        for x in range( 0, tilesInX ):
                            tilePrefix = "_tile_%sx%s_%sx%s_" % ( x + 1, y + 1, tilesInX, tilesInY )                        
                            filenum = 0
                            # Loop and write each path
                            for passName in passes:
                                passFilenames = outputFilenames[passName]
                                passFormats = fileFormats[passName]
                                passNames = outputNames[passName]
                                comboName = passName
                                if passName == deadlineEmptyPassName:
                                    comboName = ""
                                
                                combinations = EnumerateLists( [comboName], stereo )
                                for filename, format, outputName in zip( passFilenames, passFormats, passNames ):
                                    for combo in combinations:
                                        if not filename == "":
                                            combo += ",%s" % outputName # Append the renderOutput's name to the combo
                                            evaluatedPattern = EvaluateOutputPattern( outputPattern, combo )
                                            tileFile = filename + tilePrefix + evaluatedPattern + formatTranslator[format]
                                            fileHandle.write( "OutputFilename%sTile%s=%s\n" % ( filenum, currTile, tileFile ) )
                                            filenum += 1
                            
                            currTile += 1
                else:
                    currTile = 0
                    for i in range( 0, len(jigsawRegions)/4 ):                       
                        tilePrefix = "_region_%s_" % currTile
                        
                        filenum = 0
                        # Loop and write each path
                        for passName in passes:
                            passFilenames = outputFilenames[passName]
                            passFormats = fileFormats[passName]
                            passNames = outputNames[passName]
                            comboName = passName
                            if passName == deadlineEmptyPassName:
                                comboName = ""
                            combinations = EnumerateLists( [comboName], stereo )
                            for filename, format, outputName in zip( passFilenames, passFormats, passNames ):
                                for combo in combinations:
                                    if not filename == "":
                                        combo += ",%s" % outputName # Append the renderOutput's name to the combo
                                        evaluatedPattern = EvaluateOutputPattern( outputPattern, combo )
                                        tileFile = filename + tilePrefix + evaluatedPattern + formatTranslator[format]
                                        fileHandle.write( "OutputFilename%sTile%s=%s\n" % ( filenum, currTile, tileFile ) )
                                        filenum += 1

                        currTile += 1
            else:
                fileHandle.write( "Frames=%s\n" % frameList )
                fileHandle.write( "ChunkSize=%s\n" % lx.eval( 'user.value deadlineFramesPerTask ?' ) )
                
                # Evaluate modo's output pattern
                fileIndex = 0
                uniquePaths = []
                for passName in passes:
                    passFilenames = outputFilenames[passName]
                    passFormats = fileFormats[passName]
                    passNames = outputNames[passName]
                    comboName = passName
                    if passName == deadlineEmptyPassName:
                        comboName = ""
                    combinations = EnumerateLists( [comboName], stereo )
                    for filename, format, outputName in zip( passFilenames, passFormats, passNames ):
                        for combo in combinations:
                            if not filename == "":
                                combo += ",%s" % outputName # Append the renderOutput's name to the combo
                                evaluatedPattern = EvaluateOutputPattern( outputPattern, combo )
                                fullPath = filename + evaluatedPattern + formatTranslator[format]
                                
                                if not os.path.isabs( fullPath ):
                                    sceneDir = os.path.dirname( sceneFile )
                                    fullPath = os.path.join( sceneDir, fullPath )
                                
                                if fullPath not in uniquePaths:

                                    uniquePaths.append( fullPath )
                                    fileHandle.write( "OutputFilename%s=%s\n" % ( fileIndex, fullPath ) )
                                    fileIndex += 1
            
            writeAWSAssetFiles( fileHandle )
            # Handle FrameRangeOverride special case
            if lx.eval('deadline.tileEnable ?'):
                tileFrame = lx.eval('deadline.tileFrameToRender ?')
                fileHandle.write(("ExtraInfoKeyValue0=FrameRangeOverride=%s\n" % tileFrame).decode('utf-8'))

            fileHandle.close()

            if not (tileRendering and tileDependent):
                ConcatenatePipelineSettingsToJob( jobInfoFile,jobName )

            version = lx.service.Platform().AppVersion() / 100
            if lx.eval( 'pref.value render.autoThreads ?' ):
                renderThreads = 0
            else:
                renderThreads = lx.eval( 'pref.value render.numThreads ?' )

            # Create plugin file
            pluginInfoFile = os.path.join( deadlineTemp, "modo_plugin_info.job" )
            fileHandle = open( pluginInfoFile, "w" )
            fileHandle.write( "Version=%sxx\n" % version )
            fileHandle.write( "Threads=%s\n" % renderThreads )
            fileHandle.write( "PassGroup=%s\n" % passGroup )
            fileHandle.write( "SubmittedFromModo=True\n" )
            fileHandle.write( "ProjectDirectory=%s\n" % str( lx.eval( 'query platformservice path.path ? project' ) )    )
            
            if lx.eval( 'deadline.overrideOutput ?' ):
                outputFolder = CheckEmptyString( "deadlineOutputFolder" ).strip()
                outputPrefix = CheckEmptyString( "deadlineOutputPrefix" ).strip()
                fileHandle.write( "OutputFilename=%s\n" % os.path.join( outputFolder, outputPrefix ) )
                fileHandle.write( "OutputFormat=%s\n" % formats[CheckEmptyString( 'deadlineOutputFormat' )] )
                fileHandle.write( "OutputPattern=%s\n" % CheckEmptyString( 'deadlineOutputPattern' ) )
            
            if not lx.eval( 'user.value deadlineSubmitModoScene ?' ):
                fileHandle.write( "SceneFile=%s\n" % sceneFile )
            else:
                fileHandle.write( "SceneDirectory=%s\n" % os.path.dirname( sceneFile ) )
            
            fileHandle.write( "VRayRender=%s\n" % vray )

            write_aliases_to_submisison_file( fileHandle, get_path_aliases() )

            if tileRendering:
                if not tileUseJigsaw:
                    xPercentage = 100.0 / tilesInX
                    yPercentage = 100.0 / tilesInY

                    currTile = 0
                    for y in range( 0, tilesInY ):
                        for x in range( 0, tilesInX ):
                            left = float( x ) * xPercentage
                            right = float( x + 1 ) * xPercentage
                            if ( x + 1 ) == tilesInX:
                                right = 100.0

                            top = float( y ) * yPercentage
                            bottom = float( y + 1 ) * yPercentage
                            if ( y + 1 ) == tilesInY:
                                bottom = 100.0

                            tilePrefix = "_tile_%sx%s_%sx%s_" % ( x + 1, y + 1, tilesInX, tilesInY )

                            fileHandle.write( "RegionLeft%s=%s\n" % ( currTile, left ) )
                            fileHandle.write( "RegionRight%s=%s\n" % ( currTile, right ) )
                            fileHandle.write( "RegionTop%s=%s\n" % ( currTile, top ) )
                            fileHandle.write( "RegionBottom%s=%s\n" % ( currTile, bottom ) )
                            
                            filenum = 0
                            # Loop and write each path
                            for passName in passes:
                                for outputNum, outputFilename in enumerate( outputFilenames[passName] ):
                                    if not outputFilename == "":
                                        tileFile = outputFilename + tilePrefix
                                        fileHandle.write( "Output%sRegionFilename%s=%s\n" % ( filenum, currTile, tileFile ) )
                                        filenum += 1

                            currTile += 1

                    
                    fileNum = 0
                    for passName in passes:
                        outputIDs = GetOutputIDs(passGroup, passName)
                        for test, ( outputFilename, outputFormat, renderOutput ) in enumerate( zip( outputFilenames[passName], fileFormats[passName], outputIDs ) ):
                            if not outputFilename == "":
                                fileHandle.write( "OutputFormat%s=%s\n" % ( fileNum, outputFormat ) )
                                fileHandle.write( "RenderOutputID%s=%s\n" % ( fileNum, renderOutput ) )
                                fileNum += 1
                else:               
                    renderWidth = lx.eval("render.res 0 ?")
                    renderHeight = lx.eval("render.res 1 ?")
                    currTile = 0
                    for i in range( 0, len(jigsawRegions)/4 ):
                        left = (float(jigsawRegions[i*4])/renderWidth)*100
                        right = (float(jigsawRegions[i*4+1])/renderWidth)*100
                        top = (float(jigsawRegions[i*4+2])/renderHeight)*100
                        bottom = (float(jigsawRegions[i*4+3])/renderHeight)*100
                        
                        tilePrefix = "_region_%s_" % currTile
                        
                        fileHandle.write( "RegionLeft%s=%s\n" % ( currTile, left ) )
                        fileHandle.write( "RegionRight%s=%s\n" % ( currTile, right ) )
                        fileHandle.write( "RegionTop%s=%s\n" % ( currTile, top ) )
                        fileHandle.write( "RegionBottom%s=%s\n" % ( currTile, bottom ) )
                        
                        # Loop and write each path
                        filenum = 0
                        for passName in passes:
                            for outputNum, outputFilename in enumerate( outputFilenames[passName] ):
                                if not outputFilename == "":
                                    tileFile = outputFilename + tilePrefix
                                    fileHandle.write( "Output%sRegionFilename%s=%s\n" % ( filenum, currTile, tileFile ) )
                                    filenum+=1

                        currTile += 1

                    
                    fileNum = 0
                    for passName in passes:
                        outputIDs = GetOutputIDs(passGroup, passName)
                        for test, ( outputFilename, outputFormat, renderOutput ) in enumerate( zip( outputFilenames[passName], fileFormats[passName], outputIDs ) ):
                            if not outputFilename == "":
                                fileHandle.write( "OutputFormat%s=%s\n" % ( fileNum, outputFormat ) )
                                fileHandle.write( "RenderOutputID%s=%s\n" % ( fileNum, renderOutput ) )
                                fileNum +=1
            else:
                fileNum = 0
                for passName in passes:
                    outputIDs = GetOutputIDs(passGroup, passName)
                    for test, ( outputFilename, outputFormat, renderOutput ) in enumerate( zip( outputFilenames[passName], fileFormats[passName], outputIDs ) ):
                        fileHandle.write( "RenderOutputID%s=%s\n" % ( fileNum, renderOutput ) )
                        fileNum +=1
                
            fileHandle.close()

            currentDateTime = datetime.datetime.now()
            tileJobInfoFile = os.path.join( deadlineTemp, "tile_job_info.job" )
            tilePluginInfoFile = os.path.join( deadlineTemp, "tile_plugin_info.job" )
            directories = [] # no duplicate directories
            fullPaths = [] # no duplicate files

            # Create tile assembly job and plugin info file if necessary
            if tileRendering and tileDependent:
                draftConfigFiles = []
                tileJobInfoFile = os.path.join( deadlineTemp, "draft_tile_job_info.job" )
                tilePluginInfoFile = os.path.join( deadlineTemp, "draft_tile_plugin_info.job" )
                
                fileHandle = open( tileJobInfoFile, "w" )
                fileHandle.write( "Plugin=DraftTileAssembler\n" )
                fileHandle.write( "Name=%s (Frame %s - Draft Tile Assembly Job)\n" % ( jobName, tileFrame ) )
                fileHandle.write( "BatchName=%s\n" % jobName )
                fileHandle.write( "Comment=%s\n" % comment )
                fileHandle.write( "Department=%s\n" % department )
                fileHandle.write( "Pool=%s\n" % lx.eval( 'user.value deadlinePool ?' )[6:] ) # strips off the internal padding name 'pools_'
                fileHandle.write( "SecondaryPool=%s\n" % lx.eval( 'user.value deadlineSecondaryPool ?' )[15:] ) # strips off the internal padding name 'secondaryPools_'
                fileHandle.write( "Group=%s\n" % lx.eval( 'user.value deadlineGroup ?' )[7:] ) # strips off the internal padding name 'groups_'
                fileHandle.write( "Priority=%s\n" % lx.eval( 'user.value deadlinePriority ?' ) )
                fileHandle.write( "OnJobComplete=%s\n" % lx.eval( 'user.value deadlineOnJobComplete ?' ) )
                fileHandle.write( "ChunkSize=1\n" )
                fileHandle.write( "MachineLimit=1\n")

                # Evaluate modo's output pattern
                fileIndex = 0
                uniquePaths = []
                for passName in passes:
                    passFilenames = outputFilenames[passName]
                    passFormats = fileFormats[passName]
                    passNames = outputNames[passName]
                    comboName = passName
                    if passName == deadlineEmptyPassName:
                        comboName = ""
                    combinations = EnumerateLists( [comboName], stereo )
                    for filename, format, outputName in zip( passFilenames, passFormats, passNames ):
                        for combo in combinations:
                            if not filename == "":
                                combo += ",%s" % outputName # Append the renderOutput's name to the combo
                                evaluatedPattern = EvaluateOutputPattern( outputPattern, combo )
                                fullPath = filename + separator + evaluatedPattern + formatTranslator[format]
                                if fullPath not in uniquePaths:
                                    uniquePaths.append( fullPath )
                                    fileHandle.write( "OutputFilename%s=%s\n" % ( fileIndex, fullPath ) )
                                    fileIndex += 1

                # Handle FrameRangeOverride special case
                if lx.eval('deadline.tileEnable ?'):
                    tileFrame = lx.eval('deadline.tileFrameToRender ?')
                    fileHandle.write(("ExtraInfoKeyValue0=FrameRangeOverride=%s\n" % tileFrame).decode('utf-8'))

                fileHandle.close()

                fileHandle = open( tilePluginInfoFile, "w" )
                fileHandle.write( "ErrorOnMissing=%s\n" % lx.eval( 'deadline.tileErrorOnMissing ?' ) )
                fileHandle.write( "CleanupTiles=%s\n" % lx.eval( 'deadline.tileCleanUp ?' ) )
                if not lx.eval('user.value deadlineTileAssembleOver ?') == "Blank Image":
                    if lx.eval('user.value DeadlineTileErrorOnMissingBackground ?'):
                        fileHandle.write( "ErrorOnMissingBackground=True" )
                    else:
                        fileHandle.write( "ErrorOnMissingBackground=False" )
                
                fileHandle.close()
                
                
                configFolder = os.path.join( deadlineTemp, "ModoConfigFiles" )
                if os.path.isdir( configFolder ):
                    shutil.rmtree( configFolder )
                os.makedirs( configFolder )
                    
                # submit one draft config file for each output combination, each assemble is 1 task
                for passName in passes:
                    passFilenames = outputFilenames[passName]
                    passFormats = fileFormats[passName]
                    passNames = outputNames[passName]
                    comboName = passName
                    if passName == deadlineEmptyPassName:
                        comboName = ""
                    combinations = EnumerateLists( [comboName], stereo )
                    for filename, format, outputName in zip( passFilenames, passFormats, passNames ):
                        for combo in combinations:
                            if not filename == "":
                                combo += ",%s" % outputName # Append the renderOutput's name to the combo
                                evaluatedPattern = EvaluateOutputPattern( outputPattern, combo )

                                # Replace frame padding '#' with the frame being tile rendered
                                frames = re.search( '(#+)', evaluatedPattern ) # Gets the <F+> group, and labels it as group
                                if frames:
                                    paddedFrame = frames.group( 0 )
                                    actualFrame = "0" * ( len( paddedFrame ) - len( str( tileFrame ) ) ) + str( tileFrame )
                                    evaluatedPattern = evaluatedPattern.replace( paddedFrame, actualFrame ) # Replaces '#' with the padded tile frame
                                
                                draftConfigFile = os.path.join(configFolder, os.path.split(filename)[1] + separator + evaluatedPattern + "_config_{0:%y}_{0:%m}_{0:%d}_{0:%H}_{0:%M}_{0:%S}.txt".format( currentDateTime ))
                                paddedOutputFile = filename + separator + evaluatedPattern + formatTranslator[format] # join filename, evaluatedPattern and extension

                                # Check if we have renderOutputs going to the same file
                                if paddedOutputFile not in fullPaths:
                                    fullPaths.append( paddedOutputFile )

                                    if os.path.dirname( paddedOutputFile ) not in directories:
                                        directories.append( os.path.dirname( paddedOutputFile ) )

                                    draftConfigFiles.append( draftConfigFile ) # Build up all tile jobs for submission

                                    fileHandle = open( draftConfigFile, "w" )
                                    
                                    fileHandle.write( "\n" )
                                    fileHandle.write( "TileCount=%s\n" % tileCount )
                                    fileHandle.write( "ImageFileName=%s\n" % paddedOutputFile )
                                    fileHandle.write( "ImageWidth=%s\n" % paddedOutputFile )
                                    fileHandle.write( "TilesCropped=False\n" )
                                    fileHandle.write( "DistanceAsPixels=False\n" )
                                    if lx.eval('user.value deadlineTileAssembleOver ?') == "Previous Output":
                                        fileHandle.write( "BackgroundSource=" + paddedOutputFile )
                                    elif lx.eval('user.value deadlineTileAssembleOver ?') == "Selected Image":
                                        fileHandle.write( "BackgroundSource=" + lx.eval( 'user.value deadlineTileBackgroundImage ?' ) )
                                        
                                    currTile = 0
                                    
                                    if not tileUseJigsaw:
                                        for y in range( 0, tilesInY ):
                                            for x in range( 0, tilesInX ):
                                                left = float(  x) * float( xPercentage ) / 100.0
                                                bottom = float( y + 1 ) * float( yPercentage ) / 100.0
                                                if ( y + 1 ) == tilesInY:
                                                    bottom = 1.0

                                                bottom = 1.0 - bottom
                                        
                                                tilePrefix = "_tile_%sx%s_%sx%s_" % ( x + 1, y + 1, tilesInX, tilesInY )
                                                tileFile = filename + tilePrefix + separator + evaluatedPattern + formatTranslator[format]

                                                fileHandle.write( "Tile%sFileName=%s\n" % ( currTile, tileFile ) )
                                                fileHandle.write( "Tile%sX=%f\n" % ( currTile, left ) )
                                                fileHandle.write( "Tile%sY=%f\n" % ( currTile, bottom ) )
                                                fileHandle.write( "Tile%sHeight=%f\n" % ( currTile, yPercentage / 100.0 ) )
                                                fileHandle.write( "Tile%sWidth=%f\n" % ( currTile, xPercentage / 100.0 ) )
                                                currTile = currTile + 1
                                    else:
                                        renderWidth = lx.eval("render.res 0 ?")
                                        renderHeight = lx.eval("render.res 1 ?")
                                        lx.out(str(jigsawRegions))
                                        for i in range(0,len(jigsawRegions)/4 ):
                                            left = float(jigsawRegions[i*4])/renderWidth
                                            width = float(jigsawRegions[i*4+1]-jigsawRegions[i*4])/renderWidth
                                            height = float(jigsawRegions[i*4+3]-jigsawRegions[i*4+2])/renderHeight
                                            bottom = 1-float(jigsawRegions[i*4+2])/renderHeight-height
                                            tilePrefix = "_region_%s_" % currTile
                                            tileFile = filename + tilePrefix + separator + evaluatedPattern + formatTranslator[format]

                                            fileHandle.write( "Tile%sFileName=%s\n" % ( currTile, tileFile ) )
                                            fileHandle.write( "Tile%sX=%f\n" % ( currTile, left ) )
                                            fileHandle.write( "Tile%sY=%f\n" % ( currTile, bottom ) )
                                            fileHandle.write( "Tile%sHeight=%f\n" % ( currTile, height ))
                                            fileHandle.write( "Tile%sWidth=%f\n" % ( currTile, width ))
                                            currTile += 1
                                            

                                    fileHandle.close()
                                    
                                    fileFolder = os.path.dirname(filename)
                                    if os.path.isdir(fileFolder):
                                        destinationFile = filename + separator + evaluatedPattern + "_config_{0:%y}_{0:%m}_{0:%d}_{0:%H}_{0:%M}_{0:%S}.txt".format( currentDateTime )
                                        shutil.copyfile(draftConfigFile, destinationFile)
                                    
                fileHandle = open( tilePluginInfoFile, "a+" ) # Check Unique filepaths
                fileHandle.write( "MultipleConfigFiles=%s\n" % ( "True" if len( fullPaths ) > 1 else "False" ) )
                fileHandle.close()
                
            if len( fullPaths ) > 1:
                frames = ( "-" + str( len( fullPaths ) - 1 ) )
            else:
                frames = ""

            fileHandle = open( tileJobInfoFile, "a+" )
            fileHandle.write( 'Frames=0%s\n' % frames )
            
            for directoryIndex, directory in enumerate( directories ):
                fileHandle.write( 'OutputDirectory%s=%s\n' % ( directoryIndex, directory ) )
            fileHandle.close()

            # Concatenate pipeline tool settings to job info file
            ConcatenatePipelineSettingsToJob(tileJobInfoFile, jobName)
            # Setup the command line arguments
            arguments = []
            #if singleJob:
            #    arguments.append( "Notify" )
            if tileRendering and tileDependent:
                arguments.append( "-multi" )
                arguments.append( "-dependent" )
                arguments.append( "-job" )

            arguments.append( jobInfoFile )
            arguments.append( pluginInfoFile )
            if lx.eval( 'user.value deadlineSubmitModoScene ?' ):
                arguments.append( sceneFile )

            if tileRendering and tileDependent:
                arguments.append( "-job" )
                arguments.append( tileJobInfoFile )
                arguments.append( tilePluginInfoFile )
                for draftConfig in draftConfigFiles:
                    arguments.append( draftConfig )

            submitResults = CallDeadlineCommand( arguments )
            
            jobId = GetJobIDFromSubmission( submitResults )
            if jobId:
                args = [ "AWSPortalPrecacheJob", jobId ]
                lx.out( CallDeadlineCommand( args ) )
            
            if singleJob:
                infodialog( "Submission Results", submitResults )
            else:
                lx.out( "Submission Results:\n%s" % submitResults )
            
        except:
            lx.out( traceback.format_exc() )

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Button that closes the dialog
class DeadlineClose( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Execute( self, msg, flags ):
        lx.out( 'Deadline submission dialog closing' )
        lx.eval( 'layout.closeWindow' )

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass  

# 'Bake Items' checkbox
class DeadlineBakeItems( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'bakeitems', lx.symbol.sTYPE_BOOLEAN ) # Boolean attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable ) flags
        
    def basic_Enable( self, msg ):
        # Certain versions of modo do not have bakeItems installed, so we have to be careful here.
        try:
            return lx.eval( 'bakeItem.count ?' ) > 0
        except:
            return False

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineBakeItems {%s}' % self.dyna_Bool( 0, 'bakeItems' ) )
            notifier = DeadlineBakeNotifier()
            notifier.Notify( lx.symbol.fCMDNOTIFY_DISABLE | lx.symbol.fCMDNOTIFY_VALUE )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineBakeItems ?' ) ) 
        return lx.result.OK

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# 'Bake Only' checkbox
class DeadlineBakeOnly( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'bakeonly', lx.symbol.sTYPE_BOOLEAN ) # Boolean attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable ) flags

    def basic_Enable( self, msg ):
        # Certain versions of modo do not have bakeItems installed, so we have to be careful here.
        try:
            return lx.eval( 'deadline.bakeItems ?') and ( lx.eval( 'bakeItem.count ?' ) > 0 )
        except:
            return False

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineBakeOnly {%s}' % self.dyna_Bool( 0, 'bakeonly' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineBakeOnly ?' ) ) 
        return lx.result.OK

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass
    
    def arg_UIValueHints( self, index ):
        return DeadlineBakeNotifiers()

##############################################################################################################################################################################
### Override Output Commands
##############################################################################################################################################################################

# 'Override Output' checkbox
class DeadlineOutputEnable( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'overrideoutput', lx.symbol.sTYPE_BOOLEAN ) # Boolean attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable ) flags

    def basic_Enable( self, msg ):
        return True

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineOverrideOutput {%s}' % self.dyna_Bool( 0, 'overrideoutput' ) )
            notifier = DeadlineOutputNotifier()
            notifier.Notify( lx.symbol.fCMDNOTIFY_DISABLE | lx.symbol.fCMDNOTIFY_VALUE )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineOverrideOutput ?' ) ) 
        return lx.result.OK

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

        
class DeadlineOutputFolder( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'template', lx.symbol.sTYPE_STRING ) # String attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_READONLY | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.overrideOutput ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineOutputFolder {%s}' % self.dyna_String( 0, 'template' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddString( lx.eval( 'user.value deadlineOutputFolder ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineOutputNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

class DeadlineGetOutputFolder( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.overrideOutput ?' )

    # Uses deadlinecommand to bring up filebrowser as python API 'dialogs' don't work as of 701 sp5
    def basic_Execute( self, msg, flags ):
        directory = CheckEmptyString( 'deadlineOutputFolder' )
        directory = CallDeadlineCommand( ["-SelectDirectory", directory] ).strip()
        
        # Directory is empty if cancelled by user.
        if directory != "":
            lx.eval( 'user.value deadlineOutputFolder {%s}' %  directory )
            notifier = DeadlineOutputNotifier()
            notifier.Notify( lx.symbol.fCMDNOTIFY_VALUE )

    def arg_UIValueHints( self, index ):
        return DeadlineOutputNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

class DeadlineOutputPrefix( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'outputprefix', lx.symbol.sTYPE_STRING ) # String attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.overrideOutput ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineOutputPrefix {%s}' % self.dyna_String( 0, 'outputprefix' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddString( lx.eval( 'user.value deadlineOutputPrefix ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineOutputNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

class DeadlineOutputPattern( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'outputpattern', lx.symbol.sTYPE_STRING ) # String attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.overrideOutput ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineOutputPattern {%s}' % self.dyna_String( 0, 'outputpattern' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddString( lx.eval( 'user.value deadlineOutputPattern ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineOutputNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass
 
class DeadlineOutputFormatPopup(lxu.command.BasicHints, lxifc.UIValueHints):
    def __init__(self, items):
        self._items = items
        self._notifiers = [( 'deadline.outputNotifier', '' )]
 
    def uiv_Flags(self):
        # This can be a series of flags, but in this case we're only returning
        # ''fVALHINT_POPUPS'' to indicate that we just need a straight pop-up
        # List implemented.
        return lx.symbol.fVALHINT_POPUPS
 
    def uiv_PopCount(self):
        # returns the number of items in the list
        return len(self._items[0])
 
    def uiv_PopUserName(self,index):
        # returns the Username of the item at ''index''
        return self._items[0][index]
 
    def uiv_PopInternalName(self,index):
        # returns the internal name of the item at ''index' - this will be the
        # value returned when the custom command is queried
        return self._items[0][index]        
        
class DeadlineOutputFormat( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'outputformat', lx.symbol.sTYPE_STRING ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.overrideOutput ?' )
            
    def arg_UIValueHints(self, index):
        # create an instance of our pop-up list object passing it the
        # list of commands.
        if index == 0:
            return DeadlineOutputFormatPopup([formats.keys()])
 
    def cmd_Execute(self,flags):
        # in the execute method we're going to store the current value of our
        # attribute so that it can be retrieved by the query method later. There's
        # no way to permanently store this information inside the command class
        # itself as the command is created & destroyed between each use. Normally
        # we'd want to be using persistent storage but for simplicity in this
        # example we'll use a UserValue.
        if self.dyna_IsSet(0):
            lx.eval('user.value deadlineOutputFormat {%s}' % self.dyna_String(0))
            notifier = DeadlineOutputNotifier()
            notifier.Notify( lx.symbol.fCMDNOTIFY_DISABLE | lx.symbol.fCMDNOTIFY_VALUE )
 
    def cmd_Query(self,index,vaQuery):
        # In the query method we need to retrieve the value we stored in the execute
        # method and add it to a ValueArray object to be returned by the query.
        va = lx.object.ValueArray()
        # Initialise the ValueArray
        va.set(vaQuery)
        if index == 0:
            # retrieve the value we stored earlier and add it to the ValueArray
            va.AddString(lx.eval('user.value deadlineOutputFormat ?'))
        return lx.result.OK
    
    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass
    
##############################################################################################################################################################################
### Tile Rendering Commands
##############################################################################################################################################################################

# 'Enable Tile Rendering' checkbox
class DeadlineTileEnable( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'tileenable', lx.symbol.sTYPE_BOOLEAN ) # Boolean attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable ) flags

    def basic_Enable( self, msg ):
        return True

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineTileEnable {%s}' % self.dyna_Bool( 0, 'tileenable' ) )
            notifier = DeadlineTileNotifier()
            notifier.Notify( lx.symbol.fCMDNOTIFY_DISABLE | lx.symbol.fCMDNOTIFY_VALUE )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineTileEnable ?' ) ) 
        return lx.result.OK

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# 'Frame To Tile Render' integer
class DeadlineTileFrameRender( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'tileframe', lx.symbol.sTYPE_INTEGER ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineTileFrame {%s}' % self.dyna_Int( 0, 'tileframe' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineTileFrame ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# 'Tiles In X' integer
class DeadlineTilesInX( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'tilesx', lx.symbol.sTYPE_INTEGER ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineTilesInX {%s}' % self.dyna_Int( 0, 'tilesx' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineTilesInX ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# 'Tiles In Y' integer
class DeadlineTilesInY( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'tilesy', lx.symbol.sTYPE_INTEGER ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineTilesInY {%s}' % self.dyna_Int( 0, 'tilesy' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineTilesInY ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# 'Frame To Tile Render' boolean
class DeadlineTileSubmitAssembly( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'tilesubmitassembly', lx.symbol.sTYPE_BOOLEAN ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineTileSubmitAssembly {%s}' % self.dyna_Bool( 0, 'tilesubmitassembly' ) )
            notifier = DeadlineTileNotifier()
            notifier.Notify( lx.symbol.fCMDNOTIFY_DISABLE | lx.symbol.fCMDNOTIFY_VALUE )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineTileSubmitAssembly ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# 'Frame To Tile Render' boolean
class DeadlineTileCleanUp( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'tilecleanup', lx.symbol.sTYPE_BOOLEAN ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' ) and lx.eval( 'deadline.tileSubmitAssembly ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineTileCleanUp {%s}' % self.dyna_Bool( 0, 'tilecleanup' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineTileCleanUp ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# 'Frame To Tile Render' boolean
class DeadlineTileErrorOnMissing( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'tileerror', lx.symbol.sTYPE_BOOLEAN ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' ) and lx.eval( 'deadline.tileSubmitAssembly ?' ) and lx.eval( 'deadline.tileJigsaw ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineTileErrorOnMissing {%s}' % self.dyna_Bool( 0, 'tileerror' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineTileErrorOnMissing ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass


units = [('Blank Image', 'Previous Output', 'Selected Image',)]
 
# The UIValueHints class we'll be using to manage the list and it's items
class AssembleOverPopup(lxu.command.BasicHints, lxifc.UIValueHints):
    def __init__(self, items):
        self._items = items
        self._notifiers = [( 'deadline.tileNotifier', '' )]
 
    def uiv_Flags(self):
        # This can be a series of flags, but in this case we're only returning
        # ''fVALHINT_POPUPS'' to indicate that we just need a straight pop-up
        # List implemented.
        return lx.symbol.fVALHINT_POPUPS
 
    def uiv_PopCount(self):
        # returns the number of items in the list
        return len(self._items[0])
 
    def uiv_PopUserName(self,index):
        # returns the Username of the item at ''index''
        return self._items[0][index]
 
    def uiv_PopInternalName(self,index):
        # returns the internal name of the item at ''index' - this will be the
        # value returned when the custom command is queried
        return self._items[0][index]        
        
# 'Frame To Tile Render' boolean
class DeadlineTileAssembleOver( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'tileassembleover', lx.symbol.sTYPE_STRING ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        #return True
        return lx.eval( 'deadline.tileEnable ?' ) and lx.eval( 'deadline.tileSubmitAssembly ?' ) and lx.eval( 'deadline.tileJigsaw ?' )
            
    def arg_UIValueHints(self, index):
        # create an instance of our pop-up list object passing it the
        # list of commands.
        if index == 0:
            return AssembleOverPopup(units)
 
    def cmd_Execute(self,flags):
        # in the execute method we're going to store the current value of our
        # attribute so that it can be retrieved by the query method later. There's
        # no way to permanently store this information inside the command class
        # itself as the command is created & destroyed between each use. Normally
        # we'd want to be using persistent storage but for simplicity in this
        # example we'll use a UserValue.
        if self.dyna_IsSet(0):
            lx.eval('user.value deadlineTileAssembleOver {%s}' % self.dyna_String(0))
            notifier = DeadlineTileNotifier()
            notifier.Notify( lx.symbol.fCMDNOTIFY_DISABLE | lx.symbol.fCMDNOTIFY_VALUE )
 
    def cmd_Query(self,index,vaQuery):
        # In the query method we need to retrieve the value we stored in the execute
        # method and add it to a ValueArray object to be returned by the query.
        va = lx.object.ValueArray()
        # Initialise the ValueArray
        va.set(vaQuery)
        if index == 0:
            # retrieve the value we stored earlier and add it to the ValueArray
            va.AddString(lx.eval('user.value deadlineTileAssembleOver ?'))
        return lx.result.OK
    
    #def arg_UIValueHints( self, index ):
    #    return DeadlineTileNotifiers()
    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# 'Draft Template' Textbox
class DeadlineTileBackgroundImage( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'template', lx.symbol.sTYPE_STRING ) # String attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_READONLY | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' ) and lx.eval( 'deadline.tileSubmitAssembly ?' ) and lx.eval('user.value deadlineTileAssembleOver ?') == 'Selected Image' and lx.eval( 'deadline.tileJigsaw ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineTileBackgroundImage {%s}' % self.dyna_String( 0, 'template' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddString( lx.eval( 'user.value deadlineTileBackgroundImage ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# '...' Button that retrieves file path of draft template
class DeadlineTileGetBackgroundImage( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' ) and lx.eval( 'deadline.tileSubmitAssembly ?' ) and lx.eval('user.value deadlineTileAssembleOver ?') == 'Selected Image' and lx.eval( 'deadline.tileJigsaw ?' )


    # Uses deadlinecommand to bring up filebrowser as python API 'dialogs' don't work as of 701 sp5
    def basic_Execute( self, msg, flags ):
        fileName = CheckEmptyString( 'deadlineTileBackgroundImage' )
        fileName = CallDeadlineCommand( ["-SelectFilenameLoad", fileName, "All Files(*)"] ).strip()
        
        # File name is empty if cancelled by user.
        if fileName != "":
            lx.eval( 'user.value deadlineTileBackgroundImage {%s}' %  fileName )
            notifier = DeadlineTileNotifier()
            notifier.Notify( lx.symbol.fCMDNOTIFY_VALUE )

    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass
        
# 'Frame To Tile Render' boolean
class DeadlineTileErrorOnMissingBackground( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'tileerrorbackground', lx.symbol.sTYPE_BOOLEAN ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' ) and lx.eval( 'deadline.tileSubmitAssembly ?' ) and not lx.eval('user.value deadlineTileAssembleOver ?') == 'Blank Image' and lx.eval( 'deadline.tileJigsaw ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineTileErrorOnMissingBackground {%s}' % self.dyna_Bool( 0, 'tileerrorbackground' ) )
            

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineTileErrorOnMissingBackground ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass
        
# 'Frame To Tile Render' boolean
class DeadlineTileJigsaw( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'tilejigsaw', lx.symbol.sTYPE_BOOLEAN ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineTileJigsaw {%s}' % self.dyna_Bool( 0, 'tilejigsaw' ) )
            notifier = DeadlineTileNotifier()
            notifier.Notify( lx.symbol.fCMDNOTIFY_DISABLE | lx.symbol.fCMDNOTIFY_VALUE ) 

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineTileJigsaw ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass        

# Button that submits the Deadline job
class DeadlineOpenJigsaw( lxu.command.BasicCommand ):
    HostOut = ""
    PORTout = ""
    def __init__( self ):
        global deadlineSocket
        lxu.command.BasicCommand.__init__( self )
        if deadlineSocket is None:
            deadlineSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' ) and lx.eval( 'deadline.tileJigsaw ?' )
    
    def basic_Execute( self, msg, flags ):
        global deadlineSocket, submissionInfo
        
        try:
            deadlineSocket.sendall("TEST\n")
            CallDeadlineCommand( ['-ShowMessageBox', '-title' , 'Deadline Jigsaw', '-message', 'Jigsaw window is already open.'] )
            return
        except:
            pass
        
        try:
            
            self.HostOut = 'localhost'                 # Symbolic name meaning all available interfaces
            self.PORTout = self.get_open_port()              # Arbitrary non-privileged port
            deadlineSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            jigsawPath = os.path.join( submissionInfo[ "RepoDirs" ][ "submission/Jigsaw" ].strip(), "Jigsaw.py" )
            deadlineCommand = GetDeadlineCommand() +"bg"
            
            environment = {}
            for key in os.environ.keys():
                environment[key] = str(os.environ[key])
                
            # Need to set the PATH, cuz windows seems to load DLLs from the PATH earlier that cwd....
            if os.name == 'nt':
                deadlineCommandDir = os.path.dirname( deadlineCommand )
                if not deadlineCommandDir == "":
                    environment['PATH'] = deadlineCommandDir + os.pathsep + os.environ['PATH']
            
            width = lx.eval( 'render.res 0 ?' )
            height = lx.eval( 'render.res 1 ?' )
            tempDir = tempfile.gettempdir()
            jigsawBackgroundSave = tempDir+os.sep+"modoJigsawImage.tga"
            jigsawBackgroundOpen = tempDir+os.sep+"modoJigsawImage_0001.tga"
            try:
                #The width and height here might need to be adjusted based off the resolution, the padding is being added to get the correct size of image in the end
                command = 'layout.create JigsawCaptureWindow width:'+unicode(width+8)+' height:'+unicode(height+8)+' class:normal'
                lx.eval( command )
                lx.eval( 'viewport.restore {} false 3Dmodel' )
                lx.eval( 'view3d.projection cam' )
                lx.eval( 'view3d.renderCamera' )
                lx.eval( 'gl.capture true true "'+jigsawBackgroundSave+'" frameS:0 frameE:1' )
                lx.eval( 'layout.closeWindow' )
            except:
                lx.out(traceback.format_exc())
            
            subprocess.Popen( [ deadlineCommand, "-executescript", jigsawPath, str( self.PORTout ), jigsawBackgroundOpen, "False" ], env=environment)
            
            count = 0
            while True:
                try:
                    time.sleep(1)
                    deadlineSocket.connect((self.HostOut, self.PORTout))
                    break
                except:
                    count+=1
                    if count>=30:
                        errordialog("Jigsaw","Failed to connect to the Jigsaw Panel.")
                        break
        except:
            lx.out(traceback.format_exc())
        
    def get_open_port(self):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        port = s.getsockname()[1]
        s.close()
        return port
    
    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()
        
    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass
        
# Button that submits the Deadline job
class DeadlineResetJigsawBackground( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )        
    
    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' ) and lx.eval( 'deadline.tileJigsaw ?' )
    
    def basic_Execute( self, msg, flags ):
        try:
            width = lx.eval( 'render.res 0 ?' )
            height = lx.eval( 'render.res 1 ?' )
            tempDir = tempfile.gettempdir()
            jigsawBackgroundSave = tempDir+os.sep+"modoJigsawImage.tga"
            jigsawBackgroundOpen = tempDir+os.sep+"modoJigsawImage_0001.tga"
            try:
                #The width and height hear might need to be adjust based off of resolution, the padding is being added to get the correct size of image in the end
                command = 'layout.create JigsawCaptureWindow width:'+unicode(width+8)+' height:'+unicode(height+8)+' class:normal'
                lx.eval( command )
                lx.eval( 'viewport.restore {} false 3Dmodel' )
                lx.eval( 'view3d.projection cam' )
                lx.eval( 'view3d.renderCamera' )
                lx.eval( 'gl.capture true true "'+jigsawBackgroundSave+'" frameS:0 frameE:1' )
                lx.eval( 'layout.closeWindow' )
            except:
                lx.out(traceback.format_exc())
            
            try:
                deadlineSocket.sendall("screenshot="+jigsawBackgroundOpen+"\n")
            except:
                errordialog("Jigsaw","Please make sure the Jigsaw Panel is open.")
                deadlineSocket.close()
        except:
            lx.out(traceback.format_exc())
    
    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()
        
    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass
      
# Button that submits the Deadline job
class DeadlineSaveJigsawRegions( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )        
    
    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' ) and lx.eval( 'deadline.tileJigsaw ?' )
    
    def basic_Execute( self, msg, flags ):
        try:
            regions = ""
            regionString = ""
            try:
                deadlineSocket.sendall("saveregions\n")
                
                data = recvData(deadlineSocket)
            except:
                lx.out(traceback.format_exc())
                errordialog("Jigsaw","Please make sure the Jigsaw Panel is open.")
                deadlineSocket.close()
                return
                
            regionString = str(data)
            regionData = regionString.split("=")
            if len(regionData) >1:
                regions = regionData[1]
            
            if not channelExists("DeadlineJigsawRegions","Scene"):
                lx.eval('channel.create DeadlineJigsawRegions string item:Scene')  
                
            lx.eval( 'item.channel DeadlineJigsawRegions \"%s\" set Scene' % regions )
            
                
        except:
            lx.out(traceback.format_exc())
    
    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()
        
    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Button that submits the Deadline job
class DeadlineLoadJigsawRegions( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )        
    
    def basic_Enable( self, msg ):
        return lx.eval( 'deadline.tileEnable ?' ) and lx.eval( 'deadline.tileJigsaw ?' )
    
    def basic_Execute( self, msg, flags ):
        try: 
            try:
                regions = ""
                
                if channelExists("DeadlineJigsawRegions","Scene"):
                    lx.out("Loading Successful")
                    regions = lx.eval( 'item.channel DeadlineJigsawRegions ? item:Scene' )
                deadlineSocket.sendall("loadregions=%s\n"% regions)
            except:
                lx.out(traceback.format_exc())
                errordialog("Jigsaw","Please make sure the Jigsaw Panel is open.")
                deadlineSocket.close()
                return
        except:
            lx.out(traceback.format_exc())
    
    def arg_UIValueHints( self, index ):
        return DeadlineTileNotifiers()
        
    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

##############################################################################################################################################################################
### Notifiers (Essentially Callbacks)
##############################################################################################################################################################################

# Used for the Output UI
class DeadlineBakeNotifier( lxifc.Notifier, lxifc.CommandEvent ):
    masterList = {}

    def noti_Name( self ):
        return 'deadline.bakeNotifier'

    def noti_AddClient( self, event ):
        self.masterList[event.__peekobj__()] = event

    def noti_RemoveClient( self, event ):
        del self.masterList[event.__peekobj__()]

    def Notify( self, flags ):
        for event in self.masterList:
            evt = lx.object.CommandEvent( self.masterList[event] )
            evt.Event( flags )

class DeadlineBakeNotifiers( lxu.command.BasicHints ):
    def __init__( self ):
        self._notifiers = [( 'deadline.bakeNotifier', '' )]
        
class DeadlineOutputNotifier( lxifc.Notifier, lxifc.CommandEvent ):
    masterList = {}

    def noti_Name( self ):
        return 'deadline.outputNotifier'

    def noti_AddClient( self, event ):
        self.masterList[event.__peekobj__()] = event

    def noti_RemoveClient( self, event ):
        del self.masterList[event.__peekobj__()]

    def Notify( self, flags ):
        for event in self.masterList:
            evt = lx.object.CommandEvent( self.masterList[event] )
            evt.Event( flags )

class DeadlineOutputNotifiers( lxu.command.BasicHints ):
    def __init__( self ):
        self._notifiers = [( 'deadline.outputNotifier', '' )]

# Used for the Tile UI
class DeadlineTileNotifier( lxifc.Notifier, lxifc.CommandEvent ):
    masterList = {}

    def noti_Name( self ):
        return 'deadline.tileNotifier'

    def noti_AddClient( self, event ):
        self.masterList[event.__peekobj__()] = event

    def noti_RemoveClient( self, event ):
        del self.masterList[event.__peekobj__()]

    def Notify( self, flags ):
        for event in self.masterList:
            evt = lx.object.CommandEvent( self.masterList[event] )
            evt.Event( flags )

class DeadlineTileNotifiers( lxu.command.BasicHints ):
    def __init__( self ):
        self._notifiers = [( 'deadline.tileNotifier', '' )]

##############################################################################################################################################################################
### Register Custom Commands
##############################################################################################################################################################################

# Registers Job Options Commands
lx.bless( DeadlineLaunchUI, 'deadline.launchUI' )
lx.bless( DeadlineGetMachineList, 'deadline.getMachineList' )
lx.bless( DeadlineGetLimits, 'deadline.getLimits' )
lx.bless( DeadlineGetDependencies, 'deadline.getDependencies' )
lx.bless( DeadlinePipelineToolStatus, 'deadline.pipelineToolStatus' )
lx.bless( DeadlineOpenIntegrationWindow, 'deadline.unifiedIntegration' )
lx.bless( DeadlineSubmit, 'deadline.submit' )
lx.bless( DeadlineClose, 'deadline.close' )
lx.bless( DeadlineBakeItems, 'deadline.bakeItems' )
lx.bless( DeadlineBakeOnly, 'deadline.bakeOnly' )

# Registers Output Override Commands
lx.bless( DeadlineOutputEnable, 'deadline.overrideOutput' )
lx.bless( DeadlineOutputFolder, 'deadline.outputFolder')
lx.bless( DeadlineGetOutputFolder, 'deadline.getOutputFolder')
lx.bless( DeadlineOutputPrefix, 'deadline.outputPrefix')
lx.bless( DeadlineOutputPattern, 'deadline.outputPattern')
lx.bless( DeadlineOutputFormat, 'deadline.outputFormat')

# Registers Tile Rendering Commands
lx.bless( DeadlineTileEnable, 'deadline.tileEnable' )
lx.bless( DeadlineTileFrameRender, 'deadline.tileFrameToRender' )
lx.bless( DeadlineTilesInX, 'deadline.tilesInX' )
lx.bless( DeadlineTilesInY, 'deadline.tilesInY' )
lx.bless( DeadlineTileSubmitAssembly, 'deadline.tileSubmitAssembly' )
lx.bless( DeadlineTileCleanUp, 'deadline.tileCleanUp' )
lx.bless( DeadlineTileErrorOnMissing, 'deadline.tileErrorOnMissing' )
lx.bless( DeadlineTileAssembleOver, 'deadline.tileAssembleOver')
lx.bless( DeadlineTileBackgroundImage, 'deadline.tileBackgroundImage')
lx.bless( DeadlineTileGetBackgroundImage, 'deadline.tileGetBackgroundImage')
lx.bless( DeadlineTileErrorOnMissingBackground, 'deadline.tileErrorOnMissingBackground' )
lx.bless( DeadlineTileJigsaw, 'deadline.tileJigsaw')
lx.bless( DeadlineOpenJigsaw, 'deadline.openJigsaw' )
lx.bless( DeadlineResetJigsawBackground, 'deadline.resetJigsawBackground' )
lx.bless( DeadlineSaveJigsawRegions, 'deadline.saveJigsawRegions' )
lx.bless( DeadlineLoadJigsawRegions, 'deadline.loadJigsawRegions' )

# Registers Notifier Commands
lx.bless( DeadlineBakeNotifier, 'deadline.bakeNotifier' )
lx.bless( DeadlineOutputNotifier, 'deadline.outputNotifier' )
lx.bless( DeadlineTileNotifier, 'deadline.tileNotifier' )


###########################################################
### 'Non-specific' Classes/Methods
###########################################################

def infodialog(title, message):
    lx.eval('dialog.setup info')
    lx.eval('dialog.title {%s}' % title)
    lx.eval('dialog.msg {%s}' % message)
    try:
        lx.eval('+dialog.open')
    except:
        pass

def errordialog(title, message):
    lx.eval('dialog.setup error')
    lx.eval('dialog.title {%s}' % title)
    lx.eval('dialog.msg {%s}' % message)
    try:
        lx.eval('+dialog.open')
    except:
        pass

def questiondialog(title, message):
    lx.eval('dialog.setup yesNo')
    lx.eval('dialog.title {%s}' % title)
    lx.eval('dialog.msg {%s}' % message)
    try:
        lx.eval('+dialog.open')
        result = lx.eval('dialog.result ?')
        return result == "ok"
    except:
        pass
        
    return False

def channelExists(channel, item):
    try:
        chanvalue = lx.eval('!item.channel %s ? item:%s' % (channel, item))
        lx.out(str(type(chanvalue)))
        if chanvalue or chanvalue == "" or chanvalue == False:
            return True
    except:
        return False

def CallDeadlineCommand( arguments, background=True, raise_on_returncode=False ):
    deadlineCommand = GetDeadlineCommand()
    creationflags = 0
    startupinfo = None

    if os.name == 'nt':
        if background:
            # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
            if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            # still show top-level windows, but don't show a console window
            CREATE_NO_WINDOW = 0x08000000   #MSDN process creation flag
            creationflags = CREATE_NO_WINDOW
    
    arguments.insert( 0, deadlineCommand )
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediately afterwards.
    proc = subprocess.Popen( arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags )
    output, errors = proc.communicate()

    # Optionally check the return code and raise a CalledProcessError if non-zero
    if raise_on_returncode and proc.returncode != 0:
        try:
            # Python 3 moved the shell escape routine to shlex
            from shlex import quote as shell_quote
        except ImportError:
            # In Python 2 it was in the pipes module
            from pipes import quote as shell_quote
        cmd = " ".join([shell_quote(argument) for argument in arguments])
        raise subprocess.CalledProcessError(proc.returncode, cmd, output)

    return output

# Gets the output pattern format from modo ( ie. "[<pass>][<output>][<LR>]<FFFF>" ) [] is optional, <> is command 
def GetOutputPattern():
    outputPattern = ""

    overrideOutput = lx.eval( 'deadline.overrideOutput ?' )
    if overrideOutput:
        outputPattern = CheckEmptyString( 'deadlineOutputPattern' )
        outputFormat = formats[CheckEmptyString( 'deadlineOutputFormat' )]
        
        # For layered formats, remove the [<output>] part since it isn't used.
        if outputFormat in layeredFormats:
            outputPattern = outputPattern.replace( "[<output>]", "" )
    else:
        lx.eval( 'select.itemType polyRender' )
        outputPattern = lx.eval( 'item.channel outPat ?')
        
    return outputPattern

def write_aliases_to_submisison_file( fileHandle, aliases):
    """
    Writes out a dictionary of Path aliases to a job info file
    :param fileHandle: The handle to the Job Info File
    :param aliases: A dictionary containing the Path Aliases and output files
    :return: Nothing
    """
    for i, ( alias, path ) in enumerate( aliases.iteritems() ):
        fileHandle.write( "PathAlias%s=%s\n" % (i, alias ) )
        fileHandle.write( "PathAliasPath%s=%s\n" % ( i, path ) )


def get_path_aliases( ):
    """
    Reads the MODO preferences config file to retrieve a list of all path aliases and what they map to.
    :return:  A Dictionary of Aliases and the associated Local Paths
    """


    aliases = []
    try:
        return get_global_config().path_aliases
    except IOError as e:
        print( "Failed to collect path aliases, unable to open config file." )
        return [ ]
    except DeadlineModoConfig.ParseError as e:
        print( e )
        print( "Failed to collect path aliases, config file is not valid xml." )
        return []

# '[<pass>][<output>][<LR>]<FFFF>'' is an exmaple outputPattern
# 'pass01,Final Output Color,L' is an example replaceWith
# The order of 'replaceWith' must match 'patternsToReplace'
def EvaluateOutputPattern( outputPattern, replaceWith ):    
    patternsToReplace = ['\[{0,1}<pass>\]{0,1}', '\[{0,1}<LR>\]{0,1}', '\[{0,1}<output>\]{0,1}']

    for pattern, replace in zip( patternsToReplace, replaceWith.split(',') ):
        outputPattern = re.sub( pattern, replace, outputPattern )
    
    outputPattern = re.sub( '\[{0,1}<none>\]{0,1}', '', outputPattern )
    
    return outputPattern

# Makes a string of every combination. ie. ['p1', 'p2'], [], ['L', "R"], and [####] join to become ['p1,,L,####', 'p1,,R,####',...] etc.
def EnumerateLists( passes, stereos ): # Remnant of joining more than 2 lists ie. results = JoinLists( results, thirdList )
    results = JoinLists( passes, stereos )
    if results == []:
        results=[',']

    return results

# Joins each element from the first list with every element of the other list
def JoinLists( firstList, secondList ):
        result = []
        if not firstList:
            return [ ',' + item for item in secondList ]
        if not secondList:
            return [ item + ',' for item in firstList ]

        for i in firstList:
            for j in secondList:
                result += [','.join( [i, j] )]

        return result

# Gets the names of the passes inside the selected pass group
def GetPasses():
    passNames = []

    group = lx.eval( 'query sceneservice group.current ? render' ) # current pass group
    if group:
        if lx.eval( 'query sceneservice pass.isCurrent ?' ): # Double Checking, may be redundant
            passes = lx.evalN( 'query sceneservice pass.itemMembers ?' ) # Get the items in the group ( actionclips (passes) and poses )
            for passItem in passes:
                if lx.eval( 'query sceneservice actionItem.type ? {%s}' % passItem ) == "actionclip": # actionclip = pass
                    if lx.eval( 'layer.enable layer:{%s} ?' %passItem ) == "on":
                        passNames.append( lx.eval( 'query sceneservice actionItem.name ? {%s}' % passItem ) )
                    
    return passNames

# Gets the IDs of the renderOutputs ( ie. renderOutput013 )
def GetOutputIDs( passGroup="", passName="" ):
    outputs = []
    
    if not passGroup == "" and not passName == "":
        lx.eval('select.drop channel')
        lx.eval('select.item %s set' % passGroup)
        lx.eval('select.item %s set' % passName)
        lx.eval('layer.active active:on type:-1')
    
    overrideOutput = lx.eval( 'deadline.overrideOutput ?' )
    
    itemCount = lx.eval( 'query sceneservice item.N ?' ) # Number of items in the scene
    for i in range( 0, itemCount ):
        itemType = lx.eval( 'query sceneservice item.type ? {%s}' % i ) # Item types
        if itemType == "renderOutput":
            
            itemID = lx.eval( 'query sceneservice item.id ? {%s}' % i ) # Get item and select it
            lx.eval( 'select.item {%s}' % itemID )
            isEnabled = lx.eval( 'item.channel textureLayer$enable ?' ) # is the output enabled
            parent = lx.eval( 'query sceneservice item.parent ? {%s}' % i )
            lx.eval( 'select.item {%s}' % parent )
            
            parentEnabled = True
            if channelExists("enable", parent):
                parentEnabled = int(lx.eval( 'item.channel enable ? {%s}' % parent ) )
                
            lx.eval( 'select.item {%s}' % itemID )
            if isEnabled and parentEnabled:
                if overrideOutput:
                    outputs.append( lx.eval( 'query sceneservice item.id ? {%s}' % itemID ) ) # Gets output id
                else:
                    fileFormat = lx.eval( 'item.channel renderOutput$format ? {%s}' % itemID ) # Gets output format (ie. 'PNG') to check if it's valid
                    if fileFormat:# Only return the format if the filename and format are valid.
                        outputFilename = lx.eval( 'item.channel renderOutput$filename ? {%s}' % itemID ) # Gets output filename
                        if outputFilename:
                            outputs.append( lx.eval( 'query sceneservice item.id ? {%s}' % itemID ) ) # Gets output id
    
    if not passGroup == "" and not passName == "":
        lx.eval('select.drop channel')
        lx.eval('select.item %s set' % passGroup)
        lx.eval('select.item %s set' % passName)
        lx.eval('layer.active active:off type:-1')
    
    return outputs

# Uses the ID to get the name of the renderOutput ( ie. Final Color Output )
def GetOutputNames( passGroup="", passName="" ):
    outputIDs = GetOutputIDs( passGroup, passName )
    outputNames = []
    for output in outputIDs:
        outputNames.append( lx.eval( 'query sceneservice item.name ? {%s}' % output ) )

    return outputNames    

# Returns ['L', 'R'] or [''] for the output pattern. (modo doesn't add L/R to filename if it's just one)
def GetStereo():
    stereo = []
    camera = lx.eval( 'render.camera ?' )
    if camera is not None:
        lx.eval( 'select.item {%s}' % camera ) 

        isStereo = lx.eval( 'item.channel camera$stereo ?' )
        if isStereo:
            stereo = lx.eval( 'item.channel camera$stereoEye ?' ).lower()
            if stereo == "both":  # For some reason, if it's just 'left', or just 'right', modo doesn't add it to the filename
                stereo = ["L", "R"]

    return stereo

# Retrieves the output file name of a renderOutput item
def GetOutputFilenames( passGroup = "", passName = "" ):
    outputFilenames = []

    overrideOutput = lx.eval( 'deadline.overrideOutput ?' )
    outputFormatName = CheckEmptyString( 'deadlineOutputFormat' )
    outputFormat = formats[outputFormatName]
    
    if not passGroup == "" and not passName == "":
        lx.eval('select.drop channel')
        lx.eval('select.item %s set' % passGroup)
        lx.eval('select.item %s set' % passName)
        lx.eval('layer.active active:on type:-1')
    
    # Layered formats will save out to a single file, so handle appropriately.
    if overrideOutput and outputFormat in layeredFormats:
        outputFolder = CheckEmptyString( 'deadlineOutputFolder' ).strip()
        outputPrefix = CheckEmptyString( 'deadlineOutputPrefix' ).strip()
        outputFilename = os.path.join( outputFolder, outputPrefix )
        outputFilenames.append( outputFilename )
    else:
        itemCount = lx.eval( 'query sceneservice item.N ?' ) # Number of items in the scene
        for i in range( 0, itemCount ):
            itemType = lx.eval( 'query sceneservice item.type ? {%s}' % i ) # Item types
            if itemType == "renderOutput":
                itemID = lx.eval( 'query sceneservice item.id ? {%s}' % i ) # Get item and select it
                lx.eval( 'select.item {%s}' % itemID )
                isEnabled = int(lx.eval( 'item.channel enable ? {%s}' % i) ) # is the output enabled
                parentEnabled = True
                parent = lx.eval( 'query sceneservice item.parent ? {%s}' % i )
                if channelExists("enable", parent):
                    lx.eval( 'select.item {%s}' % parent )
                    try:
                        parentEnabled = int( lx.eval( 'item.channel enable ? {%s}' % parent ) )
                    except:
                        pass
                    lx.eval( 'select.item {%s}' % itemID )
                    
                if isEnabled and parentEnabled:
                    if overrideOutput:
                        outputFolder = CheckEmptyString( 'deadlineOutputFolder' ).strip()
                        outputPrefix = CheckEmptyString( 'deadlineOutputPrefix' ).strip()
                        outputFilename = os.path.join( outputFolder, outputPrefix )
                        outputFilenames.append( outputFilename )
                    else:
                        fileFormat = lx.eval('item.channel renderOutput$format ? {%s}' % itemID) # Gets output format (ie. 'PNG') to check if it's valid
                        if fileFormat:
                            outputFilename = lx.eval('item.channel renderOutput$filename ? {%s}' % itemID) # Gets output filename
                            if outputFilename:# Only return the filename if the filename and format are valid.
                                outputFilenames.append( outputFilename )
    
    if not passGroup == "" and not passName == "":
        lx.eval('select.drop channel')
        lx.eval('select.item %s set' % passGroup)
        lx.eval('select.item %s set' % passName)
        lx.eval('layer.active active:off type:-1')
    
    return outputFilenames

# Retrieves the output format of a renderOutput item
def GetFileFormats( passGroup, passName = "" ):
    fileFormats = []
    
    overrideOutput = lx.eval( 'deadline.overrideOutput ?' )
    outputFormatName = CheckEmptyString( 'deadlineOutputFormat' )
    outputFormat = formats[outputFormatName]
    
    if not passGroup == "" and not passName == "":
        lx.eval('select.drop channel')
        lx.eval('select.item %s set' % passGroup)
        lx.eval('select.item %s set' % passName)
        lx.eval('layer.active active:on type:-1')
    
     # Layered formats will save out to a single file, so handle appropriately.
    if overrideOutput and outputFormat in layeredFormats:
        fileFormats.append( outputFormat )
    else:
        itemCount = lx.eval( 'query sceneservice item.N ?' ) # Number of items in the scene
        for i in range( 0, itemCount ):
            itemType = lx.eval( 'query sceneservice item.type ? {%s}' % i ) # Item types
            if itemType == "renderOutput":
                itemID = lx.eval( 'query sceneservice item.id ? {%s}' % i ) # Get item and select it
                lx.eval( 'select.item {%s}' % itemID )
                isEnabled = lx.eval( 'item.channel enable ?' ) # is the output enabled
                parent = lx.eval( 'query sceneservice item.parent ? {%s}' % i )
                lx.eval( 'select.item {%s}' % parent )
                parentEnabled = True
                if channelExists("enable",parent):
                    parentEnabled = int( lx.eval( 'item.channel enable ? {%s}' % parent ) )
                lx.eval( 'select.item {%s}' % itemID )
                if isEnabled and parentEnabled:
                    if overrideOutput:
                        fileFormats.append( outputFormat )
                    else:
                        fileFormat = lx.eval( 'item.channel renderOutput$format ? {%s}' % itemID ) # Gets output format (ie. 'PNG') to check if it's valid
                        if fileFormat:# Only return the format if the filename and format are valid.
                            outputFilename = lx.eval( 'item.channel renderOutput$filename ? {%s}' % itemID ) # Gets output filename
                            if outputFilename:
                                fileFormats.append( fileFormat )
    
    if not passGroup == "" and not passName == "":
        lx.eval('select.drop channel')
        lx.eval('select.item %s set' % passGroup)
        lx.eval('select.item %s set' % passName)
        lx.eval('layer.active active:off type:-1')
    
    return fileFormats

# Checks if the path is local
def IsPathLocal( path ):
    lowerPath = path.lower()
    return lowerPath.startswith( "c:" ) or lowerPath.startswith( "d:" ) or lowerPath.startswith( "e:" )

def SetPools():
    global submissionInfo

    pools = ";".join( submissionInfo[ "Pools" ] ) # modo takes a list as a string separated by semi-colons. if you wish to have a semi-colon in a name, use two
    secondaryPools = "-;" + pools # modo doesn't allow empty string for the listnames in drop boxes
    previousPool = lx.eval( 'user.value deadlinePool ?' )
    previousSecondaryPool = lx.eval( 'user.value deadlineSecondaryPool ?' )
    
    poolsInternal = ""
    secondaryPoolsInternal = "secondaryPools_"
    for pool in submissionInfo[ "Pools" ]: # modo's internal list doesn't allow numbers, spaces, special characters, etc at the beginning, take out when we write job file
        poolsInternal = "%s;pools_%s" % ( poolsInternal, pool )
        secondaryPoolsInternal = "%s;secondaryPools_%s" % ( secondaryPoolsInternal, pool )

    poolsInternal = poolsInternal.lstrip(';') # Extra semi-colon at the front from the for loop, seondaryPools doesn't have since it doesn't start as blank string

    lx.eval( 'user.def deadlinePool list {%s}' % poolsInternal ) 
    lx.eval( 'user.def deadlinePool listnames {%s}' % ( pools + ';1;2;3;4;5;6;7;8;9;10;11' ) ) # MorganHack2: modo has display issues for only this dropdown if it's between length of 3 and 11... doing it for secondary and groups as well just in case
    lx.eval( 'user.def deadlineSecondaryPool list {%s}' % secondaryPoolsInternal )
    lx.eval( 'user.def deadlineSecondaryPool listnames {%s}' % ( secondaryPools + ';1;2;3;4;5;6;7;8;9;10;11' ) ) # MorganHack2

    
    # Show previous selected if possible
    if previousPool != 0 and previousPool[6:] in submissionInfo[ "Pools" ]: # Doesn't exist anymore
        lx.eval( 'user.value deadlinePool {%s}' % previousPool )
    else:
        lx.eval( 'user.value deadlinePool 0' )

    if previousSecondaryPool != 0 and previousSecondaryPool[15:] in submissionInfo[ "Pools" ]:
        lx.eval( 'user.value deadlineSecondaryPool {%s}' % previousSecondaryPool )
    else:
        lx.eval( 'user.value deadlineSecondaryPool 0' )

def recvData(theSocket):
    totalData=[]
    data=''
    while True:
        data=theSocket.recv(8192)
        if not data:
            return
        if "\n" in data:
            totalData.append(data[:data.find("\n")])
            break
        totalData.append(data)
    return ''.join(totalData)
        
def SetGroups():
    global submissionInfo

    groups = ";".join( submissionInfo[ "Groups" ] )  # modo takes lists separated by semi-colons.
    previousGroup = lx.eval( 'user.value deadlineGroup ?' )
    
    groupsInternal = ""
    for group in submissionInfo[ "Groups" ]: # modo's internal list doesn't allow numbers, spaces, special characters, etc at the beginning, take out when we write job file
        groupsInternal = "%s;groups_%s" % ( groupsInternal, group )

    lx.eval( 'user.def deadlineGroup list {%s}' % groupsInternal[1:] )
    lx.eval( 'user.def deadlineGroup listnames {%s}' % (groups + ';1;2;3;4;5;6;7;8;9;10;11') ) # MorganHack2
    
    # Show previous if possible
    if previousGroup != 0 and previousGroup[7:] in submissionInfo[ "Groups" ]:
        lx.eval( 'user.value deadlineGroup {%s}' % previousGroup )
    else:
        lx.eval( 'user.value deadlineGroup 0' )

def SetMaxPriority():
    global submissionInfo

    maxPriority = int( submissionInfo.get( "MaxPriority", 100 ) )
    lx.eval( 'user.def deadlinePriority max {%s}' % maxPriority )

    previousPriority = lx.eval( 'user.value deadlinePriority ?' )
    if lx.eval( 'user.value deadlinePool ?' ) == 0: # First time using integrated submitter
        lx.eval( 'user.value deadlinePriority {%s}' % ( maxPriority / 2 ) )
    elif 0 <= previousPriority <= maxPriority: # Show previous selected if possible
        lx.eval( 'user.value deadlinePriority {%s}' % previousPriority )
    else:
        lx.eval( 'user.value deadlinePriority {%s}' % ( maxPriority / 2 ) )

def ConcatenatePipelineSettingsToJob(jobInfoPath, batchName):
    """
    Calls an external python script through DeadlineCommand that modifies the staged job info file using the effective
    pipeline tool settings (persisted for the scene file or falls back to defaults)

    :param jobInfoPath: The path to the staged job info file to be modified
    :param batchName: The job's batch name, if applicable
    """

    jobWriterPath = os.path.join( submissionInfo["RepoDirs"]["submission/Integration/Main"].strip(), "JobWriter.py" )
    scenePath = lx.eval( 'query sceneservice scene.file ? current' )
    argArray = ["-ExecuteScript", jobWriterPath, "modo", "--write", "--scene-path", scenePath, "--job-path", jobInfoPath, "--batch-name", batchName]
    CallDeadlineCommand( argArray, False )

def GetPipelineToolStatus(raise_on_returncode=False):
    """
    Makes a call to DeadlineCommand to query the JobWriter for the effective pipeline tool settings for the current
    modo scene.

    :return The raw standard output byte stream returned from the call to DeadlineCommand
    """
    lx.out("Grabbing pipeline tool status...")

    jobWriterPath = os.path.join( submissionInfo["RepoDirs"]["submission/Integration/Main"].strip(), "JobWriter.py" )
    scenePath = lx.eval( 'query sceneservice scene.file ? current' )
    argArray = [
        # Execute the JobWriter script
        "-ExecuteScript", jobWriterPath,
        # Specify the requesting application
        "modo",
        # Query effective status (using persistent settings for scene path if they exist, falling back to defaults)
        "--status",
        # Specify the path to the scene
        "--scene-path", scenePath
    ]
    pipelineSettingsStatus = CallDeadlineCommand(argArray, False, raise_on_returncode=raise_on_returncode)

    return pipelineSettingsStatus

def HandlePipelineToolException(error):
    """
    Gracefully handles exceptions raised when attempting to accessing/modifying the pipeline tool status. Handling
    consists of:

    1.  presenting a warning pop-up message
    2.  logging the same message to Modo's event log

    The function returns a generic error status message to be presented to the user indicating an error occurred in
    the Pipeline Tools

    :param error: An instance of subprocess.CalledProcessError that was raised when executing a Pipeline Tools
                  subprocess
    :return: The generic error status message to be presented to the user
    """

    # Type checking
    if not isinstance(error, subprocess.CalledProcessError):
        raise TypeError("Error is not a subprocess.CalledProcessError")

    error_message = StringIO()
    error_message.write("An error occurred trying to fetch pipeline tool status:")
    error_message.write(os.linesep * 2)
    error_message.write("The command:")
    error_message.write(os.linesep * 2)
    error_message.write(error.cmd)
    error_message.write(os.linesep * 2)
    error_message.write("returned a non-zero exit code (%d)" % error.returncode)

    if error.output:
        error_message.write(" and produced the following output:")
        error_message.write(os.linesep * 2)
        error_message.write(error.output)

    # Output error to Modo's event log
    lx.out(error_message.getvalue())

    # Present error dialog to user
    errordialog(
        # Dialog title
        "Pipeline Tools Error",
        # Body of the dialog
        error_message.getvalue()
    )

    return "Pipeline Tools Error"

def writeAWSAssetFiles( fileHandle ):
    # 'modo' was added in 901, so for our purposes this should be fine because our amis have MODO 1101
    if 'modo' in sys.modules:

        # This is the only known item type that we want to ignore so far, if we find more types of nodes we just need to add them to this list.
        ignorableItems = [ "renderOutput" ]

        # These are the known types of channels that we care about so far since they are the only ones we are path mapping.  This list can be added to if we find additional Channel types that we need to handle.
        usableChannelTypes = ['file',
                            'filename',
                            'pattern',
                            'irrlname',
                            'irrsname',
                            'filepath',
                            'filepattern',
                            'scene',
                            'vray_file',
                            'vray_filename',
                            'vray_filepath',
                            'vray_prepass_filename',
                            'vray_ptex_file',
                            'vray_irr_file',
                            'vray_lc_file',
                            'vray_phomap_file',
                            'vray_caus_file',
                            'vray_lens_file',
                            'vray_stereo_shademap_file',
                            'vray_cache_cache_path']
        foundFiles = []
        scene = modo.scene.Scene()
        if not lx.eval( 'user.value deadlineSubmitModoScene ?' ):
            foundFiles.append( scene.filename )

        for item in scene.items():
            if not item.type in ignorableItems:
                for channel in item.channels():
                    channelType = channel.evalType
                    if channelType in usableChannelTypes:
                        channelVal = channel.get()
                        if channelVal:
                            foundFiles.append( channelVal )

        foundFiles = list( set( foundFiles ) )

        for index, assetFilename in enumerate( foundFiles ):
            fileHandle.write( "AWSAssetFile%s=%s\n" % ( index, assetFilename ) )
    
def GetJobIDFromSubmission( jobResults ):
    jobId = ""
    resultArray = jobResults.split("\n")
    for line in resultArray:
        if line.startswith("JobID="):
            jobId = line.replace("JobID=","")
            jobId = jobId.strip()
            break
    
    return jobId