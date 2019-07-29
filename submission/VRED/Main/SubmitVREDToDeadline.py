from __future__ import print_function

#Vred 2016 onwards is supported only
try:
    #Vred 2018 onwards uses PySide2
    from PySide2 import QtGui, QtCore, QtWidgets
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
    print("Deadline: Using PySide2")
except:
    try:
        #Vred 2015 and Vred 2016 prior to SR1 uses PySide
        from PySide import QtGui, QtCore
        from PySide.QtGui import *
        from PySide.QtCore import *
        from shiboken import wrapInstance
        print("Deadline: Using PySide")
    except:
        #PythonQt is needed for Vred 2016 SR1 / Vred 2017
        from PythonQt import QtGui, QtCore
        from PythonQt.QtGui import *
        from PythonQt.QtCore import *
        print("Deadline: Using PythonQt")

from vrVredUi import *
from vrFileIO import *
from vrRenderSettings import *
from vrController import *

import os
import time
import subprocess
import time

def addDeadlineMenu( window=None ):
    #PySide/PySide2 compliant menu function
    vredWindow = vredMainWindow( window )
    vredMenuBar = vredWindow.menuBar()

    vredMenuName = "Deadline"
    vredMenu = None
    deadlineAction = None

    actionList = vredMenuBar.actions()
    for action in actionList:
        if action.text() == vredMenuName:
            vredMenuBar.removeAction(action)

    vredMenu = vredMenuBar.addMenu( vredMenuName )
    lastAction = actionList[-1]
    vredMenuBar.insertMenu(lastAction, vredMenu)

    deadlineAction = vredMenu.addAction( "Submit to Deadline" )
    deadlineAction.triggered.connect( submitToDeadline )

def addDeadlinePythonQtMenu( window=None ):
    #PythonQt menu function for Vred 2016 SR1 / Vred 2017
    vredWindow = vredMainWindow( window )
    vredMenuBar = vredWindow.menuBar()
    deadlineMenu = None
    deadlineAction = None
    
    found = False
    for child in vredMenuBar.findChildren(QMenu):
        if child.title() == "Deadline":
            found = True
            deadlineMenu = child
            break

    if not found:
        deadlineMenu = QMenu("Deadline", vredMenuBar)
        deadlineMenu.setObjectName( "Deadline" )
        vredMenuBar.addMenu( deadlineMenu )
    
    found = False
    for action in deadlineMenu.actions():
        if action.text() == "Submit To Deadline":
            deadlineAction = action
            found = True
            break
    
    if not found:
        deadlineAction = QAction( "Submit To Deadline", deadlineMenu )
        deadlineAction.triggered.connect( submitToDeadline )
        deadlineMenu.addAction(deadlineAction)

def submitToDeadline():
    form = DeadlineDialog()
    form.exec_()

