import os
from functools import partial

#######################################################################################################################
# GET/SET global variables
#######################################################################################################################

FILE_READ_ENCODING="rb"
FILE_WRITE_ENCODING="wb+"


class FileParser:

    def __init__(self, DeadlinePlugin):

        self.DeadlinePlugin = DeadlinePlugin
        self.baseScenePath, self.constScenePath, self.directoryPath = self.getScenePath()


    def getScenePath(self):

        self.DeadlinePlugin.LogInfo("    Constructing file paths ")

        baseScenePath = self.DeadlinePlugin.GetPluginInfoEntry("SceneFile")
        baseScenePath = baseScenePath.replace("\\", "/")
        directoryPath, sceneFileName = os.path.split(baseScenePath)
        directoryPath = directoryPath.replace("\\", "/")
        constScenePath = os.path.join(directoryPath, "EDITED_" + sceneFileName)
        constScenePath = constScenePath.replace("\\", "/")

        self.DeadlinePlugin.LogInfo("    Original Scene Path : %s " % baseScenePath)
        self.DeadlinePlugin.LogInfo("    Edited Scene Path : %s " % constScenePath)

        return baseScenePath, constScenePath, directoryPath


    # def getDataBlock(baseScenePath):
    #
    #     END_BLOCK_LINE_NUM = None
    #     END_LINE_STRING = "luxappm.so"
    #
    #     # reading data file and inject lines to list
    #     dataFile = open(baseScenePath, "rb")
    #     dataList = dataFile.readlines()
    #     dataFile.close()
    #
    #     for counter, line in enumerate(dataList):
    #         if END_LINE_STRING in line:
    #             END_BLOCK_LINE_NUM = counter
    #
    #     return dataList[:END_BLOCK_LINE_NUM]
    #
    # def createChunckDirectory(directoryPath):
    #
    #     DIR_STRING = "CHUNKED_FILES"
    #     chunkDirectory = os.path.join(directoryPath, DIR_STRING)
    #
    #     if os.path.exists(chunkDirectory):
    #         chunkDirectory = os.path.join(directoryPath, DIR_STRING).replace("\\", "/")
    #         print "Chunk Directory Exists : %s" % chunkDirectory
    #
    #     else:
    #         try:
    #             os.mkdir(chunkDirectory)
    #         except OSError:
    #             print ("Creation of the chunk directory %s failed : " % chunkDirectory)
    #         else:
    #             print ("Chunk Directory successfully created : %s " % chunkDirectory)
    #
    #     return chunkDirectory
    #
    #
    # def getChunkName(chunkIndex, chunkDirectory):
    #
    #     CHUNK_STRING = "Chunk_"
    #     CHUNK_EXTENSION = ".bip"
    #
    #     chunkNameString = os.path.join(chunkDirectory, CHUNK_STRING, chunkIndex + CHUNK_EXTENSION).replace("\\", "/")
    #     print "Chunk name string created : %s" % chunkNameString
    #     return chunkNameString
    #
    #
    # def constructSceneFile(baseScenePath, constScenePath, directoryPath):
    #
    #     FILE_READ_ENCODING = "rb"
    #     FILE_WRITE_ENCODING = "wb+"
    #
    #     TARGET_DATA_BLOCK = getDataBlock(baseScenePath)
    #     DATA_CHUNK_SIZE = 50000000*5
    #
    #     chunkDirectory = createChunckDirectory(directoryPath)
    #
    #     # constFile = open(constScenePath, "wb+")
    #     # constFile.writelines(TARGET_DATA_BLOCK)
    #     # constFile.writelines(baseScenePath)
    #     # constFile.close()
    #
    #     with open(baseScenePath, FILE_READ_ENCODING) as inputFile:
    #
    #         chunkRead = partial(inputFile.read, DATA_CHUNK_SIZE)
    #         iterator = iter(chunkRead, b'')
    #         chunkList = []
    #
    #         for INDEX, dataBlock in enumerate(iterator):
    #
    #             # TODO : block = process_block(block)    # process block data
    #             chunkName = getChunkName(INDEX, chunkDirectory)
    #             with open(chunkName, FILE_WRITE_ENCODING) as outputChunk:
    #                 outputChunk.write(dataBlock)
    #                 chunkList.append(chunkName)
    #                 print "New chunk written to disc : %s " % outputChunk
    #
    #     return assembleOutputFile(chunkList, constScenePath)
    #
    # def assembleOutputFile(chunkList, constScenePath):
    #
    #     outFile = open(constScenePath, FILE_WRITE_ENCODING)
    #
    #     for chunk in chunkList:
    #         print "Assembling : %s" % chunk
    #
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_1.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_2.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_3.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_4.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_5.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_6.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_7.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_8.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_9.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_10.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_11.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_12.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_13.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_14.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_15.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_16.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_17.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_18.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_19.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_20.bip", "rb").readlines())
    #         # outFile.writelines(open("C:/Users/hamed.MRB/Desktop/Python_NPP_Test/chunk/chunck_21.bip", "rb").readlines())
    #
    #     outFile.close()


def __main__(*args):

    print "Running KeyShot Pre Job Script"
    DeadlinePlugin = args[0]
    FileParser(DeadlinePlugin)




