import subprocess
import os

from Deadline.Scripting import *


def __main__():

    jobIds = MonitorUtils.GetSelectedJobIds()

    for jobId in jobIds:
        job = RepositoryUtils.GetJob(jobId, True)
        print "Job Name : " % job.JobName
        path = job.GetJobPluginInfoKeyValue("SceneFile").replace("\\", "/")
        path = os.path.dirname(path).replace("/", "\\")
        print "Scene File Path : %s" % path
        subprocess.Popen('explorer "%s"' % path)
