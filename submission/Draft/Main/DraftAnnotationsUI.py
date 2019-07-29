from __future__ import print_function
from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

import os
import copy
import sys
import imp
import json

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

draftMainPath = RepositoryUtils.GetRepositoryPath( "submission/Draft/Main", True )
sys.path.append( draftMainPath )

from DraftInit import *
from DraftImageViewer import *
from DraftImageRegion import *

########################################################
## Initialize Draft
########################################################
DraftInit()
import Draft
try:
    Draft.LibraryInfo.Version()
except:
    imp.reload( Draft )

from DraftCreateAnnotations import *

#####################################################
## Globals
#####################################################
scriptDialog = None
stickyImage = ""
windowStartHeight = 700
windowStartWidth = 720
resolutionWidth = 640
resolutionHeight = 480
backgroundRedColor = 0
backgroundGreenColor = 0
backgroundBlueColor = 0
framePaddingSize = 4

########################################################################
## Main Function Called by DraftUI
########################################################################
def __main__( *args ):
    global scriptDialog
    global stickyImage
    global resolutionWidth
    global resolutionHeight
    global backgroundRedColor
    global backgroundGreenColor
    global backgroundBlueColor
    global framePaddingSize

    annotationStringArg = ""
    firstFrameFileArg = ""
    stickyImageFileArg = ""
    resolutionWidthArg = ""
    resolutionHeightArg = ""
    framePaddingArg = 0
    backgroundRedColorArg = ""
    backgroundGreenColorArg = ""
    backgroundBlueColorArg = ""

    for arg in args:
        if arg.startswith( "annotationString=" ):
            annotationStringArg = str( arg.replace( "annotationString=", "" ) )
        elif arg.startswith( "firstFrameFile=" ):
            firstFrameFileArg = arg.replace( "firstFrameFile=", "" )
        elif arg.startswith( "stickyImageFile=" ):
            stickyImageFileArg = arg.replace( "stickyImageFile=", "" )
        elif arg.startswith( "resolutionWidth=" ):
            resolutionWidthArg = arg.replace( "resolutionWidth=", "" )
        elif arg.startswith( "resolutionHeight=" ):
            resolutionHeightArg = arg.replace( "resolutionHeight=", "" )
        elif arg.startswith( "framePadding=" ):
            framePaddingArg = int( arg.replace( "framePadding=", "" ) )
        elif arg.startswith( "backgroundRedColor=" ):
            backgroundRedColorArg = arg.replace( "backgroundRedColor=", "" )
        elif arg.startswith( "backgroundGreenColor=" ):
            backgroundGreenColorArg = arg.replace( "backgroundGreenColor=", "" )
        elif arg.startswith( "backgroundBlueColor=" ):
            backgroundBlueColorArg = arg.replace( "backgroundBlueColor=", "" )
        elif arg == "":
            pass
        else:
            print("Unknown argument found on window creation: " + arg + ".")

    if framePaddingArg > 0:
        framePaddingSize = framePaddingArg

    scriptDialog = DraftAnnotationDialog( annotationStringArg )

    # If the values are available we need to set the background as the first frame, and if not then it'll be the sticky image (and then finally just change the resolution/color).
    # However if the image fails to load we should try the next option in the list as a backup. Condensing this code would be good but I'm not sure how.
    if firstFrameFileArg != "":
        SetBackgroundToFirstFrame( firstFrameFileArg)

        # The background should default to one of the two other options when the image fails to load.
        if scriptDialog.GetValue( "DraftImageFileBrowser" ) == "":
            if stickyImageFileArg != "":
                SetBackgroundToStickyImage( stickyImageFileArg )

                if scriptDialog.GetValue( "DraftImageFileBrowser" ) == "" and resolutionWidthArg != "" and resolutionHeightArg != "":
                    SetBlankBackgroundResolution( resolutionWidthArg, resolutionHeightArg )
                    ChangeBlankBackgroundColor( backgroundRedColorArg, backgroundGreenColorArg, backgroundBlueColorArg )
            elif resolutionWidthArg != "" and resolutionHeightArg != "":
                SetBlankBackgroundResolution( resolutionWidthArg, resolutionHeightArg )
                ChangeBlankBackgroundColor( backgroundRedColorArg, backgroundGreenColorArg, backgroundBlueColorArg )
    elif stickyImageFileArg != "":
        SetBackgroundToStickyImage( stickyImageFileArg )

        # The background should default to the last option when the image fails to load.
        if scriptDialog.GetValue( "DraftImageFileBrowser" ) == "" and resolutionWidthArg != "" and resolutionHeightArg != "":
            SetBlankBackgroundResolution( resolutionWidthArg, resolutionHeightArg )
            ChangeBlankBackgroundColor( backgroundRedColorArg, backgroundGreenColorArg, backgroundBlueColorArg )
    elif resolutionWidthArg != "" and resolutionHeightArg != "":
        SetBlankBackgroundResolution( resolutionWidthArg, resolutionHeightArg )
        ChangeBlankBackgroundColor( backgroundRedColorArg, backgroundGreenColorArg, backgroundBlueColorArg )

    # Show main dialog
    scriptDialog.ShowDialog( True )

