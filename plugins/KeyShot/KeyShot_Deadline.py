import os
import shutil
import time
import sys
import subprocess
import json

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
    s_file_p, s_new_file_p = file_transfer(s_file_path)
    print('s_new_file_path ={}'.format(s_file_p))
    print('s_new_temp_file_path ={}'.format(s_new_file_p))

    print("Contents of DEADLINE_KEYSHOT_INFO received in KeyShot :")
    for parameter, value in d_data.items():
        print("\t %s  [%s]  = %s" % (parameter, type(value), value))

    lux.openFile(s_file_p)

    if d_data["DAT_CAMERA"] != "":
        lux.setCamera(d_data["DAT_CAMERA"])

    lux.setAnimationFrame(d_data["DAT_START_FRAME"])

    if not d_data["DAT_MULTI_TASK_RENDERING"]:
        lux.saveFile(s_new_file_p)
        lux.openFile(s_new_file_p)

    renderOptions = lux.getRenderOptions()
    renderOptions.setAddToQueue(False)

    renderOptions.setOutputRenderLayers(d_data["DAT_RENDER_LAYERS"])
    renderOptions.setOutputAlphaChannel(d_data["DAT_INCLUDE_ALPHA"])


    print ("Set Quality Mode to : %s" % d_data["DAT_QUALITY_TYPE"])
    if d_data["DAT_QUALITY_TYPE"] == "Maximum Time":
        renderOptions.setMaxTimeRendering(d_data["DAT_MAXIMUM_TIME"])
    elif d_data["DAT_QUALITY_TYPE"] == "Maximum Samples":
        renderOptions.setMaxSamplesRendering(d_data["DAT_PROGRESSIVE_MAX_SAMPLES"])
    else:
        try:
            renderOptions.setAdvancedRendering(d_data["DAT_ADVANCED_MAX_SAMPLES"])
            renderOptions.setRayBounces(d_data["DAT_RAY_BOUNCES"])
            renderOptions.setAntiAliasing(d_data["DAT_ANTI_ALIASING"])
            renderOptions.setShadowQuality(d_data["DAT_SHADOWS"])
        except AttributeError:
            print('Failed to set advanced quality attribute')

    for frame in range(d_data["DAT_START_FRAME"], d_data["DAT_END_FRAME"]+1):
        print ("Rendering Frame : %s" % frame)
        lux.setAnimationFrame(frame)
        lux.renderImage(path=d_data["DAT_OUTPUT_FILE_NAME"].replace("%d", str(frame)),
                        width=d_data["DAT_WIDTH"],
                        height=d_data["DAT_HEIGHT"],
                        opts=renderOptions)
        print("Rendered Image: %s" % d_data["DAT_OUTPUT_FILE_NAME"].replace("%d", str(frame)))

    if not d_data["DAT_MULTI_TASK_RENDERING"]:
        os.remove(s_new_file_p)
    print('Job Completed')
    exit()


main()
