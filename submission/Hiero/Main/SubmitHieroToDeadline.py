# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import json
import os
import shutil
import subprocess
import tempfile

from distutils.util import strtobool

try:
    # Nuke 11 onwards uses PySide2
    from PySide2.QtCore import QSettings, Qt
    from PySide2.QtWidgets import  QCheckBox, QComboBox, QDialog, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget
    print("Deadline: Using PySide2")
except ImportError:
    from PySide.QtCore import QSettings, Qt
    from PySide.QtGui import QCheckBox, QComboBox, QDialog, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget
    print("Deadline: Using PySide")

import hiero.core
import hiero.ui

from hiero.core import Clip, Sequence, TaskBase, TrackItem
from hiero.exporters.FnSubmission import Submission

# Hiero is a multi scene application, and they don't provide a way to determine which
# scene file is actually being exported, so we can't pass a scene path into pipeline tools.
# Instead, user's pipeline settings will persist locally, instead of via scene file.
HIERO_PIPELINE_SCENE = 'default_hiero_scene'

def GetDeadlineCommand( useDeadlineBg=False ):
    """
    Returns the path to DeadlineCommand.
    :param useDeadlineBg: If enabled this will return the path to DeadlineCommandBg instead of DeadlineCommand
    :return: The path to the DeadlineCommand Executable
    """
    deadlineBin = ""
    try:
        deadlineBin = os.environ[ 'DEADLINE_PATH' ]
    except KeyError:
        # if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass

    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if not deadlineBin and os.path.isfile( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f:
            deadlineBin = f.read().strip()

    exeName = "deadlinecommand"
    if useDeadlineBg:
        exeName += "bg"

    deadlineCommand = os.path.join( deadlineBin, exeName )

    return deadlineCommand


def CreateArgFile( arguments, tmpDir ):
    """
    Creates a utf-8 encoded file with each argument in arguments on a separate line.
    :param arguments: The list of arguments that are to be added to the file
    :param tmpDir: The directory that the file should be written to.
    :return: The path to the argument file that was created.
    """
    tmpFile = os.path.join( tmpDir, "args.txt" )

    with io.open( tmpFile, 'w', encoding="utf-8-sig" ) as fileHandle:
        fileHandle.write( u"\n".join( arguments ) )

    return tmpFile


def CallDeadlineCommand( arguments, hideWindow=True, useArgFile=False, useDeadlineBg=False ):
    """
    Run DeadlineCommand with the specified arguments returning the standard out
    :param arguments: The list of arguments that are to be run
    :param hideWindow: If enabled all popups will be hidden
    :param useArgFile: If enabled all arguments will be written to a file and then passed in to deadline command
    :param useDeadlineBg: If enabled DeadlineCommandbg will be used instead of DeadlineCommand
    :return: The stdout from the DeadlineCommand Call
    """
    deadlineCommand = GetDeadlineCommand( useDeadlineBg )
    tmpdir = None

    if useArgFile or useDeadlineBg:
        tmpdir = tempfile.mkdtemp()

    if useDeadlineBg:
        arguments = [ "-outputfiles", os.path.join( tmpdir, "dlout.txt" ), os.path.join( tmpdir, "dlexit.txt" ) ] + arguments

    startupinfo = None
    creationflags = 0

    if os.name == 'nt':
        if hideWindow:
            # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
            if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            # still show top-level windows, but don't show a console window
            CREATE_NO_WINDOW = 0x08000000  # MSDN process creation flag
            creationflags = CREATE_NO_WINDOW

    if useArgFile:
        arguments = [ CreateArgFile( arguments, tmpdir ) ]

    arguments.insert( 0 , deadlineCommand )

    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen( arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags )
    output, errors = proc.communicate()

    if useDeadlineBg:
        with io.open( os.path.join( tmpdir, "dlout.txt" ), 'r', encoding='utf-8' ) as fileHandle:
            output = fileHandle.read()

    if tmpdir:
        try:
            shutil.rmtree( tmpdir )
        except OSError:
            print( 'Failed to remove temp directory: "%s"' % tmpdir )

    return output.strip()


class DeadlineRenderTask(TaskBase):
    def __init__(self, jobType, initDict, scriptPath, tempPath, settings):
        super(DeadlineRenderTask, self).__init__(initDict)
        # Set the submission settings.
        self.tempPath = tempPath
        self.settings = settings
        
        # Set the script path.
        self.scriptPath = scriptPath

        self.submissionInfo = {}
        
        # Figure out the job name from the script file.
        self.jobName = os.path.splitext(os.path.basename(scriptPath))[0]
        tempJobName = self.settings.value("JobName")
        if tempJobName != "":
            self.jobName = tempJobName + " - " + self.jobName
        
        # Figure out the start and end frames.
        startFrame = 0
        endFrame = 0
        if isinstance(self._item, Sequence):
            startFrame = self._sequence.inTime()
            endFrame = self._sequence.outTime()

        elif isinstance( self._item, ( Clip, TrackItem ) ):
            try:
                startFrame = initDict['startFrame']
                endFrame = initDict['endFrame']
            except KeyError:
                # The output range reported by Hiero does not appear to be correct when ignoreRetimes=False is
                # provided as a parameter, therefore we always use `ignoreRetimes=True` and only use this as a fall back.

                startFrame, endFrame = self.outputRange(ignoreRetimes=True, clampToSource=False)
        
        # Build the frame list from the start and end frames.
        self.frameList = str(startFrame)
        if startFrame != endFrame:
            self.frameList = self.frameList + "-" + str(endFrame)
            
        # Figure out the output path.
        self.outputPath = self.resolvedExportPath()
        
        # Figure out the chunksize.
        self.chunkSize = self.settings.value("FramesPerTask")
        if hiero.core.isVideoFileExtension(os.path.splitext(self.outputPath)[1].lower()):
            self.chunkSize = endFrame - startFrame + 1
    
    def startTask(self):
        print( "==============================================================" )
        print( "Preparing job for submission: " + self.jobName )
        print( "Script path: " + self.scriptPath )
        print( "Frame list: " + self.frameList )
        print( "Chunk size: " + str(self.chunkSize) )
        print( "Output path: " + self.outputPath )
        
        # Create the job info file.
        jobInfoFile = self.tempPath + "/hiero_submit_info.job"
        fileHandle = open( jobInfoFile, "w" )
        fileHandle.write( "Plugin=Nuke\n" )
        fileHandle.write( "Name=%s\n" % self.jobName )
        fileHandle.write( "Comment=%s\n" % self.settings.value("Comment") )
        fileHandle.write( "Department=%s\n" % self.settings.value("Department") )
        fileHandle.write( "Pool=%s\n" % self.settings.value("Pool") )
        fileHandle.write( "SecondaryPool=%s\n" % self.settings.value("SecondaryPool") )
        fileHandle.write( "Group=%s\n" % self.settings.value("Group") )
        fileHandle.write( "Priority=%s\n" % self.settings.value("Priority") )
        fileHandle.write( "MachineLimit=%s\n" % self.settings.value("MachineLimit") )
        fileHandle.write( "TaskTimeoutMinutes=%s\n" % self.settings.value("TaskTimeout") )
        fileHandle.write( "EnableAutoTimeout=%s\n" % self.settings.value("AutoTaskTimeout") )
        fileHandle.write( "ConcurrentTasks=%s\n" % self.settings.value("ConcurrentTasks") )
        fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % self.settings.value("LimitConcurrentTasks") )
        fileHandle.write( "LimitGroups=%s\n" % self.settings.value("Limits") )
        fileHandle.write( "OnJobComplete=%s\n" % self.settings.value("OnJobComplete") )
        fileHandle.write( "Frames=%s\n" % self.frameList )
        fileHandle.write( "ChunkSize=%s\n" % self.chunkSize )
        fileHandle.write( "OutputFilename0=%s\n" % self.outputPath )
        
        if strtobool(self.settings.value("SubmitSuspended")):
            fileHandle.write( "InitialStatus=Suspended\n" )
            
        if strtobool(self.settings.value("IsBlacklist")):
            fileHandle.write( "Blacklist=%s\n" % self.settings.value("MachineList") )
        else:
            fileHandle.write( "Whitelist=%s\n" % self.settings.value("MachineList") )
        fileHandle.close()

        self.concatenatePipelineTools( self.settings.value("IntegrationDir"), jobInfoFile, self.jobName )

        # Create the plugin info file.
        pluginInfoFile = self.tempPath +"/hiero_plugin_info.job"
        fileHandle = open( pluginInfoFile, "w" )
        if not strtobool(self.settings.value("SubmitScript")):
            fileHandle.write( "SceneFile=%s\n" % self.scriptPath )
        fileHandle.write( "Version=%s\n" % self.settings.value("Version") )
        fileHandle.write( "Threads=%s\n" % self.settings.value("Threads") )
        fileHandle.write( "RamUse=%s\n" % self.settings.value("Memory") )
        fileHandle.write( "Build=%s\n" % self.settings.value("Build") )
        fileHandle.write( "BatchMode=%s\n" % self.settings.value("BatchMode") )
        fileHandle.write( "NukeX=%s\n" % self.settings.value("UseNukeX") )
        fileHandle.write( "ContinueOnError=%s\n" % self.settings.value("ContinueOnError") )
        
        fileHandle.close()
        
        # Submit the job to Deadline
        args = [
            jobInfoFile,
            pluginInfoFile
        ]
        if strtobool(self.settings.value("SubmitScript")):
            args.append( self.scriptPath )
        
        results = CallDeadlineCommand( args, useArgFile=True )
        print( results )
        print( "Job submission complete: " + self.jobName  )


    def concatenatePipelineTools( self, integrationDir, jobInfoPath, batchName ):
        """
        Concatenate pipeline tool settings for the scene to the .job file.
        :param jobInfoPath: Path to the .job file.
        :param batchName: Value of the 'batchName' job info entry, if it is required.
        :return: None
        """
        global HIERO_PIPELINE_SCENE

        jobWriterPath = os.path.join( integrationDir, "JobWriter.py" )
        args = [ "-ExecuteScript", jobWriterPath, "Hiero", "--write", "--scene-path", HIERO_PIPELINE_SCENE, "--job-path", jobInfoPath,
                 "--batch-name", batchName ]

        CallDeadlineCommand( args )

