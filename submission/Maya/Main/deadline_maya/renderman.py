import maya.cmds as cmds
from rfm2.api import strings as rfmStrings
from rfm2.api import nodes as rfmNodes
from rfm2.api import displays as rfmDisplays
import rfm2.config as rfmConfig

def get_camera_shape( camera ):
    """
    Retrieves a cameras's shape node which contains the cameras render settings.
    :param camera: the specified camera node.
    :return: The shape node associated with a camera
    """
    try:
        camshapes = cmds.listRelatives( camera, shapes=True )
    except ValueError:
        return camera
    return camshapes[ 0 ]


class StringConverter( rfmStrings.SceneStringConverter ):
    """
    A sub class of Rendermans SceneStringConverter which we will use evaluate strings.
    This varies from Rendermans Converter by overwriting the extension if using the Default Display Name.
    """
    def __init__(self, **kwargs):
        super( StringConverter, self ).__init__()
        self.update()

        self.setTokens( **kwargs)

    def setTokens( self, **tokens ):
        """
        Updates the internal expressions tokens with the provided values.
        :param tokens: a dictionary containing all tokens that are to be updated in the internal store.
        """

        try:
            if tokens["layer"] == "defaultRenderLayer":
                tokens[ "layer" ] = ""

            tokens["renderlayer"] = tokens[ "layer" ]
        except KeyError:
            pass

        try:
            camShape = get_camera_shape( tokens[ "camera" ] )
            tokens[ "camera" ] = camShape
        except KeyError:
            pass

        self.expr.tokens.update( tokens )

    def expand( self, string, display=None, frame=None ):
        """
        Expands all tokens within a string with the values stored in the internal storage.
        :param string: the string we want to replace the tokens in
        :param display: The Display (render element) that we need to pull settings from to evaluate all tokens
        :param frame: The Frame at which we want to evaluate tokens at
        :return: The evaluated string
        """
        if frame:
            self.expr.set_frame_context( frame )
        else:
            self.expr.set_frame_context( cmds.currentTime( q=True ) )
        if display:
            self.set_display( display )
        else:
            #if the display is the default display name then we must set the ext to exr since that is what renderman does under the hood.
            self.set_display( rfmConfig.DEFAULT_DISPLAY_NAME )
            self.expr.tokens[ "ext" ] = "exr"


        return self.expr.expand(string)

    @classmethod
    def evaluateString( cls, string, display=None,frame=None, **tokens ):
        """
        Creates a one time use converter and uses it to evaluate all tokens within a string.
        :param string: the string we want to replace the tokens in
        :param display: The Display (render element) that we need to pull settings from to evaluate all tokens
        :param frame: The Frame at which we want to evaluate tokens at
        :return: The evaluated string
        """
        converter = cls( **tokens )

        return converter.expand(string, display=display, frame=frame)

def get_output_prefix():
    """
    Retrieves Rendermans output prefix without resolving tokens.
    :return: rendermans Output prefix
    """
    rmanGlobals = rfmNodes.rman_globals()
    return cmds.getAttr( '%s.imageFileFormat' % rmanGlobals )

def get_output_directory():
    """
    Retrieves Rendermans output directory without resolving tokens
    :return: Rendermans output directory
    """
    rmanGlobals = rfmNodes.rman_globals()
    return cmds.getAttr( '%s.imageOutputDir' % rmanGlobals )

def get_render_elements():
    """
    Retrieves all render elements from Renderman that have at least one display channel and are enabled.
    :return: an array of strings containing the render elements
    """

    rmanDisplayInfo = rfmDisplays.get_displays()

    elements = []
    for displayName, display in rmanDisplayInfo["displays"].iteritems():
        #Always include the Default Display Name
        if displayName == rfmConfig.DEFAULT_DISPLAY_NAME or ( get_display_param( display, "enable" ) and len( get_display_param( display, "displayChannels" ) ) > 0 ):
            elements.append( displayName )

    return elements

def get_image_type( element ):
    """
    Returns the output format for a specific render element
    :param element: the render element we want to know the output format for.
    :return: the output format
    """
    if not element or element == rfmConfig.DEFAULT_DISPLAY_NAME:
        return "exr"

    rmanDisplayInfo = rfmDisplays.get_displays()
    driverNode = rmanDisplayInfo["displays"][element]["driverNode"]
    
    return rfmConfig.cfg().displayDriverExtensions[ cmds.nodeType( driverNode ) ]

def get_display_param( display, param ):
    """
    retrieves a parameters value from a provided display.
    :param display: The display that we want to get the value from
    :param param: the name of the parameter.
    :return:
    """
    try:
        return display["params"][param]["value"]
    except KeyError as e:
        return None

def get_rib_directory():
    """
    Retrieves Rendermans export directory without resolving tokens.
    :return: rendermans export directory
    """
    rmanGlobals = rfmNodes.rman_globals()
    return cmds.getAttr( '%s.ribOutputDir' % rmanGlobals )

def get_rib_prefix():
    """
    Retrieves Rendermans export prefix without resolving tokens.
    :return: rendermans export prefix
    """
    rmanGlobals = rfmNodes.rman_globals()
    return cmds.getAttr( '%s.ribFileFormat' % rmanGlobals )
