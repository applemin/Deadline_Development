import os

from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *
from Deadline.Plugins import *
from Deadline.Scripting import *
from FranticX.Processes import *

from Deadline.Plugins import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
  return SceneParser()

######################################################################
## This is the function that Deadline calls when the plugin is no
## longer in use so that it can get cleaned up.
######################################################################
def CleanupDeadlinePlugin( deadlinePlugin ):
  deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for MyPlugin.
######################################################################
class SceneParser (DeadlinePlugin):

  def __init__(self):
    self.LogInfo("Inheriting From Deadline Plugin")



######################################################################
## GET/SET global variables
######################################################################

# class SceneParser(DeadlinePlugin):
#     def __init__(self):
#         self.LogInfo("Inheritin From Deadline Plugin")
#
# def getScenePath():
#
#     DeadlinePlugin.LogInfo("    Constructing file paths ")
#
#     baseScenePath = DeadlinePlugin.GetPluginInfoEntry("SceneFile")
#     baseScenePath = baseScenePath.replace("\\", "/")
#     directoryPath, sceneFileName = os.path.split(baseScenePath)
#     constScenePath = os.path.join(directoryPath, "EDITED_" + sceneFileName)
#
#     DeadlinePlugin.LogInfo("    Original Scene Path : %s " % baseScenePath)
#     DeadlinePlugin.LogInfo("    Edited Scene Path : %s " % constScenePath)
#
#     return baseScenePath, constScenePath


# def targetDataBlock(FILE_PATH):
#
#     END_BLOCK_LINE_NUM = None
#     END_LINE_STRING = "luxappm.so"
#
#     # reading data file and inject lines to list
#     dataFile = open(FILE_PATH, "rb")
#     dataList = dataFile.readlines()
#     dataFile.close()
#
#     for counter, line in enumerate(dataList):
#         if END_LINE_STRING in line:
#             END_BLOCK_LINE_NUM = counter
#
#     return dataList[:END_BLOCK_LINE_NUM]
#
# def constructSceneFile(FILE_PATH, OUTPUT_PATH):
#
#     TARGET_DATA_BLOCK = targetDataBlock(FILE_PATH)
#
#     outFile = open(OUTPUT_PATH, "wb+")
#     outFile.writelines(TARGET_DATA_BLOCK)
#     #outFile.writelines(MAIN_FILE)
#     outFile.close()
#
# #constructSceneFile(FILE_PATH, OUTPUT_PATH)
#
#
# # dataFile = open(FILE_PATH, "rb")
# # i = 0
# #
# # for line in dataFile:
# #     if i <= 10:
# #         print(line)
# #         i += 1
#
# from functools import partial
#
# with open(FILE_PATH, "rb") as f_in:
#
#     part_read = partial(f_in.read, 50000000*5)
#     iterator = iter(part_read, b'')
#
#     #outFile = open(OUTPUT_PATH, "wb+")
#
#     for index, block in enumerate(iterator, start=1):
#         #block = process_block(block)    # process block data
#         with open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_{}.bip".format(index), "wb+") as f_out:
#             f_out.write(block)
#
# outFile = open(OUTPUT_PATH, "wb+")
#
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_1.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_2.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_3.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_4.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_5.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_6.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_7.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_8.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_9.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_10.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_11.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_12.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_13.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_14.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_15.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_16.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_17.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_18.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_19.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_20.bip", "rb").readlines())
# outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_21.bip", "rb").readlines())
#
#
# outFile.close()

def __main__( *args ):
    print "Running KeyShot Pre Script"

    InstanceCalss = SceneParser()
