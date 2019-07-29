#!/usr/bin/env python

import lx

setup = False

def DefineModoValues():
    global setup
    ###########################################################################
    ### GUI Values (No custom commands)
    ###########################################################################

    # Job Name
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRJobName' ):
        lx.eval( 'user.defNew deadlineDBRJobName string' )
        lx.eval( 'user.value deadlineDBRJobName Untitled' )

    # Comment
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRComment' ):
        lx.eval( 'user.defNew deadlineDBRComment string temporary' )

    # Department
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRDepartment' ):
        lx.eval( 'user.defNew deadlineDBRDepartment string temporary' )

    # Pool
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRPool' ):
        lx.eval( 'user.defNew deadlineDBRPool integer' ) # lists are defined as integers

    # SecondaryPool
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRSecondaryPool' ):
        lx.eval( 'user.defNew deadlineDBRSecondaryPool integer' ) # lists are defined as integers

    # Group
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRGroup' ):
        lx.eval( 'user.defNew deadlineDBRGroup integer' ) # lists are defined as integers

    # Priority
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRPriority' ):
        lx.eval( 'user.defNew deadlineDBRPriority integer' )
        lx.eval( 'user.def deadlineDBRPriority min 0' ) # Priority never goes below 0
    
    # Priority
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRTaskTimeout' ):
        lx.eval( 'user.defNew deadlineDBRTaskTimeout integer' )
        lx.eval( 'user.def deadlineDBRTaskTimeout min 0' ) # Priority never goes below 0
    
    # Limits
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRLimits' ):
        lx.eval( 'user.defNew deadlineDBRLimits string' )

    # Machine List
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRMachineList' ):
        lx.eval( 'user.defNew deadlineDBRMachineList string' )

    # Machine List Is A Blacklist
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRIsBlacklist' ):
        lx.eval( 'user.defNew deadlineDBRIsBlacklist boolean' )
    
    # Is Interruptible
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRIsInterruptible' ):
        lx.eval( 'user.defNew deadlineDBRIsInterruptible boolean' )

    # Maximum Servers
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRMaxServers' ):
        lx.eval( 'user.defNew deadlineDBRMaxServers integer' )
        setup = True

    # Use Server IP Address Instead Of Host Name
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRUseIPAddress' ):
        lx.eval( 'user.defNew  deadlineDBRUseIPAddress boolean' )

    # Use V-Ray spawner
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRrenderVRay' ):
        lx.eval( 'user.defNew deadlineDBRrenderVRay boolean' )

    ###########################################################################
    ### Internal Values
    ###########################################################################

    # Use a user.value to store the Job ID for deadlineDBR.jobID
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRJobID' ):
        lx.eval( 'user.defNew deadlineDBRJobID string' )
    lx.eval( 'user.value deadlineDBRJobID {}')

    # Uses a user.value to store the Job Status for deadlineDBR.jobStatus
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRJobStatus' ):
        lx.eval( 'user.defNew deadlineDBRJobStatus string' )
    lx.eval( 'user.value deadlineDBRJobStatus {}')

    # Keeps track of when servers are reserverd. This allows us to enable and disable parts of the GUI
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRAreServersReserved' ):
        lx.eval( 'user.defNew  deadlineDBRAreServersReserved boolean' )
    lx.eval( 'user.value deadlineDBRAreServersReserved false' )

    # Allows us to check if a string query is empty (returns the value: (unknown) ) as string comparison does not work
    if not lx.eval( 'query scriptsysservice userValue.isDefined ? deadlineDBRUnknown' ):
        lx.eval( 'user.defNew  deadlineDBRUnknown string' )
    lx.eval( 'user.value deadlineDBRUnknown {}')

# Allows overring lower and max range
def SetMaxServers( setup, lowerMaxServers=10, upperMaxServers=100 ): # ie. lowerMaxServers is the lowest potential max servers to be used (default is a potential 10 machines to be used)
    lx.eval( 'user.def deadlineDBRMaxServers min %s' % lowerMaxServers )
    lx.eval( 'user.def deadlineDBRMaxServers max %s' % upperMaxServers )
    if setup:
        lx.eval( 'user.value deadlineDBRMaxServers %s' % lowerMaxServers )

DefineModoValues()
SetMaxServers( setup )