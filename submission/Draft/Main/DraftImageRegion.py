from __future__ import print_function
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import datetime
import re

class DraftImageRegion( QGraphicsRectItem ):

	def __init__( self, x=0, y=0, width=50, height=50, id=0, scene=None, anchor="", parent=None ):
		super( DraftImageRegion, self ).__init__( parent )
		self.id = id
		self.anchor = anchor
		self.width = width
		self.height = height
		self.x = x
		self.y = y
		self.logoImagePath = ""
		self.logoImagePixmap = None

		self.setRect( 0, 0, width, height )
		self.setBrush( QBrush() )
		self.setPen( QPen( QColor( 255, 255, 255 ) ) )
		self.setFlag( QGraphicsItem.ItemIsMovable )
		self.setFlag( QGraphicsItem.ItemIsSelectable )
		self.setFlag( QGraphicsItem.ItemSendsGeometryChanges )
		self.setAcceptHoverEvents( True )

		app = QApplication.instance()
		self.selectedColor = app.palette().highlight().color()
		self.textItem = QGraphicsTextItem()

		self.setPos( x, y )
		self.textItem.setPos( x, y )
		self.scene = scene
		self.scene.addItem( self.textItem )

		document = QTextDocument()
		document.setDocumentMargin( 0 )
		self.textItem.setDocument( document )

		self.mousePressedSignal = pyqtSignal( int, int )

	def setBoxPos( self, x, y ):
		self.x = x
		self.y = y
		self.setPos( x, y )

		if self.logoImagePixmap:
			self.setLogoPos()
		else:
			self.setTextPos()

	def updateText( self, text, framePaddingSize ):
		if text.startswith( "$logo" ):
			try:
				match = re.match( "^(\$logo)\((.*)\)$", text )
				imagePath = QImage( str( match.group( 2 ).strip() ) )
				if self.logoImagePath != imagePath:
					if self.logoImagePixmap:
						self.scene.removeItem( self.logoImagePixmap )
						
					self.logoImagePath = QImage( str( match.group( 2 ).strip() ) )
					pixmap = QPixmap.fromImage( self.logoImagePath )
					self.logoImagePixmap = QGraphicsPixmapItem( pixmap )
					self.scene.addItem( self.logoImagePixmap )
					self.setLogoPos()
					self.textItem.setPlainText( "" )
			except:
				warningMsg = "Failed to read logo from file. No logo will be added. The required format $logo( path//to//logo ) might be incorrect."
				print(warningMsg)
		else:
			frame = framePaddingSize * "#"
			text = text.replace( "$frame", frame )
			text = text.replace( "$time", datetime.datetime.now().strftime( "%m/%d/%Y %I:%M %p" ) )
			text = text.replace( "$dimensions", str( int( self.scene.width() ) ) + 'x' + str( int( self.scene.height() ) ) )
			self.textItem.setPlainText( text )
			self.setTextPos()

			if self.logoImagePixmap:
				self.scene.removeItem( self.logoImagePixmap )
				self.logoImagePixmap = None
				self.logoImagePath = ""

	def updateFont( self, colorR, colorG, colorB ):
		if colorR != "" and colorB != "" and colorG != "":
			self.textItem.setDefaultTextColor( QColor( colorR, colorG, colorB ) )

	def setTextPos( self ):
		# Initialize the font to be the same as Draft's.
		pixelSize = int( self.scene.height() * 0.045 )
		font = QFont( "Source Sans Pro", 1, QFont.Normal )
		font.setPixelSize( pixelSize )
		self.textItem.setFont( font )

		# Note: The 0.01 value is roughly similar to Draft's padding.
		textItemHeight = self.textItem.boundingRect().height()
		textItemWidth = self.textItem.boundingRect().width()
		textSideMargin = int( self.scene.height() * 0.01 )

		# Replicate the anchor positions made by Draft.
		if self.anchor == "NorthWest":
			self.textItem.setPos( self.x + textSideMargin, self.y )
		elif self.anchor == "NorthCenter":
			self.textItem.setPos( ( self.scene.width() / 2 ) - ( textItemWidth / 2 ), self.y )
		elif self.anchor == "NorthEast":
			self.textItem.setPos( self.scene.width() - textItemWidth - textSideMargin, self.y )
		elif self.anchor == "SouthWest":
			self.textItem.setPos( self.x + textSideMargin, self.scene.height() - textItemHeight )
		elif self.anchor == "SouthCenter":
			self.textItem.setPos( ( self.scene.width() / 2 ) - ( textItemWidth / 2 ), self.scene.height() - textItemHeight )
		elif self.anchor == "SouthEast":
			self.textItem.setPos( self.scene.width() - textItemWidth - textSideMargin, self.scene.height() - textItemHeight )

	def setLogoPos( self ):
		logoBoundingRect = self.logoImagePixmap.boundingRect()
		logoHeight = int( self.scene.height() * 0.045 )
		logoScale = logoHeight / logoBoundingRect.height()
		self.logoImagePixmap.setScale( logoScale )
		self.logoImagePixmap.setOpacity( 0.3 )

		scaledLogoHeight = logoBoundingRect.height() * logoScale
		scaledLogoWidth = logoBoundingRect.width() * logoScale

		# Replicate the anchor positions made by Draft.
		if self.anchor == "NorthWest":
			self.logoImagePixmap.setPos( self.x, self.y )
		elif self.anchor == "NorthCenter":
			self.logoImagePixmap.setPos( ( self.scene.width() / 2 ) - ( scaledLogoWidth / 2 ), self.y )
		elif self.anchor == "NorthEast":
			self.logoImagePixmap.setPos( self.scene.width() - scaledLogoWidth, self.y )
		elif self.anchor == "SouthWest":
			self.logoImagePixmap.setPos( self.x, self.scene.height() - scaledLogoHeight )
		elif self.anchor == "SouthCenter":
			self.logoImagePixmap.setPos( ( self.scene.width() / 2 ) - ( scaledLogoWidth / 2 ), self.scene.height() - scaledLogoHeight )
		elif self.anchor == "SouthEast":
			self.logoImagePixmap.setPos( self.scene.width() - scaledLogoWidth, self.scene.height() - scaledLogoHeight )