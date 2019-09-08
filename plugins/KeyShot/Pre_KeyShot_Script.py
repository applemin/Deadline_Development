import os
from functools import partial

#######################################################################################################################
# GET/SET global variables
#######################################################################################################################


class FileParser:

    FILE_READ_ENCODING="rb"
    FILE_WRITE_ENCODING="wb+"

    baseScenePath   = None
    constScenePath  = None
    directoryPath   = None
    chunkDirectory  = None
    chunkList       = []

    DIR_STRING = "CHUNKED_FILES"

    DATA_CHUNK_SIZE = 50000000 * 5


    def __init__(self, DeadlinePlugin):

        self.DeadlinePlugin         = DeadlinePlugin
        self.getScenePath           = self.getScenePath()
        self.createChunkDirectory   = self.createChunkDirectory()
        self.constScenePath         = self.constScenePath()
        self.assembleOutputFile     = self.assembleOutputFile()


    def getScenePath(self):

        self.DeadlinePlugin.LogInfo("    Constructing file paths ")

        self.baseScenePath = self.DeadlinePlugin.GetPluginInfoEntry("SceneFile")
        self.baseScenePath = self.baseScenePath.replace("\\", "/")

        self.directoryPath, sceneFileName = os.path.split(self.baseScenePath)
        self.directoryPath = self.directoryPath.replace("\\", "/")

        self.constScenePath = os.path.join(self.directoryPath, "EDITED_" + sceneFileName)
        self.constScenePath = self.constScenePath.replace("\\", "/")

        self.DeadlinePlugin.LogInfo("    Original Scene Path : %s " % self.baseScenePath)
        self.DeadlinePlugin.LogInfo("    Edited Scene Path : %s " % self.constScenePath)
        self.DeadlinePlugin.LogInfo("    Base Directory Path : %s " % self.directoryPath)

        return self.baseScenePath, self.constScenePath, self.constScenePath

    def createChunkDirectory(self):

        chunkDirectory = os.path.join(self.directoryPath, self.DIR_STRING)

        if os.path.exists(chunkDirectory):
            self.chunkDirectory = os.path.join(self.directoryPath, self.DIR_STRING).replace("\\", "/")
            print "Chunk Directory Exists : %s" % chunkDirectory

        else:
            try:
                os.mkdir(chunkDirectory)
            except OSError:
                print ("Creation of the chunk directory %s failed : " % chunkDirectory)
            else:
                print ("Chunk Directory successfully created : %s " % chunkDirectory)

        return self.chunkDirectory


    def constructSceneFile(self):

        #TARGET_DATA_BLOCK = getDataBlock(baseScenePath)

        # constFile = open(constScenePath, "wb+")
        # constFile.writelines(TARGET_DATA_BLOCK)
        # constFile.writelines(baseScenePath)
        # constFile.close()

        with open(self.baseScenePath, self.FILE_READ_ENCODING) as inputFile:

            chunkRead = partial(inputFile.read, self.DATA_CHUNK_SIZE)
            iterator = iter(chunkRead, b'')

            for INDEX, dataBlock in enumerate(iterator):

                # TODO : block = process_block(block)    # process block data
                chunkName = self.getChunkName(INDEX, self.chunkDirectory)
                with open(chunkName, self.FILE_WRITE_ENCODING) as outputChunk:
                    outputChunk.write(dataBlock)
                    self.chunkList.append(chunkName)
                    print "New chunk written to disc : %s " % outputChunk

        return self.chunkList

    @staticmethod
    def getChunkName(chunkIndex, chunkDirectory):

        CHUNK_STRING = "Chunk_"
        CHUNK_EXTENSION = ".bip"

        chunkNameString = os.path.join(chunkDirectory, CHUNK_STRING, chunkIndex + CHUNK_EXTENSION).replace("\\", "/")
        print "Chunk name string created : %s" % chunkNameString

        return chunkNameString

    def assembleOutputFile(self):

        outputFile = open(self.constScenePath, self.FILE_WRITE_ENCODING)

        for chunk in self.chunkList:

            print "Assembling : %s" % chunk

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

        outputFile.close()

        return True

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


def __main__(*args):

    print "Running KeyShot Pre Job Script"
    DeadlinePlugin = args[0]
    FileParser(DeadlinePlugin)




