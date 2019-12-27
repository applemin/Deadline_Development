import os
import sys
from Deadline.Scripting import RepositoryUtils

def update_scene_file(DeadlinePlugin):
    current_job = DeadlinePlugin.GetJob()
    jobs = RepositoryUtils.GetJobs()
    for job in jobs:
        if job.JobName == current_job.JobName:
            print job.JobName



def __main__(*args):

    print " Running RBZip Post Job Script"
    DeadlinePlugin = args[0]
    update_scene_file(DeadlinePlugin)