def SetBackgroundToFirstFrame( firstFrameFileArg ):
    global scriptDialog

    scriptDialog.SetValue( "DraftImageFileBrowser", firstFrameFileArg )
    scriptDialog.SetValue( "DraftImageRadio", True )

def SetBackgroundToStickyImage( stickyImageFileArg ):
    global scriptDialog
    global stickyImage

    stickyImage = stickyImageFileArg
    scriptDialog.SetValue( "DraftImageFileBrowser", stickyImage )
    scriptDialog.SetValue( "DraftImageRadio", True )

def SetBlankBackgroundResolution( resolutionWidthArg, resolutionHeightArg ):
    global scriptDialog

    resolutionWidthArg = int( resolutionWidthArg )
    resolutionHeightArg = int( resolutionHeightArg )

    # Check for preset resolution values.
    if resolutionWidthArg != 0 and resolutionHeightArg != 0:
        if resolutionWidthArg == 640 and resolutionHeightArg == 480:
            scriptDialog.SetValue( "DraftResolution", "640x480" )
        elif resolutionWidthArg == 1280 and resolutionHeightArg == 720:
            scriptDialog.SetValue( "DraftResolution", "1280x720" )
        elif resolutionWidthArg == 1920 and resolutionHeightArg == 1080:
            scriptDialog.SetValue( "DraftResolution", "1920x1080" )
        else:
            scriptDialog.SetValue( "DraftCustomWidthBox", resolutionWidthArg )
            scriptDialog.SetValue( "DraftCustomHeightBox", resolutionHeightArg )
            scriptDialog.SetValue( "DraftResolution", "Custom" )

def ChangeBlankBackgroundColor( backgroundRedColorArg, backgroundGreenColorArg, backgroundBlueColorArg ):
    global scriptDialog
    global backgroundRedColor
    global backgroundGreenColor
    global backgroundBlueColor

    if backgroundRedColorArg != "":
        backgroundRedColor = float ( backgroundRedColorArg )
    if backgroundGreenColorArg != "":
        backgroundGreenColor = float ( backgroundGreenColorArg )
    if backgroundBlueColorArg != "":
        backgroundBlueColor = float ( backgroundBlueColorArg )

    if ( backgroundRedColor + backgroundGreenColor + backgroundBlueColor ) > 0:
        scriptDialog.colorControl.setTheValue( QColor( ( backgroundRedColor * 255 ), ( backgroundGreenColor * 255 ), ( backgroundBlueColor * 255 ) ) )

def OKButtonClicked():
    annotationsString = json.dumps( scriptDialog.annotationsDict )
    ClientUtils.LogText( "DraftAnnotationsString=" + annotationsString )
    ClientUtils.LogText( "DraftAnnotationsImageString=" + stickyImage )

    if resolutionWidth != 0:
        ClientUtils.LogText( "DraftAnnotationsResWidthString=" + str( resolutionWidth ) )
    if resolutionHeight != 0:
        ClientUtils.LogText( "DraftAnnotationsResHeightString=" + str( resolutionHeight ) )

    ClientUtils.LogText( "DraftAnnotationsBGRedColorString=" + str( backgroundRedColor ) )
    ClientUtils.LogText( "DraftAnnotationsBGGreenColorString=" + str( backgroundGreenColor ) )
    ClientUtils.LogText( "DraftAnnotationsBGBlueColorString=" + str( backgroundBlueColor ) )

    super( DraftAnnotationDialog, scriptDialog ).accept()
    
def CancelButtonClicked():
    ClientUtils.LogText( "Create Annotation has been Cancelled" )
    super( DraftAnnotationDialog, scriptDialog ).reject()

def ClearAllButtonClicked():
    scriptDialog.ResetAnnotationsDict()
    scriptDialog.UpdateUI()
    scriptDialog.fontColorControl.setTheValue( QColor( 255, 255, 255 ) )

