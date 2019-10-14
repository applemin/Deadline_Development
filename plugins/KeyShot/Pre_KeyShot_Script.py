import os
from functools import partial

#######################################################################################################################
# GET/SET global variables
#######################################################################################################################


class FileParser:

    FILE_READ_ENCODING      = "rb"
    FILE_WRITE_ENCODING     = "wb+"

    baseScenePath           = None
    constScenePath          = None
    directoryPath           = None
    chunkDirectory          = None
    dataBlockFile           = None
    dataBlockPath           = None
    dataBlockReminderPath   = None
    chunkList               = []

    DIR_STRING              = "CHUNKED_FILES"

    DATA_CHUNK_SIZE         = 50000000 * 5


    def __init__(self, DeadlinePlugin):

        pass
        # self.DeadlinePlugin         = DeadlinePlugin
        # self.getScenePath           = self.getScenePath()
        # self.createChunkDirectory   = self.createChunkDirectory()
        # self.constructSceneFile     = self.constructSceneFile()
        # self.createDataBlock        = self.createDataBlock()
        # self.assembleOutputFile     = self.assembleOutputFile()
        # self.cleanup                = self.cleanup()


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
            print " Chunk Directory Exists : %s" % chunkDirectory

        else:
            try:
                os.mkdir(chunkDirectory)
            except OSError:
                self.DeadlinePlugin.LogWarning("    Creation of the chunk directory %s failed : " % chunkDirectory)
            else:
                self.DeadlinePlugin.LogInfo("   Chunk Directory successfully created : %s " % chunkDirectory)

        return self.chunkDirectory


    def constructSceneFile(self):

        with open(self.baseScenePath, self.FILE_READ_ENCODING) as inputFile:

            chunkRead = partial(inputFile.read, self.DATA_CHUNK_SIZE)
            iterator = iter(chunkRead, b'')

            for INDEX, dataBlock in enumerate(iterator):

                chunkName = self.getChunkName(INDEX, self.chunkDirectory)
                with open(chunkName, self.FILE_WRITE_ENCODING) as outputChunk:
                    outputChunk.write(dataBlock)
                    self.chunkList.append(chunkName)
                    self.DeadlinePlugin.LogInfo("   New chunk written to disc : %s " % outputChunk)

        return self.chunkList

    @staticmethod
    def getChunkName(chunkIndex, chunkDirectory):

        CHUNK_STRING = "Chunk_"
        CHUNK_EXTENSION = ".bip"
        CHUNK_FILE_NAME = CHUNK_STRING + str(chunkIndex) + CHUNK_EXTENSION

        chunkNameString = os.path.join(chunkDirectory, CHUNK_FILE_NAME)
        chunkNameString = chunkNameString.replace("\\", "/")

        print " Chunk name string created : %s" % chunkNameString

        return chunkNameString

    def createDataBlock(self):

        END_BLOCK_LINE_NUM = None
        END_LINE_STRING = "output_style_id"
        DATA_BLOCK_FILE_NAME = "_DataBlock.bip"
        DATA_REMINDER_FILE_NAME = "_DataChunckReminder.bip"

        self.dataBlockChunk = self.chunkList[0]

        dataBlockChunk = open(self.dataBlockChunk, self.FILE_READ_ENCODING)
        dataBlockLines = dataBlockChunk.readlines()
        dataBlockChunk.close()
        self.chunkList.pop(0)

        for counter, line in enumerate(dataBlockLines):
            if END_LINE_STRING in line:
                END_BLOCK_LINE_NUM = counter+1
                break

        self.dataBlockPath = os.path.join(self.chunkDirectory, DATA_BLOCK_FILE_NAME)
        self.dataBlockPath = self.dataBlockPath.replace("\\", "/")

        self.dataBlockReminderPath = os.path.join(self.chunkDirectory, DATA_REMINDER_FILE_NAME)
        self.dataBlockReminderPath = self.dataBlockReminderPath.replace("\\", "/")

        dataBlockOutputFile = open(self.dataBlockPath, self.FILE_WRITE_ENCODING)
        dataBlockOutputFile.writelines(dataBlockLines[:END_BLOCK_LINE_NUM])
        dataBlockOutputFile.close()
        self.chunkList.insert(0, self.dataBlockPath)
        self.DeadlinePlugin.LogInfo("   DataBlock file successfully created : %s" % self.dataBlockPath)

        dataBlockOutputReminder = open(self.dataBlockReminderPath, self.FILE_WRITE_ENCODING)
        dataBlockOutputReminder.writelines(dataBlockLines[END_BLOCK_LINE_NUM:])
        dataBlockOutputReminder.close()
        self.chunkList.insert(1, self.dataBlockReminderPath)
        self.DeadlinePlugin.LogInfo("   DataBlockReminder file successfully created : %s" % self.dataBlockReminderPath)

        return self.dataBlockPath, self.dataBlockReminderPath


    def assembleOutputFile(self):

        outputFile = open(self.constScenePath, self.FILE_WRITE_ENCODING)

        for chunkFile in self.chunkList:

            self.DeadlinePlugin.LogInfo("   Assembling : %s" % chunkFile)
            outputFile.writelines(open(chunkFile, "rb").readlines())

        outputFile.close()

        return True


    def cleanup(self):

        self.DeadlinePlugin.LogInfo("   Running Cleanup")


def __main__(*args):

    print " Running KeyShot Pre Job Script"
    DeadlinePlugin = args[0]
    FileParser(DeadlinePlugin)




