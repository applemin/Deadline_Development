import mantra
import re
from os import path, makedirs
from optparse import OptionParser
from math import sqrt
from time import sleep

# generic get passed options and values
def get_tile_params():
    parser = OptionParser()
    parser.add_option('-n', action="store", dest="regionNumber")
    parser.add_option('-l', action="store", dest="regionLeft")
    parser.add_option('-r', action="store", dest="regionRight")
    parser.add_option('-b', action="store", dest="regionBottom")
    parser.add_option('-t', action="store", dest="regionTop")
    (options, args) = parser.parse_args()
    return options.__dict__

def filterCamera():
    """
    Renders a tile region onto a full res clear backplate with alpha.
    Note that we only use frameNumber here to display the currently rendering frame number.
    """
    tile_params = get_tile_params()
    
    regionLeft = tile_params["regionLeft"]
    regionRight = tile_params["regionRight"]
    regionBottom = tile_params["regionBottom"]
    regionTop = tile_params["regionTop"]
    
    regions = [ regionLeft, regionRight, regionBottom, regionTop ]
    
    mantra.setproperty('image:crop', regions )

def RightReplace( fullString, oldString, newString, occurences ):
    return newString.join( fullString.rsplit( oldString, occurences ) )
    
def filterPlane():
    """
    Reads the image plane filename and then alters it's name to include the co-ordinates
    for proper stitching tools.
    """
    # set to false if you want to simply render tiles within the target folder
    # and not into a 'tiles' sub-folder as stated below.
    tile_params = get_tile_params()
    
    current_tile = int(tile_params['regionNumber'])

    mantraFileName = mantra.property('image:filename')[0]
    baseFileName = path.basename(mantraFileName)
    filePath = path.dirname(mantraFileName)

    if "/" in filePath:
        separator = "/"
    else:
        separator = "\\"

    paddedNumberRegex = re.compile( "([0-9]+)", re.IGNORECASE )
    matches = paddedNumberRegex.findall( baseFileName )
    if matches != None and len( matches ) > 0:
        paddingString = matches[ len( matches ) - 1 ]
        padding = str(current_tile)
        padding = "_tile"+padding+"_" + paddingString
        fileName = filePath + separator + RightReplace( baseFileName, paddingString, padding, 1 )
    else:
        splitFilename = path.splitext(baseFileName)
        padding = str(current_tile)
        fileName = filePath + separator + splitFilename[0]+"_tile"+padding+"_"+splitFilename[1]

    mantra.setproperty('plane:planefile', fileName)    