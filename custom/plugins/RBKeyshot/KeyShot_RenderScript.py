import os
import time
import shutil

HOME_PATH = os.path.join(os.environ["HOMEPATH"], "Desktop", "Temp")
SCENE_FILE_PATH = "A:/RenderShot_Dir/Files/ctCmh6931TKgvV2/made_to_travel_black_rev4_92630339406526/made_to_travel_black_rev4.bip"
NEW_SCENE_FILE_NAME = os.path.basename(SCENE_FILE_PATH)

NEW_TEMP_SCENE_FILE_NAME = ""
def valid_temp_folder():
    if os.path.exists(HOME_PATH):
        print("Temp folder has already been created.")
        return True
    else:
        try:
            os.makedirs(HOME_PATH)
            print("Temp folder created successfully.")
            return True
        except:
            print("Temp folder could not be created.")
            return False


def dir_update_check(NETWORK_FILE_DIR, DESTINATION_PATH):
    NETWORK_FILE_DIR_LIST = os.listdir(NETWORK_FILE_DIR)
    DESTINATION_PATH_LIST = os.listdir(DESTINATION_PATH)

    if len(NETWORK_FILE_DIR_LIST) == len(DESTINATION_PATH_LIST)or len(NETWORK_FILE_DIR_LIST) < len(DESTINATION_PATH_LIST):
        print("No directory update required.")
        return True
    else:
        print("Directory update required.")
        return False

def file_transfer(SCENE_FILE_PATH):
    NETWORK_FILE_DIR = os.path.dirname(SCENE_FILE_PATH)
    NETWORK_DIR_NAME = os.path.basename(NETWORK_FILE_DIR)
    DESTINATION_PATH = os.path.join(os.environ["HOMEPATH"], "Desktop", "Temp", NETWORK_DIR_NAME)
    NEW_SCENE_PATH = os.path.join(DESTINATION_PATH, os.path.basename(SCENE_FILE_PATH))
    if os.path.exists(DESTINATION_PATH)and dir_update_check(NETWORK_FILE_DIR, DESTINATION_PATH):
        print("Render folder has already been transferred , returning immediately .")
        return NEW_SCENE_PATH
    elif os.path.exists(DESTINATION_PATH) and not dir_update_check(NETWORK_FILE_DIR, DESTINATION_PATH):
        shutil.rmtree(DESTINATION_PATH)
        print("Render folder has been removed.")


    if valid_temp_folder() :
        try:
            shutil.copytree(NETWORK_FILE_DIR, DESTINATION_PATH)
            print("Render folder transferred successfully.")
        except:
            print("Render folder could not be transferred.")
    else:
        print("File transfer failed")

    return NEW_SCENE_PATH


def main(scene_file_path):
    lux.openFile(scene_file_path)
    lux.setCamera("Camera 2")
    lux.setAnimationFrame( 0 )
    lux.pause
    lux.setAnimationFrame( 0 )
    lux.unpause
    lux.setAnimationFrame( 0 )
    lux.saveFile( "A:/RenderShot_Dir/Files/ctCmh6931TKgvV2/made_to_travel_black_rev4_92630339406526/made_to_travel_black_rev4_1561004076_Camera 2_0_.bip")
    lux.openFile( "A:/RenderShot_Dir/Files/ctCmh6931TKgvV2/made_to_travel_black_rev4_92630339406526/made_to_travel_black_rev4_1561004076_Camera 2_0_.bip")
    path = "A:/Test_Output/made_to_travel_black_rev4_1560962403_%d.tif"
    width = 1920
    height = 1080
    opts = lux.getRenderOptions()
    opts.setAddToQueue(False)
    opts.setOutputRenderLayers(False)
    opts.setOutputAlphaChannel(False)
    try:
        opts.setOutputDiffusePass(False)
    except AttributeError:
       print( "Failed to set render pass: output_diffuse_pass" )
    try:
        opts.setOutputReflectionPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_reflection_pass" )
    try:
        opts.setOutputClownPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_clown_pass" )
    try:
        opts.setOutputDirectLightingPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_direct_lighting_pass" )
    try:
        opts.setOutputRefractionPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_refraction_pass" )
    try:
        opts.setOutputDepthPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_depth_pass" )
    try:
        opts.setOutputIndirectLightingPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_indirect_lighting_pass" )
    try:
        opts.setOutputShadowPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_indirect_lighting_pass" )
    try:
        opts.setOutputNormalsPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_normals_pass" )
    try:
        opts.setOutputCausticsPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_caustics_pass" )
    try:
        opts.setOutputShadowPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_shadow_pass" )
    try:
        opts.setOutputAmbientOcclusionPass(False)
    except AttributeError:
       print( "Failed to set render pass: output_ambient_occlusion_pass" )
    try:
        opts.setAdvancedRendering( 38 )
    except AttributeError:
       print( "Failed to set render option: advanced_samples" )
    try:
        opts.setGlobalIllumination( 1.0 )
    except AttributeError:
       print( "Failed to set render option: engine_global_illumination" )
    try:
        opts.setRayBounces( 14 )
    except AttributeError:
       print( "Failed to set render option: engine_ray_bounces" )
    try:
        opts.setPixelBlur( 1.5 )
    except AttributeError:
       print( "Failed to set render option: engine_pixel_blur" )
    try:
        opts.setAntiAliasing( 3 )
    except AttributeError:
       print( "Failed to set render option: engine_anti_aliasing" )
    try:
        opts.setDofQuality( 3 )
    except AttributeError:
       print( "Failed to set render option: engine_dof_quality" )
    try:
        opts.setShadowQuality( 4.47200012207 )
    except AttributeError:
       print( "Failed to set render option: engine_shadow_quality" )
    try:
        opts.setCausticsQuality( 0.0 )
    except AttributeError:
       print( "Failed to set render option: engine_caustics_quality" )
    try:
        opts.setSharpShadows( True )
    except AttributeError:
       print( "Failed to set render option: engine_sharp_shadows" )
    try:
        opts.setSharperTextureFiltering( True )
    except AttributeError:
       print( "Failed to set render option: engine_sharper_texture_filtering" )
    try:
        opts.setGlobalIlluminationCache( True )
    except AttributeError:
       print( "Failed to set render option: engine_global_illumination_cache" )
    for frame in range( 0, 1 ):
        renderPath = path
        renderPath =  renderPath.replace( "%d", str(frame) )
        lux.setAnimationFrame( frame )
        lux.renderImage(path = renderPath, width = width, height = height, opts = opts)
        print("Rendered Image: "+renderPath)
    os.remove( "A:/RenderShot_Dir/Files/ctCmh6931TKgvV2/made_to_travel_black_rev4_92630339406526/made_to_travel_black_rev4_1561004076_Camera 2_0_.bip")
    print ('Job Completed')
    exit()

GET_NEW_FILE_PATH = file_transfer(SCENE_FILE_PATH)
if GET_NEW_FILE_PATH:
    main(GET_NEW_FILE_PATH)
else:
    main(SCENE_FILE_PATH)

