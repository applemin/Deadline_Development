from __future__ import print_function
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from System.Diagnostics import *
from System.IO import *
from Deadline.Events import *
from Deadline.Scripting import *

import traceback
import socket
import threading
import os
import sys
import imp
import inspect

draftRepoPath = RepositoryUtils.GetRepositoryPath( "draft", False)
if SystemUtils.IsRunningOnMac():
    draftRepoPath = Path.Combine( draftRepoPath, "Mac" )
else:
    if SystemUtils.IsRunningOnLinux():
        draftRepoPath = Path.Combine(ClientUtils.GetBinDirectory(),"python","lib")+Path.PathSeparator+Path.Combine( draftRepoPath, "Linux" )
    else:
        draftRepoPath = Path.Combine( draftRepoPath, "Windows" )
    
    if SystemUtils.Is64Bit():
        draftRepoPath = Path.Combine( draftRepoPath, "64bit" )
    else:
        draftRepoPath = Path.Combine( draftRepoPath, "32bit" )
        
sys.path.append(draftRepoPath)

    
#Dialog to control Jigsaw
class JigsawForm(QWidget):
    backgroundImage=None
    jigThread=None
    mainTimer=None
    dirty = False
    quitting = False
    
    changingTable = False
    changingItemSelection = False
    #undo/Redo
    undoList = []
    redoList = []
    currSetup = None
    updatingZoom = False
    def __init__(self, parent=None, background=None, port=0, openThread = True, minWidth=0, minHeight=0, allowFit = True):
        try:
            super(JigsawForm, self).__init__(parent)
            
            reader = QImageReader(background)
            if reader.canRead():
                self.backgroundImage=reader.read()
            else:
                try:
                    import Draft
                except:
                    QMessageBox.information(None,"Error", "Failed to import Draft")
                    return
                
                img = Draft.Image.ReadFromFile(str(background))
                newName = os.path.splitext(background)[0]+".png"
                img.WriteToFile(str(newName))
                reader = QImageReader(newName)
                self.backgroundImage = reader.read()
                    
            
            self.minWidth = minWidth
            self.minHeight = minHeight
            
            self.scene = QGraphicsScene()
            self.setWindowFlags(self.windowFlags ()| Qt.WindowMinimizeButtonHint);
            
            self.viewport = JigsawView(self.scene, background=self.backgroundImage)
            self.scene.selectionChanged.connect(self.onSelectionChanged)
            #Create the UI adding all of the buttons
            self.addBtn = QPushButton("Add Region")
            self.addBtn.clicked.connect(self.createRegion)
            self.addBtn.setDefault(False)
            self.addBtn.setAutoDefault(False)
            self.addBtn.setToolTip("Add a 50X50 Region to the top Left corner")
            
            self.deleteBtn = QPushButton("Delete")
            self.deleteBtn.clicked.connect(self.deleteSelectedRegions)
            self.deleteBtn.setDefault(False)
            self.deleteBtn.setAutoDefault(False)
            self.deleteBtn.setToolTip("Delete all selected regions")
            
            self.deleteAllBtn = QPushButton("Delete All")
            self.deleteAllBtn.clicked.connect(self.deleteAllRegions)
            self.deleteAllBtn.setDefault(False)
            self.deleteAllBtn.setAutoDefault(False)
            self.deleteAllBtn.setToolTip("Delete all regions")
            
            self.mergeBtn = QPushButton("Merge")
            self.mergeBtn.clicked.connect(self.mergeSelectedRegions)
            self.mergeBtn.setDefault(False)
            self.mergeBtn.setAutoDefault(False)
            self.mergeBtn.setToolTip("Merge the selected regions to create a single region that covers the full area of the selected regions.")
            
            self.splitBtn = QPushButton("Split")
            self.splitBtn.clicked.connect(self.splitSelectedRegions)
            self.splitBtn.setDefault(False)
            self.splitBtn.setAutoDefault(False)
            self.splitBtn.setToolTip("Split the selected Regions tiles into separate regions.")
            
            self.lockBtn = QCheckBox("Lock Position")
            self.lockBtn.stateChanged.connect(self.lockSelectedRegion)
            self.lockBtn.setToolTip("Locks the position and size of the region.")
            
            self.enableBtn = QCheckBox("Enable Region")
            self.enableBtn.stateChanged.connect(self.enableSelectedRegion)
            self.enableBtn.setToolTip("Enable/Disable the region for renders.")
            
            self.getSelectedBtn = QPushButton("Fit Selection")
            self.getSelectedBtn.clicked.connect(self.getSelectedRegion)
            self.getSelectedBtn.setDefault(False)
            self.getSelectedBtn.setAutoDefault(False)
            self.getSelectedBtn.setToolTip("Create regions around the objects that are selected in the scene.")
            self.getSelectedBtn.setEnabled(openThread and allowFit)
            
            self.restBackgroundBtn = QPushButton("Reset Background")
            self.restBackgroundBtn.clicked.connect(self.resetBackground)
            self.restBackgroundBtn.setDefault(False)
            self.restBackgroundBtn.setAutoDefault(False)
            self.restBackgroundBtn.setToolTip("Get a new screenshot of the viewport to use as a background image.")
            self.restBackgroundBtn.setEnabled(openThread)
            
            self.cloneLeftBtn = QPushButton("Left")
            self.cloneLeftBtn.clicked.connect(self.cloneLeft)
            self.cloneLeftBtn.setDefault(False)
            self.cloneLeftBtn.setAutoDefault(False)
            self.cloneLeftBtn.setToolTip("Create a copy of the current regions and place them to the left of the current regions.")
            
            self.cloneRightBtn = QPushButton("Right")
            self.cloneRightBtn.clicked.connect(self.cloneRight)
            self.cloneRightBtn.setDefault(False)
            self.cloneRightBtn.setAutoDefault(False)
            self.cloneRightBtn.setToolTip("Create a copy of the current regions and place them to the right of the current regions.")
            
            self.cloneUpBtn = QPushButton("Up")
            self.cloneUpBtn.clicked.connect(self.cloneUp)
            self.cloneUpBtn.setDefault(False)
            self.cloneUpBtn.setAutoDefault(False)
            self.cloneUpBtn.setToolTip("Create a copy of the current regions and place them above the current regions.")
            
            self.cloneDownBtn = QPushButton("Down")
            self.cloneDownBtn.clicked.connect(self.cloneDown)
            self.cloneDownBtn.setDefault(False)
            self.cloneDownBtn.setAutoDefault(False)
            self.cloneDownBtn.setToolTip("Create a copy of the current regions and place them below the current regions.")
            
            self.createGridBtn = QPushButton("Create From Grid")
            self.createGridBtn.clicked.connect(self.createGrid)
            self.createGridBtn.setDefault(False)
            self.createGridBtn.setAutoDefault(False)
            self.createGridBtn.setToolTip("Create Regions in a grid to cover the full scene.")
            
            self.xGridSpin = QSpinBox()
            self.xGridSpin.setRange(1,20)
            self.xGridSpin.setValue(1)
            self.xGridSpin.setToolTip("Number of tiles in X for creating in a grid.")
            
            self.yGridSpin = QSpinBox()
            self.yGridSpin.setRange(1,20)
            self.yGridSpin.setValue(1)
            self.yGridSpin.setToolTip("Number of tiles in Y for creating in a grid.")
            
            self.cleanSceneBtn = QPushButton("Clean")
            self.cleanSceneBtn.clicked.connect(self.cleanScene)
            self.cleanSceneBtn.setDefault(False)
            self.cleanSceneBtn.setAutoDefault(False)
            self.cleanSceneBtn.setToolTip("Remove all regions from the scene that are fully contained within another region.")
            
            self.saveRegionBtn = QPushButton("Save")
            self.saveRegionBtn.clicked.connect(self.saveRegions)
            self.saveRegionBtn.setDefault(False)
            self.saveRegionBtn.setAutoDefault(False)
            self.saveRegionBtn.setToolTip("Save the regions to the current frame of the scene.")
            self.saveRegionBtn.setEnabled(openThread)
            
            self.loadRegionBtn = QPushButton("Load")
            self.loadRegionBtn.clicked.connect(self.loadRegionsFromCamera)
            self.loadRegionBtn.setDefault(False)
            self.loadRegionBtn.setAutoDefault(False)
            self.loadRegionBtn.setToolTip("Load the regions from the current frame of the scene.")
            self.loadRegionBtn.setEnabled(openThread)
            
            self.fillRegionsBtn = QPushButton("Fill")
            self.fillRegionsBtn.clicked.connect(self.fillEmptyRegions)
            self.fillRegionsBtn.setDefault(False)
            self.fillRegionsBtn.setAutoDefault(False)
            self.fillRegionsBtn.setToolTip("Fill all empty parts of the scene with Regions.")
            
            self.fitPaddingSpin = QDoubleSpinBox()
            self.fitPaddingSpin.setRange(0,100)
            self.fitPaddingSpin.setValue(0)
            self.fitPaddingSpin.setToolTip("The amount of padding to be added to each region created with Fit Scene.")
            self.fitPaddingSpin.setEnabled(openThread and allowFit)
            
            self.fitModeCombo = QComboBox()
            self.fitModeCombo.addItem("Tight")
            self.fitModeCombo.addItem("Loose")
            self.fitModeCombo.setToolTip("How to fit the objects from the scene.  Tight: Vertex based uses minimum bounding box of vertex.  Loose: creates a 2d Bounding box from the bounding box of the object.")
            self.fitModeCombo.setEnabled(openThread and allowFit)
            
            xTileLayout = QHBoxLayout()
            xTileLayout.addWidget(QLabel("Tiles in X"))
            self.xTileSpin = QSpinBox()
            self.xTileSpin.setRange(1,10)
            self.xTileSpin.setValue(1)
            self.xTileSpin.valueChanged.connect(self.changeTilesInX)
            xTileLayout.addWidget(self.xTileSpin)
            self.xTileSpin.setToolTip("Number of tiles in X in the region. Each tile is rendered as a separate region.")
            
            yTileLayout = QHBoxLayout()
            yTileLayout.addWidget(QLabel("Tiles in Y"))
            self.yTileSpin = QSpinBox()
            self.yTileSpin.setRange(1,10)
            self.yTileSpin.setValue(1)
            self.yTileSpin.valueChanged.connect(self.changeTilesInY)
            yTileLayout.addWidget(self.yTileSpin)
            self.yTileSpin.setToolTip("Number of tiles in Y in the region. Each tile is rendered as a separate region.")
            
            xPosLayout = QHBoxLayout()
            xPosLayout.addWidget(QLabel("X Position"))
            self.xPosSpin = QSpinBox()
            self.xPosSpin.setRange(0,1)
            self.xPosSpin.setValue(0)
            self.xPosSpin.valueChanged.connect(self.changeXPos)
            xPosLayout.addWidget(self.xPosSpin)
            self.xPosSpin.setToolTip("Position of the region in X.")
            
            yPosLayout = QHBoxLayout()
            yPosLayout.addWidget(QLabel("Y Position"))
            self.yPosSpin = QSpinBox()
            self.yPosSpin.setRange(0,1)
            self.yPosSpin.setValue(0)
            self.yPosSpin.valueChanged.connect(self.changeYPos)
            yPosLayout.addWidget(self.yPosSpin)
            self.yPosSpin.setToolTip("Position of the region in Y.")
            
            widthLayout = QHBoxLayout()
            widthLayout.addWidget(QLabel("Width"))
            self.widthSpin = QSpinBox()
            self.widthSpin.setRange(minWidth,minWidth+1)
            self.widthSpin.setValue(minWidth)
            self.widthSpin.valueChanged.connect(self.changeWidth)
            widthLayout.addWidget(self.widthSpin)
            self.widthSpin.setToolTip("Width of the region.")
            
            heightLayout = QHBoxLayout()
            heightLayout.addWidget(QLabel("Height"))
            self.heightSpin = QSpinBox()
            self.heightSpin.setRange(minHeight,minHeight+1)
            self.heightSpin.setValue(minHeight)
            self.heightSpin.valueChanged.connect(self.changeHeight)
            heightLayout.addWidget(self.heightSpin)
            self.heightSpin.setToolTip("Height of the region.")
            
            self.undoBtn = QPushButton("Undo")
            self.undoBtn.clicked.connect(self.undo)
            self.undoBtn.setDefault(False)
            self.undoBtn.setAutoDefault(False)
            self.undoBtn.setToolTip("Undo the last Change.")
            
            self.redoBtn = QPushButton("Redo")
            self.redoBtn.clicked.connect(self.redo)
            self.redoBtn.setDefault(False)
            self.redoBtn.setAutoDefault(False)
            self.redoBtn.setToolTip("Redo the last undo.")
            
            self.zoomSlider = QSlider(Qt.Horizontal)
            self.zoomSlider.setRange(0,500)
            self.zoomSlider.setValue(100)
            self.zoomSlider.setToolTip("The amount of padding to be added to each region created with Fit Scene.")
            self.zoomSlider.valueChanged.connect(self.changeZoom)
            
            self.fitViewportButton = QPushButton("Fit Viewport")
            self.fitViewportButton.clicked.connect(self.fitViewport)
            self.fitViewportButton.setDefault(False)
            self.fitViewportButton.setAutoDefault(False)
            self.fitViewportButton.setToolTip("Zoom to see everything in the viewport.")
            
            self.keepFitBtn = QCheckBox("Keep Fit")
            self.keepFitBtn.setChecked(True)
            self.keepFitBtn.stateChanged.connect(self.keepFit)
            self.keepFitBtn.setToolTip("Zoom to see everything in the viewport, and force the viewport to not change.")

            self.resizeRegionBtn = QCheckBox("Resize Region on Image Resize")
            self.resizeRegionBtn.setChecked(True)
            self.resizeRegionBtn.setToolTip("Automatically resize the regions when the image is resized.")
            
            self.resetZoomButton = QPushButton("Reset Zoom")
            self.resetZoomButton.clicked.connect(self.resetViewport)
            self.resetZoomButton.setDefault(False)
            self.resetZoomButton.setAutoDefault(False)
            self.resetZoomButton.setToolTip("Reset the zoom within the viewport.")
            
            cloneLayout = QGridLayout()
            cloneLayout.setColumnStretch(0,1)
            cloneLayout.setColumnStretch(1,1)
            cloneLayout.setColumnStretch(2,1)
            cloneLayout.setColumnStretch(3,1)
            cloneLayout.setColumnStretch(4,1)
            cloneLayout.addWidget( QLabel("Clone:" ), 0, 0 )
            cloneLayout.addWidget( self.cloneLeftBtn, 0, 1 )
            cloneLayout.addWidget( self.cloneRightBtn, 0,2 )
            cloneLayout.addWidget( self.cloneUpBtn, 0, 3 )
            cloneLayout.addWidget( self.cloneDownBtn, 0,4 )
            
            #Setup the Layouts
            self.selectedRegionsBox = QGroupBox()
            self.selectedRegionsBox.setTitle("Selected Region Controls")
            selectedRegionLayout = QGridLayout()
            self.selectedRegionsBox.setLayout(selectedRegionLayout)
            
            selectedRegionLayout.addWidget(self.splitBtn, 0, 0,1,2)
            selectedRegionLayout.addWidget(self.mergeBtn, 0, 2,1,2)
            selectedRegionLayout.addWidget(self.deleteBtn, 0, 4,1,2)
            selectedRegionLayout.addWidget(self.lockBtn,1,0,1,3)
            selectedRegionLayout.addWidget(self.enableBtn,1,3,1,3)
            
            selectedRegionLayout.addLayout(xPosLayout, 2, 0,1,3)
            selectedRegionLayout.addLayout(yPosLayout, 2,3,1,3)
            selectedRegionLayout.addLayout(widthLayout, 3, 0,1,3)
            selectedRegionLayout.addLayout(heightLayout, 3, 3,1,3)
            selectedRegionLayout.addLayout(xTileLayout,4,0,1,3)
            selectedRegionLayout.addLayout(yTileLayout,4, 3,1,3)
            
            selectedRegionLayout.addLayout(cloneLayout,5, 0,1,6)
            
            controlsLayout = QGridLayout()
            controlsLayout.addWidget(self.addBtn, 0, 0,1,2)
            controlsLayout.addWidget(self.deleteAllBtn, 0, 2,1,2)
            controlsLayout.addWidget(self.restBackgroundBtn, 0,4,1,2)
            controlsLayout.addWidget(self.selectedRegionsBox,1,0,1,6)
            
            controlsLayout.addWidget(self.getSelectedBtn, 3, 0,1,2)
            modeLabel = QLabel("Mode")
            modeLabel.setEnabled(openThread and allowFit)
            controlsLayout.addWidget(modeLabel, 3,2)
            controlsLayout.addWidget(self.fitModeCombo, 3,3)
            paddingLabel = QLabel("Padding")
            paddingLabel.setEnabled(openThread and allowFit)
            controlsLayout.addWidget(paddingLabel, 3,4)
            controlsLayout.addWidget(self.fitPaddingSpin, 3,5)

            controlsLayout.addWidget(self.createGridBtn, 4, 0,1,2)
            controlsLayout.addWidget(QLabel("X"), 4,2)
            controlsLayout.addWidget(self.xGridSpin, 4,3)
            controlsLayout.addWidget(QLabel("Y"), 4,4)
            controlsLayout.addWidget(self.yGridSpin, 4,5)
            
            regionButtonsLayout = QGridLayout()
            regionButtonsLayout.setColumnStretch(0,1)
            regionButtonsLayout.setColumnStretch(1,1)
            regionButtonsLayout.setColumnStretch(2,1)
            regionButtonsLayout.setColumnStretch(3,1)
            regionButtonsLayout.setColumnStretch(4,1)
            regionsLabel = QLabel("Regions:")
            
            regionButtonsLayout.addWidget( regionsLabel, 0, 0 )
            regionButtonsLayout.addWidget(self.fillRegionsBtn, 0, 1)
            regionButtonsLayout.addWidget(self.cleanSceneBtn, 0, 2)
            regionButtonsLayout.addWidget(self.saveRegionBtn, 0, 3)
            regionButtonsLayout.addWidget(self.loadRegionBtn, 0, 4)
            
            buttonsLayout = QGridLayout()
            buttonsLayout.setColumnStretch(0,1)
            buttonsLayout.setColumnStretch(1,1)
            buttonsLayout.addWidget(self.undoBtn, 0, 0)
            buttonsLayout.addWidget(self.redoBtn, 0, 1)
            
            controlsLayout.addLayout(regionButtonsLayout, 5,0,1,6)
            controlsLayout.addLayout(buttonsLayout, 6,0,1,6)
            
            #setup the table
            self.box = QVBoxLayout()
            self.box.addLayout(controlsLayout)
            self.model = QStandardItemModel()
            self.model.setHorizontalHeaderLabels (["ID","X","Y","Width","Height","Tiles","Locked","Enabled"])
            self.table = QTableView()
            self.table.setModel(self.model)
            self.table.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.verticalHeader().hide()
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.selectionModel().selectionChanged.connect(self.tableSelectionChanged)
            self.box.addWidget(self.table)
            
            zoomLayout = QHBoxLayout()
            zoomLayout.addWidget(QLabel("Zoom"))
            zoomLayout.addWidget(self.zoomSlider)
            
            topLayout = QGridLayout()
            topLayout.addLayout(zoomLayout,0,0)
            topLayout.addWidget(self.resetZoomButton, 0, 1)
            topLayout.addWidget(self.fitViewportButton, 0, 2)
            topLayout.addWidget(self.keepFitBtn, 0, 3)
            topLayout.addWidget(self.resizeRegionBtn, 0, 4)
            
            menuBar = QMenuBar(self)
            
            fileMenu = menuBar.addMenu("File")
                        
            self.saveAction = QAction('&Save', self)
            self.saveAction.triggered.connect(self.saveRegions)
            self.saveAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_S))
            self.saveAction.setEnabled(openThread)
            
            self.loadAction = QAction('&Load', self)
            self.loadAction.triggered.connect(self.loadRegionsFromCamera)
            self.loadAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_O))
            self.loadAction.setEnabled(openThread)
            
            self.exitAction = QAction('&Exit', self)
            self.exitAction.triggered.connect(self.exitApplication)
            
            fileMenu.addAction(self.saveAction)
            fileMenu.addAction(self.loadAction)
            fileMenu.addSeparator()
            fileMenu.addAction(self.exitAction)
            
            editMenu = menuBar.addMenu("Edit")
            
            self.undoAction = QAction('&Undo', self)
            self.undoAction.triggered.connect( self.undo )
            self.undoAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Z))
            self.undoAction.setEnabled(False)
            
            self.redoAction = QAction('&Redo', self)
            self.redoAction.triggered.connect( self.redo )
            self.redoAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Y))
            self.redoAction.setEnabled(False)
            
            self.createAction = QAction('&Add New Region', self)
            self.createAction.triggered.connect( self.createRegion )
            self.createAction.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_A))
            
            self.deleteRegionsAction = QAction('&Delete Selected Regions', self)
            self.deleteRegionsAction.triggered.connect( self.deleteSelectedRegions )
            self.deleteRegionsAction.setShortcuts( [ QKeySequence(Qt.Key_Backspace), QKeySequence(Qt.Key_Delete) ] )
            
            self.deleteAllAction = QAction('&Delete All Regions', self)
            self.deleteAllAction.triggered.connect( self.deleteAllRegions )
            self.deleteAllAction.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_D))
            
            self.fillRegionsAction = QAction('&Fill Regions', self)
            self.fillRegionsAction.triggered.connect( self.fillEmptyRegions )
            self.fillRegionsAction.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_F))
            
            self.cleanRegionsAction = QAction('&Clean Regions', self)
            self.cleanRegionsAction.triggered.connect( self.cleanScene )
            self.cleanRegionsAction.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_C))
            
            self.splitRegionAction = QAction('&Split Selected Regions', self )
            self.splitRegionAction.triggered.connect( self.splitSelectedRegions )
            self.splitRegionAction.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_S))
            
            self.mergeRegionsAction = QAction('&Merge Selected Regions', self)
            self.mergeRegionsAction.triggered.connect( self.mergeSelectedRegions )
            self.mergeRegionsAction.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_M))
            
            self.cloneLeftAction = QAction('&Clone Regions Left', self)
            self.cloneLeftAction.triggered.connect( self.cloneLeft )
            self.cloneLeftAction.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_Left))
            
            self.cloneRightAction = QAction('&Clone Regions Right', self)
            self.cloneRightAction.triggered.connect( self.cloneRight )
            self.cloneRightAction.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_Right))
            
            self.cloneUpAction = QAction('&Clone Regions Up', self)
            self.cloneUpAction.triggered.connect( self.cloneUp )
            self.cloneUpAction.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_Up))
            
            self.cloneDownAction = QAction('&Clone Regions Down', self)
            self.cloneDownAction.triggered.connect( self.cloneDown )
            self.cloneDownAction.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_Down))
            
            self.moveSelectionUpAction = QAction('&Move Selection Up',self)
            self.moveSelectionUpAction.triggered.connect(self.moveSelectedUp)
            self.moveSelectionUpAction.setShortcut(QKeySequence(Qt.Key_Up))
            
            self.moveSelectionDownAction = QAction('&Move Selection Down',self)
            self.moveSelectionDownAction.triggered.connect(self.moveSelectedDown)
            self.moveSelectionDownAction.setShortcut(QKeySequence(Qt.Key_Down))
            
            self.moveSelectionLeftAction = QAction('&Move Selection Left',self)
            self.moveSelectionLeftAction.triggered.connect(self.moveSelectedLeft)
            self.moveSelectionLeftAction.setShortcut(QKeySequence(Qt.Key_Left))
            
            self.moveSelectionRightAction = QAction('&Move Selection Right',self)
            self.moveSelectionRightAction.triggered.connect(self.moveSelectedRight)
            self.moveSelectionRightAction.setShortcut(QKeySequence(Qt.Key_Right))
            
            self.increaseSelectionWidthAction = QAction('&Increase Width',self)
            self.increaseSelectionWidthAction.triggered.connect(self.increaseSelectionWidth)
            self.increaseSelectionWidthAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Right))
            
            self.decreaseSelectionWidthAction = QAction('&Decrease Width',self)
            self.decreaseSelectionWidthAction.triggered.connect(self.decreaseSelectionWidth)
            self.decreaseSelectionWidthAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Left))
            
            self.increaseSelectionHeightAction = QAction('&Increase Height',self)
            self.increaseSelectionHeightAction.triggered.connect(self.increaseSelectionHeight)
            self.increaseSelectionHeightAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Down))
            
            self.decreaseSelectionHeightAction = QAction('&Decrease Height',self)
            self.decreaseSelectionHeightAction.triggered.connect(self.decreaseSelectionHeight)
            self.decreaseSelectionHeightAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Up))
            
            editMenu.addAction(self.undoAction)
            editMenu.addAction(self.redoAction)
            editMenu.addSeparator()
            editMenu.addAction(self.createAction)
            editMenu.addAction(self.deleteRegionsAction)
            editMenu.addAction(self.splitRegionAction)
            editMenu.addAction(self.mergeRegionsAction)
            editMenu.addSeparator()
            editMenu.addAction(self.moveSelectionUpAction)
            editMenu.addAction(self.moveSelectionDownAction)
            editMenu.addAction(self.moveSelectionLeftAction)
            editMenu.addAction(self.moveSelectionRightAction)
            editMenu.addSeparator()
            editMenu.addAction(self.increaseSelectionWidthAction)
            editMenu.addAction(self.decreaseSelectionWidthAction)
            editMenu.addAction(self.increaseSelectionHeightAction)
            editMenu.addAction(self.decreaseSelectionHeightAction)
            editMenu.addSeparator()
            editMenu.addAction(self.cloneLeftAction)
            editMenu.addAction(self.cloneRightAction)
            editMenu.addAction(self.cloneUpAction)
            editMenu.addAction(self.cloneDownAction)
            editMenu.addSeparator()
            editMenu.addAction(self.deleteAllAction)
            editMenu.addAction(self.fillRegionsAction)
            editMenu.addAction(self.cleanRegionsAction)    
            
            viewMenu = menuBar.addMenu("View")
            
            self.resetBackgroundAction = QAction('&Reset Background',self)
            self.resetBackgroundAction.triggered.connect(self.resetBackground)
            self.resetBackgroundAction.setEnabled(openThread)
            self.resetBackgroundAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_B))
            self.resetZoomAction = QAction('&Reset Zoom', self)
            self.resetZoomAction.triggered.connect( self.resetViewport )
            self.resetZoomAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_R))
            self.fitViewportAction = QAction('&Fit Viewport', self)
            self.fitViewportAction.triggered.connect( self.fitViewport )
            self.fitViewportAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_F))
            
            viewMenu.addAction( self.resetBackgroundAction )
            viewMenu.addSeparator()
            viewMenu.addAction(self.resetZoomAction)
            viewMenu.addAction(self.fitViewportAction)
            
            selectionMenu = menuBar.addMenu("Selection")
            
            self.selectNextAction = QAction('&Select Next',self)
            self.selectNextAction.triggered.connect(self.selectNext)
            self.selectNextAction.setShortcut(QKeySequence(Qt.Key_Space))
            
            self.addNextAction = QAction('&Add Next',self)
            self.addNextAction.triggered.connect(self.addNextSelection)
            self.addNextAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Space))
                                    
            selectionMenu.addAction(self.selectNextAction)
            selectionMenu.addAction(self.addNextAction)
            
            mainLayout = QGridLayout()
            mainLayout.setMenuBar(menuBar)
            mainLayout.addLayout(topLayout,0,0)
            mainLayout.addWidget(self.viewport, 1,0)
            mainLayout.addLayout(self.box,0,1,2,1)
            
            mainLayout.setColumnStretch(0,1)
            
            self.setLayout(mainLayout)
            self.setWindowTitle("Jigsaw")
            #set everything up so that we do not duplicate code
            self.onSelectionChanged()
            self.keepFit()
            
            #setup the signals and slots
            self.viewport.updateModel.connect(self.updateRectSpinBoxes)
            self.viewport.updateModel.connect(self.rebuildModel)
            
            self.viewport.zoomUpdated.connect(self.updatedZoomSlider)
            
            try:
                jigsawIconFilename = RepositoryUtils.GetRepositoryFilePath( "plugins/DraftTileAssembler/DraftTileAssembler.ico", True)
                jigsawIcon = QIcon(jigsawIconFilename)
                
                self.setWindowIcon(jigsawIcon)
            except:
                pass
            
            #setup the thread that will communicate with the other programs
            self.jigThread = JigsawThread(name=JigsawThread)
            self.jigThread.outgoing = port
            self.jigThread.window = self
            self.jigThread.openIncomming = openThread
            self.jigThread.start()
            
            #setup a timer which will run any code that needs to be run in the main thread (anything to do with the scene)
            self.mainTimer = QTimer(self)
            self.mainTimer.timeout.connect(self.jigThread.updateUI)
            self.mainTimer.start(500)
            
        except:
            print(traceback.format_exc())
    
    def selectNext(self):
        model = self.table.model()
        rootIndex = self.table.rootIndex()
        if model.rowCount() >0:
            selectionModel = self.table.selectionModel()
            if len(selectionModel.selectedRows()) == model.rowCount():
                return
            newSelection = 0
            if len(selectionModel.selectedRows()) > 0:
                if selectionModel.isRowSelected(model.rowCount()-1, rootIndex):
                    while selectionModel.isRowSelected(newSelection, rootIndex):
                        newSelection += 1
                    
                else:
                    newSelection = model.rowCount()-2
                    while not selectionModel.isRowSelected(newSelection, rootIndex):
                        newSelection -= 1
                    newSelection +=1
            
            for item in self.scene.selectedItems():
                item.setSelected(False)
            
            searchIndex = int(self.model.item(newSelection).text())
            for item in self.scene.items():
                if item.id == searchIndex:
                    item.setSelected(True)
                    break
                    
    def addNextSelection(self):
        model = self.table.model()
        rootIndex = self.table.rootIndex()
        if model.rowCount() >0:
            selectionModel = self.table.selectionModel()
            if len(selectionModel.selectedRows()) == model.rowCount():
                return
            newSelection = 0
            if len(selectionModel.selectedRows()) > 0:
                if selectionModel.isRowSelected(model.rowCount()-1, rootIndex):
                    while selectionModel.isRowSelected(newSelection, rootIndex):
                        newSelection += 1
                    
                else:
                    newSelection = model.rowCount()-2
                    while not selectionModel.isRowSelected(newSelection, rootIndex):
                        newSelection -= 1
                    newSelection +=1
            
            searchIndex = int(self.model.item(newSelection).text())
            for item in self.scene.items():
                if item.id == searchIndex:
                    item.setSelected(True)
                    break
    
    #Update the associated regions Y position
    def moveSelectedUp(self):
        if len(self.scene.selectedItems()) > 0:
            for selectedItem in self.scene.selectedItems():
                
                combinedRect = selectedItem.combinedRect()
                val = combinedRect.y() - 1
                val = max(0,val)
                selectedItem.setPos(0,0)
                heightMod = val-combinedRect.y()
                #update the position
                combinedRect.setY(val)
                combinedRect.setHeight(combinedRect.height()+heightMod)
                selectedItem.setRect(combinedRect)
                selectedItem.calcPath()
                self.updateRectSpinBoxes()
                #If the selected item is in the table, then we want to just update those positions
                if len(self.table.selectedIndexes())==0:
                    self.rebuildModel()
                else:
                    selected = self.table.selectedIndexes()
                    
                    for index in selected:
                        if index.column() == 2:
                            if str(self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)) == str(selectedItem.id):
                                self.model.setData(index,QVariant(val))
                                break
            self.dirty = True
            self.addUndoPoint()
 
    #Update the associated regions Y position
    def moveSelectedDown(self):
        sceneRect = self.scene.sceneRect()
        if len(self.scene.selectedItems()) > 0:
            for selectedItem in self.scene.selectedItems():
                
                combinedRect = selectedItem.combinedRect()
                val = combinedRect.y() + 1
                val = min(sceneRect.height()-combinedRect.height(),val)
                selectedItem.setPos(0,0)
                heightMod = val-combinedRect.y()
                #update the position
                combinedRect.setY(val)
                combinedRect.setHeight(combinedRect.height()+heightMod)
                selectedItem.setRect(combinedRect)
                selectedItem.calcPath()
                self.updateRectSpinBoxes()
                #If the selected item is in the table, then we want to just update those positions
                if len(self.table.selectedIndexes())==0:
                    self.rebuildModel()
                else:
                    selected = self.table.selectedIndexes()
                    
                    for index in selected:
                        if index.column() == 2:
                            if str(self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)) == str(selectedItem.id):
                                self.model.setData(index,QVariant(val))
                                break
            self.dirty = True
            self.addUndoPoint()
    
    #Update the associated regions Y position
    def moveSelectedLeft(self):
        sceneRect = self.scene.sceneRect()
        if len(self.scene.selectedItems()) > 0:
            for selectedItem in self.scene.selectedItems():
                
                combinedRect = selectedItem.combinedRect()
                val = combinedRect.x() - 1
                val = max(0,val)
                selectedItem.setPos(0,0)
                widthMod = val-combinedRect.x()
                #update the position
                combinedRect.setX(val)
                combinedRect.setWidth(combinedRect.width()+widthMod)
                selectedItem.setRect(combinedRect)
                selectedItem.calcPath()
                self.updateRectSpinBoxes()
                #If the selected item is in the table, then we want to just update those positions
                if len(self.table.selectedIndexes())==0:
                    self.rebuildModel()
                else:
                    selected = self.table.selectedIndexes()
                    
                    for index in selected:
                        if index.column() == 1:
                            if str(self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)) == str(selectedItem.id):
                                self.model.setData(index,QVariant(val))
                                break
            self.dirty = True
            self.addUndoPoint()
            
    #Update the associated regions Y position
    def moveSelectedRight(self):
        sceneRect = self.scene.sceneRect()
        if len(self.scene.selectedItems()) > 0:
            for selectedItem in self.scene.selectedItems():
                
                combinedRect = selectedItem.combinedRect()
                val = combinedRect.x() + 1
                val = min(sceneRect.width()-combinedRect.width(),val)
                
                selectedItem.setPos(0,0)
                widthMod = val-combinedRect.x()
                #update the position
                combinedRect.setX(val)
                combinedRect.setWidth(combinedRect.width()+widthMod)
                selectedItem.setRect(combinedRect)
                selectedItem.calcPath()
                self.updateRectSpinBoxes()
                #If the selected item is in the table, then we want to just update those positions
                if len(self.table.selectedIndexes())==0:
                    self.rebuildModel()
                else:
                    selected = self.table.selectedIndexes()
                    
                    for index in selected:
                        if index.column() == 1:
                            if str(self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)) == str(selectedItem.id):
                                self.model.setData(index,QVariant(val))
                                break
            self.dirty = True
            self.addUndoPoint()
    
    #Update the associated regions Y position
    def increaseSelectionWidth(self):
        sceneRect = self.scene.sceneRect()
        if len(self.scene.selectedItems()) > 0:
            for selectedItem in self.scene.selectedItems():
                
                combinedRect = selectedItem.combinedRect()
                val = combinedRect.width() + 1
                val = min(sceneRect.width()-combinedRect.x(),val)
                
                selectedItem.setPos(0,0)
                #update the position
                combinedRect.setX(combinedRect.x())
                combinedRect.setWidth(val)
                selectedItem.setRect(combinedRect)
                selectedItem.calcPath()
                self.updateRectSpinBoxes()
                #If the selected item is in the table, then we want to just update those positions
                if len(self.table.selectedIndexes())==0:
                    self.rebuildModel()
                else:
                    selected = self.table.selectedIndexes()
                    
                    for index in selected:
                        if index.column() == 3:
                            if str(self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)) == str(selectedItem.id):
                                self.model.setData(index,QVariant(val))
                                break
            self.dirty = True
            self.addUndoPoint()
            
    #Update the associated regions Y position
    def decreaseSelectionWidth(self):
        sceneRect = self.scene.sceneRect()
        if len(self.scene.selectedItems()) > 0:
            for selectedItem in self.scene.selectedItems():
                
                combinedRect = selectedItem.combinedRect()
                val = combinedRect.width() - 1
                val = max( 0, val )
                
                selectedItem.setPos(0,0)
                #update the position
                combinedRect.setX(combinedRect.x())
                combinedRect.setWidth(val)
                selectedItem.setRect(combinedRect)
                selectedItem.calcPath()
                self.updateRectSpinBoxes()
                #If the selected item is in the table, then we want to just update those positions
                if len(self.table.selectedIndexes())==0:
                    self.rebuildModel()
                else:
                    selected = self.table.selectedIndexes()
                    
                    for index in selected:
                        if index.column() == 3:
                            if str(self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)) == str(selectedItem.id):
                                self.model.setData(index,QVariant(val))
                                break
            self.dirty = True
            self.addUndoPoint()
    
    #Update the associated regions Y position
    def increaseSelectionHeight(self):
        sceneRect = self.scene.sceneRect()
        if len(self.scene.selectedItems()) > 0:
            for selectedItem in self.scene.selectedItems():
                
                combinedRect = selectedItem.combinedRect()
                val = combinedRect.height() + 1
                val = min(sceneRect.height()-combinedRect.y(),val)
                
                selectedItem.setPos(0,0)
                #update the position
                combinedRect.setY(combinedRect.y())
                combinedRect.setHeight(val)
                selectedItem.setRect(combinedRect)
                selectedItem.calcPath()
                self.updateRectSpinBoxes()
                #If the selected item is in the table, then we want to just update those positions
                if len(self.table.selectedIndexes())==0:
                    self.rebuildModel()
                else:
                    selected = self.table.selectedIndexes()
                    
                    for index in selected:
                        if index.column() == 4:
                            if str(self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)) == str(selectedItem.id):
                                self.model.setData(index,QVariant(val))
                                break
            self.dirty = True
            self.addUndoPoint()
            
    #Update the associated regions Y position
    def decreaseSelectionHeight(self):
        sceneRect = self.scene.sceneRect()
        if len(self.scene.selectedItems()) > 0:
            for selectedItem in self.scene.selectedItems():
                
                combinedRect = selectedItem.combinedRect()
                val = combinedRect.height() - 1
                val = max( 0, val )
                
                selectedItem.setPos(0,0)
                #update the position
                combinedRect.setY(combinedRect.y())
                combinedRect.setHeight(val)
                selectedItem.setRect(combinedRect)
                selectedItem.calcPath()
                self.updateRectSpinBoxes()
                #If the selected item is in the table, then we want to just update those positions
                if len(self.table.selectedIndexes())==0:
                    self.rebuildModel()
                else:
                    selected = self.table.selectedIndexes()
                    
                    for index in selected:
                        if index.column() == 4:
                            if str(self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)) == str(selectedItem.id):
                                self.model.setData(index,QVariant(val))
                                break
            self.dirty = True
            self.addUndoPoint()
    
    def resizeEvent(self,e):
        super(JigsawForm, self).resizeEvent(e)
        if self.keepFitBtn.isChecked():
            self.fitViewport()
    
    def fitViewport(self):
        self.viewport.fitInView(self.viewport.sceneRect(),Qt.KeepAspectRatio);
        self.viewport.zoomUpdated.emit()
    
    def keepFit(self):
        self.resetZoomButton.setEnabled( not self.keepFitBtn.isChecked() )
        self.resetZoomAction.setEnabled( not self.keepFitBtn.isChecked() )
        self.fitViewportButton.setEnabled( not self.keepFitBtn.isChecked() )
        self.fitViewportAction.setEnabled( not self.keepFitBtn.isChecked() )
        self.zoomSlider.setEnabled( not self.keepFitBtn.isChecked() )
        self.viewport.enableWheel = not self.keepFitBtn.isChecked()
        if self.keepFitBtn.isChecked():
            self.fitViewport()
        
    def resetViewport(self):
        self.zoomSlider.setValue(100)
    
    def updatedZoomSlider(self):
        if not self.updatingZoom:
            self.updatingZoom = True
            zoom = self.viewport.transform().m11()
            self.zoomSlider.setValue(int(zoom*100+0.5))
            self.updatingZoom = False
            
    def changeZoom(self,zoom):
        if not self.updatingZoom:
            self.updatingZoom = True
            self.viewport.setZoom(zoom/100.0)
            self.updatingZoom = False
    
    #When items are selected in the table act as though they were selected in the view.
    def tableSelectionChanged(self):
        if not self.changingItemSelection:
            self.changingTable = True
            for item in self.scene.selectedItems():
                item.setSelected(False)
                
            for index in self.table.selectionModel().selectedRows():
                searchIndex = int(self.model.item(index.row()).text())
                for item in self.scene.items():
                    if item.id == searchIndex:
                        item.setSelected(True)
                        break
            self.changingTable = False
    
    #Lock/Unlock the selected Region
    def lockSelectedRegion(self, val):
        for selectedItem in self.scene.selectedItems():
            #get the selected item
            selectedItem.lock = bool(val)
        self.rebuildModel()    
    
    #Lock/Unlock the selected Region
    def enableSelectedRegion(self, val):
        for selectedItem in self.scene.selectedItems():
            #get the selected item
            selectedItem.enabled = bool(val)
            if selectedItem.enabled:
                selectedItem.setPen(QPen(QColor("WHITE")))
                self.selectedColor=QColor(0,255,0)
            else:
                selectedItem.setPen(QPen(QColor("Grey")))
                self.selectedColor=QColor(255,0,0)
        self.rebuildModel()    
    
    #Update the associated regions X position
    def changeXPos(self, val):
        if len(self.scene.selectedItems()) == 1:
            #get the selected item
            selectedItem = self.scene.selectedItems()[0]
            if selectedItem.lock:
                return
            combinedRect = selectedItem.combinedRect()
            selectedItem.setPos(0,0)
            widthMod = val-combinedRect.x()
            #update the position
            combinedRect.setX(val)
            combinedRect.setWidth(combinedRect.width()+widthMod)
            selectedItem.setRect(combinedRect)
            selectedItem.calcPath()
            self.updateRectSpinBoxes()
            #If the selected item is in the table, then we want to just update those positions
            # print len(self.table.selectedIndexes())
            if len(self.table.selectedIndexes())==0:
                self.rebuildModel()
            else:
                selected = self.table.selectedIndexes()
                index = selected[1]
                self.model.setData(index,QVariant(val))

            self.dirty = True
            self.addUndoPoint()
    
    #Update the associated regions Y position
    def changeYPos(self, val):
        if len(self.scene.selectedItems()) == 1:
            #get the selected item
            selectedItem = self.scene.selectedItems()[0]
            combinedRect = selectedItem.combinedRect()
            selectedItem.setPos(0,0)
            heightMod = val-combinedRect.y()
            #update the position
            combinedRect.setY(val)
            combinedRect.setHeight(combinedRect.height()+heightMod)
            selectedItem.setRect(combinedRect)
            selectedItem.calcPath()
            self.updateRectSpinBoxes()
            #If the selected item is in the table, then we want to just update those positions
            if len(self.table.selectedIndexes())==0:
                self.rebuildModel()
            else:
                selected = self.table.selectedIndexes()
                index = selected[2]
                self.model.setData(index,QVariant(val))
            self.dirty = True
            self.addUndoPoint()
    
    #Update the associated regions width
    def changeWidth(self, val):
        if len(self.scene.selectedItems()) == 1:
            selectedItem = self.scene.selectedItems()[0]
            rect = selectedItem.rect()
            rect.setWidth(val)
            selectedItem.setRect(rect)
            selectedItem.calcPath()
            self.updateRectSpinBoxes()
            #If the selected item is in the table, then we want to just update those positions
            if len(self.table.selectedIndexes())==0:
                self.rebuildModel()
            else:
                selected = self.table.selectedIndexes()
                index = selected[3]
                self.model.setData(index,QVariant(val))
            self.dirty = True
            self.addUndoPoint()
    
    #Update the associated regions height
    def changeHeight(self, val):
        if len(self.scene.selectedItems()) == 1:
            selectedItem = self.scene.selectedItems()[0]
            rect = selectedItem.rect()
            rect.setHeight(val)
            selectedItem.setRect(rect)
            selectedItem.calcPath()
            self.updateRectSpinBoxes()
            #If the selected item is in the table, then we want to just update those positions
            if len(self.table.selectedIndexes())==0:
                self.rebuildModel()
            else:
                selected = self.table.selectedIndexes()
                index = selected[4]
                self.model.setData(index,QVariant(val))
            self.dirty = True
            self.addUndoPoint()
    
    #when the selection is changed we need to make sure the appropriate items are enabled
    def onSelectionChanged(self):
        numSelected = len(self.scene.selectedItems())
        selected = numSelected >0
        multipleSelected = numSelected > 1
        self.mergeBtn.setEnabled(multipleSelected)
        self.mergeRegionsAction.setEnabled(multipleSelected)
        
        modifiable = selected and not multipleSelected
        
        if modifiable:
            modifiable = not self.scene.selectedItems()[0].lock
        
        self.xPosSpin.setEnabled(modifiable)
        self.yPosSpin.setEnabled(modifiable)
        self.widthSpin.setEnabled(modifiable)
        self.heightSpin.setEnabled(modifiable)
        
        self.selectedRegionsBox.setEnabled(selected)
        self.splitRegionAction.setEnabled(selected)
        self.deleteRegionsAction.setEnabled(selected)
        
        self.moveSelectionUpAction.setEnabled(selected)
        self.moveSelectionDownAction.setEnabled(selected)
        self.moveSelectionLeftAction.setEnabled(selected)
        self.moveSelectionRightAction.setEnabled(selected)
        
        self.increaseSelectionWidthAction.setEnabled(selected)
        self.decreaseSelectionWidthAction.setEnabled(selected)
        self.increaseSelectionHeightAction.setEnabled(selected)
        self.decreaseSelectionHeightAction.setEnabled(selected)
        
        self.cloneLeftBtn.setEnabled(selected)
        self.cloneLeftAction.setEnabled(selected)
        self.cloneRightBtn.setEnabled(selected)
        self.cloneRightAction.setEnabled(selected)
        self.cloneUpBtn.setEnabled(selected)
        self.cloneUpAction.setEnabled(selected)
        self.cloneDownBtn.setEnabled(selected)
        self.cloneDownAction.setEnabled(selected)
        self.lockBtn.setEnabled(selected)
        
        #if something is selected update the spin boxes
        if selected:
            self.xTileSpin.blockSignals(True)
            self.yTileSpin.blockSignals(True)
            self.lockBtn.blockSignals(True)
            self.enableBtn.blockSignals(True)
            if multipleSelected:
                self.xTileSpin.setValue(1)
                self.yTileSpin.setValue(1)
            else:
                selectedItem = self.scene.selectedItems()[0]
                selectedRect = selectedItem.combinedRect()
                sceneRect = self.scene.sceneRect()
                self.xTileSpin.setValue(selectedItem.xTiles)
                self.yTileSpin.setValue(selectedItem.yTiles)
                self.lockBtn.setChecked(selectedItem.lock)
                self.updateRectSpinBoxes()
            
            self.enableBtn.setChecked(self.scene.selectedItems()[0].enabled)
            
            self.xTileSpin.blockSignals(False)
            self.yTileSpin.blockSignals(False)
            self.lockBtn.blockSignals(False)
            self.enableBtn.blockSignals(False)
        if not self.changingTable:
            self.changingItemSelection = True

            selectionModel = self.table.selectionModel()
            model = self.table.model()
            selectionModel.clearSelection()
            selectedItems = selectionModel.selection()
            
            for item in self.scene.selectedItems():
                for row in range(0,model.rowCount()):
                    if str(model.data(model.index(row, 0), Qt.DisplayRole)) ==  str(item.id): 
                        self.table.selectRow(row)
                        selectedItems.merge(selectionModel.selection(), QItemSelectionModel.Select)
            
            selectionModel.clearSelection()
            selectionModel.select(selectedItems, QItemSelectionModel.Select)
            self.changingItemSelection = False
    
    #Update the spin boxes 
    def updateRectSpinBoxes(self):
        if not len(self.scene.selectedItems()) == 1:
            return
        self.xPosSpin.blockSignals(True)
        self.yPosSpin.blockSignals(True)
        self.widthSpin.blockSignals(True)
        self.heightSpin.blockSignals(True)
        self.xTileSpin.blockSignals(True)
        self.yTileSpin.blockSignals(True)
        selectedItem = self.scene.selectedItems()[0]
        selectedRect = selectedItem.combinedRect()
        sceneRect = self.scene.sceneRect()
        
        self.xPosSpin.setRange(0,sceneRect.width()-selectedRect.width())
        self.xPosSpin.setValue(selectedRect.x())
        self.yPosSpin.setRange(0,sceneRect.height()-selectedRect.height())
        self.yPosSpin.setValue(selectedRect.y())
        self.widthSpin.setRange(self.minWidth,sceneRect.width()-selectedRect.x())
        self.widthSpin.setValue(selectedRect.width())
        self.heightSpin.setRange(self.minHeight,sceneRect.height()-selectedRect.y())
        self.heightSpin.setValue(selectedRect.height())
        
        maxXTiles = int(selectedRect.width()/max(1,self.minWidth))
        maxXTiles = max(1,maxXTiles)
        maxYTiles = int(selectedRect.height()/max(1,self.minHeight))
        maxYTiles = max(1,maxYTiles)
        self.xTileSpin.setRange(1,maxXTiles)
        self.yTileSpin.setRange(1,maxYTiles)
        
        if selectedItem.xTiles > maxXTiles:
            selectedItem.xTiles = maxXTiles
            self.xTileSpin.setValue(maxXTiles)
            self.calcPath()
            
        if selectedItem.yTiles > maxYTiles:
            selectedItem.yTiles = maxYTiles
            self.yTileSpin.setValue(maxYTiles)
            self.calcPath()
        
        self.xPosSpin.blockSignals(False)
        self.yPosSpin.blockSignals(False)
        self.widthSpin.blockSignals(False)
        self.heightSpin.blockSignals(False)
        self.xTileSpin.blockSignals(False)
        self.yTileSpin.blockSignals(False)
        
    #rebuild the model for the Table
    def rebuildModel(self):
        try:
            changingItemSelection = True
            changingTable = True
            
            selectedregions = self.scene.selectedItems()
            
            selectionModel = self.table.selectionModel()
            model = self.table.model()
            selectedItems = selectionModel.selection()
            selectionModel.clearSelection()
            newItems = selectionModel.selection()
            
            self.model.removeRows(0,self.model.rowCount())
            items = self.scene.items()
            for item in items:
                self.addToModel(item)
            self.model.sort(0)
            fontMet = QFontMetrics(self.table.font())
            for i in range(0,self.model.rowCount()):
                self.table.setRowHeight(i,fontMet.height())
            for item in selectedregions:
                for row in range(0,model.rowCount()):
                    if str(model.data(model.index(row, 0), Qt.DisplayRole)) ==  str(item.id): 
                        self.table.selectRow(row)
                        newItems.merge(selectionModel.selection(), QItemSelectionModel.Select)
            selectionModel.clearSelection()
            selectionModel.select(newItems, QItemSelectionModel.Select)
            
            changingItemSelection = False
            changingTable = False
        except:
            print(traceback.format_exc())
    
    #add each property to the model
    def addToModel(self,item):
        rect= item.combinedRect()
        idItem = IntItem() #the Id is a custom type of item so that they can be sorted properly
        idItem.setText(str(item.id))
        xItem = QStandardItem()
        xItem.setText(str(int(rect.x())))
        yItem = QStandardItem()
        yItem.setText(str(int(rect.y())))
        widthItem = QStandardItem()
        widthItem.setText(str(int(rect.width())))
        heightItem = QStandardItem()
        heightItem.setText(str(int(rect.height())))
        tilesItem = QStandardItem()
        tilesItem.setText(str(item.xTiles)+"X"+str(item.yTiles))
        lockItem = QStandardItem()
        lockItem.setText(str(item.lock))
        enableItem = QStandardItem()
        enableItem.setText(str(item.enabled))
        
        list = [idItem, xItem,yItem,widthItem,heightItem, tilesItem, lockItem, enableItem ]
        
        self.model.appendRow(list)
        fontMet = QFontMetrics(self.table.font())
        self.table.setRowHeight(self.model.rowCount()-1,fontMet.height())
    
    #Setup a point at which you can undo to
    def addUndoPoint(self):
        self.undoBtn.setEnabled(False)
        self.undoAction.setEnabled(False)
        if self.currSetup is not None:
            self.undoBtn.setEnabled(True)
            self.undoAction.setEnabled(True)
            self.undoList.append(self.currSetup)
        self.redoList = []
        self.currSetup = self.jigThread.getRegions(False)
        self.redoBtn.setEnabled(False)
        self.redoAction.setEnabled(False)
    
    #undo by destroying all active regions then rebuilding them using the last stored value
    def undo(self):
        if len(self.undoList) ==0:
            return
            
        self.redoList.append(self.currSetup)
        self.currSetup = self.undoList.pop()
        
        for item in self.scene.items():
            self.scene.removeItem(item)
        
        if self.currSetup is not None:
            selectors = self.currSetup.split(";")
            
            for selector in selectors:
                coordinates = selector.split(",")
                if len(coordinates)>3:
                    region = self.addRegion(int(coordinates[0]),int(coordinates[1]),int(coordinates[2]),int(coordinates[3]))
                    if len(coordinates) > 5:
                        region.xTiles = int(coordinates[4])
                        region.yTiles = int(coordinates[5])
                        if len(coordinates) > 6:
                            region.enabled = to_bool(coordinates[6])
                self.dirty=True
        self.rebuildModel()
        self.undoBtn.setEnabled(len(self.undoList))
        self.undoAction.setEnabled(len(self.undoList))
        self.redoBtn.setEnabled(True)
        self.redoAction.setEnabled(True)
    
    #redo the last undo    
    def redo(self):
        if len(self.redoList) ==0:
            return
        self.undoList.append(self.currSetup)
        self.currSetup = self.redoList.pop()
        for item in self.scene.items():
            self.scene.removeItem(item)
        if self.currSetup is not None:
            selectors = self.currSetup.split(";")
            for selector in selectors:
                coordinates = selector.split(",")
                if len(coordinates)>3:
                    region = self.addRegion(int(coordinates[0]),int(coordinates[1]),int(coordinates[2]),int(coordinates[3]))
                    if len(coordinates) > 5:
                        region.xTiles = int(coordinates[4])
                        region.yTiles = int(coordinates[5])
                        if len(coordinates) > 6:
                            region.enabled = to_bool(coordinates[6])
                self.dirty=True
        self.rebuildModel()
        self.undoBtn.setEnabled(True)
        self.undoAction.setEnabled(True)
        self.redoBtn.setEnabled(len(self.redoList))
        self.redoAction.setEnabled(len(self.redoList))
    
    #add a new region to the view and create an undo point
    def createRegion(self):
        self.addRegion()
        self.dirty = True
        self.addUndoPoint()
        self.rebuildModel()
    
    #add a new region to the view
    def addRegion(self, x=0,y=0,width=50,height=50, addToModel = True):
        newX = max(0,x)
        width -=(newX-x)
        newY = max(0,y)
        height-=(newY-y)
        width = min(width, self.scene.sceneRect().width()-newX)
        height = min(height, self.scene.sceneRect().height()-newY)
        
         #find the lowest open id value and set the region to that val
        ids = []
        for item in self.scene.items():
            ids.append(item.id)
        ids.sort()
        id = 1
        while id < len(ids)+1:
            if ids[id-1] > id:
                break
            id+=1
        
        rectItem = JigsawRegion(newX,newY,width,height, id, self.minWidth, self.minHeight)
        
        self.scene.addItem(rectItem)
        self.addToModel(rectItem)
        return rectItem
    
    #delete all regions from the scene
    def deleteAllRegions(self):
        for item in self.scene.items():
            self.scene.removeItem(item)
        self.rebuildModel()
        self.dirty = True
        self.addUndoPoint()
    
    #delete all of the selected Regions
    def deleteSelectedRegions(self):
        for item in self.scene.selectedItems():
            self.scene.removeItem(item)
        self.rebuildModel()
        self.dirty = True
        self.addUndoPoint()
    
    #Clone the selected regions to the left    
    def cloneLeft(self):
        selected = self.scene.selectedItems()
        if len(selected)>0:
            for item in selected:
                area = item.combinedRect()
                clone = self.addRegion(area.x()-area.width(),area.y(),area.width(),area.height())
                clone.xTiles = item.xTiles
                clone.yTiles = item.yTiles
                item.setSelected(False)
                clone.setSelected(True)
            self.dirty = True
            self.addUndoPoint()
            
    #Clone the selected regions to the Right            
    def cloneRight(self):
        selected = self.scene.selectedItems()
        if len(selected)>0:
            for item in selected:
                area = item.combinedRect()
                clone = self.addRegion(area.x()+area.width(),area.y(),area.width(),area.height())
                clone.xTiles = item.xTiles
                clone.yTiles = item.yTiles
                item.setSelected(False)
                clone.setSelected(True)
            self.dirty = True
            self.addUndoPoint()
    
    #Clone the selected regions to the up
    def cloneUp(self):
        selected = self.scene.selectedItems()
        if len(selected)>0:
            for item in selected:
                area = item.combinedRect()
                clone = self.addRegion(area.x(),area.y()-area.height(),area.width(),area.height())
                clone.xTiles = item.xTiles
                clone.yTiles = item.yTiles
                item.setSelected(False)
                clone.setSelected(True)
            self.dirty = True
            self.addUndoPoint()
    
    #Clone the selected regions to the down
    def cloneDown(self):
        selected = self.scene.selectedItems()
        if len(selected)>0:
            for item in selected:
                area = item.combinedRect()
                clone = self.addRegion(area.x(),area.y()+area.height(),area.width(),area.height())
                clone.xTiles = item.xTiles
                clone.yTiles = item.yTiles
                item.setSelected(False)
                clone.setSelected(True)
            self.dirty = True
            self.addUndoPoint()
    
    #Create regions to cover the full scene in a grid patternz
    def createGrid(self):
        width = self.scene.sceneRect().width()
        height = self.scene.sceneRect().height()
        
        numX = self.xGridSpin.value()
        numy = self.yGridSpin.value()
        regionWidth = width/numX
        regionHeight = height/numy
        for i in xrange(0,numX):
            for j in xrange(0,numy):
                self.addRegion(i*regionWidth,j*regionHeight,regionWidth,regionHeight)
        self.dirty = True
        self.addUndoPoint()
    
    #merge the selected regions into a single larger region
    def mergeSelectedRegions(self):
        if len(self.scene.selectedItems())>0:
            mergeArea = None
            for item in self.scene.selectedItems():
                area = item.combinedRect()
                if not mergeArea:
                    mergeArea = area
                else:
                    mergeArea = mergeArea.united(area)
                self.scene.removeItem(item)
            newRegion = self.addRegion(mergeArea.x(),mergeArea.y(),mergeArea.width(),mergeArea.height())
            newRegion.setSelected(True)
            self.rebuildModel()
            self.dirty = True
            self.addUndoPoint()
    
    #Split the selected region into smaller regions based on the tiles for that region
    def splitSelectedRegions(self):
        if len(self.scene.selectedItems())>0:
            for item in self.scene.selectedItems():
                
                xStep = item.rect().width()/item.xTiles                
                yStep = item.rect().height()/item.yTiles
                area = item.combinedRect()
                for x in range(0,item.xTiles):
                    for y in range(0,item.yTiles):
                        self.addRegion(int(area.x()+x*xStep+0.5),int(area.y()+y*yStep+0.5),int(xStep+0.5),int(yStep+0.5))
                self.scene.removeItem(item)
            self.rebuildModel()
            self.dirty = True
            self.addUndoPoint()
    
    #fit the bounding boxes of the items from within the original scene
    def getSelectedRegion(self):
        mode = self.fitModeCombo.currentText()
        padding = self.fitPaddingSpin.value()
        self.jigThread.getSelected(mode,padding)
    
    #Modify the number of tiles in X in the region
    def changeTilesInX(self,val):
        for item in self.scene.selectedItems():
            item.xTiles=val
            item.update()
            
        if len(self.table.selectedIndexes())==0:
            self.rebuildModel()
        else:
            selected = self.table.selectedIndexes()
            index = selected[5]
            self.model.setData(index,QVariant(str(val)+"X"+str(self.yTileSpin.value())))
        self.dirty = True
        self.addUndoPoint()
    
    #Modify the number of tiles in Y in the region
    def changeTilesInY(self,val):
        for item in self.scene.selectedItems():
            item.yTiles=val
            item.update()
        if len(self.table.selectedIndexes())==0:
            self.rebuildModel()
        else:
            selected = self.table.selectedIndexes()
            index = selected[5]
            self.model.setData(index,QVariant(str(self.xTileSpin.value())+"X"+str(val)))
        self.dirty = True
        self.addUndoPoint()
    
    #Query if you should save when the form is closed
    def closeEvent(self, e):
        try:
            if self.dirty and self.jigThread.openIncomming and not (SystemUtils.IsRunningOnMac() and self.quitting ):
                reply = QMessageBox.question(self, 'Message', "Would you like to save your regions?")
                if reply == QMessageBox.Yes:
                    self.saveRegions()
            self.jigThread.exit()
            super(JigsawForm, self).closeEvent(e)
        except:
            print(traceback.format_exc())
    
    #get the jigsaw thread to get a screenshot
    def resetBackground(self):
        self.jigThread.getScreenshot()
    
    #get the jigsaw thread to get the program to send its saved regions
    def loadRegionsFromCamera(self):
        self.jigThread.loadRegionsFromCamera()
        
    #get the JigsawThread to save the regions, and set it to not be dirty
    def saveRegions(self):
        self.jigThread.saveRegions()
        self.dirty = False
    
    def exitApplication(self):
        self.quitting = True
        self.close()
        
    #Go through each region and remove all regions that are fully contained within that region
    def cleanScene(self):
        count = 0
        regionList = self.scene.items()
        regionList.reverse()
        for curRegion in regionList:
            intersectedItems = self.scene.items(curRegion.combinedRect(), mode=Qt.IntersectsItemBoundingRect)
            if curRegion.scene() is None:
                continue
            for intersected in intersectedItems:
                if intersected is not curRegion:
                    if curRegion.combinedRect().contains(intersected.combinedRect()):
                        self.scene.removeItem(intersected)
                        count+=1
        self.rebuildModel()   
        self.jigThread.getRegions()
        self.dirty = True
        self.addUndoPoint()
        
    #Take a region that is the size of the full scene and subtract all regions from that one then get the rectangles from each one and add those to the scene
    def fillEmptyRegions(self):
        width = self.scene.sceneRect().width()
        height = self.scene.sceneRect().height()
        mainRegion = QRegion(0,0,width,height)
        for item in self.scene.items():
            rect = item.combinedRect()
            region = QRegion(rect.x(),rect.y(),rect.width(),rect.height())
            mainRegion = mainRegion.subtracted(region)
        endRects = mainRegion.rects()
        for rect in endRects:
            self.addRegion(rect.x(),rect.y(),rect.width(),rect.height())
        self.dirty = True
        self.addUndoPoint()
                
