from __future__ import print_function
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class DraftImageViewer( QGraphicsView ):
    mousePressedSignal = pyqtSignal( int, int, bool )
    mouseMovedSignal = pyqtSignal( int, int, bool )
    mouseReleasedSignal = pyqtSignal( int, int )
    wheelScrolledSignal = pyqtSignal( int )
    zoomUpdated = pyqtSignal()
    
    def __init__( self, scene ):
        super( DraftImageViewer, self ).__init__( scene )
        self.enableWheel = True
        self.zoom = 1
        self.startImageHeight = 480
        self.startImageWidth = 640

        self.backgroundImage = QImage( self.startImageWidth, self.startImageHeight, QImage.Format_ARGB32 )
        self.backgroundImage.fill( 0 )
        rectangle = QRectF( 0, 0, self.startImageWidth, self.startImageHeight )
        self.scene().setSceneRect( rectangle )

    def mousePressEvent( self, event ):
        middleButtonPressed = ( event.buttons() == Qt.MiddleButton )
        eventPoint = QPoint( event.x(), event.y() )
        mousePoint = self.mapToScene( eventPoint )
        self.mousePressedSignal.emit( mousePoint.x(), mousePoint.y(), middleButtonPressed )
        
    def mouseMoveEvent( self, event ):
        leftButtonPressed = ( event.buttons() == Qt.LeftButton )
        eventPoint = QPoint( event.x(), event.y() )
        mousePoint = self.mapToScene( eventPoint )
        self.mouseMovedSignal.emit( mousePoint.x(), mousePoint.y(), leftButtonPressed )

    def mouseReleaseEvent( self, event ):
        eventPoint = QPoint( event.x(), event.y() )
        mousePoint = self.mapToScene( eventPoint )
        self.mouseReleasedSignal.emit( mousePoint.x(), mousePoint.y() )

    def wheelEvent( self, event ):
        if self.enableWheel:
            self.wheelScrolledSignal.emit( event.angleDelta().y() / 120 ) 
        
    def setImage( self, backgroundImage ):
        self.backgroundImage = backgroundImage
        imageAsByteArray = self.backgroundImage.ToBytes()
        self.backgroundImage = QImage( imageAsByteArray, self.backgroundImage.width, self.backgroundImage.height, QImage.Format_ARGB32 )

        painter = QPainter()
        rectangle = QRectF( 0, 0, self.backgroundImage.width(), self.backgroundImage.height() )
        self.scene().setSceneRect( rectangle )
        self.drawBackground( painter, rectangle )

    def drawBackground( self, painter, rectangle ):
        try:
            rectangle = QRectF()
            rectangle.setRect( 0, 0, self.backgroundImage.width(), self.backgroundImage.height() )
            painter.drawImage( rectangle, self.backgroundImage )
            painter.setPen( QPen( QColor( 0, 0, 255 ) ) )
            painter.drawRect( rectangle )
        except:
            print(traceback.format_exc())
    
    def zoomImage( self, zoom ):
        self.zoom = zoom
        zoomFactor = self.zoom/self.transform().m11();
        self.scaleView( zoomFactor )

    def scaleView( self, zoomFactor ):
        factor = self.transform().scale( zoomFactor, zoomFactor ).mapRect( QRectF( 0, 0, 1, 1 ) ).width()
        
        if factor > 5 or factor < 0.01:
            return
            
        self.scale( zoomFactor, zoomFactor )
        self.zoomUpdated.emit()