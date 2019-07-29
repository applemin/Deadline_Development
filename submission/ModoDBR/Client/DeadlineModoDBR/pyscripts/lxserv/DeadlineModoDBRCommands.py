#########################################################################################################################################################################
#########################################################################################################################################################################
# ALWAYS MAKE SURE THAT EACH MorganHack WORKS! You can ctrl-f (or cmd) for 'MorganHack#' to see where it's used (mostly)
#
# TABLE OF HACKS:
# MorganHack1 - Completing Deadline Job on UI close
# MorganHack2 - Getting dropdowns to display properly
#
#########################################################################################################################################################################
# MorganHack1: Encompassses everything involving DeadlineDBRDummyCommand and the DeadlineDBRCleanUp notifier
#
# Forum Post regarding executing code on close: http://community.thefoundry.co.uk/discussion/topic.aspx?f=37&t=86438
#
#    modo hasn't included a way to override what happens when you close a layout/form/viewport. "You should never need to do that"
# is what they what they said on the forum as of April 2014 (701, sp5). However, we need that functionality for DBR! To achieve this,
# I've created a notifier for an internal command (deadlineDBR.dummyCommand). 
#
#    A notifier is executed when you tell it to Notify(...flags here...), and I didn't give it that functionality.  We want it for when it creates 
# and destorys 'clients', which are the custom commands that are attached to the notifier. This code is executed anytime a 'notifier client' is destroyed. "When 
# is a notifier client destroyed?" you may ask. Well it's destroyed anytime the command (sometimes multiple commands as is the case for my UI notifier) 
# is created (what?!), modified (ie. command is enabled/disabled, not the value) or destroyed (makes sense). It can also be executed when the form 
# that the command is in is modified (like changing an attribute in the form editor). This is the reason I don't have any collapsers on this UI, as
# they create and destroy the clients (therefore executing the code to complete the deadline job). ie. I click reserve servers, collapse a divider,
# and it'll then complete the deadline job which is really bad!
#
#    So I've attached the cleanup notifier to deadlineDBR.dummyCommand (which has no actual functionality), and since the dummy command never changes it's enable state 
# (it's not even shown on UI), or anything about it, the method 'noti_RemoveClient' will only execute when the layout is created, and when the layout is destroyed 
# (or when people do form editor stuff, which they shouldn't be in the middle of submitting a job...). I then check to see if we've reserved the servers
# and to make sure there's a jobId so that we only complete the job if there's actually a job in deadline.
#
#########################################################################################################################################################################
# MorganHack2: Involves padding the drop-down boxes
#
#    modo has been having some weird functionality issues involving dropdown boxes, where if there wasn't a certain number of items it would display the
# internal name instead of the display value (super weird). This is only a problem since we pad each internal value to prevent any mishaps with modo.
# Modo can't allow numbers (or spaces, among other reserved characters) as the first value internally, if any internal value violates that, it will 
# store ALL internal values as their index. ie. 'none' is selected in pools would be index 0, lx.eval(user.value deadlineDBRPool ?) returns 0 instead of 'none'
# or in our case, 'pools_none'). 
#
#    Anywho, padding the display values was used because if there between 3ish and 10ish items in the list (seoncdaryPools was unaffected oddly enough,
# Bhavek and I believe there's something going on regarding the '-' display value ) then it'll display either all internal values (ie. 'pools_none' even though
# we specified 'none') or just the last one as an internal value (ie. first 7 values show properly, but the 8th (last) value is the internal value). Since we add
# at least 11 displays values that don't have any internal values they are not displayed in the list and we end up with no display issues.
#
# ie. internal value issue - '3dsmax' is the problem (which is why we pad with 'pools_', etc)
# intended internal values: 3dsmax, aaa, bbb, ccc
# display value: 3dsmax, aaa, bbb, ccc
# actual internal value: 0, 1, 2, 3
#
# ie. length issue
# internal values: pool_1, pool_2, pool_3, pool_4
# intended display values: 1, 2, 3, 4
# What's actually shown when you click the dropdown: pool_1, pool_2, pool_3, pool_4
#
# ie. length issue #2
# internal values: pool_1, pool_2, pool_3, pool_4, pool_5, pool_6 pool_7, pool_8
# intended display values: 1, 2, 3, 4, 5, 6, 7, 8
# What's actually shown when you click the dropdown: 1, 2, 3, 4, 5, 6, 7, pool_8
#
#########################################################################################################################################################################
#########################################################################################################################################################################