#A custom version of the QStandard item which holds ints so they can be sorted properly                
class IntItem(QStandardItem):
    def __init__(self):
        super(IntItem, self).__init__()
    
    def __lt__(self, otherItem):
        return int(self.text())<int(otherItem.text())

#A custom version of the QGraphicsView, which will properly draw the background and set the scene rect   
class JigsawView(QGraphicsView):        
    backgroundImage = None
    updateModel = pyqtSignal()
    zoomUpdated = pyqtSignal()
    panning = False
    cursorPanCurr = None
    enableWheel = True

    def __init__(self, scene, background=None):
        super(JigsawView, self).__init__(scene)
        self.backgroundImage=background
        r = QRectF(0,0,self.backgroundImage.width(),self.backgroundImage.height())
        self.previousWidth = self.backgroundImage.width()
        self.previousHeight = self.backgroundImage.height()
        self.scene().setSceneRect(r)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setCacheMode(QGraphicsView.CacheNone)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse);
        
    def drawBackground(self, painter, rect):
        try:
            r = QRectF()
            r.setRect(0,0,self.backgroundImage.width(),self.backgroundImage.height())
            painter.drawImage(r,self.backgroundImage)
            painter.setPen(QPen(QColor(0,0,255)))
            painter.drawRect(r)
        except:
            print(traceback.format_exc())
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.updateModel.emit()
            super(JigsawView, self).mouseReleaseEvent(event)
        elif event.button() == Qt.MiddleButton:
            self.panning = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.panning = True
            self.cursorPanCurr = event.pos()
        else:
            super(JigsawView, self).mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.panning:
            self.horizontalScrollBar().setValue( self.horizontalScrollBar().value() - event.pos().x() + self.cursorPanCurr.x() )
            self.verticalScrollBar().setValue( self.verticalScrollBar().value() - event.pos().y() + self.cursorPanCurr.y())
            self.cursorPanCurr = event.pos()
        else:    
            super(JigsawView, self).mouseMoveEvent(event)
            
    def wheelEvent(self, event):
        if self.enableWheel:
            scaleFactor = pow( 2.0,(event.angleDelta().y()/480.0) )
            self.scaleView(scaleFactor)
    
    def setZoom(self,zoom):
        scaleFactor = zoom/self.transform().m11();
        self.scaleView(scaleFactor);
    
    def scaleView(self, scaleFactor):
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0,0,1,1)).width()
        
        if factor > 5 or factor < 0.01:
            return
            
        self.scale(scaleFactor,scaleFactor)
        
        self.zoomUpdated.emit()
        
