import os
import shutil
import json
import sys


# get data file path and load data fom json file
s_data_file = os.environ['DEADLINE_KEYSHOT_INFO']
with open(s_data_file, 'r') as json_data:
    d_data = json.load(json_data)
print("Data File Path : ", s_data_file)

s_home_path = os.path.join(os.environ['HOMEPATH'], 'Desktop', 'Temp')
s_file_path = d_data["DAT_SCENE_FILE_NAME"]
s_file_name = os.path.basename(s_file_path)
s_temp_file_name = d_data["DAT_TEMP_SCENE_BASE_FILE_NAME"]


def valid_temp_folder():

    if os.path.exists(s_home_path):
        print('Temp folder has already been created.')
        return True
    else:
        try:
            os.makedirs(s_home_path)
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


def file_transfer(s_file_path):

    NETWORK_FILE_DIR = os.path.dirname(s_file_path)
    NETWORK_DIR_NAME = os.path.basename(NETWORK_FILE_DIR)
    DESTINATION_PATH = os.path.join(os.environ['HOMEPATH'], 'Desktop', 'Temp', NETWORK_DIR_NAME)
    NEW_SCENE_PATH = os.path.join(DESTINATION_PATH, s_file_name)
    NEW_SCENE_TEMP_PATH = os.path.join(DESTINATION_PATH, s_temp_file_name)

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


def main():

    l_advanced_render_options = ["setAdvancedRendering",
                                 "setGlobalIllumination",
                                 "setRayBounces",
                                 "setAntiAliasing",
                                 "setShadowQuality",
                                 "setCausticsQuality",
                                 "setSharpShadows",
                                 "setSharperTextureFiltering",
                                 "setGlobalIlluminationCache"]

    l_render_pass_options = ["setOutputRenderLayers",
                             "setOutputAlphaChannel",
                             "setOutputDiffusePass",
                             "setOutputReflectionPass",
                             "setOutputClownPass",
                             "setOutputDirectLightingPass",
                             "setOutputRefractionPass",
                             "setOutputDepthPass",
                             "setOutputIndirectLightingPass",
                             "setOutputNormalsPass",
                             "setOutputCausticsPass",
                             "setOutputShadowPass",
                             "setOutputAmbientOcclusionPass"]

    s_file_p, s_new_file_p = file_transfer(s_file_path)
    b_reload = not any([d_data["DAT_MULTI_CAMERA_RENDERING"], d_data["DAT_MULTI_TASK_RENDERING"]])
    print('s_new_file_path ={}'.format(s_file_p))
    print('s_new_temp_file_path ={}'.format(s_new_file_p))

    print("Contents of DEADLINE_KEYSHOT_INFO received in KeyShot :")
    for parameter, value in sorted(d_data.items()):

        print('{0:40}{1:40}{2:40}'.format(str(parameter), str(type(value)), str(value)))

    lux.openFile(s_file_p)
    lux.pause()
    if d_data["DAT_CAMERA"]: lux.setCamera(d_data["DAT_CAMERA"])
    if any(d_data["DAT_MODEL_SET"]): lux.setModelSets(d_data["DAT_MODEL_SET"])
    lux.setAnimationFrame(d_data["DAT_START_FRAME"])

    if b_reload:
        print("\t Reloading temp scene: %s" % s_new_file_p)
        lux.saveFile(s_new_file_p)
        lux.openFile(s_new_file_p)
    lux.pause()

    renderOptions = lux.getRenderOptions()
    renderOptions.setAddToQueue(False)
    for pass_setting in l_render_pass_options:
        try:
            eval("renderOptions.%s(%s)" % (pass_setting, d_data[pass_setting]))
            print('Set render pass attribute: %s to %s' % (pass_setting, d_data[pass_setting]))
        except AttributeError:
            print('Failed to set render pass attribute: %s' % pass_setting)

    if d_data["DAT_REGION_DATA"]:
        renderOptions.setRegion(d_data["DAT_REGION_DATA"])
    if d_data["DAT_QUALITY_TYPE"] == "maximum_time":
        renderOptions.setMaxTimeRendering(d_data["DAT_MAXIMUM_TIME"])
    elif d_data["DAT_QUALITY_TYPE"] == "maximum_samples":
        renderOptions.setMaxSamplesRendering(d_data["DAT_PROGRESSIVE_MAX_SAMPLES"])
    else:
        for quality_setting in l_advanced_render_options:
            try:
                eval("renderOptions.%s(%s)" % (quality_setting, d_data[quality_setting]))
                print('Set custom quality attribute: %s to %s' % (quality_setting, d_data[quality_setting]))
            except AttributeError:
                print('Failed to set custom quality attribute: %s' % quality_setting)

    for parameter, value in sorted(renderOptions.getDict().items()):
        print('{0:40}{1:40}{2:40}'.format(str(parameter), str(type(value)), str(value)))

    for frame in range(d_data["DAT_START_FRAME"], d_data["DAT_END_FRAME"]+1):
        print("Rendering Frame : %s" % frame)
        print(d_data["DAT_OUTPUT_FILE_NAME"], type(d_data["DAT_OUTPUT_FILE_NAME"]))
        print(d_data["DAT_WIDTH"], type(d_data["DAT_WIDTH"]))
        print(d_data["DAT_HEIGHT"], type(d_data["DAT_HEIGHT"]))

        lux.setAnimationFrame(frame)

        if d_data["version"] == 8:
            print("Rendering started with KeyShot%s" % d_data["version"])
            lux.renderImage(path=d_data["DAT_OUTPUT_FILE_NAME"].replace("%d", str(frame)),
                            width=d_data["DAT_WIDTH"],
                            height=d_data["DAT_HEIGHT"],
                            opts=renderOptions)

        elif d_data["version"] == 9:
            print("Rendering started with KeyShot%s" % d_data["version"])
            lux.renderImage(path=d_data["DAT_OUTPUT_FILE_NAME"].replace("%d", str(frame)),
                            width=d_data["DAT_WIDTH"],
                            height=d_data["DAT_HEIGHT"],
                            opts=renderOptions,
                            format=int(d_data["output_id"]))
        else:
            print("Rendering started with KeyShot%s" % d_data["version"])
            return sys.exit("KeyShot version : %s is not supported." % d_data["output_id"])

        print("Rendered Image: %s" % d_data["DAT_OUTPUT_FILE_NAME"].replace("%d", str(frame)))

    if b_reload:
        print("\t Removing temp scene: %s" % s_new_file_p)
        os.remove(s_new_file_p)
    print('Job Completed')
    exit()


main()