import lx
import lxu
import lxu.command
import lxifc

import os
import subprocess
import sys
import time

persistActiveServerData = None

###########################################################
### Custom Commands / Modo-specific methods
###########################################################

# Opens the 'Submit To Deadline: Modo DBR' dialog and loads the pools, group, and max priority from deadline
class DeadlineDBRLaunchUI( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Execute( self, msg, flags ):
        # Ideally, we'd be check if it was already created, so that we only set pools/group/maxpriority on creation
        # However, I haven't found a good way of implementing that as you can also close this layout with the red 'X'

        # Populate lists
        lx.eval( 'user.value deadlineDBRrenderVRay false' )
        lx.eval( 'user.value deadlineDBRAreServersReserved false' )
        SetMaxPriority()
        SetPools()
        SetGroup()
        
        jobName = str( lx.eval( 'query sceneservice scene.name ? current' ) )
        if jobName == "":
            jobName = "Distributed Render"
        else:
            jobName = jobName + " - Distributed Render" 
            
        lx.eval( 'user.value deadlineDBRJobName {%s}' % jobName )

        windows = ['win32', 'cygwin']
        if sys.platform in windows: # windows layout size
            lx.eval( 'layout.createOrClose cookie:DEADLINEDBR layout:DeadlineModoDBRLayout title:"Submit To Deadline: Modo DBR" width:400 height:600 style:palette' )
        else: # mac size/linux size?
            lx.eval( 'layout.createOrClose cookie:DEADLINEDBR layout:DeadlineModoDBRLayout title:"Submit To Deadline: Modo DBR" width:400 height:477 style:palette' )

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Button that retrieves the Limits from Deadline
class DeadlineDBRGetLimits( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Execute( self, msg, flags ):
        output = CallDeadlineCommand( ["-selectlimitgroups", lx.eval( 'user.value deadlineDBRLimits ?' )] )
        output = output.replace( "\r", "" ).replace( "\n", "" )
        if output != "Action was cancelled by user":
            lx.eval( 'user.value deadlineDBRLimits "%s"' % output )

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Button that retrieves the Machine List from Deadline
class DeadlineDBRGetMachineList( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Execute( self, msg, flags ):
        output = CallDeadlineCommand( ["-selectmachinelist", lx.eval( 'user.value deadlineDBRMachineList ?' )] )
        output = output.replace( "\r", "" ).replace( "\n", "" )
        if output != "Action was cancelled by user":
            lx.eval( 'user.value deadlineDBRMachineList "%s"' % output )

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Creates and controls the 'Maximum Servers' integer field
class DeadlineDBRMaxServers( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'maxServers', lx.symbol.sTYPE_INTEGER ) # Integer attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return not lx.eval( 'user.value deadlineDBRAreServersReserved ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineDBRMaxServers {%s}' % self.dyna_Int( 0, 'maxServers' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddInt( lx.eval( 'user.value deadlineDBRMaxServers ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineDBRUINotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Creates and controls the 'Job ID' string field
class DeadlineDBRJobID( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'jobId', lx.symbol.sTYPE_STRING ) # String attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'user.value deadlineDBRAreServersReserved ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineDBRJobID {%s}' % self.dyna_String( 0, 'jobId' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddString( lx.eval( 'user.value deadlineDBRJobID ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineDBRUINotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Creates and controls the 'Job Status' string field
class DeadlineDBRJobStatus( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

        self.dyna_Add( 'status', lx.symbol.sTYPE_STRING ) # String attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL | lx.symbol.fCMDARG_CAN_QUERY_WHEN_DISABLED ) # ( Queryable | Setable | Queryable-whenDisabled ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'user.value deadlineDBRAreServersReserved ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            lx.eval( 'user.value deadlineDBRJobStatus {%s}' % self.dyna_String( 0, 'status' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddString( lx.eval( 'user.value deadlineDBRJobStatus ?' ) ) 
        return lx.result.OK

    def arg_UIValueHints( self, index ):
        return DeadlineDBRUINotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Creates and controls the 'Active Servers' multiline string field
class DeadlineDBRActiveServers( lxu.command.BasicCommand ):
    global persistActiveServerData

    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )
        PersistSetupActiveServers()

        self.dyna_Add( 'servers', lx.symbol.sTYPE_STRING ) # string attribute
        self.basic_SetFlags( 0, lx.symbol.fCMDARG_QUERY | lx.symbol.fCMDARG_OPTIONAL ) # ( Queryable | Setable ) flags

    def basic_Enable( self, msg ):
        return lx.eval( 'user.value deadlineDBRAreServersReserved ?' )

    def basic_Execute( self, msg, flags ):
        if self.dyna_IsSet( 0 ):
            persistActiveServerData.SetText( self.dyna_String( 0, 'servers' ) )

    def cmd_Query( self, index, vaQuery ):
        va = lx.object.ValueArray()
        va.set( vaQuery )
        if index == 0:
            va.AddString( persistActiveServerData.GetText() )
        return lx.result.OK

    def arg_UIHints( self, index, hints ): # creates the multiline aspect
        if index == 0:
            hints.TextLines( 10 )

    def arg_UIValueHints( self, index ):
        return DeadlineDBRUINotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# 'Reserve Servers' button, akin to 'Submit Job'
class DeadlineDBRReserveServers( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Enable( self, msg ):
        return not lx.eval( 'user.value deadlineDBRAreServersReserved ?' )

    def basic_Execute( self, msg, flags ):
        homeDir = CallDeadlineCommand( ["-GetCurrentUserHomeDirectory",] )
        homeDir = homeDir.replace( "\r", "" ).replace( "\n", "" )
        deadlineTemp = os.path.join( homeDir, "temp" )

        # Null strings in modo return (unknown), so must check textboxes
        jobName = CheckEmptyString( "deadlineDBRJobName" )
        comment = CheckEmptyString( "deadlineDBRComment" )
        department = CheckEmptyString( "deadlineDBRDepartment" )

        limits = CheckEmptyString( "deadlineDBRLimits" )
        machineList = CheckEmptyString( "deadlineDBRMachineList" )

        jobInfoFile = os.path.join( deadlineTemp, "modo_job_info.job" )
        fileHandle = open( jobInfoFile, "w" )

        pluginName = "Modo"
        if lx.eval( 'user.value deadlineDBRrenderVRay ?' ):
            pluginName = "VraySpawner"

        fileHandle.write( "Plugin=%s\n" % pluginName )
        fileHandle.write( "Name=%s\n" % jobName )
        fileHandle.write( "Comment=%s\n" % comment )
        fileHandle.write( "Department=%s\n" % department )
        fileHandle.write( "Pool=%s\n" % lx.eval( 'user.value deadlineDBRPool ?' )[6:] ) # strips off the internal padding name 'pools_'
        fileHandle.write( "SecondaryPool=%s\n" % lx.eval( 'user.value deadlineDBRSecondaryPool ?' )[15:] ) # strips off the internal padding name 'secondaryPools_'
        fileHandle.write( "Group=%s\n" % lx.eval( 'user.value deadlineDBRGroup ?' )[7:] ) # strips off the internal padding name 'groups_'
        fileHandle.write( "Priority=%s\n" % lx.eval( 'user.value deadlineDBRPriority ?' ) )
        fileHandle.write( "TaskTimeoutMinutes=%s\n" % lx.eval( 'user.value deadlineDBRTaskTimeout ?' ) )
        fileHandle.write( "OnTaskTimeout=Complete\n" )
        
        fileHandle.write( "LimitGroups=%s\n" % limits )

        if lx.eval( 'user.value deadlineDBRIsBlacklist ?' ):
            fileHandle.write( "Blacklist=%s\n" % machineList )
        else:
            fileHandle.write( "Whitelist=%s\n" % machineList )
        
        if lx.eval( 'user.value deadlineDBRIsInterruptible ?' ):
            fileHandle.write( "Interruptible=true\n" )

        fileHandle.write( "Frames=0-%s\n" % int( lx.eval( 'deadlineDBR.maxServers ?' ) - 1 ) )
        fileHandle.write( "ChunkSize=1\n")
        fileHandle.close()

        # Get major version number, append xx when we write version
        version = lx.service.Platform().AppVersion() / 100

        pluginInfoFile = os.path.join( deadlineTemp, "modo_plugin_info.job" )
        fileHandle = open( pluginInfoFile, "w" )

        if lx.eval( 'user.value deadlineDBRrenderVRay ?' ):
            fileHandle.write( "Version=Modo\n" )
            fileHandle.write( "PortNumber=\n" )
        else:
            fileHandle.write( "Version=%sxx\n" % version )
            fileHandle.write( "ModoDBRJob=1\n")
        
        fileHandle.close()

        arguments = []
        arguments.append( jobInfoFile )
        arguments.append( pluginInfoFile )

        results = CallDeadlineCommand( arguments )

        # Submission Results: python dialog seems to not be working (modo 701 sp5)
        lx.out( results )

        jobId = ""
        for line in results.splitlines():
            if line.startswith( "JobID=" ):
                jobId = line[6:]
                break

        if jobId != "":
            lx.out( 'ModoDBR job submitted: %s' % jobId )
            lx.eval( 'user.value deadlineDBRAreServersReserved true' )

            notifier = DeadlineDBRUINotifier()
            notifier.Notify( lx.symbol.fCMDNOTIFY_DISABLE )

            lx.eval( 'deadlineDBR.jobID {%s}' % jobId )
            lx.eval( 'deadlineDBR.jobStatus {}' )
            lx.eval( 'deadlineDBR.activeServers {}' )
            notifier.Notify( lx.symbol.fCMDNOTIFY_VALUE )

    def arg_UIValueHints( self, index ):
        return DeadlineDBRUINotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

class DeadlineDBRUpdateGUI( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Enable( self, msg ):
        return lx.eval( 'user.value deadlineDBRAreServersReserved ?' )

    def basic_Execute( self, msg, flags ):
        jobId = lx.eval( 'deadlineDBR.jobId ?' )

        #update server list
        useIpAddress = lx.eval( 'user.value deadlineDBRUseIPAddress ?' )
        servers = CallDeadlineCommand( ["GetMachinesRenderingJob", jobId, "true" if useIpAddress else "false"] )
        servers = servers.splitlines()
        servers = "\r\n".join( servers )

        lx.eval( 'deadlineDBR.activeServers {%s}' % servers )

        #update the job's status
        jobState = ""
        jobInfo = CallDeadlineCommand( ["GetJob", jobId, "false"] )
        for line in jobInfo.splitlines():
            if line.startswith( "Status=" ):
                jobState = line[7:]
                break

        if jobState == "Active":
            jobState = "Rendering" if len( servers ) > 0 else "Queued"
        elif jobState == "":
            jobState = "Deleted"

        lx.eval( 'deadlineDBR.jobStatus {%s}' % jobState )

        # Sends out notification to update values
        notifier = DeadlineDBRUINotifier()
        notifier.Notify( lx.symbol.fCMDNOTIFY_VALUE )

    def arg_UIValueHints( self, index ):
        return DeadlineDBRUINotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

class DeadlineDBRStartRender( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Enable( self, msg ):
        return lx.eval( 'user.value deadlineDBRAreServersReserved ?' )

    def basic_Execute( self, msg, flags ):
        # Gets host names
        jobId = lx.eval( 'deadlineDBR.jobId ?' )
        slaves = CallDeadlineCommand( ["GetMachinesRenderingJob", jobId, "false"] )
        slaves = slaves.splitlines()

        #if not len( slaves ) > 0:
        #    lx.eval( 'deadlineDBR.activeServers "No slaves are actively rendering this job"' )
        #    notifier = DeadlineDBRUINotifier()
        #    notifier.Notify( lx.symbol.fCMDNOTIFY_VALUE )
        #    return

        # Determine hosts manually
        lx.eval( 'pref.value lanservices.discoverWithBonjour false' )
        lx.eval( 'pref.value lanservices.discoverWithHostlist true' )
        lx.eval( 'pref.value render.useNetwork true' ) # sets network rendering on
        
        if lx.eval( 'user.value deadlineDBRrenderVRay ?' ):
            lx.eval( 'user.value vray.dr.enableForProduction true' )
            lx.eval( 'user.value vray.dr.enableHostList1 true' )
            lx.eval( 'user.value vray.dr.enableHostList2 false' )
            lx.eval( 'user.value vray.dr.enableHostList3 false' )
            lx.eval( 'user.value vray.dr.enableHostList4 false' )

            lx.eval( 'user.value vray.dr.hostList1 %s' % ";".join( slaves ) )

            try:
                lx.eval( 'vray.render' )
            except:
                lx.out( 'Render was cancelled.' )
        else:
            # Must try to add each slave
            for slave in slaves:
                try:
                    lx.eval( '!hostlist.create {%s}' % slave ) # ! suppresses dialogs, error still shows in event log
                except:
                    pass # slave was already on the list

            time.sleep( 1.0 ) # If we don't wait before enabling, the slaves won't join in

            for enableSlave in slaves:
                lx.eval( 'hostlist.enable true {%s}' % enableSlave )

            try:
                lx.eval( 'render' )
            except:
                lx.out( 'render was cancelled' )

    def arg_UIValueHints( self, index ):
        return DeadlineDBRUINotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

class DeadlineDBRReleaseServers( lxu.command.BasicCommand ):
    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    def basic_Enable( self, msg ):
        return lx.eval( 'user.value deadlineDBRAreServersReserved ?' )

    def basic_Execute( self, msg, flags ):
        jobId = lx.eval( 'deadlineDBR.jobID ?' )

        servers = CallDeadlineCommand( ["GetMachinesRenderingJob", jobId, "false"] )
        servers = servers.splitlines()

        lx.out( "Completing ModoDBR job: %s" % jobId )
        CallDeadlineCommand( ["CompleteJob", jobId] )

        if not lx.eval( 'user.value deadlineDBRrenderVRay ?' ):
            # Disables slaves we used as there is no way to go through the list to disable all
            try:
                for server in servers:
                    lx.eval( 'hostlist.enable false {%s}' % server )
            except:
                pass

        lx.eval( 'deadlineDBR.jobID {}' )
        lx.eval( 'deadlineDBR.jobStatus {}' )
        lx.eval( 'deadlineDBR.activeServers {}' )
        lx.eval( 'user.value deadlineDBRAreServersReserved false' )

        notifier = DeadlineDBRUINotifier()
        notifier.Notify( lx.symbol.fCMDNOTIFY_VALUE | lx.symbol.fCMDNOTIFY_DISABLE )

    def arg_UIValueHints( self, index ):
        return DeadlineDBRUINotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# MorganHack1: Allows me to setup my cleanup notifier
class DeadlineDBRDummyCommand( lxu.command.BasicCommand ):

    def __init__( self ):
        lxu.command.BasicCommand.__init__( self )

    # Hooks into the form. Notifier will be deleted when creation, modification, or deletion of command (sounds weird)
    def arg_UIValueHints( self, index ):
        return DeadlineDBRCleanUpNotifiers()

    # If this method is not implemented, modo's event log displays a python error, "Not Implemented | lost exception (enable trace)"
    def cmd_Interact( self ):
        pass

# Stores the multiline text in the user config file
class PersistActiveServers( object ):
    def __init__( self ):
        # 'accessor' object for the 'activeServers' atom
        self.activeServers = None
        # The 'activeServerText' atom's actual value - set to a null string by default. This is an 'attribute' object
        # connect to the 'activeServerText' accessor defined above
        self.activeServerText = ''

    def GetText( self ):
        try:
            return self.activeServerText.GetString( 0 )
        except:
            return ''

    # Appends a 'text' atom and writes the current value of the 'activeServerText' attribute
    def SetText( self, activeServerText ):
            self.activeServers.Append()
            self.activeServerText.SetString( 0, activeServerText )

# Used to traverse the XML structure of the created atom type "DeadlineDBRActiveServer"
class VisitorActiveServers( lxifc.Visitor ):
    def vis_Evaluate( self ):
        global persistActiveServerData
        persistService = lx.service.Persistence()

        persistService.Start( 'DeadlineDBRActiveServers', lx.symbol.i_PERSIST_ATOM ) # Create 'DeadlineActiveServers' atom
        persistService.AddValue( lx.symbol.sTYPE_STRING ) # Add a string value
        persistActiveServerData.activeServers = persistService.End() # Closing the atom returns the 'accessor' object which we assign to the variable setup
        persistActiveServerData.activeServerText = lx.object.Attributes( persistActiveServerData.activeServers )

# Initializes the persistent data
def PersistSetupActiveServers():
    global persistActiveServerData

    if persistActiveServerData:
        return

    # Create persistent data object, get visitor servce, and create data visitor
    persistActiveServerData = PersistActiveServers()
    persistService = lx.service.Persistence()
    persistVisitor = VisitorActiveServers()

    # Creates the outer atom type for activeServers to be stored
    persistService.Configure( 'DeadlineDBRActiveServers', persistVisitor ) 
    return lx.symbol.e_OK

# Similar to a callback, but must explicitly call to do any updating
class DeadlineDBRUINotifier( lxifc.Notifier, lxifc.CommandEvent ):
    masterList = {}

    def noti_Name( self ):
        return 'deadlineDBR.uiNotifier'

    def noti_AddClient( self, event ):
        self.masterList[event.__peekobj__()] = event

    def noti_RemoveClient( self, event ):
        del self.masterList[event.__peekobj__()]

    def Notify( self, flags ):
        for event in self.masterList:
            evt = lx.object.CommandEvent( self.masterList[event] )
            evt.Event( flags )

class DeadlineDBRUINotifiers( lxu.command.BasicHints ):
    def __init__( self ):
        self._notifiers = [( 'deadlineDBR.uiNotifier', '' )]

# MorganHack1: Hacky way of cleaning up jobs; if they quit the submission UI without releasing slaves
# we need to check if a job is running. Only then do we complete it
class DeadlineDBRCleanUpNotifier( lxifc.Notifier, lxifc.CommandEvent ):
    masterList = {}

    def noti_Name( self ):
        return 'deadlineDBR.cleanUpNotifier'

    def noti_AddClient( self, event ):
        self.masterList[event.__peekobj__()] = event

    def noti_RemoveClient( self, event ):
        serversReserved = lx.eval( 'user.value deadlineDBRAreServersReserved ?' )
        jobId = CheckEmptyString( 'deadlineDBRJobID' )
        if serversReserved and jobId != "":
             lx.out( 'Submit To Deadline window closed, completing job: %s' % jobId )
             CallDeadlineCommand( ["CompleteJob", jobId] )

        del self.masterList[event.__peekobj__()]

    def Notify( self, flags ):
        for event in self.masterList:
            evt = lx.object.CommandEvent( self.masterList[event] )
            evt.Event( flags )

# MorganHack1
class DeadlineDBRCleanUpNotifiers( lxu.command.BasicHints ):
    def __init__( self ):
        self._notifiers = [( 'deadlineDBR.cleanUpNotifier', '' )]

# Registers the Custom Commands
lx.bless( DeadlineDBRLaunchUI, 'deadlineDBR.launchUI' )
lx.bless( DeadlineDBRGetLimits, 'deadlineDBR.getLimits' )
lx.bless( DeadlineDBRGetMachineList, 'deadlineDBR.getMachineList' )
lx.bless( DeadlineDBRMaxServers, 'deadlineDBR.maxServers' )
lx.bless( DeadlineDBRJobID, 'deadlineDBR.jobID' )
lx.bless( DeadlineDBRJobStatus, 'deadlineDBR.jobStatus' )

lx.bless( DeadlineDBRActiveServers, 'deadlineDBR.activeServers' )
lx.bless( DeadlineDBRReserveServers, 'deadlineDBR.reserveServers' )
lx.bless( DeadlineDBRUpdateGUI, 'deadlineDBR.updateGUI' )
lx.bless( DeadlineDBRStartRender, 'deadlineDBR.startRender' )
lx.bless( DeadlineDBRReleaseServers, 'deadlineDBR.releaseServers' )

lx.bless( DeadlineDBRDummyCommand, 'deadlineDBR.dummyCommand' ) # MorganHack1
lx.bless( DeadlineDBRUINotifier, 'deadlineDBR.uiNotifier' )
lx.bless( DeadlineDBRCleanUpNotifier, 'deadlineDBR.cleanUpNotifier' ) # MorganHack1

###########################################################
### 'Non-specific' Classes/Methods
###########################################################

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

    deadlineCommand = os.path.join(deadlineBin, "deadlinecommand")
    
    return deadlineCommand

def CallDeadlineCommand( arguments, background=True ):
    deadlineCommand = GetDeadlineCommand()

    startupinfo = None
    if background and os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    environment = {}
    for key in os.environ.keys():
        environment[key] = str(os.environ[key])
        
    # Need to set the PATH, cuz windows seems to load DLLs from the PATH earlier that cwd....
    if os.name == 'nt':
        deadlineCommandDir = os.path.dirname( deadlineCommand )
        if not deadlineCommandDir == "":
            environment['PATH'] = deadlineCommandDir + os.pathsep + os.environ['PATH']
    
    arguments.insert( 0, deadlineCommand )
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, env=environment)
    proc.stdin.close()
    proc.stderr.close()

    output = proc.stdout.read()
    return output

# Null strings in modo return (unknown) instead of "", so must check textboxes
def CheckEmptyString( userValue ):
    if not ( lx.eval( 'user.value deadlineDBRUnknown ?' ) == lx.eval( 'user.value {%s} ?' % userValue ) ):
        return lx.eval( 'user.value {%s} ?' % userValue )
    else:
        return ""

def SetPools():
    pools = ""
    poolsInternal = ""
    secondaryPools = "-;" # modo doesn't allow empty string for the listnames in drop boxes
    secondaryPoolsInternal = "secondaryPools_"
    previousPool = lx.eval( 'user.value deadlineDBRPool ?' )
    previousSecondaryPool = lx.eval( 'user.value deadlineDBRSecondaryPool ?' )

    output = CallDeadlineCommand( ["-pools",] )

    pools = ";".join( output.splitlines() ) # modo takes a list as a string separated by semi-colons. if you wish to have a semi-colon in a name, use two
    secondaryPools += pools

    for pool in output.splitlines(): # modo's internal list doesn't allow numbers, spaces, special characters, etc at the beginning, take out when we write job file
        poolsInternal = "%s;pools_%s" % ( poolsInternal, pool )
        secondaryPoolsInternal = "%s;secondaryPools_%s" % ( secondaryPoolsInternal, pool )

    poolsInternal = poolsInternal.lstrip(';') # Extra semi-colon at the front from the for loop, seondaryPools doesn't have since it doesn't start as blank string
    
    lx.eval( 'user.def deadlineDBRPool list {%s}' % poolsInternal ) 
    lx.eval( 'user.def deadlineDBRPool listnames {%s}' % (pools + ';1;2;3;4;5;6;7;8;9;10;11') ) # MorganHack2: modo has display issues for only this dropdown if it's between length of 3 and 11... doing it for secondary and groups as well just in case
    lx.eval( 'user.def deadlineDBRSecondaryPool list {%s}' % secondaryPoolsInternal )
    lx.eval( 'user.def deadlineDBRSecondaryPool listnames {%s}' % (secondaryPools + ';1;2;3;4;5;6;7;8;9;10;11') ) # MorganHack2
    
    # Show previous selected if possible
    if previousPool != 0 and previousPool[6:] in output.splitlines(): # Doesn't exist anymore
        lx.eval( 'user.value deadlineDBRPool {%s}' % previousPool )
    else:
        lx.eval( 'user.value deadlineDBRPool 0' )

    if previousSecondaryPool != 0 and previousSecondaryPool[15:] in output.splitlines():
        lx.eval( 'user.value deadlineDBRSecondaryPool {%s}' % previousSecondaryPool )
    else:
        lx.eval( 'user.value deadlineDBRSecondaryPool 0' )

def SetGroup():
    groups = ""
    groupsInternal = ""
    previousGroup = lx.eval( 'user.value deadlineDBRGroup ?' )

    output = CallDeadlineCommand( ["-groups",] ) 

    groups = ";".join( output.splitlines() )  # modo takes lists separated by semi-colons.

    for group in output.splitlines(): # modo's internal list doesn't allow numbers, spaces, special characters, etc at the beginning, take out when we write job file
        groupsInternal = "%s;groups_%s" % ( groupsInternal, group )
    
    lx.eval( 'user.def deadlineDBRGroup list {%s}' % groupsInternal[1:] )
    lx.eval( 'user.def deadlineDBRGroup listnames {%s}' % (groups + ';1;2;3;4;5;6;7;8;9;10;11') ) # MorganHack2
    
    # Show previous if possible
    if previousGroup != 0 and previousGroup[7:] in output.splitlines():
        lx.eval( 'user.value deadlineDBRGroup {%s}' % previousGroup )
    else:
        lx.eval( 'user.value deadlineDBRGroup 0' )

def SetMaxPriority():
    previousPriority = lx.eval( 'user.value deadlineDBRPriority ?' )

    try:
        output = CallDeadlineCommand( ["-getmaximumpriority",] )
        maxPriority = int(output)
    except:
        maxPriority = 100

    lx.eval( 'user.def deadlineDBRPriority max {%s}' % maxPriority )

    # Show previous selected if possible
    if lx.eval( 'user.value deadlineDBRPool ?' ) == 0: # First time using submitter
        lx.eval( 'user.value deadlineDBRPriority {%s}' % ( maxPriority / 2 ) )
    elif 0 <= previousPriority <= maxPriority:
        lx.eval( 'user.value deadlineDBRPriority {%s}' % previousPriority )
    else:
        lx.eval( 'user.value deadlineDBRPriority {%s}' % ( maxPriority / 2 ) )