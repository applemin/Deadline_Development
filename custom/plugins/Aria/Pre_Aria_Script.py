import os


class SystemOptions():

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

        self.SystemOptions = {"SYS_directlink": self.DeadlinePlugin.GetPluginInfoEntry("SYS_directlink"),
                              "SYS_filedate": self.DeadlinePlugin.GetPluginInfoEntry("SYS_filedate"),
                              "SYS_filename": self.DeadlinePlugin.GetPluginInfoEntry("SYS_filename"),
                              "SYS_find": self.DeadlinePlugin.GetPluginInfoEntry("SYS_find"),
                              "SYS_jid": self.DeadlinePlugin.GetPluginInfoEntry("SYS_jid"),
                              "SYS_link": self.DeadlinePlugin.GetPluginInfoEntry("SYS_link"),
                              "SYS_susspend": self.DeadlinePlugin.GetPluginInfoEntry("SYS_susspend"),
                              "SYS_uid": self.DeadlinePlugin.GetPluginInfoEntry("SYS_uid"),
                              "SYS_username": self.DeadlinePlugin.GetPluginInfoEntry("SYS_username"),
                              "SYS_userpath": self.DeadlinePlugin.GetPluginInfoEntry("SYS_userpath")
                              }

        self.DeadlinePlugin.LogInfo("System Options : ")
        for key, value in self.SystemOptions.items():
            self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (key, value))


def __main__(*args):

    print " Running Aria Pre Job Script"
    DeadlinePlugin = args[0]
    PrepDownloadEnv(DeadlinePlugin)