#The thread that is used to communicate to the 3d application   
class JigsawThread(threading.Thread):
    outgoing = 0
    incoming = 0
    sockIn = None
    sockOut = None
    window = None
    conn = None
    needsUpdate = False
    updateString = None
    updateDeleteFirst = False
    failedRefresh = False
    imageFile = None
    openIncomming = True
    previousWidth = 0
    previousHeight = 0
    
    #Main function of the thread
    def run(self):
        if self.openIncomming:
            HOSToutgoing = 'localhost'
            PORToutgoing = self.outgoing              # The same port as used by the server
            self.sockOut = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sockOut.connect((HOSToutgoing, PORToutgoing))
            #connect to the 3d applications server socket
        HOSTincoming = ''                 # Symbolic name meaning all available interfaces
        PORTincoming = 0
        if self.openIncomming:
            PORTincoming = self.get_open_port()              # Arbitrary non-privileged port
            self.incoming = PORTincoming
        else:
            PORTincoming = self.outgoing
            self.incoming = self.outgoing
        self.sockIn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.sockIn.bind((HOSTincoming, PORTincoming))
        self.sockIn.listen(1)
        #create own server
        if self.openIncomming:
            self.sockOut.sendall(str(PORTincoming)+"\n")
        self.conn, addr = self.sockIn.accept()
        
        if self.openIncomming:
            self.loadRegionsFromCamera()
        while 1:
            data = recvData(self.conn)
            
            if not data:
                break
            command = str(data).split("=")
            
            if command[0].lower() == "exit":
                self.window.quitting = True
                self.window.close()
                break
            elif command[0].lower() == "screenshot":
                if len(command)>1:
                    self.imageFile = command[1]
                    #QMessageBox.information(None,"Screenshot", "Got Screenshot: "+self.imageFile)
                    reader = QImageReader(self.imageFile)
                    image = None
                    if reader.canRead():
                        image = reader.read()
                    else:
                        try:
                            import Draft
                        except:
                            QMessageBox.information(None,"Error", "Failed to import Draft")

                        img = Draft.Image.ReadFromFile(str(self.imageFile))
                        newName = os.path.splitext(self.imageFile)[0]+".png"
                        img.WriteToFile(str(newName))
                        reader = QImageReader(newName)
                        image = reader.read()

                    self.previousWidth = self.window.viewport.backgroundImage.width()
                    self.previousHeight = self.window.viewport.backgroundImage.height()
                    self.window.viewport.backgroundImage = image
                    self.window.viewport.resetCachedContent()
                    r = QRectF(0,0,image.width(),image.height())
                    self.window.scene.setSceneRect(r)

                    if self.window.resizeRegionBtn.isChecked() and ((image.width() != self.previousWidth) or (image.height() != self.previousHeight)):
                        

                        widthRatio = image.width() / float(self.previousWidth)
                        heightRatio = image.height() / float(self.previousHeight)

                        regionList = self.window.scene.items()
                        regionList.reverse()

                        for region in regionList:
                            area = region.combinedRect()

                            normalizedCenterX = area.center().x() / self.previousWidth
                            normalizedCenterY = area.center().y() / self.previousHeight

                            area.setWidth(area.width() * widthRatio)
                            area.setHeight(area.height() * heightRatio)

                            area.moveCenter(QPointF(normalizedCenterX * image.width(), normalizedCenterY * image.height()))

                            left = area.x()
                            top = area.y()
                            width = area.width()
                            height = area.height()
                            xTiles = region.xTiles
                            yTiles = region.yTiles
                            enabled = region.enabled

                            if not self.updateString == "":
                                self.updateString += ";"
                            self.updateString += "%i,%i,%i,%i,%i,%i,%r" % (left, top, width, height, xTiles, yTiles, enabled)
                        self.updateDeleteFirst = True
                        self.needsUpdate = True
                        
                    self.window.viewport.update()
                    if SystemUtils.IsRunningOnMac() or SystemUtils.IsRunningOnLinux():
                        self.window.raise_()
                else:
                    self.failedRefresh = True
            elif command[0].lower()=="create":
                if len(command)>1:
                    self.needsUpdate = True
                    self.updateString = command[1]
            elif command[0].lower() == "getrenderregions":
                regionString = self.getRegions()
                self.conn.send("renderregion="+regionString+"\n")
            elif command[0].lower() == "saveregions":
                regionString = self.getRegions(False)
                self.conn.send("saveregions="+regionString+"\n")
            elif command[0].lower() == "loadregions": 
                if len(command)>1:
                    self.updateDeleteFirst = True
                    self.updateString = command[1]
                    self.needsUpdate = True
                    self.dirty = False
        if self.openIncomming:
            self.sockOut.sendall("exit\n")
        
        self.conn.close()
    
    #Update the UI, this is called by the timer since it cannot be called by the thread without causing errors
    def updateUI(self):
        if self.needsUpdate:
            self.needsUpdate = False

            newString = self.updateString
            self.updateString = ""
            if self.updateDeleteFirst:
                self.updateDeleteFirst = False
                for item in self.window.scene.items():
                    self.window.scene.removeItem(item)
            if newString is not None:
                selectors = newString.split(";")
                for selector in selectors:
                    coordinates = selector.split(",")
                    if len(coordinates)>3:
                        region = self.window.addRegion(int(coordinates[0]),int(coordinates[1]),int(coordinates[2]),int(coordinates[3]))
                        if len(coordinates) > 5:
                            region.xTiles = int(coordinates[4])
                            region.yTiles = int(coordinates[5])
                            self.window.dirty=False
                            if len(coordinates) > 6:
                                region.enabled = to_bool(coordinates[6])
            self.window.rebuildModel()
            self.window.addUndoPoint()
        #if it failed to refresh let the user know
        if self.failedRefresh:
            self.failedRefresh = False
            QMessageBox.information(self.window,"Unable to Refresh", "Unable to get new background image.")
    
    #gather up the the all of the regions and send them to the 3d application to save
    def saveRegions(self):
        regionString = self.getRegions(False)
        self.sockOut.sendall("saveregions="+regionString+"\n")
    
    #Let the 3d application know that we want a new background
    def getScreenshot(self):
        self.sockOut.sendall("getScreenshot\n")
    
    #Find an open port so that we can use it later on
    def get_open_port(self):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        port = s.getsockname()[1]
        s.close()
        return port    
    
    #When we are going to exit let the application no we are exiting and then close the input connection
    def exit(self):
        self.sockOut.sendall("exit\n")
        self.conn.close()
    
    #Let the application know that we want to get the bounding boxes of the regions
    def getSelected(self, mode, padding):
        self.sockOut.sendall('getselected='+mode+';'+str(padding)+"\n")
    
    #Let the applications know that we want to load the saved regions
    def loadRegionsFromCamera(self):
        self.sockOut.sendall("loadregions\n")
    
    #Get all of the regions from the scene in a string representation.
    #If separate tile is true then then each tile in the regions will be brought out as a separate single region.
    def getRegions(self, separateTile = True):
        regionString = ""
        
        regionList = self.window.scene.items()
        regionList.reverse()
        for region in regionList:
            area = region.combinedRect()
            if separateTile:
                if region.enabled:
                    for x in range(0, region.xTiles):
                        for y in range(0, region.yTiles):
                            if not regionString == "":
                                regionString+=";"
                            left = (area.x()+x*(float(area.width())/float(region.xTiles)))
                            top = (area.y()+y*(area.height()/float(region.yTiles)))
                            width = (area.width()/float(region.xTiles))
                            height = (area.height()/float(region.yTiles))
                            regionString+="%.3f,%.3f,%.3f,%.3f"%(left, top, width, height)
                            #print regionString
            else:
                if not regionString == "":
                    regionString+=";"
                left = area.x()
                top = area.y()
                width = area.width()
                height = area.height()
                xTiles = region.xTiles
                yTiles = region.yTiles
                enabled = region.enabled
                regionString+="%i,%i,%i,%i,%i,%i,%r"%(left, top, width, height,xTiles,yTiles,enabled)
        return regionString

