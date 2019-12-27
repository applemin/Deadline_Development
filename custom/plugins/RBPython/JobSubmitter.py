import os
import sys
import json
import requests
from pprint import pprint

import Deadline.DeadlineConnect as Connect
conn = Connect.DeadlineCon('localhost', 1234)


class Submitter:

    STORAGE_DIRECTORY = os.getenv("FILE_STORAGE")
    CLOUD_DIRECTORY = os.getenv("CLOUD_DIRECTORY")

    def __init__(self, *args):

        print type(args), args
        for idx, arg in enumerate(args[0]):
            print "Index : %s | Arg : %s" % (idx, arg)

        # get jobs data from API
        self.job_code = args[0][1]
        self.python_job_id = args[0][2]
        jobs_data = self.get_job_data()

        self.system_options = jobs_data["data"]["SystemInfo"]
        self.job_options = jobs_data["data"]["JobInfo"]
        self.plugin_options = jobs_data["data"]["PluginInfo"]

        self.scene_file_name = jobs_data["data"]["SystemInfo"]["find"]
        self.download_link = jobs_data["data"]["SystemInfo"]["directlink"]
        self.file_date = jobs_data["data"]["SystemInfo"]["filedate"]
        self.file_name = jobs_data["data"]["SystemInfo"]["filename"]
        self.find = jobs_data["data"]["SystemInfo"]["find"]
        self.uid = jobs_data["data"]["SystemInfo"]["uid"]
        self.user_name = jobs_data["data"]["SystemInfo"]["username"]
        self.user_path = jobs_data["data"]["SystemInfo"]["userpath"]

        self.validate_system_options()
        # create aria job
        aria_job_id = self.create_aria_job(self.python_job_id)
        # create extractor job
        zip_job_id = self.create_zip_job(aria_job_id)
        # create render job
        render_job_id = self.create_render_job(zip_job_id)

    def get_job_data(self):

        token_id = os.getenv("SOCKET_ID", str())
        print "Socket ID : %s" % token_id

        url = 'https://api.renderboost.com/node/demand/job-data'
        body = {'jobcode': self.job_code}
        headers = {'token': str(token_id)}

        request_data = requests.post(url, data=body, headers=headers)
        pprint(request_data.json())

        return request_data.json()

    def validate_system_options(self):

        for key, value in self.system_options.items():
            print "SysOptions Key : %s | Value : %s" % (key, value)
            if not value:
                raise ValueError("No value given for : %s" % key)
        return

    def create_aria_job(self, python_job_id):

        print "Creating Aria Job "
        plugin = "Aria"
        output_directory = os.path.join(self.STORAGE_DIRECTORY, self.user_path, self.job_code)

        if not os.path.exists(output_directory):
            print "Download directory is not exist : %s" % output_directory
            print "Creating download directory"
            os.makedirs(output_directory)

        if not os.path.exists(os.path.join(output_directory, self.file_name)):

            JobInfo = {"Name": self.job_code + "_Downloader",
                       "Frames": "1",
                       "Priority": 100,
                       "Plugin": plugin,
                       "BatchName": self.job_code + "_Batch",
                       "Whitelist": "S11",
                       "MachineLimit": 1,
                       "JobDependency0": str(python_job_id),
                       "PreJobScript": "A:/DeadlineRepository10/custom/plugins/Aria/Pre_Aria_Script.py"}

            PluginInfo = {'OutputDirectory': output_directory,
                          'DownloadLink': self.download_link,
                          'Version': 2,
                          'Log': '',
                          'DryRun': False,
                          'OutputFilename': '',
                          'ServerConnections': 1,
                          'SplitConnections': 5,
                          'ServerTimeStamp': True,
                          'Timeout': 60}

            try:
                new_job = conn.Jobs.SubmitJob(JobInfo, PluginInfo)
                print("Job created with id {}".format(new_job['_id']))
                return new_job['_id']
            except Exception as _err:
                print("Submission failed: %s" % _err)
        else:
            return

    def create_zip_job(self, aria_job_id):
        print "Creating RBZip Job "
        plugin = 'RBZip'
        output_directory = os.path.join(self.STORAGE_DIRECTORY, self.user_path, self.job_code)
        zip_file = os.path.join(output_directory, self.file_name)

        JobInfo = {"Name": self.job_code + "_Extractor",
                   "Frames": "1",
                   "Priority": 100,
                   "Plugin": plugin,
                   "BatchName": self.job_code + "_Batch",
                   "Whitelist": "S11",
                   "MachineLimit": 1,
                   "JobDependency0": str(aria_job_id),
                   "PostJobScript": "A:/DeadlineRepository10/custom/plugins/Aria/Post_RBZip_Script.py"}

        PluginInfo = {'ZipFile': zip_file,
                      'OutputDirectory': output_directory}

        try:
            new_job = conn.Jobs.SubmitJob(JobInfo, PluginInfo)
            print("Job created with id {}".format(new_job['_id']))
            return new_job['_id']
        except Exception as _err:
            print("Submission failed: %s" % _err)

    def create_render_job(self, zip_job_id):

        print "Creating Render Job "
        extra_job_options, extra_plugin_options = self.get_extra_options()

        JobInfo = {"BatchName": self.job_code + "_Batch",
                   "JobDependency0": str(zip_job_id)}
        JobInfo.update(self.job_options)
        JobInfo.update(extra_job_options)

        PluginInfo = dict()
        PluginInfo.update(self.plugin_options)
        PluginInfo.update(extra_plugin_options)

        try:
            new_job = conn.Jobs.SubmitJob(JobInfo, PluginInfo)
            print("Job created with id {}".format(new_job['_id']))
            return new_job['_id']
        except Exception as _err:
            print("Submission failed: %s" % _err)

    def get_extra_options(self):

        output_directory = self.create_cloud_directory()

        extra_job_options = {"OutputDirectory0": output_directory}

        extra_plugin_options = {"OutputFile": os.path.join(output_directory, self.job_options["OutputFilename0"])}

        if self.job_options["Plugin"] == "RBKeyshot":
            return extra_job_options, extra_plugin_options
        elif self.job_options["Plugin"] == "Keyshot":
            return extra_job_options, extra_plugin_options
        else:
            return extra_job_options, extra_plugin_options

    def get_scene_file(self):

        base_job_dir = os.path.join(self.STORAGE_DIRECTORY, self.user_path, self.job_code)
        scene_file_path = str()

        if os.path.exists(base_job_dir):
            print "Job directory is exists: %s" % base_job_dir
        else:
            raise Exception("Job folder is not exist in storage %s" % base_job_dir)

        for (dir_path, dir_names, file_names) in os.walk(base_job_dir):
            print "Looking for scene file `%s` in `%s` " % (self.find, base_job_dir)
            scene_file_path = [os.path.join(dir_path, _file) for _file in file_names if _file == self.find]
            print "Scene file path result : %s " % scene_file_path
        if os.path.isfile(scene_file_path):
            return scene_file_path[0]
        else:
            raise Exception("Scene file path not found. %s" % scene_file_path)

    def create_cloud_directory(self):

        cloud_job_folder = os.path.join(self.CLOUD_DIRECTORY, self.job_code)
        if not os.path.exists(cloud_job_folder):
            os.makedirs(cloud_job_folder)
            print "Job folder created in cloud : %s" % cloud_job_folder

        return cloud_job_folder


if __name__ == "__main__":
    submitter = Submitter(sys.argv)



