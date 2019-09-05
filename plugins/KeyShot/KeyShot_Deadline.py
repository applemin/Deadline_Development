import os
import time
import shutil
import json

def load_data_file(JasonFile):
    with open(JasonFile, 'r') as JsonData:
        DataDict = json.load(JsonData)
        return DataDict


INFO_FILE_LINE_DESC_PATH = os.environ['DEADLINE_KEYSHOT_INFO']
print (INFO_FILE_LINE_DESC_PATH)
DATA_DICT = load_data_file(INFO_FILE_LINE_DESC_PATH)

INFO_FILE_LINE_DESC = {
    "DAT_SCENE_FILE_NAME":              DATA_DICT["DAT_SCENE_FILE_NAME"],
    "DAT_TEMP_SCENE_BASE_FILE_NAME":    DATA_DICT["DAT_TEMP_SCENE_BASE_FILE_NAME"],
    "DAT_CAMERA":                       DATA_DICT["DAT_CAMERA"],
    "DAT_START_FRAME":                  DATA_DICT["DAT_START_FRAME"],
    "DAT_END_FRAME":                    DATA_DICT["DAT_END_FRAME"],
    "DAT_WIDTH":                        DATA_DICT["DAT_WIDTH"],
    "DAT_HEIGHT":                       DATA_DICT["DAT_HEIGHT"],
    "DAT_OUTPUT_FILE_NAME":             DATA_DICT["DAT_OUTPUT_FILE_NAME"],
    "DAT_RENDER_LAYERS":                DATA_DICT["DAT_RENDER_LAYERS"],
    "DAT_INCLUDE_ALPHA":                DATA_DICT["DAT_INCLUDE_ALPHA"],
    "DAT_OVERRIDE_RENDER_PASSES":       DATA_DICT["DAT_OVERRIDE_RENDER_PASSES"],
    "DAT_MAXIMUM_TIME":                 DATA_DICT["DAT_MAXIMUM_TIME"],
    "DAT_PROGRESSIVE_MAX_SAMPLES":      DATA_DICT["DAT_PROGRESSIVE_MAX_SAMPLES"],
    "DAT_ADVANCED_MAX_SAMPLES":         DATA_DICT["DAT_ADVANCED_MAX_SAMPLES"],
    "DAT_RAY_BOUNCES":                  DATA_DICT["DAT_RAY_BOUNCES"],
    "DAT_ANTI_ALIASING":                DATA_DICT["DAT_ANTI_ALIASING"],
    "DAT_SHADOWS":                      DATA_DICT["DAT_SHADOWS"],
    "DAT_QUALITY_TYPE":                 DATA_DICT["DAT_QUALITY_TYPE"]}
        
HOME_PATH = os.path.join(os.environ['HOMEPATH'], 'Desktop', 'Temp')
SCENE_FILE_PATH = INFO_FILE_LINE_DESC["DAT_SCENE_FILE_NAME"]
NEW_SCENE_FILE_NAME = os.path.basename(SCENE_FILE_PATH)
NEW_TEMP_SCENE_FILE_NAME = INFO_FILE_LINE_DESC["DAT_TEMP_SCENE_BASE_FILE_NAME"]

def valid_temp_folder():

    if os.path.exists(HOME_PATH):
        print('Temp folder has already been created.')
        return True
    else:
        try:
            os.makedirs(HOME_PATH)
            print('Temp folder created successfully.')
            return True
        except:
            print('Temp folder could not be created.')
            return False

def dir_update_check(NETWORK_FILE_DIR, DESTINATION_PATH):

    NETWORK_FILE_DIR_LIST = os.listdir(NETWORK_FILE_DIR)
    DESTINATION_PATH_LIST = os.listdir(DESTINATION_PATH)

    if len(NETWORK_FILE_DIR_LIST) == len(DESTINATION_PATH_LIST) or len(NETWORK_FILE_DIR_LIST) < len(DESTINATION_PATH_LIST):
        print('No directory update required.')
        return True
    else:
        print('Directory update required.')
        return False

def file_transfer(SCENE_FILE_PATH):

    NETWORK_FILE_DIR = os.path.dirname(SCENE_FILE_PATH)
    NETWORK_DIR_NAME = os.path.basename(NETWORK_FILE_DIR)
    DESTINATION_PATH = os.path.join(os.environ['HOMEPATH'], 'Desktop', 'Temp', NETWORK_DIR_NAME)
    NEW_SCENE_PATH = os.path.join(DESTINATION_PATH, NEW_SCENE_FILE_NAME)
    NEW_SCENE_TEMP_PATH = os.path.join(DESTINATION_PATH, NEW_TEMP_SCENE_FILE_NAME)

    if os.path.exists(DESTINATION_PATH) and dir_update_check(NETWORK_FILE_DIR, DESTINATION_PATH):
        print('Render folder has already been transferred , returning immediately .')
        return NEW_SCENE_PATH, NEW_SCENE_TEMP_PATH
    elif os.path.exists(DESTINATION_PATH) and not dir_update_check(NETWORK_FILE_DIR, DESTINATION_PATH):
        shutil.rmtree(DESTINATION_PATH)
        print('Render folder has been removed.')

    if valid_temp_folder():
        try:
            shutil.copytree(NETWORK_FILE_DIR, DESTINATION_PATH)
            print('Render folder transferred successfully.')
        except:
            print('Render folder could not be transferred.')
    else:
        print('File transfer failed')

    return NEW_SCENE_PATH, NEW_SCENE_TEMP_PATH