#The class that contains the regions
class JigsawRegion(QGraphicsRectItem):
    id = 0
    GrabberSize = 6
    xTiles = 1
    yTiles = 1
    Resize = False
    ResizeLeft = False
    ResizeTop = False
    ResizeRight = False
    ResizeBot = False
    selectedColor = None
    curColor = None
    path = None
    modified = False
    minWidth = 0
    minHeight = 0
    lock = False
    enabled = True
    useHover = False
    disabledColor = QColor("Grey")
    disabledHoverColor = QColor(200,0,0)
    hoverColor = QColor(0,255,0)
    disabledSelectedColor = QColor(255,0,0)
    
    def __init__(self, x=0,y=0,width=50,height=50, id=0, minWidth = 0,minHeight = 0, parent=None):
        super(JigsawRegion, self).__init__(parent)
        self.id = id
        self.minWidth = minWidth
        self.minHeight = minHeight
        self.setRect(0,0,width,height)
        self.setBrush(QBrush())
        self.setPen(QPen(QColor("WHITE")))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setPos(x,y)
        app = QApplication.instance()
        self.selectedColor=app.palette().highlight().color()
        self.calcPath()
    
    #Paint a custom region
    def paint(self, painter, option, widget):
        if self.isSelected():
            if self.enabled:
                painter.setPen(QPen(self.selectedColor))
            else:
                painter.setPen(QPen(self.disabledSelectedColor))
        else:
            if self.useHover:
                if self.enabled:
                    painter.setPen(QPen(self.hoverColor))
                else:
                    painter.setPen(QPen(self.disabledHoverColor))
            else:
                if self.enabled:
                    painter.setPen(self.pen())
                else:
                    painter.setPen(QPen(self.disabledColor))
                    
                
        painter.drawPath(self.path)
        
        painter.setPen(QPen(QColor(255,192,128,175)))
        
        #draw each of the tiles.
        xStep = self.rect().width()/self.xTiles
        for x in range(1,self.xTiles):
            painter.drawLine(self.rect().x()+xStep*x,self.rect().y(),self.rect().x()+xStep*x,self.rect().y()+self.rect().height())
        
        yStep = self.rect().height()/self.yTiles
        for y in range(1,self.yTiles):
            painter.drawLine(self.rect().x(),self.rect().y()+yStep*y,self.rect().x()+self.rect().width(),self.rect().y()+yStep*y)
    
    #Create the new path which includes the grabbers
    def calcPath(self, val =None):
        areaRect = self.rect()
        halfGrab = self.GrabberSize/2
        if val is None:
            val = self.isSelected()
        
        #moving to a location closes the path, which we want each path to be closed so that area inside of them is not selectable.
        painterPath = QPainterPath()
        painterPath.moveTo(areaRect.x(),areaRect.y())
        painterPath.lineTo(areaRect.x(),areaRect.y()+areaRect.height())
        painterPath.moveTo(areaRect.x(),areaRect.y()+areaRect.height())
        painterPath.lineTo(areaRect.x()+areaRect.width(),areaRect.y()+areaRect.height())
        painterPath.moveTo(areaRect.x()+areaRect.width(),areaRect.y()+areaRect.height())
        painterPath.lineTo(areaRect.x()+areaRect.width(),areaRect.y())
        painterPath.moveTo(areaRect.x()+areaRect.width(),areaRect.y())
        painterPath.lineTo(areaRect.x(),areaRect.y())
        
        if not self.lock:
            painterPath.addEllipse(areaRect.x()+areaRect.width()/2-halfGrab,areaRect.y()+areaRect.height()/2-halfGrab,self.GrabberSize,self.GrabberSize)
        else:
            painterPath.moveTo(areaRect.x()+areaRect.width()/2,areaRect.y()+areaRect.height()/2-halfGrab)
            painterPath.lineTo(areaRect.x()+areaRect.width()/2,areaRect.y()+areaRect.height()/2+halfGrab)
            painterPath.moveTo(areaRect.x()+areaRect.width()/2-halfGrab,areaRect.y()+areaRect.height()/2)
            painterPath.lineTo(areaRect.x()+areaRect.width()/2+halfGrab,areaRect.y()+areaRect.height()/2)
            
        #add the grabbers if it is selected which are rectangles so the entire area is selectable
        if val:
            painterPath.addRect(areaRect.x()-halfGrab, areaRect.y()-halfGrab, self.GrabberSize, self.GrabberSize)
            painterPath.addRect(areaRect.x()+areaRect.width()-halfGrab, areaRect.y()-halfGrab, self.GrabberSize, self.GrabberSize)
            painterPath.addRect(areaRect.x()-halfGrab, areaRect.y()+areaRect.height()-halfGrab, self.GrabberSize, self.GrabberSize)
            painterPath.addRect(areaRect.x()+areaRect.width()-halfGrab, areaRect.y()+areaRect.height()-halfGrab, self.GrabberSize, self.GrabberSize)
            
        self.prepareGeometryChange()
        self.path=painterPath  
    
    #Control any special changes that are need
    def itemChange(self, change, value):
        #When they are selected/deselected we need to recalculate the path so that the grabbers will appear/disappea
        if change == QGraphicsItem.ItemSelectedChange:
            self.calcPath(value)
        #When the regions is moved make sure that it is never brought outside of the scene adjusting its position
        if change == QGraphicsItem.ItemPositionChange:
            #When the region is first created it is not associated with a scene it could be changed in which case
            if self.scene():
                myRect = self.rect()
                myRect.moveLeft(value.x()+myRect.x())
                myRect.moveTop(value.y()+myRect.y())
                myLeft = myRect.x()
                myRight = myRect.x()+myRect.width()
                myTop = myRect.y()
                myBottom = myRect.y()+myRect.height()
                
                bestHoriz = self.GrabberSize+1
                bestVert = self.GrabberSize+1
                for selector in self.scene().items():        
                    if self is not selector:
                        theirRect = selector.combinedRect()
                                                
                        if myRect.intersects(QRectF(theirRect.x()-self.GrabberSize,theirRect.y()-self.GrabberSize,theirRect.width()+2*self.GrabberSize,theirRect.height()+2*self.GrabberSize)):
                            horizDiff = myLeft-theirRect.x()
                            if abs(horizDiff)<abs(bestHoriz):
                                bestHoriz = horizDiff
                            horizDiff = myRight-theirRect.x()
                            if abs(horizDiff)<abs(bestHoriz):
                                bestHoriz = horizDiff
                            horizDiff = myLeft-(theirRect.x()+theirRect.width())
                            if abs(horizDiff)<abs(bestHoriz):
                                bestHoriz = horizDiff
                            horizDiff = myRight-(theirRect.x()+theirRect.width())
                            if abs(horizDiff)<abs(bestHoriz):
                                bestHoriz = horizDiff
                                
                            vertDiff = myTop-theirRect.y()
                            if abs(vertDiff)<abs(bestVert):
                                bestVert = vertDiff
                            vertDiff = myBottom-theirRect.y()
                            if abs(vertDiff)<abs(bestVert):
                                bestVert = vertDiff
                            vertDiff = myTop-(theirRect.y()+theirRect.height())
                            if abs(vertDiff)<abs(bestVert):
                                bestVert = vertDiff
                            vertDiff = myBottom-(theirRect.y()+theirRect.height())
                            if abs(vertDiff)<abs(bestVert):
                                bestVert = vertDiff
                
                if abs(bestHoriz)<self.GrabberSize+1:
                    value.setX( value.x() - bestHoriz)
                if abs(bestVert)<self.GrabberSize+1:
                    value.setY( value.y() - bestVert)
                
                myRect = self.rect()
                myRect.moveTop(value.y()+myRect.y())
                myRect.moveLeft(value.x()+myRect.x())
                myLeft = myRect.x()
                myRight = myRect.x()+myRect.width()
                myTop = myRect.y()
                myBottom = myRect.y()+myRect.height()
                                
                if myLeft <0:
                    value.setX(value.x()-myLeft)
                elif myRight > self.scene().sceneRect().width():
                    value.setX(value.x()+(self.scene().sceneRect().width()-myRight))
                    
                if myTop <0:
                    value.setY(value.y()-myTop)
                elif myBottom > self.scene().sceneRect().height():
                    value.setY(value.y()+(self.scene().sceneRect().height()-myBottom))
                
                return super(JigsawRegion, self).itemChange(change, value)
            
        return super(JigsawRegion, self).itemChange(change, value)
    
    #calculate the shape (which is the selectable area)
    def shape(self):
        #if it is selected then the entire path is selectable
        if self.isSelected():
            return self.path
        else: #otherwise it is the circle at the center
            areaRect = self.rect()
            halfGrab = self.GrabberSize/2
            painterPath = QPainterPath()
            painterPath.addEllipse(areaRect.x()+areaRect.width()/2-halfGrab,areaRect.y()+areaRect.height()/2-halfGrab,self.GrabberSize,self.GrabberSize)
            return painterPath
            
    #calculate the bounding rect 
    def boundingRect(self):
        #if the path is set(will be after creation) then use the paths bounding rect
        if self.path:
            return self.path.boundingRect()
        return super(JigsawRegion, self).boundingRect()
    
    #Return the area in the scene in which the rect is
    #this is used because when the region is moved it changes it's position while when it is resized it changes it's rectangle
    def combinedRect(self):
        area = self.rect()
        area.moveLeft(self.pos().x()+area.x())
        area.moveTop(self.pos().y()+area.y())
        return area
    
    #When you press on the Region find out where you pressed and set up resize if you pressed in the sides
    def mousePressEvent(self, event):
        scenePoint = event.scenePos()
        localPos = self.mapFromScene(scenePoint)
        areaRect = self.rect()
        halfGrab = self.GrabberSize/2
        
        if localPos.x()<areaRect.x()+halfGrab:
            self.Resize = True
            self.ResizeLeft=True
        if localPos.y()<areaRect.y()+halfGrab:
            #Top Left Corner
            self.Resize = True
            self.ResizeTop=True
        if localPos.y()>areaRect.y()+areaRect.height()-halfGrab:
            self.Resize = True
            self.ResizeBot=True
        if localPos.x()>areaRect.x()+areaRect.width()-halfGrab:
            self.Resize = True
            self.ResizeRight=True           
        
        super(JigsawRegion, self).mousePressEvent(event)
    
    #if you are resizing then resize everything otherwise let qt handle it
    def mouseMoveEvent(self, event):
        if self.lock:
            return
        self.modified = True
        if self.Resize:
            scenePoint = event.scenePos()
            localPos = self.mapFromScene(scenePoint)
            areaRect = self.rect()
            areaRect.setWidth(areaRect.width())
            areaRect.setHeight(areaRect.height())
            if self.ResizeLeft:
                areaRect.setX(localPos.x())
                if areaRect.width()<self.minWidth:
                    areaRect.setX(areaRect.x()+areaRect.width()-self.minWidth)
                                
                myLeft = areaRect.x()+self.pos().x()
                
                myRect = self.combinedRect()
                
                bestHoriz = self.GrabberSize+1
                for selector in self.scene().items():        
                    if self is not selector:
                        theirRect = selector.combinedRect()            
                        if myRect.intersects(QRectF(theirRect.x()-self.GrabberSize,theirRect.y()-self.GrabberSize,theirRect.width()+2*self.GrabberSize,theirRect.height()+2*self.GrabberSize)):
                            horizDiff = myLeft-theirRect.x()
                            if abs(horizDiff)<abs(bestHoriz):
                                bestHoriz = horizDiff
                            horizDiff = myLeft-(theirRect.x()+theirRect.width())
                            if abs(horizDiff)<abs(bestHoriz):
                                bestHoriz = horizDiff
                if abs(bestHoriz)<self.GrabberSize+1:
                    areaRect.setX( areaRect.x() - bestHoriz)
                if areaRect.x()+self.pos().x()<0:
                    areaRect.setX(-self.pos().x())    
                
            elif self.ResizeRight:
                horizDiff = (localPos.x()-(areaRect.x()+areaRect.width()))/2
                areaRect.setWidth(areaRect.width()+horizDiff)
                if areaRect.width()<self.minWidth:
                    areaRect.setWidth(minWidth)
                
                myRect = self.combinedRect()
                myRight = areaRect.x()+areaRect.width()+self.pos().x()
                bestHoriz = self.GrabberSize+1
                for selector in self.scene().items():        
                    if self is not selector:
                        theirRect = selector.combinedRect()          
                        if myRect.intersects(QRectF(theirRect.x()-self.GrabberSize,theirRect.y()-self.GrabberSize,theirRect.width()+2*self.GrabberSize,theirRect.height()+2*self.GrabberSize)):
                            horizDiff = myRight-theirRect.x()
                            if abs(horizDiff)<abs(bestHoriz):
                                bestHoriz = horizDiff
                            horizDiff = myRight-(theirRect.x()+theirRect.width())
                            if abs(horizDiff)<abs(bestHoriz):
                                bestHoriz = horizDiff
                if abs(bestHoriz)<self.GrabberSize+1:
                    areaRect.setWidth( areaRect.width() - bestHoriz)
                if areaRect.width()+areaRect.x()+self.pos().x()>self.scene().sceneRect().width():
                    areaRect.setWidth(self.scene().sceneRect().width()-areaRect.x()-self.pos().x())
            if self.ResizeTop:
                areaRect.setY(localPos.y())
                if areaRect.height()<self.minHeight:
                    areaRect.setY(areaRect.y()+areaRect.height()-self.minHeight)
                
                myRect = self.combinedRect()
                myTop = areaRect.y()+self.pos().y()
                bestVert = self.GrabberSize+1
                for selector in self.scene().items():        
                    if self is not selector:
                        theirRect = selector.combinedRect()            
                        if myRect.intersects(QRectF(theirRect.x()-self.GrabberSize,theirRect.y()-self.GrabberSize,theirRect.width()+2*self.GrabberSize,theirRect.height()+2*self.GrabberSize)):
                            vertDiff = myTop-theirRect.y()
                            if abs(vertDiff)<abs(bestVert):
                                bestVert = vertDiff
                            vertDiff = myTop-(theirRect.y()+theirRect.height())
                            if abs(vertDiff)<abs(bestVert):
                                bestVert = vertDiff
                if abs(bestVert)<self.GrabberSize+1:
                    areaRect.setY( areaRect.y() - bestVert)
                if areaRect.y()+self.pos().y()<0:
                    areaRect.setY(-self.pos().y())
            elif self.ResizeBot:
                vertDiff = (localPos.y()-(areaRect.y()+areaRect.height()))/2
                areaRect.setHeight(areaRect.height()+vertDiff)
                if areaRect.height()<self.minHeight:
                    areaRect.setHeight(self.minHeight)
                    
                myRect = self.combinedRect()
                myBottom = areaRect.y()+self.pos().y()+areaRect.height()
                bestVert = self.GrabberSize+1
                for selector in self.scene().items():        
                    if self is not selector:
                        theirRect = selector.combinedRect()              
                        if myRect.intersects(QRectF(theirRect.x()-self.GrabberSize,theirRect.y()-self.GrabberSize,theirRect.width()+2*self.GrabberSize,theirRect.height()+2*self.GrabberSize)):
                            vertDiff = myBottom-theirRect.y()
                            if abs(vertDiff)<abs(bestVert):
                                bestVert = vertDiff
                            vertDiff = myBottom-(theirRect.y()+theirRect.height())
                            if abs(vertDiff)<abs(bestVert):
                                bestVert = vertDiff
                if abs(bestVert)<self.GrabberSize+1:
                    areaRect.setHeight( areaRect.height() - bestVert)
                if areaRect.height()+areaRect.y()+self.pos().y()>self.scene().sceneRect().height():
                    areaRect.setHeight(self.scene().sceneRect().height()-areaRect.y()-self.pos().y())
                
            self.setRect(areaRect)
            self.calcPath()
            
        else:
            super(JigsawRegion, self).mouseMoveEvent(event)

    #when you release the mouse reset the mouse, if anything changed then add an undo point and set the scene as dirty
    def mouseReleaseEvent(self, event):
        self.Resize = False
        self.ResizeTop = False
        self.ResizeBot = False
        self.ResizeLeft = False
        self.ResizeRight = False
        if self.modified:
            self.scene().views()[0].parentWidget().addUndoPoint()
            self.scene().views()[0].parentWidget().dirty = True
            self.modified = False
        super(JigsawRegion, self).mouseReleaseEvent(event)
    
    #when you release the mouse reset the mouse, if anything changed then add an undo point and set the scene as dirty
    def hoverEnterEvent(self, event):
        self.useHover = True
        '''
        if self.enabled:
            self.setPen(QPen(QColor(0,255,0)))
            self.selectedColor=QColor(0,255,0)
        else:
            self.setPen(QPen(QColor(255,0,0)))
            self.selectedColor=QColor(255,0,0)
        '''
        
    #when you hover over a side/corner change the cursor to the correct diagonal
    def hoverMoveEvent(self, event):
        scenePoint = event.scenePos()
        localPos = self.mapFromScene(scenePoint)
        areaRect = self.rect()
        halfGrab = self.GrabberSize/2
        newCursor = None
        QApplication.restoreOverrideCursor()
        if localPos.x()<areaRect.x()+halfGrab:
            if localPos.y()<areaRect.y()+halfGrab:
                newCursor = QCursor(Qt.SizeFDiagCursor)
            elif localPos.y()>areaRect.y()+areaRect.height()-halfGrab:
                newCursor = QCursor(Qt.SizeBDiagCursor)
            else:
                newCursor = QCursor(Qt.SizeHorCursor)
        elif localPos.x()>areaRect.x()+areaRect.width()-halfGrab:
            if localPos.y()<areaRect.y()+halfGrab:
                newCursor = QCursor(Qt.SizeBDiagCursor)
            elif localPos.y()>areaRect.y()+areaRect.height()-halfGrab:
                newCursor = QCursor(Qt.SizeFDiagCursor)
            else:
                newCursor = QCursor(Qt.SizeHorCursor)
        elif localPos.y()<areaRect.y()+halfGrab:
            newCursor = QCursor(Qt.SizeVerCursor)
        elif localPos.y()>areaRect.y()+areaRect.height()-halfGrab:
            newCursor = QCursor(Qt.SizeVerCursor)
        else:
            newCursor = QCursor(Qt.SizeAllCursor)
        QApplication.setOverrideCursor(newCursor)
    
    #When you leave the region reset the colors and restore the cursor
    def hoverLeaveEvent(self, event):
        self.useHover = False
        '''
        if self.enabled:
            self.setPen(QPen(QColor("WHITE")))
            self.selectedColor=QApplication.palette().highlight().color()
        else:
            self.setPen(QPen(QColor("Grey")))
            self.selectedColor=QColor(200,0,0)
        '''
        
        QApplication.restoreOverrideCursor()

