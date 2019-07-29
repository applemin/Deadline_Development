#!/usr/bin/env python

import lx
import traceback

def DefineModoValues():
###########################################################################
### Job Option Values
###########################################################################

    # Job Name
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineJobName' ):
        lx.eval( 'user.defNew deadlineJobName string' )
        lx.eval( 'user.value deadlineJobName Untitled' )

    # Comment
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineComment' ):
        lx.eval( 'user.defNew deadlineComment string temporary' )

    # Department
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDepartment' ):
        lx.eval( 'user.defNew deadlineDepartment string temporary' )

    # Pool
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlinePool' ):
        lx.eval( 'user.defNew deadlinePool integer' ) # lists are defined as integers

    # SecondaryPool
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineSecondaryPool' ):
        lx.eval( 'user.defNew deadlineSecondaryPool integer' ) # lists are defined as integers

    # Group
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineGroup' ):
        lx.eval( 'user.defNew deadlineGroup integer' ) # lists are defined as integers

    # Priority
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlinePriority' ):
        lx.eval( 'user.defNew deadlinePriority integer' )
        lx.eval( 'user.def deadlinePriority min 0' )

    # Task Timeout
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTaskTimeout' ):
        lx.eval( 'user.defNew deadlineTaskTimeout integer' )
        lx.eval( 'user.def deadlineTaskTimeout min 0' )
        lx.eval( 'user.def deadlineTaskTimeout max 1000000' )

    # Enable Auto Task Timeout
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineAutoTaskTimeout' ):
        lx.eval( 'user.defNew deadlineAutoTaskTimeout boolean' )

    # Concurrent Tasks
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineConcurrentTasks' ):
        lx.eval( 'user.defNew deadlineConcurrentTasks integer' )
        lx.eval( 'user.def deadlineConcurrentTasks min 1' )
        lx.eval( 'user.def deadlineConcurrentTasks max 16' )
        lx.eval( 'user.value deadlineConcurrentTasks 1' )

    # Limit Tasks to Slave's Task Limit
    if not lx.eval( 'query scriptsysservice userValue.isDefined ?  deadlineLimitTasks' ):
        lx.eval( 'user.defNew  deadlineLimitTasks boolean' )
        lx.eval( 'user.value deadlineLimitTasks true' )

    # Machine Limit
    if not lx.eval( 'query scriptsysservice userValue.isDefined ?  deadlineMachineLimit' ):
        lx.eval( 'user.defNew  deadlineMachineLimit integer' )
        lx.eval( 'user.def deadlineMachineLimit min 0' )
        lx.eval( 'user.def deadlineMachineLimit max 1000000' )

    # Machine List Is A Blacklist
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineIsBlacklist' ):
        lx.eval( 'user.defNew deadlineIsBlacklist boolean' )

    # Machine List
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineMachineList' ):
        lx.eval( 'user.defNew deadlineMachineList string' )

    # Limits
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineLimits' ):
        lx.eval( 'user.defNew deadlineLimits string' )

    # Dependencies
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDependencies' ):
        lx.eval( 'user.defNew deadlineDependencies string' )

    # Pipeline Tool Status Message
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlinePipelineToolStatus' ):
        lx.eval( 'user.defNew deadlinePipelineToolStatus string' )

    # On Job Complete
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineOnJobComplete' ):
        lx.eval( 'user.defNew deadlineOnJobComplete integer' ) # lists are defined as integers
        lx.eval( 'user.def deadlineOnJobComplete list {%s}' % 'Nothing;Archive;Delete' ) 
        lx.eval( 'user.def deadlineOnJobComplete listnames {%s}' % 'Nothing;Archive;Delete' )
      
    # Submit Job As Suspended
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineSubmitAsSuspended' ):
        lx.eval( 'user.defNew deadlineSubmitAsSuspended boolean' )

    # Frame List
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineFrameList' ):
        lx.eval( 'user.defNew deadlineFrameList string' )

    # Frames Per Task
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineFramesPerTask' ):
        lx.eval( 'user.defNew deadlineFramesPerTask integer' )
        lx.eval( 'user.def deadlineFramesPerTask min 1' )
        lx.eval( 'user.def deadlineFramesPerTask max 1000000' )
        lx.eval( 'user.value deadlineFramesPerTask 1')

    # Submit modo Scene
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineSubmitModoScene' ):
        lx.eval( 'user.defNew deadlineSubmitModoScene boolean' )
        
    # Render with V-Ray
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineRenderWithVRay' ):
        lx.eval( 'user.defNew deadlineRenderWithVRay boolean' )
    
    # Submit Each Pass Group As A Separate Job
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineSubmitEachPassGroup' ):
        lx.eval( 'user.defNew deadlineSubmitEachPassGroup boolean' )

    # 'Submit Bake Job' 
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineBakeItems' ):
        lx.eval( 'user.defNew deadlineBakeItems boolean' )
        
    # 'Only Submit Bake Job' 
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineBakeOnly' ):
        lx.eval( 'user.defNew deadlineBakeOnly boolean' )
    
