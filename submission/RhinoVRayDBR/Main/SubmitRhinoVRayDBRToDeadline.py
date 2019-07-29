from __future__ import print_function
import os
import subprocess
import time
import traceback
import ConfigParser
import rhinoscriptsyntax as rs
import Rhino

from System.Windows.Forms import *
from System.Drawing import *
from threading import Thread, Timer

# Work-around to TickStyle.None being a syntax error in Python3
TickStyle_NONE = getattr( TickStyle, "None" )

class SubmitToDeadline( Form ):
    def __init__( self ):
        self.vray = rs.GetPlugInObject( "V-Ray for Rhino" )

        # Get the maximum priority.
        try:
            self.maximumPriority = int( CallDeadlineCommand( ["-getmaximumpriority"] ) )
        except:
            self.maximumPriority = 100
        
        # Get the pools.
        self.pools = CallDeadlineCommand( ["-pools"] ).splitlines()
        
        self.secondaryPools = [""]
        for pool in self.pools:
            self.secondaryPools.append( pool )
        
        # Get the groups.
        self.groups = CallDeadlineCommand( ["-groups"] ).splitlines()

        # Get the current user Deadline home directory, which we'll use to store temp files.
        self.deadlineHome = CallDeadlineCommand( ["-GetCurrentUserHomeDirectory"] ).replace( "\n", "" ).replace( "\r", "" )
        self.deadlineTemp = self.deadlineHome + "/temp"
        self.deadlineStickySettings = os.path.join( self.deadlineHome, "settings/rhino_vray_submission.ini" )

        self.tabIndex = 0
        # Initialize UI Controls
        self.InitJobDescriptionUI()
        self.InitJobOptionsUI()
        self.InitVRaySpawnerUI()
        self.InitButtonPanelUI()
        self.InitFormUI()

        self.ReadStickySettings()

        # Show the Form
        self.TopMost = True
        self.Show()
        self.Select()

        self.renderStarted = False

    # Event Handler for Priority controls
    def UpdatePriority( self, sender, e ):
        self.PriorityNumericUpDown.Value = sender.Value
        self.PriorityTrackBar.Value = sender.Value

    # Event Handler for the Limit Button
    def GetLimitsFromDeadline( self, *args ):
        output = CallDeadlineCommand( ["-selectlimitgroups", self.LimitsTextBox.Text], False )
        output = output.replace( "\r", "" ).replace( "\n", "" )
        if output != "Action was cancelled by user":
            self.LimitsTextBox.Text = output

    # Event Handler for the Machine List button
    def GetMachineListFromDeadline( self, *args ):
        output = CallDeadlineCommand( ["-selectmachinelist", self.MachineListTextBox.Text], False )
        output = output.replace( "\r", "" ).replace( "\n", "" )
        if output != "Action was cancelled by user":
            self.MachineListTextBox.Text = output

    # Event Handler for Task Timeout controls
    def UpdateTaskTimeout( self, sender, e ):
        self.TaskTimeoutNumericUpDown.Value = sender.Value
        self.TaskTimeoutTrackBar.Value = sender.Value
    
    # Event Handler for Max Servers controls
    def UpdateMaxServers( self, sender, e ):
        self.MaxServersNumericUpDown.Value = sender.Value
        self.MaxServersTrackBar.Value = sender.Value

    # Event Handler for 'Reserve Servers' Click
    def SubmitJob( self, *args ):
        self.ReserveServersButton.Enabled = False
        self.ClearHosts()

        # Create the job info file
        jobInfoFile = os.path.join( self.deadlineTemp, "vray_spawner_job_info.job" )
        fileHandle = open( jobInfoFile, "w" )
        fileHandle.write( "Plugin=VraySpawner\n" )
        fileHandle.write( "Frames=0-%s\n" % ( self.MaxServersNumericUpDown.Value - 1 ) )
        fileHandle.write( "Name=%s\n" % self.NameTextBox.Text )
        fileHandle.write( "Comment=%s\n" % self.CommentTextBox.Text )
        fileHandle.write( "Department=%s\n" % self.DepartmentTextBox.Text )
        fileHandle.write( "Priority=%s\n" % self.PriorityNumericUpDown.Value )
        fileHandle.write( "Pool=%s\n" % self.PoolComboBox.Text )
        fileHandle.write( "SecondaryPool=%s\n" % self.SecondaryPoolComboBox.Text )
        fileHandle.write( "Group=%s\n" % self.GroupComboBox.Text )
        fileHandle.write( "LimitGroups=%s\n" % self.LimitsTextBox.Text )
        fileHandle.write( "Interruptible=%s\n" % self.IsJobInterruptibleCheckBox.Checked )
        fileHandle.write( "TaskTimeoutMinutes=%s\n" % self.TaskTimeoutNumericUpDown.Value )
        fileHandle.write( "OnTaskTimeout=Complete\n" )
        fileHandle.write( "ChunkSize=1\n" )

        if self.IsBlacklistCheckBox.Checked:
            fileHandle.write( "Blacklist=%s\n" % self.MachineListTextBox.Text )
        else:
            fileHandle.write( "Whitelist=%s\n" % self.MachineListTextBox.Text )
        
        fileHandle.close()
        
        # Create the plugin info file
        pluginInfoFile = os.path.join( self.deadlineTemp, "vray_spawner_plugin_info.job" )
        fileHandle = open( pluginInfoFile, "w" )
        fileHandle.write( "Version=Rhino\n" )
        fileHandle.write( "PortNumber=20211\n" )
        fileHandle.close()

        self.WriteStickySettings()
        
        # Submit the job to Deadline
        args = []
        args.append( jobInfoFile )
        args.append( pluginInfoFile )
        
        results = CallDeadlineCommand( args )
        print( results )
        jobId = ""
        for line in results.splitlines():
            if line.startswith( "JobID=" ):
                jobId = line[6:]
                break
        
        if jobId != "":
            print( "Spawner job submitted: %s" % jobId )
            self.SpawnerJobIDTextBox.Text = jobId
            
            self.ReleaseServersButton.Enabled = True

            Thread( target=self.UpdateThread ).start()
        else:
            self.ReserveServersButton.Enabled = False

    # Event Handler for 'Start Render' Click
    def StartRender( self, *args ):
        self.StartRenderButton.Enabled = False
        self.renderStarted = True
        rs.Command( "_SetCurrentRenderPlugIn \"V-Ray for Rhino\"" )
        self.vray.SetDistributedRenderingOn( True )
        rs.Command( "_Render" )

    def CloseForm( self, *args ):
        self.WriteStickySettings()

        if self.ReleaseServersButton.Enabled:
            self.CompleteJob()

    # Event Handler for 'Release Servers' Click
    def CompleteJob( self, *args ):
        self.ReleaseServersButton.Enabled = False
        self.StartRenderButton.Enabled = False

        jobId = self.SpawnerJobIDTextBox.Text
        if jobId != "":
            # self forces the message box to be on top of the dialog window
            result = MessageBox.Show( self, "This will complete the VRay Spawner job. Do you wish to continue?", "Warning", MessageBoxButtons.YesNo )
            
            if result == DialogResult.Yes:
                Thread( target = self.CompleteJobThread, args=( jobId, ) ).start()
                print( "Completing spawner job: %s" % jobId )
                self.ResetSpawnerControls()
            else:
                self.ReleaseServersButton.Enabled = True
                return

    def CompleteJobThread( self, jobId ):
        CallDeadlineCommand( ["CompleteJob", jobId] )

    def ClearHosts( self ):
        try:
            vrayIni = self.GetVRayIniFile()

            if os.path.exists( vrayIni ):
                config = ConfigParser.ConfigParser()
                config.read( vrayIni )
                section = "DRServers"

                # Remove all options including this section
                config.remove_section( section )

                section = "EnabledDRServers"

                # Remove all options including this section
                config.remove_section( section )
                
                with open( vrayIni, 'wb' ) as vrayIni:
                    config.write( vrayIni )
        except:
            print( "Failed to update the VRay ini file.\n%s" % traceback.format_exc() )

    def UpdateThread( self ):  
        vrayIni = self.GetVRayIniFile() # Hopefully they add a way to bypass this, or if not that to get this location programmically
        jobId = self.SpawnerJobIDTextBox.Text
        
        while jobId != "":
            # Update the server list.
            useIpAddress = self.UseServerIPCheckBox.Checked
            servers = CallDeadlineCommand( ["GetMachinesRenderingJob", jobId, "true" if useIpAddress else "false"] )

            if self.ReleaseServersButton.Enabled:
                self.ActiveServersTextBox.Text = servers

            if len( servers ) > 0 and not self.renderStarted and self.ReleaseServersButton.Enabled:
                self.StartRenderButton.Enabled = True
            else:
                self.StartRenderButton.Enabled = False
                
            # Update the job's state.
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

            if self.ReleaseServersButton.Enabled:
                self.SpawnerJobStatusTextBox.Text = jobState
            
            # Update the vray config file.
            servers = servers.splitlines()
            self.UpdateVRayServers( vrayIni, servers )
            self.UpdateVRayEnabledServers( vrayIni, servers )
            
            if jobState != "Rendering" and jobState != "Queued":
                self.NotifyJobStateChanged( jobState )
            else:
                time.sleep( 5.0 )
            
            jobId = self.SpawnerJobIDTextBox.Text

        # In case timings don't work out
        self.ResetSpawnerControls()

    # Used in UpdateThread
    def UpdateVRayServers( self, configFile, servers ):
        try:
            if os.path.exists( configFile ):
                config = ConfigParser.ConfigParser()
                config.read( configFile )
                section = "DRServers"

                # Remove all options including this section
                config.remove_section( section )
                    
                # Add the new options, including this section
                config.add_section( section )
                for i, server in enumerate( servers ):
                    config.set( section, str( i ), server )

                with open( configFile, 'wb' ) as configFile:
                    config.write( configFile )
        except:
            print( "Failed to update the VRay ini file.\n%s" % traceback.format_exc() )

    # Used in UpdateThread
    def UpdateVRayEnabledServers( self, configFile, servers ):
        try:
            if os.path.exists( configFile ):
                config = ConfigParser.ConfigParser()
                config.read( configFile )
                section = "EnabledDRServers"

                # Remove all options including this section
                config.remove_section( section )

                # Add the new options, including this section
                config.add_section( section )

                stringList = ""
                length = len( servers )

                # Example of the section in VRay.ini file: "enabledServers="0, 1, 2,..., 8"
                if length == 1:
                    stringList = "0"
                elif length > 1:
                    stringList = "\"0"
                    for i in range( 1, length ):
                        stringList = stringList + ", %s" % i

                    stringList = stringList + "\""
                else:
                    stringList = "-1"

                config.set( section, "enabledservers", stringList )

                with open( configFile, 'wb' ) as configFile:
                    config.write( configFile )
        except:
            print( "Failed to update the VRay ini file.\n%s" % traceback.format_exc() )

    def NotifyJobStateChanged( self, jobState ):
        # self forces the message box to be on top of the dialog window
        MessageBox.Show( self, "The spawner job is no longer active, it is now %s." % jobState, "Warning", MessageBoxButtons.OK )
        self.ResetSpawnerControls()

    def ResetSpawnerControls( self ):
        self.renderStarted = False
        self.SpawnerJobIDTextBox.Text = ""
        self.SpawnerJobStatusTextBox.Text = ""
        self.ActiveServersTextBox.Text = ""

        self.ReserveServersButton.Enabled = True
        self.StartRenderButton.Enabled = False
        self.ReleaseServersButton.Enabled = False

    # Automatically sets sequential tab index
    def AddTabIndex( self, control ):
        control.TabIndex = self.tabIndex
        self.tabIndex += 1

    def GetVRayIniFile( self ):
        return os.path.expandvars( "%ProgramData%/ASGVIS/V-Ray For Rhino.ini" )

    def WriteStickySettings( self ):
        section = "Sticky"
        try:
            print( "Writing sticky settings..." )
            config = ConfigParser.ConfigParser()
            config.add_section( section )

            config.set( section, "Department", self.DepartmentTextBox.Text )
            config.set( section, "Pool", self.PoolComboBox.Text )
            config.set( section, "SecondaryPool", self.SecondaryPoolComboBox.Text )
            config.set( section, "Group", self.GroupComboBox.Text )
            config.set( section, "Priority", self.PriorityNumericUpDown.Text )
            config.set( section, "LimitGroups", self.LimitsTextBox.Text )
            config.set( section, "MachineList", self.MachineListTextBox.Text )
            config.set( section, "TaskTimeout", self.TaskTimeoutNumericUpDown.Value )
            config.set( section, "IsBlacklist", self.IsBlacklistCheckBox.Checked )
            config.set( section, "IsInterruptible", self.IsJobInterruptibleCheckBox.Checked )

            config.set( section, "MaximumServers", self.MaxServersNumericUpDown.Value )
            config.set( section, "UseServerIP", self.UseServerIPCheckBox.Checked )
            
            fileHandle = open( self.deadlineStickySettings, "w" )
            config.write( fileHandle )
            fileHandle.close()
        except:
            print( "Could not write sticky settings\n%s" % traceback.format_exc() )

    def ReadStickySettings( self ):
        section = "Sticky"
        try:
            if os.path.isfile( self.deadlineStickySettings ):
                config = ConfigParser.ConfigParser()
                config.read( self.deadlineStickySettings )
                print( "Reading sticky settings from %s" % self.deadlineStickySettings )

                if config.has_section( section ):
                    if config.has_option( section, "Department" ):
                        self.DepartmentTextBox.Text = config.get( section, "Department" )
                    if config.has_option( section, "Pool" ):
                        self.PoolComboBox.Text = config.get( section, "Pool" )
                    if config.has_option( section, "SecondaryPool" ):
                        self.SecondaryPoolComboBox.Text = config.get( section, "SecondaryPool" )
                    if config.has_option( section, "Group" ):
                        self.GroupComboBox.Text = config.get( section, "Group" )
                    if config.has_option( section, "Priority" ):
                        self.PriorityNumericUpDown.Value = int( config.get( section, "Priority" ) )
                    if config.has_option( section, "LimitGroups" ):
                        self.LimitsTextBox.Text = config.get( section, "LimitGroups" )
                    if config.has_option( section, "MachineList" ):
                        self.MachineListTextBox.Text = config.get( section, "MachineList" )
                    if config.has_option( section, "TaskTimeout" ):
                        self.TaskTimeoutNumericUpDown.Value = int( config.get( section, "TaskTimeout" ) )
                    if config.has_option( section, "IsBlacklist" ):
                        self.IsBlacklistCheckBox.Checked = ( config.get( section, "IsBlacklist" ).lower() == "true" )
                    if config.has_option( section, "IsInterruptible" ):
                        self.IsJobInterruptibleCheckBox.Checked = ( config.get( section, "IsInterruptible" ).lower() == "true" )

                    if config.has_option( section, "MaximumServers" ):
                        self.MaxServersNumericUpDown.Value = int( config.get( section, "MaximumServers" ) )
                    if config.has_option( section, "UseServerIP" ):
                        self.UseServerIPCheckBox.Checked = ( config.get( section, "UseServerIP" ).lower() == "true" )
        except:
            print( "Could not read sticky settings\n%s" % traceback.format_exc() )

    def InitJobDescriptionUI( self ):
        self.JobDescriptionGroupBox = GroupBox()

        self.NameLabel = Label()
        self.NameTextBox = TextBox()
        self.CommentLabel = Label()
        self.CommentTextBox = TextBox()
        self.DepartmentLabel = Label()
        self.DepartmentTextBox = TextBox()

        self.JobDescriptionGroupBox.Controls.Add( self.DepartmentTextBox )
        self.JobDescriptionGroupBox.Controls.Add( self.DepartmentLabel )
        self.JobDescriptionGroupBox.Controls.Add( self.CommentTextBox )
        self.JobDescriptionGroupBox.Controls.Add( self.CommentLabel )
        self.JobDescriptionGroupBox.Controls.Add( self.NameTextBox )
        self.JobDescriptionGroupBox.Controls.Add( self.NameLabel )

        self.JobDescriptionGroupBox.Location = Point( 12, 13 )
        self.JobDescriptionGroupBox.Name = "JobDescriptionGroupBox"
        self.JobDescriptionGroupBox.Size = Size( 460, 103 )
        self.JobDescriptionGroupBox.Text = "Job Description"

        self.NameLabel.AutoSize = True
        self.NameLabel.Location = Point( 7, 20 )
        self.NameLabel.Name = "NameLabel"
        self.NameLabel.Size = Size( 55, 13 )
        self.NameLabel.Text = "Job Name"

        self.NameTextBox.Location = Point( 115, 17 )
        self.NameTextBox.Name = "NameTextBox"
        self.NameTextBox.Size = Size( 334, 20 )
        self.NameTextBox.Text = "V-Ray Spawner Job (Rhino)"
        self.AddTabIndex( self.NameTextBox )

        self.CommentLabel.AutoSize = True
        self.CommentLabel.Location = Point( 7, 49 )
        self.CommentLabel.Name = "CommentLabel"
        self.CommentLabel.Size = Size( 51, 13 )
        self.CommentLabel.Text = "Comment"

        self.CommentTextBox.Location = Point( 115, 46 )
        self.CommentTextBox.Name = "CommentTextBox"
        self.CommentTextBox.Size = Size( 334, 20 )
        self.AddTabIndex( self.CommentTextBox )

        self.DepartmentLabel.AutoSize = True
        self.DepartmentLabel.Location = Point( 7, 78 )
        self.DepartmentLabel.Name = "DepartmentLabel"
        self.DepartmentLabel.Size = Size( 62, 13 )
        self.DepartmentLabel.Text = "Department"

        self.DepartmentTextBox.Location = Point( 115, 75 )
        self.DepartmentTextBox.Name = "DepartmentTextBox"
        self.DepartmentTextBox.Size = Size( 334, 20 )
        self.AddTabIndex( self.DepartmentTextBox )

    def InitJobOptionsUI( self ):
        self.JobOptionsGroupBox = GroupBox()

        self.PoolLabel = Label()
        self.PoolComboBox = ComboBox()
        self.SecondaryPoolLabel = Label()
        self.SecondaryPoolComboBox = ComboBox()
        self.GroupLabel = Label()
        self.GroupComboBox = ComboBox()
        self.PriorityLabel = Label()
        self.PriorityNumericUpDown = NumericUpDown()
        self.PriorityTrackBar = TrackBar()
        self.LimitsLabel = Label()
        self.LimitsTextBox = TextBox()
        self.LimitsButton = Button()
        self.MachineListLabel = Label()
        self.MachineListTextBox = TextBox()
        self.MachineListButton = Button()
        self.TaskTimeoutLabel = Label()
        self.TaskTimeoutNumericUpDown = NumericUpDown()
        self.TaskTimeoutTrackBar = TrackBar()
        self.IsBlacklistCheckBox = CheckBox()
        self.IsJobInterruptibleCheckBox = CheckBox()

        self.JobOptionsGroupBox.Controls.Add( self.IsJobInterruptibleCheckBox )
        self.JobOptionsGroupBox.Controls.Add( self.IsBlacklistCheckBox )
        self.JobOptionsGroupBox.Controls.Add( self.TaskTimeoutTrackBar )
        self.JobOptionsGroupBox.Controls.Add( self.TaskTimeoutNumericUpDown )
        self.JobOptionsGroupBox.Controls.Add( self.TaskTimeoutLabel )
        self.JobOptionsGroupBox.Controls.Add( self.MachineListButton )
        self.JobOptionsGroupBox.Controls.Add( self.MachineListTextBox )
        self.JobOptionsGroupBox.Controls.Add( self.MachineListLabel )
        self.JobOptionsGroupBox.Controls.Add( self.LimitsButton )
        self.JobOptionsGroupBox.Controls.Add( self.LimitsTextBox )
        self.JobOptionsGroupBox.Controls.Add( self.LimitsLabel )
        self.JobOptionsGroupBox.Controls.Add( self.PriorityTrackBar )
        self.JobOptionsGroupBox.Controls.Add( self.PriorityNumericUpDown )
        self.JobOptionsGroupBox.Controls.Add( self.PriorityLabel )
        self.JobOptionsGroupBox.Controls.Add( self.GroupComboBox )
        self.JobOptionsGroupBox.Controls.Add( self.GroupLabel )
        self.JobOptionsGroupBox.Controls.Add( self.SecondaryPoolComboBox )
        self.JobOptionsGroupBox.Controls.Add( self.SecondaryPoolLabel )
        self.JobOptionsGroupBox.Controls.Add( self.PoolComboBox )
        self.JobOptionsGroupBox.Controls.Add( self.PoolLabel )

        self.JobOptionsGroupBox.Location = Point( 12, 123 )
        self.JobOptionsGroupBox.Name = "JobOptionsGroupBox"
        self.JobOptionsGroupBox.Size = Size( 460, 270 )
        self.JobOptionsGroupBox.Text = "Job Scheduling"

        self.PoolLabel.AutoSize = True
        self.PoolLabel.Location = Point( 7, 20 )
        self.PoolLabel.Name = "PoolLabel"
        self.PoolLabel.Size = Size( 28, 13 )
        self.PoolLabel.Text = "Pool"

        self.PoolComboBox.DropDownStyle = ComboBoxStyle.DropDownList
        self.PoolComboBox.FormattingEnabled = True
        self.PoolComboBox.Location = Point( 115, 17 )
        self.PoolComboBox.Name = "PoolComboBox"
        self.PoolComboBox.Size = Size( 121, 21 )
        self.AddTabIndex( self.PoolComboBox )
        for pool in self.pools:
            self.PoolComboBox.Items.Add( pool )
        self.PoolComboBox.SelectedIndex = 0

        self.SecondaryPoolLabel.AutoSize = True
        self.SecondaryPoolLabel.Location = Point( 7, 49 )
        self.SecondaryPoolLabel.Name = "SecondaryPoolLabel"
        self.SecondaryPoolLabel.Size = Size( 82, 13 )
        self.SecondaryPoolLabel.Text = "Secondary Pool"

        self.SecondaryPoolComboBox.DropDownStyle = ComboBoxStyle.DropDownList
        self.SecondaryPoolComboBox.FormattingEnabled = True
        self.SecondaryPoolComboBox.Location = Point( 115, 46 )
        self.SecondaryPoolComboBox.Name = "SecondaryPoolComboBox"
        self.SecondaryPoolComboBox.Size = Size( 121, 21 )
        self.AddTabIndex( self.SecondaryPoolComboBox )
        for pool in self.secondaryPools:
            self.SecondaryPoolComboBox.Items.Add( pool )
        self.SecondaryPoolComboBox.SelectedIndex = 0

        self.GroupLabel.AutoSize = True
        self.GroupLabel.Location = Point( 7, 78 )
        self.GroupLabel.Name = "GroupLabel"
        self.GroupLabel.Size = Size( 36, 13 )
        self.GroupLabel.Text = "Group"

        self.GroupComboBox.DropDownStyle = ComboBoxStyle.DropDownList
        self.GroupComboBox.FormattingEnabled = True
        self.GroupComboBox.Location = Point( 115, 75 )
        self.GroupComboBox.Name = "GroupComboBox"
        self.GroupComboBox.Size = Size( 121, 21 )
        self.AddTabIndex( self.GroupComboBox )
        for group in self.groups:
            self.GroupComboBox.Items.Add( group )
        self.GroupComboBox.SelectedIndex = 0

        self.PriorityLabel.AutoSize = True
        self.PriorityLabel.Location = Point( 7, 107 )
        self.PriorityLabel.Name = "PriorityLabel"
        self.PriorityLabel.Size = Size( 38, 13 )
        self.PriorityLabel.Text = "Priority"

        self.PriorityNumericUpDown.Location = Point( 115, 105 )
        self.PriorityNumericUpDown.Maximum = self.maximumPriority
        self.PriorityNumericUpDown.Minimum = 1
        self.PriorityNumericUpDown.Name = "PriorityNumericUpDown"
        self.PriorityNumericUpDown.Size = Size( 100, 20 )
        self.PriorityNumericUpDown.Value = self.maximumPriority / 2
        self.PriorityNumericUpDown.ValueChanged += self.UpdatePriority
        self.AddTabIndex( self.PriorityNumericUpDown )

        self.PriorityTrackBar.Location = Point( 221, 105 )
        self.PriorityTrackBar.Maximum = self.maximumPriority
        self.PriorityTrackBar.Minimum = 1
        self.PriorityTrackBar.Name = "PriorityTrackBar"
        self.PriorityTrackBar.Size = Size( 228, 45 )
        self.PriorityTrackBar.TabStop = False
        self.PriorityTrackBar.TickStyle = TickStyle_NONE
        self.PriorityTrackBar.Value = self.maximumPriority / 2
        self.PriorityTrackBar.ValueChanged += self.UpdatePriority

        self.LimitsLabel.AutoSize = True
        self.LimitsLabel.Location = Point( 7, 136 )
        self.LimitsLabel.Name = "LimitsLabel"
        self.LimitsLabel.Size = Size( 33, 13 )
        self.LimitsLabel.Text = "Limits"

        self.LimitsTextBox.Location = Point( 115, 136 )
        self.LimitsTextBox.Name = "LimitsTextBox"
        self.LimitsTextBox.Size = Size( 284, 20 )
        self.AddTabIndex( self.LimitsTextBox )

        self.LimitsButton.Location = Point( 405, 135 )
        self.LimitsButton.Name = "LimitsButton"
        self.LimitsButton.Size = Size( 44, 23 )
        self.LimitsButton.Text = "..."
        self.LimitsButton.UseVisualStyleBackColor = True
        self.AddTabIndex( self.LimitsButton )
        self.LimitsButton.Click += self.GetLimitsFromDeadline

        self.MachineListLabel.AutoSize = True
        self.MachineListLabel.Location = Point( 7, 165 )
        self.MachineListLabel.Name = "MachineListLabel"
        self.MachineListLabel.Size = Size( 67, 13 )
        self.MachineListLabel.Text = "Machine List"

        self.MachineListTextBox.Location = Point( 115, 162 )
        self.MachineListTextBox.Name = "MachineListTextBox"
        self.MachineListTextBox.Size = Size( 284, 20 )
        self.AddTabIndex( self.MachineListTextBox )

        self.MachineListButton.Location = Point( 405, 161 )
        self.MachineListButton.Name = "MachineListButton"
        self.MachineListButton.Size = Size( 44, 23 )
        self.MachineListButton.Text = "..."
        self.MachineListButton.UseVisualStyleBackColor = True
        self.AddTabIndex( self.MachineListButton )
        self.MachineListButton.Click += self.GetMachineListFromDeadline

        self.TaskTimeoutLabel.AutoSize = True
        self.TaskTimeoutLabel.Location = Point( 7, 194 )
        self.TaskTimeoutLabel.Name = "TaskTimeoutLabel"
        self.TaskTimeoutLabel.Size = Size( 72, 13 )
        self.TaskTimeoutLabel.Text = "Task Timeout"

        self.TaskTimeoutNumericUpDown.Location = Point( 115, 192 )
        self.TaskTimeoutNumericUpDown.Maximum = 1000000
        self.TaskTimeoutNumericUpDown.Minimum = 0
        self.TaskTimeoutNumericUpDown.Name = "TaskTimeoutNumericUpDown"
        self.TaskTimeoutNumericUpDown.Size = Size( 100, 20 )
        self.TaskTimeoutNumericUpDown.ValueChanged += self.UpdateTaskTimeout
        self.AddTabIndex( self.TaskTimeoutNumericUpDown )

        self.TaskTimeoutTrackBar.Location = Point( 222, 192 )
        self.TaskTimeoutTrackBar.Maximum = 1000000
        self.TaskTimeoutTrackBar.Minimum = 0
        self.TaskTimeoutTrackBar.Name = "TaskTimeoutTrackBar"
        self.TaskTimeoutTrackBar.Size = Size( 227, 45 )
        self.TaskTimeoutTrackBar.TabStop = False
        self.TaskTimeoutTrackBar.TickStyle = TickStyle_NONE
        self.TaskTimeoutTrackBar.ValueChanged += self.UpdateTaskTimeout

        self.IsBlacklistCheckBox.AutoSize = True
        self.IsBlacklistCheckBox.Location = Point( 115, 221 )
        self.IsBlacklistCheckBox.Name = "IsBlacklistCheckBox"
        self.IsBlacklistCheckBox.Size = Size( 149, 17 )
        self.IsBlacklistCheckBox.Text = "Machine List Is A Blacklist"
        self.IsBlacklistCheckBox.UseVisualStyleBackColor = True
        self.AddTabIndex( self.IsBlacklistCheckBox )

        self.IsJobInterruptibleCheckBox.AutoSize = True
        self.IsJobInterruptibleCheckBox.Location = Point( 115, 246 )
        self.IsJobInterruptibleCheckBox.Name = "IsJobInterruptibleCheckBox"
        self.IsJobInterruptibleCheckBox.Size = Size( 112, 17 )
        self.IsJobInterruptibleCheckBox.Text = "Job Is Interruptible"
        self.IsJobInterruptibleCheckBox.UseVisualStyleBackColor = True
        self.AddTabIndex( self.IsJobInterruptibleCheckBox )

    def InitVRaySpawnerUI( self ):
        self.VRaySpawnerGroupBox = GroupBox()

        self.MaxServersLabel = Label()
        self.MaxServersNumericUpDown = NumericUpDown()
        self.MaxServersTrackBar = TrackBar()
        self.UseServerIPCheckBox = CheckBox()
        self.SpawnerJobIDLabel = Label()
        self.SpawnerJobIDTextBox = TextBox()
        self.SpawnerJobStatusLabel = Label()
        self.SpawnerJobStatusTextBox = TextBox()
        self.ActiveServersLabel = Label()
        self.ActiveServersTextBox = TextBox()

        self.VRaySpawnerGroupBox.Controls.Add( self.ActiveServersTextBox )
        self.VRaySpawnerGroupBox.Controls.Add( self.ActiveServersLabel )
        self.VRaySpawnerGroupBox.Controls.Add( self.SpawnerJobStatusTextBox )
        self.VRaySpawnerGroupBox.Controls.Add( self.SpawnerJobStatusLabel )
        self.VRaySpawnerGroupBox.Controls.Add( self.SpawnerJobIDTextBox )
        self.VRaySpawnerGroupBox.Controls.Add( self.SpawnerJobIDLabel )
        self.VRaySpawnerGroupBox.Controls.Add( self.UseServerIPCheckBox )
        self.VRaySpawnerGroupBox.Controls.Add( self.MaxServersTrackBar )
        self.VRaySpawnerGroupBox.Controls.Add( self.MaxServersNumericUpDown )
        self.VRaySpawnerGroupBox.Controls.Add( self.MaxServersLabel )

        self.VRaySpawnerGroupBox.Location = Point( 12, 400 )
        self.VRaySpawnerGroupBox.Name = "VRaySpawnerGroupBox"
        self.VRaySpawnerGroupBox.Size = Size( 460, 220 )
        self.VRaySpawnerGroupBox.Text = "V-Ray Spawner Options"

        self.MaxServersLabel.AutoSize = True
        self.MaxServersLabel.Location = Point( 7, 20 )
        self.MaxServersLabel.Name = "MaxServersLabel"
        self.MaxServersLabel.Size = Size( 90, 13 )
        self.MaxServersLabel.Text = "Maximum Servers"

        self.MaxServersNumericUpDown.Location = Point( 115, 18 )
        self.MaxServersNumericUpDown.Maximum = 100
        self.MaxServersNumericUpDown.Minimum = 1
        self.MaxServersNumericUpDown.Name = "MaxServersNumericUpDown"
        self.MaxServersNumericUpDown.Size = Size( 102, 20 )
        self.MaxServersNumericUpDown.Value = 10
        self.MaxServersNumericUpDown.ValueChanged += self.UpdateMaxServers
        self.AddTabIndex( self.MaxServersNumericUpDown )

        self.MaxServersTrackBar.Location = Point( 223, 20 )
        self.MaxServersTrackBar.Maximum = 100
        self.MaxServersTrackBar.Minimum = 1
        self.MaxServersTrackBar.Name = "MaxServersTrackBar"
        self.MaxServersTrackBar.Size = Size( 226, 45 )
        self.MaxServersTrackBar.TabStop = False
        self.MaxServersTrackBar.TickStyle = TickStyle_NONE
        self.MaxServersTrackBar.Value = 10
        self.MaxServersTrackBar.ValueChanged += self.UpdateMaxServers

        self.UseServerIPCheckBox.AutoSize = True
        self.UseServerIPCheckBox.Location = Point( 115, 51 )
        self.UseServerIPCheckBox.Name = "UseServerIPCheckBox"
        self.UseServerIPCheckBox.Size = Size( 239, 17 )
        self.UseServerIPCheckBox.Text = "Use Server IP Address Instead of Host Name"
        self.UseServerIPCheckBox.UseVisualStyleBackColor = True
        self.AddTabIndex( self.UseServerIPCheckBox )

        self.SpawnerJobIDLabel.AutoSize = True
        self.SpawnerJobIDLabel.Location = Point( 6, 82 )
        self.SpawnerJobIDLabel.Name = "SpawnerJobIDLabel"
        self.SpawnerJobIDLabel.Size = Size( 83, 13 )
        self.SpawnerJobIDLabel.Text = "Spawner Job ID"

        self.SpawnerJobIDTextBox.Location = Point( 115, 79 )
        self.SpawnerJobIDTextBox.Name = "SpawnerJobIDTextBox"
        self.SpawnerJobIDTextBox.ReadOnly = True
        self.SpawnerJobIDTextBox.Size = Size( 334, 20 )
        self.SpawnerJobIDTextBox.TabStop = False

        self.SpawnerJobStatusLabel.AutoSize = True
        self.SpawnerJobStatusLabel.Location = Point( 6, 108 )
        self.SpawnerJobStatusLabel.Name = "SpawnerJobStatusLabel"
        self.SpawnerJobStatusLabel.Size = Size( 102, 13 )
        self.SpawnerJobStatusLabel.Text = "Spawner Job Status"

        self.SpawnerJobStatusTextBox.Location = Point( 115, 105 )
        self.SpawnerJobStatusTextBox.Name = "SpawnerJobStatusTextBox"
        self.SpawnerJobStatusTextBox.ReadOnly = True
        self.SpawnerJobStatusTextBox.Size = Size( 334, 20 )
        self.SpawnerJobStatusTextBox.TabStop = False

        self.ActiveServersLabel.AutoSize = True
        self.ActiveServersLabel.Location = Point( 6, 166 )
        self.ActiveServersLabel.Name = "ActiveServersLabel"
        self.ActiveServersLabel.Size = Size( 76, 13 )
        self.ActiveServersLabel.Text = "Active Servers"

        self.ActiveServersTextBox.Location = Point( 115, 136 )
        self.ActiveServersTextBox.Multiline = True
        self.ActiveServersTextBox.Name = "ActiveServersTextBox"
        self.ActiveServersTextBox.ReadOnly = True
        self.ActiveServersTextBox.ScrollBars = ScrollBars.Vertical
        self.ActiveServersTextBox.Size = Size( 334, 74 )
        self.ActiveServersTextBox.TabStop = False

    def InitButtonPanelUI( self ):
        self.ButtonPanel = Panel()

        self.ReserveServersButton = Button()
        self.StartRenderButton = Button()
        self.ReleaseServersButton = Button()

        self.ButtonPanel.Controls.Add( self.ReleaseServersButton )
        self.ButtonPanel.Controls.Add( self.StartRenderButton )
        self.ButtonPanel.Controls.Add( self.ReserveServersButton )

        self.ButtonPanel.Location = Point( 12, 625 )
        self.ButtonPanel.Name = "ButtonPanel"
        self.ButtonPanel.Size = Size( 400, 30 )

        self.ReserveServersButton.Location = Point( 3, 3 )
        self.ReserveServersButton.Name = "ReserveServersButton"
        self.ReserveServersButton.Size = Size( 125, 23 )
        self.ReserveServersButton.Text = "Reserve Servers"
        self.ReserveServersButton.UseVisualStyleBackColor = True
        self.ReserveServersButton.Click += self.SubmitJob
        self.AddTabIndex( self.ReserveServersButton )

        self.StartRenderButton.Enabled = False
        self.StartRenderButton.Location = Point( 134, 3 )
        self.StartRenderButton.Name = "StartRenderButton"
        self.StartRenderButton.Size = Size( 125, 23 )
        self.StartRenderButton.Text = "Start Render"
        self.StartRenderButton.UseVisualStyleBackColor = True
        self.StartRenderButton.Click += self.StartRender
        self.AddTabIndex( self.StartRenderButton )

        self.ReleaseServersButton.Enabled = False
        self.ReleaseServersButton.Location = Point( 265, 3 )
        self.ReleaseServersButton.Name = "ReleaseServersButton"
        self.ReleaseServersButton.Size = Size( 125, 23 )
        self.ReleaseServersButton.Text = "Release Servers"
        self.ReleaseServersButton.UseVisualStyleBackColor = True
        self.ReleaseServersButton.Click += self.CompleteJob
        self.AddTabIndex( self.ReleaseServersButton )

    def InitFormUI( self ):
        # Form
        self.FormBorderStyle = FormBorderStyle.FixedSingle;
        self.Text = "Submit V-Ray DBR to Deadline"
        self.Width = 490
        self.Height = 690
        self.MinimizeBox = True
        self.MaximizeBox = False
        self.CenterToScreen()
        self.FormClosing += self.CloseForm

        # Add the controls to the form
        self.Controls.Add( self.JobDescriptionGroupBox )
        self.Controls.Add( self.JobOptionsGroupBox )
        self.Controls.Add( self.VRaySpawnerGroupBox )
        self.Controls.Add( self.ButtonPanel )

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
    creationflags = 0
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
        
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen( arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags )
    proc.stdin.close()
    proc.stderr.close()

    output = proc.stdout.read()

    return output