def main(scene_file_path, get_new_file_path):

    print ("Contents of DEADLINE_KEYSHOT_INFO received in KeyShot :")

    for parameter, value in INFO_FILE_LINE_DESC.items():
        print ("\t[%s] %s=%s" % (type(value), parameter, value))

    lux.openFile(scene_file_path)

    if INFO_FILE_LINE_DESC["DAT_CAMERA"] != "":
        lux.setCamera(INFO_FILE_LINE_DESC["DAT_CAMERA"])

    lux.setAnimationFrame(INFO_FILE_LINE_DESC["DAT_START_FRAME"])
    lux.saveFile(get_new_file_path)
    lux.openFile(get_new_file_path)

    _renderOptions = lux.getRenderOptions()
    _renderOptions.setAddToQueue(False)

    _renderOptions.setOutputRenderLayers(INFO_FILE_LINE_DESC["DAT_RENDER_LAYERS"])
    _renderOptions.setOutputAlphaChannel(INFO_FILE_LINE_DESC["DAT_INCLUDE_ALPHA"])

    # overrideRenderPasses = INFO_FILE_LINE_DESC["DAT_OVERRIDE_RENDER_PASSES"]

    # if overrideRenderPasses:
    #     renderPassOptions = [
    #         ("IncludeDiffusePass", "setOutputDiffusePass"),
    #         ("IncludeReflectionPass", "setOutputReflectionPass"),
    #         ("IncludeClownPass", "setOutputClownPass"),
    #         ("IncludeLightingPass", "setOutputDirectLightingPass"),
    #         ("IncludeRefractionPass", "setOutputRefractionPass"),
    #         ("IncludeDepthPass", "setOutputDepthPass"),
    #         ("IncludeGIPass", "setOutputIndirectLightingPass"),
    #         ("IncludeShadowPass", "setOutputShadowPass"),
    #         ("IncludeGeometricNormalPass", "setOutputNormalsPass"),
    #         ("IncludeCausticsPass", "setOutputCausticsPass"),
    #         ("IncludeAOPass", "setOutputAmbientOcclusionPass")]


    # try:
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeDiffusePass"])
    #     renderOptions.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeReflectionPass"])
    #     renderOptions.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeClownPass"])
    #     renderOptions.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeLightingPass"])
    #     renderOptions.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeRefractionPass"])
    #     renderOptions.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeDepthPass"])
    #     renderOptions.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeGIPass"])
    #     renderOptions.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeShadowPass"])
    #     renderOptions.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeGeometricNormalPass"])
    #     renderOptions.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeCausticsPass"])
    #     renderOptions.setOutputDiffusePass(INFO_FILE_LINE_DESC["DAT_IncludeAOPass"])
    #
    # except AttributeError:
    #     print( 'Failed to set render pass attributes')

    print ("Set Quality Mode to : %s" % INFO_FILE_LINE_DESC["DAT_QUALITY_TYPE"])
    if INFO_FILE_LINE_DESC["DAT_QUALITY_TYPE"] == "Maximum Time":
        _renderOptions.setMaxTimeRendering(INFO_FILE_LINE_DESC["DAT_MAXIMUM_TIME"])
    elif INFO_FILE_LINE_DESC["DAT_QUALITY_TYPE"] == "Maximum Samples":
        _renderOptions.setMaxSamplesRendering(INFO_FILE_LINE_DESC["DAT_PROGRESSIVE_MAX_SAMPLES"])
    else:
        try:
            _renderOptions.setAdvancedRendering(INFO_FILE_LINE_DESC["DAT_ADVANCED_MAX_SAMPLES"])
            _renderOptions.setRayBounces(INFO_FILE_LINE_DESC["DAT_RAY_BOUNCES"])
            _renderOptions.setAntiAliasing(INFO_FILE_LINE_DESC["DAT_ANTI_ALIASING"])
            _renderOptions.setShadowQuality(INFO_FILE_LINE_DESC["DAT_SHADOWS"])
        except AttributeError:
            print('Failed to set advanced quality attribute')

    for frame in range(INFO_FILE_LINE_DESC["DAT_START_FRAME"], INFO_FILE_LINE_DESC["DAT_END_FRAME"]+1 ):
        print ("Rendering Frame : %s" % frame)
        lux.setAnimationFrame(frame)
        lux.renderImage(path=INFO_FILE_LINE_DESC["DAT_OUTPUT_FILE_NAME"].replace("%d", str(frame)),
                        width=INFO_FILE_LINE_DESC["DAT_WIDTH"],
                        height=INFO_FILE_LINE_DESC["DAT_HEIGHT"],
                        renderOptions=_renderOptions)
        print("Rendered Image: %s" % INFO_FILE_LINE_DESC["DAT_OUTPUT_FILE_NAME"].replace("%d", str(frame)))

    os.remove(get_new_file_path)
    print ('Job Completed')
    exit()

GET_NEW_FILE_PATH, GET_NEW_TEMP_FILE_PATH = file_transfer(SCENE_FILE_PATH)
print('GET_NEW_FILE_PATH ={}'.format(GET_NEW_FILE_PATH))
print('GET_NEW_TEMP_FILE_PATH ={}'.format(GET_NEW_TEMP_FILE_PATH))

if GET_NEW_FILE_PATH:
    print('Starting new workflow...')
    main(GET_NEW_FILE_PATH, GET_NEW_TEMP_FILE_PATH)
else:
    print('Switching to old workflow...')
    main(SCENE_FILE_PATH)

