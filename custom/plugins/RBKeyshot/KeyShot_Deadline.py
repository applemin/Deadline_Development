#-
# ==========================================================================
# Copyright (C) 2018 - 2020 Ocean Cloud Rendering. and/or its licensors.  All
# rights reserved.
#
# The coded instructions, statements, computer programs, and/or related
# material (collectively the "Data") in these files contain unpublished
# information proprietary to RenderShare. ("RenderShare") and/or its
# licensors, which is protected by Canadian federal copyright
# law and by international treaties.
#
# The Data is provided for use exclusively by You. You have the right
# to use, and incorporate this Data into other products for
# purposes authorized by the RenderShare software license agreement,
# without fee.
#
# The copyright notices in the Software and this entire statement,
# including the above license grant, this restriction and the
# following disclaimer, must be included in all copies of the
# Software, in whole or in part, and all derivative works of
# the Software, unless such copies or derivative works are solely
# in the form of machine-executable object code generated by a
# source language processor.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
# RenderShare DOES NOT MAKE AND HEREBY DISCLAIMS ANY EXPRESS OR IMPLIED
# WARRANTIES INCLUDING, BUT NOT LIMITED TO, THE WARRANTIES OF
# NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A PARTICULAR
# PURPOSE, OR ARISING FROM A COURSE OF DEALING, USAGE, OR
# TRADE PRACTICE. IN NO EVENT WILL RenderShare AND/OR ITS LICENSORS
# BE LIABLE FOR ANY LOST REVENUES, DATA, OR PROFITS, OR SPECIAL,
# DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES, EVEN IF RenderShare
# AND/OR ITS LICENSORS HAS BEEN ADVISED OF THE POSSIBILITY
# OR PROBABILITY OF SUCH DAMAGES.
#
# ==========================================================================
#+

import os
import json
import sys


# get data file path and load data fom json file
s_data_file = os.environ['DEADLINE_KEYSHOT_INFO']
with open(s_data_file, 'r') as json_data:
    d_data = json.load(json_data)
print("Data File Path : ", s_data_file)


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

    s_file_path = d_data["DAT_SCENE_FILE_NAME"]
    s_file_p = d_data["new_scene_path"]
    s_new_file_p = d_data["new_scene_temp_path"]

    b_reload = not any([d_data["DAT_MULTI_CAMERA_RENDERING"], d_data["DAT_MULTI_TASK_RENDERING"]])
    print('s_new_file_path ={}'.format(s_file_p))
    print('s_new_temp_file_path ={}'.format(s_new_file_p))

    print("Contents of DEADLINE_KEYSHOT_INFO received in KeyShot :")
    for parameter, value in sorted(d_data.items()):
        print('{0:35}{1:35}{2:35}'.format(str(parameter), str(type(value)), str(value)))

    lux.openFile(s_file_p)

    if d_data["DAT_CAMERA"]:
        lux.setCamera(d_data["DAT_CAMERA"])
    if any(d_data["DAT_MODEL_SET"]):
        lux.setModelSets(d_data["DAT_MODEL_SET"])
    if d_data["DAT_STUDIO"]:
        lux.setActiveStudio(d_data["DAT_STUDIO"])
        target_image_style = lux.getActiveImageStyle()
        print('Set active image style: %s' % target_image_style)
        lux.setActiveImageStyle(target_image_style)


    lux.setAnimationFrame(d_data["DAT_START_FRAME"])

    if b_reload:
        print("\t Reloading temp scene: %s" % s_new_file_p)
        lux.saveFile(s_new_file_p)
        lux.openFile(s_new_file_p)

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
        print('{0:35}{1:35}{2:35}'.format(str(parameter), str(type(value)), str(value)))

    for frame in range(d_data["DAT_START_FRAME"], d_data["DAT_END_FRAME"]+1):
        corrected_frame = int(frame) - 1 if not int(frame) <= 0 else int(frame)
        print("Rendering Frame : %s Corrected Frame : %s" % (frame, corrected_frame))
        print(d_data["DAT_OUTPUT_FILE_NAME"], type(d_data["DAT_OUTPUT_FILE_NAME"]))
        print(d_data["DAT_WIDTH"], type(d_data["DAT_WIDTH"]))
        print(d_data["DAT_HEIGHT"], type(d_data["DAT_HEIGHT"]))

        lux.setAnimationFrame(corrected_frame)

        if d_data["version"] == 8:
            print("Rendering started with KeyShot%s" % d_data["version"])
            lux.renderImage(path=d_data["DAT_OUTPUT_FILE_NAME"].replace("%d", str(corrected_frame)),
                            width=d_data["DAT_WIDTH"],
                            height=d_data["DAT_HEIGHT"],
                            opts=renderOptions)

        elif d_data["version"] == 9:
            print("Rendering started with KeyShot%s" % d_data["version"])
            lux.renderImage(path=d_data["DAT_OUTPUT_FILE_NAME"].replace("%d", str(corrected_frame)),
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
    exit()

main()
