import os
import sys
import clr

from System import *
from System.Diagnostics import *
from Deadline.Scripting import *
from Deadline.Jobs import *
from System.IO import *
from Deadline.Plugins import *


def get_scene_file(DeadlinePlugin):

    scene_file_name = DeadlinePlugin.GetPluginInfoEntryWithDefault("SceneFile", str())
    base_job_dir = DeadlinePlugin.GetPluginInfoEntryWithDefault("JobDirectory", str())
    scene_file_path = str()

    if os.path.exists(base_job_dir):
        print "Job directory is exists: %s" % base_job_dir
    else:
        raise Exception("Job folder is not exist in storage %s" % base_job_dir)

    for (dir_path, dir_names, file_names) in os.walk(base_job_dir):
        print "Looking for scene file `%s` in `%s` " % (scene_file_name, base_job_dir)
        scene_file_path=[os.path.join(dir_path, _file) for _file in file_names if _file == scene_file_name]
        print "Scene file path result : %s " % scene_file_path
    if os.path.isfile(scene_file_path[0]):
        return str(scene_file_path[0])
    else:
        raise Exception("Scene file path not found. %s" % scene_file_path)


def update_scene_file(DeadlinePlugin):

    current_job = DeadlinePlugin.GetJob()
    target_job = None
    jobs = RepositoryUtils.GetJobs(True)

    for job in jobs:
        if job.JobName == current_job.JobName.split("_Extractor")[0]:
            target_job = RepositoryUtils.GetJob(job.JobId, True)
            print "Target job ID : %s" % str(target_job)

    target_job.SetJobPluginInfoKeyValue("SceneFile", get_scene_file(DeadlinePlugin))
    RepositoryUtils.SaveJob(target_job)


def __main__(*args):

    print " Running RBZip Post Job Script"
    DeadlinePlugin = args[0]
    update_scene_file(DeadlinePlugin)