class DeadlineDialog( QDialog ):
    def __init__( self, parent=None ):
        super(DeadlineDialog, self).__init__(parent)        
        self.setWindowTitle("Submit VRED to Deadline")
        pngFile = CallDeadlineCommand( ["-getRepositoryFilePath", "submission/VRED/Main/VRED.png"] )
        pngFile = pngFile.rstrip()
        self.setWindowIcon( QIcon(pngFile) )

        dialogWidth = 450
        tabHeight = 450
        self.resize(QSize(dialogWidth, tabHeight))        
        
        self.dialogLayout = QVBoxLayout()
        self.setLayout( self.dialogLayout )
        
        self.dialogTabs = QTabWidget()
        self.dialogLayout.addWidget(self.dialogTabs)
        self.dialogTabs.resize(QSize(dialogWidth, tabHeight))
        
        self.jobOptionsPage = QWidget()
        self.dialogTabs.addTab( self.jobOptionsPage, "Job Options" )
        
        self.jobOptionsLayout = QGridLayout()
        self.jobOptionsPage.setLayout( self.jobOptionsLayout )
        
        separator1 = createSeparator( "Job Description" )
        self.jobOptionsLayout.addWidget(separator1,0,0,1,3)
        
        self.jobNameLabel = QLabel( "Job Name" )
        self.jobNameLabel.setToolTip("The name of your job. This is optional, and if left blank, it will default to 'Untitled'.")
        self.jobOptionsLayout.addWidget(self.jobNameLabel,1,0)
        self.jobNameWidget = QLineEdit( "" )
        self.jobOptionsLayout.addWidget(self.jobNameWidget, 1, 1, 1, 2 )
        
        self.commentLabel = QLabel( "Comment" )
        self.commentLabel.setToolTip("A simple description of your job. This is optional and can be left blank.")
        self.jobOptionsLayout.addWidget(self.commentLabel,2,0)
        self.commentWidget = QLineEdit( "" )
        self.jobOptionsLayout.addWidget(self.commentWidget, 2, 1, 1, 2 )
        
        self.departmentLabel = QLabel( "Department" )
        self.departmentLabel.setToolTip( "The department you belong to. This is optional and can be left blank." )
        self.jobOptionsLayout.addWidget(self.departmentLabel, 3, 0)
        self.departmentWidget = QLineEdit( "" )
        self.jobOptionsLayout.addWidget(self.departmentWidget, 3, 1, 1, 2 )
        
        separator2 = createSeparator( "Job Options" )
        self.jobOptionsLayout.addWidget(separator2,4,0,1,3)
        
        self.poolLabel = QLabel( "Pool" )
        self.poolLabel.setToolTip( "The pool that your job will be submitted to." )
        self.jobOptionsLayout.addWidget(self.poolLabel, 5, 0)
        self.poolWidget = QComboBox( )
        self.jobOptionsLayout.addWidget(self.poolWidget, 5, 1, 1, 1 )
        
        self.secondaryPoolLabel = QLabel( "Secondary Pool" )
        self.secondaryPoolLabel.setToolTip( "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves." )
        self.jobOptionsLayout.addWidget(self.secondaryPoolLabel, 6, 0)
        self.secondaryPoolWidget = QComboBox( )
        self.jobOptionsLayout.addWidget(self.secondaryPoolWidget, 6, 1)
        
        self.groupLabel = QLabel( "Group" )
        self.groupLabel.setToolTip( "The group that your job will be submitted to." )
        self.jobOptionsLayout.addWidget(self.groupLabel, 7, 0)
        self.groupWidget = QComboBox( )
        self.jobOptionsLayout.addWidget(self.groupWidget, 7, 1)
        
        self.priorityLabel = QLabel( "Priority" )
        self.priorityLabel.setToolTip("A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.")
        self.jobOptionsLayout.addWidget(self.priorityLabel, 8, 0)
        self.priorityWidget = QSpinBox(  )
        self.jobOptionsLayout.addWidget(self.priorityWidget, 8, 1)
        
        self.taskTimeoutLabel = QLabel( "Task Timeout" )
        self.taskTimeoutLabel.setToolTip("The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.")
        self.jobOptionsLayout.addWidget( self.taskTimeoutLabel, 9, 0 )
        self.taskTimeoutWidget = QSpinBox( )
        self.jobOptionsLayout.addWidget( self.taskTimeoutWidget, 9, 1 )
        self.enableAutoTimeoutWidget = QCheckBox( "Enable Auto Task Timeout" )
        self.enableAutoTimeoutWidget.setToolTip("If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job.")
        self.jobOptionsLayout.addWidget( self.enableAutoTimeoutWidget, 9, 2 )
        
        self.concurrentTasksLabel = QLabel( "Concurrent Tasks" )
        self.concurrentTasksLabel.setToolTip("The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.")
        self.jobOptionsLayout.addWidget( self.concurrentTasksLabel, 10, 0 )
        self.concurrentTasksWidget = QSpinBox( )
        self.jobOptionsLayout.addWidget(self.concurrentTasksWidget, 10, 1)
        self.limtTasksSlaveLimit = QCheckBox( "Limit Tasks To Slave's Task Limit" )
        self.limtTasksSlaveLimit.setToolTip( "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )
        self.jobOptionsLayout.addWidget(self.limtTasksSlaveLimit, 10, 2)
        
        self.machineLimitLabel = QLabel( "Machine Limit" )
        self.machineLimitLabel.setToolTip("Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.")
        self.jobOptionsLayout.addWidget( self.machineLimitLabel, 11, 0 )
        self.machineLimitWidget = QSpinBox(  )
        self.jobOptionsLayout.addWidget(self.machineLimitWidget, 11, 1)
        self.isBlackListWidget = QCheckBox( "Machine List Is Blacklist" )
        self.isBlackListWidget.setToolTip("You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist.")
        self.jobOptionsLayout.addWidget(self.isBlackListWidget, 11, 2)
        
        self.machineListLabel = QLabel( "Machine List" )
        self.machineListLabel.setToolTip("The whitelisted or blacklisted list of machines.")
        self.jobOptionsLayout.addWidget( self.machineListLabel, 12, 0 )
        
        self.machineListLayout = QHBoxLayout()
        self.machineListWidget = QLineEdit( "" )
        self.machineListLayout.addWidget(self.machineListWidget)
        self.getMachineListWidget = QPushButton( "..." )
        self.getMachineListWidget.pressed.connect( self.browseMachineList )
        self.getMachineListWidget.setMaximumWidth(25)
        self.machineListLayout.addWidget(self.getMachineListWidget)
        self.jobOptionsLayout.addLayout( self.machineListLayout, 12, 1, 1, 2 )
        
        self.limitsLabel = QLabel( "Limits" )
        self.limitsLabel.setToolTip("The Limits that your job requires.")
        self.jobOptionsLayout.addWidget( self.limitsLabel, 13, 0 )
        self.limitsLayout = QHBoxLayout()
        self.limitsWidget = QLineEdit( "" )
        self.limitsLayout.addWidget(self.limitsWidget)
        self.getLimitsWidget = QPushButton( "..." )
        self.getLimitsWidget.pressed.connect( self.browseLimitList )
        self.getLimitsWidget.setMaximumWidth(25)
        self.limitsLayout.addWidget(self.getLimitsWidget)
        self.jobOptionsLayout.addLayout( self.limitsLayout, 13, 1, 1, 2 )
        
        self.dependenciesLabel = QLabel( "Dependencies" )
        self.dependenciesLabel.setToolTip("Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.")
        self.jobOptionsLayout.addWidget( self.dependenciesLabel, 14, 0 )
        self.dependenciesLayout = QHBoxLayout()
        self.dependenciesWidget = QLineEdit( "" )
        self.dependenciesLayout.addWidget(self.dependenciesWidget)
        self.getDependenciesWidget = QPushButton( "..." )
        self.getDependenciesWidget.setMaximumWidth(25)
        self.getDependenciesWidget.pressed.connect( self.browseDependencyList )
        self.dependenciesLayout.addWidget(self.getDependenciesWidget)
        self.jobOptionsLayout.addLayout( self.dependenciesLayout, 14, 1, 1, 2 )
        
        self.onJobCompleteLabel = QLabel( "On Job Complete" )
        self.onJobCompleteLabel.setToolTip("If desired, you can automatically archive or delete the job when it completes.")
        self.jobOptionsLayout.addWidget( self.onJobCompleteLabel, 15, 0 )
        self.onJobCompleteWidget = QComboBox( )
        self.jobOptionsLayout.addWidget(self.onJobCompleteWidget, 15, 1)
        self.submitSuspendedWidget = QCheckBox( "Submit Job as Suspended" )
        self.submitSuspendedWidget.setToolTip( "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.")
        self.jobOptionsLayout.addWidget(self.submitSuspendedWidget, 15, 2)
        
        self.jobOptionsSpacer = QSpacerItem( 0, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding )
        self.jobOptionsLayout.addItem( self.jobOptionsSpacer, 16, 0, 1, 3 )
        
        self.buttonLayout = QHBoxLayout()
        self.buttonLayoutSpacer = QSpacerItem( 0, 0, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum )
        self.buttonLayout.addItem( self.buttonLayoutSpacer )
        
        self.submitButton = QPushButton( "Submit" )
        self.submitButton.pressed.connect( self.submitToDeadline )
        self.buttonLayout.addWidget( self.submitButton )
        
        self.closeButton = QPushButton( "Close" )
        self.closeButton.pressed.connect( self.close )
        self.buttonLayout.addWidget( self.closeButton )
        
        self.dialogLayout.addLayout( self.buttonLayout )
        
        self.vredOptionsTab = QWidget()
        self.dialogTabs.addTab( self.vredOptionsTab, "VRED Options" )
        
        self.vredOptionsLayout = QGridLayout()
        self.vredOptionsTab.setLayout( self.vredOptionsLayout )
        
        separator2 = createSeparator( "General Options" )
        self.vredOptionsLayout.addWidget(separator2,0,0,1,3)
        
        self.renderJobTypeLabel = QLabel( "Job Type" )
        self.renderJobTypeLabel.setToolTip( "The type of job to Render." )
        self.vredOptionsLayout.addWidget( self.renderJobTypeLabel, 1, 0 )
        self.renderJobTypeWidget = QComboBox( )
        self.vredOptionsLayout.addWidget(self.renderJobTypeWidget, 1, 1)
        self.renderJobTypeWidget.currentIndexChanged.connect( self.jobTypeChanged )
        self.submitSceneWidget = QCheckBox( "Submit VRED Project File" )
        self.submitSceneWidget.setToolTip( "If this option is enabled, the project file will be submitted with the job, and then copied locally to the slave machine during rendering." )
        self.vredOptionsLayout.addWidget(self.submitSceneWidget, 1, 2)
        
        separator3 = createSeparator( "Render Options" )
        self.vredOptionsLayout.addWidget(separator3,2,0,1,3)
        
        self.renderOutputLabel = QLabel( "Render Output" )
        self.renderOutputLabel.setToolTip("The filename of the image(s) to be rendered.")
        self.vredOptionsLayout.addWidget(self.renderOutputLabel, 3, 0)
        
        self.renderOutputLayout = QHBoxLayout()
        self.renderOutputWidget = QLineEdit( "" )
        self.renderOutputButton = QPushButton( "..." )
        self.renderOutputButton.setMaximumWidth(25)
        self.renderOutputButton.pressed.connect( self.getRenderOutput )
        
        self.renderOutputLayout.addWidget(self.renderOutputWidget )
        self.renderOutputLayout.addWidget(self.renderOutputButton )
        
        self.vredOptionsLayout.addLayout(self.renderOutputLayout, 3, 1, 1, 2 )
                
        self.renderViewLabel = QLabel( "Render View / Camera" )
        self.renderViewLabel.setToolTip("The view or camera to render from, if left blank it will use the current view.")
        self.vredOptionsLayout.addWidget(self.renderViewLabel, 4, 0)
        self.renderViewWidget = QLineEdit( "" )
        self.vredOptionsLayout.addWidget(self.renderViewWidget, 4, 1, 1, 2 )
        
        self.renderAnimationWidget = QCheckBox( "Render Animation" )
        self.renderAnimationWidget.setToolTip("The animation to use, if left blank it will use all enabled clips.")
        self.renderAnimationWidget.stateChanged.connect( self.jobTypeChanged )
        self.vredOptionsLayout.addWidget(self.renderAnimationWidget, 5, 0 )
        #self.useRaytracingWidget = QCheckBox( "Use Raytracing" )
        #self.vredOptionsLayout.addWidget(self.useRaytracingWidget, 5, 1)
        
        self.renderQualityLabel = QLabel( "Render Quality" )
        self.renderQualityLabel.setToolTip("The Render quality to use.")
        self.vredOptionsLayout.addWidget( self.renderQualityLabel, 6, 0 )
        self.renderQualityWidget = QComboBox( )
        self.vredOptionsLayout.addWidget( self.renderQualityWidget, 6, 1, 1, 2 )
        
        self.frameRangeLabel = QLabel( "Frame Range" )
        self.frameRangeLabel.setToolTip("The list of frames to render.")
        self.vredOptionsLayout.addWidget( self.frameRangeLabel, 7, 0 )
        self.frameRangeWidget = QLineEdit( "" )
        self.vredOptionsLayout.addWidget(self.frameRangeWidget, 7, 1, 1, 2)
        
        self.framesPerTaskLabel = QLabel( "Frames Per Task" )
        self.framesPerTaskLabel.setToolTip("This is the number of frames that will be rendered at a time for each job task.")
        self.vredOptionsLayout.addWidget( self.framesPerTaskLabel, 8, 0 )
        self.framesPerTaskWidget = QSpinBox(  )
        self.vredOptionsLayout.addWidget( self.framesPerTaskWidget, 8, 1, 1, 2)
        
        separator4 = createSeparator( "Sequencer Options" )
        self.vredOptionsLayout.addWidget( separator4, 9, 0, 1, 3 )
        
        self.sequenceNameLabel = QLabel( "Sequence Name" )
        self.sequenceNameLabel.setToolTip("The name of the sequence to run, if empty all sequences will be run.")
        self.vredOptionsLayout.addWidget( self.sequenceNameLabel, 10, 0 )
        self.sequenceNameWidget = QLineEdit( "" )
        self.vredOptionsLayout.addWidget(self.sequenceNameWidget, 10, 1, 1, 2)
        
        self.vredOptionsSpacer = QSpacerItem( 0, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding )
        self.vredOptionsLayout.addItem( self.vredOptionsSpacer )
        
        self.regionRenderingPage = QWidget()
        self.dialogTabs.addTab( self.regionRenderingPage, "Region Rendering" )
        
        self.regionRenderingLayout = QGridLayout()
        self.regionRenderingPage.setLayout( self.regionRenderingLayout )
        
        self.enableRegionRenderingWidget = QCheckBox( "Enable Region Rendering" )
        self.enableRegionRenderingWidget.setToolTip("If this option is enabled, then the image will be divided into multiple tasks and assembled afterwards.")
        self.enableRegionRenderingWidget.stateChanged.connect( self.enableRegionRenderingChanged )
        self.regionRenderingLayout.addWidget( self.enableRegionRenderingWidget, 0, 0,1,2 )
        
        self.tilesInXLabel = QLabel( "Tiles in X" )
        self.tilesInXLabel.setToolTip( "The number of tiles to divide the region into." )
        self.regionRenderingLayout.addWidget(self.tilesInXLabel, 1, 0)
        self.tilesInXWidget = QSpinBox( )
        self.regionRenderingLayout.addWidget(self.tilesInXWidget, 1, 1 )
        
        self.tilesInYLabel = QLabel( "Tiles in Y" )
        self.tilesInYLabel.setToolTip( "The number of tiles to divide the region into." )
        self.regionRenderingLayout.addWidget(self.tilesInYLabel, 1, 2)
        self.tilesInYWidget = QSpinBox( )
        self.regionRenderingLayout.addWidget(self.tilesInYWidget, 1, 3 )
        
        self.submitDependentAssemblyWidget = QCheckBox( "Submit Dependent Assembly Job" )
        self.submitDependentAssemblyWidget.setToolTip("If this option is enabled then an assembly job will be submitted.")
        self.regionRenderingLayout.addWidget( self.submitDependentAssemblyWidget, 2, 0,1,2 )
        
        self.cleanupTilesWidget = QCheckBox( "Cleanup Tiles After Assembly" )
        self.cleanupTilesWidget.setToolTip("If this option is enabled, the tiles will be deleted after the assembly job is completed.")
        self.regionRenderingLayout.addWidget( self.cleanupTilesWidget, 2, 2,1,2 )
        
        self.errorOnMissingTilesWidget = QCheckBox( "Error on Missing Tiles" )
        self.errorOnMissingTilesWidget.setToolTip("If this option is enabled, the assembly job will fail if it cannot find any of the tiles.")
        self.regionRenderingLayout.addWidget( self.errorOnMissingTilesWidget, 3, 0,1,2 )
        
        self.errorOnMissingBackgroundWidget = QCheckBox( "Error on Missing Background" )
        self.errorOnMissingBackgroundWidget.setToolTip("If this option is enabled, the render will fail if the background image specified does not exist.")
        self.regionRenderingLayout.addWidget( self.errorOnMissingBackgroundWidget, 3, 2,1,2 )
        
        self.assembleOverLabel = QLabel( "Assemble Over" )
        self.assembleOverLabel.setToolTip( "The initial image you wish to assemble over." )
        self.regionRenderingLayout.addWidget(self.assembleOverLabel, 4, 0)
        self.assembleOverWidget = QComboBox( )
        self.assembleOverWidget.currentIndexChanged.connect( self.assembleOverChanged )
        self.regionRenderingLayout.addWidget(self.assembleOverWidget, 4, 1, 1, 3 )
        
        self.backgroundImageLabel = QLabel( "Background Image" )
        self.backgroundImageLabel.setToolTip("The background image file to be used for assembly over.")
        self.regionRenderingLayout.addWidget(self.backgroundImageLabel, 5, 0)
        
        self.backgroundImageLayout = QHBoxLayout()
        self.backgroundImageWidget = QLineEdit( "" )
        self.backgroundImageButton = QPushButton( "..." )
        self.backgroundImageButton.setMaximumWidth(25)
        self.backgroundImageButton.pressed.connect( self.getBackgroundFile )
        self.backgroundImageLayout.addWidget(self.backgroundImageWidget )
        self.backgroundImageLayout.addWidget(self.backgroundImageButton )
        
        self.regionRenderingLayout.addLayout(self.backgroundImageLayout, 5, 1, 1, 3)
        
        self.regionRenderingSpacer = QSpacerItem( 0, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding )
        self.regionRenderingLayout.addItem( self.regionRenderingSpacer )
        
        self.loadInitialSettings()
        self.enableRegionRenderingChanged()
    
    def enableRegionRenderingChanged( self ):
        enabled = self.enableRegionRenderingWidget.isChecked()
        
        self.tilesInXLabel.setEnabled( enabled )
        self.tilesInXWidget.setEnabled( enabled )
        self.tilesInYLabel.setEnabled( enabled )
        self.tilesInYWidget.setEnabled( enabled )
        self.submitDependentAssemblyWidget.setEnabled( enabled )
        self.cleanupTilesWidget.setEnabled( enabled )
        self.errorOnMissingTilesWidget.setEnabled( enabled )
        self.errorOnMissingBackgroundWidget.setEnabled( enabled )
        self.assembleOverLabel.setEnabled( enabled )
        self.assembleOverWidget.setEnabled( enabled )
        
        self.assembleOverChanged()
        
    def assembleOverChanged( self ):
    
        enabled = self.enableRegionRenderingWidget.isChecked() and ( self.assembleOverWidget.currentText() == "Selected Image" )
        
        self.backgroundImageLabel.setEnabled( enabled )
        self.backgroundImageWidget.setEnabled( enabled )
        self.backgroundImageButton.setEnabled( enabled )
    
    def getRenderOutput( self ):
        newOutputFile = QFileDialog.getSaveFileName( self, "Render Output", self.renderOutputWidget.text(), "*.bmp (*.bmp);;*.dds (*.dds);;*.dib (*.dib);;*.exr (*.exr);;*.hdr (*.hdr);;*.jfif (*.jfif);;*.jpe (*.jpe);;*.jpeg (*.jpeg);;*.jpg (*.jpg);;*.nrrd (*.nrrd);;*.pbm (*.pbm);;*.pgm (*.pgm);;*.png (*.png);;*.pnm (*.pnm);;*.ppm (*.ppm);;*.psb (*.psb);;*.psd (*.psd);;*.rle (*.rle);;*.tif (*.tif);;*.tiff (*.tiff);;*.bmp (*.vif)" )

        if newOutputFile:
            #PySide returns a tuple whilst PythonQt returns a QString
            if type(newOutputFile) == tuple:
                newOutputFile = newOutputFile[0]
            self.renderOutputWidget.setText(newOutputFile)
            
    def getBackgroundFile( self ):
        newBackgroundFile = QFileDialog.getOpenFileName( self, "Background Image", self.backgroundImageWidget.text(), "All Files (*.*)" )
        
        if newBackgroundFile:
            #PySide returns a tuple whilst PythonQt returns a QString
            if type(newBackgroundFile) == tuple:
                newBackgroundFile = newBackgroundFile[0]
            self.backgroundImageWidget.setText(newBackgroundFile)
        
    def submitToDeadline( self ):
        sceneFile = getFileIOFilePath()
        submitScene = self.submitSceneWidget.isChecked()

        jobName = self.jobNameWidget.text()

        if jobName == "":
            QMessageBox.critical( self, "Error", "No Job Name specified." )
            return
        
        type = self.renderJobTypeWidget.currentIndex()
        
        isRender = ( type == 0)
        isRenderQueue = ( type == 1 )
        isSequencer = ( type == 2 )
        
        isRegionRendering = isRender and self.enableRegionRenderingWidget.isChecked()
        isAnimation = self.renderAnimationWidget.isChecked()
        submitDependent = self.submitDependentAssemblyWidget.isChecked()
        
        if not submitScene and IsPathLocal(sceneFile):
            result = QMessageBox.question( self, "Warning", "The VRED file %s is local. Are you sure you want to continue?" % sceneFile,  QMessageBox.Yes|QMessageBox.No )
            if result == QMessageBox.No:
                return
        
        outputFile = self.renderOutputWidget.text()
        outputDir = os.path.dirname( outputFile )
        
        # Check output file / directory
        if isRender:
            if( len( outputFile ) == 0):
                QMessageBox.critical( self, "Error", "No output file specified!" )
                return
            elif( not os.path.exists(outputDir) ):
                QMessageBox.critical( self, "Error", "Directory for output file does not exist!" )
                return
            elif IsPathLocal( outputFile ):
                result = QMessageBox.question( self, "Warning", "The output file %s is local. Are you sure you want to continue?" % outputFile,  QMessageBox.Yes|QMessageBox.No )
                if result == QMessageBox.No:
                    return

        deadlineHome = CallDeadlineCommand( ["-GetCurrentUserHomeDirectory",] )
        deadlineHome = deadlineHome.replace( "\n", "" ).replace( "\r", "" )
        
        deadlineTemp = os.path.join( deadlineHome, "temp" )
        
        enabledPasses = getRenderPasses()
        useRenderPasses = getUseRenderPasses()
        
        successes = 0
        failures = 0
        
        jobIds = []
        
        regionJobCount = 1
        regionOutputCount = 1
        TilesInX = 1
        TilesInY = 1
        currTime = ""

        if isRender and isRegionRendering:
            TilesInX = self.tilesInXWidget.value()
            TilesInY = self.tilesInYWidget.value()
            if isAnimation:
                regionJobCount = TilesInX * TilesInY
            else:
                regionOutputCount = TilesInX * TilesInY

            if isAnimation or submitDependent:
                currTime = time.strftime(" [%m/%d/%Y %H:%M:%S %p]", time.localtime())
        
        batchname = jobName+currTime
        
        for regionJobID in range( regionJobCount ):
            renderJobName = jobName
            if isRegionRendering and isAnimation:
                renderJobName += " - Region " + str( regionJobID )
            
            jobInfoFilename = os.path.join( deadlineTemp, "vred_job_info.job" )
            fileHandle = open( jobInfoFilename, "w" )
            
            fileHandle.write( "Plugin=VRED\n" )
            fileHandle.write( "Name=%s\n" % renderJobName )
            fileHandle.write( "Comment=%s\n" % self.commentWidget.text() )
            fileHandle.write( "Department=%s\n" % self.departmentWidget.text() )
            fileHandle.write( "Pool=%s\n" % self.poolWidget.currentText() )
            fileHandle.write( "SecondaryPool=%s\n" % self.secondaryPoolWidget.currentText() )
            fileHandle.write( "Group=%s\n" % self.groupWidget.currentText() )
            fileHandle.write( "Priority=%s\n" % str( self.priorityWidget.value() ) )
            fileHandle.write( "TaskTimeoutMinutes=%s\n" % str( self.taskTimeoutWidget.value() ) )
            fileHandle.write( "EnableAutoTimeout=%s\n" % str( self.enableAutoTimeoutWidget.isChecked() ) )
            fileHandle.write( "ConcurrentTasks=%s\n" % str(self.concurrentTasksWidget.value() ) )
            fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % str(self.limtTasksSlaveLimit.isChecked()) )
            fileHandle.write( "MachineLimit=%s\n" % str(self.machineLimitWidget.value() ) )
            if self.isBlackListWidget.isChecked():
                fileHandle.write( "Blacklist=%s\n" % self.machineListWidget.text() )
            else:
                fileHandle.write( "Whitelist=%s\n" % self.machineListWidget.text() )
            
            fileHandle.write( "LimitGroups=%s\n" % self.limitsWidget.text() )
            fileHandle.write( "JobDependencies=%s\n" % self.dependenciesWidget.text() )
            fileHandle.write( "OnJobComplete=%s\n" % self.onJobCompleteWidget.currentText() )
            
            if self.submitSuspendedWidget.isChecked():
                fileHandle.write( "InitialStatus=Suspended\n" )
            
            if isRender and isAnimation:
                fileHandle.write( "ChunkSize=%s\n" % str(self.framesPerTaskWidget.value()) )
                fileHandle.write( "Frames=%s\n" % self.frameRangeWidget.text() )
                animationFileName,animationFileExt = os.path.splitext(outputFile)
                fileHandle.write( "OutputFilename0=%s\n" %( animationFileName + "-#####" + animationFileExt )  )
            else:
                if isRender and isRegionRendering:
                    fileHandle.write( "TileJob=True\n")
                    fileHandle.write( "TileJobFrame=0\n" )
                    fileHandle.write( "TileJobTilesInX=%s\n" % TilesInX )
                    fileHandle.write( "TileJobTilesInY=%s\n" % TilesInY )
                    fileHandle.write( "OutputDirectory0=%s\n" % outputDir )
                else:
                    fileHandle.write( "Frames=0\n" )
                    fileHandle.write( "ChunkSize=1\n" )
                    if isRender:
                        fileHandle.write( "OutputFilename0=%s\n" % outputFile  )
            
            if isRender and isRegionRendering:
                if isAnimation or submitDependent:
                    fileHandle.write( "BatchName=%s\n" % batchname  )
            
            fileHandle.close()
            
            pluginInfoFilename = os.path.join( deadlineTemp, "vred_plugin_info.job" )
            fileHandle = open( pluginInfoFilename, "w" )
            
            if not submitScene:
                fileHandle.write( "SceneFile=%s\n" % sceneFile )
            
            fileHandle.write( "OutputFile=%s\n" % outputFile )
            numVersion = float( getVredVersion() ) 
            fileHandle.write( "Version=%.1f\n" % numVersion )
            fileHandle.write( "JobType=%s\n" % self.renderJobTypeWidget.currentText() )
            fileHandle.write( "RenderAnimation=%s\n" % isAnimation )
            fileHandle.write( "AnimationClip=%s\n" % getRenderAnimationClip() )
            fileHandle.write( "View=%s\n" % self.renderViewWidget.text() )#Can't pull view?
            fileHandle.write( "AnimationType=%s\n" % getRenderAnimationType() )
            fileHandle.write( "RenderWidth=%s\n" % int( getRenderPixelWidth() ) )
            fileHandle.write( "RenderHeight=%s\n" % int( getRenderPixelHeight() ) )
            fileHandle.write( "DPI=%s\n" % int(getRenderPixelPerInch()) )
            fileHandle.write( "SuperSamplingFactor=%s\n" % getRenderSupersampling() )
            
            bgColor = getRenderBackgroundColor()
            fileHandle.write( "BackgroundRed=%s\n" % bgColor.x() )
            fileHandle.write( "BackgroundBlue=%s\n" % bgColor.y() )
            fileHandle.write( "BackgroundGreen=%s\n" % bgColor.z() )
            
            fileHandle.write( "IncludeAlphaChannel=%s\n" % getRenderAlpha() )
            fileHandle.write( "PremultiplyAlpha=%s\n" % getRenderPremultiply() )
            fileHandle.write( "TonemapHDR=%s\n" % getRenderTonemapHDR() )
                    
            fileHandle.write( "RenderQuality=%s\n" % self.renderQualityWidget.currentText() )
            fileHandle.write( "OverrideRenderPass=False\n" )
            fileHandle.write( "ExportRenderPass=%s\n" % useRenderPasses )
            
            
            fileHandle.write( "BeautyPass=%s\n" % ( "beauty" in enabledPasses  ) )
            fileHandle.write( "DiffuseIBLPass=%s\n" % ( "diffuse_ibl" in enabledPasses  ) )
            fileHandle.write( "DiffuseLightPass=%s\n" % ( "diffuse_light" in enabledPasses  ) )
            fileHandle.write( "DiffuseIndirectPass=%s\n" % ( "diffuse_indirect" in enabledPasses  ) )
            fileHandle.write( "IncandescencePass=%s\n" % ( "incandescence" in enabledPasses  ) )
            fileHandle.write( "BackgroundColorPass=%s\n" % ( "background_color" in enabledPasses  ) )
            fileHandle.write( "SpecularReflectionPass=%s\n" % ( "specular_reflection" in enabledPasses  ) )
            fileHandle.write( "GlossyIBLPass=%s\n" % ( "glossy_ibl" in enabledPasses  ) )
            fileHandle.write( "GlossyLightPass=%s\n" % ( "glossy_light" in enabledPasses  ) )
            fileHandle.write( "GlossyIndirectPass=%s\n" % ( "glossy_indirect" in enabledPasses  ) )
            fileHandle.write( "TranslucentPass=%s\n" % ( "translucency" in enabledPasses  ) )
            fileHandle.write( "TransparencyColorPass=%s\n" % ( "transparency_color" in enabledPasses  ) )
            fileHandle.write( "OcclusionPass=%s\n" % ( "occlusion" in enabledPasses  ) )
            fileHandle.write( "MaskPass=%s\n" % ( "mask" in enabledPasses  ) )
            fileHandle.write( "MaterialIDPass=%s\n" % ( "materialID" in enabledPasses  ) )
            fileHandle.write( "DepthPass=%s\n" % ( "depth" in enabledPasses  ) )
            fileHandle.write( "NormalPass=%s\n" % ( "normal" in enabledPasses  ) )
            fileHandle.write( "PositionPass=%s\n" % ( "position" in enabledPasses  ) )
            fileHandle.write( "ViewVectorPass=%s\n" % ( "view" in enabledPasses  ) )
            fileHandle.write( "DiffuseColorPass=%s\n" % ( "diffuse_color" in enabledPasses  ) )
            fileHandle.write( "GlossyColorPass=%s\n" % ( "glossy_color" in enabledPasses  ) )
            fileHandle.write( "SpecularColorPass=%s\n" % ( "specular_color" in enabledPasses  ) )
            fileHandle.write( "TranslucencyColorPass=%s\n" % ( "translucency_color" in enabledPasses  ) )
            fileHandle.write( "IBLDiffusePass=%s\n" % ( "diffuse_ibl_illumination" in enabledPasses  ) )
            fileHandle.write( "LightsDiffusePass=%s\n" % ( "diffuse_light_illumination" in enabledPasses  ) )
            fileHandle.write( "IndirectDiffusePass=%s\n" % ( "diffuse_indirect_illumination" in enabledPasses  ) )
            fileHandle.write( "IBLGlossyPass=%s\n" % ( "glossy_ibl_illumination" in enabledPasses  ) )
            fileHandle.write( "LightsGlossyPass=%s\n" % ( "glossy_light_illumination" in enabledPasses  ) )
            fileHandle.write( "IndirectGlossyPass=%s\n" % ( "glossy_indirect_illumination" in enabledPasses  ) )
            fileHandle.write( "IBLTranslucencyPass=%s\n" % ( "translucency_ibl_illumination" in enabledPasses  ) )
            fileHandle.write( "LightTranslucencyPass=%s\n" % ( "translucency_light_illumination" in enabledPasses  ) )
            fileHandle.write( "IndirectTranslucencyPass=%s\n" % ( "translucency_indirect_illumination" in enabledPasses  ) )
            fileHandle.write( "IndirectSpecularPass=%s\n" % ( "specular_indirect_illumination" in enabledPasses  ) )
            
            fileHandle.write( "OverrideMetaData=False\n" )
            metaDataFlags = getRenderMetaDataFlags()
            
            fileHandle.write( "EmbedSwitchMaterialStates=%s\n" % ( metaDataFlags > 127) )
            if metaDataFlags > 127:
                metaDataFlags -= 128
            fileHandle.write( "EmbedCameraSettings=%s\n" % ( metaDataFlags % 2 == 1 ) )        
            metaDataFlags = metaDataFlags / 2
            fileHandle.write( "EmbedNodeVisibilities=%s\n" % ( metaDataFlags % 2 == 1 ) )        
            metaDataFlags = metaDataFlags / 2
            fileHandle.write( "EmbedSwitchNodeStates=%s\n" % ( metaDataFlags % 2 == 1 ) )        
            metaDataFlags = metaDataFlags / 2
            fileHandle.write( "EmbedRenderSettings=%s\n" % ( metaDataFlags > 0 ) )
            
            fileHandle.write(  "RegionRendering=%s\n" % (isRender and isRegionRendering) )
            
            if isRender and isRegionRendering:
                if isAnimation:
                    x = regionJobID % TilesInX
                    y = regionJobID / TilesInX
                    
                    left = float( getRenderPixelWidth() ) / TilesInX * x
                    right = float( getRenderPixelWidth() ) / TilesInX * ( x+1)
                    
                    bottom = float( getRenderPixelHeight() ) / TilesInY * y
                    top = float( getRenderPixelHeight() ) / TilesInY * ( y+1)
                    
                    fileHandle.write( "RegionLeft=%s\n" % int( left + 0.5 )  )
                    fileHandle.write( "RegionRight=%s\n" % int( right + 0.5 )  )
                    fileHandle.write( "RegionBottom=%s\n" % int( bottom + 0.5 )  )
                    fileHandle.write( "RegionTop=%s\n" % int( top + 0.5 )  )
                    
                    fileHandle.write( "RegionID=%s\n" % regionJobID  )
                    
                else:
                    regionCounter = 0
                    for y in range( TilesInY ):
                        for x in range(TilesInX ):
                            left = float( getRenderPixelWidth() ) / TilesInX * x
                            right = float( getRenderPixelWidth() ) / TilesInX * ( x+1)
                            
                            bottom = float( getRenderPixelHeight() ) / TilesInY * y
                            top = float( getRenderPixelHeight() ) / TilesInY * ( y+1)
                            
                            fileHandle.write( "RegionLeft%s=%s\n" % ( regionCounter, int( left + 0.5 ) ) )
                            fileHandle.write( "RegionRight%s=%s\n" % ( regionCounter,  int( right + 0.5 ) ) )
                            fileHandle.write( "RegionBottom%s=%s\n" % ( regionCounter, int( bottom + 0.5 ) ) )
                            fileHandle.write( "RegionTop%s=%s\n" % ( regionCounter, int( top + 0.5 ) ) )
                            
                            regionCounter += 1
            
            fileHandle.close()
            
            arguments = []
            arguments.append( jobInfoFilename )
            arguments.append( pluginInfoFilename )
            
            if submitScene:
                arguments.append( sceneFile )
            
            results = CallDeadlineCommand( arguments )
            print(results)
            successfulSubmission = ( results.find( "Result=Success" ) != -1 )
            if successfulSubmission:
                successes+=1
                jobId = "";
                resultArray = results.split()
                for line in resultArray:
                    if line.startswith("JobID="):
                        jobId = line.replace("JobID=","")
                        break
                if not jobId == "":
                    jobIds.append(jobId)
            else:
                failures+=1
       
        if isRender and isRegionRendering and submitDependent:
            
            renderPasses = [ None ]
            if useRenderPasses:
                renderPasses = enabledPasses
            
            if isAnimation:
                frames = self.frameRangeWidget.text()
                frameListString = CallDeadlineCommand( [ "-ParseFrameList", frames, "False" ] ).strip()
                frameList = frameListString.split( ",")
                
                for renderPass in renderPasses:
                    configFiles = []
                    for frame in frameList:
                        configFiles.append( self.createConfigFile( deadlineTemp, frame, renderPass) )
                    
                    successfulSubmission =  self.submitAssemblyJob( deadlineTemp, configFiles, batchname, jobIds, renderPass )
                    
                    if successfulSubmission:
                        successes+=1
                    else:
                        failures+=1
            else:
                configFiles = []
                for renderPass in renderPasses:
                    configFiles.append( self.createConfigFile( deadlineTemp, renderPass = renderPass) )
                
                successfulSubmission =  self.submitAssemblyJob( deadlineTemp, configFiles, batchname, jobIds )
                    
                if successfulSubmission:
                    successes+=1
                else:
                    failures+=1
                
        if (successes + failures) == 1:
            QMessageBox.information( self, "Results", results )
        elif (successes + failures) > 1:
            QMessageBox.information( self, "Results", "Submission Results\n\nSuccesses: " + str(successes) + "\nFailures: " + str(failures) + "\n\nSee script console for more details" )
    
    def submitAssemblyJob( self, deadlineTemp, configFiles, batchname, jobIds, renderPass=None):
        jobName = self.jobNameWidget.text()
        
        assemblyJobName = jobName + " - Tile Assembly Job"
        if renderPass:
            assemblyJobName += " - " + renderPass
            
        jobInfoFilename = os.path.join( deadlineTemp, "vred_assembly_job_info.job" )
        fileHandle = open( jobInfoFilename, "w" )
            
        fileHandle.write( "Plugin=DraftTileAssembler\n" )
        fileHandle.write( "Name=%s\n" % assemblyJobName )
        fileHandle.write( "Comment=Draft Tile Assembly Job\n" )
        fileHandle.write( "Department=%s\n" % self.departmentWidget.text() )
        fileHandle.write( "Pool=%s\n" % self.poolWidget.currentText() )
        fileHandle.write( "SecondaryPool=%s\n" % self.secondaryPoolWidget.currentText() )
        fileHandle.write( "Group=%s\n" % self.groupWidget.currentText() )
        fileHandle.write( "Priority=%s\n" % str( self.priorityWidget.value() ) )
        fileHandle.write( "TaskTimeoutMinutes=%s\n" % str( self.taskTimeoutWidget.value() ) )
        fileHandle.write( "EnableAutoTimeout=%s\n" % str( self.enableAutoTimeoutWidget.isChecked() ) )
        fileHandle.write( "ConcurrentTasks=%s\n" % str(self.concurrentTasksWidget.value() ) )
        fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % str(self.limtTasksSlaveLimit.isChecked()) )
        fileHandle.write( "MachineLimit=%s\n" % str(self.machineLimitWidget.value() ) )
            
        if self.isBlackListWidget.isChecked():
            fileHandle.write( "Blacklist=%s\n" % self.machineListWidget.text() )
        else:
            fileHandle.write( "Whitelist=%s\n" % self.machineListWidget.text() )
        
        fileHandle.write( "LimitGroups=%s\n" % self.limitsWidget.text() )
        fileHandle.write( "JobDependencies=%s\n" % ",".join( jobIds ) )
        fileHandle.write( "OnJobComplete=%s\n" % self.onJobCompleteWidget.currentText() )
        fileHandle.write( "BatchName=%s\n" % (batchname) )
            
        if self.submitSuspendedWidget.isChecked():
            fileHandle.write( "InitialStatus=Suspended\n" )
        
        isAnimation = self.renderAnimationWidget.isChecked()
        outputFile = self.renderOutputWidget.text()
        if isAnimation:
            fileHandle.write( "ChunkSize=1\n" )
            fileHandle.write( "Frames=%s\n" % self.frameRangeWidget.text() )
            
            fileHandle.write( "OutputFilename0=%s\n" %( self.addAnimationFrame( outputFile, "", paddingCharacter = "#" ) )  )
        else:
            fileHandle.write( "Frames=0-%s\n" % ( len(configFiles) -1) )
            fileHandle.write( "ChunkSize=1\n" )
            fileHandle.write( "OutputFilename0=%s\n" % outputFile  )
            
        fileHandle.close()
        
        pluginInfoFile = os.path.join( deadlineTemp, "vred_assembly_plugin_info.job" )
        fileHandle = open( pluginInfoFile, "wb" )   
        
        fileHandle.write( "ErrorOnMissing=%s\n" % self.errorOnMissingTilesWidget.isChecked() )
        fileHandle.write( "ErrorOnMissingBackground=%s\n" % self.errorOnMissingBackgroundWidget.isChecked() )
        
        fileHandle.write( "CleanupTiles=%s\n" % self.cleanupTilesWidget.isChecked() )
        fileHandle.write( "MultipleConfigFiles=%s\n" % ( len( configFiles ) > 0 ) )
        
        fileHandle.close()
        
        arguments = []
        arguments.append( jobInfoFilename )
        arguments.append( pluginInfoFile )
        arguments.extend( configFiles )
        
        results = CallDeadlineCommand( arguments )
        print(results)
        
        successfulSubmission = ( results.find( "Result=Success" ) != -1 )
        return successfulSubmission
    
    def createConfigFile( self, deadlineTemp, frame=0, renderPass=None ):
            
        outputFile = self.renderOutputWidget.text()
        isAnimation = self.renderAnimationWidget.isChecked()
        
        tempOutputFileName = os.path.basename(outputFile)
        fileName, ext = os.path.splitext(tempOutputFileName)
        
        configFilename = ""
        date = time.strftime("%Y_%m_%d_%H_%M_%S")
        configFilename = fileName
        if isAnimation:
            configFilename += "_"+str(frame)
        
        if renderPass:
            configFilename += "_"+renderPass
        
        configFilename += "_config_"+date+".txt"

        configFilename = os.path.join( deadlineTemp, configFilename )
                
        fileHandle = open( configFilename, "w" )
        fileHandle.write( "\n" )
        
        tempOutputFile = outputFile
        tempOutputFile = self.addRenderPass( tempOutputFile, renderPass )
        if isAnimation:
            tempOutputFile = self.addAnimationFrame( tempOutputFile, frame)
        
        fileHandle.write( "ImageFileName=" +tempOutputFile +"\n" )
        
        backgroundType = self.assembleOverWidget.currentText()
        
        width = int ( getRenderPixelWidth() )
        height = int( getRenderPixelHeight() )
        
        if backgroundType == "Previous Output":
            fileHandle.write( "BackgroundSource=" +tempOutputFile +"\n" )
        elif backgroundType == "Selected Image":
            fileHandle.write( "BackgroundSource=" + self.backgroundImageWidget.text() +"\n" )
        
        fileHandle.write( "ImageWidth=%s\n" % width )
        fileHandle.write( "ImageHeight=%s\n" % height )
        fileHandle.write( "TilesCropped=False\n" )
        
        TilesInX = self.tilesInXWidget.value()
        TilesInY = self.tilesInYWidget.value()
        fileHandle.write( "TileCount=" +str( TilesInX * TilesInY ) + "\n" )
       
        regionCounter = 0
        for y in range( TilesInY ):
            for x in range(TilesInX ):
                left = float( width ) / TilesInX * x
                right = float( width ) / TilesInX * ( x+1)
                
                bottom = float( height ) / TilesInY * y
                top = float( height ) / TilesInY * ( y+1)
                
                left = int( left + 0.5 )
                right = int( right + 0.5 )
                bottom = int( bottom + 0.5 )
                top = int( top + 0.5 )
                
                regionOutputFileName = outputFile
                regionOutputFileName = self.addRegionNumber( regionOutputFileName, regionCounter )
                regionOutputFileName = self.addRenderPass( regionOutputFileName, renderPass )
                if isAnimation:
                    regionOutputFileName = self.addAnimationFrame( regionOutputFileName, frame)
                
                fileHandle.write( "Tile%iFileName=%s\n"%(regionCounter,regionOutputFileName) )
                
                fileHandle.write( "Tile%iX=%s\n"%(regionCounter, left) )
                fileHandle.write( "Tile%iY=%s\n"%(regionCounter, height - top) )
                fileHandle.write( "Tile%iWidth=%s\n"%(regionCounter, ( right - left ) ) )
                fileHandle.write( "Tile%iHeight=%s\n"%(regionCounter, ( top - bottom ) ) )
                
                regionCounter += 1
        
        fileHandle.close()
        
        return configFilename
    
    def addRenderPass(self, file, renderPass):
        if renderPass:
            tempFile, tempExt = os.path.splitext( file )
            file = tempFile+"-"+renderPass+tempExt
        return file
    
    def addAnimationFrame( self, file, frame, paddingCharacter="0" ):
        tempFile, tempExt = os.path.splitext( file )
        tempFrame = str(frame)
        while len(tempFrame) < 5:
            tempFrame = paddingCharacter+tempFrame
            
        return tempFile + "-" + tempFrame + tempExt
        
    def addRegionNumber( self, file, regionID ):
        tempFile, tempExt = os.path.splitext( file )
        return tempFile + "_region_" + str( regionID ) + "_" + tempExt
    
    def jobTypeChanged( self ):
        type = self.renderJobTypeWidget.currentIndex()
        
        isRender = ( type == 0)
        isRenderQueue = ( type == 1 )
        isSequencer = ( type == 2 )
        
        isRenderAnimation = self.renderAnimationWidget.isChecked()
        
        self.renderOutputWidget.setEnabled( isRender )
        self.renderViewWidget.setEnabled( isRender )
        self.renderAnimationWidget.setEnabled( isRender )
        self.renderQualityWidget.setEnabled( isRender )
        self.frameRangeWidget.setEnabled( isRender and isRenderAnimation )
        self.framesPerTaskWidget.setEnabled( isRender and isRenderAnimation )
        
        self.sequenceNameWidget.setEnabled( isSequencer )
        
    def browseMachineList( self ):
        output = CallDeadlineCommand(["-selectmachinelist", str(self.machineListWidget.text())], False)
        output = output.replace("\r", "").replace("\n", "")
        if output != "Action was cancelled by user":
            self.machineListWidget.setText(output)
    
    def browseLimitList( self ):
        output = CallDeadlineCommand(["-selectlimitgroups", str(self.limitsWidget.text())], False)
        output = output.replace("\r", "").replace("\n", "")
        if output != "Action was cancelled by user":
            self.limitsWidget.setText(output)
    
    def browseDependencyList( self ):
        output = CallDeadlineCommand(["-selectdependencies", str(self.dependenciesWidget.text())], False)
        output = output.replace("\r", "").replace("\n", "")
        if output != "Action was cancelled by user":
            self.dependenciesWidget.setText(output)
    
    def loadInitialSettings( self ):
        path = getFileIOFilePath()
        filename = os.path.basename(path)
        
        self.jobNameWidget.setText( os.path.splitext(filename)[0] )
        
        # Collect the pools and groups.
        output = CallDeadlineCommand( ["-pools",] )
        pools = output.splitlines()
        
        secondaryPools = []
        secondaryPools.append("")
        for currPool in pools:
            secondaryPools.append(currPool)
        
        output = CallDeadlineCommand( ["-groups",] )
        groups = output.splitlines()
        
        self.poolWidget.addItems(pools)
        self.secondaryPoolWidget.addItems(secondaryPools)
        self.groupWidget.addItems(groups)
        
        # Get maximum priority.
        maximumPriority = 100
        try:
            output = CallDeadlineCommand( ["-getmaximumpriority",] )
            maximumPriority = int(output)
        except:
            # If an error occurs here, just ignore it and use the default of 100.
            pass
            
        self.priorityWidget.setMaximum(maximumPriority)
        self.priorityWidget.setValue( min(50,maximumPriority) )
        
        self.taskTimeoutWidget.setMaximum( 1000000 )
        self.concurrentTasksWidget.setMinimum( 1 )
        self.concurrentTasksWidget.setMaximum( 16 )
        self.machineLimitWidget.setMaximum( 1000000 )
        
        onJobCompleteOptions = ("Nothing", "Archive", "Delete")
        self.onJobCompleteWidget.addItems( onJobCompleteOptions )
        
        jobTypeOptions = ( "Render", "Render Queue", "Sequencer" )
        self.renderJobTypeWidget.addItems( jobTypeOptions )
        
        startFrame =  getRenderStartFrame()
        endFrame = getRenderStopFrame()
        frameStep = getRenderFrameStep()
        
        frameString = str(startFrame)
        if not startFrame == endFrame:
            frameString += "-" + str(endFrame)
            if frameStep > 1:
                frameString +="x"+str(frameStep)
        
        self.renderOutputWidget.setText( getRenderFilename() )
        
        self.frameRangeWidget.setText( frameString )
        
        self.renderAnimationWidget.setChecked( getRenderAnimation() )
        
        self.framesPerTaskWidget.setMinimum( 1 )
        
        qualities = ( "Analytic Low", "Analytic High", "Realistic Low", "Realistic High", "Raytracing", "NPR" )
        self.renderQualityWidget.addItems( qualities )
        self.renderQualityWidget.setCurrentIndex(4)
        
        self.tilesInXWidget.setMinimum( 1 )
        self.tilesInXWidget.setMaximum( 1000000 )
        self.tilesInXWidget.setValue( 2 )
        
        self.tilesInYWidget.setMinimum( 1 )
        self.tilesInYWidget.setMaximum( 1000000 )
        self.tilesInYWidget.setValue( 2 )
        
        self.submitDependentAssemblyWidget.setChecked( True )
        
        backgroundOptions = ( "Blank Image", "Previous Output", "Selected Image" )
        self.assembleOverWidget.addItems( backgroundOptions )
        
