from __future__ import print_function
import os
import os.path
import sys
import re
import traceback
import subprocess

from PySide.QtGui import *
from PySide.QtCore import *

import mocha.project as mochaProject
proj = None

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

def callDeadlineCommand( arguments, hideWindow = True ):
    deadlineCommand = GetDeadlineCommand()
    
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
            CREATE_NO_WINDOW = 0x08000000   #MSDN process creation flag
            creationflags = CREATE_NO_WINDOW
    
    environment = {}
    for key in os.environ.keys():
        environment[key] = str(os.environ[key])
        
    # Need to set the PATH, cuz windows seems to load DLLs from the PATH earlier that cwd....
    if os.name == 'nt':
        deadlineCommandDir = os.path.dirname( deadlineCommand )
        if not deadlineCommandDir == "" :
            environment['PATH'] = deadlineCommandDir + os.pathsep + os.environ['PATH']
    
    arguments.insert( 0, deadlineCommand)
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, env=environment, creationflags=creationflags)
    proc.stdin.close()
    proc.stderr.close()
    
    output = proc.stdout.read()

    return output

def createSeparator( text ):
    separator = QWidget()
    separator.resize( 308, 37 )
    sepLayout = QHBoxLayout( separator )
    sepLayout.setContentsMargins( 0, 0, 0, -1 )
    
    sepLabel = QLabel( separator )
    sizePolicy = QSizePolicy( QSizePolicy.Maximum, QSizePolicy.Maximum )
    sizePolicy.setHorizontalStretch( 0 )
    sizePolicy.setVerticalStretch( 0 )
    sizePolicy.setHeightForWidth( sepLabel.sizePolicy().hasHeightForWidth() )
    sepLabel.setSizePolicy( sizePolicy )
    font = QFont()
    font.setBold( True )
    sepLabel.setFont( font )
    sepLabel.setText( text )
    sepLayout.addWidget( sepLabel )
    
    sepLine = QFrame( separator )
    sepLine.setFrameShadow( QFrame.Sunken )
    sepLine.setFrameShape( QFrame.HLine )
    sepLayout.addWidget( sepLine )
    
    return separator

def isPathLocal( path ):
    lowerPath = path.lower()
    return lowerPath.startswith( "c:" ) or lowerPath.startswith( "d:" ) or lowerPath.startswith( "e:" )

def submitToDeadline():
    global proj
    proj = mochaProject.get_current_project()
    if proj == None:
        QMessageBox.critical( None, "Error", "No project is open. Please open a Mocha project before submitting a job to Deadline." )
        return

    form = DeadlineDialog()
    form.exec_()

