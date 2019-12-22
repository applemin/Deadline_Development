import os


class PrepDownloadEnv:

    def __init__(self, DeadlinePlugin):

        self.DeadlinePlugin = DeadlinePlugin

        self.DeadlinePlugin.LogInfo("    Starting Download Env Preparation : %s ")
        self.job = self.DeadlinePlugin.GetJob()
        self.DeadlinePlugin.LogInfo("    Current Job ID : %s " % str(self.job.JobId))

def __main__(*args):

    print " Running Aria Pre Job Script"
    DeadlinePlugin = args[0]
    PrepDownloadEnv(DeadlinePlugin)