def createSeparator( text ):
    separator = QWidget()
    separator.resize( 308, 37 )
    sepLayout = QHBoxLayout(separator)
    sepLayout.setContentsMargins(0, 0, 0, -1)
    
    sepLabel = QLabel(separator)
    sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(sepLabel.sizePolicy().hasHeightForWidth())
    sepLabel.setSizePolicy(sizePolicy)
    font = QFont()
    font.setBold(True)
    sepLabel.setFont(font)
    sepLabel.setText(text)
    sepLayout.addWidget(sepLabel)
    
    sepLine = QFrame(separator)
    sepLine.setFrameShadow(QFrame.Sunken)
    sepLine.setFrameShape(QFrame.HLine)
    sepLayout.addWidget(sepLine)
    
    return separator

# Checks if the path is local
def IsPathLocal( path ):
    lowerPath = path.lower()
    return lowerPath.startswith( "c:" ) or lowerPath.startswith( "d:" ) or lowerPath.startswith( "e:" )

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
    
def CallDeadlineCommand( arguments, hideWindow=True ):
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
    
    arguments.insert( 0, deadlineCommand)
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags)
    proc.stdin.close()
    proc.stderr.close()
    
    output = proc.stdout.read()
    
    return output
    
def vredMainWindow( window=None ): 
    try:
        main_window_ptr = getMainWindow()
        return wrapInstance(long(main_window_ptr), QMainWindow)
    except:
        return window