class DeadlineDialog( QDialog ):
    exporters = { "Shapes": [], "Tracking": [], "Camera Solve": [] }
    renderTypes = [ "Remove", "Insert", "Stabilize" ]
    exportTypes = [ "Shapes", "Tracking", "Camera Solve", "Rendered Shapes" ]
    fileExtensions = [ "png", "cin", "dpx", "jpg", "jpeg", "bw", "iris", "rgb", "rgba", "sgi", "targa", "tga", "tif", "tiff", "tim", "exr", "sxr" ]
    colorizeTypes = [ "Grayscale", "Matte Color", "Layer" ]
    layerGroupTooltip = "When specifying which layers to render, follow these rules:\n - if you want to render all layers inside a group, put the group name followed by a colon (e.g. myGroup:)\n - if you want to render only some layers inside a group, put the group name followed by a colon and then list group's individual layer names separating them by a comma (e.g. myGroup: layer1, layer2)\n - if you want to render ungrouped layers, list their names separating them by a comma (layer1, layer2) \n - you can render multiple groups as well as ungrouped layers but you must specify one group per line and have ungrouped layers on a separate line"

    def __init__( self, parent=None ):
        super( DeadlineDialog, self ).__init__( parent )
        self.setWindowTitle( "Submit Mocha to Deadline" )
        iconPath = callDeadlineCommand( [ "-GetRepositoryFilePath", "plugins/Mocha/Mocha.png" ] ).strip()
        self.setWindowIcon( QIcon( iconPath ) )

        dialogWidth = 450
        tabHeight = 450
        self.resize( QSize( dialogWidth, tabHeight ) ) 

        self.dialogLayout = QVBoxLayout()
        self.setLayout( self.dialogLayout )
        
        self.dialogTabs = QTabWidget()
        self.dialogLayout.addWidget( self.dialogTabs )
        self.dialogTabs.Size = QSize( dialogWidth, tabHeight )
        
        # Job Options Tab
        self.jobOptionsPage = QWidget()
        self.dialogTabs.addTab( self.jobOptionsPage, "Job Options" )
        
        self.jobOptionsPageLayout = QGridLayout()
        self.jobOptionsPage.setLayout( self.jobOptionsPageLayout )

        self.jobDescSeparator = createSeparator ( "Job Description" )
        self.jobOptionsPageLayout.addWidget( self.jobDescSeparator, 0, 0, 1, 4 )
        
        self.jobNameLabel = QLabel( "Job Name" )
        self.jobNameLabel.setToolTip( "The name of your job. This is optional, and if left blank, it will default to 'Untitled'." )
        self.jobOptionsPageLayout.addWidget( self.jobNameLabel, 1, 0 )
        self.jobNameWidget = QLineEdit( "" )
        self.jobOptionsPageLayout.addWidget( self.jobNameWidget, 1, 1, 1, 3 )
        
        self.commentLabel = QLabel( "Comment" )
        self.commentLabel.setToolTip( "A simple description of your job. This is optional and can be left blank." )
        self.jobOptionsPageLayout.addWidget( self.commentLabel, 2, 0 )
        self.commentWidget = QLineEdit( "" )
        self.jobOptionsPageLayout.addWidget(self.commentWidget, 2, 1, 1, 3 )
        
        self.departmentLabel = QLabel( "Department" )
        self.departmentLabel.setToolTip( "The department you belong to. This is optional and can be left blank." )
        self.jobOptionsPageLayout.addWidget( self.departmentLabel, 3, 0 )
        self.departmentWidget = QLineEdit( "" )
        self.jobOptionsPageLayout.addWidget( self.departmentWidget, 3, 1, 1, 3 )

        self.jobOptionsSeparator = createSeparator( "Job Options" )
        self.jobOptionsPageLayout.addWidget( self.jobOptionsSeparator, 4, 0, 1, 4 )
        
        self.poolLabel = QLabel( "Pool" )
        self.poolLabel.setToolTip( "The pool that your job will be submitted to." )
        self.jobOptionsPageLayout.addWidget( self.poolLabel, 5, 0 )
        self.poolWidget = QComboBox()
        self.jobOptionsPageLayout.addWidget( self.poolWidget, 5, 1, 1, 1 )
        self.pools = callDeadlineCommand( ["-pools",] ).splitlines()
        self.poolWidget.addItems( self.pools )
        
        self.secondaryPoolLabel = QLabel( "Secondary Pool" )
        self.secondaryPoolLabel.setToolTip( "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves." )
        self.jobOptionsPageLayout.addWidget( self.secondaryPoolLabel, 6, 0 )
        self.secondaryPoolWidget = QComboBox( )
        self.jobOptionsPageLayout.addWidget( self.secondaryPoolWidget, 6, 1 )
        self.secondaryPools = [ "" ] + self.pools
        self.secondaryPoolWidget.addItems( self.secondaryPools )
        
        self.groupLabel = QLabel( "Group" )
        self.groupLabel.setToolTip( "The group that your job will be submitted to." )
        self.jobOptionsPageLayout.addWidget( self.groupLabel, 7, 0 )
        self.groupWidget = QComboBox( )
        self.jobOptionsPageLayout.addWidget( self.groupWidget, 7, 1 )     
        self.groupWidget.addItems( callDeadlineCommand( ["-groups",] ).splitlines() )   
        
        self.priorityLabel = QLabel( "Priority" )
        self.priorityLabel.setToolTip( "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority." )
        self.jobOptionsPageLayout.addWidget( self.priorityLabel, 8, 0 )
        self.priorityWidget = QSpinBox( )
        self.priorityWidget.setRange( 0, self.getMaximumPriority() )
        self.priorityWidget.setValue ( min (50, self.priorityWidget.maximum() ) )
        self.jobOptionsPageLayout.addWidget( self.priorityWidget, 8, 1 )
        
        self.taskTimeoutLabel = QLabel( "Task Timeout" )
        self.taskTimeoutLabel.setToolTip( "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit." )
        self.jobOptionsPageLayout.addWidget( self.taskTimeoutLabel, 9, 0 )
        self.taskTimeoutWidget = QSpinBox( )
        self.taskTimeoutWidget.setMaximum( 1000000 )
        self.jobOptionsPageLayout.addWidget( self.taskTimeoutWidget, 9, 1 )
        self.enableAutoTimeoutWidget = QCheckBox( "Enable Auto Task Timeout" )
        self.enableAutoTimeoutWidget.setToolTip( "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job." )
        self.jobOptionsPageLayout.addWidget( self.enableAutoTimeoutWidget, 9, 2 )
        
        self.concurrentTasksLabel = QLabel( "Concurrent Tasks" )
        self.concurrentTasksLabel.setToolTip( "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs." )
        self.jobOptionsPageLayout.addWidget( self.concurrentTasksLabel, 10, 0 )
        self.concurrentTasksWidget = QSpinBox( )
        self.concurrentTasksWidget.setRange( 1, 16 )
        self.jobOptionsPageLayout.addWidget( self.concurrentTasksWidget, 10, 1 )
        self.limtTasksSlaveLimit = QCheckBox( "Limit Tasks To Slave's Task Limit" )
        self.limtTasksSlaveLimit.setCheckState ( Qt.Checked )
        self.limtTasksSlaveLimit.setToolTip( "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )
        self.jobOptionsPageLayout.addWidget( self.limtTasksSlaveLimit, 10, 2 )
        
        self.machineLimitLabel = QLabel( "Machine Limit" )
        self.machineLimitLabel.setToolTip( "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit." )
        self.jobOptionsPageLayout.addWidget( self.machineLimitLabel, 11, 0 )
        self.machineLimitWidget = QSpinBox(  )
        self.machineLimitWidget.setMaximum( 1000000 )
        self.jobOptionsPageLayout.addWidget( self.machineLimitWidget, 11, 1 )
        self.isBlackListWidget = QCheckBox( "Machine List Is Blacklist" )
        self.isBlackListWidget.setToolTip("You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist.")
        self.jobOptionsPageLayout.addWidget( self.isBlackListWidget, 11, 2 )        

        self.machineListLabel = QLabel( "Machine List" )
        self.machineListLabel.setToolTip( "The whitelisted or blacklisted list of machines." )
        self.jobOptionsPageLayout.addWidget( self.machineListLabel, 12, 0 )        
        self.machineListWidget = QLineEdit( "" )
        self.jobOptionsPageLayout.addWidget( self.machineListWidget, 12, 1, 1, 2 )
        self.getMachineListWidget = QPushButton( "..." )
        self.getMachineListWidget.pressed.connect( self.browseMachineList )
        self.jobOptionsPageLayout.addWidget( self.getMachineListWidget, 12, 3 )
        
        self.limitsLabel = QLabel( "Limits" )
        self.limitsLabel.setToolTip( "The Limits that your job requires." )
        self.jobOptionsPageLayout.addWidget( self.limitsLabel, 13, 0 )
        self.limitsWidget = QLineEdit( "" )
        self.jobOptionsPageLayout.addWidget( self.limitsWidget, 13, 1, 1, 2 )
        self.getLimitsWidget = QPushButton( "..." )
        self.getLimitsWidget.pressed.connect( self.browseLimitList )
        self.jobOptionsPageLayout.addWidget( self.getLimitsWidget, 13, 3 )
        
        self.dependenciesLabel = QLabel( "Dependencies" )
        self.dependenciesLabel.setToolTip( "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering." )
        self.jobOptionsPageLayout.addWidget( self.dependenciesLabel, 14, 0 )
        self.dependenciesWidget = QLineEdit( "" )
        self.jobOptionsPageLayout.addWidget( self.dependenciesWidget, 14, 1, 1, 2 )
        self.getDependenciesWidget = QPushButton( "..." )
        self.getDependenciesWidget.pressed.connect( self.browseDependencyList )
        self.jobOptionsPageLayout.addWidget( self.getDependenciesWidget, 14, 3 )
          
        self.onJobCompleteLabel = QLabel( "On Job Complete" )
        self.onJobCompleteLabel.setToolTip( "If desired, you can automatically archive or delete the job when it completes." )
        self.jobOptionsPageLayout.addWidget( self.onJobCompleteLabel, 15, 0 )
        self.onJobCompleteWidget = QComboBox( )
        self.jobOptionsPageLayout.addWidget( self.onJobCompleteWidget, 15, 1 )
        self.submitSuspendedWidget = QCheckBox( "Submit Job as Suspended" )
        self.submitSuspendedWidget.setToolTip( "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.")
        self.jobOptionsPageLayout.addWidget( self.submitSuspendedWidget, 15, 2 )
        self.onJobCompleteWidget.addItems( [ "Nothing", "Archive", "Delete" ] )

        self.mochaOptionsSeparator = createSeparator ( "Mocha Options" )
        self.jobOptionsPageLayout.addWidget( self.mochaOptionsSeparator, 16, 0, 1, 4 )

        self.versionLabel = QLabel( "Version" )
        self.versionLabel.setToolTip( "The version of Mocha Pro to render/export with." )
        self.jobOptionsPageLayout.addWidget( self.versionLabel, 17, 0)
        self.versionWidget = QComboBox()
        self.jobOptionsPageLayout.addWidget( self.versionWidget, 17, 1 )
        self.versionWidget.addItems( ["5"] )
        self.submitMochaFiledWidget = QCheckBox( "Submit Mocha Project File With Job" )
        self.submitMochaFiledWidget.setToolTip( "If this option is enabled, the project file will be submitted with the job, and then copied locally to the slave machine during rendering." )
        self.jobOptionsPageLayout.addWidget( self.submitMochaFiledWidget, 17, 2)

        self.sceneFileLabel = QLabel( "Mocha Project File" )
        self.sceneFileLabel.setToolTip( "The Mocha project to be rendered/exported." )
        self.jobOptionsPageLayout.addWidget( self.sceneFileLabel, 18, 0)
        self.sceneFileWidget = QLineEdit( "Untitled" )
        self.jobOptionsPageLayout.addWidget( self.sceneFileWidget, 18, 1, 1, 2 )
        self.sceneFileBrowseButton = QPushButton()
        self.sceneFileBrowseButton.setText( "..." )
        self.sceneFileBrowseButton.pressed.connect( self.browseSceneFile )
        self.jobOptionsPageLayout.addWidget( self.sceneFileBrowseButton, 18, 3 )

        self.outputDirectoryLabel = QLabel( "Output Directory" )
        self.outputDirectoryLabel.setToolTip( "The directory where the render/export output will be written to. The location must be accessible by the slave(s)." )
        self.jobOptionsPageLayout.addWidget( self.outputDirectoryLabel, 19, 0)
        self.outputDirectoryWidget = QLineEdit( "" )
        self.jobOptionsPageLayout.addWidget( self.outputDirectoryWidget, 19, 1, 1, 2 )
        self.outputDirectoryBrowseButton = QPushButton()
        self.outputDirectoryBrowseButton.setText( "..." )
        self.outputDirectoryBrowseButton.pressed.connect( self.browseOutputDirectory )
        self.jobOptionsPageLayout.addWidget( self.outputDirectoryBrowseButton, 19, 3 )

        self.frameIndexWidthLabel = QLabel( "Frame Index Width" )
        self.frameIndexWidthLabel.setToolTip( "The number of digits allocated for the index portion of the file name. If the number is not large enough to accomodate all output frame indices, it will be ignored and the minimum required number of digits will be used instead." )
        self.jobOptionsPageLayout.addWidget( self.frameIndexWidthLabel, 20, 0 )
        self.frameIndexWidthWidget = QSpinBox( )
        self.frameIndexWidthWidget.setRange ( 0, 10 )
        self.jobOptionsPageLayout.addWidget( self.frameIndexWidthWidget, 20, 1 )

        self.frameRangeLayout = QHBoxLayout ()
        self.framesLabel = QLabel( "Frame Range" )
        self.framesLabel.setToolTip( "The frame range to render/export." )
        self.frameRangeLayout.addWidget( self.framesLabel )
        self.framesWidget = QLineEdit( "" )
        self.frameRangeLayout.addWidget( self.framesWidget )
        self.jobOptionsPageLayout.addLayout( self.frameRangeLayout, 20, 2, 1, 2 )

        self.chunkSizeLabel = QLabel( "Frames Per Task" )
        self.chunkSizeLabel.setToolTip( "This is the number of frames that will be rendered at a time for each job task." )
        self.jobOptionsPageLayout.addWidget( self.chunkSizeLabel, 21, 0 )
        self.chunkSizeWidget = QSpinBox( )
        self.chunkSizeWidget.setRange ( 1, 1000000 )
        self.jobOptionsPageLayout.addWidget( self.chunkSizeWidget, 21, 1 )

        self.jobOptionsSpacer = QSpacerItem( 0, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding )
        self.jobOptionsPageLayout.addItem( self.jobOptionsSpacer, 22, 0, 1, 3 )

        # Advanced Tab
        self.advancedPage = QWidget()
        self.dialogTabs.addTab( self.advancedPage, "Advanced" )
        
        self.advancedPageLayout = QGridLayout()
        self.advancedPage.setLayout( self.advancedPageLayout )

        self.readExportersLists()

        self.jobTypeLabel = QLabel( "Job Type" )
        self.jobTypeLabel.setToolTip( "The type of Mocha job." )
        self.advancedPageLayout.addWidget( self.jobTypeLabel, 0, 0)
        self.jobTypeWidget = QComboBox( )
        self.advancedPageLayout.addWidget( self.jobTypeWidget, 0, 1 )
        self.jobTypeWidget.addItems( [ "Render", "Export" ] )
        self.jobTypeWidget.currentIndexChanged.connect( self.jobTypeChanged )
        self.jobSubTypeLabel = QLabel( "Job Sub Type" )
        self.jobSubTypeLabel.setToolTip( "The sub type of Mocha job." )
        self.advancedPageLayout.addWidget( self.jobSubTypeLabel, 0, 2 )
        self.jobSubTypeWidget = QComboBox( )
        self.advancedPageLayout.addWidget( self.jobSubTypeWidget, 0, 3 )
        self.jobSubTypeWidget.addItems( [] )
        self.jobSubTypeWidget.currentIndexChanged.connect( self.jobSubTypeChanged )

        # Render Options
        self.renderOptionsSeparator = createSeparator ( "Render Options" )
        self.advancedPageLayout.addWidget( self.renderOptionsSeparator, 1, 0, 1, 4 )

        self.fileExtensionLabel = QLabel( "File Extension" )
        self.fileExtensionLabel.setToolTip( "The output file extension." )
        self.advancedPageLayout.addWidget( self.fileExtensionLabel, 2, 0)
        self.fileExtensionWidget = QComboBox( )
        self.advancedPageLayout.addWidget( self.fileExtensionWidget, 2, 1 )
        self.fileExtensionWidget.addItems( self.fileExtensions )

        self.clipViewIndexLabel = QLabel( "Clip View Index" )
        self.clipViewIndexLabel.setToolTip( "By default, this is zero (0), but if you are working with a multi-view clip, you can set the index here. In stereo mode, Left and Right views are 0 and 1 respectively." )
        self.advancedPageLayout.addWidget( self.clipViewIndexLabel, 2, 2)
        self.clipViewIndexWidget = QComboBox( )
        self.clipViewIndexWidget.addItems ( ["0", "1"] )
        self.advancedPageLayout.addWidget( self.clipViewIndexWidget, 2, 3 )

        self.outputPrefixLabel = QLabel( "Output Prefix" )
        self.outputPrefixLabel.setToolTip( "The output prefix goes before the frame number in the file name. Not required." )
        self.advancedPageLayout.addWidget( self.outputPrefixLabel, 3, 0)
        self.outputPrefixWidget = QLineEdit( "" )
        self.advancedPageLayout.addWidget( self.outputPrefixWidget, 3, 1 )
        self.outputSuffixLabel = QLabel( "Output Suffix" )
        self.outputSuffixLabel.setToolTip( "The output suffix goes after the frame number in the file name. Not required." )
        self.advancedPageLayout.addWidget( self.outputSuffixLabel, 3, 2 )
        self.outputSuffixWidget = QLineEdit( "" )
        self.advancedPageLayout.addWidget( self.outputSuffixWidget, 3, 3 )

        self.layerGroupLabel = QLabel( "Layers" )
        self.layerGroupLabel.setToolTip( "The layers to render." )
        self.advancedPageLayout.addWidget( self.layerGroupLabel, 4, 0)
        self.layerGroupWidget = QTextEdit( "" )
        self.layerGroupWidget.setToolTip( self.layerGroupTooltip )
        self.advancedPageLayout.addWidget( self.layerGroupWidget, 4, 1, 1, 3 )

        # Export Options
        self.exportOptionsSeparator = createSeparator ( "Export Options" )
        self.advancedPageLayout.addWidget( self.exportOptionsSeparator, 5, 0, 1, 4 )

        self.exporterNameLabel = QLabel( "Exporter Name" )
        self.exporterNameLabel.setToolTip( "The name of the exporter. The exporters list can be accessed in <repository>\plugins\Mocha." )
        self.advancedPageLayout.addWidget( self.exporterNameLabel, 6, 0)
        self.exporterNameWidget = QComboBox( )
        self.advancedPageLayout.addWidget( self.exporterNameWidget, 6, 1, 1, 3 )

        self.fileNameLabel = QLabel( "File Name" )
        self.fileNameLabel.setToolTip( "The exporter output file name, including extension." )
        self.advancedPageLayout.addWidget( self.fileNameLabel, 7, 0)
        self.fileNameWidget = QLineEdit( "" )
        self.advancedPageLayout.addWidget( self.fileNameWidget, 7, 1, 1, 3 )

        self.viewsLabel = QLabel( "View Names" )
        self.viewsLabel.setToolTip( "List of names or abbreviations of views to export (use comma as the delimiter). When in stereo mode, Left(L) will be used by default." )
        self.advancedPageLayout.addWidget( self.viewsLabel, 8, 0)
        self.viewsWidget = QLineEdit( "" )
        self.advancedPageLayout.addWidget( self.viewsWidget, 8, 1, 1, 3 )

        self.frameTimeLabel = QLabel( "Frame Time" )
        self.frameTimeLabel.setToolTip( "The frame time argument is used when working with tracking data exporters." )
        self.advancedPageLayout.addWidget( self.frameTimeLabel, 9, 0)
        self.frameTimeWidget = QDoubleSpinBox( )
        self.frameTimeWidget.setRange (0.000, 1000000)
        self.frameTimeWidget.setDecimals ( 3 )
        self.frameTimeWidget.setSingleStep ( 0.001 )
        self.advancedPageLayout.addWidget( self.frameTimeWidget, 9, 1 )

        self.colorizeLabel = QLabel( "Colorize" )
        self.colorizeLabel.setToolTip( "Used to export the colored version of the mattes." )
        self.advancedPageLayout.addWidget( self.colorizeLabel, 9, 2 )
        self.colorizeWidget = QComboBox( )
        self.advancedPageLayout.addWidget( self.colorizeWidget, 9, 3 )
        self.colorizeWidget.addItems ( self.colorizeTypes )

        self.removeLensDistortionWidget = QCheckBox( "Remove Lens Distortion" )
        self.removeLensDistortionWidget.setToolTip( "Mimes the Remove Lens Distortion checkbox of the Export Tracking Data dialog." )
        self.advancedPageLayout.addWidget( self.removeLensDistortionWidget, 10, 1 )

        self.stabilizeWidget = QCheckBox( "Stabilize" )
        self.stabilizeWidget.setToolTip( "Mimes the Stabilize checkbox of the Export Tracking Data dialog." )
        self.advancedPageLayout.addWidget( self.stabilizeWidget, 10, 2 )

        self.invertdWidget = QCheckBox( "Invert" )
        self.invertdWidget.setToolTip( "Mimes the Invert checkbox in Mocha's Export Tracking Data dialog." )
        self.advancedPageLayout.addWidget( self.invertdWidget, 10, 3 )

        self.advancedPageSpacer = QSpacerItem( 0, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding )
        self.advancedPageLayout.addItem( self.advancedPageSpacer, 21, 0, 1, 3 ) 

        # TODO: add Draft, Shotgun, and potentially NIM

        self.buttonLayout = QHBoxLayout()
        self.buttonLayoutSpacer = QSpacerItem( 0, 0, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum )
        self.buttonLayout.addItem( self.buttonLayoutSpacer )
        
        self.submitButton = QPushButton( "Submit" )
        self.submitButton.pressed.connect( self.submitButtonPressed )
        self.buttonLayout.addWidget( self.submitButton )
        
        self.closeButton = QPushButton( "Close" )
        self.closeButton.pressed.connect( self.close )
        self.buttonLayout.addWidget( self.closeButton )
        
        self.dialogLayout.addLayout( self.buttonLayout )

        self.updateJobSubTypeList()
        self.adjustOptionsSelection()
        self.updateExportersList()

        self.loadSceneSettings()

    def getLayerGroupInfo ( self ):
        layerGroupString = ""

        layers = proj.layers
        groups = proj.groups

        # ungrouped layers
        layerGroupString += " ".join( layer.name for layer in layers if layer.parent == None )
        # grouped layers
        layerGroupString += "\n" + "\n".join( group.name + ": " + ( ", ".join( layer.name for layer in group.layers ) ) for group in groups )

        return layerGroupString

    def loadSceneSettings ( self ):
        sceneFilePath = proj.project_file
        self.sceneFileWidget.setText( sceneFilePath )
        sceneFileName = os.path.basename( os.path.normpath( sceneFilePath ) )
        self.jobNameWidget.setText( sceneFileName[ :sceneFileName.find('.') ] if sceneFileName.find('.') != -1 else sceneFileName )

        outputDir = proj.get_output_dir()
        self.outputDirectoryWidget.setText ( outputDir )

        self.layerGroupWidget.setText( self.getLayerGroupInfo() )

        # don't populate the widget with all available views because some exporters can only work with one view at a time
        # if the user doesn't know/notice that, the export will fail
        defaultView = proj.default_hero_view
        self.clipViewIndexWidget.setCurrentIndex( self.clipViewIndexWidget.findText( str( defaultView.id ) ) )
        views = proj.views
        self.viewsWidget.setText( views[ defaultView.id ].name )

        self.projFrameOffset = proj.first_frame_offset
        self.framesWidget.setText( str( self.projFrameOffset ) + "-" + str( proj.first_frame_offset  + proj.length - 1 ) )      

    def jobTypeChanged ( self ):
        self.updateJobSubTypeList()  
        self.adjustOptionsSelection()

    def updateJobSubTypeList ( self ):
        self.jobSubTypeWidget.clear()
        if str( self.jobTypeWidget.currentText() ) == "Render":
            self.jobSubTypeWidget.addItems( self.renderTypes )
        else:
            self.jobSubTypeWidget.addItems( self.exportTypes )

    def adjustOptionsSelection( self ):
        if str( self.jobTypeWidget.currentText() ) == "Render":
            self.enableRenderJobOptions ( True )
            self.enableExportJobOptions ( False )
            self.enableIntegrationControls ( True )
        else:
            self.enableRenderJobOptions ( False )
            self.enableExportJobOptions ( True )
            self.enableIntegrationControls ( False )
    
    def enableRenderJobOptions ( self, enable ):
        self.renderOptionsSeparator.setEnabled( enable )
        self.fileExtensionLabel.setEnabled( enable )
        self.fileExtensionWidget.setEnabled( enable )
        self.outputPrefixLabel.setEnabled( enable )
        self.outputPrefixWidget.setEnabled( enable )
        self.outputSuffixLabel.setEnabled( enable )
        self.outputSuffixWidget.setEnabled( enable )
        self.layerGroupLabel.setEnabled( enable )
        self.layerGroupWidget.setEnabled( enable )
        self.clipViewIndexLabel.setEnabled( enable )
        self.clipViewIndexWidget.setEnabled( enable )

    def enableExportJobOptions ( self, enable ):
        self.exportOptionsSeparator.setEnabled( enable )
        self.viewsLabel.setEnabled( enable )
        self.viewsWidget.setEnabled( enable )
        self.exporterNameLabel.setEnabled( enable )
        self.exporterNameWidget.setEnabled( enable )
        self.fileNameLabel.setEnabled( enable )
        self.fileNameWidget.setEnabled( enable )
        self.frameTimeLabel.setEnabled( enable )
        self.frameTimeWidget.setEnabled( enable )
        self.colorizeLabel.setEnabled( enable )
        self.colorizeWidget.setEnabled( enable )
        self.invertdWidget.setEnabled( enable )
        self.removeLensDistortionWidget.setEnabled( enable )
        self.stabilizeWidget.setEnabled( enable )

    def enableIntegrationControls ( self, enable ):
        self.dialogTabs.setTabEnabled ( 2, enable )
    
    def updateExportersList ( self ):
        self.exporterNameWidget.clear()
        if str( self.jobSubTypeWidget.currentText() )  == "Shapes":
            self.exporterNameWidget.addItems ( self.exporters[ "Shapes" ] )
        if str( self.jobSubTypeWidget.currentText() )  == "Tracking":
            self.exporterNameWidget.addItems ( self.exporters[ "Tracking" ] )
        if str( self.jobSubTypeWidget.currentText() )  == "Camera Solve":
            self.exporterNameWidget.addItems ( self.exporters[ "Camera Solve" ] )
        if str( self.jobSubTypeWidget.currentText() )  == "Rendered Shapes":
            self.exporterNameWidget.addItems ( "" )

    #this is to accomodate Rendered Shapes export hybrid options
    def jobSubTypeChanged ( self ):
        if str( self.jobTypeWidget.currentText() ) == "Export" and str( self.jobSubTypeWidget.currentText() ) == "Rendered Shapes":
            self.updateExportOptions ( True )
        elif str( self.jobTypeWidget.currentText() ) == "Export" and str( self.jobSubTypeWidget.currentText() ) != "Rendered Shapes":
            self.updateExportOptions ( False )

        self.updateExportersList()

    def updateExportOptions ( self, enable ):
        # enable is True if subtype == "Rendered Shapes"; False otherwise
        self.renderOptionsSeparator.setEnabled( enable )

        self.fileExtensionLabel.setEnabled( enable )
        self.fileExtensionWidget.setEnabled( enable )        
        self.outputPrefixLabel.setEnabled( enable )
        self.outputPrefixWidget.setEnabled( enable )
        self.outputSuffixLabel.setEnabled( enable )
        self.outputSuffixWidget.setEnabled( enable )
        self.layerGroupLabel.setEnabled( enable )
        self.layerGroupWidget.setEnabled( enable )

        self.exporterNameLabel.setEnabled( not enable )
        self.exporterNameWidget.setEnabled( not enable )
        self.fileNameLabel.setEnabled( not enable )
        self.fileNameWidget.setEnabled( not enable )

    def readExportersLists( self ):
        exportersListFileName = callDeadlineCommand( [ "-GetRepositoryFilePath", "plugins/Mocha/Exporters.txt" ] ).strip()

        if os.path.isfile( exportersListFileName ):
            exportersListFile = open ( exportersListFileName, 'r' ) 

            line = exportersListFile.readline()
            while line != None and line != "":
                if ( not line.isspace() ):
                    exporterType = ""
                    exporterType = line[ : line.find(" data exporters") ]
                    if ( len( exporterType ) > 0 ):
                        temp = []
                        line = exportersListFile.readline()
                        while ( line != None and line != "" and not line.isspace() and line.find(" data exporters") == -1 ):
                            temp.append ( line.strip() )
                            line = exportersListFile.readline()
                        self.exporters[exporterType] = temp
                    else:
                        print ("Unexpected format of the exporters list.")
                        return
                else:
                    line = exportersListFile.readline()
        else:
            print ("The exporters list file was not found in the Mocha plugin folder.")

    def getJobSubType ( self ):
            return str( self.jobSubTypeWidget.currentText() ).lower().replace( " ", "-" )

    def getMaximumPriority ( self ):
        maximumPriority = 100
        try:
            output = callDeadlineCommand( ["-getmaximumpriority",] )
            maximumPriority = int(output)
        except:
            # If an error occurs here, just ignore it and use the default of 100.
            pass

        return maximumPriority

    def getColorizeType( self ):
        return str( self.colorizeWidget.currentText() ).lower().replace( " ", "-" )

    def getFrameWidth ( self ):
        frames = self.framesWidget.text()

        paddedNumberRegex = re.compile( "([0-9]+)", re.IGNORECASE )     
        matches = paddedNumberRegex.findall( frames )
        matches.sort (key = len)
        longestFrameNumber = matches[-1]

        frameWidthIndex = self.frameIndexWidthWidget.value() 

        return max( int (frameWidthIndex), len (longestFrameNumber) )

    def getOutputFilename ( self ):
        outputFilename = ""

        frameWidth = self.getFrameWidth()
        path = self.outputDirectoryWidget.text().strip()
        prefix =  self.outputPrefixWidget.text().strip()
        suffix =  self.outputSuffixWidget.text().strip()
        padding = "#" * frameWidth
        fileExtension =  self.fileExtensionWidget.currentText().strip()

        outputFilename = path + "/" + prefix + padding + suffix + "." + fileExtension

        return outputFilename

    def browseSceneFile( self ):
        if os.path.exists(self.sceneFileWidget.text()):
            result = QFileDialog.getOpenFileName(self, "", self.sceneFileWidget.text(), "Mocha Files (*.mocha);;All Files (*)")
        else:
            result = QFileDialog.getOpenFileName(self, "", "", "Mocha Files (*.mocha);;All Files (*)")

        # getOpenFileName() returns a tuple, so we need to look at its first element
        if result is not None and result[0] != "":
            self.sceneFileWidget.setText(result[0])

    def browseOutputDirectory ( self ):
        if os.path.exists(self.outputDirectoryWidget.text()):
            result = QFileDialog.getExistingDirectory(self, "", self.outputDirectoryWidget.text() )
        else:
            result = QFileDialog.getExistingDirectory(self, "", "" )
        
        if result is not None and result != "":
            self.outputDirectoryWidget.setText(result)

    def browseMachineList( self ):
        output = callDeadlineCommand( [ "-selectmachinelist", str( self.machineListWidget.text() ) ], False ) 
        output = output.replace( "\r", "" ).replace( "\n", "" )
        if output != "Action was cancelled by user":
            self.machineListWidget.setText( output )

    def browseLimitList( self ):
        output = callDeadlineCommand( [ "-selectlimitgroups", str( self.limitsWidget.text() ) ], False )
        output = output.replace( "\r", "" ).replace( "\n", "" )
        if output != "Action was cancelled by user":
            self.limitsWidget.setText( output )
    
    def browseDependencyList( self ):
        output = callDeadlineCommand( [ "-selectdependencies", str( self.dependenciesWidget.text() ) ], False )
        output = output.replace( "\r", "" ).replace( "\n", "" )
        if output != "Action was cancelled by user":
            self.dependenciesWidget.setText( output )    

    def packLayerGroupInfo ( self ):        
        layerGroupString = self.layerGroupWidget.toPlainText() 
        layerGroupString = layerGroupString.replace("\n", ";").replace("\r", ";")

        return layerGroupString

    def sanityChecksPassed( self ):
        # Sanity checks
        sceneFile = self.sceneFileWidget.text().strip()
        if ( len( sceneFile ) == 0 ):
            QMessageBox.critical( self, "Error", "No Mocha file specified." )
            return False
        
        if( not os.path.isfile( sceneFile ) ):
            QMessageBox.critical( self, "Error", "Mocha file %s does not exist." % sceneFile )
            return False

        outputDirectory = self.outputDirectoryWidget.text().strip()
        if ( len( outputDirectory ) == 0 ):
            QMessageBox.critical( self, "Error", "No output directory specified." )
            return False
        
        if ( not os.path.isdir( outputDirectory ) ):
            QMessageBox.critical( self, "Error", "Output directory %s does not exist." % outputDirectory )
            return False

        if ( not self.submitMochaFiledWidget.isChecked() and isPathLocal( sceneFile ) ):
            result = QMessageBox.question( self, "Warning", "The Mocha file %s is local. Are you sure you want to continue?" % sceneFile,  QMessageBox.Yes|QMessageBox.No )
            if result == QMessageBox.No:
                return False

        frames = self.framesWidget.text()
        if ( len( frames.strip() ) == 0 ):
            QMessageBox.critical( self, "Error", "Frame range %s is not valid." % frames )
            return False

        if ( self.jobTypeWidget.currentText() == "Export" and self.jobSubTypeWidget.currentText() != "Rendered Shapes" ):
            if not len( self.fileNameWidget.text().strip() ) > 0:
                QMessageBox.critical( self, "Error", "File name must be specified." )
                return False

        return True


    def submitButtonPressed ( self ):

        if not self.sanityChecksPassed():
            return

        proj.save()

        # Create job info file
        jobInfoFilename = os.path.join( callDeadlineCommand( [ "-GetCurrentUserHomeDirectory"] ).strip(), "temp", "mocha_job_info.job" )
        fileHandle = open( jobInfoFilename, "w" )

        # General parameters
        fileHandle.write( "Plugin=Mocha\n" )
        fileHandle.write( "Name=%s\n" % self.jobNameWidget.text() )
        fileHandle.write( "Comment=%s\n" % self.commentWidget.text() )
        fileHandle.write( "Department=%s\n" % self.departmentWidget.text() )
        fileHandle.write( "Pool=%s\n" % self.poolWidget.currentText() )
        fileHandle.write( "SecondaryPool=%s\n" % self.secondaryPoolWidget.currentText() )
        fileHandle.write( "Group=%s\n" % self.groupWidget.currentText() )
        fileHandle.write( "Priority=%s\n" % str( self.priorityWidget.value() ) )
        fileHandle.write( "TaskTimeoutMinutes=%s\n" % str( self.taskTimeoutWidget.value() ) )
        fileHandle.write( "EnableAutoTimeout=%s\n" % str( self.enableAutoTimeoutWidget.isChecked() ) )
        fileHandle.write( "ConcurrentTasks=%s\n" % str(self.concurrentTasksWidget.value() ) )
        fileHandle.write( "LimitGroups=%s\n" % self.limitsWidget.text() )
        fileHandle.write( "JobDependencies=%s\n" % self.dependenciesWidget.text() )
        fileHandle.write( "OnJobComplete=%s\n" % self.onJobCompleteWidget.currentText() )        
        fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % str(self.limtTasksSlaveLimit.isChecked()) )
        fileHandle.write( "ChunkSize=%s\n" % str( self.chunkSizeWidget.value() ) )
        fileHandle.write( "Frames=%s\n" % self.framesWidget.text() )
        
        fileHandle.write( "MachineLimit=%s\n" % str(self.machineLimitWidget.value() ) )
        if self.isBlackListWidget.isChecked():
            fileHandle.write( "Blacklist=%s\n" % self.machineListWidget.text() )
        else:
            fileHandle.write( "Whitelist=%s\n" % self.machineListWidget.text() )           
        
        if self.submitSuspendedWidget.isChecked():
            fileHandle.write( "InitialStatus=Suspended\n" )

        fileHandle.write("\n")
        fileHandle.write( "OutputFilename0=%s" % self.getOutputFilename() ) 

        fileHandle.close()

        # Create plugin info file
        pluginInfoFilename = os.path.join( os.path.join( callDeadlineCommand( [ "-GetCurrentUserHomeDirectory"] ).strip(), "temp", "mocha_plugin_info.job" ) )
        fileHandle = open( pluginInfoFilename, "w" )

        fileHandle.write( "Version=%s\n" % self.versionWidget.currentText() )
        fileHandle.write( "Scene=%s\n" % self.sceneFileWidget.text() )
        fileHandle.write( "Output=%s\n" %  self.outputDirectoryWidget.text() )
        fileHandle.write( "FrameIndexWidth=%s\n" % self.frameIndexWidthWidget.value() )
        fileHandle.write( "ProjFrameOffset=%s\n" % self.projFrameOffset )

        fileHandle.write( "JobType=%s\n" % self.jobTypeWidget.currentText() )
        fileHandle.write( "JobSubType=%s\n" % self.getJobSubType() )
        if self.jobTypeWidget.currentText() == "Render":
            fileHandle.write( "FileExtension=%s\n" % self.fileExtensionWidget.currentText() )
            fileHandle.write( "OutputPrefix=%s\n" % self.outputPrefixWidget.text() )
            fileHandle.write( "OutputSuffix=%s\n" % self.outputSuffixWidget.text() )
            fileHandle.write( "LayerGroupInfo=%s\n" % self.packLayerGroupInfo() ) # adds info about groups and layers

            fileHandle.write( "ClipViewIndex=%s\n" % self.clipViewIndexWidget.currentText() )
        elif self.jobTypeWidget.currentText() == "Export" and self.jobSubTypeWidget.currentText() != "Rendered Shapes":            
            fileHandle.write( "ExporterName=%s\n" % self.exporterNameWidget.currentText() )
            fileHandle.write( "FileName=%s\n" % self.fileNameWidget.text() )
            fileHandle.write( "Views=%s\n" % self.viewsWidget.text() )
            fileHandle.write( "Colorize=%s\n" % self.getColorizeType() )       
            fileHandle.write( "Invert=%s\n" % self.invertdWidget.isChecked() )
            fileHandle.write( "RemoveLensDistortion=%s\n" % self.removeLensDistortionWidget.isChecked() )
            fileHandle.write( "Stabilize=%s\n" % self.stabilizeWidget.isChecked() )

        elif self.jobTypeWidget.currentText() == "Export" and self.jobSubTypeWidget.currentText() == "Rendered Shapes":
            # "Rendered Shapes" is a hybrid between rendering and exporting
            fileHandle.write( "FileExtension=%s\n" % self.fileExtensionWidget.currentText() )
            fileHandle.write( "OutputPrefix=%s\n" % self.outputPrefixWidget.text() )
            fileHandle.write( "OutputSuffix=%s\n" % self.outputSuffixWidget.text() )
            fileHandle.write( "LayerGroupInfo=%s\n" % self.packLayerGroupInfo() ) # adds info about groups and layers
            fileHandle.write( "Views=%s\n" % self.viewsWidget.text() )
            fileHandle.write( "Colorize=%s\n" % self.getColorizeType() )       
            fileHandle.write( "Invert=%s\n" % self.invertdWidget.isChecked() )
            fileHandle.write( "RemoveLensDistortion=%s\n" % self.removeLensDistortionWidget.isChecked() )
            fileHandle.write( "Stabilize=%s\n" % self.stabilizeWidget.isChecked() )


        fileHandle.close()

        arguments = []
        arguments.append( jobInfoFilename )
        arguments.append( pluginInfoFilename )
        
        if self.submitMochaFiledWidget.isChecked():
            arguments.append( self.sceneFileWidget.text() )
        
        results = callDeadlineCommand( arguments )
        QMessageBox.information( self, "Results", results )