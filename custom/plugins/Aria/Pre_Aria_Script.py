import os
from enum import Enum


class SystemOptions(Enum):

    directlink = "SYS_directlink"
    filedate = "SYS_filedate"
    filename = "SYS_filename"
    find = "SYS_find"
    jid = "SYS_jid"
    link = "SYS_link"
    susspend = "SYS_susspend"
    uid = "SYS_uid"
    username = "SYS_username"
    userpath = "SYS_userpath"

class PrepDownloadEnv:

    def __init__(self, DeadlinePlugin):

        self.DeadlinePlugin = DeadlinePlugin

        self.DeadlinePlugin.LogInfo("Starting Download Env Preparation")
        self.job = self.DeadlinePlugin.GetJob()
        self.DeadlinePlugin.LogInfo("Current Job ID : %s " % str(self.job.JobId))

        for option in SystemOptions:
            self.DeadlinePlugin.LogInfo("System Options : ")
            self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (option, self.GetPluginInfoEntry(option)))

def __main__(*args):

    print " Running Aria Pre Job Script"
    DeadlinePlugin = args[0]
    PrepDownloadEnv(DeadlinePlugin)