# Create a Submission and add your Task
class DeadlineRenderSubmission(Submission):
    def __init__(self):
        Submission.__init__(self)
        self.dialog = None
        self.lastSelection = ""
        self.settingsFile = ""

        self.submissionInfo = {}
        self.deadlineTemp = ""
        self.integrationDir = ""

        self.pipelineToolStatusLabel = QLabel( "No Pipeline Tools set" )
        self.pipelineToolStatusLabel.setWordWrap( True )

    def initialise(self):
        self.settingsFile = os.path.join(self.findNukeHomeDir(), "deadline_settings.ini")
        print( "Loading settings: " + self.settingsFile )
        
        # Initialize the submission settings.
        self.settings = QSettings(self.settingsFile, QSettings.IniFormat)

        print( "Grabbing submitter info..." )
        try:
            dcOutput = CallDeadlineCommand(
                [ "-prettyJSON", "-GetSubmissionInfo", "Pools", "Groups", "MaxPriority", "TaskLimit", "UserHomeDir",
                  "RepoDir:submission/Hiero/Main", "RepoDir:submission/Integration/Main", ], useDeadlineBg=True )
            output = json.loads( dcOutput, encoding="utf-8" )
        except ValueError as e:
            print( "Unable to get submitter info from Deadline:\n\n" + e.message )
            raise

        if output[ "ok" ]:
            self.submissionInfo = output[ "result" ]
        else:
            raise ValueError( "DeadlineCommand returned a bad result and was unable to grab the submitter info.\n\n" + output[ "result" ] )

        # Get the Deadline temp directory.
        deadlineHome = self.submissionInfo["UserHomeDir"].strip()
        self.deadlineTemp = os.path.join(deadlineHome, "temp")

        self.integrationDir = self.submissionInfo["RepoDirs"]["submission/Integration/Main"].strip()

        # Get maximum priority.
        maximumPriority = self.submissionInfo[ "MaxPriority" ]
        
        # Collect the pools and groups.
        pools = self.submissionInfo[ "Pools" ]
        
        secondaryPools = [ "" ]
        secondaryPools.extend( pools )

        groups = self.submissionInfo[ "Groups" ]

        # Set up the other default arrays.
        onJobComplete = ("Nothing","Archive","Delete")
        nukeVersions = ("6.0","6.1","6.2","6.3","6.4","7.0","7.1","7.2","7.3","7.4","8.0","8.1","8.2","8.3","8.4","9.0","9.1","9.2","9.3","9.4","10.0","10.1","10.2","10.3","10.4","11.0","11.1","11.2","11.3")
        buildsToForce = ("None","32bit","64bit")
        
        # Main Window
        mainWindow = hiero.ui.mainWindow()
        dialog = QDialog(mainWindow)
        self.dialog = dialog
        dialog.setWindowTitle("Submit to Deadline (and render with Nuke)")
        
        # Main Layout
        topLayout = QVBoxLayout()
        dialog.setLayout(topLayout)
        tabWidget = QTabWidget(dialog)
        
        jobTab = QWidget()
        jobTabLayout = QVBoxLayout()
        jobTab.setLayout(jobTabLayout)
        
        # Job Info Layout
        jobInfoGroupBox = QGroupBox("Job Description")
        jobTabLayout.addWidget(jobInfoGroupBox)
        jobInfoLayout = QGridLayout()
        jobInfoGroupBox.setLayout(jobInfoLayout)
        
        # Job Name
        jobInfoLayout.addWidget(QLabel("Job Name"), 0, 0)
        jobNameWidget = QLineEdit(self.settings.value("JobName", ""))
        jobInfoLayout.addWidget(jobNameWidget, 0, 1)
        
        # Comment
        jobInfoLayout.addWidget(QLabel("Comment"), 1, 0)
        commentWidget = QLineEdit(self.settings.value("Comment", ""))
        jobInfoLayout.addWidget(commentWidget, 1, 1)
        
        # Department
        jobInfoLayout.addWidget(QLabel("Department"), 2, 0)
        departmentWidget = QLineEdit(self.settings.value("Department", ""))
        jobInfoLayout.addWidget(departmentWidget, 2, 1)
        
        
        # Job Options Layout
        jobOptionsGroupBox = QGroupBox("Job Options")
        jobTabLayout.addWidget(jobOptionsGroupBox)
        jobOptionsLayout = QGridLayout()
        jobOptionsGroupBox.setLayout(jobOptionsLayout)
        
        # Pool
        jobOptionsLayout.addWidget(QLabel("Pool"), 0, 0)
        poolWidget = QComboBox()
        for pool in pools:
            poolWidget.addItem(pool)
        
        defaultPool = self.settings.value("Pool", "none")
        defaultIndex = poolWidget.findText(defaultPool)
        if defaultIndex != -1:
            poolWidget.setCurrentIndex(defaultIndex)
            
        jobOptionsLayout.addWidget(poolWidget, 0, 1, 1, 3)
        
        # Secondary Pool
        jobOptionsLayout.addWidget(QLabel("Secondary Pool"), 1, 0)
        secondaryPoolWidget = QComboBox()
        for secondaryPool in secondaryPools:
            secondaryPoolWidget.addItem(secondaryPool)
        
        defaultSecondaryPool = self.settings.value("SecondaryPool", "")
        defaultIndex = secondaryPoolWidget.findText(defaultSecondaryPool)
        if defaultIndex != -1:
            secondaryPoolWidget.setCurrentIndex(defaultIndex)
            
        jobOptionsLayout.addWidget(secondaryPoolWidget, 1, 1, 1, 3)
        
        # Group
        jobOptionsLayout.addWidget(QLabel("Group"), 2, 0)
        groupWidget = QComboBox()
        for group in groups:
            groupWidget.addItem(group)
            
        defaultGroup = self.settings.value("Group", "none")
        defaultIndex = groupWidget.findText(defaultGroup)
        if defaultIndex != -1:
            groupWidget.setCurrentIndex(defaultIndex)
            
        jobOptionsLayout.addWidget(groupWidget, 2, 1, 1, 3)
        
        # Priority
        initPriority = int(self.settings.value("Priority", "50"))
        if initPriority > maximumPriority:
            initPriority = maximumPriority / 2
        
        jobOptionsLayout.addWidget(QLabel("Priority"), 3, 0)
        priorityWidget = QSpinBox()
        priorityWidget.setRange(0, maximumPriority)
        priorityWidget.setValue(initPriority)
        jobOptionsLayout.addWidget(priorityWidget, 3, 1)
        
        # Task Timeout
        jobOptionsLayout.addWidget(QLabel("Task Timeout"), 4, 0)
        taskTimeoutWidget = QSpinBox()
        taskTimeoutWidget.setRange(0, 1000000)
        taskTimeoutWidget.setValue(int(self.settings.value("TaskTimeout", "0")))
        jobOptionsLayout.addWidget(taskTimeoutWidget, 4, 1)
        
        # Auto Task Timeout
        autoTaskTimeoutWidget = QCheckBox("Enable Auto Task Timeout")
        autoTaskTimeoutWidget.setChecked(strtobool(self.settings.value("AutoTaskTimeout", "False")))
        jobOptionsLayout.addWidget(autoTaskTimeoutWidget, 4, 2)
        
        # Concurrent Tasks
        jobOptionsLayout.addWidget(QLabel("Concurrent Tasks"), 5, 0)
        concurrentTasksWidget = QSpinBox()
        concurrentTasksWidget.setRange(1, 16)
        concurrentTasksWidget.setValue(int(self.settings.value("ConcurrentTasks", "1")))
        jobOptionsLayout.addWidget(concurrentTasksWidget, 5, 1)
        
        # Limit Tasks To Slave's Task Limit
        limitConcurrentTasksWidget = QCheckBox("Limit Tasks To Slave's Task Limit")
        limitConcurrentTasksWidget.setChecked(strtobool(self.settings.value("LimitConcurrentTasks", "True")))
        jobOptionsLayout.addWidget(limitConcurrentTasksWidget, 5, 2)
        
        # Machine Limit
        jobOptionsLayout.addWidget(QLabel("Machine Limit"), 6, 0)
        machineLimitWidget = QSpinBox()
        machineLimitWidget.setRange(0, 1000000)
        machineLimitWidget.setValue(int(self.settings.value("MachineLimit", "1")))
        jobOptionsLayout.addWidget(machineLimitWidget, 6, 1)
        
        # Machine List Is A Blacklist
        isBlacklistWidget = QCheckBox("Machine List Is A Blacklist")
        isBlacklistWidget.setChecked(strtobool(self.settings.value("IsBlacklist", "False")))
        jobOptionsLayout.addWidget(isBlacklistWidget, 6, 2)
        
        # Machine List
        jobOptionsLayout.addWidget(QLabel("Machine List"), 7, 0)
        machineListWidget = QLineEdit(self.settings.value("MachineList", ""))
        jobOptionsLayout.addWidget(machineListWidget, 7, 1, 1, 2)
        
        def browseMachineList():
            output = CallDeadlineCommand(["-selectmachinelist", str(machineListWidget.text())], False)
            output = output.replace("\r", "").replace("\n", "")
            if output != "Action was cancelled by user":
                machineListWidget.setText(output)
        
        machineListButton = QPushButton("Browse")
        machineListButton.pressed.connect(browseMachineList)
        jobOptionsLayout.addWidget(machineListButton, 7, 3)
        
        # Limits
        jobOptionsLayout.addWidget(QLabel("Limits"), 8, 0)
        limitsWidget = QLineEdit(self.settings.value("Limits", ""))
        jobOptionsLayout.addWidget(limitsWidget, 8, 1, 1, 2)
        
        def browseLimitList():
            output = CallDeadlineCommand(["-selectlimitgroups", str(limitsWidget.text())], False)
            output = output.replace("\r", "").replace("\n", "")
            if output != "Action was cancelled by user":
                limitsWidget.setText(output)
        
        limitsButton = QPushButton("Browse")
        limitsButton.pressed.connect(browseLimitList)
        jobOptionsLayout.addWidget(limitsButton, 8, 3)
        
        # On Job Complete
        jobOptionsLayout.addWidget(QLabel("On Job Complete"), 9, 0)
        onJobCompleteWidget = QComboBox()
        for option in onJobComplete:
            onJobCompleteWidget.addItem(option)
            
        defaultOption = self.settings.value("OnJobComplete", "Nothing")
        defaultIndex = onJobCompleteWidget.findText(defaultOption)
        if defaultIndex != -1:
            onJobCompleteWidget.setCurrentIndex(defaultIndex)
            
        jobOptionsLayout.addWidget(onJobCompleteWidget, 9, 1)
        
        # Submit Job As Suspended
        submitSuspendedWidget = QCheckBox("Submit Job As Suspended")
        submitSuspendedWidget.setChecked(strtobool(self.settings.value("SubmitSuspended", "False")))
        jobOptionsLayout.addWidget(submitSuspendedWidget, 9, 2)

        # Nuke Options
        nukeOptionsGroupBox = QGroupBox("Nuke Options")
        jobTabLayout.addWidget(nukeOptionsGroupBox)
        nukeOptionsLayout = QGridLayout()
        nukeOptionsGroupBox.setLayout(nukeOptionsLayout)
        
        # Version
        nukeOptionsLayout.addWidget(QLabel("Version"), 0, 0)
        versionWidget = QComboBox()
        for version in nukeVersions:
            versionWidget.addItem(version)
            
        defaultVersion = self.settings.value("Version", "7.0")
        defaultIndex = versionWidget.findText(defaultVersion)
        if defaultIndex != -1:
            versionWidget.setCurrentIndex(defaultIndex)
            
        nukeOptionsLayout.addWidget(versionWidget, 0, 1)
        
        # Submit Nuke Script File With Job
        submitScriptWidget = QCheckBox("Submit Nuke Script File With Job")
        submitScriptWidget.setChecked(strtobool(self.settings.value("SubmitScript", "False")))
        nukeOptionsLayout.addWidget(submitScriptWidget, 0, 2)
        
        # Build To Force
        nukeOptionsLayout.addWidget(QLabel("Build To Force"), 1, 0)
        buildWidget = QComboBox()
        for build in buildsToForce:
            buildWidget.addItem(build)
            
        defaultBuild = self.settings.value("Build", "None")
        defaultIndex = buildWidget.findText(defaultBuild)
        if defaultIndex != -1:
            buildWidget.setCurrentIndex(defaultIndex)
            
        nukeOptionsLayout.addWidget(buildWidget, 1, 1)
        
        # Render With NukeX
        useNukeXWidget = QCheckBox("Render With NukeX")
        useNukeXWidget.setChecked(strtobool(self.settings.value("UseNukeX", "False")))
        nukeOptionsLayout.addWidget(useNukeXWidget, 1, 2)
        
        # Max RAM Usage (MB)
        nukeOptionsLayout.addWidget(QLabel("Max RAM Usage (MB)"), 2, 0)
        memoryWidget = QSpinBox()
        memoryWidget.setRange(0, 5000)
        memoryWidget.setValue(int(self.settings.value("Memory", "0")))
        nukeOptionsLayout.addWidget(memoryWidget, 2, 1)
        
        # Continue On Error
        continueOnErrorWidget = QCheckBox("Continue On Error")
        continueOnErrorWidget.setChecked(strtobool(self.settings.value("ContinueOnError", "False")))
        nukeOptionsLayout.addWidget(continueOnErrorWidget, 2, 2)
        
        # Threads
        nukeOptionsLayout.addWidget(QLabel("Threads"), 3, 0)
        threadsWidget = QSpinBox()
        threadsWidget.setRange(0, 256)
        threadsWidget.setValue(int(self.settings.value("Threads", "0")))
        nukeOptionsLayout.addWidget(threadsWidget, 3, 1)
        
        # Use Batch Mode
        batchModeWidget = QCheckBox("Use Batch Mode")
        batchModeWidget.setChecked(strtobool(self.settings.value("BatchMode", "False")))
        nukeOptionsLayout.addWidget(batchModeWidget, 3, 2)
        
        # Frames Per Task
        nukeOptionsLayout.addWidget(QLabel("Frames Per Task"), 4, 0)
        framesPerTaskWidget = QSpinBox()
        framesPerTaskWidget.setRange(1, 1000000)
        framesPerTaskWidget.setValue(int(self.settings.value("FramesPerTask", "1")))
        nukeOptionsLayout.addWidget(framesPerTaskWidget, 4, 1)
        nukeOptionsLayout.addWidget(QLabel("(this only affects non-movie jobs)"), 4, 2)
        
        tabWidget.addTab(jobTab, "Job Options")

        # Button Box (Extra work required to get the custom ordering we want)
        self.pipelineToolStatusLabel.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
        pipelineToolStatus = self.retrievePipelineToolStatus()
        self.updatePipelineToolStatusLabel(pipelineToolStatus)

        integrationButton = QPushButton("Pipeline Tools")
        integrationButton.clicked.connect( self.OpenIntegrationWindow )

        submitButton = QPushButton("Submit")
        submitButton.clicked.connect( dialog.accept )
        submitButton.setDefault( True )

        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect( dialog.reject )

        buttonGroupBox = QGroupBox()
        buttonLayout = QGridLayout()
        buttonLayout.setColumnStretch(0, 1) # Makes the pipeline status label expand, not the buttons
        buttonGroupBox.setLayout(buttonLayout)
        buttonGroupBox.setAlignment( Qt.AlignRight )
        buttonGroupBox.setFlat( True )
        buttonLayout.addWidget(self.pipelineToolStatusLabel, 0, 0)
        buttonLayout.addWidget(integrationButton, 0, 1)
        buttonLayout.addWidget(submitButton, 0, 2)
        buttonLayout.addWidget(cancelButton, 0, 3)

        topLayout.addWidget(tabWidget)
        topLayout.addWidget(buttonGroupBox)

        # Show the dialog.
        result = (dialog.exec_() == QDialog.DialogCode.Accepted)
        if result:
            # Need to pass integration dir path to render task
            self.settings.setValue("IntegrationDir", self.integrationDir)

            self.settings.setValue("JobName", jobNameWidget.text())
            self.settings.setValue("Comment", commentWidget.text())
            self.settings.setValue("Department", departmentWidget.text())
            self.settings.setValue("Pool", poolWidget.currentText())
            self.settings.setValue("SecondaryPool", secondaryPoolWidget.currentText())
            self.settings.setValue("Group", groupWidget.currentText())
            self.settings.setValue("Priority", priorityWidget.value())
            self.settings.setValue("TaskTimeout", taskTimeoutWidget.value())
            self.settings.setValue("AutoTaskTimeout", str(autoTaskTimeoutWidget.isChecked()))
            self.settings.setValue("ConcurrentTasks", concurrentTasksWidget.value())
            self.settings.setValue("LimitConcurrentTasks", str(limitConcurrentTasksWidget.isChecked()))
            self.settings.setValue("MachineLimit", machineLimitWidget.value())
            self.settings.setValue("IsBlacklist", str(isBlacklistWidget.isChecked()))
            self.settings.setValue("MachineList", machineListWidget.text())
            self.settings.setValue("Limits", limitsWidget.text())
            self.settings.setValue("OnJobComplete", onJobCompleteWidget.currentText())
            self.settings.setValue("SubmitSuspended", str(submitSuspendedWidget.isChecked()))
            self.settings.setValue("Version", versionWidget.currentText())
            self.settings.setValue("SubmitScript", str(submitScriptWidget.isChecked()))
            self.settings.setValue("Build", buildWidget.currentText())
            self.settings.setValue("UseNukeX", str(useNukeXWidget.isChecked()))
            self.settings.setValue("FramesPerTask", framesPerTaskWidget.value())
            self.settings.setValue("ContinueOnError", str(continueOnErrorWidget.isChecked()))
            self.settings.setValue("Threads", threadsWidget.value())
            self.settings.setValue("BatchMode", str(batchModeWidget.isChecked()))
            self.settings.setValue("Memory", memoryWidget.value())
            
            print( "Saving settings: " + self.settingsFile )
            self.settings.sync()
        else:
            print( "Submission canceled" )
            self.settings = None
            # Not sure if there is a better way to stop the export process. This works, but it leaves all the tasks
            # in the Queued state.
            self.setError( "Submission was canceled" )
    
    def addJob(self, jobType, initDict, filePath):
        # Only create a task if submission wasn't canceled.
        if self.settings:
            return DeadlineRenderTask( Submission.kCommandLine, initDict, filePath, self.deadlineTemp, self.settings )


    @staticmethod
    def findNukeHomeDir():
        return os.path.normpath(os.path.join( hiero.core.env["HomeDirectory"], ".nuke"))


    def retrievePipelineToolStatus( self ):
        """
        Grabs a status message from the JobWriter that indicates which pipeline tools have settings enabled for the current scene.
        :return: A string representing the status of the pipeline tools for the current scene.
        """
        global HIERO_PIPELINE_SCENE

        jobWriterPath = os.path.join( self.integrationDir, "JobWriter.py" )
        args = [ "-ExecuteScript", jobWriterPath, "Hiero", "--status", "--scene-path", HIERO_PIPELINE_SCENE ]
        statusMessage = CallDeadlineCommand( args )

        return statusMessage


    def updatePipelineToolStatusLabel( self, statusMessage ):
        """
        Updates the pipeline tools status label with a non-empty status message as there's always a status associated with the pipeline tools.
        :param statusMessage: A non-empty string representing the status of the pipeline tools for the current scene.
        :return: None
        """
        if not statusMessage:
            raise ValueError( 'The status message for the pipeline tools label is not allowed to be empty.' )

        if statusMessage.lower().startswith( "error" ):
            self.pipelineToolStatusLabel.setText( "Pipeline Tools Error" )
            print( statusMessage )
        else:
            self.pipelineToolStatusLabel.setText( statusMessage )


    def OpenIntegrationWindow( self ):
        """
        Launches a graphical interface for the pipeline tools, attempts to grab local project management info from the scene, and updates the
        Pipeline Tools status label indicating which project management tools are being used.
        """
        global HIERO_PIPELINE_SCENE

        integrationScript = os.path.join( self.integrationDir, "IntegrationUIStandAlone.py" )
        argArray = [ "-ExecuteScript", integrationScript, "-v", "2", "Hiero", "-d", "Shotgun", "FTrack" ,"NIM", "--path", HIERO_PIPELINE_SCENE ]

        statusMessage = CallDeadlineCommand( argArray, False )
        self.updatePipelineToolStatusLabel( statusMessage )

################################################################################
## DEBUGGING
################################################################################
# submission = DeadlineRenderSubmission()
# submission.initialise()
