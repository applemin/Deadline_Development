import os
import sys
sys.path.append("A:/DeadlineRepository10/api/python/Deadline")
import Deadline.DeadlineConnect as Connect

class SystemOptions():

    directlink = "SYS_directlink"
    filedate = "SYS_filedate"
    filename = "SYS_filename"
    find = "SYS_find"
    jid = "SYS_jid"
    uid = "SYS_uid"
    username = "SYS_username"
    userpath = "SYS_userpath"


class PrepDownloadEnv:

    def __init__(self, DeadlinePlugin):

        self.DeadlinePlugin = DeadlinePlugin

        self.DeadlinePlugin.LogInfo("Starting Download Env Preparation")
        self.job = self.DeadlinePlugin.GetJob()
        self.DeadlinePlugin.LogInfo("Current Job ID : %s " % str(self.job.JobId))

        self.SystemOptions = {SystemOptions.directlink: self.DeadlinePlugin.GetPluginInfoEntry("SYS_directlink"),
                              SystemOptions.filedate: self.DeadlinePlugin.GetPluginInfoEntry("SYS_filedate"),
                              SystemOptions.filename: self.DeadlinePlugin.GetPluginInfoEntry("SYS_filename"),
                              SystemOptions.find: self.DeadlinePlugin.GetPluginInfoEntry("SYS_find"),
                              SystemOptions.jid: self.DeadlinePlugin.GetPluginInfoEntry("SYS_jid"),
                              SystemOptions.uid: self.DeadlinePlugin.GetPluginInfoEntry("SYS_uid"),
                              SystemOptions.username: self.DeadlinePlugin.GetPluginInfoEntry("SYS_username"),
                              SystemOptions.userpath: self.DeadlinePlugin.GetPluginInfoEntry("SYS_userpath")}

        self.DeadlinePlugin.LogInfo("System Options : ")
        for key, value in self.SystemOptions.items():
            self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (key, value))


def __main__(*args):

    print " Running Aria Pre Job Script"
    DeadlinePlugin = args[0]
    PrepDownloadEnv(DeadlinePlugin)
