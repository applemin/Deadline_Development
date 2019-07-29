from __future__ import print_function

import io
import re


def CheckAndUpdateEnvVar( fileData, key, value ):
    settingEnvRegex = re.compile( '\A\s*%s\s*=' % key, re.IGNORECASE )
    containsKeyRegex = re.compile( '\A\s*%s\s*=.*\$%s' % (key, key), re.IGNORECASE )
    containsValueRegex = re.compile( '\A\s*%s\s*=.*%s' % (key, value), re.IGNORECASE )
    containsDefaultRegex = re.compile( '\A\s*%s\s*=.*\&' % key )

    if fileData:
        for index, line in enumerate( fileData ):
            line = line.replace( '\\', '/' ).strip()
            # Search for environment variable definition in file

            # Check if modifying current env
            if settingEnvRegex.search( line ):

                # Search if current value is there
                if not containsValueRegex.search( line ):
                    envLine = line.replace( '"', '' ).split( '=' )
                    line = '%s = "%s;%s"' % ( envLine[0].strip(), value, envLine[1].strip() )

                # Search if the env contains itself ie. 'HOUDINI_PATH = $HOUDINI_PATH;...'
                if not containsKeyRegex.search( line ):
                    envLine = line.replace( '"', '' ).split( '=' )
                    line = '%s = "$%s;%s"' % ( envLine[0].strip(), key, envLine[1].strip() )

                # Search if default value is there
                if not containsDefaultRegex.search( line ):
                    envLine = line.replace( '"', '' ).split( '=' )
                    line = '%s = "%s;&"' % (envLine[ 0 ].strip(), envLine[ 1 ].strip())

                fileData[ index ] = line.strip() + '\n'
                break
        else:
            # File is not currently setting the env, so append to the file
            fileData.append( '%s%s = "$%s;%s;&"' % ( '\n', key, key, value ) )
    else:
        # File is empty
        fileData = [ '%s = "$%s;%s;&"' % ( key, key, value ) ]

    return fileData

def __main__( filename, submitterPath ):
    # To prevent regex from breaking when searching for this path :(
    submitterPath = submitterPath.replace( '\\', '/' ).rstrip( '/' )

    fileData = []
    try:
        with io.open( filename, 'r', encoding='utf-8' ) as fileHandle:
            fileData = fileHandle.readlines()
    except:
        pass

    fileData = CheckAndUpdateEnvVar( fileData, 'HOUDINI_PATH', submitterPath )
    fileData = CheckAndUpdateEnvVar( fileData, 'HOUDINI_MENU_PATH', submitterPath )

    with io.open( filename, 'w', encoding='utf-8' ) as fileHandle:
        print( fileData )
        fileHandle.write( ''.join( fileData ) )