###########################################################################
### Override Output Values
###########################################################################  

    # 'Override Render Output' 
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineOverrideOutput' ):
        lx.eval( 'user.defNew deadlineOverrideOutput boolean' )
    lx.eval( 'user.value deadlineOverrideOutput false' )
    
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineOutputFolder' ):
        lx.eval( 'user.defNew deadlineOutputFolder string' )

    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineOutputPrefix' ):
        lx.eval( 'user.defNew deadlineOutputPrefix string' )
        
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineOutputPattern' ):
        lx.eval( 'user.defNew deadlineOutputPattern string' )
        lx.eval( 'user.value deadlineOutputPattern {[<pass>][<output>][<LR>]<FFFF>}' )
        
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineOutputFormat' ):
        lx.eval( 'user.defNew deadlineOutputFormat string' ) # lists are defined as integers
        lx.eval( 'user.value deadlineOutputFormat {Flexible Precision FLX}' )

###########################################################################
### Tile Rendering Values
###########################################################################  

    # 'Enable Tile Rendering' 
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTileEnable' ):
        lx.eval( 'user.defNew deadlineTileEnable boolean' )
    lx.eval( 'user.value deadlineTileEnable false' )

    # 'Frame To Tile Render'
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTileFrame' ):
        lx.eval( 'user.defNew deadlineTileFrame integer' )
        lx.eval( 'user.def deadlineTileFrame min 0' )
        lx.eval( 'user.def deadlineTileFrame max 1000000' )

    # 'Tiles In X'
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTilesInX' ):
        lx.eval( 'user.defNew deadlineTilesInX integer' )
        lx.eval( 'user.def deadlineTilesInX min 1' )
        lx.eval( 'user.def deadlineTilesInX max 1000' )
        lx.eval( 'user.value deadlineTilesInX 1')

    # 'Tiles In Y'
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTilesInY' ):
        lx.eval( 'user.defNew deadlineTilesInY integer' )
        lx.eval( 'user.def deadlineTilesInY min 1' )
        lx.eval( 'user.def deadlineTilesInY max 1000' )
        lx.eval( 'user.value deadlineTilesInY 1')

    # 'Submit Dependent Assembly Job'
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTileSubmitAssembly' ):
        lx.eval( 'user.defNew deadlineTileSubmitAssembly boolean' )
        lx.eval( 'user.value deadlineTileSubmitAssembly true' )

    # 'Clean Up Tiles After Assembly'
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTileCleanUp' ):
        lx.eval( 'user.defNew deadlineTileCleanUp boolean' )
        lx.eval( 'user.value deadlineTileCleanUp false' )

    # 'Error On Missing Tiles'
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTileErrorOnMissing' ):
        lx.eval( 'user.defNew deadlineTileErrorOnMissing boolean' )
        lx.eval( 'user.value deadlineTileErrorOnMissing true' )
    
    # Error on missing background
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTileAssembleOver' ):
        lx.eval( 'user.defNew deadlineTileAssembleOver string' ) # lists are defined as integers
        lx.eval( 'user.value deadlineTileAssembleOver {Blank Image}' )
    
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTileBackgroundImage' ):
        lx.eval( 'user.defNew deadlineTileBackgroundImage string' )
    
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTileErrorOnMissingBackground' ):
        lx.eval( 'user.defNew deadlineTileErrorOnMissingBackground boolean' )
        lx.eval( 'user.value deadlineTileErrorOnMissingBackground true' )
    
    
    # 'Error On Missing Tiles'
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineTileJigsaw' ):
        lx.eval( 'user.defNew deadlineTileJigsaw boolean' )
        lx.eval( 'user.value deadlineTileJigsaw true' )

#####################################################
### Other Values
###########################################################################

    # submissionInfo: Need to save in user prefs, as there's no guarantee the user reopens the UI between closes
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineSubmissionInfo' ):
        lx.eval( 'user.defNew deadlineSubmissionInfo string' ) # Evaluates to empty string

    # Allows us to check if a string query is empty (returns the value: (unknown) ) as string comparison does not work
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineUnknown' ):
        lx.eval( 'user.defNew deadlineUnknown string' )
        lx.eval( 'user.value deadlineUnknown {}' )

try:
    DefineModoValues()
except:
    lx.out( traceback.format_exc() )