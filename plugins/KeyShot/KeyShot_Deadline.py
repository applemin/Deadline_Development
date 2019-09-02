import os
import time
import shutil

INFO_FILE_LINE_DESC = "INFO_FILE_LINE_DESC"


HOME_PATH = os.path.join(os.environ['HOMEPATH'], 'Desktop', 'Temp')
SCENE_FILE_PATH ="%s" % INFO_FILE_LINE_DESC["ENV_SCENE_FILE_NAME"]
NEW_SCENE_FILE_NAME = os.path.basename(SCENE_FILE_PATH)
NEW_TEMP_SCENE_FILE_NAME ="%s" % ["ENV_TEMP_SCENE_BASE_FILE_NAME"]

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

    for key, value in INFO_FILE_LINE_DESC.items():
        print ("\t%s=%s" % (key, value))

    lux.openFile(scene_file_path)

    if INFO_FILE_LINE_DESC["ENV_CAMERA"] != "":
        lux.setCamera(INFO_FILE_LINE_DESC["ENV_CAMERA"])

        lux.setAnimationFrame(INFO_FILE_LINE_DESC["ENV_START_FRAME"])
        width = INFO_FILE_LINE_DESC["ENV_WIDTH"]
        height = INFO_FILE_LINE_DESC["ENV_HEIGHT"]
        lux.saveFile(get_new_file_path)
        lux.openFile(get_new_file_path)
        path = INFO_FILE_LINE_DESC["ENV_OUTPUT_FILE_NAME"]

        opts = lux.getRenderOptions()
        opts.setAddToQueue(False)

        opts.setOutputRenderLayers(INFO_FILE_LINE_DESC["ENV_RENDER_LAYERS"])
        opts.setOutputAlphaChannel(INFO_FILE_LINE_DESC["ENV_INCLUDE_ALPHA"])

    # overrideRenderPasses = INFO_FILE_LINE_DESC["ENV_OVERRIDE_RENDER_PASSES"]

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
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeDiffusePass"])
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeReflectionPass"])
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeClownPass"])
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeLightingPass"])
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeRefractionPass"])
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeDepthPass"])
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeGIPass"])
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeShadowPass"])
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeGeometricNormalPass"])
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeCausticsPass"])
    #     opts.setOutputDiffusePass(INFO_FILE_LINE_DESC["ENV_IncludeAOPass"])
    #
    # except AttributeError:
    #     print( 'Failed to set render pass attributes')

    if INFO_FILE_LINE_DESC["ENV_QUALITY_TYPE"] == "Maximum Time":
        opts.setMaxTimeRendering(INFO_FILE_LINE_DESC["ENV_MAXIMUM_TIME"])
    elif INFO_FILE_LINE_DESC["ENV_QUALITY_TYPE"] == "Maximum Samples":
        opts.setMaxSamplesRendering(INFO_FILE_LINE_DESC["ENV_PROGRESSIVE_MAX_SAMPLES"])
    else:

        # advancedRenderingOptions = [
        #     ("AdvancedMaxSamples", "setAdvancedRendering", int, "16"),
        #     ("RayBounces", "setRayBounces", int, "6"),
        #     ("AntiAliasing", "setAntiAliasing", int, "1"),
        #     ("Shadows", "setShadowQuality", float, "1")]

        try:

            opts.setAdvancedRendering(INFO_FILE_LINE_DESC["ENV_ADVANCED_MAX_SAMPLES"])
            opts.setAdvancedRendering(INFO_FILE_LINE_DESC["ENV_RAY_BOUNCES"])
            opts.setAdvancedRendering(INFO_FILE_LINE_DESC["ENV_ANTI_ALIASING"])
            opts.setAdvancedRendering(INFO_FILE_LINE_DESC["ENV_SHADOWS"])

        except AttributeError:
               print( 'Failed to set advaned quality attribute')

        for frame in range( INFO_FILE_LINE_DESC["ENV_START_FRAME"], INFO_FILE_LINE_DESC["ENV_END_FRAME"] ):
            renderPath = path
            renderPath =  renderPath.replace(frame)
            lux.setAnimationFrame(frame )
            lux.renderImage(path = renderPath, width = width, height = height, opts = opts)
            print("Rendered Image: %s" % renderPath)

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

