#-*- coding: utf-8 -*-
"""
A file that contains a helper class for generating Tile Rendering Tiles which can be used across multiple submitters.
"""
from __future__ import print_function

try:
    intTypes = ( int, long )
except NameError:
    intTypes = ( int, )

class TileGenerator( object ):
    ORIGINS = [
        'bottom-left',
        'top-left',
        # We don't currently support top-right/bottom-right origins
    ]

    def __init__( self, tilesInX, tilesInY, width, height, origin='bottom-left', returnSize=False, exclusiveRanges=True ):
        """
        This class maps region numbers to coordinates of tiles in an image, for use with Deadline's Tile Rendering Features.
        :param tilesInX: Number of tiles in the Horizontal direction
        :param tilesInY: Number of tiles in the Vertical direction
        :param width: The width of the image ( in pixels )
        :param height: The height of the image (in pixels )
        :param origin: Specifies the location of the origin co-ordinates. This can be overridden when generating Tiles. Defaults to 'bottom-left'. Value must be in TileGenerator.ORIGINS.
        :param returnSize: If enabled the width and Height of the tile will be returned instead of the absolute coordinates. This can be overridden when generating Tiles.
        :param exclusiveRanges:  If enabled the coordinates will use semi exclusive ranges [minX-maxX) and [minY-maxY), otherwise it will use inclusive ranges [minX-maxX] and [minY-maxY]. This can be overridden when generating Tiles.
        """

        if not all( isinstance( num, intTypes ) for num in ( tilesInX, tilesInY, width, height ) ):
            raise TypeError( "TilesInX, TilesInY, Width and Height must all be integers" )

        if any( num < 1 for num in ( tilesInX, tilesInY )):
            raise ValueError( "Both tilesInX and tilesInY must be positive integers" )

        if origin not in self.ORIGINS:
            raise ValueError( 'Origin "{0}" is not supported. Use one of the following: {1}.'.format( origin, ", ".join( self.ORIGINS ) ) )

        self.tilesInX = tilesInX
        self.tilesInY = tilesInY
        self.width = width
        self.height = height

        self.origin = origin
        self.returnSize = returnSize
        self.exclusiveRanges = exclusiveRanges

        #Internal properties for determining the size of Regions
        self.deltaX, self.widthRemainder = divmod( self.width, self.tilesInX )
        self.deltaY, self.heightRemainder = divmod( self.height, self.tilesInY )

        if any( num < 1 for num in ( self.deltaX, self.deltaY )):
            raise ValueError( "Both width and height must be positive integers that are larger than the number of tiles in the respective direction." )

    def __getitem__(self, item):
        return self.getTile( item )

    def __len__( self ):
        return self.tilesInX * self.tilesInY

    def getEachTile( self, origin=None, returnSize=None, exclusiveRanges=None ):
        """
        A generator function for retrieving each Region
        :param origin: This is an override to the class variable. Specifies the location of the origin co-ordinates. Value must be in TileGenerator.ORIGINS.
        :param returnSize: This is an override to the class variable. If enabled the width and Height of the tile will be returned instead of the absolute coordinates.
        :param exclusiveRanges: This is an override to the class variable. If enabled the coordinates will use semi exclusive ranges [minX-maxX) and [minY-maxY), otherwise it will use inclusive ranges [minX-maxX] and [minY-maxY].
        :return: Tuples of the form ( minX, (maxX or size of X), minY, ( maxY or size of Y)
        """
        for regionNum in range( len( self ) ):
            yield( self.getTile( regionNum, origin, returnSize, exclusiveRanges=exclusiveRanges ))

    def getTile( self, tileNum, origin=None, returnSize=None, exclusiveRanges=None ):
        """
        Retrieves an individual region using the specified region number.
        :param tileNum: The index of the region, or tuple (x,y) of the location to get the coordinates from.
        :param origin: This is an override to the class variable. Specifies the location of the origin co-ordinates. Value must be in TileGenerator.ORIGINS.
        :param returnSize: This is an override to the class variable. If enabled the width and height of the tile will be returned instead of the absolute coordinates.
        :param exclusiveRanges: This is an override to the class variable.  If enabled the coordinates will use semi exclusive ranges [minX-maxX) and [minY-maxY), otherwise it will use inclusive ranges [minX-maxX] and [minY-maxY].
        :return: Tuples of the form ( minX, (maxX or size of X), minY, ( maxY or size of Y)
        """
        if isinstance( tileNum, tuple ):
            try:
                x, y = tileNum
            except ValueError:
                raise TypeError( "Invalid region number (%s). The region number must be an integer or a tuple of 2 integers" % tileNum )
            if not all( isinstance( val, intTypes ) for val in ( x, y ) ):
                raise TypeError( "Invalid region number (%s). The region number must be an integer or a tuple of 2 integers" % tileNum )

            if not ( 0 <= x < self.tilesInX and 0 <= y < self.tilesInY ):
                raise ValueError( "Invalid region number (%s, %s). X must be between 0 and %s, and Y must be between 0 and %s, inclusive." % ( x, y, self.tilesInX -1, self.tilesInY -1 ) )

        elif isinstance( tileNum, intTypes ):
            if not 0 <= tileNum < len( self ):
                raise ValueError( "Invalid region number (%s). The region number must be between 0 and %s, inclusive." % (tileNum, len( self ) - 1) )

            y, x = divmod( tileNum, self.tilesInX )
        else:
            raise TypeError( "Invalid region number (%s). The region number must be an integer or a tuple of 2 integers" % tileNum )

        if origin is None:
            origin = self.origin

        if returnSize is None:
            returnSize = self.returnSize

        if exclusiveRanges is None:
            exclusiveRanges = self.exclusiveRanges

        minX = self.deltaX * x
        maxX = self.deltaX * (x + 1)
        minY = self.deltaY * y
        maxY = self.deltaY * (y + 1)

        if x == self.tilesInX - 1:
            maxX += self.widthRemainder
        if y == self.tilesInY - 1:
            maxY += self.heightRemainder

        # Default origin is 'bottom-left'
        if origin == "top-left":
            minY, maxY = self.height - maxY, self.height - minY

        if returnSize:
            return minX, ( maxX - minX ), minY, ( maxY - minY )
        else:
            if not exclusiveRanges:
                maxX -= 1
                maxY -= 1

            return minX, maxX, minY, maxY
