# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import io
import xml.etree.ElementTree as ET

class ParseError( Exception ):
    pass

class Config( object ):
    """
    A class to handle parsing settings from Modo's Config Files.
    Note: Modo Config Files are only updated when Modo exits so we can cache settings
    """

    def __init__( self, textContents ):
        """
        Creates a config object from the xml contents of a config file
        :param textContents: the xml contents of a config file.
        """

        self.cache = {}

        try:
            self.configContents = ET.fromstring( textContents.encode( "utf-8" ) )
        except ET.ParseError as e:
            raise ParseError( e.message )

    @classmethod
    def fromFile( cls, filePath, encoding=None ):
        """
        Creates a config object from the path to a config file.
        :param filePath: the path to the config file.
        :param encoding: optional argument to specify the encoding of the file if known. (defaults to system prefered encoding
        :return: A new config Object
        """
        # Modo uses the Systems preferred encoding (ANSI on english windows) and includes characters that exist in ANSI but are not valid in UTF-8 such as the euro
        # As such we must read in the file using the Default encoding and then convert everything to utf-8 so it is in the format we expect and can use from then on.
        with io.open( filePath, encoding=encoding ) as configHandle:
            textContents = configHandle.read()

        return cls( textContents )

    @property
    def path_aliases( self ):
        """
        Parses all path aliases contained in the configuration options
        :return: a dictionary of path aliases
        """

        #Check the Cache first since this will not change

        try:
            return self.cache["path_aliases"]
        except KeyError:
            pass

        aliases = {}
        for alias in self.configContents.findall( "./atom[@type='PathAliases']/hash[@type='Alias']" ):
            key = alias.get( "key" )
            try:
                aliasPath = alias.find( "./atom[@type='Path']" ).text
            except (AttributeError, IndexError):
                # This path alias does not have a to path defined so we can ignore it
                continue

            aliases[key] = aliasPath

        self.cache["path_aliases"] = aliases
        return aliases