class DraftAnnotationDialog( DeadlineScriptDialog ):
    defaultImageHeightInViewer = 480.0
    
    def __init__( self, stickyAnnotationsString=None, parent=None ):
        super( DraftAnnotationDialog, self ).__init__( parent )
        global windowStartWidth
        global windowStartHeight
        
        self.parent = parent
        self.img = None
        self.imgOrig = None
        self.imageViewer = None
        self.previousAnchor = 'NorthWest'
        self.selectedAnchor = 'NorthWest'
        self.minBoxWidth = 0
        self.minBoxHeight = 0
        self.boxList = list()
        self.movingBox = False
        self.panning = False
        self.cursorPanCurr = None

        self.annotations = [ 'NorthWest', 'NorthCenter', 'NorthEast', 'SouthWest', 'SouthCenter', 'SouthEast' ]
        self.annotationsDict = {}
        self.boxIdDict = { 'NorthWest':0, 'NorthCenter':1, 'NorthEast':2, 'SouthWest':3, 'SouthCenter':4, 'SouthEast':5 }
        self.resolutions = [ '640x480', '1280x720', '1920x1080', 'Custom' ]
        self.resolutionsDict = { '640x480':[640,480], '1280x720':[1280,720], '1920x1080':[1920,1080], 'Custom':None }

        self.ResetAnnotationsDict()

        self.SetTitle( "Draft Create Annotations" )
        self.SetIcon( self.GetIcon( 'DraftPlugin' ) )

        menuBar = QMenuBar( self )
        menuBar.setNativeMenuBar( False )
        fileMenu = menuBar.addMenu( "File" )

        self.loadAnnotationsAction = QAction( '&Load Annotations', self )
        self.loadAnnotationsAction.triggered.connect( self.LoadAnnotations )
        self.loadAnnotationsAction.setShortcut( QKeySequence( Qt.CTRL + Qt.Key_O ) )

        self.saveAnnotationsAction = QAction( '&Save Annotations', self )
        self.saveAnnotationsAction.triggered.connect( self.SaveAnnotations )
        self.saveAnnotationsAction.setShortcut( QKeySequence( Qt.CTRL + Qt.Key_S ) )
        
        fileMenu.addAction( self.loadAnnotationsAction )
        fileMenu.addAction( self.saveAnnotationsAction )

        self.layout().setMenuBar( menuBar )

        self.zoomLabel = QLabel( "Zoom %" )
        self.zoomLabel.setToolTip( "Determine how the image will be scaled in the viewer." )
        self.zoomSlider = QSlider( Qt.Horizontal )
        self.zoomSlider.setRange( 1, 500 )
        self.zoomSlider.setValue( 100 )
        self.zoomSlider.setToolTip( "The amount of padding to be added to each region created with Fit Scene." )
        self.zoomSlider.valueChanged.connect( self.AdjustZoom )

        self.resetZoomBtn = QPushButton( "Reset Zoom" )
        self.resetZoomBtn.clicked.connect( self.ResetZoom )
        self.resetZoomBtn.setDefault( False )
        self.resetZoomBtn.setAutoDefault( False )
        self.resetZoomBtn.setToolTip( "Reset the zoom to 100% within the viewport." )

        self.fitViewportBtn = QPushButton( "Fit Viewport" )
        self.fitViewportBtn.clicked.connect( self.FitViewport )
        self.fitViewportBtn.setDefault( False )
        self.fitViewportBtn.setAutoDefault( False )
        self.fitViewportBtn.setToolTip( "Zoom to see everything in the viewport." )

        self.keepFitBtn = QCheckBox( "Keep Fit" )
        self.keepFitBtn.setChecked( False )
        self.keepFitBtn.stateChanged.connect( self.KeepFit )
        self.keepFitBtn.setToolTip( "Zoom to see everything in the viewport and force the viewport to not change." )

        zoomLayout = QHBoxLayout()
        zoomLayout.addWidget( self.zoomLabel )
        zoomLayout.addWidget( self.zoomSlider )
        zoomLayout.addWidget( self.resetZoomBtn )
        zoomLayout.addWidget( self.fitViewportBtn )
        zoomLayout.addWidget( self.keepFitBtn )
        self.layout().addLayout( zoomLayout )

        self.AddImageViewer()
        self.LoadStickyAnnotations( stickyAnnotationsString )
        
        self.AddGrid()
        self.AddControlToGrid( "DraftAnnotationTextLabel", "LabelControl", "Text", 0, 0, "The annotation for the position currently selected.", expand=False )
        self.textField = self.AddControlToGrid( "DraftAnnotationTextBox", "TextControl", "", 0, 1 )
        
        addSymbolButton = self.AddControlToGrid( "AddSymbolButton", "ButtonControl", "Insert Token", 0, 2, "Menu for inserting annotation quick reference.", expand=False  )
        addSymbolButton.ValueModified.connect( self.AddSymbolPressed )
        
        self.AddControlToGrid( "DraftAnchorLabel", "LabelControl", "Position", 0, 3, "The current position.", expand=False )
        anchor = self.AddComboControlToGrid( "DraftAnchor", "ComboControl", "NorthWest", self.annotations, 0, 4, expand=False )
        anchor.ValueModified.connect( self.AnchorBoxChanged )

        updateButton = self.AddControlToGrid( "UpdateButton", "ButtonControl", "Update Annotations", 0, 5, "Updates current position with specified annotation.", expand=False )
        updateButton.clicked.connect( self.AddAnnotation )
        updateButton.setDefault( True )
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid( "DraftFontColorLabel", "LabelControl", "Font Color", 1, 0, "The font color for the current annotation.", False )
        self.fontColorControl = self.AddControlToGrid( "ColorControl", "ColorControl", "", 1, 1, "", False )
        self.fontColorControl.setTheValue( QColor( 255, 255, 255 ) )
        self.fontColorControl.ValueModified.connect( self.UpdateFontColor )
        self.AddHorizontalSpacerToGrid( "HSpacer", 1, 2 )
        self.EndGrid()

        self.AddGroupBox( "DraftPreviewGroupBox", "Preview", False )
        self.AddGrid()
        resolutionRadio = self.AddRadioControlToGrid( "DraftBlankRadio", "RadioControl", True, "Use Blank Background", "RadioGroup", 2, 0, "If selected, Draft will use a blank image for the background." )
        resolutionRadio.ValueModified.connect( self.UpdateUI )
        self.EndGrid()
        
        self.AddGrid()
        self.AddControlToGrid( "IndentLabel1", "LabelControl", "    ", 3, 0, "", False )
        self.AddControlToGrid( "DraftResolutionLabel", "LabelControl", "Resolution", 3, 1, "The blank image's resolution.", False )
        resolution = self.AddComboControlToGrid( "DraftResolution", "ComboControl", "640x480", self.resolutions, 3, 2, expand=False, colSpan=1 )
        resolution.ValueModified.connect( self.UpdateUI )
        customWidth = self.AddRangeControlToGrid( "DraftCustomWidthBox", "RangeControl", 640, 1, 9999, 0, 1, 3, 3, expand=False )
        customHeight = self.AddRangeControlToGrid( "DraftCustomHeightBox", "RangeControl", 480, 1, 9999, 0, 1, 3, 4, expand=False )
        customWidth.ValueModified.connect( self.UpdateImage )
        customHeight.ValueModified.connect( self.UpdateImage )
        self.AddControlToGrid( "ColorLabel", "LabelControl", "Background Color", 3, 5, "Choose the color to be used for the blank background preview.", False )
        self.colorControl = self.AddControlToGrid( "ColorControl", "ColorControl", "", 3, 6, "", False )
        self.colorControl.setTheValue( QColor( 0, 0, 0 ) )
        self.colorControl.ValueModified.connect( self.UpdateBackgroundColor )
        self.AddHorizontalSpacerToGrid( "HSpacer", 3, 7 )
        self.EndGrid()
        
        self.AddGrid()
        imageRadio = self.AddRadioControlToGrid( "DraftImageRadio", "RadioControl", False, "Use Image From File", "RadioGroup", 5, 0, "If selected, Draft will use the specified image file for the background." )
        self.EndGrid()
        
        self.AddGrid()
        self.AddControlToGrid( "IndentLabel3", "LabelControl", "    ", 6, 0, "", False )        
        self.AddControlToGrid( "DraftImageFileLabel", "LabelControl", "Image File", 6, 1, "The path to the image file that will be loaded in the viewer.", False )
        fileBrowser = self.AddSelectionControlToGrid( "DraftImageFileBrowser", "FileBrowserControl", "", "All Files (*)", 6, 2, colSpan=9, browserLocation=ClientUtils.GetCurrentUserHomeDirectory() )
        fileBrowser.ValueModified.connect( self.UpdateUI )
        self.EndGrid()
        self.EndGroupBox( False )

        # Add control buttons
        self.AddGrid()
        self.AddHorizontalSpacerToGrid( "HSpacer", 7, 0 )
        okButton = self.AddControlToGrid( "OkButton", "ButtonControl", "OK", 7, 1, expand=False )
        okButton.clicked.connect( OKButtonClicked )
        cancelButton = self.AddControlToGrid( "CancelButton", "ButtonControl", "Cancel", 7, 2, expand=False )
        cancelButton.clicked.connect( CancelButtonClicked )
        clearAllButton = self.AddControlToGrid( "ClearAllButton", "ButtonControl", "Clear All", 7, 3, expand=False )
        clearAllButton.clicked.connect( ClearAllButtonClicked )
        self.EndGrid()
        
        # Define context menu
        self.newSymbolMenu = QMenu()
        item = QAction( "$frame", self )
        item.triggered.connect( self.AddFrameClicked )
        self.newSymbolMenu.addAction( item )
        
        item = QAction( "$time", self )
        item.triggered.connect( self.AddTimeClicked )
        self.newSymbolMenu.addAction( item )
        
        item = QAction( "$logo", self )
        item.triggered.connect( self.AddLogoClicked )
        self.newSymbolMenu.addAction( item )
        
        item = QAction( "$dimensions", self )
        item.triggered.connect( self.AddDimensionsClicked )
        self.newSymbolMenu.addAction( item )

        self.CreateAnnotationBoxes()
        self.UpdateUI()
        self.resize( windowStartWidth, windowStartHeight )

        # Center window.
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                self.size(),
                QApplication.desktop().availableGeometry()
            )
        )

        self.keepFitBtn.setChecked( True )
        self.FitViewport()
        self.ResetAnnotationBoxPositions()
        self.HighlightBox()
        self.ChangeSelectedFont()

    def ResetAnnotationsDict( self ):
        self.annotationsDict = { 'NorthWest':{}, 'NorthCenter':{}, 'NorthEast':{}, 'SouthWest':{}, 'SouthCenter':{}, 'SouthEast':{} }

        for anchor, key in self.annotationsDict.iteritems():
            key[ 'text' ] = ""
            key[ 'colorR' ] = ""
            key[ 'colorG' ] = ""
            key[ 'colorB' ] = ""
            key[ 'type' ] = ""

    def AddImageViewer( self ):
        self.scene = QGraphicsScene()
        self.imageViewer = DraftImageViewer( self.scene )
        self.imageViewer.mousePressedSignal.connect( self.MousePressed )
        self.imageViewer.mouseMovedSignal.connect( self.MouseMoved )
        self.imageViewer.mouseReleasedSignal.connect( self.MouseReleased )
        self.imageViewer.wheelScrolledSignal.connect( self.WheelScrolled )
        self.imageViewer.zoomUpdated.connect( self.UpdatedZoomSlider )
        
        layout = QVBoxLayout()
        layout.addWidget( self.imageViewer )
        self.layout().addLayout( layout )
        
    def LoadStickyAnnotations( self, stickyAnnotationsString ):
        if stickyAnnotationsString != "":
            self.annotationsDict = json.loads( stickyAnnotationsString )
    
    def UpdateUI( self ):
        self.UpdateImage()
        self.UpdateUIState()

    def UpdateImage( self ):
        global stickyImage
        global resolutionWidth
        global resolutionHeight
        global backgroundRedColor
        global backgroundGreenColor
        global backgroundBlueColor

        self.img = None
        self.imgOrig = None
        path = self.GetValue( "DraftImageFileBrowser" ).strip()
        
        if self.GetValue( "DraftImageRadio" ) and len( path ) != 0:
            try:
                self.imgOrig = Draft.Image.ReadFromFile( path )
                stickyImage = path
            except RuntimeError:
                self.ShowMessageBox( "The image file:\n\"" + path + "\"\n is unable to be displayed. Please select another image file or set the resolution manually.", "Warning" )
                self.SetValue( "DraftImageFileBrowser", "" )
                self.SetValue( "DraftBlankRadio", True )
                stickyImage = ""
            except Exception as e:
                self.ShowMessageBox( "Unable to read the image file. " + str( e ) + "\nPlease select another image file or set the resolution manually.", "Warning" )
                self.SetValue( "DraftImageFileBrowser", "" )
                self.SetValue( "DraftBlankRadio", True )
                stickyImage = ""
        
        if self.GetValue( "DraftBlankRadio" ) or len( path ) == 0:
            stickyImage = ""
            resolution = self.GetValue( "DraftResolution" )
            if resolution != "Custom":
                dimensions = self.resolutionsDict[ resolution ]
                width = dimensions[0]
                height = dimensions[1]
            else:
                width = self.GetValue( "DraftCustomWidthBox" )
                height = self.GetValue( "DraftCustomHeightBox" )

            resolutionWidth = width
            resolutionHeight = height
            self.imgOrig = Draft.Image.CreateImage( width, height )
            self.imgOrig.SetToColor( Draft.ColorRGBA( backgroundRedColor, backgroundGreenColor, backgroundBlueColor, 1 ) )
            self.imgOrig.SetChannel( 'A', 1 )
        
        self.img = copy.deepcopy( self.imgOrig )
        self.imageViewer.setImage( self.img )
        self.ResetAnnotationBoxPositions()
        self.UpdateAllAnnotations()

        zoomFactor = min( DraftAnnotationDialog.defaultImageHeightInViewer / self.img.height, 5.0 )
        self.zoomSlider.setValue( zoomFactor * 100 )
        self.imageViewer.zoomImage( zoomFactor )
        
        if not self.keepFitBtn.isChecked():
            self.keepFitBtn.setChecked( True )

        self.FitViewport()

    def UpdateUIState( self ):
        resolutionEnabled = self.GetValue( "DraftBlankRadio" )
        imageEnabled = self.GetValue( "DraftImageRadio" )
        anchorIsNotNone = self.IsNotNone( self.selectedAnchor )
        
        self.SetEnabled( "DraftResolutionLabel", resolutionEnabled )
        self.SetEnabled( "DraftResolution", resolutionEnabled )
        self.SetEnabled( "DraftCustomWidthBox", resolutionEnabled and self.GetValue( "DraftResolution" ) == "Custom"  )
        self.SetEnabled( "DraftCustomHeightBox", resolutionEnabled and self.GetValue( "DraftResolution" ) == "Custom"  )
        
        self.SetEnabled( "DraftImageFileLabel", imageEnabled )
        self.SetEnabled( "DraftImageFileBrowser", imageEnabled )
        
        if anchorIsNotNone:
            self.SetValue( "DraftAnnotationTextBox", self.annotationsDict[ self.selectedAnchor ][ 'text' ] )  
        else:
            self.SetValue( "DraftAnnotationTextBox", "" )
             
        self.SetEnabled( "DraftAnnotationTextLabel", anchorIsNotNone )
        self.SetEnabled( "DraftAnnotationTextBox", anchorIsNotNone )
        self.SetEnabled( "AddSymbolButton", anchorIsNotNone )
        self.textField.setFocus()

    def UpdateAllAnnotations( self ):
        for anchor, boxId in self.boxIdDict.iteritems():
            self.UpdateSingleAnnotation( anchor, boxId )

    def UpdateSingleAnnotation( self, anchor, boxId ):
        if len( self.boxList ) > 0:
            anchorDict = self.annotationsDict[ anchor ]
            self.boxList[ boxId ].updateFont( anchorDict[ 'colorR'], anchorDict[ 'colorG'], anchorDict[ 'colorB'] )
            self.boxList[ boxId ].updateText( anchorDict[ 'text' ], framePaddingSize )

    def UpdateBackgroundColor( self ):
        global backgroundRedColor
        global backgroundGreenColor
        global backgroundBlueColor

        color = self.colorControl.getTheValue()
        backgroundRedColor = color.R / float( 255 )
        backgroundGreenColor = color.G / float( 255 )
        backgroundBlueColor = color.B / float( 255 )

        self.UpdateImage()

    def UpdateFontColor( self ):
        color = self.fontColorControl.getTheValue()
        anchorColorR = self.annotationsDict[ self.selectedAnchor ][ 'colorR' ]
        anchorColorG = self.annotationsDict[ self.selectedAnchor ][ 'colorG' ]
        anchorColorB = self.annotationsDict[ self.selectedAnchor ][ 'colorB' ]
        
        if self.IsNotNone( self.selectedAnchor ) and ( anchorColorR != color.R or anchorColorG != color.G or anchorColorB != color.B ):
            self.annotationsDict[ self.selectedAnchor ][ 'colorR' ] = color.R
            self.annotationsDict[ self.selectedAnchor ][ 'colorG' ] = color.G
            self.annotationsDict[ self.selectedAnchor ][ 'colorB' ] = color.B

            self.UpdateSingleAnnotation( self.selectedAnchor, self.boxIdDict[ self.selectedAnchor ] )
        
    def MoveAnnotation( self, src, dest ):
        temp = self.annotationsDict[ dest ]
        self.annotationsDict[ dest ] = self.annotationsDict[ src ]
        self.annotationsDict[ src ] = temp
        self.UpdateAllAnnotations()
    
    def AddAnnotation( self ):
        text = self.GetValue( "DraftAnnotationTextBox" )

        if self.IsNotNone( self.selectedAnchor ) and text != self.annotationsDict[ self.selectedAnchor ][ 'text' ]:
            previousText = self.annotationsDict[ self.selectedAnchor ][ 'text' ]
            self.annotationsDict[ self.selectedAnchor ][ 'text' ] = text

            if previousText == "":
                self.UpdateSingleAnnotation( self.selectedAnchor, self.boxIdDict[ self.selectedAnchor ] )
            else:
                self.UpdateAllAnnotations()
            
        self.textField.setFocus()

    def CreateAnnotationBoxes( self ):
        for anchor in self.annotations:
            box = DraftImageRegion( 0, 0, 0, 0, self.boxIdDict[ anchor ], self.scene, anchor )
            self.scene.addItem( box )
            self.boxList.append( box )
            box.updateText( self.annotationsDict[ anchor ][ 'text' ], framePaddingSize )

    def ResetAnnotationBoxPositions( self ):
        if len( self.boxList ) > 0:
            boxWidth = int( self.img.width * 0.33 )
            boxHeight = int( self.img.height * 0.08 )
            boxMargin = self.img.width - ( boxWidth * 3 )

            bottomBoxStartYPos = self.img.height * 0.92
            centerBoxStartXPos = boxWidth + ( boxMargin / 2 )
            rightBoxStartXPos = self.img.width - boxWidth

            for i in range( 0, 6 ):
                self.boxList[ i ].setRect( 0, 0, boxWidth, boxHeight )

            self.boxList[ self.boxIdDict[ 'NorthWest' ] ].setBoxPos( 0, 0 )
            self.boxList[ self.boxIdDict[ 'NorthCenter' ] ].setBoxPos( centerBoxStartXPos, 0 )
            self.boxList[ self.boxIdDict[ 'NorthEast' ] ].setBoxPos( rightBoxStartXPos, 0 )
            self.boxList[ self.boxIdDict[ 'SouthWest' ] ].setBoxPos( 0, bottomBoxStartYPos )
            self.boxList[ self.boxIdDict[ 'SouthCenter' ] ].setBoxPos( centerBoxStartXPos, bottomBoxStartYPos )
            self.boxList[ self.boxIdDict[ 'SouthEast' ] ].setBoxPos( rightBoxStartXPos, bottomBoxStartYPos )

    def AnchorBoxChanged( self ):
        # This will occur when the position dropdown is manually changed.
        if self.GetValue( "DraftAnchor" ) != self.selectedAnchor:
            self.previousAnchor = self.selectedAnchor
            self.selectedAnchor = self.GetValue( "DraftAnchor" )
            self.ChangeSelectedFont()
            self.textField.setFocus()

        self.HighlightBox()

    def HighlightBox( self ):
        self.boxList[ self.boxIdDict[ self.previousAnchor ] ].setPen( QPen( QColor( 255, 255, 255 ) ) )
        self.boxList[ self.boxIdDict[ self.selectedAnchor ] ].setPen( QPen( QColor( 0, 255, 0 ) ) )
        self.SetValue( "DraftAnnotationTextBox", self.annotationsDict[ self.selectedAnchor ][ 'text' ] )

    def ChangeSelectedFont( self ):
        redColor = self.annotationsDict[ self.selectedAnchor ][ 'colorR' ]
        greenColor = self.annotationsDict[ self.selectedAnchor ][ 'colorG' ]
        blueColor = self.annotationsDict[ self.selectedAnchor ][ 'colorB' ]

        if "" not in ( redColor, greenColor, blueColor ):
            self.fontColorControl.setTheValue( QColor( redColor, greenColor, blueColor ) )
        else:
            self.fontColorControl.setTheValue( QColor( 255, 255, 255 ) )
    
    def AdjustZoom( self ):
        zoomFactor = float( self.zoomSlider.value() )/100
        self.imageViewer.zoomImage( zoomFactor )

    def UpdatedZoomSlider(self):
        zoom = self.imageViewer.transform().m11()
        self.zoomSlider.setValue( int( zoom * 100 + 0.5 ) )
        
    def AddSymbolPressed( self, *args ):
        if len( args ) > 0:
            button = args[0]
            self.newSymbolMenu.exec_( button.mapToGlobal( QPoint( 0, 0 ) ) )
        self.textField.setFocus()
    
    def AddFrameClicked( self ):
        text = self.GetValue( "DraftAnnotationTextBox" )
        text = text + "$frame"
        self.SetValue( "DraftAnnotationTextBox", text )
        self.AddAnnotation()
        
    def AddTimeClicked( self ):
        text = self.GetValue( "DraftAnnotationTextBox" )
        text = text + "$time"
        self.SetValue( "DraftAnnotationTextBox", text )
        self.AddAnnotation()
        
    def AddDimensionsClicked( self ):
        text = self.GetValue( "DraftAnnotationTextBox" )
        text = text + "$dimensions"
        self.SetValue( "DraftAnnotationTextBox", text )
        self.AddAnnotation()
        
    def AddLogoClicked( self ):
        filePath = self.ShowOpenFileBrowser( ClientUtils.GetCurrentUserHomeDirectory(), "All Files (*.*)" )
        if filePath:
            text = "$logo( " + filePath + " )"
            self.SetValue( "DraftAnnotationTextBox", text )
            self.AddAnnotation()
    
    @pyqtSlot( int, int, bool )
    def MousePressed( self, x, y, middleButtonPressed ):
        if middleButtonPressed:
            self.panning = True
            self.cursorPanCurr = QPoint( x, y )
            QApplication.setOverrideCursor( QCursor( Qt.SizeAllCursor ) )
        else:
            self.previousAnchor = self.selectedAnchor
            self.selectedAnchor = self.GetAnchorFromPosition( self.img, x, y )
            self.HighlightBox()
            self.ChangeSelectedFont()
        
    @pyqtSlot( int, int, bool )
    def MouseMoved( self, x, y, leftButtonPressed ):
        anchor = self.GetAnchorFromPosition( self.img, x, y )

        if leftButtonPressed:
            if anchor == self.selectedAnchor:
                self.movingBox = True

            if self.IsNotNone( self.previousAnchor ) and not self.IsNotNone( anchor ):
                QApplication.setOverrideCursor( QCursor( Qt.ForbiddenCursor ) )
            else:
                QApplication.setOverrideCursor( QCursor( Qt.ClosedHandCursor ) )
        elif self.panning:
            scrollBarMaxHeight = self.imageViewer.verticalScrollBar().maximum()
            scrollBarMaxWidth = self.imageViewer.horizontalScrollBar().maximum()
            self.imageViewer.horizontalScrollBar().setValue( self.imageViewer.horizontalScrollBar().value() - ( ( x - self.cursorPanCurr.x() ) * scrollBarMaxWidth / self.img.width ) )
            self.imageViewer.verticalScrollBar().setValue( self.imageViewer.verticalScrollBar().value() - ( ( y - self.cursorPanCurr.y() ) * scrollBarMaxHeight / self.img.height ) )
            self.cursorPanCurr = QPoint( x, y )
        else:
            QApplication.setOverrideCursor( QCursor( Qt.ArrowCursor ) )
        
    @pyqtSlot( int, int )
    def MouseReleased( self, x, y ):
        self.previousAnchor = self.selectedAnchor
        self.selectedAnchor = self.GetAnchorFromPosition( self.img, x, y )

        # Determine if we need to move annotations
        if self.movingBox:
            self.movingBox = False

            if self.previousAnchor != self.selectedAnchor and self.IsNotNone( self.previousAnchor ) and self.IsNotNone( self.selectedAnchor ):
                self.MoveAnnotation( self.previousAnchor, self.selectedAnchor )
        elif self.panning:
            self.panning = False

        self.SetValue( "DraftAnchor", self.selectedAnchor )
        self.textField.setFocus()
        QApplication.setOverrideCursor( QCursor( Qt.ArrowCursor ) )
        self.HighlightBox()
    
    @pyqtSlot( int )
    def WheelScrolled( self, x ):
        temp = self.zoomSlider.value()
        self.zoomSlider.setValue( temp + x * 10 )
        self.AdjustZoom()
               
    def GetAnchorFromPosition( self, img, x, y ):
        vertical = None
        horizontal = None
        if y >= 0 and y <= img.height * 0.08:
            vertical = 'North'
        elif y >= img.height * 0.92 and y <= img.height:
            vertical = 'South'
        else:
            vertical = None
        
        if vertical:
            if x >= 0 and x <= img.width * 0.33:
                horizontal = 'West'
            elif x >= img.width * 0.33 and x <= img.width * 0.66:
                horizontal = 'Center'
            elif x >= img.width * 0.66 and x <= img.width:
                horizontal = 'East'
            else:
                horizontal = None
                
        if vertical and horizontal:
            return vertical + horizontal
        else:
            return self.selectedAnchor
    
    def IsNotNone( self, anchor ):
        return self.annotationsDict[anchor] != None

    def FitViewport( self ):
        self.imageViewer.fitInView( self.imageViewer.sceneRect(), Qt.KeepAspectRatio );
        self.imageViewer.zoomUpdated.emit()

    def KeepFit( self ):
        self.resetZoomBtn.setEnabled( not self.keepFitBtn.isChecked() )
        self.fitViewportBtn.setEnabled( not self.keepFitBtn.isChecked() )
        self.zoomSlider.setEnabled( not self.keepFitBtn.isChecked() )
        self.imageViewer.enableWheel = not self.keepFitBtn.isChecked()

        if self.keepFitBtn.isChecked():
            self.FitViewport()

    def ResetZoom( self ):
        self.zoomSlider.setValue( 100 )

    def resizeEvent( self, e ):
        super( DraftAnnotationDialog, self ).resizeEvent( e )
        if self.keepFitBtn.isChecked():
            self.FitViewport()

    def SaveAnnotations( self ):
        try:
            dialog = QFileDialog( self.parent, "Save Annotations", "", "Text Files (*.txt)" )
            dialog.setFileMode( QFileDialog.AnyFile )
            result = dialog.exec_()

            if result != 0:
                selectedFilePath = dialog.selectedFiles()[0]
                extension = os.path.splitext( selectedFilePath )[1]

                if extension == "":
                    selectedFilePath += ".txt"
                    extension = os.path.splitext( selectedFilePath )[1]

                if extension == ".txt":
                    selectedFile = open( selectedFilePath, 'w' )
                    selectedFile.write( json.dumps( scriptDialog.annotationsDict ) )
                    selectedFile.close()
        except Exception as e:
            print(e)

    def LoadAnnotations( self ):
        try:
            dialog = QFileDialog( self.parent, "Load Annotations", "", "Text Files (*.txt)" )
            dialog.setFileMode( QFileDialog.ExistingFile )
            result = dialog.exec_()

            if result != 0:
                selectedFilePath = dialog.selectedFiles()[0]

                if os.path.exists( selectedFilePath ):
                    selectedFile = open( selectedFilePath, 'r' )
                    annotationsString = selectedFile.read()
                    selectedFile.close()
                    self.annotationsDict = json.loads( annotationsString )
                    self.UpdateUI()
                    self.ChangeSelectedFont()
        except ValueError:
            self.ShowMessageBox( "An error occurred when loading the annotation string. Please try recreating the file before loading again.", "Warning" )
        except Exception as e:
            print(e)
