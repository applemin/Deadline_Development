import os
import sys
import clr

from System import *
from System.Diagnostics import *
from Deadline.Scripting import *
from Deadline.Jobs import *
from System.IO import *



from Deadline.Plugins import *
from Deadline.Scripting import *


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
    if os.path.isfile(scene_file_path):
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

    target_job.SetJobPluginInfoKeyValue("SceneFile", Path.GetFileName(get_scene_file(DeadlinePlugin)))
    RepositoryUtils.SaveJob(target_job)


def __main__(*args):

    print("Script Started...")

    MIN_COMPLETED_TASKS = 0  # Min - Number of Completed Tasks BEFORE the job is queried. Change as applicable

    for job in RepositoryUtils.GetJobs(True):
        # Filter out non-"Active" jobs
        if job.JobStatus != "Active":
            continue

        print("JobStatus: %s" % job.JobStatus)

        jobId = job.JobId
        print("JobId: %s" % jobId)

        jobName = job.JobName
        print("JobName: %s" % jobName)

        JobTaskCount = job.JobTaskCount
        print("JobTaskCount: %s" % JobTaskCount)

        jobCompletedChunks = job.CompletedChunks
        print("JobCompletedChunks: %s" % jobCompletedChunks)

        job = RepositoryUtils.GetJob(jobId, True)
        tasks = RepositoryUtils.GetJobTasks(job, True)
        stats = JobUtils.CalculateJobStatistics(job, tasks)

        jobAverageFrameRenderTime = stats.AverageFrameRenderTime
        jobPeakRamUsage = stats.PeakRamUsage / 1024 / 1024

        print("JobAverageFrameRenderTime: %s" % jobAverageFrameRenderTime)
        print("JobPeakRamUsage: %s" % jobPeakRamUsage)

        if jobCompletedChunks >= MIN_COMPLETED_TASKS:
            if not jobAverageFrameRenderTime.Equals(TimeSpan.Zero):
                if jobPeakRamUsage != 0:

                    timeSpan = jobAverageFrameRenderTime
                    timeSpan = "%02dd:%02dh:%02dm:%02ds" % (timeSpan.Days, timeSpan.Hours, timeSpan.Minutes, timeSpan.Seconds)

                    job.ExtraInfo2 = str(timeSpan)
                    job.ExtraInfo3 = str(jobPeakRamUsage) + "Mb"

                    RepositoryUtils.SaveJob(job)
                else:
                    print("Job Peak Ram Usage is 0Mb at this time, skipping check until next scan...")
            else:
                print("Job Average Frame Render Time is 00:00:00 at this time, skipping check until next scan...")
        else:
            print("Min Number of Completed Tasks: %s not yet reached, skipping check until next scan..." % MIN_COMPLETED_TASKS)

    print("...Script Completed")


def __main__(*args):

    print " Running RBZip Post Job Script"
    DeadlinePlugin = args[0]
    update_scene_file(DeadlinePlugin)