def recvData(theSocket):
    totalData=[]
    data=''
    while True:
        data=theSocket.recv(8192)
        if not data:
            return None
        if "\n" in data:
            totalData.append(data[:data.find("\n")])
            break
        totalData.append(data)
    return ''.join(totalData)
        
def to_bool(value):
    valid = {'true': True, 't': True, '1': True,
             'false': False, 'f': False, '0': False,
             }   

    if isinstance(value, bool):
        return value

    if not isinstance(value, basestring):
        raise ValueError('invalid literal for boolean. Not a string.')

    lower_value = value.lower()
    if lower_value in valid:
        return valid[lower_value]
    else:
        raise ValueError('invalid literal for boolean: "%s"' % value)
        
#create the Form
def __main__( port=0, image="", openIncomming="True", minWidth="0", minHeight="0", allowFit="True" ):
    import sys
    try:
        if openIncomming == "True":
            openIncomming = True
        else:
            openIncomming = False
        if allowFit == "True":
            allowFit = True
        else:
            allowFit = False
        
        app = QApplication(sys.argv)
        screen = JigsawForm(background=image, port=int(port),openThread=openIncomming, minWidth=int(minWidth), minHeight=int(minHeight), allowFit=allowFit )
        screen.show()
        app.exec_()
        
    except:   
        print(traceback.format_exc())