import os


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

        self.DeadlinePlugin.LogInfo("System Options : ")
        self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (SystemOptions.directlink, self.DeadlinePlugin.GetPluginInfoEntry(SystemOptions.directlink)))
        self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (SystemOptions.filedate, self.DeadlinePlugin.GetPluginInfoEntry(SystemOptions.filedate)))
        self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (SystemOptions.filename, self.DeadlinePlugin.GetPluginInfoEntry(SystemOptions.filename)))
        self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (SystemOptions.find, self.DeadlinePlugin.GetPluginInfoEntry(SystemOptions.find)))
        self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (SystemOptions.jid, self.DeadlinePlugin.GetPluginInfoEntry(SystemOptions.jid)))
        self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (SystemOptions.link, self.DeadlinePlugin.GetPluginInfoEntry(SystemOptions.link)))
        self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (SystemOptions.susspend, self.DeadlinePlugin.GetPluginInfoEntry(SystemOptions.susspend)))
        self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (SystemOptions.uid, self.DeadlinePlugin.GetPluginInfoEntry(SystemOptions.uid)))
        self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (SystemOptions.username, self.DeadlinePlugin.GetPluginInfoEntry(SystemOptions.username)))
        self.DeadlinePlugin.LogInfo("Key:%s | Value:%s" % (SystemOptions.userpath, self.DeadlinePlugin.GetPluginInfoEntry(SystemOptions.userpath)))

def __main__(*args):

    print " Running Aria Pre Job Script"
    DeadlinePlugin = args[0]
    PrepDownloadEnv(DeadlinePlugin)




